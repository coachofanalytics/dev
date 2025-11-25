"""
Base view classes for the finance application.
Provides common functionality and patterns for all finance views.
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
import logging

logger = logging.getLogger(__name__)


class BaseFinanceView:
    """
    Base class for all finance views providing common functionality.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def get_company(self, request, company_slug):
        """Get company object from slug with error handling."""
        try:
            from shared_core.models import Company
            company = Company.objects.get(slug=company_slug)
            return company
        except Company.DoesNotExist:
            self.logger.error(f"Company not found: {company_slug}")
            messages.error(request, f"Company '{company_slug}' not found.")
            return None
    
    def get_user_department(self, request, company):
        """Get user's department with error handling."""
        try:
            if hasattr(request.user, 'profile') and request.user.profile.department:
                return request.user.profile.department
            return None
        except Exception as e:
            self.logger.warning(f"Could not get user department: {e}")
            return None
    
    def handle_error(self, request, error, error_message="An error occurred"):
        """Handle errors consistently across views."""
        self.logger.error(f"{error_message}: {error}", exc_info=True)
        messages.error(request, f"{error_message}: {str(error)}")
        return None


def login_required_finance(view_func):
    """
    Decorator that combines login_required with finance-specific error handling.
    """
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Please log in to access this page.")
            return redirect('account_login')
        return view_func(request, *args, **kwargs)
    return wrapper


def company_required(view_func):
    """
    Decorator to ensure company exists and user has access.
    """
    def wrapper(request, company_slug, *args, **kwargs):
        try:
            from shared_core.models import Company
            company = Company.objects.get(slug=company_slug)
            # Add company to kwargs for use in view
            kwargs['company'] = company
            return view_func(request, company_slug, *args, **kwargs)
        except Company.DoesNotExist:
            messages.error(request, f"Company '{company_slug}' not found.")
            return redirect('main:dashboard')
    return wrapper


def json_response(data, status=200):
    """Helper function for consistent JSON responses."""
    return JsonResponse(data, status=status, json_dumps_params={'indent': 2})


def error_json_response(message, status=400):
    """Helper function for error JSON responses."""
    return json_response({'error': message}, status=status)
