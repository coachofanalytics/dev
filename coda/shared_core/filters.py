"""
Shared Core Filters

Re-exports Django filters from main.filters.
All apps should import filters from shared_core.filters, not main.filters.

This provides:
- ReturnsFilter: Filter for returns/performance data
- CredentialFilter: Filter for credentials
"""
from main.filters import ReturnsFilter, CredentialFilter, FoodFilter

__all__ = ['ReturnsFilter', 'CredentialFilter', 'FoodFilter']

