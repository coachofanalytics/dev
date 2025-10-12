"""
Budget Approvals - Unified Approval Workflows

This module consolidates all budget-related approval workflows:
1. Budget Request Approvals - Approve/reject budget requests
2. Budget Projection Approvals - Approve/reject budget projections and estimates
3. Compliance Approvals - Enhanced approvals with 33% compliance checking

Consolidated from:
- approval.py (budget request approvals)
- views_approvals.py (projection approvals)
- views_enhanced_approvals.py (compliance-integrated approvals)
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from decimal import Decimal
import json
import csv
import logging

from main.models import Company
from ..core.base import BaseFinanceView, login_required_finance, company_required, json_response, error_json_response
from ...models import Budget, BudgetCategory, BudgetSubCategory, BudgetRequest, ApprovalPolicy, BudgetEstimateProjection
from finance.services.automation_service import ApprovalEngineService
from finance.services.enhanced_budget_service import EnhancedBudgetService
from finance.services.integrated_budget_service import IntegratedBudgetService
from finance.utils.filter_utils import FilterUtils
try:
    from management.services.employee_compliance_service import EmployeeComplianceService
except ImportError:
    EmployeeComplianceService = None

logger = logging.getLogger(__name__)
User = get_user_model()


# ============================================================================
# SECTION 1: BUDGET REQUEST APPROVALS
# Handles approval workflows for budget requests
# ============================================================================

class BudgetApprovalView(BaseFinanceView):
    """Base class for budget approval views."""
    
    def __init__(self):
        super().__init__()


@login_required_finance
@company_required
def budget_approval_dashboard(request, company_slug, company=None):
    """
    Budget approval dashboard showing pending and processed approvals.
    """
    view = BudgetApprovalView()
    
    try:
        if not company:
            company = view.get_company(request, company_slug)
            if not company:
                return redirect('main:dashboard')
        
        user_department = view.get_user_department(request, company)
        
        # Get pending approvals (BudgetRequest doesn't have company field)
        pending_requests = BudgetRequest.objects.filter(
            status__in=['submitted', 'under_review']
        ).select_related('requester', 'budget_category', 'department')
        
        # Get recent approvals
        recent_approvals = BudgetRequest.objects.filter(
            status__in=['approved', 'rejected']
        ).select_related('requester', 'budget_category', 'department').order_by('-updated_at')[:10]
        
        # Get approval statistics
        approval_stats = {
            'pending_count': pending_requests.count(),
            'approved_count': BudgetRequest.objects.filter(status='approved').count(),
            'rejected_count': BudgetRequest.objects.filter(status='rejected').count(),
            'total_requests': BudgetRequest.objects.count(),
        }
        
        context = {
            'company': company,
            'user_department': user_department,
            'pending_requests': pending_requests,
            'recent_approvals': recent_approvals,
            'approval_stats': approval_stats,
        }
        
        return render(request, 'finance/budgets/approval_dashboard.html', context)
    
    except Exception as e:
        view.handle_error(request, e, "Error loading budget approval dashboard")
        return redirect('finance:unified-budget-dashboard', company_slug=company_slug)


@login_required_finance
@company_required
def budget_approval_detail(request, company_slug, request_id, company=None):
    """
    Detailed view of a budget approval request.
    """
    view = BudgetApprovalView()
    
    try:
        if not company:
            company = view.get_company(request, company_slug)
            if not company:
                return redirect('main:dashboard')
        
        # Get budget request
        budget_request = get_object_or_404(
            BudgetRequest,
            id=request_id,
            company=company
        )
        
        # Get related budgets
        related_budgets = Budget.objects.filter(
            company=company,
            category=budget_request.category
        ).select_related('subcategory', 'budget_lead')
        
        context = {
            'company': company,
            'budget_request': budget_request,
            'related_budgets': related_budgets,
        }
        
        return render(request, 'finance/budgets/approval_detail.html', context)
    
    except Exception as e:
        view.handle_error(request, e, "Error loading budget approval detail")
        return redirect('finance:budget-approval-dashboard', company_slug=company_slug)


@require_http_methods(["POST"])
@login_required_finance
@company_required
def approve_budget_request(request, company_slug, request_id, company=None):
    """
    Approve a budget request.
    """
    view = BudgetApprovalView()
    
    try:
        if not company:
            company = view.get_company(request, company_slug)
            if not company:
                return error_json_response("Company not found", 404)
        
        # Get budget request
        budget_request = get_object_or_404(
            BudgetRequest,
            id=request_id,
            company=company
        )
        
        # Check if user has permission to approve
        if not view._can_approve_budget(request.user, budget_request):
            return error_json_response("Insufficient permissions to approve this request", 403)
        
        # Approve the request
        budget_request.approve(request.user)
        
        return json_response({
            'success': True,
            'message': 'Budget request approved successfully',
            'request_id': budget_request.id,
            'status': budget_request.status
        })
    
    except Exception as e:
        view.log_error("Error approving budget request", e)
        return error_json_response("Internal server error", 500)


@require_http_methods(["POST"])
@login_required_finance
@company_required
def reject_budget_request(request, company_slug, request_id, company=None):
    """
    Reject a budget request.
    """
    view = BudgetApprovalView()
    
    try:
        if not company:
            company = view.get_company(request, company_slug)
            if not company:
                return error_json_response("Company not found", 404)
        
        # Get budget request
        budget_request = get_object_or_404(
            BudgetRequest,
            id=request_id,
            company=company
        )
        
        # Check if user has permission to reject
        if not view._can_approve_budget(request.user, budget_request):
            return error_json_response("Insufficient permissions to reject this request", 403)
        
        # Get rejection reason
        rejection_reason = request.POST.get('rejection_reason', 'No reason provided')
        
        # Reject the request
        budget_request.reject(request.user, rejection_reason)
        
        return json_response({
            'success': True,
            'message': 'Budget request rejected successfully',
            'request_id': budget_request.id,
            'status': budget_request.status
        })
    
    except Exception as e:
        view.log_error("Error rejecting budget request", e)
        return error_json_response("Internal server error", 500)


def _can_approve_budget(self, user, budget_request):
    """Check if user can approve this budget request."""
    try:
        # Check if user is in the same department or is a manager
        if hasattr(user, 'profile') and user.profile.department:
            user_department = user.profile.department
            if budget_request.department == user_department:
                return True
        
        # Check if user is a manager or admin
        if user.is_staff or user.is_superuser:
            return True
        
        # Check approval policies
        approval_policies = ApprovalPolicy.objects.filter(
            company=budget_request.company,
            category=budget_request.category
        )
        
        for policy in approval_policies:
            if policy.can_approve(user, budget_request.amount):
                return True
        
        return False
    
    except Exception as e:
        self.log_error("Error checking approval permissions", e)
        return False


# Add method to the class
BudgetApprovalView._can_approve_budget = _can_approve_budget


@require_http_methods(["GET"])
@login_required_finance
def budget_approval_api(request, company_slug):
    """
    API endpoint for budget approval data.
    """
    view = BudgetApprovalView()
    
    try:
        company = view.get_company(request, company_slug)
        if not company:
            return error_json_response("Company not found", 404)
        
        # Get approval data
        pending_requests = BudgetRequest.objects.filter(
            company=company,
            status='pending'
        ).values('id', 'title', 'amount', 'category__name', 'requested_by__username', 'created_at')
        
        approval_stats = {
            'pending_count': BudgetRequest.objects.filter(company=company, status='pending').count(),
            'approved_count': BudgetRequest.objects.filter(company=company, status='approved').count(),
            'rejected_count': BudgetRequest.objects.filter(company=company, status='rejected').count(),
        }
        
        data = {
            'pending_requests': list(pending_requests),
            'approval_stats': approval_stats,
        }
        
        return json_response(data)
    
    except Exception as e:
        view.log_error("Error in budget approval API", e)
        return error_json_response("Internal server error", 500)


# ============================================================================
# SECTION 2: BUDGET PROJECTION APPROVALS
# Handles approval workflows for budget projections and estimates
# ============================================================================

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
                    
                    messages.success(request, "Budget projection #{} approved successfully.".format(projection.id))
                    
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
                        print("Failed to send approval email: {}".format(e))
                    
                elif action == 'reject':
                    projection.status = 'rejected'
                    projection.reviewed_by = request.user
                    projection.reviewed_at = timezone.now()
                    projection.review_notes = comments
                    projection.save()
                    
                    messages.success(request, "Budget projection #{} rejected.".format(projection.id))
                    
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
                        print("Failed to send rejection email: {}".format(e))
                
                return redirect('finance:budget-projection-approvals')
                
        except Exception as e:
            messages.error(request, "Error processing approval: {}".format(str(e)))
    
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
        'status_choices': BudgetEstimateProjection.STATUS_CHOICES if hasattr(BudgetEstimateProjection, 'STATUS_CHOICES') else [],
        'horizon_choices': BudgetEstimateProjection.HORIZON_CHOICES if hasattr(BudgetEstimateProjection, 'HORIZON_CHOICES') else [],
    }
    
    return render(request, 'finance/approvals/my_projections.html', context)


# ============================================================================
# SECTION 3: COMPLIANCE-INTEGRATED APPROVALS
# Enhanced approvals with 33% completion rule enforcement
# ============================================================================

@login_required
def enhanced_budget_projection_approvals(request):
    """
    Enhanced budget approval view with compliance checking.
    """
    user = request.user
    
    # Check permissions
    if not user.is_staff and not user.is_superuser:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    # Initialize services
    if not EmployeeComplianceService:
        messages.warning(request, "Compliance service not available. Using basic approval view.")
        return redirect('finance:budget-projection-approvals')
    
    compliance_service = EmployeeComplianceService()
    budget_service = EnhancedBudgetService()
    integrated_service = IntegratedBudgetService()
    
    # Get current compliance status
    compliance_summary = compliance_service.get_compliance_summary()
    
    # Get current target month/year for salary calculations
    target_month, target_year = compliance_service.get_current_target_month_year()
    
    # Get monthly budget summary (salaries + budget items)
    monthly_budget_summary = integrated_service.get_monthly_budget_summary(target_month, target_year)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'check_compliance':
            # Check compliance for all employees
            target_month = compliance_summary['target_month']
            target_year = compliance_summary['target_year']
            
            # Get compliance report by department
            departments = compliance_service.get_company_compliance_report(target_month, target_year)
            
            context = {
                'compliance_reports': departments['department_reports'],
                'company_summary': departments,
                'target_month': target_month,
                'target_year': target_year,
                'is_rule_active': compliance_summary['is_rule_active'],
                'current_date': compliance_summary['current_date'],
                'threshold': compliance_summary['threshold']
            }
            
            return render(request, 'finance/approvals/compliance_report.html', context)
        
        elif action == 'submit_compliant_only':
            # Submit budget with only compliant employees
            budget_data = {
                'company': request.POST.get('company'),
                'department': request.POST.get('department'),
                'horizon': request.POST.get('horizon', 'monthly'),
                'method': request.POST.get('method', 'average'),
                'estimates': json.loads(request.POST.get('estimates', '{}'))
            }
            
            result = budget_service.prepare_budget_submission_with_compliance(budget_data, user)
            
            if result['success']:
                messages.success(
                    request,
                    result['message']
                )
            else:
                messages.error(request, result['message'])
            
            return redirect('finance:enhanced-budget-approvals')
        
        elif action == 'send_notifications':
            # Send notifications to non-compliant employees
            target_month = compliance_summary['target_month']
            target_year = compliance_summary['target_year']
            
            result = budget_service.send_bulk_compliance_notifications(target_month, target_year)
            
            if result['success']:
                messages.success(request, result['message'])
            else:
                messages.error(request, result['message'])
            
            return redirect('finance:enhanced-budget-approvals')
    
    # Get existing projections (exclude zero budgets)
    projections = BudgetEstimateProjection.objects.filter(
        status='submitted',
        total_estimate__gt=0  # Only include budgets with amount > $0
    ).select_related('company', 'department', 'created_by').order_by('-submitted_at')
    
    # Apply pagination
    paginator = Paginator(projections, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Ensure all projections have created_by field set to avoid None errors
    for projection in page_obj.object_list:
        if not projection.created_by:
            # Set a default user or handle appropriately
            projection.created_by = user
    
    context = {
        'page_obj': page_obj,
        'compliance_summary': compliance_summary,
        'monthly_budget_summary': monthly_budget_summary,
        'target_month': target_month,
        'target_year': target_year,
        'is_rule_active': compliance_summary['is_rule_active'],
        'current_date': compliance_summary['current_date'],
        'user': user,
    }
    
    return render(request, 'finance/approvals/enhanced_approvals.html', context)


@login_required
def compliance_report_dashboard(request):
    """
    Comprehensive compliance report dashboard.
    """
    user = request.user
    
    # Check permissions
    if not user.is_staff and not user.is_superuser:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    # Initialize services
    if not EmployeeComplianceService:
        messages.warning(request, "Compliance service not available.")
        return redirect('finance:budget-dashboard', company_slug='coda')
    
    compliance_service = EmployeeComplianceService()
    target_month, target_year = compliance_service.get_current_target_month_year()
    
    # Get company-wide compliance report
    company_report = compliance_service.get_company_compliance_report(target_month, target_year)
    
    # Get non-compliant employees for quick overview
    non_compliant_employees = compliance_service.get_non_compliant_employees(target_month, target_year)
    
    # Get compliant employees
    compliant_employees = compliance_service.get_compliant_employees(target_month, target_year)
    
    context = {
        'company_report': company_report,
        'non_compliant_employees': non_compliant_employees[:10],  # Show first 10
        'compliant_employees': compliant_employees[:10],  # Show first 10
        'target_month': target_month,
        'target_year': target_year,
        'is_rule_active': compliance_service.is_compliance_rule_active(),
        'current_date': timezone.now(),
        'user': user,
    }
    
    return render(request, 'finance/approvals/compliance_dashboard.html', context)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def send_compliance_notifications(request):
    """
    Send compliance notifications to non-compliant employees.
    """
    try:
        data = json.loads(request.body)
        action = data.get('action')
        
        if action == 'send_notifications':
            if not EmployeeComplianceService:
                return JsonResponse({'success': False, 'error': 'Compliance service not available'})
            
            compliance_service = EmployeeComplianceService()
            budget_service = EnhancedBudgetService()
            
            target_month, target_year = compliance_service.get_current_target_month_year()
            result = budget_service.send_bulk_compliance_notifications(target_month, target_year)
            
            return JsonResponse(result)
        
        return JsonResponse({'success': False, 'error': 'Invalid action'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def individual_compliance_detail(request, employee_id):
    """
    Detailed compliance view for individual employee.
    """
    user = request.user
    
    # Check permissions
    if not user.is_staff and not user.is_superuser:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    if not EmployeeComplianceService:
        messages.warning(request, "Compliance service not available.")
        return redirect('finance:compliance-dashboard')
    
    from accounts.models import CustomerUser
    
    try:
        employee = get_object_or_404(CustomerUser, id=employee_id)
        compliance_service = EmployeeComplianceService()
        target_month, target_year = compliance_service.get_current_target_month_year()
        
        # Get detailed compliance data
        compliance_data = compliance_service.check_33_percent_compliance(
            employee, target_month, target_year
        )
        
        # Get employee's task history for the month
        from management.models import TaskHistory
        task_history = TaskHistory.objects.filter(
            employee=employee,
            daf_date__month=target_month,
            daf_date__year=target_year
        ).order_by('-submission')
        
        context = {
            'employee': employee,
            'compliance_data': compliance_data,
            'task_history': task_history,
            'target_month': target_month,
            'target_year': target_year,
            'is_rule_active': compliance_service.is_compliance_rule_active()
        }
        
        return render(request, 'finance/approvals/individual_compliance.html', context)
        
    except Exception as e:
        messages.error(request, "Error loading compliance details: {}".format(str(e)))
        return redirect('finance:compliance-dashboard')


@login_required
def department_compliance_detail(request, department_id):
    """
    Detailed compliance view for specific department.
    """
    user = request.user
    
    # Check permissions
    if not user.is_staff and not user.is_superuser:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    if not EmployeeComplianceService:
        messages.warning(request, "Compliance service not available.")
        return redirect('finance:compliance-dashboard')
    
    from accounts.models import Department
    
    try:
        department = get_object_or_404(Department, id=department_id)
        compliance_service = EmployeeComplianceService()
        target_month, target_year = compliance_service.get_current_target_month_year()
        
        # Get department compliance report
        department_report = compliance_service.get_department_compliance_report(
            department, target_month, target_year
        )
        
        context = {
            'department_report': department_report,
            'target_month': target_month,
            'target_year': target_year,
            'is_rule_active': compliance_service.is_compliance_rule_active()
        }
        
        return render(request, 'finance/approvals/department_compliance.html', context)
        
    except Exception as e:
        messages.error(request, "Error loading department compliance: {}".format(str(e)))
        return redirect('finance:compliance-dashboard')


@login_required
def budget_compliance_integration(request, budget_id):
    """
    Integration view showing compliance data for specific budget.
    """
    user = request.user
    
    # Check permissions
    if not user.is_staff and not user.is_superuser:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    try:
        budget = get_object_or_404(BudgetEstimateProjection, id=budget_id)
        budget_service = EnhancedBudgetService()
        
        # Get compliance report for this budget
        compliance_report = budget_service.get_compliance_report_for_budget(budget_id)
        
        context = {
            'budget': budget,
            'compliance_report': compliance_report
        }
        
        return render(request, 'finance/approvals/budget_compliance.html', context)
        
    except Exception as e:
        messages.error(request, "Error loading budget compliance: {}".format(str(e)))
        return redirect('finance:enhanced-budget-approvals')


@login_required
def compliance_export(request):
    """
    Export compliance data to CSV/Excel.
    """
    user = request.user
    
    # Check permissions
    if not user.is_staff and not user.is_superuser:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    if not EmployeeComplianceService:
        messages.warning(request, "Compliance service not available.")
        return redirect('finance:compliance-dashboard')
    
    try:
        compliance_service = EmployeeComplianceService()
        target_month, target_year = compliance_service.get_current_target_month_year()
        
        # Get company-wide report
        company_report = compliance_service.get_company_compliance_report(target_month, target_year)
        
        # Prepare data for export
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="compliance_report_{}_{}.csv"'.format(target_month, target_year)
        
        writer = csv.writer(response)
        writer.writerow([
            'Department', 'Employee Name', 'Username', 'Email', 
            'Completion Rate (%)', 'Total Tasks', 'Completed Tasks', 
            'Required Tasks', 'Missing Tasks', 'Compliant'
        ])
        
        for dept_report in company_report['department_reports']:
            for emp_data in dept_report['employee_data']:
                compliance = emp_data['compliance']
                writer.writerow([
                    dept_report['department_name'],
                    compliance['employee_name'],
                    compliance['employee_username'],
                    compliance['employee_email'],
                    compliance['completion_rate'],
                    compliance['total_tasks'],
                    compliance['completed_tasks'],
                    compliance['required_tasks'],
                    compliance['missing_tasks'],
                    'Yes' if compliance['is_compliant'] else 'No'
                ])
        
        return response
        
    except Exception as e:
        messages.error(request, "Error exporting compliance data: {}".format(str(e)))
        return redirect('finance:compliance-dashboard')

