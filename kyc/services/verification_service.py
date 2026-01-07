"""
KYC Verification Service
Handles document verification workflow and level management
"""
from typing import Optional
from django.contrib.auth import get_user_model
from django.utils import timezone
from ..models import KYCDocument, KYCVerificationLevel
from audit.services.audit_service import AuditService

User = get_user_model()


class VerificationService:
    """Service for managing KYC verification workflow."""

    @staticmethod
    def approve_document(
        document: KYCDocument,
        staff_user: User,
        notes: str = ''
    ) -> KYCDocument:
        """
        Approve a KYC document and update user verification level.

        Args:
            document: Document to approve
            staff_user: Staff member approving
            notes: Optional approval notes

        Returns:
            Approved document

        Raises:
            PermissionError: If user is not staff
        """
        if not staff_user.is_staff:
            raise PermissionError('Only staff can approve documents')

        # Approve document
        document.approve(staff_user, notes)

        # Update user verification level
        VerificationService._update_user_verification_level(document.user, document.document_type)

        # Audit log
        AuditService.log_event(
            user=staff_user,
            event_type='kyc_document_approved',
            metadata={
                'document_id': str(document.id),
                'user_id': document.user.id,
                'document_type': document.document_type,
                'notes': notes,
            }
        )

        return document

    @staticmethod
    def reject_document(
        document: KYCDocument,
        staff_user: User,
        reason: str
    ) -> KYCDocument:
        """
        Reject a KYC document.

        Args:
            document: Document to reject
            staff_user: Staff member rejecting
            reason: Rejection reason (required)

        Returns:
            Rejected document

        Raises:
            PermissionError: If user is not staff
            ValueError: If reason not provided
        """
        if not staff_user.is_staff:
            raise PermissionError('Only staff can reject documents')

        if not reason:
            raise ValueError('Rejection reason is required')

        # Reject document
        document.reject(staff_user, reason)

        # Audit log
        AuditService.log_event(
            user=staff_user,
            event_type='kyc_document_rejected',
            metadata={
                'document_id': str(document.id),
                'user_id': document.user.id,
                'document_type': document.document_type,
                'reason': reason,
            }
        )

        return document

    @staticmethod
    def mark_under_review(
        document: KYCDocument,
        staff_user: User
    ) -> KYCDocument:
        """
        Mark document as under review.

        Args:
            document: Document to mark
            staff_user: Staff member reviewing

        Returns:
            Updated document
        """
        if not staff_user.is_staff:
            raise PermissionError('Only staff can mark documents under review')

        document.mark_under_review(staff_user)

        # Audit log
        AuditService.log_event(
            event_type='kyc_document_under_review',
            description=f'KYC document under review: {document.document_type}',
            user=staff_user,
            metadata={
                'document_id': str(document.id),
                'user_id': document.user.id,
                'document_type': document.document_type,
            }
        )

        return document

    @staticmethod
    def _update_user_verification_level(user: User, document_type: str) -> None:
        """
        Update user's verification level based on approved document.

        Args:
            user: User to update
            document_type: Type of document that was approved
        """
        # Get or create verification level
        level, created = KYCVerificationLevel.objects.get_or_create(user=user)

        # Update verification flags based on document type
        if document_type in ['national_id', 'passport', 'drivers_license']:
            level.identity_verified = True
        elif document_type == 'proof_of_address':
            level.address_verified = True
        elif document_type == 'business_registration':
            level.business_verified = True

        # Update level automatically
        level.update_level()

    @staticmethod
    def get_user_verification_level(user: User) -> KYCVerificationLevel:
        """
        Get user's verification level.

        Args:
            user: User to get level for

        Returns:
            KYCVerificationLevel instance
        """
        level, created = KYCVerificationLevel.objects.get_or_create(user=user)
        return level

    @staticmethod
    def can_user_invest(user: User) -> bool:
        """
        Check if user can make investments.

        Args:
            user: User to check

        Returns:
            True if user can invest
        """
        try:
            level = user.kyc_level
            return level.can_invest
        except KYCVerificationLevel.DoesNotExist:
            return False

    @staticmethod
    def can_user_receive_investment(user: User) -> bool:
        """
        Check if user can receive investments.

        Args:
            user: User to check

        Returns:
            True if user can receive investment
        """
        try:
            level = user.kyc_level
            return level.can_receive_investment
        except KYCVerificationLevel.DoesNotExist:
            return False

    @staticmethod
    def get_user_transaction_limit(user: User) -> float:
        """
        Get user's daily transaction limit.

        Args:
            user: User to check

        Returns:
            Daily transaction limit in USD
        """
        try:
            level = user.kyc_level
            return float(level.transaction_limit_daily)
        except KYCVerificationLevel.DoesNotExist:
            return 0.0

    @staticmethod
    def verify_email(user: User) -> None:
        """
        Mark user's email as verified.

        Args:
            user: User with verified email
        """
        level, created = KYCVerificationLevel.objects.get_or_create(user=user)
        level.email_verified = True
        level.update_level()

        AuditService.log_event(
            event_type='email_verified',
            description=f'Email verified: {user.email}',
            user=user,
            metadata={'email': user.email}
        )

    @staticmethod
    def verify_phone(user: User) -> None:
        """
        Mark user's phone as verified.

        Args:
            user: User with verified phone
        """
        level, created = KYCVerificationLevel.objects.get_or_create(user=user)
        level.phone_verified = True
        level.update_level()

        AuditService.log_event(
            event_type='phone_verified',
            description='Phone number verified',
            user=user,
            metadata={'user_id': user.id}
        )
