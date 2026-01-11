# Equity, Shareholding & Voting System (4-Tier) - Technical Analysis

**Date:** December 2025  
**Branch:** `25.12_CODA_DEV_CM`  
**Purpose:** Comprehensive technical analysis mapping BRD/FRD requirements to existing CODA codebase patterns and identifying design decisions

---

## Executive Summary

This analysis maps the Equity/Shareholding/Voting System BRD to the existing CODA Django monolith architecture. **No existing equity-specific code exists** - this is a greenfield module that must integrate with:

- **Management app**: Task/TaskHistory patterns (snapshots, time tracking, work tracking)
- **Finance app**: Payment/Transaction models, config patterns, approval workflows, FX utilities
- **Accounts app**: CustomerUser model, Department model
- **Shared Core**: Base models (TimeStampedModel, StatusMixin), Company model

**Multi-Organization Platform:** The equity engine is a **multi-organization / multi-deal platform operated by CODA**. CODA will use this to host equity and voting data for many companies it enters into relationships with (clients, partners, JV vehicles, etc.). Each Company (e.g., **Biashara Bridges**) can have one or more EquityDeal records, and a set of members/stakeholders (shareholders) with their corresponding equity %, shares, and votes.

**Example Use Case:** Biashara Bridges is a company with 13 members. These 13 members constitute the shareholders for that relationship. In the CODA UI, when a user selects Biashara Bridges, they can see its deals/relationships and a Stakeholders/Cap Table view listing all 13 members with their Equity %, Shares, and Votes.

**Recommendation:** Implement as an equity module inside the existing `finance` app, reusing existing patterns for snapshots, approvals, configs, and FX conversion. The equity code will be organized as sub-modules within `finance`: `finance/models/equity.py`, `finance/services/equity/`, `finance/views/equity/`, etc.

**Finance App Dependency Context:** The `finance` app has moderate coupling to other CODA apps, particularly the `management` app (used for employee compliance, task history, and salary calculations). However, these dependencies are concentrated in specific services (compliance services, salary dashboards, budget integrations) that the equity module will avoid. The equity module will be implemented as an **isolated sub-module** inside `finance`, depending only on `shared_core`, `accounts` (via `settings.AUTH_USER_MODEL`), and selected `finance.utils` utilities. This design ensures external developers can work on the equity module within the finance app without needing to understand the management app's internal task/compliance logic.

**Payment Provider Separation:** CODA does not store or process client funds directly. All cash contributions are executed via trusted external payment providers (e.g., M-Pesa, PayPal, Stripe, bank transfers). CODA's role is to record, normalize, and audit contributions (Cash, In-Kind, Time, Work), not to act as a wallet or payment processor. This design keeps CODA out of PCI-DSS scope and minimizes regulatory exposure, while payment providers handle KYC/AML compliance, card processing, and chargeback management. When Biashara Bridges' shareholders contribute via their website, CODA records these contributions and converts them into equity, shares, and voting power, while payments themselves remain fully handled by existing, trusted providers.

---

## A. High-Level Fit and Target Location

### A.1 Repository Scan Summary

#### Relevant Apps/Modules

1. **`coda/finance/`** (Primary location)
   - **Why:** Already handles monetary flows, payments, transactions, FX conversion, approval workflows
   - **Patterns available:** `PayslipConfig`, `ApprovalPolicy`, `BudgetRequest`, `CurrencyConverter`, scoring services
   - **Recommendation:** Equity module should live here as `coda/finance/models/equity.py` and `coda/finance/services/equity/`

2. **`coda/management/`** (Secondary integration)
   - **Why:** CODA already has a Tasks system (`Task`, `TaskHistory`, `ActivityType`) used to assign work and track time and effort
   - **Patterns available:** `TaskHistory` snapshot pattern, `Task` work tracking, `ActivityType` categorization
   - **Integration:** The Time and Work ledgers are conceptually layered on top of this Task system. Phase 1 will use standalone ledger models with optional FK to Task for future integration. Phase 2 will auto-import or link contributions from Task/TaskHistory into the equity engine, so effort logged in the Task system flows naturally into Work/Time scoring.

3. **`coda/shared_core/`** (Base models)
   - **Why:** Provides base mixins and shared models
   - **Models:** `TimeStampedModel`, `StatusMixin`, `UserReferenceMixin`, `Company`

4. **`coda/accounts/`** (User model)
   - **Why:** User/member representation
   - **Model:** `CustomerUser` (extends AbstractUser), `Department`

#### Existing Models/Services That Look Related

**✅ Found:**
- `Company` model (`main.models` → `shared_core.models`) - Represents external companies like Biashara Bridges that CODA has relationships with
- `CustomerUser` model (`accounts.models`) - Represents members/stakeholders (each shareholder is a CustomerUser; a single user can be a stakeholder in multiple companies/deals)
- `TaskHistory` model (`management.models`) - Snapshot pattern (used for monthly snapshots of Task state)
- `Task` model (`management.models`) - Core work tracking system (assigns work, tracks time and effort via points/duration)
- `ActivityType` model (`management.models`) - Categorizes work activities
- `BudgetRequest` model (`finance.models.budget`) - Approval workflow pattern
- `PayslipConfig` model (`finance.models.core`) - Config pattern
- `CurrencyConverter` service (`finance.utils.currency_converter`) - FX conversion

**❌ Not Found:**
- No equity/shareholding/cap table models
- No voting power models
- No multi-tier contribution scoring engine

### A.2 Recommendation: Where This Module Should Live

**Primary Location: `coda/finance/`**

**Justification:**
1. **Monetary domain alignment**: Equity deals with cash contributions, USD conversions, financial scoring
2. **Existing patterns**: Finance app already has:
   - Config models (`PayslipConfig`, `ApprovalPolicy`)
   - Approval workflows (`BudgetRequest` with status, approval_chain, approved_by)
   - FX utilities (`CurrencyConverter.get_exchange_rate()`)
   - Scoring services (`CreditScoringService`, pattern for weighted calculations)
   - Export utilities (CSV exports in views)

3. **Service layer architecture**: Finance app follows service-oriented design (`finance/services/`)

**Structure Proposal:**
```
coda/finance/
├── models/
│   ├── equity.py              # New: EquityDeal, DealMember, DealConfig, etc.
│   └── ...
├── services/
│   ├── equity/
│   │   ├── __init__.py
│   │   ├── equity_scoring_engine.py    # New: 4-tier scoring logic
│   │   ├── equity_config_service.py    # New: FX, weights, multipliers resolution
│   │   ├── snapshot_service.py         # New: Generate/lock snapshots
│   │   └── export_service.py           # New: Cap table Excel/PDF exports
│   └── ...
├── views/
│   ├── equity/                # New: Deal, Ledger, Snapshot views
│   └── ...
└── templates/
    └── finance/
        └── equity/            # New: Deal setup, ledger entry, cap table templates
```

**Note:** Equity code adheres to the dependency guardrails defined in Section J, to ensure external developers can work safely inside the finance app without needing to understand management's internal task/compliance logic.

---

## B. Mapping BRD Entities to Existing Models

### B.1 Organization

**BRD Requirement:** Organization entity representing the business relationship/deal owner

**Existing Model:**
- `Company` model exists in `main.models` (exported via `shared_core.models.Company`)
  - Fields: `name`, `slug`, `sector`, `mission`, `website`, `location`, `user` (FK), `relation` (client/investor/background/other)
  - Inherits `TimeStampedModel` (created_at, updated_at, is_active, is_featured)

**Multi-Company Context:**
The `Company` model represents **external companies like Biashara Bridges** that CODA has relationships with. CODA operates the equity engine as a multi-organization platform, where each Company can have:
- One or more EquityDeal records (different projects/relationships with that company)
- A set of members/stakeholders (shareholders) with their equity %, shares, and votes

**Example:** Biashara Bridges is a company with 13 members. These 13 members constitute the shareholders for that relationship. When a user selects Biashara Bridges in the CODA UI, they can see its deals/relationships and a Stakeholders/Cap Table view listing all 13 members.

**Recommendation:**
- **Option A (Preferred):** Reuse `Company` model as `Organization`
  - Pros: Already exists, has location, sector, relation types
  - Cons: `relation` field is IntegerChoices (client/investor/background/other) - may need to extend
  - **Decision:** Use `Company` model directly. Add `company` FK to `EquityDeal` model.

- **Option B:** Create `EquityOrganization` extending `Company`
  - Pros: Can add equity-specific fields
  - Cons: Unnecessary duplication if `Company` is sufficient
  - **Decision:** Not needed - `Company` is sufficient for Phase 1

**Implementation:**
```python
# In EquityDeal model:
organization = models.ForeignKey(
    'main.Company',
    on_delete=models.CASCADE,
    related_name='equity_deals',
    help_text="Organization/Company this deal belongs to (e.g., Biashara Bridges)"
)
```

### B.2 Member

**BRD Requirement:** Person/entity that can contribute and receive equity

**Existing Model:**
- `CustomerUser` model exists in `accounts.models` (exported via `shared_core.users.CustomerUser`)
  - Extends Django `AbstractUser`
  - Fields: `first_name`, `last_name`, `email`, `phone`, `category`, `is_staff`, `is_active`, etc.
  - Has computed properties: `full_name`, `employment_status`, `client_status`

**Multi-Company Context:**
For Phase 1, each shareholder is represented as a `CustomerUser`. A single user can be a stakeholder in multiple companies/deals. For example, a user might be a shareholder in both Biashara Bridges and another company relationship.

**Recommendation:**
- **Option A (Preferred):** Use `CustomerUser` directly as Member via ForeignKey
  - Pros: Already exists, has full user profile, authentication, permissions
  - Cons: Assumes all members are users (may not handle external entities)
  - **Decision:** Use `CustomerUser` for Phase 1

- **Option B:** Create `EquityMember` intermediate table
  - Pros: Can handle non-user entities (companies, trusts, holding companies)
  - Cons: More complexity, potential duplication
  - **Decision:** Defer to future phase (out of scope for pilot). In a future phase, CODA may introduce an `EquityMember` abstraction to support non-user entities, but this is not required for the initial implementation.

**Implementation:**
```python
# In all ledger models and EquitySnapshot:
from django.conf import settings

member = models.ForeignKey(
    settings.AUTH_USER_MODEL,  # Maps to 'accounts.CustomerUser'
    on_delete=models.CASCADE,
    related_name='%(class)s_contributions',  # e.g., 'cash_contributions'
    help_text="Member/stakeholder making this contribution"
)
```

**Note:** For Phase 1, all members are `CustomerUser` instances. The system supports a user being a stakeholder in multiple companies/deals simultaneously.

### B.3 Deal/Relationship

**BRD Requirement:** Project/JV/Investment Vehicle that contains members, configs, ledgers, and snapshots

**Existing Models:**
- No direct equivalent exists
- `BaseContract` in `management.models` has contract_type, client, status - but too generic

**Recommendation:**
- **Create new model:** `EquityDeal` (or `Deal` within equity context)

**Proposed Model Structure:**
```python
class EquityDeal(TimeStampedModel):
    """
    Represents a single equity relationship/deal with its own config, members, and snapshots.
    Each deal belongs to a Company (e.g., Biashara Bridges) and can have multiple stakeholders.
    """
    DEAL_STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
    ]
    
    name = models.CharField(max_length=255, help_text="Deal name (e.g., 'Q1 2025 Project')")
    slug = models.SlugField(max_length=255, unique=True, help_text="URL-friendly identifier")
    
    organization = models.ForeignKey('main.Company', on_delete=models.CASCADE, related_name='equity_deals')
    
    # Dates
    start_date = models.DateField(help_text="Deal start date")
    end_date = models.DateField(null=True, blank=True, help_text="Deal end date (if closed)")
    
    # Status (domain-specific: draft/active/completed/paused/cancelled)
    status = models.CharField(max_length=20, choices=DEAL_STATUS_CHOICES, default='draft')
    
    # Description
    description = models.TextField(blank=True, help_text="Deal description")
    
    # Template/cloning support
    cloned_from = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cloned_deals',
        help_text="If this deal was cloned from a template"
    )
    
    class Meta:
        verbose_name = "Equity Deal"
        verbose_name_plural = "Equity Deals"
        indexes = [
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['start_date', 'end_date']),
        ]
```

### B.4 Role/Position (per deal)

**BRD Requirement:** Member's role/position within a deal affects multipliers (e.g., Lead=1.2, Core=1.1, Support=1.0)

**Existing Models:**
- No direct equivalent
- `UserProfile.position` exists but is company-wide, not deal-specific
- `Task.group` exists but is for pay calculations, not equity

**Recommendation:**
- **Create new model:** `DealMemberRole` (Many-to-Many relationship through intermediate model)

**Proposed Model Structure:**
```python
class DealMemberRole(TimeStampedModel):
    """
    Links a Member to a Deal with a role/position that affects multipliers.
    """
    deal = models.ForeignKey('EquityDeal', on_delete=models.CASCADE, related_name='member_roles')
    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='deal_roles')
    
    role = models.CharField(
        max_length=100,
        help_text="Role name (e.g., 'Lead', 'Core', 'Support')"
    )
    position = models.CharField(
        max_length=100,
        blank=True,
        help_text="Position/title (e.g., 'Technical Lead', 'Product Manager')"
    )
    
    # Multiplier (can override deal-level defaults)
    role_multiplier = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('1.0'),
        help_text="Multiplier for work contributions (e.g., 1.2 for Lead, 1.1 for Core)"
    )
    
    # Effective dates
    effective_from = models.DateField(help_text="When this role assignment started")
    effective_to = models.DateField(null=True, blank=True, help_text="When this role ended (if applicable)")
    
    class Meta:
        unique_together = [('deal', 'member', 'role', 'effective_from')]
        indexes = [
            models.Index(fields=['deal', 'member']),
            models.Index(fields=['deal', 'role']),
        ]
```

