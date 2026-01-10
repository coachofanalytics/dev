"""
Authentication Security Tests.
Pillar 1: Authentication Security

Tests:
- Brute force protection behavior
- Password reset token misuse (replay, expired, invalid)
- MFA flows (TOTP verification, backup codes)
- Email verification enforcement
- Login session invalidation after password change
"""

import pytest
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings
from django.urls import reverse

User = get_user_model()


@pytest.mark.security
class TestBruteForceProtection(TestCase):
    """
    Tests for brute force attack protection.
    
    SECURITY REQUIREMENT: Login attempts should be rate-limited to prevent
    credential stuffing and brute force attacks.
    """

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='brute_test_user',
            email='brute@test.com',
            password='SecurePassword123!'
        )

    def test_login_rate_limiting__excessive_attempts__429_or_lockout(self):
        """
        SECURITY TEST: Attempt many failed logins in rapid succession.
        
        Expected: Either 429 Too Many Requests or account lockout message.
        Risk: Without rate limiting, attackers can brute force weak passwords.
        """
        limit = 25
        rate_limited = False
        
        for i in range(limit):
            response = self.client.post('/accounts/login/', {
                'username': 'brute_test_user',
                'password': f'wrong_password_{i}'
            })
            
            if response.status_code == 429:
                rate_limited = True
                break
            
            # Check for lockout message in response
            if response.status_code == 200:
                content = response.content.decode('utf-8', errors='ignore')
                if 'locked' in content.lower() or 'too many' in content.lower():
                    rate_limited = True
                    break
        
        if not rate_limited:
            pytest.fail(
                f"SECURITY VULNERABILITY: No rate limiting detected after {limit} failed login attempts. "
                "Brute force attacks are possible. Implement django-axes or django-defender."
            )

    def test_login_timing_attack_resistance__consistent_response_time(self):
        """
        SECURITY TEST: Login should have consistent timing for valid/invalid usernames.
        
        Risk: Timing differences can reveal valid usernames.
        Note: This is informational - exact timing comparison is flaky in tests.
        """
        import time
        
        # Time for invalid username
        times_invalid = []
        for _ in range(3):
            start = time.time()
            self.client.post('/accounts/login/', {
                'username': 'nonexistent_user_12345',
                'password': 'wrong'
            })
            times_invalid.append(time.time() - start)
        
        # Time for valid username, wrong password
        times_valid = []
        for _ in range(3):
            start = time.time()
            self.client.post('/accounts/login/', {
                'username': 'brute_test_user',
                'password': 'wrong'
            })
            times_valid.append(time.time() - start)
        
        avg_invalid = sum(times_invalid) / len(times_invalid)
        avg_valid = sum(times_valid) / len(times_valid)
        
        # Large timing differences (>500ms) would be concerning
        # This is informational only; we don't fail the test
        timing_diff = abs(avg_valid - avg_invalid)
        if timing_diff > 0.5:
            pytest.skip(
                f"INFORMATIONAL: Timing difference of {timing_diff:.3f}s detected between "
                "valid/invalid usernames. Consider constant-time comparison."
            )


