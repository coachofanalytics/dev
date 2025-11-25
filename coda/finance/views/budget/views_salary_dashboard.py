"""
Salary Dashboard Views for CODA Finance System

Provides comprehensive salary management and reporting interface integrating
with the 33% compliance rule and budget approval workflow.

Features:
- Detailed employee salary breakdowns
- Compliance status monitoring
- Salary approval workflow
- Integration with budget system

Created: October 2025
Phase: Budget-Salary Integration
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
import json
import logging

from shared_core.users import Department
from finance.services.integrated_budget_service import IntegratedBudgetService
from management.services.employee_compliance_service import EmployeeComplianceService

logger = logging.getLogger(__name__)


@login_required
def salary_dashboard(request):
    """
    Comprehensive salary dashboard showing all employee salary information.
    
    Displays:
    - Compliant vs non-compliant employees
    - Salary breakdowns by department
    - Compliance statistics
    - Integration with budget approval workflow
    """
    user = request.user
    
    # Check permissions
    if not user.is_staff and not user.is_superuser:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard:unified_dashboard')
    
    # Get current target month/year (last month for salary calculation)
    compliance_service = EmployeeComplianceService()
    target_month, target_year = compliance_service.get_current_target_month_year()
    
    # Get department filter
    departments = Department.objects.all()
    selected_department = None
    
    if request.GET.get('department_id'):
        try:
            selected_department = Department.objects.get(id=request.GET.get('department_id'))
        except Department.DoesNotExist:
            pass
    
    # Get salary data
    integrated_service = IntegratedBudgetService()
    salary_data = integrated_service.get_salary_dashboard_data(
        target_month, target_year, selected_department
    )
    
    # Get monthly budget summary
    budget_summary = integrated_service.get_monthly_budget_summary(
        target_month, target_year, selected_department
    )
    
    context = {
        'salary_data': salary_data,
        'budget_summary': budget_summary,
        'departments': departments,
        'selected_department': selected_department,
        'target_month': target_month,
        'target_year': target_year,
        'user': user,
        'current_date': timezone.now().date()
    }
    
    return render(request, 'finance/salary/salary_dashboard.html', context)


@login_required
def employee_salary_detail(request, employee_id):
    """
    Detailed salary breakdown for a specific employee.
    
    Shows:
    - Individual task breakdown
    - Salary calculations
    - Compliance status
    - Historical data
    """
    user = request.user
    
    # Check permissions
    if not user.is_staff and not user.is_superuser:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard:unified_dashboard')
    
    # Get employee
    from django.contrib.auth import get_user_model
    User = get_user_model()
    employee = get_object_or_404(User, id=employee_id)
    
    # Get current target month/year
    compliance_service = EmployeeComplianceService()
    target_month, target_year = compliance_service.get_current_target_month_year()
    
    # Get detailed salary information
    integrated_service = IntegratedBudgetService()
    salary_details = integrated_service.get_employee_salary_details(
        employee, target_month, target_year
    )
    
    context = {
        'employee': employee,
        'salary_details': salary_details,
        'target_month': target_month,
        'target_year': target_year,
        'user': user,
        'current_date': timezone.now().date()
    }
    
    return render(request, 'finance/salary/employee_salary_detail.html', context)


@login_required
@require_http_methods(["GET"])
def salary_compliance_report(request):
    """
    Generate salary compliance report for budget approval workflow.
    
    Returns JSON data for AJAX requests showing compliance status.
    """
    user = request.user
    
    # Check permissions
    if not user.is_staff and not user.is_superuser:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        # Get parameters
        target_month = int(request.GET.get('month', 0))
        target_year = int(request.GET.get('year', 0))
        department_id = request.GET.get('department_id')
        
        if not target_month or not target_year:
            compliance_service = EmployeeComplianceService()
            target_month, target_year = compliance_service.get_current_target_month_year()
        
        # Get department
        selected_department = None
        if department_id:
            try:
                selected_department = Department.objects.get(id=department_id)
            except Department.DoesNotExist:
                pass
        
        # Get salary data
        integrated_service = IntegratedBudgetService()
        salary_data = integrated_service.get_salary_dashboard_data(
            target_month, target_year, selected_department
        )
        
        # Get budget summary
        budget_summary = integrated_service.get_monthly_budget_summary(
            target_month, target_year, selected_department
        )
        
        return JsonResponse({
            'success': True,
            'salary_data': salary_data,
            'budget_summary': budget_summary,
            'period': f"{target_month}/{target_year}",
            'department': selected_department.name if selected_department else 'All Departments'
        })
        
    except Exception as e:
        logger.error(f"Error generating salary compliance report: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def update_compliance_status(request):
    """
    Update compliance status for all employees.
    
    This endpoint can be called to refresh compliance data.
    """
    user = request.user
    
    # Check permissions
    if not user.is_staff and not user.is_superuser:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        data = json.loads(request.body)
        target_month = int(data.get('month', 0))
        target_year = int(data.get('year', 0))
        
        if not target_month or not target_year:
            compliance_service = EmployeeComplianceService()
            target_month, target_year = compliance_service.get_current_target_month_year()
        
        # Update compliance status
        integrated_service = IntegratedBudgetService()
        compliance_update = integrated_service.update_compliance_status(
            target_month, target_year
        )
        
        return JsonResponse({
            'success': True,
            'compliance_update': compliance_update,
            'updated_at': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error updating compliance status: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def salary_export(request):
    """
    Export salary data for budget approval workflow.
    
    Returns comprehensive salary data that can be integrated with budget approvals.
    """
    user = request.user
    
    # Check permissions
    if not user.is_staff and not user.is_superuser:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        # Get parameters
        target_month = int(request.GET.get('month', 0))
        target_year = int(request.GET.get('year', 0))
        department_id = request.GET.get('department_id')
        export_format = request.GET.get('format', 'json')  # json, csv
        
        if not target_month or not target_year:
            compliance_service = EmployeeComplianceService()
            target_month, target_year = compliance_service.get_current_target_month_year()
        
        # Get department
        selected_department = None
        if department_id:
            try:
                selected_department = Department.objects.get(id=department_id)
            except Department.DoesNotExist:
                pass
        
        # Get comprehensive salary data
        integrated_service = IntegratedBudgetService()
        salary_data = integrated_service.get_salary_dashboard_data(
            target_month, target_year, selected_department
        )
        
        budget_summary = integrated_service.get_monthly_budget_summary(
            target_month, target_year, selected_department
        )
        
        if export_format == 'csv':
            # TODO: Implement CSV export
            return JsonResponse({'error': 'CSV export not yet implemented'}, status=501)
        
        # Return JSON export
        return JsonResponse({
            'success': True,
            'export_data': {
                'period': f"{target_month}/{target_year}",
                'department': selected_department.name if selected_department else 'All Departments',
                'salary_data': salary_data,
                'budget_summary': budget_summary,
                'exported_at': timezone.now().isoformat(),
                'exported_by': user.username
            }
        })
        
    except Exception as e:
        logger.error(f"Error exporting salary data: {e}")
        return JsonResponse({'error': str(e)}, status=500)

