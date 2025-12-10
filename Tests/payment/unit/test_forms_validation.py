from django.test import TestCase
from payments.forms import MPesaDepositForm, DepositForm
from decimal import Decimal


class TestMPesaDepositFormValidation(TestCase):
    """
    Unit tests for `MPesaDepositForm` phone number validation.

    These tests exercise both valid and invalid phone-number inputs and
    assert that the form raises ValidationError for incorrect formats.
    """

    def test_valid_phone_numbers(self):
        valid = [
            {'phone_number': '254712345678'},
            {'phone_number': '0712345678'},
            {'phone_number': '254 712 345 678'},
            {'phone_number': '0712-345-678'},
        ]
        for data in valid:
            form = MPesaDepositForm(data=data)
            self.assertTrue(form.is_valid(), f"Should be valid: {data}")

    def test_invalid_phone_numbers(self):
        invalid = [
            {'phone_number': '12345'},
            {'phone_number': '999712345678'},
            {'phone_number': '+254712345678'},
        ]
        for data in invalid:
            form = MPesaDepositForm(data=data)
            self.assertFalse(form.is_valid(), f"Should be invalid: {data}")


class TestDepositFormValidation(TestCase):
    """Unit tests for `DepositForm` amount boundaries and choices."""

    def test_amount_within_bounds(self):
        # Use the minimum and maximum from settings indirectly - test typical values
        form = DepositForm(data={'amount': Decimal('5.00'), 'payment_gateway': 'stripe'})
        self.assertTrue(form.is_valid())

    def test_amount_below_minimum(self):
        form = DepositForm(data={'amount': Decimal('0.01'), 'payment_gateway': 'stripe'})
        self.assertFalse(form.is_valid())
