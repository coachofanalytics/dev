"""
Admin Payment Verification Views
Staff-only views for verifying manual payments
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from django.core.paginator import Paginator
import logging

from finance.models import Payment_History, Payment_Information
from mail.custom_email import send_email

logger = logging.getLogger(__name__)


def is_staff_user(user):
    """Check if user is staff"""
    return user.is_staff or user.is_superuser


@login_required
@user_passes_test(is_staff_user)
def admin_payment_verification_dashboard(request):
    """
    Admin dashboard for verifying manual payments
    Shows pending payments that need verification
    """
    try:
        # Get filter parameters
        status_filter = request.GET.get('status', 'pending')
        method_filter = request.GET.get('method', 'all')
        search_query = request.GET.get('search', '')
        
        # Base queryset - all payments
        payments = Payment_History.objects.all().select_related('customer').order_by('-contract_submitted_date')
        
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
                Q(customer__username__icontains=search_query) |
                Q(customer__email__icontains=search_query) |
                Q(notes__icontains=search_query)
            )
        
        # Calculate summary statistics
        all_payments = Payment_History.objects.all()
        stats = {
            'pending_count': all_payments.filter(status='pending').count(),
            'completed_today': all_payments.filter(
                status='completed',
                contract_submitted_date__date=timezone.now().date()
            ).count(),
            'failed_count': all_payments.filter(status='failed').count(),
            'needs_review': all_payments.filter(status='pending').count(),  # TODO: Add proof_uploaded field
        }
        
        # Pagination
        paginator = Paginator(payments, 25)  # 25 payments per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'payments': page_obj,
            'stats': stats,
            'status_filter': status_filter,
            'method_filter': method_filter,
            'search_query': search_query,
        }
        
        return render(request, 'finance/admin/payment_verification_dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Error loading admin verification dashboard: {e}")
        messages.error(request, 'Error loading verification dashboard.')
        return redirect('admin:index')


@login_required
@user_passes_test(is_staff_user)
def approve_payment(request, payment_id):
    """
    Approve a pending payment
    """
    try:
        payment = get_object_or_404(Payment_History, id=payment_id)
        
        if payment.status != 'pending':
            messages.warning(request, 'This payment is not in pending status.')
            return redirect('finance:admin_payment_verification')
        
        # Prevent staff from approving own payments
        if payment.customer == request.user:
            messages.error(request, 'You cannot approve your own payment.')
            return redirect('finance:admin_payment_verification')
        
        # Update payment status
        payment.status = 'completed'
        
        # Add verification notes
        verification_note = f"\nVerified by {request.user.username} on {timezone.now().strftime('%Y-%m-%d %H:%M')}"
        payment.notes = (payment.notes or '') + verification_note
        payment.save()
        
        # Send confirmation email to customer
        try:
            send_payment_verification_email(
                payment=payment,
                approved=True,
                verified_by=request.user
            )
        except Exception as e:
            logger.error(f"Error sending approval email: {e}")
            messages.warning(request, 'Payment approved but email notification failed.')
        
        messages.success(
            request,
            f'Payment #{payment.id} approved for {payment.customer.username}. Email sent to {payment.customer.email}.'
        )
        
        # Log the approval
        logger.info(
            f"Payment {payment.id} approved by {request.user.username} "
            f"for customer {payment.customer.username}, amount ${payment.payment_fees}"
        )
        
        return redirect('finance:admin_payment_verification')
        
    except Payment_History.DoesNotExist:
        messages.error(request, 'Payment not found.')
        return redirect('finance:admin_payment_verification')
    except Exception as e:
        logger.error(f"Error approving payment {payment_id}: {e}")
        messages.error(request, 'Error approving payment.')
        return redirect('finance:admin_payment_verification')


@login_required
@user_passes_test(is_staff_user)
def reject_payment(request, payment_id):
    """
    Reject a pending payment with reason
    """
    try:
        payment = get_object_or_404(Payment_History, id=payment_id)
        
        if payment.status != 'pending':
            messages.warning(request, 'This payment is not in pending status.')
            return redirect('finance:admin_payment_verification')
        
        # Prevent staff from rejecting own payments
        if payment.customer == request.user:
            messages.error(request, 'You cannot reject your own payment.')
            return redirect('finance:admin_payment_verification')
        
        # Get rejection reason
        if request.method == 'POST':
            rejection_reason = request.POST.get('reason', 'Payment verification failed')
            
            # Update payment status
            payment.status = 'failed'
            
            # Add rejection notes
            rejection_note = f"\nRejected by {request.user.username} on {timezone.now().strftime('%Y-%m-%d %H:%M')}: {rejection_reason}"
            payment.notes = (payment.notes or '') + rejection_note
            payment.save()
            
            # Send rejection email to customer
            try:
                send_payment_verification_email(
                    payment=payment,
                    approved=False,
                    verified_by=request.user,
                    reason=rejection_reason
                )
            except Exception as e:
                logger.error(f"Error sending rejection email: {e}")
                messages.warning(request, 'Payment rejected but email notification failed.')
            
            messages.success(
                request,
                f'Payment #{payment.id} rejected. Email sent to {payment.customer.email}.'
            )
            
            # Log the rejection
            logger.info(
                f"Payment {payment.id} rejected by {request.user.username} "
                f"for customer {payment.customer.username}, reason: {rejection_reason}"
            )
            
            return redirect('finance:admin_payment_verification')
        
        # Show rejection form
        context = {'payment': payment}
        return render(request, 'finance/admin/reject_payment_form.html', context)
        
    except Payment_History.DoesNotExist:
        messages.error(request, 'Payment not found.')
        return redirect('finance:admin_payment_verification')
    except Exception as e:
        logger.error(f"Error rejecting payment {payment_id}: {e}")
        messages.error(request, 'Error rejecting payment.')
        return redirect('finance:admin_payment_verification')


def send_payment_verification_email(payment, approved, verified_by, reason=None):
    """
    Send email notification for payment approval/rejection
    """
    if approved:
        subject = f"Payment Approved - Receipt #{payment.id}"
        template = 'email/payment/payment_approved.html'
    else:
        subject = f"Payment Verification Issue - Reference #{payment.id}"
        template = 'email/payment/payment_rejected.html'
    
    context = {
        'payment': payment,
        'customer': payment.customer,
        'verified_by': verified_by.get_full_name() or verified_by.username,
        'verification_date': timezone.now(),
        'approved': approved,
        'reason': reason,
        'support_email': 'info@codanalytics.net',
    }
    
    try:
        send_email(
            category=payment.customer.category if hasattr(payment.customer, 'category') else 'client',
            to_email=[payment.customer.email],
            subject=subject,
            html_template=template,
            context=context
        )
        logger.info(f"Verification email sent to {payment.customer.email} for payment {payment.id}")
    except Exception as e:
        logger.error(f"Failed to send verification email: {e}")
        raise


@login_required
@user_passes_test(is_staff_user)
def bulk_approve_payments(request):
    """
    Bulk approve multiple payments at once
    """
    if request.method == 'POST':
        try:
            payment_ids = request.POST.getlist('payment_ids')
            
            if not payment_ids:
                messages.warning(request, 'No payments selected.')
                return redirect('finance:admin_payment_verification')
            
            approved_count = 0
            for payment_id in payment_ids:
                try:
                    payment = Payment_History.objects.get(id=payment_id, status='pending')
                    
                    # Skip own payments
                    if payment.customer == request.user:
                        continue
                    
                    payment.status = 'completed'
                    payment.notes = (payment.notes or '') + f"\nBulk approved by {request.user.username} on {timezone.now().strftime('%Y-%m-%d %H:%M')}"
                    payment.save()
                    
                    # Send email
                    try:
                        send_payment_verification_email(payment, True, request.user)
                    except:
                        pass
                    
                    approved_count += 1
                    
                except Exception as e:
                    logger.error(f"Error bulk approving payment {payment_id}: {e}")
                    continue
            
            messages.success(request, f'Successfully approved {approved_count} payment(s).')
            logger.info(f"Bulk approval: {approved_count} payments approved by {request.user.username}")
            
        except Exception as e:
            logger.error(f"Error in bulk approve: {e}")
            messages.error(request, 'Error processing bulk approval.')
    
    return redirect('finance:admin_payment_verification')

