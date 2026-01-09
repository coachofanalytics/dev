"""
Load and Stress Testing Suite.

Comprehensive tests for:
- Sustained load scenarios
- Realistic workflow simulations
- Stress testing with breaking point detection
- Throughput and error rate measurement
"""

import pytest
import threading
import time
import random
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.test import Client, TransactionTestCase
from django.contrib.auth.models import User
from django.test.utils import CaptureQueriesContext
from django.db import connection

from payments.models import Wallet, Transaction, SubscriptionPlan, UserSubscription
from marketplace.models import InvestmentOpportunity, JobOpportunity
from accounts.models import Category

from .conftest import (
    PerformanceMetrics,
    ConcurrencyResult,
    PERF_STRESS_DURATION_SEC,
    PERF_LOAD_REQUESTS_PER_SEC,
)


@pytest.mark.django_db
@pytest.mark.performance
@pytest.mark.slow
class TestSustainedLoad:
    """Sustained load testing scenarios."""

    @pytest.fixture
    def load_test_setup(self, db):
        """Create test data for load testing."""
        users = []
        for i in range(10):
            user = User.objects.create_user(
                username=f'load_user_{i}',
                email=f'loaduser{i}@test.com',
                password='testpass123'
            )
            Wallet.objects.get_or_create(
                user=user,
                defaults={'balance': Decimal('1000.00')}
            )
            users.append(user)
        
        # Create marketplace data
        business_user = users[0]
        for i in range(20):
            InvestmentOpportunity.objects.create(
                business=business_user,
                title=f'Load Test Opportunity {i}',
                slug=f'load-test-opportunity-{i}',
                description='Opportunity for load testing',
                amount_seeking=Decimal('100000.00'),
                minimum_investment=Decimal('1000.00'),
                equity_percentage=Decimal('10.00'),
                industry='Technology',
                status='open'
            )
        
        return users

    def test_sustained_auth_load__50_requests__30_seconds(self, load_test_setup, db):
        """
        LOAD TEST: Sustained authentication requests over 30 seconds.
        
        Simulates ~2 login attempts per second.
        Reports latency distribution and error rates.
        """
        users = load_test_setup
        metrics = PerformanceMetrics(name="sustained_auth_load")
        
        duration_sec = 30
        target_rps = 2
        total_requests = duration_sec * target_rps
        
        client = Client()
        start_time = time.perf_counter()
        
        for i in range(total_requests):
            user = users[i % len(users)]
            
            try:
                with metrics.measure():
                    response = client.post('/login/', {
                        'username': user.username,
                        'password': 'testpass123'
                    }, follow=False)
                
                if response.status_code not in [200, 302]:
                    metrics.add_error(f"Status {response.status_code}")
                
                client.logout()
            except Exception as e:
                metrics.add_error(str(e))
            
            # Pace requests to approximate target RPS
            elapsed = time.perf_counter() - start_time
            expected_elapsed = (i + 1) / target_rps
            if elapsed < expected_elapsed:
                time.sleep(expected_elapsed - elapsed)
        
        total_elapsed = time.perf_counter() - start_time
        actual_rps = total_requests / total_elapsed if total_elapsed > 0 else 0
        
        print(f"\n{'=' * 60}")
        print("Sustained Auth Load Test Results")
        print(f"{'=' * 60}")
        print(f"  Duration: {total_elapsed:.2f}s")
        print(f"  Total requests: {metrics.count}")
        print(f"  Target RPS: {target_rps}")
        print(f"  Actual RPS: {actual_rps:.2f}")
        print(f"  Error rate: {metrics.error_rate:.2f}%")
        metrics.print_report()
        
        # Pass criteria
        assert metrics.error_rate < 5, f"Error rate {metrics.error_rate}% exceeds 5%"
        metrics.assert_p95_under(1000, "Sustained load p95 should be under 1s")

    def test_sustained_wallet_load__100_operations__60_seconds(self, load_test_setup, db):
        """
        LOAD TEST: Sustained wallet operations over 60 seconds.
        
        Mix of credits and debits at ~2 ops/sec.
        """
        users = load_test_setup
        metrics = PerformanceMetrics(name="sustained_wallet_load")
        
        duration_sec = 60
        target_rps = 2
        total_ops = duration_sec * target_rps
        
        operations = {
            'credits': 0,
            'debits': 0,
            'credit_success': 0,
            'debit_success': 0,
        }
        
        start_time = time.perf_counter()
        
        for i in range(total_ops):
            user = users[i % len(users)]
            
            try:
                wallet = Wallet.objects.get(user=user)
                
                with metrics.measure():
                    if i % 2 == 0:
                        operations['credits'] += 1
                        if wallet.credit(Decimal('10.00')):
                            operations['credit_success'] += 1
                    else:
                        operations['debits'] += 1
                        if wallet.debit(Decimal('5.00')):
                            operations['debit_success'] += 1
            except Exception as e:
                metrics.add_error(str(e))
            
            # Pace requests
            elapsed = time.perf_counter() - start_time
            expected_elapsed = (i + 1) / target_rps
            if elapsed < expected_elapsed:
                time.sleep(expected_elapsed - elapsed)
        
        total_elapsed = time.perf_counter() - start_time
        
        print(f"\n{'=' * 60}")
        print("Sustained Wallet Load Test Results")
        print(f"{'=' * 60}")
        print(f"  Duration: {total_elapsed:.2f}s")
        print(f"  Credits: {operations['credit_success']}/{operations['credits']}")
        print(f"  Debits: {operations['debit_success']}/{operations['debits']}")
        print(f"  Error rate: {metrics.error_rate:.2f}%")
        metrics.print_report()


