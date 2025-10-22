# FOOD SUPPLY AUTOMATION & BUDGET INTEGRATION ROADMAP
## CODA Budget System Enhancement Strategy

**Date:** October 18, 2025  
**Focus:** Daily Inventory Tracking, Budget Integration & Approval Automation  
**Philosophy:** Automation + Integration = Efficiency

---

## EXECUTIVE SUMMARY

### Current State Analysis
The food supply system currently tracks:
- ✅ Food items (name, unit price, supplier, currency)
- ✅ Supplier information
- ✅ Basic filtering capabilities
- ❌ **MISSING:** Daily quantity tracking and consumption monitoring
- ❌ **MISSING:** Real-time budget integration
- ❌ **MISSING:** Automated approval workflows for food purchases

### Business Requirements (From User)

#### 1. **Daily Quantity Tracking** ⭐ HIGH PRIORITY
**Current Challenge:**
- Employees manually update quantities daily (e.g., Sugar: 5kg → 4.5kg → 4kg → 3kg)
- No automatic consumption tracking
- No alerts when stock is low

**Desired Outcome:**
- Automatic daily consumption tracking
- Real-time inventory updates
- Predictive restocking alerts

#### 2. **Budget System Integration** ⭐ HIGH PRIORITY
**Current Challenge:**
- Food purchases exist separately from budget system
- Manual synchronization required
- No automatic budget allocation for food expenses

**Desired Outcome:**
- Every food purchase automatically creates/updates budget entries
- Real-time budget impact visibility
- Category: "Food & Accommodation" auto-mapping

#### 3. **Automated Approval Workflows** ⭐ HIGH PRIORITY
**Current Challenge:**
- Manual approval processes
- No workflow automation
- Delays in procurement

**Desired Outcome:**
- Threshold-based auto-approval (e.g., <$50 = auto-approve)
- Multi-level approval for large purchases
- Email/SMS notifications
- Integration with existing ApprovalPolicy system

---

## TECHNICAL SOLUTION ARCHITECTURE

### Phase 1: Daily Inventory Tracking System (Weeks 1-2)

#### 1.1 Enhanced Food Model
```python
# Add to coda/finance/models/core.py

class FoodInventory(models.Model):
    """
    Daily inventory tracking for food items
    Replaces manual quantity updates with automated consumption tracking
    """
    
    # Relationships
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
    
    # Quantity Tracking
    quantity = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Current quantity available"
    )
    unit_of_measurement = models.CharField(
        max_length=20,
        choices=[
            ('kg', 'Kilograms'),
            ('liters', 'Liters'),
            ('units', 'Units'),
            ('bags', 'Bags/Sacks'),
            ('crates', 'Crates'),
        ],
        default='kg'
    )
    
    # Consumption Tracking
    daily_consumption_rate = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Average daily consumption (auto-calculated)"
    )
    
    # Restocking Thresholds
    reorder_level = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Minimum quantity before triggering reorder alert"
    )
    reorder_quantity = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Quantity to reorder when stock is low"
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
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Food Inventory"
        verbose_name_plural = "Food Inventories"
        unique_together = ['food_item', 'location']  # One inventory per item per location
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.food_item.name} - {self.location.name}: {self.quantity}{self.unit_of_measurement}"
    
    def update_status(self):
        """Auto-update status based on current quantity"""
        if self.quantity <= 0:
            self.status = 'out_of_stock'
        elif self.quantity <= self.reorder_level:
            self.status = 'low_stock'
        else:
            self.status = 'in_stock'
        self.save(update_fields=['status'])
    
    def days_until_stockout(self):
        """Calculate estimated days until stockout based on consumption rate"""
        if self.daily_consumption_rate and self.daily_consumption_rate > 0:
            return self.quantity / self.daily_consumption_rate
        return None


class FoodConsumptionLog(models.Model):
    """
    Track daily food consumption for automatic quantity updates
    Enables consumption pattern analysis and predictive ordering
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
    
    # Context
    recorded_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='food_consumption_records'
    )
    notes = models.TextField(blank=True, null=True)
    
    # Automatic vs Manual
    is_automatic = models.BooleanField(
        default=False,
        help_text="Was this logged automatically or manually?"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Food Consumption Log"
        verbose_name_plural = "Food Consumption Logs"
        ordering = ['-consumption_date']
    
    def __str__(self):
        return f"{self.inventory.food_item.name}: {self.quantity_consumed} on {self.consumption_date}"


class FoodRestockRequest(models.Model):
    """
    Automated restock requests linked to budget approval system
    """
    
    inventory = models.ForeignKey(
        FoodInventory, 
        on_delete=models.CASCADE,
        related_name='restock_requests'
    )
    
    # Request Details
    requested_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    estimated_cost = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        help_text="Estimated total cost based on unit price"
    )
    
    # Link to Budget System
    budget_request = models.OneToOneField(
        'BudgetRequest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='food_restock'
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
        ],
        default='pending'
    )
    
    # Approval
    requested_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='food_restock_requests'
    )
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_food_restocks'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Food Restock Request"
        verbose_name_plural = "Food Restock Requests"
        ordering = ['-created_at']
```

