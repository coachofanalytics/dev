# FOOD MODEL INTERACTION ANALYSIS & PROPOSALS
## Comprehensive Review of Food System Architecture

**Date:** October 18, 2025  
**Focus:** Model Interactions, Signal Handling, and Automated Tracking  
**Current Issue:** Food edits don't automatically save to FoodHistory

---

## 📊 CURRENT STATE ANALYSIS

### Existing Models

#### 1. **Food Model** (Master Data)
```python
class Food(models.Model):
    """Food item tracking - MASTER LIST"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)  # Current price
    currency = models.CharField(max_length=3, default='KES')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=True)
```

**Purpose:** Catalog of available food items (like a product catalog)  
**Type:** Master data - relatively static  
**Problem:** ❌ No automatic history tracking when price changes

#### 2. **FoodHistory Model** (Transaction Data)
```python
class FoodHistory(models.Model):
    """Food purchase history - TRANSACTIONS"""
    food = models.ForeignKey(Food, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at purchase time
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    purchase_date = models.DateTimeField(default=timezone.now)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
```

**Purpose:** Record of actual food purchases  
**Type:** Transactional data - grows over time  
**Problem:** ❌ Only created manually, not automatically from Food changes

---

## 🔍 IDENTIFIED ISSUES

### Issue 1: No Automatic History Tracking ❌
**Current Behavior:**
- User updates Food.unit_price from 100 to 120
- **Nothing happens** - change is lost to history
- No audit trail of price changes
- Cannot analyze price trends over time

**Expected Behavior:**
- Price changes should be tracked automatically
- Historical data should be preserved
- Audit trail for compliance

### Issue 2: Confusion Between Master Data and Transactions ❌
**Problem:**
- `Food` model mixes catalog info (name, description) with transactional data (unit_price)
- `FoodHistory` is for purchases, not price changes
- No clear separation of concerns

### Issue 3: No Signal-Based Automation ❌
**Current State:**
- Transaction → Budget sync exists (via signals.py)
- **Food → FoodHistory sync missing**
- Inconsistent automation across models

### Issue 4: Missing Inventory Tracking ❌
**Problem:**
- No current stock quantity tracking
- No consumption logging
- No reorder alerts
- Addressed in Food Automation Roadmap, but needs integration here

---

## 💡 PROPOSED SOLUTION ARCHITECTURE

### Option A: Enhanced Signal-Based History Tracking (QUICK WIN)

#### **Concept:**
Automatically create FoodHistory records when Food is created/purchased, but track price changes separately.

#### **New Model: FoodPriceHistory**
```python
class FoodPriceHistory(models.Model):
    """Track price changes for audit and trend analysis"""
    food = models.ForeignKey(Food, on_delete=models.CASCADE, related_name='price_history')
    old_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    new_price = models.DecimalField(max_digits=10, decimal_places=2)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    change_date = models.DateTimeField(auto_now_add=True)
    change_reason = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        ordering = ['-change_date']
        verbose_name = "Food Price History"
        verbose_name_plural = "Food Price Histories"
    
    def __str__(self):
        return f"{self.food.name}: {self.old_price} → {self.new_price} ({self.change_date})"
```

#### **Enhanced Signal Handler**
```python
# Add to coda/finance/signals.py

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from finance.models import Food, FoodPriceHistory

@receiver(pre_save, sender=Food)
def track_food_price_change(sender, instance, **kwargs):
    """
    Track price changes before saving Food model
    Pre-save signal captures the old value before it's overwritten
    """
    if instance.pk:  # Only for updates, not creates
        try:
            old_instance = Food.objects.get(pk=instance.pk)
            
            # Check if price changed
            if old_instance.unit_price != instance.unit_price:
                # Store the old price for post_save signal
                instance._old_price = old_instance.unit_price
                instance._price_changed = True
            else:
                instance._price_changed = False
        except Food.DoesNotExist:
            instance._price_changed = False


@receiver(post_save, sender=Food)
def log_food_price_change(sender, instance, created, **kwargs):
    """
    Log price changes after Food is saved
    Post-save signal ensures the change was successful
    """
    if not created and getattr(instance, '_price_changed', False):
        # Get the user who made the change from thread-local storage
        from threading import local
        _thread_locals = local()
        user = getattr(_thread_locals, 'user', None)
        
        FoodPriceHistory.objects.create(
            food=instance,
            old_price=getattr(instance, '_old_price', None),
            new_price=instance.unit_price,
            changed_by=user,
            change_reason=f"Price updated via {'admin' if user and user.is_staff else 'system'}"
        )
        
        print(f"✅ Price change logged: {instance.name} - "
              f"{instance._old_price} → {instance.unit_price}")
```

