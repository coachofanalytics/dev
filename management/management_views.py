"""
Management Views

This module contains views specifically for management operations.
Extracted from the massive management/views.py file to improve maintainability.

Following the modular monolith architecture, these views delegate business logic
to the ManagementService and focus on HTTP request/response handling.
"""

import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import reverse

from accounts.models import CustomerUser
from .models import Department, Employee, Meeting, Policy
from .services import ManagementService
from .forms import DepartmentForm, EmployeeForm, MeetingForm, PolicyForm


class ManagementViewsMixin(LoginRequiredMixin):
    """Mixin for management views with common functionality."""
    
    def dispatch(self, request, *args, **kwargs):
        """Add management service to request for easy access."""
        self.management_service = ManagementService()
        return super().dispatch(request, *args, **kwargs)


@login_required
def management_home(request):
    """
    Display the management home page.
    
    Shows management dashboard with departments, employees, meetings, and policies.
    """
    try:
        management_service = ManagementService()
        
        # Get dashboard data
        dashboard_response = management_service.get_management_dashboard_data(request.user)
        dashboard = dashboard_response.get('data', {}).get('dashboard', {})
        
        context = {
            'dashboard': dashboard,
            'total_departments': dashboard.get('total_departments', 0),
            'total_employees': dashboard.get('total_employees', 0),
            'total_meetings': dashboard.get('total_meetings', 0),
            'total_policies': dashboard.get('total_policies', 0)
        }
        
        return render(request, 'management/management_home.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading management page: {str(e)}")
        return render(request, 'management/management_home.html', {
            'dashboard': {},
            'total_departments': 0,
            'total_employees': 0,
            'total_meetings': 0,
            'total_policies': 0
        })


@login_required
def department_list(request):
    """
    Display list of departments.
    """
    try:
        management_service = ManagementService()
        
        # Get departments
        departments_response = management_service.get_departments(request.user)
        departments = departments_response.get('data', {}).get('departments', [])
        
        context = {
            'departments': departments,
            'total_count': len(departments)
        }
        
        return render(request, 'management/department_list.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading departments: {str(e)}")
        return render(request, 'management/department_list.html', {
            'departments': [],
            'total_count': 0
        })


@login_required
def create_department(request):
    """
    Handle department creation.
    """
    if request.method == 'POST':
        try:
            management_service = ManagementService()
            
            # Extract form data
            department_data = {
                'name': request.POST.get('name'),
                'description': request.POST.get('description')
            }
            
            # Create department
            result = management_service.create_department(request.user, department_data)
            
            if result['success']:
                messages.success(request, result['message'])
                return redirect('management:department_list')
            else:
                messages.error(request, result['error'])
                
        except Exception as e:
            messages.error(request, f"Error creating department: {str(e)}")
    
    # GET request - show form
    context = {
        'form': DepartmentForm()
    }
    
    return render(request, 'management/create_department.html', context)


@login_required
def employee_list(request, department_id=None):
    """
    Display list of employees.
    
    Args:
        department_id: Optional department filter
    """
    try:
        management_service = ManagementService()
        
        # Get employees
        employees_response = management_service.get_employees(department_id)
        employees = employees_response.get('data', {}).get('employees', [])
        
        # Get departments for filter
        departments_response = management_service.get_departments()
        departments = departments_response.get('data', {}).get('departments', [])
        
        context = {
            'employees': employees,
            'departments': departments,
            'selected_department': department_id,
            'total_count': len(employees)
        }
        
        return render(request, 'management/employee_list.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading employees: {str(e)}")
        return render(request, 'management/employee_list.html', {
            'employees': [],
            'departments': [],
            'selected_department': department_id,
            'total_count': 0
        })


@login_required
def create_employee(request):
    """
    Handle employee creation.
    """
    if request.method == 'POST':
        try:
            management_service = ManagementService()
            
            # Extract form data
            employee_data = {
                'first_name': request.POST.get('first_name'),
                'last_name': request.POST.get('last_name'),
                'email': request.POST.get('email'),
                'department_id': request.POST.get('department_id'),
                'position': request.POST.get('position', ''),
                'salary': request.POST.get('salary', 0)
            }
            
            # Create employee
            result = management_service.create_employee(request.user, employee_data)
            
            if result['success']:
                messages.success(request, result['message'])
                return redirect('management:employee_list')
            else:
                messages.error(request, result['error'])
                
        except Exception as e:
            messages.error(request, f"Error creating employee: {str(e)}")
    
    # GET request - show form
    # Get departments for dropdown
    management_service = ManagementService()
    departments_response = management_service.get_departments()
    departments = departments_response.get('data', {}).get('departments', [])
    
    context = {
        'form': EmployeeForm(),
        'departments': departments
    }
    
    return render(request, 'management/create_employee.html', context)


@login_required
def meeting_list(request, status=None):
    """
    Display list of meetings.
    
    Args:
        status: Optional status filter
    """
    try:
        management_service = ManagementService()
        
        # Get meetings
        meetings_response = management_service.get_meetings(request.user, status)
        meetings = meetings_response.get('data', {}).get('meetings', [])
        
        context = {
            'meetings': meetings,
            'selected_status': status,
            'total_count': len(meetings)
        }
        
        return render(request, 'management/meeting_list.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading meetings: {str(e)}")
        return render(request, 'management/meeting_list.html', {
            'meetings': [],
            'selected_status': status,
            'total_count': 0
        })


@login_required
def create_meeting(request):
    """
    Handle meeting creation.
    """
    if request.method == 'POST':
        try:
            management_service = ManagementService()
            
            # Extract form data
            meeting_data = {
                'title': request.POST.get('title'),
                'description': request.POST.get('description'),
                'meeting_date': request.POST.get('meeting_date')
            }
            
            # Create meeting
            result = management_service.create_meeting(request.user, meeting_data)
            
            if result['success']:
                messages.success(request, result['message'])
                return redirect('management:meeting_list')
            else:
                messages.error(request, result['error'])
                
        except Exception as e:
            messages.error(request, f"Error creating meeting: {str(e)}")
    
    # GET request - show form
    context = {
        'form': MeetingForm()
    }
    
    return render(request, 'management/create_meeting.html', context)


@login_required
def policy_list(request, category=None):
    """
    Display list of policies.
    
    Args:
        category: Optional category filter
    """
    try:
        management_service = ManagementService()
        
        # Get policies
        policies_response = management_service.get_policies(category)
        policies = policies_response.get('data', {}).get('policies', [])
        
        context = {
            'policies': policies,
            'selected_category': category,
            'total_count': len(policies)
        }
        
        return render(request, 'management/policy_list.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading policies: {str(e)}")
        return render(request, 'management/policy_list.html', {
            'policies': [],
            'selected_category': category,
            'total_count': 0
        })


@login_required
def create_policy(request):
    """
    Handle policy creation.
    """
    if not request.user.is_staff:
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('management:management_home')
    
    if request.method == 'POST':
        try:
            management_service = ManagementService()
            
            # Extract form data
            policy_data = {
                'title': request.POST.get('title'),
                'content': request.POST.get('content'),
                'category': request.POST.get('category')
            }
            
            # Create policy
            result = management_service.create_policy(request.user, policy_data)
            
            if result['success']:
                messages.success(request, result['message'])
                return redirect('management:policy_list')
            else:
                messages.error(request, result['error'])
                
        except Exception as e:
            messages.error(request, f"Error creating policy: {str(e)}")
    
    # GET request - show form
    context = {
        'form': PolicyForm()
    }
    
    return render(request, 'management/create_policy.html', context)


@login_required
def get_dashboard_data(request):
    """
    Get management dashboard data via AJAX.
    """
    try:
        management_service = ManagementService()
        
        # Get dashboard data
        result = management_service.get_management_dashboard_data(request.user)
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'data': result['data']['dashboard']
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





