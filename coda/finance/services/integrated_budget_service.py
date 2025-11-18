"""
Integrated Budget Service for CODA Finance System

Combines employee salary calculations with budget item management for comprehensive
monthly budget approvals and reporting.

Business Logic:
- Salaries based on last month's task completion (33% compliance rule)
- Budget items from BudgetEstimateProjection (non-zero amounts only)
- Real-time compliance checking for salary inclusion
- Admin controls for employee type regulations

Created: October 2025
Phase: Budget-Salary Integration
"""

import logging
from decimal import Decimal
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Tuple
from django.db.models import Q, Sum, Count
from django.contrib.auth import get_user_model
from django.utils import timezone

from accounts.models import Department
from management.models import TaskHistory, Task
from management.utils import calculate_total_pay
from management.services.employee_compliance_service import EmployeeComplianceService
from finance.models import BudgetEstimateProjection, Budget, BudgetCategory

User = get_user_model()
logger = logging.getLogger(__name__)


class IntegratedBudgetService:
    """
    Service to integrate employee salary calculations with budget item management.
    
    Provides comprehensive monthly budget totals combining:
    1. Employee salaries (based on task completion and 33% compliance)
    2. Budget items (from BudgetEstimateProjection, non-zero amounts)
    3. Real-time compliance checking
    4. Admin controls and regulations
    
    Phase 2: Now supports consuming Management Budget Integration APIs
    """
    
    def __init__(self, use_api: bool = False):
        """
        Initialize the service.
        
        Args:
            use_api: If True, use Management Budget Integration APIs instead of direct DB queries
        """
        self.compliance_service = EmployeeComplianceService()
        self.logger = logging.getLogger(__name__)
        self.use_api = use_api
        
        if use_api:
            try:
                from finance.services.management_integration_service import ManagementIntegrationService
                self.management_api = ManagementIntegrationService()
                self.logger.info("Using Management Budget Integration APIs")
            except ImportError:
                self.logger.warning("ManagementIntegrationService not available, falling back to direct queries")
                self.use_api = False
                self.management_api = None
        else:
            self.management_api = None
    
    def get_monthly_budget_summary(self, target_month: int, target_year: int, 
                                 department: Optional[Department] = None) -> Dict[str, Any]:
        """
        Get comprehensive monthly budget summary combining salaries and budget items.
        
        Args:
            target_month: Month for budget calculation (last month's tasks)
            target_year: Year for budget calculation
            department: Optional department filter
            
        Returns:
            Dict with comprehensive budget summary
        """
        try:
            self.logger.info(f"Getting monthly budget summary for {target_month}/{target_year}")
            
            # Get salary information
            salary_data = self._get_compliant_employee_salaries(target_month, target_year, department)
            
            # Get budget items
            budget_items_data = self._get_budget_items_summary(target_month, target_year, department)
            
            # Calculate totals
            total_salaries = salary_data['total_amount']
            total_budget_items = budget_items_data['total_amount']
            grand_total = total_salaries + total_budget_items
            
            return {
                'period': f"{target_month}/{target_year}",
                'salary_data': salary_data,
                'budget_items_data': budget_items_data,
                'totals': {
                    'total_salaries': total_salaries,
                    'total_budget_items': total_budget_items,
                    'grand_total': grand_total
                },
                'compliance_status': {
                    'is_rule_active': self.compliance_service.is_compliance_rule_active(),
                    'compliance_threshold': 33,
                    'current_date': timezone.now().date()
                },
                'department_filter': department.name if department else 'All Departments'
            }
            
        except Exception as e:
            self.logger.error(f"Error getting monthly budget summary: {e}")
            return {'error': str(e)}
    
    def _get_compliant_employee_salaries(self, target_month: int, target_year: int, 
                                       department: Optional[Department] = None) -> Dict[str, Any]:
        """
        Get salary information for compliant employees based on last month's tasks.
        
        Phase 2: Can use Management Budget Integration API or direct DB queries.
        
        Uses the same logic as payslip calculation:
        - Get TaskHistory records for target month/year
        - Calculate earnings using (point/mxpoint) * mxearning
        - Include only employees meeting 33% compliance threshold
        """
        # Phase 2: Try API first if enabled
        if self.use_api and self.management_api:
            try:
                return self._get_salaries_from_api(target_month, target_year, department)
            except Exception as e:
                self.logger.warning(f"API call failed, falling back to direct query: {e}")
                # Fall through to direct query
        
        # Direct database query (original implementation)
        try:
            # Get TaskHistory records for the target month (last month's tasks)
            task_filter = Q(
                daf_date__month=target_month,
                daf_date__year=target_year,
                employee__is_active=True,
                employee__is_staff=True
            )
            
            if department:
                # Note: TaskHistory doesn't have direct department field
                # Filter by employees who have tasks in this department
                task_filter &= Q(employee__department=department)
            
            # Exclude system users
            excluded_usernames = ["coda_info", "luke", "angel"]
            task_filter &= ~Q(employee__username__in=excluded_usernames)
            
            task_history_records = TaskHistory.objects.filter(task_filter)
            
            # Group by employee and calculate compliance
            employee_data = {}
            compliant_employees = []
            non_compliant_employees = []
            
            for employee in User.objects.filter(is_active=True, is_staff=True):
                employee_tasks = task_history_records.filter(employee=employee)
                
                if not employee_tasks.exists():
                    continue
                
                # Calculate compliance (same logic as payslip)
                total_points = sum(task.point for task in employee_tasks)
                total_max_points = sum(task.mxpoint for task in employee_tasks)
                
                if total_max_points > 0:
                    compliance_rate = (total_points / total_max_points) * 100
                    
                    # Calculate salary (same logic as calculate_total_pay)
                    employee_salary = calculate_total_pay(employee_tasks)
                    
                    employee_info = {
                        'employee': employee,
                        'username': employee.username,
                        'full_name': employee.get_full_name(),
                        'department': getattr(employee, 'department', None),
                        'total_points': total_points,
                        'total_max_points': total_max_points,
                        'compliance_rate': round(compliance_rate, 2),
                        'salary_amount': employee_salary,
                        'task_count': employee_tasks.count()
                    }
                    
                    # Check compliance threshold
                    if compliance_rate >= 33.0:
                        compliant_employees.append(employee_info)
                    else:
                        non_compliant_employees.append(employee_info)
                    
                    employee_data[employee.id] = employee_info
            
            # Calculate totals
            total_salary_amount = sum(emp['salary_amount'] for emp in compliant_employees)
            
            return {
                'compliant_employees': compliant_employees,
                'non_compliant_employees': non_compliant_employees,
                'total_amount': total_salary_amount,
                'compliant_count': len(compliant_employees),
                'non_compliant_count': len(non_compliant_employees),
                'total_employees': len(employee_data)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting compliant employee salaries: {e}")
            return {
                'compliant_employees': [],
                'non_compliant_employees': [],
                'total_amount': Decimal('0.00'),
                'compliant_count': 0,
                'non_compliant_count': 0,
                'total_employees': 0,
                'error': str(e)
            }
    
    def _get_salaries_from_api(
        self,
        target_month: int,
        target_year: int,
        department: Optional[Department] = None
    ) -> Dict[str, Any]:
        """
        Get salary information from Management Budget Integration API.
        
        Phase 2: API-based implementation.
        """
        try:
            # Call Management API
            api_result = self.management_api.get_activity_totals(
                month=target_month,
                year=target_year,
                department_id=department.id if department else None,
                include_evidence=True,
                include_validation=True
            )
            
            if not api_result['success']:
                raise Exception(f"API call failed: {api_result.get('errors', [])}")
            
            api_data = api_result['data']
            totals = api_data.get('totals', {})
            validation_status = api_data.get('validation_status', {})
            
            # Extract employee data from by_department breakdown
            # Note: API returns aggregated data, so we need to reconstruct employee-level data
            # For now, return aggregated totals - can be enhanced to parse employee details
            
            compliant_count = validation_status.get('compliant_employees', 0)
            total_employees = validation_status.get('total_employees', 0)
            non_compliant_count = total_employees - compliant_count
            
            return {
                'compliant_employees': [],  # Can be enhanced to parse from API response
                'non_compliant_employees': [],  # Can be enhanced to parse from API response
                'total_amount': Decimal(str(totals.get('total_earnings', 0))),
                'compliant_count': compliant_count,
                'non_compliant_count': non_compliant_count,
                'total_employees': total_employees,
                'api_data': api_data,  # Include raw API data for reference
                'source': 'api'
            }
            
        except Exception as e:
            self.logger.error(f"Error getting salaries from API: {e}")
            raise
    
    def _get_budget_items_summary(self, target_month: int, target_year: int, 
                                department: Optional[Department] = None) -> Dict[str, Any]:
        """
        Get budget items summary (non-zero amounts only).
        
        Args:
            target_month: Month for filtering
            target_year: Year for filtering  
            department: Optional department filter
            
        Returns:
            Dict with budget items summary
        """
        try:
            # Get budget projections with non-zero amounts
            budget_filter = Q(
                status='submitted',
                total_estimate__gt=0  # Exclude zero budgets
            )
            
            if department:
                budget_filter &= Q(department=department)
            
            budget_projections = BudgetEstimateProjection.objects.filter(budget_filter)
            
            # Calculate totals and breakdowns
            total_amount = sum(projection.total_estimate for projection in budget_projections)
            
            # Category breakdown
            category_breakdown = {}
            for projection in budget_projections:
                category_name = projection.category.name if projection.category else 'Uncategorized'
                if category_name not in category_breakdown:
                    category_breakdown[category_name] = {
                        'count': 0,
                        'total_amount': Decimal('0.00')
                    }
                category_breakdown[category_name]['count'] += 1
                category_breakdown[category_name]['total_amount'] += projection.total_estimate
            
            return {
                'budget_projections': budget_projections,
                'total_amount': total_amount,
                'item_count': budget_projections.count(),
                'category_breakdown': category_breakdown
            }
            
        except Exception as e:
            self.logger.error(f"Error getting budget items summary: {e}")
            return {
                'budget_projections': [],
                'total_amount': Decimal('0.00'),
                'item_count': 0,
                'category_breakdown': {},
                'error': str(e)
            }
    
    def get_salary_dashboard_data(self, target_month: int, target_year: int, 
                                department: Optional[Department] = None) -> Dict[str, Any]:
        """
        Get detailed salary dashboard data for admin review.
        
        Returns comprehensive employee salary information with compliance status.
        """
        try:
            salary_data = self._get_compliant_employee_salaries(target_month, target_year, department)
            
            return {
                'period': f"{target_month}/{target_year}",
                'salary_data': salary_data,
                'compliance_summary': {
                    'threshold': 33,
                    'is_rule_active': self.compliance_service.is_compliance_rule_active(),
                    'current_date': timezone.now().date()
                },
                'department_filter': department.name if department else 'All Departments'
            }
            
        except Exception as e:
            self.logger.error(f"Error getting salary dashboard data: {e}")
            return {'error': str(e)}
    
    def get_employee_salary_details(self, employee: User, target_month: int, target_year: int) -> Dict[str, Any]:
        """
        Get detailed salary calculation for a specific employee.
        
        Shows the same calculation logic used in payslip view.
        """
        try:
            # Get employee's TaskHistory records for the target month
            task_history_records = TaskHistory.objects.filter(
                employee=employee,
                daf_date__month=target_month,
                daf_date__year=target_year
            )
            
            if not task_history_records.exists():
                return {
                    'employee': employee,
                    'period': f"{target_month}/{target_year}",
                    'error': 'No task history found for this period'
                }
            
            # Calculate detailed salary breakdown
            total_points = sum(task.point for task in task_history_records)
            total_max_points = sum(task.mxpoint for task in task_history_records)
            total_salary = calculate_total_pay(task_history_records)
            
            # Individual task breakdown
            task_breakdown = []
            for task in task_history_records:
                task_salary = task.get_pay if hasattr(task, 'get_pay') else 0
                task_breakdown.append({
                    'task': task,
                    'activity_name': task.activity_name,
                    'points': task.point,
                    'max_points': task.mxpoint,
                    'max_earning': task.mxearning,
                    'calculated_salary': task_salary,
                    'compliance_rate': (task.point / task.mxpoint * 100) if task.mxpoint > 0 else 0
                })
            
            compliance_rate = (total_points / total_max_points * 100) if total_max_points > 0 else 0
            is_compliant = compliance_rate >= 33.0
            
            return {
                'employee': employee,
                'period': f"{target_month}/{target_year}",
                'total_points': total_points,
                'total_max_points': total_max_points,
                'compliance_rate': round(compliance_rate, 2),
                'is_compliant': is_compliant,
                'total_salary': total_salary,
                'task_breakdown': task_breakdown,
                'task_count': task_history_records.count()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting employee salary details: {e}")
            return {'error': str(e)}
    
    def update_compliance_status(self, target_month: int, target_year: int) -> Dict[str, Any]:
        """
        Update compliance status for all employees and return summary.
        
        This can be called periodically to refresh compliance data.
        """
        try:
            salary_data = self._get_compliant_employee_salaries(target_month, target_year)
            
            return {
                'updated_at': timezone.now(),
                'period': f"{target_month}/{target_year}",
                'compliance_summary': {
                    'total_employees': salary_data['total_employees'],
                    'compliant_employees': salary_data['compliant_count'],
                    'non_compliant_employees': salary_data['non_compliant_count'],
                    'compliance_rate': (
                        salary_data['compliant_count'] / salary_data['total_employees'] * 100
                    ) if salary_data['total_employees'] > 0 else 0
                },
                'salary_summary': {
                    'total_compliant_salaries': salary_data['total_amount'],
                    'average_compliant_salary': (
                        salary_data['total_amount'] / salary_data['compliant_count']
                    ) if salary_data['compliant_count'] > 0 else Decimal('0.00')
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error updating compliance status: {e}")
            return {'error': str(e)}

