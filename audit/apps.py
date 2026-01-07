"""
Audit app configuration.
"""

from django.apps import AppConfig


class AuditConfig(AppConfig):
    """Configuration for the audit app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "audit"
    verbose_name = "Audit & Compliance"

    def ready(self) -> None:
        """Import signals when the app is ready."""
        import audit.signals  # noqa: F401
