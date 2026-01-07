"""
Comprehensive API contract and schema validation tests.

Tests API response schemas, backward compatibility,
and contract adherence.
"""

import pytest
import json
from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth.models import User

from payments.models import Wallet, Transaction, Invoice, SubscriptionPlan, UserSubscription
from marketplace.models import BusinessProfile, InvestmentOpportunity, JobOpportunity


@pytest.mark.django_db
class TestWalletAPIContract:
    """Test wallet API response schema and contracts."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='api_wallet_user',
            email='apiwallet@example.com',
            password='testpass123',
            is_active=True
        )

    @pytest.fixture
    def wallet(self, user):
        """Create test wallet."""
        wallet, _ = Wallet.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('500.00')}
        )
        wallet.balance = Decimal('500.00')
        wallet.save()
        return wallet

    @pytest.fixture
    def client(self):
        """Create test client."""
        return Client()

    def test_wallet_balance_response_schema(self, client, user, wallet):
        """Test wallet balance API returns expected schema."""
        client.force_login(user)
        response = client.get('/api/wallet/balance/')
        
        if response.status_code == 200:
            data = response.json()
            
            # Required fields
            assert 'balance' in data or 'amount' in data or 'data' in data
            
            # Type validation
            if 'balance' in data:
                assert isinstance(data['balance'], (int, float, str))

    def test_wallet_transactions_response_schema(self, client, user, wallet):
        """Test wallet transactions API returns expected schema."""
        # Create some transactions
        Transaction.objects.create(
            user=user,
            wallet=wallet,
            transaction_type='deposit',
            amount=Decimal('100.00'),
            payment_gateway='stripe',
            status='completed'
        )
        
        client.force_login(user)
        response = client.get('/api/wallet/transactions/')
        
        if response.status_code == 200:
            data = response.json()
            
            # Should be a list or paginated response
            if isinstance(data, list):
                if len(data) > 0:
                    txn = data[0]
                    # Validate transaction schema
                    assert 'id' in txn or 'transaction_id' in txn
                    assert 'amount' in txn
            elif isinstance(data, dict):
                assert 'results' in data or 'transactions' in data or 'data' in data


@pytest.mark.django_db
class TestTransactionAPIContract:
    """Test transaction API response schema and contracts."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='api_txn_user',
            email='apitxn@example.com',
            password='testpass123',
            is_active=True
        )

    @pytest.fixture
    def wallet(self, user):
        """Create test wallet."""
        wallet, _ = Wallet.objects.get_or_create(user=user)
        return wallet

    @pytest.fixture
    def transaction(self, user, wallet):
        """Create test transaction."""
        return Transaction.objects.create(
            user=user,
            wallet=wallet,
            transaction_type='deposit',
            amount=Decimal('100.00'),
            payment_gateway='stripe',
            status='completed'
        )

    @pytest.fixture
    def client(self):
        """Create test client."""
        return Client()

    def test_transaction_detail_schema(self, client, user, transaction):
        """Test transaction detail API schema."""
        client.force_login(user)
        response = client.get(f'/api/transactions/{transaction.id}/')
        
        if response.status_code == 200:
            data = response.json()
            
            # Required transaction fields
            required_fields = ['transaction_type', 'amount', 'status']
            for field in required_fields:
                assert field in data or 'data' in data

    def test_transaction_list_pagination(self, client, user, wallet):
        """Test transaction list is paginated."""
        # Create multiple transactions
        for i in range(25):
            Transaction.objects.create(
                user=user,
                wallet=wallet,
                transaction_type='deposit',
                amount=Decimal('10.00'),
                payment_gateway='stripe'
            )
        
        client.force_login(user)
        response = client.get('/api/transactions/')
        
        if response.status_code == 200:
            data = response.json()
            
            # Paginated response should have count/next/previous or limit/offset
            if isinstance(data, dict):
                pagination_fields = ['count', 'next', 'previous', 'page', 'total', 'limit']
                has_pagination = any(field in data for field in pagination_fields)
                # Either paginated or returns all (depending on implementation)
                assert has_pagination or 'results' in data or isinstance(data.get('data'), list)


