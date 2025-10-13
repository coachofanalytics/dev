# Budget System - Testing Guide

**Last Updated:** October 13, 2025  
**Test Coverage:** Phase 1 Complete

---

## Test Environments

### Local Development
- **URL:** `http://localhost:8000`
- **Database:** SQLite or PostgreSQL
- **Setup:** `python manage.py runserver`
- **Test Users:** Create via `python manage.py createsuperuser`

### UAT (Staging)
- **URL:** `https://codamakutano.herokuapp.com`
- **Database:** Heroku PostgreSQL
- **Deployment:** `git push heroku 25.10_UAT_DEPLOYMENT_FIX_CM:main`
- **Test Users:** Existing CODA test accounts

### Production
- **URL:** `https://codatrainingapp.herokuapp.com`
- **Database:** Heroku PostgreSQL (production data)
- **Caution:** Real users, real data - test thoroughly in UAT first!

---

## Test Data Setup

### Prerequisites

#### Create Test Users
```bash
python manage.py shell
```

```python
from accounts.models import CustomerUser
from main.models import Company, Department

# Create company
company = Company.objects.get_or_create(name='Test CODA', slug='test-coda')[0]

# Create departments
ops_dept = Department.objects.get_or_create(
    name='Operations',
    company=company
)[0]

# Create regular user
regular_user = CustomerUser.objects.create_user(
    username='testuser',
    email='testuser@coda.com',
    password='testpass123',
    company=company,
    is_staff=False
)

# Create staff user (can approve)
staff_user = CustomerUser.objects.create_user(
    username='teststaff',
    email='teststaff@coda.com',
    password='testpass123',
    company=company,
    is_staff=True
)
```

#### Create Test Budget Categories
```python
from finance.models import BudgetCategory

categories = [
    'Office Supplies',
    'Utilities',
    'Travel and Entertainment',
    'Marketing and Advertising',
    'IT and Software',
]

for cat_name in categories:
    BudgetCategory.objects.get_or_create(name=cat_name)
```

#### Create Sample Budget Requests
```python
from finance.models import BudgetRequest

BudgetRequest.objects.create(
    requester=regular_user,
    amount=500.00,
    purpose="Office supplies for Q4",
    department=ops_dept,
    budget_category=BudgetCategory.objects.get(name='Office Supplies'),
    priority='medium',
    status='pending'
)

BudgetRequest.objects.create(
    requester=regular_user,
    amount=2500.00,
    purpose="Team training workshop",
    department=ops_dept,
    budget_category=BudgetCategory.objects.get(name='Marketing and Advertising'),
    priority='high',
    status='pending'
)
```

---

## Functional Tests (Phase 1)

### Test 1: Create Budget Request

**Objective:** Verify users can create budget requests

**Pre-conditions:**
- User logged in
- Budget categories exist
- Department exists

**Steps:**
1. Login as regular user (`testuser`)
2. Navigate to `/finance/budget/request/new/` (or use create button)
3. Fill form:
   - **Title:** "Test Budget Request"
   - **Amount:** $500.00
   - **Purpose:** "Testing budget creation functionality"
   - **Category:** Office Supplies
   - **Priority:** Medium
4. Click "Submit"

**Expected Result:**
- ✅ Budget request created successfully
- ✅ Status: Pending
- ✅ Requester set to current user
- ✅ Redirected to request detail or list page
- ✅ Success message shown

**Actual Result:** _[Fill during testing]_

**Status:** _[Pass/Fail]_

---

### Test 2: View Approval Dashboard (Staff User)

**Objective:** Verify staff can access approval dashboard

**Pre-conditions:**
- Staff user logged in
- At least one pending budget request exists

**Steps:**
1. Login as staff user (`teststaff`)
2. Navigate to `/finance/budget/{company-slug}/approvals/`
3. Observe page contents

