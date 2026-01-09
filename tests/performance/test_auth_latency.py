"""
Authentication Flow Latency Benchmarks.

Tests login, registration, and dashboard performance with p50/p95 metrics.
"""

import pytest
from django.test import Client
from django.contrib.auth.models import User
from django.urls import reverse

from .conftest import (
    PerformanceMetrics,
    assert_max_queries,
    PERF_P95_MS,
    PERF_MAX_QUERIES,
)


@pytest.mark.django_db
@pytest.mark.performance
@pytest.mark.latency
class TestLoginLatency:
    """Login flow latency benchmarks."""

    def test_login_page_load__normal__under_200ms(self):
        """
        LATENCY BENCHMARK: Login page GET request.
        
        Measures time to render the login page.
        Threshold: p95 < 200ms
        """
        client = Client()
        metrics = PerformanceMetrics(name="login_page_load")
        
        # Warm up
        client.get('/login/')
        
        # Measure
        for _ in range(20):
            with metrics.measure():
                response = client.get('/login/')
            assert response.status_code == 200
        
        metrics.print_report()
        metrics.assert_p95_under(
            200,
            message=f"Login page load p95 ({metrics.p95:.2f}ms) exceeds 200ms threshold"
        )

    def test_login_post__valid_credentials__under_500ms(self, db):
        """
        LATENCY BENCHMARK: Login form submission with valid credentials.
        
        Measures authentication processing time.
        Threshold: p95 < 500ms
        """
        # Create test user
        user = User.objects.create_user(
            username='login_test_user',
            email='login@test.com',
            password='testpass123'
        )
        
        client = Client()
        metrics = PerformanceMetrics(name="login_post_valid")
        
        for _ in range(10):
            with metrics.measure():
                response = client.post('/login/', {
                    'username': 'login_test_user',
                    'password': 'testpass123'
                }, follow=False)
            # Should redirect on success
            assert response.status_code in [200, 302]
            client.logout()
        
        metrics.print_report()
        metrics.assert_p95_under(
            500,
            message=f"Login POST p95 ({metrics.p95:.2f}ms) exceeds 500ms threshold"
        )

    def test_login_post__invalid_credentials__under_300ms(self, db):
        """
        LATENCY BENCHMARK: Login with invalid credentials.
        
        Failed login should not take significantly longer than success.
        Threshold: p95 < 300ms
        """
        client = Client()
        metrics = PerformanceMetrics(name="login_post_invalid")
        
        for _ in range(10):
            with metrics.measure():
                response = client.post('/login/', {
                    'username': 'nonexistent_user',
                    'password': 'wrongpass'
                })
            assert response.status_code == 200  # Returns to login page
        
        metrics.print_report()
        metrics.assert_p95_under(
            300,
            message=f"Invalid login p95 ({metrics.p95:.2f}ms) exceeds 300ms threshold"
        )


@pytest.mark.django_db
@pytest.mark.performance
@pytest.mark.latency
class TestRegistrationLatency:
    """Registration flow latency benchmarks."""

    def test_register_page_load__normal__under_200ms(self):
        """
        LATENCY BENCHMARK: Registration page GET request.
        
        Threshold: p95 < 200ms
        """
        client = Client()
        metrics = PerformanceMetrics(name="register_page_load")
        
        # Warm up
        try:
            client.get('/register/')
        except Exception:
            pytest.skip("Registration URL not available")
        
        for _ in range(20):
            with metrics.measure():
                response = client.get('/register/')
            if response.status_code == 404:
                pytest.skip("Registration URL not configured")
            assert response.status_code == 200
        
        metrics.print_report()
        metrics.assert_p95_under(
            200,
            message=f"Register page load p95 ({metrics.p95:.2f}ms) exceeds 200ms threshold"
        )


@pytest.mark.django_db
@pytest.mark.performance
@pytest.mark.latency
class TestDashboardLatency:
    """Dashboard loading latency benchmarks."""

    def test_dashboard_redirect__authenticated__under_300ms(self, db):
        """
        LATENCY BENCHMARK: Dashboard redirect for authenticated user.
        
        Measures the time to determine user category and redirect.
        Threshold: p95 < 300ms
        """
        user = User.objects.create_user(
            username='dashboard_test_user',
            email='dashboard@test.com',
            password='testpass123'
        )
        
        client = Client()
        client.force_login(user)
        metrics = PerformanceMetrics(name="dashboard_redirect")
        
        for _ in range(10):
            with metrics.measure():
                response = client.get('/dashboard/', follow=False)
            # May redirect or render directly
            assert response.status_code in [200, 301, 302]
        
        metrics.print_report()
        metrics.assert_p95_under(
            300,
            message=f"Dashboard redirect p95 ({metrics.p95:.2f}ms) exceeds 300ms threshold"
        )

    def test_profile_view__authenticated__under_300ms(self, db):
        """
        LATENCY BENCHMARK: User profile page load.
        
        Threshold: p95 < 300ms
        """
        user = User.objects.create_user(
            username='profile_test_user',
            email='profile@test.com',
            password='testpass123'
        )
        
        client = Client()
        client.force_login(user)
        metrics = PerformanceMetrics(name="profile_view")
        
        for _ in range(10):
            with metrics.measure():
                response = client.get(f'/profile/{user.username}/')
            if response.status_code == 404:
                # Try alternate URL patterns
                response = client.get('/profile/')
            assert response.status_code in [200, 301, 302]
        
        metrics.print_report()
        metrics.assert_p95_under(
            300,
            message=f"Profile view p95 ({metrics.p95:.2f}ms) exceeds 300ms threshold"
        )


@pytest.mark.django_db
@pytest.mark.performance
@pytest.mark.latency
class TestAuthQueryCounts:
    """Query count tests for authentication views."""

    def test_login_page__query_count__under_5(self):
        """
        QUERY EFFICIENCY: Login page should use minimal queries.
        
        Expected: <= 5 queries (session, middleware, context)
        """
        client = Client()
        
        with assert_max_queries(5, "login page GET"):
            response = client.get('/login/')
        
        assert response.status_code == 200

    def test_authenticated_request__query_count__under_10(self, db):
        """
        QUERY EFFICIENCY: Authenticated page request queries.
        
        Session + user + profile loading should be minimal.
        """
        user = User.objects.create_user(
            username='query_test_user',
            email='querytest@test.com',
            password='testpass123'
        )
        
        client = Client()
        client.force_login(user)
        
        # First request after login (may have more queries for session setup)
        with assert_max_queries(10, "authenticated home page"):
            response = client.get('/')
        
        assert response.status_code in [200, 301, 302]


@pytest.mark.django_db
@pytest.mark.performance
@pytest.mark.latency
class TestAuthThroughput:
    """Authentication throughput under simulated load."""

    @pytest.mark.slow
    def test_login_throughput__50_sequential__report(self, db):
        """
        THROUGHPUT TEST: Sequential login requests.
        
        Measures sustained login throughput.
        Reports requests/second achieved.
        """
        user = User.objects.create_user(
            username='throughput_user',
            email='throughput@test.com',
            password='testpass123'
        )
        
        client = Client()
        metrics = PerformanceMetrics(name="login_throughput")
        
        for _ in range(50):
            with metrics.measure():
                response = client.post('/login/', {
                    'username': 'throughput_user',
                    'password': 'testpass123'
                }, follow=False)
            client.logout()
        
        metrics.print_report()
        
        # Report only - no hard assertion on throughput
        print(f"\nLogin Throughput: {metrics.throughput:.2f} requests/second")
        print(f"Mean latency: {metrics.mean:.2f}ms")
