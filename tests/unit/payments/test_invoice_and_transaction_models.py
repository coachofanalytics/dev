"""
Comprehensive unit tests for Invoice and Transaction models.
Tests invoice generation, payment tracking, transaction management, and edge cases.
"""
from django.test import TestCase
from django.apps import apps
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import timedelta

User = get_user_model()
Invoice = apps.get_model('payments', 'Invoice')
Transaction = apps.get_model('payments', 'Transaction')
Wallet = apps.get_model('payments', 'Wallet')
SubscriptionPlan = apps.get_model('payments', 'SubscriptionPlan')
UserSubscription = apps.get_model('payments', 'UserSubscription')


class InvoiceModelBasicTests(TestCase):
    """Basic tests for Invoice model creation and representation."""

    def setUp(self):
        self.user = User.objects.create_user(username='invoiceuser', password='pass')
        self.plan = SubscriptionPlan.objects.create(
            name='Basic',
            slug='basic',
            description='Basic plan',
            price=Decimal('10.00'),
            duration_days=30
        )
        self.subscription = UserSubscription.objects.create(user=self.user, plan=self.plan)

    def test_invoice_creation(self):
        """Test creating an invoice."""
        invoice = Invoice.objects.create(
            user=self.user,
            subscription=self.subscription,
            amount=Decimal('10.00'),
            due_date=timezone.now() + timedelta(days=7),
            description='Subscription payment'
        )
        self.assertEqual(invoice.user, self.user)
        self.assertEqual(invoice.amount, Decimal('10.00'))

    def test_invoice_auto_number_generation(self):
        """Test invoice number is auto-generated."""
        invoice = Invoice.objects.create(
            user=self.user,
            subscription=self.subscription,
            amount=Decimal('10.00'),
            due_date=timezone.now() + timedelta(days=7),
            description='Test invoice'
        )
        self.assertTrue(invoice.invoice_number.startswith('INV-'))

    def test_invoice_str_representation(self):
        """Test invoice string representation."""
        invoice = Invoice.objects.create(
            user=self.user,
            subscription=self.subscription,
            amount=Decimal('10.00'),
            due_date=timezone.now() + timedelta(days=7),
            description='Test invoice'
        )
        expected = f'{invoice.invoice_number} - {self.user.username} - $10.00'
        self.assertEqual(str(invoice), expected)


class InvoiceStatusTests(TestCase):
    """Tests for invoice status management."""

    def setUp(self):
        self.user = User.objects.create_user(username='statususer', password='pass')
        self.plan = SubscriptionPlan.objects.create(
            name='Basic',
            slug='basic',
            description='Basic plan',
            price=Decimal('10.00'),
            duration_days=30
        )
        self.subscription = UserSubscription.objects.create(user=self.user, plan=self.plan)

    def test_default_status_pending(self):
        """Test default invoice status is pending."""
        invoice = Invoice.objects.create(
            user=self.user,
            subscription=self.subscription,
            amount=Decimal('10.00'),
            due_date=timezone.now() + timedelta(days=7),
            description='Test invoice'
        )
        self.assertEqual(invoice.status, 'pending')

    def test_mark_as_paid(self):
        """Test marking invoice as paid."""
        invoice = Invoice.objects.create(
            user=self.user,
            subscription=self.subscription,
            amount=Decimal('10.00'),
            due_date=timezone.now() + timedelta(days=7),
            description='Test invoice'
        )
        invoice.mark_as_paid()
        
        self.assertEqual(invoice.status, 'paid')
        self.assertIsNotNone(invoice.paid_date)

    def test_mark_as_paid_with_custom_date(self):
        """Test marking invoice as paid with custom date."""
        invoice = Invoice.objects.create(
            user=self.user,
            subscription=self.subscription,
            amount=Decimal('10.00'),
            due_date=timezone.now() + timedelta(days=7),
            description='Test invoice'
        )
        custom_date = timezone.now() - timedelta(days=1)
        invoice.mark_as_paid(payment_date=custom_date)
        
        self.assertEqual(invoice.paid_date, custom_date)