**Expected Result:**
- ✅ Page loads successfully (<2 seconds)
- ✅ Pending requests table displayed
- ✅ Approve/reject buttons visible
- ✅ Request details shown (amount, category, requester, date)
- ✅ Statistics summary displayed
- ✅ Recent approvals/rejections shown

**Actual Result:** _[Fill during testing]_

**Status:** _[Pass/Fail]_

---

### Test 3: Approve Budget Request

**Objective:** Verify staff can approve budget requests

**Pre-conditions:**
- Staff user logged in
- Pending budget request exists

**Steps:**
1. Login as staff user
2. Navigate to `/finance/budget/{company-slug}/approvals/`
3. Find pending request (e.g., "Test Budget Request - $500")
4. Click the green ✅ "Approve" icon/button
5. Confirm action (if confirmation modal exists)
6. Observe results

**Expected Result:**
- ✅ Status changes from "Pending" to "Approved"
- ✅ `approved_by` set to current staff user
- ✅ `approved_at` timestamp recorded
- ✅ Success message displayed: "Budget request approved successfully"
- ✅ Request removed from pending list
- ✅ Request appears in recent approvals section
- ✅ Email notification sent to requester (Phase 1.5)

**Actual Result:** _[Fill during testing]_

**Status:** _[Pass/Fail]_

---

### Test 4: Reject Budget Request

**Objective:** Verify staff can reject budget requests with reason

**Pre-conditions:**
- Staff user logged in
- Pending budget request exists

**Steps:**
1. Login as staff user
2. Navigate to approvals dashboard
3. Click the red ❌ "Reject" icon/button
4. **If modal appears:**
   - Enter rejection reason: "Insufficient justification for this expense"
   - Click "Confirm Reject"
5. **If no modal:**
   - Enter reason in form field
   - Submit
6. Observe results

**Expected Result:**
- ✅ Status changes to "Rejected"
- ✅ `rejected_by` set to current staff user
- ✅ `rejected_at` timestamp recorded
- ✅ `rejection_reason` saved correctly
- ✅ Success message displayed
- ✅ Request removed from pending list
- ✅ Request appears in recent rejections section
- ✅ Email notification sent to requester

**Actual Result:** _[Fill during testing]_

**Status:** _[Pass/Fail]_

---

### Test 5: Permission Check - Non-Staff Cannot Approve

**Objective:** Verify regular users cannot approve budgets

**Pre-conditions:**
- Regular (non-staff) user logged in
- Pending budget requests exist

**Steps:**
1. Login as regular user (`testuser`)
2. Try to navigate to `/finance/budget/{company-slug}/approvals/`
3. **If accessible:** Check for approve/reject buttons
4. **Attempt direct API call (advanced):**
   ```bash
   curl -X POST https://codamakutano.herokuapp.com/finance/budget/coda/approve/123/ \
        -H "Cookie: sessionid=..." \
        -H "X-CSRFToken: ..."
   ```

**Expected Result:**
- ✅ Cannot access approvals page (403 Forbidden or redirect)
- ✅ OR page accessible but no approve/reject buttons visible
- ✅ Direct API call returns 403 error
- ✅ Error message: "You don't have permission to approve requests"

**Actual Result:** _[Fill during testing]_

**Status:** _[Pass/Fail]_

---

### Test 6: View Budget Request Detail

**Objective:** Verify budget request detail page displays correctly

**Pre-conditions:**
- User logged in
- Budget request exists

**Steps:**
1. Login as any user
2. Navigate to `/finance/budget/request/{request_id}/`
3. Or click on a request from list view
4. Observe page contents

**Expected Result:**
- ✅ Request details displayed:
  - Title, amount, purpose
  - Category, department
  - Requester name, date created
  - Current status
- ✅ If approved: Shows approved_by, approved_at
- ✅ If rejected: Shows rejected_by, rejected_at, rejection_reason
- ✅ Approval history/timeline (if implemented)
- ✅ Appropriate action buttons based on permissions

