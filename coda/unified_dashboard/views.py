from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count
from django.core.paginator import Paginator
import json
import logging

from .models import DashboardWidget, UserDashboardPreferences, DashboardService, UserServiceAccess, DashboardAnalytics
from accounts.models import CategoryChoices

logger = logging.getLogger(__name__)


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


def get_dashboard_config(user_role):
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
                }
            ],
            'quick_actions': [
                {'title': 'AI Configuration', 'url': '/ai_services/diaspora/ai-configuration/', 'icon': 'fas fa-robot'},
                {'title': 'System Analytics', 'url': '/ai_services/diaspora/advanced-analytics/', 'icon': 'fas fa-chart-line'},
                {'title': 'User Management', 'url': '/admin/', 'icon': 'fas fa-users-cog'},
                {'title': 'Platform Health', 'url': '/ai_services/diaspora/ai-health/', 'icon': 'fas fa-heartbeat'},
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
                    'title': 'Company Agenda',
                    'type': 'iframe',
                    'url': '/management/companyagenda/'
                },
                {
                    'title': 'Task Management',
                    'type': 'iframe',
                    'url': '/management/userdashboard/'
                },
                {
                    'title': 'HR Services',
                    'type': 'iframe',
                    'url': '/hr/'
                }
            ],
            'quick_actions': [
                {'title': 'Company Agenda', 'url': '/management/companyagenda/', 'icon': 'fas fa-calendar-alt'},
                {'title': 'My Tasks', 'url': '/management/userdashboard/', 'icon': 'fas fa-tasks'},
                {'title': 'HR Services', 'url': '/hr/', 'icon': 'fas fa-user-tie'},
                {'title': 'Help Center', 'url': '/help/', 'icon': 'fas fa-question-circle'},
            ]
        },
        'student': {
            'title': 'Student Dashboard',
            'sections': [
                {
                    'title': 'Training Dashboard',
                    'type': 'iframe',
                    'url': '/professional_services/train/'
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
                {'title': 'Progress Tracking', 'url': '/professional_services/train/', 'icon': 'fas fa-chart-bar'},
                {'title': 'Help Center', 'url': '/help/', 'icon': 'fas fa-question-circle'},
            ]
        },
        'consultant': {
            'title': 'Consultant Dashboard',
            'sections': [
                {
                    'title': 'Interview Management',
                    'type': 'iframe',
                    'url': '/professional_services/interview_roles/'
                },
                {
                    'title': 'Client Projects',
                    'type': 'widget',
                    'template': 'unified_dashboard/widgets/client_projects.html'
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
    
    return configs.get(user_role, configs['explorer'])


def get_quick_actions(user_role):
    """Get quick actions based on user role"""
    config = get_dashboard_config(user_role)
    return config.get('quick_actions', [])


def get_recent_activities(user):
    """Get recent activities for the user"""
    # This would be implemented based on your activity tracking system
    return []


def get_user_notifications(user):
    """Get user notifications"""
    # This would be implemented based on your notification system
    return []


@login_required
def unified_dashboard(request):
    """Main unified dashboard view"""
    try:
        user_role = get_user_role(request.user)
        dashboard_config = get_dashboard_config(user_role)
        
        # Get role-based links and buttons (similar to management system)
        role_based_links = get_role_based_links(request)
        
        # Simplified context without complex model queries for now
        context = {
            'user_role': user_role,
            'dashboard_config': dashboard_config,
            'role_based_links': role_based_links,
            'quick_actions': get_quick_actions(user_role),
            'recent_activities': get_recent_activities(request.user),
            'notifications': get_user_notifications(request.user),
            'title': f'CODA Command Center - {dashboard_config["title"]}',
            'user': request.user,
        }
        
        return render(request, 'unified_dashboard/dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Error in unified dashboard: {str(e)}")
        # Don't use messages.error to avoid middleware issues
        return redirect('main:layout')


@login_required
def dashboard_overview(request):
    """Dashboard overview page"""
    user_role = get_user_role(request.user)
    dashboard_config = get_dashboard_config(user_role)
    
    context = {
        'user_role': user_role,
        'dashboard_config': dashboard_config,
        'title': 'Dashboard Overview',
    }
    
    return render(request, 'unified_dashboard/overview.html', context)


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
    links = {
        'Edit Profile': reverse('main:update_profile', args=[user.profile.id]),
        'Make a Payment': reverse('finance:unified_method_selection'),
    }
    # Staff users get management-specific links (prioritize staff status over category)
    if user.is_staff:
        links.update({
            'My DAF': reverse('management:user_pay') + '?' + urlencode({'username': user.username, 'pay_type': 'usertasks'}),
            'Last DAF': reverse('management:user_pay') + '?' + urlencode({'username': user.username, 'pay_type': 'usertaskhistory'}),
            'Tasks': reverse('management:tasks'),
            # 'Task History': reverse('management:taskhistory'),
            'My Evidence': reverse('management:user_evidence') + '?' + urlencode({'username': user.username}),
            'Evidence': reverse('management:user_evidence'),
            'My Sessions': reverse('management:user_session', args=[user.username]),
            'My Time': reverse('accounts:account-profile', args=[user]),
            'My Meetings': reverse('management:meetings', kwargs={'status': 'company'}),
            'My Schedule': reverse('main:my_availability'),
            'Apply for Loan': reverse('finance:loan-home'),
        })
    # Category-specific links (only for non-staff users)
    elif user.category == 1:  # Job Applicant
        links.update({
            'My Application': reverse('application:policies'),
            'My Interview': reverse('application:interview'),
            'Apply for Internship': reverse('main:contact'),
            'Apply for Training': reverse('main:contact'),
            'Company Policies': reverse('application:policies'),
            'Apply for Loan': reverse('finance:loan-home'),
        })
    elif user.category == 2:  # Staff (additional to is_staff check above)
        links.update({
            'Apply for Loan': reverse('finance:loan-home'),
        })
    elif user.category == 3:  # Student
        # Base links for all students
        links.update({
            'Training Dashboard': reverse('professional_services:train'),
            'My Progress': reverse('professional_services:student_feedback'),
            'My Sessions': reverse('management:user_session', args=[user.username]),
            'My Responses': reverse('professional_services:student_feedback'),
            'Apply for Loan': reverse('finance:loan-home'),
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
    elif user.category == 4:  # Investor
        links.update({
            'Investment Dashboard': reverse('investing:investment_dashboard'),
            'Apply for Investment': reverse('investing:apply_for_investment'),
            'Investment Plans': reverse('investing:investment_plan_list'),
            'Apply for Loan': reverse('finance:loan-home'),
        })
    elif user.category == 5:  # Vendor
        links.update({
            'Apply for Loan': reverse('finance:loan-home'),
        })
    elif user.category in [6, 7]:  # General User, Explorer
        links.update({
            'Apply for Loan': reverse('finance:loan-home'),
        })
    
    return links