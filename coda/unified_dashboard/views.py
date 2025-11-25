from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.urls import reverse
from decimal import Decimal
from urllib.parse import urlencode
import json
import logging

from .models import DashboardWidget, UserDashboardPreferences, DashboardService, UserServiceAccess, DashboardAnalytics
from shared_core.users import UserCategory as CategoryChoices
# Unified Dashboard app migrated to use shared_core - 25.11_UNIFIED_DASHBOARD_DEV_CM test change
from finance.services import FinancialAnalyticsService
from investing.models import ManagedTradingAccount
from investing.services.managed_trading_service import ManagedTradingService
from management.models import Meetings, Task, TaskHistory

logger = logging.getLogger(__name__)


def get_user_role(user):
    """Get user role for dashboard customization"""
    if not user.is_authenticated:
        return 'guest'
    
    # Superusers always receive the admin dashboard
    if user.is_superuser:
        return 'admin'
    
    # Get user category
    if hasattr(user, 'category'):
        # Map category numbers to names (matching choices.py definitions)
        category_mapping = {
            1: 'applicant',    # APPLICANT - Want to work for CODA
            2: 'student',      # STUDENT - Taking courses  
            3: 'consultant',   # CONSULTANT - Professionals, advisors, service providers
            4: 'investor',     # INVESTOR - Financial, strategic, KCC members
            5: 'explorer',     # EXPLORER - Visitors, researchers, networkers
        }
        mapped_role = category_mapping.get(user.category)
        if mapped_role:
            return mapped_role

    # Fallback to admin if user is staff without category mapping
    if user.is_staff:
        return 'admin'

    # Default to explorer if no category found
    return 'explorer'