#### 1.2 Migration Command
```bash
# Create migration
python manage.py makemigrations finance --name add_food_inventory_tracking

# Apply migration
python manage.py migrate finance
```

---

### Phase 2: Budget Integration Service (Weeks 2-3)

#### 2.1 Food-Budget Integration Service
```python
# Create: coda/finance/services/food_budget_integration_service.py

"""
Food Budget Integration Service
Automatically syncs food purchases with budget system
"""

from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from finance.models import (
    Food, FoodInventory, FoodRestockRequest, 
    Budget, BudgetRequest, BudgetCategory, BudgetSubCategory,
    Transaction
)
from finance.services.automation_service import ApprovalEngineService
import logging

logger = logging.getLogger(__name__)


class FoodBudgetIntegrationService:
    """
    Handles automatic integration between food purchases and budget system
    """
    
    def __init__(self):
        self.approval_engine = ApprovalEngineService()
    
    @transaction.atomic
    def create_budget_entry_for_restock(self, restock_request):
        """
        Automatically create budget entry when food restock is requested
        
        Args:
            restock_request: FoodRestockRequest instance
            
        Returns:
            BudgetRequest instance
        """
        try:
            inventory = restock_request.inventory
            food_item = inventory.food_item
            
            # Get or create Food & Accommodation category
            category, _ = BudgetCategory.objects.get_or_create(
                name='Food & Accommodation',
                defaults={'description': 'Food, beverages, and accommodation expenses'}
            )
            
            # Get or create subcategory
            subcategory, _ = BudgetSubCategory.objects.get_or_create(
                name='Food Supplies',
                category=category,
                defaults={}
            )
            
            # Create budget request
            budget_request = BudgetRequest.objects.create(
                title=f"Restock: {food_item.name} - {inventory.location.name}",
                description=f"Automatic restock request for {food_item.name}\n"
                           f"Current Stock: {inventory.quantity}{inventory.unit_of_measurement}\n"
                           f"Requested Quantity: {restock_request.requested_quantity}{inventory.unit_of_measurement}\n"
                           f"Estimated Cost: {restock_request.estimated_cost} {food_item.currency}",
                
                department=inventory.location,
                budget_category=category,
                requested_amount=restock_request.estimated_cost,
                currency=food_item.currency,
                
                priority='medium',  # Can be calculated based on stock level
                urgency='normal',
                
                created_by=restock_request.requested_by,
                last_modified_by=restock_request.requested_by,
                
                # Link metadata
                notes=f"Auto-generated from Food Inventory System\nFood Item ID: {food_item.id}\nInventory ID: {inventory.id}",
            )
            
            # Link budget request to restock request
            restock_request.budget_request = budget_request
            restock_request.save()
            
            logger.info(f"✅ Created budget request {budget_request.id} for restock {restock_request.id}")
            
            # Automatically process approval if eligible
            self._process_auto_approval(budget_request, restock_request)
            
            return budget_request
            
        except Exception as e:
            logger.error(f"❌ Error creating budget entry for restock {restock_request.id}: {e}")
            raise
    
    def _process_auto_approval(self, budget_request, restock_request):
        """
        Check if request qualifies for auto-approval based on amount thresholds
        """
        # Get applicable approval policy
        policy = self.approval_engine.get_applicable_policy(
            amount=budget_request.requested_amount,
            department=budget_request.department,
            category=budget_request.budget_category
        )
        
        if policy and policy.auto_approve:
            # Auto-approve
            budget_request.status = 'approved'
            budget_request.approved_by = None  # System approval
            budget_request.approved_at = timezone.now()
            budget_request.save()
            
            restock_request.status = 'approved'
            restock_request.approved_by = None  # System approval
            restock_request.approved_at = timezone.now()
            restock_request.save()
            
            logger.info(f"✅ Auto-approved restock request {restock_request.id} (amount: {budget_request.requested_amount})")
            
            # Trigger notification
            self._send_approval_notification(budget_request, restock_request, auto_approved=True)
        else:
            # Requires manual approval
            logger.info(f"⏳ Restock request {restock_request.id} requires manual approval")
            self._send_approval_notification(budget_request, restock_request, auto_approved=False)
    
    def _send_approval_notification(self, budget_request, restock_request, auto_approved=False):
        """
        Send email/SMS notification about approval status
        """
        # TODO: Implement notification system
        # - Email to budget manager
        # - SMS alert for urgent items
        # - Dashboard notification
        pass
    
    @transaction.atomic
    def record_purchase_transaction(self, restock_request, actual_amount_paid, payment_method='Mpesa'):
        """
        Record actual purchase as Transaction when food is received
        Automatically syncs with budget system via existing signals
        """
        try:
            inventory = restock_request.inventory
            food_item = inventory.food_item
            
            # Create transaction record
            txn = Transaction.objects.create(
                # Category mapping
                category=restock_request.budget_request.budget_category,
                subcategory=BudgetSubCategory.objects.filter(
                    name='Food Supplies'
                ).first(),
                
                # Transaction details
                type='Food_Accomodation',
                receiver=food_item.supplier.name if food_item.supplier else 'Unknown Supplier',
                description=f"Purchase: {food_item.name} ({restock_request.requested_quantity}{inventory.unit_of_measurement})",
                
                # Financial details
                amount=actual_amount_paid,
                qty=restock_request.requested_quantity,
                currency=food_item.currency,
                
                # Payment
                payment_method=payment_method,
                
                # Links
                department=inventory.location,
                sender=restock_request.approved_by,
                
                # Timestamps
                transaction_date=timezone.now(),
            )
            
            # Update inventory
            inventory.quantity += restock_request.requested_quantity
            inventory.last_restocked_date = timezone.now()
            inventory.last_restocked_quantity = restock_request.requested_quantity
            inventory.update_status()
            
            # Update restock request status
            restock_request.status = 'received'
            restock_request.save()
            
            logger.info(f"✅ Recorded purchase transaction {txn.id} for restock {restock_request.id}")
            
            # Note: Transaction → Budget sync happens automatically via signals.py
            
            return txn
            
        except Exception as e:
            logger.error(f"❌ Error recording purchase transaction for restock {restock_request.id}: {e}")
            raise
    
    def calculate_consumption_rate(self, inventory, days=30):
        """
        Calculate average daily consumption rate based on historical logs
        """
        from datetime import timedelta
        from django.db.models import Avg, Sum
        
        cutoff_date = timezone.now().date() - timedelta(days=days)
        
        logs = inventory.consumption_logs.filter(
            consumption_date__gte=cutoff_date
        )
        
        if logs.exists():
            total_consumed = logs.aggregate(Sum('quantity_consumed'))['quantity_consumed__sum']
            days_with_data = logs.values('consumption_date').distinct().count()
            
            if days_with_data > 0:
                avg_daily = total_consumed / days_with_data
                
                # Update inventory
                inventory.daily_consumption_rate = avg_daily
                inventory.save(update_fields=['daily_consumption_rate'])
                
                return avg_daily
        
        return None
    
    def check_and_trigger_restock_alerts(self):
        """
        Background task: Check all inventories and trigger restock for low stock
        Run this daily via cron job or Celery
        """
        low_stock_inventories = FoodInventory.objects.filter(
            status__in=['low_stock', 'out_of_stock']
        ).exclude(
            # Don't create duplicate requests
            restock_requests__status__in=['pending', 'approved', 'ordered']
        )
        
        for inventory in low_stock_inventories:
            # Calculate estimated cost
            estimated_cost = inventory.reorder_quantity * inventory.food_item.unit_price
            
            # Create restock request
            restock_request = FoodRestockRequest.objects.create(
                inventory=inventory,
                requested_quantity=inventory.reorder_quantity,
                estimated_cost=estimated_cost,
                requested_by=User.objects.filter(is_staff=True).first(),  # System user
                status='pending'
            )
            
            # Create budget entry (triggers approval workflow)
            self.create_budget_entry_for_restock(restock_request)
            
            logger.info(f"🔔 Created restock alert for {inventory.food_item.name} at {inventory.location.name}")
```

