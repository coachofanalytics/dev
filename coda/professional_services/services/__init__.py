"""
Professional Services Package

This package contains service layer classes for the Professional Services bounded context.
Following the modular monolith architecture plan, these services encapsulate business logic
and provide clean interfaces for views and other components.

Organized by domain:
- core: Base service classes
- training: Training-related services
- interviews: Interview management services
- job_management: Job role and tracking services
- assessments: Assessment and evaluation services
"""

# Import organized services
from .core.base_service import BaseProfessionalService
from .training.training_service import TrainingService

# Import service modules
from . import core, training, interviews, job_management, assessments

__all__ = [
    'BaseProfessionalService',
    'TrainingService',
    'core', 'training', 'interviews', 'job_management', 'assessments',
]
