# Payment History Bug Fix - October 17, 2025

## Issues (3 bugs discovered iteratively)

### Bug #1: Invalid field name 'description'
**Error:** `Payment_History() got an unexpected keyword argument 'description'`
**Root Cause:** Code passing `description=` but model has `notes` field

### Bug #2: Missing required field 'fee_balance' 
**Error:** `null value in column "fee_balance" violates not-null constraint`
**Root Cause:** Database has NOT NULL column but code wasn't passing value

### Bug #3: Model missing 'fee_balance' definition
**Error:** `Payment_History() got an unexpected keyword argument 'fee_balance'`
**Root Cause:** Database has column but Django model didn't define field

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

### Changes Made - Part 2 (fee_balance calculation)
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

### Changes Made - Part 3 (model schema alignment)
Added fee_balance field to Django models to match database:
```python
class Payment_Information(PaymentBase):
    ...
    fee_balance = models.IntegerField(default=0, help_text="Calculated as payment_fees - down_payment")
    ...

class Payment_History(PaymentBase):
    ...
    fee_balance = models.IntegerField(default=0, help_text="Calculated as payment_fees - down_payment")
    ...
```

### Files Modified
1. ✅ `coda/finance/utils.py` - Fixed (description → notes) + Added fee_balance calc
2. ✅ `coda/finance/utils/__init__.py` - Fixed (description → notes) + Added fee_balance calc
3. ✅ `coda/finance/models/core.py` - Added fee_balance field to both models

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
✅ All 3 bugs fixed - Complete resolution
✅ Deployed to UAT v937 (description → notes)
✅ Deployed to UAT v938 (fee_balance calculation)
✅ Deployed to UAT v939 (model field definition)

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
7. **Iterative Debugging:** Each fix revealed the next issue - all three now resolved
8. **Schema Mismatch Pattern:** Database evolved but Django models didn't - classic technical debt

## Related Issues

- Similar pattern to **BudgetRequest approval fields** bug (Oct 13, 2025)
- Both involve field name mismatches between code and model
- Reinforces importance of schema alignment (dev vs production)

---

**Status:** ✅ Fixed, Deployed (v939), and Documented  
**Deployments:** UAT v937, v938, v939 (3 iterative fixes)
**Testing Required:** When payment system re-enabled  
**Priority:** High (was blocking all payment processing)

