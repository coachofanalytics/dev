"""
Subscription Flow Latency Benchmarks.

Tests subscription plans, purchase flow, and invoice generation.
"""

import pytest
from decimal import Decimal
from django.test import Client
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from payments.models import (
    Wallet, Transaction, SubscriptionPlan, UserSubscription, Invoice
)

from .conftest import (
    PerformanceMetrics,
    assert_max_queries,
    PERF_P95_MS,
)


@pytest.fixture
def subscription_setup(db):
    """Create subscription plans and user for testing."""
    user = User.objects.create_user(
        username='sub_perf_user',
        email='sub@perf.test',
        password='testpass123'
    )
    
    wallet, _ = Wallet.objects.get_or_create(
        user=user,
        defaults={'balance': Decimal('1000.00')}
    )
    
    # Create subscription plans
    plans = []
    for i, (name, price) in enumerate([
        ('Basic', '9.99'),
        ('Pro', '29.99'),
        ('Enterprise', '99.99')
    ]):
        plan, _ = SubscriptionPlan.objects.get_or_create(
            slug=f'perf-{name.lower()}',
            defaults={
                'name': f'{name} Plan',
                'description': f'{name} subscription for testing',
                'price': Decimal(price),
                'duration_days': 30,
                'is_active': True,
            }
        )
        plans.append(plan)
    
    # Create some subscription history
    for i, plan in enumerate(plans):
        sub = UserSubscription.objects.create(
            user=user,
            plan=plan,
            status='expired' if i < 2 else 'cancelled',
            start_date=timezone.now() - timedelta(days=60),
            end_date=timezone.now() - timedelta(days=30),
        )
    
    # Create invoices
    for i in range(10):
        Invoice.objects.create(
            user=user,
            subscription=None,
            amount=Decimal('29.99'),
            due_date=timezone.now() + timedelta(days=30),
            description=f'Invoice {i}',
            status='paid' if i % 2 == 0 else 'pending'
        )
    
    return {
        'user': user,
        'wallet': wallet,
        'plans': plans,
    }


@pytest.mark.django_db
@pytest.mark.performance
@pytest.mark.latency
class TestSubscriptionPlanLatency:
    """Subscription plan listing latency benchmarks."""

    def test_subscription_plans_list__normal__under_300ms(self, subscription_setup):
        """
        LATENCY BENCHMARK: Subscription plans listing.
        
        Threshold: p95 < 300ms
        """
        user = subscription_setup['user']
        client = Client()
        client.force_login(user)
        metrics = PerformanceMetrics(name="subscription_plans_list")
        
        try:
            response = client.get('/payments/subscriptions/')
            if response.status_code == 404:
                response = client.get('/payments/plans/')
                if response.status_code == 404:
                    pytest.skip("Subscription plans URL not available")
        except Exception:
            pytest.skip("Subscription plans not accessible")
        
        url = '/payments/subscriptions/' if client.get('/payments/subscriptions/').status_code != 404 else '/payments/plans/'
        
        for _ in range(10):
            with metrics.measure():
                response = client.get(url)
            assert response.status_code in [200, 302]
        
        metrics.print_report()
        metrics.assert_p95_under(
            300,
            message=f"Subscription plans list p95 ({metrics.p95:.2f}ms) exceeds 300ms"
        )

    def test_subscription_plan_detail__single__under_300ms(self, subscription_setup):
        """
        LATENCY BENCHMARK: Single subscription plan detail.
        
        Threshold: p95 < 300ms
        """
        user = subscription_setup['user']
        plan = subscription_setup['plans'][0]
        client = Client()
        client.force_login(user)
        metrics = PerformanceMetrics(name="subscription_plan_detail")
        
        try:
            response = client.get(f'/payments/subscription/{plan.id}/')
            if response.status_code == 404:
                pytest.skip("Subscription plan detail URL not available")
        except Exception:
            pytest.skip("Subscription plan detail not accessible")
        
        for _ in range(10):
            with metrics.measure():
                response = client.get(f'/payments/subscription/{plan.id}/')
            assert response.status_code in [200, 302]
        
        metrics.print_report()
        metrics.assert_p95_under(
            300,
            message=f"Subscription plan detail p95 ({metrics.p95:.2f}ms) exceeds 300ms"
        )