def get_dashboard_config(user_role, user=None):
    """Get dashboard configuration based on user role"""
    configs = {
        'admin': {
            'title': 'Administrator Dashboard',
            'sections': [
                {
                    'title': 'System Overview',
                    'type': 'widget',
                    'template': 'unified_dashboard/widgets/system_overview.html'
                },
                {
                    'title': 'AI Services Analytics',
                    'type': 'widget',
                    'template': 'unified_dashboard/widgets/ai_services_analytics.html'
                },
                {
                    'title': 'Financial Analytics',
                    'type': 'widget',
                    'template': 'unified_dashboard/widgets/financial_analytics.html'
                },
                {
                    'title': 'User Management',
                    'type': 'widget',
                    'template': 'unified_dashboard/widgets/user_management.html'
                },
                {
                    'title': 'Loan Management',
                    'type': 'widget',
                    'template': 'unified_dashboard/widgets/loan_management.html'
                }
            ],
            'quick_actions': [
                {'title': 'AI Configuration', 'url': '/ai_services/diaspora/ai-configuration/', 'icon': 'fas fa-robot'},
                {'title': 'System Analytics', 'url': '/ai_services/diaspora/advanced-analytics/', 'icon': 'fas fa-chart-line'},
                {'title': 'User Management', 'url': '/admin/', 'icon': 'fas fa-users-cog'},
                {'title': 'Loan Management', 'url': '/finance/admin/loan-analytics/', 'icon': 'fas fa-money-bill-wave'},
                {'title': 'Smart Collateral', 'url': '/finance/admin/smart-collateral-dashboard/', 'icon': 'fas fa-shield-alt'},
                {'title': 'Portfolio & Presentations', 'url': '/portfolio/', 'icon': 'fas fa-briefcase'},
                {'title': 'Platform Health', 'url': '/ai_services/diaspora/ai-health/', 'icon': 'fas fa-heartbeat'},
                {'title': 'Management Analytics', 'url': '/management/analytics/', 'icon': 'fas fa-chart-bar'},
                {'title': 'Task Dashboard', 'url': '/management/enhanced-dashboard/', 'icon': 'fas fa-tachometer-alt'},
            ]
        },
        'investor': {
            'title': 'Investor Dashboard',
            'sections': [
                {
                    'title': 'Investment Portfolio',
                    'type': 'widget',
                    'template': 'unified_dashboard/widgets/investment_portfolio.html'
                },
                {
                    'title': 'AI Services Analytics',
                    'type': 'widget',
                    'template': 'unified_dashboard/widgets/ai_services_analytics.html'
                },
                {
                    'title': 'Financial Analytics',
                    'type': 'widget',
                    'template': 'unified_dashboard/widgets/financial_analytics.html'
                }
            ],
            'quick_actions': [
                {'title': 'Investment Dashboard', 'url': '/investing/dashboard/', 'icon': 'fas fa-chart-line'},
                {'title': 'Loan Applications', 'url': '/finance/loan-home/', 'icon': 'fas fa-money-bill-wave'},
                {'title': 'AI Analysis', 'url': '/ai_services/diaspora/', 'icon': 'fas fa-brain'},
                {'title': 'Financial Analytics', 'url': '/finance/analytics/', 'icon': 'fas fa-chart-pie'},
            ]
        },
        'applicant': {
            'title': 'Employee Dashboard',
            'sections': [
                {
                    'title': 'Company Agenda Overview',
                    'type': 'widget',
                    'template': 'unified_dashboard/widgets/employee_company_agenda.html'
                },
                {
                    'title': 'Tasks & Evidence Workspace',
                    'type': 'widget',
                    'template': 'unified_dashboard/widgets/employee_tasks_overview.html'
                },
                {
                    'title': 'HR Services & Policies',
                    'type': 'widget',
                    'template': 'unified_dashboard/widgets/employee_hr_services.html'
                }
            ],
            'quick_actions': [
                {'title': 'Company Agenda', 'url': '/management/companyagenda/', 'icon': 'fas fa-calendar-alt'},
                {'title': 'My Tasks', 'url': '/management/userdashboard/', 'icon': 'fas fa-tasks'},
                {'title': 'Task Dashboard', 'url': '/management/enhanced-dashboard/', 'icon': 'fas fa-tachometer-alt'},
                {'title': 'Analytics', 'url': '/management/analytics/', 'icon': 'fas fa-chart-line'},
                {'title': 'HR Services', 'url': '/hr/', 'icon': 'fas fa-user-tie'},
                {'title': 'Help Center', 'url': '/help/', 'icon': 'fas fa-question-circle'},
            ]
        },
        'student': {
            'title': 'Student Dashboard',
            'sections': [
                {
                    'title': 'Training & Sessions',
                    'type': 'widget',
                    'template': 'unified_dashboard/widgets/student_training_overview.html'
                },
                {
                    'title': 'Learning Progress',
                    'type': 'widget',
                    'template': 'unified_dashboard/widgets/learning_progress.html'
                }
            ],
            'quick_actions': [
                {'title': 'Training Center', 'url': '/professional_services/train/', 'icon': 'fas fa-graduation-cap'},
                {'title': 'Learning Resources', 'url': '/professional_services/train/', 'icon': 'fas fa-book'},
                {'title': 'Job Placement', 'url': '/professional_services/job_tracker/', 'icon': 'fas fa-briefcase'},
                {'title': 'Help Center', 'url': '/help/', 'icon': 'fas fa-question-circle'},
            ]
        },
        'consultant': {
            'title': 'Consultant Dashboard',
            'sections': [
                {
                    'title': 'Interview Management Hub',
                    'type': 'widget',
                    'template': 'unified_dashboard/widgets/consultant_interview_overview.html'
                },
                {
                    'title': 'Service Catalog',
                    'type': 'widget',
                    'template': 'unified_dashboard/widgets/service_catalog.html'
                }
            ],
            'quick_actions': [
                {'title': 'Interview Roles', 'url': '/professional_services/interview_roles/', 'icon': 'fas fa-user-tie'},
                {'title': 'Client Projects', 'url': '/professional_services/interview_roles/', 'icon': 'fas fa-project-diagram'},
                {'title': 'Service Delivery', 'url': '/professional_services/interview_roles/', 'icon': 'fas fa-handshake'},
                {'title': 'Help Center', 'url': '/help/', 'icon': 'fas fa-question-circle'},
            ]
        },
        'explorer': {
            'title': 'Explorer Dashboard',
            'sections': [
                {
                    'title': 'Welcome to CODA',
                    'type': 'widget',
                    'template': 'unified_dashboard/widgets/welcome.html'
                },
                {
                    'title': 'Available Services',
                    'type': 'widget',
                    'template': 'unified_dashboard/widgets/service_catalog.html'
                }
            ],
            'quick_actions': [
                {'title': 'Learn More', 'url': '/about/', 'icon': 'fas fa-info-circle'},
                {'title': 'Services', 'url': '/services/', 'icon': 'fas fa-cogs'},
                {'title': 'Contact Us', 'url': '/contact/', 'icon': 'fas fa-envelope'},
                {'title': 'Help Center', 'url': '/help/', 'icon': 'fas fa-question-circle'},
            ]
        }
    }
    
    config = configs.get(user_role, configs['explorer'])
    
    # Dynamically update URLs that need user-specific data
    if user and user_role == 'student':
        for action in config.get('quick_actions', []):
            if action['title'] == 'Job Placement':
                action['url'] = '/professional_services/job_tracker/' + user.username + '/'
    
    return config


def get_quick_actions(user_role, user=None):
    """Get quick actions based on user role"""
    config = get_dashboard_config(user_role, user)
    return config.get('quick_actions', [])


def get_recent_activities(user):
    """Get recent activities for the user"""
    # This would be implemented based on your activity tracking system
    return []


