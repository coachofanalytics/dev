"""
Shared Core Credential Store

Re-exports credential store service from accounts.services.credential_store.
All apps should import credential_store from shared_core.services.credential_store,
not accounts.services.credential_store.

This provides:
- credential_store: Service for managing encrypted API credentials (OptionPlay, Unusual Whales, etc.)
"""
from accounts.services.credential_store import credential_store

__all__ = ['credential_store']

