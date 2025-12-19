# Budget System - Testing

**Last Updated:** October 22, 2025  
**Test Coverage:** Phase 1 & 2 Complete  
**Purpose:** Test scenarios, validation procedures, and test results log

---

## 🧪 TEST ENVIRONMENTS

### Local Development
- **URL:** `http://localhost:8000`
- **Database:** SQLite or local PostgreSQL
- **Setup:** `python manage.py runserver`
- **Test Users:** Create via `python manage.py createsuperuser`

### UAT (Staging)
- **URL:** `https://codamakutano.herokuapp.com`
- **Database:** Heroku PostgreSQL
- **Deployment:** `git push heroku [branch]:main`
- **Test Users:** Existing CODA test accounts

### Production
- **URL:** `https://codatrainingapp.herokuapp.com`
- **Database:** Heroku PostgreSQL (production data)
- **⚠️ Caution:** Real users, real data - test thoroughly in UAT first!

---

## 📋 TEST DATA SETUP

### Create Test Users
```python
from accounts.models import CustomerUser
from main.models import Company, Department

company = Company.objects.get_or_create(name='Test CODA', slug='test-coda')[0]
ops_dept = Department.objects.get_or_create(name='Operations', company=company)[0]

# Regular user
regular_user = CustomerUser.objects.create_user(
    username='testuser',
    email='testuser@coda.com',
    password='testpass123',
    company=company,
    is_staff=False
)

# Staff user (can approve)
staff_user = CustomerUser.objects.create_user(
    username='teststaff',
    email='teststaff@coda.com',
    password='testpass123',
    company=company,
    is_staff=True
)
```

---

## 🧪 FUNCTIONAL TESTS

### Test 1: Create Budget Request
**Objective:** Verify users can create budget requests

**Steps:**
1. Login as regular user
2. Navigate to `/finance/budget/request/new/`
3. Fill form (amount: $500, category: Office Supplies, priority: medium)
4. Submit

**Expected:**
- ✅ Request created successfully
- ✅ Status: Pending
- ✅ Requester set to current user
- ✅ Success message shown

---

### Test 2: View Approval Dashboard
**Objective:** Verify staff can access approval dashboard

**Steps:**
1. Login as staff user
2. Navigate to `/finance/budget/coda/approvals/`

**Expected:**
- ✅ Page loads <2 seconds
- ✅ Pending requests displayed
- ✅ Approve/reject buttons visible
- ✅ Statistics shown

---

### Test 3: Approve Budget Request
**Objective:** Verify staff can approve requests

**Steps:**
1. Login as staff user
2. Navigate to approvals dashboard
3. Click approve ✅ button
4. Confirm

**Expected:**
- ✅ Status → "Approved"
- ✅ `approved_by` set to staff user
- ✅ `approved_at` timestamp recorded
- ✅ Success message displayed

---

### Test 4: Reject Budget Request
**Objective:** Verify rejection with reason

**Steps:**
1. Click reject ❌ button
2. Enter reason: "Insufficient justification"
3. Confirm

**Expected:**
- ✅ Status → "Rejected"
- ✅ `rejected_by` and `rejected_at` set
- ✅ `rejection_reason` saved

---

### Test 5: Permission Check
**Objective:** Non-staff cannot approve

**Steps:**
1. Login as regular user
2. Try to access approvals page

**Expected:**
- ✅ Access denied or buttons hidden
- ✅ Appropriate error message

---

## 🔐 SECURITY TESTS

### Test 6: Cross-Company Access
**Objective:** Users can't access other companies' budgets

**Steps:**
1. Login as Company A user
2. Try to access Company B approval dashboard

**Expected:**
- ✅ 404 Not Found or 403 Forbidden

---

### Test 7: CSRF Protection
**Objective:** CSRF token required for approval

**Steps:**
1. POST to approval endpoint without CSRF token

**Expected:**
- ✅ 403 Forbidden
- ✅ Request not approved

---

## 🐛 REGRESSION TESTS

### Test 8: Dashboard Aggregation (Bug Fix - Oct 2, 2025)
**Background:** Dashboard had 177x inflation bug

**Test:**
1. Create budget: $100
2. Check dashboard total

**Expected:**
- ✅ Shows $100, NOT $17,700
- ✅ Uses correct F() expression aggregation

---

### Test 9: Approval Fields Exist (Bug Fix - Oct 13, 2025)
**Background:** approved_by field was missing

**Test:**
1. Approve a budget
2. View request detail
3. Check approved_by displays

**Expected:**
- ✅ No AttributeError
- ✅ approved_by.username displays correctly

---

## 🎯 TIER SYSTEM TESTS (Phase 2)

### Test 10: Tier Classification
**Objective:** Categories correctly classified

**Expected:**
- ✅ Tier A: 1 category (Rent)
- ✅ Tier B: 5 categories (Salaries, IT, Utilities, Travel, Office)
- ✅ Tier C: 19 categories

### Test 11: Auto-Approval Logic (Basic)
**Objective:** Tier A auto-approval works

**Test:**
1. Create request for Rent category
2. Amount within variance ($1,800-$2,200)
3. Submit

**Expected:**
- ✅ Auto-approved (if enabled)
- ✅ Finance Manager notified

---

### Test 12: Complete Budget Workflow (Oct 28, 2025)
**Objective:** End-to-end transaction → estimate → edit → submit → approve

**Test Steps:**
1. Verify transaction data exists (561 transactions, 97.1% categorized)
2. Generate budget estimates: `python manage.py generate_budget_projections --company coda --months 12 --save`
3. Navigate to dashboard: `/finance/budget-dashboard/coda/`
4. Click category in table → View Details or Edit
5. Modify budget amounts
6. Select priority (low/medium/high/urgent)
7. Add justification
8. Submit for approval

