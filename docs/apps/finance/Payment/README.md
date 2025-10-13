# Payment System

## Overview
Payment processing system supporting multiple payment methods (M-Pesa, Stripe, Bank Transfer).

**Key Features:**
- Payment method selection
- M-Pesa STK Push integration
- Stripe card payments
- Bank transfer instructions
- Payment confirmation tracking

## Current Status

### ⚠️ Currently Disabled
The payment views are temporarily disabled due to missing `_deprecated` module.

**Reason:** `finance/_deprecated/legacy_views/payment_views.py` not deployed to UAT

**Affected URLs:**
- `/finance/unified/methods/` - Payment method selection
- `/finance/unified/mpesa/` - M-Pesa payment
- `/finance/unified/stripe/` - Stripe payment

### 🔄 To Re-Enable
1. Deploy `finance/_deprecated` directory, OR
2. Refactor payment views to new structure
3. Update `finance/urls.py` (uncomment payment URLs)
4. Update dashboard quick links

## Quick Start

**When Re-Enabled:**
1. Navigate to `/finance/unified/methods/`
2. Select payment method
3. Complete payment flow

## Documentation

- [README.md](README.md) - This overview
- [REQUIREMENTS.md](REQUIREMENTS.md) - Business requirements
- [IMPLEMENTATION.md](IMPLEMENTATION.md) - Technical details
- [TESTING.md](TESTING.md) - Test scenarios

## Key Code Locations

- **Views (Legacy):** `coda/finance/_deprecated/legacy_views/payment_views.py`
- **Models:** `coda/finance/models/payment.py`
- **Templates:** `coda/finance/templates/finance/payments/`
- **URLs:** `coda/finance/urls.py` (commented out lines 126-141)

## History

- **Oct 13, 2025:** Temporarily disabled (missing _deprecated module)
- **Sept 2025:** Unified payment flow implemented
- **Aug 2025:** M-Pesa STK Push integrated

---

**Last Updated:** October 13, 2025  
**Status:** Temporarily Disabled

