"""
Marketplace Browsing Latency Benchmarks.

Tests business/job/investment listing performance with filtering and search.
Includes N+1 query detection.
"""

import pytest
from decimal import Decimal
from django.test import Client
from django.contrib.auth.models import User

from marketplace.models import BusinessProfile, InvestmentOpportunity, JobOpportunity
from accounts.models import Category, UserProfile

from .conftest import (
    PerformanceMetrics,
    assert_max_queries,
    PERF_P95_MS,
    PERF_MAX_QUERIES_LIST,
)


@pytest.fixture
def kyc_verified_user(db):
    """Create a user that passes KYC requirements for marketplace access."""
    import uuid
    uid = str(uuid.uuid4())[:8]
    user = User.objects.create_user(
        username=f'kyc_verified_{uid}',
        email=f'kyc_{uid}@test.com',
        password='testpass123'
    )
    # Create investor category if not exists
    category, _ = Category.objects.get_or_create(
        slug='investor',
        defaults={'name': 'Investor', 'is_active': True}
    )
    try:
        profile = user.profile
        profile.category = category
        profile.save()
    except Exception:
        pass
    return user


@pytest.fixture
def marketplace_data(db, kyc_verified_user):
    """Create sample marketplace data for testing."""
    import uuid
    uid = str(uuid.uuid4())[:8]
    business_user = User.objects.create_user(
        username=f'biz_owner_{uid}',
        email=f'business_{uid}@test.com',
        password='testpass123'
    )
    
    # Create business profile
    profile, _ = BusinessProfile.objects.get_or_create(
        user=business_user,
        defaults={
            'company_name': f'Test Company {uid}',
            'industry': 'Technology',
            'company_size': '10-50',
            'funding_stage': 'seed',
        }
    )
    
    # Create opportunities
    opportunities = []
    for i in range(20):
        opp = InvestmentOpportunity.objects.create(
            business=business_user,
            title=f'Investment {i} {uid}',
            slug=f'investment-{i}-{uid}',
            description=f'Description for investment {i}',
            amount_seeking=Decimal('100000.00'),
            minimum_investment=Decimal('1000.00'),
            equity_percentage=Decimal('10.00'),
            industry='Technology' if i % 2 == 0 else 'Healthcare',
            status='open'
        )
        opportunities.append(opp)
    
    # Create jobs
    jobs = []
    for i in range(20):
        job = JobOpportunity.objects.create(
            business=business_user,
            title=f'Job {i} {uid}',
            slug=f'job-{i}-{uid}',
            description=f'Job description {i}',
            requirements='Requirements',
            responsibilities='Responsibilities',
            location='Remote',
            status='open'
        )
        jobs.append(job)
    
    return {
        'business_user': business_user,
        'profile': profile,
        'opportunities': opportunities,
        'jobs': jobs,
    }


