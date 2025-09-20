"""
Professional Services Package

This package contains service layer classes for the Professional Services bounded context.
Following the modular monolith architecture plan, these services encapsulate business logic
and provide clean interfaces for views and other components.
"""

from .training_service import TrainingService

__all__ = [
    'TrainingService',
]
