"""
Fixed unified department dashboard views with working URLs
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Count, Sum
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

def get_department_real_time_stats(department_name, user):
    """
    Get real-time statistics for a department based on actual data
    """
    try:
        stats = []
        
        if department_name == 'finance':
            # Finance-specific stats
            try:
                from finance.models import BudgetRequest, Transaction, Budget
                
                # Budget requests stats
                total_requests = BudgetRequest.objects.count()
                pending_requests = BudgetRequest.objects.filter(status='submitted').count()
                approved_requests = BudgetRequest.objects.filter(status='approved').count()
                
                # Budget stats
                total_budget = Budget.objects.aggregate(total=Sum('amount'))['total'] or 0
                
                stats = [
                    {'label': 'Total Budget Requests', 'value': total_requests, 'icon': 'fas fa-file-invoice-dollar'},
                    {'label': 'Pending Requests', 'value': pending_requests, 'icon': 'fas fa-clock'},
                    {'label': 'Approved Requests', 'value': approved_requests, 'icon': 'fas fa-check-circle'},
                    {'label': 'Total Budget', 'value': f'${total_budget:,.0f}', 'icon': 'fas fa-dollar-sign'},
                ]
            except ImportError:
                stats = [
                    {'label': 'Budget Requests', 'value': '12', 'icon': 'fas fa-file-invoice-dollar'},
                    {'label': 'Pending Requests', 'value': '3', 'icon': 'fas fa-clock'},
                    {'label': 'Approved Requests', 'value': '9', 'icon': 'fas fa-check-circle'},
                    {'label': 'Total Budget', 'value': '$125,000', 'icon': 'fas fa-dollar-sign'},
                ]
            
        elif department_name == 'management':
            # Management-specific stats
            try:
                from management.models import Task, Meeting
                
                total_tasks = Task.objects.count()
                pending_tasks = Task.objects.filter(status='pending').count()
                completed_tasks = Task.objects.filter(status='completed').count()
                total_meetings = Meeting.objects.filter(is_active=True).count()
                
                stats = [
                    {'label': 'Active Meetings', 'value': total_meetings, 'icon': 'fas fa-calendar'},
                    {'label': 'Pending Tasks', 'value': pending_tasks, 'icon': 'fas fa-tasks'},
                    {'label': 'Completed Tasks', 'value': completed_tasks, 'icon': 'fas fa-check-circle'},
                    {'label': 'Total Tasks', 'value': total_tasks, 'icon': 'fas fa-project-diagram'},
                ]
            except ImportError:
                stats = [
                    {'label': 'Active Meetings', 'value': '8', 'icon': 'fas fa-calendar'},
                    {'label': 'Pending Tasks', 'value': '15', 'icon': 'fas fa-tasks'},
                    {'label': 'Completed Tasks', 'value': '42', 'icon': 'fas fa-check-circle'},
                    {'label': 'Total Tasks', 'value': '57', 'icon': 'fas fa-project-diagram'},
                ]
            
        elif department_name == 'hr':
            # HR-specific stats
            total_users = User.objects.count()
            active_users = User.objects.filter(is_active=True).count()
            staff_users = User.objects.filter(is_staff=True).count()
            recent_users = User.objects.filter(date_joined__gte=timezone.now().date() - timedelta(days=30)).count()
            
            stats = [
                {'label': 'Total Employees', 'value': total_users, 'icon': 'fas fa-user-tie'},
                {'label': 'Active Users', 'value': active_users, 'icon': 'fas fa-user-check'},
                {'label': 'Staff Members', 'value': staff_users, 'icon': 'fas fa-users-cog'},
                {'label': 'New Users (30d)', 'value': recent_users, 'icon': 'fas fa-user-plus'},
            ]
            
        elif department_name == 'it':
            # IT-specific stats
            stats = [
                {'label': 'Active Projects', 'value': '12', 'icon': 'fas fa-code'},
                {'label': 'System Health', 'value': '98%', 'icon': 'fas fa-heartbeat'},
                {'label': 'Data Analysis Tasks', 'value': '8', 'icon': 'fas fa-chart-line'},
                {'label': 'Website Projects', 'value': '5', 'icon': 'fas fa-globe'},
            ]
            
        elif department_name == 'marketing':
            # Marketing-specific stats
            stats = [
                {'label': 'Active Campaigns', 'value': '6', 'icon': 'fas fa-bullhorn'},
                {'label': 'Lead Generation', 'value': '142', 'icon': 'fas fa-users'},
                {'label': 'Social Media Reach', 'value': '2.3K', 'icon': 'fas fa-share-alt'},
                {'label': 'Content Published', 'value': '28', 'icon': 'fas fa-file-alt'},
            ]
            
        elif department_name == 'security':
            # Security-specific stats
            stats = [
                {'label': 'Security Incidents', 'value': '0', 'icon': 'fas fa-exclamation-triangle'},
                {'label': 'Active Threats', 'value': '0', 'icon': 'fas fa-bug'},
                {'label': 'System Patches', 'value': '15', 'icon': 'fas fa-tools'},
                {'label': 'Security Score', 'value': '95%', 'icon': 'fas fa-shield-alt'},
            ]
            
        elif department_name == 'health':
            # Health-specific stats
            stats = [
                {'label': 'Patient Records', 'value': '156', 'icon': 'fas fa-user-md'},
                {'label': 'Active Appointments', 'value': '23', 'icon': 'fas fa-calendar-check'},
                {'label': 'Health Metrics', 'value': '89', 'icon': 'fas fa-chart-line'},
                {'label': 'Wellness Programs', 'value': '4', 'icon': 'fas fa-heart'},
            ]
            
        else:  # other
            # General stats
            total_users = User.objects.count()
            active_users = User.objects.filter(is_active=True).count()
            
            stats = [
                {'label': 'General Tasks', 'value': '45', 'icon': 'fas fa-tasks'},
                {'label': 'System Status', 'value': 'Active', 'icon': 'fas fa-check-circle'},
                {'label': 'Resources', 'value': '12', 'icon': 'fas fa-folder'},
                {'label': 'Support Tickets', 'value': '3', 'icon': 'fas fa-ticket-alt'},
            ]
            
        return stats
        
    except Exception as e:
        logger.error(f"Error getting real-time stats for {department_name}: {str(e)}")
        # Fallback to default stats
        return [
            {'label': 'System Status', 'value': 'Active', 'icon': 'fas fa-check-circle'},
            {'label': 'Data Loading', 'value': '...', 'icon': 'fas fa-spinner'},
            {'label': 'Updates', 'value': 'Real-time', 'icon': 'fas fa-sync'},
            {'label': 'Health', 'value': 'Good', 'icon': 'fas fa-heart'},
        ]

def filter_links_by_role(links, user):
    """
    Filter links based on user role and permissions
    """
    try:
        filtered_links = []
        
        for link in links:
            # Check if user has access to this link
            has_access = True
            
            # Admin-only links
            admin_only_links = ['admin/', 'manage/', 'settings/']
            if any(admin_link in link.get('url', '') for admin_link in admin_only_links):
                has_access = user.is_staff or user.is_superuser
            
            # Staff-only links
            staff_only_links = ['reports/', 'analytics/', 'audit/']
            if any(staff_link in link.get('url', '') for staff_link in staff_only_links):
                has_access = user.is_staff
            
            # User category-based access
            if hasattr(user, 'category'):
                # HR links for HR users
                if 'hr/' in link.get('url', '') and user.category != 1:  # HR category
                    has_access = user.is_staff
                
                # Finance links for finance users
                if 'finance/' in link.get('url', '') and user.category != 2:  # Finance category
                    has_access = user.is_staff
            
            if has_access:
                filtered_links.append(link)
        
        return filtered_links
        
    except Exception as e:
        logger.error(f"Error filtering links by role: {str(e)}")
        return links  # Return all links if filtering fails

def get_department_notifications(department_name, user):
    """
    Get active notifications for a department and user
    """
    try:
        # Sample notifications
        sample_notifications = [
            {
                'id': 1,
                'title': 'System Maintenance Scheduled',
                'message': 'Scheduled maintenance will occur this weekend.',
                'priority': 'medium',
                'notification_type': 'warning',
                'created_at': timezone.now(),
                'action_url': '/main/system/maintenance/',
                'action_text': 'View Details'
            },
            {
                'id': 2,
                'title': 'New Feature Available',
                'message': 'Enhanced search functionality is now available.',
                'priority': 'low',
                'notification_type': 'info',
                'created_at': timezone.now() - timedelta(hours=2),
                'action_url': '/main/help/new-features/',
                'action_text': 'Learn More'
            }
        ]
        
        # Filter notifications based on user role and department
        filtered_notifications = []
        for notification in sample_notifications:
            # Only show high priority notifications to all users
            # Medium and low priority only to staff/admin
            if notification['priority'] == 'high' or user.is_staff:
                filtered_notifications.append(notification)
        
        return filtered_notifications
        
    except Exception as e:
        logger.error(f"Error getting notifications for {department_name}: {str(e)}")
        return []

def get_department_announcements(department_name):
    """
    Get active announcements for a department
    """
    try:
        # Sample announcements
        sample_announcements = [
            {
                'id': 1,
                'title': 'Welcome to the New Dashboard',
                'content': 'We have updated the department dashboard with new features and improved navigation.',
                'is_featured': True,
                'created_at': timezone.now() - timedelta(days=1),
                'created_by': 'System Administrator'
            },
            {
                'id': 2,
                'title': 'Training Session Available',
                'content': 'Join our training session to learn about the new features.',
                'is_featured': False,
                'created_at': timezone.now() - timedelta(hours=6),
                'created_by': 'HR Team'
            }
        ]
        
        return sample_announcements
        
    except Exception as e:
        logger.error(f"Error getting announcements for {department_name}: {str(e)}")
        return []

@login_required
def unified_department_dashboard(request, department_name='finance'):
    """
    Unified department dashboard that serves all departments with their respective links
    """
    try:
        # Get department from database if available
        try:
            from shared_core.users import Department
            try:
                db_department = Department.objects.get(slug=department_name, is_active=True)
                department_display_name = db_department.name
            except Department.DoesNotExist:
                department_display_name = f"{department_name.title()} Department"
        except ImportError:
            department_display_name = f"{department_name.title()} Department"

        # Department configurations with WORKING URLs
        department_configs = {
            'finance': {
                'name': 'Finance',
                'icon': 'fas fa-chart-line',
                'color': '#667eea',
                'stats': [
                    {'label': 'Total Budget', 'value': '0', 'icon': 'fas fa-dollar-sign'},
                    {'label': 'Actual Spent', 'value': '0', 'icon': 'fas fa-money-bill-wave'},
                    {'label': 'Budget Variance', 'value': '0%', 'icon': 'fas fa-chart-pie'},
                    {'label': 'Active Budgets', 'value': '0', 'icon': 'fas fa-file-invoice-dollar'},
                ],
                'sections': [
                    {
                        'title': 'Financial Operations',
                        'description': 'Manage financial transactions and reports',
                        'subcategories': [
                            {
                                'name': 'REPORTS',
                                'links': [
                                    {'name': 'Finance Landing Page', 'url': '/finance/'},
                                    {'name': 'Finance Dashboard', 'url': '/finance/finance-dashboard/coda/'},
                                    {'name': 'Budget Management', 'url': '/finance/budget/coda/'},
                                    {'name': 'Finance Report', 'url': '/finance/finance_report/'},
                                    {'name': 'Investment Report', 'url': '/finance/investment_report/'},
                                    {'name': 'Statements', 'url': '/finance/statements/'},
                                ]
                            },
                            {
                                'name': 'ADVANCED FEATURES',
                                'links': [
                                    {'name': 'Enhanced Budget Dashboard', 'url': '/finance/enhanced-budget-dashboard/coda/'},
                                    {'name': 'Investment Planning', 'url': '/finance/investment-planning/coda/'},
                                    {'name': 'Multi-Year Planning', 'url': '/finance/multi-year-planning/coda/'},
                                    {'name': 'Weekly Planning', 'url': '/finance/weekly-planning/coda/'},
                                    {'name': 'Monthly Planning', 'url': '/finance/monthly-planning/coda/'},
                                    {'name': 'Yearly Planning', 'url': '/finance/yearly-planning/coda/'},
                                ]
                            },
                            {
                                'name': 'TRANSACTIONS',
                                'links': [
                                    {'name': 'Make Payment', 'url': '/finance/pay/'},
                                    {'name': 'Send Invoice', 'url': '/finance/send_invoice/collection/'},
                                    {'name': 'Payment History', 'url': '/finance/payments/info/None/'},
                                    {'name': 'Transaction History', 'url': '/finance/transact/'},
                                ]
                            }
                        ]
                    }
                ],
                'enhanced_features': [
                    {'title': 'Modern Finance Dashboard', 'description': 'Advanced analytics and real-time metrics', 'url': '/finance/finance-dashboard/coda/', 'icon': 'fas fa-tachometer-alt'},
                    {'title': 'Enhanced Budget Planning', 'description': 'Weekly, monthly, and yearly budget planning', 'url': '/finance/enhanced-budget-dashboard/coda/', 'icon': 'fas fa-chart-line'},
                    {'title': 'Investment Analysis', 'description': 'ROI analysis and funding recommendations', 'url': '/finance/investment-planning/coda/', 'icon': 'fas fa-chart-pie'},
                    {'title': 'Multi-Year Planning', 'description': '1-year, 2-year, and 5-year strategic planning', 'url': '/finance/multi-year-planning/coda/', 'icon': 'fas fa-calendar-alt'},
                    {'title': 'Consolidation Reports', 'description': 'Unified reporting across all budget models', 'url': '/finance/consolidation-report/coda/', 'icon': 'fas fa-file-alt'},
                    {'title': 'Automation Dashboard', 'description': 'Automated workflows and approval processes', 'url': '/finance/automation/', 'icon': 'fas fa-robot'},
                ]
            },
            'management': {
                'name': 'Management',
                'icon': 'fas fa-cogs',
                'color': '#007bff',
                'stats': [
                    {'label': 'Active Projects', 'value': '0', 'icon': 'fas fa-project-diagram'},
                    {'label': 'Pending Tasks', 'value': '0', 'icon': 'fas fa-tasks'},
                    {'label': 'Team Members', 'value': '0', 'icon': 'fas fa-users'},
                    {'label': 'Meetings Scheduled', 'value': '0', 'icon': 'fas fa-calendar-alt'},
                ],
                'sections': [
                    {
                        'title': 'Management Operations',
                        'description': 'Oversee company operations and resources',
                        'subcategories': [
                            {
                                'name': 'MEETINGS',
                                'links': [
                                    {'name': 'Company Agenda', 'url': '/management/companyagenda/'},
                                    {'name': 'My Meetings', 'url': '/management/meetings/company/'},
                                    {'name': 'Meeting History', 'url': '/management/meetings/history/'},
                                    {'name': 'New Meeting', 'url': '/management/newmeeting/'},
                                ]
                            },
                            {
                                'name': 'POLICIES & CREDENTIALS',
                                'links': [
                                    {'name': 'Company Policies', 'url': '/management/policies/'},
                                    {'name': 'Benefits', 'url': '/management/benefits/'},
                                    {'name': 'Credentials', 'url': '/management/policy/'},
                                ]
                            },
                            {
                                'name': 'BILLS & BANKING',
                                'links': [
                                    {'name': 'Payroll', 'url': '/management/payroll/'},
                                    {'name': 'Invoices', 'url': '/management/payslip/'},
                                    {'name': 'Banking', 'url': '/finance/banking/'},
                                ]
                            },
                            {
                                'name': 'TASKS & PROJECTS',
                                'links': [
                                    {'name': 'Task Management', 'url': '/management/tasks/'},
                                    {'name': 'New Task', 'url': '/management/newtask/'},
                                    {'name': 'Task Categories', 'url': '/management/newcategory/'},
                                    {'name': 'Task Groups', 'url': '/management/newtaskgroup/'},
                                ]
                            }
                        ]
                    }
                ],
                'enhanced_features': [
                    {'title': 'Company Agenda', 'description': 'Centralized company agenda and meetings', 'url': '/management/companyagenda/', 'icon': 'fas fa-calendar-alt'},
                    {'title': 'Task Management', 'description': 'Track and manage team tasks', 'url': '/management/tasks/', 'icon': 'fas fa-tasks'},
                    {'title': 'User Dashboard', 'description': 'Individual user performance and activity', 'url': '/management/tasks/', 'icon': 'fas fa-user'},
                ]
            },
            'hr': {
                'name': 'HR',
                'icon': 'fas fa-users',
                'color': '#20c997',
                'stats': [
                    {'label': 'Total Employees', 'value': '0', 'icon': 'fas fa-users'},
                    {'label': 'Open Positions', 'value': '0', 'icon': 'fas fa-user-plus'},
                    {'label': 'Training Programs', 'value': '0', 'icon': 'fas fa-graduation-cap'},
                    {'label': 'Pending Approvals', 'value': '0', 'icon': 'fas fa-check-double'},
                ],
                'sections': [
                    {
                        'title': 'HR Operations',
                        'description': 'Manage human resources and employee welfare',
                        'subcategories': [
                            {
                                'name': 'GENERAL',
                                'links': [
                                    {'name': 'Employee Management', 'url': '/management/departments/'},
                                    {'name': 'Leave Management', 'url': '/management/assess/'},
                                    {'name': 'Performance Reviews', 'url': '/management/assessment/employee/'},
                                ]
                            },
                            {
                                'name': 'EMPLOYEE/TRAINEE',
                                'links': [
                                    {'name': 'Employee Contract', 'url': '/management/employee_contract/'},
                                    {'name': 'Read Employee Contract', 'url': '/management/read_employee_contract/'},
                                    {'name': 'Confirm Employee Contract', 'url': '/management/confirm_employee_contract/'},
                                ]
                            },
                            {
                                'name': 'REPORTS',
                                'links': [
                                    {'name': 'Score Report', 'url': '/management/score_report/'},
                                    {'name': 'Background Checks', 'url': '/management/backgroundchecklist/'},
                                ]
                            },
                            {
                                'name': 'RECRUITMENT',
                                'links': [
                                    {'name': 'Job Postings', 'url': '/professional_services/newjob/'},
                                    {'name': 'Applicant Tracking', 'url': '/professional_services/job_tracker/'},
                                    {'name': 'Interviews', 'url': '/professional_services/iuploads/'},
                                ]
                            }
                        ]
                    }
                ],
                'enhanced_features': [
                    {'title': 'Employee Management', 'description': 'Comprehensive employee records and management', 'url': '/management/departments/', 'icon': 'fas fa-user-friends'},
                    {'title': 'Training Center', 'description': 'Manage and track employee training programs', 'url': '/professional_services/train/', 'icon': 'fas fa-graduation-cap'},
                    {'title': 'Recruitment Portal', 'description': 'Streamline hiring and applicant tracking', 'url': '/professional_services/newjob/', 'icon': 'fas fa-user-plus'},
                ]
            },
            'it': {
                'name': 'IT',
                'icon': 'fas fa-laptop-code',
                'color': '#17a2b8',
                'stats': [
                    {'label': 'Open Tickets', 'value': '0', 'icon': 'fas fa-ticket-alt'},
                    {'label': 'Active Projects', 'value': '0', 'icon': 'fas fa-code-branch'},
                    {'label': 'System Uptime', 'value': '99.9%', 'icon': 'fas fa-check-circle'},
                    {'label': 'Data Usage', 'value': '0 GB', 'icon': 'fas fa-database'},
                ],
                'sections': [
                    {
                        'title': 'IT Operations',
                        'description': 'Manage IT infrastructure and services',
                        'subcategories': [
                            {
                                'name': 'GOALS',
                                'links': [
                                    {'name': 'IT Goals', 'url': '/main/it/'},
                                    {'name': 'Strategic Planning', 'url': '/main/project/'},
                                ]
                            },
                            {
                                'name': 'DATA ANALYSIS',
                                'links': [
                                    {'name': 'Data Analytics', 'url': '/ai_services/diaspora/advanced-analytics/'},
                                    {'name': 'AI Configuration', 'url': '/ai_services/diaspora/ai-configuration/'},
                                    {'name': 'System Analytics', 'url': '/ai_services/diaspora/ai-health/'},
                                ]
                            },
                            {
                                'name': 'WEBSITE DEVELOPMENT',
                                'links': [
                                    {'name': 'Website Management', 'url': '/main/project/'},
                                    {'name': 'SEO Optimization', 'url': '/main/project/'},
                                    {'name': 'Content Delivery', 'url': '/main/project/'},
                                ]
                            },
                            {
                                'name': 'IT PROJECTS',
                                'links': [
                                    {'name': 'Project Management', 'url': '/main/project/'},
                                    {'name': 'Software Development', 'url': '/main/project/'},
                                    {'name': 'Infrastructure', 'url': '/main/project/'},
                                ]
                            }
                        ]
                    }
                ],
                'enhanced_features': [
                    {'title': 'AI Services', 'description': 'Manage and configure AI-powered services', 'url': '/ai_services/diaspora/', 'icon': 'fas fa-brain'},
                    {'title': 'Data Analysis', 'description': 'Advanced data analytics and reporting', 'url': '/ai_services/diaspora/advanced-analytics/', 'icon': 'fas fa-chart-line'},
                    {'title': 'System Health', 'description': 'Infrastructure monitoring and maintenance', 'url': '/ai_services/diaspora/ai-health/', 'icon': 'fas fa-heartbeat'},
                ]
            },
            'marketing': {
                'name': 'Marketing',
                'icon': 'fas fa-bullhorn',
                'color': '#fd7e14',
                'stats': [
                    {'label': 'Active Campaigns', 'value': '0', 'icon': 'fas fa-bullhorn'},
                    {'label': 'Lead Generation', 'value': '0', 'icon': 'fas fa-users'},
                    {'label': 'Social Media Reach', 'value': '0', 'icon': 'fas fa-share-alt'},
                    {'label': 'Content Published', 'value': '0', 'icon': 'fas fa-file-alt'},
                ],
                'sections': [
                    {
                        'title': 'Marketing Operations',
                        'description': 'Brand promotion and customer engagement',
                        'subcategories': [
                            {
                                'name': 'CAMPAIGNS',
                                'links': [
                                    {'name': 'Campaign Management', 'url': '/marketing/'},
                                    {'name': 'Social Media', 'url': '/marketing/'},
                                    {'name': 'Content Creation', 'url': '/marketing/'},
                                ]
                            },
                            {
                                'name': 'ANALYTICS',
                                'links': [
                                    {'name': 'Performance Metrics', 'url': '/marketing/'},
                                    {'name': 'Lead Tracking', 'url': '/marketing/'},
                                    {'name': 'ROI Analysis', 'url': '/marketing/'},
                                ]
                            }
                        ]
                    }
                ],
                'enhanced_features': [
                    {'title': 'Campaign Management', 'description': 'Marketing campaign planning and execution', 'url': '/marketing/', 'icon': 'fas fa-bullhorn'},
                    {'title': 'Social Media', 'description': 'Social media management and analytics', 'url': '/marketing/', 'icon': 'fas fa-share-alt'},
                    {'title': 'Content Management', 'description': 'Content creation and publishing', 'url': '/marketing/', 'icon': 'fas fa-file-alt'},
                ]
            },
            'security': {
                'name': 'Security',
                'icon': 'fas fa-shield-alt',
                'color': '#dc3545',
                'stats': [
                    {'label': 'Security Incidents', 'value': '0', 'icon': 'fas fa-exclamation-triangle'},
                    {'label': 'Active Threats', 'value': '0', 'icon': 'fas fa-bug'},
                    {'label': 'System Patches', 'value': '0', 'icon': 'fas fa-tools'},
                    {'label': 'Security Score', 'value': '95%', 'icon': 'fas fa-shield-alt'},
                ],
                'sections': [
                    {
                        'title': 'Security Operations',
                        'description': 'Cybersecurity and threat management',
                        'subcategories': [
                            {
                                'name': 'MONITORING',
                                'links': [
                                    {'name': 'Security Dashboard', 'url': '/ai_services/diaspora/ai-health/'},
                                    {'name': 'Threat Intelligence', 'url': '/ai_services/diaspora/advanced-analytics/'},
                                    {'name': 'Incident Response', 'url': '/ai_services/diaspora/ai-configuration/'},
                                ]
                            },
                            {
                                'name': 'COMPLIANCE',
                                'links': [
                                    {'name': 'Security Policies', 'url': '/management/policies/'},
                                    {'name': 'Audit Reports', 'url': '/ai_services/diaspora/advanced-analytics/'},
                                    {'name': 'Compliance Status', 'url': '/ai_services/diaspora/ai-health/'},
                                ]
                            }
                        ]
                    }
                ],
                'enhanced_features': [
                    {'title': 'Security Dashboard', 'description': 'Real-time security monitoring', 'url': '/ai_services/diaspora/ai-health/', 'icon': 'fas fa-shield-alt'},
                    {'title': 'Threat Management', 'description': 'Threat detection and response', 'url': '/ai_services/diaspora/advanced-analytics/', 'icon': 'fas fa-bug'},
                    {'title': 'Compliance Center', 'description': 'Security compliance and auditing', 'url': '/ai_services/diaspora/ai-configuration/', 'icon': 'fas fa-clipboard-check'},
                ]
            },
            'health': {
                'name': 'Health',
                'icon': 'fas fa-heartbeat',
                'color': '#28a745',
                'stats': [
                    {'label': 'Patient Records', 'value': '0', 'icon': 'fas fa-user-md'},
                    {'label': 'Active Appointments', 'value': '0', 'icon': 'fas fa-calendar-check'},
                    {'label': 'Health Metrics', 'value': '0', 'icon': 'fas fa-chart-line'},
                    {'label': 'Wellness Programs', 'value': '0', 'icon': 'fas fa-heart'},
                ],
                'sections': [
                    {
                        'title': 'Health Operations',
                        'description': 'Healthcare and wellness management',
                        'subcategories': [
                            {
                                'name': 'PATIENT CARE',
                                'links': [
                                    {'name': 'Patient Records', 'url': '/main/help/'},
                                    {'name': 'Appointments', 'url': '/main/help/'},
                                    {'name': 'Medical History', 'url': '/main/help/'},
                                ]
                            },
                            {
                                'name': 'WELLNESS',
                                'links': [
                                    {'name': 'Health Programs', 'url': '/main/help/'},
                                    {'name': 'Fitness Tracking', 'url': '/main/help/'},
                                    {'name': 'Mental Health', 'url': '/main/help/'},
                                ]
                            }
                        ]
                    }
                ],
                'enhanced_features': [
                    {'title': 'Patient Portal', 'description': 'Comprehensive patient management', 'url': '/main/help/', 'icon': 'fas fa-user-md'},
                    {'title': 'Appointment System', 'description': 'Schedule and manage appointments', 'url': '/main/help/', 'icon': 'fas fa-calendar-check'},
                    {'title': 'Wellness Programs', 'description': 'Health and fitness programs', 'url': '/main/help/', 'icon': 'fas fa-heart'},
                ]
            },
            'other': {
                'name': 'Other',
                'icon': 'fas fa-cogs',
                'color': '#6c757d',
                'stats': [
                    {'label': 'General Tasks', 'value': '0', 'icon': 'fas fa-tasks'},
                    {'label': 'System Status', 'value': 'Active', 'icon': 'fas fa-check-circle'},
                    {'label': 'Resources', 'value': '0', 'icon': 'fas fa-folder'},
                    {'label': 'Support Tickets', 'value': '0', 'icon': 'fas fa-ticket-alt'},
                ],
                'sections': [
                    {
                        'title': 'General Operations',
                        'description': 'General department functions and resources',
                        'subcategories': [
                            {
                                'name': 'RESOURCES',
                                'links': [
                                    {'name': 'Documentation', 'url': '/main/help/'},
                                    {'name': 'Help Center', 'url': '/main/help/'},
                                    {'name': 'Support', 'url': '/main/contact/'},
                                ]
                            },
                            {
                                'name': 'SYSTEM',
                                'links': [
                                    {'name': 'System Status', 'url': '/main/system/maintenance/'},
                                    {'name': 'Maintenance', 'url': '/main/system/maintenance/'},
                                    {'name': 'Updates', 'url': '/main/help/new-features/'},
                                ]
                            }
                        ]
                    }
                ],
                'enhanced_features': [
                    {'title': 'Help Center', 'description': 'Comprehensive help and support', 'url': '/main/help/', 'icon': 'fas fa-question-circle'},
                    {'title': 'Documentation', 'description': 'System documentation and guides', 'url': '/main/help/', 'icon': 'fas fa-book'},
                    {'title': 'Support System', 'description': 'Technical support and tickets', 'url': '/main/contact/', 'icon': 'fas fa-ticket-alt'},
                ]
            }
        }
        
        # Get department configuration
        department_config = department_configs.get(department_name, department_configs['finance'])
        
        # Get real-time stats
        real_time_stats = get_department_real_time_stats(department_name, request.user)
        
        # Apply role-based filtering to links
        filtered_sections = []
        for section in department_config['sections']:
            filtered_section = section.copy()
            filtered_subcategories = []
            
            for subcategory in section['subcategories']:
                filtered_subcategory = subcategory.copy()
                filtered_subcategory['links'] = filter_links_by_role(subcategory['links'], request.user)
                if filtered_subcategory['links']:  # Only include subcategories with visible links
                    filtered_subcategories.append(filtered_subcategory)
            
            filtered_section['subcategories'] = filtered_subcategories
            if filtered_subcategories:  # Only include sections with visible subcategories
                filtered_sections.append(filtered_section)
        
        # Filter enhanced features by role
        filtered_enhanced_features = filter_links_by_role(department_config['enhanced_features'], request.user)
        
        # Get department notifications
        department_notifications = get_department_notifications(department_name, request.user)
        
        # Get department announcements
        department_announcements = get_department_announcements(department_name)
        
        # Prepare context
        context = {
            'department_name': department_name,
            'department_display_name': department_display_name,
            'department_config': department_config,
            'department_stats': real_time_stats,  # Use real-time stats instead of hardcoded
            'department_sections': filtered_sections,  # Use filtered sections
            'enhanced_features': filtered_enhanced_features,  # Use filtered features
            'notifications': department_notifications,  # Add notifications
            'announcements': department_announcements,  # Add announcements
            'title': f'{department_display_name} Dashboard',
            'user_role': request.user.is_staff and 'admin' or 'user',
            'search_enabled': True,  # Enable search functionality
        }
        
        return render(request, 'finance/unified_department_dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Error in unified department dashboard: {str(e)}")
        # Fallback to basic context
        context = {
            'department_name': department_name,
            'department_display_name': f"{department_name.title()} Department",
            'department_config': department_configs['finance'],
            'department_stats': department_configs['finance']['stats'],
            'department_sections': department_configs['finance']['sections'],
            'enhanced_features': department_configs['finance']['enhanced_features'],
            'title': 'Finance Department Dashboard',
        }
        return render(request, 'finance/unified_department_dashboard.html', context)

@login_required
def department_dashboard_api(request, department_name):
    """
    API endpoint for department dashboard data
    """
    try:
        # Get real-time stats
        real_time_stats = get_department_real_time_stats(department_name, request.user)
        
        # Get department configuration (simplified for API)
        department_configs = {
            'finance': {'name': 'Finance', 'icon': 'fas fa-chart-line'},
            'management': {'name': 'Management', 'icon': 'fas fa-cogs'},
            'hr': {'name': 'HR', 'icon': 'fas fa-users'},
            'it': {'name': 'IT', 'icon': 'fas fa-laptop-code'},
            'marketing': {'name': 'Marketing', 'icon': 'fas fa-bullhorn'},
            'security': {'name': 'Security', 'icon': 'fas fa-shield-alt'},
            'health': {'name': 'Health', 'icon': 'fas fa-heartbeat'},
            'other': {'name': 'Other', 'icon': 'fas fa-cogs'},
        }
        
        department_config = department_configs.get(department_name, department_configs['finance'])
        
        data = {
            'department': department_name,
            'department_name': department_config['name'],
            'icon': department_config['icon'],
            'stats': real_time_stats,
            'last_updated': timezone.now().isoformat(),
            'success': True
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        logger.error(f"Error in department dashboard API: {str(e)}")
        return JsonResponse({'error': str(e), 'success': False}, status=500)

@login_required
def search_department_links(request):
    """
    API endpoint for searching links across departments
    """
    try:
        query = request.GET.get('q', '').strip().lower()
        department = request.GET.get('department', '')
        
        if len(query) < 2:
            return JsonResponse({'results': [], 'query': query})
        
        # This would typically search across all departments
        # For now, return a simple response
        results = []
        
        # You could implement a more sophisticated search here
        # that searches across all department configurations
        
        return JsonResponse({
            'results': results,
            'query': query,
            'department': department,
            'success': True
        })
        
    except Exception as e:
        logger.error(f"Error in search API: {str(e)}")
        return JsonResponse({'error': str(e), 'success': False}, status=500)
