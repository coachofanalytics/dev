from django.apps import AppConfig



class FinanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'finance'

    def ready(self):
        import finance.signals  # Ensure transaction signals are imported
        import finance.signals_food  # Ensure food system signals are imported
        import finance.admin_food  # Ensure food admin is registered
