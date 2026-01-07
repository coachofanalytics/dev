"""
Tests for PII encryption service and fields.
"""

import pytest
from cryptography.fernet import Fernet
from django.conf import settings

from core.encryption.services.encryption_service import EncryptionService


class TestEncryptionService:
    """Test encryption service."""

    def test_generate_key(self):
        """Test generating encryption key."""
        key = EncryptionService.generate_key()

        assert key is not None
        assert isinstance(key, str)
        assert len(key) == 44  # Fernet keys are 44 characters base64

        # Should be valid Fernet key
        fernet = Fernet(key.encode())
        assert fernet is not None

    def test_encrypt_decrypt(self):
        """Test encrypting and decrypting text."""
        plaintext = "Sensitive data 123"

        # Encrypt
        encrypted = EncryptionService.encrypt(plaintext)

        assert encrypted is not None
        assert encrypted != plaintext
        assert len(encrypted) > len(plaintext)  # Encrypted is longer

        # Decrypt
        decrypted = EncryptionService.decrypt(encrypted)

        assert decrypted == plaintext

    def test_encrypt_empty_string(self):
        """Test encrypting empty string."""
        encrypted = EncryptionService.encrypt("")

        assert encrypted == ""

    def test_decrypt_empty_string(self):
        """Test decrypting empty string."""
        decrypted = EncryptionService.decrypt("")

        assert decrypted == ""

    def test_encrypt_unicode(self):
        """Test encrypting Unicode characters."""
        plaintext = "Hello 世界 🌍 français"

        encrypted = EncryptionService.encrypt(plaintext)
        decrypted = EncryptionService.decrypt(encrypted)

        assert decrypted == plaintext

    def test_encrypt_long_text(self):
        """Test encrypting long text."""
        plaintext = "A" * 10000

        encrypted = EncryptionService.encrypt(plaintext)
        decrypted = EncryptionService.decrypt(encrypted)

        assert decrypted == plaintext

    def test_decrypt_invalid_token(self):
        """Test decrypting invalid token."""
        with pytest.raises(ValueError) as exc:
            EncryptionService.decrypt("invalid_encrypted_data")

        assert "Decryption failed" in str(exc.value)

    def test_get_fernet_singleton(self):
        """Test that Fernet instance is singleton."""
        fernet1 = EncryptionService.get_fernet()
        fernet2 = EncryptionService.get_fernet()

        # Should be same instance
        assert fernet1 is fernet2

    def test_get_fernet_no_key_configured(self):
        """Test error when no encryption key configured."""
        # Save original key
        original_key = getattr(settings, 'ENCRYPTION_KEY', None)

        try:
            # Temporarily remove key
            EncryptionService._fernet_instance = None
            if hasattr(settings, 'ENCRYPTION_KEY'):
                delattr(settings, 'ENCRYPTION_KEY')

            with pytest.raises(ValueError) as exc:
                EncryptionService.get_fernet()

            assert "ENCRYPTION_KEY not configured" in str(exc.value)

        finally:
            # Restore original key
            if original_key:
                settings.ENCRYPTION_KEY = original_key
            EncryptionService._fernet_instance = None

    def test_rotate_key(self):
        """Test rotating encryption key."""
        # Generate two keys
        old_key = Fernet.generate_key().decode()
        new_key = Fernet.generate_key().decode()

        # Encrypt with old key
        plaintext = "Sensitive data"
        old_fernet = Fernet(old_key.encode())
        old_encrypted = old_fernet.encrypt(plaintext.encode()).decode()

        # Rotate to new key
        import base64
        old_encrypted_b64 = base64.b64encode(old_encrypted.encode()).decode()
        new_encrypted_b64 = EncryptionService.rotate_key(
            old_key,
            new_key,
            old_encrypted_b64
        )

        # Decrypt with new key
        new_fernet = Fernet(new_key.encode())
        new_encrypted_bytes = base64.b64decode(new_encrypted_b64.encode())
        decrypted = new_fernet.decrypt(new_encrypted_bytes).decode()

        assert decrypted == plaintext

    def test_encrypt_decrypt_special_characters(self):
        """Test encrypting special characters."""
        plaintext = "!@#$%^&*(){}[]|\\:;\"'<>,.?/"

        encrypted = EncryptionService.encrypt(plaintext)
        decrypted = EncryptionService.decrypt(encrypted)

        assert decrypted == plaintext

    def test_encrypt_decrypt_multiline(self):
        """Test encrypting multiline text."""
        plaintext = """Line 1
        Line 2
        Line 3
        """

        encrypted = EncryptionService.encrypt(plaintext)
        decrypted = EncryptionService.decrypt(encrypted)

        assert decrypted == plaintext

    def test_different_plaintexts_different_ciphertexts(self):
        """Test that different plaintexts produce different ciphertexts."""
        encrypted1 = EncryptionService.encrypt("Text 1")
        encrypted2 = EncryptionService.encrypt("Text 2")

        assert encrypted1 != encrypted2

    def test_same_plaintext_different_ciphertexts(self):
        """Test that same plaintext produces different ciphertexts (due to IV)."""
        plaintext = "Same text"

        encrypted1 = EncryptionService.encrypt(plaintext)
        encrypted2 = EncryptionService.encrypt(plaintext)

        # Fernet uses random IV, so same plaintext = different ciphertext
        assert encrypted1 != encrypted2

        # But both decrypt to same plaintext
        assert EncryptionService.decrypt(encrypted1) == plaintext
        assert EncryptionService.decrypt(encrypted2) == plaintext


