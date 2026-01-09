"""
Bulk Operations and Index Performance Tests.

Comprehensive tests for:
- Bulk data creation performance
- Database index effectiveness
- N+1 query detection
- Query optimization validation
"""

import pytest
import time
from decimal import Decimal
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.db import connection
from django.contrib.auth.models import User

from payments.models import (
    Wallet, Transaction, Invoice, SubscriptionPlan, UserSubscription,
    WalletActivityLog, FraudAlert
)
from marketplace.models import BusinessProfile, InvestmentOpportunity, JobOpportunity
from accounts.models import Category, UserProfile
from audit.models import AuditLog, LoginHistory

from .conftest import (
    PerformanceMetrics,
    assert_max_queries,
    PERF_P95_MS,
    PERF_MAX_QUERIES,
)


@pytest.mark.django_db
@pytest.mark.performance
class TestBulkCreatePerformance:
    """Bulk creation performance benchmarks."""



    def test_bulk_create_transactions__500__under_5s(self, db):
        """
        BULK PERFORMANCE: Create 500 transactions in bulk.
        
        Threshold: < 5 seconds
        """
        import uuid
        uid = str(uuid.uuid4())[:8]
        user = User.objects.create_user(
            username=f'bulk_txn_{uid}',
            email=f'bulktxn_{uid}@test.com',
            password='testpass123'
        )
        wallet, _ = Wallet.objects.get_or_create(user=user)
        
        metrics = PerformanceMetrics(name="bulk_create_500_transactions")
        
        with metrics.measure():
            transactions = [
                Transaction(
                    transaction_id=f"TXN-BULK-{uid}-{i}",
                    user=user,
                    wallet=wallet,
                    transaction_type='deposit',
                    amount=Decimal('10.00'),
                    payment_gateway='stripe',
                    status='completed'
                )
                for i in range(500)
            ]
            Transaction.objects.bulk_create(transactions)
        
        count = Transaction.objects.filter(user=user).count()
        assert count == 500, f"Expected 500 transactions, got {count}"
        
        metrics.print_report()
        assert metrics.p95 < 5000, f"Bulk create took {metrics.p95:.2f}ms, exceeds 5s"

    def test_bulk_create_investment_opportunities__200__under_3s(self, db):
        """
        BULK PERFORMANCE: Create 200 investment opportunities in bulk.
        
        Threshold: < 3 seconds
        """
        import uuid
        uid = str(uuid.uuid4())[:8]
        user = User.objects.create_user(
            username=f'bulk_invest_{uid}',
            email=f'bulkinvest_{uid}@test.com',
            password='testpass123'
        )
        
        metrics = PerformanceMetrics(name="bulk_create_200_opportunities")
        
        with metrics.measure():
            opportunities = [
                InvestmentOpportunity(
                    business=user,
                    title=f'Bulk Opportunity {i} {uid}',
                    slug=f'bulk-opportunity-{i}-{uid}',
                    description='Bulk created for performance testing',
                    amount_seeking=Decimal('100000.00'),
                    minimum_investment=Decimal('1000.00'),
                    equity_percentage=Decimal('10.00'),
                    industry='Technology'
                )
                for i in range(200)
            ]
            InvestmentOpportunity.objects.bulk_create(opportunities)
        
        count = InvestmentOpportunity.objects.filter(business=user).count()
        assert count == 200, f"Expected 200 opportunities, got {count}"
        
        metrics.print_report()
        assert metrics.p95 < 3000, f"Bulk create took {metrics.p95:.2f}ms, exceeds 3s"

    def test_bulk_create_job_opportunities__200__under_3s(self, db):
        """
        BULK PERFORMANCE: Create 200 job opportunities in bulk.
        
        Threshold: < 3 seconds
        """
        import uuid
        uid = str(uuid.uuid4())[:8]
        user = User.objects.create_user(
            username=f'bulk_job_{uid}',
            email=f'bulkjob_{uid}@test.com',
            password='testpass123'
        )
        
        metrics = PerformanceMetrics(name="bulk_create_200_jobs")
        
        with metrics.measure():
            jobs = [
                JobOpportunity(
                    business=user,
                    title=f'Bulk Job {i} {uid}',
                    slug=f'bulk-job-{i}-{uid}',
                    description='Bulk created job',
                    requirements='Python, Django',
                    responsibilities='Development',
                    location='Remote'
                )
                for i in range(200)
            ]
            JobOpportunity.objects.bulk_create(jobs)
        
        count = JobOpportunity.objects.filter(business=user).count()
        assert count == 200, f"Expected 200 jobs, got {count}"
        
        metrics.print_report()
        assert metrics.p95 < 3000, f"Bulk create took {metrics.p95:.2f}ms, exceeds 3s"

    def test_bulk_create_activity_logs__1000__under_5s(self, db):
        """
        BULK PERFORMANCE: Create 1000 wallet activity logs.
        
        Threshold: < 5 seconds
        """
        import uuid
        uid = str(uuid.uuid4())[:8]
        user = User.objects.create_user(
            username=f'bulk_log_{uid}',
            email=f'bulklog_{uid}@test.com',
            password='testpass123'
        )
        wallet, _ = Wallet.objects.get_or_create(user=user)
        
        metrics = PerformanceMetrics(name="bulk_create_1000_activity_logs")
        
        with metrics.measure():
            logs = [
                WalletActivityLog(
                    user=user,
                    wallet=wallet,
                    action_type='login',
                    description=f'Activity log {i}',
                    ip_address='127.0.0.1'
                )
                for i in range(1000)
            ]
            WalletActivityLog.objects.bulk_create(logs)
        
        count = WalletActivityLog.objects.filter(user=user).count()
        assert count == 1000, f"Expected 1000 logs, got {count}"
        
        metrics.print_report()
        assert metrics.p95 < 5000, f"Bulk create took {metrics.p95:.2f}ms, exceeds 5s"

    def test_bulk_update_status__100__under_1s(self, db):
        """
        BULK PERFORMANCE: Bulk update status of 100 jobs.
        
        Threshold: < 1 second
        """
        import uuid
        uid = str(uuid.uuid4())[:8]
        user = User.objects.create_user(
            username=f'bulk_upd_{uid}',
            email=f'bulkupdate_{uid}@test.com',
            password='testpass123'
        )
        
        # Create jobs
        jobs = [
            JobOpportunity(
                business=user,
                title=f'Update Job {i} {uid}',
                slug=f'update-job-{i}-{uid}',
                description='Job for update test',
                requirements='Requirements',
                responsibilities='Responsibilities',
                location='Remote',
                status='open'
            )
            for i in range(100)
        ]
        JobOpportunity.objects.bulk_create(jobs)
        
        metrics = PerformanceMetrics(name="bulk_update_100_jobs")
        
        with metrics.measure():
            JobOpportunity.objects.filter(business=user).update(status='closed')
        
        closed_count = JobOpportunity.objects.filter(business=user, status='closed').count()
        assert closed_count == 100, f"Expected 100 closed, got {closed_count}"
        
        metrics.print_report()
        assert metrics.p95 < 1000, f"Bulk update took {metrics.p95:.2f}ms, exceeds 1s"


