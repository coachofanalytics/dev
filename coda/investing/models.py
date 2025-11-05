from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.core.exceptions import ValidationError
from decimal import *
from django.utils import timezone
from datetime import datetime, date, timedelta
from django.urls import reverse
from main.models import TimeStampedModel, ContractBase, DocumentMixin, StatusMixin
from django.contrib.auth import get_user_model

# from finance.utils import get_exchange_rate
User = get_user_model()

# Create your models here.


# ============================================================================
# FEE TIER CONFIGURATION (Admin-editable)
# ============================================================================

class FeeTierConfiguration(TimeStampedModel):
    """
    Admin-editable configuration for managed trading fee tiers
    Allows staff to update minimums, fees, descriptions without code changes
    """
    
    TIER_CHOICES = [
        ('starter', 'Starter'),
        ('professional', 'Professional'),
        ('premium', 'Premium'),
        ('consultative', 'Consultative'),
        ('co_invest', 'Co-Invest'),
    ]
    
    tier_code = models.CharField(
        max_length=20,
        choices=TIER_CHOICES,
        unique=True,
        help_text="Internal tier code"
    )
    tier_name = models.CharField(
        max_length=100,
        help_text="Display name (e.g., 'Starter - AI Powered')"
    )
    minimum_capital = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Minimum capital required for this tier"
    )
    monthly_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Fixed monthly fee (set to 0 if none)"
    )
    per_session_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Fee per session (for consultative tier)"
    )
    profit_share_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Percentage of profits shared (e.g., 10 for 10%)"
    )
    max_sessions_per_month = models.IntegerField(
        default=0,
        help_text="Maximum sessions per month (0 if unlimited)"
    )
    short_description = models.CharField(
        max_length=200,
        help_text="Brief description for tier card"
    )
    
    # Features description (for display)
    features = models.JSONField(
        default=list,
        help_text="List of features (e.g., ['AI-driven trades', 'Real-time monitoring'])"
    )
    compatible_risk_levels = models.JSONField(
        default=list,
        help_text="Risk levels this tier is suitable for (e.g., ['low', 'medium'])"
    )
    
    # Display order
    display_order = models.IntegerField(
        default=0,
        help_text="Order to display on forms (lower = first)"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Is this tier currently available?"
    )
    
    class Meta:
        verbose_name = "Fee Tier Configuration"
        verbose_name_plural = "Fee Tier Configurations"
        ordering = ['display_order', 'minimum_capital']
    
    def __str__(self):
        return f"{self.tier_name} (${self.minimum_capital:,.0f}+)"
    
    def get_fee_display(self):
        """Return formatted fee string for display"""
        parts = []
        if self.monthly_fee > 0:
            parts.append(f"${self.monthly_fee:.0f}/month")
        if self.per_session_fee > 0:
            parts.append(f"${self.per_session_fee:.0f}/session")
        if self.profit_share_percentage > 0:
            parts.append(f"{self.profit_share_percentage:.0f}% profit")
        return " + ".join(parts) if parts else "Custom"
    
    def get_features_list(self):
        """Return features as a list"""
        # Handle both list (JSONField) and string (TextField) formats
        if isinstance(self.features, list):
            return self.features
        elif isinstance(self.features, str):
            return [f.strip() for f in self.features.split(',') if f.strip()]
        return []


class Investor_Information(ContractBase, DocumentMixin, StatusMixin):
    """
    Unified model for all investor types in CODA
    Supports Individual, Angel, VC, Private, and Equity investors
    """

    MODEL_CHOICES = [
        ("Revenue", "Revenue"),
        ("Installment", "Installment"),
        ("Options", "Options"),
    ]

    # STATUS_CHOICES now inherited from StatusMixin

    # Enhanced investment type choices for all investor types
    INVESTMENT_TYPE_CHOICES = [
        ("equity", "Equity Investment"),
        ("revenue_share", "Revenue Share"),
        ("convertible_note", "Convertible Note"),
        ("loan", "Convertible Loan"),
        ("installment", "Installment"),
        ("options", "Options"),
        ("angel_investment", "Angel Investment"),
        ("vc_investment", "VC Investment"),
        ("private_equity", "Private Equity"),
    ]

    investor = models.ForeignKey(
        User,
        limit_choices_to={"is_active": True},
        on_delete=models.CASCADE,
        related_name="investor_investments",
        null=True,
        blank=True,
    )
    total_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    investment_threshold = models.IntegerField(default=10)
    amount_invested = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("1000.00"))],  # Minimum $1,000
    )
    duration = models.PositiveIntegerField(blank=True, null=True)  # Duration in months
    revenue_share_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(Decimal("0.00")),
            MaxValueValidator(Decimal("50.00")),
        ],
    )

    # New fields from IndividualInvestment for enhanced functionality
    investment_type = models.CharField(
        max_length=20, choices=INVESTMENT_TYPE_CHOICES, default="equity"
    )
    investment_date = models.DateField(
        default=date.today
    )  # Enhanced from contract_date
    maturity_date = models.DateField(null=True, blank=True)

    # Financial tracking fields
    expected_return_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("8.00"),
        validators=[
            MinValueValidator(Decimal("0.00")),
            MaxValueValidator(Decimal("50.00")),
        ],
    )
    actual_return_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Actual return rate achieved",
    )
    current_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Current value of investment",
    )
    total_returns_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Total returns paid to investor",
    )
    # Transparency and reporting fields
    investment_purpose = models.TextField(
        help_text="What the investment is being used for"
    )
    quarterly_updates = models.BooleanField(
        default=True, help_text="Send quarterly investment updates"
    )
    monthly_reports = models.BooleanField(
        default=True, help_text="Send monthly performance reports"
    )

    # Existing fields (keep all)
    model_type = models.CharField(
        max_length=20, choices=MODEL_CHOICES, default="Installment"
    )
    beneficiary_name = models.CharField(max_length=50, blank=True, null=True)
    beneficiary_relation = models.CharField(max_length=50, blank=True, null=True)
    # contract_date, status, client_signature, contract_signed, contract_signed_date now inherited from ContractBase and StatusMixin
    contract_date = models.DateField(auto_now_add=True, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    # Phase 2: Risk Assessment Fields
    RISK_TOLERANCE_CHOICES = [
        ('conservative', 'Conservative'),
        ('moderate', 'Moderate'),
        ('aggressive', 'Aggressive'),
    ]
    
    risk_tolerance = models.CharField(
        max_length=20, 
        choices=RISK_TOLERANCE_CHOICES, 
        default='moderate',
        help_text="Investor's risk tolerance level"
    )
    
    # Phase 2: Compliance Tracking Fields
    KYC_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]
    
    kyc_status = models.CharField(
        max_length=20, 
        choices=KYC_STATUS_CHOICES, 
        default='pending',
        help_text="KYC verification status"
    )
    
    # documents, last_modified_by, modification_reason now inherited from DocumentMixin and StatusMixin

    class Meta:
        verbose_name_plural = "Investor Information"
        ordering = ["-investment_date"]  # Use investment_date instead of contract_date
        indexes = [
            models.Index(fields=["investor", "status"]),
            models.Index(fields=["investment_date"]),
            models.Index(fields=["status"]),
            models.Index(fields=["investment_type"]),
        ]

    @property
    def protected_amount(self):
        return round(self.amount_invested * Decimal("0.70"), 2)

    @property
    def number_positions(self):
        return round((self.amount_invested * Decimal("0.30")) / Decimal("300"), 2)

    @property
    def monthly_payments(self):
        if self.total_amount and self.duration:
            return round(self.total_amount / self.duration, 2)
        return 0

    def save(self, *args, **kwargs):
        if not self.total_amount:
            interest_rate = self.revenue_share_percentage or Decimal("0.05")
            self.total_amount = self.amount_invested + (
                self.amount_invested * interest_rate
            )
        super().save(*args, **kwargs)

    def clean(self):
        if self.duration and self.duration < 6:
            raise ValidationError("Duration must be at least 6 months.")
        if self.amount_invested <= 0:
            raise ValidationError("Amount invested must be greater than zero.")
        
        # Phase 2: Enhanced validation
        # Validate risk tolerance
        if self.risk_tolerance not in [choice[0] for choice in self.RISK_TOLERANCE_CHOICES]:
            raise ValidationError(f"Invalid risk tolerance: {self.risk_tolerance}")
        
        # Validate KYC status
        if self.kyc_status not in [choice[0] for choice in self.KYC_STATUS_CHOICES]:
            raise ValidationError(f"Invalid KYC status: {self.kyc_status}")
        
        # Validate risk tolerance vs amount (conservative investors with large amounts need review)
        if (self.risk_tolerance == 'conservative' and 
            self.amount_invested and self.amount_invested > Decimal('50000.00')):
            # This is just a warning, not an error
            pass
    
    def get_risk_level(self):
        """Calculate overall risk level based on multiple factors"""
        risk_score = 0
        
        # Base risk from tolerance
        risk_tolerance_scores = {
            'conservative': 1,
            'moderate': 2,
            'aggressive': 3
        }
        risk_score += risk_tolerance_scores.get(self.risk_tolerance, 2)
        
        # Adjust based on amount (larger amounts = higher risk)
        if self.amount_invested:
            if self.amount_invested > Decimal('100000.00'):
                risk_score += 2
            elif self.amount_invested > Decimal('50000.00'):
                risk_score += 1
        
        # Adjust based on investment type
        high_risk_types = ['options', 'vc_investment', 'private_equity']
        if self.investment_type in high_risk_types:
            risk_score += 1
        
        # Determine risk level
        if risk_score <= 2:
            return 'low'
        elif risk_score <= 4:
            return 'medium'
        else:
            return 'high'
    
    def is_compliance_complete(self):
        """Check if all compliance requirements are met"""
        return (
            self.kyc_status == 'verified' and
            len(self.documents) > 0 and
            self.contract_signed
        )
    
    def get_compliance_percentage(self):
        """Get compliance completion percentage"""
        total_requirements = 3
        completed = 0
        
        if self.kyc_status == 'verified':
            completed += 1
        if len(self.documents) > 0:
            completed += 1
        if self.contract_signed:
            completed += 1
        
        return (completed / total_requirements) * 100

    def __str__(self):
        return f"{self.investor.username if self.investor else 'No Investor'} - ${self.amount_invested} - {self.status}"


class Investment_rates(models.Model):
    TYPE_CHOICES = [
        ("investment", "Investment"),
        ("loan", "Loan"),
    ]

    TIER_CHOICES = [
        ("Tier 1", "Tier 1 ($1,000-$5,000)"),
        ("Tier 2", "Tier 2 ($5,001-$25,000)"),
        ("Tier 3", "Tier 3 ($25,001-$50,000)"),
    ]

    id = models.AutoField(primary_key=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="investment")
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_date = models.DateField(auto_now_add=True, blank=True, null=True)

    # Financial Details
    base_amount = models.PositiveIntegerField(blank=True, null=True)
    duration = models.PositiveIntegerField(blank=True, null=True)  # Duration in months
    rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.10
    )  # Unified rate field for both loans and investments

    # Loan-Specific Fields
    late_payment_penalty = models.DecimalField(
        max_digits=5, decimal_places=2, default=5.00
    )
    # min_credit_score = models.IntegerField(default=600)
    min_credit_score = models.DecimalField(
        max_digits=5, decimal_places=2, default=600.00
    )
    max_loan_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=50000.00
    )

    # Other Features
    equity_ownership = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True
    )
    share_price_min = models.DecimalField(max_digits=10, decimal_places=2, default=5.00)
    share_price_max = models.DecimalField(
        max_digits=10, decimal_places=2, default=10.00
    )
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2, default=10.00)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=5.00)
    advantages = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=True)

    def clean(self):
        """Ensure minimum duration, proper min-max values, and type-based constraints."""
        if self.type == "investment":
            if self.duration and self.duration < 6:
                raise ValidationError("Plan duration must be at least 6 months.")

        if self.share_price_min >= self.share_price_max:
            raise ValidationError(
                "Minimum share price must be less than maximum share price."
            )

        # Validate Loans
        if (
            self.type == "loan"
            and self.base_amount
            and self.base_amount > self.max_loan_amount
        ):
            raise ValidationError(f"Loans cannot exceed ${self.max_loan_amount}")

        # Validate rate ranges
        if self.rate < 0 or self.rate > 1:
            raise ValidationError("Rate must be between 0 and 1 (0% to 100%)")

        # Validate platform fee and tax
        if self.platform_fee < 0 or self.tax < 0:
            raise ValidationError("Platform fee and tax cannot be negative")

        # Validate credit score for loans
        if (
            self.type == "loan"
            and self.min_credit_score < 300
            or self.min_credit_score > 850
        ):
            raise ValidationError("Credit score must be between 300 and 850")

    def get_dynamic_rate(self, amount, duration):
        """
        Calculate dynamic rate for **loans & investments**.
        - Higher amounts & longer durations yield better rates.
        """
        if self.type == "loan":
            base_rate = 0.05 if amount < 5000 else 0.07
        else:
            base_rate = 0.03 if amount < 5000 else 0.05

        # Bonus for duration
        if 7 <= duration <= 12:
            base_rate += 0.01
        elif duration > 12:
            base_rate += 0.02

        return base_rate

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"


