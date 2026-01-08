"""
Regression Tests for KYC Verification Features

These tests verify that existing KYC functionality remains intact
after code changes. Tests are designed to FIND and REPORT issues.

Tested Features:
- KYC document upload and management
- Document status transitions
- Verification level tracking
- KYC limits and permissions

Author: Fadhiri
Date: January 2026
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date, timedelta

import accounts.models as accounts_models
from kyc.models import KYCDocument, KYCVerificationLevel


class KYCDocumentCreationRegressionTests(TestCase):
    """
    Regression tests for KYC document model creation.
    
    These tests verify that:
    - KYC documents can be created
    - Document types are valid
    - Default values are correct
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
            username='kyc_user',
            email='kyc@test.com',
            password='KYCPass123!'
        )
        self.staff_user = User.objects.create_user(
            username='kyc_staff',
            email='kyc_staff@test.com',
            password='StaffPass123!',
            is_staff=True
        )
    
    def test_kyc_document_creation(self):
        """
        REGRESSION TEST: KYC document should be created successfully.
        
        Verifies: Basic document creation.
        Reports: Document creation failures.
        """
        doc = KYCDocument.objects.create(
            user=self.user,
            document_type='national_id',
            document_file='kyc_documents/test_id.pdf'
        )
        
        self.assertIsNotNone(doc.pk, "REGRESSION ISSUE: KYC document not created")
        self.assertEqual(doc.document_type, 'national_id', "REGRESSION ISSUE: Document type not saved")
    
    def test_kyc_document_default_status_pending(self):
        """
        REGRESSION TEST: Default document status should be 'pending'.
        
        Verifies: Default status value.
        Reports: Incorrect default status.
        """
        doc = KYCDocument.objects.create(
            user=self.user,
            document_type='passport',
            document_file='kyc_documents/test_passport.pdf'
        )
        
        self.assertEqual(doc.status, 'pending', "REGRESSION ISSUE: Default status not 'pending'")
    
    def test_kyc_document_type_choices_valid(self):
        """
        REGRESSION TEST: All document type choices should be valid.
        
        Verifies: DOCUMENT_TYPE_CHOICES are accepted.
        Reports: Invalid document type handling.
        """
        valid_types = [
            'national_id', 'passport', 'drivers_license',
            'business_registration', 'tax_certificate',
            'proof_of_address', 'bank_statement', 'other'
        ]
        
        for i, doc_type in enumerate(valid_types):
            doc = KYCDocument.objects.create(
                user=self.user,
                document_type=doc_type,
                document_file=f'kyc_documents/test_{i}.pdf'
            )
            self.assertEqual(
                doc.document_type,
                doc_type,
                f"REGRESSION ISSUE: Document type '{doc_type}' not accepted"
            )
    
    def test_kyc_document_uuid_primary_key(self):
        """
        REGRESSION TEST: Document should use UUID as primary key.
        
        Verifies: UUID field for document ID.
        Reports: Non-UUID primary key (security concern).
        """
        doc = KYCDocument.objects.create(
            user=self.user,
            document_type='national_id',
            document_file='kyc_documents/test.pdf'
        )
        
        # Check if pk is a UUID
        import uuid
        self.assertIsInstance(doc.pk, uuid.UUID, "REGRESSION ISSUE: Document ID not using UUID")