@pytest.mark.django_db
@pytest.mark.performance
class TestIndexEffectiveness:
    """Tests to verify database indexes are working correctly."""

    @pytest.fixture
    def indexed_transactions(self, db):
        """Create transactions for index testing."""
        import uuid
        uid = str(uuid.uuid4())[:8]
        user = User.objects.create_user(
            username=f'idx_user_{uid}',
            email=f'indextest_{uid}@test.com',
            password='testpass123'
        )
        wallet, _ = Wallet.objects.get_or_create(user=user)
        
        # Create 500 transactions
        transactions = [
            Transaction(
                transaction_id=f"TXN-IDX-{uid}-{i}",
                user=user,
                wallet=wallet,
                transaction_type='deposit' if i % 2 == 0 else 'subscription_payment',
                amount=Decimal(str(10 + i)),
                payment_gateway='stripe' if i % 3 == 0 else 'paypal',
                status='completed' if i % 4 == 0 else 'pending'
            )
            for i in range(500)
        ]
        Transaction.objects.bulk_create(transactions)
        
        return user, wallet

    def test_transaction_id_index__lookup__under_50ms(self, indexed_transactions):
        """
        INDEX TEST: Transaction ID lookup should use index.
        
        Primary key/unique index should make this instant.
        """
        user, wallet = indexed_transactions
        txn = Transaction.objects.filter(user=user).first()
        
        metrics = PerformanceMetrics(name="transaction_id_lookup")
        
        for _ in range(20):
            with metrics.measure():
                result = Transaction.objects.filter(
                    transaction_id=txn.transaction_id
                ).first()
            assert result is not None
        
        metrics.print_report()
        metrics.assert_p95_under(
            50,
            message=f"Transaction ID lookup p95 ({metrics.p95:.2f}ms) exceeds 50ms"
        )

    def test_user_transaction_index__filter__under_100ms(self, indexed_transactions):
        """
        INDEX TEST: User + created_at filter should use composite index.
        """
        user, wallet = indexed_transactions
        
        metrics = PerformanceMetrics(name="user_transaction_filter")
        
        for _ in range(20):
            with metrics.measure():
                results = list(
                    Transaction.objects.filter(user=user)
                    .order_by('-created_at')[:50]
                )
            assert len(results) == 50
        
        metrics.print_report()
        metrics.assert_p95_under(
            100,
            message=f"User transaction filter p95 ({metrics.p95:.2f}ms) exceeds 100ms"
        )

    def test_status_filter_index__count__under_100ms(self, indexed_transactions):
        """
        INDEX TEST: Status filter should use index.
        """
        metrics = PerformanceMetrics(name="status_filter")
        
        for _ in range(20):
            with metrics.measure():
                count = Transaction.objects.filter(status='completed').count()
            assert count > 0
        
        metrics.print_report()
        metrics.assert_p95_under(
            100,
            message=f"Status filter p95 ({metrics.p95:.2f}ms) exceeds 100ms"
        )

    def test_index_metadata_present__transaction_model(self, db):
        """
        INDEX VALIDATION: Verify Transaction model has expected indexes.
        """
        meta = Transaction._meta
        
        # Check indexes are defined
        assert hasattr(meta, 'indexes'), "Transaction model should have indexes"
        
        # Get index field names
        index_fields = []
        for index in meta.indexes:
            # index.fields is a list of strings (field names)
            index_fields.extend(index.fields)
        
        # Should have indexes on key fields
        expected_indexed_fields = ['transaction_id', 'user', 'status']
        for field in expected_indexed_fields:
            # Check either in indexes or in unique fields
            # Note: models.Index fields might include ordering prefix like '-created_at'
            has_index = (
                field in index_fields or
                any(field in idx_field for idx_field in index_fields) or
                field in [f.name for f in meta.get_fields() if getattr(f, 'unique', False)]
            )
            assert has_index, f"Transaction should have index on '{field}'"


