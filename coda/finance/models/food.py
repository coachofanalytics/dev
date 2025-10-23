# -*- coding: utf-8 -*-
"""
Finance Food Management Models

Enhanced food management system with automatic tracking, inventory management,
and budget integration.

Implements comprehensive signal-based automation for:
- Price change tracking
- Purchase recording
- Inventory management
- Consumption logging
- Automatic budget sync
"""

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.db.models import Sum, Avg
from decimal import Decimal
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

# Get the User model
User = get_user_model()


# =============================================================================
# FOOD MASTER DATA
# =============================================================================

class Food(models.Model):
    """
    Master catalog of food items
    Contains only static/semi-static reference data
    
    Changes to this model:
    - Added category field
    - Renamed unit_price to current_unit_price
    - Added unit_of_measurement
    - Added created_by tracking
    - current_unit_price is updated automatically from latest purchase
    """
    # Identification
    name = models.CharField(
        max_length=200,
        help_text="Name of the food item"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Detailed description of the item"
    )
    category = models.CharField(
        max_length=50,
        choices=[
            ('grains', 'Grains & Cereals'),
            ('vegetables', 'Vegetables'),
            ('fruits', 'Fruits'),
            ('meat', 'Meat & Poultry'),
            ('dairy', 'Dairy Products'),
            ('beverages', 'Beverages'),
            ('condiments', 'Condiments & Spices'),
            ('snacks', 'Snacks'),
            ('other', 'Other'),
        ],
        default='other',
        help_text="Food category for organization"
    )
    
    # Current Reference Info (auto-updated from latest purchase)
    current_supplier = models.ForeignKey(
        'Supplier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='current_foods',
        help_text="Latest supplier (reference only)"
    )
    current_unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Latest known price (auto-updated from purchases)"
    )
    currency = models.CharField(
        max_length=3,
        default='KES',
        help_text="Currency for pricing"
    )
    unit_of_measurement = models.CharField(
        max_length=20,
        choices=[
            ('kg', 'Kilograms'),
            ('liters', 'Liters'),
            ('units', 'Units/Pieces'),
            ('bags', 'Bags/Sacks'),
            ('crates', 'Crates'),
            ('packets', 'Packets'),
        ],
        default='kg',
        help_text="Unit of measurement for this item"
    )
    
    # Legacy field for backward compatibility
    @property
    def unit_price(self):
        """Backward compatibility property"""
        return self.current_unit_price
    
    @property
    def supplier(self):
        """Backward compatibility property"""
        return self.current_supplier
    
    # Metadata
    is_active = models.BooleanField(
        default=True,
        help_text="Is this item currently available?"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_foods',
        help_text="User who created this food item"
    )
    
    class Meta:
        ordering = ['name']
        verbose_name = _("Food Item")
        verbose_name_plural = _("Food Items")
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['category']),
            models.Index(fields=['is_active']),
        ]
    
    @property
    def current_stock(self):
        """Get total current stock across all locations"""
        from django.db.models import Sum
        total = self.inventory_records.filter(
            status__in=['in_stock', 'low_stock']
        ).aggregate(Sum('quantity'))['quantity__sum']
        return total or 0
    
    @property
    def total_amount(self):
        """For backward compatibility with existing templates"""
        return self.current_unit_price or 0
    
    @property
    def average_price_last_30_days(self):
        """Calculate average price from recent purchases"""
        cutoff = timezone.now() - timedelta(days=30)
        purchases = self.purchase_transactions.filter(
            purchase_date__gte=cutoff
        )
        if purchases.exists():
            avg = purchases.aggregate(Avg('unit_price'))['unit_price__avg']
            return avg
        return self.current_unit_price
    
    def __str__(self):
        return f"{self.name} ({self.category})"


# =============================================================================
# PRICE TRACKING
# =============================================================================

