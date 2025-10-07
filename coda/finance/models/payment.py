# -*- coding: utf-8 -*-
"""
Finance Payment Models

Payment-related models including Payment, PaymentMethod, PaymentTransaction, and related models.
"""

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

# Get the User model
User = get_user_model()


# =============================================================================
# PAYMENT MODELS
# =============================================================================

class Payment(models.Model):
    """Payment model for loan repayments"""
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('bank_transfer', 'Bank Transfer'),
        ('mpesa', 'M-Pesa'),
        ('cash', 'Cash'),
        ('check', 'Check'),
        ('other', 'Other'),
    ]
    
    loan = models.ForeignKey('LoanApplication', on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    payment_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'finance_payment'
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-payment_date']
    
    def __str__(self):
        return "Payment {} - {} for Loan {}".format(self.id, self.amount, self.loan.id)
    
    def clean(self):
        """Validate payment data"""
        if self.amount <= 0:
            raise ValidationError('Payment amount must be greater than zero')
        
        if self.payment_date > timezone.now():
            raise ValidationError('Payment date cannot be in the future')
    
    def save(self, *args, **kwargs):
        """Custom save method with validation"""
        self.clean()
        super().save(*args, **kwargs)


class PaymentMethod(models.Model):
    """Available payment methods configuration"""
    
    METHOD_TYPE_CHOICES = [
        ('bank_transfer', 'Bank Transfer'),
        ('mobile_money', 'Mobile Money'),
        ('cash', 'Cash'),
        ('check', 'Check'),
        ('card', 'Card'),
        ('crypto', 'Cryptocurrency'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=50, unique=True)
    method_type = models.CharField(max_length=20, choices=METHOD_TYPE_CHOICES)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    # Configuration
    requires_verification = models.BooleanField(default=True)
    processing_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    processing_fee_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    min_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    max_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Integration settings
    api_endpoint = models.URLField(blank=True, null=True)
    api_key = models.CharField(max_length=200, blank=True, null=True)
    webhook_url = models.URLField(blank=True, null=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Payment Method'
        verbose_name_plural = 'Payment Methods'
    
    def __str__(self):
        return self.name
    
    def calculate_processing_fee(self, amount):
        """Calculate processing fee for a given amount"""
        fixed_fee = self.processing_fee
        percentage_fee = amount * (self.processing_fee_percentage / 100)
        return fixed_fee + percentage_fee


class PaymentTransaction(models.Model):
    """Individual payment transactions"""
    
    TRANSACTION_STATUS_CHOICES = [
        ('initiated', 'Initiated'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    # Core transaction data
    transaction_id = models.CharField(max_length=100, unique=True)
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default='KES')
    processing_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Status and timing
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS_CHOICES, default='initiated')
    initiated_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # External references
    external_transaction_id = models.CharField(max_length=100, blank=True, null=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    
    # User and context
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_transactions')
    description = models.TextField(blank=True, null=True)
    
    # Metadata
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-initiated_at']
        verbose_name = 'Payment Transaction'
        verbose_name_plural = 'Payment Transactions'
    
    def __str__(self):
        return "{} - {} {} - {}".format(self.transaction_id, self.amount, self.currency, self.get_status_display())
    
    def mark_as_processing(self):
        """Mark transaction as processing"""
        self.status = 'processing'
        self.processed_at = timezone.now()
        self.save(update_fields=['status', 'processed_at'])
    
    def mark_as_completed(self, external_id=None):
        """Mark transaction as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        if external_id:
            self.external_transaction_id = external_id
        self.save(update_fields=['status', 'completed_at', 'external_transaction_id'])
    
    def mark_as_failed(self, error_message=None):
        """Mark transaction as failed"""
        self.status = 'failed'
        if error_message:
            self.gateway_response['error'] = error_message
        self.save(update_fields=['status', 'gateway_response'])


class PaymentGateway(models.Model):
    """Payment gateway configuration"""
    
    GATEWAY_TYPE_CHOICES = [
        ('mpesa', 'M-Pesa'),
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('bank', 'Bank Transfer'),
        ('custom', 'Custom Gateway'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    gateway_type = models.CharField(max_length=20, choices=GATEWAY_TYPE_CHOICES)
    is_active = models.BooleanField(default=True)
    
    # Configuration
    api_url = models.URLField()
    api_key = models.CharField(max_length=200)
    secret_key = models.CharField(max_length=200, blank=True, null=True)
    webhook_secret = models.CharField(max_length=200, blank=True, null=True)
    
    # Settings
    test_mode = models.BooleanField(default=True)
    supported_currencies = models.JSONField(default=list)
    supported_countries = models.JSONField(default=list)
    
    # Limits
    min_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    max_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Payment Gateway'
        verbose_name_plural = 'Payment Gateways'
    
    def __str__(self):
        return "{} ({})".format(self.name, 'Test' if self.test_mode else 'Live')
    
    def is_currency_supported(self, currency):
        """Check if currency is supported"""
        return currency in self.supported_currencies
    
    def is_country_supported(self, country):
        """Check if country is supported"""
        return country in self.supported_countries
