"""
Base Service Class for Professional Services

This base class provides common functionality and patterns for all professional services,
following the modular monolith architecture principles.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import transaction
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


class BaseProfessionalService:
    """
    Base service class for all professional services-related services.
    
    Provides common patterns:
    - Error handling and logging
    - Transaction management
    - User validation
    - Response formatting
    - Professional services-specific validation
    """
    
    def __init__(self):
        self.logger = logger
    
    def _validate_user(self, user: User) -> bool:
        """Validate that user exists and is active."""
        if not user or not user.is_active:
            raise ValidationError("User must be active to perform this action")
        return True
    
    def _validate_training_data(self, training_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate training-related data."""
        required_fields = ['title', 'description']
        for field in required_fields:
            if field not in training_data:
                raise ValidationError(f"Missing required field: {field}")
        
        if len(training_data['title']) < 3:
            raise ValidationError("Training title must be at least 3 characters long")
        
        if len(training_data['description']) < 10:
            raise ValidationError("Training description must be at least 10 characters long")
        
        return training_data
    
    def _validate_assessment_data(self, assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate assessment-related data."""
        required_fields = ['question', 'question_type']
        for field in required_fields:
            if field not in assessment_data:
                raise ValidationError(f"Missing required field: {field}")
        
        if len(assessment_data['question']) < 5:
            raise ValidationError("Assessment question must be at least 5 characters long")
        
        return assessment_data
    
    def _log_operation(self, operation: str, user: User, details: Dict[str, Any] = None):
        """Log service operations for audit trail."""
        log_data = {
            'operation': operation,
            'user_id': user.id,
            'user_email': user.email,
            'details': details or {}
        }
        self.logger.info(f"Professional service operation: {log_data}")
    
    def _handle_error(self, error: Exception, operation: str, user: User = None):
        """Standardized error handling and logging."""
        error_data = {
            'operation': operation,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'user_id': user.id if user else None
        }
        self.logger.error(f"Professional service error: {error_data}")
        
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





