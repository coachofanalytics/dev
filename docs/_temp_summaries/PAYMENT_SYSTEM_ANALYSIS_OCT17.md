# Payment System Analysis & Implementation Plan
**Date:** October 17, 2025  
**Purpose:** Analyze legacy PayPal system and plan integration with unified payment flow

---

## 🔍 Legacy System Analysis

### **1. How Legacy PayPal Works**

**Location:** `coda/finance/templates/finance/payments/pay.html`

**PayPal SDK Configuration:**
```javascript
// PayPal Client ID (currently in use)
<script src="https://www.paypal.com/sdk/js?client-id=AYsNJlHsAzemW-IvLkkf42iMHGdTMxFfupX6CTI2-rhDDfU67zTQ2n_lszMkxcrrYq_5Qltrw99Lep4D"></script>
```

**Payment Flow:**
1. **Page Load** (`/finance/payment/`)
   - View: `coda/finance/views.py` → `pay()` function (line 2104)
   - Fetches payment_info (from Payment_Information, loans, or history)
   - Calculates PayPal charges using `calculate_paypal_charges()`
   - Renders template with PayPal button

2. **User Clicks PayPal Button**
   - PayPal SDK handles entire transaction
   - Creates order with amount
   - User logs in to PayPal
   - Approves payment

3. **Payment Approved**
   - SDK calls `onApprove` callback
   - Captures payment
   - Calls `completeOrder()` JavaScript function
   - Posts to `/finance/payment_complete/`

4. **Backend Processing**
   - View: `paymentComplete()` (line 2251)
   - Creates Payment_History record
   - Updates PayslipConfig if exists
   - Returns success JSON

**Key Features:**
- ✅ Client-side PayPal button integration
- ✅ Automatic payment capture
- ✅ Transaction ID tracking
- ✅ Email notifications

---

### **2. How Legacy Payment Details Work**

**Location:** `coda/finance/views.py` → `payment()` function (line 1843)

**Payment Methods Supported:**
- M-Pesa (phone number)
- CashApp (username)
- Zelle (account details)
- Venmo (username)

**Flow:**
1. User clicks method button (CashApp, Zelle, Venmo, M-Pesa)
2. URL: `/finance/payment_method/<method>/`
3. Backend sends email with payment details
4. User completes payment manually
5. Admin verifies and updates system

**Payment Details (from environment variables):**
```python
# Location: coda/coda_project/coda_settings/base_settings.py (line 235)
phone_number = os.environ.get('MPESA_PHONE_NUMBER')  # M-Pesa
email_info = os.environ.get('EMAIL_INFO_USER')  # Contact email
cashapp = os.environ.get('CASHAPP')  # CashApp username
venmo = os.environ.get('VENMO')  # Venmo username
account_no = os.environ.get('STANBIC_ACCOUNT_NO')  # Bank account (Zelle)
```

**Email Template:** `email/payment/payment_method.html`

---

## 🎯 Implementation Requirements

### **Priority 1: PayPal Integration**

**Goal:** Copy working PayPal implementation to unified system

**What to Copy:**
1. ✅ PayPal SDK script tag with Client ID
2. ✅ PayPal Buttons JavaScript code
3. ✅ `completeOrder()` function
4. ✅ Payment completion endpoint
5. ✅ PayPal charges calculation

**Configuration Needed:**
- PayPal Client ID: `AYsNJlHsAzemW-IvLkkf42iMHGdTMxFfupX6CTI2-rhDDfU67zTQ2n_lszMkxcrrYq_5Qltrw99Lep4D`
- Is this Sandbox or Live? (Need to confirm)
- Webhook configuration (if any)

**Files to Modify:**
1. `coda/finance/templates/finance/payments/paypal_form.html` - Add PayPal button
2. `coda/finance/views/payment/unified_payment.py` - Update `process_paypal_payment()`
3. `coda/finance/urls.py` - Add payment completion endpoint

---

### **Priority 2: Payment Details Page**

**Goal:** Create unified payment details page for manual methods

**Methods to Redirect:**
- M-Pesa (no keys yet)
- CashApp
- Zelle  
- Venmo

**Features:**
1. **Display Payment Information:**
   - Method-specific details (phone number, username, account)
   - Amount to pay
   - Payment reference number
   - Instructions

2. **Email Notification:**
   - Send email with payment details
   - Include payment reference
   - Provide confirmation instructions

3. **Proof Upload (Optional):**
   - Allow file upload for payment proof
   - Store with reference number
   - Admin review and approval

