"""
Tests for NIST password validators.
"""

import pytest
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from unittest.mock import patch

from accounts.security.validators import (
    NISTMinimumLengthValidator,
    NISTMaximumLengthValidator,
    BreachedPasswordValidator,
    NISTCommonPasswordValidator,
    NISTUserAttributeSimilarityValidator,
)


class TestNISTMinimumLengthValidator:
    """Test NIST minimum length validator."""

    def test_valid_password(self):
        """Test password that meets minimum length."""
        validator = NISTMinimumLengthValidator(min_length=8)

        # Should not raise
        validator.validate("12345678")
        validator.validate("verylongpassword")

    def test_invalid_password_too_short(self):
        """Test password that's too short."""
        validator = NISTMinimumLengthValidator(min_length=8)

        with pytest.raises(ValidationError) as exc:
            validator.validate("short")

        assert "at least 8 characters" in str(exc.value)

    def test_custom_min_length(self):
        """Test custom minimum length."""
        validator = NISTMinimumLengthValidator(min_length=12)

        with pytest.raises(ValidationError):
            validator.validate("only10chars")

        # Should not raise
        validator.validate("exactly12chr")

    def test_help_text(self):
        """Test help text."""
        validator = NISTMinimumLengthValidator(min_length=8)
        help_text = validator.get_help_text()

        assert "8 characters" in help_text


class TestNISTMaximumLengthValidator:
    """Test NIST maximum length validator."""

    def test_valid_password(self):
        """Test password within maximum length."""
        validator = NISTMaximumLengthValidator(max_length=128)

        # Should not raise
        validator.validate("short")
        validator.validate("a" * 128)

    def test_invalid_password_too_long(self):
        """Test password that's too long."""
        validator = NISTMaximumLengthValidator(max_length=128)

        with pytest.raises(ValidationError) as exc:
            validator.validate("a" * 129)

        assert "must not exceed 128 characters" in str(exc.value)

    def test_help_text(self):
        """Test help text."""
        validator = NISTMaximumLengthValidator(max_length=128)
        help_text = validator.get_help_text()

        assert "128 characters" in help_text


class TestBreachedPasswordValidator:
    """Test breached password validator."""

    @patch('accounts.security.validators.PasswordBreachService.check_password')
    def test_valid_password_not_breached(self, mock_check):
        """Test password that hasn't been breached."""
        mock_check.return_value = (False, 0)
        validator = BreachedPasswordValidator()

        # Should not raise
        validator.validate("uniquepassword123")

    @patch('accounts.security.validators.PasswordBreachService.check_password')
    def test_invalid_password_breached(self, mock_check):
        """Test password that has been breached."""
        mock_check.return_value = (True, 5000)
        validator = BreachedPasswordValidator()

        with pytest.raises(ValidationError) as exc:
            validator.validate("password")

        assert "data breach" in str(exc.value).lower()

    @patch('accounts.security.validators.PasswordBreachService.check_password')
    def test_api_failure_allows_password(self, mock_check):
        """Test that API failure doesn't block password."""
        mock_check.return_value = (False, None)  # API failed
        validator = BreachedPasswordValidator()

        # Should not raise (fail open)
        validator.validate("password")

    def test_help_text(self):
        """Test help text."""
        validator = BreachedPasswordValidator()
        help_text = validator.get_help_text()

        assert "compromised" in help_text.lower()
        assert "data breach" in help_text.lower()


class TestNISTCommonPasswordValidator:
    """Test NIST common password validator."""

    def test_invalid_common_password(self):
        """Test common passwords are rejected."""
        validator = NISTCommonPasswordValidator()

        # Django's common password list includes these
        common_passwords = ["password", "123456", "qwerty"]

        for password in common_passwords:
            with pytest.raises(ValidationError):
                validator.validate(password)

    def test_valid_uncommon_password(self):
        """Test uncommon passwords are accepted."""
        validator = NISTCommonPasswordValidator()

        # Should not raise
        validator.validate("veryuncommonpassphrase2024!")

    def test_help_text(self):
        """Test help text."""
        validator = NISTCommonPasswordValidator()
        help_text = validator.get_help_text()

        assert "commonly used" in help_text.lower()


@pytest.mark.django_db
class TestNISTUserAttributeSimilarityValidator:
    """Test NIST user attribute similarity validator."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username="johndoe",
            email="john.doe@example.com",
            password="testpass123",
            first_name="John",
            last_name="Doe"
        )

    def test_valid_password_not_similar(self, user):
        """Test password not similar to user attributes."""
        validator = NISTUserAttributeSimilarityValidator()

        # Should not raise
        validator.validate("CompletelyUnrelatedPassword123!", user)

    def test_invalid_password_contains_username(self, user):
        """Test password containing username."""
        validator = NISTUserAttributeSimilarityValidator()

        with pytest.raises(ValidationError) as exc:
            validator.validate("johndoe123", user)

        assert "username" in str(exc.value).lower()

    def test_invalid_password_contains_email(self, user):
        """Test password containing email."""
        validator = NISTUserAttributeSimilarityValidator()

        with pytest.raises(ValidationError) as exc:
            validator.validate("john.doe@example.com", user)

        assert "email" in str(exc.value).lower()

    def test_invalid_password_contains_first_name(self, user):
        """Test password containing first name."""
        validator = NISTUserAttributeSimilarityValidator()

        with pytest.raises(ValidationError) as exc:
            validator.validate("JohnPassword123", user)

        assert "first" in str(exc.value).lower()

    def test_invalid_password_contains_last_name(self, user):
        """Test password containing last name."""
        validator = NISTUserAttributeSimilarityValidator()

        with pytest.raises(ValidationError) as exc:
            validator.validate("DoePassword123", user)

        assert "last" in str(exc.value).lower()

    def test_invalid_password_too_similar(self, user):
        """Test password too similar to username."""
        validator = NISTUserAttributeSimilarityValidator(max_similarity=0.7)

        with pytest.raises(ValidationError):
            validator.validate("johndoee", user)  # Very similar to "johndoe"

    def test_no_user_allows_password(self):
        """Test validation passes when no user provided."""
        validator = NISTUserAttributeSimilarityValidator()

        # Should not raise
        validator.validate("anypassword", user=None)

    def test_custom_attributes(self, user):
        """Test custom attribute list."""
        validator = NISTUserAttributeSimilarityValidator(
            user_attributes=("username",)  # Only check username
        )

        # Should raise for username
        with pytest.raises(ValidationError):
            validator.validate("johndoe123", user)

        # Should NOT raise for first name (not in checked attributes)
        validator.validate("JohnPassword", user)

    def test_help_text(self):
        """Test help text."""
        validator = NISTUserAttributeSimilarityValidator()
        help_text = validator.get_help_text()

        assert "personal information" in help_text.lower()
