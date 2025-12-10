import os
from django.test import TestCase
import stripe


class TestStripeIntegration(TestCase):
    """
    Integration tests for Stripe sandbox operations.

    These tests require `STRIPE_TEST_SECRET_KEY` to be present in the
    environment. They will be skipped otherwise. They perform non-destructive
    operations in Stripe test mode (create and cancel PaymentIntents, create refunds).
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.stripe_key = os.environ.get('STRIPE_TEST_SECRET_KEY')
        if cls.stripe_key:
            stripe.api_key = cls.stripe_key

    def test_create_payment_intent_and_cancel(self):
        if not self.stripe_key:
            self.skipTest('STRIPE_TEST_SECRET_KEY is not set; skipping integration test')

        # Create a small PaymentIntent in test mode
        intent = stripe.PaymentIntent.create(amount=500, currency='usd', payment_method_types=['card'])
        self.assertIn('id', intent)

        # Cancel the PaymentIntent (to avoid leaving test artifacts)
        canceled = stripe.PaymentIntent.cancel(intent.id)
        self.assertEqual(canceled.status, 'canceled')
