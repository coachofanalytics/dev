"""
Shared Core App Configuration

This app provides shared models, utilities, and services used across multiple CODA apps.
All apps should import from shared_core instead of directly from main/accounts.
"""
from django.apps import AppConfig


class SharedCoreConfig(AppConfig):
    name = 'shared_core'
    verbose_name = 'Shared Core'
    
    def ready(self):
        """App is ready"""
        pass


