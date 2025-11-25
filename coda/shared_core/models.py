"""
Shared Core Models

Re-exports base model mixins from main.models.
All apps should import base models from shared_core.models, not main.models.

This provides:
- TimeStampedModel: Abstract base with created_at, updated_at
- ContractBase: Contract-related fields
- DocumentMixin: Document storage mixin
- StatusMixin: Status tracking mixin
- UserReferenceMixin: User reference mixin
"""
from main.models import (
    TimeStampedModel,
    ContractBase,
    DocumentMixin,
    StatusMixin,
    UserReferenceMixin,
    Company,
)

__all__ = [
    'TimeStampedModel',
    'ContractBase',
    'DocumentMixin',
    'StatusMixin',
    'UserReferenceMixin',
    'Company',
]

