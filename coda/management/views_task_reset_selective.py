"""
Selective Task Reset View
Allows admins to select which employees should have their tasks reset
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.contrib.auth import get_user_model
from management.models import Task, TaskHistory
from coda_project.task import dump_data
from decimal import Decimal
from unittest.mock import Mock

User = get_user_model()


def is_admin_or_superuser(user):
    """Check if user is admin or superuser"""
    return user.is_authenticated and (user.is_admin or user.is_superuser or user.is_staff)


@login_required
@user_passes_test(is_admin_or_superuser)
def reset_tasks_select(request):
    """
    View to selectively reset tasks for chosen employees.
    
    Features:
    - List all employees with tasks
    - Allow selection of specific employees
    - Preview changes before applying
    - Exclude test accounts by default
    """
    
    # Test account patterns (usernames to highlight as test accounts)
    TEST_ACCOUNT_PATTERNS = [
        'coda_info',
        'test_',
        'demo_',
        '_test',
        'admin_test',
    ]
    
    if request.method == 'POST':
        action = request.POST.get('action')
        selected_employee_ids = request.POST.getlist('selected_employees')
        
        if not selected_employee_ids:
            messages.error(request, 'Please select at least one employee.')
            return redirect('management:reset_tasks_select')
        
        selected_employees = User.objects.filter(
            id__in=selected_employee_ids,
            is_staff=True,
            is_active=True
        )
        
        if action == 'preview':
            # Generate preview of what will happen
            preview_data = {
                'employees_count': selected_employees.count(),
                'tasks_count': 0,
                'employees': []
            }
            
            for employee in selected_employees:
                tasks = Task.objects.filter(employee=employee).exclude(employee__email=None)
                task_count = tasks.count()
                total_points = tasks.aggregate(total=Sum('point'))['total'] or Decimal('0')
                
                preview_data['tasks_count'] += task_count
                preview_data['employees'].append({
                    'username': employee.username,
                    'tasks': task_count,
                    'points': total_points
                })
            
            # Get all employees again for the form
            employees = get_employees_with_tasks(TEST_ACCOUNT_PATTERNS)
            
            return render(request, 'management/daf/reset_tasks_select.html', {
                'employees': employees,
                'preview_data': preview_data,
                'selected_ids': selected_employee_ids
            })
        
        elif action == 'confirm':
            # Actually perform the reset for selected employees only
            try:
                # Filter tasks to only process selected employees
                tasks_to_move = Task.objects.filter(
                    employee__in=selected_employees
                ).exclude(employee__email=None)
                
                # Create TaskHistory records
                bulk_history = []
                for task in tasks_to_move:
                    bulk_history.append(
                        TaskHistory(
                            group=task.group,
                            category=task.category,
                            employee=task.employee,
                            activity_name=task.activity_name,
                            description=task.description,
                            slug=task.slug,
                            duration=task.duration,
                            point=task.point,
                            mxpoint=task.mxpoint,
                            mxearning=task.mxearning,
                            submission=task.submission,
                            is_active=task.is_active,
                            featured=task.featured,
                        )
                    )
                
                TaskHistory.objects.bulk_create(bulk_history)
                
                # Reset points to 0 for selected employees
                updated_tasks = []
                for task in tasks_to_move:
                    task.point = 0
                    updated_tasks.append(task)
                
                Task.objects.bulk_update(updated_tasks, ['point'])
                
                success_data = {
                    'employees_processed': selected_employees.count(),
                    'tasks_moved': len(bulk_history),
                    'tasks_updated': len(updated_tasks)
                }
                
                messages.success(
                    request, 
                    f'Successfully reset tasks for {success_data["employees_processed"]} employee(s). '
                    f'{success_data["tasks_moved"]} tasks moved to history.'
                )
                
                # Get all employees again for the form
                employees = get_employees_with_tasks(TEST_ACCOUNT_PATTERNS)
                
                return render(request, 'management/daf/reset_tasks_select.html', {
                    'employees': employees,
                    'success_data': success_data
                })
                
            except Exception as e:
                messages.error(request, f'Error resetting tasks: {str(e)}')
                return redirect('management:reset_tasks_select')
    
    # GET request - show selection form
    employees = get_employees_with_tasks(TEST_ACCOUNT_PATTERNS)
    
    return render(request, 'management/daf/reset_tasks_select.html', {
        'employees': employees
    })


def get_employees_with_tasks(test_patterns):
    """
    Get all active staff employees with their task statistics.
    
    Args:
        test_patterns: List of username patterns to identify test accounts
        
    Returns:
        List of employee dictionaries with task stats
    """
    employees_data = []
    
    # Get all active staff employees
    employees = User.objects.filter(
        is_staff=True,
        is_active=True
    ).exclude(email=None).order_by('username')
    
    for employee in employees:
        # Get task statistics
        tasks = Task.objects.filter(employee=employee)
        task_count = tasks.count()
        total_points = tasks.aggregate(total=Sum('point'))['total'] or Decimal('0')
        
        # Get history count
        history_count = TaskHistory.objects.filter(employee=employee).count()
        
        # Check if test account
        is_test = any(
            pattern.lower() in employee.username.lower() 
            for pattern in test_patterns
        )
        
        employees_data.append({
            'id': employee.id,
            'username': employee.username,
            'email': employee.email,
            'task_count': task_count,
            'total_points': total_points,
            'history_count': history_count,
            'is_test_account': is_test
        })
    
    # Sort: non-test accounts first, then by username
    employees_data.sort(key=lambda x: (x['is_test_account'], x['username']))
    
    return employees_data


@login_required
@user_passes_test(is_admin_or_superuser)
def reset_all_tasks(request):
    """
    Original reset all tasks function (kept for backward compatibility).
    Redirects to new selective interface.
    """
    messages.info(
        request, 
        'Task reset has been updated! Please select which employees to process.'
    )
    return redirect('management:reset_tasks_select')

