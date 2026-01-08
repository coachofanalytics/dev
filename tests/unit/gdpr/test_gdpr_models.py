"""
Comprehensive unit tests for GDPR models.
Tests consent records, data export requests, data deletion requests, and privacy policies.
"""
from django.test import TestCase
from django.apps import apps
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta

User = get_user_model()
ConsentRecord = apps.get_model('gdpr', 'ConsentRecord')
DataExportRequest = apps.get_model('gdpr', 'DataExportRequest')
DataDeletionRequest = apps.get_model('gdpr', 'DataDeletionRequest')
PrivacyPolicyVersion = apps.get_model('gdpr', 'PrivacyPolicyVersion')


class ConsentRecordBasicTests(TestCase):
    """Basic tests for ConsentRecord model."""

    def setUp(self):
        self.user = User.objects.create_user(username='consentuser', password='pass')

    def test_consent_record_creation(self):
        """Test creating a consent record."""
        consent = ConsentRecord.objects.create(
            user=self.user,
            consent_type='terms_of_service',
            version='1.0'
        )
        self.assertEqual(consent.user, self.user)
        self.assertEqual(consent.consent_type, 'terms_of_service')
        self.assertFalse(consent.is_given)

    def test_consent_record_str_representation(self):
        """Test consent record string representation."""
        consent = ConsentRecord.objects.create(
            user=self.user,
            consent_type='privacy_policy',
            version='1.0',
            is_given=True
        )
        self.assertIn(self.user.username, str(consent))
        self.assertIn('Given', str(consent))

    def test_default_values(self):
        """Test consent record default values."""
        consent = ConsentRecord.objects.create(
            user=self.user,
            consent_type='marketing',
            version='1.0'
        )
        self.assertFalse(consent.is_given)
        self.assertIsNone(consent.given_at)
        self.assertIsNone(consent.withdrawn_at)


class ConsentRecordGiveConsentTests(TestCase):
    """Tests for give_consent method."""

    def setUp(self):
        self.user = User.objects.create_user(username='giveuser', password='pass')

    def test_give_consent(self):
        """Test giving consent."""
        consent = ConsentRecord.objects.create(
            user=self.user,
            consent_type='marketing',
            version='1.0'
        )
        consent.give_consent(ip_address='192.168.1.1', user_agent='Test Browser')
        consent.refresh_from_db()
        
        self.assertTrue(consent.is_given)
        self.assertIsNotNone(consent.given_at)
        self.assertEqual(consent.ip_address, '192.168.1.1')
        self.assertEqual(consent.user_agent, 'Test Browser')

    def test_give_consent_clears_withdrawn(self):
        """Test giving consent clears withdrawn_at."""
        consent = ConsentRecord.objects.create(
            user=self.user,
            consent_type='marketing',
            version='1.0',
            withdrawn_at=timezone.now()
        )
        consent.give_consent()
        consent.refresh_from_db()
        
        self.assertIsNone(consent.withdrawn_at)


class ConsentRecordWithdrawConsentTests(TestCase):
    """Tests for withdraw_consent method."""

    def setUp(self):
        self.user = User.objects.create_user(username='withdrawuser', password='pass')

    def test_withdraw_consent(self):
        """Test withdrawing consent."""
        consent = ConsentRecord.objects.create(
            user=self.user,
            consent_type='marketing',
            version='1.0',
            is_given=True,
            given_at=timezone.now()
        )
        consent.withdraw_consent()
        consent.refresh_from_db()
        
        self.assertFalse(consent.is_given)
        self.assertIsNotNone(consent.withdrawn_at)


