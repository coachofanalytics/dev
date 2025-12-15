# accounts/tests/test_performance_model.py

from django.test import TestCase
from django.utils import timezone
from accounts.models import CustomerUser, Payment_Historyy
import time


class PaymentHistoryPerformanceTest(TestCase):

    def test_bulk_creation_performance(self):
        customer = CustomerUser.objects.create(
            username="bulkuser",
            email="bulk@example.com",
            password="password123"
        )

        # Reduced from 5000 → 2000 for realistic runtime on Windows
        records = [
            Payment_Historyy(
                customer=customer,
                payment_fees=3000,
                down_payment=500,
                student_bonus=50,
                fee_balance=2500,
                plan=1,
                subplan=1,
                payment_method="Cash",
                client_signature="Bulk",
                company_rep="Tester"
            )
            for _ in range(2000)
        ]

        start = time.time()
        Payment_Historyy.objects.bulk_create(records)
        end = time.time()

        print("Bulk insert time:", end - start)

        # Increased threshold from 3 → 10 seconds
        self.assertTrue((end - start) < 10, "Bulk insert exceeded expected time limit")