class KYCDocumentStatusRegressionTests(TestCase):
    """
    Regression tests for KYC document status transitions.
    
    These tests verify that:
    - approve() method works correctly
    - reject() method works correctly
    - Status transitions are valid
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
            username='status_user',
            email='status@test.com',
            password='StatusPass123!'
        )
        self.staff_user = User.objects.create_user(
            username='status_staff',
            email='status_staff@test.com',
            password='StaffPass123!',
            is_staff=True
        )
        self.doc = KYCDocument.objects.create(
            user=self.user,
            document_type='national_id',
            document_file='kyc_documents/test.pdf'
        )
    
    def test_kyc_document_approve(self):
        """
        REGRESSION TEST: approve() should update document status.
        
        Verifies: Approval functionality.
        Reports: Approval not working.
        """
        self.doc.approve(self.staff_user, 'Document verified successfully')
        self.doc.refresh_from_db()
        
        self.assertEqual(self.doc.status, 'approved', "REGRESSION ISSUE: Status not 'approved'")
        self.assertEqual(self.doc.verified_by, self.staff_user, "REGRESSION ISSUE: verified_by not set")
        self.assertIsNotNone(self.doc.verified_at, "REGRESSION ISSUE: verified_at not set")
        self.assertEqual(self.doc.verification_notes, 'Document verified successfully', "REGRESSION ISSUE: Notes not set")
    
    def test_kyc_document_reject(self):
        """
        REGRESSION TEST: reject() should update document status.
        
        Verifies: Rejection functionality.
        Reports: Rejection not working.
        """
        self.doc.reject(self.staff_user, 'Document is blurry')
        self.doc.refresh_from_db()
        
        self.assertEqual(self.doc.status, 'rejected', "REGRESSION ISSUE: Status not 'rejected'")
        self.assertEqual(self.doc.verified_by, self.staff_user, "REGRESSION ISSUE: verified_by not set")
        self.assertEqual(self.doc.verification_notes, 'Document is blurry', "REGRESSION ISSUE: Rejection notes not set")
    
    def test_kyc_document_mark_under_review(self):
        """
        REGRESSION TEST: mark_under_review() should update status.
        
        Verifies: Under review status.
        Reports: Under review not working.
        """
        self.doc.mark_under_review(self.staff_user)
        self.doc.refresh_from_db()
        
        self.assertEqual(self.doc.status, 'under_review', "REGRESSION ISSUE: Status not 'under_review'")
    
    def test_kyc_document_status_choices_valid(self):
        """
        REGRESSION TEST: All status choices should be valid.
        
        Verifies: STATUS_CHOICES are accepted.
        Reports: Invalid status handling.
        """
        valid_statuses = ['pending', 'under_review', 'approved', 'rejected', 'expired']
        
        for status in valid_statuses:
            self.doc.status = status
            self.doc.save()
            self.doc.refresh_from_db()
            self.assertEqual(
                self.doc.status,
                status,
                f"REGRESSION ISSUE: Status '{status}' not accepted"
            )


class KYCDocumentPropertiesRegressionTests(TestCase):
    """
    Regression tests for KYC document properties.
    
    These tests verify that:
    - is_expired property works
    - is_verified property works
    - requires_review property works
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
            username='props_user',
            email='props@test.com',
            password='PropsPass123!'
        )
    
    def test_kyc_document_is_expired_for_past_expiry(self):
        """
        REGRESSION TEST: is_expired should return True for expired documents.
        
        Verifies: Expiration detection.
        Reports: Expired documents not detected.
        """
        doc = KYCDocument.objects.create(
            user=self.user,
            document_type='passport',
            document_file='kyc_documents/test.pdf',
            expiry_date=date.today() - timedelta(days=1)
        )
        
        self.assertTrue(doc.is_expired, "REGRESSION ISSUE: Expired document not detected")
    
    def test_kyc_document_not_expired_for_future_expiry(self):
        """
        REGRESSION TEST: is_expired should return False for valid documents.
        
        Verifies: Valid documents not marked expired.
        Reports: Valid documents incorrectly marked expired.
        """
        doc = KYCDocument.objects.create(
            user=self.user,
            document_type='passport',
            document_file='kyc_documents/test.pdf',
            expiry_date=date.today() + timedelta(days=365)
        )
        
        self.assertFalse(doc.is_expired, "REGRESSION ISSUE: Valid document marked as expired")
    
    def test_kyc_document_is_verified_for_approved(self):
        """
        REGRESSION TEST: is_verified should return True for approved documents.
        
        Verifies: Verification status property.
        Reports: Approved documents not marked verified.
        """
        doc = KYCDocument.objects.create(
            user=self.user,
            document_type='national_id',
            document_file='kyc_documents/test.pdf',
            status='approved'
        )
        
        self.assertTrue(doc.is_verified, "REGRESSION ISSUE: Approved document not marked verified")
    
    def test_kyc_document_not_verified_for_pending(self):
        """
        REGRESSION TEST: is_verified should return False for pending documents.
        
        Verifies: Pending documents not verified.
        Reports: Pending documents incorrectly marked verified.
        """
        doc = KYCDocument.objects.create(
            user=self.user,
            document_type='national_id',
            document_file='kyc_documents/test.pdf',
            status='pending'
        )
        
        self.assertFalse(doc.is_verified, "REGRESSION ISSUE: Pending document marked as verified")
    
    def test_kyc_document_requires_review_for_pending(self):
        """
        REGRESSION TEST: requires_review should return True for pending documents.
        
        Verifies: Review required property.
        Reports: Documents not flagged for review.
        """
        doc = KYCDocument.objects.create(
            user=self.user,
            document_type='national_id',
            document_file='kyc_documents/test.pdf',
            status='pending'
        )
        
        self.assertTrue(doc.requires_review, "REGRESSION ISSUE: Pending document not requiring review")


