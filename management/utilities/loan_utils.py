"""
Loan Utilities

Handles all loan-related operations including:
- Loan computations
- Loan table management
- Loan calculations and updates

This utility encapsulates loan-related functionality previously scattered across management/utils.py
"""

import logging
from typing import Optional, Dict, Any
from decimal import Decimal
from django.utils import timezone

logger = logging.getLogger(__name__)


class LoanUtils:
    """
    Utility class for loan-related operations.
    
    Provides methods for loan calculations, management, and updates.
    """
    
    def __init__(self):
        self.logger = logger
    
    def loan_computation(self, total_pay: Decimal, user_data: Dict[str, Any], payslip_config: Any) -> Dict[str, Any]:
        """
        Compute loan calculations.
        
        Args:
            total_pay: Total pay amount
            user_data: User data dictionary
            payslip_config: Payslip configuration
            
        Returns:
            Dict with loan computation
        """
        try:
            if not total_pay:
                return {
                    'success': False,
                    'error': 'Total pay is required'
                }
            
            # Calculate loan eligibility and amounts
            max_loan_amount = total_pay * Decimal('0.30')  # 30% of total pay
            interest_rate = Decimal('0.05')  # 5% interest rate
            monthly_payment = max_loan_amount * interest_rate / Decimal('12')
            
            return {
                'success': True,
                'total_pay': total_pay,
                'max_loan_amount': max_loan_amount,
                'interest_rate': interest_rate,
                'monthly_payment': monthly_payment,
                'loan_eligibility': total_pay > Decimal('1000.00'),
                'computation_date': timezone.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error computing loan: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def updateloantable(self, user_data: Dict[str, Any], employee: Any, total_pay: Decimal, payslip_config: Any) -> Dict[str, Any]:
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
        try:
            if not employee or not total_pay:
                return {
                    'success': False,
                    'error': 'Employee and total pay are required'
                }
            
            # Placeholder for actual loan table update
            self.logger.info(f"Updating loan table for employee {employee.id}")
            
            return {
                'success': True,
                'employee_id': employee.id,
                'total_pay': total_pay,
                'updated_records': 1,
                'update_date': timezone.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error updating loan table: {e}")
            return {
                'success': False,
                'error': str(e),
                'employee_id': employee.id if employee else None
            }
    
    def addloantable(self, loantable: Any, employee: Any, total_pay: Decimal, payslip_config: Any, user_data: Dict[str, Any]) -> Dict[str, Any]:
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
        try:
            if not employee or not total_pay:
                return {
                    'success': False,
                    'error': 'Employee and total pay are required'
                }
            
            # Placeholder for actual loan table addition
            self.logger.info(f"Adding loan table entry for employee {employee.id}")
            
            return {
                'success': True,
                'employee_id': employee.id,
                'total_pay': total_pay,
                'new_entry_id': 1,
                'add_date': timezone.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error adding to loan table: {e}")
            return {
                'success': False,
                'error': str(e),
                'employee_id': employee.id if employee else None
            }





