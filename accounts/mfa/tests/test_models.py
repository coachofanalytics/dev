"""
Tests for MFA models.
"""

import pytest
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone

from accounts.mfa.models import MFADevice, BackupCode


@pytest.mark.django_db
class TestMFADevice:
    """Test MFADevice model."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

    @pytest.fixture
    def mfa_device(self, user):
        """Create test MFA device."""
        device = MFADevice(user=user, device_name="Test Device")
        device.generate_secret()
        device.save()
        return device

    def test_create_mfa_device(self, user):
        """Test creating MFA device."""
        device = MFADevice.objects.create(
            user=user,
            secret_key="TESTSECRETKEY123",
            device_name="My Authenticator"
        )

        assert device.user == user
        assert device.secret_key == "TESTSECRETKEY123"
        assert device.device_name == "My Authenticator"
        assert device.is_active is False
        assert device.is_verified is False

    def test_generate_secret(self, user):
        """Test secret key generation."""
        device = MFADevice(user=user)
        device.generate_secret()

        assert device.secret_key is not None
        assert len(device.secret_key) == 32  # Base32 encoded
        assert device.secret_key.isalnum()

    def test_get_totp(self, mfa_device):
        """Test TOTP instance generation."""
        totp = mfa_device.get_totp()

        assert totp is not None
        assert hasattr(totp, 'now')
        assert hasattr(totp, 'verify')

    def test_verify_token_valid(self, mfa_device):
        """Test verifying valid TOTP token."""
        totp = mfa_device.get_totp()
        valid_token = totp.now()

        assert mfa_device.verify_token(valid_token) is True
        assert mfa_device.last_used_at is not None

    def test_verify_token_invalid(self, mfa_device):
        """Test verifying invalid TOTP token."""
        assert mfa_device.verify_token("000000") is False
        assert mfa_device.verify_token("") is False
        assert mfa_device.verify_token("12345") is False  # Wrong length

    def test_get_provisioning_uri(self, mfa_device):
        """Test provisioning URI generation."""
        uri = mfa_device.get_provisioning_uri()

        assert uri.startswith("otpauth://totp/")
        # Email will be URL-encoded in the URI
        assert "test%40example.com" in uri or mfa_device.user.email in uri
        assert "Biashara" in uri

    def test_activate(self, mfa_device):
        """Test activating MFA device."""
        assert mfa_device.is_active is False
        assert mfa_device.is_verified is False

        mfa_device.activate()

        assert mfa_device.is_active is True
        assert mfa_device.is_verified is True
        assert mfa_device.activated_at is not None

    def test_deactivate(self, mfa_device):
        """Test deactivating MFA device."""
        mfa_device.activate()
        assert mfa_device.is_active is True

        mfa_device.deactivate()

        assert mfa_device.is_active is False

    def test_one_device_per_user(self, user, mfa_device):
        """Test OneToOne relationship with user."""
        # Try to create another device for same user
        with pytest.raises(Exception):  # IntegrityError
            MFADevice.objects.create(
                user=user,
                secret_key="ANOTHERSECRET"
            )

    def test_str_representation(self, mfa_device):
        """Test string representation."""
        str_repr = str(mfa_device)

        assert mfa_device.user.username in str_repr
        assert mfa_device.device_name in str_repr
        assert "Inactive" in str_repr

        mfa_device.activate()
        str_repr = str(mfa_device)
        assert "Active" in str_repr


@pytest.mark.django_db
class TestBackupCode:
    """Test BackupCode model."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

    def test_generate_code(self):
        """Test backup code generation."""
        code = BackupCode.generate_code()

        # Check format: XXX-XXX-XXX-XXX
        assert len(code) == 15  # 12 chars + 3 dashes
        assert code.count('-') == 3

        # Remove dashes and check length
        code_no_dash = code.replace('-', '')
        assert len(code_no_dash) == 12
        assert code_no_dash.isalnum()

    def test_generate_codes_for_user(self, user):
        """Test generating codes for user."""
        codes = BackupCode.generate_codes_for_user(user, count=10)

        assert len(codes) == 10
        assert all(isinstance(code, BackupCode) for code in codes)
        assert all(code.user == user for code in codes)
        assert all(not code.is_used for code in codes)

    def test_generate_codes_deletes_old_unused(self, user):
        """Test that generating new codes deletes old unused ones."""
        # Generate first set
        BackupCode.generate_codes_for_user(user, count=5)
        assert BackupCode.objects.filter(user=user).count() == 5

        # Generate second set
        BackupCode.generate_codes_for_user(user, count=10)
        assert BackupCode.objects.filter(user=user).count() == 10

    def test_use_code(self, user):
        """Test using a backup code."""
        codes = BackupCode.generate_codes_for_user(user, count=1)
        code = codes[0]

        assert code.is_used is False
        assert code.used_at is None

        result = code.use()

        assert result is True
        assert code.is_used is True
        assert code.used_at is not None

    def test_use_code_twice_raises_error(self, user):
        """Test that using a code twice raises error."""
        codes = BackupCode.generate_codes_for_user(user, count=1)
        code = codes[0]

        code.use()

        with pytest.raises(ValidationError):
            code.use()

    def test_verify_code_valid(self, user):
        """Test verifying valid backup code."""
        codes = BackupCode.generate_codes_for_user(user, count=1)
        code_str = codes[0].code

        result = BackupCode.verify_code(user, code_str)

        assert result is not None
        assert result.is_used is True

    def test_verify_code_invalid(self, user):
        """Test verifying invalid backup code."""
        result = BackupCode.verify_code(user, "INVALID-CODE")
        assert result is None

    def test_verify_code_already_used(self, user):
        """Test verifying already used code."""
        codes = BackupCode.generate_codes_for_user(user, count=1)
        code_str = codes[0].code

        # Use the code
        BackupCode.verify_code(user, code_str)

        # Try to use again
        result = BackupCode.verify_code(user, code_str)
        assert result is None

    def test_verify_code_normalization(self, user):
        """Test that code verification handles different formats."""
        codes = BackupCode.generate_codes_for_user(user, count=1)
        code_str = codes[0].code

        # Remove dashes and lowercase
        code_no_dash = code_str.replace('-', '').lower()

        result = BackupCode.verify_code(user, code_no_dash)
        assert result is not None

    def test_str_representation(self, user):
        """Test string representation."""
        codes = BackupCode.generate_codes_for_user(user, count=1)
        code = codes[0]

        str_repr = str(code)
        assert user.username in str_repr
        assert "Available" in str_repr

        code.use()
        str_repr = str(code)
        assert "Used" in str_repr
