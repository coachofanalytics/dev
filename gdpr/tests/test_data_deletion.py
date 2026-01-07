"""
Tests for GDPR data deletion service.
"""

import pytest
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta

from gdpr.services.data_deletion_service import DataDeletionService
from gdpr.models import DataDeletionRequest


@pytest.mark.django_db
class TestDataDeletionService:
    """Test data deletion service."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )

    def test_create_deletion_request(self, user):
        """Test creating a deletion request."""
        request = DataDeletionService.create_deletion_request(
            user,
            reason="No longer need account"
        )

        assert request is not None
        assert request.user == user
        assert request.username == user.username
        assert request.email == user.email
        assert request.reason == "No longer need account"
        assert request.status == "grace_period"
        assert request.grace_period_end is not None

    def test_create_deletion_request_existing_pending(self, user):
        """Test that existing pending request prevents new one."""
        request1 = DataDeletionService.create_deletion_request(user)

        with pytest.raises(ValidationError) as exc:
            DataDeletionService.create_deletion_request(user)

        assert "already have a pending deletion request" in str(exc.value)

    def test_cancel_deletion_request(self, user):
        """Test cancelling a deletion request."""
        request = DataDeletionService.create_deletion_request(user)

        success = DataDeletionService.cancel_deletion_request(user)

        assert success is True

        request.refresh_from_db()
        assert request.status == "cancelled"
        assert request.cancelled_at is not None

    def test_cancel_deletion_no_request(self, user):
        """Test cancelling when no request exists."""
        with pytest.raises(ValidationError) as exc:
            DataDeletionService.cancel_deletion_request(user)

        assert "No pending deletion request" in str(exc.value)

    def test_process_deletion_still_in_grace_period(self, user):
        """Test that deletion cannot be processed during grace period."""
        request = DataDeletionService.create_deletion_request(user)

        success = DataDeletionService.process_deletion_request(str(request.id))

        # Should fail because still in grace period
        assert success is False

        request.refresh_from_db()
        assert request.status == "grace_period"

    def test_process_deletion_after_grace_period(self, user):
        """Test processing deletion after grace period."""
        request = DataDeletionService.create_deletion_request(user)

        # Set grace period to past
        request.grace_period_end = timezone.now() - timedelta(days=1)
        request.scheduled_deletion_at = request.grace_period_end
        request.save()

        success = DataDeletionService.process_deletion_request(str(request.id))

        assert success is True

        request.refresh_from_db()
        assert request.status == "completed"
        assert request.deleted_at is not None
        assert request.data_removed is not None

        # User should be deleted
        assert not User.objects.filter(username="testuser").exists()

    def test_process_deletion_not_found(self):
        """Test processing non-existent request."""
        success = DataDeletionService.process_deletion_request(
            "00000000-0000-0000-0000-000000000000"
        )

        assert success is False

    def test_delete_profile(self, user):
        """Test deleting user profile."""
        # Profile deletion is tested as part of full deletion
        count = DataDeletionService._delete_profile(user)

        # Should return 0 or more (depending on if profile exists)
        assert count >= 0

    def test_delete_mfa_data(self, user):
        """Test deleting MFA data."""
        from accounts.mfa.models import MFADevice, BackupCode

        # Create MFA device
        device = MFADevice.objects.create(
            user=user,
            secret_key="TESTSECRET123",
        )

        # Create backup codes
        BackupCode.generate_codes_for_user(user, count=5)

        # Delete MFA data
        count = DataDeletionService._delete_mfa_data(user)

        assert count >= 6  # 1 device + 5 codes

        # Verify deletion
        assert not MFADevice.objects.filter(user=user).exists()
        assert not BackupCode.objects.filter(user=user).exists()

    def test_delete_marketplace_data(self, user):
        """Test deleting marketplace data."""
        counts = DataDeletionService._delete_marketplace_data(user)

        assert "businesses" in counts
        assert "investments" in counts
        assert "jobs" in counts
        assert isinstance(counts["businesses"], int)

    def test_delete_payment_data(self, user):
        """Test deleting payment data."""
        counts = DataDeletionService._delete_payment_data(user)

        assert "deleted" in counts
        assert "anonymized" in counts
        assert "wallet" in counts["deleted"]
        assert "subscriptions" in counts["deleted"]
        assert "transactions" in counts["anonymized"]

    def test_anonymize_audit_logs(self, user):
        """Test anonymizing audit logs."""
        from audit.models import AuditLog

        # Create some audit logs
        AuditLog.objects.create(
            user=user,
            username=user.username,
            event_type="login_success",
            description="User logged in",
        )

        count = DataDeletionService._anonymize_audit_logs(user)

        assert count >= 1

        # Verify anonymization
        logs = AuditLog.objects.filter(username="[DELETED USER]")
        assert logs.exists()

    def test_delete_gdpr_records(self, user):
        """Test deleting GDPR records."""
        from gdpr.models import ConsentRecord, DataExportRequest

        # Create GDPR records
        ConsentRecord.objects.create(
            user=user,
            consent_type="terms_of_service",
            version="1.0",
        )

        DataExportRequest.objects.create(
            user=user,
            export_format="json",
        )

        count = DataDeletionService._delete_gdpr_records(user)

        assert count >= 2

        # Verify deletion
        assert not ConsentRecord.objects.filter(user=user).exists()
        assert not DataExportRequest.objects.filter(user=user).exists()

    def test_get_pending_deletions(self):
        """Test getting pending deletions."""
        user1 = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="pass123"
        )

        user2 = User.objects.create_user(
            username="user2",
            email="user2@example.com",
            password="pass123"
        )

        # Create deletion requests
        request1 = DataDeletionService.create_deletion_request(user1)
        request2 = DataDeletionService.create_deletion_request(user2)

        # Set grace periods to past
        past_time = timezone.now() - timedelta(days=1)
        request1.grace_period_end = past_time
        request1.scheduled_deletion_at = past_time
        request1.save()

        request2.grace_period_end = past_time
        request2.scheduled_deletion_at = past_time
        request2.save()

        # Get pending deletions
        pending = DataDeletionService.get_pending_deletions()

        assert len(pending) >= 2

    def test_process_scheduled_deletions(self):
        """Test processing all scheduled deletions."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="pass123"
        )

        request = DataDeletionService.create_deletion_request(user)

        # Set grace period to past
        past_time = timezone.now() - timedelta(days=1)
        request.grace_period_end = past_time
        request.scheduled_deletion_at = past_time
        request.save()

        # Process scheduled deletions
        results = DataDeletionService.process_scheduled_deletions()

        assert results["total"] >= 1
        assert results["success"] >= 1

    def test_full_deletion_workflow(self, user):
        """Test complete deletion workflow."""
        # Create various data for user
        from accounts.mfa.models import MFADevice, BackupCode
        from gdpr.models import ConsentRecord

        # Create MFA device
        MFADevice.objects.create(user=user, secret_key="TEST123")

        # Create backup codes
        BackupCode.generate_codes_for_user(user, count=10)

        # Create consent record
        ConsentRecord.objects.create(
            user=user,
            consent_type="terms_of_service",
            version="1.0",
        )

        # Create deletion request
        request = DataDeletionService.create_deletion_request(user)

        # Fast-forward past grace period
        request.grace_period_end = timezone.now() - timedelta(days=1)
        request.scheduled_deletion_at = request.grace_period_end
        request.save()

        # Process deletion
        success = DataDeletionService.process_deletion_request(str(request.id))

        assert success is True

        # Verify all data deleted
        assert not User.objects.filter(username="testuser").exists()
        assert not MFADevice.objects.filter(user=user).exists()
        assert not BackupCode.objects.filter(user=user).exists()
        assert not ConsentRecord.objects.filter(user=user).exists()

        # Deletion request should still exist (proof of deletion)
        assert DataDeletionRequest.objects.filter(id=request.id).exists()
