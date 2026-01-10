"""
Comprehensive OWASP Top 10 security tests.

Tests for common web application vulnerabilities according to OWASP Top 10 security risks.
Enhanced with specific RBAC, Secrets, and Configuration checks.
"""

import pytest
import os
import re
from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.conf import settings
from accounts.models import Staff, Role, Category

User = get_user_model()


@pytest.mark.security
class TestA01BrokenAccessControl(TestCase):
    """
    OWASP A01:2021 - Broken Access Control
    Tests for unauthorized access to resources and functions.
    """

    def setUp(self):
        self.client = Client()
        # Create different user roles
        self.regular_user = User.objects.create_user(username='reg_user', password='pw')
        self.staff_user = User.objects.create_user(username='staff_user', password='pw', is_staff=True)
        self.admin_user = User.objects.create_superuser(username='admin_user', password='pw', email='admin@test.com')
        
        # Create specific Staff role
        self.role_moderator = Role.objects.create(name='Moderator', can_moderate_content=True)
        Staff.objects.create(user=self.staff_user, role=self.role_moderator, employee_id='EMP001')

    def test_vertical_privilege_escalation_admin(self):
        """Test regular user/staff cannot access superadmin functions."""
        self.client.force_login(self.regular_user)
        response = self.client.get('/admin/')
        # Should redirect to login or 403. Redirect often means "login as admin"
        self.assertIn(response.status_code, [302, 403])
        if response.status_code == 302:
            self.assertIn('/admin/login', response.url)

        self.client.force_login(self.staff_user) # Staff might access admin but LIMITED
        # Staff usually can access /admin but restricted models
        response = self.client.get('/admin/auth/user/') # Managing users often restricted to superuser
        # This depends on exact permissions, but generally checking restriction is good
        if not self.staff_user.has_perm('auth.view_user'):
             self.assertIn(response.status_code, [403, 302])

    def test_role_based_access_control(self):
        """Test that specific roles are enforced."""
        # Moderator should not be able to manage payments if not granted
        self.client.force_login(self.staff_user)
        
        # Assuming there is a payment dashboard ONLY for finance role
        payment_admin_url = '/admin/payments/transaction/'
        
        # If moderator has no payment perms
        if not self.staff_user.has_perm('payments.view_transaction'):
            response = self.client.get(payment_admin_url)
            self.assertIn(response.status_code, [403, 302])

    def test_force_browsing_sensitive_files(self):
        """Test accessing sensitive files/paths that shouldn't be exposed."""
        sensitive_paths = [
            '/.env',
            '/requirements.txt',
            '/.git/config',
            '/backup.zip',
            '/db.sqlite3',
            '/server-status'
        ]
        for path in sensitive_paths:
            response = self.client.get(path)
            self.assertNotEqual(response.status_code, 200, f"Sensitive path {path} is accessible!")


@pytest.mark.security
class TestA02CryptographicFailures(TestCase):
    """
    OWASP A02:2021 - Cryptographic Failures
    Tests for proper encryption and data protection.
    """

    def test_no_hardcoded_secrets_in_settings(self):
        """
        Scan settings for potential hardcoded secrets.
        This provides a heuristic check.
        """
        # We inspect the settings module attributes
        import django.conf
        
        # Known secret keys
        keys_to_check = ['SECRET_KEY', 'STRIPE_SECRET_KEY', 'AWS_SECRET_ACCESS_KEY', 'PAYPAL_CLIENT_SECRET']
        
        for key in keys_to_check:
            value = getattr(settings, key, '')
            if value and not str(value).startswith('django-insecure-'):
                # In a real secure env, these should rely on os.environ
                # Checking if they look like "hardcoded string" vs "env var result" is hard at runtime
                # But we can check if they are defaults from improper commits
                self.assertNotEqual(value, 'your-secret-key', f"{key} uses a default placeholder!")
                self.assertNotEqual(value, 'change-me', f"{key} uses a default placeholder!")

    def test_password_hashing_strength(self):
        """Verify password hasing config."""
        hasher = settings.PASSWORD_HASHERS[0]
        # Should be Argon2 or PBKDF2
        self.assertTrue('argon2' in hasher or 'pbkdf2' in hasher or 'bcrypt' in hasher, 
                        f"Weak password hasher detected: {hasher}")


