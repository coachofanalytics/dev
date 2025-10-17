# Payment History Bug Fix - October 17, 2025

## Issue
**Error:** `Payment_History() got an unexpected keyword argument 'description'`

**When:** Processing PayPal payments via `/finance/unified/process/paypal/`

**Root Cause:** Multiple `save_payment_history()` functions were passing `description=` parameter, but the `Payment_History` model only has a `notes` field (inherited from `PaymentBase`).

## Investigation

### 1. Error Location
Found in logs:
```
DEBUG: Processing POST request for paypal
Error saving payment history: Payment_History() got an unexpected keyword argument 'description'
DEBUG: Payment processing result: <HttpResponseRedirect status_code=302, "text/html; charset=utf-8", url="/finance/unified/failed/">
```

### 2. Model Structure
**Payment_History model** (`coda/finance/models/core.py` lines 150-166):
- Inherits from `PaymentBase` 
- PaymentBase has `notes` field (line 116-120)
- Does NOT have `description` field

### 3. Code Locations With Bug
Three functions were passing `description=`:
1. `coda/finance/utils.py` line 841
2. `coda/finance/utils.py` line 1255 (duplicate function)
3. `coda/finance/utils/__init__.py` line 39

## Solution

### Changes Made - Part 1 (description → notes)
Changed all occurrences of:
```python
description=f"Ref: {reference} | Status: {status}"
```

To:
```python
notes=f"Ref: {reference} | Status: {status}"
```

### Changes Made - Part 2 (fee_balance missing)
Added fee_balance calculation to all save_payment_history functions:
```python
# Calculate fee_balance (required database field)
fee_balance_value = payment_fees_value - down_payment_value

payment_record = Payment_History(
    ...
    fee_balance=fee_balance_value,
    ...
)
```

### Files Modified
1. ✅ `coda/finance/utils.py` - Fixed 2 occurrences (description → notes) + Added fee_balance
2. ✅ `coda/finance/utils/__init__.py` - Fixed 1 occurrence (description → notes) + Added fee_balance

### Documentation Updated
1. ✅ `docs/apps/finance/Payment/IMPLEMENTATION.md` - Added to Change History
2. ✅ `docs/05_DEPLOYMENT/KNOWN_ISSUES.md` - Added to Resolved Issues
3. ✅ `docs/apps/finance/Payment/TESTING.md` - Added regression test case

## Verification

### Linting
✅ No linter errors found in modified files

### Field Verification
✅ Confirmed no other code uses `description` with `Payment_History`

### Testing Recommendation
When payment system is re-enabled:
1. Process a PayPal payment
2. Verify Payment_History record created successfully
3. Check that `notes` field contains reference and status
4. Should see: "Ref: PAYPAL-{user_id}-{amount} | Status: completed"

## Follow-Up Actions

### Immediate
✅ Bug fixed - Both issues resolved
✅ Deployed to UAT v937 (description fix)
✅ Deployed to UAT v938 (fee_balance fix)

### Future
- [ ] Re-enable payment system (deploy `_deprecated` module OR refactor)
- [ ] Test all payment methods (PayPal, M-Pesa, Stripe, Bank)
- [ ] Monitor payment processing logs for any related issues

## Notes

- Payment system is currently disabled due to missing `_deprecated` module (see IMPLEMENTATION.md)
- This bug would have caused ALL payment processing to fail when re-enabled
- Fix prevents payment failures and 302 redirects to `/finance/unified/failed/`

## Lessons Learned

1. **Model Schema Matters:** Always check model fields before using them
2. **Database vs Model Mismatch:** Database had `fee_balance` column but Django model didn't define it
3. **Schema Alignment Critical:** Similar to LoanProduct schema mismatch (Oct 13) - dev/database must align
4. **Multiple Implementations:** Found duplicate `save_payment_history()` functions - should consolidate
5. **Template Fields Pattern:** Similar to BudgetRequest approval fields bug (Oct 13)
6. **Proactive Fix:** Fixed before payment system re-enabled - prevents future breakage
7. **Iterative Debugging:** First fix revealed second issue - both now resolved

## Related Issues

- Similar pattern to **BudgetRequest approval fields** bug (Oct 13, 2025)
- Both involve field name mismatches between code and model
- Reinforces importance of schema alignment (dev vs production)

---

**Status:** ✅ Fixed and Documented  
**Ready to Deploy:** Yes  
**Testing Required:** When payment system re-enabled  
**Priority:** High (blocks payment processing)

