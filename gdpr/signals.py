"""
GDPR signal handlers for automatic audit logging.

Automatically logs GDPR-related events to audit system.
"""

import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from gdpr.models import ConsentRecord, DataExportRequest, DataDeletionRequest

logger = logging.getLogger(__name__)


@receiver(post_save, sender=ConsentRecord)
def log_consent_change(sender, instance, created, **kwargs):
    """Log consent record changes to audit system."""
    try:
        from audit.services.audit_service import AuditService

        if created:
            event_type = "consent_given"
            description = f"Consent given for {instance.get_consent_type_display()}"
        else:
            if instance.is_given:
                event_type = "consent_given"
                description = f"Consent re-given for {instance.get_consent_type_display()}"
            else:
                event_type = "consent_withdrawn"
                description = f"Consent withdrawn for {instance.get_consent_type_display()}"

        AuditService.log_event(
            event_type=event_type,
            description=description,
            user=instance.user,
            severity="info",
            metadata={
                "consent_type": instance.consent_type,
                "version": instance.version,
                "is_given": instance.is_given,
            }
        )

    except Exception as e:
        logger.error(f"Error logging consent change: {e}")


@receiver(post_save, sender=DataExportRequest)
def log_export_request(sender, instance, created, **kwargs):
    """Log data export requests to audit system."""
    try:
        from audit.services.audit_service import AuditService

        if created:
            event_type = "data_exported"
            description = f"Data export requested (format: {instance.export_format})"
            severity = "info"
        elif instance.status == "completed":
            event_type = "data_exported"
            description = f"Data export completed (format: {instance.export_format})"
            severity = "info"
        elif instance.status == "failed":
            event_type = "data_exported"
            description = f"Data export failed: {instance.error_message}"
            severity = "warning"
        else:
            return  # Don't log intermediate status changes

        AuditService.log_event(
            event_type=event_type,
            description=description,
            user=instance.user,
            severity=severity,
            metadata={
                "export_format": instance.export_format,
                "status": instance.status,
                "file_size": instance.file_size,
            }
        )

    except Exception as e:
        logger.error(f"Error logging export request: {e}")


@receiver(post_save, sender=DataDeletionRequest)
def log_deletion_request(sender, instance, created, **kwargs):
    """Log data deletion requests to audit system."""
    try:
        from audit.services.audit_service import AuditService

        if created:
            event_type = "data_deleted"
            description = "Account deletion requested (30-day grace period started)"
            severity = "warning"
        elif instance.status == "completed":
            event_type = "data_deleted"
            description = "Account and data permanently deleted"
            severity = "warning"
        elif instance.status == "cancelled":
            event_type = "data_deleted"
            description = "Account deletion request cancelled"
            severity = "info"
        elif instance.status == "failed":
            event_type = "data_deleted"
            description = f"Account deletion failed: {instance.error_message}"
            severity = "error"
        else:
            return  # Don't log intermediate status changes

        # Try to get user, but it may be None after deletion
        user = instance.user if hasattr(instance, 'user') and instance.user else None

        AuditService.log_event(
            event_type=event_type,
            description=description,
            user=user,
            username=instance.username,  # Preserved even after user deletion
            severity=severity,
            metadata={
                "status": instance.status,
                "grace_period_end": instance.grace_period_end.isoformat() if instance.grace_period_end else None,
                "reason": instance.reason,
            }
        )

    except Exception as e:
        logger.error(f"Error logging deletion request: {e}")
