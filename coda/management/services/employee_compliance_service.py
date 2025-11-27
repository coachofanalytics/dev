"""
Employee Compliance Service

Handles 33% completion rule checking and compliance validation for employees.
This service integrates with the budget approval system to ensure only compliant
employees are included in payroll submissions.

Business Rule: "For a new month, an employee must meet 33% of their activities 
by 15th of the month for the pay for last month to be approved"

Uses unified ComplianceCalculator for point-based calculations.
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
from management.services.compliance_calculator import ComplianceCalculator

logger = logging.getLogger(__name__)
User = get_user_model()


class EmployeeComplianceService:
    """
    Service to check employee compliance with 33% completion rule.
    
    Uses unified ComplianceCalculator for point-based calculations.
    
    Provides comprehensive compliance checking for:
    - Individual employees
    - Department-level compliance
    - Company-wide compliance reports
    - Historical compliance tracking
    - Employees who left company (still have tasks)
    """
    
    def __init__(self):
        self.logger = logger
        self.compliance_threshold = 33.0  # 33% threshold
        self.calculator = ComplianceCalculator(threshold=self.compliance_threshold)
    
    def check_33_percent_compliance(
        self,
        employee: User,
        target_month: int,
        target_year: int,
        include_inactive: bool = False
    ) -> Dict[str, Any]:
        """
        Check if employee meets 33% completion rule for given month.
        
        Uses unified ComplianceCalculator with point-based formula:
        (total_points / total_max_points) × 100 ≥ 33
        
        Args:
            employee: User object (can be active or inactive)
            target_month: Month to check (previous month)
            target_year: Year to check
            include_inactive: If True, include employees who left company
        
        Returns:
            dict: {
                'is_compliant': bool,
                'completion_rate': float,  # Point-based percentage
                'total_points': Decimal,
                'total_max_points': Decimal,
                'total_earnings': Decimal,
                'task_count': int,
                'employee_status': str,  # 'active', 'inactive', 'trainee'
                'employee_name': str,
                'department': str,
                'target_month': int,
                'target_year': int,
                'is_trainee': bool,  # True if 0 tasks
                'has_left_company': bool  # True if employee is inactive
            }
        """
        # Use unified calculator
        compliance = self.calculator.calculate_compliance(
            employee,
            target_month,
            target_year,
            include_inactive=include_inactive
        )
        
        # Add backward compatibility fields
        compliance['total_tasks'] = compliance.get('task_count', 0)
        compliance['completed_tasks'] = compliance.get('task_count', 0)  # Approximate
        compliance['required_tasks'] = int(compliance.get('task_count', 0) * 0.33)
        compliance['missing_tasks'] = max(0, compliance['required_tasks'] - compliance['completed_tasks'])
        
        return compliance
    
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
    
    def get_compliant_employees(
        self,
        target_month: int,
        target_year: int,
        include_inactive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get list of all compliant employees.
        
        Uses unified ComplianceCalculator.
        
        Args:
            target_month: Month to check
            target_year: Year to check
            include_inactive: Include employees who left company
        
        Returns:
            list: List of compliant employee data
        """
        # Use unified calculator
        result = self.calculator.get_compliant_employees(
            target_month,
            target_year,
            include_inactive=include_inactive
        )
        
        return result['compliant_employees']
    
    def is_compliance_rule_active(self) -> bool:
        """
        Check if 33% compliance rule is currently active.
        
        Returns:
            bool: True if rule is active (after 15th of month)
        """
        return self.calculator.is_rule_active()
    
    def get_current_target_month_year(self) -> Tuple[int, int]:
        """
        Get the target month and year for compliance checking.
        
        Returns:
            tuple: (target_month, target_year) - previous month
        """
        return self.calculator.get_current_target_period()
    
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