#### **Middleware for User Tracking**
```python
# Create: coda/Middleware/track_user_middleware.py

from threading import local

_thread_locals = local()

def get_current_user():
    return getattr(_thread_locals, 'user', None)

class TrackUserMiddleware:
    """
    Middleware to track current user for signal handlers
    Makes request.user available in signals
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.user = getattr(request, 'user', None)
        response = self.get_response(request)
        return response
```

---

### Option B: Comprehensive Food Management System (RECOMMENDED)

#### **Concept:**
Redesign the food system to clearly separate:
1. **Master Data** (Food catalog)
2. **Pricing History** (Price changes over time)
3. **Inventory Data** (Current stock levels)
4. **Purchase Transactions** (Actual purchases)
5. **Consumption Logs** (Daily usage)

#### **Enhanced Model Structure**

##### **1. Food Model (Master Data - Catalog)**
```python
class Food(models.Model):
    """
    Master catalog of food items
    Contains only static/semi-static reference data
    """
    # Identification
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(
        max_length=50,
        choices=[
            ('grains', 'Grains & Cereals'),
            ('vegetables', 'Vegetables'),
            ('meat', 'Meat & Poultry'),
            ('dairy', 'Dairy Products'),
            ('beverages', 'Beverages'),
            ('condiments', 'Condiments & Spices'),
            ('other', 'Other'),
        ],
        default='other'
    )
    
    # Current Reference Info
    current_supplier = models.ForeignKey(
        Supplier, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='current_foods'
    )
    current_unit_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Latest known price (reference only, see PriceHistory for actual)"
    )
    currency = models.CharField(max_length=3, default='KES')
    unit_of_measurement = models.CharField(
        max_length=20,
        choices=[
            ('kg', 'Kilograms'),
            ('liters', 'Liters'),
            ('units', 'Units/Pieces'),
            ('bags', 'Bags/Sacks'),
            ('crates', 'Crates'),
        ],
        default='kg'
    )
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='created_foods'
    )
    
    class Meta:
        ordering = ['name']
        verbose_name = "Food Item"
        verbose_name_plural = "Food Items"
    
    @property
    def current_stock(self):
        """Get total current stock across all locations"""
        return self.inventory_records.filter(
            status__in=['in_stock', 'low_stock']
        ).aggregate(Sum('quantity'))['quantity__sum'] or 0
    
    @property
    def average_price_last_30_days(self):
        """Calculate average price from recent purchases"""
        from datetime import timedelta
        cutoff = timezone.now() - timedelta(days=30)
        avg = self.purchase_transactions.filter(
            purchase_date__gte=cutoff
        ).aggregate(Avg('unit_price'))['unit_price__avg']
        return avg or self.current_unit_price
    
    def __str__(self):
        return f"{self.name} ({self.category})"
```

##### **2. FoodPriceHistory (Price Tracking)**
```python
class FoodPriceHistory(models.Model):
    """
    Track all price changes for audit and trend analysis
    Automatically populated via signals
    """
    food = models.ForeignKey(
        Food, 
        on_delete=models.CASCADE, 
        related_name='price_history'
    )
    old_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    new_price = models.DecimalField(max_digits=10, decimal_places=2)
    supplier = models.ForeignKey(
        Supplier, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    changed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True
    )
    change_date = models.DateTimeField(auto_now_add=True)
    change_reason = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        help_text="Why did the price change? (e.g., market fluctuation, supplier change)"
    )
    change_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Percentage change (positive = increase, negative = decrease)"
    )
    
    class Meta:
        ordering = ['-change_date']
        verbose_name = "Food Price History"
        verbose_name_plural = "Food Price Histories"
        indexes = [
            models.Index(fields=['food', '-change_date']),
        ]
    
    def save(self, *args, **kwargs):
        # Auto-calculate percentage change
        if self.old_price and self.new_price:
            self.change_percentage = (
                (self.new_price - self.old_price) / self.old_price * 100
            )
        super().save(*args, **kwargs)
    
    def __str__(self):
        direction = "↑" if self.new_price > (self.old_price or 0) else "↓"
        return f"{self.food.name}: {direction} {self.old_price} → {self.new_price}"
```

