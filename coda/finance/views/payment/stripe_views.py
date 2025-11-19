import json
import logging
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.utils import timezone
from finance.models import Payment_Information, Payment_History
from finance.utils import save_payment_history
from accounts.models import CustomerUser

logger = logging.getLogger(__name__)

# Optional Stripe import
try:
    import stripe
    stripe_available = True
    # Configure Stripe
    stripe.api_key = settings.STRIPE_SECRET_KEY
except ImportError:
    stripe = None
    stripe_available = False
    logger.warning("Stripe library not installed - Stripe payments will not be available")


@login_required
@require_http_methods(["POST", "GET"])
def create_checkout_session(request):
    """
    Create a Stripe Checkout Session (server-side, no JavaScript needed)
    This redirects to Stripe's hosted checkout page
    """
    if not stripe_available:
        print("[Stripe][DEBUG] stripe library unavailable in create_checkout_session")
        from django.contrib import messages
        messages.error(request, 'Stripe is not available. Please use another payment method.')
        return redirect('finance:payment_method_selection')
    
    from django.shortcuts import redirect
    from django.urls import reverse
    
    try:
        # Get user's payment information first (needed for amount calculation)
        try:
            payment_info = Payment_Information.objects.filter(
                customer=request.user
            ).only('id', 'customer', 'payment_fees', 'down_payment', 'plan').order_by('-id').first()
        except Exception as db_error:
            logger.warning(f"Database query issue: {db_error}")
            print(f"[Stripe][DEBUG] Payment info lookup failed: {db_error}")
            from django.contrib import messages
            messages.error(request, 'Payment information not found.')
            return redirect('finance:payment_method_selection')
        
        if not payment_info:
            print("[Stripe][DEBUG] No payment information found for user")
            from django.contrib import messages
            messages.error(request, 'No payment information found.')
            return redirect('finance:payment_method_selection')
        
        # Get amount from POST (form submission) or GET (direct link)
        if request.method == 'POST':
            # Handle form POST (from stripe_form.html)
            amount_type = request.POST.get('amount_type', 'full')
            
            if amount_type == 'full':
                # Get full amount from payment info
                amount = float(payment_info.get_fee_balance())
            else:
                # Partial payment - get amount from form
                amount = float(request.POST.get('amount', 0))
            
            print(f"[Stripe][DEBUG] Form POST: amount_type={amount_type} amount={amount} user={request.user.id}")
        else:
            # GET request - get amount from query string (default to full balance)
            amount = float(request.GET.get('amount', payment_info.get_fee_balance()))
            print(f"[Stripe][DEBUG] GET request: amount={amount} user={request.user.id}")
        
        if amount <= 0:
            print("[Stripe][DEBUG] Invalid amount received for Checkout Session")
            from django.contrib import messages
            messages.error(request, 'Invalid payment amount. Please enter a valid amount.')
            return redirect('finance:unified_processing', method='stripe')
        
        print(f"[Stripe][DEBUG] Using PaymentInformation id={payment_info.id} plan={payment_info.plan}")
        
        # Build success and cancel URLs
        success_url = request.build_absolute_uri(reverse('finance:stripe_checkout_success'))
        cancel_url = request.build_absolute_uri(reverse('finance:stripe_checkout_cancel'))
        
        # Add session_id parameter to success URL for verification
        success_url += '?session_id={CHECKOUT_SESSION_ID}'
        
        # Create Checkout Session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f'Payment for {request.user.username}',
                        'description': f'Payment of ${amount:.2f}',
                    },
                    'unit_amount': int(amount * 100),  # Convert to cents
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=request.user.email if hasattr(request.user, 'email') and request.user.email else None,
            metadata={
                'user_id': str(request.user.id),
                'payment_info_id': str(payment_info.id),
                'amount': str(amount),
                'reference': f"STRIPE-CHECKOUT-{request.user.id}-{amount}",
            },
        )
        
        print(f"[Stripe][DEBUG] Checkout Session created id={checkout_session.id} url={checkout_session.url}")
        
        # Redirect to Stripe Checkout
        return redirect(checkout_session.url)
        
    except stripe._error.CardError as e:
        logger.error(f"Stripe card error: {str(e)}")
        from django.contrib import messages
        messages.error(request, str(e.user_message))
        return redirect('finance:payment_method_selection')
        
    except stripe._error.RateLimitError as e:
        logger.error(f"Stripe rate limit error: {str(e)}")
        from django.contrib import messages
        messages.error(request, 'Too many requests. Please try again later.')
        return redirect('finance:payment_method_selection')
        
    except stripe._error.InvalidRequestError as e:
        logger.error(f"Stripe invalid request error: {str(e)}")
        from django.contrib import messages
        messages.error(request, 'Invalid request. Please check your payment details.')
        return redirect('finance:payment_method_selection')
        
    except stripe._error.AuthenticationError as e:
        logger.error(f"Stripe authentication error: {str(e)}")
        from django.contrib import messages
        messages.error(request, 'Payment service authentication failed.')
        return redirect('finance:payment_method_selection')
        
    except stripe._error.APIConnectionError as e:
        logger.error(f"Stripe API connection error: {str(e)}")
        from django.contrib import messages
        messages.error(request, 'Payment service temporarily unavailable.')
        return redirect('finance:payment_method_selection')
        
    except stripe._error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        from django.contrib import messages
        messages.error(request, 'Payment processing failed. Please try again.')
        return redirect('finance:payment_method_selection')
        
    except Exception as e:
        logger.error(f"Unexpected error in create_checkout_session: {str(e)}")
        import traceback
        traceback.print_exc()
        from django.contrib import messages
        messages.error(request, 'An unexpected error occurred. Please try again.')
        return redirect('finance:payment_method_selection')


