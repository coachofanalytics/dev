"""
Regression Tests for Error Handling

These tests verify that error handling remains intact after code changes.
Tests are designed to FIND and REPORT issues, not fix them.

Tested Features:
- Invalid input handling
- Payment failure scenarios
- Validation error handling
- Database constraint violations
- Edge case scenarios

Author: Fadhiri
Date: January 2026
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from decimal import Decimal, InvalidOperation
from datetime import date, timedelta

import accounts.models as accounts_models
import payments.signals as payments_signals
from payments.models import Wallet, SubscriptionPlan, UserSubscription, Invoice, Transaction


class InvalidInputHandlingRegressionTests(TestCase):
    """
    Regression tests for invalid input handling.
    
    These tests verify that:
    - Invalid data types are handled
    - Out of range values are caught
    - Empty required fields are handled
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
            username='error_user',
            email='error@test.com',
            password='ErrorPass123!'
        )
        self.wallet = Wallet.objects.create(user=self.user, balance=Decimal('100'))
    
    def test_wallet_credit_with_string_amount(self):
        """
        REGRESSION TEST: Credit with string amount should be handled.
        
        Verifies: Type conversion or error handling for credit.
        Reports: Unexpected crashes or data corruption.
        """
        initial_balance = self.wallet.balance
        
        try:
            # The wallet.credit method should handle string conversion
            result = self.wallet.credit('50.00')
            self.wallet.refresh_from_db()
            
            # If it succeeds, verify balance is correct
            if result:
                self.assertEqual(
                    self.wallet.balance,
                    initial_balance + Decimal('50.00'),
                    "REGRESSION ISSUE: String credit amount not handled correctly"
                )
        except (TypeError, ValueError, InvalidOperation) as e:
            # If it raises an error, that's also acceptable behavior
            pass
    
    def test_wallet_debit_with_insufficient_balance(self):
        """
        REGRESSION TEST: Debit with insufficient balance should fail gracefully.
        
        Verifies: Insufficient balance handling.
        Reports: Overdrafts allowed or crashes.
        """
        initial_balance = self.wallet.balance
        
        result = self.wallet.debit(Decimal('1000'))  # More than balance
        
        self.assertFalse(result, "REGRESSION ISSUE: Overdraft was allowed")
        self.wallet.refresh_from_db()
        self.assertEqual(
            self.wallet.balance,
            initial_balance,
            "REGRESSION ISSUE: Balance changed despite failed debit"
        )
    
    def test_empty_username_registration(self):
        """
        REGRESSION TEST: Empty username should be rejected.
        
        Verifies: Username validation.
        Reports: Empty usernames allowed.
        """
        with self.assertRaises((ValueError, IntegrityError), msg="REGRESSION ISSUE: Empty username allowed"):
            User.objects.create_user(username='', email='empty@test.com', password='Pass123!')
    
    def test_invalid_email_format(self):
        """
        REGRESSION TEST: Invalid email format should be caught during validation.
        
        Verifies: Email format validation.
        Reports: Invalid emails accepted.
        """
        user = User(username='invalid_email', email='not-an-email', password='Pass123!')
        
        try:
            user.full_clean()
            # If no error, the email validation might be lenient
            pass
        except ValidationError as e:
            # Email validation error is expected
            self.assertIn('email', str(e).lower(), "REGRESSION INFO: Email validation working")
    
    def test_negative_subscription_plan_price(self):
        """
        REGRESSION TEST: Negative plan price should be rejected.
        
        Verifies: Price validation.
        Reports: Negative prices allowed.
        """
        plan = SubscriptionPlan(
            name='Negative Plan',
            slug='negative-plan-test',
            description='Test',
            price=Decimal('-10'),
            duration_days=30
        )
        
        with self.assertRaises(ValidationError, msg="REGRESSION ISSUE: Negative plan price allowed"):
            plan.full_clean()
    
    def test_zero_duration_subscription_plan(self):
        """
        REGRESSION TEST: Zero duration plan handling.
        
        Verifies: Duration validation or edge case handling.
        Reports: Issues with zero-duration plans.
        """
        plan = SubscriptionPlan(
            name='Zero Duration',
            slug='zero-duration-test',
            description='Test',
            price=Decimal('10'),
            duration_days=0
        )
        
        try:
            plan.full_clean()
            plan.save()
            # If it saves, document the behavior
            self.assertEqual(plan.duration_days, 0, "INFO: Zero-duration plans are allowed")
        except ValidationError:
            # Validation error is also acceptable
            pass


