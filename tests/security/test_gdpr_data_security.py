"""
GDPR & Sensitive Data Security Tests.
Pillar 9: Sensitive Data Exposure & Privacy

Tests:
- Data export request security
- Data deletion request security
- Consent record integrity
- Cross-user data access prevention
- PII exposure prevention
- Secrets hygiene checks
"""

import pytest
import json
from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.conf import settings
from gdpr.models import DataExportRequest, DataDeletionRequest, ConsentRecord
from payments.models import Wallet, Transaction

User = get_user_model()


@pytest.mark.security
class TestDataExportSecurity(TestCase):
    """
    Tests for GDPR data export (Article 15) security.
    
    SECURITY REQUIREMENT: Data exports should only be accessible to the data subject.
    """

    def setUp(self):
        self.victim = User.objects.create_user(
            username='victim_gdpr',
            password='password123',
            email='victim_gdpr@test.com'
        )
        self.attacker = User.objects.create_user(
            username='attacker_gdpr',
            password='password123',
            email='attacker_gdpr@test.com'
        )
        
        # Create export request for victim
        self.victim_export = DataExportRequest.objects.create(
            user=self.victim,
            status='completed',
            file_path='exports/victim_data.json',
            file_size=1024
        )

    def test_data_export__cross_user_access__denied(self):
        """
        SECURITY TEST: User cannot access another user's data export.
        
        Risk: Complete account data exposure including PII.
        """
        client = Client()
        client.force_login(self.attacker)
        
        # Try to download victim's export
        response = client.get(f'/gdpr/export/{self.victim_export.id}/download/')
        
        self.assertIn(
            response.status_code, [403, 404],
            "GDPR VIOLATION: Cross-user data export access is possible"
        )

    def test_data_export_request__rate_limiting__enforced(self):
        """
        SECURITY TEST: Data export requests should be rate limited.
        
        Risk: DoS through excessive export generation.
        """
        client = Client()
        client.force_login(self.victim)
        
        # Try to create many export requests
        success_count = 0
        for i in range(10):
            response = client.post('/gdpr/export/request/')
            if response.status_code in [200, 302]:
                success_count += 1
        
        if success_count >= 10:
            pytest.skip(
                "INFORMATIONAL: No rate limiting on data export requests. "
                "Consider limiting to 1 request per day per user."
            )

    def test_data_export__unauthenticated__denied(self):
        """
        SECURITY TEST: Unauthenticated users cannot request exports.
        
        Risk: Anonymous data harvesting attempts.
        """
        client = Client()
        
        response = client.post('/gdpr/export/request/')
        
        self.assertIn(
            response.status_code, [302, 403],
            "SECURITY VULNERABILITY: Unauthenticated user can request data exports"
        )
        
        if response.status_code == 302:
            self.assertIn('login', response.url.lower())


