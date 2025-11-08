"""
Unit tests for finance models

Tests individual model methods, properties, validation, and business logic.

Author: CODA Development Team
Created: November 6, 2025
Category: Unit Tests
"""

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from finance.models import BudgetCategory, Payment_Information

User = get_user_model()


class BudgetCategoryModelTest(TestCase):
    """Tests for BudgetCategory intelligent approval logic"""

    def setUp(self):
        self.category = BudgetCategory.objects.create(
            name="Operations",
            approval_tier="A",
            auto_approve_enabled=True,
            typical_monthly_amount=Decimal("1000.00"),
            variance_threshold=Decimal("20.00"),
            is_recurring=True,
        )

    def test_needs_pattern_analysis_without_timestamp(self):
        """Category should require pattern analysis if never run."""
        self.assertTrue(self.category.needs_pattern_analysis())

    def test_needs_pattern_analysis_when_last_run_recently(self):
        """Should not require analysis when last run within 30 days."""
        self.category.last_pattern_analysis = timezone.now() - timedelta(days=10)
        self.category.save()
        self.assertFalse(self.category.needs_pattern_analysis())

    def test_needs_pattern_analysis_when_last_run_old(self):
        """Should require analysis when last run more than 30 days ago."""
        self.category.last_pattern_analysis = timezone.now() - timedelta(days=45)
        self.category.save()
        self.assertTrue(self.category.needs_pattern_analysis())

    def test_is_within_variance_true(self):
        """Amount within variance threshold should return True."""
        amount = Decimal("1100.00")  # 10% variance
        self.assertTrue(self.category.is_within_variance(amount))

    def test_is_within_variance_false(self):
        """Amount outside variance threshold should return False."""
        amount = Decimal("1500.00")  # 50% variance
        self.assertFalse(self.category.is_within_variance(amount))

    def test_should_auto_approve_success(self):
        """Auto-approval should succeed when all conditions are met."""
        amount = Decimal("1050.00")  # Within 20%
        should_approve, reason = self.category.should_auto_approve(amount)
        self.assertTrue(should_approve)
        self.assertIn("within", reason)

    def test_should_auto_approve_disabled(self):
        """Auto-approval disabled flag should prevent approval."""
        self.category.auto_approve_enabled = False
        self.category.save()
        amount = Decimal("1000.00")
        should_approve, reason = self.category.should_auto_approve(amount)
        self.assertFalse(should_approve)
        self.assertIn("disabled", reason.lower())

    def test_should_auto_approve_non_tier_a(self):
        """Non Tier-A categories require manual approval."""
        self.category.approval_tier = "B"
        self.category.save()
        amount = Decimal("1000.00")
        should_approve, reason = self.category.should_auto_approve(amount)
        self.assertFalse(should_approve)
        self.assertIn("Tier B", reason)

    def test_should_auto_approve_without_typical_amount(self):
        """Missing typical amount should require manual review."""
        self.category.typical_monthly_amount = None
        self.category.save()
        amount = Decimal("1000.00")
        should_approve, reason = self.category.should_auto_approve(amount)
        self.assertFalse(should_approve)
        self.assertIn("No typical amount", reason)

    def test_should_auto_approve_above_variance(self):
        """Amounts outside variance should not auto-approve."""
        amount = Decimal("1400.00")  # 40% variance
        should_approve, reason = self.category.should_auto_approve(amount)
        self.assertFalse(should_approve)
        self.assertIn("exceeds", reason)


class PaymentInformationModelTest(TestCase):
    """Tests for Payment_Information helper methods."""

    def setUp(self):
        self.customer = User.objects.create_user(
            username="finance_user",
            email="finance@test.com",
            password="password123",
        )
        self.payment_info = Payment_Information.objects.create(
            customer=self.customer,
            amount=Decimal("2500.00"),
            currency="USD",
            payment_fees=1500,
            down_payment=500,
            plan=1,
            client_signature="signed",
        )

    def test_fee_balance_calculation(self):
        """get_fee_balance should calculate difference between fees and down payment."""
        self.assertEqual(self.payment_info.get_fee_balance(), 1000)

    def test_string_representation(self):
        """__str__ should include username and plan."""
        self.assertIn("finance_user", str(self.payment_info))
        self.assertIn("Plan", str(self.payment_info))

    def test_default_status_pending(self):
        """New payment records default to pending status."""
        self.assertEqual(self.payment_info.status, "pending")

    def test_payment_method_default(self):
        """Default payment method should be M-Pesa."""
        self.assertEqual(self.payment_info.payment_method, "mpesa")