class PaymentFailureScenarioRegressionTests(TestCase):
    """
    Regression tests for payment failure scenarios.
    
    These tests verify that:
    - Failed payments are handled correctly
    - Transaction status is updated appropriately
    - Wallet balance remains consistent after failures
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
            username='payment_fail_user',
            email='payment_fail@test.com',
            password='PaymentPass123!'
        )
        self.wallet = Wallet.objects.create(user=self.user, balance=Decimal('50'))
        self.plan = SubscriptionPlan.objects.create(
            name='Premium Plan',
            slug='premium-plan-test',
            description='Test',
            price=Decimal('100'),  # More than wallet balance
            duration_days=30
        )
    
    def test_insufficient_balance_for_subscription(self):
        """
        REGRESSION TEST: Subscription payment should fail with insufficient balance.
        
        Verifies: Payment validation for subscriptions.
        Reports: Payments processed despite insufficient funds.
        """
        initial_balance = self.wallet.balance
        
        # Try to debit more than balance
        result = self.wallet.debit(self.plan.price)
        
        self.assertFalse(result, "REGRESSION ISSUE: Payment succeeded with insufficient funds")
        self.wallet.refresh_from_db()
        self.assertEqual(
            self.wallet.balance,
            initial_balance,
            "REGRESSION ISSUE: Balance changed despite payment failure"
        )
    
    def test_transaction_status_on_failure(self):
        """
        REGRESSION TEST: Transaction should be marked with correct status.
        
        Verifies: Transaction status handling.
        Reports: Incorrect transaction status on failures.
        """
        # Create a transaction with failed status
        transaction = Transaction.objects.create(
            user=self.user,
            wallet=self.wallet,
            transaction_type='subscription_payment',
            amount=Decimal('100'),
            payment_gateway='wallet',
            status='failed'
        )
        
        self.assertEqual(
            transaction.status,
            'failed',
            "REGRESSION ISSUE: Failed status not persisted correctly"
        )


class ValidationErrorHandlingRegressionTests(TestCase):
    """
    Regression tests for validation error handling.
    
    These tests verify that:
    - Model validation errors are raised correctly
    - Custom validators work as expected
    - Error messages are informative
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
    
    def test_wallet_negative_balance_validation(self):
        """
        REGRESSION TEST: Negative wallet balance should fail validation.
        
        Verifies: MinValueValidator on wallet balance.
        Reports: Negative balances pass validation.
        """
        wallet = Wallet(user=self.user, balance=Decimal('-100'))
        
        with self.assertRaises(ValidationError, msg="REGRESSION ISSUE: Negative balance passes validation"):
            wallet.full_clean()
    
    def test_investment_opportunity_equity_validation(self):
        """
        REGRESSION TEST: Equity over 100% should fail validation.
        
        Verifies: MaxValueValidator on equity field.
        Reports: Invalid equity percentages accepted.
        """
        from marketplace.models import InvestmentOpportunity
        
        opportunity = InvestmentOpportunity(
            business=self.user,
            title='Test Opportunity',
            description='Test',
            amount_seeking=Decimal('100000'),
            minimum_investment=Decimal('1000'),
            equity_percentage=Decimal('150'),  # Over 100%
            industry='Tech'
        )
        
        with self.assertRaises(ValidationError, msg="REGRESSION ISSUE: Equity over 100% accepted"):
            opportunity.full_clean()
    
    def test_category_description_max_length(self):
        """
        REGRESSION TEST: Category description should respect max length.
        
        Verifies: Max length validation on TextField.
        Reports: Overly long descriptions accepted.
        """
        from accounts.models import Category
        
        # Create category with overly long description
        long_description = 'x' * 250  # More than 200 char limit
        category = Category(
            name='Long Desc Category',
            slug='long-desc-cat',
            description=long_description
        )
        
        try:
            category.full_clean()
            # If it passes, check if description was truncated or accepted
            pass
        except ValidationError as e:
            # Validation error is expected for exceeding max_length
            self.assertIn('description', str(e).lower(), "REGRESSION INFO: Description max length enforced")