**Actual Result:** _[Fill during testing]_

**Status:** _[Pass/Fail]_

---

## Edge Cases & Error Handling

### Test 7: Approve Already Approved Budget

**Objective:** Verify system handles double-approval gracefully

**Steps:**
1. Approve a budget request
2. Try to approve the same request again (refresh page, click approve again)

**Expected Result:**
- ✅ Error message: "This request has already been approved"
- ✅ OR button disabled/hidden for approved requests
- ✅ No data corruption
- ✅ Original approval data preserved (approved_by, approved_at)

**Actual Result:** _[Fill during testing]_

**Status:** _[Pass/Fail]_

---

### Test 8: Reject Already Rejected Budget

**Objective:** Verify system handles double-rejection

**Steps:**
1. Reject a budget request with reason
2. Try to reject again

**Expected Result:**
- ✅ Error message or button disabled
- ✅ Original rejection data preserved

**Actual Result:** _[Fill during testing]_

**Status:** _[Pass/Fail]_

---

### Test 9: Large Budget Amount

**Objective:** Verify system handles large monetary values

**Steps:**
1. Create budget request with amount = $1,000,000.00
2. View in dashboard
3. Approve/reject

**Expected Result:**
- ✅ Amount displays correctly (no overflow, proper formatting)
- ✅ Database stores accurately (DECIMAL field)
- ✅ Approval/rejection works normally
- ✅ No JavaScript errors with large numbers

**Actual Result:** _[Fill during testing]_

**Status:** _[Pass/Fail]_

---

### Test 10: Missing Rejection Reason

**Objective:** Verify rejection requires reason

**Steps:**
1. Click "Reject" on a budget request
2. Leave rejection reason blank
3. Try to submit

**Expected Result:**
- ✅ Form validation error: "Rejection reason is required"
- ✅ Cannot submit without reason
- ✅ Request status not changed

**Actual Result:** _[Fill during testing]_

**Status:** _[Pass/Fail]_

---

### Test 11: Empty or Invalid Budget Amount

**Objective:** Verify amount validation

**Steps:**
1. Try to create budget with:
   - Amount = 0
   - Amount = negative (-500)
   - Amount = non-numeric ("abc")
   - Amount = blank

**Expected Result:**
- ✅ Validation error for each case
- ✅ Error messages user-friendly
- ✅ Form data preserved (no data loss)

**Actual Result:** _[Fill during testing]_

**Status:** _[Pass/Fail]_

---

## Integration Tests

### Test 12: Budget + Dashboard Integration

**Objective:** Verify approved budgets appear in main dashboard

**Pre-conditions:**
- Main dashboard exists at `/dashboard/`

**Steps:**
1. Approve a budget request
2. Navigate to `/dashboard/`
3. Check budget statistics section

**Expected Result:**
- ✅ Approved budget count updated
- ✅ Total approved amount accurate
- ✅ Budget appears in recent activity (if shown)
- ✅ Data consistent across pages

**Actual Result:** _[Fill during testing]_

**Status:** _[Pass/Fail]_

---

### Test 13: Budget + Email Integration

**Objective:** Verify email notifications sent on approval/rejection

**Pre-conditions:**
- Email backend configured (check settings)
- Email addresses valid

**Steps:**
1. Approve a budget request
2. Check requester's email inbox
3. Reject a budget request
4. Check email again

**Expected Result:**
- ✅ Approval email sent with:
  - Budget details
  - Approved by (name)
  - Approved at (date/time)
- ✅ Rejection email sent with:
  - Budget details
  - Rejection reason
  - Rejected by, rejected at

**Actual Result:** _[Fill during testing]_

**Status:** _[Pass/Fail]_

**Note:** Check spam folder, verify email logs in Heroku if not received

---

## Performance Tests

### Test 14: Approval Dashboard Load Time

**Objective:** Verify page loads quickly with many budgets

