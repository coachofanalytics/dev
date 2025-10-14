from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.urls import reverse
import json
import logging

from .models import DashboardWidget, UserDashboardPreferences, DashboardService, UserServiceAccess, DashboardAnalytics
from accounts.models import CategoryChoices

logger = logging.getLogger(__name__)


def get_user_role(user):
    """Get user role for dashboard customization"""
    if not user or not user.is_authenticated:
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
                {'title': 'AI Configuration', 'url': '/ai_services/', 'icon': 'fas fa-cog'},
                {'title': 'System Analytics', 'url': '/analytics/', 'icon': 'fas fa-chart-line'},
                {'title': 'User Management', 'url': '/accounts/', 'icon': 'fas fa-users'},
                {'title': 'Platform Health', 'url': '/monitoring/', 'icon': 'fas fa-heartbeat'},
            ]
        },
        'applicant': {
            'title': 'Applicant Dashboard',
            'sections': [
                {
                    'title': 'My Applications',
                    'type': 'widget',
                    'template': 'unified_dashboard/widgets/service_catalog.html'
                }
            ],
            'quick_actions': [
                {'title': 'Apply for Loan', 'url': '/finance/loan-application/', 'icon': 'fas fa-money-bill-wave'},
                {'title': 'My Profile', 'url': '/accounts/profile/', 'icon': 'fas fa-user'},
            ]
        },
        'student': {
            'title': 'Student Dashboard',
            'sections': [
                {
                    'title': 'My Learning',
                    'type': 'widget',
                    'template': 'unified_dashboard/widgets/service_catalog.html'
                }
            ],
            'quick_actions': [
                {'title': 'My Sessions', 'url': '/training/', 'icon': 'fas fa-graduation-cap'},
                {'title': 'My Time', 'url': '/time-tracking/', 'icon': 'fas fa-clock'},
            ]
        },
        'consultant': {
            'title': 'Consultant Dashboard',
            'sections': [
                {
                    'title': 'My Services',
                    'type': 'widget',
                    'template': 'unified_dashboard/widgets/service_catalog.html'
                }
            ],
            'quick_actions': [
                {'title': 'My Meetings', 'url': '/meetings/', 'icon': 'fas fa-calendar'},
                {'title': 'My Schedule', 'url': '/schedule/', 'icon': 'fas fa-calendar-alt'},
            ]
        },
        'investor': {
            'title': 'Investor Dashboard',
            'sections': [
                {
                    'title': 'My Portfolio',
                    'type': 'widget',
                    'template': 'unified_dashboard/widgets/investment_portfolio.html'
                }
            ],
            'quick_actions': [
                {'title': 'My DAF', 'url': '/investing/daf/', 'icon': 'fas fa-chart-pie'},
                {'title': 'Last DAF', 'url': '/investing/last-daf/', 'icon': 'fas fa-history'},
            ]
        },
        'explorer': {
            'title': 'Explorer Dashboard',
            'sections': [
                {
                    'title': 'Available Services',
                    'type': 'widget',
                    'template': 'unified_dashboard/widgets/service_catalog.html'
                }
            ],
            'quick_actions': [
                {'title': 'Explore Services', 'url': '/services/', 'icon': 'fas fa-compass'},
                {'title': 'My Evidence', 'url': '/evidence/', 'icon': 'fas fa-file-alt'},
            ]
        }
    }
    
    return configs.get(user_role, configs['explorer'])


def get_quick_actions(user_role):
    """Get quick actions based on user role"""
    config = get_dashboard_config(user_role)
    actions = list(config.get('quick_actions', []))
    
    return actions


