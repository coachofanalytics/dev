"""
Payment Details View - Universal Fallback System
Displays payment details when automated payment fails or is unavailable
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
import logging
import os
from datetime import datetime

from finance.models import Payment_Information, Payment_History
from mail.custom_email import send_email

logger = logging.getLogger(__name__)


def generate_payment_reference(user_id, method):
    """Generate unique payment reference number"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"PAY-{method.upper()}-{user_id}-{timestamp}"


def get_payment_details_for_method(method):
    """
    Get payment details from environment variables for each method
    Returns dict with method-specific payment information
    """
    payment_configs = {
        'paypal': {
            'display_name': 'PayPal',
            'icon': 'fa fa-paypal',
            'instructions': [
                'Send payment to the PayPal email below',
                'Include payment reference in the note/memo',
                'Keep your PayPal transaction ID',
                'Email confirmation will be sent within 24 hours'
            ],
            'details': {
                'PayPal Email': os.environ.get('PAYPAL_EMAIL', 'payments@codanalytics.net'),
                'Alternative': 'You can also use the PayPal button on the payment page'
            }
        },
        'mpesa': {
            'display_name': 'M-Pesa',
            'icon': 'fa fa-mobile',
            'instructions': [
                'Go to M-Pesa on your phone',
                'Select Lipa Na M-Pesa',
                'Select Pay Bill or Buy Goods',
                'Enter the business number below',
                'Enter the amount',
                'Use payment reference as account number',
                'Enter your M-Pesa PIN and confirm'
            ],
            'details': {
                'M-Pesa Number': os.environ.get('MPESA_PHONE_NUMBER', '+254 XXX XXX XXX'),
                'Paybill/Till Number': os.environ.get('MPESA_PAYBILL', 'Contact support'),
                'Account Number': 'Use Payment Reference below'
            }
        },
        'cashapp': {
            'display_name': 'CashApp',
            'icon': 'fa fa-dollar',
            'instructions': [
                'Open CashApp on your phone',
                'Send payment to the CashApp username below',
                'Include payment reference in the note',
                'Screenshot the confirmation',
                'Email screenshot to support (optional)'
            ],
            'details': {
                'CashApp Username': os.environ.get('CASHAPP', '$codanalytics'),
                'Note': 'Include payment reference in note field'
            }
        },
        'zelle': {
            'display_name': 'Zelle',
            'icon': 'fa fa-university',
            'instructions': [
                'Open your banking app',
                'Select Send Money with Zelle',
                'Use the account details below',
                'Include payment reference in memo',
                'Keep confirmation number'
            ],
            'details': {
                'Account Number': os.environ.get('STANBIC_ACCOUNT_NO', 'Contact support'),
                'Routing Number': os.environ.get('STANBIC_ROUTING', 'Contact support'),
                'Account Name': 'CODA Analytics',
                'Memo': 'Include payment reference'
            }
        },
        'venmo': {
            'display_name': 'Venmo',
            'icon': 'fa fa-cc-venmo',
            'instructions': [
                'Open Venmo app',
                'Search for the username below',
                'Send the exact amount',
                'Include payment reference in note',
                'Keep transaction confirmation'
            ],
            'details': {
                'Venmo Username': os.environ.get('VENMO', '@codanalytics'),
                'Note': 'Include payment reference in note field'
            }
        },
        'stripe': {
            'display_name': 'Card Payment (Stripe)',
            'icon': 'fa fa-credit-card',
            'instructions': [
                'Card payment system is temporarily unavailable',
                'Please use bank transfer as alternative',
                'Or contact support for card payment link',
                'Bank transfer details below'
            ],
            'details': {
                'Bank Account': os.environ.get('STANBIC_ACCOUNT_NO', 'Contact support'),
                'Routing': os.environ.get('STANBIC_ROUTING', 'Contact support'),
                'Account Name': 'CODA Analytics',
                'SWIFT': os.environ.get('SWIFT_CODE', 'Contact support'),
                'Reference': 'Include payment reference'
            }
        }
    }
    
    return payment_configs.get(method, {
        'display_name': method.title(),
        'icon': 'fa fa-money',
        'instructions': ['Contact support for payment details'],
        'details': {'Support Email': os.environ.get('EMAIL_INFO_USER', 'info@codanalytics.net')}
    })


