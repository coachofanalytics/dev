"""
Reusable User Queryset Filters for Forms and Admin

This module provides standardized queryset functions for filtering users by category and status.
Use these functions in Django forms (__init__) and admin (formfield_for_foreignkey) to ensure
consistent user filtering across the entire CODA platform.

Problem Solved:
    - Forms were showing ALL users (100+) instead of filtered users (10-20)
    - Dropdowns included inactive users, wrong categories (students in investor fields, etc.)
    - Each app was implementing filtering differently (or not at all)

Solution:
    - Centralized queryset functions based on UserCategory and is_active
    - Consistent ordering (first_name, last_name)
    - Easy to use in any form or admin class

Usage in Forms:
    ```python
    from accounts.utilities.user_querysets import get_active_staff_queryset
    
    class MyForm(forms.ModelForm):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields['manager'].queryset = get_active_staff_queryset()
    ```

Usage in Admin:
    ```python
    from accounts.utilities.user_querysets import get_active_investors_queryset
    
    class MyAdmin(admin.ModelAdmin):
        def formfield_for_foreignkey(self, db_field, request, **kwargs):
            if db_field.name == 'client':
                kwargs['queryset'] = get_active_investors_queryset()
            return super().formfield_for_foreignkey(db_field, request, **kwargs)
    ```

Author: CODA Development Team
Created: November 5, 2025
Related: docs/USER_FILTERING_AUDIT_AND_FIX.md
"""

from django.contrib.auth import get_user_model
from django.db.models import Q
from accounts.choices import UserCategory

User = get_user_model()


# ============================================================================
# STAFF QUERYSETS
# ============================================================================

def get_active_staff_queryset():
    """
    Get queryset of all active staff members (all levels: junior, senior, manager, executive)
    
    Filters:
        - is_staff=True (Django's built-in staff flag)
        - is_active=True (account is active, not disabled)
    
    Ordering:
        - first_name, last_name (alphabetical)
    
    Use Cases:
        - Account Manager field (investing app)
        - Task Assignment field (management app)
        - Instructor field (professional_services app)
        - Approver field (finance app)
    
    Returns:
        QuerySet of CustomerUser objects
    
    Example:
        >>> staff = get_active_staff_queryset()
        >>> staff.count()
        12  # Much better than 100+ users!
    """
    return User.objects.filter(
        is_staff=True,
        is_active=True
    ).order_by('first_name', 'last_name')


def get_active_managers_queryset():
    """
    Get queryset of active managers and executives only (not junior/senior staff)
    
    Filters:
        - is_staff=True
        - is_active=True
        - profile.staff_level IN ['manager', 'executive']
    
    Ordering:
        - first_name, last_name
    
    Use Cases:
        - Budget Approver field (finance app)
        - Department Head field (management app)
        - Senior Manager field (any app requiring management approval)
    
    Returns:
        QuerySet of CustomerUser objects
    
    Example:
        >>> managers = get_active_managers_queryset()
        >>> managers.count()
        5  # Only managers and executives
    """
    return User.objects.filter(
        is_staff=True,
        is_active=True,
        profile__staff_level__in=['manager', 'executive']
    ).select_related('profile').order_by('first_name', 'last_name')


def get_active_executives_queryset():
    """
    Get queryset of active executives only (highest level)
    
    Filters:
        - is_staff=True
        - is_active=True
        - profile.staff_level='executive'
    
    Ordering:
        - first_name, last_name
    
    Use Cases:
        - Executive Approval field (high-value transactions)
        - Board Member field
        - C-Suite assignment fields
    
    Returns:
        QuerySet of CustomerUser objects
    
    Example:
        >>> executives = get_active_executives_queryset()
        >>> executives.count()
        2  # Only top executives
    """
    return User.objects.filter(
        is_staff=True,
        is_active=True,
        profile__staff_level='executive'
    ).select_related('profile').order_by('first_name', 'last_name')


# ============================================================================
# CATEGORY-BASED QUERYSETS
# ============================================================================

