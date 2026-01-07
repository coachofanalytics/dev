"""
GDPR app configuration.
"""

from django.apps import AppConfig


class GdprConfig(AppConfig):
    """Configuration for GDPR app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gdpr'
    verbose_name = 'GDPR Compliance'

    def ready(self) -> None:
        """Import signals when app is ready."""
        import gdpr.signals  # noqa: F401
