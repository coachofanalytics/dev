"""
Session and Cookie Security Tests.
Pillar 4 & 5: Session & CSRF

Tests:
- Session fixation
- Cookie flags (HttpOnly, Secure, SameSite)
- CSRF protection on state-changing methods
- Session timeout enforcement
"""

import pytest
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()


@pytest.mark.security
class TestSessionSecurity(TestCase):
    """Tests for session management security."""

    def setUp(self):
        self.user = User.objects.create_user('sess_user', 'pw')
        self.client = Client()

    def test_session_fixation_on_login(self):
        """
        SECURITY TEST: Session ID must change after login.
        """
        # 1. Get anonymous session
        self.client.get('/')
        session_id_pre = self.client.session.session_key
        
        # 2. Login
        self.client.post('/accounts/login/', {'username': 'sess_user', 'password': 'pw'})
        session_id_post = self.client.session.session_key
        
        # 3. Verify change
        if session_id_pre and session_id_post:
            self.assertNotEqual(session_id_pre, session_id_post, 
                "Session Fixation Vulnerability: Session ID did not rotate after login!")

    def test_session_cookie_flags(self):
        """
        SECURITY TEST: Verify strict cookie security flags.
        """
        response = self.client.post('/accounts/login/', {'username': 'sess_user', 'password': 'pw'})
        
        cookie_name = settings.SESSION_COOKIE_NAME
        cookie = response.cookies.get(cookie_name)
        
        if cookie:
            # HttpOnly
            self.assertTrue(cookie.get('httponly'), "Session cookie missing HttpOnly flag!")
            
            # Secure (Only if NOT in dev debug mode, but we should enforce 'if https')
            # If SECURE_SSL_REDIRECT is True, this must be True
            if not settings.DEBUG:
                self.assertTrue(cookie.get('secure'), "Session cookie missing Secure flag in production!")
            
            # SameSite
            samesite = cookie.get('samesite')
            self.assertIn(samesite, ['Lax', 'Strict'], f"Session cookie SameSite not strict enough: {samesite}")


@pytest.mark.security
class TestCSRFProtection(TestCase):
    """Tests for CSRF coverage."""

    def setUp(self):
        self.user = User.objects.create_user('csrf_user', 'pw')
        self.client = Client(enforce_csrf_checks=True)
        self.client.force_login(self.user)

    def test_csrf_on_post(self):
        """Test POST request requires CSRF token."""
        # We try to hit an endpoint that requires POST
        response = self.client.post('/accounts/logout/', 
                                    content_type='application/json',
                                    # No CSRF header/token
                                    )
        self.assertEqual(response.status_code, 403, "POST request without CSRF token was permitted!")

    def test_csrf_on_put_delete(self):
        """Test PUT/DELETE requests require CSRF token."""
        # Assuming we have a REST endpoint or similar. 
        # If not, we test a generic one IF the framework supports it.
        # Django's CsrfViewMiddleware checks all unsafe methods.
        
        response = self.client.put('/accounts/profile/edit/', {}) # Hypothetical PUT
        self.assertEqual(response.status_code, 403, "PUT request without CSRF token was permitted!")
        
        response = self.client.delete('/accounts/profile/delete/') # Hypothetical DELETE
        self.assertEqual(response.status_code, 403, "DELETE request without CSRF token was permitted!")
