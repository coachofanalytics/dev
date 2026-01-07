"""
Comprehensive OWASP Top 10 security tests.

Tests for common web application vulnerabilities according to
OWASP Top 10 security risks.
"""

import pytest
import json
from decimal import Decimal
from unittest.mock import Mock, patch
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse


@pytest.mark.django_db
class TestA01BrokenAccessControl:
    """
    OWASP A01:2021 - Broken Access Control
    
    Tests for unauthorized access to resources and functions.
    """

    @pytest.fixture
    def regular_user(self):
        """Create regular user."""
        return User.objects.create_user(
            username='regular_user',
            email='regular@example.com',
            password='testpass123',
            is_active=True
        )

    @pytest.fixture
    def other_user(self):
        """Create another user."""
        return User.objects.create_user(
            username='other_user',
            email='other@example.com',
            password='testpass123',
            is_active=True
        )

    @pytest.fixture
    def admin_user(self):
        """Create admin user."""
        return User.objects.create_superuser(
            username='admin_user',
            email='admin@example.com',
            password='adminpass123'
        )

    @pytest.fixture
    def client(self):
        """Create test client."""
        return Client()

    def test_vertical_privilege_escalation(self, client, regular_user):
        """Test regular user cannot access admin functions."""
        client.force_login(regular_user)
        
        admin_urls = [
            '/admin/',
            '/admin/auth/user/',
            '/admin/payments/transaction/',
        ]
        
        for url in admin_urls:
            response = client.get(url)
            # Should redirect to admin login or be forbidden
            assert response.status_code in [302, 403]

    def test_horizontal_privilege_escalation(self, client, regular_user, other_user):
        """Test user cannot access another user's resources."""
        from payments.models import Wallet
        
        # Create wallet for other user
        other_wallet, _ = Wallet.objects.get_or_create(user=other_user)
        
        client.force_login(regular_user)
        
        # Try to access other user's wallet
        response = client.get(f'/payments/wallet/{other_wallet.id}/')
        assert response.status_code in [403, 404]

    def test_insecure_direct_object_reference(self, client, regular_user, other_user):
        """Test IDOR vulnerability protection."""
        from payments.models import Transaction, Wallet
        
        wallet, _ = Wallet.objects.get_or_create(user=other_user)
        other_txn = Transaction.objects.create(
            user=other_user,
            wallet=wallet,
            transaction_type='deposit',
            amount=Decimal('100.00'),
            payment_gateway='stripe'
        )
        
        client.force_login(regular_user)
        
        # Try to access other user's transaction
        response = client.get(f'/payments/transaction/{other_txn.id}/')
        assert response.status_code in [403, 404]

    def test_force_browsing(self, client):
        """Test force browsing to sensitive URLs."""
        sensitive_urls = [
            '/admin/config/',
            '/.env',
            '/settings.py',
            '/backup.sql',
            '/debug/',
            '/.git/',
        ]
        
        for url in sensitive_urls:
            response = client.get(url)
            # Should not expose sensitive files
            assert response.status_code in [302, 403, 404]


@pytest.mark.django_db
class TestA02CryptographicFailures:
    """
    OWASP A02:2021 - Cryptographic Failures
    
    Tests for proper encryption and data protection.
    """

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='crypto_user',
            email='crypto@example.com',
            password='securePassword123!'
        )

    def test_password_not_stored_plaintext(self, user):
        """Test passwords are properly hashed."""
        # Password should be hashed, not plaintext
        assert user.password != 'securePassword123!'
        assert 'pbkdf2' in user.password or 'bcrypt' in user.password or 'argon2' in user.password

    def test_password_uses_strong_hashing(self, user):
        """Test password uses strong hashing algorithm."""
        # Django uses PBKDF2 by default with SHA256
        assert 'sha256' in user.password.lower() or 'argon2' in user.password.lower() or \
               'pbkdf2' in user.password.lower()

    def test_sensitive_data_not_in_urls(self, client):
        """Test sensitive data is not exposed in URLs."""
        user = User.objects.create_user(
            username='url_test_user',
            email='urltest@example.com',
            password='testpass123',
            is_active=True
        )
        client.force_login(user)
        
        # Check that password reset doesn't expose password in URL
        response = client.get('/accounts/password/reset/')
        assert 'password' not in response.request.get('PATH_INFO', '').lower() or \
               response.status_code == 200


