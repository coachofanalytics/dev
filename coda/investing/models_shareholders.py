"""
Shareholders Management System - Core Models

MIGRATED FROM shareholders app to investing app.
Database tables remain unchanged (shareholders_* prefix preserved).

=============================================================================
CRITICAL: DO NOT MODIFY db_table SETTINGS
=============================================================================
These models explicitly specify db_table to match existing database tables.
Changing db_table would cause Django to create new tables and lose data.
=============================================================================
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.text import slugify
from shared_core.models import TimeStampedModel
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


# =============================================================================
# DEAL MODELS
# =============================================================================

class Deal(TimeStampedModel):
    """
    Represents a single equity deal/project (e.g., Project Phoenix Pilot).
    
    A Deal is the top-level container for members, ledger entries, and configuration.
    Phase 1: Single active deal supported; multi-deal scaling in future phases.
    """
    
    name = models.CharField(
        max_length=255,
        help_text="Deal name (e.g., 'Project Phoenix Pilot')"
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        blank=True,
        help_text="URL-safe identifier (auto-generated from name)"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Optional deal description"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this deal is currently active"
    )
    
    class Meta:
        db_table = 'shareholders_deal'
        ordering = ['-created_at']
        verbose_name = 'Deal'
        verbose_name_plural = 'Deals'
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Auto-generate slug from name if not provided"""
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Deal.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class DealConfig(models.Model):
    """
    Per-deal configuration for currency, FX rates, and system settings.
    
    Comprehensive governance settings for contribution approvals, dispute windows,
    snapshot scheduling, and valuation policies.
    """
    
    FX_MODE_CHOICES = [
        ('PEGGED', 'Pegged Rate'),
        ('MARKET', 'Market Rate'),
    ]
    
    SNAPSHOT_FREQUENCY_CHOICES = [
        ('MONTHLY', 'Monthly'),
        ('QUARTERLY', 'Quarterly'),
        ('MANUAL', 'Manual Only'),
    ]
    
    INKIND_MODE_CHOICES = [
        ('MANUAL', 'Manual Entry'),
        ('RATE', 'Rate-Based'),
    ]
    
    deal = models.OneToOneField(
        Deal,
        on_delete=models.CASCADE,
        related_name='config',
        help_text="Associated deal"
    )
    
    # FX & Currency Policy
    base_currency = models.CharField(
        max_length=3,
        default='USD',
        help_text="Base currency code (ISO 4217)"
    )
    fx_mode = models.CharField(
        max_length=10,
        choices=FX_MODE_CHOICES,
        default='PEGGED',
        help_text="FX rate mode: pegged or market"
    )
    fx_peg_rate = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=127.0000,
        validators=[MinValueValidator(0)],
        help_text="Pegged FX rate (e.g., 127 KES/USD); used when fx_mode=PEGGED"
    )
    
    # Valuation Rules
    time_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=50.00,
        validators=[MinValueValidator(0)],
        help_text="USD value per hour of time contribution"
    )
    work_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=100.00,
        validators=[MinValueValidator(0)],
        help_text="USD value per work unit/point"
    )
    inkind_valuation_mode = models.CharField(
        max_length=10,
        choices=INKIND_MODE_CHOICES,
        default='MANUAL',
        help_text="How to value in-kind contributions"
    )
    
    # Approval & Dispute Policy
    dispute_window_days = models.IntegerField(
        default=7,
        validators=[MinValueValidator(0)],
        help_text="Days allowed for disputes before auto-approval"
    )
    require_approval_cash = models.BooleanField(
        default=True,
        help_text="Require admin approval for cash contributions"
    )
    require_approval_inkind = models.BooleanField(
        default=True,
        help_text="Require admin approval for in-kind contributions"
    )
    require_approval_time = models.BooleanField(
        default=False,
        help_text="Require admin approval for time contributions"
    )
    require_approval_work = models.BooleanField(
        default=False,
        help_text="Require admin approval for work contributions"
    )
    
    # Snapshot Policy
    snapshot_frequency = models.CharField(
        max_length=10,
        choices=SNAPSHOT_FREQUENCY_CHOICES,
        default='MONTHLY',
        help_text="How often to auto-generate snapshots"
    )
    snapshot_day = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(28)],
        help_text="Day of month for scheduled snapshots (1-28)"
    )
    auto_lock_snapshots = models.BooleanField(
        default=True,
        help_text="Automatically lock snapshots after dispute window"
    )
    next_snapshot_date = models.DateField(
        blank=True,
        null=True,
        help_text="Next scheduled snapshot date"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'shareholders_deal_config'
        verbose_name = 'Deal Configuration'
        verbose_name_plural = 'Deal Configurations'
    
    def __str__(self):
        return f"Config for {self.deal.name}"


class DealWeights(models.Model):
    """
    Per-deal contribution tier weights (Cash/In-Kind/Time/Work).
    
    Phase 1: Stores one active weight set per deal.
    Future phases: Versioning for historical weight changes.
    
    Validation: Weights must sum to 100%.
    """
    
    deal = models.ForeignKey(
        Deal,
        on_delete=models.CASCADE,
        related_name='weights',
        help_text="Associated deal"
    )
    cash_weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=55.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Cash tier weight percentage (default 55%)"
    )
    in_kind_weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=20.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="In-Kind tier weight percentage (default 20%)"
    )
    time_weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Time tier weight percentage (default 10%)"
    )
    work_weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=15.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Work tier weight percentage (default 15%)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Only one active weight set per deal"
    )
    effective_date = models.DateField(
        default=timezone.now,
        help_text="Date these weights became effective"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'shareholders_deal_weights'
        ordering = ['-effective_date']
        verbose_name = 'Deal Weights'
        verbose_name_plural = 'Deal Weights'
        indexes = [
            models.Index(fields=['deal', 'is_active']),
        ]
    
    def __str__(self):
        return f"Weights for {self.deal.name} ({'Active' if self.is_active else 'Inactive'})"
    
    def clean(self):
        """Validate that weights sum to 100%"""
        total = self.cash_weight + self.in_kind_weight + self.time_weight + self.work_weight
        if abs(total - 100) > 0.01:  # Allow for floating point precision
            raise ValidationError(
                f"Weights must sum to 100%. Current sum: {total}%"
            )
    
    def save(self, *args, **kwargs):
        """Ensure only one active weight set per deal"""
        self.full_clean()
        if self.is_active:
            # Deactivate all other weight sets for this deal
            DealWeights.objects.filter(deal=self.deal, is_active=True).update(is_active=False)
        super().save(*args, **kwargs)


# =============================================================================
# MEMBER MODELS
# =============================================================================

class Member(TimeStampedModel):
    """
    Represents a person or entity participating in a deal.
    
    Phase 1: Basic profile information and contact details.
    Equity percentage NOT stored here (computed in Phase 4).
    
    Soft deletion via is_archived flag.
    """
    
    MEMBER_TYPE_CHOICES = [
        ('PERSON', 'Individual Person'),
        ('ENTITY', 'Entity / Joint Venture'),
    ]
    
    deal = models.ForeignKey(
        Deal,
        on_delete=models.CASCADE,
        related_name='members',
        help_text="Associated deal"
    )
    member_type = models.CharField(
        max_length=10,
        choices=MEMBER_TYPE_CHOICES,
        default='PERSON',
        help_text="Member type: individual or entity"
    )
    legal_name = models.CharField(
        max_length=255,
        help_text="Legal name as per ID/certificate"
    )
    role_title = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Role in the deal (e.g., Founder, Investor, Lead Developer)"
    )
    email = models.EmailField(
        help_text="Primary email address"
    )
    phone = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Primary phone number"
    )
    verified = models.BooleanField(
        default=False,
        help_text="Identity verification status (KYC/KYB complete)"
    )
    bio = models.TextField(
        blank=True,
        null=True,
        help_text="Optional biography or description"
    )
    is_archived = models.BooleanField(
        default=False,
        help_text="Soft deletion flag; archived members excluded from active views"
    )
    joined_date = models.DateField(
        auto_now_add=True,
        help_text="Date member was registered"
    )
    identity_document = models.FileField(
        upload_to='shareholders/identity_documents/%Y/%m/',
        blank=True,
        null=True,
        help_text="Uploaded identity document (ID, passport, or business certificate)"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_members',
        help_text="User who registered this member (ownership for edit authorization)"
    )
    
    class Meta:
        db_table = 'shareholders_member'
        ordering = ['legal_name']
        verbose_name = 'Member'
        verbose_name_plural = 'Members'
        indexes = [
            models.Index(fields=['deal', 'is_archived']),
            models.Index(fields=['email']),
            models.Index(fields=['created_by']),
        ]
    
    def __str__(self):
        return f"{self.legal_name} ({self.get_member_type_display()})"