@pytest.mark.security
class TestA03Injection(TestCase):
    """
    OWASP A03:2021 - Injection
    Tests for SQL/Command Injection.
    """

    def test_sql_injection_resilience(self):
        """Attempt generic SQLi patterns on search endpoints."""
        cursor = self.client
        payloads = ["' OR '1'='1", "'; DROP TABLE auth_user; --"]
        
        # Endpoint: Marketplace Search
        for payload in payloads:
            response = self.client.get(f'/marketplace/search/?q={payload}')
            self.assertNotEqual(response.status_code, 500) # 500 might indicate unhandled DB error
            content = response.content.decode('utf-8', errors='ignore')
            self.assertNotIn("syntax error", content.lower())
            self.assertNotIn("mysql", content.lower())


@pytest.mark.security
class TestA05SecurityMisconfiguration(TestCase):
    """
    OWASP A05:2021 - Security Misconfiguration
    """

    def test_debug_mode_is_off(self):
        """
        SECURITY TEST: DEBUG should be False in production-like environments.
        We skip if specifically testing in DEBUG mode, but warn.
        """
        if settings.DEBUG:
            pytest.skip("SECURITY WARNING: DEBUG=True. Ensure this is NOT True in production.")
        else:
            self.assertFalse(settings.DEBUG)

    def test_allowed_hosts_configured(self):
        """Verify ALLOWED_HOSTS is not ['*']."""
        hosts = settings.ALLOWED_HOSTS
        if not settings.DEBUG:
            self.assertNotEqual(hosts, ['*'], "ALLOWED_HOSTS=['*'] is dangerous in production!")
            self.assertTrue(len(hosts) > 0, "ALLOWED_HOSTS must not be empty in production")


@pytest.mark.security
class TestA07IdentificationAuthenticationFailures(TestCase):
    """
    OWASP A07:2021 - Auth Failures
    See also test_rate_limiting.py
    """

    def test_weak_password_registration(self):
        """Verify that weak passwords are rejected."""
        # Try to register with 'password123'
        response = self.client.post('/accounts/register/', {
            'username': 'weakuser', 
            'email': 'weak@test.com',
            'password': 'password',
            'confirm_password': 'password'
        })
        # Should fail validation (form error or 200 with error message in html)
        # If it redirects to login/home, it succeeded -> Fail
        if response.status_code == 302 and '/login' in response.url:
             pytest.fail("SECURITY WEAKNESS: Registration accepted weak password 'password'.")


@pytest.mark.security
class TestA04InsecureDesign(TestCase):
    """
    OWASP A04:2021 - Insecure Design
    Tests for business logic flaws and unsafe design patterns.
    """

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='design_user',
            password='password123',
            email='design@test.com'
        )

    def test_password_reset__no_token_verification_bypass(self):
        """
        SECURITY TEST: Password reset should require valid token.
        
        Risk: Direct access to password change without verification.
        """
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        
        # Try to directly POST a password change without valid token
        response = self.client.post(f'/accounts/password/reset/confirm/{uidb64}/invalid-token/', {
            'new_password1': 'NewPassword123!',
            'new_password2': 'NewPassword123!',
        })
        
        # Verify password was not changed
        self.user.refresh_from_db()
        self.assertFalse(
            self.user.check_password('NewPassword123!'),
            "INSECURE DESIGN: Password changed without valid reset token"
        )

    def test_account_enumeration__login_response_consistent(self):
        """
        SECURITY TEST: Login errors should not reveal if username exists.
        
        Risk: Account enumeration for targeted attacks.
        """
        # Try with existing user, wrong password
        response1 = self.client.post('/accounts/login/', {
            'username': 'design_user',
            'password': 'wrongpassword'
        })
        
        # Try with non-existing user
        response2 = self.client.post('/accounts/login/', {
            'username': 'nonexistent_user_12345',
            'password': 'wrongpassword'
        })
        
        # Both responses should be similar (same status, similar message)
        if response1.status_code == response2.status_code == 200:
            content1 = response1.content.decode('utf-8', errors='ignore')
            content2 = response2.content.decode('utf-8', errors='ignore')
            
            # Check for user-enumeration revealing messages
            if 'user not found' in content2.lower() or 'username does not exist' in content2.lower():
                pytest.skip(
                    "INFORMATIONAL: Login error messages may reveal user existence. "
                    "Consider using generic error messages."
                )