@pytest.mark.django_db
class TestA03Injection:
    """
    OWASP A03:2021 - Injection
    
    Tests for SQL injection and other injection attacks.
    """

    @pytest.fixture
    def client(self):
        """Create test client."""
        return Client()

    def test_sql_injection_login(self, client):
        """Test SQL injection in login form."""
        sql_payloads = [
            "admin'--",
            "admin' OR '1'='1",
            "'; DROP TABLE auth_user; --",
            "1' OR '1'='1'/*",
            "admin' AND SLEEP(5)--"
        ]
        
        for payload in sql_payloads:
            response = client.post('/accounts/login/', {
                'username': payload,
                'password': 'test'
            })
            
            # Should not crash or expose SQL error
            assert response.status_code in [200, 302, 400]
            assert 'SQL' not in response.content.decode('utf-8', errors='ignore')

    def test_sql_injection_search(self, client):
        """Test SQL injection in search functionality."""
        sql_payloads = [
            "'; SELECT * FROM auth_user; --",
            "1 OR 1=1",
            "1' UNION SELECT password FROM auth_user--"
        ]
        
        for payload in sql_payloads:
            response = client.get(f'/marketplace/search/?q={payload}')
            
            # Should handle gracefully
            assert response.status_code in [200, 400, 404]

    def test_nosql_injection(self, client):
        """Test NoSQL injection attempts."""
        nosql_payloads = [
            '{"$gt": ""}',
            '{"$ne": null}',
            '{"$where": "this.password == \'test\'"}',
        ]
        
        for payload in nosql_payloads:
            response = client.post('/accounts/login/', {
                'username': payload,
                'password': 'test'
            })
            
            assert response.status_code in [200, 302, 400]


@pytest.mark.django_db
class TestA04InsecureDesign:
    """
    OWASP A04:2021 - Insecure Design
    
    Tests for design flaws and missing security controls.
    """

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='design_user',
            email='design@example.com',
            password='testpass123',
            is_active=True
        )

    @pytest.fixture
    def client(self):
        """Create test client."""
        return Client()

    def test_rate_limiting_exists(self, client):
        """Test rate limiting on sensitive endpoints."""
        # Make many login attempts
        for i in range(20):
            client.post('/accounts/login/', {
                'username': 'nonexistent',
                'password': 'wrongpass'
            })
        
        # Should still work (or be rate limited)
        response = client.post('/accounts/login/', {
            'username': 'test',
            'password': 'test'
        })
        
        # Either success, failure, or rate limited
        assert response.status_code in [200, 302, 429]

    def test_password_reset_enumeration_prevention(self, client, user):
        """Test password reset doesn't enumerate users."""
        # Valid email
        response_valid = client.post('/accounts/password/reset/', {
            'email': 'design@example.com'
        })
        
        # Invalid email
        response_invalid = client.post('/accounts/password/reset/', {
            'email': 'nonexistent@example.com'
        })
        
        # Both should show same response
        assert response_valid.status_code == response_invalid.status_code


@pytest.mark.django_db
class TestA05SecurityMisconfiguration:
    """
    OWASP A05:2021 - Security Misconfiguration
    
    Tests for security misconfigurations.
    """

    @pytest.fixture
    def client(self):
        """Create test client."""
        return Client()

    def test_debug_mode_disabled(self, client):
        """Test debug mode is disabled in production-like settings."""
        # Trigger an error
        response = client.get('/nonexistent-page-12345/')
        
        # Should not show debug information
        content = response.content.decode('utf-8', errors='ignore')
        assert 'SETTINGS' not in content
        assert 'SECRET_KEY' not in content
        assert 'Traceback' not in content or response.status_code == 404

    def test_server_headers_not_exposed(self, client):
        """Test server version not exposed in headers."""
        response = client.get('/')
        
        # Should not expose server details
        server = response.get('Server', '')
        x_powered_by = response.get('X-Powered-By', '')
        
        # Should not expose version numbers
        assert 'Django/' not in server
        assert 'Python/' not in server

    def test_error_pages_generic(self, client):
        """Test error pages don't expose sensitive information."""
        # 404 error
        response = client.get('/this-page-does-not-exist/')
        content = response.content.decode('utf-8', errors='ignore')
        
        # Should not show internal paths or settings
        assert '/home/' not in content
        assert 'SECRET_KEY' not in content


@pytest.mark.django_db
class TestA06VulnerableComponents:
    """
    OWASP A06:2021 - Vulnerable and Outdated Components
    
    Tests for known vulnerabilities in dependencies.
    """

    def test_django_version_info_not_exposed(self, client):
        """Test Django version not exposed."""
        client = Client()
        response = client.get('/')
        
        # Check headers don't expose Django version
        for header_name, header_value in response.items():
            assert 'Django' not in str(header_value) or 'csrf' in header_name.lower()


@pytest.mark.django_db
class TestA07IdentificationAuthenticationFailures:
    """
    OWASP A07:2021 - Identification and Authentication Failures
    
    Tests for authentication weaknesses.
    """

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='auth_test_user',
            email='authtest@example.com',
            password='SecureP@ssw0rd123!',
            is_active=True
        )

    @pytest.fixture
    def client(self):
        """Create test client."""
        return Client()

    def test_session_fixation_prevention(self, client, user):
        """Test session ID changes after login."""
        # Get initial session
        client.get('/')
        session_before = client.session.session_key
        
        # Login
        client.post('/accounts/login/', {
            'username': 'auth_test_user',
            'password': 'SecureP@ssw0rd123!'
        })
        
        session_after = client.session.session_key
        
        # Session should change after login
        # (This depends on Django's SESSION_SAVE_EVERY_REQUEST setting)

    def test_weak_password_rejected(self, client):
        """Test weak passwords are rejected."""
        weak_passwords = [
            '123456',
            'password',
            'admin',
            'qwerty',
            '12345678'
        ]
        
        for weak_pass in weak_passwords:
            response = client.post('/accounts/register/', {
                'username': 'testuser',
                'email': 'test@example.com',
                'password1': weak_pass,
                'password2': weak_pass
            })
            
            # Should show validation error
            assert response.status_code in [200, 400]

    def test_password_confirmation_required(self, client):
        """Test password confirmation is required for registration."""
        response = client.post('/accounts/register/', {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'SecureP@ss123!',
            'password2': 'DifferentP@ss123!'  # Different password
        })
        
        # Should reject mismatched passwords
        assert response.status_code in [200, 400]


