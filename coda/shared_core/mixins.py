"""
Shared Core Mixins

Re-exports view mixins from accounts.mixins.
All apps should import mixins from shared_core.mixins, not accounts.mixins.

This provides:
- FilteredListViewMixin: ListView mixin with filtering support
"""
from accounts.mixins import FilteredListViewMixin

__all__ = ['FilteredListViewMixin']