def get_active_investors_queryset():
    """
    Get queryset of active investors (INVESTOR category)
    
    Filters:
        - category=4 (UserCategory.INVESTOR)
        - is_active=True
    
    Ordering:
        - first_name, last_name
    
    Use Cases:
        - Client field in ManagedTradingAccount (investing app)
        - Investor field in Investor_Information (investing app)
        - Investor Relations (finance app)
        - KCC Member field
    
    Returns:
        QuerySet of CustomerUser objects
    
    Example:
        >>> investors = get_active_investors_queryset()
        >>> investors.count()
        15  # Only active investors, not students/applicants
    """
    return User.objects.filter(
        category=UserCategory.INVESTOR,
        is_active=True
    ).order_by('first_name', 'last_name')


def get_active_students_queryset():
    """
    Get queryset of active students (STUDENT category)
    
    Filters:
        - category=2 (UserCategory.STUDENT)
        - is_active=True
    
    Ordering:
        - first_name, last_name
    
    Use Cases:
        - Student field in Course Enrollment (professional_services app)
        - Trainee field in Training Programs
        - Student Assignment field
    
    Returns:
        QuerySet of CustomerUser objects
    
    Example:
        >>> students = get_active_students_queryset()
        >>> students.count()
        25  # Only active students
    """
    return User.objects.filter(
        category=UserCategory.STUDENT,
        is_active=True
    ).order_by('first_name', 'last_name')


def get_active_consultants_queryset():
    """
    Get queryset of active consultants (CONSULTANT category)
    
    Filters:
        - category=3 (UserCategory.CONSULTANT)
        - is_active=True
    
    Ordering:
        - first_name, last_name
    
    Use Cases:
        - Consultant field in Professional Services
        - Advisor field
        - External Service Provider field
    
    Returns:
        QuerySet of CustomerUser objects
    
    Example:
        >>> consultants = get_active_consultants_queryset()
        >>> consultants.count()
        8  # Only active consultants
    """
    return User.objects.filter(
        category=UserCategory.CONSULTANT,
        is_active=True
    ).order_by('first_name', 'last_name')


def get_active_applicants_queryset():
    """
    Get queryset of active applicants (APPLICANT category)
    
    Filters:
        - category=1 (UserCategory.APPLICANT)
        - is_active=True
    
    Ordering:
        - first_name, last_name
    
    Use Cases:
        - Applicant Review forms (application app)
        - Interview Scheduling
        - Hiring Pipeline
    
    Returns:
        QuerySet of CustomerUser objects
    
    Example:
        >>> applicants = get_active_applicants_queryset()
        >>> applicants.count()
        45  # Only active applicants
    """
    return User.objects.filter(
        category=UserCategory.APPLICANT,
        is_active=True
    ).order_by('first_name', 'last_name')


def get_active_explorers_queryset():
    """
    Get queryset of active explorers/visitors (EXPLORER category)
    
    Filters:
        - category=5 (UserCategory.EXPLORER)
        - is_active=True
    
    Ordering:
        - first_name, last_name
    
    Use Cases:
        - Visitor Management
        - Research Collaboration
        - Networking Events
    
    Returns:
        QuerySet of CustomerUser objects
    
    Example:
        >>> explorers = get_active_explorers_queryset()
        >>> explorers.count()
        10  # Only active explorers
    """
    return User.objects.filter(
        category=UserCategory.EXPLORER,
        is_active=True
    ).order_by('first_name', 'last_name')


# ============================================================================
# COMBINED QUERYSETS (Multiple Categories)
# ============================================================================

def get_active_staff_and_investors_queryset():
    """
    Get queryset of active staff AND investors (useful for certain shared fields)
    
    Filters:
        - (is_staff=True OR category=4) AND is_active=True
    
    Ordering:
        - first_name, last_name
    
    Use Cases:
        - Board Members (staff + strategic investors)
        - Advisory Committee
        - Shared access fields
    
    Returns:
        QuerySet of CustomerUser objects
    
    Example:
        >>> staff_and_investors = get_active_staff_and_investors_queryset()
        >>> staff_and_investors.count()
        27  # Staff (12) + Investors (15)
    """
    return User.objects.filter(
        Q(is_staff=True) | Q(category=UserCategory.INVESTOR),
        is_active=True
    ).order_by('first_name', 'last_name')