class ConsentRecordTypeTests(TestCase):
    """Tests for different consent types."""

    def setUp(self):
        self.user = User.objects.create_user(username='typeuser', password='pass')

    def test_terms_of_service_consent(self):
        """Test terms of service consent type."""
        consent = ConsentRecord.objects.create(
            user=self.user,
            consent_type='terms_of_service',
            version='1.0'
        )
        self.assertEqual(consent.consent_type, 'terms_of_service')

    def test_privacy_policy_consent(self):
        """Test privacy policy consent type."""
        consent = ConsentRecord.objects.create(
            user=self.user,
            consent_type='privacy_policy',
            version='1.0'
        )
        self.assertEqual(consent.consent_type, 'privacy_policy')

    def test_marketing_consent(self):
        """Test marketing consent type."""
        consent = ConsentRecord.objects.create(
            user=self.user,
            consent_type='marketing',
            version='1.0'
        )
        self.assertEqual(consent.consent_type, 'marketing')

    def test_analytics_consent(self):
        """Test analytics consent type."""
        consent = ConsentRecord.objects.create(
            user=self.user,
            consent_type='analytics',
            version='1.0'
        )
        self.assertEqual(consent.consent_type, 'analytics')


class DataExportRequestBasicTests(TestCase):
    """Basic tests for DataExportRequest model."""

    def setUp(self):
        self.user = User.objects.create_user(username='exportuser', password='pass')

    def test_export_request_creation(self):
        """Test creating an export request."""
        request = DataExportRequest.objects.create(user=self.user)
        self.assertEqual(request.user, self.user)
        self.assertEqual(request.status, 'pending')

    def test_export_request_str_representation(self):
        """Test export request string representation."""
        request = DataExportRequest.objects.create(user=self.user)
        self.assertIn(self.user.username, str(request))

    def test_default_values(self):
        """Test export request default values."""
        request = DataExportRequest.objects.create(user=self.user)
        self.assertEqual(request.status, 'pending')
        self.assertEqual(request.export_format, 'json')
        self.assertEqual(request.download_count, 0)


class DataExportRequestStatusTests(TestCase):
    """Tests for export request status methods."""

    def setUp(self):
        self.user = User.objects.create_user(username='statususer', password='pass')

    def test_mark_processing(self):
        """Test marking request as processing."""
        request = DataExportRequest.objects.create(user=self.user)
        request.mark_processing()
        request.refresh_from_db()
        self.assertEqual(request.status, 'processing')

    def test_mark_completed(self):
        """Test marking request as completed."""
        request = DataExportRequest.objects.create(user=self.user)
        request.mark_completed(file_path='/exports/user_data.json', file_size=1024)
        request.refresh_from_db()
        
        self.assertEqual(request.status, 'completed')
        self.assertEqual(request.file_path, '/exports/user_data.json')
        self.assertEqual(request.file_size, 1024)
        self.assertIsNotNone(request.processed_at)
        self.assertIsNotNone(request.expires_at)

    def test_mark_failed(self):
        """Test marking request as failed."""
        request = DataExportRequest.objects.create(user=self.user)
        request.mark_failed('File generation error')
        request.refresh_from_db()
        
        self.assertEqual(request.status, 'failed')
        self.assertEqual(request.error_message, 'File generation error')


class DataExportRequestDownloadTests(TestCase):
    """Tests for export request download tracking."""

    def setUp(self):
        self.user = User.objects.create_user(username='downloaduser', password='pass')

    def test_record_download(self):
        """Test recording a download."""
        request = DataExportRequest.objects.create(user=self.user)
        request.mark_completed('/exports/test.json', 1024)
        request.record_download()
        request.refresh_from_db()
        
        self.assertEqual(request.download_count, 1)
        self.assertIsNotNone(request.last_downloaded_at)

    def test_multiple_downloads(self):
        """Test multiple downloads increment count."""
        request = DataExportRequest.objects.create(user=self.user)
        request.mark_completed('/exports/test.json', 1024)
        
        for _ in range(3):
            request.record_download()
        
        request.refresh_from_db()
        self.assertEqual(request.download_count, 3)


