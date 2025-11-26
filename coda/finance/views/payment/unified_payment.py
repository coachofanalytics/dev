from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
import logging

from finance.models import Payment_Information, Payment_History
from shared_core.users import CustomerUser
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
    Checks for loans FIRST, then service payments
    """
    try:
        from finance.models import LoanApplication
        
        payment_info = None
        payment_source = None  # Track if payment is for 'loan' or 'service'
        
        # PRIORITY 1: Check for active loans first (highest priority)
        active_loans = LoanApplication.objects.filter(
            borrower=request.user,
            status__in=['active', 'approved', 'disbursed']
        ).first()
        
        if active_loans:
            # User has active loan - create payment_info from loan
            logger.info(f"User {request.user.username} has active loan: {active_loans.id}")
            
            # IMPORTANT: Refresh the loan object from database to get latest payments
            # This ensures balance_amount property calculates with fresh payment data
            active_loans.refresh_from_db()
            
            # Clear related objects cache to force fresh query for loan_payments
            # This is critical because balance_amount depends on total_paid which sums loan_payments.all()
            if hasattr(active_loans, '_loan_payments_cache'):
                delattr(active_loans, '_loan_payments_cache')
            if hasattr(active_loans, '_prefetched_objects_cache'):
                active_loans._prefetched_objects_cache = {}
            
            # Use balance_amount (outstanding balance) if available, otherwise total_payable or amount_requested
            # balance_amount is a property that dynamically calculates: total_payable - total_paid
            current_balance = float(active_loans.balance_amount) if active_loans.balance_amount else 0.0
            if current_balance > 0:
                loan_amount = current_balance
            elif hasattr(active_loans, 'total_payable') and active_loans.total_payable:
                loan_amount = float(active_loans.total_payable)
            else:
                loan_amount = float(active_loans.amount_requested or 0)
            
            # Create payment_info-like object from loan
            # Add get_fee_balance() method that returns loan balance
            class LoanPaymentInfo:
                def __init__(self, loan, amount):
                    self.id = loan.id
                    self.customer = loan.borrower
                    self.payment_fees = amount
                    self.down_payment = 0  # Loans don't have down payments
                    self.plan = None
                    self.loan_application = loan
                    self._loan = loan
                
                def get_fee_balance(self):
                    """
                    Calculate outstanding loan balance using Loan model's balance_amount property
                    Validates property result and falls back to direct calculation if property is incorrect
                    """
                    # Refresh loan from DB to ensure we get latest payment records
                    self._loan.refresh_from_db()
                    
                    # Clear related objects cache to force fresh query for loan_payments
                    if hasattr(self._loan, '_loan_payments_cache'):
                        delattr(self._loan, '_loan_payments_cache')
                    if hasattr(self._loan, '_prefetched_objects_cache'):
                        self._loan._prefetched_objects_cache = {}
                    
                    # Calculate balance directly first to validate property result
                    from decimal import Decimal
                    total_paid = self._loan.total_paid
                    total_payable = self._loan.total_payable or Decimal('0.00')
                    calculated_balance = max(Decimal('0.00'), total_payable - total_paid)
                    calculated_float = float(calculated_balance)
                    
                    # PRIORITY 1: Try using the loan's balance_amount property (from Loan model)
                    # This is the proper way to get loan balance, but we validate it
                    try:
                        if hasattr(self._loan, 'balance_amount'):
                            balance_property = self._loan.balance_amount
                            if balance_property is not None:
                                balance_float = float(balance_property)
                                
                                # VALIDATION: Check if property value makes sense
                                # If property returns 0 but calculated balance > 0, property is wrong
                                # If property and calculated are close (within $0.01), use property
                                if balance_float >= 0:
                                    difference = abs(balance_float - calculated_float)
                                    if difference < 0.01:
                                        # Property matches calculated - use property (preferred)
                                        return balance_float
                                    elif balance_float == 0 and calculated_float > 0:
                                        # Property incorrectly returns 0 - use calculated
                                        logger.warning(f"balance_amount property returns $0.0 but calculated is ${calculated_float}, using calculated")
                                        return calculated_float
                                    else:
                                        # Property differs significantly - use calculated (more reliable)
                                        logger.warning(f"balance_amount property (${balance_float}) differs from calculated (${calculated_float}), using calculated")
                                        return calculated_float
                    except Exception as e:
                        logger.warning(f"Error using balance_amount property: {e}, using calculated value")
                    
                    # PRIORITY 2: Use calculated balance (fallback or when property is invalid)
                    return calculated_float
            
            payment_info = LoanPaymentInfo(active_loans, loan_amount)
            payment_source = 'loan'
            current_balance_display = payment_info.get_fee_balance()
            logger.info(f"Created loan payment_info: amount=${loan_amount}, balance=${current_balance_display}")
        
        # PRIORITY 2: If no active loan, check for service payment info
        if not payment_info:
            try:
                payment_info = Payment_Information.objects.filter(
                    customer=request.user
                ).order_by('-id').only('id', 'customer', 'payment_fees', 'down_payment', 'plan').first()
                
                if payment_info:
                    payment_source = 'service'
                    logger.info(f"User {request.user.username} has service payment info: {payment_info.id}")
            except Exception as db_error:
                logger.warning(f"Database query issue, trying alternate method: {db_error}")
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
                            'plan': result[4],
                            'customer': request.user  # Add customer for compatibility
                        })()
                        if payment_info:
                            payment_source = 'service'
                            logger.info(f"Created payment_info from raw query for user {request.user.username}")
        
        if not payment_info:
            # Route user to create payable context based on persona
            try:
                from finance.utilities.payment_utils import PaymentUtils
                named_url, absolute_url = PaymentUtils.get_persona_redirect_url(request.user)
                if named_url:
                    return redirect(reverse(named_url))
                if absolute_url:
                    return redirect(absolute_url)
            except Exception:
                pass
            
            # If no payment context found, redirect to loan application or service selection
            messages.error(request, 'No payment context found. Please select a service or apply for a loan to continue.')
            
            # Try to redirect to loan application first
            try:
                return redirect('finance:loan-home')
            except Exception:
                pass
            
            # Fallback to finance index
            try:
                return redirect('finance:finance-index')
            except Exception:
                pass
            
            # Last resort - show error page
            return render(request, 'finance/payments/no_payment_context.html', {
                'error_message': 'No payment context found. Please contact support or select a service.'
            })
        
        # Calculate amounts
        total_amount = payment_info.payment_fees
        down_payment = payment_info.down_payment
        
        # Calculate balance using get_fee_balance() method (accounts for payments already made)
        try:
            balance = payment_info.get_fee_balance()
        except Exception as e:
            logger.warning(f"Error calculating fee balance: {e}, using fallback calculation")
            # Fallback calculation
            balance = 0
            if total_amount and down_payment:
                balance = total_amount - down_payment
            elif total_amount:
                balance = total_amount
        
        # CRITICAL: Check if balance is zero - redirect to success if already paid
        if balance <= 0:
            logger.info(f"User {request.user.username} has zero balance (${balance}), redirecting to success page")
            messages.success(request, 'Your account balance is already paid in full. No payment needed!')
            # Store in session for success page
            request.session['payment_reference'] = 'BALANCE-PAID'
            request.session['payment_amount'] = 0
            request.session['payment_method'] = 'N/A'
            return redirect('finance:unified_success')
        
        context = {
            'available_methods': PAYMENT_METHODS,
            'total_amount': total_amount,
            'down_payment': down_payment,
            'balance': balance,
            'payment_info': payment_info,
        }
        return render(request, 'finance/payments/method_selection.html', context)
        
    except Exception as e:
        logger.error(f"Error in payment method selection: {str(e)}")
        messages.error(request, 'Error loading payment methods. Please try again.')
        return redirect('finance:payments', title='history', status='completed')


@login_required
def payment_amount_selection(request, method):
    """
    Shared payment amount selection page
    Works for all payment methods - user enters amount before proceeding
    Stores amount in session for use by all payment methods
    """
    if method not in PAYMENT_METHODS:
        messages.error(request, 'Invalid payment method selected.')
        return redirect('finance:unified_method_selection')
    
    try:
        from finance.models import LoanApplication
        
        payment_info = None
        payment_source = None
        
        # PRIORITY 1: Check for active loans first
        active_loans = LoanApplication.objects.filter(
            borrower=request.user,
            status__in=['active', 'approved', 'disbursed']
        ).first()
        
        if active_loans:
            logger.info(f"User {request.user.username} has active loan: {active_loans.id} for amount selection")
            
            # Refresh loan from DB to get latest payments
            active_loans.refresh_from_db()
            
            # Clear related objects cache to force fresh query for loan_payments
            if hasattr(active_loans, '_loan_payments_cache'):
                delattr(active_loans, '_loan_payments_cache')
            if hasattr(active_loans, '_prefetched_objects_cache'):
                active_loans._prefetched_objects_cache = {}
            
            # Force recalculation by accessing total_paid first
            _ = active_loans.total_paid
            current_balance = float(active_loans.balance_amount) if active_loans.balance_amount else 0.0
            if current_balance > 0:
                loan_amount = current_balance
            elif hasattr(active_loans, 'total_payable') and active_loans.total_payable:
                loan_amount = float(active_loans.total_payable)
            else:
                loan_amount = float(active_loans.amount_requested or 0)
            
            class LoanPaymentInfo:
                def __init__(self, loan, amount):
                    self.id = loan.id
                    self.customer = loan.borrower
                    self.payment_fees = amount
                    self.down_payment = 0
                    self.plan = None
                    self.loan_application = loan
                    self._loan = loan
                
                def get_fee_balance(self):
                    """Calculate outstanding loan balance - refreshes loan to get latest payments"""
                    # Refresh loan from DB to ensure we get latest payment records
                    self._loan.refresh_from_db()
                    
                    # Clear related objects cache to force fresh query for loan_payments
                    if hasattr(self._loan, '_loan_payments_cache'):
                        delattr(self._loan, '_loan_payments_cache')
                    if hasattr(self._loan, '_prefetched_objects_cache'):
                        self._loan._prefetched_objects_cache = {}
                    
                    # Calculate balance directly instead of relying on property
                    from decimal import Decimal
                    total_paid = self._loan.total_paid
                    total_payable = self._loan.total_payable or Decimal('0.00')
                    
                    # Calculate balance: total_payable - total_paid
                    calculated_balance = max(Decimal('0.00'), total_payable - total_paid)
                    return float(calculated_balance)
            
            payment_info = LoanPaymentInfo(active_loans, loan_amount)
            payment_source = 'loan'
        
        # PRIORITY 2: Check for service payment info
        if not payment_info:
            try:
                payment_info = Payment_Information.objects.filter(
                    customer=request.user
                ).order_by('-id').only('id', 'customer', 'payment_fees', 'down_payment', 'plan').first()
                
                if payment_info:
                    payment_source = 'service'
            except Exception as db_error:
                logger.warning(f"Database query issue: {db_error}")
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
                        payment_info = type('PaymentInfo', (), {
                            'id': result[0],
                            'customer_id': result[1],
                            'payment_fees': result[2],
                            'down_payment': result[3],
                            'plan': result[4],
                            'customer': request.user
                        })()
                        if payment_info:
                            payment_source = 'service'
        
        if not payment_info:
            messages.error(request, 'No payment information found.')
            return redirect('finance:unified_method_selection')
        
        # Calculate balance
        try:
            balance = payment_info.get_fee_balance()
        except Exception as e:
            logger.warning(f"Error calculating fee balance: {e}")
            balance = float(payment_info.payment_fees) - float(payment_info.down_payment or 0)
        
        # Check if balance is zero
        if balance <= 0:
            messages.success(request, 'Your account balance is already paid in full. No payment needed!')
            request.session['payment_reference'] = 'BALANCE-PAID'
            request.session['payment_amount'] = 0
            request.session['payment_method'] = 'N/A'
            return redirect('finance:unified_success')
        
        # Handle POST - form submission
        if request.method == 'POST':
            amount_type = request.POST.get('amount_type', 'full')
            
            if amount_type == 'full':
                amount = float(balance)
            else:
                amount = float(request.POST.get('amount', 0))
            
            # Validate amount
            if amount <= 0:
                messages.error(request, 'Payment amount must be greater than zero.')
                return redirect('finance:payment_amount_selection', method=method)
            
            if amount > balance:
                messages.error(request, f'Payment amount cannot exceed balance of ${balance:.2f}.')
                return redirect('finance:payment_amount_selection', method=method)
            
            # Store amount in session
            request.session['payment_amount'] = amount
            request.session['payment_source'] = payment_source
            if hasattr(payment_info, 'loan_application'):
                request.session['loan_application_id'] = payment_info.loan_application.id
            logger.info(f"Payment amount stored in session: ${amount} for method={method} user={request.user.username}")
            
            # Redirect to payment processing
            return redirect('finance:unified_processing', method=method)
        
        # GET - show form
        method_info = PAYMENT_METHODS.get(method, {})
        context = {
            'method': method,
            'method_info': method_info,
            'payment_info': payment_info,
            'balance': balance,
            'total_amount': payment_info.payment_fees,
            'down_payment': payment_info.down_payment,
        }
        
        return render(request, 'finance/payments/payment_amount_selection.html', context)
        
    except Exception as e:
        logger.error(f"Error in payment_amount_selection: {str(e)}")
        import traceback
        traceback.print_exc()
        messages.error(request, 'Error loading payment amount form. Please try again.')
        return redirect('finance:unified_method_selection')


@login_required
def payment_processing(request, method):
    """
    Unified payment processing view
    Handles payment initiation for all methods
    Checks for loans FIRST, then service payments
    """
    if method not in PAYMENT_METHODS:
        messages.error(request, 'Invalid payment method selected.')
        return redirect('finance:unified_method_selection')
    
    try:
        from finance.models import LoanApplication
        
        payment_info = None
        payment_source = None
        
        # PRIORITY 1: Check for active loans first (highest priority)
        active_loans = LoanApplication.objects.filter(
            borrower=request.user,
            status__in=['active', 'approved', 'disbursed']
        ).first()
        
        if active_loans:
            # User has active loan - create payment_info from loan
            logger.info(f"User {request.user.username} has active loan: {active_loans.id} for payment processing")
            
            # Refresh loan from DB to get latest payments
            active_loans.refresh_from_db()
            
            # Clear related objects cache to force fresh query for loan_payments
            if hasattr(active_loans, '_loan_payments_cache'):
                delattr(active_loans, '_loan_payments_cache')
            if hasattr(active_loans, '_prefetched_objects_cache'):
                active_loans._prefetched_objects_cache = {}
            
            # Force recalculation by accessing total_paid first
            _ = active_loans.total_paid
            current_balance = float(active_loans.balance_amount) if active_loans.balance_amount else 0.0
            if current_balance > 0:
                loan_amount = current_balance
            elif hasattr(active_loans, 'total_payable') and active_loans.total_payable:
                loan_amount = float(active_loans.total_payable)
            else:
                loan_amount = float(active_loans.amount_requested or 0)
            
            # Create payment_info-like object from loan
            class LoanPaymentInfo:
                def __init__(self, loan, amount):
                    self.id = loan.id
                    self.customer = loan.borrower
                    self.payment_fees = amount
                    self.down_payment = 0
                    self.plan = None
                    self.loan_application = loan
                    self._loan = loan
                
                def get_fee_balance(self):
                    """Calculate outstanding loan balance - refreshes loan to get latest payments"""
                    # Refresh loan from DB to ensure we get latest payment records
                    self._loan.refresh_from_db()
                    
                    # Clear related objects cache to force fresh query for loan_payments
                    if hasattr(self._loan, '_loan_payments_cache'):
                        delattr(self._loan, '_loan_payments_cache')
                    if hasattr(self._loan, '_prefetched_objects_cache'):
                        self._loan._prefetched_objects_cache = {}
                    
                    # Calculate balance directly instead of relying on property
                    # This ensures we get the correct value even if property has issues
                    from decimal import Decimal
                    total_paid = self._loan.total_paid
                    total_payable = self._loan.total_payable or Decimal('0.00')
                    
                    # Calculate balance: total_payable - total_paid
                    calculated_balance = max(Decimal('0.00'), total_payable - total_paid)
                    balance_float = float(calculated_balance)
                    
                    return balance_float
            
            payment_info = LoanPaymentInfo(active_loans, loan_amount)
            payment_source = 'loan'
            logger.info(f"Created loan payment_info for processing: amount=${loan_amount}")
        
        # PRIORITY 2: If no active loan, check for service payment info
        if not payment_info:
            try:
                payment_info = Payment_Information.objects.filter(
                    customer=request.user
                ).order_by('-id').only('id', 'customer', 'payment_fees', 'down_payment', 'plan').first()
                
                if payment_info:
                    payment_source = 'service'
            except Exception as db_error:
                logger.warning(f"Database query issue in payment processing: {db_error}")
                # Fallback: use raw query
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
                        payment_info = type('PaymentInfo', (), {
                            'id': result[0],
                            'customer_id': result[1],
                            'payment_fees': result[2],
                            'down_payment': result[3],
                            'plan': result[4],
                            'customer': request.user
                        })()
                        if payment_info:
                            payment_source = 'service'
        
        if not payment_info:
            messages.error(request, 'No payment information found.')
            return redirect('finance:unified_method_selection')
        
        # Initialize payment service (commented out for demo)
        # payment_service = PaymentService()
        payment_service = None
        
        if request.method == 'POST':
            # Process payment based on method
            result = process_payment_by_method(
                request, method, payment_info, payment_service
            )
            return result
        else:
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
    
    if not has_stripe_creds:
        logger.info(f"Stripe credentials not available for user {request.user.username}, showing payment details")
        return show_payment_details(request, 'stripe')
    
    # Get amount from request (default to full balance)
    amount = payment_info.get_fee_balance()
    if request.method == 'POST':
        amount = float(request.POST.get('amount', amount))
    elif request.method == 'GET':
        amount = float(request.GET.get('amount', amount))
    
    # Redirect to create Checkout Session (which will redirect to Stripe)
    logger.info(f"Redirecting to Stripe Checkout for user {request.user.username} amount={amount}")
    return redirect(f"{reverse('finance:stripe_checkout_session')}?amount={amount}")
@login_required
def payment_success(request):
    """Unified payment success view"""
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
        # Get any pre-selected amount from the shared amount selection step
        selected_amount = None
        try:
            if 'payment_amount' in request.session:
                selected_amount = float(request.session.get('payment_amount') or 0)
        except (TypeError, ValueError):
            selected_amount = None

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
            # If user selected an amount already, use it for display
            context = {
                'method': method,
                'method_info': method_info,
                'payment_info': payment_info,
                'selected_amount': selected_amount,
            }
            
            template_name = 'finance/payments/stripe_form.html'
            logger.info(f"Showing Stripe payment form for user {request.user.username}")
            return render(request, template_name, context)
        
        # For other automated methods (PayPal), show their specific forms
        method_info = PAYMENT_METHODS.get(method, {})
        from django.conf import settings
        
        # CRITICAL: Check if balance is zero before showing payment form
        try:
            fee_balance = payment_info.get_fee_balance()
            if fee_balance <= 0:
                logger.info(f"User {request.user.username} has zero balance (${fee_balance}), redirecting to success page")
                messages.success(request, 'Your account balance is already paid in full. No payment needed!')
                # Store in session for success page
                request.session['payment_reference'] = 'BALANCE-PAID'
                request.session['payment_amount'] = 0
                request.session['payment_method'] = 'N/A'
                return redirect('finance:unified_success')
        except Exception as e:
            logger.warning(f"Error checking fee balance: {e}, continuing with payment form")
            # If we can't check balance, continue (template will validate)
        
        context = {
            'method': method,
            'method_info': method_info,
            'payment_info': payment_info,
            'selected_amount': selected_amount,
            'PAYPAL_CLIENT_ID': getattr(settings, 'PAYPAL_CLIENT_ID', None),  # Pass PayPal client ID to template
        }
        
        template_name = f'finance/payments/{method}_form.html'

        return render(request, template_name, context)
        
    except Exception as e:
        logger.error(f"Error showing payment form for {method}: {str(e)}")
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