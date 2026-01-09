"""
Performance Test Configuration and Fixtures.

Provides shared utilities, fixtures, and metrics collection for performance testing.
All thresholds are configurable via environment variables for CI flexibility.
"""

import os
import time
import statistics
import threading
from decimal import Decimal
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from contextlib import contextmanager

import pytest
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.db import connection
from django.contrib.auth.models import User

from payments.models import Wallet, Transaction, SubscriptionPlan, UserSubscription, Invoice
from marketplace.models import BusinessProfile, InvestmentOpportunity, JobOpportunity
from accounts.models import Category, UserProfile


# =============================================================================
# CONFIGURABLE THRESHOLDS (Environment Variables)
# =============================================================================

def get_threshold(name: str, default: int) -> int:
    """Get threshold from environment variable or use default."""
    return int(os.environ.get(name, default))


# Default thresholds (can be overridden via environment)
PERF_P50_MS = get_threshold('PERF_P50_MS', 200)
PERF_P95_MS = get_threshold('PERF_P95_MS', 500)
PERF_P99_MS = get_threshold('PERF_P99_MS', 1000)
PERF_MAX_QUERIES = get_threshold('PERF_MAX_QUERIES', 10)
PERF_MAX_QUERIES_LIST = get_threshold('PERF_MAX_QUERIES_LIST', 5)
PERF_STRESS_DURATION_SEC = get_threshold('PERF_STRESS_DURATION_SEC', 30)
PERF_LOAD_REQUESTS_PER_SEC = get_threshold('PERF_LOAD_REQUESTS_PER_SEC', 10)


# =============================================================================
# PERFORMANCE METRICS COLLECTION
# =============================================================================

@dataclass
class PerformanceMetrics:
    """
    Collect and compute performance metrics from a series of measurements.
    
    Usage:
        metrics = PerformanceMetrics(name="login_view")
        for _ in range(100):
            with metrics.measure():
                response = client.get('/login/')
        metrics.report()
    """
    name: str
    measurements: List[float] = field(default_factory=list)
    query_counts: List[int] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    @contextmanager
    def measure(self, capture_queries: bool = False):
        """Context manager to measure execution time and optionally query count."""
        start_time = time.perf_counter()
        query_count = 0
        
        try:
            if capture_queries:
                with CaptureQueriesContext(connection) as context:
                    yield context
                    query_count = len(context)
                    self.query_counts.append(query_count)
            else:
                yield None
        except Exception as e:
            self.errors.append(str(e))
            raise
        finally:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            self.measurements.append(elapsed_ms)
    
    def add_measurement(self, elapsed_ms: float, query_count: int = 0):
        """Add a measurement manually."""
        self.measurements.append(elapsed_ms)
        if query_count:
            self.query_counts.append(query_count)
    
    def add_error(self, error: str):
        """Record an error."""
        self.errors.append(error)
    
    @property
    def count(self) -> int:
        """Number of measurements."""
        return len(self.measurements)
    
    @property
    def p50(self) -> float:
        """50th percentile (median) latency in ms."""
        if not self.measurements:
            return 0.0
        return statistics.median(self.measurements)
    
    @property
    def p95(self) -> float:
        """95th percentile latency in ms."""
        if not self.measurements:
            return 0.0
        sorted_m = sorted(self.measurements)
        idx = int(len(sorted_m) * 0.95)
        return sorted_m[min(idx, len(sorted_m) - 1)]
    
    @property
    def p99(self) -> float:
        """99th percentile latency in ms."""
        if not self.measurements:
            return 0.0
        sorted_m = sorted(self.measurements)
        idx = int(len(sorted_m) * 0.99)
        return sorted_m[min(idx, len(sorted_m) - 1)]
    
    @property
    def mean(self) -> float:
        """Mean latency in ms."""
        if not self.measurements:
            return 0.0
        return statistics.mean(self.measurements)
    
    @property
    def min_latency(self) -> float:
        """Minimum latency in ms."""
        return min(self.measurements) if self.measurements else 0.0
    
    @property
    def max_latency(self) -> float:
        """Maximum latency in ms."""
        return max(self.measurements) if self.measurements else 0.0
    
    @property
    def avg_queries(self) -> float:
        """Average query count per operation."""
        if not self.query_counts:
            return 0.0
        return statistics.mean(self.query_counts)
    
    @property
    def max_queries(self) -> int:
        """Maximum query count."""
        return max(self.query_counts) if self.query_counts else 0
    
    @property
    def error_rate(self) -> float:
        """Error rate as percentage."""
        total = self.count + len(self.errors)
        if total == 0:
            return 0.0
        return (len(self.errors) / total) * 100
    
    @property
    def throughput(self) -> float:
        """Requests per second based on total time."""
        if not self.measurements:
            return 0.0
        total_time_sec = sum(self.measurements) / 1000
        if total_time_sec == 0:
            return 0.0
        return self.count / total_time_sec
    
    def report(self) -> Dict[str, Any]:
        """Generate a structured report of all metrics."""
        report = {
            'name': self.name,
            'count': self.count,
            'latency': {
                'p50_ms': round(self.p50, 2),
                'p95_ms': round(self.p95, 2),
                'p99_ms': round(self.p99, 2),
                'mean_ms': round(self.mean, 2),
                'min_ms': round(self.min_latency, 2),
                'max_ms': round(self.max_latency, 2),
            },
            'errors': {
                'count': len(self.errors),
                'rate_percent': round(self.error_rate, 2),
            },
            'throughput_rps': round(self.throughput, 2),
        }
        
        if self.query_counts:
            report['queries'] = {
                'avg': round(self.avg_queries, 2),
                'max': self.max_queries,
            }
        
        return report
    
    def print_report(self):
        """Print a human-readable report to stdout."""
        r = self.report()
        print(f"\n{'=' * 60}")
        print(f"Performance Report: {r['name']}")
        print(f"{'=' * 60}")
        print(f"  Samples: {r['count']}")
        print(f"  Latency:")
        print(f"    p50: {r['latency']['p50_ms']:.2f}ms")
        print(f"    p95: {r['latency']['p95_ms']:.2f}ms")
        print(f"    p99: {r['latency']['p99_ms']:.2f}ms")
        print(f"    mean: {r['latency']['mean_ms']:.2f}ms")
        print(f"    min: {r['latency']['min_ms']:.2f}ms")
        print(f"    max: {r['latency']['max_ms']:.2f}ms")
        if 'queries' in r:
            print(f"  Queries:")
            print(f"    avg: {r['queries']['avg']:.2f}")
            print(f"    max: {r['queries']['max']}")
        print(f"  Errors: {r['errors']['count']} ({r['errors']['rate_percent']:.2f}%)")
        print(f"  Throughput: {r['throughput_rps']:.2f} req/s")
        print(f"{'=' * 60}\n")
    
    def assert_p95_under(self, threshold_ms: float, message: str = None):
        """Assert p95 latency is under threshold."""
        if self.p95 > threshold_ms:
            msg = message or f"{self.name}: p95 latency {self.p95:.2f}ms exceeds threshold {threshold_ms}ms"
            pytest.fail(msg)
    
    def assert_queries_under(self, max_queries: int, message: str = None):
        """Assert max query count is under threshold."""
        if self.max_queries > max_queries:
            msg = message or f"{self.name}: max queries {self.max_queries} exceeds threshold {max_queries}"
            pytest.fail(msg)


