"""
Webhook handlers for Stripe, PayPal, and M-Pesa payment gateways.
"""

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from decimal import Decimal
import json
import stripe
import hmac
import hashlib
import requests
from django.utils import timezone

from .models import Transaction, Wallet


# ============================================================================
# STRIPE WEBHOOK HANDLERS
# ============================================================================

@csrf_exempt
@require_http_methods(["POST"])
def stripe_webhook(request):
    """
    Main Stripe webhook handler.
    Verifies webhook signature and handles payment events.
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        # Get Stripe secret key from settings
        stripe_webhook_secret = settings.STRIPE_WEBHOOK_SECRET

        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, stripe_webhook_secret
        )
    except ValueError:
        # Invalid payload
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        return JsonResponse({'error': 'Invalid signature'}, status=400)
    except Exception as e:
        # Other errors
        return JsonResponse({'error': str(e)}, status=400)

    try:
        # Handle different event types
        event_type = event['type']
        data = event['data']['object']

        if event_type == 'payment_intent.succeeded':
            handle_stripe_payment_success(data)
        elif event_type == 'payment_intent.payment_failed':
            handle_stripe_payment_failed(data)
        elif event_type == 'charge.refunded':
            handle_stripe_refund(data)

        return JsonResponse({'status': 'received'}, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def handle_stripe_payment_success(payment_intent):
    """
    Handle successful Stripe payment.
    Updates transaction to completed and credits wallet.
    """
    try:
        gateway_transaction_id = payment_intent.get('id')
        metadata = payment_intent.get('metadata', {})

        # Find transaction by gateway ID
        transaction = Transaction.objects.get(
            gateway_transaction_id=gateway_transaction_id,
            payment_gateway='stripe'
        )

        # Update transaction status
        transaction.status = 'completed'
        transaction.metadata['stripe_event'] = 'payment_intent.succeeded'
        transaction.metadata['charged_at'] = timezone.now().isoformat()
        transaction.save()

        # Credit user's wallet
        wallet = transaction.wallet
        if wallet:
            wallet.credit(transaction.amount)

        # Mark subscription as active if linked
        if transaction.invoice:
            transaction.invoice.mark_as_paid()
            
        # Check if this payment is for a subscription purchase
        if transaction.transaction_type == 'deposit':
            subscription_plan_id = transaction.metadata.get('subscription_plan_id')
            subscription_renewal_id = transaction.metadata.get('subscription_renewal_id')
            
            if subscription_plan_id:
                # Create new subscription
                from .models import SubscriptionPlan, UserSubscription
                try:
                    plan = SubscriptionPlan.objects.get(id=subscription_plan_id, is_active=True)
                    subscription = UserSubscription.objects.create(
                        user=transaction.user,
                        plan=plan,
                        payment_method=transaction.payment_gateway,
                        status='pending'
                    )
                    subscription.activate()
                except SubscriptionPlan.DoesNotExist:
                    pass
            elif subscription_renewal_id:
                # Renew existing subscription
                from .models import UserSubscription
                try:
                    subscription = UserSubscription.objects.get(id=subscription_renewal_id, user=transaction.user)
                    subscription.status = 'active'
                    subscription.activate()
                except UserSubscription.DoesNotExist:
                    pass

    except Transaction.DoesNotExist:
        pass
    except Exception as e:
        pass


def handle_stripe_payment_failed(payment_intent):
    """
    Handle failed Stripe payment.
    Updates transaction to failed status.
    """
    try:
        gateway_transaction_id = payment_intent.get('id')
        last_payment_error = payment_intent.get('last_payment_error', {})
        error_message = last_payment_error.get('message', 'Unknown error')

        # Find transaction by gateway ID
        transaction = Transaction.objects.get(
            gateway_transaction_id=gateway_transaction_id,
            payment_gateway='stripe'
        )

        # Update transaction status
        transaction.mark_as_failed(reason=error_message)
        transaction.metadata['stripe_error'] = error_message
        transaction.metadata['failed_at'] = timezone.now().isoformat()
        transaction.save()

    except Transaction.DoesNotExist:
        pass
    except Exception as e:
        pass


def handle_stripe_refund(charge):
    """
    Handle Stripe refund.
    Creates refund transaction and credits wallet.
    """
    try:
        gateway_transaction_id = charge.get('id')
        refund_amount = Decimal(str(charge.get('amount_refunded', 0))) / 100  # Convert from cents

        # Find original transaction
        original_transaction = Transaction.objects.get(
            gateway_transaction_id=gateway_transaction_id,
            payment_gateway='stripe'
        )

        # Create refund transaction
        refund_transaction = Transaction.objects.create(
            user=original_transaction.user,
            wallet=original_transaction.wallet,
            invoice=original_transaction.invoice,
            transaction_type='refund',
            amount=refund_amount,
            currency=original_transaction.currency,
            payment_gateway='stripe',
            gateway_transaction_id=f"{gateway_transaction_id}_refund",
            status='completed',
            metadata={
                'original_transaction_id': original_transaction.transaction_id,
                'original_charge_id': gateway_transaction_id,
                'refunded_at': timezone.now().isoformat()
            }
        )

        # Update original transaction
        original_transaction.status = 'refunded'
        original_transaction.metadata['refund_id'] = refund_transaction.transaction_id
        original_transaction.save()

        # Credit wallet
        wallet = original_transaction.wallet
        if wallet:
            wallet.credit(refund_amount)

    except Transaction.DoesNotExist:
        pass
    except Exception as e:
        pass


# ============================================================================
# PAYPAL WEBHOOK HANDLERS
# ============================================================================

@csrf_exempt
@require_http_methods(["POST"])
def paypal_webhook(request):
    """
    PayPal IPN (Instant Payment Notification) handler.
    Verifies IPN with PayPal and processes payment notifications.
    """
    try:
        # Get the IPN data
        ipn_data = request.POST.dict()

        # Verify IPN with PayPal
        if not verify_paypal_ipn(ipn_data):
            return JsonResponse({'error': 'IPN verification failed'}, status=400)

        # Get payment status
        payment_status = ipn_data.get('payment_status')

        if payment_status == 'Completed':
            handle_paypal_payment_success(ipn_data)
        elif payment_status == 'Refunded':
            handle_paypal_refund(ipn_data)
        elif payment_status == 'Failed':
            handle_paypal_payment_failed(ipn_data)

        return JsonResponse({'status': 'received'}, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def verify_paypal_ipn(ipn_data):
    """
    Verify PayPal IPN signature.
    """
    try:
        paypal_url = settings.PAYPAL_IPN_URL  # Set to sandbox or live URL in settings

        # Prepare verification data
        verify_data = {'cmd': '_notify-validate'}
        verify_data.update(ipn_data)

        # Send verification request to PayPal
        response = requests.post(paypal_url, data=verify_data, timeout=10)

        return response.text == 'VERIFIED'

    except Exception as e:
        return False


def handle_paypal_payment_success(ipn_data):
    """
    Handle successful PayPal payment.
    Updates transaction to completed and credits wallet.
    """
    try:
        gateway_transaction_id = ipn_data.get('txn_id')
        custom_data = ipn_data.get('custom', '')
        amount = Decimal(ipn_data.get('mc_gross', 0))

        # Find transaction by gateway ID
        transaction = Transaction.objects.get(
            gateway_transaction_id=gateway_transaction_id,
            payment_gateway='paypal'
        )

        # Update transaction status
        transaction.status = 'completed'
        transaction.metadata['paypal_event'] = 'payment_status_completed'
        transaction.metadata['paypal_payer_email'] = ipn_data.get('payer_email', '')
        transaction.metadata['paid_at'] = timezone.now().isoformat()
        transaction.save()

        # Credit wallet
        wallet = transaction.wallet
        if wallet:
            wallet.credit(transaction.amount)

        # Mark invoice as paid if linked
        if transaction.invoice:
            transaction.invoice.mark_as_paid()

    except Transaction.DoesNotExist:
        pass
    except Exception as e:
        pass


def handle_paypal_payment_failed(ipn_data):
    """
    Handle failed PayPal payment.
    Updates transaction to failed status.
    """
    try:
        gateway_transaction_id = ipn_data.get('txn_id')
        reason = ipn_data.get('reason_code', 'Unknown reason')

        # Find transaction by gateway ID
        transaction = Transaction.objects.get(
            gateway_transaction_id=gateway_transaction_id,
            payment_gateway='paypal'
        )

        # Update transaction status
        transaction.mark_as_failed(reason=reason)
        transaction.metadata['paypal_error'] = reason
        transaction.metadata['failed_at'] = timezone.now().isoformat()
        transaction.save()

    except Transaction.DoesNotExist:
        pass
    except Exception as e:
        pass


def handle_paypal_refund(ipn_data):
    """
    Handle PayPal refund.
    Creates refund transaction and credits wallet.
    """
    try:
        gateway_transaction_id = ipn_data.get('txn_id')
        parent_txn_id = ipn_data.get('parent_txn_id')
        refund_amount = Decimal(ipn_data.get('mc_gross', 0))

        # Find original transaction
        original_transaction = Transaction.objects.get(
            gateway_transaction_id=parent_txn_id,
            payment_gateway='paypal'
        )

        # Create refund transaction
        refund_transaction = Transaction.objects.create(
            user=original_transaction.user,
            wallet=original_transaction.wallet,
            invoice=original_transaction.invoice,
            transaction_type='refund',
            amount=abs(refund_amount),
            currency=original_transaction.currency,
            payment_gateway='paypal',
            gateway_transaction_id=f"{parent_txn_id}_refund",
            status='completed',
            metadata={
                'original_transaction_id': original_transaction.transaction_id,
                'original_txn_id': parent_txn_id,
                'refund_txn_id': gateway_transaction_id,
                'refunded_at': timezone.now().isoformat()
            }
        )

        # Update original transaction
        original_transaction.status = 'refunded'
        original_transaction.metadata['refund_id'] = refund_transaction.transaction_id
        original_transaction.save()

        # Credit wallet
        wallet = original_transaction.wallet
        if wallet:
            wallet.credit(abs(refund_amount))

    except Transaction.DoesNotExist:
        pass
    except Exception as e:
        pass


# ============================================================================
# M-PESA WEBHOOK HANDLERS
# ============================================================================

@csrf_exempt
@require_http_methods(["POST"])
def mpesa_webhook(request):
    """
    M-Pesa callback handler for STK push responses.
    Processes payment confirmations from M-Pesa.
    """
    try:
        # Parse JSON callback data
        callback_data = json.loads(request.body)
        body = callback_data.get('Body', {})
        stk_callback = body.get('stkCallback', {})

        # Extract callback details
        result_code = stk_callback.get('ResultCode')
        result_desc = stk_callback.get('ResultDesc')
        merchant_request_id = stk_callback.get('MerchantRequestID')
        checkout_request_id = stk_callback.get('CheckoutRequestID')

        # Handle result
        if result_code == 0:
            # Success
            callback_metadata = stk_callback.get('CallbackMetadata', {})
            items = callback_metadata.get('Item', [])

            # Extract payment details
            amount = None
            mpesa_receipt_number = None
            phone_number = None

            for item in items:
                item_name = item.get('Name')
                item_value = item.get('Value')

                if item_name == 'Amount':
                    amount = Decimal(str(item_value))
                elif item_name == 'MpesaReceiptNumber':
                    mpesa_receipt_number = item_value
                elif item_name == 'PhoneNumber':
                    phone_number = item_value

            handle_mpesa_payment_success(
                checkout_request_id,
                amount,
                mpesa_receipt_number,
                phone_number
            )
        else:
            # Failed or cancelled
            handle_mpesa_payment_failed(
                checkout_request_id,
                result_code,
                result_desc
            )

        return JsonResponse({'ResultCode': 0}, status=200)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def handle_mpesa_payment_success(checkout_request_id, amount, mpesa_receipt_number, phone_number):
    """
    Handle successful M-Pesa payment.
    Updates transaction to completed and credits wallet.
    """
    try:
        # Find transaction by checkout request ID (stored as gateway_transaction_id)
        transaction = Transaction.objects.get(
            gateway_transaction_id=checkout_request_id,
            payment_gateway='mpesa'
        )

        # Update transaction status
        transaction.status = 'completed'
        transaction.metadata['mpesa_receipt_number'] = mpesa_receipt_number
        transaction.metadata['mpesa_phone_number'] = phone_number
        transaction.metadata['mpesa_amount'] = str(amount)
        transaction.metadata['completed_at'] = timezone.now().isoformat()
        transaction.save()

        # Credit wallet
        wallet = transaction.wallet
        if wallet:
            wallet.credit(transaction.amount)

        # Mark invoice as paid if linked
        if transaction.invoice:
            transaction.invoice.mark_as_paid()

    except Transaction.DoesNotExist:
        pass
    except Exception as e:
        pass


def handle_mpesa_payment_failed(checkout_request_id, result_code, result_desc):
    """
    Handle failed M-Pesa payment.
    Updates transaction to failed status.
    """
    try:
        # Find transaction by checkout request ID
        transaction = Transaction.objects.get(
            gateway_transaction_id=checkout_request_id,
            payment_gateway='mpesa'
        )

        # Map M-Pesa result codes to user-friendly messages
        error_messages = {
            1: 'User cancelled the operation',
            2: 'The initiator information is invalid',
            9: 'Transaction processing in progress',
        }

        error_reason = error_messages.get(result_code, result_desc)

        # Update transaction status
        transaction.mark_as_failed(reason=error_reason)
        transaction.metadata['mpesa_result_code'] = result_code
        transaction.metadata['mpesa_result_desc'] = result_desc
        transaction.metadata['failed_at'] = timezone.now().isoformat()
        transaction.save()

    except Transaction.DoesNotExist:
        pass
    except Exception as e:
        pass
