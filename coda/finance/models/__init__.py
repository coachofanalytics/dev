"""
Finance models package.
Organized by domain for better maintainability.
"""

# Core models
from .core import (
    Transaction,
    Budget,
    BudgetCategory,
    BudgetSubCategory,
    BudgetItemLibrary,
    BudgetEstimateProjection,
    Supplier,
    Food,
    FoodHistory,
)

# Budget models
from .budget import (
    BudgetRequest,
    ApprovalPolicy,
    BudgetVariance,
)

# Loan models
from .loan import (
    LoanApplication,
    LoanProduct,
    LoanPayment,
    LoanCollateral,
)

# Payment models
from .payment import (
    PaymentMethod,
    PaymentTransaction,
    PaymentGateway,
)

# Notification models
from .notifications import (
    FinanceNotification,
    BudgetAlert,
)

__all__ = [
    # Core
    'Transaction',
    'Budget',
    'BudgetCategory',
    'BudgetSubCategory',
    'BudgetItemLibrary',
    'BudgetEstimateProjection',
    'Supplier',
    'Food',
    'FoodHistory',
    
    # Budget
    'BudgetRequest',
    'ApprovalPolicy',
    'BudgetVariance',
    
    # Loan
    'LoanApplication',
    'LoanProduct',
    'LoanPayment',
    'LoanCollateral',
    
    # Payment
    'PaymentMethod',
    'PaymentTransaction',
    'PaymentGateway',
    
    # Notifications
    'FinanceNotification',
    'BudgetAlert',
]
