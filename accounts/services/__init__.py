"""
Accounts Services Package

This package contains service layer classes for the Identity & Access Management bounded context.
Following the modular monolith architecture plan, these services encapsulate business logic
and provide clean interfaces for views and other components.
"""

from .user_service import UserService

__all__ = [
    'UserService',
]