@login_required
def stripe_checkout_success(request):
    """
    Handle successful Stripe Checkout payment
    """
    from django.shortcuts import redirect
    from django.contrib import messages
    from django.urls import reverse
    
    session_id = request.GET.get('session_id')
    
    if not session_id:
        messages.error(request, 'Invalid payment session.')
        return redirect('finance:payment_method_selection')
    
    if not stripe_available:
        messages.error(request, 'Stripe is not available.')
        return redirect('finance:payment_method_selection')
    
    try:
        # Retrieve the Checkout Session
        checkout_session = stripe.checkout.Session.retrieve(session_id)
        
        print(f"[Stripe][DEBUG] Checkout success session_id={session_id} payment_status={checkout_session.payment_status}")
        
        if checkout_session.payment_status == 'paid':
            # Extract metadata
            metadata = checkout_session.metadata or {}
            user_id = metadata.get('user_id')
            payment_info_id = metadata.get('payment_info_id')
            amount = float(metadata.get('amount', 0))
            reference = metadata.get('reference', f"STRIPE-CHECKOUT-{session_id}")
            
            if user_id and payment_info_id:
                try:
                    # Get payment info
                    payment_info = Payment_Information.objects.only('id', 'customer', 'payment_fees', 'down_payment', 'plan').get(id=payment_info_id)
                    
                    # Save payment history
                    user = CustomerUser.objects.get(id=int(user_id))
                    ok = save_payment_history(
                        user=user,
                        payment_info=payment_info,
                        method='Stripe',
                        reference=reference,
                        amount=amount,
                        status='completed'
                    )
                    
                    if ok:
                        logger.info(f"Payment history saved for Stripe Checkout {session_id}")
                        print(f"[Stripe][DEBUG] Payment history saved for session={session_id}")
                        messages.success(request, f'Payment of ${amount:.2f} completed successfully!')
                    else:
                        logger.error(f"Failed to save payment history for Stripe Checkout {session_id}")
                        print(f"[Stripe][DEBUG] Failed to save payment history for session={session_id}")
                        messages.warning(request, 'Payment completed but there was an issue saving the record. Please contact support.')
                    
                    # Store payment details in session for success page
                    request.session['payment_reference'] = reference
                    request.session['payment_amount'] = amount
                    request.session['payment_method'] = 'Stripe'
                    request.session['payment_date'] = timezone.now().isoformat()
                    print(f"[Stripe][DEBUG] Stored payment details in session: amount={amount} method=Stripe reference={reference}")
                        
                except Exception as e:
                    logger.error(f"Error processing Stripe Checkout success: {str(e)}")
                    print(f"[Stripe][DEBUG] Exception while handling checkout success: {e}")
                    import traceback
                    traceback.print_exc()
                    messages.warning(request, 'Payment completed but there was an issue processing it. Please contact support.')
                    # Still store basic info even if save failed
                    request.session['payment_reference'] = reference
                    request.session['payment_amount'] = amount
                    request.session['payment_method'] = 'Stripe'
            else:
                messages.warning(request, 'Payment completed but metadata was missing. Please contact support.')
                # Store basic info from session (get amount from checkout session)
                amount_from_session = getattr(checkout_session, 'amount_total', 0) / 100 if hasattr(checkout_session, 'amount_total') else 0
                request.session['payment_reference'] = f"STRIPE-{session_id}"
                request.session['payment_amount'] = amount_from_session
                request.session['payment_method'] = 'Stripe'
        else:
            messages.warning(request, 'Payment session found but payment status is not paid.')
        
        # Redirect to unified success page
        return redirect('finance:unified_success')
        
    except stripe._error.StripeError as e:
        logger.error(f"Stripe error retrieving checkout session: {str(e)}")
        print(f"[Stripe][DEBUG] Error retrieving session: {e}")
        messages.error(request, 'Error verifying payment. Please contact support if payment was charged.')
        return redirect('finance:payment_method_selection')
    except Exception as e:
        logger.error(f"Unexpected error in stripe_checkout_success: {str(e)}")
        print(f"[Stripe][DEBUG] Unexpected error: {e}")
        messages.error(request, 'An unexpected error occurred. Please contact support.')
        return redirect('finance:payment_method_selection')