class InvoiceOverdueTests(TestCase):
    """Tests for invoice overdue detection."""

    def setUp(self):
        self.user = User.objects.create_user(username='overdueuser', password='pass')
        self.plan = SubscriptionPlan.objects.create(
            name='Basic',
            slug='basic',
            description='Basic plan',
            price=Decimal('10.00'),
            duration_days=30
        )
        self.subscription = UserSubscription.objects.create(user=self.user, plan=self.plan)

    def test_is_overdue_false_future_due_date(self):
        """Test is_overdue returns False for future due date."""
        invoice = Invoice.objects.create(
            user=self.user,
            subscription=self.subscription,
            amount=Decimal('10.00'),
            due_date=timezone.now() + timedelta(days=7),
            description='Test invoice'
        )
        self.assertFalse(invoice.is_overdue())

    def test_is_overdue_true_past_due_date(self):
        """Test is_overdue returns True for past due date."""
        invoice = Invoice.objects.create(
            user=self.user,
            subscription=self.subscription,
            amount=Decimal('10.00'),
            due_date=timezone.now() - timedelta(days=1),
            description='Test invoice'
        )
        self.assertTrue(invoice.is_overdue())

    def test_is_overdue_false_for_paid_invoice(self):
        """Test is_overdue returns False for paid invoice."""
        invoice = Invoice.objects.create(
            user=self.user,
            subscription=self.subscription,
            amount=Decimal('10.00'),
            due_date=timezone.now() - timedelta(days=1),
            description='Test invoice',
            status='paid'
        )
        self.assertFalse(invoice.is_overdue())


class InvoiceValidationTests(TestCase):
    """Tests for invoice field validations."""

    def setUp(self):
        self.user = User.objects.create_user(username='validateuser', password='pass')

    def test_amount_min_value(self):
        """Test amount minimum value validator."""
        invoice = Invoice(
            user=self.user,
            amount=Decimal('0.00'),
            due_date=timezone.now() + timedelta(days=7),
            description='Test'
        )
        invoice.full_clean()  # Should not raise

    def test_amount_negative_raises_error(self):
        """Test negative amount raises validation error."""
        invoice = Invoice(
            user=self.user,
            amount=Decimal('-10.00'),
            due_date=timezone.now() + timedelta(days=7),
            description='Test'
        )
        with self.assertRaises(ValidationError):
            invoice.full_clean()

    def test_unique_invoice_number(self):
        """Test invoice number must be unique."""
        from django.db import IntegrityError
        invoice1 = Invoice.objects.create(
            user=self.user,
            amount=Decimal('10.00'),
            due_date=timezone.now() + timedelta(days=7),
            description='Invoice 1'
        )
        
        # Try to create another invoice with same number
        with self.assertRaises(IntegrityError):
            Invoice.objects.create(
                user=self.user,
                invoice_number=invoice1.invoice_number,
                amount=Decimal('20.00'),
                due_date=timezone.now() + timedelta(days=7),
                description='Invoice 2'
            )


class TransactionModelBasicTests(TestCase):
    """Basic tests for Transaction model."""

    def setUp(self):
        self.user = User.objects.create_user(username='txnuser', password='pass')
        self.wallet, _ = Wallet.objects.get_or_create(user=self.user)

    def test_transaction_creation(self):
        """Test creating a transaction."""
        txn = Transaction.objects.create(
            user=self.user,
            wallet=self.wallet,
            transaction_type='deposit',
            amount=Decimal('50.00'),
            payment_gateway='stripe'
        )
        self.assertEqual(txn.user, self.user)
        self.assertEqual(txn.amount, Decimal('50.00'))

    def test_transaction_id_auto_generated(self):
        """Test transaction ID is auto-generated."""
        txn = Transaction.objects.create(
            user=self.user,
            wallet=self.wallet,
            transaction_type='deposit',
            amount=Decimal('50.00'),
            payment_gateway='stripe'
        )
        self.assertTrue(txn.transaction_id.startswith('TXN-'))

    def test_transaction_str_representation(self):
        """Test transaction string representation."""
        txn = Transaction.objects.create(
            user=self.user,
            wallet=self.wallet,
            transaction_type='deposit',
            amount=Decimal('50.00'),
            payment_gateway='stripe'
        )
        expected = f'{txn.transaction_id} - {self.user.username} - $50.00'
        self.assertEqual(str(txn), expected)