# =============================================================================
# LEDGER MODELS
# =============================================================================

class LedgerEntry(TimeStampedModel):
    """
    Unified ledger table for all contribution tiers (Cash/In-Kind/Time/Work).
    
    Phase 1: Records contributions with status tracking.
    Approval workflow NOT enforced (Phase 2).
    Dispute handling NOT implemented (Phase 5).
    
    tx_id: Human-readable transaction ID (auto-generated, unique).
    """
    
    TIER_CHOICES = [
        ('CASH', 'Cash Contribution'),
        ('IN_KIND', 'In-Kind Asset'),
        ('TIME', 'Time Logged'),
        ('WORK', 'Work Deliverable'),
    ]
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted for Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('IN_DISPUTE', 'In Dispute'),
    ]
    
    deal = models.ForeignKey(
        Deal,
        on_delete=models.CASCADE,
        related_name='ledger_entries',
        help_text="Associated deal"
    )
    tx_id = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        help_text="Unique transaction ID (auto-generated, e.g., TX-9012)"
    )
    contributor = models.ForeignKey(
        Member,
        on_delete=models.PROTECT,
        related_name='contributions',
        help_text="Member making the contribution"
    )
    tier = models.CharField(
        max_length=10,
        choices=TIER_CHOICES,
        help_text="Contribution tier type"
    )
    asset_class = models.CharField(
        max_length=255,
        help_text="Description of asset class (e.g., 'Capital Injection', 'Dev Work', 'Office Lease')"
    )
    internal_units_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Numeric value of internal units (e.g., 15000 for cash, 120 for hours)"
    )
    internal_units_label = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Label for units (e.g., 'USD', 'hrs', 'pts', 'units', 'months')"
    )
    value_usd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Contribution value in USD"
    )
    currency = models.CharField(
        max_length=3,
        default='USD',
        help_text="Currency code (ISO 4217)"
    )
    exchange_rate = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=1.0000,
        validators=[MinValueValidator(0)],
        help_text="Exchange rate used for conversion (e.g., 127 KES/USD)"
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='SUBMITTED',
        help_text="Entry status (Phase 1: UI state only; approvals in Phase 2)"
    )
    date = models.DateField(
        help_text="Date of contribution"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes or context"
    )
    tier_metadata = models.JSONField(
        blank=True,
        null=True,
        default=dict,
        help_text=(
            "Tier-specific structured data. "
            "IN_KIND: {valuation_method}. "
            "TIME: {role_multiplier}. "
            "WORK: {deliverable_title, impact_tier}."
        )
    )
    
    class Meta:
        db_table = 'shareholders_ledger_entry'
        ordering = ['-date', '-created_at']
        verbose_name = 'Ledger Entry'
        verbose_name_plural = 'Ledger Entries'
        indexes = [
            models.Index(fields=['deal', 'date']),
            models.Index(fields=['deal', 'tier']),
            models.Index(fields=['deal', 'status']),
            models.Index(fields=['contributor', 'date']),
            models.Index(fields=['tx_id']),
        ]
    
    def __str__(self):
        return f"{self.tx_id} | {self.contributor.legal_name} | {self.get_tier_display()}"
    
    def save(self, *args, **kwargs):
        """Auto-generate tx_id if not set"""
        if not self.tx_id:
            self.tx_id = self._generate_tx_id()
        super().save(*args, **kwargs)
    
    def _generate_tx_id(self):
        """Generate unique transaction ID in format TX-NNNN"""
        while True:
            # Use last 4 digits of UUID for uniqueness
            suffix = str(uuid.uuid4().int)[-4:]
            tx_id = f"TX-{suffix}"
            if not LedgerEntry.objects.filter(tx_id=tx_id).exists():
                return tx_id
    
    @property
    def has_proof(self):
        """Check if this entry has supporting evidence attached"""
        return self.evidence.exists()


