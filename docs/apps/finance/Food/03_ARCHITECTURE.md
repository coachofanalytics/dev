# Food Supply Management - Architecture

**Feature:** Food & Inventory Tracking  
**Status:** 🚧 Design Complete, Implementation Pending  
**Last Updated:** October 22, 2025

---

## 🏗️ SYSTEM ARCHITECTURE

### Current Models (Existing)

**Food Model** (`finance/models/core.py`)
```python
class Food(models.Model):
    name = CharField(max_length=200)
    description = TextField(blank=True, null=True)
    unit_price = DecimalField(max_digits=10, decimal_places=2)
    currency = CharField(max_length=3, default='KES')
    supplier = ForeignKey(Supplier, on_delete=models.CASCADE)
    is_active = BooleanField(default=True)
```

**FoodHistory Model** (Existing)
```python
class FoodHistory(models.Model):
    food = ForeignKey(Food, on_delete=models.CASCADE)
    quantity = PositiveIntegerField()
    unit_price = DecimalField(max_digits=10, decimal_places=2)
    total_amount = DecimalField(max_digits=15, decimal_places=2)
    purchase_date = DateTimeField(default=timezone.now)
    supplier = ForeignKey(Supplier, on_delete=models.CASCADE)
    notes = TextField(blank=True, null=True)
```

---

## 📊 NEW MODELS (Phase 1-2)

### FoodInventory Model
```python
class FoodInventory(models.Model):
    """Daily inventory tracking by location"""
    food_item = ForeignKey(Food, on_delete=models.CASCADE, related_name='inventory_records')
    location = ForeignKey(Department, on_delete=models.CASCADE)
    
    quantity = DecimalField(max_digits=10, decimal_places=2)
    unit_of_measurement = CharField(max_length=20, choices=UOM_CHOICES)
    daily_consumption_rate = DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    reorder_level = DecimalField(max_digits=10, decimal_places=2)
    reorder_quantity = DecimalField(max_digits=10, decimal_places=2)
    
    last_restocked = DateTimeField(null=True, blank=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

### FoodConsumption Model
```python
class FoodConsumption(models.Model):
    """Track daily consumption logs"""
    inventory = ForeignKey(FoodInventory, on_delete=models.CASCADE)
    quantity_used = DecimalField(max_digits=10, decimal_places=2)
    consumption_date = DateField(default=date.today)
    recorded_by = ForeignKey(CustomerUser, on_delete=models.SET_NULL, null=True)
    notes = TextField(blank=True, null=True)
    created_at = DateTimeField(auto_now_add=True)
```

### FoodPurchaseRequest Model
```python
class FoodPurchaseRequest(models.Model):
    """Purchase requests with approval workflow"""
    food_item = ForeignKey(Food, on_delete=models.CASCADE)
    location = ForeignKey(Department, on_delete=models.CASCADE)
    quantity = DecimalField(max_digits=10, decimal_places=2)
    estimated_cost = DecimalField(max_digits=15, decimal_places=2)
    
    status = CharField(max_length=20, choices=STATUS_CHOICES)  # pending, approved, rejected
    requested_by = ForeignKey(CustomerUser, on_delete=models.CASCADE, related_name='food_requests')
    approved_by = ForeignKey(CustomerUser, on_delete=models.SET_NULL, null=True, related_name='approved_food_requests')
    
    request_date = DateTimeField(auto_now_add=True)
    approval_date = DateTimeField(null=True, blank=True)
    notes = TextField(blank=True, null=True)
```

---

## 🔄 DATA FLOW

### Flow 1: Inventory Update
```
1. Office Manager logs consumption
         ↓
2. FoodConsumption record created
         ↓
3. FoodInventory.quantity updated (decremented)
         ↓
4. Check if quantity < reorder_level
         ↓
5. If YES: Create FoodPurchaseRequest (auto or manual)
         ↓
6. Send alert notification
```

### Flow 2: Purchase Approval → Budget Entry
```
1. Purchase request submitted
         ↓
2. Auto-approval logic (if < $50)
   OR Route to approver
         ↓
3. On approval: Create Budget entry
   - Category: "Food & Accommodation"
   - Amount: Purchase cost
   - Status: "Approved"
         ↓
4. Create FoodHistory record
         ↓
5. Update FoodInventory (increment quantity)
         ↓
6. Update Budget variance
```

### Flow 3: Consumption Rate Calculation
```
1. Cron job runs daily (11:59 PM)
         ↓
2. For each FoodInventory:
   - Get last 30 days consumption
   - Calculate average: total_consumed / 30
   - Update daily_consumption_rate
         ↓
3. Calculate predicted stockout:
   - days_remaining = current_qty / daily_rate
   - stockout_date = today + days_remaining
         ↓
4. If stockout_date < 7 days: Send alert
```

---

## 🖥️ VIEWS & URLS

### Views (Planned)
- `FoodInventoryListView` - Current stock by location
- `FoodConsumptionCreateView` - Log daily consumption
- `FoodPurchaseRequestCreateView` - Create purchase request
- `FoodAnalyticsDashboard` - Consumption trends, spending
- `FoodAlertView` - Low stock alerts

### URLs (Planned)
```python
path('food/inventory/', FoodInventoryListView, name='food_inventory'),
path('food/consumption/add/', FoodConsumptionCreateView, name='food_consumption_add'),
path('food/purchase/request/', FoodPurchaseRequestCreateView, name='food_purchase_request'),
path('food/analytics/', FoodAnalyticsDashboard, name='food_analytics'),
path('food/alerts/', FoodAlertView, name='food_alerts'),
```

---

## 🎨 TEMPLATES (Planned)

- `food_inventory_list.html` - Stock levels by location
- `food_consumption_form.html` - Log consumption
- `food_purchase_request_form.html` - Request purchase
- `food_analytics_dashboard.html` - Charts & trends
- `food_alerts.html` - Low stock notifications

---

## ⚙️ SERVICES

### FoodInventoryService
```python
class FoodInventoryService:
    def update_consumption(inventory_id, quantity_used, user):
        """Update inventory and log consumption"""
        
    def check_reorder_needed(inventory_id):
        """Check if below reorder level"""
        
    def calculate_consumption_rate(inventory_id):
        """Calculate average daily consumption"""
        
    def predict_stockout_date(inventory_id):
        """Predict when stock will run out"""
```

### FoodBudgetIntegrationService
```python
class FoodBudgetIntegrationService:
    def create_budget_from_purchase(purchase_request):
        """Auto-create budget entry from approved purchase"""
        
    def update_budget_variance(budget_id):
        """Update variance after purchase"""
```

---

## 🔔 NOTIFICATION SYSTEM

### Alert Types:
1. **Low Stock Alert** - When quantity < reorder_level
2. **Stockout Prediction** - When stockout_date < 7 days
3. **Purchase Approved** - When request approved
4. **Purchase Rejected** - When request rejected
5. **Daily Summary** - End-of-day inventory status

### Channels:
- Email (primary)
- In-app notifications
- SMS (future - critical alerts only)

---

## 🔌 INTEGRATIONS

### Budget System
- Auto-create Budget entries
- Map to "Food & Accommodation" category
- Update variance real-time

### Approval System
- Use existing ApprovalPolicy model
- Threshold-based routing
- Multi-level approval support

### User/Department System
- Location-based inventory
- Role-based permissions
- Department cost allocation

---

**See:** 04_IMPLEMENTATION.md for code locations