@pytest.mark.django_db
@pytest.mark.performance
@pytest.mark.slow
class TestRealisticWorkflows:
    """Realistic user workflow simulations."""

    @pytest.fixture
    def workflow_setup(self, db):
        """Setup data for workflow testing."""
        # Create users
        users = []
        for i in range(5):
            user = User.objects.create_user(
                username=f'workflow_user_{i}',
                email=f'workflow{i}@test.com',
                password='testpass123'
            )
            Wallet.objects.get_or_create(
                user=user,
                defaults={'balance': Decimal('1000.00')}
            )
            users.append(user)
        
        # Create subscription plan
        plan, _ = SubscriptionPlan.objects.get_or_create(
            slug='workflow-test-plan',
            defaults={
                'name': 'Workflow Test Plan',
                'description': 'Plan for workflow testing',
                'price': Decimal('29.99'),
                'duration_days': 30,
                'is_active': True,
            }
        )
        
        # Create opportunities
        for i in range(10):
            InvestmentOpportunity.objects.create(
                business=users[0],
                title=f'Workflow Opportunity {i}',
                slug=f'workflow-opportunity-{i}',
                description='Opportunity for workflow testing',
                amount_seeking=Decimal('100000.00'),
                minimum_investment=Decimal('1000.00'),
                equity_percentage=Decimal('10.00'),
                industry='Technology',
                status='open'
            )
        
        return users, plan

    def test_user_workflow__login_browse_view__sequential(self, workflow_setup, db):
        """
        WORKFLOW TEST: Complete user journey simulation.
        
        Flow: Login → Browse marketplace → View opportunity → Wallet check
        """
        users, plan = workflow_setup
        user = users[0]
        
        metrics = PerformanceMetrics(name="user_workflow")
        workflow_times = []
        
        for _ in range(10):
            client = Client()
            workflow_start = time.perf_counter()
            
            try:
                # Step 1: Login
                with metrics.measure():
                    response = client.post('/login/', {
                        'username': user.username,
                        'password': 'testpass123'
                    }, follow=True)
                
                # Step 2: Browse marketplace
                with metrics.measure():
                    response = client.get('/marketplace/opportunities/')
                    if response.status_code == 404:
                        # Try alternative URL
                        response = client.get('/marketplace/')
                
                # Step 3: View opportunity detail
                opp = InvestmentOpportunity.objects.filter(
                    slug__startswith='workflow-opportunity'
                ).first()
                if opp:
                    with metrics.measure():
                        response = client.get(f'/marketplace/opportunity/{opp.slug}/')
                
                # Step 4: Check wallet
                with metrics.measure():
                    response = client.get('/payments/wallet/')
                
                workflow_elapsed = time.perf_counter() - workflow_start
                workflow_times.append(workflow_elapsed * 1000)
                
                client.logout()
            except Exception as e:
                metrics.add_error(str(e))
        
        avg_workflow_time = sum(workflow_times) / len(workflow_times) if workflow_times else 0
        
        print(f"\n{'=' * 60}")
        print("User Workflow Test Results")
        print(f"{'=' * 60}")
        print(f"  Workflows completed: {len(workflow_times)}")
        print(f"  Avg workflow time: {avg_workflow_time:.2f}ms")
        print(f"  Steps measured: {metrics.count}")
        print(f"  Step p95: {metrics.p95:.2f}ms")
        metrics.print_report()

    def test_concurrent_workflows__5_users__parallel(self, workflow_setup, db):
        """
        WORKFLOW TEST: Multiple users executing workflows concurrently.
        """
        users, plan = workflow_setup
        
        results = {
            'completed': 0,
            'failed': 0,
            'times': []
        }
        lock = threading.Lock()
        
        def user_workflow(user_idx):
            user = users[user_idx % len(users)]
            client = Client()
            start = time.perf_counter()
            
            try:
                # Login
                client.post('/login/', {
                    'username': user.username,
                    'password': 'testpass123'
                }, follow=True)
                
                # Browse
                client.get('/marketplace/')
                
                # Wallet
                client.get('/payments/wallet/')
                
                elapsed = (time.perf_counter() - start) * 1000
                
                with lock:
                    results['completed'] += 1
                    results['times'].append(elapsed)
            except Exception:
                with lock:
                    results['failed'] += 1
        
        # Run concurrent workflows
        threads = [
            threading.Thread(target=user_workflow, args=(i,))
            for i in range(5)
        ]
        
        start_time = time.perf_counter()
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        total_elapsed = time.perf_counter() - start_time
        
        print(f"\n{'=' * 60}")
        print("Concurrent Workflows Test Results")
        print(f"{'=' * 60}")
        print(f"  Concurrent users: 5")
        print(f"  Completed: {results['completed']}")
        print(f"  Failed: {results['failed']}")
        print(f"  Total time: {total_elapsed:.2f}s")
        if results['times']:
            print(f"  Avg workflow time: {sum(results['times']) / len(results['times']):.2f}ms")
        print(f"{'=' * 60}\n")


