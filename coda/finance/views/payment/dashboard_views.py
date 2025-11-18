"""
Payment Dashboard Views
User-facing payment history and status tracking
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.core.paginator import Paginator
from django.utils import timezone
import logging

from finance.models import Payment_History, Payment_Information

logger = logging.getLogger(__name__)


@login_required
def payment_dashboard(request):
    """
    User payment dashboard showing all payments with filters and stats
    """
    try:
        # Get filter parameters
        status_filter = request.GET.get('status', 'all')
        method_filter = request.GET.get('method', 'all')
        search_query = request.GET.get('search', '')
        
        # Base queryset - user's payments only
        payments = Payment_History.objects.filter(customer=request.user).order_by('-contract_submitted_date')
        
        # Apply status filter
        if status_filter != 'all':
            payments = payments.filter(status=status_filter)
        
        # Apply method filter
        if method_filter != 'all':
            payments = payments.filter(payment_method__icontains=method_filter)
        
        # Apply search
        if search_query:
            payments = payments.filter(
                Q(id__icontains=search_query) |
                Q(notes__icontains=search_query) |
                Q(transaction_id__icontains=search_query)
            )
        
        # Calculate summary statistics
        all_payments = Payment_History.objects.filter(customer=request.user)
        
        stats = {
            'total_payments': all_payments.count(),
            'total_amount': all_payments.aggregate(total=Sum('payment_fees'))['total'] or 0,
            'pending_count': all_payments.filter(status='pending').count(),
            'completed_count': all_payments.filter(status='completed').count(),
            'failed_count': all_payments.filter(status='failed').count(),
            'pending_amount': all_payments.filter(status='pending').aggregate(total=Sum('payment_fees'))['total'] or 0,
        }
        
        # Get method breakdown
        method_stats = all_payments.values('payment_method').annotate(
            count=Count('id'),
            total=Sum('payment_fees')
        ).order_by('-count')
        
        # Pagination
        paginator = Paginator(payments, 20)  # 20 payments per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Get user's payment information
        payment_info = Payment_Information.objects.filter(
            customer=request.user
        ).only('id', 'customer', 'payment_fees', 'down_payment', 'plan').order_by('-id').first()
        
        context = {
            'payments': page_obj,
            'stats': stats,
            'method_stats': method_stats,
            'payment_info': payment_info,
            'status_filter': status_filter,
            'method_filter': method_filter,
            'search_query': search_query,
            'available_methods': ['PayPal', 'Stripe', 'MPESA', 'CashApp', 'Zelle', 'Venmo'],
        }
        
        return render(request, 'finance/payments/payment_dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Error loading payment dashboard for user {request.user.id}: {e}")
        messages.error(request, 'Error loading payment dashboard.')
        return redirect('finance:pay')


@login_required
def retry_payment(request, payment_id):
    """
    Retry a failed payment
    Redirects to payment method selection with pre-filled amount
    """
    try:
        payment = get_object_or_404(
            Payment_History,
            id=payment_id,
            customer=request.user
        )
        
        if payment.status != 'failed':
            messages.warning(request, 'This payment is not in failed status.')
            return redirect('finance:payment_dashboard')
        
        # Store retry context in session
        request.session['retry_payment'] = {
            'original_payment_id': payment.id,
            'amount': float(payment.payment_fees),
            'method': payment.payment_method.lower()
        }
        
        messages.info(request, f'Retrying payment of ${payment.payment_fees}. Please select payment method.')
        return redirect('finance:unified_method_selection')
        
    except Payment_History.DoesNotExist:
        messages.error(request, 'Payment not found.')
        return redirect('finance:payment_dashboard')
    except Exception as e:
        logger.error(f"Error retrying payment {payment_id}: {e}")
        messages.error(request, 'Error retrying payment.')
        return redirect('finance:payment_dashboard')

