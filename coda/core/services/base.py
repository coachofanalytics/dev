# uat/core/services/base.py
import logging
from django.db import transaction
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

class BaseService:
    """Base service class with common functionality"""
    
    def __init__(self):
        self.logger = logger
    
    def log_operation(self, operation, details=None):
        """Log service operations"""
        message = f"Service operation: {operation}"
        if details:
            message += f" - {details}"
        self.logger.info(message)
    
    def handle_error(self, error, context=None):
        """Handle and log errors consistently"""
        error_message = f"Service error: {str(error)}"
        if context:
            error_message += f" - Context: {context}"
        self.logger.error(error_message)
        return {
            'status': 'error',
            'error': str(error),
            'context': context
        }

class ModelService(BaseService):
    """Service for model operations with transaction support"""
    
    def create_with_transaction(self, model_class, data, **kwargs):
        """Create model instance with transaction support"""
        try:
            with transaction.atomic():
                instance = model_class.objects.create(**data, **kwargs)
                self.log_operation('create', f"Created {model_class.__name__}: {instance.id}")
                return {
                    'status': 'success',
                    'instance': instance,
                    'message': f'{model_class.__name__} created successfully'
                }
        except Exception as e:
            return self.handle_error(e, f"Creating {model_class.__name__}")
    
    def update_with_transaction(self, instance, data, **kwargs):
        """Update model instance with transaction support"""
        try:
            with transaction.atomic():
                for field, value in data.items():
                    setattr(instance, field, value)
                instance.save(**kwargs)
                self.log_operation('update', f"Updated {instance.__class__.__name__}: {instance.id}")
                return {
                    'status': 'success',
                    'instance': instance,
                    'message': f'{instance.__class__.__name__} updated successfully'
                }
        except Exception as e:
            return self.handle_error(e, f"Updating {instance.__class__.__name__}")
    
    def delete_with_transaction(self, instance):
        """Delete model instance with transaction support"""
        try:
            with transaction.atomic():
                instance_id = instance.id
                instance_class = instance.__class__.__name__
                instance.delete()
                self.log_operation('delete', f"Deleted {instance_class}: {instance_id}")
                return {
                    'status': 'success',
                    'message': f'{instance_class} deleted successfully'
                }
        except Exception as e:
            return self.handle_error(e, f"Deleting {instance.__class__.__name__}")
    
    def get_or_create_with_transaction(self, model_class, defaults=None, **kwargs):
        """Get or create model instance with transaction support"""
        try:
            with transaction.atomic():
                instance, created = model_class.objects.get_or_create(defaults=defaults, **kwargs)
                operation = 'created' if created else 'retrieved'
                self.log_operation(operation, f"{model_class.__name__}: {instance.id}")
                return {
                    'status': 'success',
                    'instance': instance,
                    'created': created,
                    'message': f'{model_class.__name__} {operation} successfully'
                }
        except Exception as e:
            return self.handle_error(e, f"Getting/creating {model_class.__name__}")