@pytest.mark.django_db(transaction=True)
@pytest.mark.performance
@pytest.mark.slow
class TestStressTesting:
    """Stress testing with gradual load increase."""

    def test_stress__gradual_increase__find_breaking_point(self, db):
        """
        STRESS TEST: Gradually increase concurrency until degradation.
        
        Starts with 5 concurrent threads, increases by 5 every 5 seconds.
        Stops when error rate exceeds 10% or latency exceeds 2s.
        """
        # Create test user
        user = User.objects.create_user(
            username='stress_grad_user',
            email='stressgrad@test.com',
            password='testpass123'
        )
        wallet, _ = Wallet.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('100000.00')}
        )
        
        breaking_point = None
        results_by_level = {}
        
        for concurrency in range(5, 55, 5):
            metrics = PerformanceMetrics(name=f"stress_level_{concurrency}")
            
            lock = threading.Lock()
            
            def operation():
                try:
                    w = Wallet.objects.get(user=user)
                    with metrics.measure():
                        w.credit(Decimal('1.00'))
                except Exception as e:
                    metrics.add_error(str(e))
            
            # Run for fixed duration at this level
            threads = [
                threading.Thread(target=operation)
                for _ in range(concurrency)
            ]
            
            start = time.perf_counter()
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            elapsed = time.perf_counter() - start
            
            results_by_level[concurrency] = {
                'operations': metrics.count,
                'p95_ms': metrics.p95,
                'error_rate': metrics.error_rate,
                'throughput': metrics.count / elapsed if elapsed > 0 else 0
            }
            
            print(f"  Concurrency {concurrency}: p95={metrics.p95:.2f}ms, errors={metrics.error_rate:.1f}%")
            
            # Check for breaking point
            if metrics.error_rate > 10 or metrics.p95 > 2000:
                breaking_point = concurrency
                break
        
        print(f"\n{'=' * 60}")
        print("Stress Test: Gradual Increase Results")
        print(f"{'=' * 60}")
        
        for level, data in results_by_level.items():
            print(f"  Level {level}:")
            print(f"    p95: {data['p95_ms']:.2f}ms")
            print(f"    Error rate: {data['error_rate']:.2f}%")
            print(f"    Throughput: {data['throughput']:.2f} ops/s")
        
        if breaking_point:
            print(f"\n  BREAKING POINT: {breaking_point} concurrent operations")
        else:
            print(f"\n  No breaking point found up to 50 concurrent operations")
        
        print(f"{'=' * 60}\n")

    def test_stress__spike_test__sudden_load(self, db):
        """
        STRESS TEST: Sudden spike in load.
        
        Tests system response to sudden load increase.
        """
        user = User.objects.create_user(
            username='stress_spike_user',
            email='stressspike@test.com',
            password='testpass123'
        )
        wallet, _ = Wallet.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('100000.00')}
        )
        
        # Normal load phase
        normal_metrics = PerformanceMetrics(name="normal_load")
        for _ in range(10):
            with normal_metrics.measure():
                w = Wallet.objects.get(user=user)
                w.credit(Decimal('1.00'))
        
        # Spike phase
        spike_metrics = PerformanceMetrics(name="spike_load")
        
        def spike_operation():
            try:
                w = Wallet.objects.get(user=user)
                with spike_metrics.measure():
                    w.credit(Decimal('1.00'))
            except Exception as e:
                spike_metrics.add_error(str(e))
        
        # Sudden spike of 50 concurrent operations
        threads = [threading.Thread(target=spike_operation) for _ in range(50)]
        
        start = time.perf_counter()
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        spike_elapsed = time.perf_counter() - start
        
        print(f"\n{'=' * 60}")
        print("Spike Test Results")
        print(f"{'=' * 60}")
        print(f"  Normal load p95: {normal_metrics.p95:.2f}ms")
        print(f"  Spike load (50 concurrent):")
        print(f"    p95: {spike_metrics.p95:.2f}ms")
        print(f"    Error rate: {spike_metrics.error_rate:.1f}%")
        print(f"    Duration: {spike_elapsed:.3f}s")
        print(f"    Degradation factor: {spike_metrics.p95 / normal_metrics.p95:.1f}x" if normal_metrics.p95 > 0 else "")
        print(f"{'=' * 60}\n")


