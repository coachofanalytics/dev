"""
Comprehensive tests for payment webhook handlers.

Tests Stripe, PayPal, M-Pesa, CashApp, and Venmo webhook handlers.
Covers signature validation, idempotency, error handling, and edge cases.
"""

import pytest
import json
import hmac
import hashlib
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, Client, RequestFactory, override_settings
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse

from payments.models import Transaction, Wallet, Invoice, UserSubscription, SubscriptionPlan
from payments.webhooks import (
    stripe_webhook,
    paypal_webhook,
    mpesa_webhook,
    cashapp_webhook,
    venmo_webhook,
    handle_stripe_payment_success,
    handle_stripe_payment_failed,
    handle_stripe_refund,
    handle_paypal_payment_success,
    handle_paypal_payment_failed,
    handle_paypal_refund,
    handle_mpesa_payment_success,
    handle_mpesa_payment_failed,
    verify_paypal_ipn,
)


@pytest.mark.django_db
class TestStripeWebhook:
    """Test suite for Stripe webhook handlers."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='webhook_user',
            email='webhook@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def wallet(self, user):
        """Create test wallet."""
        wallet, _ = Wallet.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('0.00')}
        )
        return wallet

    @pytest.fixture
    def transaction(self, user, wallet):
        """Create test pending transaction."""
        return Transaction.objects.create(
            user=user,
            wallet=wallet,
            transaction_type='deposit',
            amount=Decimal('100.00'),
            payment_gateway='stripe',
            gateway_transaction_id='pi_test_123',
            status='pending'
        )

    @pytest.fixture
    def client(self):
        """Create test client."""
        return Client()

    @pytest.fixture
    def request_factory(self):
        """Create request factory."""
        return RequestFactory()

    @patch('stripe.Webhook.construct_event')
    def test_stripe_webhook_valid_signature(self, mock_construct, client):
        """Test webhook with valid signature is processed."""
        mock_event = {
            'type': 'payment_intent.succeeded',
            'data': {
                'object': {
                    'id': 'pi_test_123',
                    'metadata': {}
                }
            }
        }
        mock_construct.return_value = mock_event

        response = client.post(
            '/payments/webhook/stripe/',
            data=json.dumps({}),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='test_sig'
        )

        # Should return 200 even if transaction not found
        assert response.status_code == 200

    @patch('stripe.Webhook.construct_event')
    def test_stripe_webhook_invalid_payload(self, mock_construct, client):
        """Test webhook with invalid payload returns 400."""
        mock_construct.side_effect = ValueError("Invalid payload")

        response = client.post(
            '/payments/webhook/stripe/',
            data=json.dumps({}),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='test_sig'
        )

        assert response.status_code == 400

    @patch('stripe.Webhook.construct_event')
    def test_stripe_webhook_invalid_signature(self, mock_construct, client):
        """Test webhook with invalid signature returns 400."""
        import stripe
        mock_construct.side_effect = stripe.error.SignatureVerificationError(
            "Invalid signature", sig_header='test'
        )

        response = client.post(
            '/payments/webhook/stripe/',
            data=json.dumps({}),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='invalid_sig'
        )

        assert response.status_code == 400

    def test_handle_stripe_payment_success_updates_transaction(self, user, wallet, transaction):
        """Test successful payment updates transaction status."""
        payment_intent = {
            'id': 'pi_test_123',
            'metadata': {}
        }

        handle_stripe_payment_success(payment_intent)

        transaction.refresh_from_db()
        assert transaction.status == 'completed'

    def test_handle_stripe_payment_success_credits_wallet(self, user, wallet, transaction):
        """Test successful payment credits wallet."""
        initial_balance = wallet.balance
        payment_intent = {
            'id': 'pi_test_123',
            'metadata': {}
        }

        handle_stripe_payment_success(payment_intent)

        wallet.refresh_from_db()
        assert wallet.balance == initial_balance + transaction.amount

    def test_handle_stripe_payment_success_idempotency(self, user, wallet, transaction):
        """Test idempotency - duplicate webhook doesn't double-credit."""
        transaction.status = 'completed'
        transaction.save()
        initial_balance = wallet.balance

        payment_intent = {
            'id': 'pi_test_123',
            'metadata': {}
        }

        handle_stripe_payment_success(payment_intent)

        wallet.refresh_from_db()
        assert wallet.balance == initial_balance  # No change

    def test_handle_stripe_payment_success_transaction_not_found(self):
        """Test handling of payment for non-existent transaction."""
        payment_intent = {
            'id': 'pi_nonexistent',
            'metadata': {}
        }

        # Should not raise exception
        handle_stripe_payment_success(payment_intent)

    def test_handle_stripe_payment_failed(self, user, wallet, transaction):
        """Test failed payment updates transaction status."""
        payment_intent = {
            'id': 'pi_test_123',
            'last_payment_error': {
                'message': 'Card declined'
            }
        }

        handle_stripe_payment_failed(payment_intent)

        transaction.refresh_from_db()
        assert transaction.status == 'failed'
        assert 'Card declined' in transaction.metadata.get('stripe_error', '')

    def test_handle_stripe_refund(self, user, wallet):
        """Test refund creates refund transaction and credits wallet."""
        # Create completed original transaction
        original_txn = Transaction.objects.create(
            user=user,
            wallet=wallet,
            transaction_type='deposit',
            amount=Decimal('100.00'),
            payment_gateway='stripe',
            gateway_transaction_id='ch_test_123',
            status='completed'
        )

        charge = {
            'id': 'ch_test_123',
            'amount_refunded': 10000,  # cents
        }

        handle_stripe_refund(charge)

        original_txn.refresh_from_db()
        assert original_txn.status == 'refunded'

        # Check refund transaction was created
        refund_txn = Transaction.objects.filter(
            gateway_transaction_id='ch_test_123_refund'
        ).first()
        assert refund_txn is not None
        assert refund_txn.transaction_type == 'refund'
        assert refund_txn.amount == Decimal('100.00')


