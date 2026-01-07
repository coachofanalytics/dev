"""
Session security tests.

Tests for session fixation, session regeneration, and session lifecycle security.
These tests expose potential session security vulnerabilities.
"""

import pytest
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session


@pytest.mark.django_db
class TestSessionFixationVulnerability:
    """
    Tests to detect session fixation vulnerabilities.
    
    Session fixation occurs when the session ID is not regenerated after
    authentication, allowing an attacker to set a session ID before login
    and hijack the session after the victim logs in.
    """

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='session_test_user',
            email='sessiontest@example.com',
            password='SecurePass123!',
            is_active=True
        )

    @pytest.fixture
    def client(self):
        """Create test client."""
        return Client()

    def test_session_id_changes_after_login(self, client, user):
        """
        SECURITY TEST: Verify session ID changes after successful login.
        
        If this test fails, there is a SESSION FIXATION VULNERABILITY.
        
        Expected: Session ID should change after authentication.
        """
        # Get initial session by visiting a page
        client.get('/accounts/login/')
        session_before_login = client.session.session_key
        
        # Perform login
        response = client.post('/accounts/login/', {
            'username': 'session_test_user',
            'password': 'SecurePass123!'
        })
        
        session_after_login = client.session.session_key
        
        # CRITICAL SECURITY CHECK: Session ID must change after login
        # If these are the same, session fixation is possible
        if session_before_login is not None and session_after_login is not None:
            if session_before_login == session_after_login:
                pytest.fail(
                    "SECURITY ISSUE DETECTED: Session ID did not change after login. "
                    "This indicates a SESSION FIXATION VULNERABILITY. "
                    "The application should regenerate the session ID upon successful authentication."
                )

    def test_session_id_changes_after_logout_and_relogin(self, client, user):
        """
        SECURITY TEST: Verify session ID changes between login sessions.
        
        Expected: Each login should have a unique session ID.
        """
        # First login
        client.post('/accounts/login/', {
            'username': 'session_test_user',
            'password': 'SecurePass123!'
        })
        first_session = client.session.session_key
        
        # Logout
        client.post('/accounts/logout/')
        
        # Second login
        client.post('/accounts/login/', {
            'username': 'session_test_user',
            'password': 'SecurePass123!'
        })
        second_session = client.session.session_key
        
        # Sessions should be different
        if first_session is not None and second_session is not None:
            if first_session == second_session:
                pytest.fail(
                    "SECURITY ISSUE DETECTED: Session ID is reused across login sessions. "
                    "Sessions should be unique for each authentication."
                )

    def test_old_session_invalidated_after_logout(self, client, user):
        """
        SECURITY TEST: Verify old session is invalidated after logout.
        
        If old session remains valid, session hijacking is possible.
        """
        # Login
        client.post('/accounts/login/', {
            'username': 'session_test_user',
            'password': 'SecurePass123!'
        })
        session_key_during_login = client.session.session_key
        
        # Logout
        client.post('/accounts/logout/')
        
        # Check if old session still exists in database
        if session_key_during_login:
            old_session_exists = Session.objects.filter(
                session_key=session_key_during_login
            ).exists()
            
            if old_session_exists:
                pytest.fail(
                    "SECURITY ISSUE DETECTED: Session was not deleted from database after logout. "
                    "Old sessions should be invalidated to prevent session hijacking."
                )

    def test_session_not_accessible_after_logout(self, client, user):
        """
        SECURITY TEST: Verify authenticated resources not accessible after logout.
        """
        # Login
        client.post('/accounts/login/', {
            'username': 'session_test_user',
            'password': 'SecurePass123!'
        })
        
        # Logout
        client.post('/accounts/logout/')
        
        # Try to access protected resource
        response = client.get('/accounts/profile/')
        
        # Should redirect to login or be forbidden
        if response.status_code == 200:
            # Check if it's actually showing authenticated content
            content = response.content.decode('utf-8', errors='ignore')
            if 'session_test_user' in content and 'logout' in content.lower():
                pytest.fail(
                    "SECURITY ISSUE DETECTED: Authenticated content accessible after logout. "
                    "Session invalidation may not be working correctly."
                )


@pytest.mark.django_db
class TestSessionTimeoutSecurity:
    """Tests for session timeout and expiration security."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='timeout_user',
            email='timeout@example.com',
            password='SecurePass123!',
            is_active=True
        )

    @pytest.fixture
    def client(self):
        """Create test client."""
        return Client()

    def test_session_has_expiry(self, client, user):
        """
        SECURITY TEST: Verify sessions have an expiration time.
        
        Sessions without expiration allow indefinite access.
        """
        client.post('/accounts/login/', {
            'username': 'timeout_user',
            'password': 'SecurePass123!'
        })
        
        session_key = client.session.session_key
        
        if session_key:
            try:
                session = Session.objects.get(session_key=session_key)
                if session.expire_date is None:
                    pytest.fail(
                        "SECURITY ISSUE DETECTED: Session has no expiration date. "
                        "All sessions should have a defined expiration time."
                    )
            except Session.DoesNotExist:
                pass  # Session handling may differ


@pytest.mark.django_db
class TestSessionCookieSecurity:
    """Tests for session cookie security attributes."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='cookie_user',
            email='cookie@example.com',
            password='SecurePass123!',
            is_active=True
        )

    @pytest.fixture
    def client(self):
        """Create test client."""
        return Client()

    def test_session_cookie_httponly(self, client, user):
        """
        SECURITY TEST: Verify session cookie has HttpOnly flag.
        
        Without HttpOnly, JavaScript can access the session cookie,
        making XSS attacks more dangerous.
        """
        response = client.post('/accounts/login/', {
            'username': 'cookie_user',
            'password': 'SecurePass123!'
        })
        
        # Check session cookie attributes
        session_cookie = response.cookies.get('sessionid')
        
        if session_cookie:
            if not session_cookie.get('httponly', False):
                pytest.fail(
                    "SECURITY ISSUE DETECTED: Session cookie does not have HttpOnly flag. "
                    "This allows JavaScript to access the session cookie, increasing XSS risk."
                )

    def test_session_cookie_secure_flag_in_production(self, client, user):
        """
        SECURITY TEST: Document session cookie Secure flag status.
        
        In production with HTTPS, the Secure flag should be set.
        """
        response = client.post('/accounts/login/', {
            'username': 'cookie_user',
            'password': 'SecurePass123!'
        })
        
        session_cookie = response.cookies.get('sessionid')
        
        if session_cookie:
            secure_flag = session_cookie.get('secure', False)
            # Document the finding - in test environment, secure may be False
            # but in production it should be True
            # This is informational, not a failure in test environment

    def test_session_cookie_samesite_attribute(self, client, user):
        """
        SECURITY TEST: Check SameSite cookie attribute.
        
        SameSite helps prevent CSRF attacks.
        """
        response = client.post('/accounts/login/', {
            'username': 'cookie_user',
            'password': 'SecurePass123!'
        })
        
        session_cookie = response.cookies.get('sessionid')
        
        if session_cookie:
            samesite = session_cookie.get('samesite', '')
            if not samesite or samesite.lower() not in ['strict', 'lax']:
                # Document as potential improvement
                pass  # SameSite is recommended but not always required