@pytest.mark.django_db
class TestEncryptedFields:
    """Test encrypted model fields."""

    def test_encrypted_char_field_save_load(self, db):
        """Test EncryptedCharField saves and loads correctly."""
        from django.db import models
        from core.encryption.fields import EncryptedCharField

        # Create a test model
        class TestModel(models.Model):
            encrypted_field = EncryptedCharField(max_length=100)

            class Meta:
                app_label = 'test'

        # Can't actually create table in this test, but we can test field behavior
        field = TestModel._meta.get_field('encrypted_field')

        plaintext = "Sensitive data"
        encrypted = field.get_prep_value(plaintext)

        # Should be encrypted
        assert encrypted != plaintext
        assert len(encrypted) > len(plaintext)

        # Decrypt manually to verify
        decrypted = EncryptionService.decrypt(encrypted)
        assert decrypted == plaintext

    def test_encrypted_text_field_save_load(self, db):
        """Test EncryptedTextField saves and loads correctly."""
        from django.db import models
        from core.encryption.fields import EncryptedTextField

        # Create a test model
        class TestModel(models.Model):
            encrypted_field = EncryptedTextField()

            class Meta:
                app_label = 'test'

        field = TestModel._meta.get_field('encrypted_field')

        plaintext = "Long sensitive text\nWith multiple lines"
        encrypted = field.get_prep_value(plaintext)

        # Should be encrypted
        assert encrypted != plaintext

        # Decrypt manually to verify
        decrypted = EncryptionService.decrypt(encrypted)
        assert decrypted == plaintext

    def test_encrypted_field_none_value(self, db):
        """Test encrypted field with None value."""
        from django.db import models
        from core.encryption.fields import EncryptedCharField

        class TestModel(models.Model):
            encrypted_field = EncryptedCharField(max_length=100)

            class Meta:
                app_label = 'test'

        field = TestModel._meta.get_field('encrypted_field')

        # None should stay None
        assert field.get_prep_value(None) is None

    def test_encrypted_field_empty_string(self, db):
        """Test encrypted field with empty string."""
        from django.db import models
        from core.encryption.fields import EncryptedCharField

        class TestModel(models.Model):
            encrypted_field = EncryptedCharField(max_length=100)

            class Meta:
                app_label = 'test'

        field = TestModel._meta.get_field('encrypted_field')

        # Empty string should stay empty
        assert field.get_prep_value("") == ""

    def test_encrypted_email_field(self, db):
        """Test EncryptedEmailField."""
        from django.db import models
        from core.encryption.fields import EncryptedEmailField

        class TestModel(models.Model):
            encrypted_email = EncryptedEmailField()

            class Meta:
                app_label = 'test'

        field = TestModel._meta.get_field('encrypted_email')

        plaintext = "test@example.com"
        encrypted = field.get_prep_value(plaintext)

        # Should be encrypted
        assert encrypted != plaintext

        # Decrypt manually to verify
        decrypted = EncryptionService.decrypt(encrypted)
        assert decrypted == plaintext