@pytest.mark.django_db
@pytest.mark.performance
class TestNPlusOneDetection:
    """N+1 query pattern detection tests."""

    @pytest.fixture
    def related_data(self, db):
        """Create related data for N+1 testing."""
        import uuid
        uid = str(uuid.uuid4())[:8]
        users = []
        for i in range(20):
            user = User.objects.create_user(
                username=f'n1_u_{i}_{uid}',
                email=f'n1u{i}_{uid}@test.com',
                password='testpass123'
            )
            
            wallet, _ = Wallet.objects.get_or_create(user=user)
            
            # Create transactions for each user
            for j in range(5):
                Transaction.objects.create(
                    transaction_id=f"TXN-N1-{uid}-{i}-{j}",
                    user=user,
                    wallet=wallet,
                    transaction_type='deposit',
                    amount=Decimal('10.00'),
                    payment_gateway='stripe',
                    status='completed'
                )
            
            users.append(user)
        
        return users

    def test_transaction_list__no_n_plus_1__with_user(self, related_data):
        """
        N+1 DETECTION: Transaction list should not query user per row.
        
        With 100 transactions (20 users x 5 each), query count should be low.
        """
        with CaptureQueriesContext(connection) as context:
            transactions = list(
                Transaction.objects.select_related('user', 'wallet')[:100]
            )
            # Access related fields
            for txn in transactions:
                _ = txn.user.username
                if txn.wallet:
                    _ = txn.wallet.balance
        
        query_count = len(context)
        
        if query_count > 5:
            pytest.fail(
                f"N+1 DETECTED: Transaction list made {query_count} queries.\n"
                f"With select_related, should be <= 5 queries.\n"
                f"First queries:\n" + 
                "\n".join([q['sql'][:100] for q in context.captured_queries[:5]])
            )

    def test_user_with_profile__no_n_plus_1(self, db):
        """
        N+1 DETECTION: User list with profile should use select_related.
        """
        import uuid
        uid = str(uuid.uuid4())[:8]
        # Create users (profiles created by signal)
        prefix = f'prof_n1_{uid}'
        for i in range(10):
            User.objects.create_user(
                username=f'{prefix}_{i}',
                email=f'{prefix}_{i}@test.com',
                password='testpass123'
            )
        
        with CaptureQueriesContext(connection) as context:
            users = list(
                User.objects.select_related('profile').filter(
                    username__startswith=prefix
                )
            )
            for user in users:
                try:
                    _ = user.profile.bio
                except Exception:
                    pass
        
        query_count = len(context)
        
        if query_count > 3:
            pytest.fail(
                f"N+1 DETECTED: User list made {query_count} queries.\n"
                f"With select_related, should be <= 3 queries."
            )