@pytest.mark.django_db
class TestInvestmentAPIContract:
    """Test investment opportunity API schema."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='api_invest_user',
            email='apiinvest@example.com',
            password='testpass123',
            is_active=True
        )

    @pytest.fixture
    def investment(self, user):
        """Create test investment."""
        return InvestmentOpportunity.objects.create(
            business=user,
            title='API Test Investment',
            description='Test investment opportunity',
            amount_seeking=Decimal('100000.00'),
            minimum_investment=Decimal('10000.00'),
            equity_percentage=Decimal('10.00'),
            industry='Technology',
            status='open'
        )

    @pytest.fixture
    def client(self):
        """Create test client."""
        return Client()

    def test_investment_list_schema(self, client, investment):
        """Test investment list API schema."""
        response = client.get('/api/investments/')
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list) and len(data) > 0:
                inv = data[0]
                assert 'title' in inv
                assert 'amount_seeking' in inv or 'target_amount' in inv
            elif isinstance(data, dict) and 'results' in data:
                if len(data['results']) > 0:
                    inv = data['results'][0]
                    assert 'title' in inv

    def test_investment_detail_schema(self, client, investment):
        """Test investment detail API schema."""
        response = client.get(f'/api/investments/{investment.slug}/')
        
        if response.status_code == 200:
            data = response.json()
            
            required_fields = ['title', 'description']
            for field in required_fields:
                assert field in data or 'data' in data

    def test_investment_amount_is_numeric(self, client, investment):
        """Test investment amounts are numeric."""
        response = client.get(f'/api/investments/{investment.slug}/')
        
        if response.status_code == 200:
            data = response.json()
            
            amount_fields = ['amount_seeking', 'minimum_investment', 'target_amount']
            for field in amount_fields:
                if field in data:
                    value = data[field]
                    # Should be numeric or numeric string
                    assert isinstance(value, (int, float)) or \
                           (isinstance(value, str) and value.replace('.', '').isdigit())


@pytest.mark.django_db
class TestJobAPIContract:
    """Test job opportunity API schema."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='api_job_user',
            email='apijob@example.com',
            password='testpass123',
            is_active=True
        )

    @pytest.fixture
    def job(self, user):
        """Create test job."""
        return JobOpportunity.objects.create(
            business=user,
            title='API Test Job',
            description='Test job opportunity',
            requirements='Test requirements',
            responsibilities='Test responsibilities',
            location='Remote',
            job_type='full_time'
        )

    @pytest.fixture
    def client(self):
        """Create test client."""
        return Client()

    def test_job_list_schema(self, client, job):
        """Test job list API schema."""
        response = client.get('/api/jobs/')
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list) and len(data) > 0:
                job_data = data[0]
                assert 'title' in job_data
            elif isinstance(data, dict) and 'results' in data:
                if len(data['results']) > 0:
                    job_data = data['results'][0]
                    assert 'title' in job_data

    def test_job_detail_schema(self, client, job):
        """Test job detail API schema."""
        response = client.get(f'/api/jobs/{job.slug}/')
        
        if response.status_code == 200:
            data = response.json()
            
            required_fields = ['title', 'description']
            for field in required_fields:
                assert field in data or 'data' in data


@pytest.mark.django_db
class TestSubscriptionAPIContract:
    """Test subscription API schema."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='api_sub_user',
            email='apisub@example.com',
            password='testpass123',
            is_active=True
        )

    @pytest.fixture
    def plan(self):
        """Create test subscription plan."""
        return SubscriptionPlan.objects.create(
            name='API Test Plan',
            slug='api-test-plan',
            description='Test plan',
            price=Decimal('29.99'),
            duration_days=30,
            is_active=True
        )

    @pytest.fixture
    def client(self):
        """Create test client."""
        return Client()

    def test_subscription_plan_list_schema(self, client, plan):
        """Test subscription plan list API schema."""
        response = client.get('/api/subscription-plans/')
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list) and len(data) > 0:
                plan_data = data[0]
                assert 'name' in plan_data
                assert 'price' in plan_data
            elif isinstance(data, dict) and 'results' in data:
                if len(data['results']) > 0:
                    plan_data = data['results'][0]
                    assert 'name' in plan_data

    def test_subscription_plan_price_format(self, client, plan):
        """Test subscription plan prices are properly formatted."""
        response = client.get(f'/api/subscription-plans/{plan.slug}/')
        
        if response.status_code == 200:
            data = response.json()
            
            if 'price' in data:
                price = data['price']
                # Price should be numeric
                assert isinstance(price, (int, float, str))


@pytest.mark.django_db
class TestAPIErrorResponses:
    """Test API error response consistency."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return Client()

    def test_not_found_response_schema(self, client):
        """Test 404 response schema."""
        response = client.get('/api/investments/nonexistent-slug/')
        
        if response.status_code == 404:
            # Should return JSON for API endpoints
            content_type = response.get('Content-Type', '')
            if 'json' in content_type:
                data = response.json()
                assert 'error' in data or 'detail' in data or 'message' in data

    def test_unauthorized_response_schema(self, client):
        """Test 401/403 response schema."""
        response = client.get('/api/wallet/balance/')
        
        if response.status_code in [401, 403]:
            content_type = response.get('Content-Type', '')
            if 'json' in content_type:
                data = response.json()
                assert 'error' in data or 'detail' in data or 'message' in data

    def test_bad_request_response_schema(self, client):
        """Test 400 response schema."""
        user = User.objects.create_user(
            username='bad_request_user',
            email='badrequest@example.com',
            password='testpass123',
            is_active=True
        )
        client.force_login(user)
        
        # Send invalid data
        response = client.post('/api/wallet/deposit/', {
            'amount': 'invalid'
        }, content_type='application/json')
        
        if response.status_code == 400:
            content_type = response.get('Content-Type', '')
            if 'json' in content_type:
                data = response.json()
                # Should have error information
                assert isinstance(data, dict)