##### **3. FoodInventory (Stock Tracking) - From Roadmap**
```python
class FoodInventory(models.Model):
    """
    Current inventory levels per location
    Links to FoodConsumptionLog for daily usage tracking
    """
    food_item = models.ForeignKey(
        Food, 
        on_delete=models.CASCADE, 
        related_name='inventory_records'
    )
    location = models.ForeignKey(
        'accounts.Department',  # Office location
        on_delete=models.CASCADE,
        related_name='food_inventory'
    )
    
    # Current Stock
    quantity = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Current quantity available"
    )
    
    # Reorder Thresholds
    reorder_level = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Trigger reorder when below this level"
    )
    reorder_quantity = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
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
    
    # Timestamps
    last_restocked_date = models.DateTimeField(null=True, blank=True)
    last_restocked_quantity = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    last_updated_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='food_inventory_updates'
    )
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Food Inventory"
        verbose_name_plural = "Food Inventories"
        unique_together = ['food_item', 'location']
        ordering = ['-updated_at']
    
    def days_until_stockout(self):
        """Calculate estimated days until stockout"""
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
```

##### **4. FoodPurchaseTransaction (Actual Purchases)**
```python
class FoodPurchaseTransaction(models.Model):
    """
    Record of actual food purchases (replaces FoodHistory)
    Links to Transaction model for budget integration
    """
    food_item = models.ForeignKey(
        Food, 
        on_delete=models.CASCADE,
        related_name='purchase_transactions'
    )
    inventory = models.ForeignKey(
        FoodInventory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchases',
        help_text="Which inventory this purchase restocks"
    )
    
    # Purchase Details
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Price paid per unit for this purchase"
    )
    total_amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        editable=False
    )
    currency = models.CharField(max_length=3, default='KES')
    
    # Supplier & Payment
    supplier = models.ForeignKey(
        Supplier, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    purchase_date = models.DateTimeField(default=timezone.now)
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
    receipt_number = models.CharField(max_length=100, blank=True, null=True)
    
    # Integration
    transaction = models.OneToOneField(
        'Transaction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='food_purchase',
        help_text="Linked financial transaction for budget sync"
    )
    
    # Audit
    purchased_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='food_purchases'
    )
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-purchase_date']
        verbose_name = "Food Purchase Transaction"
        verbose_name_plural = "Food Purchase Transactions"
        indexes = [
            models.Index(fields=['food_item', '-purchase_date']),
            models.Index(fields=['-purchase_date']),
        ]
    
    def save(self, *args, **kwargs):
        # Auto-calculate total
        self.total_amount = self.quantity * self.unit_price
        
        # Auto-update Food.current_unit_price if this is the latest purchase
        latest_purchase = FoodPurchaseTransaction.objects.filter(
            food_item=self.food_item
        ).order_by('-purchase_date').first()
        
        if not latest_purchase or self.purchase_date >= latest_purchase.purchase_date:
            self.food_item.current_unit_price = self.unit_price
            self.food_item.save(update_fields=['current_unit_price'])
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.food_item.name} - {self.quantity} units @ {self.unit_price} ({self.purchase_date})"
```

##### **5. FoodConsumptionLog (Daily Usage)**
```python
class FoodConsumptionLog(models.Model):
    """
    Track daily food consumption for inventory and analytics
    Enables consumption pattern analysis
    """
    inventory = models.ForeignKey(
        FoodInventory, 
        on_delete=models.CASCADE,
        related_name='consumption_logs'
    )
    
    # Consumption Details
    quantity_consumed = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Amount consumed"
    )
    consumption_date = models.DateField(default=timezone.now)
    consumption_type = models.CharField(
        max_length=20,
        choices=[
            ('normal', 'Normal Usage'),
            ('event', 'Special Event'),
            ('waste', 'Waste/Spoilage'),
            ('donation', 'Donation'),
        ],
        default='normal'
    )
    
    # Context
    recorded_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='food_consumption_records'
    )
    notes = models.TextField(blank=True, null=True)
    
    # Automation
    is_automatic = models.BooleanField(
        default=False,
        help_text="Was this logged automatically?"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Food Consumption Log"
        verbose_name_plural = "Food Consumption Logs"
        ordering = ['-consumption_date']
        unique_together = ['inventory', 'consumption_date']  # One log per day per inventory
    
    def save(self, *args, **kwargs):
        # Auto-update inventory quantity
        self.inventory.quantity -= self.quantity_consumed
        self.inventory.update_status()
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.inventory.food_item.name}: {self.quantity_consumed} on {self.consumption_date}"
```