def get_active_students_and_staff_queryset():
    """
    Get queryset of active students AND staff (useful for training programs)
    
    Filters:
        - (is_staff=True OR category=2) AND is_active=True
    
    Ordering:
        - first_name, last_name
    
    Use Cases:
        - Training Program Participants (staff can also be trainees)
        - Workshop Attendees
        - Learning Management System
    
    Returns:
        QuerySet of CustomerUser objects
    
    Example:
        >>> students_and_staff = get_active_students_and_staff_queryset()
        >>> students_and_staff.count()
        37  # Students (25) + Staff (12)
    """
    return User.objects.filter(
        Q(is_staff=True) | Q(category=UserCategory.STUDENT),
        is_active=True
    ).order_by('first_name', 'last_name')


# ============================================================================
# UTILITY FUNCTIONS (Helpful for Complex Filtering)
# ============================================================================

def get_users_by_categories(categories, active_only=True):
    """
    Generic function to get users by multiple categories
    
    Args:
        categories (list): List of UserCategory values (e.g., [UserCategory.INVESTOR, UserCategory.CONSULTANT])
        active_only (bool): If True, filter by is_active=True (default: True)
    
    Returns:
        QuerySet of CustomerUser objects
    
    Example:
        >>> from accounts.choices import UserCategory
        >>> users = get_users_by_categories([UserCategory.INVESTOR, UserCategory.CONSULTANT])
        >>> users.count()
        23  # Investors + Consultants
    """
    filters = Q(category__in=categories)
    if active_only:
        filters &= Q(is_active=True)
    
    return User.objects.filter(filters).order_by('first_name', 'last_name')


def get_staff_by_level(levels, active_only=True):
    """
    Get staff filtered by staff level(s)
    
    Args:
        levels (list): List of staff levels (e.g., ['manager', 'executive'])
        active_only (bool): If True, filter by is_active=True (default: True)
    
    Returns:
        QuerySet of CustomerUser objects
    
    Example:
        >>> managers = get_staff_by_level(['manager'])
        >>> executives = get_staff_by_level(['executive'])
        >>> leadership = get_staff_by_level(['manager', 'executive'])
    """
    filters = Q(is_staff=True, profile__staff_level__in=levels)
    if active_only:
        filters &= Q(is_active=True)
    
    return User.objects.filter(filters).select_related('profile').order_by('first_name', 'last_name')


# ============================================================================
# ADMIN HELPER (Commonly Used in formfield_for_foreignkey)
# ============================================================================

def filter_user_field(field_name, queryset_func):
    """
    Helper function for use in admin.ModelAdmin.formfield_for_foreignkey()
    
    Args:
        field_name (str): Name of the field to filter (e.g., 'client', 'account_manager')
        queryset_func (callable): Function that returns filtered queryset (e.g., get_active_investors_queryset)
    
    Returns:
        dict: kwargs to pass to formfield_for_foreignkey
    
    Example in Admin:
        ```python
        def formfield_for_foreignkey(self, db_field, request, **kwargs):
            filters = {
                'client': get_active_investors_queryset,
                'account_manager': get_active_staff_queryset,
            }
            
            if db_field.name in filters:
                kwargs['queryset'] = filters[db_field.name]()
            
            return super().formfield_for_foreignkey(db_field, request, **kwargs)
        ```
    """
    return {'queryset': queryset_func()}


# ============================================================================
# SUMMARY OF AVAILABLE FUNCTIONS
# ============================================================================

__all__ = [
    # Staff Querysets
    'get_active_staff_queryset',
    'get_active_managers_queryset',
    'get_active_executives_queryset',
    
    # Category-Based Querysets
    'get_active_investors_queryset',
    'get_active_students_queryset',
    'get_active_consultants_queryset',
    'get_active_applicants_queryset',
    'get_active_explorers_queryset',
    
    # Combined Querysets
    'get_active_staff_and_investors_queryset',
    'get_active_students_and_staff_queryset',
    
    # Utility Functions
    'get_users_by_categories',
    'get_staff_by_level',
    'filter_user_field',
]