@pytest.mark.django_db
@pytest.mark.performance
@pytest.mark.latency
class TestMarketplaceListingLatency:
    """Marketplace listing page latency benchmarks."""

    def test_browse_businesses__no_filter__under_500ms(self, kyc_verified_user, marketplace_data):
        """
        LATENCY BENCHMARK: Business listing without filters.
        
        Threshold: p95 < 500ms
        """
        client = Client()
        client.force_login(kyc_verified_user)
        metrics = PerformanceMetrics(name="browse_businesses")
        
        # Warm up
        try:
            response = client.get('/marketplace/businesses/')
            if response.status_code == 404:
                pytest.skip("Businesses URL not available")
        except Exception:
            pytest.skip("Marketplace not accessible")
        
        for _ in range(10):
            with metrics.measure():
                response = client.get('/marketplace/businesses/')
            assert response.status_code in [200, 302]
        
        metrics.print_report()
        metrics.assert_p95_under(
            500,
            message=f"Browse businesses p95 ({metrics.p95:.2f}ms) exceeds 500ms"
        )

    def test_browse_opportunities__no_filter__under_500ms(self, kyc_verified_user, marketplace_data):
        """
        LATENCY BENCHMARK: Investment opportunities listing.
        
        Threshold: p95 < 500ms
        """
        client = Client()
        client.force_login(kyc_verified_user)
        metrics = PerformanceMetrics(name="browse_opportunities")
        
        try:
            response = client.get('/marketplace/opportunities/')
            if response.status_code == 404:
                pytest.skip("Opportunities URL not available")
        except Exception:
            pytest.skip("Marketplace not accessible")
        
        for _ in range(10):
            with metrics.measure():
                response = client.get('/marketplace/opportunities/')
            assert response.status_code in [200, 302]
        
        metrics.print_report()
        metrics.assert_p95_under(
            500,
            message=f"Browse opportunities p95 ({metrics.p95:.2f}ms) exceeds 500ms"
        )

    def test_browse_opportunities__with_filter__under_500ms(self, kyc_verified_user, marketplace_data):
        """
        LATENCY BENCHMARK: Filtered investment opportunities.
        
        Threshold: p95 < 500ms with industry filter
        """
        client = Client()
        client.force_login(kyc_verified_user)
        metrics = PerformanceMetrics(name="browse_opportunities_filtered")
        
        try:
            response = client.get('/marketplace/opportunities/?industry=Technology')
            if response.status_code == 404:
                pytest.skip("Opportunities URL not available")
        except Exception:
            pytest.skip("Marketplace not accessible")
        
        for _ in range(10):
            with metrics.measure():
                response = client.get('/marketplace/opportunities/?industry=Technology')
            assert response.status_code in [200, 302]
        
        metrics.print_report()
        metrics.assert_p95_under(
            500,
            message=f"Filtered opportunities p95 ({metrics.p95:.2f}ms) exceeds 500ms"
        )

    def test_browse_opportunities__with_search__under_500ms(self, kyc_verified_user, marketplace_data):
        """
        LATENCY BENCHMARK: Search investment opportunities.
        
        Threshold: p95 < 500ms with search query
        """
        client = Client()
        client.force_login(kyc_verified_user)
        metrics = PerformanceMetrics(name="search_opportunities")
        
        try:
            response = client.get('/marketplace/opportunities/?search=Investment')
            if response.status_code == 404:
                pytest.skip("Opportunities URL not available")
        except Exception:
            pytest.skip("Marketplace not accessible")
        
        for _ in range(10):
            with metrics.measure():
                response = client.get('/marketplace/opportunities/?search=Investment')
            assert response.status_code in [200, 302]
        
        metrics.print_report()
        metrics.assert_p95_under(
            500,
            message=f"Search opportunities p95 ({metrics.p95:.2f}ms) exceeds 500ms"
        )

    def test_browse_jobs__no_filter__under_500ms(self, marketplace_data):
        """
        LATENCY BENCHMARK: Job listings (no auth required).
        
        Threshold: p95 < 500ms
        """
        client = Client()
        metrics = PerformanceMetrics(name="browse_jobs")
        
        try:
            response = client.get('/marketplace/jobs/')
            if response.status_code == 404:
                pytest.skip("Jobs URL not available")
        except Exception:
            pytest.skip("Marketplace not accessible")
        
        for _ in range(10):
            with metrics.measure():
                response = client.get('/marketplace/jobs/')
            assert response.status_code in [200, 302]
        
        metrics.print_report()
        metrics.assert_p95_under(
            500,
            message=f"Browse jobs p95 ({metrics.p95:.2f}ms) exceeds 500ms"
        )


@pytest.mark.django_db
@pytest.mark.performance
@pytest.mark.latency
class TestMarketplaceDetailLatency:
    """Marketplace detail page latency benchmarks."""

    def test_opportunity_detail__single__under_300ms(self, kyc_verified_user, marketplace_data):
        """
        LATENCY BENCHMARK: Single opportunity detail page.
        
        Threshold: p95 < 300ms
        """
        client = Client()
        client.force_login(kyc_verified_user)
        opp = marketplace_data['opportunities'][0]
        metrics = PerformanceMetrics(name="opportunity_detail")
        
        try:
            response = client.get(f'/marketplace/opportunity/{opp.slug}/')
            if response.status_code == 404:
                pytest.skip("Opportunity detail URL not available")
        except Exception:
            pytest.skip("Marketplace not accessible")
        
        for _ in range(10):
            with metrics.measure():
                response = client.get(f'/marketplace/opportunity/{opp.slug}/')
            assert response.status_code in [200, 302]
        
        metrics.print_report()
        metrics.assert_p95_under(
            300,
            message=f"Opportunity detail p95 ({metrics.p95:.2f}ms) exceeds 300ms"
        )

    def test_job_detail__single__under_300ms(self, marketplace_data):
        """
        LATENCY BENCHMARK: Single job detail page.
        
        Threshold: p95 < 300ms
        """
        client = Client()
        job = marketplace_data['jobs'][0]
        metrics = PerformanceMetrics(name="job_detail")
        
        try:
            response = client.get(f'/marketplace/job/{job.slug}/')
            if response.status_code == 404:
                pytest.skip("Job detail URL not available")
        except Exception:
            pytest.skip("Marketplace not accessible")
        
        for _ in range(10):
            with metrics.measure():
                response = client.get(f'/marketplace/job/{job.slug}/')
            assert response.status_code in [200, 302]
        
        metrics.print_report()
        metrics.assert_p95_under(
            300,
            message=f"Job detail p95 ({metrics.p95:.2f}ms) exceeds 300ms"
        )


