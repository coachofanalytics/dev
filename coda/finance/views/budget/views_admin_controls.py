"""
Admin Controls Views for CODA Finance System

Provides administrative interface for managing employee type regulations,
custom compliance thresholds, and override capabilities for the salary-budget
integration system.

Features:
- Employee type regulations management
- Custom compliance threshold configuration
- Override capabilities for special cases
- Admin permission management
- Audit logging and reporting

Created: October 2025
Phase: Advanced Admin Features
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
import json
import logging

from finance.services.admin_controls_service import AdminControlsService
from accounts.models import Department
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger(__name__)


def is_superuser_or_admin(user):
    """Check if user is superuser or has admin permissions."""
    return user.is_superuser or (user.is_staff and user.is_active)


@login_required
@user_passes_test(is_superuser_or_admin)
def admin_controls_dashboard(request):
    """
    Main admin controls dashboard for managing employee regulations and overrides.
    
    Provides comprehensive interface for:
    - Employee type regulations
    - Compliance threshold management
    - Override capabilities
    - Audit logging
    """
    try:
        # Initialize admin service
        admin_service = AdminControlsService()
        
        # Get dashboard data
        dashboard_data = admin_service.get_admin_dashboard_data()
        
        # Get all departments for employee management
        departments = Department.objects.all()
        
        # Get all users for override management
        users = User.objects.filter(is_active=True, is_staff=True)
        
        context = {
            'dashboard_data': dashboard_data,
            'departments': departments,
            'users': users,
            'user': request.user,
            'current_date': timezone.now().date()
        }
        
        return render(request, 'finance/admin/admin_controls_dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Error loading admin controls dashboard: {e}")
        messages.error(request, f"Error loading admin dashboard: {str(e)}")
        return redirect('dashboard:unified_dashboard')


@login_required
@user_passes_test(is_superuser_or_admin)
@require_http_methods(["GET"])
def get_employee_regulations(request):
    """
    Get current employee type regulations and thresholds.
    
    Returns JSON data with all employee type configurations.
    """
    try:
        admin_service = AdminControlsService()
        regulations = admin_service.get_employee_type_regulations()
        
        return JsonResponse({
            'success': True,
            'regulations': regulations
        })
        
    except Exception as e:
        logger.error(f"Error getting employee regulations: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@user_passes_test(is_superuser_or_admin)
@require_http_methods(["POST"])
@csrf_exempt
def update_compliance_threshold(request):
    """
    Update compliance threshold for a specific employee type.
    
    Expects JSON data:
    {
        "employee_type": "full_time",
        "new_threshold": 35.0
    }
    """
    try:
        data = json.loads(request.body)
        employee_type = data.get('employee_type')
        new_threshold = float(data.get('new_threshold', 0))
        
        if not employee_type:
            return JsonResponse({'error': 'Employee type is required'}, status=400)
        
        if not (0 <= new_threshold <= 100):
            return JsonResponse({'error': 'Threshold must be between 0 and 100'}, status=400)
        
        # Update threshold
        admin_service = AdminControlsService()
        result = admin_service.update_employee_type_threshold(
            employee_type, new_threshold, request.user
        )
        
        if 'error' in result:
            return JsonResponse({'error': result['error']}, status=400)
        
        return JsonResponse({
            'success': True,
            'result': result
        })
        
    except ValueError as e:
        return JsonResponse({'error': 'Invalid threshold value'}, status=400)
    except Exception as e:
        logger.error(f"Error updating compliance threshold: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@user_passes_test(is_superuser_or_admin)
@require_http_methods(["POST"])
@csrf_exempt
def create_employee_override(request):
    """
    Create an override for a specific employee.
    
    Expects JSON data:
    {
        "employee_id": 123,
        "override_type": "threshold",
        "override_data": {
            "threshold": 25.0,
            "reason": "Special circumstances",
            "expires_at": "2025-12-31T23:59:59Z"
        }
    }
    """
    try:
        data = json.loads(request.body)
        employee_id = data.get('employee_id')
        override_type = data.get('override_type')
        override_data = data.get('override_data', {})
        
        if not employee_id or not override_type:
            return JsonResponse({'error': 'Employee ID and override type are required'}, status=400)
        
        # Get employee
        employee = get_object_or_404(User, id=employee_id)
        
        # Create override
        admin_service = AdminControlsService()
        result = admin_service.create_employee_override(
            employee, override_type, override_data, request.user
        )
        
        if 'error' in result:
            return JsonResponse({'error': result['error']}, status=400)
        
        return JsonResponse({
            'success': True,
            'result': result
        })
        
    except User.DoesNotExist:
        return JsonResponse({'error': 'Employee not found'}, status=404)
    except Exception as e:
        logger.error(f"Error creating employee override: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@user_passes_test(is_superuser_or_admin)
@require_http_methods(["GET"])
def get_employee_compliance_with_overrides(request, employee_id):
    """
    Get employee compliance status with any applicable overrides applied.
    
    Returns comprehensive compliance information including base status,
    applied overrides, and final determination.
    """
    try:
        # Get employee
        employee = get_object_or_404(User, id=employee_id)
        
        # Get current target month/year
        from management.services.employee_compliance_service import EmployeeComplianceService
        compliance_service = EmployeeComplianceService()
        target_month, target_year = compliance_service.get_current_target_month_year()
        
        # Get compliance with overrides
        admin_service = AdminControlsService()
        compliance_result = admin_service.get_employee_compliance_with_overrides(
            employee, target_month, target_year
        )
        
        if 'error' in compliance_result:
            return JsonResponse({'error': compliance_result['error']}, status=500)
        
        return JsonResponse({
            'success': True,
            'compliance_result': compliance_result
        })
        
    except User.DoesNotExist:
        return JsonResponse({'error': 'Employee not found'}, status=404)
    except Exception as e:
        logger.error(f"Error getting employee compliance with overrides: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@user_passes_test(is_superuser_or_admin)
@require_http_methods(["GET"])
def get_admin_statistics(request):
    """
    Get comprehensive admin statistics for reporting and monitoring.
    
    Returns statistics about employee types, compliance rates, overrides,
    and system usage.
    """
    try:
        admin_service = AdminControlsService()
        dashboard_data = admin_service.get_admin_dashboard_data()
        
        # Get additional statistics
        from finance.services.integrated_budget_service import IntegratedBudgetService
        integrated_service = IntegratedBudgetService()
        
        # Get current target month/year
        from management.services.employee_compliance_service import EmployeeComplianceService
        compliance_service = EmployeeComplianceService()
        target_month, target_year = compliance_service.get_current_target_month_year()
        
        # Get salary data
        salary_data = integrated_service.get_salary_dashboard_data(target_month, target_year)
        
        # Calculate additional statistics
        statistics = {
            'regulations': dashboard_data['regulations'],
            'employee_statistics': {
                'total_employees': salary_data['salary_data']['total_employees'],
                'compliant_employees': salary_data['salary_data']['compliant_count'],
                'non_compliant_employees': salary_data['salary_data']['non_compliant_count'],
                'compliance_rate': (
                    salary_data['salary_data']['compliant_count'] / 
                    salary_data['salary_data']['total_employees'] * 100
                ) if salary_data['salary_data']['total_employees'] > 0 else 0,
                'total_salary_amount': float(salary_data['salary_data']['total_amount'])
            },
            'override_statistics': dashboard_data['override_statistics'],
            'employee_distribution': dashboard_data['employee_distribution'],
            'system_status': dashboard_data['system_status'],
            'generated_at': timezone.now().isoformat()
        }
        
        return JsonResponse({
            'success': True,
            'statistics': statistics
        })
        
    except Exception as e:
        logger.error(f"Error getting admin statistics: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@user_passes_test(is_superuser_or_admin)
@require_http_methods(["GET"])
def get_audit_log(request):
    """
    Get audit log of admin actions for compliance and security monitoring.
    
    Returns chronological log of all administrative actions including
    threshold changes, override creations, and system modifications.
    """
    try:
        # In a real implementation, this would query an audit log database table
        # For now, we'll return a placeholder structure
        
        audit_log = {
            'entries': [
                {
                    'timestamp': timezone.now().isoformat(),
                    'action': 'system_initialization',
                    'user': 'system',
                    'details': 'Admin controls system initialized',
                    'ip_address': request.META.get('REMOTE_ADDR', 'unknown'),
                    'user_agent': request.META.get('HTTP_USER_AGENT', 'unknown')
                }
            ],
            'total_entries': 1,
            'date_range': {
                'start': timezone.now().date().isoformat(),
                'end': timezone.now().date().isoformat()
            }
        }
        
        return JsonResponse({
            'success': True,
            'audit_log': audit_log
        })
        
    except Exception as e:
        logger.error(f"Error getting audit log: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@user_passes_test(is_superuser_or_admin)
@require_http_methods(["POST"])
@csrf_exempt
def export_admin_report(request):
    """
    Export comprehensive admin report with regulations, statistics, and audit log.
    
    Returns JSON data that can be converted to CSV or PDF format.
    """
    try:
        data = json.loads(request.body) if request.body else {}
        report_type = data.get('report_type', 'comprehensive')
        include_audit_log = data.get('include_audit_log', True)
        
        # Get admin statistics
        admin_service = AdminControlsService()
        dashboard_data = admin_service.get_admin_dashboard_data()
        
        # Get salary data
        from finance.services.integrated_budget_service import IntegratedBudgetService
        from management.services.employee_compliance_service import EmployeeComplianceService
        
        integrated_service = IntegratedBudgetService()
        compliance_service = EmployeeComplianceService()
        target_month, target_year = compliance_service.get_current_target_month_year()
        
        salary_data = integrated_service.get_salary_dashboard_data(target_month, target_year)
        
        # Build report
        report = {
            'report_type': report_type,
            'generated_at': timezone.now().isoformat(),
            'generated_by': request.user.username,
            'period': f"{target_month}/{target_year}",
            'regulations': dashboard_data['regulations'],
            'employee_statistics': {
                'total_employees': salary_data['salary_data']['total_employees'],
                'compliant_employees': salary_data['salary_data']['compliant_count'],
                'non_compliant_employees': salary_data['salary_data']['non_compliant_count'],
                'total_salary_amount': float(salary_data['salary_data']['total_amount'])
            },
            'override_statistics': dashboard_data['override_statistics']
        }
        
        if include_audit_log:
            report['audit_log'] = {
                'message': 'Audit log would be included in full implementation'
            }
        
        return JsonResponse({
            'success': True,
            'report': report
        })
        
    except Exception as e:
        logger.error(f"Error exporting admin report: {e}")
        return JsonResponse({'error': str(e)}, status=500)
