# Payment Gateway API Keys Configuration Guide
**Date:** October 20, 2025  
**Critical:** Must configure before testing Stripe and PayPal payments

---

## 🎯 OVERVIEW

This guide shows you how to configure Stripe and PayPal API keys for payment processing.

**What You Need:**
- Stripe account with API keys
- PayPal account with Client ID and Secret
- Access to Heroku config vars (for UAT/Production)

---

## 🔧 CONFIGURATION METHODS

### **Method 1: Heroku Environment Variables (UAT/Production)**

This is the **recommended** approach for deployed environments.

#### **For UAT (codamakutano.herokuapp.com):**

```bash
# Stripe Configuration
heroku config:set STRIPE_PUBLISHABLE_KEY="pk_test_XXXX..." --app codamakutano
heroku config:set STRIPE_SECRET_KEY="sk_test_XXXX..." --app codamakutano
heroku config:set STRIPE_WEBHOOK_SECRET="whsec_XXXX..." --app codamakutano

# PayPal Configuration
heroku config:set PAYPAL_CLIENT_ID="AXXX..." --app codamakutano
heroku config:set PAYPAL_CLIENT_SECRET="EXXX..." --app codamakutano
heroku config:set PAYPAL_MODE="sandbox" --app codamakutano
heroku config:set PAYPAL_EMAIL="payments@codanalytics.net" --app codamakutano

# Verify configuration
heroku config --app codamakutano | grep -E "STRIPE|PAYPAL"
```

#### **For Production (codatrainingapp.herokuapp.com):**

```bash
# Stripe Configuration (use LIVE keys for production)
heroku config:set STRIPE_PUBLISHABLE_KEY="pk_live_XXXX..." --app codatrainingapp
heroku config:set STRIPE_SECRET_KEY="sk_live_XXXX..." --app codatrainingapp
heroku config:set STRIPE_WEBHOOK_SECRET="whsec_XXXX..." --app codatrainingapp

# PayPal Configuration (use LIVE mode for production)
heroku config:set PAYPAL_CLIENT_ID="AXXX..." --app codatrainingapp
heroku config:set PAYPAL_CLIENT_SECRET="EXXX..." --app codatrainingapp
heroku config:set PAYPAL_MODE="live" --app codatrainingapp
heroku config:set PAYPAL_EMAIL="payments@codanalytics.net" --app codatrainingapp

# Verify configuration
heroku config --app codatrainingapp | grep -E "STRIPE|PAYPAL"
```

---

### **Method 2: Local Development (.env file)**

For local testing, create a `.env` file in your project root:

```bash
# .env file (in project root: /Users/coda/PROJECTS/CODA/DEVELOPMENT/DEV/)

# Stripe Configuration (TEST keys for development)
STRIPE_PUBLISHABLE_KEY=pk_test_XXXXXXXXXXXXXXXXXXXX
STRIPE_SECRET_KEY=sk_test_XXXXXXXXXXXXXXXXXXXX
STRIPE_WEBHOOK_SECRET=whsec_XXXXXXXXXXXXXXXXXXXX

# PayPal Configuration (SANDBOX for development)
PAYPAL_CLIENT_ID=AXXXXXXXXXXXXXXXXXXX
PAYPAL_CLIENT_SECRET=EXXXXXXXXXXXXXXXXXX
PAYPAL_MODE=sandbox
PAYPAL_EMAIL=payments@codanalytics.net
```

**Load .env in local_settings.py:**
```python
# coda/coda_project/coda_settings/local_settings.py
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Payment Gateway Settings
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')

PAYPAL_CLIENT_ID = os.environ.get('PAYPAL_CLIENT_ID', '')
PAYPAL_CLIENT_SECRET = os.environ.get('PAYPAL_CLIENT_SECRET', '')
PAYPAL_MODE = os.environ.get('PAYPAL_MODE', 'sandbox')
```

---

## 🔑 HOW TO GET YOUR API KEYS

### **Stripe Keys**

1. **Sign in to Stripe Dashboard:**
   - Go to: https://dashboard.stripe.com/

2. **Get Test Keys (for UAT/Development):**
   - Click **"Developers"** in top navigation
   - Click **"API keys"**
   - Find **"Test mode"** section
   - Copy:
     - **Publishable key** → `pk_test_XXXX...`
     - **Secret key** → `sk_test_XXXX...` (click "Reveal" first)

