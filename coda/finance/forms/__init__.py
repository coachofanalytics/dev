# -*- coding: utf-8 -*-
"""
Finance Forms Package
Imports all forms from legacy files and organized structure
"""

# Import from legacy forms files
from .. import forms as legacy_forms

# Import from improved forms
from ..forms_improved import SmartTransactionForm

# Import from organized forms
from .budget import *

__all__ = [
    # Legacy forms
    'legacy_forms',
    
    # Improved forms
    'SmartTransactionForm',
]
