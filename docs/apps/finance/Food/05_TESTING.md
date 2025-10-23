# Food Supply Management - Testing

**Feature:** Food & Inventory Tracking  
**Status:** 🚧 Not Started - Pending Implementation  
**Last Updated:** October 22, 2025

---

## 🧪 TEST STRATEGY

### Phase 1: Foundation Testing
- Model creation and data integrity
- Inventory tracking accuracy
- Consumption calculation logic
- Location-based filtering

### Phase 2: Integration Testing
- Budget integration workflow
- Approval routing logic
- Email notification delivery
- Cross-system data consistency

### Phase 3: User Acceptance Testing
- Office manager workflows
- Procurement workflows
- Finance manager workflows
- Mobile responsiveness

---

## 📋 TEST SCENARIOS

### Test 1: Create Inventory Record
**Objective:** Verify FoodInventory creation

**Steps:**
1. Create Food item ("Rice")
2. Create FoodInventory for Office A
3. Set quantity = 50kg, reorder_level = 10kg

**Expected:**
- ✅ Record created successfully
- ✅ Quantity = 50kg
- ✅ Location = Office A
- ✅ Reorder level = 10kg

---

### Test 2: Log Daily Consumption
**Objective:** Verify consumption tracking updates inventory

**Steps:**
1. Start with Rice inventory = 50kg
2. Log consumption: 5kg used today
3. Check updated inventory

**Expected:**
- ✅ FoodConsumption record created
- ✅ Inventory quantity = 45kg (50 - 5)
- ✅ Consumption logged with date and user

---

### Test 3: Low Stock Alert
**Objective:** Verify alert triggers when stock low

**Steps:**
1. Set Rice reorder_level = 10kg
2. Consume until quantity = 9kg
3. Check for alert

**Expected:**
- ✅ Alert created/sent
- ✅ Email notification received
- ✅ Purchase request suggested

---

### Test 4: Auto-Approval (<$50)
**Objective:** Verify threshold-based auto-approval

**Steps:**
1. Create purchase request: Sugar, 10kg @ $30
2. Submit request
3. Check approval status

**Expected:**
- ✅ Status = "Approved" (auto)
- ✅ No manual approval needed
- ✅ Budget entry created
- ✅ Inventory updated

---

### Test 5: Manual Approval (>$50)
**Objective:** Verify routing to approver

**Steps:**
1. Create purchase request: Rice, 100kg @ $150
2. Submit request
3. Check routing

**Expected:**
- ✅ Status = "Pending"
- ✅ Routed to Department Head
- ✅ Email notification sent
- ✅ Approval button visible

---

### Test 6: Budget Integration
**Objective:** Verify purchase creates budget entry

**Steps:**
1. Approve purchase: Sugar, $30
2. Check budget system
3. Verify category mapping

**Expected:**
- ✅ Budget entry created
- ✅ Category = "Food & Accommodation"
- ✅ Amount = $30
- ✅ Status = "Approved"
- ✅ Variance updated

---

### Test 7: Consumption Rate Calculation
**Objective:** Verify daily rate auto-calculation

**Steps:**
1. Log consumption for 7 days: 5kg, 6kg, 4kg, 5kg, 7kg, 5kg, 4kg
2. Run calculation job
3. Check daily_consumption_rate

**Expected:**
- ✅ daily_consumption_rate = 5.14kg (36kg / 7 days)
- ✅ Auto-calculated, no manual entry
- ✅ Updated daily

---

### Test 8: Stockout Prediction
**Objective:** Verify stockout date prediction

**Setup:**
- Current quantity = 25kg
- Daily consumption rate = 5kg/day

**Expected:**
- ✅ Predicted stockout = 5 days from now
- ✅ Alert triggered (< 7 days)
- ✅ Reorder suggestion shown

---

### Test 9: Multi-Location Filtering
**Objective:** Office managers see only their office

**Steps:**
1. Login as Office A manager
2. View inventory
3. Check visibility

**Expected:**
- ✅ See only Office A inventory
- ✅ Cannot see Office B inventory
- ✅ Totals calculated for Office A only

---

### Test 10: Purchase History
**Objective:** Track all purchases

**Steps:**
1. Approve 3 purchases over 1 month
2. View FoodHistory
3. Check records

**Expected:**
- ✅ All 3 purchases logged
- ✅ Quantities correct
- ✅ Dates accurate
- ✅ Suppliers linked

---

## 🔍 EDGE CASES

### Edge Case 1: Zero Consumption
**Scenario:** No consumption for 7 days  
**Expected:** daily_consumption_rate = 0, no stockout alert

### Edge Case 2: Negative Inventory
**Scenario:** Try to log consumption > available quantity  
**Expected:** Error message, transaction rejected

### Edge Case 3: Concurrent Updates
**Scenario:** Two users log consumption simultaneously  
**Expected:** Both updates applied, no data loss

### Edge Case 4: Deleted Supplier
**Scenario:** Delete supplier with active food items  
**Expected:** Graceful handling, reference set to NULL or prevented

---

## 📊 TEST RESULTS LOG

| Date | Test Suite | Pass | Fail | Coverage | Notes |
|------|-----------|------|------|----------|-------|
| TBD | Phase 1 | - | - | - % | Not started |
| TBD | Phase 2 | - | - | - % | Not started |
| TBD | Phase 3 | - | - | - % | Not started |

---

## 🚀 TEST EXECUTION

### When Phase 1 Complete:
```bash
# Run model tests
python manage.py test finance.tests.test_food_models

# Run view tests
python manage.py test finance.tests.test_food_views

# Run integration tests
python manage.py test finance.tests.test_food_integration
```

---

**See:** 06_MAINTENANCE.md for troubleshooting


