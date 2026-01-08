"""
Comprehensive unit tests for TransactionService.
Tests transaction creation, status management, and refunds.
"""
from django.test import TestCase
from django.apps import apps
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()
Wallet = apps.get_model('payments', 'Wallet')
Transaction = apps.get_model('payments', 'Transaction')

from payments.services.transaction_service import TransactionService


class TransactionServiceCreateTests(TestCase):
    """Tests for TransactionService create_transaction method."""

    def setUp(self):
        self.user = User.objects.create_user(username='createuser', password='pass')
        self.wallet, _ = Wallet.objects.get_or_create(user=self.user)

    def test_create_transaction_basic(self):
        """Test basic transaction creation."""
        transaction = TransactionService.create_transaction(
            user=self.user,
            wallet=self.wallet,
            amount=Decimal('50.00'),
            transaction_type='deposit',
            payment_gateway='stripe'
        )
        
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.user, self.user)
        self.assertEqual(transaction.amount, Decimal('50.00'))
        self.assertEqual(transaction.status, 'pending')

    def test_create_transaction_with_gateway_id(self):
        """Test transaction creation with gateway ID."""
        transaction = TransactionService.create_transaction(
            user=self.user,
            wallet=self.wallet,
            amount=Decimal('100.00'),
            transaction_type='deposit',
            payment_gateway='stripe',
            gateway_transaction_id='ch_12345'
        )
        
        self.assertEqual(transaction.gateway_transaction_id, 'ch_12345')

    def test_create_transaction_with_metadata(self):
        """Test transaction creation with metadata."""
        metadata = {'source': 'web', 'campaign': 'promo'}
        transaction = TransactionService.create_transaction(
            user=self.user,
            wallet=self.wallet,
            amount=Decimal('50.00'),
            transaction_type='deposit',
            payment_gateway='stripe',
            metadata=metadata
        )
        
        self.assertEqual(transaction.metadata['source'], 'web')
        self.assertEqual(transaction.metadata['campaign'], 'promo')


class TransactionServiceCompleteDepositTests(TestCase):
    """Tests for TransactionService complete_deposit method."""

    def setUp(self):
        self.user = User.objects.create_user(username='deposituser', password='pass')
        self.wallet, _ = Wallet.objects.get_or_create(user=self.user)

    def test_complete_deposit_success(self):
        """Test successful deposit completion."""
        transaction = TransactionService.create_transaction(
            user=self.user,
            wallet=self.wallet,
            amount=Decimal('100.00'),
            transaction_type='deposit',
            payment_gateway='stripe'
        )
        
        result = TransactionService.complete_deposit(transaction)
        transaction.refresh_from_db()
        self.wallet.refresh_from_db()
        
        self.assertTrue(result)
        self.assertEqual(transaction.status, 'completed')
        self.assertEqual(self.wallet.balance, Decimal('100.00'))

    def test_complete_deposit_non_pending(self):
        """Test complete_deposit on non-pending transaction fails."""
        transaction = TransactionService.create_transaction(
            user=self.user,
            wallet=self.wallet,
            amount=Decimal('100.00'),
            transaction_type='deposit',
            payment_gateway='stripe',
            status='completed'
        )
        
        result = TransactionService.complete_deposit(transaction)
        self.assertFalse(result)

    def test_complete_deposit_wrong_type(self):
        """Test complete_deposit on non-deposit transaction fails."""
        transaction = TransactionService.create_transaction(
            user=self.user,
            wallet=self.wallet,
            amount=Decimal('100.00'),
            transaction_type='refund',
            payment_gateway='stripe'
        )
        
        result = TransactionService.complete_deposit(transaction)
        self.assertFalse(result)


class TransactionServiceFailTests(TestCase):
    """Tests for TransactionService fail_transaction method."""

    def setUp(self):
        self.user = User.objects.create_user(username='failuser', password='pass')
        self.wallet, _ = Wallet.objects.get_or_create(user=self.user)

    def test_fail_transaction(self):
        """Test failing a transaction."""
        transaction = TransactionService.create_transaction(
            user=self.user,
            wallet=self.wallet,
            amount=Decimal('50.00'),
            transaction_type='deposit',
            payment_gateway='stripe'
        )
        
        result = TransactionService.fail_transaction(transaction, 'Card declined')
        transaction.refresh_from_db()
        
        self.assertTrue(result)
        self.assertEqual(transaction.status, 'failed')
        self.assertEqual(transaction.metadata.get('error'), 'Card declined')

    def test_fail_transaction_without_message(self):
        """Test failing a transaction without error message."""
        transaction = TransactionService.create_transaction(
            user=self.user,
            wallet=self.wallet,
            amount=Decimal('50.00'),
            transaction_type='deposit',
            payment_gateway='stripe'
        )
        
        result = TransactionService.fail_transaction(transaction)
        transaction.refresh_from_db()
        
        self.assertTrue(result)
        self.assertEqual(transaction.status, 'failed')


