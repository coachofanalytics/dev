# Food Supply Management - Implementation

**Feature:** Food & Inventory Tracking  
**Status:** ⚠️ Partially Complete - Needs Phase 1-3  
**Last Updated:** October 22, 2025

---

## 📂 CODE LOCATIONS

### Models
**File:** `coda/finance/models/core.py`

**Existing:**
- `Food` (lines 648-669) - Basic food item tracking
- `Supplier` (lines 628-645) - Vendor information
- `FoodHistory` (lines 672-693) - Purchase history

**To Be Added:**
- `FoodInventory` - Daily stock tracking by location
- `FoodConsumption` - Consumption logs
- `FoodPurchaseRequest` - Purchase approval workflow

### Views
**File:** `coda/finance/views.py`

**Existing:**
- `FoodListView` (lines 4507-4542) - Current food list

**To Be Added:**
- `FoodInventoryListView` - Multi-location inventory view
- `FoodConsumptionCreateView` - Log consumption
- `FoodPurchaseRequestView` - Create purchase requests
- `FoodAnalyticsDashboardView` - Charts and trends

### URLs
**File:** `coda/finance/urls.py`

**Existing:**
- `path("food/", views.FoodListView, name="supplies")` (line 207)

**To Be Added:**
```python
path('food/inventory/', views.FoodInventoryListView, name='food_inventory'),
path('food/consumption/add/', views.FoodConsumptionCreateView, name='food_consumption_add'),
path('food/purchase/request/', views.FoodPurchaseRequestCreateView, name='food_purchase_request'),
path('food/analytics/', views.FoodAnalyticsDashboard, name='food_analytics'),
```

### Templates
**Existing:** `coda/finance/templates/finance/payments/food.html`

**To Be Created:**
- `food_inventory_list.html`
- `food_consumption_form.html`
- `food_purchase_request_form.html`
- `food_analytics_dashboard.html`

### Filters
**File:** `coda/main/filters.py`

**Existing:** `FoodFilter` (lines 82-93)

**Needs Fix:** Remove references to non-existent fields

---

## 🐛 KNOWN ISSUES

### Issue #1: Template/Model Mismatch
**Status:** ⚠️ Open  
**Severity:** High  
**Description:** Template `food.html` expects 11 fields, model only has 6

**Missing Fields:**
- `office_location` (uses 'location' in template)
- `qty` (quantity)
- `bal_qty` (balance quantity)
- `budgeted_items`
- `additional_amount`
- `created_at`, `updated_at`

**Fix:** Add fields to Food model or create FoodInventory model

### Issue #2: Incorrect total_amount
**Status:** ⚠️ Open  
**Severity:** Medium  
**Description:** `total_amount` property returns `unit_price` instead of `qty × unit_price`

**Current Code:**
```python
@property
def total_amount(self):
    return self.unit_price or 0
```

**Should Be:**
```python
@property
def total_amount(self):
    return (self.quantity or 0) * (self.unit_price or 0)
```

### Issue #3: Filter References Missing Fields
**Status:** ⚠️ Open  
**Severity:** Low  
**Description:** FoodFilter might reference fields that don't exist

**Fix:** Update filter to match actual Food model fields

---

## 📊 CHANGE HISTORY

| Date | Change | Files | Dev |
|------|--------|-------|-----|
| Oct 22, 2025 | Created 7-doc structure | All docs | AI |
| Oct 18, 2025 | Analysis & roadmap created | Analysis docs | AI |
| Earlier 2025 | Basic food tracking implemented | models, views, templates | CM |

---

## ✅ IMPLEMENTATION ROADMAP

### Phase 1: Foundation (Weeks 1-2) - NOT STARTED
- [ ] Add FoodInventory model
- [ ] Add FoodConsumption model
- [ ] Migrate existing Food data
- [ ] Update templates
- [ ] Fix total_amount calculation
- [ ] Add location tracking

### Phase 2: Integration (Weeks 3-5) - NOT STARTED
- [ ] Add FoodPurchaseRequest model
- [ ] Integrate with ApprovalPolicy
- [ ] Create budget integration service
- [ ] Add email notifications
- [ ] Build approval workflow views

### Phase 3: Analytics (Weeks 6-7) - NOT STARTED
- [ ] Create analytics dashboard
- [ ] Add consumption trend charts
- [ ] Build cost analysis reports
- [ ] Mobile-responsive design
- [ ] Performance optimization

---

## 🔧 TECHNICAL DETAILS

### Database Migrations
**Required:**
1. Add `FoodInventory` model
2. Add `FoodConsumption` model
3. Add `FoodPurchaseRequest` model
4. Migrate existing `Food` records to `FoodInventory`
5. Add indexes for performance

### Services Layer
**To Be Created:**
- `FoodInventoryService` - Inventory operations
- `FoodConsumptionService` - Consumption tracking
- `FoodBudgetIntegrationService` - Budget integration
- `FoodAlertService` - Notification management

### Cron Jobs
**To Be Added:**
```python
# Daily consumption rate calculation
0 23 * * * python manage.py calculate_food_consumption_rates

# Low stock alerts
0 8 * * * python manage.py send_food_alerts
```

---

## 🔐 SECURITY

### Permissions
- Office Managers: View/update own office inventory
- Procurement: Create/view all purchase requests
- Finance: Approve high-value purchases, view all data
- Admin: Full access

### Audit Logging
- Log all inventory adjustments
- Log all consumption entries
- Log all approval actions
- Track who/when/what changed

---

**See:** 05_TESTING.md for test scenarios


