"""
Unified Compliance Calculator Service

Single source of truth for 33% compliance rule calculation.
Uses point-based calculation: (total_points / total_max_points) × 100 ≥ 33

Handles:
- Active employees
- Employees who left company (still have tasks)
- Trainees (0 tasks - not employees)
- Edge cases (division by zero, missing data)
"""

import logging
from typing import Dict, Any, Optional, Tuple
from decimal import Decimal
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from django.db.models import Q, Sum, F
from django.utils import timezone
from django.contrib.auth import get_user_model

from management.models import TaskHistory
from shared_core.users import CustomerUser, Department

logger = logging.getLogger(__name__)
User = get_user_model()


class ComplianceCalculator:
    """
    Unified compliance calculator using point-based calculation.
    
    Formula: (total_points / total_max_points) × 100 ≥ 33%
    
    This is the single source of truth for compliance calculations.
    All other services should use this calculator.
    """
    
    def __init__(self, threshold: float = 33.0):
        """
        Initialize calculator.
        
        Args:
            threshold: Compliance threshold percentage (default: 33.0)
        """
        self.threshold = threshold
        self.logger = logger
    
    def calculate_compliance(
        self,
        employee: User,
        target_month: int,
        target_year: int,
        include_inactive: bool = False
    ) -> Dict[str, Any]:
        """
        Calculate compliance for an employee using point-based formula.
        
        Formula: (total_points / total_max_points) × 100 ≥ threshold
        
        Args:
            employee: User object (can be active or inactive)
            target_month: Month to check (1-12)
            target_year: Year to check (YYYY)
            include_inactive: If True, include employees who left company
        
        Returns:
            dict: {
                'is_compliant': bool,
                'completion_rate': float,  # Percentage (0-100)
                'total_points': Decimal,
                'total_max_points': Decimal,
                'total_earnings': Decimal,
                'task_count': int,
                'employee_status': str,  # 'active', 'inactive', 'trainee'
                'employee_name': str,
                'employee_username': str,
                'employee_email': str,
                'department': str,
                'target_month': int,
                'target_year': int,
                'threshold': float,
                'is_trainee': bool,  # True if 0 tasks (not an employee)
                'has_left_company': bool  # True if employee is inactive
            }
        """
        try:
            # Check employee status
            is_active = employee.is_active and employee.is_staff
            has_left_company = not is_active
            
            # Get employee's TaskHistory for the target month
            task_filter = Q(
                employee=employee,
                daf_date__month=target_month,
                daf_date__year=target_year
            )
            
            # Only include active employees unless explicitly requested
            if not include_inactive and has_left_company:
                # Employee left company - still calculate but mark as inactive
                pass  # Continue with calculation
            
            tasks = TaskHistory.objects.filter(task_filter)
            
            # Calculate totals using point-based formula
            totals = tasks.aggregate(
                total_points=Sum('point'),
                total_max_points=Sum('mxpoint'),
                total_earnings=Sum(F('point') / F('mxpoint') * F('mxearning')),
                task_count=Sum(1)  # Count all tasks
            )
            
            total_points = totals['total_points'] or Decimal('0')
            total_max_points = totals['total_max_points'] or Decimal('0')
            total_earnings = totals['total_earnings'] or Decimal('0')
            task_count = totals['task_count'] or 0
            
            # Check if trainee (0 tasks assigned)
            is_trainee = task_count == 0
            
            # Calculate completion rate (point-based)
            if total_max_points > 0:
                completion_rate = float((total_points / total_max_points) * 100)
            else:
                # No max points - cannot calculate compliance
                completion_rate = 0.0
                if task_count > 0:
                    # Has tasks but no max points - data issue
                    self.logger.warning(
                        f"Employee {employee.username} has {task_count} tasks but total_max_points is 0"
                    )
            
            # Check compliance
            is_compliant = completion_rate >= self.threshold
            
            # Get department
            department_name = 'Unknown'
            if hasattr(employee, 'department') and employee.department:
                department_name = employee.department.name
            
            return {
                'is_compliant': is_compliant,
                'completion_rate': round(completion_rate, 2),
                'total_points': total_points,
                'total_max_points': total_max_points,
                'total_earnings': total_earnings,
                'task_count': task_count,
                'employee_status': 'active' if is_active else 'inactive',
                'employee_name': f"{employee.first_name} {employee.last_name}".strip() or employee.username,
                'employee_username': employee.username,
                'employee_email': employee.email or '',
                'department': department_name,
                'target_month': target_month,
                'target_year': target_year,
                'threshold': self.threshold,
                'is_trainee': is_trainee,
                'has_left_company': has_left_company,
                'calculation_method': 'point_based'
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating compliance for {employee.username}: {e}", exc_info=True)
            return {
                'is_compliant': False,
                'completion_rate': 0.0,
                'total_points': Decimal('0'),
                'total_max_points': Decimal('0'),
                'total_earnings': Decimal('0'),
                'task_count': 0,
                'employee_status': 'error',
                'employee_name': f"{employee.first_name} {employee.last_name}".strip() or employee.username,
                'employee_username': employee.username,
                'employee_email': employee.email or '',
                'department': 'Unknown',
                'target_month': target_month,
                'target_year': target_year,
                'threshold': self.threshold,
                'is_trainee': False,
                'has_left_company': False,
                'calculation_method': 'point_based',
                'error': str(e)
            }
    
    def get_compliant_employees(
        self,
        target_month: int,
        target_year: int,
        include_inactive: bool = False,
        department: Optional[Department] = None
    ) -> Dict[str, Any]:
        """
        Get all compliant employees for a given month.
        
        Args:
            target_month: Month to check (1-12)
            target_year: Year to check (YYYY)
            include_inactive: Include employees who left company
            department: Optional department filter
        
        Returns:
            dict: {
                'compliant_employees': [...],
                'non_compliant_employees': [...],
                'trainees': [...],  # Employees with 0 tasks
                'inactive_employees': [...],  # Employees who left
                'summary': {...}
            }
        """
        try:
            # Get all employees who have TaskHistory in target month
            task_history_employees = TaskHistory.objects.filter(
                daf_date__month=target_month,
                daf_date__year=target_year
            ).values_list('employee', flat=True).distinct()
            
            # Get employee queryset
            employee_filter = Q(id__in=task_history_employees)
            
            if department:
                employee_filter &= Q(department=department)
            
            if include_inactive:
                # Include all employees (active and inactive)
                employees = User.objects.filter(employee_filter)
            else:
                # Only active staff employees
                employees = User.objects.filter(
                    employee_filter,
                    is_staff=True,
                    is_active=True
                )
            
            compliant_employees = []
            non_compliant_employees = []
            trainees = []
            inactive_employees = []
            
            for employee in employees:
                compliance = self.calculate_compliance(
                    employee,
                    target_month,
                    target_year,
                    include_inactive=include_inactive
                )
                
                if compliance.get('error'):
                    continue  # Skip employees with calculation errors
                
                compliance_data = {
                    'employee': employee,
                    'compliance': compliance
                }
                
                if compliance['is_trainee']:
                    trainees.append(compliance_data)
                elif compliance['has_left_company']:
                    inactive_employees.append(compliance_data)
                elif compliance['is_compliant']:
                    compliant_employees.append(compliance_data)
                else:
                    non_compliant_employees.append(compliance_data)
            
            # Calculate summary
            total_employees = len(compliant_employees) + len(non_compliant_employees)
            compliance_rate = (
                (len(compliant_employees) / total_employees * 100)
                if total_employees > 0 else 0.0
            )
            
            return {
                'compliant_employees': compliant_employees,
                'non_compliant_employees': non_compliant_employees,
                'trainees': trainees,
                'inactive_employees': inactive_employees,
                'summary': {
                    'total_employees': total_employees,
                    'compliant_count': len(compliant_employees),
                    'non_compliant_count': len(non_compliant_employees),
                    'trainee_count': len(trainees),
                    'inactive_count': len(inactive_employees),
                    'compliance_rate': round(compliance_rate, 2),
                    'target_month': target_month,
                    'target_year': target_year
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting compliant employees: {e}", exc_info=True)
            return {
                'compliant_employees': [],
                'non_compliant_employees': [],
                'trainees': [],
                'inactive_employees': [],
                'summary': {
                    'total_employees': 0,
                    'compliant_count': 0,
                    'non_compliant_count': 0,
                    'trainee_count': 0,
                    'inactive_count': 0,
                    'compliance_rate': 0.0,
                    'target_month': target_month,
                    'target_year': target_year,
                    'error': str(e)
                }
            }
    
    def get_current_target_period(self) -> Tuple[int, int]:
        """
        Get the target month and year for compliance checking.
        
        Returns previous month (for current month's budget calculation).
        
        Returns:
            tuple: (target_month, target_year)
        """
        current_date = date.today()
        if current_date.month == 1:
            target_month = 12
            target_year = current_date.year - 1
        else:
            target_month = current_date.month - 1
            target_year = current_date.year
        
        return target_month, target_year
    
    def is_rule_active(self) -> bool:
        """
        Check if 33% compliance rule is currently active.
        
        Rule is active after 15th of the month.
        
        Returns:
            bool: True if rule is active
        """
        current_date = date.today()
        return current_date.day > 15

