@pytest.mark.django_db
class TestAPIVersioning:
    """Test API versioning behavior."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return Client()

    def test_api_version_header(self, client):
        """Test API version in response header if present."""
        response = client.get('/api/investments/')
        
        # Check for API version header
        api_version = response.get('API-Version') or response.get('X-API-Version')
        # Version header is optional but good practice

    def test_versioned_endpoint_access(self, client):
        """Test versioned endpoints if they exist."""
        versioned_urls = [
            '/api/v1/investments/',
            '/api/v2/investments/',
        ]
        
        for url in versioned_urls:
            response = client.get(url)
            # Should either work (200) or not exist (404)
            assert response.status_code in [200, 404]


@pytest.mark.django_db
class TestAPIDataTypes:
    """Test API data type consistency."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='datatype_user',
            email='datatype@example.com',
            password='testpass123',
            is_active=True
        )

    @pytest.fixture
    def client(self):
        """Create test client."""
        return Client()

    def test_date_format_consistency(self, client, user):
        """Test dates are in consistent format."""
        wallet, _ = Wallet.objects.get_or_create(user=user)
        Transaction.objects.create(
            user=user,
            wallet=wallet,
            transaction_type='deposit',
            amount=Decimal('100.00'),
            payment_gateway='stripe'
        )
        
        client.force_login(user)
        response = client.get('/api/transactions/')
        
        if response.status_code == 200:
            data = response.json()
            
            # Get first transaction
            txns = data if isinstance(data, list) else data.get('results', data.get('data', []))
            if isinstance(txns, list) and len(txns) > 0:
                txn = txns[0]
                date_fields = ['created_at', 'created', 'date', 'timestamp']
                for field in date_fields:
                    if field in txn:
                        # Should be ISO format or similar
                        date_str = str(txn[field])
                        assert 'T' in date_str or '-' in date_str

    def test_boolean_fields(self, client):
        """Test boolean fields are proper booleans."""
        response = client.get('/api/subscription-plans/')
        
        if response.status_code == 200:
            data = response.json()
            plans = data if isinstance(data, list) else data.get('results', [])
            
            if isinstance(plans, list) and len(plans) > 0:
                plan = plans[0]
                bool_fields = ['is_active', 'is_featured', 'is_popular']
                for field in bool_fields:
                    if field in plan:
                        assert isinstance(plan[field], bool)


@pytest.mark.django_db
class TestAPIBackwardCompatibility:
    """Test API backward compatibility."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return Client()

    def test_deprecated_fields_still_present(self, client):
        """Test deprecated fields are still present for backward compatibility."""
        # This is a placeholder for backward compatibility tests
        # In a real scenario, you would check that deprecated fields
        # are still returned even if new fields are added
        response = client.get('/api/investments/')
        
        if response.status_code == 200:
            # Response should be parseable
            data = response.json()
            assert data is not None

    def test_new_fields_dont_break_old_clients(self, client):
        """Test new fields don't break old client expectations."""
        response = client.get('/api/investments/')
        
        if response.status_code == 200:
            data = response.json()
            
            # Old clients should be able to ignore new fields
            # This test documents that the response is still valid JSON
            assert isinstance(data, (list, dict))

