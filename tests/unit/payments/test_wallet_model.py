"""
Comprehensive unit tests for Wallet model.
Tests wallet creation, credit, debit, balance checks, and edge cases.
"""
from django.test import TestCase
from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from decimal import Decimal

User = get_user_model()
Wallet = apps.get_model('payments', 'Wallet')


class WalletModelBasicTests(TestCase):
    """Basic tests for Wallet model creation and representation."""

    def setUp(self):
        self.user = User.objects.create_user(username='walletuser', password='pass')
        self.wallet, _ = Wallet.objects.get_or_create(user=self.user)

    def test_wallet_creation(self):
        """Test wallet is created for user."""
        self.assertIsNotNone(self.wallet)
        self.assertEqual(self.wallet.user, self.user)

    def test_wallet_str_representation(self):
        """Test wallet string representation."""
        expected = f"{self.user.username}'s Wallet - ${self.wallet.balance}"
        self.assertEqual(str(self.wallet), expected)

    def test_default_values(self):
        """Test wallet default values."""
        self.assertEqual(self.wallet.balance, Decimal('0.00'))
        self.assertEqual(self.wallet.currency, 'USD')
        self.assertTrue(self.wallet.is_active)


class WalletCreditTests(TestCase):
    """Tests for wallet credit operations."""

    def setUp(self):
        self.user = User.objects.create_user(username='credituser', password='pass')
        self.wallet, _ = Wallet.objects.get_or_create(user=self.user)

    def test_credit_positive_amount(self):
        """Test crediting positive amount increases balance."""
        result = self.wallet.credit(10)
        self.wallet.refresh_from_db()
        self.assertTrue(result)
        self.assertEqual(self.wallet.balance, Decimal('10.00'))

    def test_credit_decimal_amount(self):
        """Test crediting decimal amount."""
        result = self.wallet.credit(10.50)
        self.wallet.refresh_from_db()
        self.assertTrue(result)
        self.assertEqual(self.wallet.balance, Decimal('10.50'))

    def test_credit_decimal_string_amount(self):
        """Test crediting with Decimal amount from string (should be converted)."""
        result = self.wallet.credit(Decimal('25.75'))
        self.wallet.refresh_from_db()
        self.assertTrue(result)
        self.assertEqual(self.wallet.balance, Decimal('25.75'))

    def test_credit_zero_amount_fails(self):
        """Test crediting zero amount fails."""
        result = self.wallet.credit(0)
        self.assertFalse(result)
        self.assertEqual(self.wallet.balance, Decimal('0.00'))

    def test_credit_negative_amount_fails(self):
        """Test crediting negative amount fails."""
        result = self.wallet.credit(-10)
        self.assertFalse(result)
        self.assertEqual(self.wallet.balance, Decimal('0.00'))

    def test_multiple_credits(self):
        """Test multiple credit operations accumulate."""
        self.wallet.credit(10)
        self.wallet.credit(20)
        self.wallet.credit(5.50)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('35.50'))

    def test_credit_large_amount(self):
        """Test crediting large amount."""
        result = self.wallet.credit(999999.99)
        self.wallet.refresh_from_db()
        self.assertTrue(result)
        self.assertEqual(self.wallet.balance, Decimal('999999.99'))


class WalletDebitTests(TestCase):
    """Tests for wallet debit operations."""

    def setUp(self):
        self.user = User.objects.create_user(username='debituser', password='pass')
        self.wallet, _ = Wallet.objects.get_or_create(user=self.user)
        self.wallet.credit(100)  # Setup initial balance

    def test_debit_with_sufficient_balance(self):
        """Test debiting with sufficient balance."""
        result = self.wallet.debit(50)
        self.wallet.refresh_from_db()
        self.assertTrue(result)
        self.assertEqual(self.wallet.balance, Decimal('50.00'))

    def test_debit_exact_balance(self):
        """Test debiting exact balance amount."""
        result = self.wallet.debit(100)
        self.wallet.refresh_from_db()
        self.assertTrue(result)
        self.assertEqual(self.wallet.balance, Decimal('0.00'))

    def test_debit_insufficient_balance(self):
        """Test debiting more than balance fails."""
        result = self.wallet.debit(150)
        self.assertFalse(result)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('100.00'))

    def test_debit_zero_amount_fails(self):
        """Test debiting zero amount fails."""
        result = self.wallet.debit(0)
        self.assertFalse(result)

    def test_debit_negative_amount_fails(self):
        """Test debiting negative amount fails."""
        result = self.wallet.debit(-10)
        self.assertFalse(result)

    def test_multiple_debits(self):
        """Test multiple debit operations."""
        self.wallet.debit(20)
        self.wallet.debit(30)
        self.wallet.debit(10)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('40.00'))


