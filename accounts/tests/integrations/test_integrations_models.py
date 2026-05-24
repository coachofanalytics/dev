from decimal import Decimal
from datetime import datetime

import pytest

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.db.models.deletion import ProtectedError

from accounts.models import PaymentHistory, Tracker, Transaction


User = get_user_model()


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

        fetched = PaymentHistory.objects.get(
            provider_payment_id="pi_123456789"
        )

        assert fetched.id == payment.id

    def test_user_deletion_protects_payment_history(self):
        PaymentHistory.objects.create(
            user=self.user1,
            purpose="Protected",
            reference_code="INT-009",
            amount=400,
            currency="USD",
            provider="stripe",
            status="succeeded"
        )

        with pytest.raises(ProtectedError):
            self.user1.delete()


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
        tracker = Tracker.objects.get(employee="Angel")

        self.assertEqual(tracker.category, "Finance")
        self.assertEqual(tracker.sub_category, "Payments")

    def test_update_integration(self):
        tracker = Tracker.objects.get(employee="Angel")
        tracker.plan = "Premium"
        tracker.save()

        updated = Tracker.objects.get(employee="Angel")

        self.assertEqual(updated.plan, "Premium")


class TransactionIntegrationTest(TestCase):

    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username="adminuser",
            email="admin@example.com",
            password="Adminpass123"
        )

        self.normal_user = User.objects.create_user(
            username="normaluser",
            email="normal@example.com",
            password="Userpass123"
        )

        self.client = Client()

    def test_create_and_retrieve_transaction(self):
        transaction = Transaction.objects.create(
            sender=self.normal_user,
            department="Finance",
            receiver="Brenda",
            phone="254712345001",
            type="Income",
            activity_date=timezone.now(),
            receipt_link="https://example.com/receipt/001",
            qty=Decimal("1.00"),
            amount=Decimal("15000.00"),
            transaction_cost=Decimal("50.00"),
            description="Student training fee payment",
            payment_method="MPESA"
        )

        saved_transaction = Transaction.objects.get(id=transaction.id)

        self.assertEqual(saved_transaction.sender, self.normal_user)
        self.assertEqual(saved_transaction.department, "Finance")
        self.assertEqual(saved_transaction.receiver, "Brenda")
        self.assertEqual(saved_transaction.amount, Decimal("15000.00"))
        self.assertEqual(saved_transaction.payment_method, "MPESA")
        self.assertEqual(saved_transaction.total_amount, Decimal("15050.00"))

    def test_transaction_admin_list_page_loads(self):
        Transaction.objects.create(
            sender=self.normal_user,
            department="Finance",
            receiver="Angel",
            phone="254712345002",
            type="Expense",
            activity_date=timezone.now(),
            qty=Decimal("1.00"),
            amount=Decimal("5000.00"),
            transaction_cost=Decimal("0.00"),
            description="Office expense",
            payment_method="Cash"
        )

        self.client.login(
            username="adminuser",
            password="Adminpass123"
        )

        url = reverse("admin:accounts_transaction_changelist")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Angel")
        self.assertContains(response, "Cash")

    def test_transaction_admin_add_page_loads(self):
        self.client.login(
            username="adminuser",
            password="Adminpass123"
        )

        url = reverse("admin:accounts_transaction_add")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_transaction_admin_can_save_transaction(self):
        self.client.login(
            username="adminuser",
            password="Adminpass123"
        )

        url = reverse("admin:accounts_transaction_add")

        data = {
            "sender": self.normal_user.id,
            "department": "Finance",
            "receiver": "Samuel",
            "phone": "254712345003",
            "type": "Income",
            "activity_date_0": "2026-05-24",
            "activity_date_1": "10:30:00",
            "receipt_link": "https://example.com/receipt/003",
            "qty": "1.00",
            "amount": "12000.00",
            "transaction_cost": "100.00",
            "description": "Consultation payment",
            "payment_method": "MPESA",
            "_save": "Save",
        }

        response = self.client.post(url, data, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Transaction.objects.filter(receiver="Samuel").exists()
        )

        transaction = Transaction.objects.get(receiver="Samuel")
        self.assertEqual(transaction.amount, Decimal("12000.00"))
        self.assertEqual(transaction.total_amount, Decimal("12100.00"))