**Pre-conditions:**
- Create 100+ budget requests (script or fixtures)

**Steps:**
1. Navigate to `/finance/budget/{company-slug}/approvals/`
2. Measure page load time (browser dev tools, Network tab)
3. Check database query count (Django Debug Toolbar if enabled)

**Expected Result:**
- ✅ Page loads in <2 seconds
- ✅ All budgets displayed (or paginated)
- ✅ No N+1 query problems
- ✅ Responsive UI (no lag when scrolling)

**Actual Result:** _[Fill during testing]_

**Metrics:**
- Load time: _____ ms
- Query count: _____ queries
- Database time: _____ ms

**Status:** _[Pass/Fail]_

---

### Test 15: Concurrent Approvals

**Objective:** Test system behavior with simultaneous approvals

**Steps:**
1. Open two browser windows (or two users)
2. Both navigate to same pending budget request
3. Both click "Approve" at nearly the same time

**Expected Result:**
- ✅ Only one approval recorded
- ✅ Second attempt shows "already approved" message
- ✅ No database errors
- ✅ Data integrity maintained

**Actual Result:** _[Fill during testing]_

**Status:** _[Pass/Fail]_

---

## Security Tests

### Test 16: Cross-Company Access

**Objective:** Verify users cannot access other companies' budgets

**Pre-conditions:**
- Two companies exist (Company A, Company B)
- User A belongs to Company A
- Budget requests exist for both companies

**Steps:**
1. Login as User A (Company A)
2. Try to access Company B's approval dashboard:
   `/finance/budget/{company-b-slug}/approvals/`
3. Try direct URL to Company B's budget request:
   `/finance/budget/request/{company-b-request-id}/`

**Expected Result:**
- ✅ 404 Not Found or 403 Forbidden
- ✅ No data from Company B visible
- ✅ No SQL injection vulnerability

**Actual Result:** _[Fill during testing]_

**Status:** _[Pass/Fail]_

---

### Test 17: SQL Injection Attempt

**Objective:** Verify input sanitization

**Steps:**
1. Create budget request with malicious input:
   - Title: `'; DROP TABLE finance_budgetrequest; --`
   - Purpose: `<script>alert('XSS')</script>`
   - Amount: `' OR '1'='1`

**Expected Result:**
- ✅ Input escaped properly (no SQL executed)
- ✅ No database damage
- ✅ Budget created with literal string (escaped)
- ✅ No XSS when viewing (HTML escaped)

**Actual Result:** _[Fill during testing]_

**Status:** _[Pass/Fail]_

---

### Test 18: CSRF Protection

**Objective:** Verify CSRF token required for approval actions

**Steps:**
1. Try to POST to approval endpoint without CSRF token:
   ```bash
   curl -X POST https://codamakutano.herokuapp.com/finance/budget/coda/approve/123/
   ```

**Expected Result:**
- ✅ 403 Forbidden (CSRF verification failed)
- ✅ Request not approved

**Actual Result:** _[Fill during testing]_

**Status:** _[Pass/Fail]_

---

## Regression Tests (Critical Bugs)

### Test 19: Dashboard Aggregation Bug (Fixed Oct 2, 2025)

**Objective:** Verify dashboard doesn't have 177x inflation bug

**Background:** Dashboard was using `Sum('quantity') * Sum('unit_price')` which caused massive over-counting

**Steps:**
1. Create budget: $100
2. Approve it
3. Navigate to main dashboard
4. Check total approved budget amount

**Expected Result:**
- ✅ Total shows $100, **not** $17,700
- ✅ Uses correct aggregation: `Sum(F('amount'))`

**Actual Result:** _[Fill during testing]_

**Status:** _[Pass/Fail]_

**Reference:** See `MASTER_REFERENCE.md` - Critical Fixes section

---

### Test 20: Approval Fields Missing Bug (Fixed Oct 13, 2025)

**Objective:** Verify approved_by/rejected_by fields exist and work

