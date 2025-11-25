"""
Centralized Permission System for CODA

Provides decorators and utilities for role-based access control across all apps.
Consolidates permission checking logic in one place.

This is the main location for permissions. If core.permissions exists, it will
import from there for backward compatibility.
"""

# Try to import from core first (if it exists), otherwise define here
try:
    from core.permissions import *
except ImportError:
    # Define permissions here if core doesn't exist
    from functools import wraps
    from django.shortcuts import redirect
    from django.contrib.auth.decorators import user_passes_test
    from django.contrib import messages
    from django.core.exceptions import PermissionDenied
    from django.http import JsonResponse
    import logging

    logger = logging.getLogger(__name__)


    # ============================================================================
    # PERMISSION CHECK FUNCTIONS
    # ============================================================================

    def is_admin(user):
        """Check if user is admin (staff or superuser)"""
        return user.is_authenticated and (user.is_staff or user.is_superuser)


    def is_superuser(user):
        """Check if user is superuser"""
        return user.is_authenticated and user.is_superuser


    def is_staff(user):
        """Check if user is staff"""
        return user.is_authenticated and user.is_staff


    def is_employee(user):
        """Check if user is an employee (staff or applicant category)"""
        if not user.is_authenticated:
            return False
        if user.is_staff:
            return True
        if hasattr(user, 'category'):
            return user.category == 1  # APPLICANT
        return False


    def is_investor(user):
        """Check if user is an investor"""
        if not user.is_authenticated:
            return False
        if hasattr(user, 'category'):
            return user.category == 4  # INVESTOR
        return False


    def is_student(user):
        """Check if user is a student"""
        if not user.is_authenticated:
            return False
        if hasattr(user, 'category'):
            return user.category == 2  # STUDENT
        return False


    def is_consultant(user):
        """Check if user is a consultant"""
        if not user.is_authenticated:
            return False
        if hasattr(user, 'category'):
            return user.category == 3  # CONSULTANT
        return False


    def is_finance_staff(user):
        """Check if user has finance access (staff or finance department)"""
        if not user.is_authenticated:
            return False
        if user.is_staff or user.is_superuser:
            return True
        # Check if user is in finance department
        if hasattr(user, 'profile') and hasattr(user.profile, 'department'):
            if user.profile.department:
                dept_name = user.profile.department.name.lower()
                return 'finance' in dept_name or 'accounting' in dept_name
        return False


    def is_manager(user):
        """Check if user is a manager (has department management permissions)"""
        if not user.is_authenticated:
            return False
        if user.is_staff or user.is_superuser:
            return True
        # Check if user is a department head
        if hasattr(user, 'profile') and hasattr(user.profile, 'department'):
            if user.profile.department:
                # Add logic to check if user is department head
                # This would require a Department model with head field
                pass
        return False


    def has_dashboard_access(user, dashboard_name):
        """
        Check if user has access to a specific dashboard.
        
        Args:
            user: User object
            dashboard_name: Name of dashboard (e.g., 'task', 'budget', 'analytics')
        
        Returns:
            bool: True if user has access
        """
        if not user.is_authenticated:
            return False
        
        # Admin has access to everything
        if is_admin(user):
            return True
        
        # Dashboard-specific access rules
        dashboard_rules = {
            'task': is_employee,
            'analytics': is_employee,
            'budget': is_finance_staff,
            'finance': is_finance_staff,
            'investment': is_investor,
            'investing': is_investor,
            'compliance': is_manager,
            'salary': is_finance_staff,
            'loan': is_finance_staff,
            'payment': lambda u: u.is_authenticated,  # All authenticated users
        }
        
        check_func = dashboard_rules.get(dashboard_name.lower())
        if check_func:
            return check_func(user)
        
        # Default: staff only
        return is_staff(user)


    # ============================================================================
    # PERMISSION DECORATORS
    # ============================================================================

    def require_admin(view_func):
        """Decorator: Require admin (staff or superuser) access"""
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not is_admin(request.user):
                messages.error(request, "You do not have permission to access this page.")
                return redirect('dashboard:unified_dashboard')
            return view_func(request, *args, **kwargs)
        return wrapper


    def require_superuser(view_func):
        """Decorator: Require superuser access"""
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not is_superuser(request.user):
                messages.error(request, "Superuser access required.")
                return redirect('dashboard:unified_dashboard')
            return view_func(request, *args, **kwargs)
        return wrapper


    def require_staff(view_func):
        """Decorator: Require staff access"""
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not is_staff(request.user):
                messages.error(request, "Staff access required.")
                return redirect('dashboard:unified_dashboard')
            return view_func(request, *args, **kwargs)
        return wrapper


    def require_employee(view_func):
        """Decorator: Require employee access (staff or applicant)"""
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not is_employee(request.user):
                messages.error(request, "Employee access required.")
                return redirect('dashboard:unified_dashboard')
            return view_func(request, *args, **kwargs)
        return wrapper


    def require_finance_staff(view_func):
        """Decorator: Require finance staff access"""
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not is_finance_staff(request.user):
                messages.error(request, "Finance staff access required.")
                return redirect('dashboard:unified_dashboard')
            return view_func(request, *args, **kwargs)
        return wrapper


    def require_manager(view_func):
        """Decorator: Require manager access"""
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not is_manager(request.user):
                messages.error(request, "Manager access required.")
                return redirect('dashboard:unified_dashboard')
            return view_func(request, *args, **kwargs)
        return wrapper


    def require_investor(view_func):
        """Decorator: Require investor access"""
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not is_investor(request.user):
                messages.error(request, "Investor access required.")
                return redirect('dashboard:unified_dashboard')
            return view_func(request, *args, **kwargs)
        return wrapper


    def require_dashboard_access(dashboard_name):
        """
        Decorator factory: Require access to specific dashboard.
        
        Usage:
            @require_dashboard_access('task')
            def my_view(request):
                ...
        """
        def decorator(view_func):
            @wraps(view_func)
            def wrapper(request, *args, **kwargs):
                if not has_dashboard_access(request.user, dashboard_name):
                    messages.error(request, f"You do not have access to the {dashboard_name} dashboard.")
                    return redirect('dashboard:unified_dashboard')
                return view_func(request, *args, **kwargs)
            return wrapper
        return decorator


    # ============================================================================
    # UTILITY FUNCTIONS
    # ============================================================================

    def get_user_dashboards(user):
        """
        Get list of dashboards user has access to.
        
        Returns:
            list: List of dashboard dictionaries with 'name', 'url', 'icon', 'title'
        """
        dashboards = []
        
        if not user.is_authenticated:
            return dashboards
        
        # All authenticated users - Removed 'Main Dashboard' (redundant on /dashboard page)
        # dashboards.append({
        #     'name': 'unified',
        #     'title': 'Main Dashboard',
        #     'url': '/dashboard/',
        #     'icon': 'fas fa-tachometer-alt'
        # })
        
        # Employee dashboards - Removed 'Analytics' and 'Task History' per user request
        if is_employee(user):
            dashboards.append({
                'name': 'task',
                'title': 'Task Dashboard',
                'url': '/management/enhanced-dashboard/',
                'icon': 'fas fa-tasks'
            })
            # Removed Analytics button - can be accessed via other navigation
            # dashboards.append({
            #     'name': 'analytics',
            #     'title': 'Analytics',
            #     'url': '/management/analytics/',
            #     'icon': 'fas fa-chart-bar'
            # })
            # Removed Task History button - can be accessed via Task Dashboard
            # dashboards.append({
            #     'name': 'task_history',
            #     'title': 'Task History',
            #     'url': '/management/task-history/',
            #     'icon': 'fas fa-history'
            # })
        
        # Finance dashboards
        if is_finance_staff(user):
            dashboards.append({
                'name': 'budget',
                'title': 'Budget Dashboard',
                'url': '/finance/budget-dashboard/coda/',
                'icon': 'fas fa-dollar-sign'
            })
            dashboards.append({
                'name': 'payment',
                'title': 'Payments',
                'url': '/finance/my-payments/',
                'icon': 'fas fa-credit-card'
            })
        
        # Investment dashboards
        if is_investor(user) or is_admin(user):
            dashboards.append({
                'name': 'investment',
                'title': 'Investment Dashboard',
                'url': '/investing/dashboard/',
                'icon': 'fas fa-chart-line'
            })
        
        # Admin-only dashboards
        if is_admin(user):
            dashboards.append({
                'name': 'admin_controls',
                'title': 'Admin Controls',
                'url': '/finance/admin/controls-dashboard/',
                'icon': 'fas fa-cog'
            })
            dashboards.append({
                'name': 'automation',
                'title': 'Automation',
                'url': '/finance/automation/',
                'icon': 'fas fa-robot'
            })
        
        return dashboards


    def check_dashboard_permission(user, dashboard_name):
        """
        Check if user has permission to access a dashboard.
        
        Args:
            user: User object
            dashboard_name: Name of dashboard
        
        Returns:
            tuple: (has_access: bool, error_message: str)
        """
        if not user.is_authenticated:
            return False, "Please log in to access this dashboard."
        
        if has_dashboard_access(user, dashboard_name):
            return True, None
        
        return False, f"You do not have permission to access the {dashboard_name} dashboard."