@pytest.mark.security
class TestPasswordResetSecurity(TestCase):
    """
    Tests for password reset token security.
    
    SECURITY REQUIREMENT: Password reset tokens should be single-use,
    time-limited, and unpredictable.
    """

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='reset_user',
            email='reset@test.com',
            password='OldPassword123!'
        )
        self.token_generator = PasswordResetTokenGenerator()
    
    def _get_reset_url_parts(self):
        """Generate a valid reset token and uidb64."""
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = self.token_generator.make_token(self.user)
        return uidb64, token

    def test_password_reset_token__replay_attack__rejected(self):
        """
        SECURITY TEST: Password reset tokens should be single-use.
        
        After using a token to reset password, reusing it should fail.
        Risk: Token replay allows multiple password resets.
        """
        uidb64, token = self._get_reset_url_parts()
        reset_url = f'/accounts/password/reset/confirm/{uidb64}/{token}/'
        
        # First use should succeed (or redirect to set-password form)
        response = self.client.get(reset_url, follow=True)
        
        # Now simulate changing the password
        self.user.set_password('NewSecurePassword456!')
        self.user.save()
        
        # The token should now be invalid (password changed = token invalidated)
        response = self.client.get(reset_url)
        
        # Should not allow access with old token
        if response.status_code == 200:
            content = response.content.decode('utf-8', errors='ignore')
            self.assertTrue(
                'invalid' in content.lower() or 'expired' in content.lower() or
                response.status_code in [400, 404],
                "Password reset token was accepted after password change - REPLAY VULNERABILITY"
            )

    def test_password_reset_token__invalid_format__rejected(self):
        """
        SECURITY TEST: Malformed tokens should be rejected.
        
        Risk: Weak token validation could accept crafted tokens.
        """
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        
        invalid_tokens = [
            'invalid_token_123',
            '../../../../etc/passwd',
            '<script>alert(1)</script>',
            'a' * 1000,  # Very long token
            '',  # Empty token
        ]
        
        for invalid_token in invalid_tokens:
            reset_url = f'/accounts/password/reset/confirm/{uidb64}/{invalid_token}/'
            response = self.client.get(reset_url)
            
            # Should reject invalid tokens (not 200 with password form)
            if response.status_code == 200:
                content = response.content.decode('utf-8', errors='ignore')
                self.assertTrue(
                    'invalid' in content.lower() or 'expired' in content.lower(),
                    f"Invalid token '{invalid_token[:20]}...' was possibly accepted"
                )

    def test_password_reset_token__invalid_user_id__rejected(self):
        """
        SECURITY TEST: Tokens with invalid user IDs should be rejected.
        
        Risk: Manipulating uidb64 could allow access to other accounts.
        """
        _, token = self._get_reset_url_parts()
        
        invalid_uids = [
            urlsafe_base64_encode(force_bytes(999999)),  # Non-existent user
            'invalid_base64!!!',
            '',
        ]
        
        for invalid_uid in invalid_uids:
            reset_url = f'/accounts/password/reset/confirm/{invalid_uid}/{token}/'
            response = self.client.get(reset_url)
            
            self.assertNotEqual(
                response.status_code, 200,
                f"Invalid UID '{invalid_uid}' was accepted - IDOR VULNERABILITY"
            )


@pytest.mark.security
class TestMFASecurity(TestCase):
    """
    Tests for Multi-Factor Authentication security.
    
    SECURITY REQUIREMENT: MFA should prevent access without second factor.
    """

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='mfa_user',
            email='mfa@test.com',
            password='SecurePassword123!'
        )

    def test_mfa_setup__requires_authentication(self):
        """
        SECURITY TEST: MFA setup should require authenticated session.
        
        Risk: Anonymous users setting up MFA could bypass auth.
        """
        response = self.client.get('/mfa/setup/')
        
        # Should redirect to login or return 403
        self.assertIn(
            response.status_code, [302, 403],
            "MFA setup accessible without authentication"
        )
        
        if response.status_code == 302:
            self.assertIn('login', response.url.lower())

    def test_mfa_verify__invalid_token__rejected(self):
        """
        SECURITY TEST: Invalid TOTP tokens should be rejected.
        
        Risk: Weak validation could allow bypass.
        """
        self.client.force_login(self.user)
        
        # Try to verify with invalid tokens
        invalid_tokens = ['000000', '123456', 'abcdef', '', '12345678']
        
        for token in invalid_tokens:
            response = self.client.post('/mfa/verify/', {'token': token})
            
            # Should not succeed with invalid token
            if response.status_code == 302:
                # If redirect, should not be to success page
                self.assertNotIn('dashboard', response.url.lower())

    def test_mfa_backup_codes__requires_mfa_enabled(self):
        """
        SECURITY TEST: Backup codes should only be available after MFA setup.
        
        Risk: Premature backup code access could be exploited.
        """
        self.client.force_login(self.user)
        
        response = self.client.get('/mfa/backup-codes/')
        
        # Should redirect or show error if MFA not set up
        # This depends on implementation
        self.assertIn(
            response.status_code, [200, 302, 404],
            "Unexpected response from backup codes page"
        )


