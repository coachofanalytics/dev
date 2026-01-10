"""
Rate Limiting Security Tests.
Pillar 10: Rate Limiting & Abuse Protection

Tests:
- Login brute-force protection
- Password reset throttling
- Registration throttling
- API rate limits
"""

import pytest
import time
from django.test import TestCase, Client
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.security
class TestRateLimiting(TestCase):
    """
    Tests for rate limiting on sensitive endpoints.
    Failures indicate MISSING PROTECTION suitable for production.
    """

    def setUp(self):
        self.user = User.objects.create_user('rate_user', 'pw')
        self.client = Client()

    def test_login_bruteforce_protection(self):
        """
        SECURITY TEST: Attempt 20 failed logins.
        Should receive 429 Too Many Requests.
        """
        success_count = 0
        limit = 30  # Threshold
        
        for i in range(limit):
            response = self.client.post('/accounts/login/', {
                'username': 'rate_user', 
                'password': f'wrong_{i}'
            })
            if response.status_code == 429:
                return  # Test Passed: Rate limit triggered
            elif response.status_code == 200:
                success_count += 1
                
        # If we get here, no rate limit triggered
        if success_count >= limit:
             pytest.fail(
                 f"SECURITY VULNERABILITY: No rate limiting on login detected after {limit} failed attempts. "
                 "Implement django-axes or similar."
             )

    def test_password_reset_throttling(self):
        """
        SECURITY TEST: Attempt 10 password reset requests.
        """
        limit = 10
        email = 'rate@test.com'
        
        rate_limited = False
        for i in range(limit):
            response = self.client.post('/accounts/password/reset/', {'email': email})
            if response.status_code == 429:
                rate_limited = True
                break
        
        if not rate_limited:
             # We might choose to escalate this to Failure or Warning
             pytest.fail("SECURITY WARNING: No rate limiting on password reset endpoint.")

    def test_registration_throttling(self):
        """
        SECURITY TEST: Attempt 10 registrations from same IP.
        """
        limit = 10
        rate_limited = False
        
        for i in range(limit):
            response = self.client.post('/accounts/register/', {
                'username': f'bot_{i}',
                'email': f'bot_{i}@test.com',
                'password': 'password123',
                'confirm_password': 'password123'
            })
            if response.status_code == 429:
                rate_limited = True
                break
                
        if not rate_limited:
            pytest.fail("SECURITY WARNING: No rate limiting on registration endpoint.")