class TransactionStatusTests(TestCase):
    """Tests for transaction status management."""

    def setUp(self):
        self.user = User.objects.create_user(username='statususer', password='pass')
        self.wallet, _ = Wallet.objects.get_or_create(user=self.user)

    def test_default_status_pending(self):
        """Test default transaction status is pending."""
        txn = Transaction.objects.create(
            user=self.user,
            wallet=self.wallet,
            transaction_type='deposit',
            amount=Decimal('50.00'),
            payment_gateway='stripe'
        )
        self.assertEqual(txn.status, 'pending')

    def test_mark_as_completed(self):
        """Test marking transaction as completed."""
        txn = Transaction.objects.create(
            user=self.user,
            wallet=self.wallet,
            transaction_type='deposit',
            amount=Decimal('50.00'),
            payment_gateway='stripe'
        )
        txn.mark_as_completed()
        
        self.assertEqual(txn.status, 'completed')

    def test_mark_as_failed(self):
        """Test marking transaction as failed."""
        txn = Transaction.objects.create(
            user=self.user,
            wallet=self.wallet,
            transaction_type='deposit',
            amount=Decimal('50.00'),
            payment_gateway='stripe'
        )
        txn.mark_as_failed(reason='Card declined')
        
        self.assertEqual(txn.status, 'failed')
        self.assertEqual(txn.metadata.get('failure_reason'), 'Card declined')


class TransactionTypeTests(TestCase):
    """Tests for different transaction types."""

    def setUp(self):
        self.user = User.objects.create_user(username='typeuser', password='pass')
        self.wallet, _ = Wallet.objects.get_or_create(user=self.user)

    def test_deposit_transaction(self):
        """Test deposit transaction type."""
        txn = Transaction.objects.create(
            user=self.user,
            wallet=self.wallet,
            transaction_type='deposit',
            amount=Decimal('100.00'),
            payment_gateway='stripe'
        )
        self.assertEqual(txn.transaction_type, 'deposit')

    def test_subscription_payment_transaction(self):
        """Test subscription payment transaction type."""
        txn = Transaction.objects.create(
            user=self.user,
            wallet=self.wallet,
            transaction_type='subscription_payment',
            amount=Decimal('29.99'),
            payment_gateway='wallet'
        )
        self.assertEqual(txn.transaction_type, 'subscription_payment')

    def test_invoice_payment_transaction(self):
        """Test invoice payment transaction type."""
        txn = Transaction.objects.create(
            user=self.user,
            wallet=self.wallet,
            transaction_type='invoice_payment',
            amount=Decimal('150.00'),
            payment_gateway='mpesa'
        )
        self.assertEqual(txn.transaction_type, 'invoice_payment')

    def test_refund_transaction(self):
        """Test refund transaction type."""
        txn = Transaction.objects.create(
            user=self.user,
            wallet=self.wallet,
            transaction_type='refund',
            amount=Decimal('50.00'),
            payment_gateway='stripe'
        )
        self.assertEqual(txn.transaction_type, 'refund')

    def test_adjustment_transaction(self):
        """Test manual adjustment transaction type."""
        txn = Transaction.objects.create(
            user=self.user,
            wallet=self.wallet,
            transaction_type='adjustment',
            amount=Decimal('10.00'),
            payment_gateway='manual'
        )
        self.assertEqual(txn.transaction_type, 'adjustment')


class TransactionPaymentGatewayTests(TestCase):
    """Tests for different payment gateways."""

    def setUp(self):
        self.user = User.objects.create_user(username='gatewayuser', password='pass')
        self.wallet, _ = Wallet.objects.get_or_create(user=self.user)

    def test_wallet_gateway(self):
        """Test wallet payment gateway."""
        txn = Transaction.objects.create(
            user=self.user,
            wallet=self.wallet,
            transaction_type='deposit',
            amount=Decimal('50.00'),
            payment_gateway='wallet'
        )
        self.assertEqual(txn.payment_gateway, 'wallet')

    def test_stripe_gateway(self):
        """Test Stripe payment gateway."""
        txn = Transaction.objects.create(
            user=self.user,
            wallet=self.wallet,
            transaction_type='deposit',
            amount=Decimal('50.00'),
            payment_gateway='stripe',
            gateway_transaction_id='ch_1234567890'
        )
        self.assertEqual(txn.payment_gateway, 'stripe')
        self.assertEqual(txn.gateway_transaction_id, 'ch_1234567890')

    def test_mpesa_gateway(self):
        """Test M-Pesa payment gateway."""
        txn = Transaction.objects.create(
            user=self.user,
            wallet=self.wallet,
            transaction_type='deposit',
            amount=Decimal('50.00'),
            payment_gateway='mpesa'
        )
        self.assertEqual(txn.payment_gateway, 'mpesa')

    def test_paypal_gateway(self):
        """Test PayPal payment gateway."""
        txn = Transaction.objects.create(
            user=self.user,
            wallet=self.wallet,
            transaction_type='deposit',
            amount=Decimal('50.00'),
            payment_gateway='paypal'
        )
        self.assertEqual(txn.payment_gateway, 'paypal')


