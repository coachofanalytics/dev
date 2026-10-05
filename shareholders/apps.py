from django.apps import AppConfig

class ShareholdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shareholders'
    # Do NOT set 'label = "shareholders"' unless you are trying to rename it