---

## 🔄 COMPREHENSIVE SIGNAL ARCHITECTURE

### Signal Workflow Diagram
```
Food.save() 
    ↓
    ├─[pre_save]→ Capture old price
    ↓
    ├─[post_save]→ Create FoodPriceHistory (if price changed)
    ↓
    └─[post_save]→ Update FoodInventory.food_item reference

FoodPurchaseTransaction.save()
    ↓
    ├─[post_save]→ Create Transaction (for budget sync)
    │               ↓
    │               └─[post_save]→ Create Budget (existing signal)
    ↓
    ├─[post_save]→ Update FoodInventory quantity (+)
    ↓
    └─[post_save]→ Update Food.current_unit_price (if latest)

FoodConsumptionLog.save()
    ↓
    ├─[post_save]→ Update FoodInventory quantity (-)
    ↓
    ├─[post_save]→ Update daily_consumption_rate
    ↓
    └─[post_save]→ Check reorder_level → Create FoodRestockRequest

FoodRestockRequest.approved
    ↓
    └─[post_save]→ Create BudgetRequest (for approval workflow)
```

### Complete Signal Implementation

```python
# Enhanced coda/finance/signals.py

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.db import transaction as db_transaction
from finance.models import (
    Food, FoodPriceHistory, FoodInventory, 
    FoodPurchaseTransaction, FoodConsumptionLog,
    Transaction, Budget
)
import logging

logger = logging.getLogger(__name__)


# ==================== FOOD PRICE TRACKING ====================

@receiver(pre_save, sender=Food)
def capture_old_food_price(sender, instance, **kwargs):
    """Capture old price before saving (pre-save)"""
    if instance.pk:  # Only for updates
        try:
            old_instance = Food.objects.get(pk=instance.pk)
            instance._old_price = old_instance.current_unit_price
            instance._price_changed = (old_instance.current_unit_price != instance.current_unit_price)
        except Food.DoesNotExist:
            instance._price_changed = False
    else:
        instance._price_changed = False


@receiver(post_save, sender=Food)
def log_food_price_change(sender, instance, created, **kwargs):
    """Create price history record when price changes (post-save)"""
    if not created and getattr(instance, '_price_changed', False):
        try:
            from threading import local
            _thread_locals = local()
            user = getattr(_thread_locals, 'user', None)
            
            FoodPriceHistory.objects.create(
                food=instance,
                old_price=getattr(instance, '_old_price', None),
                new_price=instance.current_unit_price,
                supplier=instance.current_supplier,
                changed_by=user,
                change_reason="Price updated"
            )
            
            logger.info(f"✅ Price change logged: {instance.name} - "
                       f"{instance._old_price} → {instance.current_unit_price}")
        except Exception as e:
            logger.error(f"❌ Error logging price change for {instance.name}: {e}")


# ==================== PURCHASE → TRANSACTION → BUDGET ====================

@receiver(post_save, sender=FoodPurchaseTransaction)
def sync_food_purchase_to_transaction(sender, instance, created, **kwargs):
    """
    Create Transaction record when food is purchased
    Transaction signal will automatically create Budget entry
    """
    if created and not instance.transaction:
        try:
            with db_transaction.atomic():
                # Get or create Food & Accommodation category
                from finance.models import BudgetCategory, BudgetSubCategory
                category, _ = BudgetCategory.objects.get_or_create(
                    name='Food & Accommodation'
                )
                subcategory, _ = BudgetSubCategory.objects.get_or_create(
                    name='Food Supplies',
                    category=category
                )
                
                # Create Transaction
                txn = Transaction.objects.create(
                    category=category,
                    subcategory=subcategory,
                    type='Food_Accomodation',
                    receiver=instance.supplier.name if instance.supplier else 'Unknown Supplier',
                    description=f"Food Purchase: {instance.food_item.name} ({instance.quantity} units)",
                    amount=instance.unit_price,
                    qty=instance.quantity,
                    currency=instance.currency,
                    payment_method=instance.payment_method,
                    department=instance.inventory.location if instance.inventory else None,
                    sender=instance.purchased_by,
                    transaction_date=instance.purchase_date,
                    receipt_link=instance.receipt_number,
                )
                
                # Link transaction to purchase
                instance.transaction = txn
                instance.save(update_fields=['transaction'])
                
                logger.info(f"✅ Transaction created for food purchase: {instance.food_item.name}")
                
                # Note: Budget entry created automatically by existing Transaction signal
                
        except Exception as e:
            logger.error(f"❌ Error creating transaction for food purchase {instance.id}: {e}")


@receiver(post_save, sender=FoodPurchaseTransaction)
def update_inventory_on_purchase(sender, instance, created, **kwargs):
    """Update inventory quantity when food is purchased"""
    if created and instance.inventory:
        try:
            inventory = instance.inventory
            inventory.quantity += instance.quantity
            inventory.last_restocked_date = instance.purchase_date
            inventory.last_restocked_quantity = instance.quantity
            inventory.last_updated_by = instance.purchased_by
            inventory.update_status()
            
            logger.info(f"✅ Inventory updated: {instance.food_item.name} + {instance.quantity}")
            
        except Exception as e:
            logger.error(f"❌ Error updating inventory for purchase {instance.id}: {e}")


# ==================== CONSUMPTION → INVENTORY ====================

@receiver(post_save, sender=FoodConsumptionLog)
def update_inventory_on_consumption(sender, instance, created, **kwargs):
    """Update inventory quantity and consumption rate when food is consumed"""
    if created:
        try:
            inventory = instance.inventory
            
            # Update quantity (already done in FoodConsumptionLog.save(), but double-check)
            # inventory.quantity is already reduced in model save()
            
            # Recalculate daily consumption rate
            from datetime import timedelta
            from django.db.models import Avg
            
            cutoff_date = timezone.now().date() - timedelta(days=30)
            avg_consumption = FoodConsumptionLog.objects.filter(
                inventory=inventory,
                consumption_date__gte=cutoff_date,
                consumption_type='normal'  # Exclude waste, events
            ).aggregate(Avg('quantity_consumed'))['quantity_consumed__avg']
            
            if avg_consumption:
                inventory.daily_consumption_rate = avg_consumption
                inventory.save(update_fields=['daily_consumption_rate'])
            
            logger.info(f"✅ Consumption logged: {inventory.food_item.name} - {instance.quantity_consumed}")
            
            # Check if reorder needed
            check_reorder_trigger(inventory)
            
        except Exception as e:
            logger.error(f"❌ Error processing consumption log {instance.id}: {e}")


def check_reorder_trigger(inventory):
    """Check if inventory needs restocking and create request"""
    if inventory.quantity <= inventory.reorder_level:
        # Check if reorder already pending
        from finance.models import FoodRestockRequest
        
        existing_request = FoodRestockRequest.objects.filter(
            inventory=inventory,
            status__in=['pending', 'approved', 'ordered']
        ).exists()
        
        if not existing_request:
            # Create restock request
            estimated_cost = inventory.reorder_quantity * inventory.food_item.current_unit_price
            
            FoodRestockRequest.objects.create(
                inventory=inventory,
                requested_quantity=inventory.reorder_quantity,
                estimated_cost=estimated_cost,
                requested_by=inventory.last_updated_by,
                status='pending'
            )
            
            logger.warning(f"🔔 Restock request created: {inventory.food_item.name} at {inventory.location.name}")


# ==================== RESTOCK → BUDGET REQUEST ====================

@receiver(post_save, sender='finance.FoodRestockRequest')
def create_budget_request_for_restock(sender, instance, created, **kwargs):
    """Create BudgetRequest when food restock is requested"""
    if created and not instance.budget_request:
        try:
            from finance.models import BudgetRequest, BudgetCategory
            
            category, _ = BudgetCategory.objects.get_or_create(
                name='Food & Accommodation'
            )
            
            budget_request = BudgetRequest.objects.create(
                title=f"Food Restock: {instance.inventory.food_item.name}",
                description=f"Automatic restock request\n"
                           f"Item: {instance.inventory.food_item.name}\n"
                           f"Location: {instance.inventory.location.name}\n"
                           f"Current Stock: {instance.inventory.quantity}\n"
                           f"Requested: {instance.requested_quantity}\n"
                           f"Estimated Cost: {instance.estimated_cost}",
                department=instance.inventory.location,
                budget_category=category,
                requested_amount=instance.estimated_cost,
                priority='medium',
                created_by=instance.requested_by,
                last_modified_by=instance.requested_by,
            )
            
            instance.budget_request = budget_request
            instance.save(update_fields=['budget_request'])
            
            logger.info(f"✅ Budget request created for restock: {instance.inventory.food_item.name}")
            
        except Exception as e:
            logger.error(f"❌ Error creating budget request for restock {instance.id}: {e}")
```