class Investments(models.Model):
    client = models.ForeignKey(
        User, limit_choices_to={"is_active": True}, on_delete=models.CASCADE
    )
    # investment_plan = models.ForeignKey(Investment_rates, on_delete=models.CASCADE , default='Long term investment')
    investment_plan = models.ForeignKey(Investment_rates, on_delete=models.CASCADE)
    investment_date = models.DateField(auto_now_add=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()

    def calculate_returns(self):
        if self.investment_plan.investment_rate:
            return self.amount + (self.amount * self.investment_plan.investment_rate)
        return 0

    def get_absolute_url(self):
        if self.client and self.client.username:
            return reverse("investing:user_investments", args=[self.client.username])
        return "#"  # Return a fallback URL if client or username is not available

    def __str__(self):
        return f"Investment ID: {self.id}, Client: {self.client.username}, Plan: {self.investment_plan.name}"


class InvestmentContent(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "InvestmentContent"

    def save(self, *args, **kwargs):
        # Ensure description is never empty
        if not self.description:
            self.description = "Welcome to our investment platform. We provide comprehensive investment solutions for all types of investors."
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Ticker_Data(models.Model):
    symbol = models.CharField(max_length=255, blank=True, null=True)
    overallrisk = models.DecimalField(
        max_digits=17, decimal_places=3, blank=True, null=True
    )
    sharesshort = models.DecimalField(
        max_digits=17, decimal_places=3, blank=True, null=True
    )
    enterprisetoebitda = models.DecimalField(
        max_digits=17, decimal_places=3, blank=True, null=True
    )
    ebitda = models.DecimalField(max_digits=17, decimal_places=3, blank=True, null=True)
    quickratio = models.DecimalField(
        max_digits=17, decimal_places=3, blank=True, null=True
    )
    currentratio = models.DecimalField(
        max_digits=17, decimal_places=3, blank=True, null=True
    )
    revenuegrowth = models.DecimalField(
        max_digits=17, decimal_places=3, blank=True, null=True
    )
    fetched_date = models.DateField(auto_now_add=True, blank=True, null=True)
    industry = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Option Measures"

    def __str__(self):
        return self.symbol


class credit_spread(models.Model):
    symbol = models.CharField(max_length=255, blank=True, null=True)
    strategy = models.CharField(max_length=255, blank=True, null=True)
    type = models.CharField(max_length=255, blank=True, null=True)
    price = models.CharField(max_length=255, blank=True, null=True)
    sell_strike = models.CharField(max_length=255, blank=True, null=True)
    buy_strike = models.CharField(max_length=255, blank=True, null=True)
    expiry = models.CharField(max_length=255, blank=True, null=True)
    premium = models.CharField(max_length=255, blank=True, null=True)
    width = models.CharField(max_length=255, blank=True, null=True)
    prem_width = models.CharField(max_length=255, blank=True, null=True)
    # iv_rank = models.CharField(max_length=255,blank=True, null=True)
    rank = models.CharField(max_length=255, blank=True, null=True)
    earnings_date = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name_plural = "credit_spread"

    # def __str__(self):
    #     return self.symbol


class ShortPut(models.Model):
    symbol = models.CharField(max_length=255, blank=True, null=True)
    industry = models.CharField(max_length=255, blank=True, null=True)
    expiry = models.CharField(max_length=255, blank=True, null=True)
    days_to_expiry = models.CharField(max_length=255, blank=True, null=True)
    strike_price = models.CharField(max_length=255, blank=True, null=True)
    mid_price = models.CharField(max_length=255, blank=True, null=True)
    bid_price = models.CharField(max_length=255, blank=True, null=True)
    ask_price = models.CharField(max_length=255, blank=True, null=True)
    implied_volatility_rank = models.CharField(max_length=255, blank=True, null=True)
    earnings_date = models.CharField(max_length=255, blank=True, null=True)
    earnings_flag = models.CharField(max_length=255, blank=True, null=True)
    stock_price = models.CharField(max_length=255, blank=True, null=True)
    raw_return = models.CharField(max_length=255, blank=True, null=True)
    annualized_return = models.CharField(max_length=255, blank=True, null=True)
    distance_to_strike = models.CharField(max_length=255, blank=True, null=True)
    comment = models.CharField(max_length=255, blank=True, null=True)
    on_date = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "ShortPut"

    # def __str__(self):
    #     return self.symbol


class covered_calls(models.Model):
    symbol = models.CharField(max_length=255, blank=True, null=True)
    action = models.CharField(max_length=255, blank=True, null=True)
    expiry = models.CharField(max_length=255, blank=True, null=True)
    days_to_expiry = models.CharField(max_length=255, blank=True, null=True)
    strike_price = models.CharField(max_length=255, blank=True, null=True)
    mid_price = models.CharField(max_length=255, blank=True, null=True)
    bid_price = models.CharField(max_length=255, blank=True, null=True)
    ask_price = models.CharField(max_length=255, blank=True, null=True)
    implied_volatility_rank = models.CharField(max_length=255, blank=True, null=True)
    # rank = models.CharField(max_length=255,blank=True, null=True)
    earnings_date = models.CharField(max_length=255, blank=True, null=True)
    earnings_flag = models.CharField(max_length=255, blank=True, null=True)
    stock_price = models.CharField(max_length=255, blank=True, null=True)
    raw_return = models.CharField(max_length=255, blank=True, null=True)
    annualized_return = models.CharField(max_length=255, blank=True, null=True)
    distance_to_strike = models.CharField(max_length=255, blank=True, null=True)
    comment = models.CharField(max_length=255, blank=True, null=True)
    on_date = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "covered_calls"

    # def __str__(self):
    #     return self.symbol


class Portfolio(TimeStampedModel):

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    symbol = models.CharField(max_length=255, blank=True, null=True)
    industry = models.CharField(max_length=255, blank=True, null=True)
    action = models.CharField(max_length=255, blank=True, null=True)
    # strike_price = models.CharField(max_length=255,blank=True, null=True)
    implied_volatility_rank = models.CharField(max_length=255, blank=True, null=True)
    expiry = models.CharField(max_length=255, blank=True, null=True)
    earnings_date = models.CharField(max_length=255, blank=True, null=True)
    condition = models.CharField(max_length=255, blank=True, null=True)
    comment = models.CharField(max_length=255, blank=True, null=True)
    on_date = models.CharField(max_length=255, blank=True, null=True)

    strategy = models.CharField(max_length=255, blank=True, null=True)
    returns = models.DecimalField(max_digits=10, decimal_places=4, default=0.00)
    short_strike = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    long_strike = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    # short_strike = models.CharField(max_length=255,blank=True, null=True)
    # long_strike = models.CharField(max_length=255,blank=True, null=True)

    amount = models.DecimalField(max_digits=10, decimal_places=4, default=0.00)

    long_leg_delta = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=0.00,
        validators=[MinValueValidator(0.20)],
    )
    short_leg_delta = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=0.00,
        validators=[MaxValueValidator(0.45)],
    )
    long_leg_theta = models.DecimalField(max_digits=10, decimal_places=4, default=0.00)
    short_leg_theta = models.DecimalField(max_digits=10, decimal_places=4, default=0.00)
    number_of_contract = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Comes from TimeStampedModel in main
    class Meta:
        verbose_name_plural = "Portfolio"
        indexes = [
            models.Index(fields=["symbol"]),
            models.Index(fields=["user"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["updated_at"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["is_featured"]),
            # Composite indexes for common query patterns
            models.Index(fields=["user", "symbol"]),
            models.Index(fields=["symbol", "is_active"]),
            models.Index(fields=["created_at", "is_active"]),
        ]

    def clean(self):
        """Validate Portifolio model data"""
        from django.core.exceptions import ValidationError

        # Validate delta values
        if self.long_leg_delta < 0.20:
            raise ValidationError("Long leg delta must be at least 0.20")

        if self.short_leg_delta > 0.45:
            raise ValidationError("Short leg delta cannot exceed 0.45")

        # Validate strike prices
        if self.short_strike and self.long_strike:
            if self.short_strike >= self.long_strike:
                raise ValidationError("Short strike must be less than long strike")

        # Validate amount
        if self.amount < 0:
            raise ValidationError("Amount cannot be negative")

        # Validate number of contracts
        if self.number_of_contract <= 0:
            raise ValidationError("Number of contracts must be positive")

    def save(self, *args, **kwargs):
        """Override save to ensure validation"""
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.symbol


class OverBoughtSold(models.Model):
    symbol = models.CharField(max_length=255, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    last = models.CharField(max_length=255, blank=True, null=True)
    volume = models.CharField(max_length=255, blank=True, null=True)
    RSI = models.CharField(max_length=255, blank=True, null=True)
    EPS = models.CharField(max_length=255, blank=True, null=True)
    PE = models.CharField(max_length=255, blank=True, null=True)
    rank = models.CharField(max_length=255, blank=True, null=True)
    profit_margins = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    @property
    def condition_integer(self):
        try:
            # Convert to float, round, and then convert to int
            rsi_value = int(round(float(self.RSI)))
            if rsi_value >= 30:
                return 1  # 'oversold'
            else:
                return 0  # 'overbought'
        except ValueError:
            # Handle any exceptions gracefully
            return -1  # neutral

    class Meta:
        verbose_name_plural = "Oversold"

    def __str__(self):
        return self.symbol


class SavedResponses(models.Model):
    CONDITION_CHOICES = (
        ("80", "Overbought (RSI > 80)"),
        ("20", "Oversold (RSI < 20)"),
    )

    condition = models.CharField(max_length=10, choices=CONDITION_CHOICES, unique=True)
    standard_response = models.TextField(null=True)

    def __str__(self):
        return f"{self.condition} Standard Response"


class Options_Returns(models.Model):
    symbol = models.CharField(max_length=255, blank=True, null=True)
    expiration_date = models.CharField(max_length=255, blank=True, null=True)
    action = models.CharField(max_length=255, blank=True, null=True)
    event = models.CharField(max_length=255, blank=True, null=True)
    qty = models.CharField(max_length=255, blank=True, null=True)
    strike_price = models.CharField(max_length=255, blank=True, null=True)
    open_date = models.CharField(max_length=255, blank=True, null=True)
    closed_date = models.CharField(max_length=255, blank=True, null=True)
    cost = models.CharField(max_length=255, blank=True, null=True)
    LT_GL = models.CharField(max_length=255, blank=True, null=True)
    ST_GL = models.CharField(max_length=255, blank=True, null=True)
    proceeds = models.CharField(max_length=255, blank=True, null=True)
    covered = models.CharField(max_length=255, blank=True, null=True)
    security_number = models.CharField(max_length=255, blank=True, null=True)
    cbm = models.CharField(max_length=255, blank=True, null=True)
    other = models.CharField(max_length=255, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)

    @property
    def wash_days(self):
        date_today = datetime.now(timezone.utc)
        date_today_date = date_today.date()
        wash_days = (date_today_date - self.closed_date).days
        return wash_days

    @property
    def wait_time(self):
        wait_time = (self.closed_date - self.open_date).days
        return wait_time

    class Meta:
        verbose_name_plural = "returns"

    def __str__(self):
        return self.symbol


class Cost_Basis(models.Model):
    symbol = models.CharField(max_length=255, blank=True, null=True)
    expiration_date = models.CharField(max_length=255, blank=True, null=True)
    action = models.CharField(max_length=255, blank=True, null=True)
    qty = models.CharField(max_length=255, blank=True, null=True)
    strike_price = models.CharField(max_length=255, blank=True, null=True)
    open_date = models.CharField(max_length=255, blank=True, null=True)
    cost = models.CharField(max_length=255, blank=True, null=True)
    covered = models.CharField(max_length=255, blank=True, null=True)
    security_number = models.CharField(max_length=255, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name_plural = "cost_basis"

    def __str__(self):
        return self.symbol


class InvestmentsStrategy(models.Model):
    symbol = models.CharField(max_length=255, blank=True, null=True)
    action = models.CharField(max_length=255, blank=True, null=True)
    expiry = models.CharField(max_length=255, blank=True, null=True)
    days_to_expiry = models.CharField(max_length=255, blank=True, null=True)
    strike_price = models.DecimalField(max_digits=10, decimal_places=2)
    mid_price = models.DecimalField(max_digits=10, decimal_places=2)
    bid_price = models.DecimalField(max_digits=10, decimal_places=2)
    ask_price = models.DecimalField(max_digits=10, decimal_places=2)
    implied_volatility_rank = models.DecimalField(max_digits=10, decimal_places=2)
    earnings_date = models.DateField(auto_now_add=True)
    earnings_flag = models.BooleanField(default=True)
    stock_price = models.DecimalField(max_digits=10, decimal_places=2)
    raw_return = models.DecimalField(max_digits=10, decimal_places=2)
    annualized_return = models.DecimalField(max_digits=10, decimal_places=2)
    distance_to_strike = models.DecimalField(max_digits=10, decimal_places=2)
    comment = models.TextField()
    on_date = models.DateTimeField()
    trade_type = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.symbol}-{self.get_type_display()}"


class Returns_Balances(TimeStampedModel):
    opening = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    closing = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    closing_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"Closing Balance of {self.closing} as of {self.created_at}"

    @property
    def balances(self):
        try:
            net_balance = round(Decimal(self.closing - self.opening), 2)
        except:
            net_balance = 0
        return net_balance


class Daily_Trades(TimeStampedModel):
    symbol = models.CharField(max_length=255, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    strike_price = models.DecimalField(max_digits=10, decimal_places=2)
    action = models.CharField(max_length=255, blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    expiry = models.DateField(blank=True, null=True)
    transaction = models.CharField(max_length=255, blank=True, null=True)
    account_type = models.CharField(max_length=255, blank=True, null=True)
    credit = models.DecimalField(max_digits=10, decimal_places=2)
    debit = models.DecimalField(max_digits=10, decimal_places=2)
    qty = models.IntegerField(blank=True, null=True)
    page_number = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.symbol}-{self.date}"

    def clean(self):
        """Validate Daily_Trades model data"""
        from django.core.exceptions import ValidationError

        # Validate price and strike price
        if self.price <= 0:
            raise ValidationError("Price must be positive")

        if self.strike_price <= 0:
            raise ValidationError("Strike price must be positive")

        # Validate quantity
        if self.qty and self.qty <= 0:
            raise ValidationError("Quantity must be positive")

        # Validate credit and debit
        if self.credit < 0:
            raise ValidationError("Credit cannot be negative")

        if self.debit < 0:
            raise ValidationError("Debit cannot be negative")

        # Validate dates
        if self.date and self.expiry:
            if self.date >= self.expiry:
                raise ValidationError("Trade date must be before expiry date")

    def save(self, *args, **kwargs):
        """Override save to ensure validation"""
        self.clean()
        super().save(*args, **kwargs)

    @property
    def returns(self):
        try:
            raw_returns = round(Decimal(self.credit - self.debit), 2)
        except:
            raw_returns = 0
        return raw_returns


class InvestmentPerformance(TimeStampedModel):
    """
    Track monthly performance metrics for individual investments
    """

    investment = models.ForeignKey(
        Investor_Information,
        on_delete=models.CASCADE,
        related_name="performance_records",
    )

    # Performance Period
    performance_date = models.DateField(default=date.today)
    period_start = models.DateField()
    period_end = models.DateField()

    # Financial Metrics
    period_start_value = models.DecimalField(max_digits=10, decimal_places=2)
    period_end_value = models.DecimalField(max_digits=10, decimal_places=2)
    period_return = models.DecimalField(max_digits=10, decimal_places=2)
    period_return_percentage = models.DecimalField(max_digits=5, decimal_places=2)

    # Business Metrics (for transparency)
    revenue_generated = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Revenue generated by CODA during this period",
    )
    expenses_incurred = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Expenses incurred by CODA during this period",
    )
    net_profit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Net profit for this period",
    )

    # Key Performance Indicators
    customer_acquisition_cost = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    customer_lifetime_value = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    monthly_recurring_revenue = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    # Notes and Updates
    key_achievements = models.TextField(
        blank=True, help_text="Key business achievements during this period"
    )
    challenges_faced = models.TextField(
        blank=True, help_text="Challenges faced during this period"
    )
    next_period_goals = models.TextField(
        blank=True, help_text="Goals for the next period"
    )

    class Meta:
        verbose_name = "Investment Performance"
        verbose_name_plural = "Investment Performance Records"
        ordering = ["-performance_date"]
        unique_together = ["investment", "performance_date"]

    def __str__(self):
        return f"{self.investment.investor.username} - {self.performance_date.strftime('%Y-%m')}"


class InvestmentReport(TimeStampedModel):
    """
    Track sent reports to investors
    """

    REPORT_TYPE_CHOICES = [
        ("monthly", "Monthly Report"),
        ("quarterly", "Quarterly Report"),
        ("annual", "Annual Report"),
        ("special", "Special Update"),
    ]

    investment = models.ForeignKey(
        Investor_Information, on_delete=models.CASCADE, related_name="reports"
    )

    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    report_date = models.DateField(default=date.today)
    period_start = models.DateField()
    period_end = models.DateField()

    # Report Content
    subject = models.CharField(max_length=200)
    content = models.TextField()
    attachments = models.JSONField(default=list, blank=True)

    # Delivery Status
    sent_date = models.DateTimeField(null=True, blank=True)
    delivery_status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("sent", "Sent"),
            ("delivered", "Delivered"),
            ("failed", "Failed"),
        ],
        default="pending",
    )
    email_opened = models.BooleanField(default=False)
    email_opened_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Investment Report"
        verbose_name_plural = "Investment Reports"
        ordering = ["-report_date"]

    def __str__(self):
        return f"{self.investment.investor.username} - {self.get_report_type_display()} - {self.report_date}"


