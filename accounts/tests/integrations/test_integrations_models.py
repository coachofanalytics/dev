import pytest
from django.utils import timezone
from django.contrib.auth import get_user_model
from accounts.models import PaymentHistory
User = get_user_model()


        from django.test import TestCase
from accounts.models import Tracker
from datetime import datetime

@pytest.mark.django_db
class TestPaymentHistoryIntegration:

    def setup_method(self):
        self.user1 = User.objects.create_user(
            username="user1",
            email="user1@test.com",
            password="password123"
        )

        self.user2 = User.objects.create_user(
            username="user2",
            email="user2@test.com",
            password="password123"
        )

    # ---------------------------------------------------
    # User Relationship Integration
    # ---------------------------------------------------

    def test_payment_linked_to_correct_user(self):
        payment = PaymentHistory.objects.create(
            user=self.user1,
            purpose="Contribution",
            reference_code="INT-001",
            amount=500,
            currency="USD",
            provider="stripe",
            status="initiated"
        )

        assert payment.user == self.user1
        assert self.user1.payment_history.count() == 1

    def test_multiple_users_have_separate_payments(self):
        PaymentHistory.objects.create(
            user=self.user1,
            purpose="Membership",
            reference_code="INT-002",
            amount=200,
            currency="USD",
            provider="paypal",
            status="succeeded"
        )

        PaymentHistory.objects.create(
            user=self.user2,
            purpose="Donation",
            reference_code="INT-003",
            amount=300,
            currency="USD",
            provider="stripe",
            status="succeeded"
        )

        assert self.user1.payment_history.count() == 1
        assert self.user2.payment_history.count() == 1

    # ---------------------------------------------------
    # Business Logic Integration
    # ---------------------------------------------------

    def test_mark_succeeded_updates_db_correctly(self):
        payment = PaymentHistory.objects.create(
            user=self.user1,
            purpose="Invoice",
            reference_code="INT-004",
            amount=1000,
            currency="USD",
            provider="stripe",
            transaction_fee=50,
            status="initiated"
        )

        payment.mark_succeeded()
        payment.refresh_from_db()

        assert payment.status == "succeeded"
        assert payment.net_amount == 950
        assert payment.completed_at is not None

    def test_mark_failed_persists_notes(self):
        payment = PaymentHistory.objects.create(
            user=self.user1,
            purpose="Order",
            reference_code="INT-005",
            amount=150,
            currency="USD",
            provider="stripe",
            status="initiated"
        )

        payment.mark_failed("Payment declined by bank")
        payment.refresh_from_db()

        assert payment.status == "failed"
        assert "Payment declined by bank" in payment.notes

    # ---------------------------------------------------
    # Filtering + Aggregation Integration
    # ---------------------------------------------------

    def test_total_succeeded_amount_for_user(self):
        PaymentHistory.objects.create(
            user=self.user1,
            purpose="Contribution",
            reference_code="INT-006",
            amount=100,
            currency="USD",
            provider="stripe",
            status="succeeded"
        )

        PaymentHistory.objects.create(
            user=self.user1,
            purpose="Contribution",
            reference_code="INT-007",
            amount=200,
            currency="USD",
            provider="stripe",
            status="succeeded"
        )

        total = sum(
            p.amount for p in self.user1.payment_history.filter(status="succeeded")
        )

        assert total == 300

    # ---------------------------------------------------
    # Provider + External ID Integration
    # ---------------------------------------------------

    def test_provider_payment_id_unique_lookup(self):
        payment = PaymentHistory.objects.create(
            user=self.user1,
            purpose="Membership",
            reference_code="INT-008",
            amount=500,
            currency="USD",
            provider="stripe",
            provider_payment_id="pi_123456789",
            status="succeeded"
        )

        fetched = PaymentHistory.objects.get(provider_payment_id="pi_123456789")

        assert fetched.id == payment.id

    # ---------------------------------------------------
    # Cascade Protection Integration
    # ---------------------------------------------------

    def test_user_deletion_protects_payment_history(self):
        payment = PaymentHistory.objects.create(
            user=self.user1,
            purpose="Protected",
            reference_code="INT-009",
            amount=400,
            currency="USD",
            provider="stripe",
            status="succeeded"
        )

        with pytest.raises(Exception):
            self.user1.delete()

        assert PaymentHistory.objects.filter(id=payment.id).exists()








class TrackerIntegrationTest(TestCase):

    def setUp(self):
        self.tracker = Tracker.objects.create(
            category="Finance",
            sub_category="Payments",
            plan="Basic",
            empname=101,
            author=1,
            employee="Angel",
            login_date=datetime.now(),
            duration=120
        )

    def test_database_integration(self):
        """Ensure tracker is saved and retrieved correctly"""
        tracker = Tracker.objects.get(employee="Angel")

        self.assertEqual(tracker.category, "Finance")
        self.assertEqual(tracker.sub_category, "Payments")

    def test_update_integration(self):
        """Ensure updates persist in database"""
        tracker = Tracker.objects.get(employee="Angel")
        tracker.plan = "Premium"
        tracker.save()

        updated = Tracker.objects.get(employee="Angel")

        self.assertEqual(updated.plan, "Premium")