@login_required
def show_payment_details(request, method):
    """
    Universal payment details view
    Shows payment details when automated payment fails or is unavailable
    Checks for loans FIRST, then service payments
    """
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
            logger.info(f"User {request.user.username} has active loan: {active_loans.id} for payment details")
            
            # Refresh loan from DB to get latest payments
            active_loans.refresh_from_db()
            
            # Clear related objects cache
            if hasattr(active_loans, '_loan_payments_cache'):
                delattr(active_loans, '_loan_payments_cache')
            if hasattr(active_loans, '_prefetched_objects_cache'):
                active_loans._prefetched_objects_cache = {}
            
            # Calculate loan amount (balance)
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
                    self.down_payment = 0  # Loans don't have down payments
                    self.plan = None
                    self.loan_application = loan
                    self._loan = loan
                
                def get_fee_balance(self):
                    """Calculate outstanding loan balance"""
                    self._loan.refresh_from_db()
                    if hasattr(self._loan, '_loan_payments_cache'):
                        delattr(self._loan, '_loan_payments_cache')
                    if hasattr(self._loan, '_prefetched_objects_cache'):
                        self._loan._prefetched_objects_cache = {}
                    
                    from decimal import Decimal
                    total_paid = self._loan.total_paid
                    total_payable = self._loan.total_payable or Decimal('0.00')
                    calculated_balance = max(Decimal('0.00'), total_payable - total_paid)
                    return float(calculated_balance)
            
            payment_info = LoanPaymentInfo(active_loans, loan_amount)
            payment_source = 'loan'
        
        # PRIORITY 2: If no active loan, check for service payment info
        if not payment_info:
            payment_info = Payment_Information.objects.filter(
                customer=request.user
            ).only('id', 'customer', 'payment_fees', 'down_payment', 'plan').order_by('-id').first()
            
            if payment_info:
                payment_source = 'service'
        
        # If still no payment_info, redirect
        if not payment_info:
            messages.error(request, 'No payment information found. Please create a payment or apply for a loan first.')
            try:
                return redirect('finance:loan-home')
            except Exception:
                return redirect('finance:finance-index')
        
        # Generate payment reference
        payment_reference = generate_payment_reference(request.user.id, method)
        
        # Get method-specific payment details
        method_config = get_payment_details_for_method(method)
        
        # Calculate amounts
        # For loans, use payment_fees (which is the loan balance)
        # For service payments, use down_payment if available, otherwise payment_fees
        if payment_source == 'loan':
            amount = payment_info.payment_fees  # This is the loan balance
        else:
            amount = payment_info.down_payment if hasattr(payment_info, 'down_payment') and payment_info.down_payment else payment_info.payment_fees
        
        # Check if this is a fallback (error scenario)
        error_message = request.GET.get('error', None)
        is_fallback = error_message is not None
        
        context = {
            'method': method,
            'method_config': method_config,
            'payment_info': payment_info,
            'payment_reference': payment_reference,
            'amount': amount,
            'user': request.user,
            'is_fallback': is_fallback,
            'error_message': error_message,
            'support_email': os.environ.get('EMAIL_INFO_USER', 'info@codanalytics.net'),
            'timestamp': timezone.now()
        }
        
        # Send email notification with payment details
        try:
            send_payment_details_email(
                user=request.user,
                method=method,
                amount=amount,
                reference=payment_reference,
                method_config=method_config
            )
            messages.success(
                request, 
                f'Payment details sent to your email ({request.user.email})'
            )
        except Exception as e:
            logger.error(f"Failed to send payment details email: {e}")
            messages.warning(
                request,
                'Payment details displayed below. Email notification failed - please save this information.'
            )
        
        # Log the fallback event
        logger.info(
            f"Payment details shown for user {request.user.username}, "
            f"method: {method}, reference: {payment_reference}, "
            f"is_fallback: {is_fallback}"
        )
        
        return render(request, 'finance/payments/payment_details.html', context)
        
    except Exception as e:
        logger.error(f"Error showing payment details: {str(e)}")
        messages.error(request, 'Error displaying payment details. Please contact support.')
        # Redirect to loan application instead of method selection to avoid loop
        try:
            return redirect('finance:loan-home')
        except Exception:
            return redirect('finance:finance-index')


def send_payment_details_email(user, method, amount, reference, method_config):
    """Send email with payment details to user"""
    subject = f"Payment Details for {method_config['display_name']}"
    
    context = {
        'user': user,
        'method': method,
        'method_name': method_config['display_name'],
        'amount': amount,
        'reference': reference,
        'instructions': method_config['instructions'],
        'details': method_config['details'],
        'support_email': os.environ.get('EMAIL_INFO_USER', 'info@codanalytics.net')
    }
    
    try:
        send_email(
            category=user.category if hasattr(user, 'category') else 'client',
            to_email=[user.email],
            subject=subject,
            html_template='email/payment/payment_details.html',
            context=context
        )
        logger.info(f"Payment details email sent to {user.email} for method {method}")
    except Exception as e:
        logger.error(f"Failed to send payment details email: {e}")
        raise


@login_required
def upload_payment_proof(request, reference):
    """
    Allow users to upload proof of payment (optional)
    For manual payment verification
    """
    if request.method == 'POST':
        try:
            proof_file = request.FILES.get('proof_file')
            notes = request.POST.get('notes', '')
            
            if not proof_file:
                messages.error(request, 'Please select a file to upload')
                return redirect('finance:payment_details', method='unknown')
            
            # TODO: Save proof file (implement file storage)
            # For now, just log
            logger.info(
                f"Payment proof uploaded by {request.user.username}, "
                f"reference: {reference}, file: {proof_file.name}"
            )
            
            messages.success(
                request,
                'Payment proof uploaded successfully. Our team will verify within 24 hours.'
            )
            return redirect('finance:payments', title='history', status='pending')
            
        except Exception as e:
            logger.error(f"Error uploading payment proof: {e}")
            messages.error(request, 'Error uploading file. Please try again or contact support.')
            return redirect('finance:payment_details', method='unknown')
    
    # Fallback redirect - go to loan application instead of method selection
    try:
        return redirect('finance:loan-home')
    except Exception:
        return redirect('finance:finance-index')