def get_user_notifications(user):
    """Get user notifications"""
    # This would be implemented based on your notification system
    return []


def unified_dashboard(request):
    """Main unified dashboard view"""
    if not request.user.is_authenticated:
        return redirect('main:layout')
    try:
        user_role = get_user_role(request.user)
        dashboard_config = get_dashboard_config(user_role, request.user)
        
        # Get role-based links and buttons (similar to management system)
        role_based_links = get_role_based_links(request)
        
        # Get quick actions and add backup button for admin users
        quick_actions = get_quick_actions(user_role, request.user)
        if user_role == 'admin' or request.user.is_staff or request.user.is_superuser:
            # Add database backup action for admins
            quick_actions.append({
                'title': 'Database Backup',
                'icon': 'fas fa-database',
                'url': '/dashboard/admin/backup-database/',
            })
        
        # Get accessible dashboards using permission system
        accessible_dashboards = get_accessible_dashboards(request.user)

        financial_summary = {}
        financial_cards = []
        financial_activity = []
        investment_summary = {}
        investment_cards = []
        investment_activity = []

        if user_role in ('admin', 'investor'):
            analytics_service = FinancialAnalyticsService()
            analytics_result = analytics_service.get_admin_loan_dashboard()

            if analytics_result.get('status') == 'success':
                analytics_data = analytics_result.get('data', {})
                summary = analytics_data.get('summary', {})
                summary_numeric = analytics_data.get('summary_numeric', summary)
                financial_summary = summary

                total_lent = summary_numeric.get('total_lent', 0)
                total_outstanding = summary_numeric.get('total_outstanding', 0)
                approval_rate = summary_numeric.get('approval_rate', 0)
                borrower_total = (
                    summary_numeric.get('staff_borrowers', 0)
                    + summary_numeric.get('other_borrowers', 0)
                )

                financial_cards = [
                    {
                        'icon': 'fas fa-dollar-sign text-success',
                        'label': 'Total Lent',
                        'value': total_lent,
                        'prefix': '$',
                        'decimals': 2,
                    },
                    {
                        'icon': 'fas fa-wallet text-warning',
                        'label': 'Outstanding',
                        'value': total_outstanding,
                        'prefix': '$',
                        'decimals': 2,
                    },
                    {
                        'icon': 'fas fa-percentage text-info',
                        'label': 'Approval Rate',
                        'value': approval_rate,
                        'suffix': '%',
                        'decimals': 1,
                    },
                    {
                        'icon': 'fas fa-users text-primary',
                        'label': 'Borrowers',
                        'value': borrower_total,
                        'decimals': 0,
                    },
                ]

                financial_activity = analytics_data.get('recent_rejections', [])[:5]

        if user_role == 'investor':
            accounts = ManagedTradingAccount.objects.filter(client=request.user).prefetch_related(
                'activities', 'positions'
            )

            if accounts.exists():
                managed_service = ManagedTradingService()
                total_balance = Decimal('0')
                total_initial = Decimal('0')
                total_profit = Decimal('0')
                active_plans = accounts.filter(status='active').count()
                maturity_dates = []
                recent_activity = []

                for account in accounts:
                    total_balance += account.current_balance or Decimal('0')
                    total_initial += account.initial_capital or Decimal('0')
                    total_profit += account.total_profit_loss or Decimal('0')

                    summary = managed_service.get_account_summary(account)
                    maturity_dates.extend(
                        [
                            pos.expiration_date
                            for pos in summary['positions']['upcoming_expirations']
                            if getattr(pos, 'expiration_date', None)
                        ]
                    )
                    recent_activity.extend(summary['activity']['recent'])

                roi = Decimal('0')
                if total_initial > 0:
                    roi = ((total_balance - total_initial) / total_initial) * 100

                next_maturity = min(maturity_dates) if maturity_dates else None

                investment_summary = {
                    'total_balance': total_balance,
                    'total_initial': total_initial,
                    'total_profit_loss': total_profit,
                    'roi': roi,
                    'active_plans': active_plans,
                    'next_maturity': next_maturity,
                }

                investment_cards = [
                    {
                        'icon': 'fas fa-chart-line text-success',
                        'label': 'Total Balance',
                        'value': total_balance,
                        'prefix': '$',
                        'decimals': 2,
                    },
                    {
                        'icon': 'fas fa-percentage text-info',
                        'label': 'ROI',
                        'value': roi,
                        'suffix': '%',
                        'decimals': 1,
                    },
                    {
                        'icon': 'fas fa-coins text-warning',
                        'label': 'Active Accounts',
                        'value': active_plans,
                        'decimals': 0,
                    },
                    {
                        'icon': 'fas fa-calendar text-primary',
                        'label': 'Next Expiration',
                        'value': next_maturity,
                        'decimals': None,
                        'date_format': 'M d, Y',
                        'fallback': 'N/A',
                    },
                ]

                investment_activity = sorted(
                    recent_activity,
                    key=lambda activity: getattr(activity, 'timestamp', getattr(activity, 'created_at', timezone.now())),
                    reverse=True,
                )[:5]

        company_agenda_items = []
        employee_task_summary = {}
        employee_task_history = []
        hr_links = []
        daf_current_url = None
        daf_history_url = None
        student_training_links = []
        student_training_sessions = []
        consultant_interview_links = []
        consultant_interview_stats = {}
        consultant_recent_interviews = []

        if user_role in ('applicant', 'admin'):
            meetings_qs = Meetings.objects.filter(is_active=True).order_by('meeting_time')[:5]
            company_agenda_items = [
                {
                    'topic': meeting.meeting_topic or 'Company Meeting',
                    'group': meeting.group.title() if meeting.group else '',
                    'time': meeting.meeting_time,
                    'link': meeting.meeting_link,
                    'description': meeting.meeting_description,
                }
                for meeting in meetings_qs
            ]

            tasks_qs = Task.objects.filter(employee=request.user)
            assigned_count = tasks_qs.count()

            # Task model does not store completion status; fall back to history entries
            completed_count = TaskHistory.objects.filter(employee=request.user).count()
            completed_count = min(completed_count, assigned_count) if assigned_count else completed_count
            pending_count = max(assigned_count - completed_count, 0)

            employee_task_summary = {
                'assigned': assigned_count,
                'completed': completed_count,
                'pending': pending_count,
            }

            history_qs = TaskHistory.objects.filter(employee=request.user).order_by('-submission')[:5]
            employee_task_history = [
                {
                    'activity': history.activity_name,
                    'points': history.point,
                    'submitted': history.submission,
                }
                for history in history_qs
            ]


            query_base = {
                'username': request.user.username,
                'pay_type': 'usertasks',
            }
            daf_current_url = f"{reverse('management:user_pay')}?{urlencode(query_base)}"

            history_query = query_base.copy()
            history_query['pay_type'] = 'usertaskhistory'
            daf_history_url = f"{reverse('management:user_pay')}?{urlencode(history_query)}"

            hr_links = [
                {
                    'title': 'Company Policies',
                    'description': 'Review company-wide policies and guidelines.',
                    'url': reverse('management:policies'),
                    'icon': 'fas fa-book',
                },
                {
                    'title': 'Benefits Overview',
                    'description': 'Explore employee benefits and resources.',
                    'url': reverse('management:benefits'),
                    'icon': 'fas fa-hand-holding-heart',
                },
                {
                    'title': 'Employee Contract',
                    'description': 'View or sign the latest employee contract.',
                    'url': reverse('management:employee_contract'),
                    'icon': 'fas fa-file-signature',
                },
                {
                    'title': 'Meeting Calendar',
                    'description': 'Browse upcoming company meetings.',
                    'url': reverse('management:meetings', kwargs={'status': 'company'}),
                    'icon': 'fas fa-calendar-alt',
                },
            ]
        
        if user_role == 'student':
            student_training_links = [
                {
                    'title': 'Training Center',
                    'description': 'Access curated learning modules and practice assets.',
                    'url': reverse('professional_services:train'),
                    'icon': 'fas fa-chalkboard-teacher',
                },
                {
                    'title': 'Training Schedule',
                    'description': 'Confirm upcoming coaching sessions and DSU events.',
                    'url': reverse('professional_services:Schedule'),
                    'icon': 'fas fa-calendar-check',
                },
                {
                    'title': 'Interview Prep',
                    'description': 'Review question banks and rehearsal resources.',
                    'url': reverse('professional_services:interview_roles'),
                    'icon': 'fas fa-user-tie',
                },
                {
                    'title': 'Job Tracker',
                    'description': 'Track open opportunities and your submissions.',
                    'url': reverse('professional_services:job-list'),
                    'icon': 'fas fa-briefcase',
                },
            ]

            training_sessions_qs = Meetings.objects.filter(
                is_active=True,
                category=3
            ).order_by('created_at')[:5]

            student_training_sessions = [
                {
                    'title': session.meeting_topic or 'Training Session',
                    'group': session.group,
                    'scheduled_time': session.meeting_time,
                    'created_at': getattr(session, 'created_at', None),
                    'link': session.meeting_link,
                }
                for session in training_sessions_qs
            ]

        if user_role == 'consultant':
            from professional_services.models import Interviews, JobRoles, ClientAssessment

            interviews_qs = Interviews.objects.filter(is_active=True).order_by('-upload_date')[:5]

            consultant_recent_interviews = [
                {
                    'category': interview.category,
                    'question_type': interview.question_type,
                    'uploaded_at': interview.upload_date,
                    'link': interview.link,
                }
                for interview in interviews_qs
            ]

            category_breakdown = list(
                Interviews.objects.filter(is_active=True)
                .values('category')
                .annotate(count=Count('id'))
                .order_by('-count')[:5]
            )

            consultant_interview_stats = {
                'total_interviews': Interviews.objects.filter(is_active=True).count(),
                'active_roles': JobRoles.objects.filter(is_active=True).count(),
                'interview_clients': ClientAssessment.objects.filter(category='Interview').count(),
                'top_categories': category_breakdown,
            }

            consultant_interview_links = [
                {
                    'title': 'Manage Prep Questions',
                    'description': 'Review and update interview preparation content.',
                    'url': reverse('professional_services:interview_roles'),
                    'icon': 'fas fa-tasks',
                },
                {
                    'title': 'Upload Interviews',
                    'description': 'Add new interview assignments or recordings.',
                    'url': reverse('professional_services:uploadinterview'),
                    'icon': 'fas fa-upload',
                },
                {
                    'title': 'View Responses',
                    'description': 'Track candidate submissions and follow-ups.',
                    'url': reverse('professional_services:responses'),
                    'icon': 'fas fa-comments',
                },
                {
                    'title': 'Client Assessments',
                    'description': 'Evaluate client readiness and development plans.',
                    'url': reverse('professional_services:dsu'),
                    'icon': 'fas fa-clipboard-check',
                },
            ]
        
        # Simplified context without complex model queries for now
        context = {
            'user_role': user_role,
            'dashboard_config': dashboard_config,
            'role_based_links': role_based_links,
            'quick_actions': quick_actions,
            'accessible_dashboards': accessible_dashboards,
            'recent_activities': get_recent_activities(request.user),
            'notifications': get_user_notifications(request.user),
            'title': 'CODA Command Center - ' + dashboard_config["title"],
            'user': request.user,
            'financial_summary': financial_summary,
            'financial_cards': financial_cards,
            'financial_activity': financial_activity,
            'investment_summary': investment_summary,
            'investment_cards': investment_cards,
            'investment_activity': investment_activity,
            'company_agenda_items': company_agenda_items,
            'employee_task_summary': employee_task_summary,
            'employee_task_history': employee_task_history,
            'hr_links': hr_links,
            'daf_current_url': daf_current_url,
            'daf_history_url': daf_history_url,
            'student_training_links': student_training_links,
            'student_training_sessions': student_training_sessions,
            'consultant_interview_links': consultant_interview_links,
            'consultant_interview_stats': consultant_interview_stats,
            'consultant_recent_interviews': consultant_recent_interviews,
        }
        
        return render(request, 'unified_dashboard/dashboard.html', context)
        
    except Exception as e:
        logger.error("Error in unified dashboard: " + str(e))
        # Redirect to dashboard overview instead of main layout
        return redirect('dashboard:dashboard_overview')


