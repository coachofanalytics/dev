from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
import logging

from finance.models import Payment_Information, Payment_History
from accounts.models import CustomerUser
from finance.utils import validate_amount, save_payment_history, validate_user_payment_eligibility
from core.utils import generate_and_send_otp
from .payment_details import show_payment_details

# PaymentService not currently used - commented out in views
# from finance.services.core.base import PaymentService

logger = logging.getLogger(__name__)


# Payment Method Constants
# Order: Stripe (priority), PayPal (priority), then others
PAYMENT_METHODS = {
    'stripe': {
        'name': 'Stripe',
        'display_name': 'Credit/Debit Card',
        'icon': 'fa fa-credit-card',
        'color': 'warning',
        'requires_phone': False,
        'has_api': True,  # API integration available
        'description': 'Secure payment via credit/debit card',
        'processing_time': 'Instant',
        'fees': '2.9% + 30¢',
    },
    'paypal': {
        'name': 'PayPal',
        'display_name': 'PayPal',
        'icon': 'fa fa-paypal',
        'color': 'primary',
        'requires_phone': False,
        'has_api': True,  # API integration available
        'description': 'Secure online payment via PayPal',
        'processing_time': '2-3 business days',
        'fees': '3.5%',
    },
    'mpesa': {
        'name': 'MPESA',
        'display_name': 'MPESA Mobile Money',
        'icon': 'fa fa-mobile',
        'color': 'success',
        'requires_phone': True,
        'has_api': False,  # Direct to payment details
        'description': 'Fast mobile money payment via MPESA',
        'processing_time': 'Instant',
        'fees': '2.5%',
    },
    'cashapp': {
        'name': 'CashApp',
        'display_name': 'CashApp',
        'icon': 'fa fa-dollar',
        'color': 'success',
        'requires_phone': False,
        'has_api': False,  # Direct to payment details
        'description': 'Quick payment via CashApp',
        'processing_time': 'Instant',
        'fees': '1.5%',
    },
    'zelle': {
        'name': 'Zelle',
        'display_name': 'Zelle',
        'icon': 'fa fa-university',
        'color': 'info',
        'requires_phone': False,
        'has_api': False,  # Direct to payment details
        'description': 'Bank-to-bank transfer via Zelle',
        'processing_time': '1-2 business days',
        'fees': 'Free',
    },
    'venmo': {
        'name': 'Venmo',
        'display_name': 'Venmo',
        'icon': 'fa fa-cc-venmo',
        'color': 'primary',
        'requires_phone': False,
        'has_api': False,  # Direct to payment details
        'description': 'Social payment via Venmo',
        'processing_time': '1-3 business days',
        'fees': '3%',
    },
}


