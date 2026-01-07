"""
Unit tests for KYC DocumentService.
"""
import os
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from kyc.models import KYCDocument, KYCVerificationLevel
from kyc.services.document_service import DocumentService


class DocumentServiceTestCase(TestCase):
    """Test cases for DocumentService."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_upload_document_success(self):
        """Test successful document upload."""
        # Create a simple uploaded file
        test_file = SimpleUploadedFile(
            "test_document.pdf",
            b"file_content",
            content_type="application/pdf"
        )

        # Upload document
        document = DocumentService.upload_document(
            user=self.user,
            document_type='national_id',
            document_file=test_file,
            document_number='123456789',
            scan_for_viruses=False  # Skip virus scanning in tests
        )

        # Assertions
        self.assertIsNotNone(document)
        self.assertEqual(document.user, self.user)
        self.assertEqual(document.document_type, 'national_id')
        self.assertEqual(document.document_number, '123456789')
        self.assertEqual(document.status, 'pending')

    def test_validate_file_size_exceeds_limit(self):
        """Test file validation fails when size exceeds limit."""
        # Create a file larger than 10MB
        large_content = b'a' * (11 * 1024 * 1024)  # 11MB
        large_file = SimpleUploadedFile(
            "large_file.pdf",
            large_content,
            content_type="application/pdf"
        )

        with self.assertRaises(ValueError) as context:
            DocumentService.upload_document(
                user=self.user,
                document_type='passport',
                document_file=large_file,
                scan_for_viruses=False
            )

        self.assertIn('file size exceeds', str(context.exception).lower())

    def test_validate_file_invalid_extension(self):
        """Test file validation fails with invalid extension."""
        invalid_file = SimpleUploadedFile(
            "test.exe",
            b"file_content",
            content_type="application/octet-stream"
        )

        with self.assertRaises(ValueError) as context:
            DocumentService.upload_document(
                user=self.user,
                document_type='passport',
                document_file=invalid_file,
                scan_for_viruses=False
            )

        self.assertIn('invalid file type', str(context.exception).lower())

    def test_check_user_verification_status(self):
        """Test checking user's verification status."""
        # Create KYC documents
        test_file = SimpleUploadedFile(
            "id.pdf",
            b"file_content",
            content_type="application/pdf"
        )

        DocumentService.upload_document(
            user=self.user,
            document_type='national_id',
            document_file=test_file,
            scan_for_viruses=False
        )

        # Check status
        status = DocumentService.check_user_verification_status(self.user)

        self.assertIn('total_documents', status)
        self.assertIn('pending_documents', status)
        self.assertIn('approved_documents', status)
        self.assertEqual(status['total_documents'], 1)
        self.assertEqual(status['pending_documents'], 1)

    def test_get_user_documents(self):
        """Test retrieving user's documents."""
        # Create multiple documents
        for doc_type in ['national_id', 'passport']:
            test_file = SimpleUploadedFile(
                f"{doc_type}.pdf",
                b"file_content",
                content_type="application/pdf"
            )

            DocumentService.upload_document(
                user=self.user,
                document_type=doc_type,
                document_file=test_file,
                scan_for_viruses=False
            )

        # Get documents
        documents = DocumentService.get_user_documents(self.user)

        self.assertEqual(documents.count(), 2)

    def test_get_pending_documents(self):
        """Test retrieving pending documents for review."""
        # Create documents with different statuses
        for status in ['pending', 'approved']:
            test_file = SimpleUploadedFile(
                f"{status}.pdf",
                b"file_content",
                content_type="application/pdf"
            )

            doc = DocumentService.upload_document(
                user=self.user,
                document_type='national_id',
                document_file=test_file,
                scan_for_viruses=False
            )

            if status == 'approved':
                doc.status = 'approved'
                doc.save()

        # Get pending documents
        pending = DocumentService.get_pending_documents()

        self.assertEqual(pending.count(), 1)
        self.assertEqual(pending.first().status, 'pending')


class KYCDocumentModelTestCase(TestCase):
    """Test cases for KYCDocument model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        test_file = SimpleUploadedFile(
            "test.pdf",
            b"file_content",
            content_type="application/pdf"
        )

        self.document = KYCDocument.objects.create(
            user=self.user,
            document_type='national_id',
            document_file=test_file
        )

    def test_approve_document(self):
        """Test approving a document."""
        staff_user = User.objects.create_user(
            username='staff',
            is_staff=True,
            password='staffpass'
        )

        self.document.approve(staff_user, 'Document approved')

        self.document.refresh_from_db()
        self.assertEqual(self.document.status, 'approved')
        self.assertEqual(self.document.verified_by, staff_user)
        self.assertIsNotNone(self.document.verified_at)

    def test_reject_document(self):
        """Test rejecting a document."""
        staff_user = User.objects.create_user(
            username='staff',
            is_staff=True,
            password='staffpass'
        )

        self.document.reject(staff_user, 'Invalid document')

        self.document.refresh_from_db()
        self.assertEqual(self.document.status, 'rejected')
        self.assertEqual(self.document.verification_notes, 'Invalid document')

    def test_is_expired(self):
        """Test checking if document is expired."""
        from datetime import date, timedelta

        # Set expiry date in the past
        self.document.expiry_date = date.today() - timedelta(days=1)
        self.assertTrue(self.document.is_expired())

        # Set expiry date in the future
        self.document.expiry_date = date.today() + timedelta(days=1)
        self.assertFalse(self.document.is_expired())