@pytest.mark.django_db
class TestPayPalWebhook:
    """Test suite for PayPal webhook handlers."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='paypal_user',
            email='paypal@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def wallet(self, user):
        """Create test wallet."""
        wallet, _ = Wallet.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('0.00')}
        )
        return wallet

    @pytest.fixture
    def transaction(self, user, wallet):
        """Create test pending PayPal transaction."""
        return Transaction.objects.create(
            user=user,
            wallet=wallet,
            transaction_type='deposit',
            amount=Decimal('50.00'),
            payment_gateway='paypal',
            gateway_transaction_id='PAY-test123',
            status='pending'
        )

    @patch('payments.webhooks.verify_paypal_ipn')
    def test_paypal_webhook_valid_ipn(self, mock_verify, client):
        """Test PayPal webhook with valid IPN."""
        mock_verify.return_value = True

        response = client.post(
            '/payments/webhook/paypal/',
            data={
                'payment_status': 'Completed',
                'txn_id': 'PAY-test123',
                'mc_gross': '50.00',
            }
        )

        assert response.status_code == 200

    @patch('payments.webhooks.verify_paypal_ipn')
    def test_paypal_webhook_invalid_ipn(self, mock_verify, client):
        """Test PayPal webhook with invalid IPN verification."""
        mock_verify.return_value = False

        response = client.post(
            '/payments/webhook/paypal/',
            data={
                'payment_status': 'Completed',
                'txn_id': 'PAY-fake',
            }
        )

        assert response.status_code == 400

    @patch('requests.post')
    def test_verify_paypal_ipn_success(self, mock_post):
        """Test PayPal IPN verification success."""
        mock_response = MagicMock()
        mock_response.text = 'VERIFIED'
        mock_post.return_value = mock_response

        ipn_data = {
            'payment_status': 'Completed',
            'txn_id': 'test123',
        }

        result = verify_paypal_ipn(ipn_data)
        assert result is True

    @patch('requests.post')
    def test_verify_paypal_ipn_invalid(self, mock_post):
        """Test PayPal IPN verification failure."""
        mock_response = MagicMock()
        mock_response.text = 'INVALID'
        mock_post.return_value = mock_response

        ipn_data = {'payment_status': 'Completed'}
        result = verify_paypal_ipn(ipn_data)
        assert result is False

    @patch('requests.post')
    def test_verify_paypal_ipn_timeout(self, mock_post):
        """Test PayPal IPN verification timeout."""
        import requests
        mock_post.side_effect = requests.exceptions.Timeout()

        result = verify_paypal_ipn({})
        assert result is False

    def test_handle_paypal_payment_success(self, user, wallet, transaction):
        """Test successful PayPal payment updates transaction."""
        ipn_data = {
            'txn_id': 'PAY-test123',
            'mc_gross': '50.00',
            'payer_email': 'payer@example.com',
        }

        handle_paypal_payment_success(ipn_data)

        transaction.refresh_from_db()
        assert transaction.status == 'completed'

    def test_handle_paypal_payment_success_credits_wallet(self, user, wallet, transaction):
        """Test successful PayPal payment credits wallet."""
        initial_balance = wallet.balance

        ipn_data = {
            'txn_id': 'PAY-test123',
            'mc_gross': '50.00',
        }

        handle_paypal_payment_success(ipn_data)

        wallet.refresh_from_db()
        assert wallet.balance == initial_balance + Decimal('50.00')

    def test_handle_paypal_payment_success_idempotency(self, user, wallet, transaction):
        """Test PayPal idempotency - duplicate IPN doesn't double-credit."""
        transaction.status = 'completed'
        transaction.save()
        initial_balance = wallet.balance

        ipn_data = {'txn_id': 'PAY-test123', 'mc_gross': '50.00'}

        handle_paypal_payment_success(ipn_data)

        wallet.refresh_from_db()
        assert wallet.balance == initial_balance

    def test_handle_paypal_payment_failed(self, user, wallet, transaction):
        """Test failed PayPal payment updates transaction."""
        ipn_data = {
            'txn_id': 'PAY-test123',
            'reason_code': 'buyer_complaint',
        }

        handle_paypal_payment_failed(ipn_data)

        transaction.refresh_from_db()
        assert transaction.status == 'failed'

    def test_handle_paypal_refund(self, user, wallet):
        """Test PayPal refund handling."""
        original_txn = Transaction.objects.create(
            user=user,
            wallet=wallet,
            transaction_type='deposit',
            amount=Decimal('75.00'),
            payment_gateway='paypal',
            gateway_transaction_id='PAY-original',
            status='completed'
        )

        ipn_data = {
            'txn_id': 'PAY-refund123',
            'parent_txn_id': 'PAY-original',
            'mc_gross': '-75.00',
        }

        handle_paypal_refund(ipn_data)

        original_txn.refresh_from_db()
        assert original_txn.status == 'refunded'