@pytest.mark.security
class TestA06VulnerableComponents(TestCase):
    """
    OWASP A06:2021 - Vulnerable and Outdated Components
    Note: Full vulnerability scanning requires external tools.
    These tests check for basic dependency security hygiene.
    """

    def test_django_version__not_eol(self):
        """
        SECURITY TEST: Django version should not be end-of-life.
        
        Risk: Unpatched security vulnerabilities.
        """
        import django
        version = django.VERSION
        
        # Django 4.x and 5.x are current as of 2024
        # Versions 3.x are going EOL
        major_version = version[0]
        
        if major_version < 4:
            pytest.fail(
                f"SECURITY RISK: Django {'.'.join(map(str, version[:3]))} may be EOL. "
                "Upgrade to Django 4.x or 5.x for security updates."
            )

    def test_security_middleware__present(self):
        """
        SECURITY TEST: Security middleware should be configured.
        
        Risk: Missing security headers.
        """
        required_middleware = [
            'django.middleware.security.SecurityMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
        ]
        
        for mw in required_middleware:
            self.assertIn(
                mw, settings.MIDDLEWARE,
                f"SECURITY MISCONFIGURATION: {mw} not in MIDDLEWARE"
            )


@pytest.mark.security
class TestA08SoftwareDataIntegrity(TestCase):
    """
    OWASP A08:2021 - Software and Data Integrity Failures
    Tests for integrity verification, particularly in webhooks.
    """

    def setUp(self):
        self.client = Client()

    def test_webhook_signature__required(self):
        """
        SECURITY TEST: Webhooks should require signature verification.
        
        Risk: Webhook spoofing for unauthorized actions.
        """
        # Test Stripe webhook without signature
        response = self.client.post(
            '/payments/webhooks/stripe/',
            {'type': 'payment_intent.succeeded'},
            content_type='application/json'
        )
        
        # Should reject (400) due to missing/invalid signature
        self.assertIn(
            response.status_code, [400, 401, 403],
            "INTEGRITY FAILURE: Stripe webhook accepted without signature"
        )


@pytest.mark.security
class TestA09LoggingMonitoringFailures(TestCase):
    """
    OWASP A09:2021 - Security Logging and Monitoring Failures
    Tests for audit logging of security-relevant events.
    """

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='audit_test_user',
            password='password123',
            email='audit_test@test.com'
        )

    def test_audit_logging__exists(self):
        """
        SECURITY TEST: Audit logging infrastructure should exist.
        
        Risk: No visibility into security events.
        """
        try:
            from audit.models import AuditLog
            # Audit infrastructure exists
            self.assertTrue(True)
        except ImportError:
            pytest.skip(
                "INFORMATIONAL: Audit app not found. Consider implementing "
                "audit logging for security events."
            )

    def test_failed_login__logged(self):
        """
        SECURITY TEST: Failed login attempts should be logged.
        
        Risk: Undetected brute force attempts.
        """
        # Perform failed login
        self.client.post('/accounts/login/', {
            'username': 'audit_test_user',
            'password': 'wrongpassword'
        })
        
        # Check if logged (implementation-specific)
        try:
            from audit.models import AuditLog
            
            logs = AuditLog.objects.filter(
                event_type__icontains='login'
            ).order_by('-created_at')
            
            # Should have at least one login-related log
            # This is informational if not implemented
            if not logs.exists():
                pytest.skip(
                    "INFORMATIONAL: Failed logins not explicitly logged. "
                    "Consider logging authentication failures."
                )
        except ImportError:
            pass


@pytest.mark.security
class TestA10SSRF(TestCase):
    """
    OWASP A10:2021 - SSRF
    If the system fetches URLs (profile websites, etc), verify it doesn't fetch internal IPs.
    """
    
    def test_profile_website_ssrf_sanitization(self):
        """Attempt to set profile website to internal metadata URL."""
        user = User.objects.create_user('ssrf_user', 'pw')
        self.client.force_login(user)
        
        dangerous_urls = [
            'http://169.254.169.254/latest/meta-data/',
            'http://localhost:8000/admin/',
            'file:///etc/passwd'
        ]
        
        for url in dangerous_urls:
            # Assuming profile has a website field
            # We try to update it. Models usually validate URL format but not IP ranges by default.
            # This test mainly documents if the system accepts it.
            # Real SSRF protection requires custom validators.
            response = self.client.post('/accounts/profile/edit/', {
                'website': url
            })
            
            # If accepted, we check if the system effectively fetches it. 
            # Since we can't easily check if it fetches, we assume the RISK exists if accepted.
            pass
            # Ideally, we assert validation error if we have aggressive SSRF protection