@login_required
def dashboard_overview(request):
    """Dashboard overview page"""
    user_role = get_user_role(request.user)
    dashboard_config = get_dashboard_config(user_role, request.user)
    
    # Add loan statistics for admin users
    loan_stats = {}
    recent_activities = []
    
    if user_role == 'admin':
        from finance.models import LoanApplication
        from django.db.models import Count, Sum, Q
        from django.utils import timezone
        from datetime import timedelta
        
        # Get loan statistics
        loan_stats = {
            'pending_count': LoanApplication.objects.filter(status='pending').count(),
            'approved_count': LoanApplication.objects.filter(status='approved').count(),
            'active_count': LoanApplication.objects.filter(status='active').count(),
            'total_outstanding': LoanApplication.objects.filter(
                status__in=['active', 'approved']
            ).aggregate(total=Sum('amount_requested'))['total'] or 0,
        }
        
        # Get recent loan activities
        recent_loans = LoanApplication.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        ).order_by('-created_at')[:5]
        
        recent_activities = [
            {
                'type': 'New Application',
                'description': f"${loan.amount_requested} loan from {loan.borrower.get_full_name()}",
                'timestamp': loan.created_at
            }
            for loan in recent_loans
        ]
    
    context = {
        'user_role': user_role,
        'dashboard_config': dashboard_config,
        'title': 'Dashboard Overview',
        'loan_stats': loan_stats,
        'recent_activities': recent_activities,
    }
    
    return render(request, 'unified_dashboard/dashboard.html', context)


