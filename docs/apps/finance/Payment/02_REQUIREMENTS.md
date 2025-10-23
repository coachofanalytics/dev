# Payment System - Requirements

**Last Updated:** October 22, 2025  
**Status:** ⚠️ Implemented but Disabled

---

## 📋 PHASE 1: Unified Payment System (IMPLEMENTED ✅)

### REQ-001: Payment Method Selection
**Status:** ✅ Implemented (temporarily disabled)

**Requirements:**
- ✅ Unified method selection interface
- ✅ Support 6 payment methods:
  1. M-Pesa (Kenya)
  2. Stripe (Cards)
  3. PayPal
  4. CashApp
  5. Zelle
  6. Venmo
- ✅ Clear method descriptions
- ✅ Consistent UI

---

### REQ-002: M-Pesa Integration
**Status:** ✅ Implemented (STK Push ready)

**Requirements:**
- ✅ Phone number validation (254 format)
- ✅ STK Push initiation
- ✅ OTP verification
- ✅ Payment confirmation
- ✅ Receipt generation

---

### REQ-003: Stripe Integration
**Status:** ✅ Implemented (service layer ready)

**Requirements:**
- ✅ Card payment form
- ✅ PCI-compliant (Stripe.js)
- ✅ Payment processing
- ✅ Confirmation handling

---

## 📋 PHASE 2: Re-Enablement (CURRENT 🔄)

### REQ-010: Deploy or Refactor
**Priority:** HIGH  
**Status:** Blocked

**Options:**
1. Deploy `_deprecated` module to production
2. Refactor views to new structure

**Requirements:**
- [ ] Choose deployment strategy
- [ ] Test thoroughly in UAT
- [ ] Update URLs in `finance/urls.py`
- [ ] Update dashboard links

---

## 📜 BUSINESS RULES

### BR-001: Payment Methods

**M-Pesa:**
- For Kenya users only
- Amount limits: KES 100 - 150,000
- 2.5% transaction fee

**Stripe:**
- International cards accepted
- 2.9% + $0.30 per transaction
- PCI compliance required

---

**See:** IMPLEMENTATION.md for technical details


