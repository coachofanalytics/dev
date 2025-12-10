import os
from django.test import TestCase
try:
    import paypalrestsdk
except Exception:
    paypalrestsdk = None


class TestPaypalIntegration(TestCase):
    """
    Integration tests for PayPal sandbox. Requires `PAYPAL_CLIENT_ID` and
    `PAYPAL_CLIENT_SECRET` to be set in the environment. Tests will be skipped
    if the SDK or credentials are not present.
    """

    def setUp(self):
        self.client_id = os.environ.get('PAYPAL_CLIENT_ID')
        self.client_secret = os.environ.get('PAYPAL_CLIENT_SECRET')
        if paypalrestsdk and self.client_id and self.client_secret:
            paypalrestsdk.configure({
                'mode': 'sandbox',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
            })

    def test_create_payment(self):
        if not paypalrestsdk or not (self.client_id and self.client_secret):
            self.skipTest('PayPal SDK or credentials missing; skipping integration test')

        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {"payment_method": "paypal"},
            "transactions": [{"amount": {"total": "1.00", "currency": "USD"}, "description": "Test payment"}],
            "redirect_urls": {"return_url": "http://localhost/return", "cancel_url": "http://localhost/cancel"}
        })

        created = payment.create()
        self.assertTrue(created)
        self.assertIsNotNone(payment.id)