@pytest.mark.django_db
@pytest.mark.performance
class TestQueryOptimizationPatterns:
    """Tests for common query optimization patterns."""

    def test_exists_vs_count__performance(self, db):
        """
        OPTIMIZATION: exists() should be faster than count() for existence checks.
        """
        import uuid
        uid = str(uuid.uuid4())[:8]
        username = f'exist_{uid}'
        user = User.objects.create_user(
            username=username,
            email=f'{username}@test.com',
            password='testpass123'
        )
        
        exists_metrics = PerformanceMetrics(name="exists_check")
        count_metrics = PerformanceMetrics(name="count_check")
        
        for _ in range(50):
            with exists_metrics.measure():
                _ = User.objects.filter(username=username).exists()
            
            with count_metrics.measure():
                _ = User.objects.filter(username=username).count() > 0
        
        print("\n--- Exists vs Count Comparison ---")
        exists_metrics.print_report()
        count_metrics.print_report()
        
        # Both should be fast
        exists_metrics.assert_p95_under(50)
        count_metrics.assert_p95_under(50)

    def test_values_list__memory_efficiency(self, db):
        """
        OPTIMIZATION: values_list() should be efficient for single field retrieval.
        """
        import uuid
        uid = str(uuid.uuid4())[:8]
        # Create categories
        for i in range(50):
            Category.objects.create(
                name=f'Opt Category {i} {uid}',
                slug=f'opt-category-{i}-{uid}',
                is_active=True
            )
        
        metrics = PerformanceMetrics(name="values_list_retrieval")
        
        for _ in range(20):
            with metrics.measure():
                slugs = list(
                    Category.objects.filter(
                        slug__startswith=f'opt-category'
                    ).values_list('slug', flat=True)
                )
            # Relax count assertion as there might be other categories
            assert len(slugs) >= 50
        
        metrics.print_report()
        metrics.assert_p95_under(100)

    def test_only_defer__selective_loading(self, db):
        """
        OPTIMIZATION: only() and defer() for selective field loading.
        """
        import uuid
        uid = str(uuid.uuid4())[:8]
        user = User.objects.create_user(
            username=f'defer_u_{uid}',
            email=f'defer{uid}@test.com',
            password='testpass123'
        )
        wallet, _ = Wallet.objects.get_or_create(user=user)
        
        # Create transactions with metadata
        for i in range(50):
            Transaction.objects.create(
                transaction_id=f"TXN-DEF-{uid}-{i}",
                user=user,
                wallet=wallet,
                transaction_type='deposit',
                amount=Decimal('10.00'),
                payment_gateway='stripe',
                status='completed',
                metadata={'key': 'value' * 100}  # Large metadata
            )
        
        full_metrics = PerformanceMetrics(name="full_load")
        deferred_metrics = PerformanceMetrics(name="deferred_metadata")
        
        for _ in range(10):
            with full_metrics.measure():
                _ = list(Transaction.objects.filter(user=user)[:50])
            
            with deferred_metrics.measure():
                _ = list(
                    Transaction.objects.filter(user=user)
                    .defer('metadata')[:50]
                )
        
        print("\n--- Full vs Deferred Load ---")
        full_metrics.print_report()
        deferred_metrics.print_report()


@pytest.mark.django_db
@pytest.mark.performance
@pytest.mark.slow
class TestLargeDatasetIndexPerformance:
    """Index performance with larger datasets."""

    def test_10k_transactions__index_effectiveness(self, db):
        """
        SCALING TEST: Index effectiveness with 10,000 transactions.
        
        Queries should remain fast even with large data.
        """
        import uuid
        uid = str(uuid.uuid4())[:8]
        user = User.objects.create_user(
            username=f'10k_txn_{uid}',
            email=f'10ktxn_{uid}@test.com',
            password='testpass123'
        )
        wallet, _ = Wallet.objects.get_or_create(user=user)
        
        # Create 10k transactions in batches
        batch_size = 1000
        for batch in range(10):
            transactions = [
                Transaction(
                    transaction_id=f"TXN-10K-{uid}-{batch * batch_size + i}",
                    user=user,
                    wallet=wallet,
                    transaction_type='deposit' if i % 2 == 0 else 'subscription_payment',
                    amount=Decimal('10.00'),
                    payment_gateway='stripe',
                    status='completed'
                )
                for i in range(batch_size)
            ]
            Transaction.objects.bulk_create(transactions)
        
        total = Transaction.objects.filter(user=user).count()
        assert total == 10000, f"Expected 10000, got {total}"
        
        # Test query performance
        metrics = PerformanceMetrics(name="10k_transactions_query")
        
        for _ in range(10):
            with metrics.measure():
                results = list(
                    Transaction.objects.filter(user=user)
                    .order_by('-created_at')[:50]
                )
            assert len(results) == 50
        
        metrics.print_report()
        
        # Even with 10k transactions, paginated query should be fast
        metrics.assert_p95_under(
            200,
            message=f"10k transactions query p95 ({metrics.p95:.2f}ms) exceeds 200ms"
        )
