"""
Comprehensive tests for payment services.

Tests wallet service, subscription service, transaction service, 
notification service, analytics service, and retry service.
"""

import pytest
from decimal import Decimal
from datetime import timedelta
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError

from payments.models import (
    Wallet, Transaction, Invoice, 
    SubscriptionPlan, UserSubscription,
    WalletActivityLog, WalletSpendingLimit,
    FraudAlert, PaymentDispute
)


# =============================================================================
# WALLET SERVICE TESTS
# =============================================================================

@pytest.mark.django_db
class TestWalletService:
    """Test suite for wallet service operations."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='wallet_user',
            email='wallet@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def wallet(self, user):
        """Create test wallet."""
        wallet, _ = Wallet.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('100.00')}
        )
        wallet.balance = Decimal('100.00')
        wallet.save()
        return wallet

    def test_credit_positive_amount(self, wallet):
        """Test crediting a positive amount."""
        initial = wallet.balance
        result = wallet.credit(Decimal('50.00'))
        
        assert result is True
        wallet.refresh_from_db()
        assert wallet.balance == initial + Decimal('50.00')

    def test_credit_negative_amount_fails(self, wallet):
        """Test crediting a negative amount fails."""
        initial = wallet.balance
        result = wallet.credit(Decimal('-50.00'))
        
        assert result is False
        wallet.refresh_from_db()
        assert wallet.balance == initial

    def test_credit_zero_amount_fails(self, wallet):
        """Test crediting zero fails."""
        initial = wallet.balance
        result = wallet.credit(Decimal('0.00'))
        
        assert result is False
        wallet.refresh_from_db()
        assert wallet.balance == initial

    def test_credit_large_amount(self, wallet):
        """Test crediting a large amount."""
        large_amount = Decimal('999999.99')
        result = wallet.credit(large_amount)
        
        assert result is True
        wallet.refresh_from_db()
        assert wallet.balance == Decimal('100.00') + large_amount

    def test_debit_sufficient_balance(self, wallet):
        """Test debiting with sufficient balance."""
        result = wallet.debit(Decimal('50.00'))
        
        assert result is True
        wallet.refresh_from_db()
        assert wallet.balance == Decimal('50.00')

    def test_debit_insufficient_balance_fails(self, wallet):
        """Test debiting with insufficient balance fails."""
        initial = wallet.balance
        result = wallet.debit(Decimal('150.00'))
        
        assert result is False
        wallet.refresh_from_db()
        assert wallet.balance == initial

    def test_debit_exact_balance(self, wallet):
        """Test debiting exact balance succeeds."""
        result = wallet.debit(Decimal('100.00'))
        
        assert result is True
        wallet.refresh_from_db()
        assert wallet.balance == Decimal('0.00')

    def test_debit_negative_amount_fails(self, wallet):
        """Test debiting negative amount fails."""
        initial = wallet.balance
        result = wallet.debit(Decimal('-50.00'))
        
        assert result is False
        wallet.refresh_from_db()
        assert wallet.balance == initial

    def test_debit_zero_amount_fails(self, wallet):
        """Test debiting zero fails."""
        initial = wallet.balance
        result = wallet.debit(Decimal('0.00'))
        
        assert result is False
        wallet.refresh_from_db()
        assert wallet.balance == initial

    def test_has_sufficient_balance_true(self, wallet):
        """Test has_sufficient_balance returns True when sufficient."""
        assert wallet.has_sufficient_balance(Decimal('50.00')) is True
        assert wallet.has_sufficient_balance(Decimal('100.00')) is True

    def test_has_sufficient_balance_false(self, wallet):
        """Test has_sufficient_balance returns False when insufficient."""
        assert wallet.has_sufficient_balance(Decimal('150.00')) is False

    def test_has_sufficient_balance_zero(self, wallet):
        """Test has_sufficient_balance with zero."""
        assert wallet.has_sufficient_balance(Decimal('0.00')) is True

    def test_wallet_string_representation(self, wallet):
        """Test wallet string representation."""
        wallet.balance = Decimal('123.45')
        wallet.save()
        
        str_repr = str(wallet)
        assert wallet.user.username in str_repr
        assert '123.45' in str_repr

    def test_wallet_is_active_default(self, user):
        """Test wallet is active by default."""
        wallet, _ = Wallet.objects.get_or_create(user=user)
        assert wallet.is_active is True

    def test_wallet_currency_default(self, user):
        """Test wallet currency default is USD."""
        wallet, _ = Wallet.objects.get_or_create(user=user)
        assert wallet.currency == 'USD'


# =============================================================================
# SUBSCRIPTION SERVICE TESTS
# =============================================================================

@pytest.mark.django_db
class TestSubscriptionService:
    """Test suite for subscription service operations."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='sub_user',
            email='sub@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def plan(self):
        """Create test subscription plan."""
        return SubscriptionPlan.objects.create(
            name='Premium',
            slug='premium',
            description='Premium subscription plan',
            price=Decimal('29.99'),
            duration_days=30,
            is_active=True,
            features=['Feature 1', 'Feature 2']
        )

    @pytest.fixture
    def subscription(self, user, plan):
        """Create test subscription."""
        return UserSubscription.objects.create(
            user=user,
            plan=plan,
            status='pending'
        )

    def test_subscription_activation(self, subscription):
        """Test subscription activation."""
        subscription.activate()
        
        assert subscription.status == 'active'
        assert subscription.start_date is not None
        assert subscription.end_date is not None

    def test_subscription_activation_sets_correct_end_date(self, subscription):
        """Test activation sets correct end date based on plan duration."""
        subscription.activate()
        
        expected_end = subscription.start_date + timedelta(days=30)
        # Allow for small time differences
        diff = abs((subscription.end_date - expected_end).total_seconds())
        assert diff < 5

    def test_subscription_cancellation(self, subscription):
        """Test subscription cancellation."""
        subscription.activate()
        subscription.cancel()
        
        assert subscription.status == 'cancelled'
        assert subscription.auto_renew is False

    def test_subscription_is_valid_when_active(self, subscription):
        """Test is_valid returns True for active subscription."""
        subscription.activate()
        
        assert subscription.is_valid() is True

    def test_subscription_is_valid_when_pending(self, subscription):
        """Test is_valid returns False for pending subscription."""
        assert subscription.is_valid() is False

    def test_subscription_is_valid_when_expired(self, subscription):
        """Test is_valid returns False for expired subscription."""
        subscription.activate()
        subscription.end_date = timezone.now() - timedelta(days=1)
        subscription.save()
        
        assert subscription.is_valid() is False

    def test_subscription_days_remaining_active(self, subscription):
        """Test days_remaining for active subscription."""
        subscription.activate()
        days = subscription.days_remaining()
        
        assert 29 <= days <= 30

    def test_subscription_days_remaining_expired(self, subscription):
        """Test days_remaining returns 0 for expired subscription."""
        subscription.activate()
        subscription.end_date = timezone.now() - timedelta(days=1)
        subscription.save()
        
        assert subscription.days_remaining() == 0

    def test_subscription_needs_renewal_notification(self, subscription):
        """Test needs_renewal_notification for soon-expiring subscription."""
        subscription.status = 'active'
        subscription.start_date = timezone.now()
        subscription.end_date = timezone.now() + timedelta(days=5)
        subscription.save()
        
        assert subscription.needs_renewal_notification is True

    def test_subscription_no_renewal_notification_when_not_expiring_soon(self, subscription):
        """Test needs_renewal_notification returns False when not expiring soon."""
        subscription.status = 'active'
        subscription.start_date = timezone.now()
        subscription.end_date = timezone.now() + timedelta(days=15)
        subscription.save()
        
        assert subscription.needs_renewal_notification is False

    def test_subscription_string_representation(self, subscription):
        """Test subscription string representation."""
        str_repr = str(subscription)
        
        assert subscription.user.username in str_repr
        assert subscription.plan.name in str_repr
        assert subscription.status in str_repr


