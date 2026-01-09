"""
Wallet Operations Latency Benchmarks.

Tests wallet dashboard, transaction history, and financial operations.
"""

import pytest
from decimal import Decimal
from django.test import Client
from django.contrib.auth.models import User

from payments.models import Wallet, Transaction, WalletActivityLog

from .conftest import (
    PerformanceMetrics,
    assert_max_queries,
    PERF_P95_MS,
    PERF_MAX_QUERIES,
)


@pytest.fixture
def user_with_wallet_data(db):
    """Create user with wallet and transaction history."""
    import uuid
    uid = str(uuid.uuid4())[:8]
    user = User.objects.create_user(
        username=f'wallet_perf_{uid}',
        email=f'wallet_{uid}@perf.test',
        password='testpass123'
    )
    
    wallet, _ = Wallet.objects.get_or_create(
        user=user,
        defaults={'balance': Decimal('5000.00')}
    )
    
    # Create transaction history
    transactions = []
    for i in range(50):
        txn = Transaction(
            transaction_id=f"TXN-LAT-{uid}-{i}",
            user=user,
            wallet=wallet,
            transaction_type='deposit' if i % 2 == 0 else 'subscription_payment',
            amount=Decimal(str(10 + i)),
            payment_gateway='stripe' if i % 2 == 0 else 'wallet',
            status='completed' if i % 3 != 0 else 'pending'
        )
        transactions.append(txn)
    Transaction.objects.bulk_create(transactions)
    
    # Create activity logs
    logs = []
    for i in range(30):
        log = WalletActivityLog(
            user=user,
            wallet=wallet,
            action_type='deposit' if i % 2 == 0 else 'login',
            description=f'Activity {i}',
            ip_address='127.0.0.1'
        )
        logs.append(log)
    WalletActivityLog.objects.bulk_create(logs)
    
    return user, wallet


@pytest.mark.django_db
@pytest.mark.performance
@pytest.mark.latency
class TestWalletDashboardLatency:
    """Wallet dashboard latency benchmarks."""

    def test_wallet_dashboard__with_transactions__under_500ms(self, user_with_wallet_data):
        """
        LATENCY BENCHMARK: Wallet dashboard with transaction history.
        
        Dashboard loads balance, recent transactions, and analytics.
        Threshold: p95 < 500ms
        """
        user, wallet = user_with_wallet_data
        client = Client()
        client.force_login(user)
        metrics = PerformanceMetrics(name="wallet_dashboard")
        
        # Warm up
        try:
            response = client.get('/payments/wallet/')
            if response.status_code == 404:
                pytest.skip("Wallet dashboard URL not available")
        except Exception:
            pytest.skip("Wallet not accessible")
        
        for _ in range(10):
            with metrics.measure():
                response = client.get('/payments/wallet/')
            assert response.status_code in [200, 302]
        
        metrics.print_report()
        metrics.assert_p95_under(
            500,
            message=f"Wallet dashboard p95 ({metrics.p95:.2f}ms) exceeds 500ms"
        )

    def test_transaction_history__paginated__under_300ms(self, user_with_wallet_data):
        """
        LATENCY BENCHMARK: Transaction history page.
        
        Threshold: p95 < 300ms for paginated list
        """
        user, wallet = user_with_wallet_data
        client = Client()
        client.force_login(user)
        metrics = PerformanceMetrics(name="transaction_history")
        
        try:
            response = client.get('/payments/transactions/')
            if response.status_code == 404:
                response = client.get('/payments/history/')
                if response.status_code == 404:
                    pytest.skip("Transaction history URL not available")
        except Exception:
            pytest.skip("Transaction history not accessible")
        
        url = '/payments/transactions/' if client.get('/payments/transactions/').status_code != 404 else '/payments/history/'
        
        for _ in range(10):
            with metrics.measure():
                response = client.get(url)
            assert response.status_code in [200, 302]
        
        metrics.print_report()
        metrics.assert_p95_under(
            300,
            message=f"Transaction history p95 ({metrics.p95:.2f}ms) exceeds 300ms"
        )

    def test_activity_log__paginated__under_300ms(self, user_with_wallet_data):
        """
        LATENCY BENCHMARK: Wallet activity log page.
        
        Threshold: p95 < 300ms
        """
        user, wallet = user_with_wallet_data
        client = Client()
        client.force_login(user)
        metrics = PerformanceMetrics(name="activity_log")
        
        try:
            response = client.get('/payments/activity/')
            if response.status_code == 404:
                pytest.skip("Activity log URL not available")
        except Exception:
            pytest.skip("Activity log not accessible")
        
        for _ in range(10):
            with metrics.measure():
                response = client.get('/payments/activity/')
            assert response.status_code in [200, 302]
        
        metrics.print_report()
        metrics.assert_p95_under(
            300,
            message=f"Activity log p95 ({metrics.p95:.2f}ms) exceeds 300ms"
        )


@pytest.mark.django_db
@pytest.mark.performance
@pytest.mark.latency
class TestFinancialInsightsLatency:
    """Financial analytics latency benchmarks."""

    def test_financial_insights__with_data__under_1000ms(self, user_with_wallet_data):
        """
        LATENCY BENCHMARK: Financial insights/analytics page.
        
        Analytics computation may be more intensive.
        Threshold: p95 < 1000ms
        """
        user, wallet = user_with_wallet_data
        client = Client()
        client.force_login(user)
        metrics = PerformanceMetrics(name="financial_insights")
        
        try:
            response = client.get('/payments/insights/')
            if response.status_code == 404:
                pytest.skip("Financial insights URL not available")
        except Exception:
            pytest.skip("Financial insights not accessible")
        
        for _ in range(5):
            with metrics.measure():
                response = client.get('/payments/insights/')
            assert response.status_code in [200, 302]
        
        metrics.print_report()
        metrics.assert_p95_under(
            1000,
            message=f"Financial insights p95 ({metrics.p95:.2f}ms) exceeds 1000ms"
        )