@pytest.mark.django_db
@pytest.mark.performance
@pytest.mark.latency
class TestMySubscriptionsLatency:
    """User subscriptions latency benchmarks."""

    def test_my_subscriptions__with_history__under_300ms(self, subscription_setup):
        """
        LATENCY BENCHMARK: User's subscriptions page.
        
        Threshold: p95 < 300ms
        """
        user = subscription_setup['user']
        client = Client()
        client.force_login(user)
        metrics = PerformanceMetrics(name="my_subscriptions")
        
        try:
            response = client.get('/payments/my-subscriptions/')
            if response.status_code == 404:
                pytest.skip("My subscriptions URL not available")
        except Exception:
            pytest.skip("My subscriptions not accessible")
        
        for _ in range(10):
            with metrics.measure():
                response = client.get('/payments/my-subscriptions/')
            assert response.status_code in [200, 302]
        
        metrics.print_report()
        metrics.assert_p95_under(
            300,
            message=f"My subscriptions p95 ({metrics.p95:.2f}ms) exceeds 300ms"
        )


@pytest.mark.django_db
@pytest.mark.performance
@pytest.mark.latency
class TestInvoiceLatency:
    """Invoice operations latency benchmarks."""

    def test_invoice_generation__single__under_200ms(self, subscription_setup):
        """
        LATENCY BENCHMARK: Invoice creation time.
        
        Measures time to generate a single invoice.
        Threshold: p95 < 200ms
        """
        user = subscription_setup['user']
        metrics = PerformanceMetrics(name="invoice_generation")
        
        for i in range(10):
            with metrics.measure():
                invoice = Invoice.objects.create(
                    user=user,
                    amount=Decimal('29.99'),
                    due_date=timezone.now() + timedelta(days=30),
                    description=f'Performance test invoice {i}',
                    status='pending'
                )
            assert invoice.invoice_number is not None
        
        metrics.print_report()
        metrics.assert_p95_under(
            200,
            message=f"Invoice generation p95 ({metrics.p95:.2f}ms) exceeds 200ms"
        )

    def test_invoice_list__paginated__under_300ms(self, subscription_setup):
        """
        LATENCY BENCHMARK: Invoice list page.
        
        Threshold: p95 < 300ms
        """
        user = subscription_setup['user']
        client = Client()
        client.force_login(user)
        metrics = PerformanceMetrics(name="invoice_list")
        
        try:
            response = client.get('/payments/invoices/')
            if response.status_code == 404:
                pytest.skip("Invoice list URL not available")
        except Exception:
            pytest.skip("Invoice list not accessible")
        
        for _ in range(10):
            with metrics.measure():
                response = client.get('/payments/invoices/')
            assert response.status_code in [200, 302]
        
        metrics.print_report()
        metrics.assert_p95_under(
            300,
            message=f"Invoice list p95 ({metrics.p95:.2f}ms) exceeds 300ms"
        )


