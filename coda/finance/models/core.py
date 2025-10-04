# -*- coding: utf-8 -*-
"""
Core finance models - the fundamental models used across the finance application.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

# Get the User model
User = get_user_model()

# Import models from other apps
try:
    from main.models import Company, Department
except ImportError:
    Company = Department = None


class BudgetCategory(models.Model):
    """Budget categories for organizing expenses and income."""
    
    name = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        default='Operations',
        help_text="Name of the budget category"
    )
    description = models.TextField(
        max_length=1000,
        null=True,
        blank=True,
        help_text="Description of what this category covers"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Budget Category")
        verbose_name_plural = _("Budget Categories")
        ordering = ['name']
    
    def __str__(self):
        return self.name or "Unnamed Category"


class BudgetSubCategory(models.Model):
    """Subcategories within budget categories for more granular organization."""
    
    category = models.ForeignKey(
        BudgetCategory,
        on_delete=models.CASCADE,
        related_name='subcategories',
        help_text="Parent budget category"
    )
    name = models.CharField(
        max_length=100,
        help_text="Name of the subcategory"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of what this subcategory covers"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Budget Subcategory")
        verbose_name_plural = _("Budget Subcategories")
        ordering = ['category__name', 'name']
        unique_together = ['category', 'name']
    
    def __str__(self):
        return "{} -> {}".format(self.category.name, self.name)


class BudgetItemLibrary(models.Model):
    """
    Master library of budget items for all categories.
    Provides standardized items for consistent data entry.
    """
    
    category = models.ForeignKey(
        BudgetCategory, 
        on_delete=models.CASCADE, 
        related_name='items',
        help_text="Budget category this item belongs to"
    )
    subcategory = models.ForeignKey(
        BudgetSubCategory, 
        on_delete=models.CASCADE, 
        related_name='items',
        help_text="Budget subcategory this item belongs to"
    )
    item_name = models.CharField(
        max_length=200,
        help_text="Name of the budget item (e.g., 'Safaricom internet subscription')"
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed description of the item"
    )
    typical_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Typical/average amount based on historical data"
    )
    unit_type = models.CharField(
        max_length=50,
        blank=True,
        default='each',
        help_text="Unit of measurement (each, month, year, etc.)"
    )
    usage_count = models.IntegerField(
        default=0,
        help_text="Number of times this item has been used (for sorting)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this item is active and available for selection"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Budget Item")
        verbose_name_plural = _("Budget Item Library")
        ordering = ['-usage_count', 'item_name']
        unique_together = ['category', 'subcategory', 'item_name']
    
    def __str__(self):
        return "{} -> {} -> {}".format(self.category.name, self.subcategory.name, self.item_name)
    
    def increment_usage(self):
        """Increment usage count when item is selected."""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])
    
    def update_typical_amount(self, new_amount):
        """Update typical amount based on new transaction."""
        if self.typical_amount and self.usage_count > 0:
            total = (self.typical_amount * self.usage_count) + new_amount
            self.typical_amount = total / (self.usage_count + 1)
        else:
            self.typical_amount = new_amount
        self.save(update_fields=['typical_amount'])


class Transaction(models.Model):
    """Core transaction model for all financial transactions."""
    
    # Transaction categories
    CAT_CHOICES = [
        ('Income', 'Income'),
        ('Expense', 'Expense'),
        ('Transfer', 'Transfer'),
        ('Investment', 'Investment'),
    ]
    
    # Transaction types
    TYPE_CHOICES = [
        ('Cash', 'Cash'),
        ('Bank Transfer', 'Bank Transfer'),
        ('Mobile Money', 'Mobile Money'),
        ('Credit Card', 'Credit Card'),
        ('Check', 'Check'),
        ('Other', 'Other'),
    ]
    
    # Transaction status
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
        ('Cancelled', 'Cancelled'),
    ]
    
    # Basic transaction fields
    company = models.ForeignKey(
        'main.Company',
        on_delete=models.CASCADE,
        related_name='transactions',
        help_text="Company this transaction belongs to"
    )
    category = models.CharField(
        max_length=20,
        choices=CAT_CHOICES,
        help_text="Transaction category"
    )
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        help_text="Transaction type"
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Transaction amount"
    )
    currency = models.CharField(
        max_length=3,
        default='USD',
        help_text="Transaction currency"
    )
    
    # Budget categorization
    budget_category = models.ForeignKey(
        BudgetCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        help_text="Budget category for this transaction"
    )
    budget_subcategory = models.ForeignKey(
        BudgetSubCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        help_text="Budget subcategory for this transaction"
    )
    
    # Transaction details
    description = models.TextField(
        help_text="Transaction description"
    )
    receiver = models.CharField(
        max_length=200,
        help_text="Receiver/payee name"
    )
    reference = models.CharField(
        max_length=100,
        blank=True,
        help_text="Transaction reference number"
    )
    
    # Status and dates
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Completed',
        help_text="Transaction status"
    )
    transaction_date = models.DateTimeField(
        default=timezone.now,
        help_text="Date and time of transaction"
    )
    
    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_transactions',
        help_text="User who created this transaction"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Additional fields
    receipt_link = models.URLField(
        blank=True,
        help_text="Link to receipt or supporting document"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes about the transaction"
    )
    
    class Meta:
        verbose_name = _("Transaction")
        verbose_name_plural = _("Transactions")
        ordering = ['-transaction_date', '-created_at']
        indexes = [
            models.Index(fields=['company', 'transaction_date']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['budget_category', 'budget_subcategory']),
        ]
    
    def __str__(self):
        return "{} - {} {} - {}".format(self.category, self.amount, self.currency, self.receiver)
    
    @property
    def is_income(self):
        """Check if transaction is income."""
        return self.category == 'Income'
    
    @property
    def is_expense(self):
        """Check if transaction is expense."""
        return self.category == 'Expense'
    
    def get_absolute_url(self):
        """Get URL for transaction detail view."""
        from django.urls import reverse
        return reverse('finance:transaction-detail', kwargs={'pk': self.pk})


class Budget(models.Model):
    """Budget model for planning and tracking financial allocations."""
    
    # Budget types
    BUDGET_TYPE_CHOICES = [
        ('Operating', 'Operating Budget'),
        ('Capital', 'Capital Budget'),
        ('Project', 'Project Budget'),
        ('Department', 'Department Budget'),
    ]
    
    # Budget status
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Submitted', 'Submitted'),
        ('Approved', 'Approved'),
        ('Active', 'Active'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]
    
    # Basic budget fields
    company = models.ForeignKey(
        'main.Company',
        on_delete=models.CASCADE,
        related_name='budgets',
        help_text="Company this budget belongs to"
    )
    department = models.ForeignKey(
        'accounts.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='budgets',
        help_text="Department this budget is for"
    )
    
    # Budget categorization
    category = models.ForeignKey(
        BudgetCategory,
        on_delete=models.CASCADE,
        related_name='budgets',
        help_text="Budget category"
    )
    subcategory = models.ForeignKey(
        BudgetSubCategory,
        on_delete=models.CASCADE,
        related_name='budgets',
        help_text="Budget subcategory"
    )
    
    # Budget details
    item_name = models.CharField(
        max_length=200,
        help_text="Name of the budget item"
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed description of the budget item"
    )
    
    # Financial amounts
    estimated_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Estimated budget amount"
    )
    actual_spent = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Actual amount spent"
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('1.00'),
        help_text="Quantity of items"
    )
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Price per unit"
    )
    cases = models.IntegerField(
        default=1,
        help_text="Number of cases (for bulk items)"
    )
    
    # Budget metadata
    budget_type = models.CharField(
        max_length=20,
        choices=BUDGET_TYPE_CHOICES,
        default='Operating',
        help_text="Type of budget"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Draft',
        help_text="Budget status"
    )
    
    # Dates
    start_date = models.DateField(
        help_text="Budget start date"
    )
    end_date = models.DateField(
        help_text="Budget end date"
    )
    
    # Approval workflow
    requires_approval = models.BooleanField(
        default=False,
        help_text="Whether this budget requires approval"
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_budgets',
        help_text="User who approved this budget"
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this budget was approved"
    )
    
    # Budget lead
    budget_lead = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='led_budgets',
        help_text="User responsible for this budget"
    )
    
    # Additional fields
    notes = models.TextField(
        blank=True,
        help_text="Additional notes about the budget"
    )
    receipt_link = models.URLField(
        blank=True,
        help_text="Link to supporting documents"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Budget")
        verbose_name_plural = _("Budgets")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['category', 'subcategory']),
            models.Index(fields=['start_date', 'end_date']),
        ]
    
    def __str__(self):
        return "{} - {} ({})".format(self.item_name, self.estimated_amount, self.status)
    
    @property
    def total_amount(self):
        """Calculate total budget amount."""
        return self.unit_price * self.quantity * self.cases
    
    @property
    def variance(self):
        """Calculate variance between estimated and actual."""
        return self.actual_spent - self.estimated_amount
    
    @property
    def variance_percentage(self):
        """Calculate variance percentage."""
        if self.estimated_amount == 0:
            return 0
        return (self.variance / self.estimated_amount) * 100
    
    @property
    def is_over_budget(self):
        """Check if budget is over the estimated amount."""
        return self.actual_spent > self.estimated_amount
    
    def get_absolute_url(self):
        """Get URL for budget detail view."""
        from django.urls import reverse
        return reverse('finance:budget-detail', kwargs={'pk': self.pk})


class BudgetEstimateProjection(models.Model):
    """Stored output of an estimation run for user review/approval."""
    
    company = models.ForeignKey(
        'main.Company',
        on_delete=models.CASCADE,
        related_name='budget_projections',
        help_text="Company this projection belongs to"
    )
    
    # Projection details
    projection_name = models.CharField(
        max_length=200,
        help_text="Name of this budget projection"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of the projection"
    )
    
    # Estimation parameters
    estimation_method = models.CharField(
        max_length=50,
        help_text="Method used for estimation"
    )
    estimation_source = models.CharField(
        max_length=100,
        help_text="Source of estimation data"
    )
    estimation_confidence = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Confidence level of estimation (0-100)"
    )
    
    # Projection results
    total_estimated_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Total estimated budget amount"
    )
    projection_data = models.JSONField(
        help_text="Detailed projection data"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('Draft', 'Draft'),
            ('Submitted', 'Submitted'),
            ('Approved', 'Approved'),
            ('Rejected', 'Rejected'),
        ],
        default='Draft',
        help_text="Projection status"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Budget Estimate Projection")
        verbose_name_plural = _("Budget Estimate Projections")
        ordering = ['-created_at']
    
    def __str__(self):
        return "{} - {}".format(self.projection_name, self.total_estimated_amount)


class Supplier(models.Model):
    """Supplier model for food and other items."""
    
    name = models.CharField(max_length=200, help_text="Supplier name")
    contact_person = models.CharField(max_length=200, blank=True, help_text="Contact person")
    email = models.EmailField(blank=True, help_text="Supplier email")
    phone = models.CharField(max_length=20, blank=True, help_text="Supplier phone")
    address = models.TextField(blank=True, help_text="Supplier address")
    active = models.BooleanField(default=True, help_text="Whether supplier is active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Supplier")
        verbose_name_plural = _("Suppliers")
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Food(models.Model):
    """Food items model."""
    
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.RESTRICT,
        help_text="Supplier for this food item"
    )
    office_location = models.CharField(
        max_length=255,
        default='makutano',
        help_text="Office location"
    )
    item = models.CharField(
        max_length=255,
        unique=True,
        help_text="Food item name"
    )
    unit_amt = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Unit amount"
    )
    slug = models.SlugField(
        blank=True,
        null=True,
        help_text="URL slug"
    )
    qty = models.PositiveIntegerField(help_text="Quantity")
    bal_qty = models.PositiveIntegerField(help_text="Balance quantity")
    description = models.TextField(help_text="Item description")
    created_at = models.DateTimeField(auto_now_add=True)
    featured = models.BooleanField(default=False, help_text="Whether item is featured")
    active = models.BooleanField(default=True, help_text="Whether item is active")
    
    class Meta:
        verbose_name = _("Food Item")
        verbose_name_plural = _("Food Items")
        ordering = ['item']
    
    def __str__(self):
        return self.item
    
    def get_absolute_url(self):
        """Get URL for food item detail view."""
        from django.urls import reverse
        return reverse('finance:food-detail', kwargs={'slug': self.slug})
    
    @property
    def budgeted_items(self):
        """Calculate budgeted quantity."""
        return self.qty - self.bal_qty
    
    @property
    def total_amount(self):
        """Calculate total amount."""
        return Decimal(self.qty) * self.unit_amt
    
    @property
    def additional_amount(self):
        """Calculate additional amount."""
        return Decimal(self.qty - self.bal_qty) * self.unit_amt


class FoodHistory(models.Model):
    """Food item history tracking."""
    
    item = models.ForeignKey(
        Food,
        on_delete=models.CASCADE,
        related_name='history',
        help_text="Food item"
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.RESTRICT,
        help_text="Supplier"
    )
    office_location = models.CharField(
        max_length=255,
        default='makutano',
        help_text="Office location"
    )
    unit_amt = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Unit amount"
    )
    qty = models.PositiveIntegerField(help_text="Quantity")
    bal_qty = models.PositiveIntegerField(help_text="Balance quantity")
    description = models.TextField(help_text="Description")
    created_at = models.DateTimeField(auto_now_add=True)
    featured = models.BooleanField(default=False, help_text="Whether item is featured")
    active = models.BooleanField(default=True, help_text="Whether item is active")
    
    class Meta:
        verbose_name = _("Food History")
        verbose_name_plural = _("Food History")
        ordering = ['-created_at']
    
    def __str__(self):
        return "{} - {}".format(self.item.item, self.created_at.strftime('%Y-%m-%d'))
