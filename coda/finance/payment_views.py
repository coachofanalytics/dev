from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
import logging
from finance.models import Payment_Information, Payment_History
from finance.services import PaymentProcessingService
from accounts.models import CustomerUser
from finance.utils import validate_amount, save_payment_history, validate_user_payment_eligibility
# In finance/payment_views.py:
from core.utils import generate_and_send_otp
logger = logging.getLogger(__name__)


    # Payment Method Constants
PAYMENT_METHODS = {
    'mpesa': {
        'name': 'MPESA',
        'display_name': 'MPESA Mobile Money',
        'icon': 'fa fa-mobile',
        'color': 'success',
        'requires_phone': True,
        'description': 'Fast mobile money payment via MPESA',
        'processing_time': 'Instant',
        'fees': '2.5%',
    },
    'paypal': {
        'name': 'PayPal',
        'display_name': 'PayPal',
        'icon': 'fa fa-paypal',
        'color': 'primary',
        'requires_phone': False,
        'description': 'Secure online payment via PayPal',
        'processing_time': '2-3 business days',
        'fees': '3.5%',
    },
    'cashapp': {
        'name': 'CashApp',
        'display_name': 'CashApp',
        'icon': 'fa fa-dollar',
        'color': 'success',
        'requires_phone': False,
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
        'description': 'Social payment via Venmo',
        'processing_time': '1-3 business days',
        'fees': '3%',
    },
    'stripe': {
        'name': 'Stripe',
        'display_name': 'Credit/Debit Card',
        'icon': 'fa fa-credit-card',
        'color': 'warning',
        'requires_phone': False,
        'description': 'Secure payment via credit/debit card',
        'processing_time': 'Instant',
        'fees': '2.9% + 30¢',
    },
}


@login_required
def payment_method_selection(request):
    """
    Unified payment method selection view
    Shows all available payment methods with consistent UI
    """
    try:
        print(f"DEBUG: Starting payment_method_selection for user {request.user.id}")
        
        # Get user's payment information
        payment_info = Payment_Information.objects.filter(customer_id=request.user.id).first()
        print(f"DEBUG: payment_info found: {payment_info}")
        
        if not payment_info:
            print("DEBUG: No payment_info found, redirecting")
            messages.error(request, 'No payment information found. Please contact support.')
            return redirect('finance:payments', title='history', status='completed')
        
        # Calculate amounts
        total_amount = payment_info.payment_fees
        down_payment = payment_info.down_payment
        balance = payment_info.fee_balance  # This will now use the updated calculation
        print(f"DEBUG: total_amount: {total_amount}, down_payment: {down_payment}, balance: {balance}")
        
        context = {
            'available_methods': PAYMENT_METHODS,
            'total_amount': total_amount,
            'down_payment': down_payment,
            'balance': balance,
            'payment_info': payment_info,
        }
        print(f"DEBUG: Context created successfully: {context}")
        
        print("DEBUG: About to render template")
        return render(request, 'finance/payments/method_selection.html', context)
        
    except Exception as e:
        print(f"DEBUG: Exception occurred: {str(e)}")
        print(f"DEBUG: Exception type: {type(e)}")
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
        # Get payment information
        payment_info = Payment_Information.objects.filter(customer_id=request.user.id).first()
        
        if not payment_info:
            messages.error(request, 'No payment information found.')
            return redirect('finance:unified_method_selection')
        
        # Initialize payment service (commented out for demo)
        # payment_service = PaymentService()
        payment_service = None
        
        if request.method == 'POST':
            print(f"DEBUG: Processing POST request for {method}")
            # Process payment based on method
            result = process_payment_by_method(
                request, method, payment_info, payment_service
            )
            print(f"DEBUG: Payment processing result: {result}")
            return result
        else:
            print(f"DEBUG: Showing payment form for {method}")
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
    """Process MPESA payment"""
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
    """Process PayPal payment"""
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
    # Simulate successful payment
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
            request.session['error_message'] = 'Payment failed to save'
            return redirect('finance:unified_failed')
        messages.success(request, f"PayPal payment of ${amount_float} completed successfully!")
        
        # Store payment data in session for success page
        request.session['payment_reference'] = reference
        request.session['payment_amount'] = amount_float
        request.session['payment_method'] = 'paypal'  # Use lowercase for consistency
        
        return redirect("finance:unified_success")
        
    except Exception as e:
        logger.error(f"Error creating PayPal payment record: {str(e)}")
        request.session['error_message'] = 'Payment processing failed'
        return redirect('finance:unified_failed')
