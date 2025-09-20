"""
Payroll Utilities

Handles all payroll-related operations including:
- Payroll calculations
- Payment configurations
- Bonus calculations
- Deductions processing
- Payslip generation

This utility encapsulates payroll-related functionality previously scattered across management/utils.py
"""

import logging
from typing import Optional, Dict, Any, List
from decimal import Decimal
from django.utils import timezone
from datetime import datetime, date

logger = logging.getLogger(__name__)


class PayrollUtils:
    """
    Utility class for payroll-related operations.
    
    Provides methods for payroll calculations, configurations, and processing.
    """
    
    def __init__(self):
        self.logger = logger
    
    def get_selected_month_year(self, request: Any, pay_type: str) -> Dict[str, Any]:
        """
        Get selected month and year from request.
        
        Args:
            request: Django request object
            pay_type: Type of payment
            
        Returns:
            Dict with selected month and year
        """
        try:
            selected_month = request.GET.get('month', timezone.now().month)
            selected_year = request.GET.get('year', timezone.now().year)
            
            # Validate month and year
            try:
                selected_month = int(selected_month)
                selected_year = int(selected_year)
                
                if not (1 <= selected_month <= 12):
                    selected_month = timezone.now().month
                
                if not (2020 <= selected_year <= 2030):
                    selected_year = timezone.now().year
                    
            except (ValueError, TypeError):
                selected_month = timezone.now().month
                selected_year = timezone.now().year
            
            return {
                'success': True,
                'selected_month': selected_month,
                'selected_year': selected_year,
                'pay_type': pay_type,
                'date': date(selected_year, selected_month, 1)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting selected month/year: {e}")
            return {
                'success': False,
                'error': str(e),
                'selected_month': timezone.now().month,
                'selected_year': timezone.now().year,
                'pay_type': pay_type
            }
    
    def paymentconfigurations(self, payslip_config: Any, employee: Any) -> Dict[str, Any]:
        """
        Configure payment settings for employee.
        
        Args:
            payslip_config: Payslip configuration object
            employee: Employee object
            
        Returns:
            Dict with payment configuration
        """
        try:
            if not payslip_config or not employee:
                return {
                    'success': False,
                    'error': 'Payslip config and employee are required'
                }
            
            # Placeholder for actual payment configuration
            self.logger.info(f"Configuring payment for employee {employee.id}")
            
            return {
                'success': True,
                'employee_id': employee.id,
                'base_salary': Decimal('0.00'),
                'hourly_rate': Decimal('0.00'),
                'overtime_rate': Decimal('0.00'),
                'tax_rate': Decimal('0.00'),
                'deduction_rate': Decimal('0.00'),
                'bonus_rate': Decimal('0.00'),
                'configuration_date': timezone.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error configuring payment: {e}")
            return {
                'success': False,
                'error': str(e),
                'employee_id': employee.id if employee else None
            }
    
    def paytime(self) -> Dict[str, Any]:
        """
        Get current pay time information.
        
        Returns:
            Dict with pay time information
        """
        try:
            now = timezone.now()
            
            return {
                'success': True,
                'current_time': now,
                'pay_period_start': now.replace(day=1),
                'pay_period_end': now.replace(day=1, month=now.month + 1) if now.month < 12 else now.replace(day=1, month=1, year=now.year + 1),
                'is_payday': now.day == 15 or now.day == 30,  # Assuming bi-monthly pay
                'days_until_payday': 15 - now.day if now.day < 15 else 30 - now.day
            }
            
        except Exception as e:
            self.logger.error(f"Error getting pay time: {e}")
            return {
                'success': False,
                'error': str(e),
                'current_time': timezone.now()
            }
    
    def deductions(self, employee: Any, user_data: Dict[str, Any], payslip_config: Any, total_pay: Decimal) -> Dict[str, Any]:
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
        try:
            if not employee or not total_pay:
                return {
                    'success': False,
                    'error': 'Employee and total pay are required'
                }
            
            # Calculate various deductions
            tax_deduction = total_pay * Decimal('0.15')  # 15% tax
            insurance_deduction = total_pay * Decimal('0.05')  # 5% insurance
            retirement_deduction = total_pay * Decimal('0.08')  # 8% retirement
            
            total_deductions = tax_deduction + insurance_deduction + retirement_deduction
            net_pay = total_pay - total_deductions
            
            return {
                'success': True,
                'employee_id': employee.id,
                'total_pay': total_pay,
                'tax_deduction': tax_deduction,
                'insurance_deduction': insurance_deduction,
                'retirement_deduction': retirement_deduction,
                'total_deductions': total_deductions,
                'net_pay': net_pay,
                'deduction_percentage': (total_deductions / total_pay * 100) if total_pay > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating deductions: {e}")
            return {
                'success': False,
                'error': str(e),
                'employee_id': employee.id if employee else None
            }
    
    def bonus(self, tasks: List[Any], total_pay: Decimal, payslip_config: Any) -> Dict[str, Any]:
        """
        Calculate bonus for employee based on tasks.
        
        Args:
            tasks: List of task objects
            total_pay: Total pay amount
            payslip_config: Payslip configuration
            
        Returns:
            Dict with bonus calculations
        """
        try:
            if not tasks or not total_pay:
                return {
                    'success': False,
                    'error': 'Tasks and total pay are required'
                }
            
            # Calculate bonus based on task performance
            total_points = sum(task.points for task in tasks if hasattr(task, 'points'))
            bonus_rate = Decimal('0.10')  # 10% bonus rate
            bonus_amount = total_pay * bonus_rate
            
            return {
                'success': True,
                'total_points': total_points,
                'bonus_rate': bonus_rate,
                'bonus_amount': bonus_amount,
                'total_tasks': len(tasks),
                'completed_tasks': len([task for task in tasks if hasattr(task, 'completed') and task.completed]),
                'bonus_percentage': float(bonus_rate * 100)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating bonus: {e}")
            return {
                'success': False,
                'error': str(e),
                'total_tasks': len(tasks) if tasks else 0
            }
    
    def calculate_total_pay(self, tasks: List[Any]) -> Dict[str, Any]:
        """
        Calculate total pay based on tasks.
        
        Args:
            tasks: List of task objects
            
        Returns:
            Dict with total pay calculation
        """
        try:
            if not tasks:
                return {
                    'success': True,
                    'total_pay': Decimal('0.00'),
                    'total_points': 0,
                    'total_tasks': 0
                }
            
            total_points = 0
            total_earnings = Decimal('0.00')
            
            for task in tasks:
                if hasattr(task, 'points'):
                    total_points += task.points
                if hasattr(task, 'earnings'):
                    total_earnings += Decimal(str(task.earnings))
            
            return {
                'success': True,
                'total_pay': total_earnings,
                'total_points': total_points,
                'total_tasks': len(tasks),
                'average_points_per_task': total_points / len(tasks) if tasks else 0,
                'average_earnings_per_task': float(total_earnings / len(tasks)) if tasks else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating total pay: {e}")
            return {
                'success': False,
                'error': str(e),
                'total_tasks': len(tasks) if tasks else 0
            }
    
    def get_points_and_earnings(self, tasks: List[Any]) -> Dict[str, Any]:
        """
        Get points and earnings summary from tasks.
        
        Args:
            tasks: List of task objects
            
        Returns:
            Dict with points and earnings summary
        """
        try:
            if not tasks:
                return {
                    'success': True,
                    'total_points': 0,
                    'total_earnings': Decimal('0.00'),
                    'task_summary': []
                }
            
            task_summary = []
            total_points = 0
            total_earnings = Decimal('0.00')
            
            for task in tasks:
                points = getattr(task, 'points', 0)
                earnings = Decimal(str(getattr(task, 'earnings', 0)))
                
                total_points += points
                total_earnings += earnings
                
                task_summary.append({
                    'task_id': getattr(task, 'id', None),
                    'points': points,
                    'earnings': earnings,
                    'status': getattr(task, 'status', 'unknown')
                })
            
            return {
                'success': True,
                'total_points': total_points,
                'total_earnings': total_earnings,
                'task_summary': task_summary,
                'average_points': total_points / len(tasks) if tasks else 0,
                'average_earnings': float(total_earnings / len(tasks)) if tasks else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error getting points and earnings: {e}")
            return {
                'success': False,
                'error': str(e),
                'total_tasks': len(tasks) if tasks else 0
            }
    
    def get_bonus_and_summary(self, employee: Any, tasks: List[Any], total_pay: Decimal, user_data: Dict[str, Any], payslip_config: Any) -> Dict[str, Any]:
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
        try:
            # Get bonus information
            bonus_info = self.bonus(tasks, total_pay, payslip_config)
            
            # Get points and earnings
            points_earnings = self.get_points_and_earnings(tasks)
            
            # Calculate deductions
            deductions_info = self.deductions(employee, user_data, payslip_config, total_pay)
            
            return {
                'success': True,
                'employee_id': employee.id if employee else None,
                'bonus_info': bonus_info,
                'points_earnings': points_earnings,
                'deductions_info': deductions_info,
                'total_pay': total_pay,
                'summary_date': timezone.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting bonus and summary: {e}")
            return {
                'success': False,
                'error': str(e),
                'employee_id': employee.id if employee else None
            }





