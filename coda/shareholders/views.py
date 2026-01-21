"""
Shareholders Management System Views

This module provides the dashboard view for the Shareholders Management System.
Access is restricted to admin users only (same permission as Automation dashboard).
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import logging

from core.permissions import is_admin, require_admin

logger = logging.getLogger(__name__)


@login_required
@require_admin
def shareholders_dashboard(request):
    """
    Main shareholders dashboard view.
    
    Access Control:
        - Requires login
        - Requires admin privileges (is_staff or is_superuser)
        - Same permission logic as Automation dashboard
    
    If unauthorized user tries to access directly via URL, they are redirected
    to the unified dashboard with an error message.
    """
    try:
        context = {
            'title': 'Shareholders Management Dashboard',
            'page_title': 'Shareholders Management System',
            'user': request.user,
        }
        
        return render(request, 'shareholders/dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Error in shareholders dashboard: {str(e)}")
        messages.error(request, f"Error loading shareholders dashboard: {str(e)}")
        return redirect('dashboard:unified_dashboard')