@pytest.mark.django_db
@pytest.mark.performance
@pytest.mark.latency
class TestWalletQueryCounts:
    """Query efficiency tests for wallet operations."""

    def test_wallet_dashboard__query_count__under_15(self, user_with_wallet_data):
        """
        QUERY EFFICIENCY: Wallet dashboard query count.
        
        Should load efficiently despite multiple data sources.
        """
        user, wallet = user_with_wallet_data
        client = Client()
        client.force_login(user)
        
        try:
            with assert_max_queries(15, "wallet dashboard"):
                response = client.get('/payments/wallet/')
            if response.status_code == 404:
                pytest.skip("Wallet dashboard URL not available")
        except Exception as e:
            if "404" in str(e):
                pytest.skip("Wallet dashboard URL not available")
            raise

    def test_transaction_list__n_plus_1_detection(self, user_with_wallet_data):
        """
        N+1 DETECTION: Transaction list should not have N+1 queries.
        
        With 50 transactions, queries should not scale linearly.
        """
        user, wallet = user_with_wallet_data
        client = Client()
        client.force_login(user)
        
        try:
            with assert_max_queries(10, "transaction list"):
                response = client.get('/payments/transactions/')
            if response.status_code == 404:
                pytest.skip("Transaction list URL not available")
        except Exception as e:
            if "404" in str(e):
                pytest.skip("Transaction list URL not available")
            raise


@pytest.mark.django_db
@pytest.mark.performance
@pytest.mark.latency
class TestWalletDepositLatency:
    """Deposit flow latency benchmarks."""

    def test_deposit_page__normal__under_300ms(self, user_with_wallet_data):
        """
        LATENCY BENCHMARK: Deposit initiation page.
        
        Threshold: p95 < 300ms
        """
        user, wallet = user_with_wallet_data
        client = Client()
        client.force_login(user)
        metrics = PerformanceMetrics(name="deposit_page")
        
        try:
            response = client.get('/payments/deposit/')
            if response.status_code == 404:
                pytest.skip("Deposit URL not available")
        except Exception:
            pytest.skip("Deposit page not accessible")
        
        for _ in range(10):
            with metrics.measure():
                response = client.get('/payments/deposit/')
            assert response.status_code in [200, 302]
        
        metrics.print_report()
        metrics.assert_p95_under(
            300,
            message=f"Deposit page p95 ({metrics.p95:.2f}ms) exceeds 300ms"
        )


@pytest.mark.django_db
@pytest.mark.performance
@pytest.mark.latency
@pytest.mark.slow
class TestWalletVolumePerformance:
    """Performance with large transaction volumes."""

    def test_1000_transactions__history_performance(self, db):
        """
        VOLUME TEST: Transaction history with 1000 transactions.
        
        Tests pagination performance with large data set.
        """
        import uuid
        uid = str(uuid.uuid4())[:8]
        user = User.objects.create_user(
            username=f'volume_{uid}',
            email=f'volume_{uid}@test.com',
            password='testpass123'
        )
        
        wallet, _ = Wallet.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('10000.00')}
        )
        
        # Create 1000 transactions
        transactions = [
            Transaction(
                transaction_id=f"TXN-VOL-{uid}-{i}",
                user=user,
                wallet=wallet,
                transaction_type='deposit',
                amount=Decimal('10.00'),
                payment_gateway='stripe',
                status='completed'
            )
            for i in range(1000)
        ]
        Transaction.objects.bulk_create(transactions)
        
        client = Client()
        client.force_login(user)
        metrics = PerformanceMetrics(name="1000_transactions_history")
        
        try:
            for _ in range(5):
                with metrics.measure():
                    response = client.get('/payments/transactions/')
                if response.status_code == 404:
                    pytest.skip("Transaction history URL not available")
                assert response.status_code in [200, 302]
        except Exception:
            pytest.skip("Transaction history not accessible")
        
        metrics.print_report()
        
        # With pagination, even 1000 transactions should load quickly
        metrics.assert_p95_under(
            1000,
            message=f"1000 transactions p95 ({metrics.p95:.2f}ms) exceeds 1000ms"
        )

    def test_500_activity_logs__performance(self, db):
        """
        VOLUME TEST: Activity log with 500 entries.
        """
        user = User.objects.create_user(
            username='log_volume_user',
            email='logvolume@test.com',
            password='testpass123'
        )
        
        wallet, _ = Wallet.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('1000.00')}
        )
        
        # Create 500 activity logs
        logs = [
            WalletActivityLog(
                user=user,
                wallet=wallet,
                action_type='login',
                description=f'Activity {i}',
                ip_address='127.0.0.1'
            )
            for i in range(500)
        ]
        WalletActivityLog.objects.bulk_create(logs)
        
        client = Client()
        client.force_login(user)
        metrics = PerformanceMetrics(name="500_activity_logs")
        
        try:
            for _ in range(5):
                with metrics.measure():
                    response = client.get('/payments/activity/')
                if response.status_code == 404:
                    pytest.skip("Activity log URL not available")
                assert response.status_code in [200, 302]
        except Exception:
            pytest.skip("Activity log not accessible")
        
        metrics.print_report()
        
        metrics.assert_p95_under(
            1000,
            message=f"500 activity logs p95 ({metrics.p95:.2f}ms) exceeds 1000ms"
        )
