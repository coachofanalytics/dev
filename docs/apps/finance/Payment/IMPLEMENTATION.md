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

## Recommended Architecture (Enterprise Pattern)

### Overview
Payment system should follow **Account-Based Architecture** with separation of concerns:

```
Customer Account (Master Record)
├── Current Balance (calculated)
├── Payment Plan
├── Account Status
└── Payment Methods

Payment Transactions (Immutable)
├── Transaction ID
├── Amount
├── Type (payment, refund, adjustment)
├── Payment Method
├── Reference Number
├── Timestamp
└── Status
```

### Recommended Models

#### CustomerAccount Model
```python
class CustomerAccount(models.Model):
    """Customer's financial account status"""
    customer = models.OneToOneField(CustomerUser, on_delete=models.CASCADE)
    
    # Account Details
    total_amount_owed = models.DecimalField(max_digits=10, decimal_places=2)
    initial_down_payment = models.DecimalField(max_digits=10, decimal_places=2)
    student_bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Current Status
    current_balance = models.DecimalField(max_digits=10, decimal_places=2)
    account_status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('suspended', 'Suspended'),
            ('paid_off', 'Paid Off'),
            ('defaulted', 'Defaulted'),
        ]
    )
    
    # Payment Plan
    plan = models.ForeignKey('PaymentPlan', on_delete=models.CASCADE)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def remaining_balance(self):
        """Calculate remaining balance from transactions"""
        total_paid = self.transactions.filter(
            transaction_type='payment',
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        return max(0, self.total_amount_owed - total_paid)
```

#### PaymentTransaction Model
```python
class PaymentTransaction(models.Model):
    """Immutable record of all payment-related transactions"""
    TRANSACTION_TYPES = [
        ('payment', 'Payment'),
        ('refund', 'Refund'),
        ('adjustment', 'Adjustment'),
        ('fee', 'Fee'),
    ]
    
    TRANSACTION_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Transaction Details
    account = models.ForeignKey(CustomerAccount, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Payment Details
    payment_method = models.CharField(max_length=50)  # mpesa, stripe, bank
    reference_number = models.CharField(max_length=100, unique=True)
    external_reference = models.CharField(max_length=100, blank=True)  # M-Pesa/Stripe ID
    
    # Status & Metadata
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS)
    description = models.TextField(blank=True)
    processed_at = models.DateTimeField(auto_now_add=True)
    
    # Audit Trail
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-processed_at']
        indexes = [
            models.Index(fields=['account', 'processed_at']),
            models.Index(fields=['reference_number']),
            models.Index(fields=['status']),
        ]
```

### Service Layer

#### PaymentService
```python
class PaymentService:
    """Handles all payment-related business logic"""
    
    def create_payment(self, account_id, amount, payment_method, **kwargs):
        """Create a new payment transaction"""
        with transaction.atomic():
            payment = PaymentTransaction.objects.create(
                account_id=account_id,
                transaction_type='payment',
                amount=amount,
                payment_method=payment_method,
                reference_number=self._generate_reference(),
                status='pending',
                **kwargs
            )
            self._update_account_balance(account_id)
            return payment
    
    def process_payment(self, transaction_id, external_reference=None):
        """Process a pending payment"""
        with transaction.atomic():
            payment = PaymentTransaction.objects.select_for_update().get(id=transaction_id)
            
            if payment.status != 'pending':
                raise ValueError("Payment is not pending")
            
            payment.status = 'completed'
            payment.external_reference = external_reference
            payment.save()
            
            self._update_account_balance(payment.account_id)
            return payment
```

**Source:** PAYMENT_SYSTEM_ARCHITECTURE_ANALYSIS.md

---

## Legacy Implementation (Currently Disabled)

### Payment Views (Not Currently Deployed)
**Location:** `coda/finance/_deprecated/legacy_views/payment_views.py`

**Key Functions:**
- `payment_method_selection()` - Choose M-Pesa/Stripe/Bank
- `mpesa_payment()` - Initiate STK Push
- `stripe_payment()` - Create payment intent
- `payment_confirmation()` - Handle callbacks

### Current Payment Models
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