class FoodPriceHistory(models.Model):
    """
    Track all price changes for audit and trend analysis
    Automatically populated via signals when Food.current_unit_price changes
    """
    food = models.ForeignKey(
        Food,
        on_delete=models.CASCADE,
        related_name='price_history',
        help_text="Food item whose price changed"
    )
    old_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Previous price"
    )
    new_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="New price"
    )
    supplier = models.ForeignKey(
        'Supplier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Supplier at time of price change"
    )
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='food_price_changes',
        help_text="User who made the change"
    )
    change_date = models.DateTimeField(
        auto_now_add=True,
        help_text="When the price changed"
    )
    change_reason = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Reason for price change"
    )
    change_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        editable=False,
        help_text="Percentage change (auto-calculated)"
    )
    
    class Meta:
        ordering = ['-change_date']
        verbose_name = _("Food Price History")
        verbose_name_plural = _("Food Price Histories")
        indexes = [
            models.Index(fields=['food', '-change_date']),
            models.Index(fields=['-change_date']),
        ]
    
    def save(self, *args, **kwargs):
        """Auto-calculate percentage change"""
        if self.old_price and self.new_price and self.old_price > 0:
            self.change_percentage = (
                (self.new_price - self.old_price) / self.old_price * 100
            )
        super().save(*args, **kwargs)
    
    def __str__(self):
        if self.old_price and self.new_price:
            direction = "↑" if self.new_price > self.old_price else "↓"
            return f"{self.food.name}: {direction} {self.old_price} → {self.new_price}"
        return f"{self.food.name}: Set to {self.new_price}"


# =============================================================================
# INVENTORY MANAGEMENT
# =============================================================================

class FoodInventory(models.Model):
    """
    Current inventory levels per location
    Tracks stock quantities and consumption patterns
    """
    food_item = models.ForeignKey(
        Food,
        on_delete=models.CASCADE,
        related_name='inventory_records',
        help_text="Food item being tracked"
    )
    location = models.ForeignKey(
        'accounts.Department',
        on_delete=models.CASCADE,
        related_name='food_inventory',
        help_text="Office location/department"
    )
    
    # Current Stock
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Current quantity available"
    )
    
    # Reorder Thresholds
    reorder_level = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=10,
        help_text="Trigger reorder when below this level"
    )
    reorder_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=50,
        help_text="Amount to order when restocking"
    )
    
    # Analytics
    daily_consumption_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Average daily consumption (auto-calculated)"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('in_stock', 'In Stock'),
            ('low_stock', 'Low Stock'),
            ('out_of_stock', 'Out of Stock'),
            ('reorder_pending', 'Reorder Pending'),
        ],
        default='in_stock'
    )
    
    # Audit Fields
    last_restocked_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time inventory was restocked"
    )
    last_restocked_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Quantity added in last restock"
    )
    last_updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='food_inventory_updates',
        help_text="User who last updated this inventory"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Food Inventory")
        verbose_name_plural = _("Food Inventories")
        unique_together = ['food_item', 'location']
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['food_item', 'location']),
            models.Index(fields=['status']),
        ]
    
    def days_until_stockout(self):
        """Calculate estimated days until stockout based on consumption rate"""
        if self.daily_consumption_rate and self.daily_consumption_rate > 0:
            return float(self.quantity) / float(self.daily_consumption_rate)
        return None
    
    def update_status(self):
        """Auto-update status based on current quantity"""
        if self.quantity <= 0:
            self.status = 'out_of_stock'
        elif self.quantity <= self.reorder_level:
            self.status = 'low_stock'
        else:
            self.status = 'in_stock'
        self.save(update_fields=['status'])
    
    def __str__(self):
        return f"{self.food_item.name} @ {self.location.name}: {self.quantity}{self.food_item.unit_of_measurement}"


# =============================================================================
# PURCHASE TRANSACTIONS
# =============================================================================

