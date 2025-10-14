"""
Finance models - organized by domain for better maintainability.

This file now imports from the organized model structure:
- models.core: Core models (Transaction, Inflow, Payment_Information, etc.)
- models.budget: Budget-specific models (Budget, BudgetCategory, BudgetRequest, etc.)
- models.loan: Loan-specific models (LoanApplication, LoanProduct, LoanPayment, etc.)
- models.payment: Payment-specific models (PaymentMethod, PaymentTransaction, etc.)
- models.notifications: Notification models (FinanceNotification, BudgetAlert, etc.)
"""

# Import all models from organized structure
from .models.core import *
from .models.budget import *
from .models.loan import *
from .models.payment import *
from .models.notifications import *

# All model definitions have been moved to organized structure:
# - Core models: models/core.py
# - Budget models: models/budget.py  
# - Loan models: models/loan.py
# - Payment models: models/payment.py
# - Notification models: models/notifications.py