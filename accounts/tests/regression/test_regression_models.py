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