@pytest.mark.django_db
class TestMPesaWebhook:
    """Test suite for M-Pesa webhook handlers."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='mpesa_user',
            email='mpesa@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def wallet(self, user):
        """Create test wallet."""
        wallet, _ = Wallet.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('0.00')}
        )
        return wallet

    @pytest.fixture
    def transaction(self, user, wallet):
        """Create test pending M-Pesa transaction."""
        return Transaction.objects.create(
            user=user,
            wallet=wallet,
            transaction_type='deposit',
            amount=Decimal('1000.00'),
            currency='KES',
            payment_gateway='mpesa',
            gateway_transaction_id='ws_CO_test123',
            status='pending'
        )

    def test_mpesa_webhook_success_callback(self, client, user, wallet, transaction):
        """Test M-Pesa success callback."""
        callback_data = {
            'Body': {
                'stkCallback': {
                    'MerchantRequestID': 'mr_test',
                    'CheckoutRequestID': 'ws_CO_test123',
                    'ResultCode': 0,
                    'ResultDesc': 'Success',
                    'CallbackMetadata': {
                        'Item': [
                            {'Name': 'Amount', 'Value': 1000},
                            {'Name': 'MpesaReceiptNumber', 'Value': 'QEI1234567'},
                            {'Name': 'PhoneNumber', 'Value': 254712345678},
                        ]
                    }
                }
            }
        }

        response = client.post(
            '/payments/webhook/mpesa/',
            data=json.dumps(callback_data),
            content_type='application/json'
        )

        assert response.status_code == 200

    def test_mpesa_webhook_failed_callback(self, client, user, wallet, transaction):
        """Test M-Pesa failed/cancelled callback."""
        callback_data = {
            'Body': {
                'stkCallback': {
                    'MerchantRequestID': 'mr_test',
                    'CheckoutRequestID': 'ws_CO_test123',
                    'ResultCode': 1032,
                    'ResultDesc': 'Request cancelled by user',
                }
            }
        }

        response = client.post(
            '/payments/webhook/mpesa/',
            data=json.dumps(callback_data),
            content_type='application/json'
        )

        assert response.status_code == 200

    def test_mpesa_webhook_invalid_json(self, client):
        """Test M-Pesa webhook with invalid JSON."""
        response = client.post(
            '/payments/webhook/mpesa/',
            data='invalid json',
            content_type='application/json'
        )

        assert response.status_code == 400

    def test_handle_mpesa_payment_success(self, user, wallet, transaction):
        """Test successful M-Pesa payment processing."""
        handle_mpesa_payment_success(
            checkout_request_id='ws_CO_test123',
            amount=Decimal('1000.00'),
            mpesa_receipt_number='QEI1234567',
            phone_number='254712345678'
        )

        transaction.refresh_from_db()
        assert transaction.status == 'completed'
        assert transaction.metadata.get('mpesa_receipt_number') == 'QEI1234567'

    def test_handle_mpesa_payment_success_credits_wallet(self, user, wallet, transaction):
        """Test M-Pesa payment credits wallet."""
        initial_balance = wallet.balance

        handle_mpesa_payment_success(
            checkout_request_id='ws_CO_test123',
            amount=Decimal('1000.00'),
            mpesa_receipt_number='QEI1234567',
            phone_number='254712345678'
        )

        wallet.refresh_from_db()
        assert wallet.balance == initial_balance + Decimal('1000.00')

    def test_handle_mpesa_payment_success_idempotency(self, user, wallet, transaction):
        """Test M-Pesa idempotency check."""
        transaction.status = 'completed'
        transaction.save()
        initial_balance = wallet.balance

        handle_mpesa_payment_success(
            checkout_request_id='ws_CO_test123',
            amount=Decimal('1000.00'),
            mpesa_receipt_number='QEI1234567',
            phone_number='254712345678'
        )

        wallet.refresh_from_db()
        assert wallet.balance == initial_balance

    def test_handle_mpesa_payment_failed(self, user, wallet, transaction):
        """Test M-Pesa payment failure handling."""
        handle_mpesa_payment_failed(
            checkout_request_id='ws_CO_test123',
            result_code=1,
            result_desc='User cancelled'
        )

        transaction.refresh_from_db()
        assert transaction.status == 'failed'
        assert transaction.metadata.get('mpesa_result_code') == 1

    def test_handle_mpesa_user_cancelled_error_code(self, user, wallet, transaction):
        """Test M-Pesa user cancellation error code mapping."""
        handle_mpesa_payment_failed(
            checkout_request_id='ws_CO_test123',
            result_code=1032,
            result_desc='Request cancelled by user'
        )

        transaction.refresh_from_db()
        assert 'cancelled' in transaction.metadata.get('mpesa_result_desc', '').lower()


@pytest.mark.django_db
class TestCashAppWebhook:
    """Test suite for CashApp (Square) webhook handlers."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='cashapp_user',
            email='cashapp@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def wallet(self, user):
        """Create test wallet."""
        wallet, _ = Wallet.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('0.00')}
        )
        return wallet

    @pytest.fixture
    def transaction(self, user, wallet):
        """Create test CashApp transaction."""
        return Transaction.objects.create(
            user=user,
            wallet=wallet,
            transaction_type='deposit',
            amount=Decimal('25.00'),
            payment_gateway='cashapp',
            gateway_transaction_id='cash_pay_123',
            status='pending'
        )

    def test_cashapp_webhook_payment_created(self, client):
        """Test CashApp payment.created webhook."""
        payload = {
            'type': 'payment.created',
            'data': {
                'object': {
                    'id': 'cash_pay_123',
                    'status': 'PENDING'
                }
            }
        }

        response = client.post(
            '/payments/webhook/cashapp/',
            data=json.dumps(payload),
            content_type='application/json'
        )

        assert response.status_code == 200

    def test_cashapp_webhook_payment_completed(self, client, user, wallet, transaction):
        """Test CashApp payment.updated with COMPLETED status."""
        payload = {
            'type': 'payment.updated',
            'data': {
                'object': {
                    'id': 'cash_pay_123',
                    'status': 'COMPLETED'
                }
            }
        }

        response = client.post(
            '/payments/webhook/cashapp/',
            data=json.dumps(payload),
            content_type='application/json'
        )

        assert response.status_code == 200
        transaction.refresh_from_db()
        assert transaction.status == 'completed'

    def test_cashapp_webhook_payment_failed(self, client, user, wallet, transaction):
        """Test CashApp payment.updated with FAILED status."""
        payload = {
            'type': 'payment.updated',
            'data': {
                'object': {
                    'id': 'cash_pay_123',
                    'status': 'FAILED'
                }
            }
        }

        response = client.post(
            '/payments/webhook/cashapp/',
            data=json.dumps(payload),
            content_type='application/json'
        )

        assert response.status_code == 200
        transaction.refresh_from_db()
        assert transaction.status == 'failed'

    def test_cashapp_webhook_invalid_json(self, client):
        """Test CashApp webhook with invalid JSON."""
        response = client.post(
            '/payments/webhook/cashapp/',
            data='not json',
            content_type='application/json'
        )

        assert response.status_code == 400