class WalletBalanceCheckTests(TestCase):
    """Tests for wallet balance checking methods."""

    def setUp(self):
        self.user = User.objects.create_user(username='balanceuser', password='pass')
        self.wallet, _ = Wallet.objects.get_or_create(user=self.user)
        self.wallet.credit(50)

    def test_has_sufficient_balance_true(self):
        """Test has_sufficient_balance returns True when sufficient."""
        self.assertTrue(self.wallet.has_sufficient_balance(50))
        self.assertTrue(self.wallet.has_sufficient_balance(25))
        self.assertTrue(self.wallet.has_sufficient_balance(0))

    def test_has_sufficient_balance_false(self):
        """Test has_sufficient_balance returns False when insufficient."""
        self.assertFalse(self.wallet.has_sufficient_balance(51))
        self.assertFalse(self.wallet.has_sufficient_balance(100))

    def test_has_sufficient_balance_with_string_amount(self):
        """Test has_sufficient_balance with string amount."""
        self.assertTrue(self.wallet.has_sufficient_balance('50'))
        self.assertTrue(self.wallet.has_sufficient_balance('25.50'))

    def test_has_sufficient_balance_exact_amount(self):
        """Test has_sufficient_balance with exact balance."""
        self.assertTrue(self.wallet.has_sufficient_balance(50))


class WalletEdgeCaseTests(TestCase):
    """Tests for wallet edge cases and boundary conditions."""

    def setUp(self):
        self.user = User.objects.create_user(username='edgeuser', password='pass')
        self.wallet, _ = Wallet.objects.get_or_create(user=self.user)

    def test_wallet_one_to_one_constraint(self):
        """Test only one wallet per user."""
        with self.assertRaises(IntegrityError):
            Wallet.objects.create(user=self.user)

    def test_balance_precision(self):
        """Test balance precision to 2 decimal places."""
        self.wallet.credit(10.999)
        self.wallet.refresh_from_db()
        # Should round or truncate to 2 decimal places
        self.assertLessEqual(len(str(self.wallet.balance).split('.')[-1]), 2)

    def test_minimum_balance_validator(self):
        """Test balance cannot go below zero (model level)."""
        self.wallet.balance = Decimal('-1.00')
        with self.assertRaises(ValidationError):
            self.wallet.full_clean()

    def test_credit_very_small_amount(self):
        """Test crediting very small amount."""
        result = self.wallet.credit(0.01)
        self.wallet.refresh_from_db()
        self.assertTrue(result)
        self.assertEqual(self.wallet.balance, Decimal('0.01'))

    def test_debit_after_credit(self):
        """Test debit after credit operations."""
        self.wallet.credit(100)
        self.wallet.debit(25)
        self.wallet.credit(10)
        self.wallet.debit(35)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('50.00'))


class WalletActiveStatusTests(TestCase):
    """Tests for wallet is_active field behavior."""

    def setUp(self):
        self.user = User.objects.create_user(username='activeuser', password='pass')
        self.wallet, _ = Wallet.objects.get_or_create(user=self.user)

    def test_default_is_active(self):
        """Test wallet is active by default."""
        self.assertTrue(self.wallet.is_active)

    def test_deactivate_wallet(self):
        """Test deactivating wallet."""
        self.wallet.is_active = False
        self.wallet.save()
        self.wallet.refresh_from_db()
        self.assertFalse(self.wallet.is_active)


class WalletCurrencyTests(TestCase):
    """Tests for wallet currency field."""

    def setUp(self):
        self.user = User.objects.create_user(username='currencyuser', password='pass')
        self.wallet, _ = Wallet.objects.get_or_create(user=self.user)

    def test_default_currency_usd(self):
        """Test default currency is USD."""
        self.assertEqual(self.wallet.currency, 'USD')

    def test_change_currency(self):
        """Test changing wallet currency."""
        self.wallet.currency = 'EUR'
        self.wallet.save()
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.currency, 'EUR')


class WalletTimestampTests(TestCase):
    """Tests for wallet timestamp fields."""

    def setUp(self):
        self.user = User.objects.create_user(username='timestampuser', password='pass')
        # Get existing wallet created by signal or create one
        self.wallet, _ = Wallet.objects.get_or_create(user=self.user)

    def test_created_at_auto_set(self):
        """Test created_at is automatically set."""
        self.assertIsNotNone(self.wallet.created_at)

    def test_updated_at_changes_on_save(self):
        """Test updated_at changes on save."""
        original_updated = self.wallet.updated_at
        
        self.wallet.credit(10)
        self.wallet.refresh_from_db()
        
        self.assertGreaterEqual(self.wallet.updated_at, original_updated)


class WalletUserDeleteTests(TestCase):
    """Tests for cascade delete behavior."""

    def test_wallet_deleted_when_user_deleted(self):
        """Test wallet is deleted when user is deleted."""
        user = User.objects.create_user(username='deleteuser', password='pass')
        Wallet.objects.get_or_create(user=user)
        
        user_id = user.id
        user.delete()
        
        self.assertFalse(Wallet.objects.filter(user_id=user_id).exists())