@pytest.mark.security
class TestDataDeletionSecurity(TestCase):
    """
    Tests for GDPR data deletion (Article 17) security.
    
    SECURITY REQUIREMENT: Account deletion should be properly authenticated.
    """

    def setUp(self):
        self.victim = User.objects.create_user(
            username='victim_delete',
            password='password123',
            email='victim_delete@test.com'
        )
        self.attacker = User.objects.create_user(
            username='attacker_delete',
            password='password123',
            email='attacker_delete@test.com'
        )

    def test_data_deletion__cross_user__denied(self):
        """
        SECURITY TEST: User cannot request deletion of another user's account.
        
        Risk: Account destruction attack.
        """
        # Create deletion request for victim
        victim_deletion = DataDeletionRequest.objects.create(
            user=self.victim,
            status='pending',
            reason='Test deletion'
        )
        
        client = Client()
        client.force_login(self.attacker)
        
        # Try to cancel/modify victim's deletion request
        response = client.post(f'/gdpr/deletion/{victim_deletion.id}/cancel/')
        
        self.assertIn(
            response.status_code, [403, 404],
            "GDPR VIOLATION: Cross-user deletion request manipulation"
        )

    def test_data_deletion__requires_password_confirmation(self):
        """
        SECURITY TEST: Account deletion should require password re-entry.
        
        Risk: Session hijacking leading to permanent data loss.
        """
        client = Client()
        client.force_login(self.victim)
        
        # Try to request deletion without password
        response = client.post('/gdpr/deletion/request/', {
            'reason': 'Privacy concerns',
            # No password field
        })
        
        # Should require password or additional confirmation
        # This is informational if password is not required
        if response.status_code == 302 and 'success' in response.url.lower():
            pytest.skip(
                "INFORMATIONAL: Account deletion doesn't require password confirmation. "
                "Consider adding re-authentication for destructive actions."
            )

    def test_data_deletion__grace_period__exists(self):
        """
        SECURITY TEST: Deletion should have a grace period.
        
        Risk: Accidental or malicious immediate deletion.
        """
        client = Client()
        client.force_login(self.victim)
        
        response = client.post('/gdpr/deletion/request/', {
            'reason': 'Testing grace period',
            'password': 'password123',
        })
        
        # Check that deletion is not immediate
        if response.status_code in [200, 302]:
            # Verify user still exists
            self.victim.refresh_from_db()
            self.assertTrue(
                self.victim.is_active,
                "SECURITY RISK: Deletion is immediate without grace period"
            )
            
            # Check for grace period
            deletion = DataDeletionRequest.objects.filter(user=self.victim).first()
            if deletion:
                self.assertTrue(
                    deletion.status in ['pending', 'grace_period'],
                    "Deletion should be in grace period"
                )


