# -*- coding: utf-8 -*-
"""
Finance Models Package

Organized models for the finance app:
- core: Core models (Transaction, Inflow, Payment_Information, etc.)
- budget: Budget-specific models (Budget, BudgetCategory, BudgetRequest, etc.)
- loan: Loan-specific models (LoanApplication, LoanProduct, LoanPayment, etc.)
- payment: Payment-specific models (PaymentMethod, PaymentTransaction, etc.)
- notifications: Notification models (FinanceNotification, BudgetAlert, etc.)
"""

# Import all models from organized structure (direct imports from .py files)
from .core import *
from .budget import *
from .loan import *
from .payment import *
from .notifications import *

__all__ = [
    # Core models
    'DeletedPaymentHistory',
    'Default_Payment_Fees',
    'PayslipConfig',
    'Inflow',
    'DC48_Inflow',
    'Transaction',
    'Field_Expense',
    'BalanceSheetCategory',
    'WebCategory',
    'WebSubCategory',
    'Supplier',
    'Food',
    'FoodHistory',
    
    # Budget models
    'BudgetCategory',
    'BudgetSubCategory',
    'BudgetItemLibrary',
    'Budget',
    'BudgetEstimationTemplate',
    'BudgetEstimateProjection',
    'MultiYearBudgetPlan',
    
    # Loan models
    'LoanProduct',
    'LoanApplication',
    'LoanPayment',
    'LoanCollateral',
    'LoanRollover',
    'LoanConfiguration',
    'LoanDecisionAudit',
    'LoanPerformance',
    
    # Payment models
    'Payment',
    'PaymentMethod',
    'PaymentTransaction',
    'PaymentGateway',
    
    # Notification models
    'FinanceNotification',
    'BudgetAlert',
    'LoanNotification',
    'DepartmentNotification',
    'DepartmentAnnouncement',
    'UserDashboardPreferences',
    
    # Model modules
    'core', 'budget', 'loan', 'payment', 'notifications',
]