@login_required
def service_catalog(request):
    """Service catalog page"""
    user_role = get_user_role(request.user)
    services = DashboardService.objects.filter(is_active=True).order_by('order', 'name')
    
    # Filter services based on user role and permissions
    if user_role != 'admin':
        services = services.filter(
            Q(user_roles__contains=[user_role]) | Q(user_roles__isnull=True)
        )
    
    context = {
        'services': services,
        'user_role': user_role,
        'title': 'Service Catalog',
    }
    
    return render(request, 'unified_dashboard/service_catalog.html', context)


@login_required
def user_profile(request):
    """User profile management"""
    user = request.user
    preferences, created = UserDashboardPreferences.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        # Update preferences
        preferences.theme = request.POST.get('theme', preferences.theme)
        preferences.layout = request.POST.get('layout', preferences.layout)
        preferences.notifications_enabled = 'notifications_enabled' in request.POST
        preferences.email_notifications = 'email_notifications' in request.POST
        preferences.auto_refresh = 'auto_refresh' in request.POST
        preferences.refresh_interval = int(request.POST.get('refresh_interval', preferences.refresh_interval))
        preferences.sidebar_collapsed = 'sidebar_collapsed' in request.POST
        preferences.save()
        
        messages.success(request, 'Your preferences have been updated.')
        return redirect('dashboard:user_profile')
    
    context = {
        'user': user,
        'preferences': preferences,
        'title': 'User Profile',
    }
    
    return render(request, 'unified_dashboard/user_profile.html', context)


