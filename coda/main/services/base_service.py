"""
Base Service Class for Main Services

This base class provides common functionality and patterns for all main services,
following the modular monolith architecture principles.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import transaction
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


class BaseMainService:
    """
    Base service class for all main services-related services.
    
    Provides common patterns:
    - Error handling and logging
    - Transaction management
    - User validation
    - Response formatting
    - Main services-specific validation
    """
    
    def __init__(self):
        self.logger = logger
    
    def _validate_user(self, user: User) -> bool:
        """Validate that user exists and is active."""
        if not user or not user.is_active:
            raise ValidationError("User must be active to perform this action")
        return True
    
    def _validate_content_data(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate content-related data."""
        required_fields = ['title', 'content']
        for field in required_fields:
            if field not in content_data:
                raise ValidationError(f"Missing required field: {field}")
        
        if len(content_data['title']) < 3:
            raise ValidationError("Content title must be at least 3 characters long")
        
        if len(content_data['content']) < 10:
            raise ValidationError("Content must be at least 10 characters long")
        
        return content_data
    
    def _validate_service_data(self, service_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate service-related data."""
        required_fields = ['name', 'description']
        for field in required_fields:
            if field not in service_data:
                raise ValidationError(f"Missing required field: {field}")
        
        if len(service_data['name']) < 2:
            raise ValidationError("Service name must be at least 2 characters long")
        
        return service_data
    
    def _log_operation(self, operation: str, user: User, details: Dict[str, Any] = None):
        """Log service operations for audit trail."""
        log_data = {
            'operation': operation,
            'user_id': user.id,
            'user_email': user.email,
            'details': details or {}
        }
        self.logger.info(f"Main service operation: {log_data}")
    
    def _handle_error(self, error: Exception, operation: str, user: User = None):
        """Standardized error handling and logging."""
        error_data = {
            'operation': operation,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'user_id': user.id if user else None
        }
        self.logger.error(f"Main service error: {error_data}")
        
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





