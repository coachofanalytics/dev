"""
Budget Projection Approval Views

Handles approval workflow for budget projections, connecting to the existing
approval system and policies.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db import transaction
from django.core.paginator import Paginator

from finance.models import BudgetEstimateProjection, ApprovalPolicy
from finance.services.automation_service import ApprovalEngineService
from finance.utils.filter_utils import FilterUtils


@login_required
def budget_projection_approvals(request):
    """
    List budget projections pending approval
    """
    user = request.user
    
    # Get projections pending approval
    projections = BudgetEstimateProjection.objects.filter(
        status='submitted'
    ).order_by('-submitted_at')
    
    # Filter by user permissions
    if not user.is_staff and not user.is_superuser:
        # Non-staff users can only see their own projections
        projections = projections.filter(created_by=user)
    
    # Apply filters
    company_id = request.GET.get('company_id')
    department_id = request.GET.get('department_id')
    horizon = request.GET.get('horizon')
    
    if company_id:
        projections = projections.filter(company_id=company_id)
    if department_id:
        projections = projections.filter(department_id=department_id)
    if horizon:
        projections = projections.filter(horizon=horizon)
    
    # Pagination
    paginator = Paginator(projections, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'projections': page_obj,
        'filters': {
            'company_id': company_id,
            'department_id': department_id,
            'horizon': horizon,
        }
    }
    
    return render(request, 'finance/approvals/budget_projection_approvals.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def approve_budget_projection(request, projection_id):
    """
    Approve or reject a budget projection
    """
    projection = get_object_or_404(BudgetEstimateProjection, id=projection_id)
    
    # Check permissions
    if not request.user.is_staff and not request.user.is_superuser:
        if projection.created_by != request.user:
            messages.error(request, "You don't have permission to approve this projection.")
            return redirect('finance:budget-projection-approvals')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        comments = request.POST.get('comments', '')
        
        try:
            with transaction.atomic():
                if action == 'approve':
                    projection.status = 'approved'
                    projection.reviewed_by = request.user
                    projection.reviewed_at = timezone.now()
                    projection.review_notes = comments
                    projection.save()
                    
                    messages.success(request, f"Budget projection #{projection.id} approved successfully.")
                    
                    # Send notification email (if email service is available)
                    try:
                        from finance.services.email_service import EmailService
                        email_service = EmailService()
                        email_service.send_approval_notification(
                            projection.created_by,
                            projection,
                            'approved',
                            comments
                        )
                    except Exception as e:
                        # Log error but don't fail the approval
                        print(f"Failed to send approval email: {e}")
                    
                elif action == 'reject':
                    projection.status = 'rejected'
                    projection.reviewed_by = request.user
                    projection.reviewed_at = timezone.now()
                    projection.review_notes = comments
                    projection.save()
                    
                    messages.success(request, f"Budget projection #{projection.id} rejected.")
                    
                    # Send notification email
                    try:
                        from finance.services.email_service import EmailService
                        email_service = EmailService()
                        email_service.send_approval_notification(
                            projection.created_by,
                            projection,
                            'rejected',
                            comments
                        )
                    except Exception as e:
                        print(f"Failed to send rejection email: {e}")
                
                return redirect('finance:budget-projection-approvals')
                
        except Exception as e:
            messages.error(request, f"Error processing approval: {str(e)}")
    
    context = {
        'projection': projection,
        'approval_policies': ApprovalPolicy.objects.filter(is_active=True)
    }
    
    return render(request, 'finance/approvals/approve_projection.html', context)


@login_required
def budget_projection_detail(request, projection_id):
    """
    View detailed information about a budget projection
    """
    projection = get_object_or_404(BudgetEstimateProjection, id=projection_id)
    
    # Check permissions
    if not request.user.is_staff and not request.user.is_superuser:
        if projection.created_by != request.user:
            messages.error(request, "You don't have permission to view this projection.")
            return redirect('finance:budget-projection-approvals')
    
    context = {
        'projection': projection,
        'can_approve': request.user.is_staff or request.user.is_superuser,
    }
    
    return render(request, 'finance/approvals/projection_detail.html', context)


@login_required
def my_budget_projections(request):
    """
    View user's own budget projections
    """
    projections = BudgetEstimateProjection.objects.filter(
        created_by=request.user
    ).order_by('-created_at')
    
    # Apply filters
    status = request.GET.get('status')
    horizon = request.GET.get('horizon')
    
    if status:
        projections = projections.filter(status=status)
    if horizon:
        projections = projections.filter(horizon=horizon)
    
    # Pagination
    paginator = Paginator(projections, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'projections': page_obj,
        'filters': {
            'status': status,
            'horizon': horizon,
        },
        'status_choices': BudgetEstimateProjection.STATUS_CHOICES,
        'horizon_choices': BudgetEstimateProjection.HORIZON_CHOICES,
    }
    
    return render(request, 'finance/approvals/my_projections.html', context)