---

### Phase 3: Automated Daily Consumption Tracking (Weeks 3-4)

#### 3.1 Daily Consumption Automation Options

**Option A: Smart POS Integration** (Recommended for Long-term)
- Integrate with Point of Sale (POS) system
- Automatically deduct quantities when meals are served
- Real-time inventory updates

**Option B: Employee Self-Service Portal** (Quick Win)
- Simple mobile-friendly form
- Employees log daily consumption at end of day
- Validates against yesterday's stock

**Option C: IoT Smart Scales** (Future Enhancement)
- Install smart scales in storage areas
- Automatic weight monitoring
- Real-time alerts

#### 3.2 Daily Update Service
```python
# Create: coda/finance/services/food_consumption_service.py

class FoodConsumptionService:
    """
    Handles daily food consumption tracking and inventory updates
    """
    
    @transaction.atomic
    def log_daily_consumption(self, inventory_id, quantity_consumed, user, notes=''):
        """
        Log daily consumption and update inventory
        """
        try:
            inventory = FoodInventory.objects.get(id=inventory_id)
            
            # Validate quantity
            if quantity_consumed > inventory.quantity:
                raise ValueError(f"Cannot consume {quantity_consumed} - only {inventory.quantity} available")
            
            # Create consumption log
            log = FoodConsumptionLog.objects.create(
                inventory=inventory,
                quantity_consumed=quantity_consumed,
                consumption_date=timezone.now().date(),
                recorded_by=user,
                notes=notes,
                is_automatic=False
            )
            
            # Update inventory
            inventory.quantity -= quantity_consumed
            inventory.last_updated_by = user
            inventory.update_status()
            
            # Recalculate consumption rate
            self._update_consumption_rate(inventory)
            
            # Check if restock needed
            if inventory.status in ['low_stock', 'out_of_stock']:
                self._trigger_restock_alert(inventory)
            
            logger.info(f"✅ Logged consumption: {quantity_consumed}{inventory.unit_of_measurement} of {inventory.food_item.name}")
            
            return log
            
        except Exception as e:
            logger.error(f"❌ Error logging consumption: {e}")
            raise
    
    def _update_consumption_rate(self, inventory):
        """Calculate and update average daily consumption rate"""
        integration_service = FoodBudgetIntegrationService()
        integration_service.calculate_consumption_rate(inventory, days=30)
    
    def _trigger_restock_alert(self, inventory):
        """Trigger restock workflow when stock is low"""
        integration_service = FoodBudgetIntegrationService()
        integration_service.check_and_trigger_restock_alerts()
```

