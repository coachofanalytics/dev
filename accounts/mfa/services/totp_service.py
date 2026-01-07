"""
TOTP service for MFA functionality.

Handles QR code generation, token verification, and TOTP management.
"""

import io
from typing import Optional, Tuple

import pyotp
import qrcode
from django.contrib.auth.models import User
from django.core.files.base import ContentFile

from accounts.mfa.models import MFADevice


class TOTPService:
    """Service for TOTP-based multi-factor authentication."""

    @staticmethod
    def create_device(
        user: User, device_name: str = "Authenticator App"
    ) -> MFADevice:
        """
        Create a new MFA device for a user.

        Args:
            user: User to create device for
            device_name: Friendly name for the device

        Returns:
            MFADevice: Newly created MFA device (not yet verified)
        """
        # Delete any existing unverified device
        MFADevice.objects.filter(user=user, is_verified=False).delete()

        # Create new device
        device = MFADevice(user=user, device_name=device_name)
        device.generate_secret()
        device.save()

        return device

    @staticmethod
    def get_or_create_device(user: User) -> Tuple[MFADevice, bool]:
        """
        Get existing MFA device or create a new one.

        Args:
            user: User to get device for

        Returns:
            Tuple of (MFADevice, created: bool)
        """
        try:
            device = MFADevice.objects.get(user=user)
            return device, False
        except MFADevice.DoesNotExist:
            device = TOTPService.create_device(user)
            return device, True

    @staticmethod
    def generate_qr_code(device: MFADevice, issuer_name: str = "Biashara Bridges") -> bytes:
        """
        Generate QR code for TOTP provisioning.

        Args:
            device: MFA device to generate QR code for
            issuer_name: Name of the service (shown in authenticator app)

        Returns:
            bytes: PNG image data for QR code
        """
        provisioning_uri = device.get_provisioning_uri(issuer_name)

        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(provisioning_uri)
        qr.make(fit=True)

        # Create image
        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to bytes
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        return buffer.getvalue()

    @staticmethod
    def verify_and_activate(device: MFADevice, token: str) -> bool:
        """
        Verify TOTP token and activate device.

        Args:
            device: MFA device to verify
            token: 6-digit TOTP code

        Returns:
            bool: True if verification successful and device activated
        """
        if device.verify_token(token):
            device.activate()
            return True
        return False

    @staticmethod
    def disable_mfa(user: User) -> bool:
        """
        Disable MFA for a user.

        Args:
            user: User to disable MFA for

        Returns:
            bool: True if MFA was disabled
        """
        try:
            device = MFADevice.objects.get(user=user)
            device.deactivate()
            return True
        except MFADevice.DoesNotExist:
            return False

    @staticmethod
    def get_device(user: User) -> Optional[MFADevice]:
        """
        Get MFA device for a user.

        Args:
            user: User to get device for

        Returns:
            MFADevice or None if user has no MFA device
        """
        try:
            return MFADevice.objects.get(user=user)
        except MFADevice.DoesNotExist:
            return None

    @staticmethod
    def is_mfa_enabled(user: User) -> bool:
        """
        Check if MFA is enabled for a user.

        Args:
            user: User to check

        Returns:
            bool: True if MFA is enabled
        """
        try:
            device = MFADevice.objects.get(user=user)
            return device.is_active and device.is_verified
        except MFADevice.DoesNotExist:
            return False