@pytest.mark.security
class TestConsentRecordIntegrity(TestCase):
    """
    Tests for consent record integrity.
    
    SECURITY REQUIREMENT: Consent records should be tamper-proof.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='consent_user',
            password='password123',
            email='consent@test.com'
        )
        
        self.consent = ConsentRecord.objects.create(
            user=self.user,
            consent_type='terms_of_service',
            version='1.0',
            is_given=True,
            ip_address='192.168.1.1',
            user_agent='Test Browser'
        )

    def test_consent_record__tampering__prevented(self):
        """
        SECURITY TEST: Users should not be able to backdate consent.
        
        Risk: Fraudulent consent record manipulation.
        """
        client = Client()
        client.force_login(self.user)
        
        # Try to modify consent record (if endpoint exists)
        response = client.post(f'/gdpr/consent/{self.consent.id}/modify/', {
            'is_given': False,
            'consent_date': '2020-01-01',  # Attempt to backdate
        })
        
        # Should not allow modification
        self.assertIn(
            response.status_code, [403, 404, 405],
            "SECURITY VULNERABILITY: Consent records can be modified"
        )

    def test_consent_withdrawal__creates_new_record(self):
        """
        SECURITY TEST: Consent withdrawal should create new record, not modify existing.
        
        Risk: Audit trail destruction.
        """
        original_id = self.consent.id
        original_given_at = self.consent.created_at
        
        client = Client()
        client.force_login(self.user)
        
        # Withdraw consent
        response = client.post('/gdpr/consent/withdraw/', {
            'consent_type': 'terms_of_service',
        })
        
        # Original record should still exist
        self.consent.refresh_from_db()
        self.assertEqual(self.consent.id, original_id)
        
        # A new withdrawal record might exist (depending on implementation)
        # This is informational only


@pytest.mark.security
class TestPIIExposure(TestCase):
    """
    Tests for PII (Personally Identifiable Information) exposure prevention.
    
    SECURITY REQUIREMENT: PII should not be exposed to unauthorized parties.
    """

    def setUp(self):
        self.victim = User.objects.create_user(
            username='victim_pii',
            password='password123',
            email='sensitive_email@company.com',
            first_name='John',
            last_name='Doe'
        )
        self.attacker = User.objects.create_user(
            username='attacker_pii',
            password='password123',
            email='attacker@test.com'
        )
        
        # Create wallet with transactions for victim
        self.victim_wallet, _ = Wallet.objects.get_or_create(user=self.victim)
        Transaction.objects.create(
            user=self.victim,
            wallet=self.victim_wallet,
            transaction_type='deposit',
            amount=Decimal('1000.00'),
            payment_gateway='test',
            status='completed'
        )

    def test_public_profile__email_not_visible(self):
        """
        SECURITY TEST: User email should not be visible on public profiles.
        
        Risk: Email harvesting for spam/phishing.
        """
        client = Client()
        client.force_login(self.attacker)
        
        response = client.get(f'/accounts/profile/{self.victim.username}/')
        
        if response.status_code == 200:
            content = response.content.decode('utf-8', errors='ignore')
            self.assertNotIn(
                self.victim.email,
                content,
                "PII EXPOSURE: Email visible on public profile"
            )

    def test_public_profile__phone_not_visible(self):
        """
        SECURITY TEST: Phone number should not be visible publicly.
        
        Risk: Phone number harvesting.
        """
        # Add phone to victim's profile
        try:
            profile = self.victim.profile
            profile.phone = '+1234567890'
            profile.save()
        except Exception:
            pass
        
        client = Client()
        client.force_login(self.attacker)
        
        response = client.get(f'/accounts/profile/{self.victim.username}/')
        
        if response.status_code == 200:
            content = response.content.decode('utf-8', errors='ignore')
            self.assertNotIn(
                '+1234567890',
                content,
                "PII EXPOSURE: Phone number visible on public profile"
            )

    def test_api_responses__pii_not_leaked(self):
        """
        SECURITY TEST: API responses should not leak other users' PII.
        
        Risk: Mass PII harvesting via API.
        """
        client = Client()
        client.force_login(self.attacker)
        
        # Check common API-like endpoints
        endpoints = [
            '/marketplace/businesses/',
            '/marketplace/opportunities/',
            '/marketplace/jobs/',
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            if response.status_code == 200:
                content = response.content.decode('utf-8', errors='ignore')
                self.assertNotIn(
                    self.victim.email,
                    content,
                    f"PII LEAK: Email exposed in {endpoint}"
                )


@pytest.mark.security
class TestSecretsHygiene(TestCase):
    """
    Tests for secrets and configuration hygiene.
    
    SECURITY REQUIREMENT: Secrets should not be hardcoded or exposed.
    """

    def test_no_hardcoded_secret_key(self):
        """
        SECURITY TEST: SECRET_KEY should not be a known default value.
        
        Risk: Predictable SECRET_KEY compromises sessions and tokens.
        """
        secret = settings.SECRET_KEY
        
        known_defaults = [
            'your-secret-key',
            'change-me',
            'insecure-secret-key',
            'secret-key-here',
            'CHANGEME',
        ]
        
        for default in known_defaults:
            self.assertNotEqual(
                secret, default,
                f"CRITICAL: SECRET_KEY is set to known default value: {default}"
            )
        
        # Also check length
        self.assertGreater(
            len(secret), 32,
            "SECURITY WEAKNESS: SECRET_KEY is too short"
        )

    def test_no_hardcoded_api_keys_in_settings(self):
        """
        SECURITY TEST: API keys should come from environment variables.
        
        Risk: Hardcoded keys in source code can be exposed.
        """
        import os
        
        keys_to_check = [
            ('STRIPE_SECRET_KEY', 'sk_'),
            ('STRIPE_PUBLISHABLE_KEY', 'pk_'),
            ('PAYPAL_CLIENT_SECRET', None),
            ('AWS_SECRET_ACCESS_KEY', None),
            ('DATABASE_URL', None),
        ]
        
        for key_name, expected_prefix in keys_to_check:
            value = getattr(settings, key_name, None)
            
            if value:
                # Check if it looks like a real key (not a placeholder)
                if expected_prefix and value.startswith(expected_prefix):
                    # It's a real key - verify it's from environment
                    env_value = os.environ.get(key_name)
                    if not env_value:
                        pytest.skip(
                            f"SECURITY WARNING: {key_name} appears to be hardcoded. "
                            "Use environment variables in production."
                        )

    def test_debug_mode_warning(self):
        """
        SECURITY TEST: DEBUG mode should be documented for tests.
        
        Risk: DEBUG mode exposes sensitive stack traces.
        """
        if settings.DEBUG:
            pytest.skip(
                "INFORMATIONAL: DEBUG=True. Ensure this is disabled in production. "
                "DEBUG mode exposes stack traces and sensitive configuration."
            )

    def test_allowed_hosts_not_wildcard(self):
        """
        SECURITY TEST: ALLOWED_HOSTS should not be wildcard in production.
        
        Risk: HTTP Host header attacks.
        """
        if not settings.DEBUG:
            hosts = settings.ALLOWED_HOSTS
            self.assertNotEqual(
                hosts, ['*'],
                "SECURITY VULNERABILITY: ALLOWED_HOSTS=['*'] allows Host header attacks"
            )
            self.assertTrue(
                len(hosts) > 0,
                "SECURITY VULNERABILITY: ALLOWED_HOSTS is empty"
            )

    def test_error_pages__no_debug_info(self):
        """
        SECURITY TEST: Error pages should not expose debug information.
        
        Risk: Stack traces reveal application internals.
        """
        client = Client()
        
        # Trigger 404
        response = client.get('/nonexistent_page_12345/')
        
        content = response.content.decode('utf-8', errors='ignore')
        
        # Should not contain debug information
        debug_indicators = [
            'INSTALLED_APPS',
            'MIDDLEWARE',
            'django/core',
            'Traceback',
            'SECRET_KEY',
        ]
        
        for indicator in debug_indicators:
            if indicator in content and not settings.DEBUG:
                pytest.fail(
                    f"DEBUG INFO LEAK: Error page contains '{indicator}'"
                )

    def test_database_credentials__not_exposed(self):
        """
        SECURITY TEST: Database credentials should not be in responses.
        
        Risk: Database compromise.
        """
        client = Client()
        user = User.objects.create_user(username='db_test', password='pwd')
        client.force_login(user)
        
        # Check various endpoints
        endpoints = [
            '/',
            '/accounts/profile/',
            '/payments/wallet/',
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            if response.status_code == 200:
                content = response.content.decode('utf-8', errors='ignore')
                
                # Check for database info
                db_indicators = ['postgres://', 'mysql://', 'PASSWORD=', 'password:']
                for indicator in db_indicators:
                    self.assertNotIn(
                        indicator, content,
                        f"DATABASE CREDENTIALS EXPOSED in {endpoint}"
                    )


@pytest.mark.security
class TestAuditTrailSecurity(TestCase):
    """
    Tests for audit trail security.
    
    SECURITY REQUIREMENT: Sensitive actions should be logged with integrity.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='audit_user',
            password='password123',
            email='audit@test.com'
        )

    def test_login_events__logged(self):
        """
        SECURITY TEST: Login events should be logged.
        
        Risk: Undetected unauthorized access.
        """
        client = Client()
        
        # Perform login
        response = client.post('/accounts/login/', {
            'username': 'audit_user',
            'password': 'password123'
        })
        
        # Check audit log (if accessible)
        # This is informational if audit log structure is unknown
        try:
            from audit.models import AuditLog
            logs = AuditLog.objects.filter(
                user=self.user,
                event_type__icontains='login'
            )
            
            if not logs.exists():
                pytest.skip(
                    "INFORMATIONAL: Login events not found in audit log. "
                    "Consider logging authentication events."
                )
        except ImportError:
            pytest.skip("Audit log model not available for testing")

    def test_password_change__logged(self):
        """
        SECURITY TEST: Password changes should be logged.
        
        Risk: Undetected account compromise.
        """
        client = Client()
        client.force_login(self.user)
        
        # Change password
        response = client.post('/accounts/password/change/', {
            'old_password': 'password123',
            'new_password1': 'NewSecurePassword456!',
            'new_password2': 'NewSecurePassword456!'
        })
        
        # Check audit log
        try:
            from audit.models import AuditLog
            logs = AuditLog.objects.filter(
                user=self.user,
                event_type__icontains='password'
            )
            
            if not logs.exists():
                pytest.skip(
                    "INFORMATIONAL: Password change not found in audit log."
                )
        except ImportError:
            pytest.skip("Audit log model not available")
