from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid
from datetime import timedelta


class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))])
    currency = models.CharField(max_length=3, default='USD')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Wallet'
        verbose_name_plural = 'Wallets'


    def get_features_list(self):
        """Return features as a list for template compatibility"""
        if isinstance(self.features, list):
            return self.features
        return []

    def __str__(self):
        return f"{self.user.username}'s Wallet - ${self.balance}"

    def credit(self, amount):
        if amount > 0:
            self.balance += Decimal(str(amount))
            self.save()
            return True
        return False

    def debit(self, amount):
        if amount > 0 and self.balance >= Decimal(str(amount)):
            self.balance -= Decimal(str(amount))
            self.save()
            return True
        return False

    def has_sufficient_balance(self, amount):
        return self.balance >= Decimal(str(amount))


class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    duration_days = models.IntegerField(default=30, help_text="Number of days the subscription is valid")
    features = models.JSONField(default=list, help_text="List of features included in this plan")
    is_active = models.BooleanField(default=True)
    category = models.ForeignKey('accounts.Category', on_delete=models.SET_NULL, null=True, blank=True)
    is_featured = models.BooleanField(default=False, help_text="Highlight this plan as featured")
    billing_period = models.CharField(max_length=50, default='per month', help_text="Display text for billing period")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['price']
        verbose_name = 'Subscription Plan'
        verbose_name_plural = 'Subscription Plans'

    def __str__(self):
        return f"{self.name} - ${self.price}/{self.duration_days} days"


class UserSubscription(models.Model):
    STATUS_CHOICES = [('active', 'Active'), ('expired', 'Expired'), ('cancelled', 'Cancelled'), ('pending', 'Pending Payment')]
    PAYMENT_METHOD_CHOICES = [('wallet', 'Wallet'), ('stripe', 'Stripe (Card)'), ('mpesa', 'M-Pesa'), ('paypal', 'PayPal')]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    auto_renew = models.BooleanField(default=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='wallet')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'User Subscription'
        verbose_name_plural = 'User Subscriptions'

    def __str__(self):
        return f"{self.user.username} - {self.plan.name} ({self.status})"

    def activate(self):
        self.status = 'active'
        self.start_date = timezone.now()
        self.end_date = timezone.now() + timedelta(days=self.plan.duration_days)
        self.save()

    def cancel(self):
        self.status = 'cancelled'
        self.auto_renew = False
        self.save()

    def is_valid(self):
        if self.status == 'active' and self.end_date:
            return timezone.now() <= self.end_date
        return False

    def days_remaining(self):
        if self.is_valid():
            return (self.end_date - timezone.now()).days
        return 0

    @property
    def days_until_expiry(self):
        """Property version of days_remaining for template compatibility"""
        return self.days_remaining()
    
    @property
    def needs_renewal_notification(self):
        """Check if subscription is expiring soon (7 days or less)"""
        if self.status == 'active' and self.end_date:
            days_left = self.days_remaining()
            return days_left <= 7 and days_left > 0
        return False


class Invoice(models.Model):
    STATUS_CHOICES = [('pending', 'Pending'), ('paid', 'Paid'), ('cancelled', 'Cancelled'), ('refunded', 'Refunded')]

    invoice_number = models.CharField(max_length=50, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invoices')
    subscription = models.ForeignKey(UserSubscription, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    due_date = models.DateTimeField()
    paid_date = models.DateTimeField(null=True, blank=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Invoice'
        verbose_name_plural = 'Invoices'

    def __str__(self):
        return f"{self.invoice_number} - {self.user.username} - ${self.amount}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            date_part = timezone.now().strftime('%Y%m%d')
            random_part = str(uuid.uuid4().hex[:4]).upper()
            self.invoice_number = f"INV-{date_part}-{random_part}"
        super().save(*args, **kwargs)

    def mark_as_paid(self, payment_date=None):
        self.status = 'paid'
        self.paid_date = payment_date or timezone.now()
        self.save()

    def is_overdue(self):
        if self.status == 'pending' and self.due_date:
            return timezone.now() > self.due_date
        return False


class Transaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [('deposit', 'Deposit'), ('subscription_payment', 'Subscription Payment'), ('invoice_payment', 'Invoice Payment'), ('refund', 'Refund'), ('adjustment', 'Manual Adjustment')]
    STATUS_CHOICES = [('pending', 'Pending'), ('completed', 'Completed'), ('failed', 'Failed'), ('refunded', 'Refunded')]
    GATEWAY_CHOICES = [('wallet', 'Wallet'), ('stripe', 'Stripe'), ('mpesa', 'M-Pesa'), ('paypal', 'PayPal'), ('manual', 'Manual')]

    transaction_id = models.CharField(max_length=100, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    wallet = models.ForeignKey(Wallet, on_delete=models.SET_NULL, null=True, blank=True)
    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, blank=True)
    transaction_type = models.CharField(max_length=30, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    currency = models.CharField(max_length=3, default='USD')
    payment_gateway = models.CharField(max_length=20, choices=GATEWAY_CHOICES)
    gateway_transaction_id = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    metadata = models.JSONField(default=dict, blank=True, help_text="Store gateway response, fees, and other details")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        indexes = [models.Index(fields=['transaction_id']), models.Index(fields=['user', '-created_at']), models.Index(fields=['status'])]

    def __str__(self):
        return f"{self.transaction_id} - {self.user.username} - ${self.amount}"

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            random_part = str(uuid.uuid4().hex[:6]).upper()
            self.transaction_id = f"TXN-{timestamp}-{random_part}"
        super().save(*args, **kwargs)

    def mark_as_completed(self):
        self.status = 'completed'
        self.save()

    def mark_as_failed(self, reason=None):
        self.status = 'failed'
        if reason:
            self.metadata['failure_reason'] = reason
        self.save()


class PaymentGatewayConfig(models.Model):
    GATEWAY_CHOICES = [('stripe', 'Stripe'), ('mpesa', 'M-Pesa'), ('paypal', 'PayPal')]

    gateway_name = models.CharField(max_length=20, choices=GATEWAY_CHOICES, unique=True)
    is_active = models.BooleanField(default=True, help_text="Enable/disable this payment gateway")
    is_test_mode = models.BooleanField(default=True, help_text="Use test/sandbox credentials")
    config_data = models.JSONField(default=dict, help_text="Store API keys and configuration")
    last_updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='gateway_configs_updated')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Payment Gateway Config'
        verbose_name_plural = 'Payment Gateway Configs'

    def __str__(self):
        mode = "TEST" if self.is_test_mode else "LIVE"
        status = "Active" if self.is_active else "Inactive"
        return f"{self.get_gateway_name_display()} ({mode}) - {status}"


class IdempotencyKey(models.Model):
    STATUS_CHOICES = [('pending', 'Pending'), ('used', 'Used'), ('cancelled', 'Cancelled')]

    key = models.CharField(max_length=255, unique=True, db_index=True)
    created_by = models.ForeignKey('auth.User', null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    response = models.JSONField(null=True, blank=True, help_text='Stored gateway response for idempotent replay')
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Idempotency Key'
        verbose_name_plural = 'Idempotency Keys'

    def mark_used(self, response_data: dict):
        self.status = 'used'
        self.response = response_data
        self.save()

    def mark_cancelled(self):
        self.status = 'cancelled'
        self.save()

    def is_active(self):
        return self.status == 'pending'
