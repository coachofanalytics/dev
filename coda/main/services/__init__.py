"""
Main Services Package

This package contains service layer classes for the Main/Core bounded context.
Following the modular monolith architecture plan, these services encapsulate business logic
and provide clean interfaces for views and other components.
"""

from .core_service import CoreService

__all__ = [
    'CoreService',
]