class DataExportRequestExpiryTests(TestCase):
    """Tests for export request expiry."""

    def setUp(self):
        self.user = User.objects.create_user(username='expiryuser', password='pass')

    def test_is_expired_no_expiry(self):
        """Test is_expired when no expiry date set."""
        request = DataExportRequest.objects.create(user=self.user)
        self.assertFalse(request.is_expired)

    def test_is_expired_future_date(self):
        """Test is_expired with future expiry date."""
        request = DataExportRequest.objects.create(user=self.user)
        request.expires_at = timezone.now() + timedelta(days=30)
        request.save()
        self.assertFalse(request.is_expired)

    def test_is_expired_past_date(self):
        """Test is_expired with past expiry date."""
        request = DataExportRequest.objects.create(user=self.user)
        request.expires_at = timezone.now() - timedelta(days=1)
        request.save()
        self.assertTrue(request.is_expired)


class DataDeletionRequestBasicTests(TestCase):
    """Basic tests for DataDeletionRequest model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='deleteuser',
            email='delete@example.com',
            password='pass'
        )

    def test_deletion_request_creation(self):
        """Test creating a deletion request."""
        request = DataDeletionRequest.objects.create(user=self.user)
        self.assertEqual(request.user, self.user)
        self.assertEqual(request.status, 'pending')

    def test_deletion_request_str_representation(self):
        """Test deletion request string representation."""
        request = DataDeletionRequest.objects.create(user=self.user)
        self.assertIn(self.user.username, str(request))

    def test_user_info_captured(self):
        """Test user info is captured on save."""
        request = DataDeletionRequest.objects.create(user=self.user)
        self.assertEqual(request.username, 'deleteuser')
        self.assertEqual(request.email, 'delete@example.com')


class DataDeletionRequestGracePeriodTests(TestCase):
    """Tests for deletion request grace period."""

    def setUp(self):
        self.user = User.objects.create_user(username='graceuser', password='pass')

    def test_start_grace_period(self):
        """Test starting grace period."""
        request = DataDeletionRequest.objects.create(user=self.user)
        request.start_grace_period()
        request.refresh_from_db()
        
        self.assertEqual(request.status, 'grace_period')
        self.assertIsNotNone(request.grace_period_end)
        self.assertIsNotNone(request.scheduled_deletion_at)

    def test_is_in_grace_period_true(self):
        """Test is_in_grace_period during grace period."""
        request = DataDeletionRequest.objects.create(user=self.user)
        request.start_grace_period()
        request.refresh_from_db()
        
        self.assertTrue(request.is_in_grace_period)

    def test_is_in_grace_period_false(self):
        """Test is_in_grace_period when grace period passed."""
        request = DataDeletionRequest.objects.create(user=self.user)
        request.grace_period_end = timezone.now() - timedelta(days=1)
        request.save()
        
        self.assertFalse(request.is_in_grace_period)

    def test_days_until_deletion(self):
        """Test days_until_deletion calculation."""
        request = DataDeletionRequest.objects.create(user=self.user)
        request.scheduled_deletion_at = timezone.now() + timedelta(days=15)
        request.save()
        
        self.assertGreaterEqual(request.days_until_deletion, 14)


class DataDeletionRequestCancelTests(TestCase):
    """Tests for cancelling deletion requests."""

    def setUp(self):
        self.user = User.objects.create_user(username='canceluser', password='pass')

    def test_cancel_request(self):
        """Test cancelling a deletion request."""
        request = DataDeletionRequest.objects.create(user=self.user)
        request.start_grace_period()
        request.cancel_request()
        request.refresh_from_db()
        
        self.assertEqual(request.status, 'cancelled')
        self.assertIsNotNone(request.cancelled_at)

    def test_cancel_completed_request_fails(self):
        """Test cancelling completed request raises error."""
        request = DataDeletionRequest.objects.create(
            user=self.user,
            status='completed'
        )
        with self.assertRaises(ValidationError):
            request.cancel_request()


class DataDeletionRequestStatusTests(TestCase):
    """Tests for deletion request status methods."""

    def setUp(self):
        self.user = User.objects.create_user(username='statususer', password='pass')

    def test_mark_processing(self):
        """Test marking request as processing."""
        request = DataDeletionRequest.objects.create(user=self.user)
        request.mark_processing()
        request.refresh_from_db()
        self.assertEqual(request.status, 'processing')

    def test_mark_completed(self):
        """Test marking request as completed."""
        request = DataDeletionRequest.objects.create(user=self.user)
        data_removed = {'profile': True, 'documents': 5}
        request.mark_completed(data_removed)
        request.refresh_from_db()
        
        self.assertEqual(request.status, 'completed')
        self.assertEqual(request.data_removed, data_removed)
        self.assertIsNotNone(request.deleted_at)

    def test_mark_failed(self):
        """Test marking request as failed."""
        request = DataDeletionRequest.objects.create(user=self.user)
        request.mark_failed('Database error')
        request.refresh_from_db()
        
        self.assertEqual(request.status, 'failed')
        self.assertEqual(request.error_message, 'Database error')


class PrivacyPolicyVersionBasicTests(TestCase):
    """Basic tests for PrivacyPolicyVersion model."""

    def setUp(self):
        self.user = User.objects.create_user(username='policyuser', password='pass', is_staff=True)

    def test_policy_creation(self):
        """Test creating a privacy policy version."""
        policy = PrivacyPolicyVersion.objects.create(
            version='1.0',
            title='Privacy Policy v1.0',
            content='Full privacy policy content',
            effective_date=timezone.now(),
            created_by=self.user
        )
        self.assertEqual(policy.version, '1.0')
        self.assertEqual(policy.title, 'Privacy Policy v1.0')

    def test_policy_str_representation(self):
        """Test policy string representation."""
        policy = PrivacyPolicyVersion.objects.create(
            version='1.0',
            title='Privacy Policy v1.0',
            content='Content',
            effective_date=timezone.now(),
            created_by=self.user
        )
        self.assertIn('1.0', str(policy))

    def test_default_is_active_false(self):
        """Test default is_active is False."""
        policy = PrivacyPolicyVersion.objects.create(
            version='1.0',
            title='Privacy Policy',
            content='Content',
            effective_date=timezone.now()
        )
        self.assertFalse(policy.is_active)


class PrivacyPolicyVersionActiveTests(TestCase):
    """Tests for active policy version management."""

    def setUp(self):
        self.user = User.objects.create_user(username='activeuser', password='pass', is_staff=True)

    def test_setting_active_deactivates_others(self):
        """Test setting a policy as active deactivates others."""
        policy1 = PrivacyPolicyVersion.objects.create(
            version='1.0',
            title='Policy v1.0',
            content='Content',
            effective_date=timezone.now(),
            is_active=True
        )
        policy2 = PrivacyPolicyVersion.objects.create(
            version='1.1',
            title='Policy v1.1',
            content='Updated content',
            effective_date=timezone.now(),
            is_active=True
        )
        
        policy1.refresh_from_db()
        self.assertFalse(policy1.is_active)
        self.assertTrue(policy2.is_active)

    def test_only_one_active_policy(self):
        """Test only one policy can be active at a time."""
        PrivacyPolicyVersion.objects.create(
            version='1.0',
            title='Policy v1.0',
            content='Content',
            effective_date=timezone.now(),
            is_active=True
        )
        PrivacyPolicyVersion.objects.create(
            version='1.1',
            title='Policy v1.1',
            content='Content',
            effective_date=timezone.now(),
            is_active=True
        )
        
        active_count = PrivacyPolicyVersion.objects.filter(is_active=True).count()
        self.assertEqual(active_count, 1)


class PrivacyPolicyVersionUniqueConstraintTests(TestCase):
    """Tests for policy version unique constraints."""

    def test_unique_version(self):
        """Test version must be unique."""
        from django.db import IntegrityError
        PrivacyPolicyVersion.objects.create(
            version='1.0',
            title='Policy v1.0',
            content='Content',
            effective_date=timezone.now()
        )
        
        with self.assertRaises(IntegrityError):
            PrivacyPolicyVersion.objects.create(
                version='1.0',
                title='Another Policy',
                content='Content',
                effective_date=timezone.now()
            )

