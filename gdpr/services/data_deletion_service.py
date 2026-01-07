"""
Data Deletion Service for GDPR Article 17 compliance.

Implements the "Right to be Forgotten" with:
- 30-day grace period
- Complete data removal
- Anonymization of required records
- Audit trail of deletion
"""

import logging
from typing import Dict, Any, Optional
from datetime import timedelta

from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError

from gdpr.models import DataDeletionRequest

logger = logging.getLogger(__name__)


class DataDeletionService:
    """
    Service for handling user data deletion (Right to be Forgotten).

    GDPR Article 17: Right to erasure ('right to be forgotten')
    Implements 30-day grace period and comprehensive data removal.
    """

    GRACE_PERIOD_DAYS = 30

    @staticmethod
    def create_deletion_request(
        user: User,
        reason: str = ""
    ) -> DataDeletionRequest:
        """
        Create a new data deletion request with grace period.

        Args:
            user: User requesting deletion
            reason: Optional reason for deletion

        Returns:
            DataDeletionRequest: Created request

        Raises:
            ValidationError: If user already has pending deletion
        """
        # Check for existing pending requests
        existing = DataDeletionRequest.objects.filter(
            user=user,
            status__in=["pending", "grace_period", "processing"]
        ).first()

        if existing:
            raise ValidationError(
                f"You already have a pending deletion request. "
                f"Status: {existing.get_status_display()}"
            )

        # Create new request
        request = DataDeletionRequest.objects.create(
            user=user,
            username=user.username,
            email=user.email,
            reason=reason,
            status="pending",
        )

        # Start grace period
        request.start_grace_period()

        logger.info(
            f"Created deletion request {request.id} for user {user.username}. "
            f"Grace period ends: {request.grace_period_end}"
        )

        return request

    @classmethod
    def cancel_deletion_request(cls, user: User) -> bool:
        """
        Cancel a pending deletion request.

        Args:
            user: User cancelling deletion

        Returns:
            True if cancelled successfully

        Raises:
            ValidationError: If no cancellable request exists
        """
        request = DataDeletionRequest.objects.filter(
            user=user,
            status__in=["pending", "grace_period"]
        ).first()

        if not request:
            raise ValidationError("No pending deletion request found")

        request.cancel_request()

        logger.info(f"Cancelled deletion request {request.id} for user {user.username}")
        return True

    @classmethod
    @transaction.atomic
    def process_deletion_request(cls, request_id: str) -> bool:
        """
        Process a deletion request after grace period.

        Args:
            request_id: UUID of deletion request

        Returns:
            True if successful, False otherwise
        """
        try:
            request = DataDeletionRequest.objects.select_for_update().get(id=request_id)

            # Verify grace period has ended
            if request.is_in_grace_period:
                logger.warning(
                    f"Cannot process deletion {request_id}: still in grace period"
                )
                return False

            # Verify status is correct
            if request.status not in ["grace_period", "pending"]:
                logger.warning(
                    f"Cannot process deletion {request_id}: status is {request.status}"
                )
                return False

            request.mark_processing()

            user = request.user
            if not user:
                logger.error(f"User not found for deletion request {request_id}")
                request.mark_failed("User not found")
                return False

            # Perform deletion
            data_removed = cls._delete_user_data(user)

            # Mark as completed
            request.mark_completed(data_removed)

            logger.info(
                f"Successfully processed deletion request {request_id} "
                f"for user {request.username}"
            )
            return True

        except DataDeletionRequest.DoesNotExist:
            logger.error(f"Deletion request {request_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error processing deletion request {request_id}: {e}")
            try:
                request.mark_failed(str(e))
            except:
                pass
            return False

    @classmethod
    def _delete_user_data(cls, user: User) -> Dict[str, Any]:
        """
        Delete all user data across the system.

        Args:
            user: User to delete data for

        Returns:
            Dictionary of what was deleted
        """
        data_removed = {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "deleted_at": timezone.now().isoformat(),
            "items_deleted": {},
            "items_anonymized": {},
        }

        # Delete profile
        profile_count = cls._delete_profile(user)
        data_removed["items_deleted"]["profile"] = profile_count

        # Delete MFA devices and backup codes
        mfa_count = cls._delete_mfa_data(user)
        data_removed["items_deleted"]["mfa"] = mfa_count

        # Delete marketplace data
        marketplace_counts = cls._delete_marketplace_data(user)
        data_removed["items_deleted"]["marketplace"] = marketplace_counts

        # Delete payment data (anonymize transactions)
        payment_counts = cls._delete_payment_data(user)
        data_removed["items_deleted"]["payments"] = payment_counts["deleted"]
        data_removed["items_anonymized"]["payments"] = payment_counts["anonymized"]

        # Anonymize audit logs (required for compliance)
        audit_count = cls._anonymize_audit_logs(user)
        data_removed["items_anonymized"]["audit_logs"] = audit_count

        # Delete GDPR records (except deletion request itself)
        gdpr_count = cls._delete_gdpr_records(user)
        data_removed["items_deleted"]["gdpr"] = gdpr_count

        # Finally, delete the user account
        user.delete()
        data_removed["items_deleted"]["user_account"] = 1

        logger.info(f"Deleted all data for user {user.username}")
        return data_removed

    @staticmethod
    def _delete_profile(user: User) -> int:
        """Delete user profile."""
        try:
            from accounts.models import UserProfile
            count = UserProfile.objects.filter(user=user).delete()[0]
            logger.info(f"Deleted {count} profile(s) for user {user.username}")
            return count
        except Exception as e:
            logger.error(f"Error deleting profile: {e}")
            return 0

    @staticmethod
    def _delete_mfa_data(user: User) -> int:
        """Delete MFA devices and backup codes."""
        try:
            from accounts.mfa.models import MFADevice, BackupCode

            device_count = MFADevice.objects.filter(user=user).delete()[0]
            code_count = BackupCode.objects.filter(user=user).delete()[0]

            total = device_count + code_count
            logger.info(
                f"Deleted {device_count} MFA device(s) and {code_count} "
                f"backup code(s) for user {user.username}"
            )
            return total
        except Exception as e:
            logger.error(f"Error deleting MFA data: {e}")
            return 0

    @staticmethod
    def _delete_marketplace_data(user: User) -> Dict[str, int]:
        """Delete marketplace-related data."""
        counts = {
            "businesses": 0,
            "investments": 0,
            "jobs": 0,
        }

        try:
            from marketplace.models import Business, InvestmentOpportunity, JobOpportunity

            counts["businesses"] = Business.objects.filter(owner=user).delete()[0]
            counts["investments"] = InvestmentOpportunity.objects.filter(
                posted_by=user
            ).delete()[0]
            counts["jobs"] = JobOpportunity.objects.filter(posted_by=user).delete()[0]

            logger.info(
                f"Deleted marketplace data for user {user.username}: {counts}"
            )
        except Exception as e:
            logger.error(f"Error deleting marketplace data: {e}")

        return counts

    @staticmethod
    def _delete_payment_data(user: User) -> Dict[str, Any]:
        """
        Delete payment data.

        Note: Transactions are anonymized rather than deleted for
        financial compliance reasons.
        """
        counts = {
            "deleted": {"wallet": 0, "subscriptions": 0},
            "anonymized": {"transactions": 0},
        }

        try:
            from payments.models import Wallet, Transaction, Subscription

            # Delete wallet
            counts["deleted"]["wallet"] = Wallet.objects.filter(user=user).delete()[0]

            # Delete subscriptions
            counts["deleted"]["subscriptions"] = Subscription.objects.filter(
                user=user
            ).delete()[0]

            # Anonymize transactions (required for financial records)
            transactions = Transaction.objects.filter(user=user)
            counts["anonymized"]["transactions"] = transactions.count()

            # Set user to None to anonymize
            transactions.update(user=None)

            logger.info(f"Processed payment data for user {user.username}: {counts}")
        except Exception as e:
            logger.error(f"Error deleting payment data: {e}")

        return counts

    @staticmethod
    def _anonymize_audit_logs(user: User) -> int:
        """
        Anonymize audit logs (cannot delete due to compliance).

        Args:
            user: User whose logs to anonymize

        Returns:
            Number of logs anonymized
        """
        try:
            from audit.models import AuditLog, LoginHistory

            # Anonymize audit logs
            audit_count = AuditLog.objects.filter(user=user).update(
                user=None,
                username="[DELETED USER]",
            )

            # Anonymize login history
            login_count = LoginHistory.objects.filter(user=user).update(
                user=None,
                username="[DELETED USER]",
            )

            total = audit_count + login_count
            logger.info(f"Anonymized {total} audit records for user {user.username}")
            return total
        except Exception as e:
            logger.error(f"Error anonymizing audit logs: {e}")
            return 0

    @staticmethod
    def _delete_gdpr_records(user: User) -> int:
        """Delete GDPR records except the deletion request itself."""
        try:
            from gdpr.models import ConsentRecord, DataExportRequest

            consent_count = ConsentRecord.objects.filter(user=user).delete()[0]
            export_count = DataExportRequest.objects.filter(user=user).delete()[0]

            # Note: DataDeletionRequest is NOT deleted - it serves as proof of deletion

            total = consent_count + export_count
            logger.info(f"Deleted {total} GDPR records for user {user.username}")
            return total
        except Exception as e:
            logger.error(f"Error deleting GDPR records: {e}")
            return 0

    @classmethod
    def get_pending_deletions(cls) -> list:
        """
        Get all deletion requests ready to be processed.

        Returns:
            List of DataDeletionRequest objects ready for deletion
        """
        now = timezone.now()

        requests = DataDeletionRequest.objects.filter(
            status__in=["grace_period", "pending"],
            scheduled_deletion_at__lte=now,
        )

        return list(requests)

    @classmethod
    def process_scheduled_deletions(cls) -> Dict[str, int]:
        """
        Process all scheduled deletions whose grace period has ended.

        Returns:
            Dictionary with counts of processed and failed deletions
        """
        pending = cls.get_pending_deletions()

        results = {
            "total": len(pending),
            "success": 0,
            "failed": 0,
        }

        for request in pending:
            success = cls.process_deletion_request(str(request.id))
            if success:
                results["success"] += 1
            else:
                results["failed"] += 1

        logger.info(
            f"Processed {results['success']}/{results['total']} scheduled deletions"
        )
        return results