3. **Get Live Keys (for Production):**
   - Toggle **"View test data"** to OFF (top right)
   - Find **"Standard keys"** section
   - Copy:
     - **Publishable key** → `pk_live_XXXX...`
     - **Secret key** → `sk_live_XXXX...`

4. **Get Webhook Secret:**
   - Click **"Developers"** → **"Webhooks"**
   - Click **"+ Add endpoint"**
   - Enter webhook URL:
     - UAT: `https://codamakutano.herokuapp.com/finance/stripe/webhook/`
     - Prod: `https://codatrainingapp.herokuapp.com/finance/stripe/webhook/`
   - Select events:
     - `payment_intent.succeeded`
     - `payment_intent.payment_failed`
   - Click **"Add endpoint"**
   - Copy **"Signing secret"** → `whsec_XXXX...`

---

### **PayPal Keys**

1. **Sign in to PayPal Developer:**
   - Go to: https://developer.paypal.com/

2. **Create/Access Your App:**
   - Click **"Dashboard"**
   - Click **"My Apps & Credentials"**
   - If no app exists, click **"Create App"**
   - Give it a name (e.g., "CODA Payment System")

3. **Get Sandbox Keys (for UAT/Development):**
   - Make sure **"Sandbox"** tab is selected
   - Find your app and expand it
   - Copy:
     - **Client ID** → `AXXXXXXXXXXX...`
     - **Secret** → Click "Show" → `EXXXXXXXXX...`

4. **Get Live Keys (for Production):**
   - Click **"Live"** tab
   - Find your app and expand it
   - Copy:
     - **Client ID** → `AXXXXXXXXXXX...`
     - **Secret** → Click "Show" → `EXXXXXXXXX...`

5. **Note on PayPal Webhook URL (if needed):**
   - PayPal uses instant payment notification (IPN)
   - Current implementation uses client-side SDK (no webhook needed)
   - If you want webhooks: `https://codamakutano.herokuapp.com/finance/paypal/webhook/`

---

## 📋 COMPLETE CHECKLIST

### **Before Testing in UAT:**

- [ ] Get Stripe **TEST** keys from dashboard
- [ ] Get PayPal **SANDBOX** keys from developer portal
- [ ] Set all Heroku config vars for `codamakutano` app
- [ ] Verify config with: `heroku config --app codamakutano | grep -E "STRIPE|PAYPAL"`
- [ ] Deploy latest code to UAT
- [ ] Test Stripe payment with test card: `4242 4242 4242 4242`
- [ ] Test PayPal payment with sandbox account
- [ ] Check payment appears in Payment History
- [ ] Verify email notifications sent

### **Before Deploying to Production:**

- [ ] All UAT tests passed ✅
- [ ] Get Stripe **LIVE** keys from dashboard
- [ ] Get PayPal **LIVE** keys from developer portal
- [ ] Set production config vars for `codatrainingapp` app
- [ ] Update webhook URLs to production domain
- [ ] Verify PAYPAL_MODE is set to "live"
- [ ] Test with small real payment ($0.50)
- [ ] Monitor Heroku logs for first few payments
- [ ] Have rollback plan ready

---

## 🧪 TESTING GUIDE

### **Test Stripe (UAT with Test Keys)**

**Test Card Numbers:**
```
Success: 4242 4242 4242 4242
Decline: 4000 0000 0000 0002
Insufficient funds: 4000 0000 0000 9995
Expired: 4000 0000 0000 0069
```

**Test Details:**
- Any future expiration date (e.g., 12/25)
- Any 3-digit CVC (e.g., 123)
- Any postal code (e.g., 12345)

**Expected Flow:**
1. Select "Credit/Debit Card" payment method
2. Card form loads (not greyed out)
3. Enter test card details
4. Click "Pay $XX.XX"
5. Payment processes instantly
6. Redirects to success page
7. Payment appears in history

**If Form is Greyed Out:**
- Check browser console (F12) for errors
- Verify `STRIPE_PUBLISHABLE_KEY` is set in Heroku
- Check it starts with `pk_test_` for UAT
- Redeploy if needed: `git push heroku [branch]:main`

---

### **Test PayPal (UAT with Sandbox Keys)**

**Sandbox Test Account:**
- Create at: https://developer.paypal.com/dashboard/accounts
- Use sandbox email/password to login during payment