class TransactionServiceCancelTests(TestCase):
    """Tests for TransactionService cancel_transaction method."""

    def setUp(self):
        self.user = User.objects.create_user(username='canceluser', password='pass')
        self.wallet, _ = Wallet.objects.get_or_create(user=self.user)

    def test_cancel_pending_transaction(self):
        """Test cancelling a pending transaction."""
        transaction = TransactionService.create_transaction(
            user=self.user,
            wallet=self.wallet,
            amount=Decimal('50.00'),
            transaction_type='deposit',
            payment_gateway='stripe'
        )
        
        result = TransactionService.cancel_transaction(transaction, 'User requested')
        transaction.refresh_from_db()
        
        self.assertTrue(result)
        self.assertEqual(transaction.status, 'cancelled')
        self.assertEqual(transaction.metadata.get('cancellation_reason'), 'User requested')

    def test_cancel_completed_transaction_fails(self):
        """Test cancelling a completed transaction fails."""
        transaction = TransactionService.create_transaction(
            user=self.user,
            wallet=self.wallet,
            amount=Decimal('50.00'),
            transaction_type='deposit',
            payment_gateway='stripe',
            status='completed'
        )
        
        result = TransactionService.cancel_transaction(transaction)
        self.assertFalse(result)


class TransactionServiceRefundTests(TestCase):
    """Tests for TransactionService process_refund method."""

    def setUp(self):
        self.user = User.objects.create_user(username='refunduser', password='pass')
        self.wallet, _ = Wallet.objects.get_or_create(user=self.user)
        # Add initial balance for refund
        self.wallet.credit(Decimal('100.00'))

    def test_process_full_refund(self):
        """Test processing a full refund."""
        original = TransactionService.create_transaction(
            user=self.user,
            wallet=self.wallet,
            amount=Decimal('50.00'),
            transaction_type='deposit',
            payment_gateway='stripe',
            status='completed'
        )
        
        refund = TransactionService.process_refund(original)
        self.wallet.refresh_from_db()
        
        self.assertIsNotNone(refund)
        self.assertEqual(refund.transaction_type, 'refund')
        self.assertEqual(refund.amount, Decimal('50.00'))
        self.assertEqual(self.wallet.balance, Decimal('50.00'))

    def test_process_partial_refund(self):
        """Test processing a partial refund."""
        original = TransactionService.create_transaction(
            user=self.user,
            wallet=self.wallet,
            amount=Decimal('50.00'),
            transaction_type='deposit',
            payment_gateway='stripe',
            status='completed'
        )
        
        refund = TransactionService.process_refund(original, Decimal('20.00'))
        self.wallet.refresh_from_db()
        
        self.assertIsNotNone(refund)
        self.assertEqual(refund.amount, Decimal('20.00'))
        self.assertEqual(refund.metadata.get('refund_type'), 'partial')

    def test_process_refund_pending_transaction(self):
        """Test refund on pending transaction fails."""
        original = TransactionService.create_transaction(
            user=self.user,
            wallet=self.wallet,
            amount=Decimal('50.00'),
            transaction_type='deposit',
            payment_gateway='stripe'
        )
        
        refund = TransactionService.process_refund(original)
        self.assertIsNone(refund)

    def test_process_refund_exceeds_amount(self):
        """Test refund exceeding original amount fails."""
        original = TransactionService.create_transaction(
            user=self.user,
            wallet=self.wallet,
            amount=Decimal('50.00'),
            transaction_type='deposit',
            payment_gateway='stripe',
            status='completed'
        )
        
        refund = TransactionService.process_refund(original, Decimal('100.00'))
        self.assertIsNone(refund)


class TransactionServiceGatewayIdTests(TestCase):
    """Tests for TransactionService gateway ID update method."""

    def setUp(self):
        self.user = User.objects.create_user(username='gatewayuser', password='pass')
        self.wallet, _ = Wallet.objects.get_or_create(user=self.user)

    def test_update_gateway_transaction_id(self):
        """Test updating gateway transaction ID."""
        transaction = TransactionService.create_transaction(
            user=self.user,
            wallet=self.wallet,
            amount=Decimal('50.00'),
            transaction_type='deposit',
            payment_gateway='stripe'
        )
        
        result = TransactionService.update_gateway_transaction_id(
            transaction,
            'ch_new_id_123'
        )
        transaction.refresh_from_db()
        
        self.assertTrue(result)
        self.assertEqual(transaction.gateway_transaction_id, 'ch_new_id_123')


class TransactionServiceRetryTests(TestCase):
    """Tests for TransactionService retry tracking method."""

    def setUp(self):
        self.user = User.objects.create_user(username='retryuser', password='pass')
        self.wallet, _ = Wallet.objects.get_or_create(user=self.user)

    def test_increment_retry_count(self):
        """Test incrementing retry count."""
        transaction = TransactionService.create_transaction(
            user=self.user,
            wallet=self.wallet,
            amount=Decimal('50.00'),
            transaction_type='deposit',
            payment_gateway='stripe'
        )
        
        count = TransactionService.increment_retry_count(transaction)
        transaction.refresh_from_db()
        
        self.assertEqual(count, 1)
        self.assertEqual(transaction.retry_count, 1)

    def test_multiple_retry_increments(self):
        """Test multiple retry increments."""
        transaction = TransactionService.create_transaction(
            user=self.user,
            wallet=self.wallet,
            amount=Decimal('50.00'),
            transaction_type='deposit',
            payment_gateway='stripe'
        )
        
        TransactionService.increment_retry_count(transaction)
        TransactionService.increment_retry_count(transaction)
        count = TransactionService.increment_retry_count(transaction)
        
        self.assertEqual(count, 3)

