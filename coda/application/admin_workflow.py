"""
Admin views for managing application workflows
Provides interface for admins to review and approve/reject applications
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone

from .models import ApplicationWorkflow, WorkflowStatusLog
from .services import workflow_service
from shared_core.users import CustomerUser


def is_staff_user(user):
    """Check if user is staff"""
    return user.is_staff


@login_required
@user_passes_test(is_staff_user)
def workflow_dashboard(request):
    """
    Dashboard for admins to view all application workflows
    """
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    
    # Base queryset
    workflows = ApplicationWorkflow.objects.select_related('applicant').order_by('-applied_date')
    
    # Apply filters
    if status_filter:
        workflows = workflows.filter(status=status_filter)
    
    if search_query:
        workflows = workflows.filter(
            Q(applicant__username__icontains=search_query) |
            Q(applicant__first_name__icontains=search_query) |
            Q(applicant__last_name__icontains=search_query) |
            Q(applicant__email__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(workflows, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    stats = {
        'total': ApplicationWorkflow.objects.count(),
        'pending_review': ApplicationWorkflow.objects.filter(
            status=ApplicationWorkflow.WorkflowStatus.FINAL_REVIEW
        ).count(),
        'approved_today': ApplicationWorkflow.objects.filter(
            status=ApplicationWorkflow.WorkflowStatus.EMPLOYEE,
            completed_date__date=timezone.now().date()
        ).count(),
        'rejected_today': ApplicationWorkflow.objects.filter(
            status=ApplicationWorkflow.WorkflowStatus.REJECTED,
            completed_date__date=timezone.now().date()
        ).count(),
    }
    
    context = {
        'page_obj': page_obj,
        'stats': stats,
        'status_choices': ApplicationWorkflow.WorkflowStatus.choices,
        'current_status': status_filter,
        'search_query': search_query,
    }
    
    return render(request, 'application/admin/workflow_dashboard.html', context)


@login_required
@user_passes_test(is_staff_user)
def workflow_detail(request, workflow_id):
    """
    Detailed view of a specific workflow
    """
    workflow = get_object_or_404(
        ApplicationWorkflow.objects.select_related('applicant', 'reviewed_by'),
        id=workflow_id
    )
    
    # Get status logs
    status_logs = WorkflowStatusLog.objects.filter(
        workflow=workflow
    ).order_by('-changed_at')
    
    # Get applicant's ratings/scores
    ratings = workflow.applicant.rating_empname.all().order_by('-rating_date')
    
    context = {
        'workflow': workflow,
        'status_logs': status_logs,
        'ratings': ratings,
    }
    
    return render(request, 'application/admin/workflow_detail.html', context)


@login_required
@user_passes_test(is_staff_user)
@require_POST
def approve_application(request, workflow_id):
    """
    Approve an application for promotion
    """
    workflow = get_object_or_404(ApplicationWorkflow, id=workflow_id)
    notes = request.POST.get('notes', '')
    
    try:
        success = workflow_service.admin_approve(
            workflow.applicant,
            request.user,
            notes
        )
        
        if success:
            messages.success(
                request,
                f"Application for {workflow.applicant.username} has been approved and promoted to employee."
            )
        else:
            messages.error(request, "Failed to approve application.")
            
    except Exception as e:
        messages.error(request, f"Error approving application: {str(e)}")
    
    return redirect('application:workflow_detail', workflow_id=workflow_id)


@login_required
@user_passes_test(is_staff_user)
@require_POST
def reject_application(request, workflow_id):
    """
    Reject an application
    """
    workflow = get_object_or_404(ApplicationWorkflow, id=workflow_id)
    notes = request.POST.get('notes', '')
    
    if not notes:
        messages.error(request, "Rejection reason is required.")
        return redirect('application:workflow_detail', workflow_id=workflow_id)
    
    try:
        success = workflow_service.admin_reject(
            workflow.applicant,
            request.user,
            notes
        )
        
        if success:
            messages.success(
                request,
                f"Application for {workflow.applicant.username} has been rejected."
            )
        else:
            messages.error(request, "Failed to reject application.")
            
    except Exception as e:
        messages.error(request, f"Error rejecting application: {str(e)}")
    
    return redirect('application:workflow_detail', workflow_id=workflow_id)


@login_required
@user_passes_test(is_staff_user)
def bulk_approve(request):
    """
    Bulk approve multiple applications
    """
    if request.method == 'POST':
        workflow_ids = request.POST.getlist('workflow_ids')
        notes = request.POST.get('notes', 'Bulk approval')
        
        approved_count = 0
        failed_count = 0
        
        for workflow_id in workflow_ids:
            try:
                workflow = ApplicationWorkflow.objects.get(id=workflow_id)
                success = workflow_service.admin_approve(
                    workflow.applicant,
                    request.user,
                    f"{notes} (Bulk approval)"
                )
                if success:
                    approved_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                failed_count += 1
        
        if approved_count > 0:
            messages.success(request, f"Successfully approved {approved_count} applications.")
        if failed_count > 0:
            messages.warning(request, f"Failed to approve {failed_count} applications.")
    
    return redirect('application:workflow_dashboard')


@login_required
@user_passes_test(is_staff_user)
def workflow_analytics(request):
    """
    Analytics view for workflow performance
    """
    # Get date range
    from_date = request.GET.get('from_date', '')
    to_date = request.GET.get('to_date', '')
    
    # Base queryset
    workflows = ApplicationWorkflow.objects.all()
    
    if from_date:
        workflows = workflows.filter(applied_date__date__gte=from_date)
    if to_date:
        workflows = workflows.filter(applied_date__date__lte=to_date)
    
    # Analytics data
    analytics = {
        'total_applications': workflows.count(),
        'status_distribution': {},
        'promotion_types': {},
        'average_duration': 0,
        'success_rate': 0,
    }
    
    # Status distribution
    for status, _ in ApplicationWorkflow.WorkflowStatus.choices:
        count = workflows.filter(status=status).count()
        analytics['status_distribution'][status] = count
    
    # Promotion types
    for ptype, _ in ApplicationWorkflow.PromotionType.choices:
        count = workflows.filter(promotion_type=ptype).count()
        analytics['promotion_types'][ptype] = count
    
    # Average duration
    completed_workflows = workflows.filter(
        completed_date__isnull=False
    )
    if completed_workflows.exists():
        total_days = sum(
            (w.completed_date - w.applied_date).days 
            for w in completed_workflows
        )
        analytics['average_duration'] = total_days / completed_workflows.count()
    
    # Success rate
    successful = workflows.filter(
        status=ApplicationWorkflow.WorkflowStatus.EMPLOYEE
    ).count()
    if workflows.count() > 0:
        analytics['success_rate'] = (successful / workflows.count()) * 100
    
    context = {
        'analytics': analytics,
        'from_date': from_date,
        'to_date': to_date,
    }
    
    return render(request, 'application/admin/workflow_analytics.html', context)


@login_required
@user_passes_test(is_staff_user)
def ajax_workflow_status(request, workflow_id):
    """
    AJAX endpoint to get workflow status
    """
    try:
        workflow = ApplicationWorkflow.objects.get(id=workflow_id)
        return JsonResponse({
            'status': workflow.status,
            'status_display': workflow.get_status_display(),
            'is_eligible': workflow.is_eligible_for_promotion,
            'skills_score': workflow.skills_assessment_score,
            'min_skills_score': workflow.min_skills_score,
            'documents_completed': workflow.documents_completed,
            'interview_completed': workflow.interview_completed,
            'admin_approval': workflow.admin_approval,
        })
    except ApplicationWorkflow.DoesNotExist:
        return JsonResponse({'error': 'Workflow not found'}, status=404)


@login_required
@user_passes_test(is_staff_user)
def create_workflow_manual(request):
    """
    Manually create workflow for existing applicant
    """
    if request.method == 'POST':
        applicant_username = request.POST.get('applicant_username')
        
        try:
            applicant = CustomerUser.objects.get(
                username=applicant_username,
                category=1,  # Applicant category
                is_active=True
            )
            
            workflow = workflow_service.create_workflow(applicant)
            
            if workflow:
                messages.success(
                    request,
                    f"Workflow created for {applicant.username}"
                )
            else:
                messages.error(request, "Failed to create workflow.")
                
        except CustomerUser.DoesNotExist:
            messages.error(request, "Applicant not found.")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
    
    return redirect('application:workflow_dashboard')



