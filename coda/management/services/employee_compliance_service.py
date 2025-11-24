"""
Employee Compliance Service

Handles 33% completion rule checking and compliance validation for employees.
This service integrates with the budget approval system to ensure only compliant
employees are included in payroll submissions.

Business Rule: "For a new month, an employee must meet 33% of their activities 
by 15th of the month for the pay for last month to be approved"
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from django.db.models import Q, Sum, Avg, Count, Max, Min, F
from django.utils import timezone
from django.contrib.auth import get_user_model

# Import models
from management.models import Task, TaskHistory, TaskCategory, TaskLinks
from shared_core.users import CustomerUser, Department
from accounts.models import TaskGroups

logger = logging.getLogger(__name__)
User = get_user_model()


class EmployeeComplianceService:
    """
    Service to check employee compliance with 33% completion rule.
    
    Provides comprehensive compliance checking for:
    - Individual employees
    - Department-level compliance
    - Company-wide compliance reports
    - Historical compliance tracking
    """
    
    def __init__(self):
        self.logger = logger
        self.compliance_threshold = 33.0  # 33% threshold
    
    def check_33_percent_compliance(self, employee: User, target_month: int, target_year: int) -> Dict[str, Any]:
        """
        Check if employee meets 33% completion rule for given month.
        
        Args:
            employee: User object
            target_month: Month to check (previous month)
            target_year: Year to check
            
        Returns:
            dict: {
                'is_compliant': bool,
                'completion_rate': float,
                'total_tasks': int,
                'completed_tasks': int,
                'required_tasks': int,
                'missing_tasks': int,
                'employee_name': str,
                'department': str,
                'target_month': int,
                'target_year': int
            }
        """
        try:
            # Get employee's tasks for the target month
            tasks = TaskHistory.objects.filter(
                employee=employee,
                daf_date__month=target_month,
                daf_date__year=target_year
            )
            
            total_tasks = tasks.count()
            completed_tasks = tasks.filter(point__gt=0).count()
            
            # Calculate completion rate
            completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            # Calculate required tasks (33% of total)
            required_tasks = int(total_tasks * 0.33)
            missing_tasks = max(0, required_tasks - completed_tasks)
            
            is_compliant = completion_rate >= self.compliance_threshold
            
            return {
                'is_compliant': is_compliant,
                'completion_rate': round(completion_rate, 2),
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'required_tasks': required_tasks,
                'missing_tasks': missing_tasks,
                'employee_name': f"{employee.first_name} {employee.last_name}".strip() or employee.username,
                'employee_username': employee.username,
                'employee_email': employee.email,
                'department': 'Unknown',  # TODO: Implement proper department detection
                'target_month': target_month,
                'target_year': target_year,
                'threshold': self.compliance_threshold
            }
            
        except Exception as e:
            self.logger.error(f"Error checking compliance for employee {employee.username}: {e}")
            return {
                'is_compliant': False,
                'completion_rate': 0.0,
                'total_tasks': 0,
                'completed_tasks': 0,
                'required_tasks': 0,
                'missing_tasks': 0,
                'employee_name': f"{employee.first_name} {employee.last_name}".strip() or employee.username,
                'employee_username': employee.username,
                'employee_email': employee.email,
                'department': 'Unknown',  # TODO: Implement proper department detection
                'target_month': target_month,
                'target_year': target_year,
                'threshold': self.compliance_threshold,
                'error': str(e)
            }
    
    def get_department_compliance_report(self, department: Department, target_month: int, target_year: int) -> Dict[str, Any]:
        """
        Get compliance report for entire department.
        
        Note: Since TaskHistory doesn't have a department field, this method
        currently returns a placeholder report. In the future, this should be
        enhanced to work with the actual department relationships.
        
        Args:
            department: Department object
            target_month: Month to check
            target_year: Year to check
            
        Returns:
            dict: Department compliance report
        """
        try:
            # TODO: Implement proper department filtering when department relationships are clarified
            # For now, return a placeholder report
            
            # Get all employees who have tasks in the target month (no department filtering)
            employees_with_tasks = TaskHistory.objects.filter(
                daf_date__month=target_month,
                daf_date__year=target_year
            ).values_list('employee', flat=True).distinct()
            
            employees = CustomerUser.objects.filter(
                id__in=employees_with_tasks,
                is_staff=True,
                is_active=True
            )
            
            compliance_data = []
            compliant_count = 0
            total_completion_rate = 0.0
            
            for employee in employees:
                compliance = self.check_33_percent_compliance(employee, target_month, target_year)
                compliance_data.append({
                    'employee': employee,
                    'compliance': compliance
                })
                
                if compliance['is_compliant']:
                    compliant_count += 1
                
                total_completion_rate += compliance['completion_rate']
            
            total_employees = employees.count()
            department_compliance_rate = (compliant_count / total_employees * 100) if total_employees > 0 else 0
            average_completion_rate = (total_completion_rate / total_employees) if total_employees > 0 else 0
            
            return {
                'department': department,
                'department_name': department.name,
                'total_employees': total_employees,
                'compliant_employees': compliant_count,
                'non_compliant_employees': total_employees - compliant_count,
                'department_compliance_rate': round(department_compliance_rate, 2),
                'average_completion_rate': round(average_completion_rate, 2),
                'employee_data': compliance_data,
                'target_month': target_month,
                'target_year': target_year
            }
            
        except Exception as e:
            self.logger.error(f"Error generating department compliance report for {department.name}: {e}")
            return {
                'department': department,
                'department_name': department.name,
                'total_employees': 0,
                'compliant_employees': 0,
                'non_compliant_employees': 0,
                'department_compliance_rate': 0.0,
                'average_completion_rate': 0.0,
                'employee_data': [],
                'target_month': target_month,
                'target_year': target_year,
                'error': str(e)
            }
    
    def get_company_compliance_report(self, target_month: int, target_year: int) -> Dict[str, Any]:
        """
        Get compliance report for entire company.
        
        Args:
            target_month: Month to check
            target_year: Year to check
            
        Returns:
            dict: Company-wide compliance report
        """
        try:
            # Get all employees who have tasks in the target month
            employees_with_tasks = TaskHistory.objects.filter(
                daf_date__month=target_month,
                daf_date__year=target_year
            ).values_list('employee', flat=True).distinct()
            
            all_employees = CustomerUser.objects.filter(
                id__in=employees_with_tasks,
                is_staff=True,
                is_active=True
            )
            
            # Calculate overall compliance
            compliant_count = 0
            total_completion_rate = 0.0
            
            for employee in all_employees:
                compliance = self.check_33_percent_compliance(employee, target_month, target_year)
                if compliance['is_compliant']:
                    compliant_count += 1
                total_completion_rate += compliance['completion_rate']
            
            total_employees = all_employees.count()
            company_compliance_rate = (compliant_count / total_employees * 100) if total_employees > 0 else 0
            average_completion_rate = (total_completion_rate / total_employees) if total_employees > 0 else 0
            
            # Get department reports
            departments = Department.objects.filter(is_active=True)
            department_reports = []
            
            for department in departments:
                dept_report = self.get_department_compliance_report(department, target_month, target_year)
                department_reports.append(dept_report)
            
            return {
                'total_employees': total_employees,
                'total_compliant': compliant_count,
                'total_non_compliant': total_employees - compliant_count,
                'company_compliance_rate': round(company_compliance_rate, 2),
                'average_completion_rate': round(average_completion_rate, 2),
                'department_reports': department_reports,
                'target_month': target_month,
                'target_year': target_year,
                'threshold': self.compliance_threshold
            }
            
        except Exception as e:
            self.logger.error(f"Error generating company compliance report: {e}")
            return {
                'total_employees': 0,
                'total_compliant': 0,
                'total_non_compliant': 0,
                'company_compliance_rate': 0.0,
                'average_completion_rate': 0.0,
                'department_reports': [],
                'target_month': target_month,
                'target_year': target_year,
                'threshold': self.compliance_threshold,
                'error': str(e)
            }
    
    def get_non_compliant_employees(self, target_month: int, target_year: int) -> List[Dict[str, Any]]:
        """
        Get list of all non-compliant employees.
        
        Args:
            target_month: Month to check
            target_year: Year to check
            
        Returns:
            list: List of non-compliant employee data
        """
        try:
            non_compliant_employees = []
            
            # Get employees who have tasks in the target month
            employees_with_tasks = TaskHistory.objects.filter(
                daf_date__month=target_month,
                daf_date__year=target_year
            ).values_list('employee', flat=True).distinct()
            
            all_employees = CustomerUser.objects.filter(
                id__in=employees_with_tasks,
                is_staff=True,
                is_active=True
            )
            
            for employee in all_employees:
                compliance = self.check_33_percent_compliance(employee, target_month, target_year)
                
                if not compliance['is_compliant']:
                    non_compliant_employees.append({
                        'employee': employee,
                        'compliance': compliance
                    })
            
            return non_compliant_employees
            
        except Exception as e:
            self.logger.error(f"Error getting non-compliant employees: {e}")
            return []
    
    def get_compliant_employees(self, target_month: int, target_year: int) -> List[Dict[str, Any]]:
        """
        Get list of all compliant employees.
        
        Args:
            target_month: Month to check
            target_year: Year to check
            
        Returns:
            list: List of compliant employee data
        """
        try:
            compliant_employees = []
            
            # Get employees who have tasks in the target month
            employees_with_tasks = TaskHistory.objects.filter(
                daf_date__month=target_month,
                daf_date__year=target_year
            ).values_list('employee', flat=True).distinct()
            
            all_employees = CustomerUser.objects.filter(
                id__in=employees_with_tasks,
                is_staff=True,
                is_active=True
            )
            
            for employee in all_employees:
                compliance = self.check_33_percent_compliance(employee, target_month, target_year)
                
                if compliance['is_compliant']:
                    compliant_employees.append({
                        'employee': employee,
                        'compliance': compliance
                    })
            
            return compliant_employees
            
        except Exception as e:
            self.logger.error(f"Error getting compliant employees: {e}")
            return []
    
    def is_compliance_rule_active(self) -> bool:
        """
        Check if 33% compliance rule is currently active.
        
        Returns:
            bool: True if rule is active (after 15th of month)
        """
        current_date = datetime.now()
        return current_date.day > 15
    
    def get_current_target_month_year(self) -> Tuple[int, int]:
        """
        Get the target month and year for compliance checking.
        
        Returns:
            tuple: (target_month, target_year) - previous month
        """
        current_date = datetime.now()
        if current_date.month == 1:
            target_month = 12
            target_year = current_date.year - 1
        else:
            target_month = current_date.month - 1
            target_year = current_date.year
        
        return target_month, target_year
    
    def get_compliance_summary(self) -> Dict[str, Any]:
        """
        Get a summary of current compliance status.
        
        Returns:
            dict: Summary of compliance status
        """
        target_month, target_year = self.get_current_target_month_year()
        is_active = self.is_compliance_rule_active()
        
        company_report = self.get_company_compliance_report(target_month, target_year)
        
        return {
            'is_rule_active': is_active,
            'target_month': target_month,
            'target_year': target_year,
            'current_date': datetime.now(),
            'threshold': self.compliance_threshold,
            'company_summary': company_report
        }
