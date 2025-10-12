# Finance App Testing Guide - Post Reorganization

## Test Environment Setup

### Test Users Created
All passwords: `test123`

| Username | Email | Role | Staff |
|----------|-------|------|-------|
| budget_manager | budget@coda.co.ke | Budget Manager | Yes |
| finance_officer | finance@coda.co.ke | Finance Officer | No |
| it_manager | it@coda.co.ke | IT Manager | No |
| investor_user | investor@coda.co.ke | Investor | No |

### Local Server
```bash
cd /Users/coda/PROJECTS/CODA/DEVELOPMENT/DEV
source venv/bin/activate
cd coda
python manage.py runserver 0.0.0.0:8000
```

Server URL: `http://127.0.0.1:8000`

---

## TEST CHECKLIST

### 1. Budget Dashboard Tests

#### Test 1.1: Budget Dashboard Access
- [ ] Login as `budget_manager`
- [ ] Navigate to: `http://127.0.0.1:8000/finance/budget-dashboard/coda/`
- [ ] Verify:
  - Dashboard loads without errors
  - Budget categories display correctly
  - Budget totals calculate properly
  - Charts/graphs render (if any)

#### Test 1.2: Budget Data Display
- [ ] Check budget category breakdown
- [ ] Verify transaction history displays
- [ ] Test budget vs actual comparison
- [ ] Check date range filters work

---

### 2. Budget Request Flow Tests

#### Test 2.1: Create Budget Request
- [ ] Login as `finance_officer`
- [ ] Navigate to: `http://127.0.0.1:8000/finance/budget-requests/`
- [ ] Click "New Budget Request" or similar button
- [ ] Fill out form:
  - Category
  - Amount
  - Justification
  - Date range
- [ ] Submit request
- [ ] Verify success message

#### Test 2.2: View Budget Requests
- [ ] Login as `budget_manager`
- [ ] Navigate to budget requests list
- [ ] Verify request appears in list
- [ ] Check request details display correctly
- [ ] Verify status shows "Pending"

---

### 3. Approval Workflow Tests

#### Test 3.1: Approve Budget Request
- [ ] Login as `budget_manager`
- [ ] Navigate to: `http://127.0.0.1:8000/finance/budget-approvals/`
- [ ] Find pending request
- [ ] Click "Approve" button
- [ ] Add approval notes (if required)
- [ ] Confirm approval
- [ ] Verify:
  - Status changes to "Approved"
  - Approval notification sent (check logs)
  - Approval audit trail created

#### Test 3.2: Reject Budget Request
- [ ] Create another budget request
- [ ] Login as `budget_manager`
- [ ] Click "Reject" button
- [ ] Add rejection reason
- [ ] Confirm rejection
- [ ] Verify:
  - Status changes to "Rejected"
  - Rejection notification sent
  - Reason saved correctly

---

### 4. Template Buttons Tests

#### Test 4.1: Budget Dashboard Buttons
- [ ] "Add Budget Item" button
- [ ] "Edit Budget" button
- [ ] "Delete Budget" button (if applicable)
- [ ] "Export Budget" button
- [ ] "View Details" button

#### Test 4.2: Transaction Entry Buttons
- [ ] Navigate to: `http://127.0.0.1:8000/finance/smart-transaction-entry/`
- [ ] "Add Transaction" button
- [ ] "Save Transaction" button
- [ ] "Cancel" button
- [ ] "Attachment Upload" button (if any)

#### Test 4.3: Approval Buttons
- [ ] "Approve" button (green)
- [ ] "Reject" button (red)
- [ ] "Request More Info" button (if applicable)
- [ ] "View History" button

---

### 5. Smart Transaction Entry Tests

#### Test 5.1: Create Transaction
- [ ] Navigate to: `http://127.0.0.1:8000/finance/smart-transaction-entry/`
- [ ] Fill transaction form:
  - Amount
  - Category (should auto-suggest)
  - Subcategory
  - Description
  - Date
- [ ] Test AI predictions (if enabled)
- [ ] Verify cascading dropdowns work
- [ ] Submit transaction
- [ ] Verify success

#### Test 5.2: Transaction Validation
- [ ] Try submitting with missing required fields
- [ ] Test amount validation (negative, zero, large numbers)
- [ ] Test date validation (future dates, past dates)
- [ ] Verify error messages display correctly

