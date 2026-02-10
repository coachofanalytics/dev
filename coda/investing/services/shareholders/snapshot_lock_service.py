"""
Snapshot Lock Service

Handles snapshot locking with dispute window validation and audit logging.
"""

from datetime import date
from django.utils import timezone
from django.core.exceptions import ValidationError
import logging

from investing.models_shareholders import EquitySnapshot, SnapshotAuditLog

logger = logging.getLogger(__name__)


class SnapshotLockService:
    """
    Service for locking and unlocking snapshots with validation.
    """
    
    @staticmethod
    def lock_snapshot(
        snapshot: EquitySnapshot,
        locked_by=None,
        force: bool = False,
        ip_address: str = None
    ) -> EquitySnapshot:
        """
        Lock a snapshot, making it immutable.
        
        Args:
            snapshot: EquitySnapshot instance to lock
            locked_by: User locking the snapshot
            force: Force lock even if dispute window not passed
            ip_address: IP address of the request
            
        Returns:
            Locked EquitySnapshot instance
            
        Raises:
            ValidationError: If snapshot cannot be locked
        """
        # Validation: Already locked
        if snapshot.is_locked:
            raise ValidationError(f"Snapshot {snapshot.version_id} is already locked")
        
        # Validation: Dispute window (unless forced)
        if not force:
            today = date.today()
            if snapshot.auto_lock_date and today < snapshot.auto_lock_date:
                days_remaining = (snapshot.auto_lock_date - today).days
                raise ValidationError(
                    f"Cannot lock snapshot {snapshot.version_id}. "
                    f"Dispute window ends in {days_remaining} days."
                )
        
        # Lock the snapshot
        snapshot.is_locked = True
        snapshot.status = 'FINALIZED'
        snapshot.locked_at = timezone.now()
        snapshot.locked_by = locked_by
        snapshot.save()
        
        # Create audit log
        SnapshotAuditLog.objects.create(
            snapshot=snapshot,
            action='LOCKED',
            performed_by=locked_by,
            details={
                'forced': force,
                'dispute_window_days': snapshot.dispute_window_days,
                'auto_lock_date': snapshot.auto_lock_date.isoformat() if snapshot.auto_lock_date else None,
            },
            ip_address=ip_address
        )
        
        logger.info(
            f"Locked snapshot {snapshot.version_id} "
            f"(force={force}, user={locked_by})"
        )
        
        return snapshot
    
    @staticmethod
    def unlock_snapshot(
        snapshot: EquitySnapshot,
        unlocked_by=None,
        reason: str = None,
        ip_address: str = None
    ) -> EquitySnapshot:
        """
        Unlock a snapshot (admin override only).
        
        Args:
            snapshot: EquitySnapshot instance to unlock
            unlocked_by: User unlocking the snapshot
            reason: Reason for unlocking
            ip_address: IP address of the request
            
        Returns:
            Unlocked EquitySnapshot instance
            
        Raises:
            ValidationError: If snapshot cannot be unlocked
        """
        # Validation: Not locked
        if not snapshot.is_locked:
            raise ValidationError(f"Snapshot {snapshot.version_id} is not locked")
        
        # Unlock the snapshot
        snapshot.is_locked = False
        snapshot.status = 'DRAFT'
        snapshot.locked_at = None
        snapshot.locked_by = None
        snapshot.save()
        
        # Create audit log
        SnapshotAuditLog.objects.create(
            snapshot=snapshot,
            action='UNLOCKED',
            performed_by=unlocked_by,
            details={
                'reason': reason,
            },
            ip_address=ip_address
        )
        
        logger.warning(
            f"Unlocked snapshot {snapshot.version_id} "
            f"(user={unlocked_by}, reason={reason})"
        )
        
        return snapshot
    
    @staticmethod
    def can_lock(snapshot: EquitySnapshot) -> tuple[bool, str]:
        """
        Check if a snapshot can be locked.
        
        Args:
            snapshot: EquitySnapshot instance
            
        Returns:
            Tuple of (can_lock, message)
        """
        if snapshot.is_locked:
            return False, "Snapshot is already locked"
        
        today = date.today()
        if snapshot.auto_lock_date and today < snapshot.auto_lock_date:
            days_remaining = (snapshot.auto_lock_date - today).days
            return False, f"Dispute window active ({days_remaining} days remaining)"
        
        return True, "Snapshot can be locked"
    
    @staticmethod
    def log_snapshot_view(
        snapshot: EquitySnapshot,
        viewed_by=None,
        ip_address: str = None
    ):
        """
        Log a snapshot view for audit purposes.
        
        Args:
            snapshot: EquitySnapshot instance
            viewed_by: User viewing the snapshot
            ip_address: IP address of the request
        """
        SnapshotAuditLog.objects.create(
            snapshot=snapshot,
            action='VIEWED',
            performed_by=viewed_by,
            ip_address=ip_address
        )
    
    @staticmethod
    def log_snapshot_export(
        snapshot: EquitySnapshot,
        exported_by=None,
        export_format: str = 'CSV',
        ip_address: str = None
    ):
        """
        Log a snapshot export for audit purposes.
        
        Args:
            snapshot: EquitySnapshot instance
            exported_by: User exporting the snapshot
            export_format: Export format (CSV, PDF, etc.)
            ip_address: IP address of the request
        """
        SnapshotAuditLog.objects.create(
            snapshot=snapshot,
            action='EXPORTED',
            performed_by=exported_by,
            details={
                'format': export_format,
            },
            ip_address=ip_address
        )
