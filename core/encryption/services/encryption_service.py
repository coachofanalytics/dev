"""
Encryption Service for PII protection.

Uses Fernet symmetric encryption (AES-128 in CBC mode).
Key should be stored securely in environment variables.
"""

import logging
import base64
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings

logger = logging.getLogger(__name__)


class EncryptionService:
    """
    Service for encrypting and decrypting PII data.

    Uses Fernet symmetric encryption with key from settings.
    """

    _fernet_instance: Optional[Fernet] = None

    @classmethod
    def get_fernet(cls) -> Fernet:
        """
        Get Fernet encryption instance.

        Returns:
            Fernet: Encryption instance

        Raises:
            ValueError: If encryption key is not configured
        """
        if cls._fernet_instance is None:
            encryption_key = getattr(settings, 'ENCRYPTION_KEY', None)

            if not encryption_key:
                raise ValueError(
                    "ENCRYPTION_KEY not configured in settings. "
                    "Generate one using: Fernet.generate_key()"
                )

            # Ensure key is bytes
            if isinstance(encryption_key, str):
                encryption_key = encryption_key.encode()

            cls._fernet_instance = Fernet(encryption_key)

        return cls._fernet_instance

    @classmethod
    def encrypt(cls, plaintext: str) -> str:
        """
        Encrypt plaintext string.

        Args:
            plaintext: String to encrypt

        Returns:
            Base64-encoded encrypted string

        Raises:
            ValueError: If input is None or empty
        """
        if not plaintext:
            return ""

        try:
            fernet = cls.get_fernet()

            # Convert to bytes
            plaintext_bytes = plaintext.encode('utf-8')

            # Encrypt
            encrypted_bytes = fernet.encrypt(plaintext_bytes)

            # Return as base64 string for storage
            return base64.b64encode(encrypted_bytes).decode('utf-8')

        except Exception as e:
            logger.error(f"Encryption error: {e}")
            raise

    @classmethod
    def decrypt(cls, encrypted_text: str) -> str:
        """
        Decrypt encrypted string.

        Args:
            encrypted_text: Base64-encoded encrypted string

        Returns:
            Decrypted plaintext string

        Raises:
            ValueError: If input is None or empty
            InvalidToken: If decryption fails (wrong key or corrupted data)
        """
        if not encrypted_text:
            return ""

        try:
            fernet = cls.get_fernet()

            # Decode from base64
            encrypted_bytes = base64.b64decode(encrypted_text.encode('utf-8'))

            # Decrypt
            plaintext_bytes = fernet.decrypt(encrypted_bytes)

            # Return as string
            return plaintext_bytes.decode('utf-8')

        except InvalidToken:
            logger.error("Decryption failed: invalid token or wrong key")
            raise ValueError("Decryption failed: invalid token or wrong key")
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            raise

    @classmethod
    def rotate_key(cls, old_key: str, new_key: str, encrypted_text: str) -> str:
        """
        Rotate encryption key for a value.

        Decrypts with old key and re-encrypts with new key.

        Args:
            old_key: Old encryption key
            new_key: New encryption key
            encrypted_text: Text encrypted with old key

        Returns:
            Text encrypted with new key
        """
        # Temporarily use old key to decrypt
        old_fernet = Fernet(old_key.encode() if isinstance(old_key, str) else old_key)
        encrypted_bytes = base64.b64decode(encrypted_text.encode('utf-8'))
        plaintext_bytes = old_fernet.decrypt(encrypted_bytes)

        # Use new key to encrypt
        new_fernet = Fernet(new_key.encode() if isinstance(new_key, str) else new_key)
        new_encrypted_bytes = new_fernet.encrypt(plaintext_bytes)

        return base64.b64encode(new_encrypted_bytes).decode('utf-8')

    @staticmethod
    def generate_key() -> str:
        """
        Generate a new Fernet encryption key.

        Returns:
            Base64-encoded Fernet key as string

        Example:
            >>> key = EncryptionService.generate_key()
            >>> print(f"ENCRYPTION_KEY={key}")
        """
        key = Fernet.generate_key()
        return key.decode('utf-8')
