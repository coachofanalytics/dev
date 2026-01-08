"""
Regression Tests for GDPR Compliance Features

These tests verify that existing GDPR functionality remains intact
after code changes. Tests are designed to FIND and REPORT issues.

Tested Features:
- Consent record management
- Data export requests
- Data deletion requests
- Privacy policy versioning
- Consent withdrawal

Author: Fadhiri
Date: January 2026
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta

import accounts.models as accounts_models
from gdpr.models import (
    ConsentRecord, DataExportRequest, 
    DataDeletionRequest, PrivacyPolicyVersion
)


class ConsentRecordRegressionTests(TestCase):
    """
    Regression tests for consent record model.
    
    These tests verify that:
    - Consent records can be created
    - Consent types are valid
    - Give/withdraw consent functionality works
    """
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            post_save.disconnect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
    
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        try:
            post_save.connect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='consent_user',
            email='consent@test.com',
            password='ConsentPass123!'
        )
    
    def test_consent_record_creation(self):
        """
        REGRESSION TEST: Consent record should be created successfully.
        
        Verifies: Basic consent record creation.
        Reports: Consent record creation failures.
        """
        consent = ConsentRecord.objects.create(
            user=self.user,
            consent_type='privacy_policy',
            version='1.0'
        )
        
        self.assertIsNotNone(consent.pk, "REGRESSION ISSUE: Consent record not created")
        self.assertEqual(consent.consent_type, 'privacy_policy', "REGRESSION ISSUE: Consent type not saved")
    
    def test_consent_record_default_not_given(self):
        """
        REGRESSION TEST: Default consent should be not given (False).
        
        Verifies: Default is_given value.
        Reports: Consent defaulting to given (GDPR violation risk).
        """
        consent = ConsentRecord.objects.create(
            user=self.user,
            consent_type='marketing',
            version='1.0'
        )
        
        self.assertFalse(consent.is_given, "REGRESSION ISSUE: Consent defaulting to True (GDPR VIOLATION RISK)")
    
    def test_consent_give_consent_method(self):
        """
        REGRESSION TEST: give_consent() should mark consent as given.
        
        Verifies: Consent giving functionality.
        Reports: Consent recording failures.
        """
        consent = ConsentRecord.objects.create(
            user=self.user,
            consent_type='privacy_policy',
            version='1.0'
        )
        
        consent.give_consent(ip_address='192.168.1.1', user_agent='TestBrowser/1.0')
        consent.refresh_from_db()
        
        self.assertTrue(consent.is_given, "REGRESSION ISSUE: give_consent() not setting is_given to True")
        self.assertIsNotNone(consent.given_at, "REGRESSION ISSUE: given_at not set")
        self.assertEqual(consent.ip_address, '192.168.1.1', "REGRESSION ISSUE: IP address not recorded")
    
    def test_consent_withdraw_consent_method(self):
        """
        REGRESSION TEST: withdraw_consent() should mark consent as withdrawn.
        
        Verifies: Consent withdrawal functionality.
        Reports: Withdrawal not working.
        """
        consent = ConsentRecord.objects.create(
            user=self.user,
            consent_type='marketing',
            version='1.0',
            is_given=True,
            given_at=timezone.now()
        )
        
        consent.withdraw_consent()
        consent.refresh_from_db()
        
        self.assertFalse(consent.is_given, "REGRESSION ISSUE: withdraw_consent() not setting is_given to False")
        self.assertIsNotNone(consent.withdrawn_at, "REGRESSION ISSUE: withdrawn_at not set")
    
    def test_consent_type_choices_valid(self):
        """
        REGRESSION TEST: All consent types should be valid.
        
        Verifies: CONSENT_TYPE_CHOICES are accepted.
        Reports: Invalid consent type handling.
        """
        valid_types = [
            'terms_of_service', 'privacy_policy', 'marketing',
            'analytics', 'third_party_sharing', 'cookies', 'data_processing'
        ]
        
        for consent_type in valid_types:
            consent = ConsentRecord.objects.create(
                user=self.user,
                consent_type=consent_type,
                version='1.0'
            )
            self.assertEqual(
                consent.consent_type,
                consent_type,
                f"REGRESSION ISSUE: Consent type '{consent_type}' not accepted"
            )


class DataExportRequestRegressionTests(TestCase):
    """
    Regression tests for data export request model.
    
    These tests verify that:
    - Export requests can be created
    - Status transitions work
    - Expiration handling works
    """
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            post_save.disconnect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
    
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        try:
            post_save.connect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='export_user',
            email='export@test.com',
            password='ExportPass123!'
        )
    
    def test_export_request_creation(self):
        """
        REGRESSION TEST: Export request should be created successfully.
        
        Verifies: Basic export request creation.
        Reports: Export request creation failures.
        """
        request = DataExportRequest.objects.create(
            user=self.user,
            export_format='json'
        )
        
        self.assertIsNotNone(request.pk, "REGRESSION ISSUE: Export request not created")
        self.assertEqual(request.export_format, 'json', "REGRESSION ISSUE: Export format not saved")
    
    def test_export_request_default_status_pending(self):
        """
        REGRESSION TEST: Default status should be 'pending'.
        
        Verifies: Default status value.
        Reports: Incorrect default status.
        """
        request = DataExportRequest.objects.create(
            user=self.user,
            export_format='json'
        )
        
        self.assertEqual(request.status, 'pending', "REGRESSION ISSUE: Default status not 'pending'")
    
    def test_export_request_mark_processing(self):
        """
        REGRESSION TEST: mark_processing() should update status.
        
        Verifies: Processing status update.
        Reports: Status update failures.
        """
        request = DataExportRequest.objects.create(
            user=self.user,
            export_format='json'
        )
        
        request.mark_processing()
        request.refresh_from_db()
        
        self.assertEqual(request.status, 'processing', "REGRESSION ISSUE: mark_processing() not working")
    
    def test_export_request_mark_completed(self):
        """
        REGRESSION TEST: mark_completed() should update status and set file info.
        
        Verifies: Completion status and file path.
        Reports: Completion handling failures.
        """
        request = DataExportRequest.objects.create(
            user=self.user,
            export_format='json'
        )
        
        request.mark_completed('/exports/user_data.json', 1024)
        request.refresh_from_db()
        
        self.assertEqual(request.status, 'completed', "REGRESSION ISSUE: Status not 'completed'")
        self.assertEqual(request.file_path, '/exports/user_data.json', "REGRESSION ISSUE: file_path not set")
        self.assertEqual(request.file_size, 1024, "REGRESSION ISSUE: file_size not set")
        self.assertIsNotNone(request.expires_at, "REGRESSION ISSUE: expires_at not set")
    
    def test_export_request_mark_failed(self):
        """
        REGRESSION TEST: mark_failed() should update status and set error message.
        
        Verifies: Failure status and error recording.
        Reports: Failure handling issues.
        """
        request = DataExportRequest.objects.create(
            user=self.user,
            export_format='json'
        )
        
        request.mark_failed('Database connection error')
        request.refresh_from_db()
        
        self.assertEqual(request.status, 'failed', "REGRESSION ISSUE: Status not 'failed'")
        self.assertEqual(request.error_message, 'Database connection error', "REGRESSION ISSUE: error_message not set")
    
    def test_export_request_is_expired_property(self):
        """
        REGRESSION TEST: is_expired should correctly identify expired exports.
        
        Verifies: Expiration detection.
        Reports: Expired exports not detected.
        """
        request = DataExportRequest.objects.create(
            user=self.user,
            export_format='json'
        )
        request.mark_completed('/exports/test.json', 1024)
        
        # Manually set expiry to past
        request.expires_at = timezone.now() - timedelta(days=1)
        request.save()
        
        self.assertTrue(request.is_expired, "REGRESSION ISSUE: Expired export not detected")
    
    def test_export_request_download_count_tracking(self):
        """
        REGRESSION TEST: record_download() should increment download count.
        
        Verifies: Download tracking.
        Reports: Download count not updating.
        """
        request = DataExportRequest.objects.create(
            user=self.user,
            export_format='json'
        )
        
        request.record_download()
        request.refresh_from_db()
        
        self.assertEqual(request.download_count, 1, "REGRESSION ISSUE: Download count not incremented")
        self.assertIsNotNone(request.last_downloaded_at, "REGRESSION ISSUE: last_downloaded_at not set")


class DataDeletionRequestRegressionTests(TestCase):
    """
    Regression tests for data deletion request model.
    
    These tests verify that:
    - Deletion requests can be created
    - Grace period handling works
    - Cancellation functionality works
    """
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            post_save.disconnect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
    
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        try:
            post_save.connect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='deletion_user',
            email='deletion@test.com',
            password='DeletionPass123!'
        )
    
    def test_deletion_request_creation(self):
        """
        REGRESSION TEST: Deletion request should be created successfully.
        
        Verifies: Basic deletion request creation.
        Reports: Deletion request creation failures.
        """
        request = DataDeletionRequest.objects.create(
            user=self.user,
            reason='No longer need the service'
        )
        
        self.assertIsNotNone(request.pk, "REGRESSION ISSUE: Deletion request not created")
        self.assertEqual(request.user, self.user, "REGRESSION ISSUE: User not linked")
    
    def test_deletion_request_default_status_pending(self):
        """
        REGRESSION TEST: Default status should be 'pending'.
        
        Verifies: Default status value.
        Reports: Incorrect default status.
        """
        request = DataDeletionRequest.objects.create(
            user=self.user
        )
        
        self.assertEqual(request.status, 'pending', "REGRESSION ISSUE: Default status not 'pending'")
    
    def test_deletion_request_captures_user_info(self):
        """
        REGRESSION TEST: User info should be captured on save.
        
        Verifies: Username and email are stored.
        Reports: User info not preserved.
        """
        request = DataDeletionRequest.objects.create(
            user=self.user
        )
        
        self.assertEqual(request.username, 'deletion_user', "REGRESSION ISSUE: Username not captured")
        self.assertEqual(request.email, 'deletion@test.com', "REGRESSION ISSUE: Email not captured")
    
    def test_deletion_request_grace_period(self):
        """
        REGRESSION TEST: start_grace_period() should set correct dates.
        
        Verifies: Grace period functionality.
        Reports: Grace period not working.
        """
        request = DataDeletionRequest.objects.create(
            user=self.user
        )
        
        request.start_grace_period()
        request.refresh_from_db()
        
        self.assertEqual(request.status, 'grace_period', "REGRESSION ISSUE: Status not 'grace_period'")
        self.assertIsNotNone(request.grace_period_end, "REGRESSION ISSUE: grace_period_end not set")
        self.assertIsNotNone(request.scheduled_deletion_at, "REGRESSION ISSUE: scheduled_deletion_at not set")
    
    def test_deletion_request_cancellation(self):
        """
        REGRESSION TEST: cancel_request() should cancel the request.
        
        Verifies: Cancellation functionality.
        Reports: Cancellation not working.
        """
        request = DataDeletionRequest.objects.create(
            user=self.user
        )
        request.start_grace_period()
        
        request.cancel_request()
        request.refresh_from_db()
        
        self.assertEqual(request.status, 'cancelled', "REGRESSION ISSUE: Status not 'cancelled'")
        self.assertIsNotNone(request.cancelled_at, "REGRESSION ISSUE: cancelled_at not set")
    
    def test_deletion_request_cannot_cancel_completed(self):
        """
        REGRESSION TEST: Completed requests cannot be cancelled.
        
        Verifies: Cancellation validation.
        Reports: Completed requests can be cancelled (data integrity risk).
        """
        request = DataDeletionRequest.objects.create(
            user=self.user,
            status='completed'
        )
        
        with self.assertRaises(ValidationError, msg="REGRESSION ISSUE: Completed request can be cancelled"):
            request.cancel_request()
    
    def test_deletion_request_days_until_deletion(self):
        """
        REGRESSION TEST: days_until_deletion should calculate correctly.
        
        Verifies: Days calculation property.
        Reports: Incorrect days calculation.
        """
        request = DataDeletionRequest.objects.create(
            user=self.user
        )
        request.start_grace_period()
        
        days = request.days_until_deletion
        self.assertGreater(days, 0, "REGRESSION ISSUE: days_until_deletion not positive")
        self.assertLessEqual(days, 30, "REGRESSION ISSUE: days_until_deletion exceeds 30 days")


class PrivacyPolicyVersionRegressionTests(TestCase):
    """
    Regression tests for privacy policy version model.
    
    These tests verify that:
    - Policy versions can be created
    - Only one active version at a time
    - Version uniqueness is enforced
    """
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            post_save.disconnect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
    
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        try:
            post_save.connect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
    
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='policy_admin',
            email='policy@test.com',
            password='PolicyPass123!'
        )
    
    def test_policy_version_creation(self):
        """
        REGRESSION TEST: Policy version should be created successfully.
        
        Verifies: Basic policy creation.
        Reports: Policy creation failures.
        """
        policy = PrivacyPolicyVersion.objects.create(
            version='1.0',
            title='Privacy Policy',
            content='Full policy content here...',
            effective_date=timezone.now(),
            created_by=self.admin_user
        )
        
        self.assertIsNotNone(policy.pk, "REGRESSION ISSUE: Policy version not created")
        self.assertEqual(policy.version, '1.0', "REGRESSION ISSUE: Version not saved")
    
    def test_policy_version_unique(self):
        """
        REGRESSION TEST: Version numbers should be unique.
        
        Verifies: Unique constraint on version field.
        Reports: Duplicate versions allowed.
        """
        from django.db import IntegrityError
        
        PrivacyPolicyVersion.objects.create(
            version='1.0',
            title='Privacy Policy v1',
            content='Content',
            effective_date=timezone.now(),
            created_by=self.admin_user
        )
        
        with self.assertRaises(IntegrityError, msg="REGRESSION ISSUE: Duplicate policy versions allowed"):
            PrivacyPolicyVersion.objects.create(
                version='1.0',
                title='Privacy Policy v1 duplicate',
                content='Content',
                effective_date=timezone.now(),
                created_by=self.admin_user
            )
    
    def test_policy_version_default_not_active(self):
        """
        REGRESSION TEST: New policies should not be active by default.
        
        Verifies: Default is_active value.
        Reports: Policies active by default (could cause issues).
        """
        policy = PrivacyPolicyVersion.objects.create(
            version='2.0',
            title='Privacy Policy v2',
            content='Content',
            effective_date=timezone.now(),
            created_by=self.admin_user
        )
        
        self.assertFalse(policy.is_active, "REGRESSION ISSUE: Policy active by default")
    
    def test_policy_version_only_one_active(self):
        """
        REGRESSION TEST: Only one policy version should be active at a time.
        
        Verifies: Active version exclusivity.
        Reports: Multiple active versions allowed.
        """
        policy1 = PrivacyPolicyVersion.objects.create(
            version='1.0',
            title='Privacy Policy v1',
            content='Content v1',
            effective_date=timezone.now(),
            created_by=self.admin_user,
            is_active=True
        )
        
        policy2 = PrivacyPolicyVersion.objects.create(
            version='2.0',
            title='Privacy Policy v2',
            content='Content v2',
            effective_date=timezone.now(),
            created_by=self.admin_user,
            is_active=True
        )
        
        policy1.refresh_from_db()
        
        # Policy1 should now be inactive
        self.assertFalse(policy1.is_active, "REGRESSION ISSUE: Multiple active policy versions allowed")
        self.assertTrue(policy2.is_active, "REGRESSION ISSUE: New active policy not marked active")