### B.5 Config (weights, FX, multipliers, rules)

**BRD Requirement:** Per-deal configuration for FX policy, tier weights, multipliers, approval workflows, voting rules

**Existing Patterns:**
- `PayslipConfig` (`finance.models.core`) - Per-user config with DecimalFields
- `ApprovalPolicy` (`finance.models.budget`) - Policy config with JSONField for flexible rules
- `TradingRule` (`investing.models`) - Config with JSONField for rule_config

**Recommendation:**
- **Create new model:** `DealConfig` following `ApprovalPolicy` pattern (JSONField for flexibility + key fields as separate columns)

**Proposed Model Structure:**
```python
class DealConfig(TimeStampedModel):
    """
    Configuration for a Deal: FX policy, tier weights, multipliers, approval rules, voting rules.
    Follows config-driven pattern to avoid code changes per deal.
    """
    deal = models.OneToOneField(
        'EquityDeal',
        on_delete=models.CASCADE,
        related_name='config',
        help_text="Deal this configuration belongs to"
    )
    
    # FX Configuration
    base_currency = models.CharField(max_length=3, default='USD', help_text="Base currency (USD)")
    pegged_rate_enabled = models.BooleanField(default=True, help_text="Use pegged rate instead of market rate")
    pegged_rate_value = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=Decimal('127.0'),
        help_text="Pegged rate (e.g., 127 KSh = 1 USD)"
    )
    pegged_rate_effective_from = models.DateField(help_text="When pegged rate became effective")
    pegged_rate_revision_frequency = models.CharField(
        max_length=20,
        choices=[('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('annual', 'Annual')],
        default='quarterly',
        help_text="How often pegged rate can be revised"
    )
    
    # Tier Weights (must sum to 100%)
    weight_cash = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('55.0'), help_text="Cash tier weight (%)")
    weight_in_kind = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('20.0'), help_text="In-Kind tier weight (%)")
    weight_time = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('10.0'), help_text="Time tier weight (%)")
    weight_work = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('15.0'), help_text="Work tier weight (%)")
    
    # Weights effective date (for history)
    weights_effective_from = models.DateField(help_text="When these weights became effective")
    
    # Multipliers (stored as JSON for flexibility: month-based or phase-based)
    time_multipliers = models.JSONField(
        default=dict,
        help_text="Time multipliers by month/phase. Example: {'1': 1.2, '2': 1.1, '3': 1.0} or {'phase_1': 1.2}"
    )
    role_multipliers = models.JSONField(
        default=dict,
        help_text="Role multipliers. Example: {'Lead': 1.2, 'Core': 1.1, 'Support': 1.0}"
    )
    
    # Caps and Safeguards
    max_share_per_member = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum equity % per member (if capped)"
    )
    time_scoring_cap = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum time score per member (to prevent inflation)"
    )
    in_kind_approval_threshold = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="In-kind value threshold requiring special approval"
    )
    
    # Approval Workflow Configuration
    approval_workflow_config = models.JSONField(
        default=dict,
        help_text="Approval chain configuration. Example: {'cash': ['finance'], 'in_kind': ['finance', 'lead'], 'time': ['admin'], 'work': ['department_lead']}"
    )
    
    # Voting Rule Configuration
    voting_rule = models.CharField(
        max_length=50,
        choices=[('one_share_one_vote', '1 Share = 1 Vote'), ('capped', 'Capped Voting Power'), ('class_based', 'Class-Based Voting')],
        default='one_share_one_vote',
        help_text="Voting rule for this deal"
    )
    voting_config = models.JSONField(
        default=dict,
        help_text="Additional voting configuration (e.g., cap percentage, class definitions)"
    )
    
    # Share Model Configuration
    share_model = models.CharField(
        max_length=50,
        choices=[('fixed_total', 'Fixed Total Shares'), ('share_price', 'Share Price Model')],
        default='fixed_total',
        help_text="How shares are calculated"
    )
    total_shares = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total shares (for fixed_total model)"
    )
    share_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Share price in USD (for share_price model)"
    )
    
    class Meta:
        verbose_name = "Deal Configuration"
        verbose_name_plural = "Deal Configurations"
```

**Service Pattern:**
Create `EquityConfigService` in `finance/services/equity/equity_config_service.py` to:
- Resolve FX rate for a given date (check pegged vs market rate)
- Resolve tier weights for a given date (if weights changed over time)
- Resolve time multiplier for a given date (based on deal start_date)
- Resolve role multiplier for a given member+role+date
- Validate config (weights sum to 100%, etc.)

### B.6 Ledgers

**BRD Requirement:** Four ledger types - Cash, In-Kind, Time, Work - each with approval workflow

**Existing Models:**
- **Cash:** `Transaction` model (`finance.models.core`) tracks payments, but not structured for equity contributions
- **Time:** CODA's `Task` and `TaskHistory` models (`management.models`) track time/points and work done. The `Task` system is used to assign work and track time and effort. The Time and Work ledgers are conceptually layered on top of this Task system.
- **Work:** `Task` model tracks work done, `ActivityType` categorizes work
- **In-Kind:** No equivalent exists

**Integration Strategy:**
- **Phase 1:** Create standalone ledger models (`CashContribution`, `InKindContribution`, `TimeContribution`, `WorkContribution`) with optional FK to Task for future integration
- **Phase 2:** Auto-import or link contributions from Task/TaskHistory into the equity engine, so effort logged in the Task system flows naturally into Work/Time scoring

**Recommendation:**
- **Create new ledger models:** `CashContribution`, `InKindContribution`, `TimeContribution`, `WorkContribution`

**Proposed Model Structure:**

#### B.6.1 Cash Contributions Ledger