**Files to Create:**
1. `coda/finance/views/payment/payment_details.py` - New view
2. `coda/finance/templates/finance/payments/payment_details.html` - Template
3. Update `unified_payment.py` to route methods

---

### **Priority 3: Stripe Integration**

**Goal:** Implement Stripe payment with your sandbox

**Configuration Needed from You:**
1. Stripe Publishable Key: `pk_test_...`
2. Stripe Secret Key: `sk_test_...`
3. Webhook Secret: `whsec_...`

**Preferred Integration:**
- Option A: **Stripe Elements** (embedded card form)
- Option B: **Stripe Checkout** (redirect to Stripe page)

**Features:**
1. Credit/Debit card processing
2. 3D Secure authentication
3. Webhook for payment confirmation
4. Payment intent creation
5. Error handling

**Files to Create:**
1. `coda/finance/views/payment/stripe_integration.py` - Stripe logic
2. Update `stripe_form.html` with Stripe Elements
3. Add Stripe webhook endpoint

---

## 📋 Environment Variables Needed

### **Current (from base_settings.py):**
```bash
MPESA_PHONE_NUMBER="..."  # For payment details display
EMAIL_INFO_USER="info@codanalytics.net"  # Support email
CASHAPP="$..."  # CashApp username
VENMO="@..."  # Venmo username
STANBIC_ACCOUNT_NO="..."  # Bank account for Zelle
```

### **New Variables Needed:**

**For PayPal:**
```bash
PAYPAL_CLIENT_ID="AYsNJlHsAzemW-IvLkkf42iMHGdTMxFfupX6CTI2-rhDDfU67zTQ2n_lszMkxcrrYq_5Qltrw99Lep4D"
PAYPAL_MODE="sandbox"  # or "live"
```

**For Stripe:**
```bash
STRIPE_PUBLISHABLE_KEY="pk_test_..."  # Need from you
STRIPE_SECRET_KEY="sk_test_..."  # Need from you  
STRIPE_WEBHOOK_SECRET="whsec_..."  # Need from you
```

**For M-Pesa (when ready):**
```bash
MPESA_CONSUMER_KEY="..."
MPESA_CONSUMER_SECRET="..."
MPESA_SHORTCODE="..."
MPESA_PASSKEY="..."
MPESA_CALLBACK_URL="https://codamakutano.herokuapp.com/finance/mpesa/callback/"
```

---

## 🔧 Implementation Phases

### **Phase 1: PayPal (Week 1)**
1. Copy legacy PayPal code to unified system
2. Test in UAT with existing Client ID
3. Verify payment completion flow
4. Add payment history recording

### **Phase 2: Payment Details (Week 1)**
1. Create payment details page
2. Add email notification
3. Route M-Pesa, CashApp, Zelle, Venmo to details page
4. Test email delivery

### **Phase 3: Stripe (Week 2)**
1. Get Stripe sandbox credentials from you
2. Implement Stripe Elements or Checkout
3. Add webhook handler
4. Test card payments in sandbox

---

## ❓ Questions for You

### **1. PayPal Configuration**
- [ ] Is the current PayPal Client ID for Sandbox or Live?
- [ ] Do you have PayPal webhook configured?
- [ ] What's your PayPal business account email?

### **2. Payment Details**
- [ ] What are the actual payment details to display?
  - M-Pesa phone number: ?
  - CashApp username: ?
  - Zelle account details: ?
  - Venmo username: ?
- [ ] Should users upload proof of payment?
- [ ] Who verifies manual payments?

### **3. Stripe Setup**
- [ ] Do you have Stripe test account?
- [ ] Can you provide test credentials?
  - Publishable Key: `pk_test_...`
  - Secret Key: `sk_test_...`
- [ ] Prefer Stripe Elements or Stripe Checkout?

### **4. M-Pesa Future**
- [ ] When will you get M-Pesa credentials?
- [ ] Sandbox or Live for initial testing?

---

## 🚀 Ready to Start?

**Next Steps:**
1. You confirm the payment details (accounts, usernames, etc.)
2. You provide Stripe sandbox credentials
3. I implement Phase 1 (PayPal) first
4. We test in UAT
5. Then Phase 2 (Payment Details)
6. Finally Phase 3 (Stripe)

**Should I start with Phase 1 (PayPal integration)?**

---

**Status:** ✅ Analysis Complete - Awaiting Your Confirmation  
**Priority:** PayPal → Payment Details → Stripe → M-Pesa (future)

