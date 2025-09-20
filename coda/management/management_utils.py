"""
Management Utils

This module contains utility functions for management operations.
Extracted from the massive management/utils.py file to improve maintainability.

Following the modular monolith architecture, these utilities delegate complex operations
to specialized utility classes and provide simple interfaces for common tasks.
"""

import logging
from typing import Optional, Dict, Any, List
from decimal import Decimal
from django.utils import timezone

from .utilities import PayrollUtils, EmployeeUtils, TaskUtils, LoanUtils

logger = logging.getLogger(__name__)

# Initialize utility classes
payroll_utils = PayrollUtils()
employee_utils = EmployeeUtils()
task_utils = TaskUtils()
loan_utils = LoanUtils()


def get_selected_month_year(request: Any, pay_type: str) -> Dict[str, Any]:
    """
    Get selected month and year from request.
    
    Args:
        request: Django request object
        pay_type: Type of payment
        
    Returns:
        Dict with selected month and year
    """
    return payroll_utils.get_selected_month_year(request, pay_type)


def get_tasks(employee: Any, selected_month: int, selected_year: int, pay_type: str) -> Dict[str, Any]:
    """
    Get tasks for employee for selected month/year.
    
    Args:
        employee: Employee object
        selected_month: Selected month
        selected_year: Selected year
        pay_type: Type of payment
        
    Returns:
        Dict with tasks information
    """
    return task_utils.get_tasks(employee, selected_month, selected_year, pay_type)


def compute_total_points(instance: Any) -> Dict[str, Any]:
    """
    Compute total points for instance.
    
    Args:
        instance: Instance object
        
    Returns:
        Dict with total points calculation
    """
    return task_utils.compute_total_points(instance)


def best_employee(task_obj: Any) -> Dict[str, Any]:
    """
    Find best employee based on task performance.
    
    Args:
        task_obj: Task object
        
    Returns:
        Dict with best employee information
    """
    return employee_utils.best_employee(task_obj)


def employee_reward(tasks: List[Any]) -> Dict[str, Any]:
    """
    Calculate employee reward based on tasks.
    
    Args:
        tasks: List of task objects
        
    Returns:
        Dict with reward calculation
    """
    return employee_utils.employee_reward(tasks)


def employee_group_level(historytasks: List[Any], task_groups: List[Any]) -> Dict[str, Any]:
    """
    Determine employee group level based on history tasks.
    
    Args:
        historytasks: List of historical task objects
        task_groups: List of task group objects
        
    Returns:
        Dict with group level information
    """
    return employee_utils.employee_group_level(historytasks, task_groups)


def increment_in_graduation_of_employee(employee: Any, max_earning: Decimal, new_group: str, payslip_config: Any) -> Dict[str, Any]:
    """
    Increment employee graduation level.
    
    Args:
        employee: Employee object
        max_earning: Maximum earning amount
        new_group: New group name
        payslip_config: Payslip configuration
        
    Returns:
        Dict with graduation increment result
    """
    return employee_utils.increment_in_graduation_of_employee(employee, max_earning, new_group, payslip_config)


def payinitial(tasks: List[Any]) -> Dict[str, Any]:
    """
    Calculate initial pay for tasks.
    
    Args:
        tasks: List of task objects
        
    Returns:
        Dict with initial pay calculation
    """
    return payroll_utils.payinitial(tasks)


def paymentconfigurations(payslip_config: Any, employee: Any) -> Dict[str, Any]:
    """
    Configure payment settings for employee.
    
    Args:
        payslip_config: Payslip configuration object
        employee: Employee object
        
    Returns:
        Dict with payment configuration
    """
    return payroll_utils.paymentconfigurations(payslip_config, employee)


def paytime() -> Dict[str, Any]:
    """
    Get current pay time information.
    
    Returns:
        Dict with pay time information
    """
    return payroll_utils.paytime()


