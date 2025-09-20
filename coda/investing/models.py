from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.core.exceptions import ValidationError
from decimal import *
from django.utils import timezone
from datetime import datetime, date
from django.urls import reverse
from main.models import TimeStampedModel
from django.contrib.auth import get_user_model

# from finance.utils import get_exchange_rate
User = get_user_model()

# Create your models here.


class Investor_Information(TimeStampedModel):
    """
    Unified model for all investor types in CODA
    Supports Individual, Angel, VC, Private, and Equity investors
    """

    MODEL_CHOICES = [
        ("Revenue", "Revenue"),
        ("Installment", "Installment"),
        ("Options", "Options"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("active", "Active"),
        ("completed", "Completed"),
        ("paused", "Paused"),
        ("cancelled", "Cancelled"),
    ]

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
    company_rep = models.CharField(max_length=255, blank=True, null=True)
    contract_date = models.DateField(auto_now_add=True, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    client_signature = models.ImageField(upload_to="signatures/", blank=True, null=True)

    # New metadata fields
    contract_signed = models.BooleanField(default=False)
    contract_signed_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

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
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "InvestmentContent"

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


class Portifolio(TimeStampedModel):

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
        verbose_name_plural = "portifolio"
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