---

## 📋 IMPLEMENTATION CHECKLIST

### Phase 1: Data Model Updates (Week 1)
- [ ] Create `FoodPriceHistory` model
- [ ] Rename `FoodHistory` to `FoodPurchaseTransaction` (or create new)
- [ ] Create `FoodInventory` model
- [ ] Create `FoodConsumptionLog` model
- [ ] Create `FoodRestockRequest` model
- [ ] Generate and run migrations

### Phase 2: Signal Implementation (Week 1-2)
- [ ] Implement `TrackUserMiddleware` for user tracking in signals
- [ ] Add signals to `coda/finance/signals.py`:
  - [ ] Food price change tracking
  - [ ] Purchase → Transaction → Budget sync
  - [ ] Consumption → Inventory update
  - [ ] Restock → Budget request
- [ ] Test signal chains thoroughly

### Phase 3: Service Layer (Week 2)
- [ ] Create `FoodBudgetIntegrationService`
- [ ] Create `FoodConsumptionService`
- [ ] Add business logic methods
- [ ] Add validation and error handling

### Phase 4: Views & Forms (Week 2-3)
- [ ] Update `FoodCreateView` to initialize inventory
- [ ] Update `FoodUpdateView` to handle price changes
- [ ] Create `FoodPurchaseCreateView`
- [ ] Create `FoodConsumptionLogView`
- [ ] Add AJAX endpoints for quick logging