class InvestmentMilestone(TimeStampedModel):
    """
    Track key milestones and achievements for investor transparency
    """

    MILESTONE_TYPE_CHOICES = [
        ("revenue", "Revenue Milestone"),
        ("customer", "Customer Milestone"),
        ("product", "Product Milestone"),
        ("partnership", "Partnership Milestone"),
        ("funding", "Funding Milestone"),
        ("other", "Other Achievement"),
    ]

    investment = models.ForeignKey(
        Investor_Information, on_delete=models.CASCADE, related_name="milestones"
    )

    milestone_type = models.CharField(max_length=20, choices=MILESTONE_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    achieved_date = models.DateField(default=date.today)

    # Impact on Investment
    impact_on_investment = models.TextField(
        blank=True, help_text="How this milestone impacts the investment"
    )
    expected_value_increase = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Expected increase in investment value",
    )

    # Notification
    notify_investor = models.BooleanField(default=True)
    notification_sent = models.BooleanField(default=False)
    notification_sent_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Investment Milestone"
        verbose_name_plural = "Investment Milestones"
        ordering = ["-achieved_date"]

    def __str__(self):
        return f"{self.investment.investor.username} - {self.title}"


class InvestmentUpgradeOffer(TimeStampedModel):
    """
    Track upgrade offers to encourage larger investments
    """

    OFFER_TYPE_CHOICES = [
        ("tier_upgrade", "Tier Upgrade"),
        ("bonus_rate", "Bonus Interest Rate"),
        ("early_access", "Early Access to New Products"),
        ("exclusive_benefits", "Exclusive Benefits"),
        ("equity_bonus", "Equity Bonus"),
    ]

    investment = models.ForeignKey(
        Investor_Information, on_delete=models.CASCADE, related_name="upgrade_offers"
    )

    offer_type = models.CharField(max_length=20, choices=OFFER_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField()

    # Offer Details
    minimum_additional_investment = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Minimum additional investment required",
    )
    bonus_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Additional interest rate bonus",
    )
    bonus_equity = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Additional equity percentage",
    )

    # Validity
    valid_from = models.DateField(default=date.today)
    valid_until = models.DateField()
    is_active = models.BooleanField(default=True)

    # Tracking
    offer_sent_date = models.DateTimeField(null=True, blank=True)
    investor_response = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("accepted", "Accepted"),
            ("declined", "Declined"),
            ("expired", "Expired"),
        ],
        default="pending",
    )
    response_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Investment Upgrade Offer"
        verbose_name_plural = "Investment Upgrade Offers"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.investment.investor.username} - {self.title}"

    @property
    def is_expired(self):
        """Check if offer has expired"""
        return date.today() > self.valid_until


# =============================================================================
# PHASE 3: NEW MODELS FOR ENHANCED FUNCTIONALITY
# =============================================================================

class RiskAssessment(TimeStampedModel):
    """
    Comprehensive risk assessment for investments
    """
    
    RISK_RATING_CHOICES = [
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
        ('critical', 'Critical Risk'),
    ]
    
    investment = models.ForeignKey(
        Investor_Information, 
        on_delete=models.CASCADE, 
        related_name="risk_assessments"
    )
    assessment_date = models.DateField(default=date.today)
    
    # Risk Scores (1-10 scale)
    market_risk_score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Market risk score (1-10)"
    )
    credit_risk_score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Credit risk score (1-10)"
    )
    liquidity_risk_score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Liquidity risk score (1-10)"
    )
    operational_risk_score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Operational risk score (1-10)"
    )
    
    # Overall Assessment
    overall_risk_rating = models.CharField(
        max_length=20, 
        choices=RISK_RATING_CHOICES,
        help_text="Overall risk rating"
    )
    
    # Risk Mitigation
    mitigation_strategies = models.JSONField(
        default=list,
        help_text="List of mitigation strategies"
    )
    
    # Additional Information
    notes = models.TextField(blank=True, null=True)
    assessed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name="risk_assessments"
    )
    
    class Meta:
        verbose_name = "Risk Assessment"
        verbose_name_plural = "Risk Assessments"
        ordering = ["-assessment_date"]
        indexes = [
            models.Index(fields=["investment", "assessment_date"]),
            models.Index(fields=["overall_risk_rating"]),
        ]
    
    def clean(self):
        """Validate risk assessment data"""
        if self.market_risk_score < 1 or self.market_risk_score > 10:
            raise ValidationError("Market risk score must be between 1 and 10")
        if self.credit_risk_score < 1 or self.credit_risk_score > 10:
            raise ValidationError("Credit risk score must be between 1 and 10")
        if self.liquidity_risk_score < 1 or self.liquidity_risk_score > 10:
            raise ValidationError("Liquidity risk score must be between 1 and 10")
        if self.operational_risk_score < 1 or self.operational_risk_score > 10:
            raise ValidationError("Operational risk score must be between 1 and 10")
    
    @property
    def average_risk_score(self):
        """Calculate average risk score"""
        scores = [
            self.market_risk_score,
            self.credit_risk_score,
            self.liquidity_risk_score,
            self.operational_risk_score
        ]
        return sum(scores) / len(scores)
    
    def __str__(self):
        return f"{self.investment.investor.username} - Risk Assessment - {self.assessment_date}"


class RiskAlert(TimeStampedModel):
    """
    Risk alerts and notifications for investments
    """
    
    ALERT_TYPE_CHOICES = [
        ('price_drop', 'Price Drop'),
        ('volatility_spike', 'Volatility Spike'),
        ('liquidity_concern', 'Liquidity Concern'),
        ('credit_downgrade', 'Credit Downgrade'),
        ('market_crash', 'Market Crash'),
        ('regulatory_change', 'Regulatory Change'),
        ('operational_issue', 'Operational Issue'),
    ]
    
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    investment = models.ForeignKey(
        Investor_Information, 
        on_delete=models.CASCADE, 
        related_name="risk_alerts"
    )
    alert_type = models.CharField(
        max_length=20, 
        choices=ALERT_TYPE_CHOICES
    )
    severity = models.CharField(
        max_length=20, 
        choices=SEVERITY_CHOICES
    )
    message = models.TextField()
    
    # Alert Status
    is_resolved = models.BooleanField(default=False)
    resolved_date = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name="resolved_alerts"
    )
    resolution_notes = models.TextField(blank=True, null=True)
    
    # Metadata
    triggered_by = models.CharField(max_length=100, blank=True, null=True)
    data_snapshot = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = "Risk Alert"
        verbose_name_plural = "Risk Alerts"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["investment", "is_resolved"]),
            models.Index(fields=["severity"]),
            models.Index(fields=["alert_type"]),
        ]
    
    def __str__(self):
        return f"{self.investment.investor.username} - {self.get_alert_type_display()} - {self.severity}"


