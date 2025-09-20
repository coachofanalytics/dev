"""
Base Service Class for Management Services

This base class provides common functionality and patterns for all management services,
following the modular monolith architecture principles.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import transaction
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


class BaseManagementService:
    """
    Base service class for all management-related services.
    
    Provides common patterns:
    - Error handling and logging
    - Transaction management
    - User validation
    - Response formatting
    - Management-specific validation
    """
    
    def __init__(self):
        self.logger = logger
    
    def _validate_user(self, user: User) -> bool:
        """Validate that user exists and is active."""
        if not user or not user.is_active:
            raise ValidationError("User must be active to perform this action")
        return True
    
    def _validate_manager_permissions(self, user: User) -> bool:
        """Validate that user has manager permissions."""
        if not user.is_staff and not hasattr(user, 'is_manager') and not user.is_manager:
            raise ValidationError("Manager permissions required for this action")
        return True
    
    def _validate_department_access(self, user: User, department_id: int) -> bool:
        """Validate that user has access to the department."""
        # This would typically check if user is assigned to the department
        # For now, we'll just validate the user exists
        self._validate_user(user)
        return True
    
    def _validate_task_data(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate task-related data."""
        required_fields = ['title', 'description', 'assigned_to']
        for field in required_fields:
            if field not in task_data:
                raise ValidationError(f"Missing required field: {field}")
        
        if len(task_data['title']) < 3:
            raise ValidationError("Task title must be at least 3 characters long")
        
        if len(task_data['description']) < 10:
            raise ValidationError("Task description must be at least 10 characters long")
        
        return task_data
    
    def _log_operation(self, operation: str, user: User, details: Dict[str, Any] = None):
        """Log service operations for audit trail."""
        log_data = {
            'operation': operation,
            'user_id': user.id,
            'user_email': user.email,
            'details': details or {}
        }
        self.logger.info(f"Management service operation: {log_data}")
    
    def _handle_error(self, error: Exception, operation: str, user: User = None):
        """Standardized error handling and logging."""
        error_data = {
            'operation': operation,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'user_id': user.id if user else None
        }
        self.logger.error(f"Management service error: {error_data}")
        
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





