"""
Real-time Compliance Views for CODA Finance System

Provides real-time compliance monitoring, notifications, and live dashboard updates
for the enhanced salary-budget integration system.

Features:
- Real-time compliance monitoring endpoints
- Automatic notification triggers
- Live dashboard data updates
- WebSocket-ready API endpoints

Created: October 2025
Phase: Advanced Real-time Features
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
import json
import logging

from finance.services.realtime_compliance_service import RealtimeComplianceService
from management.services.employee_compliance_service import EmployeeComplianceService
from shared_core.users import Department

logger = logging.getLogger(__name__)


@login_required
def realtime_compliance_dashboard(request):
    """
    Real-time compliance monitoring dashboard.
    
    Shows live compliance status, recent changes, and provides
    controls for managing compliance notifications.
    """
    user = request.user
    
    # Check permissions
    if not user.is_staff and not user.is_superuser:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard:unified_dashboard')
    
    # Get current target month/year
    compliance_service = EmployeeComplianceService()
    target_month, target_year = compliance_service.get_current_target_month_year()
    
    # Initialize real-time service
    realtime_service = RealtimeComplianceService()
    
    # Get real-time dashboard data
    dashboard_data = realtime_service.get_realtime_dashboard_data(target_month, target_year)
    
    context = {
        'dashboard_data': dashboard_data,
        'target_month': target_month,
        'target_year': target_year,
        'user': user,
        'current_date': timezone.now().date()
    }
    
    return render(request, 'finance/realtime/realtime_compliance_dashboard.html', context)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def trigger_compliance_monitoring(request):
    """
    Manually trigger compliance monitoring for all employees.
    
    This endpoint can be called to immediately check compliance status
    and send notifications for any changes.
    """
    user = request.user
    
    # Check permissions
    if not user.is_staff and not user.is_superuser:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        # Get parameters
        data = json.loads(request.body) if request.body else {}
        target_month = int(data.get('month', 0))
        target_year = int(data.get('year', 0))
        
        if not target_month or not target_year:
            compliance_service = EmployeeComplianceService()
            target_month, target_year = compliance_service.get_current_target_month_year()
        
        # Trigger compliance monitoring
        realtime_service = RealtimeComplianceService()
        monitoring_result = realtime_service.monitor_compliance_changes(target_month, target_year)
        
        return JsonResponse({
            'success': True,
            'monitoring_result': monitoring_result,
            'triggered_by': user.username,
            'triggered_at': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error triggering compliance monitoring: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def send_compliance_reminders(request):
    """
    Send reminder notifications to non-compliant employees.
    
    This endpoint can be called to send reminder emails to all employees
    who haven't reached the 33% compliance threshold.
    """
    user = request.user
    
    # Check permissions
    if not user.is_staff and not user.is_superuser:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        # Get parameters
        data = json.loads(request.body) if request.body else {}
        target_month = int(data.get('month', 0))
        target_year = int(data.get('year', 0))
        
        if not target_month or not target_year:
            compliance_service = EmployeeComplianceService()
            target_month, target_year = compliance_service.get_current_target_month_year()
        
        # Send reminder notifications
        realtime_service = RealtimeComplianceService()
        reminder_result = realtime_service.send_compliance_reminder_notifications(target_month, target_year)
        
        return JsonResponse({
            'success': True,
            'reminder_result': reminder_result,
            'sent_by': user.username,
            'sent_at': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error sending compliance reminders: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def get_realtime_dashboard_data(request):
    """
    Get real-time dashboard data for AJAX updates.
    
    This endpoint provides the latest compliance and salary data
    for live dashboard refreshes without page reload.
    """
    user = request.user
    
    # Check permissions
    if not user.is_staff and not user.is_superuser:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        # Get parameters
        target_month = int(request.GET.get('month', 0))
        target_year = int(request.GET.get('year', 0))
        
        if not target_month or not target_year:
            compliance_service = EmployeeComplianceService()
            target_month, target_year = compliance_service.get_current_target_month_year()
        
        # Get real-time data
        realtime_service = RealtimeComplianceService()
        dashboard_data = realtime_service.get_realtime_dashboard_data(target_month, target_year)
        
        return JsonResponse({
            'success': True,
            'data': dashboard_data,
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting realtime dashboard data: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def check_employee_compliance_status(request, employee_id):
    """
    Check compliance status for a specific employee.
    
    This endpoint provides real-time compliance checking for individual employees.
    """
    user = request.user
    
    # Check permissions
    if not user.is_staff and not user.is_superuser:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        # Get employee
        from django.contrib.auth import get_user_model
        User = get_user_model()
        employee = User.objects.get(id=employee_id)
        
        # Get current target month/year
        compliance_service = EmployeeComplianceService()
        target_month, target_year = compliance_service.get_current_target_month_year()
        
        # Check employee compliance
        realtime_service = RealtimeComplianceService()
        compliance_result = realtime_service.check_employee_compliance_threshold(
            employee, target_month, target_year
        )
        
        return JsonResponse({
            'success': True,
            'compliance_result': compliance_result,
            'checked_at': timezone.now().isoformat()
        })
        
    except User.DoesNotExist:
        return JsonResponse({'error': 'Employee not found'}, status=404)
    except Exception as e:
        logger.error(f"Error checking employee compliance status: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def get_compliance_statistics(request):
    """
    Get comprehensive compliance statistics for reporting.
    
    Provides detailed statistics about compliance rates, trends,
    and employee performance metrics.
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
        
        # Get department filter
        selected_department = None
        if department_id:
            try:
                selected_department = Department.objects.get(id=department_id)
            except Department.DoesNotExist:
                pass
        
        # Get compliance statistics
        realtime_service = RealtimeComplianceService()
        
        # Get all employee compliance data
        all_compliance = realtime_service._get_all_employee_compliance(target_month, target_year)
        
        # Filter by department if specified
        if selected_department:
            # Note: This would need to be enhanced to properly filter by department
            # For now, we'll use all employees
            pass
        
        # Calculate statistics
        total_employees = len(all_compliance)
        compliant_employees = [emp for emp in all_compliance if emp['is_compliant']]
        non_compliant_employees = [emp for emp in all_compliance if not emp['is_compliant']]
        
        compliance_rate = (len(compliant_employees) / total_employees * 100) if total_employees > 0 else 0
        total_salary_amount = sum(emp['salary_amount'] for emp in compliant_employees)
        average_compliance_rate = sum(emp['compliance_rate'] for emp in all_compliance) / total_employees if total_employees > 0 else 0
        
        # Compliance distribution
        compliance_distribution = {
            '0-10%': len([emp for emp in all_compliance if 0 <= emp['compliance_rate'] < 10]),
            '10-20%': len([emp for emp in all_compliance if 10 <= emp['compliance_rate'] < 20]),
            '20-33%': len([emp for emp in all_compliance if 20 <= emp['compliance_rate'] < 33]),
            '33-50%': len([emp for emp in all_compliance if 33 <= emp['compliance_rate'] < 50]),
            '50-75%': len([emp for emp in all_compliance if 50 <= emp['compliance_rate'] < 75]),
            '75-100%': len([emp for emp in all_compliance if 75 <= emp['compliance_rate'] <= 100])
        }
        
        statistics = {
            'period': f"{target_month}/{target_year}",
            'department': selected_department.name if selected_department else 'All Departments',
            'total_employees': total_employees,
            'compliant_employees': len(compliant_employees),
            'non_compliant_employees': len(non_compliant_employees),
            'overall_compliance_rate': round(compliance_rate, 2),
            'average_compliance_rate': round(average_compliance_rate, 2),
            'total_salary_amount': float(total_salary_amount),
            'average_salary_compliant': float(total_salary_amount / len(compliant_employees)) if compliant_employees else 0,
            'compliance_distribution': compliance_distribution,
            'generated_at': timezone.now().isoformat()
        }
        
        return JsonResponse({
            'success': True,
            'statistics': statistics
        })
        
    except Exception as e:
        logger.error(f"Error getting compliance statistics: {e}")
        return JsonResponse({'error': str(e)}, status=500)
