"""
Finance models package.
Organized by domain for better maintainability.
"""

# Core models
from .core import (
    Transaction,
    Inflow,
    Budget,
    BudgetCategory,
    BudgetSubCategory,
    BudgetItemLibrary,
    BudgetEstimateProjection,
    BudgetEstimationTemplate,
    MultiYearBudgetPlan,
    Supplier,
    Food,
    FoodHistory,
    Payment_Information,
    Payment_History,
    WebCategory,
    WebSubCategory,
    PayslipConfig,
    CodaBudget,
    BalanceSheetCategory,
)

# Budget models
from .budget import (
    BudgetRequest,
    ApprovalPolicy,
    BudgetVariance,
    DisbursementRequest,
    AutomationAuditLog,
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
    'Inflow',
    'Budget',
    'BudgetCategory',
    'BudgetSubCategory',
    'BudgetItemLibrary',
    'BudgetEstimateProjection',
    'BudgetEstimationTemplate',
    'MultiYearBudgetPlan',
    'Supplier',
    'Food',
    'FoodHistory',
    'Payment_Information',
    'Payment_History',
    'WebCategory',
    'WebSubCategory',
    'PayslipConfig',
    'CodaBudget',
    'BalanceSheetCategory',
    
    # Budget
    'BudgetRequest',
    'ApprovalPolicy',
    'BudgetVariance',
    'DisbursementRequest',
    'AutomationAuditLog',
    
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