@login_required
def notifications(request):
    """Notifications page"""
    # This would be implemented based on your notification system
    notifications_list = get_user_notifications(request.user)
    
    context = {
        'notifications': notifications_list,
        'title': 'Notifications',
    }
    
    return render(request, 'unified_dashboard/notifications.html', context)


@login_required
def role_analytics(request):
    """Role-based analytics page"""
    user_role = get_user_role(request.user)
    
    # Get analytics data based on user role
    analytics_data = {}
    
    if user_role == 'admin':
        # Admin analytics
        analytics_data = {
            'total_users': User.objects.count(),
            'active_users': User.objects.filter(is_active=True).count(),
            'recent_signups': User.objects.filter(date_joined__gte=timezone.now().date()).count(),
        }
    else:
        # User-specific analytics
        user_analytics = DashboardAnalytics.objects.filter(user=request.user).order_by('-date')[:30]
        analytics_data = {
            'dashboard_views': sum(analytics.page_views for analytics in user_analytics),
            'time_spent': sum(analytics.time_spent for analytics in user_analytics),
            'services_used': len(set().union(*[analytics.services_accessed for analytics in user_analytics])),
        }
    
    context = {
        'analytics_data': analytics_data,
        'user_role': user_role,
        'title': 'Analytics',
    }
    
    return render(request, 'unified_dashboard/analytics.html', context)


@login_required
def user_settings(request):
    """User settings page"""
    preferences, created = UserDashboardPreferences.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Update settings
        preferences.theme = request.POST.get('theme', preferences.theme)
        preferences.layout = request.POST.get('layout', preferences.layout)
        preferences.notifications_enabled = 'notifications_enabled' in request.POST
        preferences.email_notifications = 'email_notifications' in request.POST
        preferences.auto_refresh = 'auto_refresh' in request.POST
        preferences.refresh_interval = int(request.POST.get('refresh_interval', preferences.refresh_interval))
        preferences.sidebar_collapsed = 'sidebar_collapsed' in request.POST
        preferences.save()
        
        messages.success(request, 'Your settings have been updated.')
        return redirect('dashboard:user_settings')
    
    context = {
        'preferences': preferences,
        'title': 'Settings',
    }
    
    return render(request, 'unified_dashboard/settings.html', context)


@login_required
def add_widget(request):
    """Add a widget to user's dashboard"""
    if request.method == 'POST':
        widget_type = request.POST.get('widget_type')
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        config = json.loads(request.POST.get('config', '{}'))
        
        # Get next position
        last_widget = DashboardWidget.objects.filter(user=request.user).order_by('-position').first()
        position = (last_widget.position + 1) if last_widget else 0
        
        widget = DashboardWidget.objects.create(
            user=request.user,
            widget_type=widget_type,
            title=title,
            description=description,
            position=position,
            config=config
        )
        
        return JsonResponse({'success': True, 'widget_id': widget.id})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def remove_widget(request, widget_id):
    """Remove a widget from user's dashboard"""
    widget = get_object_or_404(DashboardWidget, id=widget_id, user=request.user)
    widget.delete()
    
    return JsonResponse({'success': True})


@login_required
def reorder_widgets(request):
    """Reorder widgets on user's dashboard"""
    if request.method == 'POST':
        widget_ids = request.POST.getlist('widget_ids[]')
        
        for index, widget_id in enumerate(widget_ids):
            DashboardWidget.objects.filter(id=widget_id, user=request.user).update(position=index)
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def track_service_access(request, service_id):
    """Track user access to a service"""
    service = get_object_or_404(DashboardService, id=service_id)
    
    access, created = UserServiceAccess.objects.get_or_create(
        user=request.user,
        service=service,
        defaults={'access_count': 0}
    )
    
    access.access_count += 1
    access.last_accessed = timezone.now()
    access.save()
    
    return JsonResponse({'success': True})


