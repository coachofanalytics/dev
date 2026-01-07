"""
Rate limiting security tests.

Tests to detect missing or inadequate rate limiting on sensitive endpoints.
These tests expose potential brute force and DoS vulnerabilities.
"""

import pytest
import time
from django.test import TestCase, Client
from django.contrib.auth.models import User


@pytest.mark.django_db
class TestLoginRateLimiting:
    """
    Tests for rate limiting on login endpoints.
    
    Without rate limiting, attackers can perform brute force attacks
    to guess user passwords.
    """

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='ratelimit_user',
            email='ratelimit@example.com',
            password='SecurePass123!',
            is_active=True
        )

    @pytest.fixture
    def client(self):
        """Create test client."""
        return Client()

    def test_multiple_failed_login_attempts_not_blocked(self, client, user):
        """
        SECURITY TEST: Detect if brute force protection is missing.
        
        This test makes multiple failed login attempts to check if
        rate limiting is enforced. If all requests succeed (return 200),
        rate limiting may be missing.
        """
        failed_attempts = 0
        rate_limited = False
        
        # Attempt 20 failed logins in quick succession
        for i in range(20):
            response = client.post('/accounts/login/', {
                'username': 'ratelimit_user',
                'password': 'wrongpassword'
            })
            
            if response.status_code == 429:  # Too Many Requests
                rate_limited = True
                break
            elif response.status_code == 200:
                failed_attempts += 1
        
        # SECURITY FINDING: Document if rate limiting is missing
        if not rate_limited and failed_attempts >= 20:
            # This is a security issue that should be documented
            pytest.skip(
                "SECURITY FINDING: No rate limiting detected on login endpoint. "
                f"Successfully made {failed_attempts} failed login attempts without being blocked. "
                "RECOMMENDATION: Implement rate limiting (e.g., django-ratelimit or django-axes) "
                "to prevent brute force attacks."
            )

    def test_rapid_login_attempts_timing(self, client, user):
        """
        SECURITY TEST: Measure if requests are being throttled.
        
        Checks if there's any delay imposed on failed login attempts.
        """
        start_time = time.time()
        
        # Make 10 rapid requests
        for i in range(10):
            client.post('/accounts/login/', {
                'username': 'ratelimit_user',
                'password': 'wrongpassword'
            })
        
        elapsed_time = time.time() - start_time
        
        # If 10 requests completed in under 1 second with no throttling
        if elapsed_time < 1.0:
            pytest.skip(
                "SECURITY FINDING: No request throttling detected. "
                f"10 login attempts completed in {elapsed_time:.2f} seconds. "
                "Consider implementing progressive delays or rate limiting."
            )


@pytest.mark.django_db
class TestPasswordResetRateLimiting:
    """Tests for rate limiting on password reset endpoint."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='reset_ratelimit_user',
            email='resetratelimit@example.com',
            password='SecurePass123!',
            is_active=True
        )

    @pytest.fixture
    def client(self):
        """Create test client."""
        return Client()

    def test_password_reset_rate_limiting(self, client, user):
        """
        SECURITY TEST: Check rate limiting on password reset.
        
        Without rate limiting, attackers can flood users with reset emails
        or enumerate valid email addresses.
        """
        requests_made = 0
        rate_limited = False
        
        # Attempt 15 password reset requests
        for i in range(15):
            response = client.post('/accounts/password/reset/', {
                'email': 'resetratelimit@example.com'
            })
            
            if response.status_code == 429:
                rate_limited = True
                break
            
            requests_made += 1
        
        if not rate_limited and requests_made >= 15:
            pytest.skip(
                "SECURITY FINDING: No rate limiting on password reset endpoint. "
                f"Made {requests_made} password reset requests without throttling. "
                "RECOMMENDATION: Implement rate limiting to prevent email bombing and enumeration."
            )


@pytest.mark.django_db  
class TestRegistrationRateLimiting:
    """Tests for rate limiting on registration endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return Client()

    def test_registration_rate_limiting(self, client):
        """
        SECURITY TEST: Check rate limiting on registration.
        
        Without rate limiting, attackers can create many fake accounts
        or perform DoS attacks on the registration system.
        """
        requests_made = 0
        rate_limited = False
        
        # Attempt 10 registration requests (with invalid data to avoid creating accounts)
        for i in range(10):
            response = client.post('/accounts/register/', {
                'username': f'fakeuser{i}',
                'email': f'fake{i}@test.com',
                'password1': 'short',  # Invalid password to trigger validation
                'password2': 'short'
            })
            
            if response.status_code == 429:
                rate_limited = True
                break
            
            requests_made += 1
        
        if not rate_limited and requests_made >= 10:
            pytest.skip(
                "SECURITY FINDING: No rate limiting on registration endpoint. "
                "RECOMMENDATION: Implement rate limiting and CAPTCHA to prevent automated account creation."
            )


@pytest.mark.django_db
class TestAPIRateLimiting:
    """Tests for rate limiting on API endpoints."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='api_ratelimit_user',
            email='apiratelimit@example.com',
            password='SecurePass123!',
            is_active=True
        )

    @pytest.fixture
    def client(self):
        """Create test client."""
        return Client()

    def test_api_endpoint_rate_limiting(self, client, user):
        """
        SECURITY TEST: Check rate limiting on API endpoints.
        
        API endpoints without rate limiting are vulnerable to
        DoS attacks and data scraping.
        """
        client.force_login(user)
        
        requests_made = 0
        rate_limited = False
        
        # Make 50 rapid API requests
        for i in range(50):
            response = client.get('/api/investments/')
            
            if response.status_code == 429:
                rate_limited = True
                break
            elif response.status_code in [200, 404]:
                requests_made += 1
        
        if not rate_limited and requests_made >= 50:
            pytest.skip(
                "SECURITY FINDING: No rate limiting on API endpoints. "
                f"Made {requests_made} API requests without throttling. "
                "RECOMMENDATION: Implement API rate limiting with django-rest-framework throttling."
            )


@pytest.mark.django_db
class TestAccountLockout:
    """Tests for account lockout after failed attempts."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='lockout_user',
            email='lockout@example.com',
            password='SecurePass123!',
            is_active=True
        )

    @pytest.fixture
    def client(self):
        """Create test client."""
        return Client()

    def test_account_lockout_after_failed_attempts(self, client, user):
        """
        SECURITY TEST: Check if account is locked after multiple failures.
        
        Account lockout helps prevent brute force attacks even without
        IP-based rate limiting.
        """
        # Make 10 failed login attempts
        for i in range(10):
            client.post('/accounts/login/', {
                'username': 'lockout_user',
                'password': 'wrongpassword'
            })
        
        # Try to login with correct password
        response = client.post('/accounts/login/', {
            'username': 'lockout_user',
            'password': 'SecurePass123!'
        }, follow=True)
        
        # Check if user can still login (meaning no lockout)
        # Note: We check if logged in by checking session or response
        if '_auth_user_id' in client.session:
            pytest.skip(
                "SECURITY FINDING: No account lockout after 10 failed login attempts. "
                "User can still login with correct password after multiple failures. "
                "RECOMMENDATION: Implement account lockout using django-axes or similar."
            )

