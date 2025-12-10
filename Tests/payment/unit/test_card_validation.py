"""
Unit tests for card number, CVV, and expiry validation.

These tests include a small Luhn implementation, CVV checks, and expiry
validation logic used to verify common card input validation rules. They are
intended to be deterministic unit tests that do not call external services.
"""
from datetime import datetime
import unittest


def luhn_checksum(card_number: str) -> bool:
    """Return True if `card_number` passes the Luhn checksum."""
    digits = [int(ch) for ch in card_number if ch.isdigit()]
    if not digits:
        return False
    checksum = 0
    parity = len(digits) % 2

    for i, digit in enumerate(digits):
        if i % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit

    return checksum % 10 == 0


def valid_cvv(cvv: str) -> bool:
    """Return True for valid CVV strings (3 or 4 digits)."""
    return cvv.isdigit() and len(cvv) in (3, 4)


def expiry_not_passed(month: int, year: int) -> bool:
    """Return True if the expiry `month`/`year` is in the future (not expired).

    Year may be provided as two-digit (YY) or four-digit (YYYY). This helper
    normalizes both forms and compares against the current month.
    """
    if year < 100:
        # assume 2000-2099 for two-digit years
        year += 2000

    now = datetime.utcnow()
    # Card expires at the end of the month, so compare using year, month
    return (year, month) >= (now.year, now.month)


class CardValidationTests(unittest.TestCase):
    """Test Luhn, CVV and expiry validation behaviour."""

    def test_luhn_valid_numbers(self):
        """Known valid card numbers should pass the Luhn checksum."""
        valid_numbers = [
            '4242424242424242',  # Stripe Visa test
            '4012888888881881',  # Visa
            '5555555555554444',  # MasterCard
            '6011111111111117',  # Discover
        ]

        for num in valid_numbers:
            with self.subTest(num=num):
                self.assertTrue(luhn_checksum(num))

    def test_luhn_invalid_numbers(self):
        """Malformed or wrong numbers should fail Luhn checks."""
        invalid_numbers = [
            '',
            '4242424242424241',
            '1234567890123456',
        ]

        for num in invalid_numbers:
            with self.subTest(num=num):
                self.assertFalse(luhn_checksum(num))

    def test_cvv_validation(self):
        """CVV should be numeric and length 3 or 4."""
        self.assertTrue(valid_cvv('123'))
        self.assertTrue(valid_cvv('1234'))
        self.assertFalse(valid_cvv('12'))
        self.assertFalse(valid_cvv('abcd'))
        self.assertFalse(valid_cvv('12a'))

    def test_expiry_validation_future_and_past(self):
        """Expiry validation accepts future months and rejects past months."""
        now = datetime.utcnow()
        # Current month should be valid (cards expire at end of month)
        self.assertTrue(expiry_not_passed(now.month, now.year))

        # Next month is valid
        next_month = now.month + 1
        next_year = now.year
        if next_month > 12:
            next_month = 1
            next_year += 1

        self.assertTrue(expiry_not_passed(next_month, next_year))

        # Last month should be invalid
        prev_month = now.month - 1
        prev_year = now.year
        if prev_month < 1:
            prev_month = 12
            prev_year -= 1

        self.assertFalse(expiry_not_passed(prev_month, prev_year))


if __name__ == '__main__':
    unittest.main()