class TransactionMetadataTests(TestCase):
    """Tests for transaction metadata handling."""

    def setUp(self):
        self.user = User.objects.create_user(username='metauser', password='pass')
        self.wallet, _ = Wallet.objects.get_or_create(user=self.user)

    def test_default_metadata_empty_dict(self):
        """Test default metadata is empty dict."""
        txn = Transaction.objects.create(
            user=self.user,
            wallet=self.wallet,
            transaction_type='deposit',
            amount=Decimal('50.00'),
            payment_gateway='stripe'
        )
        self.assertEqual(txn.metadata, {})

    def test_metadata_with_data(self):
        """Test metadata with custom data."""
        metadata = {
            'source': 'web',
            'ip_address': '192.168.1.1',
            'notes': 'Manual deposit'
        }
        txn = Transaction.objects.create(
            user=self.user,
            wallet=self.wallet,
            transaction_type='deposit',
            amount=Decimal('50.00'),
            payment_gateway='stripe',
            metadata=metadata
        )
        self.assertEqual(txn.metadata['source'], 'web')
        self.assertEqual(txn.metadata['ip_address'], '192.168.1.1')


class TransactionValidationTests(TestCase):
    """Tests for transaction field validations."""

    def setUp(self):
        self.user = User.objects.create_user(username='validateuser', password='pass')
        self.wallet, _ = Wallet.objects.get_or_create(user=self.user)

    def test_amount_min_value(self):
        """Test amount minimum value validator (0.01)."""
        txn = Transaction(
            user=self.user,
            wallet=self.wallet,
            transaction_type='deposit',
            amount=Decimal('0.01'),
            payment_gateway='stripe'
        )
        txn.full_clean()  # Should not raise

    def test_amount_below_minimum_raises_error(self):
        """Test amount below minimum raises validation error."""
        txn = Transaction(
            user=self.user,
            wallet=self.wallet,
            transaction_type='deposit',
            amount=Decimal('0.00'),
            payment_gateway='stripe'
        )
        with self.assertRaises(ValidationError):
            txn.full_clean()

    def test_unique_transaction_id(self):
        """Test transaction ID must be unique."""
        from django.db import IntegrityError
        txn1 = Transaction.objects.create(
            user=self.user,
            wallet=self.wallet,
            transaction_type='deposit',
            amount=Decimal('50.00'),
            payment_gateway='stripe'
        )
        
        with self.assertRaises(IntegrityError):
            Transaction.objects.create(
                user=self.user,
                wallet=self.wallet,
                transaction_id=txn1.transaction_id,
                transaction_type='deposit',
                amount=Decimal('100.00'),
                payment_gateway='stripe'
            )


class TransactionRetryTests(TestCase):
    """Tests for transaction retry tracking."""

    def setUp(self):
        self.user = User.objects.create_user(username='retryuser', password='pass')
        self.wallet, _ = Wallet.objects.get_or_create(user=self.user)

    def test_default_retry_count_zero(self):
        """Test default retry count is zero."""
        txn = Transaction.objects.create(
            user=self.user,
            wallet=self.wallet,
            transaction_type='deposit',
            amount=Decimal('50.00'),
            payment_gateway='stripe'
        )
        self.assertEqual(txn.retry_count, 0)

    def test_increment_retry_count(self):
        """Test incrementing retry count."""
        txn = Transaction.objects.create(
            user=self.user,
            wallet=self.wallet,
            transaction_type='deposit',
            amount=Decimal('50.00'),
            payment_gateway='stripe'
        )
        txn.retry_count = 1
        txn.save()
        txn.refresh_from_db()
        
        self.assertEqual(txn.retry_count, 1)
