import time
import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from accounts.models import PaymentHistory
User = get_user_model()

from django.test import TestCase
from accounts.models import Tracker
from datetime import datetime

@pytest.mark.django_db
class TestPaymentHistoryPerformance:

    def setup_method(self):
        self.user = User.objects.create_user(
            username="perfuser",
            email="perf@example.com",
            password="password123"
        )

    # ---------------------------------------------------
    # BULK INSERT PERFORMANCE
    # ---------------------------------------------------

    def test_bulk_create_1000_payments_under_2_seconds(self):
        payments = [
            PaymentHistory(
                user=self.user,
                purpose="PerformanceTest",
                reference_code=f"PERF-{i}",
                amount=100,
                currency="USD",
                provider="stripe",
                status="initiated"
            )
            for i in range(1000)
        ]

        start = time.time()
        PaymentHistory.objects.bulk_create(payments)
        duration = time.time() - start

        assert duration < 2.0, f"Bulk insert too slow: {duration}s"

    # ---------------------------------------------------
    # QUERY PERFORMANCE
    # ---------------------------------------------------

    def test_filter_by_status_under_1_second(self):
        PaymentHistory.objects.bulk_create([
            PaymentHistory(
                user=self.user,
                purpose="FilterTest",
                reference_code=f"FILTER-{i}",
                amount=50,
                currency="USD",
                provider="stripe",
                status="succeeded"
            )
            for i in range(2000)
        ])

        start = time.time()
        results = PaymentHistory.objects.filter(status="succeeded")
        count = results.count()
        duration = time.time() - start

        assert count == 2000
        assert duration < 1.0, f"Filtering too slow: {duration}s"

    # ---------------------------------------------------
    # INDEX PERFORMANCE (provider_payment_id indexed)
    # ---------------------------------------------------

    def test_lookup_by_provider_payment_id_fast(self):
        payment = PaymentHistory.objects.create(
            user=self.user,
            purpose="IndexTest",
            reference_code="INDEX-001",
            amount=120,
            currency="USD",
            provider="stripe",
            provider_payment_id="pi_fast_lookup",
            status="succeeded"
        )

        start = time.time()
        result = PaymentHistory.objects.get(provider_payment_id="pi_fast_lookup")
        duration = time.time() - start

        assert result.id == payment.id
        assert duration < 0.5, f"Indexed lookup too slow: {duration}s"

    # ---------------------------------------------------
    # UPDATE PERFORMANCE
    # ---------------------------------------------------

    def test_bulk_update_status_under_1_second(self):
        payments = [
            PaymentHistory(
                user=self.user,
                purpose="UpdateTest",
                reference_code=f"UPDATE-{i}",
                amount=70,
                currency="USD",
                provider="stripe",
                status="initiated"
            )
            for i in range(1000)
        ]

        PaymentHistory.objects.bulk_create(payments)

        start = time.time()
        PaymentHistory.objects.filter(status="initiated").update(status="succeeded")
        duration = time.time() - start

        assert duration < 1.0, f"Bulk update too slow: {duration}s"

    # ---------------------------------------------------
    # QUERY COUNT CHECK (avoid N+1)
    # ---------------------------------------------------

    def test_query_count_for_simple_fetch(self):
        PaymentHistory.objects.create(
            user=self.user,
            purpose="QueryCount",
            reference_code="QC-001",
            amount=200,
            currency="USD",
            provider="stripe",
            status="succeeded"
        )

        with connection.cursor() as cursor:
            start_queries = len(connection.queries)

            list(PaymentHistory.objects.all())

            end_queries = len(connection.queries)

        assert (end_queries - start_queries) <= 2






class TrackerPerformanceTest(TestCase):

    def test_bulk_create_performance(self):
        """Test performance of bulk creating tracker records"""

        start_time = time.time()

        trackers = []
        for i in range(1000):
            trackers.append(
                Tracker(
                    category="Finance",
                    sub_category="Payments",
                    plan="Standard",
                    empname=i,
                    author=1,
                    employee=f"Employee {i}",
                    login_date=datetime.now(),
                    duration=60
                )
            )

        Tracker.objects.bulk_create(trackers)

        end_time = time.time()
        duration = end_time - start_time

        print(f"\nBulk create 1000 records took: {duration} seconds")

        self.assertTrue(duration < 5)  # should complete within 5 seconds


    def test_query_performance(self):
        """Test performance of querying many tracker records"""

        for i in range(500):
            Tracker.objects.create(
                category="Finance",
                sub_category="Payments",
                plan="Standard",
                empname=i,
                author=1,
                employee=f"Employee {i}",
                login_date=datetime.now(),
                duration=60
            )

        start_time = time.time()

        trackers = Tracker.objects.filter(category="Finance")

        list(trackers)  # force evaluation

        end_time = time.time()
        duration = end_time - start_time

        print(f"\nQuery 500 records took: {duration} seconds")

        self.assertTrue(duration < 2)


    def test_update_performance(self):
        """Test performance of updating many records"""

        for i in range(500):
            Tracker.objects.create(
                category="Finance",
                sub_category="Payments",
                plan="Standard",
                empname=i,
                author=1,
                employee=f"Employee {i}",
                login_date=datetime.now(),
                duration=60
            )

        start_time = time.time()

        Tracker.objects.filter(category="Finance").update(plan="Premium")

        end_time = time.time()
        duration = end_time - start_time

        print(f"\nBulk update took: {duration} seconds")

        self.assertTrue(duration < 2)