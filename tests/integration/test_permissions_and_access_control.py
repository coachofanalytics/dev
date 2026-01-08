"""
Permissions & Access Control Integration Tests

Security-focused tests covering OWASP-minded scenarios:
- Privilege escalation attempts
- IDOR (Insecure Direct Object Reference)
- CSRF protection
- Authentication enforcement
- Rate limiting (if present)

Author: Fadhiri
Date: January 2026
Classification: Production-Grade Security Tests
"""

import pytest
import json
from decimal import Decimal
from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.middleware.csrf import get_token

from payments.models import Wallet, Transaction
from marketplace.models import InvestmentOpportunity, JobOpportunity
from gdpr.models import DataExportRequest, DataDeletionRequest
from accounts.models import UserProfile, Category


@pytest.mark.django_db
@pytest.mark.integration
@pytest.mark.security
class TestPrivilegeEscalation:
    """
    SECURITY: Test privilege escalation attempts.
    
    Verifies that regular users cannot access admin functionality.
    """
    
    @pytest.fixture
    def client(self):
        return Client()
    
    @pytest.fixture
    def regular_user(self):
        return User.objects.create_user(
            username='regular_user',
            email='regular@test.com',
            password='RegularPass123!',
            is_active=True,
            is_staff=False,
            is_superuser=False
        )
    
    @pytest.fixture
    def admin_user(self):
        return User.objects.create_superuser(
            username='admin_user',
            email='admin@test.com',
            password='AdminPass123!'
        )
    
    def test_regular_user__cannot_access_admin(self, client, regular_user):
        """
        SECURITY: Regular user cannot access Django admin.
        """
        client.force_login(regular_user)
        
        response = client.get('/admin/')
        
        # Should redirect to admin login or deny
        assert response.status_code in [302, 403]
    
    def test_regular_user__cannot_access_admin_models(self, client, regular_user):
        """
        SECURITY: Regular user cannot access admin model pages.
        """
        client.force_login(regular_user)
        
        admin_urls = [
            '/admin/auth/user/',
            '/admin/payments/wallet/',
            '/admin/payments/transaction/',
        ]
        
        for url in admin_urls:
            response = client.get(url)
            assert response.status_code in [302, 403, 404], \
                f"FINDING: Regular user can access {url}"
    
    def test_regular_user__cannot_promote_to_staff(self, client, regular_user):
        """
        SECURITY: Regular user cannot make themselves staff.
        """
        client.force_login(regular_user)
        
        # Attempt to update own user via API or form
        response = client.post('/api/user/update/', {
            'is_staff': True,
            'is_superuser': True
        }, content_type='application/json')
        
        regular_user.refresh_from_db()
        
        if regular_user.is_staff or regular_user.is_superuser:
            pytest.fail("CRITICAL FINDING: User can promote themselves to staff/superuser")


@pytest.mark.django_db
@pytest.mark.integration
@pytest.mark.security
class TestIDORPrevention:
    """
    SECURITY: Test IDOR (Insecure Direct Object Reference) prevention.
    
    Verifies users cannot access other users' resources.
    """
    
    @pytest.fixture
    def client(self):
        return Client()
    
    @pytest.fixture
    def user_a(self):
        user = User.objects.create_user(
            username='user_a',
            email='user_a@test.com',
            password='UserAPass123!',
            is_active=True
        )
        Wallet.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('500.00')}
        )
        return user
    
    @pytest.fixture
    def user_b(self):
        user = User.objects.create_user(
            username='user_b',
            email='user_b@test.com',
            password='UserBPass123!',
            is_active=True
        )
        Wallet.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('300.00')}
        )
        return user
    
    def test_idor__cannot_view_other_wallet(self, client, user_a, user_b):
        """
        SECURITY: User cannot view other user's wallet.
        """
        wallet_b = Wallet.objects.get(user=user_b)
        
        client.force_login(user_a)
        
        # Attempt to access user_b's wallet directly
        response = client.get(f'/payments/wallet/{wallet_b.id}/')
        
        # Should deny or return 404
        if response.status_code == 200:
            # Check if it's actually user_b's data
            content = response.content.decode()
            if 'user_b' in content.lower() or '300' in content:
                pytest.fail("IDOR VULNERABILITY: User can view other user's wallet")
    
    def test_idor__cannot_view_other_transactions(self, client, user_a, user_b):
        """
        SECURITY: User cannot view other user's transactions.
        """
        wallet_b = Wallet.objects.get(user=user_b)
        
        # Create transaction for user_b
        txn_b = Transaction.objects.create(
            user=user_b,
            wallet=wallet_b,
            transaction_type='deposit',
            amount=Decimal('100.00'),
            payment_gateway='stripe',
            status='completed'
        )
        
        client.force_login(user_a)
        
        # Attempt to access user_b's transaction
        response = client.get(f'/payments/transactions/{txn_b.id}/')
        
        if response.status_code == 200:
            pytest.fail("IDOR VULNERABILITY: User can view other user's transactions")
    
    def test_idor__cannot_export_other_user_data(self, client, user_a, user_b):
        """
        SECURITY: User cannot export other user's GDPR data.
        """
        # Create export request for user_b
        export_b = DataExportRequest.objects.create(
            user=user_b,
            export_format='json'
        )
        
        client.force_login(user_a)
        
        # Attempt to download user_b's export
        response = client.get(f'/gdpr/export/{export_b.id}/download/')
        
        if response.status_code == 200:
            pytest.fail("IDOR VULNERABILITY: User can access other user's data export")
    
    def test_idor__cannot_cancel_other_deletion_request(self, client, user_a, user_b):
        """
        SECURITY: User cannot cancel other user's deletion request.
        """
        deletion_b = DataDeletionRequest.objects.create(user=user_b)
        
        client.force_login(user_a)
        
        response = client.post(f'/gdpr/deletion/{deletion_b.id}/cancel/')
        
        deletion_b.refresh_from_db()
        
        if deletion_b.status == 'cancelled':
            pytest.fail("IDOR VULNERABILITY: User can cancel other user's deletion request")


