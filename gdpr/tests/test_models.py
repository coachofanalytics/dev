"""
Tests for GDPR models.
"""

import pytest
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta

from gdpr.models import (
    ConsentRecord,
    DataExportRequest,
    DataDeletionRequest,
    PrivacyPolicyVersion,
)


@pytest.mark.django_db
class TestConsentRecord:
    """Test ConsentRecord model."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

    def test_create_consent_record(self, user):
        """Test creating a consent record."""
        consent = ConsentRecord.objects.create(
            user=user,
            consent_type="terms_of_service",
            version="1.0",
            consent_text="I agree to the terms",
        )

        assert consent.user == user
        assert consent.consent_type == "terms_of_service"
        assert consent.version == "1.0"
        assert consent.is_given is False  # Default

    def test_give_consent(self, user):
        """Test giving consent."""
        consent = ConsentRecord.objects.create(
            user=user,
            consent_type="privacy_policy",
            version="1.0",
        )

        consent.give_consent(ip_address="192.168.1.1", user_agent="Test Browser")

        assert consent.is_given is True
        assert consent.given_at is not None
        assert consent.withdrawn_at is None
        assert consent.ip_address == "192.168.1.1"
        assert consent.user_agent == "Test Browser"

    def test_withdraw_consent(self, user):
        """Test withdrawing consent."""
        consent = ConsentRecord.objects.create(
            user=user,
            consent_type="marketing",
            version="1.0",
        )

        consent.give_consent()
        assert consent.is_given is True

        consent.withdraw_consent()
        assert consent.is_given is False
        assert consent.withdrawn_at is not None

    def test_str_representation(self, user):
        """Test string representation."""
        consent = ConsentRecord.objects.create(
            user=user,
            consent_type="analytics",
            version="1.0",
        )

        str_repr = str(consent)
        assert user.username in str_repr
        assert "Analytics" in str_repr


@pytest.mark.django_db
class TestDataExportRequest:
    """Test DataExportRequest model."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

    def test_create_export_request(self, user):
        """Test creating an export request."""
        request = DataExportRequest.objects.create(
            user=user,
            export_format="json",
        )

        assert request.user == user
        assert request.export_format == "json"
        assert request.status == "pending"
        assert request.download_count == 0

    def test_mark_processing(self, user):
        """Test marking request as processing."""
        request = DataExportRequest.objects.create(
            user=user,
            export_format="json",
        )

        request.mark_processing()
        assert request.status == "processing"

    def test_mark_completed(self, user):
        """Test marking request as completed."""
        request = DataExportRequest.objects.create(
            user=user,
            export_format="json",
        )

        request.mark_completed(file_path="/exports/test.json", file_size=1024)

        assert request.status == "completed"
        assert request.file_path == "/exports/test.json"
        assert request.file_size == 1024
        assert request.processed_at is not None
        assert request.expires_at is not None

    def test_mark_failed(self, user):
        """Test marking request as failed."""
        request = DataExportRequest.objects.create(
            user=user,
            export_format="json",
        )

        request.mark_failed("Test error message")

        assert request.status == "failed"
        assert request.error_message == "Test error message"
        assert request.processed_at is not None

    def test_record_download(self, user):
        """Test recording downloads."""
        request = DataExportRequest.objects.create(
            user=user,
            export_format="json",
        )

        request.mark_completed("/exports/test.json", 1024)

        assert request.download_count == 0

        request.record_download()
        assert request.download_count == 1
        assert request.last_downloaded_at is not None

        request.record_download()
        assert request.download_count == 2

    def test_is_expired(self, user):
        """Test checking if export has expired."""
        request = DataExportRequest.objects.create(
            user=user,
            export_format="json",
        )

        # Not expired when no expiry set
        assert request.is_expired is False

        # Set expiry in the past
        request.expires_at = timezone.now() - timedelta(days=1)
        request.save()
        assert request.is_expired is True

        # Set expiry in the future
        request.expires_at = timezone.now() + timedelta(days=1)
        request.save()
        assert request.is_expired is False


