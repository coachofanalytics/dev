"""
Shared Core Package

Re-exports shared models, utilities, mixins, and services from main and accounts apps.
This provides a consistent import interface for all apps.

All apps should import from shared_core instead of directly from main/accounts.

Example:
    # Instead of:
    from main.models import TimeStampedModel
    from accounts.models import CustomerUser
    
    # Use:
    from shared_core.models import TimeStampedModel
    from shared_core.users import CustomerUser
"""

__version__ = '1.0.0'


