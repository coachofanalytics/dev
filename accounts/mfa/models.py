"""
Multi-Factor Authentication (MFA) models.

Provides TOTP-based two-factor authentication with backup codes
for account recovery.
"""

import secrets
import string
from typing import Optional

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
import pyotp


class MFADevice(models.Model):
    """
    TOTP device for multi-factor authentication.

    Each user can have one active MFA device using Time-based One-Time Password (TOTP).
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="mfa_device",
        help_text="User who owns this MFA device",
    )

    secret_key = models.CharField(
        max_length=32,
        help_text="Base32-encoded secret key for TOTP generation",
    )

    is_active = models.BooleanField(
        default=False,
        help_text="Whether MFA is enabled for this user",
    )

    is_verified = models.BooleanField(
        default=False,
        help_text="Whether the device has been verified with a valid code",
    )

    device_name = models.CharField(
        max_length=100,
        default="Authenticator App",
        help_text="Friendly name for this device",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    activated_at = models.DateTimeField(null=True, blank=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "accounts_mfa_device"
        verbose_name = "MFA Device"
        verbose_name_plural = "MFA Devices"

    def __str__(self) -> str:
        """Return string representation."""
        status = "Active" if self.is_active else "Inactive"
        return f"{self.user.username} - {self.device_name} ({status})"

    def generate_secret(self) -> None:
        """Generate a new random secret key."""
        self.secret_key = pyotp.random_base32()

    def get_totp(self) -> pyotp.TOTP:
        """
        Get TOTP instance for this device.

        Returns:
            pyotp.TOTP: TOTP generator instance
        """
        return pyotp.TOTP(self.secret_key)

    def verify_token(self, token: str) -> bool:
        """
        Verify a TOTP token.

        Args:
            token: 6-digit TOTP code to verify

        Returns:
            bool: True if token is valid
        """
        if not token or len(token) != 6:
            return False

        totp = self.get_totp()
        # Allow 1 time step before and after for clock drift (30 second window on each side)
        is_valid = totp.verify(token, valid_window=1)

        if is_valid:
            self.last_used_at = timezone.now()
            self.save(update_fields=["last_used_at"])

        return is_valid

    def get_provisioning_uri(self, issuer_name: str = "Biashara Bridges") -> str:
        """
        Get provisioning URI for QR code generation.

        Args:
            issuer_name: Name of the service (shown in authenticator app)

        Returns:
            str: Provisioning URI for QR code
        """
        totp = self.get_totp()
        return totp.provisioning_uri(
            name=self.user.email,
            issuer_name=issuer_name,
        )

    def activate(self) -> None:
        """Activate this MFA device."""
        self.is_active = True
        self.is_verified = True
        self.activated_at = timezone.now()
        self.save()

    def deactivate(self) -> None:
        """Deactivate this MFA device."""
        self.is_active = False
        self.save()


class BackupCode(models.Model):
    """
    Backup codes for MFA recovery.

    Users can use backup codes to access their account if they lose
    their MFA device. Each code can only be used once.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="backup_codes",
        help_text="User who owns these backup codes",
    )

    code = models.CharField(
        max_length=16,
        unique=True,
        help_text="Backup code (stored as hash in production)",
    )

    is_used = models.BooleanField(
        default=False,
        help_text="Whether this code has been used",
    )

    used_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this code was used",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "accounts_backup_code"
        verbose_name = "Backup Code"
        verbose_name_plural = "Backup Codes"
        indexes = [
            models.Index(fields=["user", "is_used"]),
        ]

    def __str__(self) -> str:
        """Return string representation."""
        status = "Used" if self.is_used else "Available"
        return f"{self.user.username} - {self.code[:4]}**** ({status})"

    @staticmethod
    def generate_code() -> str:
        """
        Generate a secure random backup code.

        Returns:
            str: 12-character alphanumeric code
        """
        alphabet = string.ascii_uppercase + string.digits
        # Remove ambiguous characters
        alphabet = alphabet.replace('O', '').replace('0', '').replace('I', '').replace('1', '')

        code = ''.join(secrets.choice(alphabet) for _ in range(12))
        # Format as XXX-XXX-XXX-XXX for readability
        return f"{code[0:3]}-{code[3:6]}-{code[6:9]}-{code[9:12]}"

    @classmethod
    def generate_codes_for_user(cls, user: User, count: int = 10) -> list["BackupCode"]:
        """
        Generate backup codes for a user.

        Args:
            user: User to generate codes for
            count: Number of codes to generate (default: 10)

        Returns:
            list: List of BackupCode instances
        """
        # Delete any existing unused codes
        cls.objects.filter(user=user, is_used=False).delete()

        codes = []
        for _ in range(count):
            code = cls(
                user=user,
                code=cls.generate_code(),
            )
            codes.append(code)

        # Bulk create for efficiency
        cls.objects.bulk_create(codes)

        return codes

    def use(self) -> bool:
        """
        Mark this code as used.

        Returns:
            bool: True if code was successfully used

        Raises:
            ValidationError: If code has already been used
        """
        if self.is_used:
            raise ValidationError("This backup code has already been used")

        self.is_used = True
        self.used_at = timezone.now()
        self.save()

        return True

    @classmethod
    def verify_code(cls, user: User, code: str) -> Optional["BackupCode"]:
        """
        Verify a backup code for a user.

        Args:
            user: User attempting to use the code
            code: Backup code to verify

        Returns:
            BackupCode instance if valid, None otherwise
        """
        # Normalize input code (remove spaces and dashes, convert to uppercase)
        normalized_input = code.replace(" ", "").replace("-", "").upper()

        # Get all unused codes for this user
        unused_codes = cls.objects.filter(user=user, is_used=False)

        # Check each code by normalizing it
        for backup_code in unused_codes:
            # Normalize stored code for comparison
            normalized_stored = backup_code.code.replace(" ", "").replace("-", "").upper()

            if normalized_input == normalized_stored:
                backup_code.use()
                return backup_code

        return None
