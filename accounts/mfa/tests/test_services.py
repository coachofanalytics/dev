"""
Tests for MFA services.
"""

import pytest
from django.contrib.auth.models import User

from accounts.mfa.models import MFADevice, BackupCode
from accounts.mfa.services import TOTPService, BackupCodesService


@pytest.mark.django_db
class TestTOTPService:
    """Test TOTP service."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

    def test_create_device(self, user):
        """Test creating MFA device."""
        device = TOTPService.create_device(user, device_name="My App")

        assert device.user == user
        assert device.device_name == "My App"
        assert device.secret_key is not None
        assert device.is_verified is False
        assert device.is_active is False

    def test_create_device_deletes_old_unverified(self, user):
        """Test that creating new device deletes old unverified ones."""
        # Create first device (unverified)
        device1 = TOTPService.create_device(user)
        device1_id = device1.id

        # Create second device
        device2 = TOTPService.create_device(user)

        # First device should be deleted
        assert not MFADevice.objects.filter(id=device1_id).exists()
        assert MFADevice.objects.filter(user=user).count() == 1

    def test_get_or_create_device_creates(self, user):
        """Test get_or_create when device doesn't exist."""
        device, created = TOTPService.get_or_create_device(user)

        assert created is True
        assert device.user == user
        assert device.secret_key is not None

    def test_get_or_create_device_gets_existing(self, user):
        """Test get_or_create when device exists."""
        # Create device first
        device1 = TOTPService.create_device(user)
        device1.activate()

        # Get it
        device2, created = TOTPService.get_or_create_device(user)

        assert created is False
        assert device2.id == device1.id

    def test_generate_qr_code(self, user):
        """Test QR code generation."""
        device = TOTPService.create_device(user)
        qr_bytes = TOTPService.generate_qr_code(device)

        assert qr_bytes is not None
        assert isinstance(qr_bytes, bytes)
        assert len(qr_bytes) > 0

    def test_verify_and_activate_valid_token(self, user):
        """Test verify and activate with valid token."""
        device = TOTPService.create_device(user)
        totp = device.get_totp()
        valid_token = totp.now()

        result = TOTPService.verify_and_activate(device, valid_token)

        assert result is True
        device.refresh_from_db()
        assert device.is_active is True
        assert device.is_verified is True
        assert device.activated_at is not None

    def test_verify_and_activate_invalid_token(self, user):
        """Test verify and activate with invalid token."""
        device = TOTPService.create_device(user)

        result = TOTPService.verify_and_activate(device, "000000")

        assert result is False
        device.refresh_from_db()
        assert device.is_active is False
        assert device.is_verified is False

    def test_disable_mfa(self, user):
        """Test disabling MFA."""
        device = TOTPService.create_device(user)
        device.activate()

        result = TOTPService.disable_mfa(user)

        assert result is True
        device.refresh_from_db()
        assert device.is_active is False

    def test_disable_mfa_no_device(self, user):
        """Test disabling MFA when no device exists."""
        result = TOTPService.disable_mfa(user)
        assert result is False

    def test_get_device(self, user):
        """Test getting MFA device."""
        device = TOTPService.create_device(user)

        retrieved = TOTPService.get_device(user)

        assert retrieved is not None
        assert retrieved.id == device.id

    def test_get_device_no_device(self, user):
        """Test getting device when none exists."""
        result = TOTPService.get_device(user)
        assert result is None

    def test_is_mfa_enabled_true(self, user):
        """Test checking if MFA is enabled (true)."""
        device = TOTPService.create_device(user)
        device.activate()

        assert TOTPService.is_mfa_enabled(user) is True

    def test_is_mfa_enabled_false_no_device(self, user):
        """Test checking if MFA is enabled (false - no device)."""
        assert TOTPService.is_mfa_enabled(user) is False

    def test_is_mfa_enabled_false_not_activated(self, user):
        """Test checking if MFA is enabled (false - not activated)."""
        TOTPService.create_device(user)  # Not activated

        assert TOTPService.is_mfa_enabled(user) is False


@pytest.mark.django_db
class TestBackupCodesService:
    """Test backup codes service."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

    def test_generate_codes(self, user):
        """Test generating backup codes."""
        codes = BackupCodesService.generate_codes(user, count=10)

        assert len(codes) == 10
        assert all(isinstance(code, BackupCode) for code in codes)
        assert all(code.user == user for code in codes)

    def test_get_unused_codes(self, user):
        """Test getting unused codes."""
        BackupCodesService.generate_codes(user, count=5)

        unused = BackupCodesService.get_unused_codes(user)

        assert len(unused) == 5
        assert all(not code.is_used for code in unused)

    def test_get_unused_codes_after_using_some(self, user):
        """Test getting unused codes after using some."""
        codes = BackupCodesService.generate_codes(user, count=5)

        # Use 2 codes
        codes[0].use()
        codes[1].use()

        unused = BackupCodesService.get_unused_codes(user)

        assert len(unused) == 3

    def test_get_used_codes(self, user):
        """Test getting used codes."""
        codes = BackupCodesService.generate_codes(user, count=5)

        # Use 2 codes
        codes[0].use()
        codes[1].use()

        used = BackupCodesService.get_used_codes(user)

        assert len(used) == 2
        assert all(code.is_used for code in used)

    def test_verify_code_valid(self, user):
        """Test verifying valid code."""
        codes = BackupCodesService.generate_codes(user, count=1)
        code_str = codes[0].code

        result = BackupCodesService.verify_code(user, code_str)

        assert result is not None
        assert result.is_used is True

    def test_verify_code_invalid(self, user):
        """Test verifying invalid code."""
        result = BackupCodesService.verify_code(user, "INVALID")
        assert result is None

    def test_get_remaining_count(self, user):
        """Test getting remaining code count."""
        BackupCodesService.generate_codes(user, count=10)

        count = BackupCodesService.get_remaining_count(user)
        assert count == 10

        # Use one code
        codes = BackupCode.objects.filter(user=user, is_used=False)
        codes[0].use()

        count = BackupCodesService.get_remaining_count(user)
        assert count == 9

    def test_regenerate_codes(self, user):
        """Test regenerating codes."""
        # Generate initial codes
        BackupCodesService.generate_codes(user, count=5)
        old_codes = list(BackupCode.objects.filter(user=user).values_list('code', flat=True))

        # Regenerate
        new_codes = BackupCodesService.regenerate_codes(user, count=10)

        assert len(new_codes) == 10

        # Old codes should be deleted
        current_codes = list(BackupCode.objects.filter(user=user).values_list('code', flat=True))
        assert len(current_codes) == 10
        assert not any(code in current_codes for code in old_codes)
