"""
Enhanced Budget Service with 33% Compliance Checking

Integrates employee compliance validation with budget submission process.
Ensures only compliant employees are included in budget approvals and
sends notifications to non-compliant employees.

Business Rule Integration: 33% completion rule enforcement at budget submission level.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal
from datetime import datetime, date, timedelta
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

# Import services
from management.services.employee_compliance_service import EmployeeComplianceService
from finance.services.base_service import BaseFinanceService
from finance.services.email_service import EmailService

# Import models
from finance.models import BudgetEstimateProjection, BudgetRequest, BudgetCategory, BudgetSubCategory
from accounts.models import CustomerUser, Department

logger = logging.getLogger(__name__)
User = get_user_model()


class EnhancedBudgetService(BaseFinanceService):
    """
    Enhanced budget service with 33% compliance checking integration.
    
    Provides:
    - Budget submission with compliance validation
    - Email notifications for non-compliant employees
    - Compliance-based employee filtering
    - Integration with existing budget approval workflow
    """
    
    def __init__(self):
        super().__init__()
        self.logger = logger
        self.compliance_service = EmployeeComplianceService()
        self.email_service = EmailService()
    
    def prepare_budget_submission_with_compliance(self, budget_data: Dict[str, Any], 
                                                user: User, 
                                                request=None) -> Dict[str, Any]:
        """
        Prepare budget submission with 33% compliance validation.
        
        Args:
            budget_data: Budget submission data
            user: User submitting the budget
            request: HTTP request object (optional)
            
        Returns:
            dict: {
                'compliant_employees': list,
                'non_compliant_employees': list,
                'emails_sent': int,
                'budget_submission': BudgetEstimateProjection,
                'compliance_summary': dict,
                'success': bool,
                'message': str
            }
        """
        try:
            with transaction.atomic():
                # Check if compliance rule is active
                is_rule_active = self.compliance_service.is_compliance_rule_active()
                target_month, target_year = self.compliance_service.get_current_target_month_year()
                
                if not is_rule_active:
                    # Before 15th - no compliance check needed, submit all employees
                    return self._create_budget_submission_without_compliance(budget_data, user)
                
                # After 15th - enforce 33% rule
                return self._create_budget_submission_with_compliance(
                    budget_data, user, target_month, target_year
                )
                
        except Exception as e:
            self.logger.error(f"Error preparing budget submission with compliance: {e}")
            return {
                'compliant_employees': [],
                'non_compliant_employees': [],
                'emails_sent': 0,
                'budget_submission': None,
                'compliance_summary': {},
                'success': False,
                'message': f"Error preparing budget submission: {str(e)}"
            }
    
    def _create_budget_submission_with_compliance(self, budget_data: Dict[str, Any], 
                                                user: User, 
                                                target_month: int, 
                                                target_year: int) -> Dict[str, Any]:
        """
        Create budget submission with compliance checking.
        """
        try:
            # Get compliance data
            compliant_employees = self.compliance_service.get_compliant_employees(target_month, target_year)
            non_compliant_employees = self.compliance_service.get_non_compliant_employees(target_month, target_year)
            
            # Send email notifications to non-compliant employees
            emails_sent = 0
            for emp_data in non_compliant_employees:
                success = self._send_compliance_notification(emp_data['employee'], emp_data['compliance'])
                if success:
                    emails_sent += 1
            
            # Create budget submission with only compliant employees
            budget_submission = self._create_budget_submission(
                budget_data, 
                user, 
                compliant_employees=compliant_employees
            )
            
            # Generate compliance summary
            compliance_summary = {
                'total_employees': len(compliant_employees) + len(non_compliant_employees),
                'compliant_count': len(compliant_employees),
                'non_compliant_count': len(non_compliant_employees),
                'compliance_rate': (len(compliant_employees) / (len(compliant_employees) + len(non_compliant_employees)) * 100) if (len(compliant_employees) + len(non_compliant_employees)) > 0 else 0,
                'target_month': target_month,
                'target_year': target_year,
                'emails_sent': emails_sent
            }
            
            return {
                'compliant_employees': compliant_employees,
                'non_compliant_employees': non_compliant_employees,
                'emails_sent': emails_sent,
                'budget_submission': budget_submission,
                'compliance_summary': compliance_summary,
                'success': True,
                'message': f'Budget submitted with {len(compliant_employees)} compliant employees. {len(non_compliant_employees)} non-compliant employees notified.'
            }
            
        except Exception as e:
            self.logger.error(f"Error creating budget submission with compliance: {e}")
            raise
    
    def _create_budget_submission_without_compliance(self, budget_data: Dict[str, Any], 
                                                   user: User) -> Dict[str, Any]:
        """
        Create budget submission without compliance checking (before 15th of month).
        """
        try:
            # Get all active employees
            all_employees = CustomerUser.objects.filter(is_staff=True, is_active=True)
            
            budget_submission = self._create_budget_submission(
                budget_data, 
                user, 
                compliant_employees=[{'employee': emp} for emp in all_employees]
            )
            
            return {
                'compliant_employees': [{'employee': emp} for emp in all_employees],
                'non_compliant_employees': [],
                'emails_sent': 0,
                'budget_submission': budget_submission,
                'compliance_summary': {
                    'total_employees': all_employees.count(),
                    'compliant_count': all_employees.count(),
                    'non_compliant_count': 0,
                    'compliance_rate': 100.0,
                    'rule_active': False,
                    'message': 'Compliance rule not active (before 15th of month)'
                },
                'success': True,
                'message': 'Budget submitted with all employees (compliance rule not active)'
            }
            
        except Exception as e:
            self.logger.error(f"Error creating budget submission without compliance: {e}")
            raise
    
    def _create_budget_submission(self, budget_data: Dict[str, Any], 
                                user: User, 
                                compliant_employees: List[Dict[str, Any]]) -> BudgetEstimateProjection:
        """
        Create the actual budget submission record.
        """
        try:
            # Extract budget data
            company = budget_data.get('company')
            department = budget_data.get('department')
            horizon = budget_data.get('horizon', 'monthly')
            method = budget_data.get('method', 'average')
            estimates = budget_data.get('estimates', {})
            
            # Calculate total estimate from compliant employees
            total_estimate = Decimal('0.00')
            for emp_data in compliant_employees:
                employee = emp_data['employee']
                # Add employee-specific budget calculations here
                # This would integrate with existing budget calculation logic
                employee_estimate = self._calculate_employee_budget(employee, estimates)
                total_estimate += employee_estimate
            
            # Create budget projection
            budget_submission = BudgetEstimateProjection.objects.create(
                company=company,
                department=department,
                horizon=horizon,
                method=method,
                estimates=estimates,
                total_estimate=total_estimate,
                status='submitted',
                created_by=user,
                submitted_at=datetime.now()
            )
            
            return budget_submission
            
        except Exception as e:
            self.logger.error(f"Error creating budget submission record: {e}")
            raise
    
    def _calculate_employee_budget(self, employee: User, estimates: Dict[str, Any]) -> Decimal:
        """
        Calculate budget estimate for a specific employee.
        This would integrate with existing budget calculation logic.
        """
        try:
            # This is a placeholder - integrate with actual budget calculation logic
            # from the existing budget system
            
            base_salary = getattr(employee, 'base_salary', Decimal('0.00'))
            department_multiplier = estimates.get('department_multiplier', Decimal('1.00'))
            performance_multiplier = estimates.get('performance_multiplier', Decimal('1.00'))
            
            return base_salary * department_multiplier * performance_multiplier
            
        except Exception as e:
            self.logger.error(f"Error calculating budget for employee {employee.username}: {e}")
            return Decimal('0.00')
    
    def _send_compliance_notification(self, employee: User, compliance_data: Dict[str, Any]) -> bool:
        """
        Send email notification to non-compliant employee.
        """
        try:
            context = {
                'employee_name': compliance_data['employee_name'],
                'employee_username': compliance_data['employee_username'],
                'completion_rate': compliance_data['completion_rate'],
                'total_tasks': compliance_data['total_tasks'],
                'completed_tasks': compliance_data['completed_tasks'],
                'required_tasks': compliance_data['required_tasks'],
                'missing_tasks': compliance_data['missing_tasks'],
                'threshold': compliance_data['threshold'],
                'target_month': compliance_data['target_month'],
                'target_year': compliance_data['target_year'],
                'current_date': datetime.now().strftime('%B %d, %Y'),
                'deadline': '15th of next month',
                'dashboard_url': '/dashboard/',  # Add actual dashboard URL
                'tasks_url': '/management/tasks/'  # Add actual tasks URL
            }
            
            success = self.email_service.send_email(
                to_email=employee.email,
                subject='Action Required: Complete 33% of Tasks for Payroll Approval',
                template_name='management/email/compliance_notification.html',
                context=context
            )
            
            if success:
                self.logger.info(f"Compliance notification sent to {employee.username}")
            else:
                self.logger.error(f"Failed to send compliance notification to {employee.username}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending compliance notification to {employee.username}: {e}")
            return False
    
    def get_compliance_report_for_budget(self, budget_id: int) -> Dict[str, Any]:
        """
        Get compliance report for a specific budget submission.
        """
        try:
            budget = BudgetEstimateProjection.objects.get(id=budget_id)
            target_month, target_year = self.compliance_service.get_current_target_month_year()
            
            # Get compliance data for the budget's department
            if budget.department:
                department_report = self.compliance_service.get_department_compliance_report(
                    budget.department, target_month, target_year
                )
            else:
                # Company-wide report
                department_report = self.compliance_service.get_company_compliance_report(
                    target_month, target_year
                )
            
            return {
                'budget': budget,
                'compliance_report': department_report,
                'target_month': target_month,
                'target_year': target_year,
                'is_rule_active': self.compliance_service.is_compliance_rule_active()
            }
            
        except BudgetEstimateProjection.DoesNotExist:
            self.logger.error(f"Budget {budget_id} not found")
            return {'error': 'Budget not found'}
        except Exception as e:
            self.logger.error(f"Error getting compliance report for budget {budget_id}: {e}")
            return {'error': str(e)}
    
    def send_bulk_compliance_notifications(self, target_month: int, target_year: int) -> Dict[str, Any]:
        """
        Send bulk compliance notifications to all non-compliant employees.
        """
        try:
            non_compliant_employees = self.compliance_service.get_non_compliant_employees(target_month, target_year)
            emails_sent = 0
            failed_emails = []
            
            for emp_data in non_compliant_employees:
                success = self._send_compliance_notification(emp_data['employee'], emp_data['compliance'])
                if success:
                    emails_sent += 1
                else:
                    failed_emails.append(emp_data['employee'].username)
            
            return {
                'success': True,
                'total_non_compliant': len(non_compliant_employees),
                'emails_sent': emails_sent,
                'failed_emails': failed_emails,
                'message': f'Notifications sent to {emails_sent} out of {len(non_compliant_employees)} non-compliant employees'
            }
            
        except Exception as e:
            self.logger.error(f"Error sending bulk compliance notifications: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to send compliance notifications'
            }
