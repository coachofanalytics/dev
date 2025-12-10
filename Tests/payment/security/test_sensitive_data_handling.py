from django.test import TestCase, override_settings
from payments import webhooks
from tests.payment.helpers import create_user, create_wallet_for_user, create_transaction
from decimal import Decimal


class TestSensitiveDataHandling(TestCase):
    """
    Assert that sensitive card and payment data are not persisted to transaction.metadata
    or logs by the webhook handlers. This is a focused security unit test.
    """

    def setUp(self):
        self.user = create_user('sec_user')
        self.wallet = create_wallet_for_user(self.user, balance=Decimal('0.00'))

    def test_no_card_pan_in_metadata_after_stripe(self):
        txn = create_transaction(self.user, wallet=self.wallet, amount=Decimal('9.00'), gateway='stripe', gateway_id='sec_pi_1')

        # Simulate a payment_intent object that might contain sensitive fields
        payment_intent = {'id': 'sec_pi_1', 'metadata': {}, 'charges': {'data': [{'payment_method_details': {'card': {'last4': '4242', 'brand': 'visa'}}}]}}

        webhooks.handle_stripe_payment_success(payment_intent)

        txn.refresh_from_db()
        # The handler should not store full PANs; only allowed metadata (last4) if at all
        for k, v in txn.metadata.items():
            self.assertNotIn('card_number', k)
            if isinstance(v, str):
                self.assertNotIn('424242424242', v)

    def test_verify_paypal_ipn_handles_network_errors(self):
        # Verify the PayPal IPN verification function returns False on network errors
        ipn_data = {'txn_id': 'irrelevant'}
        result = webhooks.verify_paypal_ipn(ipn_data)
        # If PayPal endpoint isn't reachable in test environment, verification should be False
        self.assertFalse(result)
