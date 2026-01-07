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
    retry_count = models.IntegerField(default=0, help_text="Number of retry attempts for failed transactions")
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

    # Encrypted storage for API keys and sensitive configuration
    # This field stores JSON data in encrypted format for PCI DSS compliance
    config_data_encrypted = models.TextField(
        help_text="Encrypted JSON containing API keys and configuration",
        blank=True,
        default=''
    )

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

    @property
    def config_data(self):
        """
        Decrypt and deserialize config data.

        Returns:
            dict: Decrypted configuration data as dictionary
        """
        if not self.config_data_encrypted:
            return {}

        try:
            from core.encryption.services.encryption_service import EncryptionService
            import json

            # Decrypt the stored data
            decrypted = EncryptionService.decrypt(self.config_data_encrypted)
            # Parse JSON
            return json.loads(decrypted)
        except (json.JSONDecodeError, ValueError, Exception) as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error decrypting config_data: {e}")
            return {}

    @config_data.setter
    def config_data(self, value):
        """
        Serialize and encrypt config data.

        Args:
            value (dict): Configuration data to encrypt and store
        """
        if value is None:
            self.config_data_encrypted = ""
        else:
            from core.encryption.services.encryption_service import EncryptionService
            import json

            # Serialize to JSON
            json_data = json.dumps(value)
            # Encrypt
            encrypted = EncryptionService.encrypt(json_data)
            self.config_data_encrypted = encrypted