**Expected Flow:**
1. Select "PayPal" payment method
2. PayPal button appears (blue button)
3. Click PayPal button
4. Login to sandbox account
5. Confirm payment
6. Redirects to success page
7. Payment appears in history

**If Button Doesn't Appear:**
- Check browser console for errors
- Verify `PAYPAL_CLIENT_ID` is set in Heroku
- Check PayPal SDK loaded: Look for `https://www.paypal.com/sdk/js` in network tab
- Try "Show Payment Details" fallback link

---

## 🚨 TROUBLESHOOTING

### **Stripe Form Greyed Out / Disabled**

**Symptoms:**
- Card input fields appear but are disabled/greyed out
- Cannot type in fields
- Submit button disabled

**Causes & Solutions:**

1. **Missing Publishable Key:**
   ```bash
   # Check if key is set
   heroku config:get STRIPE_PUBLISHABLE_KEY --app codamakutano
   
   # If empty, set it
   heroku config:set STRIPE_PUBLISHABLE_KEY="pk_test_XXXX..." --app codamakutano
   ```

2. **Wrong Key Format:**
   - Test keys must start with `pk_test_`
   - Live keys must start with `pk_live_`
   - Check for extra spaces or quotes

3. **Stripe.js Not Loading:**
   - Check browser console for CDN errors
   - Verify: `https://js.stripe.com/v3/` loads
   - Check network connectivity

4. **JavaScript Error:**
   ```javascript
   // Check console (F12) for errors like:
   // "Stripe is not defined"
   // "Cannot read property 'elements' of undefined"
   ```

**Debug Steps:**
```javascript
// In browser console:
console.log('Stripe publishable key:', '{{ stripe_publishable_key }}');
console.log('Stripe object:', typeof Stripe);
console.log('Elements:', typeof Stripe.elements);
```

---

### **PayPal Button Not Appearing**

**Symptoms:**
- PayPal button container is empty
- Only shows fallback "Show Payment Details" link

**Causes & Solutions:**

1. **Missing Client ID:**
   ```bash
   # Check if key is set
   heroku config:get PAYPAL_CLIENT_ID --app codamakutano
   
   # If empty, set it
   heroku config:set PAYPAL_CLIENT_ID="AXXX..." --app codamakutano
   ```

2. **Wrong Mode:**
   ```bash
   # For UAT, mode should be 'sandbox'
   heroku config:set PAYPAL_MODE="sandbox" --app codamakutano
   
   # For Production, mode should be 'live'
   heroku config:set PAYPAL_MODE="live" --app codatrainingapp
   ```

3. **Client ID in Template:**
   - Currently hardcoded in `paypal_form.html` line 97
   - Should be replaced with Django template variable
   - **TODO:** Update template to use `{{ paypal_client_id }}`

---

### **Payment Completes But Not Saved**

**Symptoms:**
- Payment processed successfully
- But doesn't appear in Payment History
- No error shown to user

**Causes & Solutions:**

1. **Check Heroku Logs:**
   ```bash
   # See recent payment processing logs
   heroku logs --tail --app codamakutano | grep -i payment
   ```

2. **Database Connection Issues:**
   - Check database connection in logs
   - Verify Payment_Information exists for user

3. **Webhook Not Configured (Stripe):**
   - Stripe relies on webhooks for confirmation
   - Ensure webhook URL is set in Stripe dashboard
   - Endpoint: `https://codamakutano.herokuapp.com/finance/stripe/webhook/`

---

## 📊 VERIFICATION COMMANDS

### **Check Configuration:**
```bash
# UAT - Check all payment-related config
heroku config --app codamakutano | grep -E "STRIPE|PAYPAL|MPESA|CASHAPP|VENMO"

# Production - Check all payment-related config
heroku config --app codatrainingapp | grep -E "STRIPE|PAYPAL|MPESA|CASHAPP|VENMO"
```

### **Test Deployment:**
```bash
# After setting config vars, deploy
git push heroku [your-branch]:main --app codamakutano

# Monitor deployment
heroku logs --tail --app codamakutano

# Test immediately after deploy
curl -I https://codamakutano.herokuapp.com/finance/unified/methods/
```

### **Check Payment Processing:**
```bash
# Watch logs during payment test
heroku logs --tail --app codamakutano | grep -E "payment|stripe|paypal"

# Check for errors
heroku logs --app codamakutano --num 200 | grep -i error
```

---

## 🔄 DEPLOYMENT WORKFLOW

