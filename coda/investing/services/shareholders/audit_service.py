"""
Audit Service

Centralized service for creating audit log entries for all member and
contribution operations. Uses existing LedgerAuditLog model.

Migrated to investing app - models imported from shareholders app.
"""

from typing import Dict, Any, Optional
from django.contrib.auth import get_user_model
import json
import logging

# Models imported from original shareholders app (preserves DB ownership)
from investing.models_shareholders import LedgerAuditLog, Member, LedgerEntry

logger = logging.getLogger(__name__)
User = get_user_model()


class AuditService:
    """Service for creating audit trail entries."""
    
    # Action types for audit logging (using LedgerAuditLog's ACTION_CHOICES)
    ACTION_MEMBER_CREATED = 'CREATED'
    ACTION_MEMBER_UPDATED = 'UPDATED'
    ACTION_MEMBER_ARCHIVED = 'UPDATED'  # Use UPDATED for archival
    ACTION_LEDGER_SUBMITTED = 'CREATED'
    ACTION_LEDGER_APPROVED = 'APPROVED'
    ACTION_LEDGER_DISPUTED = 'DISPUTE_RAISED'
    
    @staticmethod
    def log_member_created(member: Member, actor: User, ip_address: Optional[str] = None) -> Optional[LedgerAuditLog]:
        """
        Log member creation event.
        
        Note: This creates a placeholder audit entry tied to the member.
        Since LedgerAuditLog requires a ledger_entry, we skip audit logging
        for member-only operations in Phase 3.
        
        Args:
            member: The Member instance that was created
            actor: The user who performed the action
            ip_address: IP address of the request (optional)
            
        Returns:
            None (member-only operations not logged in LedgerAuditLog in Phase 3)
        """
        # LedgerAuditLog requires a ledger_entry foreign key
        # Member-only operations are not logged in Phase 3
        logger.info(f"Member created: {member.legal_name} by {actor.username}")
        return None
    
    @staticmethod
    def log_member_updated(
        member: Member, 
        actor: User, 
        changed_fields: Dict[str, Any],
        ip_address: Optional[str] = None
    ) -> Optional[LedgerAuditLog]:
        """
        Log member update event.
        
        Args:
            member: The Member instance that was updated
            actor: The user who performed the action
            changed_fields: Dict of field names to new values
            ip_address: IP address of the request (optional)
            
        Returns:
            None (member-only operations not logged in LedgerAuditLog in Phase 3)
        """
        logger.info(f"Member updated: {member.legal_name} by {actor.username}, fields: {list(changed_fields.keys())}")
        return None
    
    @staticmethod
    def log_member_archived(
        member: Member, 
        actor: User,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Optional[LedgerAuditLog]:
        """
        Log member archival (soft delete) event.
        
        Args:
            member: The Member instance that was archived
            actor: The user who performed the action
            reason: Optional reason for archival
            ip_address: IP address of the request (optional)
            
        Returns:
            None (member-only operations not logged in LedgerAuditLog in Phase 3)
        """
        logger.info(f"Member archived: {member.legal_name} by {actor.username}, reason: {reason}")
        return None
    
    @staticmethod
    def log_ledger_submitted(
        entry: LedgerEntry,
        actor: User,
        ip_address: Optional[str] = None
    ) -> LedgerAuditLog:
        """
        Log ledger entry submission event.
        
        Args:
            entry: The LedgerEntry instance that was submitted
            actor: The user who performed the action
            ip_address: IP address of the request (optional)
            
        Returns:
            The created LedgerAuditLog instance
        """
        details = {
            'tx_id': entry.tx_id,
            'contributor_id': entry.contributor.id,
            'contributor_name': entry.contributor.legal_name,
            'tier': entry.tier,
            'value_usd': str(entry.value_usd),
            'asset_class': entry.asset_class,
        }
        
        # Phase 3: Include auto-calculation metadata
        if entry.is_auto_calculated:
            details['auto_calculated'] = True
            details['calculation_note'] = f'Value auto-calculated from DealConfig {entry.tier.lower()}_rate'
        
        return LedgerAuditLog.objects.create(
            ledger_entry=entry,
            action='CREATED',
            performed_by=actor,
            details=details,
            ip_address=ip_address or 'unknown'
        )
    
    @staticmethod
    def log_value_override(
        entry: LedgerEntry,
        actor: User,
        old_value: Any,
        new_value: Any,
        reason: str,
        ip_address: Optional[str] = None
    ) -> LedgerAuditLog:
        """
        Log when an admin manually overrides an auto-calculated value.
        
        Args:
            entry: The LedgerEntry instance being modified
            actor: The admin user performing the override
            old_value: The original auto-calculated value
            new_value: The new manually entered value
            reason: Explanation for the override
            ip_address: IP address of the request (optional)
            
        Returns:
            The created LedgerAuditLog instance
        """
        details = {
            'tx_id': entry.tx_id,
            'override_type': 'value_manual_override',
            'old_calculated_value': str(old_value),
            'new_manual_value': str(new_value),
            'override_reason': reason,
            'tier': entry.tier,
        }
        
        return LedgerAuditLog.objects.create(
            ledger_entry=entry,
            action='UPDATED',
            performed_by=actor,
            old_value=str(old_value),
            new_value=str(new_value),
            details=details,
            ip_address=ip_address or 'unknown'
        )


def get_client_ip(request) -> str:
    """
    Extract client IP address from request.
    
    Args:
        request: Django HttpRequest object
        
    Returns:
        IP address as string
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', 'unknown')
    return ip