# =============================================================================
# QUERY COUNT UTILITIES
# =============================================================================

@contextmanager
def assert_max_queries(max_count: int, description: str = "operation"):
    """
    Context manager to assert maximum query count.
    
    Usage:
        with assert_max_queries(5, "user list view"):
            response = client.get('/users/')
    """
    with CaptureQueriesContext(connection) as context:
        yield context
    
    actual = len(context)
    if actual > max_count:
        query_summary = "\n".join([
            f"  {i+1}. {q['sql'][:100]}..."
            for i, q in enumerate(context.captured_queries[:10])
        ])
        pytest.fail(
            f"Query count exceeded for {description}!\n"
            f"Expected: <= {max_count}\n"
            f"Actual: {actual}\n"
            f"First 10 queries:\n{query_summary}"
        )


def count_queries(func: Callable) -> int:
    """Execute a function and return the query count."""
    with CaptureQueriesContext(connection) as context:
        func()
    return len(context)


# =============================================================================
# TIMING UTILITIES
# =============================================================================

def timed_execution(func: Callable, iterations: int = 10) -> PerformanceMetrics:
    """
    Execute a function multiple times and collect timing metrics.
    
    Usage:
        metrics = timed_execution(lambda: client.get('/login/'), iterations=100)
        metrics.assert_p95_under(500)
    """
    metrics = PerformanceMetrics(name=func.__name__ if hasattr(func, '__name__') else 'anonymous')
    
    for _ in range(iterations):
        try:
            with metrics.measure():
                func()
        except Exception as e:
            metrics.add_error(str(e))
    
    return metrics


# =============================================================================
# CONCURRENT EXECUTION UTILITIES
# =============================================================================

@dataclass
class ConcurrencyResult:
    """Results from concurrent operation execution."""
    successful: int = 0
    failed: int = 0
    errors: List[str] = field(default_factory=list)
    timings: List[float] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        total = self.successful + self.failed
        return (self.successful / total * 100) if total > 0 else 0.0
    
    @property
    def avg_time_ms(self) -> float:
        return statistics.mean(self.timings) if self.timings else 0.0