def get_role_based_links(request):
    """Get role-based links and buttons similar to management system"""
    from django.urls import reverse
    from urllib.parse import urlencode
    
    user = request.user
    
    # Debug logging
    print("DEBUG: User category: " + str(user.category) + ", is_staff: " + str(user.is_staff) + ", is_superuser: " + str(user.is_superuser))
    
    links = {
        'Edit Profile': reverse('main:update_profile', args=[user.profile.id]),
        # 'Make a Payment': reverse('finance:unified_method_selection'),  # TEMPORARILY DISABLED - URL not available
    }
    # Staff users get management-specific links (prioritize staff status over category)
    if user.is_staff:
        links.update({
            'Company Agenda': reverse('management:companyagenda'),
            'My DAF (Current)': reverse('management:user_pay') + '?' + urlencode({'username': user.username, 'pay_type': 'usertasks'}),
            'Last DAF (History)': reverse('management:user_pay') + '?' + urlencode({'username': user.username, 'pay_type': 'usertaskhistory'}),
            'Tasks': reverse('management:tasks'),
            'My Evidence': reverse('management:user_evidence') + '?' + urlencode({'username': user.username}),
            'Evidence Inbox': reverse('management:user_evidence'),
            'My Sessions': reverse('management:user_session', args=[user.username]),
            'My Time': reverse('accounts:account-profile', args=[user]),
            'My Meetings': reverse('management:meetings', kwargs={'status': 'company 2'}),
            'My Schedule': reverse('main:my_availability'),
            'Apply for Loan': reverse('finance:loan-home'),
            # Phase 3: Analytics links
            'Task Dashboard': reverse('management:enhanced-dashboard'),
            'Analytics': reverse('management:analytics-dashboard'),
        })
    # Category-specific links (only for non-staff users)
    elif user.category == 1:  # Job Applicant
        links.update({
            'My Application': reverse('application:policies'),
            'My Interview': reverse('application:interview'),
            'Apply for Internship': reverse('main:contact'),
            'Apply for Training': reverse('main:contact'),
            'Company Policies': reverse('application:policies'),
        })
    elif user.category == 2:  # Student
        print("DEBUG: Student category logic executed")
        # Base links for all students
        links.update({
            'Training Dashboard': reverse('professional_services:train'),
            'Job Placement': reverse('professional_services:userjoblist', args=[user.username]),
            'My Sessions': reverse('management:user_session', args=[user.username]),
            'My Responses': reverse('professional_services:student_feedback'),
        })
        
        # Add subcategory-specific links
        if user.sub_category == 1:  # DATA_ANALYTICS
            links.update({
                'Data Analysis Training': reverse('professional_services:bitraining'),
                'Analytics Tools': reverse('professional_services:train'),
            })
        elif user.sub_category == 2:  # PROGRAMMING
            links.update({
                'Programming Courses': reverse('professional_services:bitraining'),
                'Code Practice': reverse('professional_services:train'),
            })
        elif user.sub_category == 3:  # OTHER
            links.update({
                'Business Training': reverse('professional_services:bitraining'),
                'General Courses': reverse('professional_services:train'),
            })
            
    elif user.category == 3:  # Consultant
        print("DEBUG: Consultant category logic executed")
        # Base links for all consultants
        links.update({
            'Interview Management': reverse('professional_services:interview_roles'),
            'Client Projects': reverse('professional_services:interview_roles'),
            'Service Delivery': reverse('professional_services:interview_roles'),
        })
        
        # Add subcategory-specific links
        if user.sub_category == 1:  # TECHNICAL
            links.update({
                'Technical Resources': reverse('professional_services:bitraining'),
                'System Architecture': reverse('professional_services:train'),
            })
        elif user.sub_category == 2:  # BUSINESS
            links.update({
                'Business Tools': reverse('professional_services:bitraining'),
                'Strategy Resources': reverse('professional_services:train'),
            })
        elif user.sub_category == 3:  # CAREER
            links.update({
                'Career Development': reverse('professional_services:bitraining'),
                'Job Placement Tools': reverse('professional_services:train'),
            })
        elif user.sub_category == 4:  # PROJECT
            links.update({
                'Project Management': reverse('professional_services:bitraining'),
                'Implementation Tools': reverse('professional_services:train'),
            })
            
    elif user.category == 4:  # Investor
        links.update({
            # 'Investment Dashboard': reverse('investing:investment_dashboard'),
            'Apply for Investment': reverse('investing:apply_for_investment'),
            'Investment Plans': reverse('investing:investment_plan_list'),
            'Apply for Loan': reverse('finance:loan-home'),
        })
    elif user.category == 5:  # Explorer
        print("DEBUG: Explorer category logic executed")
        # Base links for all explorers
        links.update({
            'Learn More': reverse('main:about'),
            'Services': reverse('main:services'),
            'Contact Us': reverse('main:contact'),
            'Help Center': reverse('main:help'),
        })
    
    print("DEBUG: Final links for user: " + str(links))
    return links


