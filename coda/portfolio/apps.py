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
        
        # Register services with ProjectRegistry
        from .services.base_presentation import ProjectRegistry
        
        ProjectRegistry.register("budget-tier", BudgetTierPresentationService)
        ProjectRegistry.register("ai-diaspora", AIDiasporaPresentationService)
        ProjectRegistry.register("smart-loan", SmartLoanPresentationService)