### **After Adding/Updating Keys:**

1. **Set Environment Variables:**
   ```bash
   heroku config:set STRIPE_PUBLISHABLE_KEY="pk_test_XXX" --app codamakutano
   heroku config:set STRIPE_SECRET_KEY="sk_test_XXX" --app codamakutano
   heroku config:set PAYPAL_CLIENT_ID="AXXX" --app codamakutano
   heroku config:set PAYPAL_CLIENT_SECRET="EXXX" --app codamakutano
   ```

2. **Verify Configuration:**
   ```bash
   heroku config --app codamakutano | grep -E "STRIPE|PAYPAL"
   ```

3. **Restart Dynos (to load new config):**
   ```bash
   heroku restart --app codamakutano
   ```

4. **Test Immediately:**
   - Go to: https://codamakutano.herokuapp.com/finance/unified/methods/
   - Click "Credit/Debit Card" - should show form (not greyed out)
   - Click "PayPal" - should show PayPal button

5. **If Issues Persist:**
   ```bash
   # Check if config loaded
   heroku run "printenv | grep STRIPE" --app codamakutano
   
   # Force redeploy
   git commit --allow-empty -m "Trigger redeploy for payment config"
   git push heroku [branch]:main
   ```

---

## 📝 SUMMARY - QUICK START

### **Fastest Way to Test (UAT):**

```bash
# 1. Get your keys from Stripe and PayPal dashboards (see sections above)

# 2. Set all keys at once
heroku config:set \
  STRIPE_PUBLISHABLE_KEY="pk_test_XXXX..." \
  STRIPE_SECRET_KEY="sk_test_XXXX..." \
  STRIPE_WEBHOOK_SECRET="whsec_XXXX..." \
  PAYPAL_CLIENT_ID="AXXX..." \
  PAYPAL_CLIENT_SECRET="EXXX..." \
  PAYPAL_MODE="sandbox" \
  --app codamakutano

# 3. Restart
heroku restart --app codamakutano

# 4. Test
# Visit: https://codamakutano.herokuapp.com/finance/unified/methods/
# Try Stripe with card: 4242 4242 4242 4242
# Try PayPal with sandbox account

# 5. Verify
heroku logs --tail --app codamakutano
```

---

## 🎯 WHAT'S BEEN CHANGED

### **Code Changes Made:**

1. ✅ **Reordered Payment Methods** (`unified_payment.py`)
   - Stripe is now first
   - PayPal is second
   - Added `has_api` flag to each method

2. ✅ **Updated Template** (`method_selection.html`)
   - Stripe/PayPal show "Continue" button (goes to form)
   - Others show "Get Details" button (goes to payment_details)

3. ✅ **Added Settings** (heroku_settings.py, prod_settings.py)
   - All Stripe config variables
   - All PayPal config variables
   - Manual payment details variables

### **What Still Needs Attention:**

⚠️ **PayPal Client ID in Template:**
- File: `coda/finance/templates/finance/payments/paypal_form.html`
- Line 97 has hardcoded Client ID
- Should be updated to: `client-id={{ paypal_client_id }}`

⚠️ **Pass Client ID to Template:**
- Update `show_payment_form()` in `unified_payment.py`
- Add PayPal client ID to context

---

## ✅ FINAL CHECKLIST

**Before You Say "It Works":**

- [ ] Stripe form loads and is **NOT** greyed out
- [ ] Can type in Stripe card fields
- [ ] Test payment with `4242 4242 4242 4242` succeeds
- [ ] Stripe payment appears in Payment History
- [ ] PayPal button appears (blue button)
- [ ] PayPal payment redirects to sandbox login
- [ ] PayPal payment completes successfully
- [ ] PayPal payment appears in Payment History
- [ ] Email notifications sent for both
- [ ] Success page shows correct reference number
- [ ] Can download receipt
- [ ] Other methods (M-Pesa, CashApp, etc.) go to payment details
- [ ] Payment details show correct information

---

**Configuration Complete!** 🎉

You now have:
- ✅ Stripe and PayPal prioritized
- ✅ Settings configured in all environments
- ✅ Non-API methods routing to payment details
- ✅ Clear guide for adding API keys

**Next Step:** Add your API keys using the commands above and test!

---

**Created:** October 20, 2025  
**For:** CODA Payment System  
**Environment:** UAT (codamakutano.herokuapp.com)