**Expected:**
- ✅ Budget estimates generated from transaction data
- ✅ Dashboard shows all categories with real data
- ✅ Tier information card displays correctly
- ✅ Priority selector works
- ✅ SmartApprovalService processes request
- ✅ Auto-approves Tier A or routes appropriately

---

### Test 13: Tier A Auto-Approval (Within Variance)
**Objective:** Verify auto-approval for Tier A categories within variance

**Setup:**
```python
from finance.models import BudgetCategory
category = BudgetCategory.objects.get(name="Rent")
category.approval_tier = 'A'
category.auto_approve_enabled = True
category.typical_monthly_amount = 10000.00
category.variance_threshold = 20.0  # 20% = ±$2,000
category.save()
```

**Test:**
1. Edit Rent category budget
2. Set amount to $11,000 (10% variance - within 20% threshold)
3. Add justification
4. Submit

**Expected:**
- ✅ Green success message: "✅ Budget request AUTO-APPROVED!"
- ✅ Status = 'approved'
- ✅ approved_by = system/auto
- ✅ approved_at timestamp set
- ✅ Instant approval (no manual step)

---

### Test 14: Tier A Manual Approval (Exceeds Variance)
**Objective:** Verify manual routing when variance threshold exceeded

**Test:**
1. Edit same Rent category
2. Set amount to $13,000 (30% variance - EXCEEDS 20% threshold)
3. Submit

**Expected:**
- ℹ️ Blue info message: "📋 Budget request submitted for manual approval"
- ✅ Status = 'submitted' (NOT approved)
- ✅ Routing reason: "Amount variance 30% exceeds threshold 20%"
- ✅ current_approver = Finance Manager
- ✅ Shows in Approvals tab as "Pending"

---

### Test 15: Tier B Priority-Based Routing
**Objective:** Verify Tier B routes based on priority

**Setup:**
```python
category = BudgetCategory.objects.get(name="IT and Software")
category.approval_tier = 'B'
category.save()
```

**Test 15a: High Priority**
1. Edit IT category
2. Set priority = "High"
3. Submit

**Expected:**
- ✅ Routes to Department Manager (fast-track)
- ✅ Message: "High priority operational expense"

**Test 15b: Low Priority**
1. Edit IT category
2. Set priority = "Low"
3. Submit

**Expected:**
- ✅ Routes to Finance Manager
- ✅ Message: "Low priority - Finance Manager approval required"

---

### Test 16: Tier C Strategic Approval
**Objective:** Verify Tier C routes to senior management

**Setup:**
```python
category = BudgetCategory.objects.get(name="Marketing and Advertising")
category.approval_tier = 'C'
category.save()
```

**Test:**
1. Edit Marketing category
2. Set priority = "High"
3. Submit

**Expected:**
- ✅ Routes to Senior Manager
- ✅ Message: "High priority strategic - Senior Manager"
- ✅ If priority = Low → Routes to Executive

---

### Test 17: UI Components Display
**Objective:** Verify all UI improvements display correctly

**Test:**
1. Navigate to Overview tab
2. Check button layout
3. Click Edit on any category
4. Verify tier information card
5. Verify priority selector
6. Verify submit button

**Expected:**
- ✅ Overview buttons grouped logically (Primary + Projections dropdown)
- ✅ Tier card shows: Category Type, Auto-Approval status, Typical Amount, Expected Approver
- ✅ Color-coded by tier (Green A, Yellow B, Blue C)
- ✅ Priority selector shows 4 options with emojis
- ✅ Context-aware help text based on tier
- ✅ Submit button large and prominent
- ✅ Dynamic message about auto-approval possibility

---

### Test 18: Dashboard Tab Navigation
**Objective:** Verify all 8 tabs work correctly

**Test:**
1. Click each tab: Overview, Approvals, Requests, Projections, Analytics, Estimation, Planning, Edit
2. Verify data loads

**Expected:**
- ✅ Overview: Shows statistics and category table
- ✅ Approvals: Shows pending requests
- ✅ Requests: Shows user's requests
- ✅ Projections: Shows budget projections
- ✅ All tabs load without errors
- ✅ No $0.00 or empty data (where data exists)

---

## ⚡ PERFORMANCE TESTS

### Test 12: Dashboard Load Time
**Objective:** Fast page load

**Test:** Load approval dashboard with 100+ requests

**Expected:**
- ✅ Page loads <2 seconds
- ✅ No N+1 queries (use select_related)

---

## 📊 TEST RESULTS LOG

| Date | Test Suite | Pass | Fail | Coverage | Notes |
|------|-----------|------|------|----------|-------|
| **Oct 28, 2025** | **Complete workflow** | **18** | **0** | **90%** | **SmartApproval integrated, UI improved** |
| Oct 22, 2025 | Full suite | 12 | 0 | 85% | Post-migration validation |
| Oct 13, 2025 | Phase 1 | 8 | 0 | 80% | Approval workflow complete |
| Oct 2, 2025 | Dashboard fix | 5 | 1 | 75% | Fixed aggregation bug |

---

## 🔧 TEST EXECUTION

### Run All Tests
```bash
# Django test suite
python manage.py test finance.tests.test_budget

# Regression tests
./tests/run_tests.sh --regression

# With coverage
python manage.py test finance --with-coverage
```

---

## 🔍 TROUBLESHOOTING TESTS

### Issue: Tests Fail Due to Missing Migrations
**Solution:**
```bash
python manage.py migrate
python manage.py test finance
```

### Issue: Permission Tests Fail
**Solution:** Check user.is_staff flag is set correctly

---

**Document Owner:** QA Team  
**Last Test Run:** October 28, 2025  
**Next Review:** After Phase 3 implementation


