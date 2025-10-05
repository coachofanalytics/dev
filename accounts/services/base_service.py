"""
Base Service Class for Accounts Services

This base class provides common functionality and patterns for all accounts services,
following the modular monolith architecture principles.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import transaction
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


class BaseAccountsService:
    """
    Base service class for all accounts services-related services.
    
    Provides common patterns:
    - Error handling and logging
    - Transaction management
    - User validation
    - Response formatting
    - Accounts services-specific validation
    """
    
    def __init__(self):
        self.logger = logger
    
    def _validate_user(self, user: User) -> bool:
        """Validate that user exists and is active."""
        if not user or not user.is_active:
            raise ValidationError("User must be active to perform this action")
        return True
    
    def _validate_email(self, email: str) -> str:
        """Validate email format."""
        if not email or '@' not in email or '.' not in email.split('@')[1]:
            raise ValidationError("Invalid email format")
        return email.lower().strip()
    
    def _validate_password(self, password: str) -> str:
        """Validate password strength."""
        if not password or len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long")
        return password
    
    def _validate_profile_data(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate profile-related data."""
        required_fields = ['first_name', 'last_name']
        for field in required_fields:
            if field not in profile_data:
                raise ValidationError(f"Missing required field: {field}")
        
        if len(profile_data['first_name']) < 2:
            raise ValidationError("First name must be at least 2 characters long")
        
        if len(profile_data['last_name']) < 2:
            raise ValidationError("Last name must be at least 2 characters long")
        
        return profile_data
    
    def _log_operation(self, operation: str, user: User, details: Dict[str, Any] = None):
        """Log service operations for audit trail."""
        log_data = {
            'operation': operation,
            'user_id': user.id,
            'user_email': user.email,
            'details': details or {}
        }
        self.logger.info(f"Accounts service operation: {log_data}")
    
    def _handle_error(self, error: Exception, operation: str, user: User = None):
        """Standardized error handling and logging."""
        error_data = {
            'operation': operation,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'user_id': user.id if user else None
        }
        self.logger.error(f"Accounts service error: {error_data}")
        
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





