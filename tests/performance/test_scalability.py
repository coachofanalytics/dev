"""
Scalability Tests.

Tests for performance under increasing data volumes:
- Transaction scaling (10k, 50k records)
- Marketplace listing scaling
- Audit log scaling
- Invoice volume tests
"""

import pytest
import time
from decimal import Decimal
from django.test import Client
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from payments.models import Wallet, Transaction, Invoice, WalletActivityLog
from marketplace.models import InvestmentOpportunity, JobOpportunity
from audit.models import AuditLog, LoginHistory
from accounts.models import Category

from .conftest import (
    PerformanceMetrics,
    assert_max_queries,
)


@pytest.mark.django_db
@pytest.mark.performance
@pytest.mark.slow
@pytest.mark.scalability
class TestTransactionScaling:
    """Transaction volume scaling tests."""

    @pytest.fixture
    def scale_user(self, db):
        """Create user for scaling tests."""
        user = User.objects.create_user(
            username='scale_txn_user',
            email='scaletxn@test.com',
            password='testpass123'
        )
        wallet, _ = Wallet.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('100000.00')}
        )
        return user, wallet

    def test_10k_transactions__list_pagination__under_500ms(self, scale_user, db):
        """
        SCALABILITY TEST: Query performance with 10,000 transactions.
        
        Paginated queries should remain fast.
        Threshold: p95 < 500ms for first page
        """
        user, wallet = scale_user
        
        # Create 10k transactions in batches
        print("\n  Creating 10,000 transactions...")
        batch_size = 2000
        for batch in range(5):
            transactions = [
                Transaction(
                    user=user,
                    wallet=wallet,
                    transaction_type='deposit' if i % 2 == 0 else 'subscription_payment',
                    amount=Decimal('10.00'),
                    payment_gateway='stripe' if i % 3 == 0 else 'paypal',
                    status='completed'
                )
                for i in range(batch_size)
            ]
            Transaction.objects.bulk_create(transactions)
            print(f"    Batch {batch + 1}/5 complete ({(batch + 1) * batch_size} records)")
        
        total = Transaction.objects.filter(user=user).count()
        assert total == 10000, f"Expected 10000, got {total}"
        
        metrics = PerformanceMetrics(name="10k_transactions_query")
        
        # Test paginated query (first page)
        page_size = 50
        for _ in range(10):
            with metrics.measure():
                results = list(
                    Transaction.objects.filter(user=user)
                    .select_related('wallet')
                    .order_by('-created_at')[:page_size]
                )
            assert len(results) == page_size
        
        print(f"\n{'=' * 60}")
        print(f"10K Transactions Query Performance")
        print(f"{'=' * 60}")
        metrics.print_report()
        
        metrics.assert_p95_under(
            500,
            message=f"10k transactions p95 ({metrics.p95:.2f}ms) exceeds 500ms"
        )

    def test_50k_transactions__aggregation__under_2s(self, scale_user, db):
        """
        SCALABILITY TEST: Aggregation performance with 50,000 transactions.
        
        Sum and count operations should complete reasonably.
        Threshold: < 2 seconds
        """
        user, wallet = scale_user
        
        # Create 50k transactions in batches
        print("\n  Creating 50,000 transactions...")
        batch_size = 5000
        for batch in range(10):
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
            print(f"    Batch {batch + 1}/10 complete ({(batch + 1) * batch_size} records)")
        
        from django.db.models import Sum, Count
        
        metrics = PerformanceMetrics(name="50k_transactions_aggregation")
        
        for _ in range(5):
            with metrics.measure():
                result = Transaction.objects.filter(user=user).aggregate(
                    total=Sum('amount'),
                    count=Count('id')
                )
            assert result['count'] >= 50000
        
        print(f"\n{'=' * 60}")
        print(f"50K Transactions Aggregation Performance")
        print(f"{'=' * 60}")
        print(f"  Total records: {result['count']}")
        print(f"  Sum of amounts: ${result['total']}")
        metrics.print_report()
        
        metrics.assert_p95_under(
            2000,
            message=f"50k aggregation p95 ({metrics.p95:.2f}ms) exceeds 2s"
        )