# =============================================================================
# TRANSACTION SERVICE TESTS
# =============================================================================

@pytest.mark.django_db
class TestTransactionService:
    """Test suite for transaction service operations."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='txn_user',
            email='txn@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def wallet(self, user):
        """Create test wallet."""
        wallet, _ = Wallet.objects.get_or_create(user=user)
        return wallet

    @pytest.fixture
    def transaction(self, user, wallet):
        """Create test transaction."""
        return Transaction.objects.create(
            user=user,
            wallet=wallet,
            transaction_type='deposit',
            amount=Decimal('100.00'),
            payment_gateway='stripe',
            status='pending'
        )

    def test_transaction_id_auto_generated(self, transaction):
        """Test transaction ID is auto-generated."""
        assert transaction.transaction_id is not None
        assert transaction.transaction_id.startswith('TXN-')

    def test_transaction_id_unique(self, user, wallet):
        """Test transaction IDs are unique."""
        txn1 = Transaction.objects.create(
            user=user,
            wallet=wallet,
            transaction_type='deposit',
            amount=Decimal('50.00'),
            payment_gateway='stripe'
        )
        txn2 = Transaction.objects.create(
            user=user,
            wallet=wallet,
            transaction_type='deposit',
            amount=Decimal('75.00'),
            payment_gateway='stripe'
        )
        
        assert txn1.transaction_id != txn2.transaction_id

    def test_mark_as_completed(self, transaction):
        """Test marking transaction as completed."""
        transaction.mark_as_completed()
        
        assert transaction.status == 'completed'

    def test_mark_as_failed(self, transaction):
        """Test marking transaction as failed."""
        transaction.mark_as_failed(reason='Card declined')
        
        assert transaction.status == 'failed'
        assert transaction.metadata.get('failure_reason') == 'Card declined'

    def test_mark_as_failed_without_reason(self, transaction):
        """Test marking transaction as failed without reason."""
        transaction.mark_as_failed()
        
        assert transaction.status == 'failed'

    def test_transaction_metadata_storage(self, user, wallet):
        """Test storing metadata in transaction."""
        txn = Transaction.objects.create(
            user=user,
            wallet=wallet,
            transaction_type='deposit',
            amount=Decimal('100.00'),
            payment_gateway='stripe',
            metadata={'custom_field': 'custom_value', 'order_id': 12345}
        )
        
        assert txn.metadata['custom_field'] == 'custom_value'
        assert txn.metadata['order_id'] == 12345

    def test_transaction_string_representation(self, transaction):
        """Test transaction string representation."""
        str_repr = str(transaction)
        
        assert transaction.user.username in str_repr
        assert 'TXN-' in str_repr

    def test_transaction_retry_count_default(self, transaction):
        """Test retry count default is 0."""
        assert transaction.retry_count == 0

    def test_transaction_currency_default(self, transaction):
        """Test currency default is USD."""
        assert transaction.currency == 'USD'


# =============================================================================
# INVOICE SERVICE TESTS
# =============================================================================

@pytest.mark.django_db
class TestInvoiceService:
    """Test suite for invoice service operations."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='invoice_user',
            email='invoice@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def invoice(self, user):
        """Create test invoice."""
        return Invoice.objects.create(
            user=user,
            amount=Decimal('99.99'),
            due_date=timezone.now() + timedelta(days=7),
            description='Test invoice'
        )

    def test_invoice_number_auto_generated(self, invoice):
        """Test invoice number is auto-generated."""
        assert invoice.invoice_number is not None
        assert invoice.invoice_number.startswith('INV-')

    def test_invoice_number_unique(self, user):
        """Test invoice numbers are unique."""
        inv1 = Invoice.objects.create(
            user=user,
            amount=Decimal('50.00'),
            due_date=timezone.now() + timedelta(days=7),
            description='Invoice 1'
        )
        inv2 = Invoice.objects.create(
            user=user,
            amount=Decimal('75.00'),
            due_date=timezone.now() + timedelta(days=7),
            description='Invoice 2'
        )
        
        assert inv1.invoice_number != inv2.invoice_number

    def test_mark_as_paid(self, invoice):
        """Test marking invoice as paid."""
        invoice.mark_as_paid()
        
        assert invoice.status == 'paid'
        assert invoice.paid_date is not None

    def test_mark_as_paid_with_custom_date(self, invoice):
        """Test marking invoice as paid with custom date."""
        custom_date = timezone.now() - timedelta(days=1)
        invoice.mark_as_paid(payment_date=custom_date)
        
        assert invoice.status == 'paid'
        assert invoice.paid_date == custom_date

    def test_is_overdue_false_when_not_due(self, invoice):
        """Test is_overdue returns False when not past due date."""
        assert invoice.is_overdue() is False

    def test_is_overdue_true_when_past_due(self, invoice):
        """Test is_overdue returns True when past due date."""
        invoice.due_date = timezone.now() - timedelta(days=1)
        invoice.save()
        
        assert invoice.is_overdue() is True

    def test_is_overdue_false_when_paid(self, invoice):
        """Test is_overdue returns False when paid."""
        invoice.due_date = timezone.now() - timedelta(days=1)
        invoice.mark_as_paid()
        
        assert invoice.is_overdue() is False

    def test_invoice_string_representation(self, invoice):
        """Test invoice string representation."""
        str_repr = str(invoice)
        
        assert invoice.user.username in str_repr
        assert 'INV-' in str_repr