@login_required
def unified_dashboard(request):
    """Main unified dashboard view"""
    try:
        # Get user role
        user_role = get_user_role(request.user)
        
        # Get dashboard configuration
        dashboard_config = get_dashboard_config(user_role)
        
        # Get quick actions
        quick_actions = get_quick_actions(user_role)
        
        # Get role-based links (from management system)
        role_based_links = {}
        
        # If user is superuser, show all services
        if request.user.is_superuser:
            role_based_links.update({
                # Applicant services
                'Edit Profile': '/accounts/profile/',
                'Make a Payment': '/finance/payment/',
                'My Evidence': '/evidence/',
                'Evidence': '/evidence/',
                
                # Student services
                'My Sessions': '/training/',
                'My Time': '/time-tracking/',
                'My Meetings': '/meetings/',
                'My Schedule': '/schedule/',
                
                # Investor services
                'My DAF': '/investing/daf/',
                'Last DAF': '/investing/last-daf/',
                
                # Consultant services
                'Professional Services': '/professional_services/',
                'Job Tracking': '/professional_services/job-tracking/',
            })
        elif hasattr(request.user, 'category'):
            # Add category-specific links for regular users
            if request.user.category == 1:  # Applicant
                role_based_links.update({
                    'Edit Profile': '/accounts/profile/',
                    'Make a Payment': '/finance/payment/',
                    'My Evidence': '/evidence/',
                    'Evidence': '/evidence/',
                })
            elif request.user.category == 2:  # Student
                role_based_links.update({
                    'My Sessions': '/training/',
                    'My Time': '/time-tracking/',
                    'My Meetings': '/meetings/',
                    'My Schedule': '/schedule/',
                })
            elif request.user.category == 4:  # Investor
                role_based_links.update({
                    'My DAF': '/investing/daf/',
                    'Last DAF': '/investing/last-daf/',
                    'My Evidence': '/evidence/',
                    'Evidence': '/evidence/',
                })
        
        # Default links for all users
        role_based_links.update({
            'Edit Profile': '/accounts/profile/',
            'Apply for Loan': '/finance/loan-application/',
            'My Tasks': '/management/tasks/',
            'Task History': '/management/tasks/',
        })
        
        # Get user preferences
        preferences = {
            'theme': 'light',
            'auto_refresh': False,
            'refresh_interval': 30
        }
        
        # Get recent activities (placeholder)
        recent_activities = []
        
        # Get notifications (placeholder)
        notifications = []
        
        # Get widgets (placeholder)
        widgets = []
        
        context = {
            'title': 'CODA Dashboard',
            'user_role': user_role,
            'dashboard_config': dashboard_config,
            'quick_actions': quick_actions,
            'role_based_links': role_based_links,
            'preferences': preferences,
            'recent_activities': recent_activities,
            'notifications': notifications,
            'widgets': widgets,
        }
        
        return render(request, 'unified_dashboard/dashboard.html', context)
        
    except Exception as e:
        logger.error("Dashboard error: {}".format(e))
        # Return minimal dashboard on error
        context = {
            'title': 'CODA Dashboard',
            'user_role': 'explorer',
            'dashboard_config': {'title': 'Dashboard', 'sections': []},
            'quick_actions': [],
            'role_based_links': {
                'Edit Profile': '/accounts/profile/',
                'Apply for Loan': '/finance/loan-application/',
                'My Tasks': '/management/tasks/',
                'Task History': '/management/tasks/',
                'My Evidence': '/evidence/',
                'My Sessions': '/training/',
                'My DAF': '/investing/daf/',
            },
            'preferences': {'theme': 'light', 'auto_refresh': False, 'refresh_interval': 30},
            'recent_activities': [],
            'notifications': [],
            'widgets': [],
        }
        return render(request, 'unified_dashboard/dashboard.html', context)


@login_required
def service_access(request):
    """Track service access for analytics"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            service_name = data.get('service_name')
            timestamp = data.get('timestamp')
            
            # Log service access
            logger.info("Service access: {} by {} at {}".format(service_name, request.user.username, timestamp))
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            logger.error("Service access tracking error: {}".format(e))
            return JsonResponse({'status': 'error'}, status=400)
    
    return JsonResponse({'status': 'error'}, status=405)


@login_required
def widget_remove(request, widget_id):
    """Remove a widget from user dashboard"""
    if request.method == 'POST':
        try:
            widget = get_object_or_404(DashboardWidget, id=widget_id, user=request.user)
            widget.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            logger.error("Widget removal error: {}".format(e))
            return JsonResponse({'success': False})
    
    return JsonResponse({'success': False}, status=405)


@login_required
def dashboard_settings(request):
    """Update dashboard settings"""
    if request.method == 'POST':
        try:
            theme = request.POST.get('theme', 'light')
            auto_refresh = request.POST.get('auto_refresh') == 'on'
            refresh_interval = int(request.POST.get('refresh_interval', 30))
            
            # Update user preferences
            preferences, created = UserDashboardPreferences.objects.get_or_create(
                user=request.user,
                defaults={
                    'theme': theme,
                    'auto_refresh': auto_refresh,
                    'refresh_interval': refresh_interval
                }
            )
            
            if not created:
                preferences.theme = theme
                preferences.auto_refresh = auto_refresh
                preferences.refresh_interval = refresh_interval
                preferences.save()
            
            messages.success(request, 'Dashboard settings updated successfully!')
            return redirect('dashboard:unified_dashboard')
            
        except Exception as e:
            logger.error("Dashboard settings error: {}".format(e))
            messages.error(request, 'Error updating dashboard settings.')
    
    return redirect('dashboard:unified_dashboard')