"""
Password breach checking service using HaveIBeenPwned API.

Uses k-anonymity model to check passwords without sending full password hashes.
"""

import hashlib
import logging
from typing import Optional

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class PasswordBreachService:
    """
    Service for checking if passwords have been breached using HaveIBeenPwned API.

    Uses k-anonymity model: only sends first 5 characters of SHA-1 hash to API.
    """

    API_URL = "https://api.pwnedpasswords.com/range/"
    TIMEOUT = 5  # seconds
    ENABLED = getattr(settings, "PASSWORD_BREACH_CHECK_ENABLED", True)

    @classmethod
    def check_password(cls, password: str) -> tuple[bool, Optional[int]]:
        """
        Check if a password has been breached.

        Args:
            password: Plain text password to check

        Returns:
            Tuple of (is_breached: bool, breach_count: int or None)
            breach_count is None if check failed or is disabled
        """
        if not cls.ENABLED:
            return False, None

        try:
            # Generate SHA-1 hash of password
            # Note: SHA1 is required by HaveIBeenPwned API, not used for security
            password_hash = hashlib.sha1(
                password.encode("utf-8"), usedforsecurity=False
            ).hexdigest().upper()

            # Split hash: first 5 chars (prefix) and remaining (suffix)
            hash_prefix = password_hash[:5]
            hash_suffix = password_hash[5:]

            # Query API with prefix only (k-anonymity model)
            response = requests.get(
                f"{cls.API_URL}{hash_prefix}",
                timeout=cls.TIMEOUT,
                headers={"User-Agent": "Biashara Bridges Security Check"},
            )

            if response.status_code != 200:
                logger.warning(
                    f"HaveIBeenPwned API returned status {response.status_code}"
                )
                return False, None

            # Parse response to find matching suffix
            hashes = response.text.splitlines()
            for line in hashes:
                # Format: SUFFIX:COUNT
                hash_part, count_str = line.split(":")
                if hash_part == hash_suffix:
                    breach_count = int(count_str)
                    logger.info(
                        f"Password found in {breach_count} breaches (hash prefix: {hash_prefix})"
                    )
                    return True, breach_count

            # Password not found in breaches
            return False, 0

        except requests.exceptions.Timeout:
            logger.warning("HaveIBeenPwned API timeout")
            return False, None
        except requests.exceptions.RequestException as e:
            logger.error(f"HaveIBeenPwned API error: {e}")
            return False, None
        except Exception as e:
            logger.error(f"Unexpected error checking password breach: {e}")
            return False, None

    @classmethod
    def get_breach_message(cls, breach_count: int) -> str:
        """
        Get user-friendly message for breached password.

        Args:
            breach_count: Number of times password appears in breaches

        Returns:
            User-friendly error message
        """
        if breach_count == 0:
            return "This password is secure and has not been found in any known data breaches."

        if breach_count < 10:
            return (
                f"This password has been found in {breach_count} data breach(es). "
                "Please choose a different password."
            )

        if breach_count < 100:
            return (
                f"This password has been found in {breach_count} data breaches. "
                "This is a commonly compromised password. Please choose a different password."
            )

        if breach_count < 1000:
            return (
                f"This password has been found in {breach_count} data breaches. "
                "This is a very common password. Please choose a different password."
            )

        return (
            f"This password has been found in {breach_count} data breaches. "
            "This is an extremely common password. Please choose a different password."
        )