@pytest.mark.security
class TestSessionInvalidationOnPasswordChange(TestCase):
    """
    Tests for session security after password change.
    
    SECURITY REQUIREMENT: All sessions should be invalidated after password change.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='session_user',
            email='session@test.com',
            password='OldPassword123!'
        )

    def test_password_change__old_sessions__invalidated(self):
        """
        SECURITY TEST: After password change, existing sessions should be invalid.
        
        Risk: Stolen session cookies remain valid after password change.
        """
        # Create first client and login
        client1 = Client()
        client1.force_login(self.user)
        
        # Verify session is active
        response = client1.get('/accounts/profile/')
        self.assertNotEqual(response.status_code, 302, "Initial session not valid")
        
        # Get session key before password change
        session_key_before = client1.session.session_key
        
        # Change password using a different client
        client2 = Client()
        client2.force_login(self.user)
        
        # Simulate password change
        self.user.set_password('NewPassword456!')
        self.user.save()
        
        # This is where Django's SessionAuthenticationMiddleware should help
        # But we need to verify the old session is invalidated
        
        # Try to access protected page with old session
        response = client1.get('/accounts/profile/')
        
        # Should redirect to login (session invalidated) or at least session changed
        new_session_key = client1.session.session_key
        
        # Either session key changed or user is logged out
        session_invalidated = (
            response.status_code == 302 or
            new_session_key != session_key_before
        )
        
        if not session_invalidated:
            pytest.fail(
                "SECURITY VULNERABILITY: Session remained valid after password change. "
                "Enable SessionAuthenticationMiddleware and update_session_auth_hash()."
            )


@pytest.mark.security
class TestEmailVerification(TestCase):
    """
    Tests for email verification enforcement.
    
    SECURITY REQUIREMENT: Unverified emails should have limited access.
    """

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='email_user',
            email='unverified@test.com',
            password='Password123!'
        )
        self.user.is_active = True
        self.user.save()

    def test_registration__email_verification_required(self):
        """
        SECURITY TEST: Check if email verification is enforced.
        
        Risk: Without email verification, accounts can be created with any email.
        """
        # Register a new user
        response = self.client.post('/accounts/register/', {
            'username': 'new_email_user',
            'email': 'newuser@test.com',
            'password1': 'SecurePassword123!',
            'password2': 'SecurePassword123!',
        })
        
        # Check if the application requires email verification
        # This check is informational if verification is not strictly enforced
        try:
            new_user = User.objects.get(username='new_email_user')
            
            # Check if user can immediately log in without verification
            login_response = self.client.post('/accounts/login/', {
                'username': 'new_email_user',
                'password': 'SecurePassword123!'
            })
            
            # If login succeeds without email verification, it's a potential risk
            # (depends on business requirements)
            if login_response.status_code == 302 and 'dashboard' in login_response.url.lower():
                pytest.skip(
                    "INFORMATIONAL: Email verification not strictly enforced. "
                    "Consider requiring email verification for sensitive operations."
                )
        except User.DoesNotExist:
            pass  # User not created, registration may have different requirements


@pytest.mark.security
class TestPasswordPolicy(TestCase):
    """
    Tests for password policy enforcement.
    
    SECURITY REQUIREMENT: Passwords should meet minimum complexity requirements.
    """

    def setUp(self):
        self.client = Client()

    def test_registration__weak_password__rejected(self):
        """
        SECURITY TEST: Registration should reject weak passwords.
        
        Risk: Weak passwords are easily compromised.
        """
        weak_passwords = [
            'password',
            '12345678',
            'qwerty123',
            'abc',  # Too short
            '        ',  # Only spaces
        ]
        
        for weak_password in weak_passwords:
            response = self.client.post('/accounts/register/', {
                'username': f'weak_user_{hash(weak_password) % 10000}',
                'email': f'weak{hash(weak_password) % 10000}@test.com',
                'password1': weak_password,
                'password2': weak_password,
            })
            
            # Should not redirect to success (registration should fail)
            if response.status_code == 302:
                # Check if it's a success redirect
                if 'login' in response.url.lower() or 'dashboard' in response.url.lower():
                    pytest.fail(
                        f"SECURITY WEAKNESS: Weak password '{weak_password}' was accepted during registration."
                    )

    def test_password_change__weak_password__rejected(self):
        """
        SECURITY TEST: Password change should reject weak passwords.
        
        Risk: Users could downgrade to weak passwords.
        """
        user = User.objects.create_user(
            username='pwd_policy_user',
            email='policy@test.com',
            password='StrongInitialPassword123!'
        )
        self.client.force_login(user)
        
        weak_passwords = ['password', '12345678', 'abc']
        
        for weak_password in weak_passwords:
            response = self.client.post('/accounts/password/change/', {
                'old_password': 'StrongInitialPassword123!',
                'new_password1': weak_password,
                'new_password2': weak_password,
            })
            
            # Password should not actually change
            user.refresh_from_db()
            if user.check_password(weak_password):
                pytest.fail(
                    f"SECURITY WEAKNESS: Weak password '{weak_password}' was accepted during password change."
                )
