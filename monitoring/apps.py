"""
Monitoring app configuration.
"""

from django.apps import AppConfig


class MonitoringConfig(AppConfig):
    """Configuration for monitoring app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'monitoring'
    verbose_name = 'Security Monitoring'
