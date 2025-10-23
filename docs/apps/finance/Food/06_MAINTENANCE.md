# Food Supply Management - Maintenance

**Feature:** Food & Inventory Tracking  
**Status:** ⚠️ Partially Functional - Needs Completion  
**Last Updated:** October 22, 2025

---

## 🐛 KNOWN ISSUES

### Issue #1: Template/Model Mismatch ⚠️ HIGH
**Status:** Open  
**Discovered:** October 18, 2025  
**Severity:** High

**Problem:**
Template `food.html` expects 11 fields, but Food model only has 6. Causes AttributeError when accessing missing fields.

**Missing Fields:**
- office_location
- qty (quantity)
- bal_qty (balance quantity)
- budgeted_items
- additional_amount
- created_at, updated_at

**Workaround:** View uses `getattr(supply, 'field', 0)` to avoid crashes

**Permanent Fix:** Implement Phase 1 - Add FoodInventory model with all required fields

---

### Issue #2: Incorrect Total Amount ⚠️ MEDIUM
**Status:** Open  
**Discovered:** October 18, 2025  
**Severity:** Medium

**Problem:**
`total_amount` property returns only `unit_price` instead of `quantity × unit_price`

**Current Code:**
```python
@property
def total_amount(self):
    return self.unit_price or 0
```

**Impact:** Financial reports show incorrect totals

**Fix:** Update property to multiply quantity × unit_price (requires qty field first)

---

### Issue #3: No Inventory Tracking ⚠️ HIGH
**Status:** Open  
**Discovered:** October 18, 2025  
**Severity:** High

**Problem:**
System tracks food items but not daily quantities. Manual tracking required.

**Impact:**
- No consumption monitoring
- No low stock alerts
- No automated reordering

**Fix:** Implement Phase 1 & 2 features

---

## 📋 TODO LIST

### Phase 1: Foundation (HIGH PRIORITY)
- [ ] Add FoodInventory model with all fields
- [ ] Add FoodConsumption model for tracking
- [ ] Fix total_amount calculation
- [ ] Migrate existing Food data
- [ ] Update food.html template
- [ ] Fix FoodFilter to match model fields
- [ ] Add location-based filtering

**Estimated:** 2 weeks  
**Blocked By:** None  
**Assigned:** TBD

---

### Phase 2: Integration (MEDIUM PRIORITY)
- [ ] Add FoodPurchaseRequest model
- [ ] Integrate with ApprovalPolicy system
- [ ] Create FoodBudgetIntegrationService
- [ ] Add email notification system
- [ ] Build approval workflow views
- [ ] Create auto-approval logic (<$50)

**Estimated:** 3 weeks  
**Blocked By:** Phase 1 completion  
**Assigned:** TBD

---

### Phase 3: Analytics (LOW PRIORITY)
- [ ] Build analytics dashboard
- [ ] Add consumption trend charts
- [ ] Create cost analysis reports
- [ ] Add supplier performance metrics
- [ ] Make mobile-responsive
- [ ] Add data export functionality

**Estimated:** 2 weeks  
**Blocked By:** Phase 2 completion  
**Assigned:** TBD

---

## 🔍 TROUBLESHOOTING

### Problem: AttributeError on food.html template
**Symptoms:** Template crashes with "Food object has no attribute 'qty'"  
**Cause:** Template expects fields that don't exist  
**Solution:** Phase 1 implementation or update template to use only existing fields

### Problem: Total amounts incorrect in reports
**Symptoms:** Food costs show only unit prices, not totals  
**Cause:** total_amount property doesn't multiply by quantity  
**Solution:** Add qty field and fix total_amount calculation

### Problem: No alerts when stock low
**Symptoms:** Running out of items unexpectedly  
**Cause:** No low stock alert system implemented  
**Solution:** Implement Phase 1 (reorder_level, alerts)

### Problem: Food purchases don't appear in budget
**Symptoms:** Budget variance doesn't reflect food spending  
**Cause:** No budget integration  
**Solution:** Implement Phase 2 (FoodBudgetIntegrationService)

---

## 📊 TECHNICAL DEBT

### Debt #1: Manual Quantity Tracking
**Impact:** 6 hours/day staff time wasted  
**Cost:** $15,600/year  
**Fix:** Automate via Phase 1 implementation

### Debt #2: No Consumption Analytics
**Impact:** Can't optimize purchasing, 10% waste  
**Cost:** $12,000/year  
**Fix:** Phase 3 analytics dashboard

### Debt #3: Manual Approval Process
**Impact:** 2-3 day delays in procurement  
**Cost:** Stockouts, emergency purchases  
**Fix:** Phase 2 approval automation

---

## 🔔 MONITORING

### Metrics to Track (Post-Implementation):
- Daily consumption rate by item
- Stockout frequency
- Purchase approval turnaround time
- Food cost vs budget variance
- Supplier performance scores

### Alerts to Configure:
- Stock below reorder level
- Stockout predicted < 7 days
- Purchase pending approval > 48 hours
- Budget variance > 20%
- Consumption rate spike > 50%

---

## 📞 SUPPORT

### Current Workarounds:
1. **Manual tracking:** Use Excel spreadsheet for daily quantities
2. **Budget entry:** Manually create budget entries for food purchases
3. **Alerts:** Office managers check stock levels daily

### Future State:
- All automatic
- Real-time visibility
- Proactive alerts
- Integrated workflows

---

**See:** 07_DEPLOYMENT.md for implementation timeline


