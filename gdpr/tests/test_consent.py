"""
Tests for GDPR consent service.
"""

import pytest
from django.contrib.auth.models import User
from django.utils import timezone

from gdpr.services.consent_service import ConsentService, PrivacyPolicyService
from gdpr.models import ConsentRecord, PrivacyPolicyVersion


@pytest.mark.django_db
class TestConsentService:
    """Test consent management service."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

    def test_give_consent(self, user):
        """Test giving consent."""
        consent = ConsentService.give_consent(
            user=user,
            consent_type="terms_of_service",
            version="1.0",
            consent_text="I agree to the terms",
            ip_address="192.168.1.1",
            user_agent="Test Browser",
        )

        assert consent is not None
        assert consent.user == user
        assert consent.consent_type == "terms_of_service"
        assert consent.version == "1.0"
        assert consent.is_given is True
        assert consent.ip_address == "192.168.1.1"
        assert consent.user_agent == "Test Browser"

    def test_give_consent_updates_existing(self, user):
        """Test that giving consent updates existing record."""
        # Give consent first time
        consent1 = ConsentService.give_consent(
            user=user,
            consent_type="privacy_policy",
            version="1.0",
        )

        # Give consent again with new version
        consent2 = ConsentService.give_consent(
            user=user,
            consent_type="privacy_policy",
            version="1.1",
        )

        # Should be same record
        assert consent1.id == consent2.id
        assert consent2.version == "1.1"

    def test_withdraw_consent(self, user):
        """Test withdrawing consent."""
        # First give consent
        ConsentService.give_consent(
            user=user,
            consent_type="marketing",
            version="1.0",
        )

        # Then withdraw it
        consent = ConsentService.withdraw_consent(user, "marketing")

        assert consent is not None
        assert consent.is_given is False
        assert consent.withdrawn_at is not None

    def test_withdraw_consent_not_given(self, user):
        """Test withdrawing consent that wasn't given."""
        consent = ConsentService.withdraw_consent(user, "analytics")

        assert consent is None

    def test_has_consent_true(self, user):
        """Test checking consent when given."""
        ConsentService.give_consent(
            user=user,
            consent_type="cookies",
            version="1.0",
        )

        assert ConsentService.has_consent(user, "cookies") is True

    def test_has_consent_false(self, user):
        """Test checking consent when not given."""
        assert ConsentService.has_consent(user, "third_party_sharing") is False

    def test_has_consent_after_withdrawal(self, user):
        """Test checking consent after withdrawal."""
        ConsentService.give_consent(user, "data_processing", "1.0")
        ConsentService.withdraw_consent(user, "data_processing")

        assert ConsentService.has_consent(user, "data_processing") is False

    def test_get_consent_record(self, user):
        """Test getting a specific consent record."""
        ConsentService.give_consent(user, "terms_of_service", "1.0")

        record = ConsentService.get_consent_record(user, "terms_of_service")

        assert record is not None
        assert record.consent_type == "terms_of_service"

    def test_get_consent_record_not_exists(self, user):
        """Test getting non-existent consent record."""
        record = ConsentService.get_consent_record(user, "marketing")

        assert record is None

    def test_get_all_consents(self, user):
        """Test getting all consent records."""
        # Give multiple consents
        ConsentService.give_consent(user, "terms_of_service", "1.0")
        ConsentService.give_consent(user, "privacy_policy", "1.0")
        ConsentService.give_consent(user, "marketing", "1.0")

        consents = ConsentService.get_all_consents(user)

        assert len(consents) == 3

    def test_get_consent_summary(self, user):
        """Test getting consent summary."""
        # Give some consents
        ConsentService.give_consent(user, "terms_of_service", "1.0")
        ConsentService.give_consent(user, "privacy_policy", "1.0")

        summary = ConsentService.get_consent_summary(user)

        assert isinstance(summary, dict)
        assert summary["terms_of_service"] is True
        assert summary["privacy_policy"] is True
        assert summary["marketing"] is False  # Not given

    def test_check_required_consents_compliant(self, user):
        """Test checking required consents when compliant."""
        # Give required consents
        ConsentService.give_consent(user, "terms_of_service", "1.0")
        ConsentService.give_consent(user, "privacy_policy", "1.0")

        result = ConsentService.check_required_consents(user)

        assert result["compliant"] is True
        assert len(result["missing"]) == 0

    def test_check_required_consents_non_compliant(self, user):
        """Test checking required consents when not compliant."""
        # Give only one required consent
        ConsentService.give_consent(user, "terms_of_service", "1.0")

        result = ConsentService.check_required_consents(user)

        assert result["compliant"] is False
        assert "privacy_policy" in result["missing"]