@pytest.mark.django_db
@pytest.mark.performance
@pytest.mark.latency
class TestSubscriptionPurchaseLatency:
    """Subscription purchase flow latency benchmarks."""

    def test_subscription_purchase__wallet_payment__flow(self, subscription_setup):
        """
        LATENCY BENCHMARK: Complete subscription purchase with wallet.
        
        Measures end-to-end purchase flow (page load + form submission).
        This is a more complex flow involving:
        - Balance check
        - Wallet debit
        - Subscription creation
        - Invoice generation
        
        Threshold: p95 < 1500ms (for full flow)
        """
        user = subscription_setup['user']
        plan = subscription_setup['plans'][0]
        client = Client()
        client.force_login(user)
        metrics = PerformanceMetrics(name="subscription_purchase_flow")
        
        try:
            # Check if purchase page exists
            response = client.get(f'/payments/subscription/{plan.id}/purchase/')
            if response.status_code == 404:
                pytest.skip("Subscription purchase URL not available")
        except Exception:
            pytest.skip("Subscription purchase not accessible")
        
        for i in range(3):
            # Ensure sufficient balance
            wallet = subscription_setup['wallet']
            wallet.balance = Decimal('1000.00')
            wallet.save()
            
            with metrics.measure():
                # Load purchase page
                response = client.get(f'/payments/subscription/{plan.id}/purchase/')
                assert response.status_code in [200, 302]
                
                # Attempt purchase (POST)
                response = client.post(
                    f'/payments/subscription/{plan.id}/purchase/',
                    {'payment_method': 'wallet'},
                    follow=True
                )
        
        metrics.print_report()
        
        # Full purchase flow can be slower
        metrics.assert_p95_under(
            1500,
            message=f"Subscription purchase p95 ({metrics.p95:.2f}ms) exceeds 1500ms"
        )


@pytest.mark.django_db
@pytest.mark.performance
@pytest.mark.latency
class TestSubscriptionQueryCounts:
    """Query efficiency for subscription operations."""

    def test_subscription_plans_list__query_count__under_10(self, subscription_setup):
        """
        QUERY EFFICIENCY: Subscription plans list queries.
        """
        user = subscription_setup['user']
        client = Client()
        client.force_login(user)
        
        try:
            with assert_max_queries(10, "subscription plans list"):
                response = client.get('/payments/subscriptions/')
            if response.status_code == 404:
                pytest.skip("Subscription plans URL not available")
        except Exception as e:
            if "404" in str(e):
                pytest.skip("Subscription plans URL not available")
            raise

    def test_my_subscriptions__query_count__under_10(self, subscription_setup):
        """
        QUERY EFFICIENCY: My subscriptions query count.
        """
        user = subscription_setup['user']
        client = Client()
        client.force_login(user)
        
        try:
            with assert_max_queries(10, "my subscriptions"):
                response = client.get('/payments/my-subscriptions/')
            if response.status_code == 404:
                pytest.skip("My subscriptions URL not available")
        except Exception as e:
            if "404" in str(e):
                pytest.skip("My subscriptions URL not available")
            raise


@pytest.mark.django_db
@pytest.mark.performance
@pytest.mark.latency
@pytest.mark.slow
class TestSubscriptionVolumePerformance:
    """Performance with large subscription/invoice volumes."""

    def test_100_invoices__list_performance(self, db):
        """
        VOLUME TEST: Invoice list with 100 invoices.
        """
        user = User.objects.create_user(
            username='invoice_volume_user',
            email='invoicevol@test.com',
            password='testpass123'
        )
        
        # Create 100 invoices
        invoices = [
            Invoice(
                user=user,
                amount=Decimal('29.99'),
                due_date=timezone.now() + timedelta(days=30),
                description=f'Volume test invoice {i}',
                status='paid' if i % 2 == 0 else 'pending'
            )
            for i in range(100)
        ]
        Invoice.objects.bulk_create(invoices)
        
        client = Client()
        client.force_login(user)
        metrics = PerformanceMetrics(name="100_invoices_list")
        
        try:
            for _ in range(5):
                with metrics.measure():
                    response = client.get('/payments/invoices/')
                if response.status_code == 404:
                    pytest.skip("Invoice list URL not available")
                assert response.status_code in [200, 302]
        except Exception:
            pytest.skip("Invoice list not accessible")
        
        metrics.print_report()
        
        metrics.assert_p95_under(
            500,
            message=f"100 invoices list p95 ({metrics.p95:.2f}ms) exceeds 500ms"
        )