@login_required
def unified_department_view(request, department_slug=None):
    """
    Unified department view that handles both admin and staff views
    Consolidates all department functionality into one place
    """
    from shared_core.users import Department
    from management.models import SubCategory, Link
    from management.views import defined_links
    
    # Check user role
    is_admin = request.user.is_superuser or request.user.is_admin
    is_staff = request.user.is_staff and not is_admin
    
    # If no department specified, show role-appropriate view
    if not department_slug:
        if is_admin:
            # Admin: Redirect to management companyagenda for now
            return redirect('management:companyagenda')
        elif is_staff:
            # Staff: Show HR department by default
            department_slug = 'hr-department'
        else:
            # Regular user: Redirect to main dashboard
            return redirect('dashboard:unified_dashboard')
    
    # Get the department by slug
    try:
        department = Department.objects.get(slug=department_slug, is_active=True)
    except Department.DoesNotExist:
        # Fallback to HR department
        try:
            department = Department.objects.get(name="HR Department", is_active=True)
        except Department.DoesNotExist:
            return redirect('dashboard:unified_dashboard')
    
    # Get all departments for navigation
    all_departments = Department.objects.filter(is_active=True).order_by('name')
    
    # Get real subcategories and links from database
    subcategories_with_links = []
    for subcategory in department.subcategory_set.all():
        subcategory_links = subcategory.link_set.all()
        if subcategory_links.exists():
            subcategories_with_links.append((subcategory, subcategory_links))
    
    # Get user role for dashboard config
    user_role = 'admin' if is_admin else 'staff' if is_staff else 'user'
    
    # Prepare context
    context = {
        'header_links': defined_links(request),
        'title': department.name + ' - Department View',
        'categories_with_links': [(department, subcategories_with_links)],
        'is_admin': is_admin,
        'is_staff': is_staff,
        'user_role': user_role,
        'department': department,
        'all_departments': all_departments,
        'is_department_view': True,
    }
    
    try:
        return render(request, 'unified_dashboard/department_unified.html', context)
    except Exception as e:
        # Debug: Return error details
        from django.http import HttpResponse
        return HttpResponse("Error in unified_department_view: " + str(e), status=500)


# Admin utility views
def is_admin_user(user):
    """Check if user is admin/staff/superuser"""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def get_accessible_dashboards(user):
    """
    Get list of dashboards user has access to.
    Uses the centralized permission system.
    """
    try:
        from core.permissions import get_user_dashboards
        return get_user_dashboards(user)
    except ImportError:
        try:
            from accounts.permissions import get_user_dashboards
            return get_user_dashboards(user)
        except ImportError:
            # Fallback if permissions not available
            return []


@login_required
@user_passes_test(is_admin_user)
def backup_database(request):
    """Trigger database backup to Google Drive (admin only)"""
    if request.method == 'POST':
        try:
            from platform_services.database_service import DatabaseService
            from platform_services.google_drive_service import GoogleDriveBackupService
            
            # Initialize services
            db_service = DatabaseService()
            drive_service = GoogleDriveBackupService()
            
            # Run backup workflow
            logger.info(f"Database backup initiated by {request.user.username}")
            result = drive_service.backup_and_upload(
                database_service=db_service,
                keep_count=2
            )
            
            if result.get('success'):
                messages.success(
                    request,
                    f"✅ Database backup completed successfully! "
                    f"({result.get('backup_size_mb', 0)} MB uploaded to Google Drive)"
                )
                if result.get('deleted_count', 0) > 0:
                    messages.info(
                        request,
                        f"🧹 Cleaned up {result['deleted_count']} old backup(s)"
                    )
            else:
                error_msg = result.get('error', 'Unknown error')
                messages.error(request, f"❌ Backup failed: {error_msg}")
                logger.error(f"Backup failed for {request.user.username}: {error_msg}")
            
        except Exception as e:
            messages.error(request, f"❌ Backup error: {str(e)}")
            logger.error(f"Backup exception for {request.user.username}: {e}", exc_info=True)
        
        return redirect('dashboard:unified_dashboard')
    
    # GET request - show confirmation page
    context = {
        'title': 'Database Backup',
        'user': request.user,
    }
    return render(request, 'unified_dashboard/backup_confirm.html', context)