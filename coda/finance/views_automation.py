"""
Finance Automation Dashboard Views
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q
from django.http import JsonResponse
from django.core.paginator import Paginator
import logging

from .models import BudgetRequest, ApprovalPolicy, DisbursementRequest, AutomationAuditLog, BudgetCategory
from .services.automation_service import (
    BudgetRequestService, ApprovalEngineService, DisbursementService, AutomationAuditService
)

logger = logging.getLogger(__name__)


@login_required
def automation_dashboard(request):
    """Main automation dashboard view"""
    try:
        # Get user role
        user_role = get_user_role(request.user)
        
        # Get dashboard data
        dashboard_data = get_automation_dashboard_data(request.user, user_role)
        
        # Get recent activities
        recent_activities = get_recent_automation_activities(request.user)
        
        # Get notifications
        notifications = get_automation_notifications(request.user)
        
        context = {
            'user_role': user_role,
            'dashboard_data': dashboard_data,
            'recent_activities': recent_activities,
            'notifications': notifications,
            'page_title': 'Finance Automation Dashboard',
            'active_tab': 'automation',
            'user': request.user,
        }
        
        return render(request, 'finance/automation_dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Error in automation dashboard: {str(e)}")
        messages.error(request, f"Error loading dashboard: {str(e)}")
        return redirect('dashboard:unified_dashboard')


@login_required
def budget_requests_dashboard(request):
    """Budget requests management dashboard"""
    try:
        # Get filter parameters
        status_filter = request.GET.get('status', '')
        priority_filter = request.GET.get('priority', '')
        department_filter = request.GET.get('department', '')
        
        # Build query
        query = Q()
        if status_filter:
            query &= Q(status=status_filter)
        if priority_filter:
            query &= Q(priority=priority_filter)
        if department_filter:
            query &= Q(department_id=department_filter)
        
        # Get budget requests
        budget_requests = BudgetRequest.objects.filter(query).order_by('-created_at')
        
        # Pagination
        paginator = Paginator(budget_requests, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Get statistics
        stats = {
            'total_requests': BudgetRequest.objects.count(),
            'pending_requests': BudgetRequest.objects.filter(status='submitted').count(),
            'approved_requests': BudgetRequest.objects.filter(status='approved').count(),
            'rejected_requests': BudgetRequest.objects.filter(status='rejected').count(),
        }
        
        context = {
            'page_obj': page_obj,
            'stats': stats,
            'status_filter': status_filter,
            'priority_filter': priority_filter,
            'department_filter': department_filter,
            'page_title': 'Budget Requests Management',
            'active_tab': 'budget_requests',
        }
        
        return render(request, 'finance/budget_requests_dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Error in budget requests dashboard: {str(e)}")
        messages.error(request, f"Error loading budget requests: {str(e)}")
        return redirect('finance:automation_dashboard')


@login_required
def disbursements_dashboard(request):
    """Disbursements management dashboard"""
    try:
        # Get filter parameters
        status_filter = request.GET.get('status', '')
        method_filter = request.GET.get('method', '')
        
        # Build query
        query = Q()
        if status_filter:
            query &= Q(status=status_filter)
        if method_filter:
            query &= Q(disbursement_method=method_filter)
        
        # Get disbursement requests
        disbursements = DisbursementRequest.objects.filter(query).order_by('-created_at')
        
        # Pagination
        paginator = Paginator(disbursements, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Get statistics
        stats = {
            'total_disbursements': DisbursementRequest.objects.count(),
            'pending_disbursements': DisbursementRequest.objects.filter(status='pending').count(),
            'completed_disbursements': DisbursementRequest.objects.filter(status='completed').count(),
            'failed_disbursements': DisbursementRequest.objects.filter(status='failed').count(),
        }
        
        context = {
            'page_obj': page_obj,
            'stats': stats,
            'status_filter': status_filter,
            'method_filter': method_filter,
            'page_title': 'Disbursements Management',
            'active_tab': 'disbursements',
        }
        
        return render(request, 'finance/disbursements_dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Error in disbursements dashboard: {str(e)}")
        messages.error(request, f"Error loading disbursements: {str(e)}")
        return redirect('finance:automation_dashboard')


@login_required
def approval_policies_dashboard(request):
    """Approval policies management dashboard"""
    try:
        # Get approval policies
        policies = ApprovalPolicy.objects.all().order_by('-created_at')
        
        # Get statistics
        stats = {
            'total_policies': ApprovalPolicy.objects.count(),
            'active_policies': ApprovalPolicy.objects.filter(is_active=True).count(),
            'inactive_policies': ApprovalPolicy.objects.filter(is_active=False).count(),
        }
        
        context = {
            'policies': policies,
            'stats': stats,
            'page_title': 'Approval Policies Management',
            'active_tab': 'approval_policies',
        }
        
        return render(request, 'finance/approval_policies_dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Error in approval policies dashboard: {str(e)}")
        messages.error(request, f"Error loading approval policies: {str(e)}")
        return redirect('finance:automation_dashboard')


@login_required
def audit_logs_dashboard(request):
    """Audit logs dashboard"""
    try:
        # Get filter parameters
        action_filter = request.GET.get('action', '')
        action_type_filter = request.GET.get('action_type', '')
        success_filter = request.GET.get('success', '')
        
        # Build query
        query = Q()
        if action_filter:
            query &= Q(action__icontains=action_filter)
        if action_type_filter:
            query &= Q(action_type=action_type_filter)
        if success_filter:
            query &= Q(success=success_filter == 'true')
        
        # Get audit logs
        audit_logs = AutomationAuditLog.objects.filter(query).order_by('-created_at')
        
        # Pagination
        paginator = Paginator(audit_logs, 50)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Get statistics
        stats = {
            'total_logs': AutomationAuditLog.objects.count(),
            'successful_actions': AutomationAuditLog.objects.filter(success=True).count(),
            'failed_actions': AutomationAuditLog.objects.filter(success=False).count(),
        }
        
        context = {
            'page_obj': page_obj,
            'stats': stats,
            'action_filter': action_filter,
            'action_type_filter': action_type_filter,
            'success_filter': success_filter,
            'page_title': 'Audit Logs',
            'active_tab': 'audit_logs',
        }
        
        return render(request, 'finance/audit_logs_dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Error in audit logs dashboard: {str(e)}")
        messages.error(request, f"Error loading audit logs: {str(e)}")
        return redirect('finance:automation_dashboard')


def get_user_role(user):
    """Get user role for dashboard customization"""
    if not user.is_authenticated:
        return 'guest'
    
    # Check if user is staff/admin
    if user.is_staff or user.is_superuser:
        return 'admin'
    
    # Get user category
    if hasattr(user, 'category'):
        # Map category numbers to names
        category_mapping = {
            1: 'applicant',
            2: 'student', 
            3: 'consultant',
            4: 'investor',
            5: 'explorer',
        }
        return category_mapping.get(user.category, 'explorer')
    else:
        return 'explorer'


def get_automation_dashboard_data(user, user_role):
    """Get automation dashboard data based on user role"""
    try:
        data = {
            'budget_requests': {
                'total': BudgetRequest.objects.count(),
                'pending': BudgetRequest.objects.filter(status='submitted').count(),
                'approved': BudgetRequest.objects.filter(status='approved').count(),
                'rejected': BudgetRequest.objects.filter(status='rejected').count(),
            },
            'disbursements': {
                'total': DisbursementRequest.objects.count(),
                'pending': DisbursementRequest.objects.filter(status='pending').count(),
                'completed': DisbursementRequest.objects.filter(status='completed').count(),
                'failed': DisbursementRequest.objects.filter(status='failed').count(),
            },
            'approval_policies': {
                'total': ApprovalPolicy.objects.count(),
                'active': ApprovalPolicy.objects.filter(is_active=True).count(),
                'inactive': ApprovalPolicy.objects.filter(is_active=False).count(),
            },
            'audit_logs': {
                'total': AutomationAuditLog.objects.count(),
                'successful': AutomationAuditLog.objects.filter(success=True).count(),
                'failed': AutomationAuditLog.objects.filter(success=False).count(),
            }
        }
        
        # Add user-specific data
        if user_role in ['admin', 'staff']:
            data['user_requests'] = BudgetRequest.objects.filter(requester=user).count()
            data['user_disbursements'] = DisbursementRequest.objects.filter(
                budget_request__requester=user
            ).count()
        
        return data
        
    except Exception as e:
        logger.error(f"Error getting automation dashboard data: {str(e)}")
        return {}


def get_recent_automation_activities(user):
    """Get recent automation activities"""
    try:
        activities = []
        
        # Get recent budget requests
        recent_requests = BudgetRequest.objects.filter(requester=user).order_by('-created_at')[:5]
        for request in recent_requests:
            activities.append({
                'type': 'budget_request',
                'title': f'Budget Request #{request.id}',
                'description': f'{request.purpose} - {request.get_status_display()}',
                'timestamp': request.created_at,
                'status': request.status,
            })
        
        # Get recent disbursements
        recent_disbursements = DisbursementRequest.objects.filter(
            budget_request__requester=user
        ).order_by('-created_at')[:5]
        for disbursement in recent_disbursements:
            activities.append({
                'type': 'disbursement',
                'title': f'Disbursement #{disbursement.id}',
                'description': f'{disbursement.recipient_name} - {disbursement.get_status_display()}',
                'timestamp': disbursement.created_at,
                'status': disbursement.status,
            })
        
        # Sort by timestamp
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return activities[:10]  # Return top 10
        
    except Exception as e:
        logger.error(f"Error getting recent activities: {str(e)}")
        return []


def get_automation_notifications(user):
    """Get automation notifications for user"""
    try:
        notifications = []
        
        # Get pending approvals for user
        if user.is_staff:
            pending_requests = BudgetRequest.objects.filter(
                status='under_review',
                current_approver=user
            )
            for request in pending_requests:
                notifications.append({
                    'type': 'approval_required',
                    'title': 'Approval Required',
                    'message': f'Budget Request #{request.id} requires your approval',
                    'url': f'/admin/finance/budgetrequest/{request.id}/change/',
                    'priority': 'high',
                })
        
        # Get overdue requests
        overdue_requests = BudgetRequest.objects.filter(
            requester=user,
            status='submitted',
            required_date__lt=timezone.now().date()
        )
        for request in overdue_requests:
            notifications.append({
                'type': 'overdue',
                'title': 'Overdue Request',
                'message': f'Budget Request #{request.id} is overdue',
                'url': f'/admin/finance/budgetrequest/{request.id}/change/',
                'priority': 'medium',
            })
        
        return notifications
        
    except Exception as e:
        logger.error(f"Error getting notifications: {str(e)}")
        return []


@login_required
def automation_dashboard_api(request):
    """API endpoint for automation dashboard data"""
    try:
        user_role = get_user_role(request.user)
        dashboard_data = get_automation_dashboard_data(request.user, user_role)
        
        return JsonResponse({
            'status': 'success',
            'data': dashboard_data
        })
        
    except Exception as e:
        logger.error(f"Error in automation dashboard API: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