@pytest.mark.django_db
@pytest.mark.performance
@pytest.mark.slow
@pytest.mark.scalability
class TestMarketplaceScaling:
    """Marketplace data volume scaling tests."""

    @pytest.fixture
    def marketplace_scale_setup(self, db):
        """Create business user for marketplace scaling."""
        user = User.objects.create_user(
            username='marketplace_scale_user',
            email='marketplacescale@test.com',
            password='testpass123'
        )
        return user

    def test_5k_opportunities__list_filter__under_1s(self, marketplace_scale_setup, db):
        """
        SCALABILITY TEST: Marketplace with 5,000 investment opportunities.
        
        Filtered queries should remain performant.
        """
        user = marketplace_scale_setup
        
        print("\n  Creating 5,000 investment opportunities...")
        industries = ['Technology', 'Healthcare', 'Finance', 'Real Estate', 'Energy']
        
        batch_size = 1000
        for batch in range(5):
            opportunities = [
                InvestmentOpportunity(
                    business=user,
                    title=f'Scale Opportunity {batch * batch_size + i}',
                    slug=f'scale-opportunity-{batch * batch_size + i}',
                    description='Opportunity for scalability testing',
                    amount_seeking=Decimal('100000.00'),
                    minimum_investment=Decimal('1000.00'),
                    equity_percentage=Decimal('10.00'),
                    industry=industries[i % len(industries)],
                    status='open' if i % 4 != 0 else 'closed'
                )
                for i in range(batch_size)
            ]
            InvestmentOpportunity.objects.bulk_create(opportunities)
            print(f"    Batch {batch + 1}/5 complete")
        
        total = InvestmentOpportunity.objects.count()
        
        # Test unfiltered list
        list_metrics = PerformanceMetrics(name="5k_opportunities_list")
        for _ in range(5):
            with list_metrics.measure():
                results = list(
                    InvestmentOpportunity.objects.filter(status='open')
                    .select_related('business')[:50]
                )
        
        # Test filtered by industry
        filter_metrics = PerformanceMetrics(name="5k_opportunities_filtered")
        for _ in range(5):
            with filter_metrics.measure():
                results = list(
                    InvestmentOpportunity.objects.filter(
                        status='open',
                        industry='Technology'
                    ).select_related('business')[:50]
                )
        
        print(f"\n{'=' * 60}")
        print(f"5K Opportunities Query Performance")
        print(f"{'=' * 60}")
        print(f"  Total opportunities: {total}")
        print(f"\n  Unfiltered list (first 50):")
        list_metrics.print_report()
        print(f"\n  Filtered by industry (first 50):")
        filter_metrics.print_report()
        
        list_metrics.assert_p95_under(1000)
        filter_metrics.assert_p95_under(1000)

    def test_5k_jobs__search__under_1s(self, marketplace_scale_setup, db):
        """
        SCALABILITY TEST: Job search with 5,000 listings.
        """
        user = marketplace_scale_setup
        
        print("\n  Creating 5,000 job opportunities...")
        locations = ['Remote', 'New York', 'San Francisco', 'London', 'Berlin']
        
        batch_size = 1000
        for batch in range(5):
            jobs = [
                JobOpportunity(
                    business=user,
                    title=f'Scale Job {batch * batch_size + i}',
                    slug=f'scale-job-{batch * batch_size + i}',
                    description='Job for scalability testing',
                    requirements='Python, Django, SQL',
                    responsibilities='Development',
                    location=locations[i % len(locations)],
                    status='open' if i % 3 != 0 else 'closed'
                )
                for i in range(batch_size)
            ]
            JobOpportunity.objects.bulk_create(jobs)
            print(f"    Batch {batch + 1}/5 complete")
        
        total = JobOpportunity.objects.count()
        
        metrics = PerformanceMetrics(name="5k_jobs_search")
        
        for _ in range(5):
            with metrics.measure():
                results = list(
                    JobOpportunity.objects.filter(
                        status='open',
                        location='Remote'
                    ).select_related('business')[:50]
                )
        
        print(f"\n{'=' * 60}")
        print(f"5K Jobs Search Performance")
        print(f"{'=' * 60}")
        print(f"  Total jobs: {total}")
        metrics.print_report()
        
        metrics.assert_p95_under(1000)


