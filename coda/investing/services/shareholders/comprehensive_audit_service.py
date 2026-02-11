"""
Comprehensive Audit Service

System-wide audit logging service for all critical Shareholders actions.
Uses the immutable AuditLog model for complete compliance tracking.
"""

from typing import Dict, Any, Optional
from django.contrib.auth import get_user_model
from django.db import transaction
import logging

from investing.models_shareholders import (
    AuditLog, Deal, Member, LedgerEntry, EquitySnapshot, 
    DealConfig, DealWeights
)

logger = logging.getLogger(__name__)
User = get_user_model()


class ComprehensiveAuditService:
    """
    Service for creating immutable audit trail entries across all Shareholders entities.
    
    All methods are append-only and create AuditLog records that cannot be modified or deleted.
    """
    
    @staticmethod
    def _create_audit_log(
        deal: Deal,
        action_type: str,
        entity_type: str,
        entity_id: str,
        entity_reference: str,
        description: str,
        actor: Optional[User] = None,
        ip_address: Optional[str] = None,
        request_source: str = 'web',
        status: str = 'SUCCESS',
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """
        Internal method to create audit log entries.
        
        Args:
            deal: The Deal this action belongs to
            action_type: Type of action (from AuditLog.ACTION_TYPE_CHOICES)
            entity_type: Type of entity (from AuditLog.ENTITY_TYPE_CHOICES)
            entity_id: Unique identifier of the entity
            entity_reference: Human-readable reference
            description: Human-readable description
            actor: User who performed the action (None for system actions)
            ip_address: IP address of the request
            request_source: Source of the request (web, api, admin, system)
            status: Status of the action (SUCCESS, FAILED, PENDING)
            old_values: Previous values (for updates)
            new_values: New values (for updates)
            details: Additional structured metadata
            
        Returns:
            Created AuditLog instance
        """
        try:
            with transaction.atomic():
                audit_log = AuditLog.objects.create(
                    deal=deal,
                    actor=actor,
                    action_type=action_type,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    entity_reference=entity_reference,
                    description=description,
                    ip_address=ip_address,
                    request_source=request_source,
                    status=status,
                    old_values=old_values,
                    new_values=new_values,
                    details=details
                )
                logger.info(f"Audit log created: {action_type} - {entity_reference} by {actor.username if actor else 'System'}")
                return audit_log
        except Exception as e:
            logger.error(f"Failed to create audit log: {str(e)}")
            raise
    
    # =============================================================================
    # MEMBER ACTIONS
    # =============================================================================
    
    @staticmethod
    def log_member_created(
        member: Member,
        actor: User,
        ip_address: Optional[str] = None,
        request_source: str = 'web'
    ) -> AuditLog:
        """Log member creation event."""
        return ComprehensiveAuditService._create_audit_log(
            deal=member.deal,
            action_type='MEMBER_CREATED',
            entity_type='MEMBER',
            entity_id=str(member.id),
            entity_reference=member.legal_name,
            description=f"Registered new member: {member.legal_name} ({member.get_member_type_display()})",
            actor=actor,
            ip_address=ip_address,
            request_source=request_source,
            new_values={
                'legal_name': member.legal_name,
                'member_type': member.member_type,
                'email': member.email,
                'phone': member.phone,
            }
        )
    
    @staticmethod
    def log_member_updated(
        member: Member,
        actor: User,
        changed_fields: Dict[str, tuple],  # {field: (old_val, new_val)}
        ip_address: Optional[str] = None,
        request_source: str = 'web'
    ) -> AuditLog:
        """Log member update event."""
        old_values = {field: old_val for field, (old_val, _) in changed_fields.items()}
        new_values = {field: new_val for field, (_, new_val) in changed_fields.items()}
        
        return ComprehensiveAuditService._create_audit_log(
            deal=member.deal,
            action_type='MEMBER_UPDATED',
            entity_type='MEMBER',
            entity_id=str(member.id),
            entity_reference=member.legal_name,
            description=f"Updated member: {member.legal_name} (fields: {', '.join(changed_fields.keys())})",
            actor=actor,
            ip_address=ip_address,
            request_source=request_source,
            old_values=old_values,
            new_values=new_values
        )
    
    @staticmethod
    def log_member_archived(
        member: Member,
        actor: User,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        request_source: str = 'web'
    ) -> AuditLog:
        """Log member archival event."""
        return ComprehensiveAuditService._create_audit_log(
            deal=member.deal,
            action_type='MEMBER_ARCHIVED',
            entity_type='MEMBER',
            entity_id=str(member.id),
            entity_reference=member.legal_name,
            description=f"Archived member: {member.legal_name}" + (f" (reason: {reason})" if reason else ""),
            actor=actor,
            ip_address=ip_address,
            request_source=request_source,
            details={'reason': reason} if reason else None
        )
    
    # =============================================================================
    # LEDGER ACTIONS
    # =============================================================================
    
    @staticmethod
    def log_ledger_created(
        entry: LedgerEntry,
        actor: User,
        ip_address: Optional[str] = None,
        request_source: str = 'web'
    ) -> AuditLog:
        """Log ledger entry creation event."""
        return ComprehensiveAuditService._create_audit_log(
            deal=entry.deal,
            action_type='LEDGER_CREATED',
            entity_type='LEDGER_ENTRY',
            entity_id=entry.tx_id,
            entity_reference=entry.tx_id,
            description=f"Created {entry.get_tier_display()} contribution: ${entry.value_usd} for {entry.contributor.legal_name}",
            actor=actor,
            ip_address=ip_address,
            request_source=request_source,
            new_values={
                'contributor': entry.contributor.legal_name,
                'tier': entry.tier,
                'asset_class': entry.asset_class,
                'value_usd': str(entry.value_usd),
                'status': entry.status,
            }
        )
    
    @staticmethod
    def log_ledger_approved(
        entry: LedgerEntry,
        actor: User,
        ip_address: Optional[str] = None,
        request_source: str = 'web'
    ) -> AuditLog:
        """Log ledger entry approval event."""
        return ComprehensiveAuditService._create_audit_log(
            deal=entry.deal,
            action_type='LEDGER_APPROVED',
            entity_type='LEDGER_ENTRY',
            entity_id=entry.tx_id,
            entity_reference=entry.tx_id,
            description=f"Approved {entry.get_tier_display()} contribution of ${entry.value_usd}",
            actor=actor,
            ip_address=ip_address,
            request_source=request_source,
            old_values={'status': 'PENDING'},
            new_values={'status': 'APPROVED'}
        )
    
    @staticmethod
    def log_ledger_disputed(
        entry: LedgerEntry,
        actor: User,
        dispute_reason: str,
        ip_address: Optional[str] = None,
        request_source: str = 'web'
    ) -> AuditLog:
        """Log ledger entry dispute event."""
        return ComprehensiveAuditService._create_audit_log(
            deal=entry.deal,
            action_type='LEDGER_DISPUTED',
            entity_type='LEDGER_ENTRY',
            entity_id=entry.tx_id,
            entity_reference=entry.tx_id,
            description=f"Raised dispute on {entry.tx_id}: {dispute_reason}",
            actor=actor,
            ip_address=ip_address,
            request_source=request_source,
            details={'dispute_reason': dispute_reason}
        )
    
    # =============================================================================
    # SNAPSHOT ACTIONS
    # =============================================================================
    
    @staticmethod
    def log_snapshot_created(
        snapshot: EquitySnapshot,
        actor: User,
        ip_address: Optional[str] = None,
        request_source: str = 'web'
    ) -> AuditLog:
        """Log snapshot creation event."""
        return ComprehensiveAuditService._create_audit_log(
            deal=snapshot.deal,
            action_type='SNAPSHOT_CREATED',
            entity_type='SNAPSHOT',
            entity_id=str(snapshot.id),
            entity_reference=snapshot.version_id,
            description=f"Created snapshot {snapshot.version_id} with {snapshot.member_snapshots.count()} members",
            actor=actor,
            ip_address=ip_address,
            request_source=request_source,
            new_values={
                'version_id': snapshot.version_id,
                'is_locked': snapshot.is_locked,
                'created_by': actor.username,
            }
        )
    
    @staticmethod
    def log_snapshot_locked(
        snapshot: EquitySnapshot,
        actor: User,
        ip_address: Optional[str] = None,
        request_source: str = 'web'
    ) -> AuditLog:
        """Log snapshot lock event."""
        return ComprehensiveAuditService._create_audit_log(
            deal=snapshot.deal,
            action_type='SNAPSHOT_LOCKED',
            entity_type='SNAPSHOT',
            entity_id=str(snapshot.id),
            entity_reference=snapshot.version_id,
            description=f"Locked snapshot {snapshot.version_id} (now immutable)",
            actor=actor,
            ip_address=ip_address,
            request_source=request_source,
            old_values={'is_locked': False},
            new_values={'is_locked': True}
        )
    
    # =============================================================================
    # DEAL CONFIG ACTIONS
    # =============================================================================
    
    @staticmethod
    def log_config_updated(
        config: DealConfig,
        actor: User,
        changed_fields: Dict[str, tuple],
        ip_address: Optional[str] = None,
        request_source: str = 'web'
    ) -> AuditLog:
        """Log deal config update event."""
        old_values = {field: str(old_val) for field, (old_val, _) in changed_fields.items()}
        new_values = {field: str(new_val) for field, (_, new_val) in changed_fields.items()}
        
        # Create human-readable description
        changes = []
        for field, (old_val, new_val) in changed_fields.items():
            if field == 'fx_peg_rate':
                changes.append(f"FX rate from {old_val} to {new_val}")
            elif field == 'dispute_window_days':
                changes.append(f"dispute window from {old_val} to {new_val} days")
            else:
                changes.append(f"{field} from {old_val} to {new_val}")
        
        return ComprehensiveAuditService._create_audit_log(
            deal=config.deal,
            action_type='CONFIG_UPDATED',
            entity_type='DEAL_CONFIG',
            entity_id=str(config.id),
            entity_reference=config.deal.name,
            description=f"Updated deal configuration: {', '.join(changes)}",
            actor=actor,
            ip_address=ip_address,
            request_source=request_source,
            old_values=old_values,
            new_values=new_values
        )
    
    @staticmethod
    def log_weights_updated(
        weights: DealWeights,
        actor: User,
        ip_address: Optional[str] = None,
        request_source: str = 'web'
    ) -> AuditLog:
        """Log contribution weights update event."""
        return ComprehensiveAuditService._create_audit_log(
            deal=weights.deal,
            action_type='WEIGHTS_UPDATED',
            entity_type='DEAL_WEIGHTS',
            entity_id=str(weights.id),
            entity_reference=weights.deal.name,
            description=f"Updated contribution weights: Cash {weights.cash_weight}%, InKind {weights.in_kind_weight}%, Time {weights.time_weight}%, Work {weights.work_weight}%",
            actor=actor,
            ip_address=ip_address,
            request_source=request_source,
            new_values={
                'cash_weight': str(weights.cash_weight),
                'in_kind_weight': str(weights.in_kind_weight),
                'time_weight': str(weights.time_weight),
                'work_weight': str(weights.work_weight),
            }
        )


def get_client_ip(request) -> str:
    """
    Extract client IP address from Django request.
    
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
