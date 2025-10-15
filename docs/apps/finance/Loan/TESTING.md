# Loan System - Testing

Before Testing:
[ ] Run: python manage.py populate_loan_products (creates loan products)
[ ] Configure email backend (see EMAIL_TESTING_GUIDE.md)
[ ] Create test users (borrower + guarantor)
[ ] Verify email settings in environment
## Key Test Scenarios

### Test 1: View Loan Products
1. Navigate to `/finance/loans/products/`
2. Verify products display with details
3. Check KCC products marked correctly

**Expected:** All active products shown with accurate info

### Test 2: Apply for Loan
1. Select a loan product
2. Fill application form
3. Submit
4. Check status = "Pending"

**Expected:** Application created successfully

### Test 3: Eligibility Check
1. Navigate to `/finance/loans/eligibility/`
2. Enter loan amount
3. System checks employment, income, existing loans
4. Returns: Eligible or Not Eligible with reason

**Expected:** Accurate eligibility determination

### Test 4: Loan Analytics Dashboard (Admin)
1. Login as admin
2. Navigate to `/finance/loans/analytics/`
3. View metrics

**Expected:** 
- Applications count
- Approval rate
- Charts display correctly

## Regression Tests

### Test 5: LoanProduct.term_months (Fixed Oct 13)
1. Access admin: `/admin/finance/loanproduct/`
2. Verify column shows "Term Months" (not min_term_months)
3. Create new product with term_months=12

Scenario 1: Loan Application Without Guarantor
1. Login as staff member
2. Navigate to /finance/loan-home/
3. Select a loan product
4. Fill application form (no guarantor)
5. Submit
✅ Expected: Success, confirmation page


Scenario 2: Loan Application With Staff Guarantor

1. Login as staff member
2. Select loan product
3. Fill application form
4. Select staff guarantor from top 3 list
5. Submit
✅ Expected: Success + "Guarantor approval request sent" message
✅ Check: Email sent to guarantor (check test_emails directory if using file backend)


Scenario 3: Guarantor Approval
1. Guarantor receives email
2. Clicks approval link
3. Confirms approval
✅ Expected: Loan status → 'approved'
✅ Check: Borrower receives approval notification

Scenario 4: Guarantor Rejection

1. Guarantor receives email
2. Clicks rejection link
3. Confirms rejection
✅ Expected: Loan status → 'pending_guarantor'
✅ Check: Borrower receives rejection email with suggested guarantors

**Expected:** No errors, field displays correctly

---

**Last Updated:** October 13, 2025

