"""
CODA API App Configuration
"""

from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
    verbose_name = 'CODA API'
    
    def ready(self):
        """Initialize API services when app is ready."""
        # Import API services to ensure they're registered
        from . import serializers, viewsets, urls


