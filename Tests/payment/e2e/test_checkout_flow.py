from django.test import TestCase, Client
from tests.payment.helpers import create_user, create_wallet_for_user, create_invoice, create_transaction
from payments import webhooks
from decimal import Decimal


class TestCheckoutDepositFlow(TestCase):
    """
    E2E-like tests emulating a user deposit checkout flow.

    Scenario:
    - Create user, wallet and invoice (cart)
    - Create a pending transaction for the gateway
    - Simulate gateway webhook calling our handler
    - Assert the invoice is marked paid, wallet credited and transaction completed
    """

    def setUp(self):
        self.client = Client()
        self.user = create_user('e2e_user')
        self.wallet = create_wallet_for_user(self.user, balance=Decimal('0.00'))

    def test_deposit_flow_stripe(self):
        invoice = create_invoice(self.user, amount=Decimal('12.00'))
        txn = create_transaction(self.user, wallet=self.wallet, invoice=invoice, amount=Decimal('12.00'), gateway='stripe', gateway_id='e2e_pi_1')

        # Simulate Stripe webhook that signals success
        payment_intent = {'id': 'e2e_pi_1', 'metadata': {}, 'amount': 1200}
        webhooks.handle_stripe_payment_success(payment_intent)

        invoice.refresh_from_db()
        txn.refresh_from_db()
        self.wallet.refresh_from_db()

        self.assertEqual(invoice.status, 'paid')
        self.assertEqual(txn.status, 'completed')
        self.assertEqual(self.wallet.balance, Decimal('12.00'))

    def test_deposit_flow_mpesa(self):
        invoice = create_invoice(self.user, amount=Decimal('7.00'))
        txn = create_transaction(self.user, wallet=self.wallet, invoice=invoice, amount=Decimal('7.00'), gateway='mpesa', gateway_id='e2e_stk_1')

        webhooks.handle_mpesa_payment_success('e2e_stk_1', Decimal('7.00'), 'RCPT_E2E_1', '254712345678')

        invoice.refresh_from_db()
        txn.refresh_from_db()
        self.wallet.refresh_from_db()

        self.assertEqual(invoice.status, 'paid')
        self.assertEqual(txn.status, 'completed')
        self.assertEqual(self.wallet.balance, Decimal('7.00'))