**Background:** Initial model lacked audit fields, causing template errors

**Steps:**
1. Approve a budget
2. View budget detail page
3. Check that approved_by username displays

**Expected Result:**
- ✅ `approved_by.username` displays correctly
- ✅ No template errors: "AttributeError: 'BudgetRequest' object has no attribute 'approved_by'"
- ✅ Migration 0099 applied successfully

**Actual Result:** _[Fill during testing]_

**Status:** _[Pass/Fail]_

---

## Browser Compatibility

### Test 21: Theme Switcher (Cross-Browser)

**Browsers to Test:** Chrome, Firefox, Safari, Edge

**Steps:**
1. Load approval dashboard
2. Click "Navy & Gold" theme button
3. Observe color changes
4. Click "Purple" theme button
5. Reload page
6. Check if theme persists

**Expected Result (All Browsers):**
- ✅ Theme switches correctly
- ✅ Colors apply to all elements
- ✅ Preference saved in localStorage
- ✅ Theme persists after reload
- ✅ No JavaScript errors in console

**Actual Results:**
- Chrome: _[Pass/Fail]_
- Firefox: _[Pass/Fail]_
- Safari: _[Pass/Fail]_
- Edge: _[Pass/Fail]_

---

## Automated Tests (Future)

### Unit Tests
**File:** `coda/finance/tests/test_budget_approval.py`

```python
from django.test import TestCase
from finance.models import BudgetRequest
from accounts.models import CustomerUser

class BudgetApprovalTestCase(TestCase):
    def setUp(self):
        self.staff_user = CustomerUser.objects.create_user(
            username='staff',
            is_staff=True
        )
        self.regular_user = CustomerUser.objects.create_user(
            username='regular',
            is_staff=False
        )
        self.budget = BudgetRequest.objects.create(
            requester=self.regular_user,
            amount=500.00,
            status='pending'
        )
    
    def test_staff_can_approve(self):
        """Test that staff users can approve budgets"""
        from finance.views.budget.editing import _can_approve_request
        self.assertTrue(_can_approve_request(self.staff_user, self.budget))
    
    def test_regular_user_cannot_approve(self):
        """Test that regular users cannot approve budgets"""
        from finance.views.budget.editing import _can_approve_request
        self.assertFalse(_can_approve_request(self.regular_user, self.budget))
    
    def test_approve_sets_fields(self):
        """Test that approving sets approved_by and approved_at"""
        self.budget.approve(self.staff_user)
        self.assertEqual(self.budget.approved_by, self.staff_user)
        self.assertIsNotNone(self.budget.approved_at)
        self.assertEqual(self.budget.status, 'approved')
```

**Run:**
```bash
python manage.py test finance.tests.test_budget_approval
```

---

## Test Results Log

### Test Run: October 13, 2025 (UAT v904)

| Test # | Name | Status | Notes |
|--------|------|--------|-------|
| 1 | Create Budget Request | ✅ Pass | - |
| 2 | View Approval Dashboard | ✅ Pass | - |
| 3 | Approve Budget | ✅ Pass | - |
| 4 | Reject Budget | ✅ Pass | - |
| 5 | Permission Check | ✅ Pass | Non-staff correctly blocked |
| 6 | View Detail | ✅ Pass | - |
| 19 | Dashboard Aggregation | ✅ Pass | No inflation bug |
| 20 | Approval Fields | ✅ Pass | Fields display correctly |

**Overall:** 8/8 tests passed  
**Tester:** CM  
**Environment:** UAT  
**Version:** v904  
**Date:** October 13, 2025

---

### Test Run: October 2, 2025 (UAT v895)

| Test # | Name | Status | Notes |
|--------|------|--------|-------|
| 1 | Create Budget | ✅ Pass | - |
| 3 | Approve Budget | ❌ Fail | `approved_by` field missing |

