# -*- coding: utf-8 -*-
"""
Finance Notification Models

Notification-related models including FinanceNotification, BudgetAlert, LoanNotification, and related models.
"""

# Import all models from the notifications.py file
from .notifications import *

__all__ = [
    'FinanceNotification',
    'BudgetAlert',
    'LoanNotification',
    'DepartmentNotification',
    'DepartmentAnnouncement',
    'UserDashboardPreferences',
]
