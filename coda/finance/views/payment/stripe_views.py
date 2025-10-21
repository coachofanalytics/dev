import json
import logging
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.conf import settings
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
@require_http_methods(["POST"])
def create_payment_intent(request):
    """
    Create a Stripe PaymentIntent for the payment
    """
    if not stripe_available:
        return JsonResponse({'error': 'Stripe is not available'}, status=503)
    
    try:
        data = json.loads(request.body)
        payment_method_id = data.get('payment_method_id')
        amount = float(data.get('amount', 0))
        
        if not payment_method_id:
            return JsonResponse({'error': 'Payment method ID is required'}, status=400)
        
        if amount <= 0:
            return JsonResponse({'error': 'Invalid amount'}, status=400)
        
        # Get user's payment information
        try:
            payment_info = Payment_Information.objects.filter(
                customer_id=request.user.id
            ).only('id', 'customer_id', 'payment_fees', 'down_payment', 'plan', 'created_at').order_by('-id').first()
        except Exception as db_error:
            logger.warning(f"Database query issue: {db_error}")
            return JsonResponse({'error': 'Payment information not found'}, status=400)
        
        if not payment_info:
            return JsonResponse({'error': 'No payment information found'}, status=400)
        
        # Create PaymentIntent (without payment_method first)
        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # Convert to cents
            currency='usd',
            confirmation_method='manual',
            return_url=request.build_absolute_uri('/finance/unified/success/'),
            metadata={
                'user_id': str(request.user.id),
                'payment_info_id': str(payment_info.id),
                'reference': f"STRIPE-{request.user.id}-{amount}"
            }
        )
        
        return JsonResponse({
            'client_secret': intent.client_secret,
            'status': intent.status
        })
        
    except stripe._error.CardError as e:
        logger.error(f"Stripe card error: {str(e)}")
        return JsonResponse({'error': str(e.user_message)}, status=400)
        
    except stripe._error.RateLimitError as e:
        logger.error(f"Stripe rate limit error: {str(e)}")
        return JsonResponse({'error': 'Too many requests. Please try again later.'}, status=429)
        
    except stripe._error.InvalidRequestError as e:
        logger.error(f"Stripe invalid request error: {str(e)}")
        return JsonResponse({'error': 'Invalid request. Please check your payment details.'}, status=400)
        
    except stripe._error.AuthenticationError as e:
        logger.error(f"Stripe authentication error: {str(e)}")
        return JsonResponse({'error': 'Payment service authentication failed.'}, status=500)
        
    except stripe._error.APIConnectionError as e:
        logger.error(f"Stripe API connection error: {str(e)}")
        return JsonResponse({'error': 'Payment service temporarily unavailable.'}, status=503)
        
    except stripe._error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        return JsonResponse({'error': 'Payment processing failed. Please try again.'}, status=500)
        
    except Exception as e:
        logger.error(f"Unexpected error in create_payment_intent: {str(e)}")
        return JsonResponse({'error': 'An unexpected error occurred. Please try again.'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def stripe_webhook(request):
    """
    Handle Stripe webhooks for payment confirmation
    """
    if not stripe_available:
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
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid signature")
        return HttpResponse(status=400)
    
    # Handle the event
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        logger.info(f"Payment succeeded: {payment_intent['id']}")
        
        # Extract metadata
        metadata = payment_intent.get('metadata', {})
        user_id = metadata.get('user_id')
        payment_info_id = metadata.get('payment_info_id')
        reference = metadata.get('reference')
        amount = payment_intent['amount'] / 100  # Convert from cents
        
        if user_id and payment_info_id and reference:
            try:
                # Get payment info
                payment_info = Payment_Information.objects.only('id', 'customer_id', 'payment_fees', 'down_payment', 'plan', 'created_at').get(id=payment_info_id)
                
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
                else:
                    logger.error(f"Failed to save payment history for Stripe payment {payment_intent['id']}")
                    
            except Exception as e:
                logger.error(f"Error processing Stripe webhook: {str(e)}")
    
    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        logger.warning(f"Payment failed: {payment_intent['id']}")
        
        # You could save failed payment attempts here if needed
        
    else:
        logger.info(f"Unhandled event type: {event['type']}")
    
    return HttpResponse(status=200)
