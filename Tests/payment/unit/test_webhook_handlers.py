from django.test import TestCase
from django.contrib.auth.models import User
from payments import webhooks
from payments.models import Transaction, Wallet
from tests.payment.helpers import create_user, create_wallet_for_user, create_transaction
from decimal import Decimal


class TestStripeWebhookHandlers(TestCase):
    """
    Unit tests for Stripe webhook handler functions.

    These tests do not contact Stripe; they directly call the handler
    functions with simulated payload objects. They assert correct
    transaction state transitions and wallet crediting.
    """

    def setUp(self):
        self.user = create_user('stripe_user')
        self.wallet = create_wallet_for_user(self.user, balance=Decimal('0.00'))

    def test_handle_stripe_payment_success(self):
        # Create pending transaction that matches the mocked gateway id
        txn = create_transaction(self.user, wallet=self.wallet, amount=Decimal('10.00'), gateway='stripe', gateway_id='pi_test_123')

        # Simulate a Stripe PaymentIntent object as received in webhook
        payment_intent = {'id': 'pi_test_123', 'metadata': {}, 'amount': 1000}

        webhooks.handle_stripe_payment_success(payment_intent)

        txn.refresh_from_db()
        self.wallet.refresh_from_db()

        self.assertEqual(txn.status, 'completed')
        self.assertEqual(self.wallet.balance, Decimal('10.00'))

    def test_handle_stripe_payment_failed(self):
        txn = create_transaction(self.user, wallet=self.wallet, amount=Decimal('5.00'), gateway='stripe', gateway_id='pi_failed_1')
        payment_intent = {'id': 'pi_failed_1', 'last_payment_error': {'message': 'card_declined'}}

        webhooks.handle_stripe_payment_failed(payment_intent)

        txn.refresh_from_db()
        self.assertEqual(txn.status, 'failed')

    def test_handle_stripe_refund(self):
        # Create original transaction
        original = create_transaction(self.user, wallet=self.wallet, amount=Decimal('20.00'), gateway='stripe', gateway_id='ch_123')

        # Simulate charge dict with amount_refunded in cents
        charge = {'id': 'ch_123', 'amount_refunded': 5000}

        webhooks.handle_stripe_refund(charge)

        original.refresh_from_db()
        self.assertEqual(original.status, 'refunded')


class TestMpesaWebhookHandlers(TestCase):
    """Unit tests for M-Pesa webhook handlers (callbacks)."""

    def setUp(self):
        self.user = create_user('mpesa_user')
        self.wallet = create_wallet_for_user(self.user, balance=Decimal('0.00'))

    def test_handle_mpesa_payment_success(self):
        txn = create_transaction(self.user, wallet=self.wallet, amount=Decimal('15.00'), gateway='mpesa', gateway_id='stk_abc')

        webhooks.handle_mpesa_payment_success('stk_abc', Decimal('15.00'), 'RCPT123', '254712345678')

        txn.refresh_from_db()
        self.wallet.refresh_from_db()

        self.assertEqual(txn.status, 'completed')
        self.assertEqual(self.wallet.balance, Decimal('15.00'))

    def test_handle_mpesa_payment_failed(self):
        txn = create_transaction(self.user, wallet=self.wallet, amount=Decimal('10.00'), gateway='mpesa', gateway_id='stk_fail')
        webhooks.handle_mpesa_payment_failed('stk_fail', 1, 'User cancelled')

        txn.refresh_from_db()
        self.assertEqual(txn.status, 'failed')


class TestPaypalWebhookHandlers(TestCase):
    """Unit tests for PayPal IPN handler functions."""

    def setUp(self):
        self.user = create_user('pp_user')
        self.wallet = create_wallet_for_user(self.user, balance=Decimal('0.00'))

    def test_handle_paypal_payment_success(self):
        txn = create_transaction(self.user, wallet=self.wallet, amount=Decimal('8.00'), gateway='paypal', gateway_id='txn_pp_1')
        ipn_data = {'txn_id': 'txn_pp_1', 'mc_gross': '8.00', 'payer_email': 'payer@example.com'}

        webhooks.handle_paypal_payment_success(ipn_data)

        txn.refresh_from_db()
        self.wallet.refresh_from_db()

        self.assertEqual(txn.status, 'completed')
        self.assertEqual(self.wallet.balance, Decimal('8.00'))
