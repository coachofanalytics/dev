# Payment System - Implementation

## Current Status: DISABLED

### Why Disabled?
`ModuleNotFoundError: No module named 'finance._deprecated'`

**Root Cause:** Payment views in `finance/_deprecated/legacy_views/payment_views.py` not deployed

**Temporary Fix (Oct 13):**
```python
# finance/urls.py
try:
    from ._deprecated.legacy_views import payment_views
except ImportError:
    payment_views = None  # Graceful degradation

# URLs commented out (lines 126-141)
```

## Legacy Implementation

### Payment Views (Not Currently Deployed)
**Location:** `coda/finance/_deprecated/legacy_views/payment_views.py`

**Key Functions:**
- `payment_method_selection()` - Choose M-Pesa/Stripe/Bank
- `mpesa_payment()` - Initiate STK Push
- `stripe_payment()` - Create payment intent
- `payment_confirmation()` - Handle callbacks

### Payment Models
**Location:** `coda/finance/models/payment.py`

```python
class Payment(models.Model):
    user = ForeignKey(User)
    amount = DecimalField()
    method = CharField(choices=['mpesa', 'stripe', 'bank'])
    status = CharField(choices=['pending', 'completed', 'failed'])
    transaction_id = CharField(unique=True)
    created_at = DateTimeField(auto_now_add=True)
```

## Re-Enabling Payment System

### Option A: Deploy `_deprecated` Module
```bash
# Ensure _deprecated directory included in deployment
git add coda/finance/_deprecated/
git commit -m "Deploy payment views"
git push heroku ...
```

### Option B: Refactor to New Structure
1. Move payment views to `coda/finance/views/payment/`
2. Update imports in `urls.py`
3. Remove `_deprecated` dependency
4. Test thoroughly

## M-Pesa Integration (When Re-Enabled)

### STK Push Flow
1. User enters phone number, amount
2. Backend calls Safaricom API
3. User receives payment prompt on phone
4. User enters M-Pesa PIN
5. Callback received
6. Payment status updated

### Configuration
```python
# settings.py
MPESA_CONSUMER_KEY = env('MPESA_CONSUMER_KEY')
MPESA_CONSUMER_SECRET = env('MPESA_CONSUMER_SECRET')
MPESA_SHORTCODE = env('MPESA_SHORTCODE')
MPESA_PASSKEY = env('MPESA_PASSKEY')
```

## Stripe Integration (When Re-Enabled)

### Payment Intent Flow
1. Frontend creates payment intent
2. Stripe Elements collects card details
3. 3D Secure authentication (if required)
4. Payment confirmed
5. Webhook updates database

---

**Last Updated:** October 13, 2025  
**Status:** Documentation only - system disabled