class ComplianceRecord(TimeStampedModel):
    """
    Compliance tracking for investments
    """
    
    REQUIREMENT_TYPE_CHOICES = [
        ('kyc', 'KYC Verification'),
        ('accredited_investor', 'Accredited Investor Status'),
        ('aml', 'AML Compliance'),
        ('regulatory', 'Regulatory Compliance'),
        ('documentation', 'Documentation'),
        ('reporting', 'Reporting Requirements'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]
    
    investment = models.ForeignKey(
        Investor_Information, 
        on_delete=models.CASCADE, 
        related_name="compliance_records"
    )
    requirement_type = models.CharField(
        max_length=20, 
        choices=REQUIREMENT_TYPE_CHOICES
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # Dates
    due_date = models.DateField()
    completed_date = models.DateField(null=True, blank=True)
    
    # Documents and Notes
    documents = models.JSONField(
        default=list,
        help_text="Required documents and their status"
    )
    notes = models.TextField(blank=True, null=True)
    
    # Assignment
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name="assigned_compliance_records"
    )
    
    class Meta:
        verbose_name = "Compliance Record"
        verbose_name_plural = "Compliance Records"
        ordering = ["due_date"]
        indexes = [
            models.Index(fields=["investment", "status"]),
            models.Index(fields=["due_date"]),
            models.Index(fields=["requirement_type"]),
        ]
    
    @property
    def is_overdue(self):
        """Check if compliance record is overdue"""
        return date.today() > self.due_date and self.status not in ['approved', 'rejected']
    
    @property
    def days_until_due(self):
        """Calculate days until due date"""
        delta = self.due_date - date.today()
        return delta.days
    
    def __str__(self):
        return f"{self.investment.investor.username} - {self.get_requirement_type_display()} - {self.status}"


class AuditTrail(TimeStampedModel):
    """
    Comprehensive audit trail for all investment changes
    """
    
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('deleted', 'Deleted'),
        ('status_changed', 'Status Changed'),
        ('amount_updated', 'Amount Updated'),
        ('document_uploaded', 'Document Uploaded'),
        ('compliance_updated', 'Compliance Updated'),
    ]
    
    investment = models.ForeignKey(
        Investor_Information, 
        on_delete=models.CASCADE, 
        related_name="audit_trails"
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    performed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name="audit_actions"
    )
    
    # Change Tracking
    old_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    reason = models.TextField(blank=True, null=True)
    
    # Request Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    session_id = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        verbose_name = "Audit Trail"
        verbose_name_plural = "Audit Trails"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["investment", "action"]),
            models.Index(fields=["performed_by"]),
            models.Index(fields=["created_at"]),
        ]
    
    def __str__(self):
        return f"{self.investment.investor.username} - {self.get_action_display()} - {self.created_at}"


class MarketData(TimeStampedModel):
    """
    Market data for investment analytics
    """
    
    DATA_TYPE_CHOICES = [
        ('price', 'Price'),
        ('volume', 'Volume'),
        ('volatility', 'Volatility'),
        ('yield', 'Yield'),
        ('spread', 'Spread'),
        ('rating', 'Rating'),
    ]
    
    symbol = models.CharField(max_length=20, help_text="Market symbol/ticker")
    data_type = models.CharField(max_length=20, choices=DATA_TYPE_CHOICES)
    timestamp = models.DateTimeField()
    value = models.DecimalField(max_digits=20, decimal_places=6)
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)
    source = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        verbose_name = "Market Data"
        verbose_name_plural = "Market Data"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["symbol", "data_type", "timestamp"]),
            models.Index(fields=["timestamp"]),
        ]
        unique_together = [["symbol", "data_type", "timestamp"]]
    
    def __str__(self):
        return f"{self.symbol} - {self.get_data_type_display()} - {self.value}"


class InvestmentAnalytics(TimeStampedModel):
    """
    Advanced analytics for investments
    """
    
    investment = models.ForeignKey(
        Investor_Information, 
        on_delete=models.CASCADE, 
        related_name="analytics"
    )
    analysis_date = models.DateField(default=date.today)
    
    # Performance Metrics
    sharpe_ratio = models.DecimalField(
        max_digits=8, decimal_places=4, null=True, blank=True
    )
    max_drawdown = models.DecimalField(
        max_digits=8, decimal_places=4, null=True, blank=True
    )
    volatility = models.DecimalField(
        max_digits=8, decimal_places=4, null=True, blank=True
    )
    
    # Predictive Analytics
    predicted_return = models.DecimalField(
        max_digits=8, decimal_places=4, null=True, blank=True
    )
    confidence_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    
    # Market Correlation
    market_correlation = models.DecimalField(
        max_digits=5, decimal_places=3, null=True, blank=True
    )
    beta = models.DecimalField(
        max_digits=5, decimal_places=3, null=True, blank=True
    )
    
    # Additional Metrics
    value_at_risk = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    expected_shortfall = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    
    # Analysis Metadata
    analysis_notes = models.TextField(blank=True, null=True)
    calculated_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name="calculated_analytics"
    )
    
    class Meta:
        verbose_name = "Investment Analytics"
        verbose_name_plural = "Investment Analytics"
        ordering = ["-analysis_date"]
        indexes = [
            models.Index(fields=["investment", "analysis_date"]),
            models.Index(fields=["analysis_date"]),
        ]
    
    @property
    def get_risk_level(self):
        """Determine risk level based on volatility and drawdown"""
        if not self.volatility or not self.max_drawdown:
            return 'unknown'
        
        if self.volatility < 5 and self.max_drawdown < 3:
            return 'low'
        elif self.volatility < 15 and self.max_drawdown < 10:
            return 'medium'
        else:
            return 'high'
    
    @property
    def get_performance_rating(self):
        """Determine performance rating based on Sharpe ratio"""
        if not self.sharpe_ratio:
            return 'unknown'
        
        if self.sharpe_ratio >= 2:
            return 'excellent'
        elif self.sharpe_ratio >= 1:
            return 'good'
        elif self.sharpe_ratio >= 0:
            return 'fair'
        else:
            return 'poor'
    
    def __str__(self):
        return f"{self.investment.investor.username} - Analytics - {self.analysis_date}"


class InvestorCommunication(TimeStampedModel):
    """
    Communication tracking with investors
    """
    
    COMMUNICATION_TYPE_CHOICES = [
        ('email', 'Email'),
        ('phone', 'Phone Call'),
        ('meeting', 'Meeting'),
        ('report', 'Report'),
        ('notification', 'Notification'),
    ]
    
    investment = models.ForeignKey(
        Investor_Information, 
        on_delete=models.CASCADE, 
        related_name="communications"
    )
    communication_type = models.CharField(
        max_length=20, 
        choices=COMMUNICATION_TYPE_CHOICES
    )
    subject = models.CharField(max_length=200)
    content = models.TextField()
    
    # Communication Details
    sent_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name="sent_communications"
    )
    sent_date = models.DateTimeField(default=timezone.now)
    
    # Response Tracking
    investor_response = models.TextField(blank=True, null=True)
    response_date = models.DateTimeField(null=True, blank=True)
    satisfaction_rating = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Investor satisfaction rating (1-5)"
    )
    
    # Metadata
    is_automated = models.BooleanField(default=False)
    template_used = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        verbose_name = "Investor Communication"
        verbose_name_plural = "Investor Communications"
        ordering = ["-sent_date"]
        indexes = [
            models.Index(fields=["investment", "communication_type"]),
            models.Index(fields=["sent_date"]),
            models.Index(fields=["sent_by"]),
        ]
    
    def __str__(self):
        return f"{self.investment.investor.username} - {self.get_communication_type_display()} - {self.subject}"


class NotificationPreference(TimeStampedModel):
    """
    Investor notification preferences
    """
    
    NOTIFICATION_TYPE_CHOICES = [
        ('performance_update', 'Performance Update'),
        ('market_alert', 'Market Alert'),
        ('milestone', 'Milestone Achievement'),
        ('compliance', 'Compliance Reminder'),
        ('payment', 'Payment Notification'),
        ('report', 'Report Available'),
    ]
    
    FREQUENCY_CHOICES = [
        ('immediate', 'Immediate'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('never', 'Never'),
    ]
    
    DELIVERY_METHOD_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
        ('dashboard', 'Dashboard Only'),
    ]
    
    investor = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="notification_preferences"
    )
    notification_type = models.CharField(
        max_length=20, 
        choices=NOTIFICATION_TYPE_CHOICES
    )
    frequency = models.CharField(
        max_length=20, 
        choices=FREQUENCY_CHOICES
    )
    delivery_method = models.CharField(
        max_length=20, 
        choices=DELIVERY_METHOD_CHOICES
    )
    enabled = models.BooleanField(default=True)
    
    # Additional Settings
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)
    timezone = models.CharField(max_length=50, default='UTC')
    
    class Meta:
        verbose_name = "Notification Preference"
        verbose_name_plural = "Notification Preferences"
        ordering = ["investor", "notification_type"]
        indexes = [
            models.Index(fields=["investor", "enabled"]),
            models.Index(fields=["notification_type"]),
            models.Index(fields=["frequency"]),
        ]
        unique_together = [["investor", "notification_type", "delivery_method"]]
    
    def __str__(self):
        return f"{self.investor.username} - {self.get_notification_type_display()} - {self.frequency}"


# ============================================================================
# MANAGED OPTIONS TRADING MODELS
# ============================================================================
# New models for professional options account management service
# These models support CODA managing client accounts with options strategies

