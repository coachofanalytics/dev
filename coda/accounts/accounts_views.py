"""
Accounts Views

This module contains views specifically for accounts operations.
Extracted from the massive accounts/views.py file to improve maintainability.

Following the modular monolith architecture, these views delegate business logic
to the UserService and focus on HTTP request/response handling.
"""

import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.core.exceptions import ValidationError

from accounts.models import CustomerUser
from .services import UserService


def accounts_home(request):
    """
    Display the accounts home page.
    """
    try:
        user_service = UserService()
        
        # Get user analytics if user is staff
        analytics_data = {}
        if request.user.is_authenticated and request.user.is_staff:
            analytics_response = user_service.get_user_analytics(request.user)
            analytics_data = analytics_response.get('data', {})
        
        context = {
            'analytics_data': analytics_data,
            'total_users': analytics_data.get('total_users', 0),
            'active_users': analytics_data.get('active_users', 0),
            'staff_users': analytics_data.get('staff_users', 0)
        }
        
        return render(request, 'accounts/home.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading accounts page: {str(e)}")
        return render(request, 'accounts/home.html', {
            'analytics_data': {},
            'total_users': 0,
            'active_users': 0,
            'staff_users': 0
        })


def join(request):
    """
    Handle user registration.
    """
    if request.method == 'POST':
        try:
            user_service = UserService()
            
            # Extract form data
            registration_data = {
                'username': request.POST.get('username'),
                'email': request.POST.get('email'),
                'password': request.POST.get('password'),
                'first_name': request.POST.get('first_name'),
                'last_name': request.POST.get('last_name')
            }
            
            # Register user
            result = user_service.register_user(registration_data)
            
            if result['success']:
                messages.success(request, result['message'])
                return redirect('accounts:email_verification_notice', user_id=result['data']['user_id'])
            else:
                messages.error(request, result['error'])
                
        except Exception as e:
            messages.error(request, f"Error registering user: {str(e)}")
    
    # GET request - show registration form
    return render(request, 'accounts/registration/join.html')


def email_verification_notice(request, user_id):
    """
    Display email verification notice.
    """
    try:
        context = {
            'user_id': user_id,
            'message': 'Please check your email and click the verification link to activate your account.'
        }
        
        return render(request, 'accounts/registration/email_verification_notice.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading verification notice: {str(e)}")
        return render(request, 'accounts/registration/email_verification_notice.html', {
            'user_id': user_id,
            'message': 'An error occurred.'
        })


def verify_email(request, token):
    """
    Handle email verification.
    """
    try:
        user_service = UserService()
        
        # Verify email
        result = user_service.verify_email(token)
        
        if result['success']:
            messages.success(request, result['message'])
            return redirect('accounts:login')
        else:
            messages.error(request, result['error'])
            
    except Exception as e:
        messages.error(request, f"Error verifying email: {str(e)}")
    
    return redirect('accounts:join')


@login_required
def profile(request, username=None):
    """
    Display user profile.
    """
    try:
        user_service = UserService()
        
        # Get user profile
        profile_response = user_service.get_user_profile(request.user, username)
        profile_data = profile_response.get('data', {})
        
        context = {
            'profile_data': profile_data,
            'target_username': username,
            'is_own_profile': username is None or username == request.user.username
        }
        
        return render(request, 'accounts/profile.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading profile: {str(e)}")
        return render(request, 'accounts/profile.html', {
            'profile_data': {},
            'target_username': username,
            'is_own_profile': True
        })


@login_required
def edit_profile(request):
    """
    Handle profile editing.
    """
    if request.method == 'POST':
        try:
            user_service = UserService()
            
            # Extract form data
            profile_data = {
                'first_name': request.POST.get('first_name'),
                'last_name': request.POST.get('last_name'),
                'email': request.POST.get('email')
            }
            
            # Update profile
            result = user_service.update_user_profile(request.user, profile_data)
            
            if result['success']:
                messages.success(request, result['message'])
                return redirect('accounts:profile')
            else:
                messages.error(request, result['error'])
                
        except Exception as e:
            messages.error(request, f"Error updating profile: {str(e)}")
    
    # GET request - show edit form
    return render(request, 'accounts/edit_profile.html')


@login_required
def users(request):
    """
    Display list of users (staff only).
    """
    try:
        if not request.user.is_staff:
            messages.error(request, "Access denied. Staff privileges required.")
            return redirect('accounts:home')
        
        user_service = UserService()
        
        # Get users
        users_response = user_service.get_users(request.user)
        users_data = users_response.get('data', {}).get('users', [])
        
        context = {
            'users': users_data,
            'total_count': len(users_data)
        }
        
        return render(request, 'accounts/users.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading users: {str(e)}")
        return render(request, 'accounts/users.html', {
            'users': [],
            'total_count': 0
        })


@login_required
def user_login_history(request, username=None):
    """
    Display user login history.
    """
    try:
        user_service = UserService()
        
        # Get login history
        history_response = user_service.get_user_login_history(request.user, username)
        history_data = history_response.get('data', {})
        
        context = {
            'login_history': history_data,
            'target_username': username or request.user.username,
            'total_logins': history_data.get('total_logins', 0)
        }
        
        return render(request, 'accounts/login_history.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading login history: {str(e)}")
        return render(request, 'accounts/login_history.html', {
            'login_history': {},
            'target_username': username or request.user.username,
            'total_logins': 0
        })


@login_required
def create_user_group(request):
    """
    Handle user group creation (staff only).
    """
    if not request.user.is_staff:
        messages.error(request, "Access denied. Staff privileges required.")
        return redirect('accounts:home')
    
    if request.method == 'POST':
        try:
            user_service = UserService()
            
            # Extract form data
            group_data = {
                'name': request.POST.get('name'),
                'description': request.POST.get('description', '')
            }
            
            # Create group
            result = user_service.create_user_group(request.user, group_data)
            
            if result['success']:
                messages.success(request, result['message'])
                return redirect('accounts:users')
            else:
                messages.error(request, result['error'])
                
        except Exception as e:
            messages.error(request, f"Error creating group: {str(e)}")
    
    # GET request - show form
    return render(request, 'accounts/create_group.html')


@require_http_methods(["GET"])
def get_user_analytics(request):
    """
    Get user analytics via AJAX (staff only).
    """
    try:
        if not request.user.is_staff:
            return JsonResponse({
                'success': False,
                'error': 'Access denied. Staff privileges required.'
            })
        
        user_service = UserService()
        
        # Get analytics
        result = user_service.get_user_analytics(request.user)
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'data': result['data']
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result['error']
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@require_http_methods(["GET"])
def get_users_data(request):
    """
    Get users data via AJAX (staff only).
    """
    try:
        if not request.user.is_staff:
            return JsonResponse({
                'success': False,
                'error': 'Access denied. Staff privileges required.'
            })
        
        user_service = UserService()
        
        active_only = request.GET.get('active_only', 'true').lower() == 'true'
        staff_only = request.GET.get('staff_only', 'false').lower() == 'true'
        
        # Get users
        result = user_service.get_users(request.user, active_only, staff_only)
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'data': result['data']
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result['error']
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


def thank(request):
    """
    Display thank you page.
    """
    return render(request, 'accounts/thank.html')


def security_verification(request):
    """
    Display security verification page.
    """
    return render(request, 'accounts/security_verification.html')





