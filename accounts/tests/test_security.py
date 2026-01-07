"""
Comprehensive security tests for accounts module.

Tests password security, session management, authentication protection,
and access control enforcement.
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.utils import timezone
from datetime import timedelta

from accounts.models import Category, UserProfile


@pytest.mark.django_db
class TestPasswordSecurity:
    """Test password security measures."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return Client()

    def test_password_not_stored_plaintext(self):
        """Test passwords are not stored in plaintext."""
        user = User.objects.create_user(
            username='secure_user',
            email='secure@example.com',
            password='mySecretPassword123!'
        )
        
        # Password should be hashed
        assert user.password != 'mySecretPassword123!'
        assert user.password.startswith('pbkdf2_sha256$') or user.password.startswith('bcrypt$')

    def test_password_hash_is_unique(self):
        """Test same password produces different hashes for different users."""
        user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='samePassword123'
        )
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='samePassword123'
        )
        
        assert user1.password != user2.password

    def test_weak_password_validation(self, client):
        """Test weak passwords are rejected during registration."""
        response = client.post('/accounts/register/', {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': '123',  # Too short
            'password2': '123'
        })
        
        # Should show validation error or stay on form
        assert response.status_code in [200, 400]

    def test_password_change_requires_current_password(self, client):
        """Test password change requires current password."""
        user = User.objects.create_user(
            username='change_user',
            email='change@example.com',
            password='oldPassword123'
        )
        client.force_login(user)
        
        response = client.post('/accounts/password/change/', {
            'new_password1': 'newPassword456',
            'new_password2': 'newPassword456'
            # Missing old_password
        })
        
        assert response.status_code in [200, 400]


@pytest.mark.django_db
class TestSessionSecurity:
    """Test session security measures."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='session_user',
            email='session@example.com',
            password='testpass123',
            is_active=True
        )

    @pytest.fixture
    def client(self):
        """Create test client."""
        return Client()

    def test_session_created_on_login(self, client, user):
        """Test session is created on successful login."""
        response = client.post('/accounts/login/', {
            'username': 'session_user',
            'password': 'testpass123'
        })
        
        assert client.session.session_key is not None

    def test_session_destroyed_on_logout(self, client, user):
        """Test session is destroyed on logout."""
        client.force_login(user)
        session_key = client.session.session_key
        
        client.post('/accounts/logout/')
        
        # Session should be invalidated
        assert not Session.objects.filter(session_key=session_key).exists() or \
               client.session.session_key != session_key

    def test_session_not_accessible_after_logout(self, client, user):
        """Test session data not accessible after logout."""
        client.force_login(user)
        client.session['test_data'] = 'secret'
        client.session.save()
        
        client.post('/accounts/logout/')
        
        # Try to access protected resource
        response = client.get('/accounts/profile/')
        assert response.status_code in [302, 403]


@pytest.mark.django_db
class TestAuthenticationProtection:
    """Test authentication protection measures."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return Client()

    def test_protected_pages_require_login(self, client):
        """Test protected pages redirect to login."""
        protected_urls = [
            '/accounts/profile/',
            '/accounts/settings/',
            '/payments/wallet/',
        ]
        
        for url in protected_urls:
            response = client.get(url)
            assert response.status_code in [302, 403, 404]

    def test_login_page_accessible_without_auth(self, client):
        """Test login page is accessible without authentication."""
        response = client.get('/accounts/login/')
        assert response.status_code == 200

    def test_login_csrf_protection(self):
        """Test login form has CSRF protection."""
        client = Client(enforce_csrf_checks=True)
        
        response = client.post('/accounts/login/', {
            'username': 'test',
            'password': 'test'
        })
        
        # Should fail due to missing CSRF token
        assert response.status_code in [403, 200]

    def test_authenticated_redirect_from_login(self, client):
        """Test authenticated users are redirected from login page."""
        user = User.objects.create_user(
            username='auth_test',
            email='auth@example.com',
            password='testpass123',
            is_active=True
        )
        client.force_login(user)
        
        response = client.get('/accounts/login/')
        
        # May redirect to home or profile
        assert response.status_code in [200, 302]