### Phase 5: Admin Interface (Week 3)
- [ ] Register all new models in admin
- [ ] Add inline views for related models
- [ ] Create custom admin actions
- [ ] Add filters and search fields

### Phase 6: Testing & Validation (Week 3-4)
- [ ] Unit tests for all models
- [ ] Integration tests for signal chains
- [ ] Test Transaction → Budget sync
- [ ] Test consumption tracking
- [ ] Test reorder automation

### Phase 7: Documentation & Training (Week 4)
- [ ] Update API documentation
- [ ] Create user guides
- [ ] Train staff on new workflows
- [ ] Create video tutorials

### Phase 8: Deployment (Week 5)
- [ ] Deploy to UAT
- [ ] Pilot testing (1-2 locations)
- [ ] Gather feedback
- [ ] Deploy to production

---

## 🎯 BENEFITS OF PROPOSED ARCHITECTURE

### 1. **Complete Automation** ✅
- **Zero manual budget entries** - Signals handle everything
- **Automatic price history** - Every change tracked
- **Auto-reorder triggers** - Never run out unexpectedly
- **Real-time inventory** - Always accurate

### 2. **Clear Separation of Concerns** ✅
- **Food** = Master catalog (what items exist)
- **FoodPriceHistory** = Price changes over time
- **FoodInventory** = Current stock per location
- **FoodPurchaseTransaction** = Actual purchases
- **FoodConsumptionLog** = Daily usage

### 3. **Audit Trail & Compliance** ✅
- Every price change logged with user & timestamp
- Every purchase linked to Transaction & Budget
- Every consumption tracked
- Complete history for audits

### 4. **Budget Integration** ✅
- Food purchases → Transaction → Budget (automatic)
- Restock requests → BudgetRequest (automatic)
- Approval workflows integrated
- Real-time budget impact

### 5. **Analytics & Insights** ✅
- Price trend analysis
- Consumption pattern tracking
- Predictive ordering
- Cost optimization

