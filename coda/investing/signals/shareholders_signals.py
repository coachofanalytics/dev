"""
Shareholders Management System - Django Signals

Phase 3: Auto-calculation and audit trail signals.

Handles:
- DealConfig rate change tracking and audit logging
- Future: Auto-recalculation when rates change (if enabled)
"""

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from decimal import Decimal
import logging

from investing.models import DealConfig, LedgerEntry
from investing.services.shareholders.audit_service import AuditService

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=DealConfig)
def track_dealconfig_rate_changes(sender, instance, **kwargs):
    """
    Track when time_rate or work_rate changes in DealConfig.
    
    Logs rate changes to audit trail for compliance and transparency.
    Future enhancement: Could trigger recalculation of existing contributions.
    """
    # Skip if this is a new DealConfig (no previous state to compare)
    if not instance.pk:
        return
    
    try:
        # Get the old instance from database
        old_instance = DealConfig.objects.get(pk=instance.pk)
        
        # Check if time_rate changed
        if old_instance.time_rate != instance.time_rate:
            logger.info(
                f"DealConfig {instance.deal.name}: time_rate changed from "
                f"${old_instance.time_rate} to ${instance.time_rate}"
            )
            # Future: Add audit log entry for rate change
            # AuditService.log_rate_change(
            #     deal=instance.deal,
            #     rate_type='time_rate',
            #     old_value=old_instance.time_rate,
            #     new_value=instance.time_rate,
            #     actor=None  # Would need to pass from request
            # )
        
        # Check if work_rate changed
        if old_instance.work_rate != instance.work_rate:
            logger.info(
                f"DealConfig {instance.deal.name}: work_rate changed from "
                f"${old_instance.work_rate} to ${instance.work_rate}"
            )
            # Future: Add audit log entry for rate change
            
    except DealConfig.DoesNotExist:
        # Should not happen, but handle gracefully
        logger.warning(f"DealConfig {instance.pk} not found in database during pre_save")
        pass


@receiver(post_save, sender=LedgerEntry)
def log_auto_calculated_contribution(sender, instance, created, **kwargs):
    """
    Log when a contribution with auto-calculated value is created.
    
    This provides additional audit trail for transparency.
    """
    if created and instance.is_auto_calculated:
        logger.info(
            f"Auto-calculated contribution created: {instance.tx_id} | "
            f"{instance.contributor.legal_name} | {instance.tier} | "
            f"${instance.value_usd} ({instance.internal_units_value} {instance.internal_units_label})"
        )