**Design Principle:** CODA records contributions; payment providers move money. CODA stores amount, currency, FX rate used, payment provider (e.g., PayPal, Stripe, M-Pesa, Bank), provider transaction ID/reference, status (pending, confirmed, failed), and evidence (receipt PDF, screenshot, etc.). Payment providers store card numbers, M-Pesa details, KYC/AML checks, chargeback handling, and regulatory compliance. This keeps CODA out of PCI-DSS scope (no card handling), lean on AML/KYC (rely on providers' compliance stack), and focused on equity math and audit, not banking regulation.

**CashContribution Model:**
```python
class CashContribution(TimeStampedModel):
    """
    Cash contribution ledger entry with approval workflow.
    
    Note: Uses domain-specific status workflow (draft/submitted/approved/rejected) instead of StatusMixin
    to avoid field conflicts and keep the logic explicit.
    
    CODA expects to be called after the payment has been confirmed by the external provider,
    and does not initiate or settle the payment itself. All monetary movements are processed
    through trusted payment providers (PayPal, Stripe, M-Pesa, banks, etc.).
    """
    from django.conf import settings
    
    deal = models.ForeignKey('EquityDeal', on_delete=models.CASCADE, related_name='cash_contributions')
    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cash_contributions')
    
    # Contribution details
    date = models.DateField(help_text="Date of contribution")
    amount = models.DecimalField(max_digits=15, decimal_places=2, help_text="Amount in original currency")
    currency = models.CharField(max_length=3, default='KES', help_text="Original currency (KES, USD, etc.)")
    usd_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Amount in USD (calculated based on FX policy)"
    )
    
    # Payment provider (external provider that handled the actual money movement)
    provider = models.CharField(
        max_length=50,
        choices=[
            ('paypal', 'PayPal'),
            ('stripe', 'Stripe'),
            ('mpesa', 'M-Pesa'),
            ('bank_transfer', 'Bank Transfer'),
            ('other', 'Other')
        ],
        help_text="External payment provider that processed the transaction"
    )
    provider_reference = models.CharField(
        max_length=255,
        blank=True,
        help_text="Transaction ID/reference from the payment provider (e.g., PayPal payment ID, M-Pesa transaction code, bank reference)"
    )
    provider_status = models.CharField(
        max_length=50,
        blank=True,
        help_text="Raw status from provider if needed (e.g., 'completed', 'pending', 'failed')"
    )
    
    # Reconciliation tracking
    reconciled = models.BooleanField(default=False, help_text="Whether this contribution has been reconciled with provider records")
    reconciled_at = models.DateTimeField(null=True, blank=True, help_text="When reconciliation occurred")
    reconciled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reconciled_cash_contributions',
        help_text="User who performed reconciliation"
    )
    
    # Evidence
    receipt_file = models.FileField(upload_to='equity/receipts/', blank=True, null=True, help_text="Upload receipt")
    notes = models.TextField(blank=True, help_text="Additional notes")
    
    # Status and Approval (domain-specific workflow: draft/submitted/approved/rejected)
    status = models.CharField(
        max_length=20,
        choices=[('draft', 'Draft'), ('submitted', 'Submitted'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        default='draft'
    )
    approved_by = models.ForeignKey(
        'accounts.CustomerUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_cash_contributions',
        help_text="Finance/Accounts user who approved"
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_by = models.ForeignKey(
        'accounts.CustomerUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rejected_cash_contributions'
    )
    rejected_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Cash Contribution"
        verbose_name_plural = "Cash Contributions"
        indexes = [
            models.Index(fields=['deal', 'member', 'status']),
            models.Index(fields=['deal', 'date']),
        ]
```

#### B.6.2 In-Kind Contributions Ledger

```python
class InKindContribution(TimeStampedModel):
    """
    In-kind contribution ledger entry (goods/services).
    
    Note: Uses domain-specific status workflow instead of StatusMixin to avoid field conflicts.
    """
    from django.conf import settings
    
    deal = models.ForeignKey('EquityDeal', on_delete=models.CASCADE, related_name='in_kind_contributions')
    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='in_kind_contributions')
    
    # Contribution details
    date = models.DateField()
    item_service = models.CharField(max_length=255, help_text="Item or service description")
    category = models.CharField(
        max_length=100,
        choices=[('equipment', 'Equipment'), ('software', 'Software'), ('services', 'Services'), ('other', 'Other')],
        help_text="Category of contribution"
    )
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('1.0'))
    
    # Valuation
    proposed_value = models.DecimalField(max_digits=15, decimal_places=2, help_text="Member's proposed value in USD")
    valuation_method = models.CharField(
        max_length=50,
        choices=[
            ('invoice_value', 'Invoice Value Only'),
            ('market_value', 'Market Value Agreed'),
            ('lower_of', 'Lower of Invoice vs Market'),
            ('catalog_pricing', 'Catalog Pricing')
        ],
        help_text="Valuation method used"
    )
    approved_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Finance-approved value in USD"
    )
    
    # Evidence
    evidence = models.FileField(upload_to='equity/in_kind_evidence/', blank=True, null=True)
    invoice_file = models.FileField(upload_to='equity/invoices/', blank=True, null=True)
    
    # Status and Approval (requires Finance + Lead approval)
    status = models.CharField(
        max_length=20,
        choices=[('draft', 'Draft'), ('submitted', 'Submitted'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        default='draft'
    )
    approved_by_finance = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_in_kind_finance'
    )
    approved_by_lead = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_in_kind_lead'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "In-Kind Contribution"
        verbose_name_plural = "In-Kind Contributions"
```

#### B.6.3 Time Ledger

```python
class TimeContribution(TimeStampedModel):
    """
    Time contribution ledger entry (meetings, coordination, support).
    
    Note: Uses domain-specific status workflow instead of StatusMixin to avoid field conflicts.
    Phase 1: Standalone model. Phase 2: Will integrate with Task/TaskHistory for auto-import.
    """
    from django.conf import settings
    
    deal = models.ForeignKey('EquityDeal', on_delete=models.CASCADE, related_name='time_contributions')
    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='time_contributions')
    
    # Optional link to underlying Task (for Phase 2 integration)
    task = models.ForeignKey(
        'management.Task',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='equity_time_contributions',
        help_text="Optional link to the underlying Task driving this time entry (Phase 2 integration)"
    )
    
    # Time details
    date = models.DateField()
    type = models.CharField(
        max_length=50,
        choices=[('meeting', 'Meeting'), ('coordination', 'Coordination'), ('support', 'Support')],
        help_text="Type of time contribution"
    )
    duration = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Duration in hours"
    )
    
    # Phase/Month for multiplier calculation
    phase_month = models.CharField(
        max_length=50,
        help_text="Phase or month identifier (e.g., '1' for Month 1, 'phase_1')"
    )
    multiplier_applied = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('1.0'),
        help_text="Multiplier applied (calculated based on date relative to deal start)"
    )
    
    # Evidence
    evidence = models.FileField(upload_to='equity/time_evidence/', blank=True, null=True, help_text="Attendance record")
    meeting_link = models.URLField(blank=True, help_text="Meeting link/recording")
    
    # Status and Approval (Admin/PM approves)
    status = models.CharField(
        max_length=20,
        choices=[('draft', 'Draft'), ('submitted', 'Submitted'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        default='draft'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_time_contributions'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Time Contribution"
        verbose_name_plural = "Time Contributions"
```

**Phase 1 vs Phase 2 Integration:**
- **Phase 1:** Time and Work contributions can be entered directly into the equity ledger (standalone models with optional task FK for future use)
- **Phase 2:** The plan is to auto-import or link contributions from Task/TaskHistory into the equity engine, so effort logged in the Task system flows naturally into Work/Time scoring. This will involve:
  - Standardizing mappings from Task fields (effort, status, type) to equity Work/Time scoring
  - Potentially adding batch ingestion or background jobs that read TaskHistory and create/update TimeContribution/WorkContribution entries

#### B.6.4 Work Done Ledger

```python
class WorkContribution(TimeStampedModel):
    """
    Work done contribution ledger entry (deliverables, impact-based work).
    
    Note: Uses domain-specific status workflow instead of StatusMixin to avoid field conflicts.
    Phase 1: Standalone model. Phase 2: Will integrate with Task/TaskHistory for auto-import.
    """
    from django.conf import settings
    
    deal = models.ForeignKey('EquityDeal', on_delete=models.CASCADE, related_name='work_contributions')
    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='work_contributions')
    
    # Optional link to underlying Task (for Phase 2 integration)
    task = models.ForeignKey(
        'management.Task',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='equity_work_contributions',
        help_text="Optional link to the underlying Task driving this work entry (Phase 2 integration)"
    )
    
    # Work details
    date = models.DateField()
    deliverable = models.CharField(max_length=255, help_text="Deliverable description")
    category = models.CharField(
        max_length=100,
        choices=[('development', 'Development'), ('analysis', 'Analysis'), ('design', 'Design'), ('other', 'Other')],
        help_text="Work category"
    )
    impact_tier = models.CharField(
        max_length=10,
        choices=[('H', 'High'), ('M', 'Medium'), ('L', 'Low')],
        help_text="Impact tier"
    )
    
    # Role and multiplier
    role = models.ForeignKey(
        'DealMemberRole',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='work_contributions',
        help_text="Member's role at time of work (for multiplier)"
    )
    multiplier_applied = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('1.0'),
        help_text="Role multiplier applied"
    )
    
    # Scoring (configurable per deal: deliverables-based, impact-tier, hybrid)
    points = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Points assigned (calculated based on scoring method)"
    )
    
    # Reviewer
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_work_contributions',
        help_text="Department Lead or PM who reviewed"
    )
    
    # Evidence
    evidence = models.URLField(blank=True, help_text="Link to deliverable/evidence")
    
    # Status and Approval (Department Lead + optional PM)
    status = models.CharField(
        max_length=20,
        choices=[('draft', 'Draft'), ('submitted', 'Submitted'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        default='draft'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_work_contributions'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Work Contribution"
        verbose_name_plural = "Work Contributions"
```

**Note:** Consider referencing `Task` model for work data. For Phase 1, create standalone `WorkContribution`. In Phase 2, add integration to auto-import from `Task` if desired.

### B.7 Approvals + Audit Log

**BRD Requirement:** Approval workflows for each ledger type, audit trail of all changes

**Existing Patterns:**
- `BudgetRequest` model (`finance.models.budget`) has:
  - `status` field (draft/pending/approved/rejected)
  - `approved_by`, `approved_at`, `rejected_by`, `rejected_at` fields
  - `approval_chain` JSONField
  - `last_modified_by` field (from StatusMixin)
- `ApprovalEngineService` (`finance.services.automation_service`) processes approvals

**Recommendation:**
- **Use domain-specific status workflow** (draft/submitted/approved/rejected) implemented directly on equity models instead of reusing StatusMixin to avoid field conflicts and keep the logic explicit
- **Add approval fields** to each ledger model (as shown in B.6)
- **Create audit log model** for detailed change tracking

**Note on StatusMixin:** Equity models use their own status fields rather than StatusMixin because:
- Equity uses domain-specific status workflow (draft/submitted/approved/rejected) that differs from StatusMixin's choices (pending/active/completed/paused/cancelled)
- This avoids field conflicts and keeps the approval logic explicit and clear

**Proposed Audit Log Model:**
```python
class EquityAuditLog(TimeStampedModel):
    """
    Audit log for all equity-related actions (create, edit, approve, reject, delete).
    """
    from django.conf import settings
    from django.contrib.contenttypes.fields import GenericForeignKey
    from django.contrib.contenttypes.models import ContentType
    
    ACTION_CHOICES = [
        ('create', 'Created'),
        ('edit', 'Edited'),
        ('approve', 'Approved'),
        ('reject', 'Rejected'),
        ('delete', 'Deleted (Soft)'),
    ]
    
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    # Generic foreign key to any equity model
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Change details
    changes = models.JSONField(default=dict, help_text="Before/after values")
    reason = models.TextField(blank=True, help_text="Reason for change/approval/rejection")
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Equity Audit Log"
        verbose_name_plural = "Equity Audit Logs"
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['user', 'created_at']),
        ]
```

**Service Pattern:**
Create `EquityAuditService` to log actions automatically via signals or service methods.

### B.8 Equity Snapshot + Voting Snapshot

**BRD Requirement:** Monthly (or on-demand) snapshots of equity %, shares, votes, with locking after dispute window

**Existing Patterns:**
- `TaskHistory` model (`management.models`) - **Perfect pattern to emulate**
  - Snapshot of `Task` state at monthly reset
  - Fields: `daf_date` (monthly filter date), immutable after creation
  - Used for budget/salary calculations

**Recommendation:**
- **Create `EquitySnapshot` model** following `TaskHistory` pattern

**Proposed Model Structure:**
```python
class EquitySnapshot(TimeStampedModel):
    """
    Immutable monthly snapshot of equity calculations for a deal.
    Similar to TaskHistory - captures state at a point in time.
    """
    from django.conf import settings
    
    deal = models.ForeignKey('EquityDeal', on_delete=models.CASCADE, related_name='snapshots')
    
    # Snapshot date (monthly, e.g., 2025-01-31 for January snapshot)
    snapshot_date = models.DateField(help_text="Date this snapshot represents (typically month-end)")
    
    # Locking
    is_locked = models.BooleanField(default=False, help_text="Snapshot is locked (no edits allowed)")
    locked_at = models.DateTimeField(null=True, blank=True, help_text="When snapshot was locked")
    locked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='locked_equity_snapshots'
    )
    dispute_window_days = models.IntegerField(default=7, help_text="Dispute window in days")
    dispute_window_end = models.DateField(null=True, blank=True, help_text="When dispute window ends")
    
    # Config snapshot (at time of calculation)
    config_snapshot = models.JSONField(default=dict, help_text="DealConfig values at snapshot time")
    
    # Tier totals (aggregated)
    total_cash_usd = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.0'))
    total_in_kind_usd = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.0'))
    total_time_score = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.0'))
    total_work_score = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.0'))
    
    class Meta:
        verbose_name = "Equity Snapshot"
        verbose_name_plural = "Equity Snapshots"
        unique_together = [('deal', 'snapshot_date')]
        indexes = [
            models.Index(fields=['deal', 'snapshot_date']),
            models.Index(fields=['deal', 'is_locked']),
        ]


class EquitySnapshotMember(TimeStampedModel):
    """
    Per-member equity breakdown within a snapshot.
    """
    from django.conf import settings
    
    snapshot = models.ForeignKey('EquitySnapshot', on_delete=models.CASCADE, related_name='members')
    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='equity_snapshots')
    
    # Tier totals for this member
    cash_usd_total = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.0'))
    in_kind_usd_total = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.0'))
    time_score_total = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.0'))
    work_score_total = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.0'))
    
    # Normalized tier shares (0-1, sum to 1 across all members per tier)
    cash_share = models.DecimalField(max_digits=10, decimal_places=6, default=Decimal('0.0'))
    in_kind_share = models.DecimalField(max_digits=10, decimal_places=6, default=Decimal('0.0'))
    time_share = models.DecimalField(max_digits=10, decimal_places=6, default=Decimal('0.0'))
    work_share = models.DecimalField(max_digits=10, decimal_places=6, default=Decimal('0.0'))
    
    # Weighted tier scores
    weighted_cash_score = models.DecimalField(max_digits=10, decimal_places=6, default=Decimal('0.0'))
    weighted_in_kind_score = models.DecimalField(max_digits=10, decimal_places=6, default=Decimal('0.0'))
    weighted_time_score = models.DecimalField(max_digits=10, decimal_places=6, default=Decimal('0.0'))
    weighted_work_score = models.DecimalField(max_digits=10, decimal_places=6, default=Decimal('0.0'))
    
    # Final equity score and %
    equity_score = models.DecimalField(max_digits=10, decimal_places=6, default=Decimal('0.0'))
    equity_percentage = models.DecimalField(max_digits=10, decimal_places=6, default=Decimal('0.0'))
    
    # Shares and votes
    shares = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.0'))
    votes = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.0'))
    
    class Meta:
        unique_together = [('snapshot', 'member')]
        indexes = [
            models.Index(fields=['snapshot', 'member']),
            models.Index(fields=['member']),
        ]
```

**Service Pattern:**
Create `EquitySnapshotService` to:
- Generate snapshot for a given deal + date
- Calculate all tier totals, normalization, weighting, equity scores
- Compute shares and votes based on DealConfig
- Lock snapshot after dispute window
- Prevent edits to locked snapshots

---

## C. Mapping BRD Functional Modules to Code-Level Components

### C.1 Deal/Relationship Setup (BRD 10.1)

**BRD Requirements:**
- Create Deal with name, dates, status, members, config
- Clone Deal config from template

**Views Needed:**
1. **Deal List View** (`/equity/deals/`)
   - List all deals for user's organization
   - Filter by status, date range
   - Template: Reuse `finance/templates/finance/budgets/budget_list.html` pattern

2. **Deal Create/Edit View** (`/equity/deals/create/`, `/equity/deals/<id>/edit/`)
   - Form for Deal fields (name, dates, organization, status)
   - Add members with roles (inline formset or separate step)
   - Template: Reuse `finance/templates/finance/budgets/budget_form.html` pattern

3. **Deal Detail View** (`/equity/deals/<id>/`)
   - Show deal info, members, config summary, recent snapshots
   - Template: Create new `finance/templates/finance/equity/deal_detail.html`

4. **Deal Clone View** (`/equity/deals/<id>/clone/`)
   - Clone Deal + DealConfig (create new deal with same config)
   - Template: Reuse create view with pre-filled data

**Forms Needed:**
- `EquityDealForm` - Basic deal fields
- `DealMemberRoleFormSet` - For adding multiple members with roles

**Admin:**
- Register `EquityDeal`, `DealConfig`, `DealMemberRole` in Django Admin
- Use admin for initial setup, custom views for user-facing forms

### C.2 Configuration Engine (BRD 10.2)

**BRD Requirements:**
- FX config (pegged rate, validity period, revision frequency)
- Weights config (with effective dates for history)
- Multipliers (time by month/phase, role by position)
- Caps & safeguards

**Service Design:**
Create `EquityConfigService` in `finance/services/equity/equity_config_service.py`:

```python
class EquityConfigService:
    """
    Service for resolving deal configuration (FX, weights, multipliers) for a given date.
    Handles history-aware resolution (weights changed over time).
    """
    
    def __init__(self, deal: EquityDeal):
        self.deal = deal
        self.config = deal.config
    
    def get_fx_rate(self, date: date, from_currency: str = 'KES', to_currency: str = 'USD') -> Decimal:
        """
        Get FX rate for given date.
        If pegged_rate_enabled, use pegged_rate_value.
        Otherwise, use CurrencyConverter service.
        """
        if self.config.pegged_rate_enabled:
            return Decimal(str(self.config.pegged_rate_value))
        else:
            from finance.utils.currency_converter import CurrencyConverter
            converter = CurrencyConverter()
            return converter.get_exchange_rate(from_currency, to_currency)
    
    def get_weights(self, date: date) -> Dict[str, Decimal]:
        """
        Get tier weights for given date.
        For Phase 1, return current weights. For Phase 2, support weight history.
        """
        # Phase 1: Single weight set
        return {
            'cash': self.config.weight_cash,
            'in_kind': self.config.weight_in_kind,
            'time': self.config.weight_time,
            'work': self.config.weight_work,
        }
    
    def get_time_multiplier(self, date: date) -> Decimal:
        """
        Get time multiplier for given date based on months since deal start.
        """
        months_since_start = (date.year - self.deal.start_date.year) * 12 + (date.month - self.deal.start_date.month) + 1
        multiplier_key = str(months_since_start)
        multipliers = self.config.time_multipliers or {}
        return Decimal(str(multipliers.get(multiplier_key, 1.0)))
    
    def get_role_multiplier(self, role_name: str) -> Decimal:
        """
        Get role multiplier for given role name.
        """
        multipliers = self.config.role_multipliers or {}
        return Decimal(str(multipliers.get(role_name, 1.0)))
    
    def validate_weights(self) -> bool:
        """
        Validate that weights sum to 100%.
        """
        total = (
            self.config.weight_cash +
            self.config.weight_in_kind +
            self.config.weight_time +
            self.config.weight_work
        )
        return total == Decimal('100.0')
```

**Reuse:**
- `CurrencyConverter.get_exchange_rate()` from `finance/utils/currency_converter.py` for market rates
- Config validation in model `clean()` method

### C.3 Ledger Modules (BRD 10.3)

**BRD Requirements:**
- Create, edit, submit, approve/reject entries
- Attach evidence
- Audit trail

**Service Patterns:**
Create per-ledger services OR one generic service:

**Option A (Preferred):** Generic `EquityLedgerService`
```python
class EquityLedgerService:
    """
    Generic service for all ledger types (cash, in-kind, time, work).
    Handles approval workflow, status transitions, evidence attachment.
    """
    
    def submit_for_approval(self, contribution, user):
        """Mark contribution as submitted, trigger approval workflow."""
        contribution.status = 'submitted'
        contribution.save()
        # Log audit
        EquityAuditService.log_action('submit', user, contribution)
    
    def approve(self, contribution, approver, comments=None):
        """Approve contribution based on type."""
        if isinstance(contribution, CashContribution):
            contribution.approved_by = approver
            contribution.approved_at = timezone.now()
        elif isinstance(contribution, InKindContribution):
            # Check if finance or lead approval needed
            if not contribution.approved_by_finance:
                contribution.approved_by_finance = approver
            elif not contribution.approved_by_lead:
                contribution.approved_by_lead = approver
                contribution.approved_at = timezone.now()
        # ... similar for time/work
        
        contribution.status = 'approved'
        contribution.save()
        EquityAuditService.log_action('approve', approver, contribution, reason=comments)
```

**Views Needed:**
1. **Ledger List Views** (`/equity/deals/<id>/ledgers/cash/`, `/in-kind/`, `/time/`, `/work/`)
   - List contributions for deal, filter by status, member, date
   - Template: Reuse `finance/templates/finance/budgets/budget_request_list.html` pattern

2. **Ledger Entry Forms** (`/equity/deals/<id>/ledgers/cash/create/`, etc.)
   - Create/edit contribution entry
   - Upload evidence
   - Template: Create new `finance/templates/finance/equity/contribution_form.html`

3. **Approval Dashboard** (`/equity/deals/<id>/approvals/`)
   - List pending approvals (all ledger types)
   - Approve/reject actions
   - Template: Reuse `finance/templates/finance/approvals/budget_projection_approvals.html` pattern

**Reuse:**
- Approval workflow pattern from `BudgetRequest` (status, approved_by, approval_chain)
- File upload pattern from `TaskLinks` (evidence storage)
- Form patterns from finance forms

### C.4 Scoring & Equity Engine (BRD 10.4)

**BRD Requirements:**
- Step 1: Tier totals per member
- Step 2: Normalize each tier (tier share = member total / total across all members)
- Step 3: Apply weights (weighted score = tier share × tier weight)
- Step 4: Final equity score (sum of weighted scores)

**Service Design:**
Create `EquityScoringEngine` in `finance/services/equity/equity_scoring_engine.py`:

```python
class EquityScoringEngine:
    """
    Core scoring engine for 4-tier equity calculation.
    """
    
    def __init__(self, deal: EquityDeal, snapshot_date: date):
        self.deal = deal
        self.snapshot_date = snapshot_date
        self.config_service = EquityConfigService(deal)
    
    def calculate_equity_scores(self) -> Dict:
        """
        Calculate equity scores for all members in deal.
        
        Returns:
            Dict mapping member (User instance) to breakdown dictionary
        """
        Calculate equity scores for all members in deal.
        
        Returns:
            Dict mapping member to breakdown:
            {
                member: {
                    'cash_usd_total': Decimal,
                    'in_kind_usd_total': Decimal,
                    'time_score_total': Decimal,
                    'work_score_total': Decimal,
                    'cash_share': Decimal,  # Normalized
                    'in_kind_share': Decimal,
                    'time_share': Decimal,
                    'work_share': Decimal,
                    'weighted_cash_score': Decimal,
                    'weighted_in_kind_score': Decimal,
                    'weighted_time_score': Decimal,
                    'weighted_work_score': Decimal,
                    'equity_score': Decimal,  # Final score
                    'equity_percentage': Decimal,  # Final %
                }
            }
        """
        # Step 1: Calculate tier totals per member
        member_totals = self._calculate_tier_totals()
        
        # Step 2: Normalize each tier
        normalized_shares = self._normalize_tiers(member_totals)
        
        # Step 3: Apply weights
        weighted_scores = self._apply_weights(normalized_shares)
        
        # Step 4: Final equity score
        equity_scores = self._calculate_final_scores(weighted_scores)
        
        return equity_scores
    
    def _calculate_tier_totals(self) -> Dict:
        """Step 1: Aggregate approved contributions per member per tier."""
        members = self.deal.member_roles.values_list('member', flat=True).distinct()
        
        totals = {}
        for member in members:
            # Cash total (USD)
            cash_total = CashContribution.objects.filter(
                deal=self.deal,
                member=member,
                status='approved',
                date__lte=self.snapshot_date
            ).aggregate(total=Sum('usd_amount'))['total'] or Decimal('0.0')
            
            # In-kind total (USD)
            in_kind_total = InKindContribution.objects.filter(
                deal=self.deal,
                member=member,
                status='approved',
                date__lte=self.snapshot_date
            ).aggregate(total=Sum('approved_value'))['total'] or Decimal('0.0')
            
            # Time total (hours × multiplier)
            from django.db.models import F, Sum, ExpressionWrapper, DecimalField
            
            time_expr = ExpressionWrapper(
                F('duration') * F('multiplier_applied'),
                output_field=DecimalField(max_digits=15, decimal_places=2)
            )
            time_total = TimeContribution.objects.filter(
                deal=self.deal,
                member=member,
                status='approved',
                date__lte=self.snapshot_date
            ).aggregate(
                total=Sum(time_expr)
            )['total'] or Decimal('0.0')
            
            # Work total (points × role multiplier)
            work_expr = ExpressionWrapper(
                F('points') * F('multiplier_applied'),
                output_field=DecimalField(max_digits=15, decimal_places=2)
            )
            work_total = WorkContribution.objects.filter(
                deal=self.deal,
                member=member,
                status='approved',
                date__lte=self.snapshot_date
            ).aggregate(
                total=Sum(work_expr)
            )['total'] or Decimal('0.0')
            
            totals[member] = {
                'cash': cash_total,
                'in_kind': in_kind_total,
                'time': time_total,
                'work': work_total,
            }
        
        return totals
    
    def _normalize_tiers(self, member_totals: Dict) -> Dict:
        """Step 2: Normalize each tier (member total / tier total across all members)."""
        # Calculate tier totals across all members
        tier_totals = {
            'cash': sum(t['cash'] for t in member_totals.values()),
            'in_kind': sum(t['in_kind'] for t in member_totals.values()),
            'time': sum(t['time'] for t in member_totals.values()),
            'work': sum(t['work'] for t in member_totals.values()),
        }
        
        # Normalize
        normalized = {}
        for member, totals in member_totals.items():
            normalized[member] = {
                'cash_share': totals['cash'] / tier_totals['cash'] if tier_totals['cash'] > 0 else Decimal('0.0'),
                'in_kind_share': totals['in_kind'] / tier_totals['in_kind'] if tier_totals['in_kind'] > 0 else Decimal('0.0'),
                'time_share': totals['time'] / tier_totals['time'] if tier_totals['time'] > 0 else Decimal('0.0'),
                'work_share': totals['work'] / tier_totals['work'] if tier_totals['work'] > 0 else Decimal('0.0'),
            }
        
        return normalized
    
    def _apply_weights(self, normalized_shares: Dict) -> Dict:
        """Step 3: Apply tier weights."""
        weights = self.config_service.get_weights(self.snapshot_date)
        
        weighted = {}
        for member, shares in normalized_shares.items():
            weighted[member] = {
                'weighted_cash': shares['cash_share'] * (weights['cash'] / Decimal('100.0')),
                'weighted_in_kind': shares['in_kind_share'] * (weights['in_kind'] / Decimal('100.0')),
                'weighted_time': shares['time_share'] * (weights['time'] / Decimal('100.0')),
                'weighted_work': shares['work_share'] * (weights['work'] / Decimal('100.0')),
            }
        
        return weighted
    
    def _calculate_final_scores(self, weighted_scores: Dict) -> Dict:
        """Step 4: Sum weighted scores to get final equity score and percentage."""
        final_scores = {}
        total_equity_score = sum(
            w['weighted_cash'] + w['weighted_in_kind'] + w['weighted_time'] + w['weighted_work']
            for w in weighted_scores.values()
        )
        
        for member, weighted in weighted_scores.items():
            equity_score = (
                weighted['weighted_cash'] +
                weighted['weighted_in_kind'] +
                weighted['weighted_time'] +
                weighted['weighted_work']
            )
            equity_percentage = (equity_score / total_equity_score * Decimal('100.0')) if total_equity_score > 0 else Decimal('0.0')
            
            final_scores[member] = {
                **weighted,
                'equity_score': equity_score,
                'equity_percentage': equity_percentage,
            }
        
        return final_scores
```

**Reuse:**
- Aggregation patterns from `TaskHistory` queries (Sum, F expressions)
- Decimal math patterns from `PayCalculationService` (if exists) or `Task.get_pay`

### C.5 Shares and Voting Power (BRD 10.5)

**BRD Requirements:**
- Fixed total shares model OR share price model
- Calculate shares from equity %
- 1 share = 1 vote (default), with optional caps

**Service Design:**
Extend `EquityScoringEngine` with share/vote calculation:

```python
    def calculate_shares_and_votes(self, equity_scores: Dict) -> Dict:
    """
    Calculate shares and votes for each member based on equity %.
    """
    config = self.deal.config
    
    results = {}
    for member, scores in equity_scores.items():
        equity_pct = scores['equity_percentage']
        
        # Calculate shares based on model
        if config.share_model == 'fixed_total':
            shares = equity_pct / Decimal('100.0') * config.total_shares
        elif config.share_model == 'share_price':
            # Convert equity score to USD value, then divide by share price
            # (This requires additional business logic - placeholder)
            equity_usd_value = equity_pct / Decimal('100.0') * self._get_deal_total_value()
            shares = equity_usd_value / config.share_price if config.share_price > 0 else Decimal('0.0')
        else:
            shares = Decimal('0.0')
        
        # Calculate votes (default: 1 share = 1 vote)
        if config.voting_rule == 'one_share_one_vote':
            votes = shares
        elif config.voting_rule == 'capped':
            max_votes_pct = config.voting_config.get('max_votes_percentage', 100)
            votes = min(shares, equity_pct / Decimal('100.0') * max_votes_pct * config.total_shares)
        else:
            votes = shares  # Default
        
        results[member] = {
            **scores,
            'shares': shares,
            'votes': votes,
        }
    
    return results
```

**Storage:**
- Store shares and votes in `EquitySnapshotMember` model (part of snapshot)

### C.6 Snapshot & Locking (BRD 10.6)

**BRD Requirements:**
- Generate monthly (or on-demand) snapshots
- Lock after dispute window (e.g., 7 days)
- Prevent edits after lock
- Full history for audit

**Service Design:**
Create `EquitySnapshotService` in `finance/services/equity/snapshot_service.py`:

```python
class EquitySnapshotService:
    """
    Service for generating and managing equity snapshots.
    """
    
    def generate_snapshot(self, deal: EquityDeal, snapshot_date: date, user) -> EquitySnapshot:
        """
        Generate a new equity snapshot for a deal.
        
        Args:
            deal: EquityDeal instance
            snapshot_date: Date for the snapshot (typically month-end)
            user: User instance (from settings.AUTH_USER_MODEL) who is generating the snapshot
        """
        # Check if snapshot already exists
        if EquitySnapshot.objects.filter(deal=deal, snapshot_date=snapshot_date).exists():
            raise ValueError(f"Snapshot for {snapshot_date} already exists")
        
        # Calculate equity scores
        scoring_engine = EquityScoringEngine(deal, snapshot_date)
        equity_results = scoring_engine.calculate_equity_scores()
        share_results = scoring_engine.calculate_shares_and_votes(equity_results)
        
        # Create snapshot
        snapshot = EquitySnapshot.objects.create(
            deal=deal,
            snapshot_date=snapshot_date,
            config_snapshot=self._snapshot_config(deal.config),
            dispute_window_end=snapshot_date + timedelta(days=deal.config.dispute_window_days or 7),
            # Calculate tier totals
            total_cash_usd=sum(r['cash_usd_total'] for r in equity_results.values()),
            # ... other totals
        )
        
        # Create snapshot members
        for member, results in share_results.items():
            EquitySnapshotMember.objects.create(
                snapshot=snapshot,
                member=member,
                **results  # All calculated values
            )
        
        # Log audit
        EquityAuditService.log_action('create', user, snapshot)
        
        return snapshot
    
    def lock_snapshot(self, snapshot: EquitySnapshot, user) -> None:
        """
        Lock a snapshot (no edits allowed after lock).
        
        Args:
            snapshot: EquitySnapshot instance to lock
            user: User instance (from settings.AUTH_USER_MODEL) who is locking the snapshot
        """
        """
        Lock a snapshot (no edits allowed after lock).
        """
        if snapshot.is_locked:
            raise ValueError("Snapshot is already locked")
        
        snapshot.is_locked = True
        snapshot.locked_at = timezone.now()
        snapshot.locked_by = user
        snapshot.save()
        
        EquityAuditService.log_action('lock', user, snapshot)
    
    def can_edit_snapshot(self, snapshot: EquitySnapshot) -> bool:
        """
        Check if snapshot can be edited (not locked and within dispute window).
        """
        if snapshot.is_locked:
            return False
        
        if snapshot.dispute_window_end and timezone.now().date() > snapshot.dispute_window_end:
            return False
        
        return True
```

**Views Needed:**
1. **Snapshot List View** (`/equity/deals/<id>/snapshots/`)
   - List all snapshots for deal
   - Show locked status, dispute window
   - Template: Create new

2. **Generate Snapshot View** (`/equity/deals/<id>/snapshots/generate/`)
   - Trigger snapshot generation
   - Preview before generating
   - Template: Create new

3. **Snapshot Detail View** (`/equity/deals/<id>/snapshots/<snapshot_id>/`)
   - Show cap table, member breakdown
   - Lock action (if authorized)
   - Template: Create new

**Reuse:**
- Snapshot pattern from `TaskHistory` (immutable, date-based)
- Locking pattern from budget approvals (is_locked, locked_at)

### C.7 Reporting & Exports (BRD 10.7)

**BRD Requirements:**
- Cap table report (members, equity %, shares, votes)
- Contribution reports by tier
- Approval status reports
- Excel export (template-aligned)
- PDF summary report

**Existing Patterns:**
- CSV exports in `finance/views.py` (`analytics_export`, `compliance_export`)
- Excel utilities in `ai_services/utils.py` (`process_excel_file`)
- PDF generation in `finance/services/payment_receipt_service.py` (receipt generation)

**Service Design:**
Create `EquityExportService` in `finance/services/equity/export_service.py`:

```python
class EquityExportService:
    """
    Service for exporting equity data to Excel/PDF.
    """
    
    def export_cap_table_excel(self, snapshot: EquitySnapshot) -> HttpResponse:
        """
        Export cap table to Excel format (aligned with legacy template).
        """
        import openpyxl
        from django.http import HttpResponse
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Cap Table"
        
        # Headers
        ws.append(['Member', 'Equity %', 'Shares', 'Votes', 'Cash USD', 'In-Kind USD', 'Time Score', 'Work Score'])
        
        # Data
        for member_data in snapshot.members.all().order_by('-equity_percentage'):
            ws.append([
                member_data.member.full_name,
                float(member_data.equity_percentage),
                float(member_data.shares),
                float(member_data.votes),
                float(member_data.cash_usd_total),
                float(member_data.in_kind_usd_total),
                float(member_data.time_score_total),
                float(member_data.work_score_total),
            ])
        
        # Create response
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="cap_table_{snapshot.snapshot_date}.xlsx"'
        wb.save(response)
        
        return response
    
    def export_contribution_report(self, deal: EquityDeal, tier: str, start_date: date, end_date: date) -> HttpResponse:
        """
        Export contribution report for a tier.
        """
        # Similar pattern, filter by tier type
        pass
    
    def export_pdf_summary(self, snapshot: EquitySnapshot) -> HttpResponse:
        """
        Export PDF summary report.
        """
        # Use reportlab or weasyprint (if available)
        # Or reuse payment receipt service pattern
        pass
```

**Views Needed:**
1. **Export Cap Table** (`/equity/deals/<id>/snapshots/<snapshot_id>/export/excel/`)
2. **Export Contributions** (`/equity/deals/<id>/ledgers/<tier>/export/`)
3. **Export PDF Summary** (`/equity/deals/<id>/snapshots/<snapshot_id>/export/pdf/`)

**Reuse:**
- CSV export pattern from `compliance_export` view
- Excel generation (if openpyxl is available, or use CSV)
- PDF generation pattern from `PaymentReceiptService`

### C.8 Audit & Compliance (BRD 10.8)

**BRD Requirements:**
- Log all actions (create, edit, approve, reject, delete)
- Timestamp, user, old/new values, reason
- Soft delete only

**Implementation:**
- Use `EquityAuditLog` model (defined in B.7)
- Create `EquityAuditService` to log actions
- Add signals or service method calls to log automatically

**Service Design:**
```python
class EquityAuditService:
    """
    Service for logging equity-related actions.
    """
    
    @staticmethod
    def log_action(
        action: str,
        user,
        content_object: models.Model,
        changes: dict = None,
        reason: str = None,
        request = None
    ) -> EquityAuditLog:
        """
        Log an action on an equity model.
        
        Args:
            action: Action type (create, edit, approve, reject, delete)
            user: User instance (from settings.AUTH_USER_MODEL) performing the action
            content_object: The equity model instance being acted upon
            changes: Dict of before/after values (optional)
            reason: Reason for the action (optional)
            request: Django request object for IP address (optional)
        """
        """
        Log an action on an equity model.
        """
        return EquityAuditLog.objects.create(
            action=action,
            user=user,
            content_object=content_object,
            changes=changes or {},
            reason=reason or '',
            ip_address=request.META.get('REMOTE_ADDR') if request else None,
        )
```

**Views Needed:**
1. **Audit Log View** (`/equity/deals/<id>/audit/`)
   - List all audit log entries for deal
   - Filter by action, user, date
   - Template: Create new or reuse admin audit log pattern

**Soft Delete:**
- Add `is_deleted` boolean field to all ledger models (or use `is_active=False`)
- Override `delete()` method to set `is_deleted=True` instead of actual deletion

### C.9 Roles & Permissions Implementation

**BRD Requirement:** Role-based access control for equity module operations

**Mapping BRD Roles to Django Groups:**

| BRD Role | Django Group / Mechanism | Main Capabilities in Equity Module |
|----------|-------------------------|-----------------------------------|
| System Admin | Group `equity_system_admin` or `superuser` | Manage organizations, deals, configs, snapshots, exports, audit |
| Finance/Accounts | Group `equity_finance` | Approve cash, approve in-kind (finance side), view all ledger entries |
| Admin/PM | Group `equity_admin_pm` | Approve time entries, see all contributions for assigned deals |
| Department Lead | Group `equity_department_lead` | Approve work contributions, approve in-kind as lead |
| Member/Contributor | Authenticated user or `equity_member` group | Submit own cash/in-kind/time/work entries, view own snapshots |
| Viewer/Auditor | Group `equity_auditor` | Read-only access to snapshots and audit log |

**External Company Integration:**
External companies like Biashara Bridges can expose CODA equity features to their users (shareholders) while still letting CODA control internal roles such as Equity Finance, Equity Admin/PM, and Equity Auditor inside the CODA platform. Shareholders from external companies authenticate via SSO/JWT tokens or user tokens, and their access is scoped to their company's deals. They can view their own contributions, cap tables, and make new contributions, but approval workflows remain within CODA's role-based system.

**Implementation Notes:**
- Enforcement will be done via existing permission/authorization patterns used in finance and management apps (e.g., decorators like `@user_passes_test`, mixins like `LoginRequiredMixin`)
- Specific permission names (e.g., `can_approve_equity_cash`, `can_view_equity_snapshots`) can be added as Django model permissions on the relevant models
- Permission checks will be implemented in views and services, following the pattern used in `BudgetRequest` approval workflows

**Example Permission Decorators:**
```python
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import Group

def is_equity_finance(user):
    return user.groups.filter(name='equity_finance').exists() or user.is_superuser

@user_passes_test(is_equity_finance)
def approve_cash_contribution(request, contribution_id):
    # Approval logic
    pass
```

---

## D. Views, Templates, and Reusability

### D.1 Views & URLs

**Proposed URL Structure:**
```python
# finance/urls.py (add equity section)
urlpatterns += [
    path('equity/', include('finance.urls_equity')),
]

# finance/urls_equity.py (new file)
urlpatterns = [
    # Deals
    path('deals/', views.equity.deal_list, name='equity-deal-list'),
    path('deals/create/', views.equity.deal_create, name='equity-deal-create'),
    path('deals/<int:deal_id>/', views.equity.deal_detail, name='equity-deal-detail'),
    path('deals/<int:deal_id>/edit/', views.equity.deal_edit, name='equity-deal-edit'),
    path('deals/<int:deal_id>/clone/', views.equity.deal_clone, name='equity-deal-clone'),
    
    # Ledgers
    path('deals/<int:deal_id>/ledgers/cash/', views.equity.cash_list, name='equity-cash-list'),
    path('deals/<int:deal_id>/ledgers/cash/create/', views.equity.cash_create, name='equity-cash-create'),
    path('deals/<int:deal_id>/ledgers/in-kind/', views.equity.in_kind_list, name='equity-in-kind-list'),
    # ... similar for time/work
    
    # Approvals
    path('deals/<int:deal_id>/approvals/', views.equity.approval_dashboard, name='equity-approval-dashboard'),
    path('deals/<int:deal_id>/approvals/<int:contribution_id>/approve/', views.equity.approve_contribution, name='equity-approve'),
    path('deals/<int:deal_id>/approvals/<int:contribution_id>/reject/', views.equity.reject_contribution, name='equity-reject'),
    
    # Snapshots
    path('deals/<int:deal_id>/snapshots/', views.equity.snapshot_list, name='equity-snapshot-list'),
    path('deals/<int:deal_id>/snapshots/generate/', views.equity.snapshot_generate, name='equity-snapshot-generate'),
    path('deals/<int:deal_id>/snapshots/<int:snapshot_id>/', views.equity.snapshot_detail, name='equity-snapshot-detail'),
    path('deals/<int:deal_id>/snapshots/<int:snapshot_id>/lock/', views.equity.snapshot_lock, name='equity-snapshot-lock'),
    
    # Exports
    path('deals/<int:deal_id>/snapshots/<int:snapshot_id>/export/excel/', views.equity.export_cap_table_excel, name='equity-export-cap-table'),
    path('deals/<int:deal_id>/snapshots/<int:snapshot_id>/export/pdf/', views.equity.export_cap_table_pdf, name='equity-export-cap-table-pdf'),
    
    # Audit
    path('deals/<int:deal_id>/audit/', views.equity.audit_log, name='equity-audit-log'),
]
```

**View Patterns:**
- Use class-based views (ListView, CreateView, UpdateView, DetailView) following finance app patterns
- Reuse permission decorators (`@login_required`, `@user_passes_test`)
- Reuse form handling patterns from budget views

### D.2 Templates & Front-End

**Templates to Create:**
1. `finance/templates/finance/equity/deal_list.html` - List deals
2. `finance/templates/finance/equity/deal_form.html` - Create/edit deal
3. `finance/templates/finance/equity/deal_detail.html` - Deal overview
4. `finance/templates/finance/equity/contribution_list.html` - List contributions (cash/in-kind/time/work)
5. `finance/templates/finance/equity/contribution_form.html` - Create/edit contribution
6. `finance/templates/finance/equity/approval_dashboard.html` - Approval dashboard
7. `finance/templates/finance/equity/snapshot_list.html` - List snapshots
8. `finance/templates/finance/equity/snapshot_detail.html` - Cap table view
9. `finance/templates/finance/equity/audit_log.html` - Audit log

**Templates to Reuse/Adapt:**
- Base template: `finance/templates/finance/base.html` (if exists) or `templates/base.html`
- List pattern: `finance/templates/finance/budgets/budget_list.html`
- Form pattern: `finance/templates/finance/budgets/budget_form.html`
- Approval pattern: `finance/templates/finance/approvals/budget_projection_approvals.html`

**Front-End:**
- Reuse existing CSS/JS from finance app
- Use Django forms (not separate front-end framework)
- Consider AJAX for approval actions (reuse patterns from budget approvals)

### D.3 Admin & Staff Interface

**Admin Registration:**
- Register `EquityDeal`, `DealConfig`, `DealMemberRole`, all ledger models, `EquitySnapshot`, `EquitySnapshotMember`, `EquityAuditLog` in `finance/admin.py`

**Admin vs Custom UI:**
- **Admin-first:** Deal creation, DealConfig setup, initial member assignment (for staff)
- **User-facing forms:** Contribution submission (members), approval dashboard (finance/admin), snapshot viewing (all)

**Recommendation:**
- Use Django Admin for configuration and setup
- Use custom views for user-facing workflows (contributions, approvals, snapshots)

### D.4 UI Navigation Example

**Top-Level Navigation:**
The equity module will be accessible via a "Companies" (or "Organizations") list page showing all companies CODA has relationships with.

**Example User Journey - Biashara Bridges:**

1. **Companies List** (`/equity/companies/`)
   - User sees list of all companies (e.g., Biashara Bridges, Company B, Company C)
   - Each company shows: name, number of deals, number of stakeholders, latest snapshot date

2. **Company Detail Page** (`/equity/companies/<company_id>/`)
   - When user clicks "Biashara Bridges", they go to the Company detail page
   - This page has an **Equity tab** that shows:
     - List of EquityDeals for Biashara Bridges
     - A prominent **"Current cap table"** link for the active deal
     - Summary statistics (total stakeholders: 13, total equity %, etc.)

3. **Deal Detail / Cap Table View** (`/equity/deals/<deal_id>/snapshots/<snapshot_id>/`)
   - When user clicks into the current deal or snapshot, they see a **Cap Table / Stakeholders view** with columns:
     - **Member** (name)
     - **Equity %**
     - **Shares**
     - **Votes**
     - **Tier totals** (Cash USD, In-Kind USD, Time Score, Work Score)
   - Each member row is clickable and links to a member detail view

4. **Member Detail View** (`/equity/deals/<deal_id>/members/<member_id>/`)
   - Shows individual member's:
     - Contributions across all four ledgers (Cash, In-Kind, Time, Work)
     - Time and work efforts (and potentially underlying Tasks if linked in Phase 2)
     - Equity history (snapshots over time)
     - Role assignments and multipliers

**Note:** Biashara Bridges is used as a concrete example, but this UI pattern is reusable for any company. The system supports multiple companies, each with their own deals and stakeholders. Biashara Bridges will surface equity functionality on their own website via either: (1) redirect to CODA's equity module (PayPal-style flow), or (2) embedded CODA UI (iframe) using Biashara's theme, so shareholders feel they are still "inside" the Biashara environment even when hosted by CODA.

---

## E. External Website Integration & Platform / White-Label Model

### E.1 Platform Role (Multi-Company)

CODA acts as a **platform** that can host equity for many companies (Biashara Bridges and others). Each company has one or more `EquityDeal` records; each deal has its own stakeholders, configuration (weights, FX, multipliers), and snapshots. The same equity engine serves all companies, but data is strictly partitioned by `Company` / `EquityDeal`. This multi-tenant architecture allows CODA to provide equity services to multiple clients while maintaining data isolation and company-specific branding.

### E.2 Integration Pattern (PayPal-Style Redirect / Embed)

CODA supports two primary integration modes for company websites:

**Redirect Flow:**
From Biashara's site, a user clicks "My Equity" or "Contribute Cash". They are redirected to a CODA-hosted equity page for that company/deal (e.g., `https://coda-equity.com/biashara-bridges/deals/{deal_slug}/contribute-cash?user_token=...`). The page is themed to match Biashara's brand (logo, colors, typography). For cash contributions, CODA then redirects the user to the chosen payment provider (M-Pesa, PayPal, bank, etc.) to complete the payment. After payment succeeds, the provider redirects back to CODA with a transaction reference. CODA records the contribution, links it to the Biashara Bridges equity deal, and updates the cap table. CODA can optionally redirect back to Biashara with a status URL (e.g., `https://biasharabridges.com/equity/thanks?status=success&amount=...`).

**Embedded / Iframe Flow:**
Biashara can embed CODA's equity UI inside their site using an iframe or similar mechanism (e.g., `/embed/cap-table?company=biashara-bridges&deal={slug}`). This allows shareholders to feel they never left the Biashara environment, while logic and calculations still run on CODA. The embedded UI reads company theme settings and renders with Biashara's branding.

This integration pattern is conceptually similar to PayPal: the client website integrates with CODA, but CODA is the equity engine, not the payment processor. Payment execution, KYC/AML, and regulatory compliance remain with trusted payment providers.

### E.3 White-Label / Theming (Look & Feel Per Company)

To ensure companies like Biashara Bridges maintain their brand identity when using CODA's equity platform, the system supports company-specific theming. This can be implemented via a `CompanyTheme` model or by adding branding fields to the `Company` or `EquityDeal` model:

**Proposed Theme Configuration:**
- Logo URL (company logo for display on equity pages)
- Primary color (main brand color for headers, buttons)
- Secondary color (accent color for highlights)
- Optional: Typography preferences (font family, button styles)

All equity front-end templates will read theme settings and render with company-specific styling, so Biashara (or any company) still feels "inside their own site" regardless of whether CODA is rendered as a redirect page or embedded iframe. This white-label approach maintains brand consistency while leveraging CODA's equity calculation and audit capabilities.

### E.4 API Option (Server-to-Server)

In addition to hosted UI (redirect/embed), CODA may expose server-to-server REST APIs for advanced integrations:

**Example API Endpoints:**
- `POST /api/equity/deals/{deal_id}/contributions/cash/` - Client systems can push confirmed transactions (with provider reference, amount, currency) into CODA
- `GET /api/equity/deals/{deal_id}/cap-table/` - Returns latest snapshot: members, equity %, shares, votes, tier totals
- `GET /api/equity/deals/{deal_id}/members/{member_id}/contributions/` - Full breakdown of Cash/In-Kind/Time/Work for one member

In this model, payment execution and KYC/AML remain on the payment provider side; CODA stays focused on record-keeping and equity logic. Client systems authenticate via API keys or JWT tokens, and all requests are tenant-scoped by Company/Deal.

### E.5 Compliance & Risk Separation

Using external, trusted providers for monetary flows helps CODA minimize regulatory exposure. CODA focuses on transparent, auditable records for contributions and equity, while cash handling, KYC, and AML remain with providers already trusted by the public (PayPal, Stripe, M-Pesa, banks). This separation of concerns keeps CODA out of PCI-DSS scope (no card handling), reduces AML/KYC burden (rely on providers' compliance stacks), and allows CODA to focus on equity math and audit rather than banking regulation.

---

## F. Risk, Complexity & Phasing

### E.1 Technical Risk Assessment

**High Complexity Areas:**
1. **FX/history resolution** (Medium-High)
   - Need to handle pegged rate vs market rate
   - Weight history over time (Phase 2)
   - **Mitigation:** Start with simple pegged rate (Phase 1), add history in Phase 2

2. **Multiplier calculations** (Medium)
   - Time multipliers by month/phase
   - Role multipliers per member
   - **Mitigation:** Use JSONField for flexibility, validate in service layer

3. **Snapshot locking and dispute window** (Medium)
   - Prevent edits after lock
   - Handle regenerating snapshots within dispute window
   - **Mitigation:** Use boolean `is_locked`, check in views/services before edits

4. **Scoring engine normalization** (Medium)
   - Normalize across different units (USD, hours, points)
   - Ensure equity % sums to 100%
   - **Mitigation:** Use Decimal math, add validation tests

**High Coupling Areas:**
1. **Integration with Task/Time models** (Low-Medium for Phase 1, High for Phase 2)
   - Phase 1: Standalone `TimeContribution` model
   - Phase 2: Auto-import from `TaskHistory`
   - **Mitigation:** Start standalone, add integration later

2. **Integration with existing approval system** (Low)
   - Reuse patterns but keep separate (equity approvals are different from budget approvals)
   - **Mitigation:** Use similar patterns but separate models/services

**DB-Heavy Changes:**
- New models: ~8-10 new models (Deal, Config, 4 ledger models, Snapshot, SnapshotMember, AuditLog, DealMemberRole)
- Migrations: Will require migrations for all new models
- Indexes: Critical indexes on (deal, member, status), (deal, snapshot_date)

### E.2 Suggested Implementation Phases (Technical)

**Phase E1: Core Foundation (Weeks 1-2)**
- **Models:** `EquityDeal`, `DealConfig`, `DealMemberRole`
- **Services:** `EquityConfigService` (basic FX, weights, multipliers)
- **Views:** Deal CRUD, DealConfig form, Companies list view
- **Admin:** Register core models
- **Testing:** Unit tests for config service, deal creation
- **Multi-Company Support:** Design already supports multiple companies and deals. Biashara Bridges (13 stakeholders) is the first concrete use case, but the system is built to handle any number of companies.

**Deliverables:**
- Can create a deal with config for any company (e.g., Biashara Bridges)
- Can add members with roles (e.g., 13 stakeholders for Biashara Bridges)
- Can view deal details and company-level equity overview

**Phase E2: Cash & In-Kind Ledgers (Weeks 3-4)**
- **Models:** `CashContribution`, `InKindContribution`
- **Services:** `EquityLedgerService` (submit, approve, reject)
- **Views:** Ledger entry forms, approval dashboard
- **Integration:** FX conversion using `CurrencyConverter.get_exchange_rate()`
- **Testing:** Approval workflow, FX conversion
- **Multi-Company Support:** Each company's contributions are isolated by deal/organization FK.

**Deliverables:**
- Members can submit cash/in-kind contributions
- Finance can approve/reject
- USD conversion works (pegged rate)

**Phase E3: Time & Work Ledgers (Weeks 5-6)**
- **Models:** `TimeContribution`, `WorkContribution` (with optional `task` FK for Phase 2 integration)
- **Services:** Multiplier calculation (time by month, role by position)
- **Views:** Time/work entry forms, approval workflows
- **Testing:** Multiplier calculations, approval chains
- **Tasks Integration:** Time and Work ledgers are built with future Tasks integration in mind via the optional `task` FK field. Phase 1 uses standalone models; Phase 2 will add auto-import from Task/TaskHistory.

**Deliverables:**
- Members can submit time/work contributions (standalone entry)
- Multipliers apply correctly
- Approvals work for all ledger types
- Optional task FK field in place for future integration

**Phase E4: Scoring Engine & Snapshots (Weeks 7-8)**
- **Models:** `EquitySnapshot`, `EquitySnapshotMember`
- **Services:** `EquityScoringEngine`, `EquitySnapshotService`
- **Views:** Generate snapshot, snapshot detail (cap table)
- **Testing:** Scoring calculations (normalization, weighting, equity %), snapshot generation

**Deliverables:**
- Can generate snapshot for a deal
- Equity % calculates correctly (sums to 100%)
- Cap table displays correctly

**Phase E5: Shares, Votes, Locking (Weeks 9-10)**
- **Services:** Share/vote calculation, snapshot locking
- **Views:** Lock snapshot, dispute window handling
- **Testing:** Share calculations, locking enforcement

**Deliverables:**
- Shares and votes calculate correctly
- Snapshots can be locked
- Locked snapshots cannot be edited

**Phase E6: Exports & Reporting (Weeks 11-12)**
- **Services:** `EquityExportService`
- **Views:** Excel/PDF export endpoints
- **Testing:** Export formats, template alignment

**Deliverables:**
- Cap table exports to Excel
- Contribution reports export
- PDF summary available

**Phase E7: Audit & Polish (Week 13)**
- **Models:** `EquityAuditLog` (if not done earlier)
- **Services:** `EquityAuditService`
- **Views:** Audit log view
- **Testing:** Audit logging, soft delete

**Deliverables:**
- All actions logged
- Audit trail visible
- Soft delete works

**Future Enhancements (Beyond Phase E7):**
- **Phase E8: Deep Task/TaskHistory Integration (Optional)**
  - Standardize mappings from Task fields (effort, status, type) to equity Work/Time scoring
  - Batch ingestion or background jobs that read TaskHistory and create/update TimeContribution/WorkContribution entries
  - Configurable mappings between Task types and equity impact tiers
  - Auto-link existing Task records to equity contributions

**Note:** Phases can overlap (e.g., start Phase E4 while Phase E3 is being tested). The design already supports multiple companies and deals from Phase E1, with Biashara Bridges serving as the first concrete use case.

### E.3 Alignment with Existing Master Architecture

**Service-Oriented Architecture:**
- Equity module follows same pattern as `PayCalculationService`, `CreditScoringService`
- Services in `finance/services/equity/`
- Models in `finance/models/equity.py` (or separate file per model group)

**Shared Utilities:**
- **FX:** Reuse `CurrencyConverter.get_exchange_rate()` from `finance/utils/currency_converter.py`
- **Base Models:** Use `TimeStampedModel` from `shared_core.models` (StatusMixin not used for equity models due to domain-specific status workflow)
- **User Model:** Use `CustomerUser` via `settings.AUTH_USER_MODEL` (maps to `accounts.CustomerUser`)

**Patterns to Consolidate (Future):**
- Consider generic `SnapshotService` base class (if other modules need snapshots)
- Consider generic `ApprovalService` base class (if approval patterns converge)
- Consider generic `ExportService` base class (if export patterns converge)

**Integration Points:**
- **Task/Time:** Phase 2 integration to auto-import from `TaskHistory`
- **Work:** Phase 2 integration to auto-import from `Task`
- **Permissions:** Reuse existing permission patterns (is_staff, is_superuser, custom permissions)

---

## G. Summary of Decisions

### F.1 Model Decisions

| Entity | Decision | Rationale |
|--------|----------|-----------|
| Organization | Reuse `Company` model | Already exists, sufficient for Phase 1 |
| Member | Use `CustomerUser` FK | All members are users in Phase 1 |
| Deal | Create `EquityDeal` model | New entity, no equivalent exists |
| Role | Create `DealMemberRole` model | Deal-specific roles needed |
| Config | Create `DealConfig` model | Per-deal config needed (FX, weights, multipliers) |
| Cash Ledger | Create `CashContribution` model | Structured for equity, not general transactions |
| In-Kind Ledger | Create `InKindContribution` model | New entity |
| Time Ledger | Create `TimeContribution` model | Standalone for Phase 1, integrate with TaskHistory in Phase 2 |
| Work Ledger | Create `WorkContribution` model | Standalone for Phase 1, integrate with Task in Phase 2 |
| Snapshot | Create `EquitySnapshot` + `EquitySnapshotMember` | Follows TaskHistory pattern |
| Audit | Create `EquityAuditLog` model | Generic FK to any equity model |

### F.2 Service Decisions

| Service | Location | Reuse |
|---------|----------|-------|
| `EquityConfigService` | `finance/services/equity/equity_config_service.py` | `CurrencyConverter.get_exchange_rate()` |
| `EquityLedgerService` | `finance/services/equity/equity_ledger_service.py` | Approval patterns from `BudgetRequest` |
| `EquityScoringEngine` | `finance/services/equity/equity_scoring_engine.py` | Aggregation patterns from TaskHistory queries |
| `EquitySnapshotService` | `finance/services/equity/snapshot_service.py` | Snapshot pattern from `TaskHistory` |
| `EquityExportService` | `finance/services/equity/export_service.py` | CSV export patterns, Excel/PDF if available |
| `EquityAuditService` | `finance/services/equity/audit_service.py` | New, but follows logging patterns |

### F.3 App Location Decision

**Decision:** Implement equity module inside the existing `coda/finance/` app

**Rationale:**
- Monetary domain alignment
- Existing patterns (config, approvals, FX, scoring, exports)
- Service-oriented architecture already established
- Can share entire `finance/` app with external developers if needed
- Equity organized as well-structured sub-modules within finance: `finance/models/equity.py`, `finance/services/equity/`, `finance/views/equity/`

---

## H. Open Questions for Discussion

1. **Member Model:** Should we support non-user entities (companies, trusts) in Phase 1, or defer to Phase 2?
2. **Time/Work Integration:** Should we auto-import from Task/TaskHistory in Phase 1, or start standalone?
3. **Export Format:** Excel (openpyxl) or CSV? PDF (reportlab/weasyprint) or HTML-to-PDF?
4. **Dispute Window:** Should dispute window be configurable per deal, or fixed at 7 days?
5. **Weight History:** Should we support weight changes over time in Phase 1, or defer to Phase 2?
6. **Share Price Model:** Business rules for share price model need clarification (how is total deal value calculated?)

---

## I. Next Steps

1. **Review this analysis** with stakeholders
2. **Clarify open questions** (Section H)
3. **Finalize model designs** (adjust based on feedback)
4. **Create implementation plan** (detailed task breakdown per phase)
5. **Begin Phase E1** (Core Foundation)

---

**Document Status:** ✅ Complete - Ready for Review  
**Next Update:** After stakeholder review and open questions resolved

---

## J. Modularity & Third-Party Implementation Strategy

### I.1 Historical Modularity Problem

CODA's Django monolith has historically suffered from tight coupling between apps, making it difficult to share individual apps with external developers. The `management` app, for example, originally depended heavily on `finance`, `ai_services`, and `professional_services`, making it impossible to share `management` without exposing large portions of the monolith.

**The Problem:**
- Apps directly imported models and services from other apps
- No abstraction layer for cross-app communication
- Circular dependencies (e.g., `main` depends on `management`, `management` depends on `main`)
- Infrastructure code (base models, utilities) scattered across `main` and `accounts`

**The Solution (Partial):**
CODA created `shared_core` to address this by:
- Re-exporting base models (`TimeStampedModel`, `StatusMixin`, `Company`) from `main.models`
- Re-exporting user models (`CustomerUser`, `Department`) from `accounts.models`
- Re-exporting utilities, mixins, and filters
- Providing interfaces for cross-app services (e.g., `AIServiceInterface`, `FinanceTaskServiceInterface`)

**Remaining Challenges:**
- `finance` and `management` still have bidirectional dependencies
- Domain-specific utilities (e.g., `CurrencyConverter`) remain in app-specific locations
- No generic abstraction for Task/Work/Time data that equity needs
- Approval and config patterns are app-specific, not shared

### I.2 Current Django App Dependency Graph

Based on codebase analysis, the following dependency map shows cross-app imports:

#### Dependency Adjacency List

| App | Depends On | Dependency Type | Notes |
|-----|------------|-----------------|-------|
| **accounts** | `management`, `finance`, `ai_services` | Direct imports | Uses `Task` from management, `Payment_History` from finance, `TokenEncryptionService` from ai_services |
| **finance** | `shared_core`, `accounts` (via shared_core), `management` (optional) | Direct + optional | Uses `EmployeeComplianceService` from management (optional), `Task`/`TaskHistory` in some views |
| **management** | `shared_core`, `finance`, `ai_services`, `professional_services`, `accounts` | Direct + interface-based | Heavy dependencies on finance (via interfaces), ai_services (via interfaces), professional_services (direct) |
| **main** | `professional_services`, `investing`, `management`, `finance`, `ai_services`, `unified_dashboard` | Direct imports | Core app with many dependencies, creates circular concerns |
| **investing** | `shared_core`, `finance` (optional), `ai_services` (optional) | Optional with try/except | Well-isolated, uses shared_core, optional dependencies handled gracefully |
| **ai_services** | `shared_core`, `accounts` (via shared_core) | Minimal | Relatively isolated |
| **professional_services** | `shared_core` | Minimal | Relatively isolated |
| **shared_core** | `main.models`, `accounts.models` | Re-exports only | Infrastructure layer, no business logic dependencies |

#### Dependency Commentary

**Acceptable Dependencies:**
- ✅ **shared_core** → `main.models`, `accounts.models` (re-exports only, no business logic)
- ✅ **investing** → `shared_core` + optional `finance`/`ai_services` (graceful degradation)
- ✅ **ai_services** → `shared_core` (minimal coupling)

**Problematic Dependencies:**
- ❌ **management** → `finance`, `ai_services`, `professional_services` (heavy coupling, though partially mitigated by interfaces)
- ❌ **finance** → `management` (bidirectional dependency)
- ❌ **main** → multiple apps (circular dependency risks)
- ❌ **accounts** → `management`, `finance` (should be more isolated)

### I.3 Equity Module Location Decision

**Decision: Implement equity module inside the existing `finance` app**

**Rationale:**
1. **Shared App Context:** We are comfortable sharing the entire `coda/finance/` app with an external developer if needed. This provides a natural boundary for the equity module implementation.
2. **Internal Modularity:** While equity lives inside finance, it will be organized as a well-structured sub-module with clear separation:
   - `finance/models/equity.py` - Equity models
   - `finance/services/equity/` - Equity services directory
   - `finance/views/equity/` - Equity views directory
   - `finance/templates/finance/equity/` - Equity templates
3. **Direct Access to Finance Utilities:** Equity can directly use finance utilities like `CurrencyConverter` without needing to move them to `shared_core` first.
4. **Pattern Reuse:** Equity can directly reference and reuse existing finance patterns (approvals, configs, exports) within the same app.
5. **Simplified Structure:** Fewer Django apps to manage, while maintaining internal code organization.

**Target Structure:**
```
coda/finance/
├── models/
│   ├── equity.py                    # EquityDeal, DealConfig, DealMemberRole
│   ├── equity_ledgers.py           # CashContribution, InKindContribution, TimeContribution, WorkContribution
│   ├── equity_snapshot.py          # EquitySnapshot, EquitySnapshotMember
│   ├── equity_audit.py             # EquityAuditLog
│   └── ... (existing finance models)
├── services/
│   ├── equity/
│   │   ├── __init__.py
│   │   ├── equity_config_service.py    # FX, weights, multipliers resolution
│   │   ├── equity_ledger_service.py    # Ledger CRUD and approvals
│   │   ├── equity_scoring_engine.py    # 4-tier scoring logic
│   │   ├── equity_snapshot_service.py  # Generate/lock snapshots
│   │   └── equity_export_service.py    # Cap table Excel/PDF exports
│   └── ... (existing finance services)
├── views/
│   ├── equity/
│   │   ├── __init__.py
│   │   ├── deal_views.py           # Deal setup, list, detail
│   │   ├── ledger_views.py         # Ledger entry forms, list
│   │   ├── snapshot_views.py       # Snapshot generation, cap table view
│   │   └── export_views.py         # Export endpoints
│   └── ... (existing finance views)
├── templates/
│   └── finance/
│       └── equity/
│           ├── deal_setup.html
│           ├── ledger_entry.html
│           ├── cap_table.html
│           └── ...
└── urls.py                          # Add equity URL patterns
```

**Dependency Strategy:**
- ✅ Equity code **CAN** depend on: `shared_core.models`, `shared_core.users`, `finance.utils.currency_converter`, other internal `finance` services/utilities that do not import from `management`
- ❌ Equity code **SHOULD AVOID** depending directly on `management` models (especially `Task`/`TaskHistory`) in Phase 1
- ⏳ Time/Work → Task integration remains a Phase 2 enhancement via an adapter service or interface
- **Note:** Equity code adheres to the dependency guardrails defined in Section J to ensure external developers can work safely inside the finance app without needing to understand management's internal task/compliance logic.

### I.4 Required Refactoring: Dependencies and Shared Interfaces

Since equity will be implemented inside the `finance` app, and we are comfortable sharing the entire `finance` app with external developers, the dependency strategy is simplified. However, we still want equity code to avoid unnecessary dependencies on other apps (especially `management`). The following guidance applies:

#### Dependencies Equity Can Use Directly (Inside Finance App)

1. **FX / Currency Conversion Utilities**
   - **Location:** `finance.utils.currency_converter.CurrencyConverter`
   - **Usage:** Equity can import directly: `from finance.utils.currency_converter import CurrencyConverter`
   - **Rationale:** Since equity is inside the finance app, it has direct access to finance utilities. No refactoring needed. This is a pure utility with no external dependencies beyond Django and standard libraries.

2. **Finance Approval Patterns**
   - **Location:** `finance.models.budget.ApprovalPolicy`, `finance.services.automation_service.ApprovalEngineService`
   - **Usage:** Equity can reference these patterns and implement similar approval workflows for equity-specific models
   - **Rationale:** Equity can reuse approval patterns directly within the finance app. No need to abstract to shared_core. Note: Check that these services do not import from `management` before using them.

3. **Company Model Access**
   - **Current Location:** `main.models.Company` (re-exported via `shared_core.models`)
   - **Status:** ✅ Already in `shared_core.models` as `Company`
   - **Action:** None needed - equity can use `from shared_core.models import Company`

4. **User Model Access**
   - **Current Location:** `accounts.models.CustomerUser` (re-exported via `shared_core.users`)
   - **Status:** ✅ Already in `shared_core.users` as `CustomerUser`
   - **Action:** None needed - equity should use `settings.AUTH_USER_MODEL` or `from shared_core.users import CustomerUser`

#### Dependencies Equity Should Avoid (Phase 1)

5. **Task / Work / Time Summary Interface (Phase 2 Enhancement)**
   - **Current Location:** `management.models.Task`, `management.models.TaskHistory`
   - **Strategy:** In Phase 1, equity Time and Work ledgers will be standalone with optional FK to `management.Task`. 
   - **Future Enhancement (Phase 2):** Consider creating a `shared_core.tasks.task_summary` interface if Task integration becomes critical, but this is not required for Phase 1.
   - **Rationale:** Equity should avoid direct imports from `management` models in Phase 1 to maintain modularity. Time/Work ledger entries can be manually entered or imported later.

#### Shared Infrastructure (Already Available)

6. **Base Model Mixins**
   - **Current Location:** `main.models` (re-exported via `shared_core.models`)
   - **Status:** ✅ Already available (`TimeStampedModel`, `StatusMixin`, `UserReferenceMixin`, `DocumentMixin`, `ContractBase`)
   - **Action:** None needed - equity can use these from `shared_core.models`

#### Implementation Checklist for Equity Module

**Before Equity Implementation:**
- [x] Verify `Company` and `CustomerUser` are accessible via `shared_core` (already done)
- [ ] Create directory structure: `finance/models/equity.py`, `finance/services/equity/`, `finance/views/equity/`, `finance/templates/finance/equity/`
- [ ] Review finance approval patterns for reuse in equity workflows

**During Equity Implementation (Phase 1):**
- [ ] Implement equity models in `finance/models/equity.py` using `shared_core.models` for base mixins
- [ ] Implement equity services using `finance.utils.currency_converter` directly (no refactoring needed)
- [ ] Implement equity views following finance app patterns
- [ ] **Avoid** direct imports from `management.models` (use optional FK to Task for future integration)
- [ ] Ensure Time and Work ledgers can function standalone (manual entry or future import)

**Future Enhancements (Phase 2+):**
- [ ] Consider Task integration via adapter service if needed (optional, not required for Phase 1)
- [ ] Evaluate if any equity patterns should be extracted to `shared_core` for reuse elsewhere (unlikely, but possible)

### I.5 External Developer Boundary Definition

**Target App Boundary:**
Share the entire `coda/finance/` app with the external developer. The equity module will be implemented as a sub-module within finance.

**What the External Developer Receives:**
- **Working Area:** `coda/finance/` (entire finance app)
- **Equity Code Location:** 
  - Models: `finance/models/equity.py`
  - Services: `finance/services/equity/`
  - Views: `finance/views/equity/`
  - Templates: `finance/templates/finance/equity/`

**Dependencies Equity Code Can Use:**
- ✅ `shared_core.models` (Company, base mixins)
- ✅ `shared_core.users` (CustomerUser)
- ✅ `finance.utils.currency_converter.CurrencyConverter` (direct access, same app)
- ✅ Other `finance` services, utilities, and patterns (direct access, same app)
- ✅ `settings.AUTH_USER_MODEL`

**Stable Contracts (What External Developer Can Rely On):**

1. **Company Model** (`shared_core.models.Company`)
   - Fields: `name`, `slug`, `sector`, `mission`, `website`, `location`, `user`, `description`, `relation`
   - Behavior: Standard Django model, `TimeStampedModel` mixin
   - Usage: `organization = models.ForeignKey('shared_core.Company', ...)`

2. **User Model** (`settings.AUTH_USER_MODEL` or `shared_core.users.CustomerUser`)
   - Fields: Standard Django user fields + `category`, `department`, etc.
   - Behavior: Standard Django user model
   - Usage: `member = models.ForeignKey(settings.AUTH_USER_MODEL, ...)`

3. **FX Helper** (`shared_core.fx.currency_converter.CurrencyConverter`)
   - Interface:
     ```python
     converter = CurrencyConverter()
     rate = converter.get_exchange_rate('KES', 'USD')
     usd_amount = converter.convert_to_usd(Decimal('1000'), 'KES')
     ```

4. **Base Model Mixins** (`shared_core.models`)
   - `TimeStampedModel`: Provides `created_at`, `updated_at`, `is_active`, `is_featured`
   - `StatusMixin`: Provides status field (if needed, though equity uses domain-specific status)
   - `UserReferenceMixin`: Provides `user` FK
   - `DocumentMixin`: Provides document storage fields
   - `ContractBase`: Provides contract-related fields

5. **Task Summary Interface** (Phase 2, optional)
   - Interface: `shared_core.tasks.task_summary.TaskSummaryService`
   - Usage: Query task effort without importing management models

**What Equity Code Should Avoid:**

- ❌ **Direct management imports:** `management.models.Task`, `management.models.TaskHistory` (in Phase 1 - use optional FK for future integration)
- ❌ **Other app dependencies:** Avoid importing from `ai_services`, `professional_services`, `investing`, etc. unless absolutely necessary
- ⚠️ **Finance models:** Equity can reference other finance models for patterns/inspiration, but should maintain clear separation (equity models are distinct from Payment, Transaction, etc.)

**Permissions / Groups / Feature Flags:**

Equity can use Django's built-in permission system without breaking modularity:
- Django groups: `equity_system_admin`, `equity_finance`, `equity_admin_pm`, `equity_department_lead`, `equity_member`, `equity_auditor`
- Model permissions: `can_approve_equity_cash`, `can_view_equity_snapshots`, etc.
- Enforcement: Via decorators/mixins in equity views/services (no dependencies on other apps like management)

### I.6 Implementation Strategy Summary

**Phase 1: Setup (CODA Team)**
1. Create equity module directory structure within `finance/` app
2. Set up initial models file (`finance/models/equity.py`) with imports from `shared_core`
3. Create equity services directory (`finance/services/equity/`)
4. Create equity views directory (`finance/views/equity/`)
5. Create equity templates directory (`finance/templates/finance/equity/`)

**Phase 2: Equity Implementation (External Developer)**
1. Implement equity models in `finance/models/equity.py`:
   - Use `shared_core.models.Company` for organization references
   - Use `settings.AUTH_USER_MODEL` for member references
   - Use `shared_core.models` base mixins (TimeStampedModel, etc.)
2. Implement equity services in `finance/services/equity/`:
   - Use `finance.utils.currency_converter.CurrencyConverter` directly (same app)
   - Reference finance approval patterns for equity approval workflows
   - Implement scoring, snapshot, and export services
3. Implement equity views in `finance/views/equity/`:
   - Follow finance app view patterns
   - Use finance templates structure
4. **Avoid** direct imports from `management.models` in Phase 1
5. Ensure Time/Work ledgers work standalone (optional FK to Task for future)

**Phase 3: Optional Integration (Future)**
1. If Task integration needed: Consider adapter service or interface (not required for Phase 1)
2. Evaluate if equity patterns should be extracted (unlikely, but possible)

**Success Criteria:**
- ✅ External developer can implement equity module within `finance/` app structure
- ✅ Equity code uses `shared_core` for base models and user models
- ✅ Equity code uses `finance.utils.currency_converter` directly (same app)
- ✅ Equity code avoids direct imports from `management` models in Phase 1
- ✅ Equity functionality works within the finance app context
- ✅ All equity code is well-organized in sub-modules within finance

---

## K. Finance App Dependency Analysis & Equity Guardrails

This section provides a detailed analysis of the `finance` app's external dependencies and establishes explicit guardrails for the equity module to ensure it can be safely implemented by external developers without requiring deep knowledge of the management app or other tightly coupled components.

### J.1 Overview of Finance App Dependencies

The `finance` app has **moderate coupling** to other CODA apps. The following table classifies external dependencies by risk level:

| External App | Risk Level | Dependency Count | Primary Use Cases |
|--------------|------------|-------------------|-------------------|
| **shared_core** | ✅ **LOW** | ~40+ files | Infrastructure: base models (Company, TimeStampedModel), user models (CustomerUser, Department), utilities, mixins |
| **management** | ❌ **HIGH** | ~14 files | Business logic: Task/TaskHistory tracking, employee compliance (33% rule), salary calculations, budget integrations |
| **main** | ⚠️ **MEDIUM** | ~5 files | Service definitions (Service, ServiceCategory), some Company references (should use shared_core) |
| **investing** | ✅ **LOW** | ~2 files | Optional: investment data and calculations (graceful degradation with try/except) |
| **ai_services** | ✅ **LOW** | ~3 files | Optional: AI-powered features (budget suggestions, data correction) |

**Key Finding:** Approximately **14 files** in `finance` import from `management`, creating a dependency that would require external developers to understand the management app's structure. However, these dependencies are **concentrated in specific services and views** (compliance services, salary dashboards, budget integrations) that the equity module will deliberately avoid.

### J.2 High-Risk Management Dependencies

The `management` app dependencies in `finance` represent the highest risk for modularity. These dependencies are found in:

**Services with High Coupling:**
- `services/realtime_compliance_service.py` - Full dependency on TaskHistory, Task, EmployeeComplianceService
- `services/integrated_budget_service.py` - Full dependency on TaskHistory, Task, calculate_total_pay
- `services/admin_controls_service.py` - Full dependency on TaskHistory, Task, EmployeeComplianceService
- `services/enhanced_budget_service.py` - Uses EmployeeComplianceService
- `services/management_integration_service.py` - Calls management views/APIs
- `services/financial_analytics_service.py` - Uses management models (likely should use shared_core)

**Views with Medium Coupling:**
- Budget views that use `EmployeeComplianceService` (salary dashboard, realtime compliance, enhanced approvals, admin controls)
- Legacy views that reference Task/Meeting models

**Utils:**
- `utils.py` - Uses TaskHistory and management salary calculation utilities

**Risk Assessment:** These services and views require understanding:
- Management's task system (Task, TaskHistory models)
- Employee compliance rules (33% compliance threshold)
- Salary calculation logic (calculate_total_pay, emp_average_earnings)
- Budget-salary integration patterns

**Equity Module Strategy:** The equity module will **not** depend on these management-dependent services in Phase 1. Equity code will be implemented in isolated sub-modules that avoid any imports from `management.*`.

### J.3 Safe Neighborhoods for Equity Inside Finance

The equity module will be implemented in clearly defined sub-modules within the `finance` app that avoid management dependencies:

**Equity Module Structure:**
```
coda/finance/
├── models/
│   └── equity.py                    # Equity models (isolated)
├── services/
│   └── equity/                      # Equity services (isolated)
│       ├── equity_config_service.py
│       ├── equity_scoring_engine.py
│       ├── equity_snapshot_service.py
│       └── equity_export_service.py
├── views/
│   └── equity/                      # Equity views (isolated)
│       ├── deal_views.py
│       ├── ledger_views.py
│       └── snapshot_views.py
└── templates/
    └── finance/
        └── equity/                  # Equity templates (isolated)
```

**Allowed Dependencies for Equity Sub-Modules:**
- **Django Core:** Standard Django ORM, views, forms, utilities
- **shared_core.models:** Company, TimeStampedModel, StatusMixin, and other base mixins
- **shared_core.users:** CustomerUser, Department (via `settings.AUTH_USER_MODEL` or direct import)
- **finance.utils.currency_converter:** CurrencyConverter class for FX conversion (same app, no external dependencies)
- **Other finance utilities:** Any `finance.utils.*` or `finance.utilities.*` that do not import from `management`
- **Equity models/services/views:** Internal equity code can reference other equity components

**Safety Guarantee:** This design makes it safe to hand an external developer the entire `finance` app, with clear instructions to work only within the equity sub-modules (`models/equity.py`, `services/equity/`, `views/equity/`, `templates/finance/equity/`). The external developer does not need to understand management's task system, compliance rules, or salary calculations to implement equity functionality.

**Note:** Equity code adheres to the dependency guardrails defined in this section (J.4) to ensure external developers can work safely inside the finance app without needing to understand management's internal task/compliance logic.

### J.4 Allowed vs Forbidden Dependencies for Equity

This section defines the explicit "contract" for equity module dependencies. All equity code (models, services, views) must follow these rules:

**✅ ALLOWED Dependencies (Phase 1):**

- **Django Core:**
  - `django.db.models`, `django.contrib.auth`, `django.utils`, `django.core.exceptions`, etc.

- **Shared Core:**
  - `shared_core.models` (Company, TimeStampedModel, StatusMixin, UserReferenceMixin, DocumentMixin, ContractBase)
  - `shared_core.users` (CustomerUser, Department, UserCategory)
  - `shared_core.utils` (if needed: path_values, dates_functionality, date_converter)
  - `shared_core.mixins` (FilteredListViewMixin, etc.)
  - `shared_core.filters` (if needed)

- **Settings:**
  - `settings.AUTH_USER_MODEL` (canonical way to reference CustomerUser)

- **Finance Utilities (Same App):**
  - `finance.utils.currency_converter.CurrencyConverter` (pure utility, no external dependencies)
  - Other `finance.utils.*` utilities that do not import from `management`
  - `finance.utilities.*` utilities that do not import from `management`

- **Finance Models (Same App, Check Dependencies):**
  - `finance.models.budget.ApprovalPolicy` (for pattern reference, check for management deps)
  - Other finance models that do not import from `management`

- **Equity Internal:**
  - Equity models can reference other equity models
  - Equity services can reference equity models and other equity services
  - Equity views can reference equity models, services, and other equity views

**❌ FORBIDDEN Dependencies (Phase 1):**

- **Management App (High Risk):**
  - `management.models.*` (Task, TaskHistory, Requirement, Meeting, etc.)
  - `management.utils.*` (calculate_total_pay, paytime, emp_average_earnings, etc.)
  - `management.services.*` (EmployeeComplianceService, etc.)
  - `management.views.*` (any management views)

- **Main App (Medium Risk):**
  - `main.models.*` (Service, ServiceCategory, Pricing)
  - `main.models.Company` (use `shared_core.models.Company` instead)
  - `main.utils.*` (PayChoices, etc.)

- **Management-Dependent Finance Services:**
  - `finance.services.realtime_compliance_service.RealtimeComplianceService`
  - `finance.services.integrated_budget_service.IntegratedBudgetService`
  - `finance.services.admin_controls_service.AdminControlsService`
  - `finance.services.enhanced_budget_service.EnhancedBudgetService`
  - `finance.services.management_integration_service.ManagementIntegrationService`

- **Management-Dependent Finance Views:**
  - Views in `finance/views/budget/` that import `EmployeeComplianceService`
  - `finance/views/legacy/views_unified_department.py`

**⏳ FUTURE Integration (Phase 2+):**

- **Task Integration (Optional):**
  - If equity Time/Work ledgers need to integrate with `management.Task`/`TaskHistory`:
    - Create adapter service: `finance/services/equity/task_adapter.py`
    - Use thin interface, not direct imports
    - Mark clearly as Phase 2 enhancement with `# PHASE 2: Task Integration` comment

### J.5 External Developer Boundary

**Working Area:** External developers will receive the entire `coda/finance/` app as their working area.

**✅ What External Developers CAN Safely Work On:**

- **All Equity Module Code:**
  - `finance/models/equity.py` - All equity model definitions
  - `finance/services/equity/*.py` - All equity services (scoring, config, snapshot, export)
  - `finance/views/equity/*.py` - All equity views (deal setup, ledger entry, cap table, exports)
  - `finance/templates/finance/equity/*.html` - All equity templates

- **Finance Utilities (Non-Management-Dependent):**
  - `finance/utils/currency_converter.py` - CurrencyConverter class
  - Other `finance/utils.*` utilities that do not import from `management`
  - `finance.utilities.*` utilities that do not import from `management`

- **Finance Models (Check Individual Files):**
  - Most finance models (budget, payment, loan) - check individual files for management imports
  - Finance models can be referenced for pattern inspiration, but equity should implement its own models

**❌ What External Developers Should NOT Touch:**

- **Management-Dependent Services:**
  - `finance/services/realtime_compliance_service.py`
  - `finance/services/integrated_budget_service.py`
  - `finance/services/admin_controls_service.py`
  - `finance/services/enhanced_budget_service.py`
  - `finance/services/management_integration_service.py`

- **Management-Dependent Views:**
  - `finance/views/budget/views_salary_dashboard.py`
  - `finance/views/budget/views_realtime_compliance.py`
  - `finance/views/budget/views_enhanced_approvals.py`
  - `finance/views/budget/views_admin_controls.py`
  - `finance/views/legacy/views_unified_department.py`

**Required Knowledge for External Developers:**

- **Django Fundamentals:**
  - Django ORM and model definitions
  - Django views (class-based and function-based)
  - Django forms and form handling
  - Django templates and template tags

- **CODA Shared Infrastructure:**
  - `shared_core.models` (Company, base mixins: TimeStampedModel, StatusMixin, etc.)
  - `shared_core.users` (CustomerUser, Department)
  - `settings.AUTH_USER_MODEL` pattern

- **Finance App Patterns:**
  - `finance.utils.currency_converter.CurrencyConverter` usage
  - Finance approval patterns (reference `ApprovalPolicy` for inspiration, but implement equity-specific logic)
  - Finance config patterns (reference `PayslipConfig` for inspiration)
  - Finance export patterns (CSV/Excel exports)

**NOT Required Knowledge:**

- **Management App:**
  - Management's task system (Task, TaskHistory models)
  - Management's compliance rules (33% compliance threshold)
  - Management's salary calculation logic
  - Management's budget integration APIs

- **Main App:**
  - Main app's service definitions
  - Main app's internal utilities

**Conclusion:** External developers can safely implement the equity module within the finance app, working exclusively in the equity sub-modules and using only the allowed dependencies listed above. They do **not** need to understand the management app's task system or compliance logic to implement equity functionality.

---

**Document Status:** ✅ Complete - Includes Modularity Strategy & Finance Dependency Analysis  
**Next Update:** After stakeholder review and refactoring completion
