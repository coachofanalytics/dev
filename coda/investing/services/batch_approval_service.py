"""
Batch Approval Service
Handles weekly position batches and 24-hour timeout mechanism
"""

import logging
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings

from ..models import (
    PositionBatch,
    OptionsPosition,
    ManagedTradingAccount
)

logger = logging.getLogger(__name__)


class BatchApprovalService:
    """
    Service for creating, managing, and processing position batches
    """
    
    def create_weekly_batch(self, managed_account):
        """
        Create weekly batch of pending positions for client approval
        
        Args:
            managed_account: ManagedTradingAccount instance
        
        Returns:
            PositionBatch instance or None if no pending positions
        """
        # Get all pending positions not yet in a batch
        pending_positions = OptionsPosition.objects.filter(
            managed_account=managed_account,
            status='pending',
            batch__isnull=True,
            requires_client_approval=True
        )
        
        if not pending_positions.exists():
            logger.info(f"No pending positions for {managed_account.account_number}")
            return None
        
        with transaction.atomic():
            # Generate batch number
            batch_number = self.generate_batch_number()
            
            # Calculate totals
            total_positions = pending_positions.count()
            total_capital = sum(p.capital_required for p in pending_positions)
            
            # Create batch
            now = timezone.now()
            batch = PositionBatch.objects.create(
                managed_account=managed_account,
                batch_number=batch_number,
                approval_deadline=now + timedelta(hours=24),
                auto_approve_at=now + timedelta(hours=3),
                total_positions=total_positions,
                total_capital_required=total_capital
            )
            
            # Link positions to batch
            pending_positions.update(batch=batch)
            
            logger.info(
                f"Created batch {batch_number} for {managed_account.account_number}: "
                f"{total_positions} positions, ${total_capital:,.2f} capital"
            )
            
            # Send notification
            from .notification_service import NotificationService
            notification_service = NotificationService()
            notification_service.send_batch_notification(batch)
            
            return batch
    
    def generate_batch_number(self):
        """
        Generate unique batch number: BATCH-YYYY-Wxx
        
        Example: BATCH-2025-W47
        """
        now = timezone.now()
        year = now.year
        week = now.isocalendar()[1]
        
        base_number = f"BATCH-{year}-W{week:02d}"
        
        # Check for duplicates (if multiple batches same week)
        existing = PositionBatch.objects.filter(
            batch_number__startswith=base_number
        ).count()
        
        if existing > 0:
            return f"{base_number}-{existing + 1}"
        
        return base_number
    
    def process_expired_batches(self):
        """
        Process batches that hit their SLA thresholds:
        1. Auto-approve batches that crossed the 3-hour client timeout window.
        2. Expire any remaining pending batches that crossed the full 24-hour deadline.
        """
        now = timezone.now()

        auto_approved_batches = 0
        positions_auto_approved = 0

        from .notification_service import NotificationService
        notification_service = NotificationService()

        auto_ready = PositionBatch.objects.filter(
            status='pending',
            auto_approve_at__isnull=False,
            auto_approve_at__lte=now
        )

        for batch in auto_ready:
            updated = batch.auto_approve_without_entry()
            if updated > 0:
                auto_approved_batches += 1
                positions_auto_approved += updated
                notification_service.send_auto_approved_notification(batch, updated)
                logger.info(
                    "Auto-approved batch %s after client timeout (%s positions)",
                    batch.batch_number,
                    updated,
                )

        expired_batches = PositionBatch.objects.filter(
            status='pending',
            approval_deadline__lt=now
        )
        
        expired_count = 0
        positions_rejected = 0
        
        for batch in expired_batches:
            # Expire the batch
            rejected = batch.expire_batch()
            positions_rejected += rejected
            expired_count += 1
            
            # Send timeout notification
            notification_service.send_timeout_notification(batch)
            
            logger.warning(
                f"Batch {batch.batch_number} expired - {rejected} positions rejected"
            )
        
        logger.info(
            f"Expired {expired_count} batches, rejected {positions_rejected} positions"
        )
        
        return {
            'auto_approved_batches': auto_approved_batches,
            'positions_auto_approved': positions_auto_approved,
            'expired_batches': expired_count,
            'positions_rejected': positions_rejected
        }
    
    def send_batch_reminders(self):
        """
        Send reminder emails for batches approaching deadline (12 hours)
        Called hourly via cron job
        
        Returns:
            int count of reminders sent
        """
        # Find batches between 11-13 hours from deadline (1-hour window)
        now = timezone.now()
        window_start = now + timedelta(hours=11)
        window_end = now + timedelta(hours=13)
        
        batches_needing_reminder = PositionBatch.objects.filter(
            status='pending',
            approval_deadline__gte=window_start,
            approval_deadline__lte=window_end,
            reminder_sent=False
        )
        
        from .notification_service import NotificationService
        notification_service = NotificationService()
        
        reminders_sent = 0
        for batch in batches_needing_reminder:
            notification_service.send_batch_reminder(batch)
            batch.reminder_sent = True
            batch.save()
            reminders_sent += 1
        
        logger.info(f"Sent {reminders_sent} batch reminder notifications")
        
        return reminders_sent
    
    def create_batches_for_all_accounts(self):
        """
        Create weekly batches for all active managed accounts
        Called weekly (e.g., every Friday)
        
        Returns:
            dict with counts of accounts processed and batches created
        """
        active_accounts = ManagedTradingAccount.objects.filter(
            status='active',
            trading_enabled=True
        )
        
        batches_created = 0
        accounts_with_positions = 0
        
        for account in active_accounts:
            batch = self.create_weekly_batch(account)
            if batch:
                batches_created += 1
                accounts_with_positions += 1
        
        logger.info(
            f"Weekly batch creation: {batches_created} batches created "
            f"for {accounts_with_positions} accounts"
        )
        
        return {
            'total_accounts': active_accounts.count(),
            'accounts_with_positions': accounts_with_positions,
            'batches_created': batches_created
        }
    
    def get_batch_summary(self, batch):
        """
        Get comprehensive summary for a batch
        Used in approval interface
        """
        positions = batch.positions.all()
        
        return {
            'batch': batch,
            'positions': positions,
            'total_positions': batch.total_positions,
            'total_capital': batch.total_capital_required,
            'time_remaining': batch.time_remaining,
            'hours_remaining': batch.hours_remaining,
            'is_expired': batch.is_expired,
            'can_approve': batch.is_pending,
        }