@pytest.mark.django_db
class TestVenmoWebhook:
    """Test suite for Venmo (Braintree) webhook handlers."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='venmo_user',
            email='venmo@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def wallet(self, user):
        """Create test wallet."""
        wallet, _ = Wallet.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('0.00')}
        )
        return wallet

    @pytest.fixture
    def transaction(self, user, wallet):
        """Create test Venmo transaction."""
        return Transaction.objects.create(
            user=user,
            wallet=wallet,
            transaction_type='deposit',
            amount=Decimal('30.00'),
            payment_gateway='venmo',
            gateway_transaction_id='venmo_txn_123',
            status='pending'
        )

    def test_venmo_webhook_transaction_settled(self, client, user, wallet, transaction):
        """Test Venmo transaction_settled webhook."""
        payload = {
            'kind': 'transaction_settled',
            'transaction': {
                'id': 'venmo_txn_123',
                'status': 'settled'
            }
        }

        response = client.post(
            '/payments/webhook/venmo/',
            data=json.dumps(payload),
            content_type='application/json'
        )

        assert response.status_code == 200
        transaction.refresh_from_db()
        assert transaction.status == 'completed'

    def test_venmo_webhook_transaction_declined(self, client, user, wallet, transaction):
        """Test Venmo transaction_settlement_declined webhook."""
        payload = {
            'kind': 'transaction_settlement_declined',
            'transaction': {
                'id': 'venmo_txn_123',
                'processor_response_text': 'Insufficient funds'
            }
        }

        response = client.post(
            '/payments/webhook/venmo/',
            data=json.dumps(payload),
            content_type='application/json'
        )

        assert response.status_code == 200
        transaction.refresh_from_db()
        assert transaction.status == 'failed'

    def test_venmo_webhook_invalid_json(self, client):
        """Test Venmo webhook with invalid JSON."""
        response = client.post(
            '/payments/webhook/venmo/',
            data='invalid',
            content_type='application/json'
        )

        assert response.status_code == 400


@pytest.mark.django_db
class TestWebhookReplayProtection:
    """Test webhook replay and idempotency protection."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='replay_user',
            email='replay@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def wallet(self, user):
        """Create test wallet."""
        wallet, _ = Wallet.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('100.00')}
        )
        return wallet

    def test_stripe_replay_protection(self, user, wallet):
        """Test that replayed Stripe webhooks don't double-credit."""
        # Create completed transaction
        txn = Transaction.objects.create(
            user=user,
            wallet=wallet,
            transaction_type='deposit',
            amount=Decimal('50.00'),
            payment_gateway='stripe',
            gateway_transaction_id='pi_replay_test',
            status='completed'  # Already completed
        )

        initial_balance = wallet.balance

        # Simulate replay
        handle_stripe_payment_success({'id': 'pi_replay_test', 'metadata': {}})

        wallet.refresh_from_db()
        assert wallet.balance == initial_balance  # No change

    def test_paypal_replay_protection(self, user, wallet):
        """Test that replayed PayPal IPNs don't double-credit."""
        txn = Transaction.objects.create(
            user=user,
            wallet=wallet,
            transaction_type='deposit',
            amount=Decimal('75.00'),
            payment_gateway='paypal',
            gateway_transaction_id='PAY-replay',
            status='completed'
        )

        initial_balance = wallet.balance

        handle_paypal_payment_success({
            'txn_id': 'PAY-replay',
            'mc_gross': '75.00'
        })

        wallet.refresh_from_db()
        assert wallet.balance == initial_balance

    def test_mpesa_replay_protection(self, user, wallet):
        """Test that replayed M-Pesa callbacks don't double-credit."""
        txn = Transaction.objects.create(
            user=user,
            wallet=wallet,
            transaction_type='deposit',
            amount=Decimal('500.00'),
            payment_gateway='mpesa',
            gateway_transaction_id='ws_CO_replay',
            status='completed'
        )

        initial_balance = wallet.balance

        handle_mpesa_payment_success(
            checkout_request_id='ws_CO_replay',
            amount=Decimal('500.00'),
            mpesa_receipt_number='QEI999',
            phone_number='254712345678'
        )

        wallet.refresh_from_db()
        assert wallet.balance == initial_balance