class ManagedTradingAccount(TimeStampedModel):
    """
    Managed options trading account for clients
    
    This model tracks client accounts where CODA manages options trading
    on behalf of the client. Includes fee structure, risk parameters,
    performance tracking, and account status.
    """
    
    # Client Information
    client = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='managed_trading_accounts',
        help_text="Client who owns this account"
    )
    account_number = models.CharField(
        max_length=20,
        unique=True,
        help_text="Unique account identifier (e.g., CODA-OPT-001)"
    )
    account_name = models.CharField(
        max_length=100,
        help_text="Descriptive name for the account"
    )
    account_manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_accounts',
        help_text="CODA staff member managing this account"
    )
    
    # Financial Details
    initial_capital = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('5000.00'))],
        help_text="Starting account balance"
    )
    current_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Current total account value"
    )
    cash_available = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Cash available for new positions"
    )
    cash_reserved = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Cash reserved for margin/collateral"
    )
    high_water_mark = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Highest account value reached (for performance fees)"
    )
    
    # Fee Structure
    FEE_TIER_CHOICES = [
        ('consultative', 'Consultative Coaching - $420/month + 10% bonus'),
        ('starter', 'Starter - 0% mgmt + 25% performance'),
        ('professional', 'Professional - 1.5% mgmt + 20% perf'),
        ('premium', 'Premium - 1% mgmt + 15% perf + $500/mo min'),
        ('co_invest', 'Co-Investment - 50/50 split'),
        ('custom', 'Custom Fee Structure')
    ]
    fee_tier = models.CharField(
        max_length=20,
        choices=FEE_TIER_CHOICES,
        default='professional',
        help_text="Fee tier selected by client"
    )
    management_fee_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('1.50'),
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('5.00'))],
        help_text="Annual management fee percentage (0-5%)"
    )
    performance_fee_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('20.00'),
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('50.00'))],
        help_text="Performance fee percentage (0-50%)"
    )
    performance_threshold = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('8.00'),
        help_text="Hurdle rate - only pay performance fee above this return %"
    )
    
    # Consultative Tier Fields
    session_fee = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal('50.00'),
        help_text="Fee per coaching session (for consultative tier)"
    )
    sessions_per_month = models.IntegerField(
        default=8,
        help_text="Number of sessions per month"
    )
    monthly_platform_fee = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal('20.00'),
        help_text="Monthly platform/software fee"
    )
    sessions_completed_this_month = models.IntegerField(
        default=0,
        help_text="Sessions completed in current month"
    )
    total_sessions_completed = models.IntegerField(
        default=0,
        help_text="Total sessions completed all-time"
    )
    next_session_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Next scheduled coaching session"
    )
    
    # Risk Parameters
    max_position_risk = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('7000.00'),
        help_text="Maximum capital at risk per position"
    )
    max_total_risk = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('15.00'),
        help_text="Maximum total portfolio risk as % of balance"
    )
    max_daily_loss = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('2.00'),
        help_text="Maximum daily loss as % of balance"
    )
    max_weekly_loss = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('5.00'),
        help_text="Maximum weekly loss as % of balance"
    )
    max_monthly_loss = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('10.00'),
        help_text="Maximum monthly loss as % of balance"
    )
    max_positions = models.IntegerField(
        default=10,
        help_text="Maximum number of simultaneous open positions"
    )
    
    # Account Status
    STATUS_CHOICES = [
        ('pending', 'Pending Activation'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('closed', 'Closed'),
        ('suspended', 'Suspended')
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    trading_enabled = models.BooleanField(
        default=True,
        help_text="Can trader execute new positions"
    )
    auto_trading_enabled = models.BooleanField(
        default=False,
        help_text="Allow automated position entry/exit"
    )
    activation_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date account was activated"
    )
    closure_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date account was closed"
    )
    
    # Performance Tracking
    total_trades = models.IntegerField(
        default=0,
        help_text="Total number of closed positions"
    )
    winning_trades = models.IntegerField(
        default=0,
        help_text="Number of profitable closed positions"
    )
    losing_trades = models.IntegerField(
        default=0,
        help_text="Number of losing closed positions"
    )
    total_profit_loss = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Cumulative profit/loss all-time"
    )
    total_fees_paid = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total fees paid by client"
    )
    last_fee_calculation_date = models.DateField(
        null=True,
        blank=True,
        help_text="Last date fees were calculated"
    )
    
    # Notification Preferences (Phase 3: WhatsApp/Telegram)
    whatsapp_enabled = models.BooleanField(
        default=False,
        help_text="Enable WhatsApp notifications for position updates"
    )
    whatsapp_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Client phone number in international format (+1234567890)"
    )
    telegram_enabled = models.BooleanField(
        default=False,
        help_text="Enable Telegram notifications for position updates"
    )
    telegram_chat_id = models.CharField(
        max_length=50,
        blank=True,
        help_text="Client Telegram chat ID"
    )
    
    class Meta:
        verbose_name = "Managed Trading Account"
        verbose_name_plural = "Managed Trading Accounts"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['client', 'status']),
            models.Index(fields=['account_number']),
            models.Index(fields=['account_manager', 'status']),
        ]
    
    def __str__(self):
        return f"{self.account_number} - {self.client.get_full_name()}"
    
    @property
    def available_buying_power(self):
        """Calculate available buying power for new positions"""
        if self.cash_available is None or self.cash_reserved is None:
            return Decimal('0.00')
        return self.cash_available - self.cash_reserved
    
    @property
    def current_risk_exposure(self):
        """Calculate current risk exposure as % of balance"""
        if self.current_balance is None or self.current_balance == 0:
            return Decimal('0.00')
        open_positions = self.positions.filter(status='open')
        total_risk = sum([pos.max_loss for pos in open_positions])
        return (total_risk / self.current_balance) * 100
    
    @property
    def win_rate(self):
        """Calculate win rate percentage"""
        if self.total_trades > 0:
            return (self.winning_trades / self.total_trades) * 100
        return Decimal('0.00')
    
    @property
    def return_on_investment(self):
        """Calculate ROI percentage"""
        if self.initial_capital is None or self.initial_capital == 0:
            return Decimal('0.00')
        if self.current_balance is None:
            return Decimal('0.00')
        return ((self.current_balance - self.initial_capital) / self.initial_capital) * 100


class OptionsPosition(TimeStampedModel):
    """
    Individual options position/trade
    
    Tracks a single options position including entry/exit details,
    Greeks, P&L, and current status.
    """
    
    # Account Linkage
    managed_account = models.ForeignKey(
        ManagedTradingAccount,
        on_delete=models.CASCADE,
        related_name='positions'
    )
    
    # Batch Linkage (Phase 7)
    batch = models.ForeignKey(
        'PositionBatch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='positions',
        help_text="Batch this position belongs to (if requires approval)"
    )
    
    # Approval tracking
    requires_client_approval = models.BooleanField(
        default=True,
        help_text="Does this position require client approval via batch?"
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When position was approved (batch or session)"
    )
    approval_method = models.CharField(
        max_length=20,
        choices=[
            ('batch', 'Batch Approval'),
            ('session', 'Session Pre-Approved'),
            ('manual', 'Manual Staff Approval'),
        ],
        blank=True,
        help_text="How this position was approved"
    )
    approval_notes = models.TextField(
        blank=True,
        help_text="Notes about approval (e.g., session number)"
    )
    rejection_reason = models.TextField(
        blank=True,
        help_text="Reason for rejection (if applicable)"
    )
    
    # Position Details
    symbol = models.CharField(
        max_length=10,
        help_text="Underlying stock ticker (e.g., AAPL)"
    )
    
    STRATEGY_CHOICES = [
        ('short_put', 'Cash-Secured Short Put'),
        ('covered_call', 'Covered Call'),
        ('short_call', 'Naked Short Call'),
        ('bull_put_spread', 'Bull Put Spread'),
        ('bear_call_spread', 'Bear Call Spread'),
        ('iron_condor', 'Iron Condor'),
        ('long_call', 'Long Call'),
        ('long_put', 'Long Put'),
        ('straddle', 'Straddle'),
        ('strangle', 'Strangle'),
        ('other', 'Other Strategy')
    ]
    strategy = models.CharField(
        max_length=20,
        choices=STRATEGY_CHOICES,
        help_text="Options strategy type"
    )
    
    # Position Legs (stored as JSON for multi-leg strategies)
    positions = models.JSONField(
        help_text="Array of position legs with strike, type, contracts, etc."
    )
    
    # Financial Details
    capital_required = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Capital required/reserved for this position"
    )
    premium_collected = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Total premium collected (credit received)"
    )
    max_profit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Maximum possible profit"
    )
    max_loss = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Maximum possible loss"
    )
    
    # Greeks (at position level)
    position_delta = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        default=Decimal('0.0000'),
        help_text="Net position delta"
    )
    position_theta = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        default=Decimal('0.0000'),
        help_text="Net position theta (daily decay)"
    )
    position_gamma = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        default=Decimal('0.0000'),
        help_text="Net position gamma"
    )
    position_vega = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        default=Decimal('0.0000'),
        help_text="Net position vega"
    )
    
    # Dates
    entry_date = models.DateField(
        auto_now_add=True,
        help_text="Date position was opened"
    )
    expiration_date = models.DateField(
        help_text="Options expiration date"
    )
    exit_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date position was closed"
    )
    
    # Status
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('assigned', 'Assigned'),
        ('expired', 'Expired'),
        ('rolled', 'Rolled')
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='open'
    )
    
    # P&L Tracking
    current_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Current market value of position"
    )
    realized_pnl = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Realized profit/loss (for closed positions)"
    )
    unrealized_pnl = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Unrealized profit/loss (for open positions)"
    )
    
    # Exit Details
    EXIT_REASON_CHOICES = [
        ('profit_target', 'Profit Target Reached'),
        ('stop_loss', 'Stop Loss Hit'),
        ('expiration', 'Approaching Expiration'),
        ('delta_shift', 'Delta Shifted'),
        ('roll', 'Rolled to Next Cycle'),
        ('assignment', 'Assigned'),
        ('manual', 'Manual Close'),
        ('other', 'Other')
    ]
    exit_reason = models.CharField(
        max_length=20,
        choices=EXIT_REASON_CHOICES,
        null=True,
        blank=True,
        help_text="Reason for closing position"
    )
    exit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Price at which position was closed"
    )
    
    # Notes
    notes = models.TextField(
        blank=True,
        help_text="Trade notes, rationale, observations"
    )
    
    class Meta:
        verbose_name = "Options Position"
        verbose_name_plural = "Options Positions"
        ordering = ['-entry_date', 'expiration_date']
        indexes = [
            models.Index(fields=['managed_account', 'status']),
            models.Index(fields=['symbol', 'status']),
            models.Index(fields=['expiration_date', 'status']),
        ]
    
    def __str__(self):
        return f"{self.symbol} {self.get_strategy_display()} - {self.managed_account.account_number}"
    
    @property
    def days_in_trade(self):
        """Calculate number of days position has been open"""
        if self.exit_date:
            return (self.exit_date - self.entry_date).days
        return (date.today() - self.entry_date).days
    
    @property
    def days_to_expiration(self):
        """Calculate days until expiration"""
        return (self.expiration_date - date.today()).days
    
    @property
    def is_profitable(self):
        """Check if position is currently profitable"""
        if self.status == 'open':
            return self.unrealized_pnl > 0
        return self.realized_pnl > 0
    
    @property
    def profit_percentage(self):
        """Calculate profit as percentage of max profit"""
        if self.max_profit > 0:
            if self.status == 'open':
                return (self.unrealized_pnl / self.max_profit) * 100
            return (self.realized_pnl / self.max_profit) * 100
        return Decimal('0.00')


class TradingRule(TimeStampedModel):
    """
    Configurable trading rules per account
    
    Defines rules for position sizing, risk limits, profit targets,
    stop losses, and other trading constraints.
    """
    
    managed_account = models.ForeignKey(
        ManagedTradingAccount,
        on_delete=models.CASCADE,
        related_name='trading_rules'
    )
    
    rule_name = models.CharField(
        max_length=100,
        help_text="Descriptive name for the rule"
    )
    
    RULE_TYPE_CHOICES = [
        ('position_limit', 'Position Size Limit'),
        ('position_size_percentage', 'Position Size % of Capital'),  # NEW: Industry standard
        ('risk_limit', 'Risk Limit'),
        ('profit_target', 'Profit Target'),
        ('stop_loss', 'Stop Loss'),
        ('time_based', 'Time-Based Rule'),
        ('exposure_limit', 'Total Exposure Limit'),
        ('custom', 'Custom Rule')
    ]
    rule_type = models.CharField(
        max_length=30,  # Increased from 20 to accommodate longer type names
        choices=RULE_TYPE_CHOICES
    )
    
    # Rule Configuration (stored as JSON for flexibility)
    rule_config = models.JSONField(
        help_text="Rule parameters and thresholds"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Is this rule currently enforced"
    )
    priority = models.IntegerField(
        default=10,
        help_text="Rule priority (1=highest, 10=lowest)"
    )
    
    class Meta:
        verbose_name = "Trading Rule"
        verbose_name_plural = "Trading Rules"
        ordering = ['priority', 'rule_name']
        indexes = [
            models.Index(fields=['managed_account', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.rule_name} ({self.managed_account.account_number})"


class TradingActivity(TimeStampedModel):
    """
    Audit trail of all trading activities
    
    Logs every action taken on managed accounts including position
    entry/exit, rule changes, account modifications, etc.
    """
    
    managed_account = models.ForeignKey(
        ManagedTradingAccount,
        on_delete=models.CASCADE,
        related_name='activities'
    )
    
    position = models.ForeignKey(
        OptionsPosition,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activities',
        help_text="Related position (if applicable)"
    )
    
    ACTIVITY_TYPE_CHOICES = [
        ('account_created', 'Account Created'),
        ('account_modified', 'Account Modified'),
        ('account_paused', 'Account Paused'),
        ('account_activated', 'Account Activated'),
        ('position_opened', 'Position Opened'),
        ('position_closed', 'Position Closed'),
        ('position_rolled', 'Position Rolled'),
        ('pnl_adjusted', 'P&L Manually Adjusted'),  # NEW: For manual P&L edits
        ('alert_generated', 'Alert Generated'),
        ('rule_violated', 'Rule Violated'),
        ('rule_changed', 'Rule Changed'),
        ('fee_calculated', 'Fee Calculated'),
        ('session_completed', 'Coaching Session Completed'),
        ('other', 'Other Activity')
    ]
    activity_type = models.CharField(
        max_length=30,
        choices=ACTIVITY_TYPE_CHOICES
    )
    
    description = models.TextField(
        help_text="Human-readable description of the activity"
    )
    
    # Data Snapshot (stores state at time of activity)
    data_snapshot = models.JSONField(
        default=dict,
        help_text="JSON snapshot of relevant data"
    )
    
    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User who performed the action"
    )
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text="When this activity occurred"
    )
    
    class Meta:
        verbose_name = "Trading Activity"
        verbose_name_plural = "Trading Activities"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['managed_account', '-timestamp']),
            models.Index(fields=['activity_type', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.get_activity_type_display()} - {self.managed_account.account_number} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


class TradingSession(TimeStampedModel):
    """
    Track coaching/review sessions with clients
    For Consultative tier accounts
    """
    
    managed_account = models.ForeignKey(
        ManagedTradingAccount,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    
    session_date = models.DateTimeField(
        help_text="Date and time of session"
    )
    session_duration_minutes = models.IntegerField(
        default=30,
        help_text="Session duration in minutes"
    )
    
    SESSION_TYPE_CHOICES = [
        ('position_review', 'Position Review'),
        ('strategy_planning', 'Strategy Planning'),
        ('performance_review', 'Performance Review'),
        ('education', 'Education/Training'),
        ('risk_review', 'Risk Management Review')
    ]
    session_type = models.CharField(
        max_length=20,
        choices=SESSION_TYPE_CHOICES
    )
    
    # Session content
    topics_discussed = models.TextField(
        help_text="Topics covered in session"
    )
    positions_reviewed = models.ManyToManyField(
        OptionsPosition,
        blank=True,
        related_name='review_sessions',
        help_text="Positions discussed in session"
    )
    action_items = models.JSONField(
        default=list,
        help_text="Action items from session"
    )
    
    # Session notes
    session_notes = models.TextField(
        blank=True,
        help_text="Detailed session notes"
    )
    client_feedback = models.TextField(
        blank=True,
        help_text="Client feedback on session"
    )
    
    # Billing
    fee_charged = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal('50.00'),
        help_text="Fee charged for this session"
    )
    is_billed = models.BooleanField(
        default=False,
        help_text="Has this session been billed?"
    )
    billing_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date session was billed"
    )
    
    # Recording (optional)
    recording_url = models.URLField(
        blank=True,
        null=True,
        help_text="URL to session recording"
    )
    
    class Meta:
        verbose_name = "Trading Session"
        verbose_name_plural = "Trading Sessions"
        ordering = ['-session_date']
        indexes = [
            models.Index(fields=['managed_account', '-session_date']),
        ]
    
    def __str__(self):
        return f"{self.managed_account.account_number} - {self.session_date.strftime('%Y-%m-%d')}"