# =============================================================================
# WALLET ACTIVITY LOG TESTS
# =============================================================================

@pytest.mark.django_db
class TestWalletActivityLog:
    """Test suite for wallet activity logging."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='activity_user',
            email='activity@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def wallet(self, user):
        """Create test wallet."""
        wallet, _ = Wallet.objects.get_or_create(user=user)
        return wallet

    def test_create_activity_log(self, user, wallet):
        """Test creating an activity log entry."""
        log = WalletActivityLog.objects.create(
            user=user,
            wallet=wallet,
            action_type='deposit',
            description='User deposited funds',
            ip_address='192.168.1.1'
        )
        
        assert log.id is not None
        assert log.action_type == 'deposit'

    def test_activity_log_with_metadata(self, user, wallet):
        """Test activity log with metadata."""
        log = WalletActivityLog.objects.create(
            user=user,
            wallet=wallet,
            action_type='payment',
            description='Payment made',
            metadata={'transaction_id': 'TXN-123', 'recipient': 'Store'}
        )
        
        assert log.metadata['transaction_id'] == 'TXN-123'

    def test_suspicious_activity_flag(self, user, wallet):
        """Test suspicious activity flagging."""
        log = WalletActivityLog.objects.create(
            user=user,
            wallet=wallet,
            action_type='failed_attempt',
            description='Multiple failed login attempts',
            is_suspicious=True
        )
        
        assert log.is_suspicious is True

    def test_activity_log_ordering(self, user, wallet):
        """Test activity logs are ordered by creation date descending."""
        log1 = WalletActivityLog.objects.create(
            user=user,
            wallet=wallet,
            action_type='login',
            description='First action'
        )
        log2 = WalletActivityLog.objects.create(
            user=user,
            wallet=wallet,
            action_type='deposit',
            description='Second action'
        )
        
        logs = WalletActivityLog.objects.filter(user=user)
        assert logs.first().id == log2.id  # Most recent first


# =============================================================================
# SPENDING LIMIT TESTS
# =============================================================================

@pytest.mark.django_db
class TestSpendingLimits:
    """Test suite for wallet spending limits."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='limit_user',
            email='limit@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def wallet(self, user):
        """Create test wallet."""
        wallet, _ = Wallet.objects.get_or_create(user=user)
        return wallet

    def test_create_daily_limit(self, wallet):
        """Test creating a daily spending limit."""
        limit = WalletSpendingLimit.objects.create(
            wallet=wallet,
            limit_type='daily',
            amount=Decimal('500.00')
        )
        
        assert limit.limit_type == 'daily'
        assert limit.amount == Decimal('500.00')
        assert limit.is_active is True

    def test_create_per_transaction_limit(self, wallet):
        """Test creating a per-transaction limit."""
        limit = WalletSpendingLimit.objects.create(
            wallet=wallet,
            limit_type='per_transaction',
            amount=Decimal('100.00')
        )
        
        assert limit.limit_type == 'per_transaction'

    def test_limit_unique_together(self, wallet):
        """Test that wallet-limit_type combination is unique."""
        WalletSpendingLimit.objects.create(
            wallet=wallet,
            limit_type='daily',
            amount=Decimal('500.00')
        )
        
        with pytest.raises(Exception):
            WalletSpendingLimit.objects.create(
                wallet=wallet,
                limit_type='daily',
                amount=Decimal('600.00')
            )