def run_concurrent(
    func: Callable,
    num_threads: int,
    result_tracker: Optional[ConcurrencyResult] = None
) -> ConcurrencyResult:
    """
    Run a function concurrently across multiple threads.
    
    Usage:
        def debit_wallet():
            wallet = Wallet.objects.get(user=user)
            wallet.debit(Decimal('10.00'))
        
        result = run_concurrent(debit_wallet, num_threads=50)
    """
    result = result_tracker or ConcurrencyResult()
    lock = threading.Lock()
    
    def wrapper():
        start = time.perf_counter()
        try:
            func()
            elapsed = (time.perf_counter() - start) * 1000
            with lock:
                result.successful += 1
                result.timings.append(elapsed)
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            with lock:
                result.failed += 1
                result.errors.append(str(e))
                result.timings.append(elapsed)
    
    threads = [threading.Thread(target=wrapper) for _ in range(num_threads)]
    
    for t in threads:
        t.start()
    
    for t in threads:
        t.join()
    
    return result


# =============================================================================
# TEST DATA GENERATORS
# =============================================================================

@pytest.fixture
def perf_user(db):
    """Create a test user for performance testing."""
    user = User.objects.create_user(
        username='perf_test_user',
        email='perf@example.com',
        password='testpass123'
    )
    return user


@pytest.fixture
def perf_user_with_wallet(db, perf_user):
    """Create a test user with wallet for performance testing."""
    wallet, _ = Wallet.objects.get_or_create(
        user=perf_user,
        defaults={'balance': Decimal('10000.00')}
    )
    return perf_user, wallet


@pytest.fixture
def perf_client(db):
    """Create an authenticated test client for performance testing."""
    user = User.objects.create_user(
        username='perf_client_user',
        email='perfclient@example.com',
        password='testpass123'
    )
    client = Client()
    client.force_login(user)
    return client, user


@pytest.fixture
def bulk_users(db):
    """Create bulk users for load testing."""
    def create_users(count: int) -> List[User]:
        users = []
        for i in range(count):
            user = User.objects.create_user(
                username=f'bulk_user_{i}',
                email=f'bulk{i}@example.com',
                password='testpass123'
            )
            users.append(user)
        return users
    return create_users


@pytest.fixture
def bulk_transactions(db, perf_user_with_wallet):
    """Create bulk transactions for volume testing."""
    user, wallet = perf_user_with_wallet
    
    def create_transactions(count: int) -> List[Transaction]:
        transactions = [
            Transaction(
                user=user,
                wallet=wallet,
                transaction_type='deposit',
                amount=Decimal('10.00'),
                payment_gateway='stripe',
                status='completed'
            )
            for _ in range(count)
        ]
        return Transaction.objects.bulk_create(transactions)
    
    return create_transactions


@pytest.fixture
def bulk_opportunities(db, perf_user):
    """Create bulk investment opportunities for volume testing."""
    def create_opportunities(count: int) -> List[InvestmentOpportunity]:
        opportunities = [
            InvestmentOpportunity(
                business=perf_user,
                title=f'Investment Opportunity {i}',
                slug=f'investment-opportunity-{i}',
                description='Test investment opportunity for performance testing',
                amount_seeking=Decimal('100000.00'),
                minimum_investment=Decimal('1000.00'),
                equity_percentage=Decimal('10.00'),
                industry='Technology'
            )
            for i in range(count)
        ]
        return InvestmentOpportunity.objects.bulk_create(opportunities)
    
    return create_opportunities


@pytest.fixture
def bulk_jobs(db, perf_user):
    """Create bulk job opportunities for volume testing."""
    def create_jobs(count: int) -> List[JobOpportunity]:
        jobs = [
            JobOpportunity(
                business=perf_user,
                title=f'Job Opportunity {i}',
                slug=f'job-opportunity-{i}',
                description='Test job for performance testing',
                requirements='Python, Django',
                responsibilities='Development',
                location='Remote'
            )
            for i in range(count)
        ]
        return JobOpportunity.objects.bulk_create(jobs)
    
    return create_jobs


@pytest.fixture
def subscription_plan(db):
    """Create a subscription plan for testing."""
    plan, _ = SubscriptionPlan.objects.get_or_create(
        slug='perf-test-plan',
        defaults={
            'name': 'Performance Test Plan',
            'description': 'Plan for performance testing',
            'price': Decimal('29.99'),
            'duration_days': 30,
            'is_active': True,
        }
    )
    return plan


# =============================================================================
# PYTEST MARKERS
# =============================================================================

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (load/stress/volume tests)"
    )
    config.addinivalue_line(
        "markers", "concurrency: marks tests as concurrency/race condition tests"
    )
    config.addinivalue_line(
        "markers", "latency: marks tests as latency benchmark tests"
    )
    config.addinivalue_line(
        "markers", "scalability: marks tests as scalability/volume tests"
    )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_test_category(name: str, slug: str) -> Category:
    """Create or get a test category."""
    category, _ = Category.objects.get_or_create(
        slug=slug,
        defaults={'name': name, 'is_active': True}
    )
    return category


def create_user_with_profile(username: str, category_slug: str = None) -> User:
    """Create a user with optional category assignment."""
    user = User.objects.create_user(
        username=username,
        email=f'{username}@example.com',
        password='testpass123'
    )
    if category_slug:
        category = create_test_category(category_slug.title(), category_slug)
        try:
            profile = user.profile
            profile.category = category
            profile.save()
        except Exception:
            pass
    return user
