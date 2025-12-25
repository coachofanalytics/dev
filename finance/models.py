from django.db import models
from decimal import Decimal
from django.db import models
from django.utils import timezone

# Create your models here.
from django.utils import timezone


# # Create your models here.


class FinanceRecord(models.Model):
    category = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name_plural = "Finance Records"

    def __str__(self):
        return f"{self.category} - {self.amount}"


class OverBoughtSold(models.Model):
    symbol = models.CharField(max_length=50, null=True, blank=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    last = models.FloatField(null=True, blank=True, help_text="Last traded stock price")
    volume = models.PositiveIntegerField(null=True, blank=True)
    RSI = models.FloatField(null=True, blank=True, help_text="Relative Strength Index")
    EPS = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Earnings Per Share",
    )
    PE = models.FloatField(null=True, blank=True, help_text="Price-to-Earnings Ratio")
    rank = models.CharField(max_length=255, null=True, blank=True)
    profit_margins = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Profit margin (%)",
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Overbought/Oversold Stocks"
        ordering = ["-created_at"]

    def __str__(self):
        return self.symbol if self.symbol else "No Symbol"

    @property
    def status(self):
        """
        Returns the stock condition based on RSI value.
        RSI > 70 = Overbought
        RSI < 30 = Oversold
        Otherwise = Neutral
        """
        if self.RSI is None:
            return "Unknown"

        try:
            rsi_value = float(self.RSI)

            if rsi_value > 70:
                return "Overbought"
            elif rsi_value < 30:
                return "Oversold"
            return "Neutral"
        except (ValueError, TypeError):
            return "Unknown"

from django.db import models
from decimal import Decimal
from django.utils import timezone

class PaymentInformation(models.Model):
    PAYMENT_METHOD_CHOICES = (
        ("Cash", "Cash"),
        ("Mpesa", "Mpesa"),
        ("Bank Transfer", "Bank Transfer"),
        ("Card", "Card"),
        ("Other", "Other"),
    )

    customer = models.ForeignKey(
        "accounts.CustomerUser",
        on_delete=models.CASCADE,
        related_name="payment_infos"
    )

    total_fees = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    down_payment = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    student_bonus = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    remaining_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES, default="Cash")
    contract_submitted_date = models.DateTimeField(default=timezone.now)
    client_signature = models.CharField(max_length=1000, blank=True, default="")
    company_rep = models.CharField(max_length=1000, blank=True, default="")
    is_active = models.BooleanField(default=True)
    is_tested = models.BooleanField(default=False)
    is_reviewed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "-created_at"]

    @property
    def computed_balance(self):
        return (self.total_fees or 0) - ((self.down_payment or 0) + (self.student_bonus or 0))

    def save(self, *args, **kwargs):
        self.remaining_balance = self.computed_balance
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.customer} | Fees {self.total_fees} | Bal {self.remaining_balance}"