---

### Phase 4: Enhanced UI & User Experience (Week 4)

#### 4.1 Enhanced Food Dashboard
```html
<!-- coda/finance/templates/finance/inventory/food_inventory_dashboard.html -->

{% extends "main/base_templates/new_base.html" %}
{% load static %}

{% block content %}
<div class="container-fluid">
    <h2>Food Inventory Dashboard</h2>
    
    <!-- Summary Cards -->
    <div class="row mb-4">
        <div class="col-md-3">
            <div class="card bg-success text-white">
                <div class="card-body">
                    <h5>In Stock</h5>
                    <h2>{{ in_stock_count }}</h2>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card bg-warning text-white">
                <div class="card-body">
                    <h5>Low Stock</h5>
                    <h2>{{ low_stock_count }}</h2>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card bg-danger text-white">
                <div class="card-body">
                    <h5>Out of Stock</h5>
                    <h2>{{ out_of_stock_count }}</h2>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card bg-info text-white">
                <div class="card-body">
                    <h5>Pending Restocks</h5>
                    <h2>{{ pending_restocks }}</h2>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Inventory Table with Real-time Status -->
    <div class="card">
        <div class="card-header">
            <h4>Current Inventory</h4>
        </div>
        <div class="card-body">
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>Item</th>
                        <th>Location</th>
                        <th>Current Stock</th>
                        <th>Daily Usage</th>
                        <th>Days Until Stockout</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for inventory in inventories %}
                    <tr class="{% if inventory.status == 'out_of_stock' %}table-danger{% elif inventory.status == 'low_stock' %}table-warning{% endif %}">
                        <td>{{ inventory.food_item.name }}</td>
                        <td>{{ inventory.location.name }}</td>
                        <td>
                            <strong>{{ inventory.quantity }}</strong> {{ inventory.unit_of_measurement }}
                            <br><small class="text-muted">Reorder at: {{ inventory.reorder_level }}</small>
                        </td>
                        <td>
                            {% if inventory.daily_consumption_rate %}
                                {{ inventory.daily_consumption_rate }} {{ inventory.unit_of_measurement }}/day
                            {% else %}
                                <span class="text-muted">Not tracked</span>
                            {% endif %}
                        </td>
                        <td>
                            {% with days=inventory.days_until_stockout %}
                                {% if days %}
                                    {% if days < 3 %}
                                        <span class="badge bg-danger">{{ days|floatformat:0 }} days</span>
                                    {% elif days < 7 %}
                                        <span class="badge bg-warning">{{ days|floatformat:0 }} days</span>
                                    {% else %}
                                        <span class="badge bg-success">{{ days|floatformat:0 }} days</span>
                                    {% endif %}
                                {% else %}
                                    -
                                {% endif %}
                            {% endwith %}
                        </td>
                        <td>
                            <span class="badge 
                                {% if inventory.status == 'in_stock' %}bg-success
                                {% elif inventory.status == 'low_stock' %}bg-warning
                                {% elif inventory.status == 'out_of_stock' %}bg-danger
                                {% else %}bg-info{% endif %}">
                                {{ inventory.get_status_display }}
                            </span>
                        </td>
                        <td>
                            <button class="btn btn-sm btn-primary" onclick="logConsumption({{ inventory.id }})">
                                Log Usage
                            </button>
                            {% if inventory.status in 'low_stock,out_of_stock' %}
                            <button class="btn btn-sm btn-warning" onclick="requestRestock({{ inventory.id }})">
                                Request Restock
                            </button>
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    
    <!-- Quick Log Consumption Modal -->
    <div class="modal fade" id="logConsumptionModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Log Daily Consumption</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <form id="consumptionForm">
                        {% csrf_token %}
                        <input type="hidden" id="inventory_id" name="inventory_id">
                        <div class="mb-3">
                            <label>Item: <strong id="item_name"></strong></label>
                        </div>
                        <div class="mb-3">
                            <label>Current Stock: <strong id="current_stock"></strong></label>
                        </div>
                        <div class="mb-3">
                            <label for="quantity_consumed" class="form-label">Quantity Used Today</label>
                            <input type="number" class="form-control" id="quantity_consumed" 
                                   name="quantity_consumed" step="0.01" required>
                        </div>
                        <div class="mb-3">
                            <label for="notes" class="form-label">Notes (Optional)</label>
                            <textarea class="form-control" id="notes" name="notes" rows="2"></textarea>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="button" class="btn btn-primary" onclick="submitConsumption()">Save</button>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
function logConsumption(inventoryId) {
    // Fetch inventory details and show modal
    fetch(`/finance/api/food-inventory/${inventoryId}/`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('inventory_id').value = inventoryId;
            document.getElementById('item_name').textContent = data.food_item.name;
            document.getElementById('current_stock').textContent = 
                `${data.quantity} ${data.unit_of_measurement}`;
            new bootstrap.Modal(document.getElementById('logConsumptionModal')).show();
        });
}

function submitConsumption() {
    const form = document.getElementById('consumptionForm');
    const formData = new FormData(form);
    
    fetch('/finance/api/food-consumption/log/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': formData.get('csrfmiddlewaretoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Consumption logged successfully!');
            location.reload();
        } else {
            alert('Error: ' + data.error);
        }
    });
}

function requestRestock(inventoryId) {
    if (confirm('Request restock for this item? This will create a budget request.')) {
        fetch(`/finance/api/food-inventory/${inventoryId}/request-restock/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Restock request created! Budget request ID: ' + data.budget_request_id);
                location.reload();
            }
        });
    }
}
</script>
{% endblock %}
```

---

## IMPLEMENTATION ROADMAP

### Week 1: Foundation
- [ ] Create database models (FoodInventory, FoodConsumptionLog, FoodRestockRequest)
- [ ] Run migrations
- [ ] Create admin interfaces for testing

### Week 2: Core Services
- [ ] Build FoodBudgetIntegrationService
- [ ] Build FoodConsumptionService
- [ ] Set up signal handlers for automatic budget sync
- [ ] Create API endpoints

### Week 3: Automation & Approval
- [ ] Configure ApprovalPolicy rules for food purchases
- [ ] Implement auto-approval logic (threshold-based)
- [ ] Build notification system (email/SMS)
- [ ] Create background task for restock alerts

### Week 4: UI & Testing
- [ ] Build enhanced food inventory dashboard
- [ ] Create mobile-friendly consumption logging form
- [ ] User acceptance testing
- [ ] Documentation and training

### Week 5: Deployment
- [ ] Deploy to UAT
- [ ] Staff training
- [ ] Monitor and fix issues
- [ ] Deploy to production

---

## APPROVAL AUTOMATION RULES

### Recommended Threshold Configuration

```python
# Auto-Approval Rules (to be configured in Admin)

