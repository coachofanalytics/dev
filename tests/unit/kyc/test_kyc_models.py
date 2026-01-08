"""
Comprehensive unit tests for KYC models.
Tests KYC documents, verification levels, and document processing.
"""
from django.test import TestCase
from django.apps import apps
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import date, timedelta

User = get_user_model()
KYCDocument = apps.get_model('kyc', 'KYCDocument')
KYCVerificationLevel = apps.get_model('kyc', 'KYCVerificationLevel')


class KYCDocumentBasicTests(TestCase):
    """Basic tests for KYCDocument model."""

    def setUp(self):
        self.user = User.objects.create_user(username='kycuser', password='pass')

    def test_kyc_document_creation(self):
        """Test creating a KYC document."""
        doc = KYCDocument.objects.create(
            user=self.user,
            document_type='national_id',
            document_file='kyc_documents/test.pdf'
        )
        self.assertEqual(doc.user, self.user)
        self.assertEqual(doc.document_type, 'national_id')

    def test_kyc_document_str_representation(self):
        """Test KYC document string representation."""
        doc = KYCDocument.objects.create(
            user=self.user,
            document_type='passport',
            document_file='kyc_documents/test.pdf'
        )
        self.assertIn(self.user.username, str(doc))
        self.assertIn('Passport', str(doc))

    def test_default_values(self):
        """Test KYC document default values."""
        doc = KYCDocument.objects.create(
            user=self.user,
            document_type='national_id',
            document_file='kyc_documents/test.pdf'
        )
        self.assertEqual(doc.status, 'pending')
        self.assertFalse(doc.is_scanned)
        self.assertFalse(doc.is_encrypted)


class KYCDocumentStatusTests(TestCase):
    """Tests for KYC document status management."""

    def setUp(self):
        self.user = User.objects.create_user(username='statususer', password='pass')
        self.staff_user = User.objects.create_user(
            username='staff',
            password='pass',
            is_staff=True
        )

    def test_default_status_pending(self):
        """Test default status is pending."""
        doc = KYCDocument.objects.create(
            user=self.user,
            document_type='national_id',
            document_file='kyc_documents/test.pdf'
        )
        self.assertEqual(doc.status, 'pending')

    def test_mark_under_review(self):
        """Test marking document as under review."""
        doc = KYCDocument.objects.create(
            user=self.user,
            document_type='national_id',
            document_file='kyc_documents/test.pdf'
        )
        doc.mark_under_review(self.staff_user)
        doc.refresh_from_db()
        self.assertEqual(doc.status, 'under_review')

    def test_reject_document(self):
        """Test rejecting a document."""
        doc = KYCDocument.objects.create(
            user=self.user,
            document_type='national_id',
            document_file='kyc_documents/test.pdf'
        )
        doc.reject(self.staff_user, 'Document not clear')
        doc.refresh_from_db()
        
        self.assertEqual(doc.status, 'rejected')
        self.assertEqual(doc.verification_notes, 'Document not clear')
        self.assertIsNotNone(doc.verified_at)


class KYCDocumentPropertiesTests(TestCase):
    """Tests for KYC document properties."""

    def setUp(self):
        self.user = User.objects.create_user(username='propsuser', password='pass')

    def test_is_expired_no_expiry_date(self):
        """Test is_expired when no expiry date set."""
        doc = KYCDocument.objects.create(
            user=self.user,
            document_type='national_id',
            document_file='kyc_documents/test.pdf'
        )
        self.assertFalse(doc.is_expired)

    def test_is_expired_future_date(self):
        """Test is_expired with future expiry date."""
        doc = KYCDocument.objects.create(
            user=self.user,
            document_type='passport',
            document_file='kyc_documents/test.pdf',
            expiry_date=date.today() + timedelta(days=365)
        )
        self.assertFalse(doc.is_expired)

    def test_is_expired_past_date(self):
        """Test is_expired with past expiry date."""
        doc = KYCDocument.objects.create(
            user=self.user,
            document_type='passport',
            document_file='kyc_documents/test.pdf',
            expiry_date=date.today() - timedelta(days=1)
        )
        self.assertTrue(doc.is_expired)

    def test_is_verified_approved(self):
        """Test is_verified returns True for approved documents."""
        doc = KYCDocument.objects.create(
            user=self.user,
            document_type='national_id',
            document_file='kyc_documents/test.pdf',
            status='approved'
        )
        self.assertTrue(doc.is_verified)

    def test_is_verified_pending(self):
        """Test is_verified returns False for pending documents."""
        doc = KYCDocument.objects.create(
            user=self.user,
            document_type='national_id',
            document_file='kyc_documents/test.pdf'
        )
        self.assertFalse(doc.is_verified)

    def test_requires_review_pending(self):
        """Test requires_review for pending documents."""
        doc = KYCDocument.objects.create(
            user=self.user,
            document_type='national_id',
            document_file='kyc_documents/test.pdf'
        )
        self.assertTrue(doc.requires_review)

    def test_requires_review_approved(self):
        """Test requires_review for approved documents."""
        doc = KYCDocument.objects.create(
            user=self.user,
            document_type='national_id',
            document_file='kyc_documents/test.pdf',
            status='approved'
        )
        self.assertFalse(doc.requires_review)