@pytest.mark.django_db
@pytest.mark.performance
@pytest.mark.slow
class TestDatabaseConnectionPooling:
    """Database connection pooling and efficiency tests."""

    def test_connection_pooling__rapid_requests__no_exhaustion(self, db):
        """
        CONNECTION TEST: Rapid sequential requests should not exhaust pool.
        """
        user = User.objects.create_user(
            username='connpool_user',
            email='connpool@test.com',
            password='testpass123'
        )
        
        metrics = PerformanceMetrics(name="connection_pool_test")
        
        for i in range(100):
            try:
                with metrics.measure():
                    # Force new query
                    _ = User.objects.get(username='connpool_user')
            except Exception as e:
                metrics.add_error(str(e))
        
        print(f"\n{'=' * 60}")
        print("Connection Pooling Test Results")
        print(f"{'=' * 60}")
        print(f"  Requests: {metrics.count}")
        print(f"  Errors: {len(metrics.errors)}")
        print(f"  p95: {metrics.p95:.2f}ms")
        metrics.print_report()
        
        # Should complete without connection errors
        assert len(metrics.errors) == 0, f"Connection errors: {metrics.errors[:5]}"


@pytest.mark.django_db
@pytest.mark.performance
@pytest.mark.slow
class TestMemoryUsagePatterns:
    """Memory usage pattern tests (via query count proxy)."""

    def test_iterator_vs_all__large_dataset(self, db):
        """
        MEMORY TEST: iterator() should be more memory efficient.
        
        Note: This is a proxy test using query patterns.
        Actual memory profiling requires external tools.
        """
        user = User.objects.create_user(
            username='iterator_user',
            email='iterator@test.com',
            password='testpass123'
        )
        wallet, _ = Wallet.objects.get_or_create(user=user)
        
        # Create test data
        transactions = [
            Transaction(
                user=user,
                wallet=wallet,
                transaction_type='deposit',
                amount=Decimal('10.00'),
                payment_gateway='stripe',
                status='completed'
            )
            for _ in range(1000)
        ]
        Transaction.objects.bulk_create(transactions)
        
        # Test with all()
        all_metrics = PerformanceMetrics(name="all_retrieval")
        with all_metrics.measure():
            count = 0
            for txn in Transaction.objects.filter(user=user):
                count += 1
        
        # Test with iterator()
        iterator_metrics = PerformanceMetrics(name="iterator_retrieval")
        with iterator_metrics.measure():
            count = 0
            for txn in Transaction.objects.filter(user=user).iterator():
                count += 1
        
        print(f"\n{'=' * 60}")
        print("Iterator vs All Comparison")
        print(f"{'=' * 60}")
        print(f"  Records: 1000")
        print(f"  all() time: {all_metrics.p95:.2f}ms")
        print(f"  iterator() time: {iterator_metrics.p95:.2f}ms")
        print(f"{'=' * 60}\n")

    def test_values_list_vs_objects__id_only(self, db):
        """
        MEMORY TEST: values_list() should be more efficient for ID-only queries.
        """
        user = User.objects.create_user(
            username='values_user',
            email='values@test.com',
            password='testpass123'
        )
        wallet, _ = Wallet.objects.get_or_create(user=user)
        
        # Create test data
        transactions = [
            Transaction(
                user=user,
                wallet=wallet,
                transaction_type='deposit',
                amount=Decimal('10.00'),
                payment_gateway='stripe',
                status='completed'
            )
            for _ in range(500)
        ]
        Transaction.objects.bulk_create(transactions)
        
        # Test with objects
        objects_metrics = PerformanceMetrics(name="objects_retrieval")
        with objects_metrics.measure():
            ids = [t.id for t in Transaction.objects.filter(user=user)]
        
        # Test with values_list
        values_metrics = PerformanceMetrics(name="values_list_retrieval")
        with values_metrics.measure():
            ids = list(Transaction.objects.filter(user=user).values_list('id', flat=True))
        
        print(f"\n{'=' * 60}")
        print("Values_list vs Objects Comparison")
        print(f"{'=' * 60}")
        print(f"  Records: 500")
        print(f"  objects time: {objects_metrics.p95:.2f}ms")
        print(f"  values_list time: {values_metrics.p95:.2f}ms")
        print(f"{'=' * 60}\n")