@pytest.mark.django_db
class TestWebhookAtomicity:
    """Test atomic transaction handling in webhooks."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='atomic_user',
            email='atomic@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def wallet(self, user):
        """Create test wallet."""
        wallet, _ = Wallet.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('0.00')}
        )
        return wallet

    def test_atomic_transaction_on_success(self, user, wallet):
        """Test that transaction and wallet update are atomic."""
        txn = Transaction.objects.create(
            user=user,
            wallet=wallet,
            transaction_type='deposit',
            amount=Decimal('100.00'),
            payment_gateway='stripe',
            gateway_transaction_id='pi_atomic_test',
            status='pending'
        )

        handle_stripe_payment_success({'id': 'pi_atomic_test', 'metadata': {}})

        txn.refresh_from_db()
        wallet.refresh_from_db()

        # Both should be updated
        assert txn.status == 'completed'
        assert wallet.balance == Decimal('100.00')


@pytest.mark.django_db
class TestWebhookSubscriptionHandling:
    """Test subscription activation through webhooks."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username='sub_user',
            email='sub@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def wallet(self, user):
        """Create test wallet."""
        wallet, _ = Wallet.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('0.00')}
        )
        return wallet

    @pytest.fixture
    def subscription_plan(self):
        """Create test subscription plan."""
        return SubscriptionPlan.objects.create(
            name='Premium',
            slug='premium',
            description='Premium plan',
            price=Decimal('29.99'),
            duration_days=30,
            is_active=True
        )

    @pytest.fixture
    def invoice(self, user, subscription_plan):
        """Create test invoice."""
        subscription = UserSubscription.objects.create(
            user=user,
            plan=subscription_plan,
            status='pending'
        )
        return Invoice.objects.create(
            user=user,
            subscription=subscription,
            amount=Decimal('29.99'),
            due_date=timezone.now(),
            description='Subscription payment'
        )

    def test_webhook_marks_invoice_as_paid(self, user, wallet, invoice):
        """Test that webhook marks linked invoice as paid."""
        txn = Transaction.objects.create(
            user=user,
            wallet=wallet,
            invoice=invoice,
            transaction_type='invoice_payment',
            amount=Decimal('29.99'),
            payment_gateway='stripe',
            gateway_transaction_id='pi_invoice_test',
            status='pending'
        )

        handle_stripe_payment_success({'id': 'pi_invoice_test', 'metadata': {}})

        invoice.refresh_from_db()
        assert invoice.status == 'paid'
        assert invoice.paid_date is not None

