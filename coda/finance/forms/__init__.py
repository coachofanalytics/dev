# -*- coding: utf-8 -*-
"""
Finance Forms Package
Clean organized structure without circular imports
"""

# Import from legacy forms files directly
import importlib.util
import os

# Load legacy forms module directly
legacy_forms_path = os.path.join(os.path.dirname(__file__), '..', 'forms.py')
spec = importlib.util.spec_from_file_location("legacy_forms", legacy_forms_path)
legacy_forms = importlib.util.module_from_spec(spec)
spec.loader.exec_module(legacy_forms)

# Make legacy forms available
BudgetRequestForm = legacy_forms.BudgetRequestForm
TransactionForm = legacy_forms.TransactionForm
InflowForm = legacy_forms.InflowForm
DepartmentFilterForm = legacy_forms.DepartmentFilterForm
FoodHistoryForm = legacy_forms.FoodHistoryForm
BudgetForm = legacy_forms.BudgetForm

# Import from improved forms
from ..forms_improved import SmartTransactionForm

# Import from organized forms
from .budget import *

__all__ = [
    # Legacy forms
    'BudgetRequestForm',
    'TransactionForm',
    'InflowForm',
    'DepartmentFilterForm',
    'FoodHistoryForm',
    'BudgetForm',
    
    # Improved forms
    'SmartTransactionForm',
]