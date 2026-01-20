"""
AI Prediction Cache - Self-Learning System

Caches AI predictions to avoid repeated API calls.
System becomes smarter over time as cache grows.

3-Tier Architecture:
- Tier 1: Historical transactions (95% coverage, FREE)
- Tier 2: AI cache (4% coverage, FREE) 
- Tier 3: AI API (1% coverage, ~$1/month)
"""
from django.db import models
from django.utils import timezone
from datetime import timedelta


class AIPredictionCache(models.Model):
    """
    Caches AI predictions to avoid repeated API calls
    """
    # Input parameters (cache key)
    receiver_name = models.CharField(max_length=200, db_index=True)
    department = models.ForeignKey('accounts.Department', null=True, blank=True, on_delete=models.SET_NULL)
    amount_range_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    amount_range_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    context_hash = models.CharField(max_length=64, db_index=True, unique=True)  # MD5 of all inputs
    
    # AI Response (cached value)
    predicted_category = models.ForeignKey('finance.BudgetCategory', on_delete=models.CASCADE, null=True, blank=True)
    predicted_subcategory = models.ForeignKey('finance.BudgetSubCategory', null=True, blank=True, on_delete=models.SET_NULL)
    predicted_item = models.CharField(max_length=200)
    predicted_amount = models.DecimalField(max_digits=10, decimal_places=2)
    predicted_description = models.TextField()
    
    # Metadata
    ai_provider = models.CharField(
        max_length=50,
        choices=[
            ('historical', 'Historical Data (Free)'),
            ('openai', 'OpenAI GPT-4'),
            ('claude', 'Anthropic Claude'),
            ('dummy', 'Dummy AI (Testing)'),
        ],
        default='historical'
    )
    confidence_score = models.IntegerField(default=0, help_text='0-100')  
    ai_reasoning = models.TextField(blank=True)  # Why AI made this prediction
    tokens_used = models.IntegerField(default=0)
    api_cost = models.DecimalField(max_digits=8, decimal_places=4, default=0)  # Cost in USD
    
    # Cache management
    times_used = models.IntegerField(default=0, help_text='How many times this prediction was reused')
    last_used = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)  # Cache expiration
    
    # Validation
    user_confirmed = models.BooleanField(default=False, help_text='Did user accept this prediction?')
    user_modified = models.BooleanField(default=False, help_text='Did user change it?')
    accuracy_score = models.IntegerField(null=True, blank=True, help_text='0-100, calculated after user saves')
    
    class Meta:
        indexes = [
            models.Index(fields=['receiver_name', 'context_hash']),
            models.Index(fields=['-last_used']),
            models.Index(fields=['ai_provider', '-created_at']),
        ]
        ordering = ['-last_used']
        verbose_name = 'AI Prediction Cache'
        verbose_name_plural = 'AI Prediction Cache'
    
    def __str__(self):
        return f"{self.receiver_name} → {self.predicted_category.name} (used {self.times_used}x)"
    
    @property
    def cache_age_days(self):
        """How old is this cache entry"""
        return (timezone.now() - self.created_at).days
    
    @property
    def money_saved(self):
        """How much money saved by caching"""
        return float(self.api_cost) * self.times_used
    
    def mark_as_used(self):
        """Increment usage counter"""
        self.times_used += 1
        self.last_used = timezone.now()
        self.save(update_fields=['times_used', 'last_used'])