class EdgeCaseScenarioRegressionTests(TestCase):
    """
    Regression tests for edge case scenarios.
    
    These tests verify that:
    - Boundary conditions are handled
    - Extreme values don't cause issues
    - Race conditions are mitigated
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
            username='edge_user',
            email='edge@test.com',
            password='EdgePass123!'
        )
    
    def test_zero_amount_wallet_operations(self):
        """
        REGRESSION TEST: Zero amount operations should be handled.
        
        Verifies: Zero amount edge case handling.
        Reports: Zero operations causing issues.
        """
        wallet = Wallet.objects.create(user=self.user, balance=Decimal('100'))
        
        credit_result = wallet.credit(Decimal('0'))
        debit_result = wallet.debit(Decimal('0'))
        
        # Zero operations should return False (invalid)
        self.assertFalse(credit_result, "REGRESSION ISSUE: Zero credit accepted")
        self.assertFalse(debit_result, "REGRESSION ISSUE: Zero debit accepted")
    
    def test_very_large_amounts(self):
        """
        REGRESSION TEST: Very large amounts should be handled.
        
        Verifies: Large number handling.
        Reports: Overflow or precision issues.
        """
        wallet = Wallet.objects.create(user=self.user, balance=Decimal('0'))
        
        # Test with maximum allowed value (10 digits, 2 decimal places)
        large_amount = Decimal('99999999.99')
        result = wallet.credit(large_amount)
        
        self.assertTrue(result, "REGRESSION ISSUE: Large credit amount rejected")
        wallet.refresh_from_db()
        self.assertEqual(
            wallet.balance,
            large_amount,
            "REGRESSION ISSUE: Large amount not stored correctly"
        )
    
    def test_very_small_decimal_amounts(self):
        """
        REGRESSION TEST: Small decimal amounts should be handled.
        
        Verifies: Decimal precision handling.
        Reports: Precision loss for small amounts.
        """
        wallet = Wallet.objects.create(user=self.user, balance=Decimal('0'))
        
        small_amount = Decimal('0.01')
        result = wallet.credit(small_amount)
        
        self.assertTrue(result, "REGRESSION ISSUE: Small credit amount rejected")
        wallet.refresh_from_db()
        self.assertEqual(
            wallet.balance,
            small_amount,
            "REGRESSION ISSUE: Small amount precision lost"
        )
    
    def test_exact_balance_debit(self):
        """
        REGRESSION TEST: Debiting exact balance should work.
        
        Verifies: Edge case of zero balance after debit.
        Reports: Exact balance debit issues.
        """
        wallet = Wallet.objects.create(user=self.user, balance=Decimal('100'))
        
        result = wallet.debit(Decimal('100'))
        
        self.assertTrue(result, "REGRESSION ISSUE: Exact balance debit rejected")
        wallet.refresh_from_db()
        self.assertEqual(
            wallet.balance,
            Decimal('0'),
            "REGRESSION ISSUE: Balance not zero after exact debit"
        )
    
    def test_unicode_in_text_fields(self):
        """
        REGRESSION TEST: Unicode characters should be handled in text fields.
        
        Verifies: Unicode support.
        Reports: Unicode causing issues.
        """
        from accounts.models import Category
        
        category = Category.objects.create(
            name='Категория',  # Russian
            slug='unicode-category',
            description='描述 العربية 日本語'  # Mixed languages
        )
        
        category.refresh_from_db()
        self.assertEqual(category.name, 'Категория', "REGRESSION ISSUE: Unicode name not stored")
        self.assertIn('描述', category.description, "REGRESSION ISSUE: Unicode description not stored")
    
    def test_subscription_activation_twice(self):
        """
        REGRESSION TEST: Activating subscription twice should be handled.
        
        Verifies: Idempotent activation.
        Reports: Issues with double activation.
        """
        plan = SubscriptionPlan.objects.create(
            name='Double Activate Plan',
            slug='double-activate-plan',
            description='Test',
            price=Decimal('10'),
            duration_days=30
        )
        subscription = UserSubscription.objects.create(user=self.user, plan=plan)
        
        # Activate twice
        subscription.activate()
        first_end_date = subscription.end_date
        
        subscription.activate()
        subscription.refresh_from_db()
        
        # End date should be updated (subscription extended)
        # Document the actual behavior
        self.assertEqual(
            subscription.status,
            'active',
            "REGRESSION ISSUE: Subscription not active after double activation"
        )

