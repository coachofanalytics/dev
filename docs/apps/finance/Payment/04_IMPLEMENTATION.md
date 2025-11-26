# Payment System - Implementation

**Last Updated:** October 22, 2025  
**Status:** ⚠️ Implemented but Disabled

---

## 📁 FILE STRUCTURE

```
coda/finance/
├── _deprecated/legacy_views/
│   └── payment_views.py             # Payment views (586 lines)
│
├── services/
│   ├── mpesa_service.py             # M-Pesa integration (293 lines)
│   ├── stripe_service.py            # Stripe integration
│   ├── paypal_service.py            # PayPal integration
│   ├── cashapp_service.py           # CashApp integration
│   ├── zelle_service.py             # Zelle integration
│   └── venmo_service.py             # Venmo integration
│
├── models/
│   └── payment.py                   # Payment models
│
├── templates/finance/payments/
│   ├── method_selection.html        # Method selection UI
│   ├── mpesa_otp_confirmation.html  # M-Pesa OTP form
│   ├── unified_success.html         # Success page
│   └── unified_failed.html          # Failure page
│
└── urls.py                          # URLs (commented out lines 126-141)
```

---

## 🚨 CURRENT ISSUE

**Problem:** Payment views reference `finance/_deprecated` module that doesn't exist in deployed environment

**Impact:** Payment URLs disabled to prevent 500 errors

**Solutions:**
1. **Option A:** Deploy `_deprecated` directory
2. **Option B:** Refactor to `finance/payment_views.py`
3. **Option C:** Move to `finance/views/payment/`

---

## 🔌 IMPLEMENTED FEATURES

### Payment Method Selection View
**File:** `finance/_deprecated/legacy_views/payment_views.py` (lines 82-123)

**Features:**
- 6 payment methods configured
- Method-specific forms
- Configuration-driven PAYMENT_METHODS dict
- Session management for multi-step flows

---

### M-Pesa STK Push
**File:** `finance/services/mpesa_service.py` (293 lines)

**Features:**
- Phone number validation
- STK Push API integration
- OTP generation & verification
- Payment confirmation

---

### Payment History Tracking
**Model:** Payment_History

**Tracks:**
- User, amount, method
- Status (pending/completed/failed)
- Reference number
- Transaction timestamp

---

---

## 🔌 MULTI-ORGANIZATION RECEIPT BRANDING (Nov 25, 2025)

### Organization Detection
**File:** `coda/shared_core/utils.py`

**Features:**
- Domain-based organization detection from HTTP request
- Maps domains to Company records via database lookup
- Supports: CODA, DC48K, Biashara Bridges (and extensible to more)
- Logo URL mapping for static logo files
- Functions: `detect_organization_from_request()`, `get_company_receipt_data()`, `get_company_logo_url()`

### Company Model Extension
**File:** `coda/main/models.py`

**Fields Added:**
- `logo` - ImageField (for future use)
- `receipt_email` - EmailField (e.g., info@domain.com)
- `display_name` - CharField (e.g., "CODA ANALYTICS" or "DC48K")
- `address` - CharField (organization address)

### Payment_History Model Update
**File:** `coda/finance/models/core.py`

**Fields Added:**
- `company` - ForeignKey to Company (links payment to organization)

### Stripe Integration Updates
**File:** `coda/finance/views/payment/stripe_views.py`

**Changes:**
- `create_checkout_session()` - Detects organization from request domain, stores in Stripe metadata
- `stripe_checkout_success()` - Retrieves company from metadata, passes to payment history
- `stripe_webhook()` - Handles company in webhook callbacks

### Receipt Service Updates
**File:** `coda/finance/services/payment_receipt_service.py`

**Changes:**
- Uses `Payment_History.company` to get organization data
- Generates dynamic receipt branding (name, email, logo, address)
- Falls back to CODA defaults if company not set

### Receipt Templates
**File:** `coda/finance/templates/finance/receipts/payment_receipt.html`

**Changes:**
- Dynamic company name/display name
- Dynamic company email/website/address
- Conditional logo display

---

## 📊 CHANGE HISTORY

| Date | Change | Files | Dev |
|------|--------|-------|-----|
| Nov 25, 2025 | Multi-organization receipt branding | Company model, Payment_History, Stripe views, receipt service | AI |
| Nov 14, 2025 | Auto-create Payment_Information on loan approval | finance/signals.py | AI |
| Oct 22, 2025 | 7-doc migration | All docs | AI |
| Oct 13, 2025 | Disabled (missing module) | urls.py | CM |
| Sept 2025 | Unified payment flow | payment_views.py | CM |
| Aug 2025 | M-Pesa integration | mpesa_service.py | CM |

---

**See:** 02_REQUIREMENTS.md for features, 07_DEPLOYMENT.md for re-enablement


