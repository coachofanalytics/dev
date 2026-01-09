"""
Resource Smoke Tests.

Lightweight regression detection tests:
- Query count stability
- Response time consistency
- Basic resource usage patterns

These tests are designed to be fast and run frequently to catch regressions.
"""

import pytest
import time
from decimal import Decimal
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.db import connection
from django.contrib.auth.models import User

from payments.models import Wallet, Transaction
from marketplace.models import InvestmentOpportunity

from .conftest import (
    PerformanceMetrics,
    assert_max_queries,
)


@pytest.mark.django_db
@pytest.mark.performance
class TestQueryCountSmoke:
    """Query count stability tests - lightweight regression detection."""

    @pytest.fixture
    def smoke_user(self, db):
        """Create user for smoke tests."""
        user = User.objects.create_user(
            username='smoke_test_user',
            email='smoke@test.com',
            password='testpass123'
        )
        wallet, _ = Wallet.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('1000.00')}
        )
        
        # Create some transactions
        for i in range(10):
            Transaction.objects.create(
                user=user,
                wallet=wallet,
                transaction_type='deposit',
                amount=Decimal('10.00'),
                payment_gateway='stripe',
                status='completed'
            )
        
        return user, wallet

    def test_smoke__user_fetch__query_count_stable(self, smoke_user, db):
        """
        SMOKE TEST: User fetch should have consistent query count.
        
        Baseline: 1 query
        """
        user, wallet = smoke_user
        
        with CaptureQueriesContext(connection) as context:
            _ = User.objects.get(username='smoke_test_user')
        
        query_count = len(context)
        
        if query_count > 2:
            pytest.fail(
                f"REGRESSION: User fetch made {query_count} queries.\n"
                f"Expected: 1-2 queries\n"
                f"Investigate changes to User model or signal handlers."
            )

    def test_smoke__wallet_with_user__query_count_stable(self, smoke_user, db):
        """
        SMOKE TEST: Wallet fetch with user should use select_related.
        
        Baseline: 1-2 queries
        """
        user, wallet = smoke_user
        
        with CaptureQueriesContext(connection) as context:
            w = Wallet.objects.select_related('user').get(user=user)
            _ = w.user.username  # Access related field
        
        query_count = len(context)
        
        if query_count > 2:
            pytest.fail(
                f"REGRESSION: Wallet+User fetch made {query_count} queries.\n"
                f"Expected: 1-2 queries with select_related.\n"
                f"Check if select_related is being used correctly."
            )

    def test_smoke__transaction_list__query_count_stable(self, smoke_user, db):
        """
        SMOKE TEST: Transaction list query count should not scale with rows.
        
        With 10 transactions, should still be ~2-3 queries, not 11+.
        """
        user, wallet = smoke_user
        
        with CaptureQueriesContext(connection) as context:
            transactions = list(
                Transaction.objects.filter(user=user)
                .select_related('wallet', 'user')[:10]
            )
            # Access related fields
            for txn in transactions:
                _ = txn.user.username
                if txn.wallet:
                    _ = txn.wallet.balance
        
        query_count = len(context)
        
        if query_count > 5:
            pytest.fail(
                f"REGRESSION: Transaction list made {query_count} queries.\n"
                f"Expected: 2-5 queries with select_related.\n"
                f"Possible N+1 issue detected."
            )


@pytest.mark.django_db
@pytest.mark.performance
class TestResponseTimeSmoke:
    """Response time consistency tests."""

    @pytest.fixture
    def response_time_setup(self, db):
        """Setup for response time tests."""
        user = User.objects.create_user(
            username='response_time_user',
            email='responsetime@test.com',
            password='testpass123'
        )
        return user

    def test_smoke__login_page__response_time_consistent(self, response_time_setup):
        """
        SMOKE TEST: Login page response time should be consistent.
        
        Run multiple times, variance should be low.
        """
        client = Client()
        metrics = PerformanceMetrics(name="login_page_smoke")
        
        for _ in range(10):
            with metrics.measure():
                response = client.get('/login/')
            assert response.status_code == 200
        
        # Check variance
        variance = max(metrics.measurements) - min(metrics.measurements)
        mean = metrics.mean
        
        if variance > mean * 2:  # More than 2x variance from mean
            print(f"\n  WARNING: High response time variance detected")
            print(f"  Mean: {mean:.2f}ms")
            print(f"  Min: {metrics.min_latency:.2f}ms")
            print(f"  Max: {metrics.max_latency:.2f}ms")
            print(f"  Variance: {variance:.2f}ms")
        
        # Should complete in reasonable time
        metrics.assert_p95_under(500)

    def test_smoke__home_page__response_time_consistent(self, response_time_setup):
        """
        SMOKE TEST: Home page response time consistency.
        """
        client = Client()
        metrics = PerformanceMetrics(name="home_page_smoke")
        
        for _ in range(10):
            with metrics.measure():
                response = client.get('/')
            # Accept redirect or success
            assert response.status_code in [200, 301, 302]
        
        metrics.assert_p95_under(500)


