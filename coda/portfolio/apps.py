from django.apps import AppConfig


class PortfolioConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'portfolio'
    
    def ready(self):
        """Import services to register them on app startup"""
        # Import all presentation services to trigger registration
        from .services import (
            BudgetTierPresentationService,
            AIDiasporaPresentationService,
            SmartLoanPresentationService,
        )