"""
Finance Task Service Interface

Abstract interface for finance-related services used by management app.
Defines the contract for checking loans, payment history, and payslip configuration.

This interface is implemented by:
- FinanceTaskAdapter (in finance app) - wraps LoanApplication, Payment_History, PayslipConfig
- NoOpFinanceTaskServiceAdapter (in shared_core) - safe fallback when finance is not installed
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from decimal import Decimal


class FinanceTaskServiceInterface(ABC):
    """
    Abstract interface for finance services related to task management.
    
    This interface defines what management needs from finance app for:
    - Loan status checking (affects task assignment/filtering)
    - Payment history checking (affects permissions)
    - Payslip configuration (affects payroll calculations)
    
    All methods return dicts/primitives, never Django models, to ensure
    loose coupling between apps.
    """
    
    @abstractmethod
    def has_active_loan(self, user_id: int) -> bool:
        """
        Check if a user has an active loan.
        
        Used by:
        - Task assignment logic (filtering tasks based on loan status)
        - User data retrieval in views
        
        Args:
            user_id: ID of the user to check
            
        Returns:
            bool - True if user has an active loan, False otherwise
            
        Example:
            if finance_service.has_active_loan(employee.id):
                # Filter tasks or apply loan-related logic
        """
        pass
    
    @abstractmethod
    def get_user_loan_summary(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get loan summary information for a user.
        
        Used by:
        - Views that display user financial information
        - Task assignment workflows that need loan details
        
        Args:
            user_id: ID of the user to get loan info for
            
        Returns:
            Dict with loan details or None if no active loan:
            - loan_id: int - Loan application ID
            - borrower_id: int - User ID
            - amount: Decimal - Loan amount
            - status: str - Loan status (e.g., 'active', 'paid', 'pending')
            - remaining_balance: Optional[Decimal] - Remaining balance
            - monthly_payment: Optional[Decimal] - Monthly payment amount
            - start_date: Optional[date] - Loan start date
            - Other loan metadata
            
        Example:
            {
                'loan_id': 123,
                'borrower_id': 456,
                'amount': Decimal('5000.00'),
                'status': 'active',
                'remaining_balance': Decimal('3000.00'),
                'monthly_payment': Decimal('500.00')
            }
        """
        pass
    
    @abstractmethod
    def has_payment_history(self, user_id: int) -> bool:
        """
        Check if a user has payment history records.
        
        Used by:
        - Permission checking functions (students/consultants must have payment history)
        - Access control for certain features
        
        Args:
            user_id: ID of the user to check
            
        Returns:
            bool - True if user has payment history, False otherwise
            
        Example:
            if not finance_service.has_payment_history(user.id):
                # Deny access or show warning
        """
        pass
    
    @abstractmethod
    def get_payslip_config(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get payslip configuration for a user.
        
        Used by:
        - Payroll calculations
        - Payslip generation
        - Task payment calculations
        
        Args:
            user_id: ID of the user to get payslip config for
            
        Returns:
            Dict with payslip configuration or None if not found:
            - user_id: int - User ID
            - loan_amount: Optional[Decimal] - Loan amount
            - loan_repayment_percentage: Optional[Decimal] - Repayment percentage
            - laptop_status: Optional[bool] - Laptop status
            - ls_amount: Optional[Decimal] - Laptop status amount
            - rp_starting_amount: Optional[Decimal] - Retirement starting amount
            - Other payslip configuration fields
            
        Example:
            {
                'user_id': 456,
                'loan_amount': Decimal('5000.00'),
                'loan_repayment_percentage': Decimal('10.00'),
                'laptop_status': False,
                'ls_amount': Decimal('10000.00'),
                'rp_starting_amount': Decimal('200.00')
            }
        """
        pass
    
    @abstractmethod
    def get_recent_payments_for_user(
        self,
        user_id: int,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recent payment history for a user.
        
        Used by:
        - Payment history displays
        - Financial reporting
        
        Args:
            user_id: ID of the user to get payments for
            limit: Maximum number of payments to return
            
        Returns:
            List of payment dicts:
            - payment_id: int - Payment ID
            - customer_id: int - User ID
            - amount: Decimal - Payment amount
            - payment_date: date - Payment date
            - payment_method: Optional[str] - Payment method
            - status: str - Payment status
            - Other payment metadata
            
        Example:
            [
                {
                    'payment_id': 789,
                    'customer_id': 456,
                    'amount': Decimal('100.00'),
                    'payment_date': date(2025, 12, 1),
                    'status': 'completed'
                }
            ]
        """
        pass