class KYCDocumentTypeTests(TestCase):
    """Tests for different document types."""

    def setUp(self):
        self.user = User.objects.create_user(username='typeuser', password='pass')

    def test_national_id_type(self):
        """Test national ID document type."""
        doc = KYCDocument.objects.create(
            user=self.user,
            document_type='national_id',
            document_file='kyc_documents/test.pdf'
        )
        self.assertEqual(doc.document_type, 'national_id')
        self.assertEqual(doc.get_document_type_display(), 'National ID')

    def test_passport_type(self):
        """Test passport document type."""
        doc = KYCDocument.objects.create(
            user=self.user,
            document_type='passport',
            document_file='kyc_documents/test.pdf'
        )
        self.assertEqual(doc.document_type, 'passport')
        self.assertEqual(doc.get_document_type_display(), 'Passport')

    def test_drivers_license_type(self):
        """Test driver's license document type."""
        doc = KYCDocument.objects.create(
            user=self.user,
            document_type='drivers_license',
            document_file='kyc_documents/test.pdf'
        )
        self.assertEqual(doc.document_type, 'drivers_license')

    def test_business_registration_type(self):
        """Test business registration document type."""
        doc = KYCDocument.objects.create(
            user=self.user,
            document_type='business_registration',
            document_file='kyc_documents/test.pdf'
        )
        self.assertEqual(doc.document_type, 'business_registration')

    def test_proof_of_address_type(self):
        """Test proof of address document type."""
        doc = KYCDocument.objects.create(
            user=self.user,
            document_type='proof_of_address',
            document_file='kyc_documents/test.pdf'
        )
        self.assertEqual(doc.document_type, 'proof_of_address')


class KYCVerificationLevelBasicTests(TestCase):
    """Basic tests for KYCVerificationLevel model."""

    def setUp(self):
        self.user = User.objects.create_user(username='leveluser', password='pass')

    def test_verification_level_creation(self):
        """Test creating a verification level."""
        level = KYCVerificationLevel.objects.create(user=self.user)
        self.assertEqual(level.user, self.user)
        self.assertEqual(level.level, 'basic')

    def test_verification_level_str_representation(self):
        """Test verification level string representation."""
        level = KYCVerificationLevel.objects.create(user=self.user)
        self.assertIn(self.user.username, str(level))

    def test_default_values(self):
        """Test verification level default values."""
        level = KYCVerificationLevel.objects.create(user=self.user)
        self.assertFalse(level.email_verified)
        self.assertFalse(level.phone_verified)
        self.assertFalse(level.identity_verified)
        self.assertFalse(level.address_verified)
        self.assertFalse(level.business_verified)
        self.assertFalse(level.can_invest)
        self.assertFalse(level.can_receive_investment)


class KYCVerificationLevelUpdateTests(TestCase):
    """Tests for update_level method."""

    def setUp(self):
        self.user = User.objects.create_user(username='updateuser', password='pass')
        self.level = KYCVerificationLevel.objects.create(user=self.user)

    def test_basic_level(self):
        """Test basic verification level."""
        self.level.update_level()
        self.assertEqual(self.level.level, 'basic')
        self.assertEqual(self.level.transaction_limit_daily, 100)
        self.assertFalse(self.level.can_invest)

    def test_standard_level(self):
        """Test standard verification level."""
        self.level.email_verified = True
        self.level.identity_verified = True
        self.level.update_level()
        
        self.assertEqual(self.level.level, 'standard')
        self.assertEqual(self.level.transaction_limit_daily, 1000)
        self.assertFalse(self.level.can_invest)

    def test_enhanced_level(self):
        """Test enhanced verification level."""
        self.level.email_verified = True
        self.level.phone_verified = True
        self.level.identity_verified = True
        self.level.address_verified = True
        self.level.update_level()
        
        self.assertEqual(self.level.level, 'enhanced')
        self.assertEqual(self.level.transaction_limit_daily, 10000)
        self.assertTrue(self.level.can_invest)
        self.assertTrue(self.level.can_receive_investment)

    def test_premium_level(self):
        """Test premium verification level."""
        self.level.email_verified = True
        self.level.phone_verified = True
        self.level.identity_verified = True
        self.level.address_verified = True
        self.level.business_verified = True
        self.level.update_level()
        
        self.assertEqual(self.level.level, 'premium')
        self.assertEqual(self.level.transaction_limit_daily, 100000)
        self.assertTrue(self.level.can_invest)
        self.assertTrue(self.level.can_receive_investment)


class KYCVerificationLevelConstraintsTests(TestCase):
    """Tests for verification level constraints."""

    def test_one_to_one_constraint(self):
        """Test one verification level per user."""
        from django.db import IntegrityError
        user = User.objects.create_user(username='constraintuser', password='pass')
        KYCVerificationLevel.objects.create(user=user)
        
        with self.assertRaises(IntegrityError):
            KYCVerificationLevel.objects.create(user=user)

