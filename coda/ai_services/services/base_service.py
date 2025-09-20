"""
Base Service Class for AI Services

This base class provides common functionality and patterns for all AI services,
following the modular monolith architecture principles.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import transaction
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


class BaseAIService:
    """
    Base service class for all AI-related services.
    
    Provides common patterns:
    - Error handling and logging
    - Transaction management
    - User validation
    - Response formatting
    - AI-specific validation
    """
    
    def __init__(self):
        self.logger = logger
    
    def _validate_user(self, user: User) -> bool:
        """Validate that user exists and is active."""
        if not user or not user.is_active:
            raise ValidationError("User must be active to perform this action")
        return True
    
    def _validate_data_format(self, data: Any, expected_format: str) -> bool:
        """Validate data format for AI processing."""
        if expected_format == 'csv' and not hasattr(data, 'read'):
            raise ValidationError("CSV data must be a file-like object")
        elif expected_format == 'json' and not isinstance(data, (dict, list)):
            raise ValidationError("JSON data must be a dictionary or list")
        return True
    
    def _log_operation(self, operation: str, user: User, details: Dict[str, Any] = None):
        """Log service operations for audit trail."""
        log_data = {
            'operation': operation,
            'user_id': user.id,
            'user_email': user.email,
            'details': details or {}
        }
        self.logger.info(f"AI service operation: {log_data}")
    
    def _handle_error(self, error: Exception, operation: str, user: User = None):
        """Standardized error handling and logging."""
        error_data = {
            'operation': operation,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'user_id': user.id if user else None
        }
        self.logger.error(f"AI service error: {error_data}")
        
        # Re-raise with additional context
        raise ValidationError(f"Operation '{operation}' failed: {str(error)}")
    
    @transaction.atomic
    def _execute_with_transaction(self, operation_func, *args, **kwargs):
        """Execute operation within a database transaction."""
        try:
            return operation_func(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"Transaction failed: {str(e)}")
            raise
    
    def create_success_response(self, data: Any, message: str = "Operation successful") -> Dict[str, Any]:
        """Create standardized success response."""
        return {
            'success': True,
            'message': message,
            'data': data
        }
    
    def create_error_response(self, error: str, details: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create standardized error response."""
        return {
            'success': False,
            'error': error,
            'details': details or {}
        }