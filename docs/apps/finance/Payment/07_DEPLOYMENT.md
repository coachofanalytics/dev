# Payment System - Deployment

**Last Updated:** October 22, 2025  
**Status:** ⚠️ Not Deployed (Implementation Ready)

---

## 🚨 CURRENT DEPLOYMENT STATUS

**Status:** BLOCKED  
**Reason:** Missing `_deprecated` module in deployment  
**Impact:** Payment system cannot be accessed

---

## 🎯 RE-ENABLEMENT PROCEDURE

### Option A: Deploy Missing Module (Quick)

**Steps:**
```bash
# 1. Verify _deprecated directory exists locally
ls coda/finance/_deprecated/legacy_views/payment_views.py

# 2. Commit to git
git add coda/finance/_deprecated/
git commit -m "Payment: Add missing _deprecated module"

# 3. Deploy to UAT
git push heroku [branch]:main

# 4. Test payment URLs
curl -I https://codamakutano.herokuapp.com/finance/unified/methods/

# 5. If working, uncomment URLs in finance/urls.py
# Lines 126-141

# 6. Deploy again with URLs enabled
git add coda/finance/urls.py
git commit -m "Payment: Enable payment URLs"
git push heroku [branch]:main
```

**Time:** 1-2 hours  
**Risk:** LOW  
**Maintenance:** Medium (temporary structure)

---

### Option B: Refactor to New Structure (Recommended)

**Steps:**
```bash
# 1. Move payment views to proper location
mkdir -p coda/finance/views/payment/
mv coda/finance/_deprecated/legacy_views/payment_views.py \
   coda/finance/views/payment/views.py

# 2. Update imports in urls.py
# Change: from finance._deprecated.legacy_views.payment_views import *
# To: from finance.views.payment.views import *

# 3. Update all internal imports
# Search and replace references

# 4. Test locally
python manage.py runserver
# Navigate to /finance/unified/methods/

# 5. Deploy to UAT
git add -A
git commit -m "Payment: Refactor to new structure"
git push heroku [branch]:main

# 6. Test thoroughly in UAT
./tests/test_payment_flow.sh

# 7. Deploy to production (with user permission)
```

**Time:** 1 week  
**Risk:** MEDIUM  
**Maintenance:** Low (proper structure)

---

## ⚙️ ENVIRONMENT VARIABLES REQUIRED

### M-Pesa Configuration
```bash
MPESA_CONSUMER_KEY=your_consumer_key
MPESA_CONSUMER_SECRET=your_consumer_secret
MPESA_SHORTCODE=174379
MPESA_PASSKEY=your_passkey
MPESA_CALLBACK_URL=https://codatrainingapp.herokuapp.com/finance/mpesa/callback/
```

### Stripe Configuration

**UAT (Test Keys):**
```bash
heroku config:set STRIPE_PUBLISHABLE_KEY="pk_test_XXXX..." --app codamakutano
heroku config:set STRIPE_SECRET_KEY="sk_test_XXXX..." --app codamakutano
heroku config:set STRIPE_WEBHOOK_SECRET="whsec_XXXX..." --app codamakutano
```

**Production (Live Keys):**
```bash
heroku config:set STRIPE_PUBLISHABLE_KEY="pk_live_XXXX..." --app codatrainingapp
heroku config:set STRIPE_SECRET_KEY="sk_live_XXXX..." --app codatrainingapp
heroku config:set STRIPE_WEBHOOK_SECRET="whsec_XXXX..." --app codatrainingapp
```

**Local Development (.env file):**
```bash
# .env file in project root
STRIPE_PUBLISHABLE_KEY=pk_test_XXXXXXXXXXXXXXXXXXXX
STRIPE_SECRET_KEY=sk_test_XXXXXXXXXXXXXXXXXXXX
STRIPE_WEBHOOK_SECRET=whsec_XXXXXXXXXXXXXXXXXXXX
```

**Getting Stripe Keys:**
1. Go to https://dashboard.stripe.com/
2. Login to your Stripe account
3. Navigate to Developers → API keys
4. Copy Publishable key (starts with `pk_`)
5. Click "Reveal" on Secret key (starts with `sk_`)
6. For webhooks: Developers → Webhooks → Add endpoint → Get signing secret

### PayPal Configuration

**UAT (Sandbox):**
```bash
heroku config:set PAYPAL_CLIENT_ID="AXXX..." --app codamakutano
heroku config:set PAYPAL_CLIENT_SECRET="EXXX..." --app codamakutano
heroku config:set PAYPAL_MODE="sandbox" --app codamakutano
heroku config:set PAYPAL_EMAIL="payments@codanalytics.net" --app codamakutano
```

**Production (Live):**
```bash
heroku config:set PAYPAL_CLIENT_ID="AXXX..." --app codatrainingapp
heroku config:set PAYPAL_CLIENT_SECRET="EXXX..." --app codatrainingapp
heroku config:set PAYPAL_MODE="live" --app codatrainingapp
heroku config:set PAYPAL_EMAIL="payments@codanalytics.net" --app codatrainingapp
```

**Local Development (.env file):**
```bash
# .env file in project root
PAYPAL_CLIENT_ID=AXXXXXXXXXXXXXXXXXXX
PAYPAL_CLIENT_SECRET=EXXXXXXXXXXXXXXXXXX
PAYPAL_MODE=sandbox
PAYPAL_EMAIL=payments@codanalytics.net
```

**Getting PayPal Keys:**
1. Go to https://developer.paypal.com/
2. Login to your PayPal account
3. Go to My Apps & Credentials
4. Create new app or select existing
5. Copy Client ID (starts with 'A')
6. Click "Show" to reveal Secret (starts with 'E')
7. Use "sandbox" mode for testing, "live" for production

**Verify Configuration:**
```bash
# Check UAT
heroku config --app codamakutano | grep -E "STRIPE|PAYPAL"

# Check Production
heroku config --app codatrainingapp | grep -E "STRIPE|PAYPAL"
```

---

## ✅ POST-RE-ENABLEMENT VERIFICATION

```bash
# 1. Test method selection page
curl -I https://codamakutano.herokuapp.com/finance/unified/methods/
# Expected: HTTP/1.1 200 OK

# 2. Test M-Pesa flow (if credentials configured)
# Navigate to page, submit test payment

# 3. Check payment history
heroku run "cd coda && python manage.py shell" --app codamakutano
# >>> from finance.models import Payment_History
# >>> Payment_History.objects.count()

# 4. Monitor logs
heroku logs --tail --app codamakutano | grep payment
```

---

## 📊 DEPLOYMENT HISTORY

| Date | Version | Changes | Status |
|------|---------|---------|--------|
| Oct 13, 2025 | v904 | Disabled (missing module) | ⚠️ Disabled |
| Sept 2025 | v880 | Unified payment flow | ✅ Implemented |
| Aug 2025 | v860 | M-Pesa integration | ✅ Implemented |

---

## 🚀 RECOMMENDED PATH FORWARD

1. **User Decision:** Choose Option A (quick) or B (better)
2. **If Option B:** Schedule 1 week for refactoring
3. **Configure APIs:** Set M-Pesa/Stripe credentials
4. **Test in UAT:** Complete payment test suite
5. **User Approval:** Get permission for production
6. **Deploy:** Enable payment system
7. **Monitor:** Watch for payment errors

---

**Blocked By:** User decision on deployment approach  
**Ready to Deploy:** Yes (code complete)  
**Next Step:** Choose Option A or B


