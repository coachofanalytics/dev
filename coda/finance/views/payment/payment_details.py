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
                'M-Pesa Number': os.environ.get('MPESA_PHONE_NUMBER', '+254 728905233'),
                'Paybill/Till Number': os.environ.get('MPESA_PAYBILL', '600100'),
                'Account Number': os.environ.get('MPESA_ACCOUNT_NUMBER', '0100008710958')
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
                'CashApp Username': os.environ.get('CASHAPP', '$codainfo'),
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
                'Account Number': os.environ.get('ZELLE_ACCOUNT_NUMBER', '354012506439'),
                'Routing Number': os.environ.get('ZELLE_ROUTING_NUMBER', '081000032'),
                'Account Name': os.environ.get('ZELLE_ACCOUNT_NAME', 'Crown Data Analysis And Consulting LLC'),
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
                'Venmo Username': os.environ.get('VENMO', '@coda_info'),
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
    Shows payment details for ANY logged-in user
    Accessible to investors, donors, loan borrowers, service clients, etc.
    Amount can come from:
    1. Query parameter (?amount=XXX)
    2. Session (if set during payment flow)
    3. User's outstanding balance (loan or service) if exists
    4. User can specify custom amount in the form
    """
    try:
        from finance.models import LoanApplication
        
        payment_info = None
        payment_source = None
        suggested_amount = 0.0
        
        # PRIORITY 1: Check for active loans first (to suggest amount)
        active_loans = LoanApplication.objects.filter(
            borrower=request.user,
            status__in=['active', 'approved', 'disbursed']
        ).first()
        
        if active_loans:
            # User has active loan - get balance for suggested amount
            logger.info(f"User {request.user.username} has active loan: {active_loans.id} for payment details")
            
            active_loans.refresh_from_db()
            if hasattr(active_loans, '_loan_payments_cache'):
                delattr(active_loans, '_loan_payments_cache')
            if hasattr(active_loans, '_prefetched_objects_cache'):
                active_loans._prefetched_objects_cache = {}
            
            current_balance = float(active_loans.balance_amount) if active_loans.balance_amount else 0.0
            if current_balance > 0:
                suggested_amount = current_balance
            elif hasattr(active_loans, 'total_payable') and active_loans.total_payable:
                suggested_amount = float(active_loans.total_payable)
            else:
                suggested_amount = float(active_loans.amount_requested or 0)
            
            payment_source = 'loan'
        
        # PRIORITY 2: If no active loan, check for service payment info (to suggest amount)
        if not payment_info:
            payment_info = Payment_Information.objects.filter(
                customer=request.user
            ).only('id', 'customer', 'payment_fees', 'down_payment', 'plan').order_by('-id').first()
            
            if payment_info:
                payment_source = 'service'
                # Suggest down_payment or full payment_fees
                suggested_amount = payment_info.down_payment if hasattr(payment_info, 'down_payment') and payment_info.down_payment else payment_info.payment_fees
        
        # Get amount from (in order of priority):
        # 1) Query parameter (explicit amount specified)
        # 2) Session (from payment flow)
        # 3) Suggested amount (from loan or service balance)
        amount = None
        
        if request.GET.get('amount'):
            try:
                amount = float(request.GET.get('amount'))
            except (ValueError, TypeError):
                pass
        
        if amount is None and 'payment_amount' in request.session:
            try:
                amount = float(request.session.get('payment_amount'))
            except (ValueError, TypeError):
                pass
        
        if amount is None:
            amount = suggested_amount
        
        # Default to 0 if still no amount (user can specify in form)
        if amount is None or amount <= 0:
            amount = 0.0
        
        # Generate payment reference
        payment_reference = generate_payment_reference(request.user.id, method)
        
        # Get method-specific payment details
        method_config = get_payment_details_for_method(method)
        
        # Check if this is a fallback (error scenario)
        error_message = request.GET.get('error', None)
        is_fallback = error_message is not None
        
        context = {
            'method': method,
            'method_config': method_config,
            'payment_info': payment_info,  # May be None - that's OK
            'payment_source': payment_source,  # 'loan', 'service', or None
            'payment_reference': payment_reference,
            'amount': amount,
            'suggested_amount': suggested_amount,  # Amount from loan/service if exists
            'has_outstanding_balance': suggested_amount > 0,
            'user': request.user,
            'is_fallback': is_fallback,
            'error_message': error_message,
            'support_email': os.environ.get('EMAIL_INFO_USER', 'info@codanalytics.net'),
            'timestamp': timezone.now()
        }
        
        # Send email notification with payment details (only if amount > 0)
        if amount > 0:
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
        else:
            messages.info(
                request,
                'Please specify the payment amount. Payment details will be shown below.'
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