@pytest.mark.django_db
class TestDataDeletionRequest:
    """Test DataDeletionRequest model."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

    def test_create_deletion_request(self, user):
        """Test creating a deletion request."""
        request = DataDeletionRequest.objects.create(
            user=user,
            reason="No longer need account",
        )

        assert request.user == user
        assert request.username == user.username
        assert request.email == user.email
        assert request.reason == "No longer need account"
        assert request.status == "pending"

    def test_save_captures_user_info(self, user):
        """Test that save captures username and email."""
        request = DataDeletionRequest(
            user=user,
        )
        request.save()

        assert request.username == user.username
        assert request.email == user.email

    def test_start_grace_period(self, user):
        """Test starting grace period."""
        request = DataDeletionRequest.objects.create(
            user=user,
        )

        request.start_grace_period()

        assert request.status == "grace_period"
        assert request.grace_period_end is not None
        assert request.scheduled_deletion_at is not None

        # Grace period should be 30 days
        expected_end = timezone.now() + timedelta(days=30)
        delta = abs((request.grace_period_end - expected_end).total_seconds())
        assert delta < 10  # Within 10 seconds

    def test_cancel_request(self, user):
        """Test cancelling a deletion request."""
        request = DataDeletionRequest.objects.create(
            user=user,
        )

        request.start_grace_period()
        request.cancel_request()

        assert request.status == "cancelled"
        assert request.cancelled_at is not None

    def test_cannot_cancel_completed(self, user):
        """Test that completed requests cannot be cancelled."""
        request = DataDeletionRequest.objects.create(
            user=user,
        )

        request.mark_completed({})

        with pytest.raises(ValidationError):
            request.cancel_request()

    def test_mark_processing(self, user):
        """Test marking as processing."""
        request = DataDeletionRequest.objects.create(
            user=user,
        )

        request.mark_processing()
        assert request.status == "processing"

    def test_mark_completed(self, user):
        """Test marking as completed."""
        request = DataDeletionRequest.objects.create(
            user=user,
        )

        data_removed = {"users": 1, "profiles": 1}
        request.mark_completed(data_removed)

        assert request.status == "completed"
        assert request.deleted_at is not None
        assert request.data_removed == data_removed

    def test_mark_failed(self, user):
        """Test marking as failed."""
        request = DataDeletionRequest.objects.create(
            user=user,
        )

        request.mark_failed("Test error")

        assert request.status == "failed"
        assert request.error_message == "Test error"

    def test_is_in_grace_period(self, user):
        """Test checking if in grace period."""
        request = DataDeletionRequest.objects.create(
            user=user,
        )

        # No grace period set
        assert request.is_in_grace_period is False

        # Start grace period
        request.start_grace_period()
        assert request.is_in_grace_period is True

        # Set grace period in the past
        request.grace_period_end = timezone.now() - timedelta(days=1)
        request.save()
        assert request.is_in_grace_period is False

    def test_days_until_deletion(self, user):
        """Test calculating days until deletion."""
        request = DataDeletionRequest.objects.create(
            user=user,
        )

        # No deletion scheduled
        assert request.days_until_deletion == 0

        # Schedule for 10 days from now
        request.scheduled_deletion_at = timezone.now() + timedelta(days=10)
        request.save()
        assert 9 <= request.days_until_deletion <= 10


@pytest.mark.django_db
class TestPrivacyPolicyVersion:
    """Test PrivacyPolicyVersion model."""

    @pytest.fixture
    def admin_user(self):
        """Create admin user."""
        return User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="adminpass123"
        )

    def test_create_policy_version(self, admin_user):
        """Test creating a privacy policy version."""
        policy = PrivacyPolicyVersion.objects.create(
            version="1.0",
            title="Privacy Policy v1.0",
            content="Full policy text here",
            summary="Initial version",
            effective_date=timezone.now(),
            created_by=admin_user,
        )

        assert policy.version == "1.0"
        assert policy.title == "Privacy Policy v1.0"
        assert policy.is_active is False  # Default

    def test_only_one_active_version(self, admin_user):
        """Test that only one version can be active."""
        # Create first version
        policy1 = PrivacyPolicyVersion.objects.create(
            version="1.0",
            title="Privacy Policy v1.0",
            content="Version 1.0",
            effective_date=timezone.now(),
            created_by=admin_user,
            is_active=True,
        )

        assert policy1.is_active is True

        # Create second version and activate it
        policy2 = PrivacyPolicyVersion.objects.create(
            version="1.1",
            title="Privacy Policy v1.1",
            content="Version 1.1",
            effective_date=timezone.now(),
            created_by=admin_user,
            is_active=True,
        )

        # Refresh policy1 from database
        policy1.refresh_from_db()

        assert policy2.is_active is True
        assert policy1.is_active is False  # Should be deactivated

    def test_str_representation(self, admin_user):
        """Test string representation."""
        policy = PrivacyPolicyVersion.objects.create(
            version="1.0",
            title="Privacy Policy",
            content="Content",
            effective_date=timezone.now(),
            created_by=admin_user,
            is_active=True,
        )

        str_repr = str(policy)
        assert "1.0" in str_repr
        assert "Active" in str_repr