**Note:** Current models need refactoring to match recommended architecture above

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
```
1. User selects M-Pesa payment method
   ↓
2. User enters phone number (254XXXXXXXXX format)
   ↓
3. User enters amount (min KES 10, max KES 150,000)
   ↓
4. Backend generates transaction reference
   ↓
5. Backend calls Safaricom API (STK Push)
   ↓
6. User receives payment prompt on phone
   ↓
7. User enters M-Pesa PIN on phone
   ↓
8. M-Pesa processes payment
   ↓
9. Callback received at /finance/mpesa/callback/
   ↓
10. Payment status updated (completed/failed)
   ↓
11. User redirected to confirmation page
```

### Configuration
```python
# settings.py
MPESA_CONSUMER_KEY = env('MPESA_CONSUMER_KEY')
MPESA_CONSUMER_SECRET = env('MPESA_CONSUMER_SECRET')
MPESA_SHORTCODE = env('MPESA_SHORTCODE')
MPESA_PASSKEY = env('MPESA_PASSKEY')
MPESA_CALLBACK_URL = env('MPESA_CALLBACK_URL')  # https://yourapp.com/finance/mpesa/callback/
```

### API Endpoints
```python
# Initiate STK Push
POST /finance/mpesa/initiate/
Body: {
    "phone": "254712345678",
    "amount": 1000,
    "account_reference": "ACC123"
}
Response: {
    "status": "pending",
    "checkout_request_id": "ws_CO_13102025123456",
    "message": "Check your phone for M-Pesa prompt"
}

# Callback (Safaricom calls this)
POST /finance/mpesa/callback/
Body: {
    "ResultCode": 0,  # 0 = success
    "ResultDesc": "The service request is processed successfully",
    "CheckoutRequestID": "ws_CO_13102025123456",
    "MpesaReceiptNumber": "OEI2AK4Q16"
}
```

### Error Handling
- **Timeout:** User didn't enter PIN (30 seconds)
- **Insufficient Funds:** User has insufficient M-Pesa balance
- **Invalid Phone:** Phone number format incorrect
- **API Error:** Safaricom API unavailable

---

## Stripe Integration (When Re-Enabled)

### Payment Intent Flow
```
1. User selects Stripe (card) payment
   ↓
2. Frontend creates payment intent via API
   ↓
3. Stripe Elements renders card input form
   ↓
4. User enters card details (number, expiry, CVC)
   ↓
5. Stripe validates card
   ↓
6. 3D Secure authentication (if required)
   ↓
7. Payment processed
   ↓
8. Webhook received at /finance/stripe/webhook/
   ↓
9. Payment status updated
   ↓
10. User redirected to confirmation
```

### Configuration
```python
# settings.py
STRIPE_PUBLIC_KEY = env('STRIPE_PUBLIC_KEY')
STRIPE_SECRET_KEY = env('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = env('STRIPE_WEBHOOK_SECRET')
```

### API Endpoints
```python
# Create payment intent
POST /finance/stripe/create-intent/
Body: {
    "amount": 10000,  # Amount in cents
    "currency": "usd",
    "account_id": 123
}
Response: {
    "client_secret": "pi_xxx_secret_xxx",
    "payment_intent_id": "pi_xxx"
}

# Webhook (Stripe calls this)
POST /finance/stripe/webhook/
Headers: {
    "Stripe-Signature": "t=xxx,v1=xxx"
}
Body: {
    "type": "payment_intent.succeeded",
    "data": {
        "object": {
            "id": "pi_xxx",
            "amount": 10000,
            "status": "succeeded"
        }
    }
}
```

### Error Handling
- **Card Declined:** Insufficient funds, card blocked
- **Invalid Card:** Card number invalid
- **3D Secure Failed:** Authentication failed
- **Network Error:** Stripe API unavailable

---

## Bank Transfer Integration

### Flow
```
1. User selects Bank Transfer
   ↓
2. System displays bank account details
   ↓
3. User makes transfer manually
   ↓
4. User uploads proof of payment
   ↓
5. Admin verifies payment
   ↓
6. Payment marked as completed
```

### Bank Details Display
```
Bank: Example Bank
Account Name: CODA Training
Account Number: 1234567890
Reference: [Auto-generated - e.g., PAY-2025-001]
Amount: $XXX.XX
```

**Source:** PAYMENT_SYSTEM_MANUAL_TESTING_GUIDE.md

---

## Change History

| Date | Change | Files Modified | Reason |
|------|--------|----------------|---------|
| Oct 17, 2025 | Fixed Payment_History field error | `utils.py`, `utils/__init__.py` | Changed `description=` to `notes=` to match model field |

---

**Last Updated:** October 17, 2025  
**Status:** Architecture complete, implementation pending

