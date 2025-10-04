# -*- coding: utf-8 -*-
"""
Payment-specific models for payment methods, transactions, and gateways.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
import uuid

# Get the User model
User = get_user_model()

# Import models from other apps
try:
    from main.models import Company
except ImportError:
    Company = None


class PaymentMethod(models.Model):
    """Payment methods available for transactions."""
    
    # Payment method types
    METHOD_TYPE_CHOICES = [
        ('Cash', 'Cash'),
        ('Bank Transfer', 'Bank Transfer'),
        ('Mobile Money', 'Mobile Money'),
        ('Credit Card', 'Credit Card'),
        ('Debit Card', 'Debit Card'),
        ('Check', 'Check'),
        ('PayPal', 'PayPal'),
        ('M-Pesa', 'M-Pesa'),
        ('Other', 'Other'),
    ]
    
    # Payment method status
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('Suspended', 'Suspended'),
    ]
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='payment_methods',
        help_text="Company this payment method belongs to"
    )
    
    # Payment method details
    name = models.CharField(
        max_length=100,
        help_text="Name of the payment method"
    )
    method_type = models.CharField(
        max_length=20,
        choices=METHOD_TYPE_CHOICES,
        help_text="Type of payment method"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of the payment method"
    )
    
    # Payment method settings
    is_default = models.BooleanField(
        default=False,
        help_text="Whether this is the default payment method"
    )
    requires_verification = models.BooleanField(
        default=False,
        help_text="Whether this method requires verification"
    )
    supports_refunds = models.BooleanField(
        default=True,
        help_text="Whether this method supports refunds"
    )
    
    # Fees and limits
    processing_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Processing fee for this method"
    )
    fee_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Fee percentage for this method"
    )
    min_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Minimum transaction amount"
    )
    max_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum transaction amount"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Active',
        help_text="Payment method status"
    )
    
    # Configuration
    configuration = models.JSONField(
        default=dict,
        blank=True,
        help_text="Payment method configuration"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Payment Method")
        verbose_name_plural = _("Payment Methods")
        ordering = ['name']
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['method_type']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.method_type})"
    
    @property
    def is_active(self):
        """Check if payment method is active."""
        return self.status == 'Active'
    
    def calculate_fee(self, amount):
        """Calculate processing fee for given amount."""
        fee = self.processing_fee
        if self.fee_percentage > 0:
            fee += (amount * self.fee_percentage) / 100
        return fee
    
    def is_amount_valid(self, amount):
        """Check if amount is within limits."""
        if self.min_amount and amount < self.min_amount:
            return False
        if self.max_amount and amount > self.max_amount:
            return False
        return True


class PaymentGateway(models.Model):
    """Payment gateway configurations."""
    
    # Gateway types
    GATEWAY_TYPE_CHOICES = [
        ('Bank', 'Bank Gateway'),
        ('Mobile', 'Mobile Money Gateway'),
        ('Card', 'Card Processing Gateway'),
        ('Digital', 'Digital Wallet Gateway'),
        ('Other', 'Other Gateway'),
    ]
    
    # Gateway status
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('Testing', 'Testing'),
        ('Suspended', 'Suspended'),
    ]
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='payment_gateways',
        help_text="Company this gateway belongs to"
    )
    
    # Gateway details
    name = models.CharField(
        max_length=100,
        help_text="Name of the payment gateway"
    )
    gateway_type = models.CharField(
        max_length=20,
        choices=GATEWAY_TYPE_CHOICES,
        help_text="Type of payment gateway"
    )
    provider = models.CharField(
        max_length=100,
        help_text="Gateway provider name"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of the gateway"
    )
    
    # Gateway configuration
    api_endpoint = models.URLField(
        blank=True,
        help_text="API endpoint URL"
    )
    api_key = models.CharField(
        max_length=200,
        blank=True,
        help_text="API key for gateway"
    )
    secret_key = models.CharField(
        max_length=200,
        blank=True,
        help_text="Secret key for gateway"
    )
    webhook_url = models.URLField(
        blank=True,
        help_text="Webhook URL for notifications"
    )
    
    # Gateway settings
    is_default = models.BooleanField(
        default=False,
        help_text="Whether this is the default gateway"
    )
    supports_refunds = models.BooleanField(
        default=True,
        help_text="Whether gateway supports refunds"
    )
    supports_partial_refunds = models.BooleanField(
        default=False,
        help_text="Whether gateway supports partial refunds"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Testing',
        help_text="Gateway status"
    )
    
    # Additional configuration
    configuration = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional gateway configuration"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Payment Gateway")
        verbose_name_plural = _("Payment Gateways")
        ordering = ['name']
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['gateway_type']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.provider})"
    
    @property
    def is_active(self):
        """Check if gateway is active."""
        return self.status == 'Active'
    
    @property
    def is_testing(self):
        """Check if gateway is in testing mode."""
        return self.status == 'Testing'


class PaymentTransaction(models.Model):
    """Payment transactions processed through the system."""
    
    # Transaction types
    TRANSACTION_TYPE_CHOICES = [
        ('Payment', 'Payment'),
        ('Refund', 'Refund'),
        ('Chargeback', 'Chargeback'),
        ('Adjustment', 'Adjustment'),
    ]
    
    # Transaction status
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
        ('Cancelled', 'Cancelled'),
        ('Refunded', 'Refunded'),
    ]
    
    # Unique identifier
    transaction_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        help_text="Unique transaction identifier"
    )
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='payment_transactions',
        help_text="Company this transaction belongs to"
    )
    
    # Transaction details
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPE_CHOICES,
        help_text="Type of transaction"
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Transaction amount"
    )
    currency = models.CharField(
        max_length=3,
        default='USD',
        help_text="Transaction currency"
    )
    
    # Payment method and gateway
    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        help_text="Payment method used"
    )
    payment_gateway = models.ForeignKey(
        PaymentGateway,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        help_text="Payment gateway used"
    )
    
    # Transaction metadata
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending',
        help_text="Transaction status"
    )
    reference = models.CharField(
        max_length=100,
        blank=True,
        help_text="Transaction reference"
    )
    external_reference = models.CharField(
        max_length=100,
        blank=True,
        help_text="External system reference"
    )
    
    # Parties involved
    payer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payment_transactions',
        help_text="User making the payment"
    )
    payee_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Name of payee"
    )
    payee_account = models.CharField(
        max_length=100,
        blank=True,
        help_text="Payee account details"
    )
    
    # Transaction details
    description = models.TextField(
        blank=True,
        help_text="Transaction description"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes"
    )
    
    # Fees
    processing_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Processing fee charged"
    )
    gateway_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Gateway fee charged"
    )
    
    # Dates
    initiated_at = models.DateTimeField(
        default=timezone.now,
        help_text="When transaction was initiated"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When transaction was completed"
    )
    
    # Gateway response
    gateway_response = models.JSONField(
        default=dict,
        blank=True,
        help_text="Response from payment gateway"
    )
    gateway_status = models.CharField(
        max_length=50,
        blank=True,
        help_text="Status from payment gateway"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Payment Transaction")
        verbose_name_plural = _("Payment Transactions")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['initiated_at']),
        ]
    
    def __str__(self):
        return f"{self.transaction_type} - {self.amount} {self.currency} ({self.status})"
    
    @property
    def is_pending(self):
        """Check if transaction is pending."""
        return self.status in ['Pending', 'Processing']
    
    @property
    def is_completed(self):
        """Check if transaction is completed."""
        return self.status == 'Completed'
    
    @property
    def is_failed(self):
        """Check if transaction failed."""
        return self.status == 'Failed'
    
    @property
    def net_amount(self):
        """Calculate net amount after fees."""
        return self.amount - self.processing_fee - self.gateway_fee
    
    def mark_completed(self, gateway_response=None):
        """Mark transaction as completed."""
        self.status = 'Completed'
        self.completed_at = timezone.now()
        if gateway_response:
            self.gateway_response = gateway_response
        self.save(update_fields=['status', 'completed_at', 'gateway_response'])
    
    def mark_failed(self, reason=None):
        """Mark transaction as failed."""
        self.status = 'Failed'
        if reason:
            self.notes = f"Failed: {reason}"
        self.save(update_fields=['status', 'notes'])
    
    def process_refund(self, refund_amount=None):
        """Process refund for this transaction."""
        if not self.payment_gateway or not self.payment_gateway.supports_refunds:
            raise ValueError("Refunds not supported for this transaction")
        
        refund_amount = refund_amount or self.amount
        if refund_amount > self.amount:
            raise ValueError("Refund amount cannot exceed original amount")
        
        # Create refund transaction
        refund = PaymentTransaction.objects.create(
            company=self.company,
            transaction_type='Refund',
            amount=refund_amount,
            currency=self.currency,
            payment_method=self.payment_method,
            payment_gateway=self.payment_gateway,
            payer=self.payer,
            payee_name=self.payee_name,
            payee_account=self.payee_account,
            description=f"Refund for transaction {self.transaction_id}",
            reference=f"REF-{self.reference}",
        )
        
        # Update original transaction
        self.status = 'Refunded'
        self.save(update_fields=['status'])
        
        return refund