class LedgerEvidence(models.Model):
    """
    Supporting documents/proof for ledger entries (receipts, invoices, etc.).
    
    Phase 1: Basic file upload support.
    Future: Document verification, approval workflow integration.
    """
    
    ledger_entry = models.ForeignKey(
        LedgerEntry,
        on_delete=models.CASCADE,
        related_name='evidence',
        help_text="Associated ledger entry"
    )
    file = models.FileField(
        upload_to='shareholders/evidence/%Y/%m/',
        help_text="Uploaded proof document (PDF, JPG, PNG)"
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_ledger_evidence',
        help_text="User who uploaded this evidence"
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Upload timestamp"
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Optional description of the document"
    )
    
    class Meta:
        db_table = 'shareholders_ledger_evidence'
        ordering = ['-uploaded_at']
        verbose_name = 'Ledger Evidence'
        verbose_name_plural = 'Ledger Evidence'
    
    def __str__(self):
        return f"Evidence for {self.ledger_entry.tx_id}"


# =============================================================================
# VALUATION MODELS (Phase 2)
# =============================================================================

class ValuationRate(models.Model):
    """
    Configurable valuation rates for non-cash contribution tiers.
    
    Used to convert internal units (hours, points, units) to USD value.
    Each deal can have custom rates per tier.
    """
    
    TIER_CHOICES = [
        ('IN_KIND', 'In-Kind Asset'),
        ('TIME', 'Time Logged'),
        ('WORK', 'Work Deliverable'),
    ]
    
    deal = models.ForeignKey(
        Deal,
        on_delete=models.CASCADE,
        related_name='valuation_rates',
        help_text="Associated deal"
    )
    tier = models.CharField(
        max_length=10,
        choices=TIER_CHOICES,
        help_text="Contribution tier this rate applies to"
    )
    rate_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        validators=[MinValueValidator(0)],
        help_text="USD value per internal unit (e.g., 50.00 USD/hour)"
    )
    unit_label = models.CharField(
        max_length=50,
        help_text="Unit label (e.g., 'hour', 'point', 'unit')"
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Description of this rate (e.g., 'Senior Developer hourly rate')"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this rate is currently active"
    )
    effective_date = models.DateField(
        auto_now_add=True,
        help_text="Date this rate became effective"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'shareholders_valuation_rate'
        ordering = ['-effective_date']
        verbose_name = 'Valuation Rate'
        verbose_name_plural = 'Valuation Rates'
        indexes = [
            models.Index(fields=['deal', 'tier', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.deal.name} - {self.get_tier_display()}: ${self.rate_per_unit}/{self.unit_label}"


# =============================================================================
# APPROVAL & DISPUTE MODELS (Phase 2)
# =============================================================================

class LedgerApproval(models.Model):
    """
    Approval record for ledger entries.
    
    Tracks who approved an entry and when, with audit trail.
    """
    
    ACTION_CHOICES = [
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    
    ledger_entry = models.ForeignKey(
        LedgerEntry,
        on_delete=models.CASCADE,
        related_name='approvals',
        help_text="The ledger entry being approved"
    )
    action = models.CharField(
        max_length=10,
        choices=ACTION_CHOICES,
        help_text="Approval action taken"
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='ledger_approvals',
        help_text="User who approved this entry"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Approval notes or comments"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'shareholders_ledger_approval'
        ordering = ['-created_at']
        verbose_name = 'Ledger Approval'
        verbose_name_plural = 'Ledger Approvals'
    
    def __str__(self):
        return f"{self.ledger_entry.tx_id} - {self.action} by {self.approved_by}"


class LedgerDispute(models.Model):
    """
    Dispute record for ledger entries.
    
    Tracks disputes raised against entries within the dispute window.
    """
    
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('UNDER_REVIEW', 'Under Review'),
        ('RESOLVED', 'Resolved'),
        ('DISMISSED', 'Dismissed'),
    ]
    
    ledger_entry = models.ForeignKey(
        LedgerEntry,
        on_delete=models.CASCADE,
        related_name='disputes',
        help_text="The ledger entry being disputed"
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='OPEN',
        help_text="Current dispute status"
    )
    raised_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='raised_disputes',
        help_text="User who raised this dispute"
    )
    reason = models.TextField(
        help_text="Reason for the dispute"
    )
    resolution_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Notes on how the dispute was resolved"
    )
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_disputes',
        help_text="User who resolved this dispute"
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the dispute was resolved"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'shareholders_ledger_dispute'
        ordering = ['-created_at']
        verbose_name = 'Ledger Dispute'
        verbose_name_plural = 'Ledger Disputes'
    
    def __str__(self):
        return f"{self.ledger_entry.tx_id} - Dispute ({self.status})"


class LedgerAuditLog(models.Model):
    """
    Audit log for all ledger-related actions.
    
    Provides complete traceability for compliance and debugging.
    """
    
    ACTION_CHOICES = [
        ('CREATED', 'Entry Created'),
        ('UPDATED', 'Entry Updated'),
        ('STATUS_CHANGED', 'Status Changed'),
        ('APPROVED', 'Entry Approved'),
        ('REJECTED', 'Entry Rejected'),
        ('DISPUTE_RAISED', 'Dispute Raised'),
        ('DISPUTE_RESOLVED', 'Dispute Resolved'),
        ('EVIDENCE_ADDED', 'Evidence Added'),
        ('EVIDENCE_REMOVED', 'Evidence Removed'),
    ]
    
    ledger_entry = models.ForeignKey(
        LedgerEntry,
        on_delete=models.CASCADE,
        related_name='audit_logs',
        help_text="The ledger entry this log pertains to"
    )
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        help_text="Action performed"
    )
    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='ledger_audit_actions',
        help_text="User who performed this action"
    )
    old_value = models.TextField(
        blank=True,
        null=True,
        help_text="Previous value (for updates)"
    )
    new_value = models.TextField(
        blank=True,
        null=True,
        help_text="New value (for updates)"
    )
    details = models.JSONField(
        blank=True,
        null=True,
        help_text="Additional context in JSON format"
    )
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        help_text="IP address of the request"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'shareholders_ledger_audit_log'
        ordering = ['-created_at']
        verbose_name = 'Ledger Audit Log'
        verbose_name_plural = 'Ledger Audit Logs'
        indexes = [
            models.Index(fields=['ledger_entry', 'action']),
            models.Index(fields=['performed_by', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.ledger_entry.tx_id} - {self.action} at {self.created_at}"


# =============================================================================
# SNAPSHOT MODELS (Phase 2)
# =============================================================================

class EquitySnapshot(TimeStampedModel):
    """
    Immutable point-in-time record of the capitalization table.
    
    Snapshots freeze equity percentages, contribution totals, and member data
    at a specific moment. Once locked (after dispute window), snapshots cannot
    be modified.
    
    Locking Rules:
        - Snapshots can be locked manually or auto-lock after dispute_window_days
        - Locked snapshots are immutable
        - Checksum ensures data integrity
    """
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('LOCKED', 'Locked'),
        ('FINALIZED', 'Finalized'),
    ]
    
    deal = models.ForeignKey(
        Deal,
        on_delete=models.CASCADE,
        related_name='snapshots',
        help_text="Associated deal"
    )
    version_id = models.CharField(
        max_length=100,
        unique=True,
        help_text="Version identifier (e.g., 'v1.2-q3', 'v1.0-genesis')"
    )
    period_start = models.DateField(
        help_text="Start date of the snapshot period"
    )
    period_end = models.DateField(
        help_text="End date of the snapshot period"
    )
    snapshot_date = models.DateField(
        default=timezone.now,
        help_text="Date when snapshot was taken"
    )
    
    # Status and locking
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='DRAFT',
        help_text="Snapshot status"
    )
    is_locked = models.BooleanField(
        default=False,
        help_text="Whether this snapshot is locked and immutable"
    )
    locked_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the snapshot was locked"
    )
    locked_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='locked_snapshots',
        help_text="User who locked this snapshot"
    )
    
    # Dispute window
    dispute_window_days = models.IntegerField(
        default=7,
        validators=[MinValueValidator(0)],
        help_text="Days allowed for disputes before auto-lock"
    )
    auto_lock_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when snapshot will auto-lock (snapshot_date + dispute_window_days)"
    )
    
    # Aggregated totals (cached from snapshot lines)
    total_cash_usd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Total cash contributions in USD"
    )
    total_inkind_usd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Total in-kind contributions in USD"
    )
    total_time_usd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Total time contributions in USD"
    )
    total_work_usd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Total work contributions in USD"
    )
    total_valuation_usd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Total weighted valuation in USD"
    )
    
    # Members count
    members_count = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Number of members in this snapshot"
    )
    
    # Cryptographic integrity
    checksum = models.CharField(
        max_length=64,
        blank=True,
        help_text="SHA-256 checksum of snapshot data for integrity verification"
    )
    
    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_snapshots',
        help_text="User who created this snapshot"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Optional notes about this snapshot"
    )
    
    class Meta:
        db_table = 'shareholders_equity_snapshot'
        ordering = ['-snapshot_date', '-created_at']
        verbose_name = 'Equity Snapshot'
        verbose_name_plural = 'Equity Snapshots'
        indexes = [
            models.Index(fields=['deal', 'snapshot_date']),
            models.Index(fields=['deal', 'is_locked']),
            models.Index(fields=['deal', 'status']),
            models.Index(fields=['version_id']),
        ]
    
    def __str__(self):
        return f"{self.version_id} - {self.snapshot_date} ({self.status})"
    
    def save(self, *args, **kwargs):
        """Calculate auto_lock_date on save"""
        if self.snapshot_date and not self.auto_lock_date:
            from datetime import timedelta
            self.auto_lock_date = self.snapshot_date + timedelta(days=self.dispute_window_days)
        super().save(*args, **kwargs)
    
    @property
    def can_be_locked(self):
        """Check if snapshot can be locked"""
        return not self.is_locked and self.status in ['DRAFT', 'LOCKED']
    
    @property
    def days_until_auto_lock(self):
        """Calculate days until auto-lock"""
        if self.is_locked or not self.auto_lock_date:
            return 0
        from datetime import date
        delta = self.auto_lock_date - date.today()
        return max(0, delta.days)


