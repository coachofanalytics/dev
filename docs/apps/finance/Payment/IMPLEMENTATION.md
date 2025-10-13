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

