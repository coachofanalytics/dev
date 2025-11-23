"""
Shared Core Users

Re-exports user models and choices from accounts.
All apps should import user models from shared_core.users, not accounts.models.

This provides:
- CustomerUser: Custom user model
- UserCategory: User category choices
"""
from accounts.models import CustomerUser
from accounts.choices import UserCategory

__all__ = ['CustomerUser', 'UserCategory']

