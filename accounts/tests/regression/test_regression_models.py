import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from accounts.models import PaymentHistory
User = get_user_model()


        from django.test import TestCase
from accounts.models import Tracker
from datetime import datetime

@pytest.mark.django_db
class TestPaymentHistoryRegression:

    def setup_method(self):
        self.user = User.objects.create_user(
            username="regression_user",
            email="reg@test.com",
            password="password123"
        )

    # ---------------------------------------------------
    # REGRESSION: Default Field Values
    # ---------------------------------------------------

    def test_default_status_is_initiated(self):
        payment = PaymentHistory.objects.create(
            user=self.user,
            reference_code="REG-001",
            amount=100,
            currency="USD",
            provider="stripe"
        )

        assert payment.status == "initiated"

    def test_default_transaction_fee_is_zero(self):
        payment = PaymentHistory.objects.create(
            user=self.user,
            reference_code="REG-002",
            amount=200,
            currency="USD",
            provider="stripe"
        )

        assert payment.transaction_fee == 0

    # ---------------------------------------------------
    # REGRESSION: String Representation Stability
    # ---------------------------------------------------

    def test_string_format_remains_consistent(self):
        payment = PaymentHistory.objects.create(
            user=self.user,
            reference_code="REG-003",
            amount=300,
            currency="USD",
            provider="stripe",
            status="succeeded"
        )

        expected = "REG-003 | 300 USD | stripe | succeeded"
        assert str(payment) == expected

    # ---------------------------------------------------
    # REGRESSION: mark_succeeded Behavior
    # ---------------------------------------------------

    def test_mark_succeeded_sets_net_amount_correctly(self):
        payment = PaymentHistory.objects.create(
            user=self.user,
            reference_code="REG-004",
            amount=500,
            currency="USD",
            provider="stripe",
            transaction_fee=50
        )

        payment.mark_succeeded()
        payment.refresh_from_db()

        assert payment.net_amount == 450
        assert payment.status == "succeeded"

    # ---------------------------------------------------
    # REGRESSION: mark_failed Appends Notes
    # ---------------------------------------------------

    def test_mark_failed_appends_note(self):
        payment = PaymentHistory.objects.create(
            user=self.user,
            reference_code="REG-005",
            amount=100,
            currency="USD",
            provider="stripe"
        )

        payment.mark_failed("Initial failure")
        payment.mark_failed("Second failure")
        payment.refresh_from_db()

        assert "Initial failure" in payment.notes
        assert "Second failure" in payment.notes

    # ---------------------------------------------------
    # REGRESSION: Provider Payment ID Lookup
    # ---------------------------------------------------

    def test_provider_payment_id_lookup_still_works(self):
        payment = PaymentHistory.objects.create(
            user=self.user,
            reference_code="REG-006",
            amount=250,
            currency="USD",
            provider="stripe",
            provider_payment_id="pi_regression_test"
        )

        fetched = PaymentHistory.objects.get(provider_payment_id="pi_regression_test")
        assert fetched.id == payment.id

    # ---------------------------------------------------
    # REGRESSION: Required Fields Validation
    # ---------------------------------------------------

    def test_amount_is_required(self):
        with pytest.raises(Exception):
            PaymentHistory.objects.create(
                user=self.user,
                reference_code="REG-007",
                currency="USD",
                provider="stripe"
            )

    # ---------------------------------------------------
    # REGRESSION: Currency Choices Still Valid
    # ---------------------------------------------------

    def test_currency_choices_not_removed(self):
        valid = [c[0] for c in PaymentHistory.Currency.choices]
        assert "USD" in valid
        assert "KES" in valid

    # ---------------------------------------------------
    # REGRESSION: Status Choices Stability
    # ---------------------------------------------------

    def test_status_choices_not_modified(self):
        valid_statuses = [s[0] for s in PaymentHistory.Status.choices]
        assert "initiated" in valid_statuses
        assert "succeeded" in valid_statuses
        assert "failed" in valid_statuses






class TrackerRegressionTest(TestCase):

    def test_tracker_creation_regression(self):
        """Ensure tracker creation still works after updates"""

        tracker = Tracker.objects.create(
            category="Finance",
            sub_category="Salary",
            plan="Enterprise",
            empname=999,
            author=1,
            employee="Regression Test",
            login_date=datetime.now(),
            duration=45
        )

        self.assertEqual(tracker.employee, "Regression Test")
        self.assertEqual(tracker.plan, "Enterprise")

    def test_duration_positive(self):
        """Ensure duration remains positive"""

        tracker = Tracker.objects.create(
            category="Finance",
            sub_category="Audit",
            plan="Basic",
            empname=50,
            author=2,
            employee="Test",
            login_date=datetime.now(),
            duration=30
        )

        self.assertTrue(tracker.duration > 0)




        from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from accounts.models import Transaction


