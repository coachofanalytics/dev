from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.db.models import Q
from django.utils.text import slugify
from django.db.models.signals import pre_save

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