@pytest.mark.django_db
class TestPrivacyPolicyService:
    """Test privacy policy service."""

    @pytest.fixture
    def admin_user(self):
        """Create admin user."""
        return User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="adminpass123"
        )

    @pytest.fixture
    def user(self):
        """Create regular user."""
        return User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

    def test_create_version(self, admin_user):
        """Test creating a privacy policy version."""
        policy = PrivacyPolicyService.create_version(
            version="1.0",
            title="Privacy Policy v1.0",
            content="Full policy content here",
            summary="Initial version",
            effective_date=timezone.now(),
            created_by=admin_user,
            is_active=True,
        )

        assert policy is not None
        assert policy.version == "1.0"
        assert policy.title == "Privacy Policy v1.0"
        assert policy.is_active is True
        assert policy.created_by == admin_user

    def test_get_active_version(self, admin_user):
        """Test getting active version."""
        # Create versions
        PrivacyPolicyService.create_version(
            version="1.0",
            title="Privacy Policy v1.0",
            content="Content 1.0",
            effective_date=timezone.now(),
            created_by=admin_user,
            is_active=False,
        )

        PrivacyPolicyService.create_version(
            version="1.1",
            title="Privacy Policy v1.1",
            content="Content 1.1",
            effective_date=timezone.now(),
            created_by=admin_user,
            is_active=True,
        )

        active = PrivacyPolicyService.get_active_version()

        assert active is not None
        assert active.version == "1.1"

    def test_get_all_versions(self, admin_user):
        """Test getting all versions."""
        # Create multiple versions
        PrivacyPolicyService.create_version(
            version="1.0",
            title="Privacy Policy v1.0",
            content="Content",
            effective_date=timezone.now(),
            created_by=admin_user,
        )

        PrivacyPolicyService.create_version(
            version="1.1",
            title="Privacy Policy v1.1",
            content="Content",
            effective_date=timezone.now(),
            created_by=admin_user,
        )

        versions = PrivacyPolicyService.get_all_versions()

        assert len(versions) >= 2

    def test_activate_version(self, admin_user):
        """Test activating a specific version."""
        # Create versions
        policy1 = PrivacyPolicyService.create_version(
            version="1.0",
            title="Privacy Policy v1.0",
            content="Content",
            effective_date=timezone.now(),
            created_by=admin_user,
            is_active=True,
        )

        PrivacyPolicyService.create_version(
            version="1.1",
            title="Privacy Policy v1.1",
            content="Content",
            effective_date=timezone.now(),
            created_by=admin_user,
            is_active=False,
        )

        # Activate version 1.1
        activated = PrivacyPolicyService.activate_version("1.1")

        assert activated is not None
        assert activated.version == "1.1"
        assert activated.is_active is True

        # Check that 1.0 is now inactive
        policy1.refresh_from_db()
        assert policy1.is_active is False

    def test_activate_version_not_found(self):
        """Test activating non-existent version."""
        result = PrivacyPolicyService.activate_version("99.9")

        assert result is None

    def test_get_user_accepted_version(self, user, admin_user):
        """Test getting user's accepted version."""
        # Create policy version
        PrivacyPolicyService.create_version(
            version="1.0",
            title="Privacy Policy",
            content="Content",
            effective_date=timezone.now(),
            created_by=admin_user,
            is_active=True,
        )

        # User accepts it
        ConsentService.give_consent(user, "privacy_policy", "1.0")

        accepted_version = PrivacyPolicyService.get_user_accepted_version(user)

        assert accepted_version == "1.0"

    def test_get_user_accepted_version_none(self, user):
        """Test getting accepted version when user hasn't accepted."""
        accepted_version = PrivacyPolicyService.get_user_accepted_version(user)

        assert accepted_version is None

    def test_needs_new_consent_true(self, user, admin_user):
        """Test checking if user needs new consent."""
        # Create and activate version 1.0
        PrivacyPolicyService.create_version(
            version="1.0",
            title="Privacy Policy",
            content="Content",
            effective_date=timezone.now(),
            created_by=admin_user,
            is_active=True,
        )

        # User accepts 1.0
        ConsentService.give_consent(user, "privacy_policy", "1.0")

        # Create and activate new version 1.1
        PrivacyPolicyService.create_version(
            version="1.1",
            title="Privacy Policy Updated",
            content="New content",
            effective_date=timezone.now(),
            created_by=admin_user,
            is_active=True,
        )

        # User should need new consent
        needs_consent = PrivacyPolicyService.needs_new_consent(user)

        assert needs_consent is True

    def test_needs_new_consent_false(self, user, admin_user):
        """Test checking if user needs consent when already accepted."""
        # Create and activate version
        PrivacyPolicyService.create_version(
            version="1.0",
            title="Privacy Policy",
            content="Content",
            effective_date=timezone.now(),
            created_by=admin_user,
            is_active=True,
        )

        # User accepts it
        ConsentService.give_consent(user, "privacy_policy", "1.0")

        # User should not need new consent
        needs_consent = PrivacyPolicyService.needs_new_consent(user)

        assert needs_consent is False

    def test_needs_new_consent_no_acceptance(self, user, admin_user):
        """Test checking consent when user never accepted."""
        # Create and activate version
        PrivacyPolicyService.create_version(
            version="1.0",
            title="Privacy Policy",
            content="Content",
            effective_date=timezone.now(),
            created_by=admin_user,
            is_active=True,
        )

        # User never accepted
        needs_consent = PrivacyPolicyService.needs_new_consent(user)

        assert needs_consent is True