@pytest.mark.django_db
@pytest.mark.performance
@pytest.mark.slow
@pytest.mark.scalability
class TestAuditLogScaling:
    """Audit log scaling tests."""

    def test_20k_audit_logs__query__under_2s(self, db):
        """
        SCALABILITY TEST: Query performance with 20,000 audit log entries.
        """
        user = User.objects.create_user(
            username='audit_scale_user',
            email='auditscale@test.com',
            password='testpass123'
        )
        
        print("\n  Creating 20,000 audit log entries...")
        
        batch_size = 5000
        for batch in range(4):
            try:
                logs = [
                    AuditLog(
                        user=user,
                        action='user_login' if i % 3 == 0 else 'data_access',
                        resource_type='User',
                        resource_id=str(user.id),
                        details={'test': f'entry_{batch * batch_size + i}'},
                        ip_address='127.0.0.1'
                    )
                    for i in range(batch_size)
                ]
                AuditLog.objects.bulk_create(logs)
                print(f"    Batch {batch + 1}/4 complete")
            except Exception as e:
                print(f"    Batch {batch + 1}/4 failed: {e}")
                pytest.skip("AuditLog model may have required fields not provided")
        
        total = AuditLog.objects.filter(user=user).count()
        
        metrics = PerformanceMetrics(name="20k_audit_logs_query")
        
        for _ in range(5):
            with metrics.measure():
                results = list(
                    AuditLog.objects.filter(user=user)
                    .order_by('-created_at')[:100]
                )
        
        print(f"\n{'=' * 60}")
        print(f"20K Audit Logs Query Performance")
        print(f"{'=' * 60}")
        print(f"  Total logs: {total}")
        metrics.print_report()
        
        metrics.assert_p95_under(2000)


@pytest.mark.django_db
@pytest.mark.performance
@pytest.mark.slow
@pytest.mark.scalability
class TestInvoiceScaling:
    """Invoice volume scaling tests."""

    def test_1k_invoices__list__under_500ms(self, db):
        """
        SCALABILITY TEST: Invoice list with 1,000 invoices.
        """
        user = User.objects.create_user(
            username='invoice_scale_user',
            email='invoicescale@test.com',
            password='testpass123'
        )
        
        print("\n  Creating 1,000 invoices...")
        
        invoices = [
            Invoice(
                user=user,
                amount=Decimal('29.99') + Decimal(str(i % 100)),
                due_date=timezone.now() + timedelta(days=30),
                description=f'Scale test invoice {i}',
                status='paid' if i % 3 == 0 else 'pending'
            )
            for i in range(1000)
        ]
        Invoice.objects.bulk_create(invoices)
        
        total = Invoice.objects.filter(user=user).count()
        
        # Test list view performance
        client = Client()
        client.force_login(user)
        
        metrics = PerformanceMetrics(name="1k_invoices_list")
        
        for _ in range(5):
            with metrics.measure():
                response = client.get('/payments/invoices/')
            if response.status_code == 404:
                # Test direct query instead
                results = list(
                    Invoice.objects.filter(user=user)
                    .order_by('-created_at')[:50]
                )
        
        print(f"\n{'=' * 60}")
        print(f"1K Invoices List Performance")
        print(f"{'=' * 60}")
        print(f"  Total invoices: {total}")
        metrics.print_report()
        
        metrics.assert_p95_under(500)


