"""
KYC Document Service
Handles document upload, validation, and management
"""
from typing import Optional, List
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import UploadedFile
from django.db.models import QuerySet
from ..models import KYCDocument
from .file_scanner_service import FileScannerService
from audit.services.audit_service import AuditService

User = get_user_model()


class DocumentService:
    """Service for managing KYC documents."""

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = ['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx']

    @staticmethod
    def upload_document(
        user: User,
        document_type: str,
        document_file: UploadedFile,
        document_number: str = '',
        issue_date: Optional[str] = None,
        expiry_date: Optional[str] = None,
        issuing_authority: str = '',
        scan_for_viruses: bool = True
    ) -> KYCDocument:
        """
        Upload and create a new KYC document.

        Args:
            user: User uploading the document
            document_type: Type of document
            document_file: Uploaded file
            document_number: Document ID/reference number
            issue_date: Document issue date
            expiry_date: Document expiry date
            issuing_authority: Issuing authority name
            scan_for_viruses: Whether to scan file for viruses

        Returns:
            Created KYCDocument instance

        Raises:
            ValueError: If file validation fails
        """
        # Validate file
        DocumentService._validate_file(document_file)

        # Create document
        document = KYCDocument.objects.create(
            user=user,
            document_type=document_type,
            document_file=document_file,
            document_number=document_number,
            issue_date=issue_date,
            expiry_date=expiry_date,
            issuing_authority=issuing_authority,
        )

        # Scan for viruses if enabled
        if scan_for_viruses:
            scanner = FileScannerService()
            is_clean, scan_result = scanner.scan_file(document.document_file.path)
            document.is_scanned = True
            document.scan_result = scan_result

            if not is_clean:
                document.status = 'rejected'
                document.verification_notes = f'File failed virus scan: {scan_result}'

            document.save()

        # Audit log
        AuditService.log_event(
            event_type='kyc_document_upload',
            description=f'KYC document uploaded: {document_type}',
            user=user,
            metadata={
                'document_id': str(document.id),
                'document_type': document_type,
                'scan_result': document.scan_result,
            }
        )

        return document

    @staticmethod
    def _validate_file(file: UploadedFile) -> None:
        """
        Validate uploaded file.

        Args:
            file: Uploaded file to validate

        Raises:
            ValueError: If validation fails
        """
        # Check file size
        if file.size > DocumentService.MAX_FILE_SIZE:
            raise ValueError(
                f'File size exceeds maximum allowed size of '
                f'{DocumentService.MAX_FILE_SIZE / (1024*1024)}MB'
            )

        # Check file extension
        ext = file.name.split('.')[-1].lower()
        if ext not in DocumentService.ALLOWED_EXTENSIONS:
            raise ValueError(
                f'File type .{ext} is not allowed. '
                f'Allowed types: {", ".join(DocumentService.ALLOWED_EXTENSIONS)}'
            )

    @staticmethod
    def get_user_documents(
        user: User,
        status: Optional[str] = None,
        document_type: Optional[str] = None
    ) -> QuerySet:
        """
        Get documents for a user with optional filtering.

        Args:
            user: User to get documents for
            status: Optional status filter
            document_type: Optional document type filter

        Returns:
            QuerySet of KYCDocument
        """
        queryset = KYCDocument.objects.filter(user=user)

        if status:
            queryset = queryset.filter(status=status)

        if document_type:
            queryset = queryset.filter(document_type=document_type)

        return queryset.order_by('-uploaded_at')

    @staticmethod
    def get_pending_documents() -> QuerySet:
        """Get all documents pending review."""
        return KYCDocument.objects.filter(
            status__in=['pending', 'under_review']
        ).select_related('user').order_by('uploaded_at')

    @staticmethod
    def delete_document(document: KYCDocument, user: User) -> None:
        """
        Delete a KYC document.

        Args:
            document: Document to delete
            user: User requesting deletion

        Raises:
            PermissionError: If user doesn't have permission
        """
        # Check permissions
        if document.user != user and not user.is_staff:
            raise PermissionError('You do not have permission to delete this document')

        # Audit log
        AuditService.log_event(
            event_type='kyc_document_delete',
            description=f'KYC document deleted: {document.document_type}',
            user=user,
            metadata={
                'document_id': str(document.id),
                'document_type': document.document_type,
                'status': document.status,
            }
        )

        # Delete file and document
        if document.document_file:
            document.document_file.delete()

        document.delete()

    @staticmethod
    def check_user_verification_status(user: User) -> dict:
        """
        Check user's KYC verification status.

        Args:
            user: User to check

        Returns:
            Dictionary with verification status information
        """
        documents = KYCDocument.objects.filter(user=user)

        status = {
            'total_documents': documents.count(),
            'approved_documents': documents.filter(status='approved').count(),
            'pending_documents': documents.filter(status='pending').count(),
            'rejected_documents': documents.filter(status='rejected').count(),
            'has_identity_document': documents.filter(
                document_type__in=['national_id', 'passport', 'drivers_license'],
                status='approved'
            ).exists(),
            'has_address_proof': documents.filter(
                document_type='proof_of_address',
                status='approved'
            ).exists(),
            'has_business_registration': documents.filter(
                document_type='business_registration',
                status='approved'
            ).exists(),
            'is_fully_verified': False,
        }

        # User is fully verified if they have approved identity and address documents
        status['is_fully_verified'] = (
            status['has_identity_document'] and
            status['has_address_proof']
        )

        return status
