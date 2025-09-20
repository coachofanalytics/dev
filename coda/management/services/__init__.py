"""
Management Services Package

This package contains service layer classes for the Management & HR bounded context.
Following the modular monolith architecture plan, these services encapsulate business logic
and provide clean interfaces for views and other components.
"""

from .management_service import ManagementService

__all__ = [
    'ManagementService',
]