---

### 6. Automation Tests

#### Test 6.1: Auto-Approval Rules
- [ ] Navigate to: `http://127.0.0.1:8000/finance/automation/`
- [ ] Check if automation dashboard loads
- [ ] Verify approval policies display
- [ ] Test creating auto-approval rule
- [ ] Submit request that meets auto-approval criteria
- [ ] Verify automatic approval happens

#### Test 6.2: Notification Automation
- [ ] Submit budget request
- [ ] Check if email notification sent (check logs)
- [ ] Approve request
- [ ] Verify approval notification
- [ ] Check notification history

#### Test 6.3: Compliance Checks
- [ ] Submit request exceeding budget limit
- [ ] Verify compliance warning appears
- [ ] Check audit logs created
- [ ] Test policy enforcement

---

### 7. KCC Loan System Tests

#### Test 7.1: Loan Application
- [ ] Navigate to loan system (URL TBD)
- [ ] Create new loan application
- [ ] Fill application form:
  - Loan amount
  - Purpose
  - Collateral
  - Repayment period
- [ ] Submit application
- [ ] Verify success

#### Test 7.2: Loan Approval
- [ ] Login as approver
- [ ] View pending loan applications
- [ ] Review application details
- [ ] Approve/reject loan
- [ ] Verify status update

---

### 8. Investor Dashboard Tests

#### Test 8.1: Investor View
- [ ] Login as `investor_user`
- [ ] Navigate to investor dashboard
- [ ] Verify:
  - Portfolio summary displays
  - Investment performance metrics
  - Transaction history
  - Reports accessible

#### Test 8.2: Investor Reports
- [ ] Generate financial report
- [ ] Export to PDF/Excel
- [ ] Verify data accuracy
- [ ] Check date range filters

---

## URLS TO TEST

### Core Finance URLs
- `/finance/` - Finance home
- `/finance/budget-dashboard/coda/` - Budget dashboard
- `/finance/smart-transaction-entry/` - Smart transaction form
- `/finance/transactions/` - Transaction list
- `/finance/budget-requests/` - Budget requests list
- `/finance/budget-approvals/` - Approval dashboard

### Budget Management
- `/finance/budget/<company_slug>/` - Company budget view
- `/finance/budget_projection/<subtitle>/` - Budget projections
- `/finance/add_budget_item/` - Add budget item

### Automation & Workflow
- `/finance/automation/` - Automation dashboard
- `/finance/automation/budget-requests/` - Request automation
- `/finance/automation/policies/` - Approval policies
- `/finance/automation/audit-logs/` - Audit logs

### API Endpoints
- `/finance/api/categories/` - Category API
- `/finance/api/subcategories/` - Subcategory API
- `/finance/api/budget-predictions/` - AI predictions

---

## EXPECTED RESULTS

### ✅ Success Criteria
1. All URLs load without 500 errors
2. Forms submit successfully
3. Buttons trigger correct actions
4. Approval flow completes end-to-end
5. Notifications are generated
6. Audit trails are created
7. Data displays accurately
8. No console errors in browser
9. Mobile responsive (if applicable)
10. Performance is acceptable (<2s load time)

### ❌ Issues to Log
- Any 404 or 500 errors
- Broken buttons
- Missing form fields
- Incorrect calculations
- Missing notifications
- Permission errors
- Template rendering issues

---

## BROWSER TESTING

Test in multiple browsers:
- [ ] Chrome/Chromium
- [ ] Firefox
- [ ] Safari
- [ ] Mobile Safari (iOS)
- [ ] Chrome Mobile (Android)

---

## PERFORMANCE TESTING

- [ ] Dashboard load time < 2 seconds
- [ ] Form submission response < 1 second
- [ ] API calls respond < 500ms
- [ ] No memory leaks (check browser DevTools)

---

## NOTES

- Check browser console (F12) for JavaScript errors
- Check Django server logs for backend errors
- Test with both staff and non-staff users
- Verify permissions are enforced correctly
- Document any issues in GitHub/issue tracker

---

**Testing Date:** _______________  
**Tested By:** _______________  
**Build Version:** Post-reorganization (Oct 7, 2025)  
**Status:** [ ] PASS  [ ] FAIL  [ ] NEEDS WORK