class WalletActivityLog(models.Model):
    """
    Log of all wallet-related activities for audit and security purposes.
    """
    ACTION_TYPES = [
        ('login', 'Login'),
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('payment', 'Payment'),
        ('transfer', 'Transfer'),
        ('settings_change', 'Settings Change'),
        ('limit_change', 'Limit Change'),
        ('failed_attempt', 'Failed Attempt'),
        ('suspicious_activity', 'Suspicious Activity'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wallet_activity_logs')
    wallet = models.ForeignKey(Wallet, on_delete=models.SET_NULL, null=True, blank=True)
    action_type = models.CharField(max_length=30, choices=ACTION_TYPES)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    is_suspicious = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Wallet Activity Log'
        verbose_name_plural = 'Wallet Activity Logs'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['action_type']),
            models.Index(fields=['is_suspicious']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.action_type} - {self.created_at}"


class WalletSpendingLimit(models.Model):
    """
    Spending and withdrawal limits for wallet security.
    """
    LIMIT_TYPES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('per_transaction', 'Per Transaction'),
    ]

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='spending_limits')
    limit_type = models.CharField(max_length=20, choices=LIMIT_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['wallet', 'limit_type']
        verbose_name = 'Wallet Spending Limit'
        verbose_name_plural = 'Wallet Spending Limits'

    def __str__(self):
        return f"{self.wallet.user.username} - {self.limit_type}: {self.amount}"


class FraudAlert(models.Model):
    """
    Fraud alerts and suspicious activity records.
    """
    ALERT_TYPES = [
        ('velocity', 'Unusual Transaction Velocity'),
        ('amount', 'Unusual Transaction Amount'),
        ('location', 'Unusual Location'),
        ('device', 'New Device'),
        ('pattern', 'Unusual Pattern'),
        ('failed_attempts', 'Multiple Failed Attempts'),
        ('limit_exceeded', 'Limit Exceeded Attempt'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('investigating', 'Under Investigation'),
        ('resolved', 'Resolved'),
        ('false_positive', 'False Positive'),
        ('confirmed_fraud', 'Confirmed Fraud'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fraud_alerts')
    wallet = models.ForeignKey(Wallet, on_delete=models.SET_NULL, null=True, blank=True)
    transaction = models.ForeignKey(Transaction, on_delete=models.SET_NULL, null=True, blank=True)
    alert_type = models.CharField(max_length=30, choices=ALERT_TYPES)
    severity = models.CharField(max_length=20, default='medium')
    description = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reviewed_fraud_alerts'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Fraud Alert'
        verbose_name_plural = 'Fraud Alerts'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['alert_type']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.alert_type} - {self.status}"


class PaymentDispute(models.Model):
    """
    Payment dispute management for handling conflicts.
    Enhanced with automated categorization, SLA tracking, and evidence uploads.
    """
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('under_review', 'Under Review'),
        ('resolved_favor_user', 'Resolved - User Favor'),
        ('resolved_favor_merchant', 'Resolved - Merchant Favor'),
        ('closed', 'Closed'),
    ]

    REASON_CHOICES = [
        ('unauthorized', 'Unauthorized Transaction'),
        ('not_received', 'Product/Service Not Received'),
        ('not_as_described', 'Not As Described'),
        ('duplicate', 'Duplicate Charge'),
        ('cancelled', 'Cancelled Service Still Charged'),
        ('other', 'Other'),
    ]

    RISK_LEVEL_CHOICES = [
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
    ]

    PRIORITY_CHOICES = [
        ('normal', 'Normal'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    # Basic Information
    dispute_id = models.CharField(max_length=50, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_disputes')
    transaction = models.ForeignKey(Transaction, on_delete=models.PROTECT, related_name='disputes')
    reason = models.CharField(max_length=30, choices=REASON_CHOICES)
    description = models.TextField()

    # Evidence Storage
    evidence = models.JSONField(default=dict, blank=True, help_text="Store evidence files and documents")
    evidence_files = models.CharField(
        max_length=500,
        blank=True,
        help_text="Comma-separated list of uploaded evidence file paths"
    )

    # Status & Resolution
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='open')
    amount_disputed = models.DecimalField(max_digits=10, decimal_places=2)
    amount_refunded = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    assigned_to = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_disputes'
    )
    resolution_notes = models.TextField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    # Automated Categorization
    risk_level = models.CharField(
        max_length=10,
        choices=RISK_LEVEL_CHOICES,
        default='medium',
        help_text="Auto-calculated risk level based on amount and reason"
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='normal',
        help_text="Auto-calculated priority for resolution"
    )

    # SLA Tracking
    sla_deadline = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Service Level Agreement deadline for resolution"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Payment Dispute'
        verbose_name_plural = 'Payment Disputes'
        indexes = [
            models.Index(fields=['status', 'sla_deadline']),
            models.Index(fields=['priority', 'created_at']),
        ]

    def __str__(self):
        return f"{self.dispute_id} - {self.user.username} - {self.status}"

    @property
    def is_overdue(self) -> bool:
        """Check if dispute is past SLA deadline."""
        if self.sla_deadline and self.status in ['open', 'under_review']:
            return timezone.now() > self.sla_deadline
        return False

    @property
    def days_open(self) -> int:
        """Calculate how many days the dispute has been open."""
        if self.resolved_at:
            delta = self.resolved_at - self.created_at
        else:
            delta = timezone.now() - self.created_at
        return delta.days

    @property
    def hours_until_sla(self) -> float:
        """Calculate hours remaining until SLA deadline."""
        if self.sla_deadline:
            delta = self.sla_deadline - timezone.now()
            return delta.total_seconds() / 3600
        return None

    def auto_categorize(self):
        """
        Automatically categorize dispute based on amount, reason, and user history.
        """
        # Calculate risk level based on amount
        if self.amount_disputed >= Decimal('1000.00'):
            self.risk_level = 'high'
        elif self.amount_disputed >= Decimal('100.00'):
            self.risk_level = 'medium'
        else:
            self.risk_level = 'low'

        # Adjust risk based on reason
        high_risk_reasons = ['unauthorized', 'duplicate']
        if self.reason in high_risk_reasons:
            self.risk_level = 'high'

        # Calculate priority
        if self.risk_level == 'high' or self.amount_disputed >= Decimal('500.00'):
            self.priority = 'critical'
        elif self.risk_level == 'medium' or self.reason == 'not_received':
            self.priority = 'high'
        else:
            self.priority = 'normal'

        # Check user's dispute history
        previous_disputes = PaymentDispute.objects.filter(
            user=self.user,
            status__in=['resolved_favor_user', 'resolved_favor_merchant']
        ).count()

        if previous_disputes >= 3:
            # Escalate priority for repeat disputers
            if self.priority == 'normal':
                self.priority = 'high'
            elif self.priority == 'high':
                self.priority = 'critical'

    def set_sla_deadline(self):
        """
        Set SLA deadline based on priority level.
        Critical: 24 hours, High: 48 hours, Normal: 72 hours
        """
        from datetime import timedelta

        if self.priority == 'critical':
            hours = 24
        elif self.priority == 'high':
            hours = 48
        else:
            hours = 72

        self.sla_deadline = self.created_at + timedelta(hours=hours)

    def save(self, *args, **kwargs):
        # Generate dispute ID if new
        if not self.dispute_id:
            date_part = timezone.now().strftime('%Y%m%d')
            random_part = str(uuid.uuid4().hex[:4]).upper()
            self.dispute_id = f"DSP-{date_part}-{random_part}"

        # Auto-categorize if new dispute
        is_new = self.pk is None
        if is_new:
            self.auto_categorize()
            self.set_sla_deadline()

        super().save(*args, **kwargs)


class SegregatedFundsLedger(models.Model):
    """
    Track segregation of customer funds from operational funds.
    Required for bankruptcy protection and regulatory compliance.
    Customer funds are held in trust and never commingled with operational funds.
    """
    FUND_TYPES = [
        ('customer', 'Customer Funds'),
        ('operational', 'Operational Funds'),
        ('reserve', 'Reserve Funds'),
    ]

    ENTRY_TYPES = [
        ('deposit', 'Customer Deposit'),
        ('withdrawal', 'Customer Withdrawal'),
        ('fee_collection', 'Fee Collection'),
        ('refund', 'Refund to Customer'),
        ('transfer_to_operational', 'Transfer to Operational'),
        ('transfer_from_operational', 'Transfer from Operational'),
        ('reconciliation_adjustment', 'Reconciliation Adjustment'),
    ]

    entry_id = models.CharField(max_length=50, unique=True, editable=False)
    fund_type = models.CharField(max_length=20, choices=FUND_TYPES)
    entry_type = models.CharField(max_length=30, choices=ENTRY_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)
    reference_transaction = models.ForeignKey(
        'Transaction', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='fund_ledger_entries'
    )
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        help_text="User associated with this fund movement"
    )
    description = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='fund_entries_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Segregated Funds Ledger Entry'
        verbose_name_plural = 'Segregated Funds Ledger Entries'
        indexes = [
            models.Index(fields=['fund_type', '-created_at']),
            models.Index(fields=['entry_type']),
        ]

    def __str__(self):
        return f"{self.entry_id} - {self.fund_type} - {self.entry_type}: ${self.amount}"

    def save(self, *args, **kwargs):
        if not self.entry_id:
            date_part = timezone.now().strftime('%Y%m%d%H%M%S')
            random_part = str(uuid.uuid4().hex[:6]).upper()
            self.entry_id = f"FND-{date_part}-{random_part}"
        super().save(*args, **kwargs)


class FundsReconciliation(models.Model):
    """
    Daily reconciliation records to ensure customer funds match wallet balances.
    Required for bankruptcy protection and regulatory compliance.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reconciled', 'Reconciled'),
        ('discrepancy', 'Discrepancy Found'),
        ('resolved', 'Resolved'),
    ]

    reconciliation_id = models.CharField(max_length=50, unique=True, editable=False)
    reconciliation_date = models.DateField()
    total_customer_wallets = models.DecimalField(
        max_digits=14, decimal_places=2,
        help_text="Sum of all customer wallet balances"
    )
    total_customer_funds_ledger = models.DecimalField(
        max_digits=14, decimal_places=2,
        help_text="Total in segregated customer funds ledger"
    )
    discrepancy_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'),
        help_text="Difference between wallets and ledger"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(null=True, blank=True)
    performed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reconciliations_performed'
    )
    reviewed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reconciliations_reviewed'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-reconciliation_date']
        verbose_name = 'Funds Reconciliation'
        verbose_name_plural = 'Funds Reconciliations'
        unique_together = ['reconciliation_date']

    def __str__(self):
        return f"{self.reconciliation_id} - {self.reconciliation_date} - {self.status}"

    def save(self, *args, **kwargs):
        if not self.reconciliation_id:
            date_part = self.reconciliation_date.strftime('%Y%m%d')
            random_part = str(uuid.uuid4().hex[:4]).upper()
            self.reconciliation_id = f"REC-{date_part}-{random_part}"
        # Calculate discrepancy
        self.discrepancy_amount = abs(self.total_customer_wallets - self.total_customer_funds_ledger)
        if self.discrepancy_amount == Decimal('0.00'):
            self.status = 'reconciled'
        elif self.discrepancy_amount > Decimal('0.00') and self.status == 'pending':
            self.status = 'discrepancy'
        super().save(*args, **kwargs)


class CustomerFundsProtection(models.Model):
    """
    Configuration and status for customer funds protection.
    Documents the segregation policy and protection status.
    """
    is_active = models.BooleanField(default=True)
    segregation_policy = models.TextField(
        default="Customer funds are held in segregated accounts separate from operational funds. "
                "These funds are held in trust for customers and are not used for operational purposes. "
                "In the event of bankruptcy, customer funds are protected and will be returned to customers."
    )
    last_audit_date = models.DateField(null=True, blank=True)
    next_audit_date = models.DateField(null=True, blank=True)
    compliance_status = models.CharField(
        max_length=20,
        choices=[
            ('compliant', 'Compliant'),
            ('review_needed', 'Review Needed'),
            ('non_compliant', 'Non-Compliant'),
        ],
        default='compliant'
    )
    audit_notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Customer Funds Protection'
        verbose_name_plural = 'Customer Funds Protection'

    def __str__(self):
        return f"Customer Funds Protection - {self.compliance_status}"

    @classmethod
    def get_current(cls):
        """Get or create the current protection configuration."""
        config, created = cls.objects.get_or_create(pk=1)
        return config


class FinancialAnalytics(models.Model):
    """
    Store pre-calculated financial analytics for users.
    """
    PERIOD_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='financial_analytics')
    period_type = models.CharField(max_length=20, choices=PERIOD_CHOICES)
    period_start = models.DateField()
    period_end = models.DateField()
    total_deposits = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_spending = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_transactions = models.IntegerField(default=0)
    average_transaction = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    closing_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-period_start']
        unique_together = ['user', 'period_type', 'period_start']
        verbose_name = 'Financial Analytics'
        verbose_name_plural = 'Financial Analytics'

    def __str__(self):
        return f"{self.user.username} - {self.period_type} - {self.period_start}"
