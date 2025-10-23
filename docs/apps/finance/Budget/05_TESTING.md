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

### Test 11: Auto-Approval Logic
**Objective:** Tier A auto-approval works

**Test:**
1. Create request for Rent category
2. Amount within variance ($1,800-$2,200)
3. Submit

**Expected:**
- ✅ Auto-approved (if enabled)
- ✅ Finance Manager notified

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
**Last Test Run:** October 22, 2025  
**Next Review:** After Phase 3 implementation