# Rule 1: Small Purchases (Auto-Approve)
ApprovalPolicy.objects.create(
    name="Food - Small Purchase Auto-Approval",
    description="Automatically approve food purchases under $50",
    min_amount=0,
    max_amount=50,
    auto_approve=True,
    requires_otp=False,
    applicable_categories=[food_category],
)

# Rule 2: Medium Purchases (Manager Approval)
ApprovalPolicy.objects.create(
    name="Food - Manager Approval",
    description="Require manager approval for $50-$500",
    min_amount=50,
    max_amount=500,
    auto_approve=False,
    approval_chain=[
        {"role": "manager", "required": True}
    ],
    requires_otp=True,
)

# Rule 3: Large Purchases (Finance + Director Approval)
ApprovalPolicy.objects.create(
    name="Food - Large Purchase Multi-Approval",
    description="Require Finance Manager + Director approval for >$500",
    min_amount=500,
    max_amount=None,  # No upper limit
    auto_approve=False,
    approval_chain=[
        {"role": "finance_manager", "required": True},
        {"role": "director", "required": True}
    ],
    requires_otp=True,
)
```

---

## BUDGET CATEGORY MAPPING

### Automatic Category Assignment
```python
# Food items automatically map to:
Category: "Food & Accommodation"
Subcategory: "Food Supplies"
Type: "Food_Accomodation"  # Matches existing Transaction.CAT_CHOICES