# ============================================================================
# PHASE 6: CLIENT ONBOARDING & COMPLIANCE MODELS
# ============================================================================

class FeeTierConfiguration(TimeStampedModel):
    """
    Configurable fee tier settings - editable in Django Admin
    Allows staff to update tier minimums, fees, descriptions without code changes
    """
    
    FEE_TIER_CHOICES = [
        ('starter', 'Starter - Automated Execution'),
        ('professional', 'Professional - Weekly Strategy'),
        ('premium', 'Premium - Enhanced Support'),
        ('consultative', 'Consultative - 1-on-1 Sessions'),
        ('co_invest', 'Co-Investment - Partnership'),
    ]
    
    # Tier identification
    tier_code = models.CharField(
        max_length=20,
        choices=FEE_TIER_CHOICES,
        unique=True,
        help_text="Unique identifier for this tier"
    )
    tier_name = models.CharField(
        max_length=100,
        help_text="Display name (e.g., 'Starter - Automated Execution')"
    )
    
    # Financial requirements
    minimum_capital = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Minimum capital required for this tier"
    )
    
    # Fee structure
    monthly_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Fixed monthly fee (set to 0 if none)"
    )
    profit_share_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Percentage of profits shared (e.g., 10 for 10%)"
    )
    per_session_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Fee per session (for consultative tier)"
    )
    max_sessions_per_month = models.IntegerField(
        default=0,
        help_text="Maximum sessions per month (0 if unlimited)"
    )
    
    # Descriptions for display
    short_description = models.CharField(
        max_length=200,
        help_text="Brief description for tier card"
    )
    
    # Features (stored as JSON for flexibility)
    features = models.JSONField(
        default=list,
        help_text="List of features (e.g., ['AI-driven trades', 'Real-time monitoring'])"
    )
    
    # Risk compatibility
    compatible_risk_levels = models.JSONField(
        default=list,
        help_text="Risk levels this tier is suitable for (e.g., ['low', 'medium'])"
    )
    
    # Active status
    is_active = models.BooleanField(
        default=True,
        help_text="Is this tier currently available?"
    )
    
    # Display order
    display_order = models.IntegerField(
        default=0,
        help_text="Order to display tiers (lower = first)"
    )
    
    class Meta:
        verbose_name = "Fee Tier Configuration"
        verbose_name_plural = "Fee Tier Configurations"
        ordering = ['display_order', 'minimum_capital']
    
    def __str__(self):
        return f"{self.tier_name} (Min: ${self.minimum_capital:,.0f})"
    
    @property
    def fee_display(self):
        """Human-readable fee structure"""
        parts = []
        if self.monthly_fee > 0:
            parts.append(f"${self.monthly_fee:.0f}/mo")
        if self.per_session_fee > 0:
            parts.append(f"${self.per_session_fee:.0f}/session")
        if self.profit_share_percentage > 0:
            parts.append(f"{self.profit_share_percentage:.0f}% profit")
        return " + ".join(parts) if parts else "Custom"
    
    @classmethod
    def get_tier_minimum(cls, tier_code):
        """Get minimum capital for a tier (fallback to hardcoded if not found)"""
        try:
            config = cls.objects.get(tier_code=tier_code, is_active=True)
            return config.minimum_capital
        except cls.DoesNotExist:
            # Fallback to hardcoded defaults
            defaults = {
                'starter': Decimal('5000.00'),
                'professional': Decimal('15000.00'),
                'premium': Decimal('25000.00'),
                'consultative': Decimal('25000.00'),
                'co_invest': Decimal('100000.00'),
            }
            return defaults.get(tier_code, Decimal('5000.00'))
    
    @classmethod
    def get_all_active_tiers(cls):
        """Get all active tier configurations"""
        return cls.objects.filter(is_active=True).order_by('display_order', 'minimum_capital')


class InvestorRiskProfile(TimeStampedModel):
    """
    Risk tolerance assessment for managed trading clients
    Based on 10-question questionnaire scoring 0-100
    """
    
    RISK_CATEGORY_CHOICES = [
        ('conservative', 'Conservative (0-30)'),
        ('moderate', 'Moderate (31-60)'),
        ('aggressive', 'Aggressive (61-100)'),
    ]
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='risk_profile'
    )
    
    # Questionnaire responses (stored as JSON)
    questionnaire_data = models.JSONField(
        help_text="All 10 question responses"
    )
    
    # Calculated risk score (0-100)
    risk_score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Total score from questionnaire (0-100)"
    )
    
    # Derived risk category
    risk_category = models.CharField(
        max_length=20,
        choices=RISK_CATEGORY_CHOICES,
        help_text="Conservative, Moderate, or Aggressive"
    )
    
    # Assessment metadata
    assessed_date = models.DateTimeField(
        auto_now_add=True,
        help_text="When assessment was completed"
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        help_text="Last time profile was updated"
    )
    
    # Validity
    is_current = models.BooleanField(
        default=True,
        help_text="Is this the current valid assessment?"
    )
    expires_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when reassessment is required (typically 1 year)"
    )
    
    class Meta:
        verbose_name = "Investor Risk Profile"
        verbose_name_plural = "Investor Risk Profiles"
        ordering = ['-assessed_date']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.risk_category} ({self.risk_score})"
    
    def save(self, *args, **kwargs):
        # Auto-set expiry date (1 year from assessment)
        if not self.expires_date:
            self.expires_date = timezone.now().date() + timedelta(days=365)
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        """Check if risk assessment has expired"""
        if self.expires_date:
            return timezone.now().date() > self.expires_date
        return False
    
    @property
    def recommended_tiers(self):
        """Get recommended fee tiers based on risk category"""
        if self.risk_category == 'conservative':
            return ['starter', 'professional', 'consultative']
        elif self.risk_category == 'moderate':
            return ['professional', 'premium', 'consultative']
        else:  # aggressive
            return ['premium', 'consultative', 'co_invest']