class FoodPurchaseTransaction(models.Model):
    """
    Record of actual food purchases
    Automatically creates Transaction records for budget integration
    Replaces the old FoodHistory model with clearer purpose
    """
    food_item = models.ForeignKey(
        Food,
        on_delete=models.CASCADE,
        related_name='purchase_transactions',
        help_text="Food item purchased"
    )
    inventory = models.ForeignKey(
        FoodInventory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchases',
        help_text="Which inventory this purchase restocks (optional)"
    )
    
    # Purchase Details
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Quantity purchased"
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Price paid per unit for this purchase"
    )
    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        editable=False,
        help_text="Total amount (auto-calculated)"
    )
    currency = models.CharField(
        max_length=3,
        default='KES'
    )
    
    # Supplier & Payment
    supplier = models.ForeignKey(
        'Supplier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='food_purchases',
        help_text="Supplier for this purchase"
    )
    purchase_date = models.DateTimeField(
        default=timezone.now,
        help_text="Date of purchase"
    )
    payment_method = models.CharField(
        max_length=25,
        choices=[
            ('Cash', 'Cash'),
            ('Mpesa', 'M-Pesa'),
            ('Bank Transfer', 'Bank Transfer'),
            ('Check', 'Check'),
            ('Credit', 'Credit/Account'),
        ],
        default='Mpesa'
    )
    receipt_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Receipt or invoice number"
    )
    
    # Integration with Finance System
    transaction = models.OneToOneField(
        'Transaction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='food_purchase',
        help_text="Linked financial transaction (auto-created)"
    )
    
    # Audit
    purchased_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='food_purchases',
        help_text="User who made the purchase"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes about this purchase"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-purchase_date']
        verbose_name = _("Food Purchase Transaction")
        verbose_name_plural = _("Food Purchase Transactions")
        indexes = [
            models.Index(fields=['food_item', '-purchase_date']),
            models.Index(fields=['-purchase_date']),
            models.Index(fields=['supplier']),
        ]
    
    def save(self, *args, **kwargs):
        """Auto-calculate total amount"""
        self.total_amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.food_item.name} - {self.quantity} @ {self.unit_price} ({self.purchase_date.date()})"


# =============================================================================
# CONSUMPTION TRACKING
# =============================================================================

class FoodConsumptionLog(models.Model):
    """
    Track daily food consumption for inventory and analytics
    Enables consumption pattern analysis and predictive ordering
    """
    inventory = models.ForeignKey(
        FoodInventory,
        on_delete=models.CASCADE,
        related_name='consumption_logs',
        help_text="Inventory being consumed from"
    )
    
    # Consumption Details
    quantity_consumed = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Amount consumed"
    )
    consumption_date = models.DateField(
        default=timezone.now,
        help_text="Date of consumption"
    )
    consumption_type = models.CharField(
        max_length=20,
        choices=[
            ('normal', 'Normal Usage'),
            ('event', 'Special Event'),
            ('waste', 'Waste/Spoilage'),
            ('donation', 'Donation'),
        ],
        default='normal',
        help_text="Type of consumption"
    )
    
    # Context
    recorded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='food_consumption_records',
        help_text="User who logged this consumption"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes"
    )
    
    # Automation
    is_automatic = models.BooleanField(
        default=False,
        help_text="Was this logged automatically?"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _("Food Consumption Log")
        verbose_name_plural = _("Food Consumption Logs")
        ordering = ['-consumption_date', '-created_at']
        indexes = [
            models.Index(fields=['inventory', '-consumption_date']),
            models.Index(fields=['-consumption_date']),
        ]
    
    def __str__(self):
        return f"{self.inventory.food_item.name}: {self.quantity_consumed} on {self.consumption_date}"


# =============================================================================
# RESTOCK REQUESTS
# =============================================================================

class FoodRestockRequest(models.Model):
    """
    Automated restock requests linked to budget approval system
    Created automatically when inventory falls below reorder level
    """
    inventory = models.ForeignKey(
        FoodInventory,
        on_delete=models.CASCADE,
        related_name='restock_requests',
        help_text="Inventory that needs restocking"
    )
    
    # Request Details
    requested_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Quantity to order"
    )
    estimated_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Estimated total cost"
    )
    
    # Link to Budget System
    budget_request = models.OneToOneField(
        'BudgetRequest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='food_restock',
        help_text="Linked budget request (auto-created)"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending Approval'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('ordered', 'Ordered'),
            ('received', 'Received'),
            ('cancelled', 'Cancelled'),
        ],
        default='pending'
    )
    
    # Approval
    requested_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='food_restock_requests',
        help_text="User who requested restock (or system)"
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_food_restocks',
        help_text="User who approved the request"
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the request was approved"
    )
    rejection_reason = models.TextField(
        blank=True,
        null=True,
        help_text="Reason for rejection (if applicable)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Food Restock Request")
        verbose_name_plural = _("Food Restock Requests")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['inventory', 'status']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Restock: {self.inventory.food_item.name} @ {self.inventory.location.name} ({self.status})"


# =============================================================================
# BACKWARD COMPATIBILITY
# =============================================================================

# Keep FoodHistory as alias for backward compatibility
# This allows existing code to continue working while we transition
FoodHistory = FoodPurchaseTransaction