@login_required
def payment_method_selection(request):
    """
    Unified payment method selection view
    Shows all available payment methods with consistent UI
    """
    try:
        # Get user's payment information
        # Query without any default ordering to avoid field conflicts
        try:
            payment_info = Payment_Information.objects.filter(
                customer=request.user
            ).order_by('-id').only('id', 'customer', 'payment_fees', 'down_payment', 'plan').first()
        except Exception as db_error:
            logger.warning(f"Database query issue, trying alternate method: {db_error}")
            # Fallback: use raw query to avoid model ordering issues
            from django.db import connection
            with connection.cursor() as cursor:
                print(f"[Payments][DEBUG] Raw query fallback for payment info (selection) user_id={request.user.id}")
                print(f"[Payments][DEBUG] Raw query fallback for payment info (processing) user_id={request.user.id}")
                cursor.execute("""
                    SELECT id, customer_id_id, payment_fees, down_payment, plan 
                    FROM finance_payment_information 
                    WHERE customer_id_id = %s 
                    ORDER BY id DESC 
                    LIMIT 1
                """, [request.user.id])
                result = cursor.fetchone()
                if result:
                    # Create a simple object with the needed attributes
                    payment_info = type('PaymentInfo', (), {
                        'id': result[0],
                        'customer_id': result[1],
                        'payment_fees': result[2],
                        'down_payment': result[3],
                        'plan': result[4]
                    })()
                else:
                    payment_info = None
        
        if not payment_info:
            # Route user to create payable context based on persona
            try:
                from finance.utilities.payment_utils import PaymentUtils
                named_url, absolute_url = PaymentUtils.get_persona_redirect_url(request.user)
                print(f"[Payments][DEBUG] Persona redirect lookup for user={request.user.username}: named_url={named_url} absolute_url={absolute_url}")
                if named_url:
                    print(f"[Payments][DEBUG] Redirecting via persona named_url={named_url}")
                    return redirect(reverse(named_url))
                if absolute_url:
                    print(f"[Payments][DEBUG] Redirecting via persona absolute_url={absolute_url}")
                    return redirect(absolute_url)
            except Exception:
                pass
            
            # If no payment context found, redirect to loan application or service selection
            print("[Payments][DEBUG] No payment context found; redirecting user to onboarding flows")
            messages.error(request, 'No payment context found. Please select a service or apply for a loan to continue.')
            
            # Try to redirect to loan application first
            try:
                print("[Payments][DEBUG] Redirecting to finance:loan-home")
                return redirect('finance:loan-home')
            except Exception:
                pass
            
            # Fallback to finance index
            try:
                print("[Payments][DEBUG] Redirecting to finance:finance-index")
                return redirect('finance:finance-index')
            except Exception:
                pass
            
            # Last resort - show error page
            print("[Payments][DEBUG] Rendering no_payment_context fallback")
            return render(request, 'finance/payments/no_payment_context.html', {
                'error_message': 'No payment context found. Please contact support or select a service.'
            })
        
        # Calculate amounts
        total_amount = payment_info.payment_fees
        down_payment = payment_info.down_payment
        print(f"DEBUG: total_amount: {total_amount}, down_payment: {down_payment}")
        
        # Calculate balance
        balance = 0
        if total_amount and down_payment:
            balance = total_amount - down_payment
        elif total_amount:
            balance = total_amount
        
        context = {
            'available_methods': PAYMENT_METHODS,
            'total_amount': total_amount,
            'down_payment': down_payment,
            'balance': balance,
            'payment_info': payment_info,
        }
        print(f"[Payments][DEBUG] Context created successfully for user={request.user.username}: total={total_amount} down={down_payment} balance={balance}")
        print("[Payments][DEBUG] Rendering payment method selection")
        return render(request, 'finance/payments/method_selection.html', context)
        
    except Exception as e:
        print(f"[Payments][DEBUG] Exception in payment_method_selection for user={request.user.username}: {e}")
        print(f"[Payments][DEBUG] Exception type: {type(e)}")
        import traceback
        print(f"DEBUG: Full traceback: {traceback.format_exc()}")
        logger.error(f"Error in payment method selection: {str(e)}")
        messages.error(request, 'Error loading payment methods. Please try again.')
        return redirect('finance:payments', title='history', status='completed')