class KYCVerificationLevelRegressionTests(TestCase):
    """
    Regression tests for KYC verification level model.
    
    These tests verify that:
    - Verification levels can be created
    - Level updates work correctly
    - Limits and permissions are set correctly
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
            username='level_user',
            email='level@test.com',
            password='LevelPass123!'
        )
    
    def test_verification_level_creation(self):
        """
        REGRESSION TEST: Verification level should be created successfully.
        
        Verifies: Basic level creation.
        Reports: Level creation failures.
        """
        level = KYCVerificationLevel.objects.create(user=self.user)
        
        self.assertIsNotNone(level.pk, "REGRESSION ISSUE: Verification level not created")
        self.assertEqual(level.user, self.user, "REGRESSION ISSUE: User not linked")
    
    def test_verification_level_default_basic(self):
        """
        REGRESSION TEST: Default level should be 'basic'.
        
        Verifies: Default level value.
        Reports: Incorrect default level.
        """
        level = KYCVerificationLevel.objects.create(user=self.user)
        
        self.assertEqual(level.level, 'basic', "REGRESSION ISSUE: Default level not 'basic'")
    
    def test_verification_level_default_flags(self):
        """
        REGRESSION TEST: Default verification flags should be False.
        
        Verifies: Default flag values.
        Reports: Flags defaulting to True (security risk).
        """
        level = KYCVerificationLevel.objects.create(user=self.user)
        
        self.assertFalse(level.email_verified, "REGRESSION ISSUE: email_verified defaulting to True")
        self.assertFalse(level.phone_verified, "REGRESSION ISSUE: phone_verified defaulting to True")
        self.assertFalse(level.identity_verified, "REGRESSION ISSUE: identity_verified defaulting to True")
        self.assertFalse(level.address_verified, "REGRESSION ISSUE: address_verified defaulting to True")
        self.assertFalse(level.business_verified, "REGRESSION ISSUE: business_verified defaulting to True")
    
    def test_verification_level_default_permissions(self):
        """
        REGRESSION TEST: Default permissions should be False.
        
        Verifies: Default permission values.
        Reports: Permissions defaulting to True (security risk).
        """
        level = KYCVerificationLevel.objects.create(user=self.user)
        
        self.assertFalse(level.can_invest, "REGRESSION ISSUE: can_invest defaulting to True (SECURITY RISK)")
        self.assertFalse(level.can_receive_investment, "REGRESSION ISSUE: can_receive_investment defaulting to True")
    
    def test_verification_level_update_to_standard(self):
        """
        REGRESSION TEST: update_level() should set standard for email+identity.
        
        Verifies: Level upgrade to standard.
        Reports: Level calculation errors.
        """
        level = KYCVerificationLevel.objects.create(user=self.user)
        level.email_verified = True
        level.identity_verified = True
        level.update_level()
        level.refresh_from_db()
        
        self.assertEqual(level.level, 'standard', "REGRESSION ISSUE: Level not upgraded to 'standard'")
        self.assertEqual(level.transaction_limit_daily, Decimal('1000'), "REGRESSION ISSUE: Standard limit not set")
    
    def test_verification_level_update_to_enhanced(self):
        """
        REGRESSION TEST: update_level() should set enhanced for full non-business verification.
        
        Verifies: Level upgrade to enhanced.
        Reports: Level calculation errors.
        """
        level = KYCVerificationLevel.objects.create(user=self.user)
        level.email_verified = True
        level.phone_verified = True
        level.identity_verified = True
        level.address_verified = True
        level.update_level()
        level.refresh_from_db()
        
        self.assertEqual(level.level, 'enhanced', "REGRESSION ISSUE: Level not upgraded to 'enhanced'")
        self.assertEqual(level.transaction_limit_daily, Decimal('10000'), "REGRESSION ISSUE: Enhanced limit not set")
        self.assertTrue(level.can_invest, "REGRESSION ISSUE: can_invest not enabled for enhanced")
    
    def test_verification_level_update_to_premium(self):
        """
        REGRESSION TEST: update_level() should set premium for full verification.
        
        Verifies: Level upgrade to premium.
        Reports: Level calculation errors.
        """
        level = KYCVerificationLevel.objects.create(user=self.user)
        level.email_verified = True
        level.phone_verified = True
        level.identity_verified = True
        level.address_verified = True
        level.business_verified = True
        level.update_level()
        level.refresh_from_db()
        
        self.assertEqual(level.level, 'premium', "REGRESSION ISSUE: Level not upgraded to 'premium'")
        self.assertEqual(level.transaction_limit_daily, Decimal('100000'), "REGRESSION ISSUE: Premium limit not set")
        self.assertTrue(level.can_invest, "REGRESSION ISSUE: can_invest not enabled for premium")
        self.assertTrue(level.can_receive_investment, "REGRESSION ISSUE: can_receive_investment not enabled for premium")
    
    def test_verification_level_one_per_user(self):
        """
        REGRESSION TEST: Each user should have only one verification level.
        
        Verifies: User as primary key constraint.
        Reports: Multiple levels per user allowed.
        """
        from django.db import IntegrityError
        
        KYCVerificationLevel.objects.create(user=self.user)
        
        with self.assertRaises(IntegrityError, msg="REGRESSION ISSUE: Multiple verification levels per user allowed"):
            KYCVerificationLevel.objects.create(user=self.user)