class EquitySnapshotLine(models.Model):
    """
    Individual member's equity position within a snapshot.
    
    Stores per-member contribution breakdowns and equity percentage
    at the time of snapshot creation. This preserves historical data
    even if member contributions change later.
    """
    
    snapshot = models.ForeignKey(
        EquitySnapshot,
        on_delete=models.CASCADE,
        related_name='lines',
        help_text="Associated snapshot"
    )
    member = models.ForeignKey(
        Member,
        on_delete=models.PROTECT,
        related_name='snapshot_lines',
        help_text="Member this line refers to"
    )
    
    # Contribution totals by tier (at snapshot time)
    cash_usd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Cash contributions in USD"
    )
    inkind_usd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="In-kind contributions in USD"
    )
    time_usd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Time contributions in USD"
    )
    work_usd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Work contributions in USD"
    )
    
    # Weighted total and equity
    weighted_total_usd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Weighted total based on tier weights"
    )
    equity_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Equity ownership percentage"
    )
    
    # Member snapshot metadata
    member_name = models.CharField(
        max_length=255,
        help_text="Member name at snapshot time (cached)"
    )
    member_type = models.CharField(
        max_length=10,
        help_text="Member type at snapshot time (cached)"
    )
    member_role = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Member role at snapshot time (cached)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'shareholders_equity_snapshot_line'
        ordering = ['-equity_percentage', 'member_name']
        verbose_name = 'Equity Snapshot Line'
        verbose_name_plural = 'Equity Snapshot Lines'
        indexes = [
            models.Index(fields=['snapshot', 'member']),
            models.Index(fields=['snapshot', 'equity_percentage']),
        ]
        unique_together = [['snapshot', 'member']]
    
    def __str__(self):
        return f"{self.snapshot.version_id} - {self.member_name}: {self.equity_percentage}%"


