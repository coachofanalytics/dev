from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.db.models import Q
from django.utils.text import slugify

from django.core.exceptions import ValidationError

from django.urls import reverse
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.auth.models import User






class InvestmentStrategy(models.Model):
   
    symbol = models.CharField(max_length=50, help_text="e.g., AAPL, TSLA")
    action = models.CharField(max_length=50, help_text="e.g., BUY, SELL, IRON CONDOR")
    expiry = models.DateField()
    day_to_expiry = models.IntegerField()
    earnings_date = models.DateField()
    earning_flag = models.BooleanField(default=False)
    on_date = models.DateField()
    closing_date = models.DateField(null=True, blank=True)
    strike_price = models.DecimalField(max_digits=12, decimal_places=2)
    mid_price = models.DecimalField(max_digits=12, decimal_places=2)
    ask_price = models.DecimalField(max_digits=12, decimal_places=2)
    iv_rank = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="IV Rank")
    stock_price = models.DecimalField(max_digits=12, decimal_places=2)
    raw_return = models.DecimalField(max_digits=10, decimal_places=4)
    annualized_return = models.DecimalField(max_digits=10, decimal_places=4)
    opening = models.DecimalField(max_digits=12, decimal_places=2)
    closing = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)  
    comment = models.TextField()
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Investment Strategy"
        verbose_name_plural = "Investment Strategies"
        ordering = ['-on_date']

    def __str__(self):
        return f"{self.symbol} - {self.action} ({self.on_date})"







class Daily_Trades(models.Model):
  
    symbol = models.CharField(max_length=255, null=True, blank=True)
    transaction = models.CharField(max_length=255, null=True, blank=True)
    price = models.DecimalField(max_digits=19,decimal_places=4,null=False,blank=False)
    strike_price = models.DecimalField(max_digits=19,decimal_places=4,null=False,blank=False)


    ACTION_TYPES = [
        ('BTO', 'Buy to Open'),
        ('STO', 'Sell to Open'),
        ('BTC', 'Buy to Close'),
        ('STC', 'Sell to Close'),
    ]
    action = models.CharField(max_length=255,choices=ACTION_TYPES,null=True,blank=True)
    qty = models.IntegerField(null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    expiry = models.DateField(null=True, blank=True)
    account_type = models.CharField(max_length=255, null=True, blank=True)
    page_number = models.CharField(max_length=255, null=True, blank=True)
    credit = models.DecimalField(max_digits=19,decimal_places=4,null=False,blank=False)
    debit = models.DecimalField(max_digits=19,decimal_places=4,null=False,blank=False)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "daily_trades"
        ordering = ["-date"]
        indexes = [
            models.Index(fields=["symbol"]),
            models.Index(fields=["date"]),
            models.Index(fields=["action"]),
            models.Index(fields=["account_type"]),
        ]

    def clean(self):
        """
        Business validation rules
        """
        # Ensure decimals are non-negative
        for field in ["price", "strike_price", "credit", "debit"]:
            value = getattr(self, field)
            if value is not None and value < 0:
                raise ValidationError({field: "Value cannot be negative."})

        # Options validation: strike price implies expiry
        if self.strike_price and not self.expiry:
            raise ValidationError({
                "expiry": "Expiry date is required when strike price is provided."})
        if self.qty is not None and self.qty <= 0:
            raise ValidationError({"qty": "Quantity must be greater than zero." })

    def __str__(self):
        return f"{self.symbol} | {self.action} | {self.date}"


