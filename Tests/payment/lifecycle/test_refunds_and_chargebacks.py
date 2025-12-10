from django.test import TestCase
from tests.payment.helpers import create_user, create_wallet_for_user, create_transaction
from payments import webhooks
from decimal import Decimal


class TestRefundsLifecycle(TestCase):
    """
    Tests simulating refunds and lifecycle transitions for transactions.
    """

    def setUp(self):
        self.user = create_user('life_user')
        self.wallet = create_wallet_for_user(self.user, balance=Decimal('0.00'))

    def test_paypal_refund_creates_refund_transaction(self):
        original = create_transaction(self.user, wallet=self.wallet, amount=Decimal('30.00'), gateway='paypal', gateway_id='pp_txn_1', status='completed')
        ipn_data = {'txn_id': 'pp_txn_refund', 'parent_txn_id': 'pp_txn_1', 'mc_gross': '-30.00'}

        webhooks.handle_paypal_refund(ipn_data)

        original.refresh_from_db()
        self.assertEqual(original.status, 'refunded')

    def test_stripe_refund_marks_original_and_credits_wallet(self):
        original = create_transaction(self.user, wallet=self.wallet, amount=Decimal('25.00'), gateway='stripe', gateway_id='ch_rep_1', status='completed')
        charge = {'id': 'ch_rep_1', 'amount_refunded': 2500}

        webhooks.handle_stripe_refund(charge)

        original.refresh_from_db()
        self.wallet.refresh_from_db()

        self.assertEqual(original.status, 'refunded')
        self.assertEqual(self.wallet.balance, Decimal('25.00'))
