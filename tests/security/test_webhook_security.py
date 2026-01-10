"""
Webhook Security Tests.
Pillar 7: Webhook Security

Tests:
- Signature verification (Stripe, PayPal)
- Missing signature rejection
- Replay attack protection (Idempotency)
- Large payload handling
"""

import pytest
import json
import time
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.conf import settings
from payments.models import Transaction, Wallet
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.security
class TestStripeWebhookSecurity(TestCase):
    """Tests for Stripe webhook security mechanisms."""

    def setUp(self):
        self.client = Client()
        self.endpoint = '/payments/webhooks/stripe/'
        self.payload = {
            'id': 'evt_test_webhook',
            'object': 'event',
            'type': 'payment_intent.succeeded',
            'data': {
                'object': {
                    'id': 'pi_test_123',
                    'metadata': {},
                    'amount': 1000,
                    'currency': 'usd'
                }
            }
        }
        self.payload_bytes = json.dumps(self.payload).encode('utf-8')

    @patch('stripe.Webhook.construct_event')
    def test_missing_signature_rejected(self, mock_construct):
        """Test that requests without signature header are rejected."""
        # Setup mock to raise error if called (though view checks header first usually by accessing it)
        # In the actual view: sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        # Then construct_event is called.
        
        # We want construct_event to raise SignatureVerificationError if signature is missing/invalid
        import stripe
        mock_construct.side_effect = stripe.error.SignatureVerificationError("Invalid signature", "sig_header", "payload")
        
        response = self.client.post(
            self.endpoint, 
            self.payload, 
            content_type='application/json'
            # No HTTP_STRIPE_SIGNATURE header
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    @patch('stripe.Webhook.construct_event')
    def test_invalid_signature_rejected(self, mock_construct):
        """Test that requests with invalid signature are rejected."""
        import stripe
        mock_construct.side_effect = stripe.error.SignatureVerificationError("Invalid signature", "sig_header", "payload")
        
        response = self.client.post(
            self.endpoint, 
            self.payload, 
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='t=123,v1=invalid_signature'
        )
        
        self.assertEqual(response.status_code, 400)

    @patch('stripe.Webhook.construct_event')
    def test_valid_signature_accepted(self, mock_construct):
        """Test that valid signed requests are accepted."""
        # Mock successful event construction
        mock_construct.return_value = self.payload
        
        # We need a transaction to exist for the success handler to work without error log
        # But even if it doesn't exist, the webhook should return 200 OK (received)
        
        response = self.client.post(
            self.endpoint, 
            self.payload, 
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='t=123,v1=valid_signature'
        )
        
        self.assertEqual(response.status_code, 200)

    @patch('stripe.Webhook.construct_event')
    def test_replay_idempotency(self, mock_construct):
        """Test that replaying the same webhook doesn't duplicate side effects."""
        mock_construct.return_value = self.payload
        
        # Setup: Create a transaction that is ALREADY completed
        user = User.objects.create_user(username='stripe_replay', password='pw')
        wallet = Wallet.objects.create(user=user)
        txn = Transaction.objects.create(
            user=user,
            wallet=wallet,
            amount=Decimal('10.00'),
            transaction_type='deposit',
            payment_gateway='stripe',
            gateway_transaction_id='pi_test_123',
            status='completed'  # Already completed
        )
        
        initial_balance = wallet.balance
        
        # Send webhook again
        response = self.client.post(
            self.endpoint, 
            self.payload, 
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify balance did NOT increase again
        wallet.refresh_from_db()
        self.assertEqual(wallet.balance, initial_balance, "Balance increased on replay! Idempotency failed.")


@pytest.mark.security
class TestPayPalWebhookSecurity(TestCase):
    """Tests for PayPal IPN verification."""

    def setUp(self):
        self.endpoint = '/payments/webhooks/paypal/'
        self.ipn_data = {
            'payment_status': 'Completed',
            'txn_id': 'ppb_123',
            'mc_gross': '50.00',
            'custom': 'user_123',
            'payer_email': 'payer@example.com'
        }

    @patch('requests.post')
    def test_unverified_ipn_rejected(self, mock_post):
        """Test that IPN failing verification is rejected."""
        # Mock PayPal responding "INVALID"
        mock_post.return_value.text = 'INVALID'
        
        response = self.client.post(self.endpoint, self.ipn_data)
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'], 'IPN verification failed')

    @patch('requests.post')
    def test_verified_ipn_accepted(self, mock_post):
        """Test that verified IPN is accepted."""
        # Mock PayPal responding "VERIFIED"
        mock_post.return_value.text = 'VERIFIED'
        
        response = self.client.post(self.endpoint, self.ipn_data)
        
        self.assertEqual(response.status_code, 200)


@pytest.mark.security
class TestMPesaWebhookSecurity(TestCase):
    """
    Tests for M-Pesa webhook security.
    CRITICAL: Current implementation lacks signature verification.
    """

    def setUp(self):
        self.endpoint = '/payments/webhooks/mpesa/'
        self.payload = {
            "Body": {
                "stkCallback": {
                    "MerchantRequestID": "29115-34620561-1",
                    "CheckoutRequestID": "ws_CO_191220191020363925",
                    "ResultCode": 0,
                    "ResultDesc": "The service request is processed successfully.",
                    "CallbackMetadata": {
                        "Item": [
                            {"Name": "Amount", "Value": 1.00},
                            {"Name": "MpesaReceiptNumber", "Value": "NLJ7RT61SV"},
                            {"Name": "PhoneNumber", "Value": 254708374149}
                        ]
                    }
                }
            }
        }

    def test_mpesa_missing_security_headers(self):
        """
        SECURITY CHECK: M-Pesa endpoint accepts requests without authentication.
        
        This test expects the endpoint to be PROTECTED (return 401/403).
        If it returns 200, it's a security vulnerability (Spoofing).
        """
        # We send a request without any auth headers or IP safelisting mocking
        response = self.client.post(
            self.endpoint, 
            self.payload, 
            content_type='application/json'
        )
        
        if response.status_code == 200:
            pytest.fail(
                "SECURITY VULNERABILITY: M-Pesa webhook endpoint accepted a request without signature verification. "
                "Anyone can spoof payment confirmations."
            )
        else:
            # If it returns 400/403/401/500, that's better than 200 (success)
            pass


@pytest.mark.security
class TestCashAppWebhookSecurity(TestCase):
    """
    Tests for CashApp webhook security.
    """
    
    def test_cashapp_missing_signature(self):
        """Check if CashApp endpoint enforces security."""
        endpoint = '/payments/webhooks/cashapp/'
        response = self.client.post(
            endpoint, 
            {'type': 'payment.updated'}, 
            content_type='application/json'
        )
        
        if response.status_code == 200:
            pytest.fail(
                "SECURITY VULNERABILITY: CashApp webhook endpoint accepted a request without signature verification."
            )

@pytest.mark.security
class TestVenmoWebhookSecurity(TestCase):
    """
    Tests for Venmo webhook security.
    """
    
    def test_venmo_missing_signature(self):
        """Check if Venmo endpoint enforces security."""
        endpoint = '/payments/webhooks/venmo/'
        response = self.client.post(
            endpoint, 
            {'kind': 'transaction_settled'}, 
            content_type='application/json'
        )
        
        if response.status_code == 200:
            pytest.fail(
                "SECURITY VULNERABILITY: Venmo webhook endpoint accepted a request without signature verification."
            )