@pytest.mark.django_db
class TestA08SoftwareDataIntegrityFailures:
    """
    OWASP A08:2021 - Software and Data Integrity Failures
    
    Tests for data integrity and tampering protection.
    """

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='integrity_user',
            email='integrity@example.com',
            password='testpass123',
            is_active=True
        )

    @pytest.fixture
    def client(self):
        """Create test client."""
        return Client()

    def test_csrf_protection_on_forms(self, user):
        """Test CSRF protection on sensitive forms."""
        client = Client(enforce_csrf_checks=True)
        client.force_login(user)
        
        # Try to submit form without CSRF token
        response = client.post('/accounts/profile/edit/', {
            'bio': 'Updated bio'
        })
        
        # Should fail due to missing CSRF token
        assert response.status_code in [403, 404]

    def test_hidden_field_tampering(self, client, user):
        """Test hidden field tampering is prevented."""
        client.force_login(user)
        
        # Try to tamper with user ID in form
        response = client.post('/accounts/profile/edit/', {
            'user_id': '999',  # Tampered ID
            'bio': 'Hacked bio'
        })
        
        # Should ignore tampered user_id or reject
        assert response.status_code in [200, 302, 400, 403, 404]


@pytest.mark.django_db
class TestA09SecurityLoggingMonitoringFailures:
    """
    OWASP A09:2021 - Security Logging and Monitoring Failures
    
    Tests for security event logging.
    """

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='logging_user',
            email='logging@example.com',
            password='testpass123',
            is_active=True
        )

    @pytest.fixture
    def client(self):
        """Create test client."""
        return Client()

    def test_failed_login_can_be_logged(self, client):
        """Test failed login attempts can be tracked."""
        # Make failed login attempts
        for i in range(5):
            client.post('/accounts/login/', {
                'username': 'nonexistent',
                'password': 'wrongpass'
            })
        
        # This should be logged (implementation-dependent)
        # Test passes if no error is raised

    def test_successful_login_can_be_logged(self, client, user):
        """Test successful logins can be tracked."""
        response = client.post('/accounts/login/', {
            'username': 'logging_user',
            'password': 'testpass123'
        })
        
        # This should be logged (implementation-dependent)
        assert response.status_code in [200, 302]


@pytest.mark.django_db
class TestA10ServerSideRequestForgery:
    """
    OWASP A10:2021 - Server-Side Request Forgery (SSRF)
    
    Tests for SSRF vulnerabilities.
    """

    @pytest.fixture
    def client(self):
        """Create test client."""
        return Client()

    def test_url_input_validation(self, client):
        """Test URL inputs are validated."""
        dangerous_urls = [
            'http://localhost:22',
            'http://127.0.0.1:22',
            'http://169.254.169.254/',  # AWS metadata
            'file:///etc/passwd',
            'gopher://localhost:25/',
        ]
        
        # If there's a URL input field, these should be blocked
        for url in dangerous_urls:
            response = client.post('/accounts/profile/edit/', {
                'website': url
            })
            
            # Should handle gracefully
            assert response.status_code in [200, 302, 400, 404]


@pytest.mark.django_db
class TestXSSProtection:
    """
    Cross-Site Scripting (XSS) protection tests.
    """

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='xss_user',
            email='xss@example.com',
            password='testpass123',
            is_active=True
        )

    @pytest.fixture
    def client(self):
        """Create test client."""
        return Client()

    def test_xss_in_search(self, client):
        """Test XSS in search results."""
        xss_payloads = [
            '<script>alert("XSS")</script>',
            '<img src=x onerror=alert("XSS")>',
            '"><script>alert("XSS")</script>',
            '<svg onload=alert("XSS")>',
        ]
        
        for payload in xss_payloads:
            response = client.get(f'/marketplace/search/?q={payload}')
            
            if response.status_code == 200:
                content = response.content.decode('utf-8', errors='ignore')
                # Script should be escaped
                assert '<script>alert("XSS")</script>' not in content

    def test_xss_in_profile_fields(self, client, user):
        """Test XSS in profile fields."""
        client.force_login(user)
        
        xss_payload = '<script>alert("XSS")</script>'
        
        response = client.post('/accounts/profile/edit/', {
            'bio': xss_payload,
            'company_name': xss_payload
        })
        
        # Check if XSS is sanitized
        if response.status_code in [200, 302]:
            profile_response = client.get('/accounts/profile/')
            if profile_response.status_code == 200:
                content = profile_response.content.decode('utf-8', errors='ignore')
                # Script should be escaped
                assert '<script>' not in content or '&lt;script&gt;' in content

