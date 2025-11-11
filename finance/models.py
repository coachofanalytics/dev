from django.db import models

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