def loan_computation(total_pay: Decimal, user_data: Dict[str, Any], payslip_config: Any) -> Dict[str, Any]:
    """
    Compute loan calculations.
    
    Args:
        total_pay: Total pay amount
        user_data: User data dictionary
        payslip_config: Payslip configuration
        
    Returns:
        Dict with loan computation
    """
    return loan_utils.loan_computation(total_pay, user_data, payslip_config)


def updateloantable(user_data: Dict[str, Any], employee: Any, total_pay: Decimal, payslip_config: Any) -> Dict[str, Any]:
    """
    Update loan table with new data.
    
    Args:
        user_data: User data dictionary
        employee: Employee object
        total_pay: Total pay amount
        payslip_config: Payslip configuration
        
    Returns:
        Dict with update result
    """
    return loan_utils.updateloantable(user_data, employee, total_pay, payslip_config)


def addloantable(loantable: Any, employee: Any, total_pay: Decimal, payslip_config: Any, user_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add new entry to loan table.
    
    Args:
        loantable: Loan table object
        employee: Employee object
        total_pay: Total pay amount
        payslip_config: Payslip configuration
        user_data: User data dictionary
        
    Returns:
        Dict with add result
    """
    return loan_utils.addloantable(loantable, employee, total_pay, payslip_config, user_data)


def lap_save_bonus(payslip_config: Any) -> Dict[str, Any]:
    """
    Save bonus to payslip configuration.
    
    Args:
        payslip_config: Payslip configuration object
        
    Returns:
        Dict with save result
    """
    return payroll_utils.lap_save_bonus(payslip_config)


def deductions(employee: Any, user_data: Dict[str, Any], payslip_config: Any, total_pay: Decimal) -> Dict[str, Any]:
    """
    Calculate deductions for employee.
    
    Args:
        employee: Employee object
        user_data: User data dictionary
        payslip_config: Payslip configuration
        total_pay: Total pay amount
        
    Returns:
        Dict with deduction calculations
    """
    return payroll_utils.deductions(employee, user_data, payslip_config, total_pay)


def bonus(tasks: List[Any], total_pay: Decimal, payslip_config: Any) -> Dict[str, Any]:
    """
    Calculate bonus for employee based on tasks.
    
    Args:
        tasks: List of task objects
        total_pay: Total pay amount
        payslip_config: Payslip configuration
        
    Returns:
        Dict with bonus calculations
    """
    return payroll_utils.bonus(tasks, total_pay, payslip_config)


def calculate_total_pay(tasks: List[Any]) -> Dict[str, Any]:
    """
    Calculate total pay based on tasks.
    
    Args:
        tasks: List of task objects
        
    Returns:
        Dict with total pay calculation
    """
    return payroll_utils.calculate_total_pay(tasks)


def get_points_and_earnings(tasks: List[Any]) -> Dict[str, Any]:
    """
    Get points and earnings summary from tasks.
    
    Args:
        tasks: List of task objects
        
    Returns:
        Dict with points and earnings summary
    """
    return payroll_utils.get_points_and_earnings(tasks)


def get_bonus_and_summary(employee: Any, tasks: List[Any], total_pay: Decimal, user_data: Dict[str, Any], payslip_config: Any) -> Dict[str, Any]:
    """
    Get comprehensive bonus and summary information.
    
    Args:
        employee: Employee object
        tasks: List of task objects
        total_pay: Total pay amount
        user_data: User data dictionary
        payslip_config: Payslip configuration
        
    Returns:
        Dict with bonus and summary information
    """
    return payroll_utils.get_bonus_and_summary(employee, tasks, total_pay, user_data, payslip_config)


def emp_average_earnings(request: Any, task_history: List[Any], goal_amount: Decimal, employee: Any) -> Dict[str, Any]:
    """
    Calculate employee average earnings.
    
    Args:
        request: Django request object
        task_history: List of historical task objects
        goal_amount: Goal amount
        employee: Employee object
        
    Returns:
        Dict with average earnings calculation
    """
    return employee_utils.emp_average_earnings(request, task_history, goal_amount, employee)





