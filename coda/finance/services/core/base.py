"""
Base service classes for the finance application.
Provides common functionality and patterns for all finance services.
"""

import logging
from typing import Dict, List, Optional, Any
from django.db import transaction
from django.core.exceptions import ValidationError


class BaseFinanceService:
    """
    Base class for all finance services providing common functionality.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def log_info(self, message: str, **kwargs):
        """Log info message with context."""
        self.logger.info(f"{message} | Context: {kwargs}")
    
    def log_error(self, message: str, error: Exception = None, **kwargs):
        """Log error message with context and exception."""
        if error:
            self.logger.error(f"{message} | Context: {kwargs}", exc_info=True)
        else:
            self.logger.error(f"{message} | Context: {kwargs}")
    
    def validate_required_fields(self, data: Dict, required_fields: List[str]) -> bool:
        """Validate that required fields are present in data."""
        missing_fields = [field for field in required_fields if field not in data or not data[field]]
        if missing_fields:
            raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")
        return True
    
    def safe_get(self, data: Dict, key: str, default: Any = None) -> Any:
        """Safely get value from dictionary with default."""
        return data.get(key, default)
    
    @transaction.atomic
    def execute_with_transaction(self, func, *args, **kwargs):
        """Execute function within database transaction."""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.log_error(f"Transaction failed in {func.__name__}", e)
            raise


class BudgetServiceMixin:
    """Mixin for budget-related service functionality."""
    
    def calculate_budget_totals(self, budgets) -> Dict[str, float]:
        """Calculate total amounts for budget collections."""
        totals = {
            'estimated': 0,
            'actual': 0,
            'variance': 0
        }
        
        for budget in budgets:
            totals['estimated'] += float(budget.estimated_amount or 0)
            totals['actual'] += float(budget.actual_spent or 0)
            totals['variance'] += float(budget.variance or 0)
        
        return totals
    
    def calculate_variance_percentage(self, estimated: float, actual: float) -> float:
        """Calculate variance percentage."""
        if estimated == 0:
            return 0
        return ((actual - estimated) / estimated) * 100


class LoanServiceMixin:
    """Mixin for loan-related service functionality."""
    
    def calculate_loan_eligibility(self, company, requested_amount: float) -> Dict[str, Any]:
        """Calculate loan eligibility based on company budget."""
        # This will be implemented by specific loan services
        return {
            'eligible': False,
            'max_amount': 0,
            'reason': 'Not implemented'
        }
    
    def calculate_interest(self, principal: float, rate: float, term_months: int) -> float:
        """Calculate simple interest."""
        return (principal * rate * term_months) / 12


class PaymentServiceMixin:
    """Mixin for payment-related service functionality."""
    
    def validate_payment_amount(self, amount: float) -> bool:
        """Validate payment amount is positive."""
        if amount <= 0:
            raise ValidationError("Payment amount must be positive")
        return True
    
    def format_currency(self, amount: float, currency: str = 'USD') -> str:
        """Format amount as currency string."""
        if currency == 'USD':
            return f"${amount:,.2f}"
        elif currency == 'KES':
            return f"KSh {amount:,.2f}"
        else:
            return f"{amount:,.2f} {currency}"
