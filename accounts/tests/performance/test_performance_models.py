# accounts/tests/test_performance_model.py

from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import Payment_History
from django.utils import timezone

import time


from accounts.models import LoginHistory
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



User = get_user_model()


class LoginHistoryPerformanceTest(TestCase):
    """
    Performance tests for LoginHistory model.
    Focuses on scalability and query efficiency.
    """

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="perf_user",
            email="perf@test.com",
            password="password123"
        )

        # Preload large dataset
        cls.records = [
            LoginHistory(
                user=cls.user,
                ip_address="10.0.0.1",
                user_agent="Performance Test Agent",
                login_time=timezone.now() - timezone.timedelta(seconds=i)
            )
            for i in range(1000)
        ]
        LoginHistory.objects.bulk_create(cls.records)

    def test_bulk_insert_performance(self):
        """
        Performance: bulk inserts should be fast and efficient
        """
        start = time.perf_counter()

        LoginHistory.objects.bulk_create([
            LoginHistory(user=self.user) for _ in range(500)
        ])

        duration = time.perf_counter() - start

        # Soft assertion (no hard timing dependency)
        self.assertLess(duration, 1.5)

    def test_login_history_fetch_query_count(self):
        """
        Performance: fetching login history should use a single query
        """
        with self.assertNumQueries(1):
            list(LoginHistory.objects.all())

    def test_latest_login_retrieval_is_fast(self):
        """
        Performance: latest login lookup must be efficient
        """
        start = time.perf_counter()
        latest = LoginHistory.objects.first()
        duration = time.perf_counter() - start

        self.assertIsNotNone(latest)
        self.assertLess(duration, 0.1)

    def test_filter_by_user_performance(self):
        """
        Performance: filtering by user should not degrade
        """
        start = time.perf_counter()
        logs = list(LoginHistory.objects.filter(user=self.user))
        duration = time.perf_counter() - start

        self.assertEqual(len(logs), LoginHistory.objects.count())
        self.assertLess(duration, 0.5)

    def test_ordering_by_login_time_is_respected(self):
        """
        Performance + correctness: ordering remains intact at scale
        """
        logs = LoginHistory.objects.all()[:10]
        times = [log.login_time for log in logs]

        self.assertEqual(times, sorted(times, reverse=True))