class TransactionRegressionTest(TestCase):
    """
    Regression tests for Transaction.

    These tests protect against old bugs coming back, such as:
    1. Transaction amount saving incorrectly.
    2. Transaction cost being ignored.
    3. Null amount breaking total_amount.
    4. Empty department causing errors.
    5. Payment method default not applying.
    """

    def setUp(self):
        User = get_user_model()

        self.user = User.objects.create_user(
            username="regressionuser",
            email="regression@example.com",
            password="Testpass123"
        )

    def test_transaction_cost_is_added_to_total_amount(self):
        transaction = Transaction.objects.create(
            sender=self.user,
            department="Finance",
            receiver="Brenda",
            phone="254712345001",
            type="Income",
            activity_date=timezone.now(),
            qty=Decimal("1.00"),
            amount=Decimal("15000.00"),
            transaction_cost=Decimal("50.00"),
            description="Testing total amount calculation",
            payment_method="MPESA"
        )

        self.assertEqual(transaction.total_amount, Decimal("15050.00"))

    def test_transaction_total_amount_does_not_fail_when_amount_is_null(self):
        transaction = Transaction.objects.create(
            sender=self.user,
            department="Finance",
            receiver="Angel",
            phone="254712345002",
            type="Expense",
            activity_date=timezone.now(),
            qty=Decimal("1.00"),
            amount=None,
            transaction_cost=Decimal("100.00"),
            description="Testing null amount",
            payment_method="Cash"
        )

        self.assertEqual(transaction.total_amount, Decimal("100.00"))

    def test_transaction_total_amount_does_not_fail_when_transaction_cost_is_null(self):
        transaction = Transaction.objects.create(
            sender=self.user,
            department="Finance",
            receiver="Samuel",
            phone="254712345003",
            type="Income",
            activity_date=timezone.now(),
            qty=Decimal("1.00"),
            amount=Decimal("5000.00"),
            transaction_cost=None,
            description="Testing null transaction cost",
            payment_method="Bank"
        )

        self.assertEqual(transaction.total_amount, Decimal("5000.00"))

    def test_transaction_can_save_without_department(self):
        transaction = Transaction.objects.create(
            sender=self.user,
            department=None,
            receiver="Judy",
            phone="254712345004",
            type="Advance",
            activity_date=timezone.now(),
            qty=Decimal("1.00"),
            amount=Decimal("2500.00"),
            transaction_cost=Decimal("0.00"),
            description="Testing empty department",
            payment_method="Cash"
        )

        self.assertIsNone(transaction.department)
        self.assertEqual(transaction.amount, Decimal("2500.00"))

    def test_payment_method_defaults_to_cash(self):
        transaction = Transaction.objects.create(
            sender=self.user,
            department="Training",
            receiver="Mercy",
            phone="254712345005",
            type="Income",
            activity_date=timezone.now(),
            qty=Decimal("1.00"),
            amount=Decimal("7000.00"),
            transaction_cost=Decimal("0.00"),
            description="Testing default payment method"
        )

        self.assertEqual(transaction.payment_method, "Cash")

    def test_transaction_type_defaults_to_other(self):
        transaction = Transaction.objects.create(
            sender=self.user,
            department="Operations",
            receiver="Brian",
            phone="254712345006",
            activity_date=timezone.now(),
            qty=Decimal("1.00"),
            amount=Decimal("3000.00"),
            transaction_cost=Decimal("0.00"),
            description="Testing default transaction type",
            payment_method="MPESA"
        )

        self.assertEqual(transaction.type, "Other")

    def test_transaction_string_format_does_not_change(self):
        transaction = Transaction.objects.create(
            sender=self.user,
            department="IT",
            receiver="Developer Team",
            phone="254712345007",
            type="Expense",
            activity_date=timezone.now(),
            qty=Decimal("1.00"),
            amount=Decimal("8000.00"),
            transaction_cost=Decimal("200.00"),
            description="Testing string format",
            payment_method="PayPal"
        )

        self.assertEqual(str(transaction), "Expense - 8000.00 - PayPal")