@pytest.mark.django_db
@pytest.mark.performance
class TestDatabaseOperationSmoke:
    """Database operation smoke tests."""

    def test_smoke__create_user__timing_consistent(self, db):
        """
        SMOKE TEST: User creation timing should be consistent.
        """
        metrics = PerformanceMetrics(name="user_creation_smoke")
        
        for i in range(5):
            with metrics.measure():
                user = User.objects.create_user(
                    username=f'smoke_create_user_{i}',
                    email=f'smokecreate{i}@test.com',
                    password='testpass123'
                )
            assert user.id is not None
        
        if metrics.p95 > 500:
            print(f"\n  WARNING: User creation is slow: {metrics.p95:.2f}ms p95")
            print(f"  Check signal handlers and related model creation.")

    def test_smoke__wallet_credit__timing_consistent(self, db):
        """
        SMOKE TEST: Wallet credit timing should be consistent.
        """
        user = User.objects.create_user(
            username='smoke_wallet_user',
            email='smokewallet@test.com',
            password='testpass123'
        )
        wallet, _ = Wallet.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('0.00')}
        )
        
        metrics = PerformanceMetrics(name="wallet_credit_smoke")
        
        for _ in range(10):
            with metrics.measure():
                wallet.credit(Decimal('10.00'))
        
        if metrics.p95 > 100:
            print(f"\n  WARNING: Wallet credit is slow: {metrics.p95:.2f}ms p95")

    def test_smoke__transaction_create__timing_consistent(self, db):
        """
        SMOKE TEST: Transaction creation timing consistency.
        """
        user = User.objects.create_user(
            username='smoke_txn_user',
            email='smoketxn@test.com',
            password='testpass123'
        )
        wallet, _ = Wallet.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('1000.00')}
        )
        
        metrics = PerformanceMetrics(name="transaction_create_smoke")
        
        for i in range(10):
            with metrics.measure():
                Transaction.objects.create(
                    user=user,
                    wallet=wallet,
                    transaction_type='deposit',
                    amount=Decimal('10.00'),
                    payment_gateway='stripe',
                    status='completed'
                )
        
        if metrics.p95 > 200:
            print(f"\n  WARNING: Transaction creation is slow: {metrics.p95:.2f}ms p95")
            print(f"  Check signal handlers and audit logging.")


@pytest.mark.django_db
@pytest.mark.performance
class TestRepeatedOperationSmoke:
    """Repeated operation stability tests."""

    def test_smoke__repeated_queries__no_degradation(self, db):
        """
        SMOKE TEST: Repeated queries should not degrade over time.
        
        Runs same query 50 times, compares first 10 vs last 10.
        """
        user = User.objects.create_user(
            username='repeat_query_user',
            email='repeatquery@test.com',
            password='testpass123'
        )
        
        timings = []
        
        for _ in range(50):
            start = time.perf_counter()
            _ = User.objects.get(username='repeat_query_user')
            elapsed = (time.perf_counter() - start) * 1000
            timings.append(elapsed)
        
        first_10_avg = sum(timings[:10]) / 10
        last_10_avg = sum(timings[-10:]) / 10
        
        degradation = (last_10_avg - first_10_avg) / first_10_avg * 100 if first_10_avg > 0 else 0
        
        if degradation > 50:  # More than 50% slower
            pytest.fail(
                f"DEGRADATION DETECTED in repeated queries!\n"
                f"First 10 avg: {first_10_avg:.2f}ms\n"
                f"Last 10 avg: {last_10_avg:.2f}ms\n"
                f"Degradation: {degradation:.1f}%\n"
                f"Possible memory leak or connection pool issue."
            )

    def test_smoke__repeated_creates__no_degradation(self, db):
        """
        SMOKE TEST: Repeated creates should not degrade.
        """
        user = User.objects.create_user(
            username='repeat_create_user',
            email='repeatcreate@test.com',
            password='testpass123'
        )
        wallet, _ = Wallet.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('0.00')}
        )
        
        timings = []
        
        for i in range(30):
            start = time.perf_counter()
            Transaction.objects.create(
                user=user,
                wallet=wallet,
                transaction_type='deposit',
                amount=Decimal('1.00'),
                payment_gateway='stripe',
                status='completed'
            )
            elapsed = (time.perf_counter() - start) * 1000
            timings.append(elapsed)
        
        first_10_avg = sum(timings[:10]) / 10
        last_10_avg = sum(timings[-10:]) / 10
        
        if last_10_avg > first_10_avg * 2:
            print(f"\n  WARNING: Create operation degradation detected")
            print(f"  First 10 avg: {first_10_avg:.2f}ms")
            print(f"  Last 10 avg: {last_10_avg:.2f}ms")


@pytest.mark.django_db
@pytest.mark.performance
class TestResourceLimitations:
    """Document known resource testing limitations."""

    def test_documentation__memory_profiling_not_available(self):
        """
        DOCUMENTATION: True memory profiling is not available in-process.
        
        For accurate memory usage analysis, use external tools:
        - memory_profiler package with @profile decorator
        - tracemalloc for Python object allocation
        - Django Debug Toolbar for request memory
        - External profilers like py-spy
        
        This test documents the limitation.
        """
        print(f"\n{'=' * 60}")
        print("Memory Profiling Limitations")
        print(f"{'=' * 60}")
        print("  This test suite uses query count and timing as proxies")
        print("  for resource usage. For true memory profiling, use:")
        print("    - memory_profiler: pip install memory-profiler")
        print("    - tracemalloc: import tracemalloc; tracemalloc.start()")
        print("    - Django Debug Toolbar for per-request analysis")
        print(f"{'=' * 60}\n")
        
        # This test always passes - it's documentation
        assert True

    def test_documentation__connection_pool_monitoring(self):
        """
        DOCUMENTATION: Connection pool monitoring recommendations.
        
        For production connection pool monitoring:
        - Use database-level monitoring (pg_stat_activity for PostgreSQL)
        - Django connection.queries for query debugging
        - New Relic or similar APM tools
        """
        print(f"\n{'=' * 60}")
        print("Connection Pool Monitoring")
        print(f"{'=' * 60}")
        print("  For connection pool issues, monitor:")
        print("    - Database max connections setting")
        print("    - CONN_MAX_AGE in Django settings")
        print("    - pg_stat_activity (PostgreSQL)")
        print("    - SHOW PROCESSLIST (MySQL)")
        print(f"{'=' * 60}\n")
        
        assert True
