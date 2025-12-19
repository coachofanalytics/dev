# Payment System - Maintenance

**Last Updated:** October 22, 2025  
**System Health:** ⚠️ Disabled

---

## 🔴 CRITICAL ISSUES (1)

### ISSUE-001: Payment System Disabled
**Severity:** CRITICAL  
**Impact:** No payment processing available  
**Affected:** All payment-dependent features

**Description:**
- Payment views reference `finance/_deprecated/legacy_views/payment_views.py`
- Module not deployed to UAT/Production
- URLs commented out to prevent 500 errors

**Root Cause:**
- `_deprecated` directory not in deployment
- Import fails: `ModuleNotFoundError: No module named 'finance._deprecated'`

**Solutions:**

**Option A: Deploy Missing Module** (Quick - 1 hour)
```bash
# Add _deprecated to deployment
git add coda/finance/_deprecated/
git commit -m "Payment: Deploy missing _deprecated module"
git push heroku [branch]:main
```

**Option B: Refactor Structure** (Better - 1 week)
```bash
# Move payment_views.py to proper location
mv coda/finance/_deprecated/legacy_views/payment_views.py \
   coda/finance/views/payment_views.py

# Update imports in urls.py
# Update all references
```

**Workaround:**
- External payment collection (manual)
- Cash payments recorded manually in system

**Priority:** HIGH  
**ETA:** User decision needed (Option A or B)  
**Tracking:** PAYMENT-001  
**Owner:** Development Team

---

## 🟡 MEDIUM PRIORITY (2)

#### ISSUE-002: M-Pesa API Credentials
**Severity:** MEDIUM  
**Impact:** M-Pesa won't work without credentials configured  
**Workaround:** Use test mode or manual confirmation  
**ETA:** When re-enabling  
**Tracking:** PAYMENT-002

#### ISSUE-003: No Payment Reconciliation
**Severity:** MEDIUM  
**Impact:** Manual reconciliation required  
**Workaround:** Export Payment_History to CSV  
**ETA:** Phase 2  
**Tracking:** PAYMENT-003

---

## ✅ IMPLEMENTATION STATUS

**Complete:**
- ✅ 586 lines of payment view code (6 methods)
- ✅ M-Pesa service (293 lines, STK Push ready)
- ✅ Unified payment flow
- ✅ Payment_History model
- ✅ All templates created

**Blocked:**
- ❌ Deployment (missing module)
- ❌ URL integration
- ❌ Testing (can't test disabled system)

---

## ✅ RESOLVED ISSUES

### October 17, 2025 - Payment History Bug Fixes
**Status:** ✅ Fixed (4 bugs)

**Bug #1: Invalid field name 'description'**
- **Error:** `Payment_History() got an unexpected keyword argument 'description'`
- **Root Cause:** Code passing `description=` but model has `notes` field
- **Fix:** Changed all `description=` to `notes=` in utils.py (3 locations)

**Bug #2: Missing required field 'fee_balance'**
- **Error:** `null value in column "fee_balance" violates not-null constraint`
- **Root Cause:** Database has NOT NULL column but code wasn't passing value
- **Fix:** Added fee_balance calculation to all save_payment_history functions

**Bug #3: Model missing 'fee_balance' definition**
- **Error:** `Payment_History() got an unexpected keyword argument 'fee_balance'`
- **Root Cause:** Database has column but Django model didn't define field
- **Fix:** Added `fee_balance = DecimalField()` to Payment_History model

**Bug #4: Payment_Information schema mismatch**
- **Error:** `column finance_payment_information.fee_balance does not exist`
- **Root Cause:** Payment_Information table doesn't have fee_balance, only Payment_History does
- **Fix:** Only pass fee_balance to Payment_History, not Payment_Information

**Files Changed:**
- `coda/finance/utils.py` (lines 841, 1255)
- `coda/finance/utils/__init__.py` (line 39)
- `coda/finance/models/core.py` (Payment_History model)

**Impact:** Payment processing now works without database constraint errors

### October 20, 2025 - Payment Method Reordering
**Status:** ✅ Implemented

**Changes:**
1. Reordered payment methods: Stripe first, PayPal second
2. Direct non-API methods (M-Pesa, CashApp, Zelle, Venmo) to payment details page
3. Fixed Stripe form greyed-out issue with proper API key configuration

**Files Changed:**
- `coda/finance/views/payment/unified_payment.py` - PAYMENT_METHODS dict reordered
- `coda/finance/templates/finance/payments/method_selection.html` - has_api check logic

**Impact:** Better UX - users see Stripe/PayPal first, non-API methods skip to details

---

## 📋 TODO LIST

### Re-Enablement (HIGH PRIORITY)
- [ ] **Decide:** Deploy _deprecated OR refactor
- [ ] Implement chosen solution
- [ ] Test in UAT thoroughly
- [ ] Uncomment URLs in finance/urls.py
- [ ] Configure M-Pesa API credentials
- [ ] Configure Stripe API keys
- [ ] Update dashboard quick links
- [ ] Deploy to production

### Phase 2 (After Re-Enablement)
- [ ] Payment reconciliation tools
- [ ] Automated confirmation emails
- [ ] Payment analytics dashboard
- [ ] Refund processing

---

## 🔍 TROUBLESHOOTING

### Problem: ModuleNotFoundError: finance._deprecated
**Symptoms:** ImportError on payment URL access  
**Cause:** `_deprecated` directory not deployed  
**Solution:** Deploy directory or refactor

### Problem: M-Pesa STK Push Not Working
**Symptoms:** No push notification received  
**Cause:** API credentials not configured  
**Solution:** Set M-Pesa environment variables

---

## 📞 RE-ENABLEMENT DECISION NEEDED

**User must choose:**
- **Option A:** Deploy `_deprecated` (quick, temporary)
- **Option B:** Refactor structure (better, longer)

**Recommendation:** Option B (cleaner long-term)

---

**Document Owner:** Development Team  
**Blocked By:** Deployment decision  
**Next Step:** User approval for chosen approach