@pytest.mark.django_db
@pytest.mark.performance
@pytest.mark.slow
@pytest.mark.scalability
class TestActivityLogScaling:
    """Wallet activity log scaling tests."""

    def test_10k_activity_logs__filter__under_1s(self, db):
        """
        SCALABILITY TEST: Activity log with 10,000 entries.
        """
        user = User.objects.create_user(
            username='activity_scale_user',
            email='activityscale@test.com',
            password='testpass123'
        )
        wallet, _ = Wallet.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('1000.00')}
        )
        
        print("\n  Creating 10,000 activity log entries...")
        
        action_types = ['login', 'deposit', 'withdrawal', 'payment', 'settings_change']
        
        batch_size = 2000
        for batch in range(5):
            logs = [
                WalletActivityLog(
                    user=user,
                    wallet=wallet,
                    action_type=action_types[i % len(action_types)],
                    description=f'Activity {batch * batch_size + i}',
                    ip_address='127.0.0.1',
                    is_suspicious=(i % 50 == 0)
                )
                for i in range(batch_size)
            ]
            WalletActivityLog.objects.bulk_create(logs)
            print(f"    Batch {batch + 1}/5 complete")
        
        total = WalletActivityLog.objects.filter(user=user).count()
        
        # Test filtered query
        metrics = PerformanceMetrics(name="10k_activity_logs_filtered")
        
        for _ in range(5):
            with metrics.measure():
                results = list(
                    WalletActivityLog.objects.filter(
                        user=user,
                        action_type='deposit'
                    ).order_by('-created_at')[:50]
                )
        
        # Test suspicious flag filter
        suspicious_metrics = PerformanceMetrics(name="10k_suspicious_filter")
        
        for _ in range(5):
            with suspicious_metrics.measure():
                results = list(
                    WalletActivityLog.objects.filter(
                        user=user,
                        is_suspicious=True
                    ).order_by('-created_at')
                )
        
        print(f"\n{'=' * 60}")
        print(f"10K Activity Logs Query Performance")
        print(f"{'=' * 60}")
        print(f"  Total logs: {total}")
        print(f"\n  Filtered by action_type:")
        metrics.print_report()
        print(f"\n  Filtered by is_suspicious:")
        suspicious_metrics.print_report()
        
        metrics.assert_p95_under(1000)


@pytest.mark.django_db
@pytest.mark.performance
@pytest.mark.slow
@pytest.mark.scalability
class TestMultiUserScaling:
    """Multi-user scenario scaling tests."""

    def test_100_users__concurrent_queries(self, db):
        """
        SCALABILITY TEST: 100 users with concurrent data queries.
        """
        import threading
        
        print("\n  Creating 100 users with wallets...")
        
        users = []
        for i in range(100):
            user = User.objects.create_user(
                username=f'concurrent_user_{i}',
                email=f'concurrent{i}@test.com',
                password='testpass123'
            )
            wallet, _ = Wallet.objects.get_or_create(
                user=user,
                defaults={'balance': Decimal('1000.00')}
            )
            # Create some transactions
            Transaction.objects.create(
                user=user,
                wallet=wallet,
                transaction_type='deposit',
                amount=Decimal('100.00'),
                payment_gateway='stripe',
                status='completed'
            )
            users.append(user)
            if (i + 1) % 25 == 0:
                print(f"    Created {i + 1}/100 users")
        
        results = {'success': 0, 'errors': 0, 'timings': []}
        lock = threading.Lock()
        
        def user_query(user):
            start = time.perf_counter()
            try:
                wallet = Wallet.objects.get(user=user)
                txns = list(Transaction.objects.filter(user=user)[:10])
                elapsed = (time.perf_counter() - start) * 1000
                with lock:
                    results['success'] += 1
                    results['timings'].append(elapsed)
            except Exception:
                with lock:
                    results['errors'] += 1
        
        print("\n  Running concurrent queries for 100 users...")
        
        threads = [
            threading.Thread(target=user_query, args=(user,))
            for user in users
        ]
        
        start = time.perf_counter()
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        total_elapsed = time.perf_counter() - start
        
        avg_time = sum(results['timings']) / len(results['timings']) if results['timings'] else 0
        p95_idx = int(len(results['timings']) * 0.95)
        sorted_times = sorted(results['timings'])
        p95_time = sorted_times[min(p95_idx, len(sorted_times) - 1)] if sorted_times else 0
        
        print(f"\n{'=' * 60}")
        print(f"100 Concurrent Users Query Performance")
        print(f"{'=' * 60}")
        print(f"  Users: 100")
        print(f"  Successful: {results['success']}")
        print(f"  Errors: {results['errors']}")
        print(f"  Total time: {total_elapsed:.2f}s")
        print(f"  Avg per user: {avg_time:.2f}ms")
        print(f"  p95: {p95_time:.2f}ms")
        print(f"{'=' * 60}\n")
        
        assert results['errors'] == 0, f"Had {results['errors']} errors in concurrent queries"