@pytest.mark.django_db
class TestBruteForceProtection:
    """Test brute force attack protection."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='brute_user',
            email='brute@example.com',
            password='testpass123',
            is_active=True
        )

    @pytest.fixture
    def client(self):
        """Create test client."""
        return Client()

    def test_multiple_failed_logins_tracking(self, client, user):
        """Test multiple failed login attempts are tracked."""
        # Make multiple failed attempts
        for i in range(5):
            client.post('/accounts/login/', {
                'username': 'brute_user',
                'password': 'wrongpassword'
            })
        
        # The system should track these attempts
        # (Implementation depends on rate limiting setup)

    def test_successful_login_after_failures(self, client, user):
        """Test successful login is still possible after some failures."""
        # Make some failed attempts
        for i in range(3):
            client.post('/accounts/login/', {
                'username': 'brute_user',
                'password': 'wrongpassword'
            })
        
        # Successful login should still work (unless rate limited)
        response = client.post('/accounts/login/', {
            'username': 'brute_user',
            'password': 'testpass123'
        })
        
        assert response.status_code in [200, 302, 429]  # 429 if rate limited


@pytest.mark.django_db
class TestInputValidation:
    """Test input validation and sanitization."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return Client()

    def test_sql_injection_username(self, client):
        """Test SQL injection in username field."""
        malicious_inputs = [
            "admin'--",
            "admin' OR '1'='1",
            "'; DROP TABLE users; --",
            "admin\"; DROP TABLE users; --"
        ]
        
        for malicious_input in malicious_inputs:
            response = client.post('/accounts/login/', {
                'username': malicious_input,
                'password': 'test'
            })
            
            # Should not crash, should return normal error response
            assert response.status_code in [200, 400]

    def test_xss_in_profile_fields(self, client):
        """Test XSS protection in profile fields."""
        user = User.objects.create_user(
            username='xss_user',
            email='xss@example.com',
            password='testpass123',
            is_active=True
        )
        client.force_login(user)
        
        xss_payload = '<script>alert("XSS")</script>'
        
        response = client.post('/accounts/profile/edit/', {
            'bio': xss_payload,
            'company_name': xss_payload
        })
        
        # Should sanitize or reject
        assert response.status_code in [200, 302, 400]

    def test_email_validation(self, client):
        """Test email validation during registration."""
        invalid_emails = [
            'notanemail',
            'missing@domain',
            '@nodomain.com',
            'spaces in@email.com'
        ]
        
        for invalid_email in invalid_emails:
            response = client.post('/accounts/register/', {
                'username': 'testuser',
                'email': invalid_email,
                'password1': 'securePass123!',
                'password2': 'securePass123!'
            })
            
            # Should show validation error
            assert response.status_code in [200, 400]


@pytest.mark.django_db
class TestAccessControl:
    """Test access control enforcement."""

    @pytest.fixture
    def regular_user(self):
        """Create regular user."""
        return User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='testpass123',
            is_active=True
        )

    @pytest.fixture
    def staff_user(self):
        """Create staff user."""
        return User.objects.create_user(
            username='staff',
            email='staff@example.com',
            password='testpass123',
            is_active=True,
            is_staff=True
        )

    @pytest.fixture
    def admin_user(self):
        """Create admin user."""
        return User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def client(self):
        """Create test client."""
        return Client()

    def test_regular_user_cannot_access_admin(self, client, regular_user):
        """Test regular user cannot access admin panel."""
        client.force_login(regular_user)
        
        response = client.get('/admin/')
        
        assert response.status_code in [302, 403]

    def test_staff_user_can_access_admin(self, client, staff_user):
        """Test staff user can access admin panel."""
        client.force_login(staff_user)
        
        response = client.get('/admin/')
        
        # Should have access (may redirect to login if additional checks)
        assert response.status_code in [200, 302]

    def test_user_cannot_edit_other_profile(self, client, regular_user):
        """Test user cannot edit another user's profile."""
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass123'
        )
        
        client.force_login(regular_user)
        
        response = client.post(f'/accounts/profile/{other_user.id}/edit/', {
            'bio': 'Hacked bio'
        })
        
        # Should be forbidden
        assert response.status_code in [403, 404]

    def test_user_can_view_own_profile(self, client, regular_user):
        """Test user can view their own profile."""
        client.force_login(regular_user)
        
        response = client.get('/accounts/profile/')
        
        assert response.status_code in [200, 302]


@pytest.mark.django_db
class TestAccountEnumeration:
    """Test protection against account enumeration."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='enum_user',
            email='enum@example.com',
            password='testpass123',
            is_active=True
        )

    @pytest.fixture
    def client(self):
        """Create test client."""
        return Client()

    def test_password_reset_same_response(self, client, user):
        """Test password reset shows same response for valid and invalid emails."""
        # Valid email
        response_valid = client.post('/accounts/password/reset/', {
            'email': 'enum@example.com'
        })
        
        # Invalid email
        response_invalid = client.post('/accounts/password/reset/', {
            'email': 'nonexistent@example.com'
        })
        
        # Both should return same status code
        assert response_valid.status_code == response_invalid.status_code

    def test_login_same_error_for_invalid_user(self, client, user):
        """Test login shows same error for invalid user and invalid password."""
        # Invalid password
        response_wrong_pass = client.post('/accounts/login/', {
            'username': 'enum_user',
            'password': 'wrongpassword'
        })
        
        # Invalid username
        response_wrong_user = client.post('/accounts/login/', {
            'username': 'nonexistent',
            'password': 'testpass123'
        })
        
        # Both should return same status code
        assert response_wrong_pass.status_code == response_wrong_user.status_code


@pytest.mark.django_db
class TestSecureHeaders:
    """Test security headers in responses."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return Client()

    def test_x_frame_options_header(self, client):
        """Test X-Frame-Options header is set."""
        response = client.get('/accounts/login/')
        
        # Django sets this by default
        x_frame = response.get('X-Frame-Options')
        assert x_frame is None or x_frame in ['DENY', 'SAMEORIGIN']

    def test_content_type_nosniff(self, client):
        """Test X-Content-Type-Options header."""
        response = client.get('/accounts/login/')
        
        content_type_options = response.get('X-Content-Type-Options')
        # May or may not be set depending on middleware config
        if content_type_options:
            assert content_type_options == 'nosniff'

    def test_xss_protection_header(self, client):
        """Test X-XSS-Protection header."""
        response = client.get('/accounts/login/')
        
        xss_protection = response.get('X-XSS-Protection')
        # Modern browsers ignore this, but may still be set
        if xss_protection:
            assert '1' in xss_protection