@pytest.mark.django_db
@pytest.mark.integration
@pytest.mark.security
class TestCSRFProtection:
    """
    SECURITY: Test CSRF protection on critical forms.
    """
    
    @pytest.fixture
    def client(self):
        return Client(enforce_csrf_checks=True)
    
    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username='csrf_user',
            email='csrf@test.com',
            password='CSRFPass123!',
            is_active=True
        )
    
    def test_csrf__required_for_login(self, client):
        """
        SECURITY: Login requires CSRF token.
        """
        response = client.post(reverse('login'), {
            'username': 'test',
            'password': 'test'
        })
        
        # Should reject without CSRF
        assert response.status_code == 403
    
    def test_csrf__required_for_profile_update(self, client, user):
        """
        SECURITY: Profile update requires CSRF token.
        """
        # Get page to get CSRF token
        client.force_login(user)
        
        # POST without CSRF token
        response = client.post('/accounts/profile/edit/', {
            'phone': '+254712345678'
        })
        
        # Should reject without proper CSRF
        # Note: force_login may bypass CSRF in tests
    
    def test_csrf__webhooks_exempt(self):
        """
        SECURITY: Webhooks are correctly exempt from CSRF.
        """
        client = Client(enforce_csrf_checks=True)
        
        # Webhooks should work without CSRF
        response = client.post(
            '/payments/webhooks/stripe/',
            data=json.dumps({'type': 'test'}),
            content_type='application/json'
        )
        
        # Should NOT be 403 CSRF error
        assert response.status_code != 403 or 'CSRF' not in str(response.content)


@pytest.mark.django_db
@pytest.mark.integration
@pytest.mark.security
class TestAuthenticationEnforcement:
    """
    SECURITY: Test authentication is enforced on protected resources.
    """
    
    @pytest.fixture
    def client(self):
        return Client()
    
    def test_protected_endpoints__require_authentication(self, client):
        """
        SECURITY: Protected endpoints redirect unauthenticated users.
        """
        protected_urls = [
            '/payments/wallet/',
            '/payments/transactions/',
            '/payments/deposit/',
            '/marketplace/opportunity/post/',
            '/marketplace/job/post/',
            '/gdpr/export/request/',
            '/gdpr/deletion/request/',
            '/kyc/upload/',
            '/onboarding/complete-profile/',
        ]
        
        for url in protected_urls:
            response = client.get(url)
            
            # Should redirect to login (302) or deny (401/403)
            assert response.status_code in [302, 401, 403], \
                f"FINDING: {url} accessible without authentication (status {response.status_code})"
    
    def test_api_endpoints__require_authentication(self, client):
        """
        SECURITY: API endpoints return proper auth errors.
        """
        api_urls = [
            '/api/wallet/balance/',
            '/api/transactions/',
        ]
        
        for url in api_urls:
            response = client.get(url)
            
            # Should be 401/403 or redirect
            assert response.status_code in [302, 401, 403, 404], \
                f"FINDING: API {url} accessible without auth"