class ManagedTradingApplication(TimeStampedModel):
    """
    Client application for managed trading services
    Includes capital commitment, tier selection, and approval workflow
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn by Client'),
    ]
    
    FUNDING_METHOD_CHOICES = [
        ('wire', 'Wire Transfer'),
        ('ach', 'ACH Transfer'),
        ('check', 'Check'),
        ('crypto', 'Cryptocurrency'),
    ]
    
    # Applicant
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='trading_applications'
    )
    
    # Risk profile (required)
    risk_profile = models.ForeignKey(
        InvestorRiskProfile,
        on_delete=models.PROTECT,
        help_text="Must complete risk assessment first"
    )
    
    # Investment details
    initial_capital = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('5000.00'))],
        help_text="Initial capital to invest (minimum $5,000)"
    )
    
    fee_tier = models.CharField(
        max_length=20,
        choices=ManagedTradingAccount.FEE_TIER_CHOICES,
        help_text="Selected fee tier"
    )
    
    # Preferences
    preferred_manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_applications',
        limit_choices_to={'is_staff': True},
        help_text="Preferred account manager (optional)"
    )
    
    funding_method = models.CharField(
        max_length=20,
        choices=FUNDING_METHOD_CHOICES,
        default='wire'
    )
    
    # Application status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    applied_date = models.DateTimeField(
        auto_now_add=True
    )
    
    # Review
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_applications'
    )
    reviewed_date = models.DateTimeField(
        null=True,
        blank=True
    )
    
    # Approval/Rejection
    approval_notes = models.TextField(
        blank=True,
        help_text="Internal notes about approval decision"
    )
    rejection_reason = models.TextField(
        blank=True,
        help_text="Reason for rejection (shown to client)"
    )
    
    # Contract status
    contracts_generated = models.BooleanField(
        default=False,
        help_text="Have contracts been generated?"
    )
    all_contracts_signed = models.BooleanField(
        default=False,
        help_text="Have all required contracts been signed?"
    )
    
    # Created account (after approval)
    managed_account = models.OneToOneField(
        ManagedTradingAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='source_application',
        help_text="Created managed trading account"
    )
    
    class Meta:
        verbose_name = "Managed Trading Application"
        verbose_name_plural = "Managed Trading Applications"
        ordering = ['-applied_date']
        indexes = [
            models.Index(fields=['status', '-applied_date']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.fee_tier} ({self.status})"
    
    @property
    def risk_tier_match(self):
        """Check if selected tier matches risk profile"""
        recommended = self.risk_profile.recommended_tiers
        return self.fee_tier in recommended
    
    @property
    def capital_tier_match(self):
        """Check if capital meets tier minimum (using database configuration)"""
        try:
            tier_config = FeeTierConfiguration.objects.get(tier_code=self.fee_tier, is_active=True)
            return self.initial_capital >= tier_config.minimum_capital
        except FeeTierConfiguration.DoesNotExist:
            # Fallback to hardcoded minimums if config not found
            tier_minimums = {
                'starter': Decimal('5000.00'),
                'professional': Decimal('15000.00'),
                'premium': Decimal('25000.00'),
                'consultative': Decimal('25000.00'),
                'co_invest': Decimal('100000.00'),
            }
            return self.initial_capital >= tier_minimums.get(self.fee_tier, Decimal('5000.00'))
    
    @property
    def is_qualified_for_auto_approval(self):
        """
        Check if application qualifies for automatic approval
        Criteria:
        - Risk/tier match
        - Capital meets minimum
        - All contracts signed
        - No red flags
        """
        return (
            self.risk_tier_match and
            self.capital_tier_match and
            self.all_contracts_signed and
            self.status == 'pending'
        )


class ManagedTradingContract(TimeStampedModel):
    """
    Contracts for managed trading (extends base contract system)
    4 required contracts: IMA, Risk Disclosure, Fee Agreement, Terms
    """
    
    CONTRACT_TYPE_CHOICES = [
        ('ima', 'Investment Management Agreement'),
        ('risk_disclosure', 'Options Trading Risk Disclosure'),
        ('fee_agreement', 'Fee Schedule Agreement'),
        ('terms', 'Terms of Service'),
    ]
    
    # Link to application or account
    application = models.ForeignKey(
        ManagedTradingApplication,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='contracts',
        help_text="Application this contract belongs to"
    )
    
    managed_account = models.ForeignKey(
        ManagedTradingAccount,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='contracts',
        help_text="Account this contract belongs to (if approved)"
    )
    
    # Contract details
    contract_type = models.CharField(
        max_length=20,
        choices=CONTRACT_TYPE_CHOICES
    )
    
    title = models.CharField(
        max_length=200,
        help_text="Contract title"
    )
    
    # Contract content
    contract_text = models.TextField(
        help_text="Full contract text (can be HTML)"
    )
    
    # Signature
    is_signed = models.BooleanField(
        default=False
    )
    signature_data = models.TextField(
        blank=True,
        help_text="Base64 encoded signature image"
    )
    signed_date = models.DateTimeField(
        null=True,
        blank=True
    )
    signature_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address where contract was signed"
    )
    
    # PDF generation
    pdf_generated = models.BooleanField(
        default=False
    )
    pdf_url = models.URLField(
        blank=True,
        null=True,
        help_text="URL to signed PDF"
    )
    
    class Meta:
        verbose_name = "Managed Trading Contract"
        verbose_name_plural = "Managed Trading Contracts"
        ordering = ['contract_type']
        unique_together = [['application', 'contract_type']]
    
    def __str__(self):
        if self.application:
            return f"{self.application.user.get_full_name()} - {self.get_contract_type_display()}"
        return f"{self.title} - {self.get_contract_type_display()}"
    
    def sign(self, signature_data, ip_address=None):
        """Sign the contract"""
        self.is_signed = True
        self.signature_data = signature_data
        self.signed_date = timezone.now()
        self.signature_ip = ip_address
        self.save()
        
        # Check if all contracts for application are signed
        if self.application:
            all_signed = not self.application.contracts.filter(is_signed=False).exists()
            if all_signed:
                self.application.all_contracts_signed = True
                self.application.save()


# ============================================================================
# PHASE 7: BATCH APPROVAL SYSTEM
# ============================================================================

class PositionBatch(TimeStampedModel):
    """
    Weekly batch of positions for client approval
    Positions must be approved within 24 hours or auto-rejected
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending Client Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected by Client'),
        ('expired', 'Expired (24hr timeout)'),
        ('partial', 'Partially Approved'),
    ]
    
    # Account
    managed_account = models.ForeignKey(
        ManagedTradingAccount,
        on_delete=models.CASCADE,
        related_name='position_batches'
    )
    
    # Batch identification
    batch_number = models.CharField(
        max_length=50,
        unique=True,
        help_text="Format: BATCH-YYYY-Wxx (e.g., BATCH-2025-W47)"
    )
    
    # Timing
    created_date = models.DateTimeField(
        auto_now_add=True
    )
    approval_deadline = models.DateTimeField(
        help_text="Client must approve before this time (24 hours from creation)"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # Client approval
    approved_date = models.DateTimeField(
        null=True,
        blank=True
    )
    approval_signature = models.TextField(
        blank=True,
        help_text="Base64 encoded signature for batch approval"
    )
    approval_ip = models.GenericIPAddressField(
        null=True,
        blank=True
    )
    
    # Batch summary
    total_positions = models.IntegerField(
        default=0,
        help_text="Number of positions in batch"
    )
    total_capital_required = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total capital required for all positions"
    )
    
    # Notification tracking
    reminder_sent = models.BooleanField(
        default=False,
        help_text="Was 12-hour reminder sent?"
    )
    timeout_notification_sent = models.BooleanField(
        default=False,
        help_text="Was timeout notification sent?"
    )
    
    # Real-time notification tracking (Phase 9: Real-time Client Approval)
    whatsapp_notification_sent = models.BooleanField(
        default=False,
        help_text="Was WhatsApp notification sent?"
    )
    whatsapp_notification_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When WhatsApp notification was sent"
    )
    sms_notification_sent = models.BooleanField(
        default=False,
        help_text="Was SMS notification sent?"
    )
    sms_notification_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When SMS notification was sent"
    )
    
    # Approval method tracking
    APPROVAL_METHOD_CHOICES = [
        ('whatsapp', 'WhatsApp Reply'),
        ('sms', 'SMS Reply'),
        ('portal', 'Client Portal'),
        ('email', 'Email Link'),
        ('phone', 'Phone Call'),
    ]
    approval_method = models.CharField(
        max_length=20,
        choices=APPROVAL_METHOD_CHOICES,
        blank=True,
        help_text="How client approved this batch"
    )
    
    # Quick approval token (for WhatsApp/SMS replies)
    approval_token = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        unique=True,
        help_text="Token for quick approval via WhatsApp/SMS"
    )
    
    class Meta:
        verbose_name = "Position Batch"
        verbose_name_plural = "Position Batches"
        ordering = ['-created_date']
        indexes = [
            models.Index(fields=['managed_account', '-created_date']),
            models.Index(fields=['status', 'approval_deadline']),
        ]
    
    def __str__(self):
        return f"{self.batch_number} - {self.managed_account.account_number} ({self.status})"
    
    @property
    def is_expired(self):
        """Check if batch has passed approval deadline"""
        return timezone.now() > self.approval_deadline and self.status == 'pending'
    
    @property
    def time_remaining(self):
        """Calculate time remaining until deadline"""
        if self.status != 'pending':
            return timedelta(0)
        remaining = self.approval_deadline - timezone.now()
        return remaining if remaining.total_seconds() > 0 else timedelta(0)
    
    @property
    def hours_remaining(self):
        """Get hours remaining as integer"""
        return int(self.time_remaining.total_seconds() / 3600)
    
    @property
    def is_pending(self):
        """Check if batch is pending approval"""
        return self.status == 'pending' and not self.is_expired
    
    def expire_batch(self):
        """
        Auto-reject all positions after 24-hour timeout
        Called by cron job
        """
        self.status = 'expired'
        self.save()
        
        # Reject all pending positions in batch
        for position in self.positions.filter(status='pending'):
            position.status = 'rejected'
            position.rejection_reason = 'Batch approval timeout (24 hours) - automatically rejected'
            position.save()
        
        return self.positions.count()
    
    def approve_all(self, signature_data, ip_address=None):
        """
        Approve all positions in batch
        Called when client approves entire batch
        Deducts capital from account balance
        """
        from django.db import transaction
        
        with transaction.atomic():
            self.status = 'approved'
            self.approved_date = timezone.now()
            self.approval_signature = signature_data
            self.approval_ip = ip_address
            self.save()
            
            # Get account
            account = self.managed_account
            
            # Open all positions and deduct balance
            approved_count = 0
            total_capital_deployed = Decimal('0.00')
            
            for position in self.positions.all():
                if position.status == 'pending':
                    position.status = 'open'
                    position.approved_at = timezone.now()
                    position.save()
                    
                    # Deduct capital from account
                    account.cash_reserved += position.capital_required
                    account.cash_available -= position.capital_required
                    
                    total_capital_deployed += position.capital_required
                    approved_count += 1
            
            # Save account balance changes
            if approved_count > 0:
                account.save(update_fields=['cash_reserved', 'cash_available', 'updated_at'])
            
            return approved_count
    
    def reject_all(self, reason="Rejected by client"):
        """Reject all positions in batch"""
        self.status = 'rejected'
        self.save()
        
        # Reject all positions
        rejected_count = self.positions.update(
            status='rejected',
            rejection_reason=reason
        )
        
        return rejected_count


# ============================================================================
# POSITION AUTOMATION: AUTO-FETCHED POSITIONS
# ============================================================================

class SuggestedPosition(TimeStampedModel):
    """
    Auto-fetched positions from OptionPlay/Thinkorswim pending staff review
    
    Workflow:
    1. Daily fetch from APIs → Creates SuggestedPosition (status=pending)
    2. Staff reviews/edits → Updates status to approved/modified/rejected
    3. Staff creates batch → Converts to OptionsPosition objects
    4. Client approves batch → Positions become active
    """
    
    # Source tracking
    SOURCE_CHOICES = [
        ('optionplay', 'OptionPlay API'),
        ('thinkorswim', 'Thinkorswim/TD Ameritrade'),
        ('manual', 'Manual Entry'),
    ]
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        help_text="Where this position was sourced from"
    )
    fetched_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When position was fetched from API"
    )
    
    # Position Details (same structure as OptionsPosition)
    symbol = models.CharField(
        max_length=10,
        help_text="Underlying stock ticker (e.g., AAPL, TSLA)"
    )
    
    STRATEGY_CHOICES = [
        ('short_put', 'Cash-Secured Short Put'),
        ('covered_call', 'Covered Call'),
        ('bull_put_spread', 'Bull Put Spread'),
        ('bear_call_spread', 'Bear Call Spread'),
        ('bull_call_spread', 'Bull Call Spread'),
        ('bear_put_spread', 'Bear Put Spread'),
        ('iron_condor', 'Iron Condor'),
        ('long_call', 'Long Call'),
        ('long_put', 'Long Put'),
        ('other', 'Other Strategy')
    ]
    strategy = models.CharField(
        max_length=30,
        choices=STRATEGY_CHOICES,
        help_text="Options strategy type"
    )
    
    # Position Legs (JSON for multi-leg strategies)
    positions = models.JSONField(
        help_text="Array of position legs: [{type, strike, contracts, premium, delta, theta}]"
    )
    
    # Dates
    expiration_date = models.DateField(
        help_text="Option expiration date"
    )
    dte = models.IntegerField(
        help_text="Days to expiration (calculated at fetch time)"
    )
    
    # Financial Metrics
    premium_collected = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Total premium collected/paid"
    )
    capital_required = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Capital required for position"
    )
    max_profit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Maximum possible profit"
    )
    max_loss = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Maximum possible loss"
    )
    breakeven = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Breakeven price"
    )
    
    # HIGH PROBABILITY INDICATORS (Key filtering criteria)
    probability_of_profit = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Probability of profit % (e.g., 75.00 = 75%)"
    )
    
    # Greeks (at position level)
    position_delta = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        default=Decimal('0.0000'),
        help_text="Net position delta"
    )
    position_theta = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        default=Decimal('0.0000'),
        help_text="Net position theta (daily time decay)"
    )
    position_gamma = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        default=Decimal('0.0000'),
        help_text="Net position gamma"
    )
    position_vega = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        default=Decimal('0.0000'),
        help_text="Net position vega (volatility sensitivity)"
    )
    
    # AI/API Metadata
    api_response_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Raw API response for reference"
    )
    ai_confidence = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="AI confidence score (0-100) - DEPRECATED, use ai_score instead"
    )
    ai_reasoning = models.TextField(
        blank=True,
        help_text="Why AI recommended this position - DEPRECATED, use ai_recommendation instead"
    )
    
    # AI Position Scoring (6-Factor Algorithm) - NEW
    ai_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="AI position score (0-100) from 6-factor algorithm"
    )
    ai_rating = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        choices=[
            ('EXCELLENT', 'Excellent (95-100)'),
            ('GOOD', 'Good (85-94)'),
            ('AVERAGE', 'Average (70-84)'),
            ('BELOW_AVERAGE', 'Below Average (50-69)'),
            ('POOR', 'Poor (0-49)'),
        ],
        help_text="AI rating based on score"
    )
    ai_breakdown = models.JSONField(
        default=dict,
        blank=True,
        help_text="Detailed breakdown of 6 scoring factors"
    )
    ai_recommendation = models.TextField(
        blank=True,
        help_text="AI recommendation text (approve/review/reject)"
    )
    ai_confidence_level = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        choices=[
            ('HIGH', 'High Confidence'),
            ('MEDIUM', 'Medium Confidence'),
            ('LOW', 'Low Confidence'),
        ],
        help_text="Confidence level based on data availability"
    )
    
    # Staff Review
    REVIEW_STATUS_CHOICES = [
        ('pending', 'Pending Staff Review'),
        ('approved', 'Approved by Staff'),
        ('modified', 'Modified & Approved'),
        ('rejected', 'Rejected by Staff'),
        ('converted', 'Converted to Batch'),
    ]
    review_status = models.CharField(
        max_length=20,
        choices=REVIEW_STATUS_CHOICES,
        default='pending',
        help_text="Staff review status"
    )
    
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_suggested_positions',
        limit_choices_to={'is_staff': True},
        help_text="Staff member who reviewed this"
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When staff reviewed this position"
    )
    staff_notes = models.TextField(
        blank=True,
        help_text="Staff comments, modifications, or rejection reasons"
    )
    
    # System-generated notes (technical analysis, cross-validation, etc.)
    notes = models.TextField(
        blank=True,
        help_text="System-generated notes (technical analysis, cross-validation, flow signals, etc.)"
    )
    
    # Link to created position (if approved and converted)
    created_position = models.OneToOneField(
        'OptionsPosition',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='source_suggestion',
        help_text="Actual position created from this suggestion"
    )
    
    # Target account (if pre-assigned by staff)
    target_account = models.ForeignKey(
        'ManagedTradingAccount',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='suggested_positions',
        help_text="Which account this position is intended for (optional)"
    )
    
    class Meta:
        verbose_name = "Suggested Position"
        verbose_name_plural = "Suggested Positions"
        ordering = ['-probability_of_profit', '-fetched_at']
        indexes = [
            models.Index(fields=['review_status', '-fetched_at']),
            models.Index(fields=['source', 'review_status']),
            models.Index(fields=['-probability_of_profit']),
        ]
    
    def __str__(self):
        return f"{self.symbol} {self.strategy} ({self.probability_of_profit}% prob) - {self.get_review_status_display()}"
    
    @property
    def risk_reward_ratio(self):
        """Calculate risk/reward ratio"""
        if self.max_loss and self.max_loss != 0:
            return float(self.max_profit / abs(self.max_loss))
        return 0.0
    
    @property
    def meets_criteria(self):
        """Check if position meets high-probability criteria"""
        return (
            self.probability_of_profit >= Decimal('70.00') and  # 70%+ probability
            self.premium_collected >= Decimal('100.00') and     # $100+ premium
            30 <= self.dte <= 60                                 # 30-60 DTE
        )
    
    def approve(self, staff_user, notes=''):
        """Approve this suggestion"""
        self.review_status = 'approved'
        self.reviewed_by = staff_user
        self.reviewed_at = timezone.now()
        if notes:
            self.staff_notes = notes
        self.save()
    
    def reject(self, staff_user, reason):
        """Reject this suggestion"""
        self.review_status = 'rejected'
        self.reviewed_by = staff_user
        self.reviewed_at = timezone.now()
        self.staff_notes = reason
        self.save()
    
    def modify(self, staff_user, updated_data, notes=''):
        """Modify position details and mark as modified"""
        # Update position details
        for field, value in updated_data.items():
            if hasattr(self, field):
                setattr(self, field, value)
        
        self.review_status = 'modified'
        self.reviewed_by = staff_user
        self.reviewed_at = timezone.now()
        self.staff_notes = f"Modified: {notes}" if notes else "Modified by staff"
        self.save()


