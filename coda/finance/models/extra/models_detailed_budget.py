"""
Detailed Budget Models

Additional models for detailed budget item breakdown and user estimates
"""

from django.db import models
from django.contrib.auth import get_user_model
from .models import BudgetCategory, BudgetSubCategory, BudgetEstimateProjection

User = get_user_model()


class BudgetItemDetail(models.Model):
    """
    Detailed breakdown of budget categories into specific items
    """
    category = models.ForeignKey(
        BudgetCategory,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='item_details'
    )
    subcategory = models.ForeignKey(
        BudgetSubCategory,
        on_delete=models.CASCADE,
        related_name='item_details',
        null=True,
        blank=True
    )
    item_name = models.CharField(
        max_length=200,
        help_text="Specific item name (e.g., 'Office Rent', 'Software Licenses')"
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed description of the item"
    )
    unit_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Cost per unit"
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1,
        help_text="Quantity needed"
    )
    frequency = models.CharField(
        max_length=50,
        choices=[
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
            ('annually', 'Annually'),
            ('one_time', 'One Time'),
        ],
        default='monthly',
        help_text="How often this item is needed"
    )
    is_recurring = models.BooleanField(
        default=True,
        help_text="Whether this is a recurring expense"
    )
    is_essential = models.BooleanField(
        default=True,
        help_text="Whether this is an essential expense"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_budget_items'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Budget Item Detail"
        verbose_name_plural = "Budget Item Details"
        ordering = ['category', 'item_name']
    
    def __str__(self):
        return f"{self.category.name} - {self.item_name}"
    
    @property
    def total_cost(self):
        """Calculate total cost for this item"""
        return self.unit_cost * self.quantity
    
    @property
    def monthly_cost(self):
        """Calculate monthly cost based on frequency"""
        if self.frequency == 'monthly':
            return self.total_cost
        elif self.frequency == 'quarterly':
            return self.total_cost / 3
        elif self.frequency == 'annually':
            return self.total_cost / 12
        else:  # one_time
            return self.total_cost / 12  # Spread over a year


class BudgetEstimateItem(models.Model):
    """
    User's specific estimates for budget items
    """
    projection = models.ForeignKey(
        BudgetEstimateProjection,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='estimate_items'
    )
    item_detail = models.ForeignKey(
        BudgetItemDetail,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='estimates'
    )
    estimated_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="User's estimated quantity"
    )
    estimated_unit_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="User's estimated unit cost"
    )
    notes = models.TextField(
        blank=True,
        help_text="User's notes about this estimate"
    )
    is_approved = models.BooleanField(
        default=False,
        help_text="Whether this item is approved"
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_budget_items'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Budget Estimate Item"
        verbose_name_plural = "Budget Estimate Items"
        unique_together = ['projection', 'item_detail']
    
    def __str__(self):
        return f"{self.projection.id} - {self.item_detail.item_name}"
    
    @property
    def estimated_total(self):
        """Calculate estimated total for this item"""
        return self.estimated_quantity * self.estimated_unit_cost
    
    @property
    def variance_from_default(self):
        """Calculate variance from default cost"""
        default_total = self.item_detail.total_cost
        return self.estimated_total - default_total
    
    @property
    def variance_percentage(self):
        """Calculate variance percentage"""
        default_total = self.item_detail.total_cost
        if default_total > 0:
            return (self.variance_from_default / default_total) * 100
        return 0

