"""
Regression Tests for Wallet Operations

These tests verify that existing wallet functionality remains intact
after code changes. Tests are designed to FIND and REPORT issues.

Tested Features:
- Wallet creation and initialization
- Credit operations
- Debit operations
- Balance calculations
- Insufficient balance handling
- Currency support

Author: Fadhiri
Date: January 2026
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from decimal import Decimal, InvalidOperation
from django.core.exceptions import ValidationError

import accounts.models as accounts_models
import payments.signals as payments_signals
from payments.models import Wallet, Transaction


class WalletCreationRegressionTests(TestCase):
    """
    Regression tests for wallet creation.
    
    These tests verify that:
    - Wallets can be created with default values
    - Wallet-User relationship works
    - Currency defaults are correct
    """
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            post_save.disconnect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
        try:
            post_save.disconnect(payments_signals.create_user_wallet, sender=User)
        except Exception:
            pass
        try:
            post_save.disconnect(payments_signals.save_user_wallet, sender=User)
        except Exception:
            pass
    
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        try:
            post_save.connect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
        try:
            post_save.connect(payments_signals.create_user_wallet, sender=User)
        except Exception:
            pass
        try:
            post_save.connect(payments_signals.save_user_wallet, sender=User)
        except Exception:
            pass
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='wallet_user',
            email='wallet@test.com',
            password='WalletPass123!'
        )
    
    def test_wallet_creation_with_defaults(self):
        """
        REGRESSION TEST: Wallet should be created with correct defaults.
        
        Verifies: Default balance is 0.00 and currency is USD.
        Reports: Issues with default values.
        """
        wallet = Wallet.objects.create(user=self.user)
        self.assertEqual(
            wallet.balance, 
            Decimal('0.00'),
            "REGRESSION ISSUE: Default balance is not 0.00"
        )
        self.assertEqual(
            wallet.currency, 
            'USD',
            "REGRESSION ISSUE: Default currency is not USD"
        )
    
    def test_wallet_is_active_by_default(self):
        """
        REGRESSION TEST: New wallets should be active by default.
        
        Verifies: is_active field default value.
        Reports: Wallets created inactive.
        """
        wallet = Wallet.objects.create(user=self.user)
        self.assertTrue(wallet.is_active, "REGRESSION ISSUE: Wallet not active by default")
    
    def test_wallet_user_relationship(self):
        """
        REGRESSION TEST: Wallet should be linked to user.
        
        Verifies: OneToOne relationship between Wallet and User.
        Reports: Relationship issues.
        """
        wallet = Wallet.objects.create(user=self.user)
        self.assertEqual(wallet.user, self.user, "REGRESSION ISSUE: Wallet not linked to user")
    
    def test_one_wallet_per_user(self):
        """
        REGRESSION TEST: Each user should have only one wallet.
        
        Verifies: OneToOne constraint enforced.
        Reports: Multiple wallets per user allowed.
        """
        from django.db import IntegrityError
        
        Wallet.objects.create(user=self.user)
        
        with self.assertRaises(IntegrityError, msg="REGRESSION ISSUE: Multiple wallets per user allowed"):
            Wallet.objects.create(user=self.user)
    
    def test_wallet_timestamps_set(self):
        """
        REGRESSION TEST: Wallet timestamps should be automatically set.
        
        Verifies: created_at and updated_at fields are populated.
        Reports: Missing timestamp values.
        """
        wallet = Wallet.objects.create(user=self.user)
        wallet.refresh_from_db()
        self.assertIsNotNone(wallet.created_at, "REGRESSION ISSUE: created_at not set")
        self.assertIsNotNone(wallet.updated_at, "REGRESSION ISSUE: updated_at not set")


class WalletCreditRegressionTests(TestCase):
    """
    Regression tests for wallet credit operations.
    
    These tests verify that:
    - Credit operation increases balance
    - Positive amounts are required
    - Balance precision is maintained
    """
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            post_save.disconnect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
        try:
            post_save.disconnect(payments_signals.create_user_wallet, sender=User)
        except Exception:
            pass
        try:
            post_save.disconnect(payments_signals.save_user_wallet, sender=User)
        except Exception:
            pass
    
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        try:
            post_save.connect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
        try:
            post_save.connect(payments_signals.create_user_wallet, sender=User)
        except Exception:
            pass
        try:
            post_save.connect(payments_signals.save_user_wallet, sender=User)
        except Exception:
            pass
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='credit_user',
            email='credit@test.com',
            password='CreditPass123!'
        )
        self.wallet = Wallet.objects.create(user=self.user, balance=Decimal('100.00'))
    
    def test_credit_increases_balance(self):
        """
        REGRESSION TEST: Credit should increase wallet balance.
        
        Verifies: credit() method adds to balance correctly.
        Reports: Balance not updated properly.
        """
        initial_balance = self.wallet.balance
        result = self.wallet.credit(Decimal('50.00'))
        
        self.assertTrue(result, "REGRESSION ISSUE: credit() returned False for valid amount")
        self.wallet.refresh_from_db()
        self.assertEqual(
            self.wallet.balance,
            initial_balance + Decimal('50.00'),
            "REGRESSION ISSUE: Balance not increased correctly"
        )
    
    def test_credit_zero_amount_rejected(self):
        """
        REGRESSION TEST: Zero amount credit should be rejected.
        
        Verifies: credit() rejects zero amounts.
        Reports: Zero credits allowed.
        """
        initial_balance = self.wallet.balance
        result = self.wallet.credit(Decimal('0.00'))
        
        self.assertFalse(result, "REGRESSION ISSUE: Zero amount credit was accepted")
        self.wallet.refresh_from_db()
        self.assertEqual(
            self.wallet.balance,
            initial_balance,
            "REGRESSION ISSUE: Balance changed for zero credit"
        )
    
    def test_credit_negative_amount_rejected(self):
        """
        REGRESSION TEST: Negative amount credit should be rejected.
        
        Verifies: credit() rejects negative amounts.
        Reports: Negative credits allowed (security issue).
        """
        initial_balance = self.wallet.balance
        result = self.wallet.credit(Decimal('-50.00'))
        
        self.assertFalse(result, "REGRESSION ISSUE: Negative credit was accepted (SECURITY RISK)")
        self.wallet.refresh_from_db()
        self.assertEqual(
            self.wallet.balance,
            initial_balance,
            "REGRESSION ISSUE: Balance changed for negative credit"
        )
    
    def test_credit_decimal_precision(self):
        """
        REGRESSION TEST: Credit should maintain decimal precision.
        
        Verifies: Decimal precision is maintained (2 decimal places).
        Reports: Precision loss in balance.
        """
        self.wallet.balance = Decimal('0.00')
        self.wallet.save()
        
        self.wallet.credit(Decimal('10.99'))
        self.wallet.refresh_from_db()
        
        self.assertEqual(
            self.wallet.balance,
            Decimal('10.99'),
            "REGRESSION ISSUE: Decimal precision lost"
        )
    
    def test_credit_large_amount(self):
        """
        REGRESSION TEST: Large credit amounts should work.
        
        Verifies: credit() handles large values.
        Reports: Issues with large transactions.
        """
        self.wallet.balance = Decimal('0.00')
        self.wallet.save()
        
        large_amount = Decimal('99999999.99')
        result = self.wallet.credit(large_amount)
        
        self.assertTrue(result, "REGRESSION ISSUE: Large credit rejected")
        self.wallet.refresh_from_db()
        self.assertEqual(
            self.wallet.balance,
            large_amount,
            "REGRESSION ISSUE: Large credit amount not stored correctly"
        )


class WalletDebitRegressionTests(TestCase):
    """
    Regression tests for wallet debit operations.
    
    These tests verify that:
    - Debit operation decreases balance
    - Insufficient balance is handled
    - Negative amounts are rejected
    """
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            post_save.disconnect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
        try:
            post_save.disconnect(payments_signals.create_user_wallet, sender=User)
        except Exception:
            pass
        try:
            post_save.disconnect(payments_signals.save_user_wallet, sender=User)
        except Exception:
            pass
    
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        try:
            post_save.connect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
        try:
            post_save.connect(payments_signals.create_user_wallet, sender=User)
        except Exception:
            pass
        try:
            post_save.connect(payments_signals.save_user_wallet, sender=User)
        except Exception:
            pass
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='debit_user',
            email='debit@test.com',
            password='DebitPass123!'
        )
        self.wallet = Wallet.objects.create(user=self.user, balance=Decimal('100.00'))
    
    def test_debit_decreases_balance(self):
        """
        REGRESSION TEST: Debit should decrease wallet balance.
        
        Verifies: debit() method subtracts from balance correctly.
        Reports: Balance not updated properly.
        """
        initial_balance = self.wallet.balance
        result = self.wallet.debit(Decimal('30.00'))
        
        self.assertTrue(result, "REGRESSION ISSUE: debit() returned False for valid amount")
        self.wallet.refresh_from_db()
        self.assertEqual(
            self.wallet.balance,
            initial_balance - Decimal('30.00'),
            "REGRESSION ISSUE: Balance not decreased correctly"
        )
    
    def test_debit_insufficient_balance_rejected(self):
        """
        REGRESSION TEST: Debit exceeding balance should be rejected.
        
        Verifies: debit() checks balance before processing.
        Reports: Overdrafts allowed (financial risk).
        """
        initial_balance = self.wallet.balance
        result = self.wallet.debit(Decimal('150.00'))  # More than balance
        
        self.assertFalse(result, "REGRESSION ISSUE: Overdraft was allowed (FINANCIAL RISK)")
        self.wallet.refresh_from_db()
        self.assertEqual(
            self.wallet.balance,
            initial_balance,
            "REGRESSION ISSUE: Balance changed despite insufficient funds"
        )
    
    def test_debit_exact_balance_allowed(self):
        """
        REGRESSION TEST: Debit of exact balance should be allowed.
        
        Verifies: Debiting entire balance works.
        Reports: Issues with zero-balance transactions.
        """
        result = self.wallet.debit(Decimal('100.00'))
        
        self.assertTrue(result, "REGRESSION ISSUE: Exact balance debit rejected")
        self.wallet.refresh_from_db()
        self.assertEqual(
            self.wallet.balance,
            Decimal('0.00'),
            "REGRESSION ISSUE: Balance not zero after exact debit"
        )
    
    def test_debit_zero_amount_rejected(self):
        """
        REGRESSION TEST: Zero amount debit should be rejected.
        
        Verifies: debit() rejects zero amounts.
        Reports: Zero debits allowed.
        """
        initial_balance = self.wallet.balance
        result = self.wallet.debit(Decimal('0.00'))
        
        self.assertFalse(result, "REGRESSION ISSUE: Zero amount debit was accepted")
        self.wallet.refresh_from_db()
        self.assertEqual(
            self.wallet.balance,
            initial_balance,
            "REGRESSION ISSUE: Balance changed for zero debit"
        )
    
    def test_debit_negative_amount_rejected(self):
        """
        REGRESSION TEST: Negative amount debit should be rejected.
        
        Verifies: debit() rejects negative amounts.
        Reports: Negative debits allowed (could increase balance - security issue).
        """
        initial_balance = self.wallet.balance
        result = self.wallet.debit(Decimal('-50.00'))
        
        self.assertFalse(result, "REGRESSION ISSUE: Negative debit was accepted (SECURITY RISK)")
        self.wallet.refresh_from_db()
        self.assertEqual(
            self.wallet.balance,
            initial_balance,
            "REGRESSION ISSUE: Balance changed for negative debit"
        )


class WalletBalanceCheckRegressionTests(TestCase):
    """
    Regression tests for wallet balance checking.
    
    These tests verify that:
    - has_sufficient_balance works correctly
    - Edge cases are handled properly
    """
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            post_save.disconnect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
        try:
            post_save.disconnect(payments_signals.create_user_wallet, sender=User)
        except Exception:
            pass
        try:
            post_save.disconnect(payments_signals.save_user_wallet, sender=User)
        except Exception:
            pass
    
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        try:
            post_save.connect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
        try:
            post_save.connect(payments_signals.create_user_wallet, sender=User)
        except Exception:
            pass
        try:
            post_save.connect(payments_signals.save_user_wallet, sender=User)
        except Exception:
            pass
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='balance_user',
            email='balance@test.com',
            password='BalancePass123!'
        )
        self.wallet = Wallet.objects.create(user=self.user, balance=Decimal('100.00'))
    
    def test_sufficient_balance_returns_true(self):
        """
        REGRESSION TEST: has_sufficient_balance should return True when balance is sufficient.
        
        Verifies: Correct response for valid transaction amounts.
        Reports: False negatives in balance check.
        """
        result = self.wallet.has_sufficient_balance(Decimal('50.00'))
        self.assertTrue(result, "REGRESSION ISSUE: has_sufficient_balance returned False for valid amount")
    
    def test_insufficient_balance_returns_false(self):
        """
        REGRESSION TEST: has_sufficient_balance should return False when balance is insufficient.
        
        Verifies: Correct response for invalid transaction amounts.
        Reports: False positives in balance check (financial risk).
        """
        result = self.wallet.has_sufficient_balance(Decimal('150.00'))
        self.assertFalse(result, "REGRESSION ISSUE: has_sufficient_balance returned True for insufficient funds")
    
    def test_exact_balance_returns_true(self):
        """
        REGRESSION TEST: has_sufficient_balance should return True for exact balance.
        
        Verifies: Edge case of exact amount.
        Reports: Issues with exact balance transactions.
        """
        result = self.wallet.has_sufficient_balance(Decimal('100.00'))
        self.assertTrue(result, "REGRESSION ISSUE: has_sufficient_balance returned False for exact balance")
    
    def test_zero_amount_returns_true(self):
        """
        REGRESSION TEST: has_sufficient_balance should return True for zero amount.
        
        Verifies: Zero amount handling.
        Reports: Issues with zero amount checks.
        """
        result = self.wallet.has_sufficient_balance(Decimal('0.00'))
        self.assertTrue(result, "REGRESSION ISSUE: has_sufficient_balance returned False for zero amount")


class WalletStringRepresentationRegressionTests(TestCase):
    """
    Regression tests for wallet string representation.
    
    These tests verify that:
    - Wallet __str__ returns expected format
    - Display values are correct
    """
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            post_save.disconnect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
        try:
            post_save.disconnect(payments_signals.create_user_wallet, sender=User)
        except Exception:
            pass
        try:
            post_save.disconnect(payments_signals.save_user_wallet, sender=User)
        except Exception:
            pass
    
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        try:
            post_save.connect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
        try:
            post_save.connect(payments_signals.create_user_wallet, sender=User)
        except Exception:
            pass
        try:
            post_save.connect(payments_signals.save_user_wallet, sender=User)
        except Exception:
            pass
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='strtest_user',
            email='strtest@test.com',
            password='StrPass123!'
        )
        self.wallet = Wallet.objects.create(user=self.user, balance=Decimal('250.50'))
    
    def test_wallet_string_format(self):
        """
        REGRESSION TEST: Wallet string representation should include username and balance.
        
        Verifies: __str__ method format.
        Reports: Display format changes.
        """
        str_repr = str(self.wallet)
        self.assertIn('strtest_user', str_repr, "REGRESSION ISSUE: Username not in wallet string")
        self.assertIn('250.50', str_repr, "REGRESSION ISSUE: Balance not in wallet string")


class WalletValidationRegressionTests(TestCase):
    """
    Regression tests for wallet validation.
    
    These tests verify that:
    - Balance minimum value constraint works
    - Invalid values are rejected
    """
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            post_save.disconnect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
        try:
            post_save.disconnect(payments_signals.create_user_wallet, sender=User)
        except Exception:
            pass
        try:
            post_save.disconnect(payments_signals.save_user_wallet, sender=User)
        except Exception:
            pass
    
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        try:
            post_save.connect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
        try:
            post_save.connect(payments_signals.create_user_wallet, sender=User)
        except Exception:
            pass
        try:
            post_save.connect(payments_signals.save_user_wallet, sender=User)
        except Exception:
            pass
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='validation_user',
            email='validation@test.com',
            password='ValidationPass123!'
        )
    
    def test_negative_balance_validation(self):
        """
        REGRESSION TEST: Negative balance should fail validation.
        
        Verifies: MinValueValidator on balance field.
        Reports: Negative balances allowed (financial risk).
        """
        wallet = Wallet(user=self.user, balance=Decimal('-100.00'))
        
        with self.assertRaises(ValidationError, msg="REGRESSION ISSUE: Negative balance allowed"):
            wallet.full_clean()
    
    def test_valid_balance_passes_validation(self):
        """
        REGRESSION TEST: Valid balance should pass validation.
        
        Verifies: Positive balances are accepted.
        Reports: Valid balances rejected.
        """
        wallet = Wallet(user=self.user, balance=Decimal('100.00'))
        
        try:
            wallet.full_clean()
        except ValidationError:
            self.fail("REGRESSION ISSUE: Valid balance rejected during validation")

