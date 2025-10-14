from django.apps import AppConfig


class ApplicationConfig(AppConfig):
    name = "application"

    def ready(self):
        import application.signals