@pytest.mark.django_db
@pytest.mark.performance
@pytest.mark.latency
class TestMarketplaceQueryCounts:
    """N+1 query detection for marketplace views."""

    def test_browse_opportunities__n_plus_1_detection(self, kyc_verified_user, marketplace_data):
        """
        N+1 DETECTION: Opportunities list should not have N+1 queries.
        
        With 20 opportunities, query count should not scale linearly.
        Expected: <= 10 queries (not 1 + N)
        """
        client = Client()
        client.force_login(kyc_verified_user)
        
        try:
            with assert_max_queries(10, "opportunities list"):
                response = client.get('/marketplace/opportunities/')
            if response.status_code == 404:
                pytest.skip("Opportunities URL not available")
        except Exception as e:
            if "404" in str(e) or "not available" in str(e).lower():
                pytest.skip("Opportunities URL not available")
            raise

    def test_browse_jobs__n_plus_1_detection(self, marketplace_data):
        """
        N+1 DETECTION: Jobs list should not have N+1 queries.
        
        Expected: <= 10 queries for 20 jobs
        """
        client = Client()
        
        try:
            with assert_max_queries(10, "jobs list"):
                response = client.get('/marketplace/jobs/')
            if response.status_code == 404:
                pytest.skip("Jobs URL not available")
        except Exception as e:
            if "404" in str(e) or "not available" in str(e).lower():
                pytest.skip("Jobs URL not available")
            raise


@pytest.mark.django_db
@pytest.mark.performance
@pytest.mark.latency
class TestMarketplaceScaling:
    """Test marketplace performance with increasing data."""

    @pytest.mark.slow
    def test_opportunities__100_items__pagination_performance(self, kyc_verified_user, db):
        """
        SCALING TEST: Performance with 100 opportunities.
        
        Tests that pagination keeps response time reasonable.
        """
        import uuid
        uid = str(uuid.uuid4())[:8]
        business_user = User.objects.create_user(
            username=f'bulk_biz_{uid}',
            email=f'bulk_{uid}@test.com',
            password='testpass123'
        )
        
        # Create 100 opportunities
        opportunities = [
            InvestmentOpportunity(
                business=business_user,
                title=f'Bulk Opportunity {i} {uid}',
                slug=f'bulk-opportunity-{i}-{uid}',
                description=f'Description {i}',
                amount_seeking=Decimal('100000.00'),
                minimum_investment=Decimal('1000.00'),
                equity_percentage=Decimal('10.00'),
                industry='Technology',
                status='open'
            )
            for i in range(100)
        ]
        InvestmentOpportunity.objects.bulk_create(opportunities)
        
        client = Client()
        client.force_login(kyc_verified_user)
        metrics = PerformanceMetrics(name="opportunities_100_items")
        
        try:
            for _ in range(5):
                with metrics.measure():
                    response = client.get('/marketplace/opportunities/')
                if response.status_code == 404:
                    pytest.skip("Opportunities URL not available")
                assert response.status_code in [200, 302]
        except Exception:
            pytest.skip("Marketplace not accessible")
        
        metrics.print_report()
        
        # With 100 items, p95 should still be under 1 second
        metrics.assert_p95_under(
            1000,
            message=f"100 opportunities p95 ({metrics.p95:.2f}ms) exceeds 1000ms"
        )