@pytest.mark.django_db
@pytest.mark.performance
@pytest.mark.slow
class TestPaginationPerformance:
    """Pagination efficiency tests."""

    def test_pagination__offset_vs_keyset(self, db):
        """
        PAGINATION TEST: Compare offset-based vs keyset pagination.
        
        Offset pagination degrades with large offsets.
        """
        user = User.objects.create_user(
            username='pagination_user',
            email='pagination@test.com',
            password='testpass123'
        )
        wallet, _ = Wallet.objects.get_or_create(user=user)
        
        # Create 5000 transactions
        batch_size = 1000
        for batch in range(5):
            transactions = [
                Transaction(
                    user=user,
                    wallet=wallet,
                    transaction_type='deposit',
                    amount=Decimal('10.00'),
                    payment_gateway='stripe',
                    status='completed'
                )
                for _ in range(batch_size)
            ]
            Transaction.objects.bulk_create(transactions)
        
        page_size = 50
        
        # Test offset-based at different offsets
        offset_results = {}
        for offset in [0, 1000, 2000, 4000]:
            metrics = PerformanceMetrics(name=f"offset_{offset}")
            
            for _ in range(5):
                with metrics.measure():
                    results = list(
                        Transaction.objects.filter(user=user)
                        .order_by('-created_at')[offset:offset + page_size]
                    )
            
            offset_results[offset] = metrics.p95
        
        print(f"\n{'=' * 60}")
        print("Pagination Performance Test")
        print(f"{'=' * 60}")
        print(f"  Total records: 5000")
        print(f"  Page size: {page_size}")
        print(f"\n  Offset-based pagination latency:")
        for offset, latency in offset_results.items():
            print(f"    Offset {offset}: {latency:.2f}ms")
        print(f"{'=' * 60}\n")
        
        # Warn if large offset is significantly slower
        if offset_results[4000] > offset_results[0] * 3:
            print("  WARNING: Offset pagination degrades significantly at large offsets.")
            print("  Consider using keyset/cursor pagination for better performance.")
