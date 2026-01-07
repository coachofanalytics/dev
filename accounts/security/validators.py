"""
NIST 800-63B compliant password validators.

Implements password validation according to NIST Special Publication 800-63B:
- Minimum length of 8 characters
- Maximum length of 64 characters (or more)
- Check against breached password databases
- No composition rules (e.g., requiring uppercase, numbers, symbols)
- No password hints
- No knowledge-based authentication
"""

import logging
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from accounts.security.services import PasswordBreachService

logger = logging.getLogger(__name__)


class NISTMinimumLengthValidator:
    """
    Validate password has minimum length of 8 characters (NIST requirement).
    """

    def __init__(self, min_length=8):
        """
        Initialize validator.

        Args:
            min_length: Minimum password length (default: 8)
        """
        self.min_length = min_length

    def validate(self, password, user=None):
        """
        Validate password length.

        Args:
            password: Password to validate
            user: User object (unused)

        Raises:
            ValidationError: If password is too short
        """
        if len(password) < self.min_length:
            raise ValidationError(
                _(f"Password must be at least {self.min_length} characters long."),
                code="password_too_short",
                params={"min_length": self.min_length},
            )

    def get_help_text(self):
        """Get help text for this validator."""
        return _(f"Your password must contain at least {self.min_length} characters.")


class NISTMaximumLengthValidator:
    """
    Validate password doesn't exceed maximum length (NIST recommends at least 64).
    """

    def __init__(self, max_length=128):
        """
        Initialize validator.

        Args:
            max_length: Maximum password length (default: 128)
        """
        self.max_length = max_length

    def validate(self, password, user=None):
        """
        Validate password length.

        Args:
            password: Password to validate
            user: User object (unused)

        Raises:
            ValidationError: If password is too long
        """
        if len(password) > self.max_length:
            raise ValidationError(
                _(f"Password must not exceed {self.max_length} characters."),
                code="password_too_long",
                params={"max_length": self.max_length},
            )

    def get_help_text(self):
        """Get help text for this validator."""
        return _(f"Your password must not exceed {self.max_length} characters.")


class BreachedPasswordValidator:
    """
    Validate password against HaveIBeenPwned database.

    Uses k-anonymity model for privacy.
    """

    def validate(self, password, user=None):
        """
        Validate password is not breached.

        Args:
            password: Password to validate
            user: User object (unused)

        Raises:
            ValidationError: If password has been breached
        """
        is_breached, breach_count = PasswordBreachService.check_password(password)

        if is_breached and breach_count and breach_count > 0:
            message = PasswordBreachService.get_breach_message(breach_count)
            raise ValidationError(
                _(message),
                code="password_breached",
                params={"breach_count": breach_count},
            )

    def get_help_text(self):
        """Get help text for this validator."""
        return _(
            "Your password must not have been compromised in a known data breach."
        )


class NISTCommonPasswordValidator:
    """
    Validate password is not a commonly used password.

    Note: This validator uses Django's built-in common password list.
    For production, consider using a more comprehensive list.
    """

    def __init__(self, password_list_path=None):
        """
        Initialize validator.

        Args:
            password_list_path: Optional path to custom password list
        """
        from django.contrib.auth.password_validation import (
            CommonPasswordValidator as DjangoCommonPasswordValidator,
        )

        if password_list_path:
            self.django_validator = DjangoCommonPasswordValidator(
                password_list_path=password_list_path
            )
        else:
            # Use default (no password_list_path argument)
            self.django_validator = DjangoCommonPasswordValidator()

    def validate(self, password, user=None):
        """
        Validate password is not common.

        Args:
            password: Password to validate
            user: User object (passed to Django validator)

        Raises:
            ValidationError: If password is too common
        """
        self.django_validator.validate(password, user)

    def get_help_text(self):
        """Get help text for this validator."""
        return _("Your password must not be a commonly used password.")


class NISTUserAttributeSimilarityValidator:
    """
    Validate password is not too similar to user attributes.

    Checks against username, email, first name, and last name.
    """

    def __init__(self, user_attributes=("username", "email", "first_name", "last_name"), max_similarity=0.7):
        """
        Initialize validator.

        Args:
            user_attributes: Tuple of user attributes to check
            max_similarity: Maximum allowed similarity ratio (0.0 - 1.0)
        """
        self.user_attributes = user_attributes
        self.max_similarity = max_similarity

    def validate(self, password, user=None):
        """
        Validate password similarity to user attributes.

        Args:
            password: Password to validate
            user: User object

        Raises:
            ValidationError: If password is too similar to user attributes
        """
        if not user:
            return

        from difflib import SequenceMatcher

        password_lower = password.lower()

        for attribute_name in self.user_attributes:
            value = getattr(user, attribute_name, None)
            if not value:
                continue

            value_lower = value.lower()

            # Check if password contains the attribute or vice versa
            if value_lower in password_lower or password_lower in value_lower:
                raise ValidationError(
                    _(
                        f"Password is too similar to your {attribute_name.replace('_', ' ')}."
                    ),
                    code="password_too_similar",
                    params={"verbose_name": attribute_name},
                )

            # Check similarity ratio
            similarity = SequenceMatcher(a=password_lower, b=value_lower).ratio()
            if similarity >= self.max_similarity:
                raise ValidationError(
                    _(
                        f"Password is too similar to your {attribute_name.replace('_', ' ')}."
                    ),
                    code="password_too_similar",
                    params={"verbose_name": attribute_name},
                )

    def get_help_text(self):
        """Get help text for this validator."""
        return _(
            "Your password must not be too similar to your personal information."
        )