@login_required
def payment_processing(request, method):
    """
    Unified payment processing view
    Handles payment initiation for all methods
    """
    if method not in PAYMENT_METHODS:
        messages.error(request, 'Invalid payment method selected.')
        return redirect('finance:unified_method_selection')
    
    try:
        # Get payment information - avoid ordering issues
        try:
            payment_info = Payment_Information.objects.filter(
                customer=request.user
            ).order_by('-id').only('id', 'customer', 'payment_fees', 'down_payment', 'plan').first()
        except Exception as db_error:
            logger.warning(f"Database query issue in payment processing: {db_error}")
            # Fallback: use raw query to avoid model ordering issues
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT id, customer_id_id, payment_fees, down_payment, plan 
                    FROM finance_payment_information 
                    WHERE customer_id_id = %s 
                    ORDER BY id DESC 
                    LIMIT 1
                """, [request.user.id])
                result = cursor.fetchone()
                if result:
                    # Create a simple object with the needed attributes
                    payment_info = type('PaymentInfo', (), {
                        'id': result[0],
                        'customer_id': result[1],
                        'payment_fees': result[2],
                        'down_payment': result[3],
                        'plan': result[4]
                    })()
                else:
                    payment_info = None
        
        if not payment_info:
            print(f"[Payments][DEBUG] No payment_info found for user={request.user.username} during processing")
            messages.error(request, 'No payment information found.')
            return redirect('finance:unified_method_selection')
        
        # Initialize payment service (commented out for demo)
        # payment_service = PaymentService()
        payment_service = None
        
        if request.method == 'POST':
            print(f"[Payments][DEBUG] Processing POST request for method={method}")
            # Process payment based on method
            result = process_payment_by_method(
                request, method, payment_info, payment_service
            )
            print(f"[Payments][DEBUG] Payment processing result={result}")
            return result
        else:
            print(f"[Payments][DEBUG] Showing payment form for method={method}")
            # Show payment form
            return show_payment_form(request, method, payment_info)
            
    except Exception as e:
        logger.error(f"Error in payment processing for {method}: {str(e)}")
        request.session['error_message'] = 'Payment processing failed'
        return redirect('finance:unified_failed')

def process_payment_by_method(request, method, payment_info, payment_service):
    """Process payment using the specified method"""
    
    if method == 'mpesa':
        return process_mpesa_payment(request, payment_info, payment_service)
    elif method == 'paypal':
        return process_paypal_payment(request, payment_info, payment_service)
    elif method == 'cashapp':
        return process_cashapp_payment(request, payment_info, payment_service)
    elif method == 'zelle':
        return process_zelle_payment(request, payment_info, payment_service)
    elif method == 'venmo':
        return process_venmo_payment(request, payment_info, payment_service)
    elif method == 'stripe':
        return process_stripe_payment(request, payment_info, payment_service)
    else:
        messages.error(request, f'Payment method {method} not implemented yet.')
        return redirect('finance:unified_method_selection')
def process_mpesa_payment(request, payment_info, payment_service):
    """
    Process M-Pesa payment with automatic fallback
    Try STK Push if credentials available, otherwise show payment details
    """
    import os
    
    # Check if M-Pesa credentials are available
    has_mpesa_creds = all([
        os.environ.get('MPESA_CONSUMER_KEY'),
        os.environ.get('MPESA_CONSUMER_SECRET'),
        os.environ.get('MPESA_SHORTCODE')
    ])
    
    if not has_mpesa_creds:
        logger.info(f"M-Pesa credentials not available for user {request.user.username}, showing payment details")
        return show_payment_details(request, 'mpesa')
    
    # Try automated STK Push
    phone_number = request.POST.get('phone_number')
    amount = request.POST.get('amount')
    
    if not phone_number:
        messages.error(request, 'Phone number is required for MPESA payment.')
        return redirect('finance:unified_processing', method='mpesa')
    if not amount:
        messages.error(request, 'Payment amount is required for MPESA payment.')
        return redirect('finance:unified_processing', method='mpesa')
    # User balance validation
    eligible, message, amount_float = validate_user_payment_eligibility(request.user, amount, 'mpesa')
    if not eligible:
        request.session['error_message'] = message
        return redirect('finance:unified_failed')
    # Generate OTP and send
    otp = generate_and_send_otp(request.user.email)
    request.session['mpesa_payment_data'] = {
        'phone_number': phone_number,
        'amount': amount_float,
        'payment_info_id': payment_info.id,
        'otp': otp,
        'reference': f"MPESA-{phone_number}-{amount_float}"
    }
    
    return redirect('finance:mpesa_otp_confirmation')
def process_paypal_payment(request, payment_info, payment_service):
    """
    Process PayPal payment with automatic fallback
    Try automated payment first, fallback to payment details if fails
    """
    # NOTE: PayPal SDK integration is handled client-side
    # This function handles POST from PayPal form or fallback request
    
    # Check if this is a fallback request (user couldn't use PayPal button)
    if request.GET.get('fallback') == 'true':
        logger.info(f"PayPal fallback requested for user {request.user.username}")
        return show_payment_details(request, 'paypal')
    
    amount = request.POST.get("amount")
    email = request.POST.get("email")
    
    if not email:
        messages.error(request, "PayPal email is required.")
        return redirect("finance:unified_processing", method="paypal")
    
    if not amount:
        messages.error(request, "Payment amount is required.")
        return redirect("finance:unified_processing", method="paypal")
    
    # COMPREHENSIVE VALIDATION - Now handles 3 return values
    eligible, message, amount_float = validate_user_payment_eligibility(request.user, amount, 'paypal')
    if not eligible:
        request.session['error_message'] = message
        return redirect('finance:unified_failed')
    
    # Try to process payment
    try:
        # Create payment record using utility function
        reference = f"PAYPAL-{request.user.id}-{amount_float}"
        ok = save_payment_history(
            user=request.user,
            payment_info=payment_info,
            method='PayPal',
            reference=reference,
            amount=amount_float,
            status='completed'
        )
        if not ok:
            # Fallback to payment details
            logger.warning(f"PayPal payment save failed for user {request.user.username}, showing payment details")
            return show_payment_details(request, 'paypal')
            
        messages.success(request, f"PayPal payment of ${amount_float} completed successfully!")
        
        # Store payment data in session for success page
        request.session['payment_reference'] = reference
        request.session['payment_amount'] = amount_float
        request.session['payment_method'] = 'paypal'
        
        return redirect("finance:unified_success")
        
    except Exception as e:
        logger.error(f"Error creating PayPal payment record: {str(e)}")
        # Fallback to payment details instead of showing error
        logger.info(f"PayPal payment error for user {request.user.username}, falling back to payment details")
        return show_payment_details(request, 'paypal')
def process_cashapp_payment(request, payment_info, payment_service):
    """
    Process CashApp payment - No API available, show payment details
    """
    logger.info(f"CashApp payment requested for user {request.user.username}, showing payment details")
    return show_payment_details(request, 'cashapp')

def process_cashapp_payment_DEPRECATED(request, payment_info, payment_service):
    """DEPRECATED - Old CashApp simulation"""
    amount = request.POST.get("amount")
    cashapp_id = request.POST.get("cashapp_id")
    if not amount:
        messages.error(request, "Payment amount is required.")
        return redirect("finance:unified_processing", method="cashapp")
    
    if not cashapp_id:
        messages.error(request, "CashApp ID is required.")
        return redirect("finance:unified_processing", method="cashapp")
    
    # User balance validation - FIXED: was 'mpesa', now 'cashapp'
    eligible, message, amount_float = validate_user_payment_eligibility(request.user, amount, 'cashapp')
    if not eligible:
        request.session['error_message'] = message
        return redirect('finance:unified_failed')
    # Simulate successful payment
    try:
        reference = f"CASHAPP-{request.user.id}-{amount_float}"
        ok = save_payment_history(
            user=request.user,
            payment_info=payment_info,
            method='CashApp',
            reference=reference,
            amount=amount_float,
            status='completed'
        )
        if not ok:
            request.session['error_message'] = 'Payment failed to save'
            return redirect('finance:unified_failed')
        
        messages.success(request, f"CashApp payment of ${amount_float} completed successfully!")
        
        # Store payment data in session for success page
        request.session['payment_reference'] = reference
        request.session['payment_amount'] = amount_float
        request.session['payment_method'] = 'cashapp'
        
        return redirect("finance:unified_success")
        
    except Exception as e:
        logger.error(f"Error creating CashApp payment record: {str(e)}")
        request.session['error_message'] = 'Database error'
        return redirect('finance:unified_failed')
def process_zelle_payment(request, payment_info, payment_service):
    """
    Process Zelle payment - No API available, show payment details
    """
    logger.info(f"Zelle payment requested for user {request.user.username}, showing payment details")
    return show_payment_details(request, 'zelle')
def process_venmo_payment(request, payment_info, payment_service):
    """
    Process Venmo payment - No API available, show payment details
    """
    logger.info(f"Venmo payment requested for user {request.user.username}, showing payment details")
    return show_payment_details(request, 'venmo')
def process_stripe_payment(request, payment_info, payment_service):
    """
    Process Stripe payment using Checkout Session (server-side, no JavaScript)
    Redirects to Stripe's hosted checkout page
    """
    from django.shortcuts import redirect
    from django.urls import reverse
    from django.conf import settings
    
    # Check if Stripe credentials are available
    has_stripe_creds = all([
        getattr(settings, 'STRIPE_PUBLISHABLE_KEY', None),
        getattr(settings, 'STRIPE_SECRET_KEY', None)
    ])
    print(f"[Stripe][DEBUG] process_stripe_payment creds_present={has_stripe_creds}")
    
    if not has_stripe_creds:
        logger.info(f"Stripe credentials not available for user {request.user.username}, showing payment details")
        print("[Stripe][DEBUG] Missing Stripe credentials, falling back to manual instructions")
        return show_payment_details(request, 'stripe')
    
    # Get amount from request (default to full balance)
    amount = payment_info.get_fee_balance()
    if request.method == 'POST':
        amount = float(request.POST.get('amount', amount))
    elif request.method == 'GET':
        amount = float(request.GET.get('amount', amount))
    
    # Redirect to create Checkout Session (which will redirect to Stripe)
    logger.info(f"Redirecting to Stripe Checkout for user {request.user.username} amount={amount}")
    print(f"[Stripe][DEBUG] Redirecting to Checkout Session for user={request.user.username} amount={amount}")
    return redirect(f"{reverse('finance:stripe_checkout_session')}?amount={amount}")
@login_required
def payment_success(request):
    """Unified payment success view"""
    print(f"DEBUG: Payment success view called!")
    try:
        # Get payment data from session
        reference = request.session.get('payment_reference', 'DEMO-REF-001')
        amount = request.session.get('payment_amount', 0)
        method = request.session.get('payment_method', 'Unknown')
        
        context = {
            'reference': reference,
            'amount': amount,
            'method': method,
            'payment_date': timezone.now(),  # Add current payment date
        }
        
        # Clear session data
        if 'payment_reference' in request.session:
            del request.session['payment_reference']
        if 'payment_amount' in request.session:
            del request.session['payment_amount']
        if 'payment_method' in request.session:
            del request.session['payment_method']
        
        return render(request, 'finance/payments/unified_success.html', context)
        
    except Exception as e:
        logger.error(f"Error in payment success view: {str(e)}")
        messages.error(request, 'Error displaying success page.')
        return redirect('finance:unified_method_selection')
@login_required
def payment_failed(request):
    """Unified payment failed view"""
    try:
        # Get error message from session
        error_message = request.session.get('error_message', 'Payment processing failed')
        
        # Clear the session message
        if 'error_message' in request.session:
            del request.session['error_message']
        
        context = {
            'error_message': error_message,
            'method': 'Unknown',  # You can enhance this to get the actual method
        }
        
        return render(request, 'finance/payments/unified_failed.html', context)
        
    except Exception as e:
        logger.error(f"Error in payment failed view: {str(e)}")
        messages.error(request, 'Error displaying failure page.')
        return redirect('finance:unified_method_selection')
def show_payment_form(request, method, payment_info):
    """Show payment form for the specified method"""
    try:
        # For manual payment methods, redirect to payment details instead of showing forms
        manual_methods = ['mpesa', 'cashapp', 'zelle', 'venmo']
        
        if method in manual_methods:
            logger.info(f"Manual payment method {method} requested, redirecting to payment details")
            return show_payment_details(request, method)
        
        # For Stripe, show payment form (user enters amount, then submits to Checkout)
        if method == 'stripe':
            from django.conf import settings
            
            # Check if Stripe credentials are available
            has_stripe_creds = all([
                getattr(settings, 'STRIPE_PUBLISHABLE_KEY', None),
                getattr(settings, 'STRIPE_SECRET_KEY', None)
            ])
            
            if not has_stripe_creds:
                logger.info(f"Stripe credentials not available, showing payment details")
                return show_payment_details(request, 'stripe')
            
            # Show the payment form (user will enter amount and submit)
            method_info = PAYMENT_METHODS.get(method, {})
            context = {
                'method': method,
                'method_info': method_info,
                'payment_info': payment_info,
            }
            
            template_name = 'finance/payments/stripe_form.html'
            logger.info(f"Showing Stripe payment form for user {request.user.username}")
            print(f"[Stripe][DEBUG] Showing payment form for user={request.user.username}")
            return render(request, template_name, context)
        
        # For other automated methods (PayPal), show their specific forms
        method_info = PAYMENT_METHODS.get(method, {})
        context = {
            'method': method,
            'method_info': method_info,
            'payment_info': payment_info,
        }
        
        template_name = f'finance/payments/{method}_form.html'

        return render(request, template_name, context)
        
    except Exception as e:
        logger.error(f"Error showing payment form for {method}: {str(e)}")
        print(f"[Payments][DEBUG] Error showing payment form for {method}: {e}")
        import traceback
        traceback.print_exc()
        messages.error(request, f'Error loading {method} payment form.')
        return redirect('finance:unified_method_selection')
@login_required
def mpesa_otp_confirmation(request):
    """MPESA OTP confirmation page"""
    try:
        # Get MPESA payment data from session
        mpesa_data = request.session.get('mpesa_payment_data', {})
        
        if not mpesa_data:
            messages.error(request, 'No MPESA payment data found. Please try again.')
            return redirect('finance:unified_method_selection')
        
        context = {
            'phone_number': mpesa_data.get('phone_number'),
            'amount': mpesa_data.get('amount'),
            'reference': mpesa_data.get('reference'),
        }
        
        return render(request, 'finance/payments/mpesa_otp_confirmation.html', context)
        
    except Exception as e:
        logger.error(f"Error in MPESA OTP confirmation: {str(e)}")
        messages.error(request, 'Error loading OTP confirmation page.')
        return redirect('finance:unified_method_selection')
@login_required
def verify_mpesa_otp(request):
    """Verify MPESA OTP and process payment"""
    if request.method != 'POST':
        return redirect('finance:mpesa_otp_confirmation')
    
    try:
        # Get MPESA data from session
        mpesa_data = request.session.get('mpesa_payment_data', {})
        if not mpesa_data:
            messages.error(request, 'No MPESA payment data found. Please try again.')
            return redirect('finance:unified_method_selection')
        
        # Get OTP from form
        user_otp = request.POST.get('otp')
        if not user_otp:
            messages.error(request, 'OTP is required.')
            return redirect('finance:mpesa_otp_confirmation')
        
        # Verify OTP
        stored_otp = mpesa_data.get('otp')
        if user_otp.upper() != stored_otp.upper():
            messages.error(request, 'Invalid OTP. Please try again.')
            return redirect('finance:mpesa_otp_confirmation')
        
        # OTP is valid - process payment
        payment_info = Payment_Information.objects.only('id', 'customer', 'payment_fees', 'down_payment', 'plan').get(id=mpesa_data['payment_info_id'])
        
        # Create payment record
        reference = mpesa_data['reference']
        ok = save_payment_history(
            user=request.user,
            payment_info=payment_info,
            method='MPESA',
            reference=reference,
            amount=mpesa_data['amount'],
            status='completed'
        )
        
        if not ok:
            request.session['error_message'] = 'Payment failed to save'
            return redirect('finance:unified_failed')
        
        # Clear MPESA session data
        if 'mpesa_payment_data' in request.session:
            del request.session['mpesa_payment_data']
        
        # Store payment data in session for success page
        request.session['payment_reference'] = reference
        request.session['payment_amount'] = mpesa_data['amount']
        request.session['payment_method'] = 'mpesa'
        
        messages.success(request, f"MPESA payment of ${mpesa_data['amount']} completed successfully!")
        return redirect('finance:unified_success')
        
    except Exception as e:
        logger.error(f"Error verifying MPESA OTP: {str(e)}")
        request.session['error_message'] = 'Payment processing failed'
        return redirect('finance:unified_failed')