# ============================================================================
# OPTIONPLAY RAW DATA: Manual CSV Upload Fallback
# ============================================================================

class OptionPlayRawData(TimeStampedModel):
    """
    Raw data manually uploaded from OptionPlay CSV exports
    Serves as fallback when Playwright scraper fails on Heroku
    
    Workflow:
    1. Staff downloads CSV from OptionPlay.com
    2. Uploads via Django admin
    3. System converts to SuggestedPosition format
    4. Regular approval workflow continues
    
    Supports 3 CSV formats:
    - Credit Spreads (Bull Put, Bear Call)
    - Short Puts (Cash-Secured)
    - Covered Calls
    """
    
    # Source tracking
    STRATEGY_TYPE_CHOICES = [
        ('credit_spread', 'Credit Spread'),
        ('bull_put_spread', 'Bull Put Spread'),
        ('bear_call_spread', 'Bear Call Spread'),
        ('iron_condor', 'Iron Condor'),
        ('short_put', 'Short Put'),
        ('covered_call', 'Covered Call'),
        ('short_call', 'Short Call'),
    ]
    strategy_type = models.CharField(
        max_length=30,  # Increased from 20 to fit 'bull_put_spread'
        choices=STRATEGY_TYPE_CHOICES,
        help_text="Type of position from CSV"
    )
    
    # Core position data
    symbol = models.CharField(max_length=10, help_text="Stock ticker symbol")
    
    # Credit Spread specific fields
    spread_strategy = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Bearish or Bullish (for credit spreads)"
    )
    option_type = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        help_text="Call or Put (for credit spreads)"
    )
    stock_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Current stock price"
    )
    sell_strike = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Short leg strike price"
    )
    buy_strike = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Long leg strike price (null for naked short puts)"
    )
    
    # Common fields
    expiry = models.DateField(help_text="Option expiration date")
    days_to_expiry = models.IntegerField(help_text="Days to expiration at upload time")
    premium = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Premium collected per contract"
    )
    
    # Spread metrics (for credit spreads)
    width = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Spread width (for spreads only)"
    )
    prem_width_ratio = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Premium/Width ratio (%) - indicates edge"
    )
    
    # Volatility and Greeks
    iv_rank = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Implied Volatility Rank (%)"
    )
    
    # Returns (for short puts/covered calls)
    raw_return = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Return on capital if held to expiration (%)"
    )
    annualized_return = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Annualized return (%)"
    )
    distance_to_strike = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="% distance from current price to strike (negative = OTM)"
    )
    
    # Earnings info
    earnings_date = models.CharField(
        max_length=50,
        blank=True,
        help_text="Earnings date from CSV"
    )
    earnings_flag = models.CharField(
        max_length=5,
        blank=True,
        help_text="Y/N - position includes earnings"
    )
    
    # Upload tracking
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_optionplay_data',
        limit_choices_to={'is_staff': True}
    )
    upload_date = models.DateTimeField(auto_now_add=True)
    upload_notes = models.TextField(blank=True, help_text="Notes about this upload batch")
    
    # Processing status
    is_processed = models.BooleanField(
        default=False,
        help_text="Has this been converted to SuggestedPosition?"
    )
    processed_date = models.DateTimeField(null=True, blank=True)
    created_suggestion = models.ForeignKey(
        'SuggestedPosition',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='source_raw_data'
    )
    processing_error = models.TextField(blank=True, help_text="Error message if conversion failed")
    
    # Raw CSV data (for reference)
    csv_row_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Original CSV row as JSON"
    )
    
    class Meta:
        verbose_name = "OptionPlay Raw Data"
        verbose_name_plural = "OptionPlay Raw Data Uploads"
        ordering = ['-upload_date', 'symbol']
        indexes = [
            models.Index(fields=['strategy_type', 'is_processed']),
            models.Index(fields=['symbol', 'expiry']),
            models.Index(fields=['is_processed', 'upload_date']),
        ]
    
    def __str__(self):
        return f"{self.symbol} {self.get_strategy_type_display()} - {self.expiry}"
    
    @property
    def is_expired(self):
        """Check if position is past expiration"""
        if not self.expiry:
            return False
        return self.expiry < timezone.now().date()
    
    @property
    def calculated_dte(self):
        """Calculate current DTE"""
        if not self.expiry:
            return None
        return (self.expiry - timezone.now().date()).days
    
    def convert_to_suggestion(self) -> 'SuggestedPosition':
        """
        Convert this raw data to a SuggestedPosition
        
        Returns:
            SuggestedPosition instance
        """
        from .services.optionplay_converter import OptionPlayConverterService
        converter = OptionPlayConverterService()
        return converter.convert_raw_to_suggestion(self)


# ============================================================================
# AI POSITION SCORING: MACHINE LEARNING FOR TRADE SELECTION
# ============================================================================

class OptionsPositionHistory(TimeStampedModel):
    """
    Historical outcomes of closed positions - enables ML-powered scoring
    
    Purpose:
    - Track every position outcome (win/loss, ROI, duration)
    - Learn which setups work best
    - Train AI scoring model
    - Improve future position selection
    
    Data Collection:
    - Auto-populated when position closes (via signal)
    - Captures entry conditions for ML features
    - AI analyzes why position succeeded/failed
    
    ML Features:
    - Symbol historical win rate
    - Strategy effectiveness
    - IV rank patterns
    - Market condition correlation
    - Earnings impact
    
    Based on: InvestmentAnalytics model (proven pattern)
    """
    
    # Link to original position
    position = models.OneToOneField(
        OptionsPosition,
        on_delete=models.CASCADE,
        related_name='outcome_history',
        help_text="Original position that was closed"
    )
    
    # Outcome Metrics
    was_profitable = models.BooleanField(
        help_text="True if position made money"
    )
    actual_return_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Actual profit/loss in dollars"
    )
    actual_return_percentage = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text="ROI as percentage of capital required"
    )
    days_held = models.IntegerField(
        help_text="Number of days position was open"
    )
    annualized_return = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text="Return annualized (ROI * 365 / days_held)"
    )
    
    # Exit Details
    exit_reason = models.CharField(
        max_length=50,
        choices=[
            ('profit_target', 'Hit Profit Target'),
            ('stop_loss', 'Hit Stop Loss'),
            ('expiration', 'Held to Expiration'),
            ('early_close', 'Early Close (Manual)'),
            ('rolled', 'Rolled to New Position'),
            ('market_conditions', 'Market Conditions Changed'),
            ('other', 'Other Reason')
        ],
        default='expiration'
    )
    exit_notes = models.TextField(blank=True, help_text="Why position was closed")
    
    # Entry Conditions (ML Features - snapshot at entry time)
    entry_iv_rank = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="IV Rank when position opened (0-100)"
    )
    entry_market_trend = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        choices=[
            ('strong_bullish', 'Strong Bullish'),
            ('bullish', 'Bullish'),
            ('neutral', 'Neutral'),
            ('bearish', 'Bearish'),
            ('strong_bearish', 'Strong Bearish')
        ],
        help_text="Market trend at entry"
    )
    entry_vix = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="VIX level at entry"
    )
    entry_stock_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Stock price when position opened"
    )
    days_to_earnings = models.IntegerField(
        null=True,
        blank=True,
        help_text="Days until next earnings when opened"
    )
    
    # Exit Conditions (for analysis)
    exit_stock_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Stock price when closed"
    )
    max_profit_captured = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="% of max profit captured (50% = closed at 50% target)"
    )
    
    # AI Analysis
    ai_post_analysis = models.TextField(
        blank=True,
        help_text="AI-generated analysis of why position succeeded/failed"
    )
    ai_confidence_at_entry = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="AI confidence score when position was opened"
    )
    
    # Performance Categorization
    performance_category = models.CharField(
        max_length=20,
        choices=[
            ('excellent', 'Excellent (>30% ROI)'),
            ('good', 'Good (15-30% ROI)'),
            ('average', 'Average (5-15% ROI)'),
            ('poor', 'Poor (0-5% ROI)'),
            ('loss', 'Loss (<0% ROI)')
        ],
        blank=True,
        help_text="Auto-categorized performance"
    )
    
    class Meta:
        verbose_name = "Options Position History"
        verbose_name_plural = "Options Position Histories"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['was_profitable', 'actual_return_percentage']),
            models.Index(fields=['entry_market_trend', 'was_profitable']),
            models.Index(fields=['performance_category']),
            models.Index(fields=['exit_reason']),
        ]
    
    def __str__(self):
        profit_loss = "WIN" if self.was_profitable else "LOSS"
        return f"{self.position.symbol} {self.position.strategy} - {profit_loss} ({self.actual_return_percentage}%)"
    
    @property
    def risk_reward_realized(self):
        """Actual risk/reward that was realized"""
        if self.position.max_loss and self.position.max_loss > 0:
            return abs(self.actual_return_amount / self.position.max_loss)
        return Decimal('0')
    
    @property
    def holding_efficiency(self):
        """How efficiently was the position held? (annualized return / days held)"""
        if self.days_held > 0:
            return self.annualized_return / Decimal(str(self.days_held))
        return Decimal('0')
    
    def save(self, *args, **kwargs):
        """Auto-categorize performance on save"""
        if self.actual_return_percentage:
            roi = self.actual_return_percentage
            if roi > 30:
                self.performance_category = 'excellent'
            elif roi > 15:
                self.performance_category = 'good'
            elif roi > 5:
                self.performance_category = 'average'
            elif roi > 0:
                self.performance_category = 'poor'
            else:
                self.performance_category = 'loss'
        
        super().save(*args, **kwargs)