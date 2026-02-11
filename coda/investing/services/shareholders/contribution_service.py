"""
Contribution Submission Service

Handles the creation of LedgerEntry records with optional proof upload.
Enforces business rules and immutability constraints.

Migrated to investing app - models imported from shareholders app.
"""

from typing import Optional, Dict, Any
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from decimal import Decimal
import uuid
import logging

# Models now owned by investing app
from investing.models_shareholders import (
    LedgerEntry, LedgerEvidence, Member, Deal
)
from .audit_service import AuditService

logger = logging.getLogger(__name__)
User = get_user_model()


class ContributionSubmissionService:
    """Service for submitting new contributions."""
    
    def __init__(self, deal: Deal):
        """Initialize service for a specific deal."""
        self.deal = deal
    
    @transaction.atomic
    def submit_contribution(
        self,
        contributor: Member,
        tier: str,
        asset_class: str,
        date,
        internal_units_value: Decimal,
        internal_units_label: str,
        value_usd: Decimal,
        currency: str,
        exchange_rate: Decimal,
        actor: User,
        notes: Optional[str] = None,
        proof_document: Optional[UploadedFile] = None,
        ip_address: Optional[str] = None,
        tier_metadata: Optional[dict] = None
    ) -> LedgerEntry:
        """
        Submit a new contribution (creates LedgerEntry in SUBMITTED status).
        
        Args:
            contributor: Member making the contribution
            tier: Contribution tier (CASH, IN_KIND, TIME, WORK)
            asset_class: Description of the contribution
            date: Date of contribution
            internal_units_value: Quantity in internal units
            internal_units_label: Unit label (USD, hrs, pts, etc.)
            value_usd: Value in USD
            currency: Currency code
            exchange_rate: Exchange rate used
            actor: User submitting the contribution
            notes: Optional notes
            proof_document: Optional uploaded file as evidence
            ip_address: IP address of submitter
            tier_metadata: Tier-specific structured data (valuation_method,
                           role_multiplier, deliverable_title, impact_tier)
            
        Returns:
            The created LedgerEntry instance
        """
        # Generate transaction ID
        tx_id = self._generate_tx_id(tier)
        
        # Create ledger entry
        entry = LedgerEntry.objects.create(
            deal=self.deal,
            contributor=contributor,
            tx_id=tx_id,
            tier=tier,
            asset_class=asset_class,
            date=date,
            internal_units_value=internal_units_value,
            internal_units_label=internal_units_label,
            value_usd=value_usd,
            currency=currency,
            exchange_rate=exchange_rate,
            status='SUBMITTED',  # Always start as SUBMITTED
            notes=notes or '',
            tier_metadata=tier_metadata or {},
        )
        
        # Upload proof document if provided
        if proof_document:
            self._attach_proof(entry, proof_document, actor)
        
        # Create audit log
        AuditService.log_ledger_submitted(
            entry=entry,
            actor=actor,
            ip_address=ip_address
        )
        
        logger.info(
            f"Contribution submitted: {tx_id} by {contributor.legal_name} "
            f"({tier}, ${value_usd})"
        )
        
        return entry
    
    def _generate_tx_id(self, tier: str) -> str:
        """
        Generate a unique transaction ID.
        
        Format: TIER-PREFIX-TIMESTAMP-RANDOM
        Example: CSH-20260203-A3B5
        """
        prefix_map = {
            'CASH': 'CSH',
            'IN_KIND': 'IKD',
            'TIME': 'TIM',
            'WORK': 'WRK',
        }
        prefix = prefix_map.get(tier, 'UNK')
        
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d')
        random_suffix = uuid.uuid4().hex[:4].upper()
        
        tx_id = f"{prefix}-{timestamp}-{random_suffix}"
        
        # Ensure uniqueness
        while LedgerEntry.objects.filter(tx_id=tx_id).exists():
            random_suffix = uuid.uuid4().hex[:4].upper()
            tx_id = f"{prefix}-{timestamp}-{random_suffix}"
        
        return tx_id
    
    def _attach_proof(
        self,
        entry: LedgerEntry,
        proof_file: UploadedFile,
        actor: User
    ) -> LedgerEvidence:
        """
        Attach proof document to a ledger entry.
        
        Args:
            entry: The LedgerEntry to attach proof to
            proof_file: Uploaded file
            actor: User uploading the file
            
        Returns:
            The created LedgerEvidence instance
        """
        evidence = LedgerEvidence.objects.create(
            ledger_entry=entry,
            file=proof_file,
            uploaded_by=actor,
            description=f"Proof for {entry.tx_id}"
        )
        
        logger.info(f"Proof document attached to {entry.tx_id}: {proof_file.name}")
        
        return evidence
    
    @staticmethod
    def can_edit_entry(entry: LedgerEntry) -> bool:
        """
        Check if a ledger entry can be edited.
        
        Phase 3 policy: Entries cannot be edited after submission.
        Returns False always (immutability enforced).
        
        Future phases may allow edits for REJECTED entries only.
        """
        return False
    
    @staticmethod
    def can_delete_entry(entry: LedgerEntry) -> bool:
        """
        Check if a ledger entry can be deleted.
        
        Phase 3 policy: Entries cannot be deleted after submission.
        Returns False always.
        """
        return False
