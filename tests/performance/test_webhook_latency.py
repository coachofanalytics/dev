"""
Webhook Processing Latency Benchmarks.

Tests payment gateway webhook processing performance.
Uses mocked gateway responses for safe, repeatable testing.
"""

import pytest
import json
import time
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.test import Client, RequestFactory
from django.contrib.auth.models import User

from payments.models import Wallet, Transaction

from .conftest import (
    PerformanceMetrics,
    assert_max_queries,
    PERF_P95_MS,
)


@pytest.fixture
def webhook_user_setup(db):
    """Create user with wallet and pending transaction for webhook testing."""
    user = User.objects.create_user(
        username='webhook_perf_user',
        email='webhook@perf.test',
        password='testpass123'
    )
    
    wallet, _ = Wallet.objects.get_or_create(
        user=user,
        defaults={'balance': Decimal('100.00')}
    )
    
    return user, wallet


def create_pending_transaction(user, wallet, gateway='stripe', amount='50.00'):
    """Create a pending transaction for webhook testing."""
    txn = Transaction.objects.create(
        user=user,
        wallet=wallet,
        transaction_type='deposit',
        amount=Decimal(amount),
        payment_gateway=gateway,
        status='pending'
    )
    return txn


@pytest.mark.django_db(transaction=True)
@pytest.mark.performance
@pytest.mark.latency
class TestStripeWebhookLatency:
    """Stripe webhook processing latency benchmarks."""

    @patch('stripe.Webhook.construct_event')
    def test_stripe_webhook__payment_success__under_500ms(
        self, mock_construct_event, webhook_user_setup
    ):
        """
        LATENCY BENCHMARK: Stripe payment success webhook processing.
        
        Simulates Stripe webhook callback and measures processing time.
        Threshold: p95 < 500ms
        """
        user, wallet = webhook_user_setup
        client = Client()
        metrics = PerformanceMetrics(name="stripe_webhook_success")
        
        for i in range(10):
            # Create pending transaction
            txn = create_pending_transaction(user, wallet, 'stripe')
            
            # Mock Stripe event
            mock_event = MagicMock()
            mock_event.type = 'payment_intent.succeeded'
            mock_event.data.object = {
                'id': f'pi_test_{i}',
                'metadata': {'transaction_id': txn.transaction_id},
                'amount': 5000,
                'currency': 'usd',
            }
            mock_construct_event.return_value = mock_event
            
            payload = json.dumps({
                'type': 'payment_intent.succeeded',
                'data': {'object': mock_event.data.object}
            })
            
            with metrics.measure():
                response = client.post(
                    '/webhooks/stripe/',
                    data=payload,
                    content_type='application/json',
                    HTTP_STRIPE_SIGNATURE='test_sig'
                )
            
            # Accept 200, 400 (validation), or 404 (URL not configured)
            if response.status_code == 404:
                pytest.skip("Stripe webhook URL not configured")
        
        metrics.print_report()
        metrics.assert_p95_under(
            500,
            message=f"Stripe webhook p95 ({metrics.p95:.2f}ms) exceeds 500ms"
        )


@pytest.mark.django_db(transaction=True)
@pytest.mark.performance
@pytest.mark.latency
class TestPayPalWebhookLatency:
    """PayPal webhook processing latency benchmarks."""

    @patch('payments.webhooks.verify_paypal_ipn')
    def test_paypal_webhook__ipn_payment__under_500ms(
        self, mock_verify, webhook_user_setup
    ):
        """
        LATENCY BENCHMARK: PayPal IPN webhook processing.
        
        Threshold: p95 < 500ms
        """
        user, wallet = webhook_user_setup
        client = Client()
        metrics = PerformanceMetrics(name="paypal_webhook_ipn")
        mock_verify.return_value = True
        
        for i in range(10):
            txn = create_pending_transaction(user, wallet, 'paypal')
            
            ipn_data = {
                'payment_status': 'Completed',
                'txn_id': f'paypal_txn_{i}',
                'custom': txn.transaction_id,
                'mc_gross': '50.00',
                'mc_currency': 'USD',
            }
            
            with metrics.measure():
                response = client.post(
                    '/webhooks/paypal/',
                    data=ipn_data,
                    content_type='application/x-www-form-urlencoded'
                )
            
            if response.status_code == 404:
                pytest.skip("PayPal webhook URL not configured")
        
        metrics.print_report()
        metrics.assert_p95_under(
            500,
            message=f"PayPal webhook p95 ({metrics.p95:.2f}ms) exceeds 500ms"
        )


@pytest.mark.django_db(transaction=True)
@pytest.mark.performance
@pytest.mark.latency
class TestMPesaWebhookLatency:
    """M-Pesa webhook processing latency benchmarks."""

    def test_mpesa_webhook__callback__under_500ms(self, webhook_user_setup):
        """
        LATENCY BENCHMARK: M-Pesa callback webhook processing.
        
        Threshold: p95 < 500ms
        """
        user, wallet = webhook_user_setup
        client = Client()
        metrics = PerformanceMetrics(name="mpesa_webhook_callback")
        
        for i in range(10):
            txn = create_pending_transaction(user, wallet, 'mpesa')
            
            callback_data = {
                'Body': {
                    'stkCallback': {
                        'MerchantRequestID': f'merchant_req_{i}',
                        'CheckoutRequestID': txn.transaction_id,
                        'ResultCode': 0,
                        'ResultDesc': 'Success',
                        'CallbackMetadata': {
                            'Item': [
                                {'Name': 'Amount', 'Value': 50.00},
                                {'Name': 'MpesaReceiptNumber', 'Value': f'MPESA{i}'},
                                {'Name': 'PhoneNumber', 'Value': '254712345678'},
                            ]
                        }
                    }
                }
            }
            
            with metrics.measure():
                response = client.post(
                    '/webhooks/mpesa/',
                    data=json.dumps(callback_data),
                    content_type='application/json'
                )
            
            if response.status_code == 404:
                pytest.skip("M-Pesa webhook URL not configured")
        
        metrics.print_report()
        metrics.assert_p95_under(
            500,
            message=f"M-Pesa webhook p95 ({metrics.p95:.2f}ms) exceeds 500ms"
        )


