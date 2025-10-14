"""
Vendor and Receiver Management Models
Created: October 2025
Purpose: Standardize receiver names and enable intelligent categorization

Based on learnings from transaction data analysis:
- Same person entered multiple ways (typos, caps)
- Need vendor lookup for consistency
- Enable category auto-suggestion
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class Vendor(models.Model):
    """
    Master list of vendors/receivers with standardized names
    
    Purpose:
    - Standardize receiver names across transactions
    - Provide default category suggestions
    - Track vendor transaction history
    - Enable auto-complete functionality
    """
    
    VENDOR_TYPE_CHOICES = [
        ('employee', 'Employee'),
        ('supplier', 'Supplier/Vendor'),
        ('utility', 'Utility Company'),
        ('service_provider', 'Service Provider'),
        ('government', 'Government Agency'),
        ('contractor', 'Contractor'),
        ('other', 'Other'),
    ]
    
    # Primary Information
    name = models.CharField(
        max_length=200,
        unique=True,
        help_text="Standardized vendor/receiver name"
    )
    
    vendor_type = models.CharField(
        max_length=30,
        choices=VENDOR_TYPE_CHOICES,
        help_text="Type of vendor"
    )
    
    # Default Categorization
    default_category = models.ForeignKey(
        'BudgetCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='default_vendors',
        help_text="Suggested category for transactions with this vendor"
    )
    
    # Contact Information
    phone = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    
    # Statistics (auto-calculated)
    total_transactions = models.IntegerField(
        default=0,
        help_text="Total number of transactions with this vendor"
    )
    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Total amount transacted with this vendor"
    )
    average_transaction = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Average transaction amount"
    )
    
    # Metadata
    is_active = models.BooleanField(
        default=True,
        help_text="Is this vendor still active?"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes about this vendor"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = _("Vendor")
        verbose_name_plural = _("Vendors")
    
    def __str__(self):
        return self.name
    
    def update_statistics(self):
        """Update transaction statistics for this vendor"""
        from django.db.models import Count, Sum, Avg
        
        # Get all transactions (including aliases)
        all_receiver_names = [self.name] + list(
            self.aliases.values_list('alias', flat=True)
        )
        
        from finance.models import Transaction
        transactions = Transaction.objects.filter(
            receiver__in=all_receiver_names
        )
        
        stats = transactions.aggregate(
            count=Count('id'),
            total=Sum('amount'),
            avg=Avg('amount')
        )
        
        self.total_transactions = stats['count'] or 0
        self.total_amount = stats['total'] or 0
        self.average_transaction = stats['avg'] or 0
        self.save()


class VendorAlias(models.Model):
    """
    Alternative spellings/names for vendors
    
    Purpose:
    - Map typos to correct vendor (geogre ndalo → George Ndalo)
    - Handle case variations (IDAH WAIRIMU → Idah Wairimu)
    - Link old names to new standardized names
    
    Example:
    Vendor: "George Ndalo"
    Aliases: "geogre ndalo", "GEORGE NDALO", "george"
    """
    
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.CASCADE,
        related_name='aliases',
        help_text="The standardized vendor this alias refers to"
    )
    
    alias = models.CharField(
        max_length=200,
        unique=True,
        help_text="Alternative spelling/name"
    )
    
    confidence = models.CharField(
        max_length=20,
        choices=[
            ('exact', 'Exact Match'),
            ('high', 'High Confidence'),
            ('medium', 'Medium Confidence'),
            ('low', 'Low Confidence - Review'),
        ],
        default='high',
        help_text="Confidence level for this alias match"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _("Vendor Alias")
        verbose_name_plural = _("Vendor Aliases")
        ordering = ['vendor', 'alias']
    
    def __str__(self):
        return f"{self.alias} → {self.vendor.name}"


class VendorCategory(models.Model):
    """
    Track which categories a vendor typically uses
    
    Purpose:
    - Some vendors may have multiple categories
    - Track frequency to improve suggestions
    - Show user "You usually categorize X as Y"
    """
    
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.CASCADE,
        related_name='category_patterns'
    )
    
    category = models.ForeignKey(
        'BudgetCategory',
        on_delete=models.CASCADE
    )
    
    transaction_count = models.IntegerField(
        default=0,
        help_text="Number of transactions in this category"
    )
    
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Percentage of vendor's transactions in this category"
    )
    
    class Meta:
        unique_together = ('vendor', 'category')
        ordering = ['-transaction_count']
        verbose_name = _("Vendor Category Pattern")
        verbose_name_plural = _("Vendor Category Patterns")
    
    def __str__(self):
        return f"{self.vendor.name} → {self.category.name} ({self.percentage}%)"


