"""
Position History Auto-Collection Signals
Automatically track closed positions for ML training

Purpose:
- Auto-populate OptionsPositionHistory when position closes
- No manual intervention needed
- Build ML training dataset automatically

Usage:
    # Signals are auto-loaded in apps.py
    # Just close a position and history is created automatically

Architecture:
- post_save signal on OptionsPosition
- Triggers PositionHistoryCollector
- Only fires when status changes to 'closed'

Author: CODA Development Team
Created: November 2, 2025
Part of: AI Position Scoring System (Week 1)
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender='investing.OptionsPosition')
def auto_collect_position_history(sender, instance, created, **kwargs):
    """
    Automatically collect history when position closes
    
    Trigger:
    - Position status changes to 'closed'
    - No existing history record
    
    Actions:
    - Call PositionHistoryCollector
    - Create OptionsPositionHistory
    - Log metrics for ML
    """
    from investing.services.position_history_collector import PositionHistoryCollector
    
    # Only process closed positions
    if instance.status != 'closed':
        return
    
    # Skip if history already exists (avoid duplicates)
    if hasattr(instance, 'outcome_history'):
        return
    
    # Skip if created just now (wait for exit data to be set)
    if created:
        return
    
    # Collect history asynchronously (don't block position save)
    try:
        collector = PositionHistoryCollector()
        history = collector.collect_from_position(instance)
        logger.info(f"✅ Auto-collected history for position {instance.id}: "
                   f"{'WIN' if history.was_profitable else 'LOSS'} "
                   f"({history.actual_return_percentage}% ROI)")
    except Exception as e:
        # Log error but don't raise (don't block position updates)
        logger.error(f"❌ Error auto-collecting history for position {instance.id}: {e}", exc_info=True)


# Import in apps.py ready() method to ensure signals are loaded
def load_position_history_signals():
    """Called from apps.py to load signals"""
    logger.info("📊 Position history auto-collection signals loaded")

