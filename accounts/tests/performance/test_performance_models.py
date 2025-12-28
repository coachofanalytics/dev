# accounts/tests/test_performance_model.py

from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import Payment_History

User = get_user_model()


class PaymentHistoryPerformanceTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="perfuser",
            email="perf@example.com",
            password="password123"
        )

    def test_bulk_payment_history_creation(self):
        payments = [
            Payment_History(
                customer=self.user,
                payment_fees=5000,
                down_payment=500,
                student_bonus=500,
                plan=1,
                payment_method="Cash",
                client_signature="Client",
                company_rep="Company"
            )
            for _ in range(100)
        ]

        Payment_History.objects.bulk_create(payments)

        self.assertEqual(Payment_History.objects.count(), 100)
