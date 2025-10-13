# Loan System - Testing

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

**Expected:** No errors, field displays correctly

---

**Last Updated:** October 13, 2025

