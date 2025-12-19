from django.apps import AppConfig


class MainConfig(AppConfig):
    name = 'main'
    label = 'main'  # Explicitly set label to match app name
    verbose_name = 'Main'