class SnapshotAuditLog(models.Model):
    """
    Audit trail for snapshot-related actions.
    
    Tracks all snapshot operations for compliance and debugging.
    """
    
    ACTION_CHOICES = [
        ('CREATED', 'Snapshot Created'),
        ('LOCKED', 'Snapshot Locked'),
        ('UNLOCKED', 'Snapshot Unlocked'),
        ('EXPORTED', 'Snapshot Exported'),
        ('VIEWED', 'Snapshot Viewed'),
        ('DELETED', 'Snapshot Deleted'),
    ]
    
    snapshot = models.ForeignKey(
        EquitySnapshot,
        on_delete=models.CASCADE,
        related_name='audit_logs',
        help_text="The snapshot this log pertains to"
    )
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        help_text="Action performed"
    )
    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='snapshot_audit_actions',
        help_text="User who performed this action"
    )
    details = models.JSONField(
        blank=True,
        null=True,
        help_text="Additional context in JSON format"
    )
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        help_text="IP address of the request"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'shareholders_snapshot_audit_log'
        ordering = ['-created_at']
        verbose_name = 'Snapshot Audit Log'
        verbose_name_plural = 'Snapshot Audit Logs'
        indexes = [
            models.Index(fields=['snapshot', 'action']),
            models.Index(fields=['performed_by', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.snapshot.version_id} - {self.action} at {self.created_at}"


# =============================================================================
# COMPREHENSIVE AUDIT LOG (System-Wide)
# =============================================================================

class AuditLog(models.Model):
    """
    Immutable, system-wide audit trail for all critical Shareholders actions.
    
    This model provides comprehensive audit logging across all entities:
    members, contributions, ledgers, snapshots, deal config, and verifications.
    
    Audit logs are append-only and cannot be modified or deleted.
    """
    
    ACTION_TYPE_CHOICES = [
        # Member Actions
        ('MEMBER_CREATED', 'Member Created'),
        ('MEMBER_UPDATED', 'Member Updated'),
        ('MEMBER_ARCHIVED', 'Member Archived'),
        ('MEMBER_RESTORED', 'Member Restored'),
        
        # Contribution Actions
        ('CONTRIBUTION_SUBMITTED', 'Contribution Submitted'),
        ('CONTRIBUTION_UPDATED', 'Contribution Updated'),
        
        # Ledger Actions
        ('LEDGER_CREATED', 'Ledger Entry Created'),
        ('LEDGER_APPROVED', 'Ledger Entry Approved'),
        ('LEDGER_REJECTED', 'Ledger Entry Rejected'),
        ('LEDGER_DISPUTED', 'Ledger Entry Disputed'),
        ('LEDGER_DISPUTE_RESOLVED', 'Dispute Resolved'),
        
        # Snapshot Actions
        ('SNAPSHOT_CREATED', 'Snapshot Created'),
        ('SNAPSHOT_LOCKED', 'Snapshot Locked'),
        ('SNAPSHOT_UNLOCKED', 'Snapshot Unlocked'),
        ('SNAPSHOT_EXPORTED', 'Snapshot Exported'),
        ('SNAPSHOT_DELETED', 'Snapshot Deleted'),
        
        # Deal Config Actions
        ('CONFIG_UPDATED', 'Deal Config Updated'),
        ('WEIGHTS_UPDATED', 'Contribution Weights Updated'),
        ('FX_RATE_UPDATED', 'FX Rate Updated'),
        
        # Verification Actions
        ('VERIFICATION_SUBMITTED', 'Verification Submitted'),
        ('VERIFICATION_APPROVED', 'Verification Approved'),
        ('VERIFICATION_REJECTED', 'Verification Rejected'),
        
        # Evidence Actions
        ('EVIDENCE_UPLOADED', 'Evidence Uploaded'),
        ('EVIDENCE_REMOVED', 'Evidence Removed'),
    ]
    
    ENTITY_TYPE_CHOICES = [
        ('MEMBER', 'Member'),
        ('CONTRIBUTION', 'Contribution'),
        ('LEDGER_ENTRY', 'Ledger Entry'),
        ('SNAPSHOT', 'Equity Snapshot'),
        ('DEAL_CONFIG', 'Deal Configuration'),
        ('DEAL_WEIGHTS', 'Deal Weights'),
        ('VERIFICATION', 'Verification'),
        ('EVIDENCE', 'Evidence'),
        ('DEAL', 'Deal'),
    ]
    
    STATUS_CHOICES = [
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('PENDING', 'Pending'),
    ]
    
    # Core Fields
    deal = models.ForeignKey(
        Deal,
        on_delete=models.CASCADE,
        related_name='audit_logs',
        help_text="The deal this audit log belongs to"
    )
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When this action occurred"
    )
    
    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='shareholder_audit_logs',
        help_text="User who performed this action"
    )
    
    action_type = models.CharField(
        max_length=50,
        choices=ACTION_TYPE_CHOICES,
        db_index=True,
        help_text="Type of action performed"
    )
    
    entity_type = models.CharField(
        max_length=50,
        choices=ENTITY_TYPE_CHOICES,
        db_index=True,
        help_text="Type of entity affected"
    )
    
    entity_id = models.CharField(
        max_length=255,
        db_index=True,
        help_text="ID or unique identifier of the affected entity"
    )
    
    entity_reference = models.CharField(
        max_length=255,
        help_text="Human-readable reference (e.g., TX-20260211-001, v1.3-q1)"
    )
    
    description = models.TextField(
        help_text="Human-readable description of what happened"
    )
    
    # Request Metadata
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        help_text="IP address of the request"
    )
    
    request_source = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Source of request (web, api, admin, system)"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='SUCCESS',
        help_text="Status of the action"
    )
    
    # Additional Context
    details = models.JSONField(
        blank=True,
        null=True,
        help_text="Additional structured data (changes, metadata, etc.)"
    )
    
    old_values = models.JSONField(
        blank=True,
        null=True,
        help_text="Previous values before the change"
    )
    
    new_values = models.JSONField(
        blank=True,
        null=True,
        help_text="New values after the change"
    )
    
    class Meta:
        db_table = 'shareholders_audit_log'
        ordering = ['-timestamp']
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        indexes = [
            models.Index(fields=['deal', 'timestamp']),
            models.Index(fields=['action_type', 'timestamp']),
            models.Index(fields=['entity_type', 'timestamp']),
            models.Index(fields=['actor', 'timestamp']),
            models.Index(fields=['entity_type', 'entity_id']),
        ]
        permissions = [
            ('view_audit_log', 'Can view audit logs'),
        ]
    
    def __str__(self):
        actor_name = self.actor.username if self.actor else 'System'
        return f"{actor_name} - {self.get_action_type_display()} - {self.entity_reference}"
    
    def save(self, *args, **kwargs):
        """Override save to enforce immutability."""
        # Allow creation but prevent updates
        if self.pk is not None:
            raise ValidationError("Audit logs are immutable and cannot be modified.")
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Override delete to prevent deletion."""
        raise ValidationError("Audit logs are immutable and cannot be deleted.")