def process_cashapp_payment(request, payment_info, payment_service):
    """Process CashApp payment"""
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
    """Process Zelle payment"""
    amount = request.POST.get("amount")
    email = request.POST.get("email")
    
    if not amount:
        messages.error(request, "Payment amount is required.")
        return redirect("finance:unified_processing", method="zelle")
    
    if not email:
        messages.error(request, "Zelle email is required.")
        return redirect("finance:unified_processing", method="zelle")
    
    # User balance validation - FIXED: was 'mpesa', now 'zelle'
    eligible, message, amount_float = validate_user_payment_eligibility(request.user, amount, 'zelle')
    if not eligible:
        request.session['error_message'] = message
        return redirect('finance:unified_failed')
    # Simulate successful payment
    try:
        reference = f"ZELLE-{request.user.id}-{amount_float}"
        ok = save_payment_history(
            user=request.user,
            payment_info=payment_info,
            method='Zelle',
            reference=reference,
            amount=amount_float,
            status='completed'
        )
        if not ok:
            request.session['error_message'] = 'Payment failed to save'
            return redirect('finance:unified_failed')
        
        messages.success(request, f"Zelle payment of ${amount_float} completed successfully!")
        
        # Store payment data in session for success page
        request.session['payment_reference'] = reference
        request.session['payment_amount'] = amount_float
        request.session['payment_method'] = 'zelle'
        
        return redirect("finance:unified_success")
        
    except Exception as e:
        logger.error(f"Error creating Zelle payment record: {str(e)}")
        request.session['error_message'] = 'Database error'
        return redirect('finance:unified_failed')
def process_venmo_payment(request, payment_info, payment_service):
    """Process Venmo payment"""
    amount = request.POST.get("amount")
    venmo_username = request.POST.get("venmo_username")
    
    if not amount:
        messages.error(request, "Payment amount is required.")
        return redirect("finance:unified_processing", method="venmo")
    
    if not venmo_username:
        messages.error(request, "Venmo username is required.")
        return redirect("finance:unified_processing", method="venmo")
    
    # User balance validation - FIXED: was 'mpesa', now 'venmo'
    eligible, message, amount_float = validate_user_payment_eligibility(request.user, amount, 'venmo')
    if not eligible:
        request.session['error_message'] = message
        return redirect('finance:unified_failed')
    
    # Simulate successful payment
    try:
        reference = f"VENMO-{request.user.id}-{amount_float}"
        ok = save_payment_history(
            user=request.user,
            payment_info=payment_info,
            method='Venmo',
            reference=reference,
            amount=amount_float,
            status='completed'
        )
        if not ok:
            request.session['error_message'] = 'Payment failed to save'
            return redirect('finance:unified_failed')
        
        messages.success(request, f"Venmo payment of ${amount_float} completed successfully!")
        
        # Store payment data in session for success page
        request.session['payment_reference'] = reference
        request.session['payment_amount'] = amount_float
        request.session['payment_method'] = 'venmo'
        
        return redirect("finance:unified_success")
        
    except Exception as e:
        logger.error(f"Error creating Venmo payment record: {str(e)}")
        request.session['error_message'] = 'Database error'
        return redirect('finance:unified_failed')
def process_stripe_payment(request, payment_info, payment_service):
    """Process Stripe payment"""
    amount = request.POST.get("amount")
    if not amount:
        messages.error(request, "Payment amount is required.")
        return redirect("finance:unified_processing", method="stripe")
    # User balance validation - FIXED: was 'mpesa', now 'stripe'
    eligible, message, amount_float = validate_user_payment_eligibility(request.user, amount, 'stripe')
    if not eligible:
        request.session['error_message'] = message
        return redirect('finance:unified_failed')
    # Simulate successful payment
    try:
        reference = f"STRIPE-{request.user.id}-{amount_float}"
        ok = save_payment_history(
            user=request.user,
            payment_info=payment_info,
            method='Stripe',
            reference=reference,
            amount=amount_float,
            status='completed'
        )
        if not ok:
            request.session['error_message'] = 'Payment failed to save'
            return redirect('finance:unified_failed')
        
        messages.success(request, f"Stripe payment of ${amount_float} completed successfully!")
        
        # Store payment data in session for success page
        request.session['payment_reference'] = reference
        request.session['payment_amount'] = amount_float
        request.session['payment_method'] = 'stripe'
        
        return redirect("finance:unified_success")
        
    except Exception as e:
        logger.error(f"Error creating Stripe payment record: {str(e)}")
        request.session['error_message'] = 'Database error'
        return redirect('finance:unified_failed')
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
        payment_info = Payment_Information.objects.get(id=mpesa_data['payment_info_id'])
        
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