"""
Phase 7: Batch Approval Views
Client approval interface and staff batch management
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from decimal import Decimal

from ...models import PositionBatch, OptionsPosition
from ...services.batch_approval_service import BatchApprovalService
from ...services.notification_service import NotificationService


def is_staff(user):
    return user.is_staff


@login_required
def batch_approval_view(request, batch_id):
    """
    Client view: Approve or reject position batch
    Shows all positions with option to approve all, reject all, or review individually
    """
    batch = get_object_or_404(
        PositionBatch,
        id=batch_id,
        managed_account__client=request.user
    )
    
    # Check if batch is expired
    if batch.is_expired:
        messages.error(request, "This batch has expired (24-hour timeout). All positions have been rejected.")
        return redirect('investing:client_portal')
    
    # Check if batch is already processed
    if batch.status != 'pending':
        messages.info(request, f"This batch has already been {batch.status}.")
        return redirect('investing:client_portal')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        signature_data = request.POST.get('signature')
        ip_address = request.META.get('REMOTE_ADDR')
        
        if action == 'approve_all':
            if not signature_data:
                messages.error(request, "Signature required to approve batch")
            else:
                approved_count = batch.approve_all(signature_data, ip_address)
                
                # Send confirmation email
                notification_service = NotificationService()
                notification_service.send_batch_approved_notification(batch, approved_count)
                
                messages.success(
                    request,
                    f"✅ Approved {approved_count} positions! "
                    f"${batch.total_capital_required:,.2f} capital deployed."
                )
                return redirect('investing:client_portal')
        
        elif action == 'reject_all':
            reason = request.POST.get('rejection_reason', 'Rejected by client')
            rejected_count = batch.reject_all(reason)
            
            messages.info(request, f"Rejected {rejected_count} positions")
            return redirect('investing:client_portal')
        
        elif action == 'review_individually':
            # Client approves some, rejects others
            from django.db import transaction
            
            with transaction.atomic():
                now = timezone.now()
                approved_count = 0
                rejected_count = 0
                account = batch.managed_account
                total_capital_deployed = Decimal('0.00')
                
                for position in batch.positions.all():
                    position_action = request.POST.get(f'position_{position.id}')
                    
                    if position_action == 'approve':
                        position.status = 'open'
                        position.approved_at = now
                        position.approval_method = 'batch'
                        position.auto_approved = False
                        position.entered_at = now
                        position.entered_by = request.user if request.user.is_staff else None
                        position.save()
                        
                        # Deduct capital from account
                        account.cash_reserved += position.capital_required
                        account.cash_available -= position.capital_required
                        total_capital_deployed += position.capital_required
                        
                        approved_count += 1
                    
                    elif position_action == 'reject':
                        position.status = 'rejected'
                        position.rejection_reason = request.POST.get(
                            f'rejection_reason_{position.id}',
                            'Rejected by client'
                        )
                        position.auto_approved = False
                        position.save()
                        rejected_count += 1
                
                # Save account balance changes
                if approved_count > 0:
                    account.save(update_fields=['cash_reserved', 'cash_available', 'updated_at'])
                
                # Update batch status
                if approved_count > 0 and rejected_count > 0:
                    batch.status = 'partial'
                elif approved_count > 0:
                    batch.status = 'approved'
                elif rejected_count > 0:
                    batch.status = 'rejected'
                
                batch.approved_date = now
                batch.approval_signature = signature_data
                batch.approval_ip = ip_address
                batch.save()
            
            messages.success(
                request,
                f"Approved {approved_count} positions, Rejected {rejected_count} positions. ${total_capital_deployed:,.2f} capital deployed."
            )
            return redirect('investing:client_portal')
    
    # GET request - show batch for approval
    batch_service = BatchApprovalService()
    summary = batch_service.get_batch_summary(batch)
    
    context = {
        'batch': batch,
        'positions': summary['positions'],
        'total_capital': summary['total_capital'],
        'time_remaining': summary['time_remaining'],
        'hours_remaining': summary['hours_remaining'],
        'can_approve': summary['can_approve'],
    }
    return render(request, 'investing/batches/batch_approval.html', context)


@login_required
def client_batches_list(request):
    """
    Client view: List all their batches (pending, approved, expired)
    """
    batches = PositionBatch.objects.filter(
        managed_account__client=request.user
    ).select_related('managed_account').order_by('-created_date')
    
    context = {
        'batches': batches,
        'pending_count': batches.filter(status='pending').count(),
    }
    return render(request, 'investing/batches/client_batches_list.html', context)


@user_passes_test(is_staff)
def staff_create_batch_view(request, account_id):
    """
    Staff view: Manually create a batch for an account
    """
    from ...models import ManagedTradingAccount
    account = get_object_or_404(ManagedTradingAccount, id=account_id)
    
    batch_service = BatchApprovalService()
    batch = batch_service.create_weekly_batch(account)
    
    if batch:
        messages.success(
            request,
            f"Created batch {batch.batch_number} with {batch.total_positions} positions"
        )
    else:
        messages.info(request, "No pending positions to batch")
    
    return redirect('investing:managed_account_detail', account_id=account_id)


@user_passes_test(is_staff)
def staff_batches_list(request):
    """
    Staff view: All batches across all accounts
    """
    batches = PositionBatch.objects.all().select_related(
        'managed_account', 'managed_account__client'
    ).order_by('-created_date')[:50]  # Last 50 batches
    
    context = {
        'batches': batches,
        'pending_count': PositionBatch.objects.filter(status='pending').count(),
        'expiring_soon': PositionBatch.objects.filter(
            status='pending',
            approval_deadline__lte=timezone.now() + timezone.timedelta(hours=6)
        ).count(),
    }
    return render(request, 'investing/batches/staff_batches_list.html', context)


@require_http_methods(["POST"])
@login_required
def ajax_check_batch_status(request, batch_id):
    """
    AJAX endpoint: Check if batch is still valid for approval
    Returns JSON with batch status
    """
    batch = get_object_or_404(PositionBatch, id=batch_id)
    
    return JsonResponse({
        'status': batch.status,
        'is_expired': batch.is_expired,
        'hours_remaining': batch.hours_remaining,
        'can_approve': batch.is_pending,
    })