---

## 🔄 COMPARISON: CURRENT vs. PROPOSED

| Feature | Current State | Proposed State |
|---------|--------------|----------------|
| **Price Change Tracking** | ❌ Lost forever | ✅ Full history with audit trail |
| **Purchase Recording** | 🔶 Manual FoodHistory | ✅ Automatic FoodPurchaseTransaction |
| **Budget Integration** | ❌ Manual entry needed | ✅ Automatic via signals |
| **Inventory Tracking** | ❌ No tracking | ✅ Real-time per location |
| **Consumption Logging** | ❌ Not tracked | ✅ Daily logs with analytics |
| **Reorder Automation** | ❌ Manual process | ✅ Automatic triggers |
| **Approval Workflows** | ❌ None | ✅ Threshold-based automation |
| **Transaction Sync** | ❌ Disconnected | ✅ Full integration |
| **Audit Trail** | ❌ Incomplete | ✅ Complete history |
| **Predictive Analytics** | ❌ Not possible | ✅ Days-until-stockout |

---

## 💡 ALTERNATIVE OPTIONS

### Option C: Minimal Changes (Quick Fix)
If full redesign is too much work right now:

1. **Add simple price tracking signal:**
```python
@receiver(post_save, sender=Food)
def log_price_to_history(sender, instance, created, **kwargs):
    """Quick fix: Log every Food save as FoodHistory"""
    if not created:  # Only on updates
        FoodHistory.objects.create(
            food=instance,
            quantity=1,  # Placeholder
            unit_price=instance.unit_price,
            total_amount=instance.unit_price,
            supplier=instance.supplier,
            notes="Price update via system"
        )
```

**Pros:** Quick, minimal code changes  
**Cons:** Misuses FoodHistory model, no proper audit trail, no inventory tracking

### Option D: Hybrid Approach
Keep current models but add signals:

1. Keep `Food` and `FoodHistory` as-is
2. Add `FoodPriceHistory` for price tracking only
3. Add signals for automatic logging
4. Defer inventory tracking to Phase 2

**Pros:** Incremental approach, less disruptive  
**Cons:** Technical debt accumulates, harder to refactor later

---

## 🎯 RECOMMENDATION

**I recommend Option B: Comprehensive Food Management System**

### Why?
1. **You're already planning food automation** (from roadmap)
2. **Technical debt is expensive** - fix architecture now
3. **CODA values automation** - do it right from the start
4. **5-week timeline is achievable** - structured phasing
5. **Long-term ROI is massive** - 20+ hours/month saved

### Quick Wins to Start
1. **Week 1:** Add `FoodPriceHistory` model + signals (2 days)
2. **Week 1:** Test price tracking works (1 day)
3. **Week 2:** Add `FoodPurchaseTransaction` + Transaction sync (3 days)
4. **Week 2:** Test budget integration (1 day)
5. **Week 3:** Add inventory models (from roadmap)
6. **Weeks 4-5:** Full automation rollout

---

## 📞 NEXT STEPS

### Immediate Actions
1. **Review this proposal** with stakeholders
2. **Decide on approach:**
   - Option A: Signal-based history (2 weeks)
   - Option B: Comprehensive system (5 weeks) ⭐ RECOMMENDED
   - Option C: Quick fix (1 week)
   - Option D: Hybrid (3 weeks)
3. **Approve timeline and resources**
4. **Begin Phase 1 development**

### Questions for Decision
1. **Timeline:** 5 weeks acceptable for Option B?
2. **Resources:** Developer availability?
3. **Pilot:** Which location to test first?
4. **Priority:** Implement immediately or after other work?

---

## 📚 RELATED DOCUMENTS

- **FOOD_AUTOMATION_ROADMAP.md** - Original 5-week implementation plan
- **FOOD_SYSTEM_ANALYSIS.md** - Current state analysis
- **Transaction Signal (signals.py)** - Existing Transaction → Budget automation

---

**Author:** AI Development Assistant  
**Date:** October 18, 2025  
**Status:** Proposal - Awaiting Stakeholder Review  
**Recommendation:** Option B - Comprehensive System ⭐

**CODA Mission:** Automation + Integration = Efficiency 🚀

---

*End of Analysis & Proposals*

