"""
Shareholders Management System - Core Models (Phase 1)

=============================================================================
PRE-FLIGHT SAFETY DECISION LOG
=============================================================================
After scanning CODA codebase:
- No existing canonical "Deal" model found in shared_core or finance that fits equity management
- Finance app has Transaction/Payment models for financial operations (different purpose)
- No existing "Member" model for equity participants (accounts.CustomerUser is for platform users)
- Decision: Create new shareholders-scoped models with clear naming to avoid conflicts
- Using CODA's shared_core.models.TimeStampedModel as base for consistency
- All models namespaced to 'shareholders' app to prevent conflicts

Phase 1 Scope:
- Models for persistence: Deal, DealConfig, DealWeights, Member, LedgerEntry, LedgerEvidence
- NO approval workflow logic (Phase 2)
- NO dispute window enforcement (Phase 5)
- NO equity calculation engine (Phase 4)
- NO checksum generation (Phase 6)
- Statuses exist for UI state management and future phases

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
    
    Phase 1: Stores base currency and FX peg rate.
    Future phases: Dispute windows, snapshot scheduling, multi-currency support.
    """
    
    FX_MODE_CHOICES = [
        ('PEGGED', 'Pegged Rate'),
        ('MARKET', 'Market Rate'),
    ]
    
    deal = models.OneToOneField(
        Deal,
        on_delete=models.CASCADE,
        related_name='config',
        help_text="Associated deal"
    )
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
    dispute_window_days = models.IntegerField(
        default=7,
        validators=[MinValueValidator(0)],
        help_text="Days allowed for disputes (Phase 5 placeholder)"
    )
    next_snapshot_date = models.DateField(
        blank=True,
        null=True,
        help_text="Next scheduled snapshot date (Phase 6 placeholder for dashboard display)"
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
    
    class Meta:
        db_table = 'shareholders_member'
        ordering = ['legal_name']
        verbose_name = 'Member'
        verbose_name_plural = 'Members'
        indexes = [
            models.Index(fields=['deal', 'is_archived']),
            models.Index(fields=['email']),
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
