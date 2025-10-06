"""
Finance Services Package

This package contains service layer classes for the Finance & Lending bounded context.
Following the modular monolith architecture plan, these services encapsulate business logic
and provide clean interfaces for views and other components.

Organized by domain:
- core: Base service classes
- budget: Budget-related services
- loan: Loan-related services
- payment: Payment-related services
"""

# Import organized services
from .core.base import BaseFinanceService
from .budget.estimation import BudgetEstimationService
from .budget.consolidation import BudgetConsolidationService
from .loan.eligibility import LoanEligibilityService
from .loan.performance import LoanPerformanceService
from .payment.processing import PaymentProcessingService
from .analytics_service import FinancialAnalyticsService

# Import service modules
from . import core, budget, loan, payment

__all__ = [
    'BaseFinanceService',
    'BudgetEstimationService',
    'BudgetConsolidationService',
    'LoanEligibilityService',
    'LoanPerformanceService',
    'PaymentProcessingService',
    'FinancialAnalyticsService',
    'core', 'budget', 'loan', 'payment',
]