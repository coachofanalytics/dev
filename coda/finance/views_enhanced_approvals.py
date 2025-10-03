"""
Enhanced Budget Approval Views with 33% Compliance Checking

Integrates employee compliance validation with budget approval workflow.
Provides comprehensive compliance reporting and management interface.

Business Rule: 33% completion rule enforcement at budget submission level.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db import transaction
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
import json

from finance.models import BudgetEstimateProjection, ApprovalPolicy, BudgetRequest
from finance.services.enhanced_budget_service import EnhancedBudgetService
from finance.services.automation_service import ApprovalEngineService
from finance.utils.filter_utils import FilterUtils
from management.services.employee_compliance_service import EmployeeComplianceService


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
    compliance_service = EmployeeComplianceService()
    budget_service = EnhancedBudgetService()
    
    # Get current compliance status
    compliance_summary = compliance_service.get_compliance_summary()
    
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
    
    # Get existing projections
    projections = BudgetEstimateProjection.objects.filter(
        status='submitted'
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
        'is_rule_active': compliance_summary['is_rule_active'],
        'current_date': compliance_summary['current_date'],
        'user': user,  # Add user to context
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
        'user': user,  # Add user to context
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
        messages.error(request, f"Error loading compliance details: {str(e)}")
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
        messages.error(request, f"Error loading department compliance: {str(e)}")
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
        messages.error(request, f"Error loading budget compliance: {str(e)}")
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
    
    try:
        compliance_service = EmployeeComplianceService()
        target_month, target_year = compliance_service.get_current_target_month_year()
        
        # Get company-wide report
        company_report = compliance_service.get_company_compliance_report(target_month, target_year)
        
        # Prepare data for export
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="compliance_report_{target_month}_{target_year}.csv"'
        
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
        messages.error(request, f"Error exporting compliance data: {str(e)}")
        return redirect('finance:compliance-dashboard')
