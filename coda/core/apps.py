"""
Core Services App Configuration
"""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Core Services'
    
    def ready(self):
        """Initialize core services when app is ready."""
        # Import and initialize performance monitoring
        from .performance_monitoring import resource_monitor
        resource_monitor.start_monitoring()


