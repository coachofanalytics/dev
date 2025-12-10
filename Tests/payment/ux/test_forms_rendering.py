from django.test import TestCase
from django.template import Context, Template
from payments.forms import DepositForm, MPesaDepositForm


class TestPaymentFormsRendering(TestCase):
    """
    Basic UI/UX smoke tests to ensure templates/forms render required fields
    and placeholder/help text are present for clarity.
    """

    def test_deposit_form_contains_payment_method_choices(self):
        form = DepositForm()
        html = form.as_p()
        self.assertIn('payment_gateway', html)

    def test_mpesa_help_text_and_placeholder(self):
        form = MPesaDepositForm()
        html = form.as_p()
        self.assertIn('M-Pesa Phone Number', html)
        self.assertIn('placeholder', html)
