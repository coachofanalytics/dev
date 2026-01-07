"""
Backup codes service for MFA recovery.

Handles generation, verification, and management of backup codes.
"""

from typing import List, Optional

from django.contrib.auth.models import User

from accounts.mfa.models import BackupCode


class BackupCodesService:
    """Service for managing MFA backup codes."""

    @staticmethod
    def generate_codes(user: User, count: int = 10) -> List[BackupCode]:
        """
        Generate backup codes for a user.

        Args:
            user: User to generate codes for
            count: Number of codes to generate (default: 10)

        Returns:
            List of BackupCode instances
        """
        return BackupCode.generate_codes_for_user(user, count)

    @staticmethod
    def get_unused_codes(user: User) -> List[BackupCode]:
        """
        Get all unused backup codes for a user.

        Args:
            user: User to get codes for

        Returns:
            List of unused BackupCode instances
        """
        return list(BackupCode.objects.filter(user=user, is_used=False))

    @staticmethod
    def get_used_codes(user: User) -> List[BackupCode]:
        """
        Get all used backup codes for a user.

        Args:
            user: User to get codes for

        Returns:
            List of used BackupCode instances
        """
        return list(BackupCode.objects.filter(user=user, is_used=True))

    @staticmethod
    def verify_code(user: User, code: str) -> Optional[BackupCode]:
        """
        Verify and use a backup code.

        Args:
            user: User attempting to use the code
            code: Backup code to verify

        Returns:
            BackupCode instance if valid, None otherwise
        """
        return BackupCode.verify_code(user, code)

    @staticmethod
    def get_remaining_count(user: User) -> int:
        """
        Get count of remaining unused backup codes.

        Args:
            user: User to check

        Returns:
            int: Number of unused backup codes
        """
        return BackupCode.objects.filter(user=user, is_used=False).count()

    @staticmethod
    def regenerate_codes(user: User, count: int = 10) -> List[BackupCode]:
        """
        Regenerate backup codes (deletes old unused codes).

        Args:
            user: User to regenerate codes for
            count: Number of codes to generate

        Returns:
            List of new BackupCode instances
        """
        return BackupCode.generate_codes_for_user(user, count)
