"""
Custom Django model fields for encrypted data.

Provides transparent encryption/decryption for PII fields:
- EncryptedCharField: For short strings (phone, SSN, etc.)
- EncryptedTextField: For longer text (addresses, notes, etc.)
"""

import logging
from typing import Optional, Any

from django.db import models
from django.core.exceptions import ValidationError

from core.encryption.services.encryption_service import EncryptionService

logger = logging.getLogger(__name__)


class EncryptedCharField(models.CharField):
    """
    CharField that encrypts data before saving to database.

    Data is encrypted at rest using Fernet symmetric encryption.
    Transparent encryption/decryption on save/load.

    Usage:
        class UserProfile(models.Model):
            phone_number = EncryptedCharField(max_length=255)
    """

    description = "A CharField that stores encrypted data"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize encrypted char field."""
        # Encrypted data is stored as base64, so we need more space
        # Each character becomes ~1.33x larger with base64 encoding
        # Plus Fernet adds ~57 bytes of overhead
        if 'max_length' in kwargs:
            # Adjust max_length to account for encryption overhead
            original_max = kwargs['max_length']
            # Formula: base64(fernet(text)) ≈ (original + 57) * 1.33
            kwargs['max_length'] = int((original_max + 57) * 1.33) + 10

        super().__init__(*args, **kwargs)

    def get_prep_value(self, value: Optional[str]) -> Optional[str]:
        """
        Encrypt value before saving to database.

        Args:
            value: Plaintext value

        Returns:
            Encrypted value or None
        """
        if value is None or value == "":
            return value

        try:
            encrypted = EncryptionService.encrypt(value)
            return encrypted
        except Exception as e:
            logger.error(f"Error encrypting field value: {e}")
            raise ValidationError(f"Encryption failed: {e}")

    def from_db_value(
        self,
        value: Optional[str],
        expression: Any,
        connection: Any
    ) -> Optional[str]:
        """
        Decrypt value when loading from database.

        Args:
            value: Encrypted value from database
            expression: Query expression (unused)
            connection: Database connection (unused)

        Returns:
            Decrypted plaintext value or None
        """
        if value is None or value == "":
            return value

        try:
            decrypted = EncryptionService.decrypt(value)
            return decrypted
        except Exception as e:
            logger.error(f"Error decrypting field value: {e}")
            # Return encrypted value if decryption fails
            # This prevents data loss but indicates a problem
            return value

    def to_python(self, value: Optional[str]) -> Optional[str]:
        """
        Convert value to Python type.

        Args:
            value: Value to convert

        Returns:
            String value
        """
        if isinstance(value, str) or value is None:
            return value
        return str(value)


class EncryptedTextField(models.TextField):
    """
    TextField that encrypts data before saving to database.

    Similar to EncryptedCharField but for longer text content.

    Usage:
        class UserProfile(models.Model):
            address = EncryptedTextField()
    """

    description = "A TextField that stores encrypted data"

    def get_prep_value(self, value: Optional[str]) -> Optional[str]:
        """
        Encrypt value before saving to database.

        Args:
            value: Plaintext value

        Returns:
            Encrypted value or None
        """
        if value is None or value == "":
            return value

        try:
            encrypted = EncryptionService.encrypt(value)
            return encrypted
        except Exception as e:
            logger.error(f"Error encrypting field value: {e}")
            raise ValidationError(f"Encryption failed: {e}")

    def from_db_value(
        self,
        value: Optional[str],
        expression: Any,
        connection: Any
    ) -> Optional[str]:
        """
        Decrypt value when loading from database.

        Args:
            value: Encrypted value from database
            expression: Query expression (unused)
            connection: Database connection (unused)

        Returns:
            Decrypted plaintext value or None
        """
        if value is None or value == "":
            return value

        try:
            decrypted = EncryptionService.decrypt(value)
            return decrypted
        except Exception as e:
            logger.error(f"Error decrypting field value: {e}")
            # Return encrypted value if decryption fails
            return value

    def to_python(self, value: Optional[str]) -> Optional[str]:
        """
        Convert value to Python type.

        Args:
            value: Value to convert

        Returns:
            String value
        """
        if isinstance(value, str) or value is None:
            return value
        return str(value)


class EncryptedEmailField(models.EmailField):
    """
    EmailField that encrypts data before saving to database.

    Provides email validation plus encryption at rest.

    Usage:
        class UserProfile(models.Model):
            backup_email = EncryptedEmailField()
    """

    description = "An EmailField that stores encrypted data"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize encrypted email field."""
        # Adjust max_length for encryption overhead
        if 'max_length' in kwargs:
            original_max = kwargs['max_length']
            kwargs['max_length'] = int((original_max + 57) * 1.33) + 10
        super().__init__(*args, **kwargs)

    def get_prep_value(self, value: Optional[str]) -> Optional[str]:
        """Encrypt value before saving."""
        if value is None or value == "":
            return value

        try:
            encrypted = EncryptionService.encrypt(value)
            return encrypted
        except Exception as e:
            logger.error(f"Error encrypting email field: {e}")
            raise ValidationError(f"Encryption failed: {e}")

    def from_db_value(
        self,
        value: Optional[str],
        expression: Any,
        connection: Any
    ) -> Optional[str]:
        """Decrypt value when loading from database."""
        if value is None or value == "":
            return value

        try:
            decrypted = EncryptionService.decrypt(value)
            return decrypted
        except Exception as e:
            logger.error(f"Error decrypting email field: {e}")
            return value

    def to_python(self, value: Optional[str]) -> Optional[str]:
        """Convert value to Python type."""
        if isinstance(value, str) or value is None:
            return value
        return str(value)
