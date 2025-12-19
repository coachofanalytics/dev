"""
No-Op Finance Task Service Adapter

Fallback implementation of FinanceTaskServiceInterface that provides safe default behavior
when the finance app is not installed or unavailable.

This adapter ensures that management app can run standalone without crashing,
while gracefully degrading finance-related functionality when finance app is unavailable.
"""

import logging
from typing import Dict, List, Optional, Any
from decimal import Decimal

from shared_core.interfaces.finance_task_service import FinanceTaskServiceInterface


logger = logging.getLogger(__name__)


class NoOpFinanceTaskServiceAdapter(FinanceTaskServiceInterface):
    """
    No-operation finance task service adapter.
    
    Implements FinanceTaskServiceInterface with safe defaults that indicate:
    - No loans (returns False, None)
    - No payment history (returns False)
    - No payslip config (returns None)
    - Empty payment lists
    
    This allows the management app to run without the finance app installed,
    while clearly indicating that finance features are unavailable.
    
    Usage:
        # In management services:
        try:
            from finance.adapters.finance_task_adapter import FinanceTaskAdapter
            finance_service = FinanceTaskAdapter()
        except ImportError:
            from shared_core.services.adapters.noop_finance_task_adapter import NoOpFinanceTaskServiceAdapter
            finance_service = NoOpFinanceTaskServiceAdapter()
    """
    
    def __init__(self):
        """Initialize the no-op adapter with logging."""
        self.logger = logger
        self.logger.info("NoOpFinanceTaskServiceAdapter initialized - Finance services unavailable")
    
    def has_active_loan(self, user_id: int) -> bool:
        """
        Return False when finance services are unavailable.
        
        Returns False (no active loan) to allow task assignment to proceed
        without blocking on loan status checks.
        """
        self.logger.debug(f"NoOp: has_active_loan called for user_id={user_id}")
        return False
    
    def get_user_loan_summary(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Return None when finance services are unavailable.
        
        Returns None to indicate no loan information available, allowing
        calling code to handle gracefully (e.g., skip loan-related logic).
        """
        self.logger.debug(f"NoOp: get_user_loan_summary called for user_id={user_id}")
        return None
    
    def has_payment_history(self, user_id: int) -> bool:
        """
        Return True when finance services are unavailable.
        
        Returns True (has payment history) to avoid blocking access for
        users when finance app is not installed. This is a safe default
        that allows access, rather than blocking it.
        
        Note: In production, you might want to return False and explicitly
        handle permission checks, but True is safer for graceful degradation.
        """
        self.logger.debug(f"NoOp: has_payment_history called for user_id={user_id}")
        # Return True to avoid blocking access when finance is unavailable
        # This is a safe default - permission checks should handle this gracefully
        return True
    
    def get_payslip_config(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Return None when finance services are unavailable.
        
        Returns None to indicate no payslip configuration available, allowing
        calling code to use default values or skip payslip-related calculations.
        """
        self.logger.debug(f"NoOp: get_payslip_config called for user_id={user_id}")
        return None
    
    def get_recent_payments_for_user(
        self,
        user_id: int,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Return empty list when finance services are unavailable.
        
        Returns empty list instead of crashing, allowing calling code to
        display "no payments" or skip payment history features.
        """
        self.logger.debug(
            f"NoOp: get_recent_payments_for_user called for user_id={user_id}, limit={limit}"
        )
        return []











