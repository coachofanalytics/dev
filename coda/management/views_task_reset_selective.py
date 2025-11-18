"""
Selective Task Reset View
Allows admins to select which employees should have their tasks reset

Features:
- Shows PAID vs PRACTICING employees
- Checks 33% compliance rule
- Filters for only employees who need reset (points > 0)
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.contrib.auth import get_user_model
from management.models import Task, TaskHistory
from management.services.employee_compliance_service import EmployeeComplianceService
from accounts.choices import UserCategory as CategoryChoices, ApplicantSubCategoryChoices
from coda_project.task import dump_data
from decimal import Decimal
from unittest.mock import Mock

User = get_user_model()


def is_admin_or_superuser(user):
    """Check if user is admin or superuser"""
    return user.is_authenticated and (user.is_admin or user.is_superuser or user.is_staff)


def get_employee_type(employee):
    """
    Determine employee type for display.
    
    Returns: tuple (type_name, is_paid)
    """
    if employee.category == CategoryChoices.APPLICANT:
        if employee.sub_category == ApplicantSubCategoryChoices.FULL_TIME:
            return ("Full-Time", True)
        elif employee.sub_category == ApplicantSubCategoryChoices.PART_TIME:
            return ("Part-Time", False)
        elif employee.sub_category == ApplicantSubCategoryChoices.CONTRACTOR:
            return ("Contractor", True)
        else:
            return ("Applicant", False)
    elif employee.category == CategoryChoices.STUDENT:
        return ("Student", False)
    elif hasattr(CategoryChoices, 'GENERAL_USER') and employee.category == CategoryChoices.GENERAL_USER:
        return ("General User", False)
    else:
        return ("Other", False)


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
                # Only count tasks with points > 0 (skip already reset tasks)
                tasks = Task.objects.filter(
                    employee=employee,
                    point__gt=0  # Only tasks with points will be moved
                ).exclude(employee__email=None)
                task_count = tasks.count()
                total_points = tasks.aggregate(total=Sum('point'))['total'] or Decimal('0')
                
                # Only show employee in preview if they have tasks to move
                if task_count > 0:
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
                # ONLY process tasks with points > 0 (skip already reset tasks)
                tasks_to_move = Task.objects.filter(
                    employee__in=selected_employees,
                    point__gt=0  # Only move tasks with points greater than 0
                ).exclude(employee__email=None)
                
                # Create TaskHistory records (only for tasks with points)
                # OPTION 1: Set daf_date based on when reset is run
                from dateutil.relativedelta import relativedelta
                from datetime import date
                import calendar
                
                current_date = date.today()
                if current_date.day == 1:
                    # Running on 1st - use last day of previous month
                    last_month = current_date - relativedelta(months=1)
                    last_day = calendar.monthrange(last_month.year, last_month.month)[1]
                    default_daf_date = date(last_month.year, last_month.month, last_day)
                else:
                    # Manual reset - use same day of last month
                    default_daf_date = current_date - relativedelta(months=1)
                
                bulk_history = []
                for task in tasks_to_move:
                    # Use task submission date if available, otherwise use default
                    daf_date_value = default_daf_date
                    if task.submission:
                        from django.utils import timezone
                        submission_date = timezone.localtime(task.submission).date()
                        if submission_date.month == current_date.month and submission_date.year == current_date.year:
                            # Submitted this month, use calculated daf_date
                            daf_date_value = default_daf_date
                        else:
                            # Older submission, use submission - 1 month
                            daf_date_value = submission_date - relativedelta(months=1)
                    
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
                            daf_date=daf_date_value,  # Set daf_date when creating TaskHistory
                        )
                    )
                
                TaskHistory.objects.bulk_create(bulk_history)
                
                # Reset points to 0 for tasks that were moved
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
    
    Includes:
    - Employee type (Full-time, Student, etc.)
    - Paid status (Yes/No)
    - 33% compliance check
    - Only shows employees with points > 0
    
    Args:
        test_patterns: List of username patterns to identify test accounts
        
    Returns:
        List of employee dictionaries with task stats
    """
    employees_data = []
    
    # Initialize compliance service
    compliance_service = EmployeeComplianceService()
    target_month, target_year = compliance_service.get_current_target_month_year()
    
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
        
        # SKIP employees with 0 points - they've already been reset
        # Only show employees who actually need reset
        if total_points <= 0:
            continue
        
        # Get history count
        history_count = TaskHistory.objects.filter(employee=employee).count()
        
        # Determine employee type and paid status
        employee_type, is_paid = get_employee_type(employee)
        
        # Check 33% compliance for previous month
        compliance = compliance_service.check_33_percent_compliance(
            employee, target_month, target_year
        )
        
        # Check if test account
        is_test = any(
            pattern.lower() in employee.username.lower() 
            for pattern in test_patterns
        )
        
        # Auto-select if:
        # - Has tasks AND points > 0
        # - Is a PAID employee (Full-time)
        # - NOT a test account
        # - Has history (is active)
        should_auto_select = (
            task_count > 0 and 
            total_points > 0 and 
            is_paid and  # NEW: Only auto-select paid employees
            not is_test and
            history_count > 0  # NEW: Has history (active employee)
        )
        
        employees_data.append({
            'id': employee.id,
            'username': employee.username,
            'email': employee.email,
            'employee_type': employee_type,  # NEW
            'is_paid': is_paid,  # NEW
            'is_compliant': compliance['is_compliant'],  # NEW
            'completion_rate': compliance['completion_rate'],  # NEW
            'task_count': task_count,
            'total_points': total_points,
            'history_count': history_count,
            'is_test_account': is_test,
            'auto_select': should_auto_select
        })
    
    # Sort: paid first, then non-test accounts, then by username
    employees_data.sort(key=lambda x: (
        not x['is_paid'],  # Paid employees first
        x['is_test_account'],  # Then non-test
        x['username']  # Then alphabetically
    ))
    
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