@pytest.mark.django_db(transaction=True)
@pytest.mark.performance
@pytest.mark.latency
class TestWebhookIdempotency:
    """Webhook idempotency handling performance."""

    @patch('stripe.Webhook.construct_event')
    def test_webhook_idempotency__duplicate_event__under_100ms(
        self, mock_construct_event, webhook_user_setup
    ):
        """
        LATENCY BENCHMARK: Duplicate webhook event handling.
        
        Second call with same event should be fast (idempotent check).
        Threshold: p95 < 100ms for duplicate
        """
        user, wallet = webhook_user_setup
        client = Client()
        
        # Create and complete a transaction
        txn = create_pending_transaction(user, wallet, 'stripe')
        txn.status = 'completed'
        txn.gateway_transaction_id = 'pi_duplicate_test'
        txn.save()
        
        mock_event = MagicMock()
        mock_event.type = 'payment_intent.succeeded'
        mock_event.data.object = {
            'id': 'pi_duplicate_test',
            'metadata': {'transaction_id': txn.transaction_id},
            'amount': 5000,
            'currency': 'usd',
        }
        mock_construct_event.return_value = mock_event
        
        payload = json.dumps({
            'type': 'payment_intent.succeeded',
            'data': {'object': mock_event.data.object}
        })
        
        metrics = PerformanceMetrics(name="webhook_idempotency")
        
        for _ in range(20):
            with metrics.measure():
                response = client.post(
                    '/webhooks/stripe/',
                    data=payload,
                    content_type='application/json',
                    HTTP_STRIPE_SIGNATURE='test_sig'
                )
            
            if response.status_code == 404:
                pytest.skip("Stripe webhook URL not configured")
        
        metrics.print_report()
        
        # Idempotent handling should be very fast
        metrics.assert_p95_under(
            100,
            message=f"Idempotency check p95 ({metrics.p95:.2f}ms) exceeds 100ms"
        )


@pytest.mark.django_db(transaction=True)
@pytest.mark.performance
@pytest.mark.latency
class TestWebhookQueryCounts:
    """Query efficiency for webhook processing."""

    @patch('stripe.Webhook.construct_event')
    def test_stripe_webhook__query_count__under_10(
        self, mock_construct_event, webhook_user_setup
    ):
        """
        QUERY EFFICIENCY: Stripe webhook query count.
        
        Webhook processing should be efficient.
        """
        user, wallet = webhook_user_setup
        client = Client()
        
        txn = create_pending_transaction(user, wallet, 'stripe')
        
        mock_event = MagicMock()
        mock_event.type = 'payment_intent.succeeded'
        mock_event.data.object = {
            'id': 'pi_query_test',
            'metadata': {'transaction_id': txn.transaction_id},
            'amount': 5000,
            'currency': 'usd',
        }
        mock_construct_event.return_value = mock_event
        
        payload = json.dumps({
            'type': 'payment_intent.succeeded',
            'data': {'object': mock_event.data.object}
        })
        
        try:
            with assert_max_queries(10, "stripe webhook"):
                response = client.post(
                    '/webhooks/stripe/',
                    data=payload,
                    content_type='application/json',
                    HTTP_STRIPE_SIGNATURE='test_sig'
                )
            if response.status_code == 404:
                pytest.skip("Stripe webhook URL not configured")
        except Exception as e:
            if "404" in str(e):
                pytest.skip("Stripe webhook URL not configured")
            raise


@pytest.mark.django_db(transaction=True)
@pytest.mark.performance
@pytest.mark.latency
@pytest.mark.slow
class TestWebhookThroughput:
    """Webhook processing throughput under load."""

    @patch('stripe.Webhook.construct_event')
    def test_webhook_throughput__50_sequential__report(
        self, mock_construct_event, webhook_user_setup
    ):
        """
        THROUGHPUT TEST: Sequential webhook processing.
        
        Measures sustained webhook throughput.
        """
        user, wallet = webhook_user_setup
        client = Client()
        metrics = PerformanceMetrics(name="webhook_throughput")
        
        for i in range(50):
            txn = create_pending_transaction(user, wallet, 'stripe')
            
            mock_event = MagicMock()
            mock_event.type = 'payment_intent.succeeded'
            mock_event.data.object = {
                'id': f'pi_throughput_{i}',
                'metadata': {'transaction_id': txn.transaction_id},
                'amount': 5000,
                'currency': 'usd',
            }
            mock_construct_event.return_value = mock_event
            
            payload = json.dumps({
                'type': 'payment_intent.succeeded',
                'data': {'object': mock_event.data.object}
            })
            
            with metrics.measure():
                response = client.post(
                    '/webhooks/stripe/',
                    data=payload,
                    content_type='application/json',
                    HTTP_STRIPE_SIGNATURE='test_sig'
                )
            
            if response.status_code == 404:
                pytest.skip("Stripe webhook URL not configured")
        
        metrics.print_report()
        print(f"\nWebhook Throughput: {metrics.throughput:.2f} webhooks/second")
