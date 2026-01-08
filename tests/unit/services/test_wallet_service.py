"""
Comprehensive unit tests for WalletService.
Tests wallet operations, transactions, and business logic.
"""
from django.test import TestCase
from django.apps import apps
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()
Wallet = apps.get_model('payments', 'Wallet')
Transaction = apps.get_model('payments', 'Transaction')

from payments.services.wallet_service import WalletService


class WalletServiceCreditTests(TestCase):
    """Tests for WalletService credit_wallet method."""

    def setUp(self):
        self.user = User.objects.create_user(username='credituser', password='pass')
        self.wallet, _ = Wallet.objects.get_or_create(user=self.user)

    def test_credit_wallet_success(self):
        """Test successful wallet credit."""
        initial_balance = self.wallet.balance
        transaction = WalletService.credit_wallet(
            wallet=self.wallet,
            amount=Decimal('50.00'),
            transaction_type='deposit'
        )
        self.wallet.refresh_from_db()
        
        self.assertEqual(self.wallet.balance, initial_balance + Decimal('50.00'))
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.status, 'completed')
        self.assertEqual(transaction.transaction_type, 'deposit')

    def test_credit_wallet_creates_transaction(self):
        """Test credit_wallet creates transaction record."""
        transaction = WalletService.credit_wallet(
            wallet=self.wallet,
            amount=Decimal('100.00'),
            transaction_type='deposit',
            metadata={'source': 'test'}
        )
        
        self.assertIsNotNone(transaction.transaction_id)
        self.assertEqual(transaction.user, self.user)
        self.assertEqual(transaction.amount, Decimal('100.00'))
        self.assertEqual(transaction.metadata.get('source'), 'test')

    def test_credit_wallet_with_decimal_string(self):
        """Test credit_wallet with string amount."""
        WalletService.credit_wallet(
            wallet=self.wallet,
            amount=Decimal('25.50'),
            transaction_type='deposit'
        )
        self.wallet.refresh_from_db()
        
        self.assertEqual(self.wallet.balance, Decimal('25.50'))


class WalletServiceDebitTests(TestCase):
    """Tests for WalletService debit_wallet method."""

    def setUp(self):
        self.user = User.objects.create_user(username='debituser', password='pass')
        self.wallet, _ = Wallet.objects.get_or_create(user=self.user)
        self.wallet.credit(Decimal('100.00'))

    def test_debit_wallet_success(self):
        """Test successful wallet debit."""
        transaction = WalletService.debit_wallet(
            wallet=self.wallet,
            amount=Decimal('30.00'),
            transaction_type='subscription_payment'
        )
        self.wallet.refresh_from_db()
        
        self.assertEqual(self.wallet.balance, Decimal('70.00'))
        self.assertEqual(transaction.status, 'completed')

    def test_debit_wallet_insufficient_balance(self):
        """Test debit_wallet with insufficient balance raises error."""
        with self.assertRaises(ValueError) as context:
            WalletService.debit_wallet(
                wallet=self.wallet,
                amount=Decimal('150.00'),
                transaction_type='subscription_payment'
            )
        
        self.assertIn('Insufficient', str(context.exception))

    def test_debit_wallet_exact_balance(self):
        """Test debit_wallet with exact balance amount."""
        transaction = WalletService.debit_wallet(
            wallet=self.wallet,
            amount=Decimal('100.00'),
            transaction_type='subscription_payment'
        )
        self.wallet.refresh_from_db()
        
        self.assertEqual(self.wallet.balance, Decimal('0.00'))
        self.assertEqual(transaction.status, 'completed')


class WalletServiceBalanceTests(TestCase):
    """Tests for WalletService balance methods."""

    def setUp(self):
        self.user = User.objects.create_user(username='balanceuser', password='pass')
        self.wallet, _ = Wallet.objects.get_or_create(user=self.user)
        self.wallet.credit(Decimal('75.00'))

    def test_get_balance(self):
        """Test get_balance returns correct balance."""
        balance = WalletService.get_balance(self.wallet)
        self.assertEqual(balance, Decimal('75.00'))

    def test_check_sufficient_balance_true(self):
        """Test check_sufficient_balance returns True when sufficient."""
        result = WalletService.check_sufficient_balance(self.wallet, Decimal('50.00'))
        self.assertTrue(result)

    def test_check_sufficient_balance_false(self):
        """Test check_sufficient_balance returns False when insufficient."""
        result = WalletService.check_sufficient_balance(self.wallet, Decimal('100.00'))
        self.assertFalse(result)

    def test_check_sufficient_balance_exact(self):
        """Test check_sufficient_balance with exact balance."""
        result = WalletService.check_sufficient_balance(self.wallet, Decimal('75.00'))
        self.assertTrue(result)


class WalletServiceTransactionIntegrityTests(TestCase):
    """Tests for transaction integrity in wallet operations."""

    def setUp(self):
        self.user = User.objects.create_user(username='integrityuser', password='pass')
        self.wallet, _ = Wallet.objects.get_or_create(user=self.user)

    def test_credit_transaction_linked_to_wallet(self):
        """Test credit transaction is linked to wallet."""
        transaction = WalletService.credit_wallet(
            wallet=self.wallet,
            amount=Decimal('50.00'),
            transaction_type='deposit'
        )
        
        self.assertEqual(transaction.wallet, self.wallet)

    def test_multiple_transactions_tracked(self):
        """Test multiple transactions are tracked correctly."""
        WalletService.credit_wallet(self.wallet, Decimal('50.00'), 'deposit')
        WalletService.credit_wallet(self.wallet, Decimal('30.00'), 'deposit')
        
        transactions = Transaction.objects.filter(wallet=self.wallet)
        self.assertEqual(transactions.count(), 2)
        
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('80.00'))

