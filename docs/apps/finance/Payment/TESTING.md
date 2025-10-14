# Payment System - Testing

## Current Status: CANNOT TEST

**Reason:** Payment system disabled (missing `_deprecated` module)

## When Re-Enabled

### Test 1: Payment Method Selection
1. Navigate to `/finance/unified/methods/`
2. Verify 3 methods shown (M-Pesa, Stripe, Bank)
3. Select M-Pesa
4. Redirects to M-Pesa form

**Expected:** Method selection works, redirects correctly

### Test 2: M-Pesa STK Push (Test Environment)
1. Enter test phone: 254700000000
2. Enter amount: KES 100
3. Submit
4. Check for STK Push prompt (simulator)

**Expected:** Prompt received, payment processes

### Test 3: Stripe Payment (Test Mode)
1. Select Stripe payment
2. Enter test card: 4242 4242 4242 4242
3. Expiry: any future date
4. CVC: any 3 digits
5. Submit

**Expected:** Payment succeeds in test mode

### Test 4: Bank Transfer Instructions
1. Select Bank Transfer
2. View account details
3. Note payment reference

**Expected:** Details displayed correctly

## Test Environment Setup

**Required:**
1. M-Pesa sandbox credentials
2. Stripe test mode keys
3. Test bank account details

## Re-Enabling Checklist

- [ ] Deploy `_deprecated` module OR refactor
- [ ] Uncomment URLs in `finance/urls.py`
- [ ] Verify payment gateway credentials
- [ ] Test in UAT (all 3 methods)
- [ ] Enable "Make a Payment" link in dashboard
- [ ] Update `management/utils.py` quick links
- [ ] Monitor payment callbacks/webhooks

---

**Last Updated:** October 13, 2025  
**Status:** Cannot test - system disabled