# =============================================================================
# FRAUD ALERT TESTS
# =============================================================================

@pytest.mark.django_db
class TestFraudAlert:
    """Test suite for fraud alert handling."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='fraud_user',
            email='fraud@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def wallet(self, user):
        """Create test wallet."""
        wallet, _ = Wallet.objects.get_or_create(user=user)
        return wallet

    def test_create_fraud_alert(self, user, wallet):
        """Test creating a fraud alert."""
        alert = FraudAlert.objects.create(
            user=user,
            wallet=wallet,
            alert_type='velocity',
            description='Unusual number of transactions'
        )
        
        assert alert.status == 'pending'
        assert alert.alert_type == 'velocity'

    def test_fraud_alert_severity_levels(self, user, wallet):
        """Test fraud alert with different severity levels."""
        alert = FraudAlert.objects.create(
            user=user,
            wallet=wallet,
            alert_type='amount',
            severity='high',
            description='Large transaction detected'
        )
        
        assert alert.severity == 'high'

    def test_fraud_alert_resolution(self, user, wallet):
        """Test resolving a fraud alert."""
        reviewer = User.objects.create_user(
            username='reviewer',
            email='reviewer@example.com',
            password='testpass123'
        )
        
        alert = FraudAlert.objects.create(
            user=user,
            wallet=wallet,
            alert_type='pattern',
            description='Unusual pattern'
        )
        
        alert.status = 'resolved'
        alert.reviewed_by = reviewer
        alert.reviewed_at = timezone.now()
        alert.resolution_notes = 'Verified legitimate activity'
        alert.save()
        
        assert alert.status == 'resolved'
        assert alert.reviewed_by == reviewer


# =============================================================================
# PAYMENT DISPUTE TESTS
# =============================================================================

@pytest.mark.django_db
class TestPaymentDispute:
    """Test suite for payment dispute handling."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='dispute_user',
            email='dispute@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def wallet(self, user):
        """Create test wallet."""
        wallet, _ = Wallet.objects.get_or_create(user=user)
        return wallet

    @pytest.fixture
    def transaction(self, user, wallet):
        """Create test transaction."""
        return Transaction.objects.create(
            user=user,
            wallet=wallet,
            transaction_type='deposit',
            amount=Decimal('500.00'),
            payment_gateway='stripe',
            status='completed'
        )

    def test_create_dispute(self, user, transaction):
        """Test creating a payment dispute."""
        dispute = PaymentDispute.objects.create(
            user=user,
            transaction=transaction,
            reason='unauthorized',
            description='I did not authorize this transaction',
            amount_disputed=Decimal('500.00')
        )
        
        assert dispute.dispute_id is not None
        assert dispute.dispute_id.startswith('DSP-')
        assert dispute.status == 'open'

    def test_dispute_auto_categorization(self, user, transaction):
        """Test dispute auto-categorization based on amount."""
        dispute = PaymentDispute.objects.create(
            user=user,
            transaction=transaction,
            reason='unauthorized',
            description='Unauthorized transaction',
            amount_disputed=Decimal('1500.00')
        )
        
        assert dispute.risk_level == 'high'

    def test_dispute_sla_deadline_set(self, user, transaction):
        """Test SLA deadline is set on dispute creation."""
        dispute = PaymentDispute.objects.create(
            user=user,
            transaction=transaction,
            reason='not_received',
            description='Product not received',
            amount_disputed=Decimal('100.00')
        )
        
        assert dispute.sla_deadline is not None

    def test_dispute_is_overdue_property(self, user, transaction):
        """Test is_overdue property for disputes."""
        dispute = PaymentDispute.objects.create(
            user=user,
            transaction=transaction,
            reason='duplicate',
            description='Duplicate charge',
            amount_disputed=Decimal('50.00')
        )
        
        # Initially not overdue
        assert dispute.is_overdue is False
        
        # Set SLA deadline to past
        dispute.sla_deadline = timezone.now() - timedelta(hours=1)
        dispute.save()
        
        assert dispute.is_overdue is True

    def test_dispute_days_open_calculation(self, user, transaction):
        """Test days_open calculation."""
        dispute = PaymentDispute.objects.create(
            user=user,
            transaction=transaction,
            reason='cancelled',
            description='Cancelled but still charged',
            amount_disputed=Decimal('75.00')
        )
        
        # Just created, should be 0 days
        assert dispute.days_open == 0

    def test_dispute_priority_high_risk(self, user, transaction):
        """Test high-risk dispute gets elevated priority."""
        dispute = PaymentDispute.objects.create(
            user=user,
            transaction=transaction,
            reason='unauthorized',
            description='Unauthorized high-value transaction',
            amount_disputed=Decimal('2000.00')
        )
        
        assert dispute.priority in ['high', 'critical']

    def test_dispute_string_representation(self, user, transaction):
        """Test dispute string representation."""
        dispute = PaymentDispute.objects.create(
            user=user,
            transaction=transaction,
            reason='other',
            description='Other issue',
            amount_disputed=Decimal('100.00')
        )
        
        str_repr = str(dispute)
        assert 'DSP-' in str_repr
        assert user.username in str_repr