**Overall:** 1/2 tests passed  
**Tester:** CM  
**Environment:** UAT  
**Version:** v895  
**Action Taken:** Created migration 0099, added missing fields

---

## Known Issues

### Current (as of Oct 13, 2025)
- [ ] No email notifications yet (SMTP not configured in UAT)
- [ ] Cannot bulk approve multiple requests
- [ ] Mobile UI needs polish (buttons small on phone)
- [ ] No pagination on approval list (slow with 100+ requests)

### Resolved
- ✅ BudgetRequest.approved_by missing (Fixed Oct 13)
- ✅ Dashboard aggregation bug (Fixed Oct 2)
- ✅ Permission check errors (Fixed Oct 13)

---

## Test Checklist (Pre-Deployment)

### Before Deploying to UAT
- [ ] All unit tests pass locally
- [ ] No linter errors (`flake8`, `pylint`)
- [ ] Migrations created and run locally
- [ ] Test data created successfully
- [ ] Manual smoke tests pass

### UAT Testing (Before Production)
- [ ] Test 1-6: Core functionality
- [ ] Test 7-11: Edge cases
- [ ] Test 12-13: Integration
- [ ] Test 14-15: Performance
- [ ] Test 16-18: Security
- [ ] Test 19-20: Regression
- [ ] Test 21: Browser compatibility

### Production Deployment Checklist
- [ ] All UAT tests pass
- [ ] Database backup created
- [ ] Migrations reviewed (no data loss)
- [ ] Rollback plan prepared
- [ ] Deploy during low-traffic window
- [ ] Monitor logs for 1 hour post-deployment
- [ ] Run smoke tests on production
- [ ] Notify users of changes

---

## Troubleshooting

### Issue: Cannot approve budget (button does nothing)

**Possible Causes:**
1. User not staff (check `user.is_staff`)
2. Budget already approved (check status)
3. JavaScript error (check browser console F12)
4. CSRF token missing (check form)

**Debug Steps:**
```bash
# Check user permissions
python manage.py shell
>>> from accounts.models import CustomerUser
>>> user = CustomerUser.objects.get(username='teststaff')
>>> user.is_staff
True  # Should be True

# Check budget status
>>> from finance.models import BudgetRequest
>>> budget = BudgetRequest.objects.get(id=123)
>>> budget.status
'pending'  # Should be pending

# Check browser console for JS errors
# F12 → Console tab
```

---

### Issue: 500 error on approval page

**Possible Causes:**
1. Missing database fields (migration needed)
2. Template error (undefined variable)
3. Query error (database issue)

**Debug Steps:**
```bash
# Check Heroku logs
heroku logs --tail --app codamakutano --num 100

# Look for traceback

# Common errors:
# - AttributeError: object has no attribute 'approved_by'
#   → Run migration 0099
# - VariableDoesNotExist: Failed lookup for key [username] in None
#   → Budget has no approved_by (fix template to check if None)
```

---

### Issue: Theme not saving

**Possible Causes:**
1. Browser localStorage disabled
2. JavaScript error preventing save
3. Incorrect theme attribute

**Debug Steps:**
```javascript
// Open browser console (F12)
// Check localStorage
localStorage.getItem('dashboardTheme')
// Should return 'navy' or 'purple'

// Try setting manually
localStorage.setItem('dashboardTheme', 'purple')
location.reload()
// Page should load with purple theme
```

---

## Test Data Cleanup

### After Testing (Local/UAT)
```python
# Delete test budget requests
BudgetRequest.objects.filter(requester__username='testuser').delete()

# Delete test users
CustomerUser.objects.filter(username__startswith='test').delete()

# Or reset entire database (LOCAL ONLY!)
python manage.py flush
python manage.py migrate
```

**WARNING:** Never run `flush` on production!

---

**Maintained by:** Cursor AI Assistant  
**Last Test Run:** October 13, 2025  
**Next Scheduled Test:** After Phase 2 implementation