@login_required
def stripe_checkout_cancel(request):
    """
    Handle cancelled Stripe Checkout payment
    """
    from django.contrib import messages
    from django.shortcuts import redirect
    
    messages.info(request, 'Payment was cancelled. You can try again when ready.')
    print(f"[Stripe][DEBUG] Checkout cancelled by user={request.user.id}")
    return redirect('finance:payment_method_selection')


@csrf_exempt
@require_http_methods(["POST"])
def stripe_webhook(request):
    """
    Handle Stripe webhooks for payment confirmation (Checkout Sessions)
    """
    if not stripe_available:
        print("[Stripe][DEBUG] Webhook received but stripe not available")
        from django.http import HttpResponse
        return HttpResponse(status=503)
    
    import os
    from django.http import HttpResponse
    
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        logger.error("Invalid payload")
        print("[Stripe][DEBUG] Webhook invalid payload")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid signature")
        print("[Stripe][DEBUG] Webhook signature verification failed")
        return HttpResponse(status=400)
    
    # Handle the event
    print(f"[Stripe][DEBUG] Webhook event type={event['type']}")
    
    # Handle Checkout Session completed (preferred for Checkout)
    if event['type'] == 'checkout.session.completed':
        checkout_session = event['data']['object']
        logger.info(f"Checkout session completed: {checkout_session['id']}")
        print(f"[Stripe][DEBUG] Checkout session completed webhook for session={checkout_session['id']}")
        
        # Extract metadata
        metadata = checkout_session.get('metadata', {})
        user_id = metadata.get('user_id')
        payment_info_id = metadata.get('payment_info_id')
        amount = float(metadata.get('amount', checkout_session.get('amount_total', 0) / 100))
        reference = metadata.get('reference', f"STRIPE-CHECKOUT-{checkout_session['id']}")
        
        if user_id and payment_info_id and reference:
            try:
                # Get payment info
                payment_info = Payment_Information.objects.only('id', 'customer', 'payment_fees', 'down_payment', 'plan').get(id=payment_info_id)
                
                # Save payment history
                user = CustomerUser.objects.get(id=int(user_id))
                ok = save_payment_history(
                    user=user,
                    payment_info=payment_info,
                    method='Stripe',
                    reference=reference,
                    amount=amount,
                    status='completed'
                )
                
                if ok:
                    logger.info(f"Payment history saved for Stripe Checkout {checkout_session['id']}")
                    print(f"[Stripe][DEBUG] Payment history saved for session={checkout_session['id']}")
                else:
                    logger.error(f"Failed to save payment history for Stripe Checkout {checkout_session['id']}")
                    print(f"[Stripe][DEBUG] Failed to save payment history for session={checkout_session['id']}")
                    
            except Exception as e:
                logger.error(f"Error processing Stripe webhook: {str(e)}")
                print(f"[Stripe][DEBUG] Exception while handling webhook: {e}")
    
    # Also handle payment_intent.succeeded for backwards compatibility
    elif event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        logger.info(f"Payment succeeded: {payment_intent['id']}")
        print(f"[Stripe][DEBUG] Payment succeeded webhook for intent={payment_intent['id']}")
        
        # Extract metadata
        metadata = payment_intent.get('metadata', {})
        user_id = metadata.get('user_id')
        payment_info_id = metadata.get('payment_info_id')
        reference = metadata.get('reference')
        amount = payment_intent['amount'] / 100  # Convert from cents
        
        if user_id and payment_info_id and reference:
            try:
                # Get payment info
                payment_info = Payment_Information.objects.only('id', 'customer', 'payment_fees', 'down_payment', 'plan').get(id=payment_info_id)
                
                # Save payment history
                user = CustomerUser.objects.get(id=int(user_id))
                ok = save_payment_history(
                    user=user,
                    payment_info=payment_info,
                    method='Stripe',
                    reference=reference,
                    amount=amount,
                    status='completed'
                )
                
                if ok:
                    logger.info(f"Payment history saved for Stripe payment {payment_intent['id']}")
                    print(f"[Stripe][DEBUG] Payment history saved for intent={payment_intent['id']}")
                else:
                    logger.error(f"Failed to save payment history for Stripe payment {payment_intent['id']}")
                    print(f"[Stripe][DEBUG] Failed to save payment history for intent={payment_intent['id']}")
                    
            except Exception as e:
                logger.error(f"Error processing Stripe webhook: {str(e)}")
                print(f"[Stripe][DEBUG] Exception while handling webhook: {e}")
    
    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        logger.warning(f"Payment failed: {payment_intent['id']}")
        print(f"[Stripe][DEBUG] Payment failed webhook for intent={payment_intent['id']}")
        
    else:
        logger.info(f"Unhandled event type: {event['type']}")
        print(f"[Stripe][DEBUG] Unhandled webhook type {event['type']}")
    
    return HttpResponse(status=200)