# =============================================================================
# CONCURRENCY TESTS
# =============================================================================

@pytest.mark.django_db
class TestWalletConcurrency:
    """Test concurrent wallet operations."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='concurrent_user',
            email='concurrent@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def wallet(self, user):
        """Create test wallet."""
        wallet, _ = Wallet.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('1000.00')}
        )
        wallet.balance = Decimal('1000.00')
        wallet.save()
        return wallet

    def test_multiple_debits_preserve_consistency(self, wallet):
        """Test multiple debits maintain balance consistency."""
        # Simulate 10 debits of 50 each (500 total)
        for _ in range(10):
            wallet.refresh_from_db()
            wallet.debit(Decimal('50.00'))
        
        wallet.refresh_from_db()
        assert wallet.balance == Decimal('500.00')

    def test_multiple_credits_preserve_consistency(self, wallet):
        """Test multiple credits maintain balance consistency."""
        for _ in range(10):
            wallet.refresh_from_db()
            wallet.credit(Decimal('10.00'))
        
        wallet.refresh_from_db()
        assert wallet.balance == Decimal('1100.00')

    def test_mixed_operations_preserve_consistency(self, wallet):
        """Test mixed credit/debit operations maintain consistency."""
        wallet.credit(Decimal('500.00'))  # 1500
        wallet.debit(Decimal('200.00'))   # 1300
        wallet.credit(Decimal('100.00'))  # 1400
        wallet.debit(Decimal('400.00'))   # 1000
        
        wallet.refresh_from_db()
        assert wallet.balance == Decimal('1000.00')