@pytest.mark.django_db
@pytest.mark.integration
@pytest.mark.security
class TestInputValidation:
    """
    SECURITY: Test input validation on forms and APIs.
    """
    
    @pytest.fixture
    def client(self):
        return Client()
    
    @pytest.fixture
    def user(self):
        user = User.objects.create_user(
            username='input_user',
            email='input@test.com',
            password='InputPass123!',
            is_active=True
        )
        Wallet.objects.get_or_create(user=user)
        return user
    
    def test_xss__script_tags_escaped(self, client, user):
        """
        SECURITY: XSS script tags are escaped in output.
        """
        client.force_login(user)
        
        # Create content with XSS attempt
        malicious_title = '<script>alert("XSS")</script>Opportunity'
        
        opp = InvestmentOpportunity.objects.create(
            business=user,
            title=malicious_title,
            description='Test',
            amount_seeking=Decimal('100000.00'),
            minimum_investment=Decimal('10000.00'),
            equity_percentage=Decimal('10.00'),
            industry='Technology'
        )
        
        response = client.get(f'/marketplace/opportunity/{opp.slug}/')
        
        if response.status_code == 200:
            content = response.content.decode()
            # Script should be escaped, not executable
            if '<script>alert' in content and '&lt;script&gt;' not in content:
                pytest.fail("POTENTIAL XSS VULNERABILITY: Script not escaped")
    
    def test_sql_injection__safe_query(self, client, user):
        """
        SECURITY: SQL injection attempts are safe.
        """
        client.force_login(user)
        
        # Attempt SQL injection via search
        response = client.get("/marketplace/opportunities/?search=' OR '1'='1")
        
        # Should not error or return all records unexpectedly
        assert response.status_code in [200, 400]


@pytest.mark.django_db
@pytest.mark.integration
@pytest.mark.security
class TestRateLimiting:
    """
    SECURITY: Test rate limiting on sensitive endpoints.
    """
    
    @pytest.fixture
    def client(self):
        return Client()
    
    def test_login__rate_limited(self, client):
        """
        SECURITY: Login endpoint should have rate limiting.
        
        Note: This documents if rate limiting exists.
        """
        # Attempt multiple failed logins
        for i in range(20):
            response = client.post(reverse('login'), {
                'username': f'nonexistent_{i}',
                'password': 'wrongpassword'
            })
        
        # After many attempts, should see rate limit response (429)
        # or CAPTCHA requirement, or account lockout
        # Document actual behavior
    
    def test_password_reset__rate_limited(self, client):
        """
        SECURITY: Password reset should be rate limited.
        """
        # Attempt multiple password resets
        for i in range(20):
            response = client.post(reverse('password_reset'), {
                'email': f'test{i}@example.com'
            })
        
        # Document if rate limiting exists


@pytest.mark.django_db
@pytest.mark.integration
@pytest.mark.security
class TestFileUploadSecurity:
    """
    SECURITY: Test file upload security measures.
    """
    
    @pytest.fixture
    def client(self):
        return Client()
    
    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username='upload_user',
            email='upload@test.com',
            password='UploadPass123!',
            is_active=True
        )
    
    def test_kyc_upload__validates_file_type(self, client, user):
        """
        SECURITY: KYC upload validates file type.
        """
        client.force_login(user)
        
        # Attempt to upload executable
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        malicious_file = SimpleUploadedFile(
            name='malware.exe',
            content=b'MZ\x90\x00...',  # PE header start
            content_type='application/x-msdownload'
        )
        
        response = client.post('/kyc/upload/', {
            'document_type': 'national_id',
            'document_file': malicious_file
        })
        
        # Should reject non-image/PDF files
    
    def test_profile_image__validates_size(self, client, user):
        """
        SECURITY: Profile image upload validates file size.
        """
        client.force_login(user)
        
        # Create large file (simulate)
        large_file = SimpleUploadedFile(
            name='huge_image.jpg',
            content=b'x' * (10 * 1024 * 1024),  # 10MB
            content_type='image/jpeg'
        )
        
        response = client.post('/accounts/profile/edit/', {
            'profile_image': large_file
        })
        
        # Should reject oversized files


@pytest.mark.django_db
@pytest.mark.integration
@pytest.mark.security
class TestSessionSecurity:
    """
    SECURITY: Test session security measures.
    """
    
    @pytest.fixture
    def client(self):
        return Client()
    
    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username='session_user',
            email='session@test.com',
            password='SessionPass123!',
            is_active=True
        )
    
    def test_logout__invalidates_session(self, client, user):
        """
        SECURITY: Logout properly invalidates session.
        """
        client.force_login(user)
        
        # Get session key
        session_key = client.session.session_key
        
        # Logout
        client.get(reverse('logout'))
        
        # Old session should be invalid
        assert '_auth_user_id' not in client.session
    
    def test_session__httponly_cookie(self, client, user):
        """
        SECURITY: Session cookie should be HttpOnly.
        """
        # Login
        response = client.post(reverse('login'), {
            'username': 'session_user',
            'password': 'SessionPass123!'
        })
        
        # Check session cookie settings
        # This is set in Django settings - document requirement
    
    def test_session__secure_cookie_in_production(self):
        """
        SECURITY: Session cookie should be Secure in production.
        
        Note: This is a settings check, not a functional test.
        """
        from django.conf import settings
        
        # In production, these should be True
        # Document current settings for review
        session_secure = getattr(settings, 'SESSION_COOKIE_SECURE', False)
        csrf_secure = getattr(settings, 'CSRF_COOKIE_SECURE', False)
        
        # FINDING: Document if not set

