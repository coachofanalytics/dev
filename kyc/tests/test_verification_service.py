"""
Unit tests for KYC VerificationService.
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from kyc.models import KYCDocument, KYCVerificationLevel
from kyc.services.verification_service import VerificationService
from kyc.services.document_service import DocumentService


class VerificationServiceTestCase(TestCase):
    """Test cases for VerificationService."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.staff_user = User.objects.create_user(
            username='staff',
            is_staff=True,
            password='staffpass'
        )

        # Create a test document
        test_file = SimpleUploadedFile(
            "test_id.pdf",
            b"file_content",
            content_type="application/pdf"
        )

        self.document = DocumentService.upload_document(
            user=self.user,
            document_type='national_id',
            document_file=test_file,
            scan_for_viruses=False
        )

    def test_approve_document(self):
        """Test approving a KYC document."""
        result = VerificationService.approve_document(
            self.document,
            self.staff_user,
            'Document verified successfully'
        )

        # Check document status
        result.refresh_from_db()
        self.assertEqual(result.status, 'approved')
        self.assertEqual(result.verified_by, self.staff_user)

    def test_reject_document(self):
        """Test rejecting a KYC document."""
        result = VerificationService.reject_document(
            self.document,
            self.staff_user,
            'Document is not clear'
        )

        result.refresh_from_db()
        self.assertEqual(result.status, 'rejected')