# This ensures:
- ✅ All food purchases appear in food budget reports
- ✅ Budget vs. Actual comparisons are accurate
- ✅ Department-level food spending is tracked
- ✅ No manual categorization needed
```

---

## INTEGRATION TOUCHPOINTS

### Existing System Integration Points

1. **Transaction Model** (Already exists)
   - Food purchases create Transaction records
   - Signals automatically sync to Budget

2. **Budget Model** (Already exists)
   - Receives food purchase data
   - Tracks actual vs. budgeted food spending

3. **BudgetRequest Model** (Already exists)
   - Handles restock request approvals
   - Links to FoodRestockRequest

4. **ApprovalPolicy Model** (Already exists)
   - Controls food purchase approval workflows
   - Enables threshold-based auto-approval

5. **Notification System** (To be enhanced)
   - Email alerts for low stock
   - SMS for urgent restocks
   - Dashboard notifications

---

## BENEFITS SUMMARY

### For Employees
- ✅ Simple daily consumption logging (2-minute task)
- ✅ No manual calculations - system does math
- ✅ Mobile-friendly interface
- ✅ Instant visibility of stock levels

### For Managers
- ✅ Real-time inventory visibility
- ✅ Predictive alerts before stockouts
- ✅ Automatic budget impact analysis
- ✅ One-click approval for small purchases

### For Finance
- ✅ Automatic budget integration - zero manual work
- ✅ Accurate food spending tracking
- ✅ Budget vs. Actual always in sync
- ✅ Audit trail for all purchases

### For CODA
- ✅ **100% automation** - no manual budget entries
- ✅ **100% integration** - food → budget → approval → transaction
- ✅ Reduced food waste through better tracking
- ✅ Cost savings through predictive ordering
- ✅ Compliance-ready audit trails

---

## RECOMMENDED NEXT STEPS

### Immediate (This Week)
1. **Review and approve this roadmap**
2. **Set budget approval thresholds** (what amounts require approval?)
3. **Identify test users** for UAT phase
4. **Determine office locations** for inventory tracking

### Development Phase (Weeks 1-2)
1. Create database models
2. Build core services
3. Set up admin interfaces

### Testing Phase (Weeks 3-4)
1. Internal testing with 1-2 office locations
2. Gather employee feedback
3. Refine UI/UX

### Rollout Phase (Week 5)
1. Train staff on new system
2. Gradual rollout to all locations
3. Monitor and support

---

## QUESTIONS FOR STAKEHOLDERS

1. **Approval Thresholds:**
   - What amount should auto-approve? (Suggested: $50)
   - Who approves medium purchases ($50-$500)?
   - Who approves large purchases (>$500)?

2. **Office Locations:**
   - Which offices will track inventory separately?
   - Should each location have its own reorder levels?

3. **Consumption Logging:**
   - Who logs daily consumption? (kitchen staff, office admin?)
   - What time each day? (end of day, morning review?)
   - Mobile app needed or web form sufficient?

4. **Integration Timeline:**
   - Acceptable timeline for full rollout? (5 weeks recommended)
   - Pilot location for initial testing?
   - Training requirements for staff?

---

## SUCCESS METRICS

### Key Performance Indicators (KPIs)

1. **Automation Rate**
   - Target: 100% of food purchases auto-sync to budget
   - Measure: % of food transactions appearing in budget system

2. **Approval Speed**
   - Target: Small purchases (<$50) approved instantly
   - Measure: Average time from request to approval

3. **Stockout Prevention**
   - Target: Zero unexpected stockouts
   - Measure: # of emergency purchases vs. planned restocks

4. **Data Quality**
   - Target: Daily consumption logged 95% of days
   - Measure: % of days with consumption records

5. **Cost Savings**
   - Target: 10% reduction in food waste
   - Measure: Compare food spending before/after implementation

---

## TECHNICAL NOTES

### Database Considerations
- **New tables:** 3 (FoodInventory, FoodConsumptionLog, FoodRestockRequest)
- **Estimated storage:** ~1MB per year per location
- **Indexes needed:** food_item, location, consumption_date
- **Backup strategy:** Daily backups recommended

### Performance Considerations
- **API calls:** Minimal - only during logging
- **Background tasks:** 1 daily cron job for restock alerts
- **Caching:** Cache inventory counts for dashboard

### Security Considerations
- **Permissions:** Only authorized staff can log consumption
- **Audit trail:** All changes tracked with user + timestamp
- **Data validation:** Prevent negative inventory quantities

---

## CONCLUSION

This roadmap provides a comprehensive, phased approach to:

1. ✅ **Automatic daily inventory tracking** - replacing manual spreadsheets
2. ✅ **Seamless budget integration** - zero manual data entry
3. ✅ **Intelligent approval workflows** - threshold-based automation
4. ✅ **Predictive restocking** - never run out unexpectedly

**Timeline:** 5 weeks from approval to full production deployment

**Cost:** Development time only - no external services required

**ROI:** Estimated 20+ hours/month saved on manual tracking + budget entry

---

**Ready to proceed?** Let's discuss approval thresholds and pilot location selection.

**Questions?** Contact the development team for technical clarification.

**CODA Mission:** Automation + Integration = Efficiency 🚀

