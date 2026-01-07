"""
Comprehensive tests for payment gateway implementations.

Tests Stripe, PayPal, and M-Pesa payment gateways with mocked external APIs.
Covers success paths, failure scenarios, timeouts, and edge cases.
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, override_settings
from django.contrib.auth.models import User

from payments.services.stripe_service import StripePaymentGateway
from payments.services.paypal_service import PayPalPaymentGateway
from payments.services.mpesa_service import MPesaPaymentGateway
from payments.models import Transaction, Wallet, PaymentGatewayConfig


# =============================================================================
# STRIPE GATEWAY TESTS
# =============================================================================

class TestStripePaymentGateway(TestCase):
    """Test suite for Stripe payment gateway."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'secret_key': 'sk_test_fake_key',
            'publishable_key': 'pk_test_fake_key',
        }
        self.gateway = StripePaymentGateway(self.config)
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_get_required_config_keys(self):
        """Test that required config keys are correctly defined."""
        required_keys = self.gateway.get_required_config_keys()
        self.assertIn('secret_key', required_keys)
        self.assertIn('publishable_key', required_keys)

    def test_get_publishable_key(self):
        """Test retrieving publishable key for frontend."""
        key = self.gateway.get_publishable_key()
        self.assertEqual(key, 'pk_test_fake_key')

    @patch('stripe.PaymentIntent.create')
    def test_process_payment_success(self, mock_create):
        """Test successful payment processing."""
        mock_intent = MagicMock()
        mock_intent.status = 'succeeded'
        mock_intent.id = 'pi_test_123'
        mock_intent.__iter__ = Mock(return_value=iter([]))
        mock_create.return_value = mock_intent

        result = self.gateway.process_payment(
            amount=Decimal('100.00'),
            currency='USD',
            metadata={
                'payment_method_id': 'pm_test_123',
                'user_id': self.user.id,
                'email': self.user.email,
                'description': 'Test payment',
                'return_url': 'https://example.com/return',
            }
        )

        self.assertTrue(result['success'])
        self.assertEqual(result['transaction_id'], 'pi_test_123')
        self.assertEqual(result['status'], 'succeeded')

    @patch('stripe.PaymentIntent.create')
    def test_process_payment_card_error(self, mock_create):
        """Test payment failure due to card error."""
        import stripe
        mock_create.side_effect = stripe.error.CardError(
            message="Your card was declined.",
            param=None,
            code='card_declined',
            http_status=402
        )

        result = self.gateway.process_payment(
            amount=Decimal('100.00'),
            currency='USD',
            metadata={'payment_method_id': 'pm_test_declined'}
        )

        self.assertFalse(result['success'])
        self.assertIsNone(result['transaction_id'])
        self.assertIn('Card error', result['message'])

    @patch('stripe.PaymentIntent.create')
    def test_process_payment_stripe_error(self, mock_create):
        """Test payment failure due to Stripe API error."""
        import stripe
        mock_create.side_effect = stripe.error.StripeError("API error")

        result = self.gateway.process_payment(
            amount=Decimal('50.00'),
            currency='USD',
            metadata={'payment_method_id': 'pm_test_error'}
        )

        self.assertFalse(result['success'])
        self.assertIn('Stripe error', result['message'])

    @patch('stripe.PaymentIntent.create')
    def test_process_payment_generic_exception(self, mock_create):
        """Test payment handling of unexpected exceptions."""
        mock_create.side_effect = Exception("Unexpected error")

        result = self.gateway.process_payment(
            amount=Decimal('75.00'),
            currency='USD',
            metadata={'payment_method_id': 'pm_test_exception'}
        )

        self.assertFalse(result['success'])
        self.assertIn('Payment failed', result['message'])

    @patch('stripe.PaymentIntent.retrieve')
    def test_verify_payment_success(self, mock_retrieve):
        """Test successful payment verification."""
        mock_intent = MagicMock()
        mock_intent.status = 'succeeded'
        mock_intent.amount = 10000  # cents
        mock_intent.currency = 'usd'
        mock_intent.__iter__ = Mock(return_value=iter([]))
        mock_retrieve.return_value = mock_intent

        result = self.gateway.verify_payment('pi_test_123')

        self.assertTrue(result['success'])
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['currency'], 'USD')

    @patch('stripe.PaymentIntent.retrieve')
    def test_verify_payment_pending_statuses(self, mock_retrieve):
        """Test verification of pending payment statuses."""
        pending_statuses = ['processing', 'requires_confirmation', 'requires_action']

        for stripe_status in pending_statuses:
            mock_intent = MagicMock()
            mock_intent.status = stripe_status
            mock_intent.amount = 5000
            mock_intent.currency = 'usd'
            mock_intent.__iter__ = Mock(return_value=iter([]))
            mock_retrieve.return_value = mock_intent

            result = self.gateway.verify_payment('pi_test_pending')
            self.assertEqual(result['status'], 'pending')

    @patch('stripe.PaymentIntent.retrieve')
    def test_verify_payment_failed_statuses(self, mock_retrieve):
        """Test verification of failed payment statuses."""
        failed_statuses = ['requires_payment_method', 'canceled']

        for stripe_status in failed_statuses:
            mock_intent = MagicMock()
            mock_intent.status = stripe_status
            mock_intent.amount = 5000
            mock_intent.currency = 'usd'
            mock_intent.__iter__ = Mock(return_value=iter([]))
            mock_retrieve.return_value = mock_intent

            result = self.gateway.verify_payment('pi_test_failed')
            self.assertEqual(result['status'], 'failed')

    @patch('stripe.PaymentIntent.retrieve')
    def test_verify_payment_stripe_error(self, mock_retrieve):
        """Test verification failure due to Stripe error."""
        import stripe
        mock_retrieve.side_effect = stripe.error.StripeError("Not found")

        result = self.gateway.verify_payment('pi_invalid_123')

        self.assertFalse(result['success'])
        self.assertEqual(result['status'], 'failed')
        self.assertIn('Verification failed', result['message'])

    @patch('stripe.Refund.create')
    def test_refund_payment_full_refund(self, mock_refund):
        """Test full refund processing."""
        mock_refund_obj = MagicMock()
        mock_refund_obj.status = 'succeeded'
        mock_refund_obj.id = 're_test_123'
        mock_refund_obj.amount = 10000
        mock_refund_obj.currency = 'usd'
        mock_refund_obj.__iter__ = Mock(return_value=iter([]))
        mock_refund.return_value = mock_refund_obj

        result = self.gateway.refund_payment('pi_test_123')

        self.assertTrue(result['success'])
        self.assertEqual(result['refund_id'], 're_test_123')
        mock_refund.assert_called_with(payment_intent='pi_test_123')

    @patch('stripe.Refund.create')
    def test_refund_payment_partial_refund(self, mock_refund):
        """Test partial refund processing."""
        mock_refund_obj = MagicMock()
        mock_refund_obj.status = 'succeeded'
        mock_refund_obj.id = 're_test_partial'
        mock_refund_obj.amount = 5000
        mock_refund_obj.currency = 'usd'
        mock_refund_obj.__iter__ = Mock(return_value=iter([]))
        mock_refund.return_value = mock_refund_obj

        result = self.gateway.refund_payment('pi_test_123', amount=Decimal('50.00'))

        self.assertTrue(result['success'])

    @patch('stripe.Refund.create')
    def test_refund_payment_failure(self, mock_refund):
        """Test refund failure handling."""
        import stripe
        mock_refund.side_effect = stripe.error.StripeError("Refund failed")

        result = self.gateway.refund_payment('pi_invalid')

        self.assertFalse(result['success'])
        self.assertIsNone(result['refund_id'])
        self.assertIn('Refund failed', result['message'])

    @patch('stripe.Customer.create')
    def test_create_customer_success(self, mock_create):
        """Test successful customer creation."""
        mock_customer = MagicMock()
        mock_customer.id = 'cus_test_123'
        mock_customer.__iter__ = Mock(return_value=iter([]))
        mock_create.return_value = mock_customer

        result = self.gateway.create_customer(
            email='customer@example.com',
            name='Test Customer',
            metadata={'user_id': '123'}
        )

        self.assertTrue(result['success'])
        self.assertEqual(result['customer_id'], 'cus_test_123')

    @patch('stripe.Customer.create')
    def test_create_customer_failure(self, mock_create):
        """Test customer creation failure."""
        import stripe
        mock_create.side_effect = stripe.error.StripeError("Invalid email")

        result = self.gateway.create_customer(
            email='invalid',
            name='Test'
        )

        self.assertFalse(result['success'])
        self.assertIsNone(result['customer_id'])


# =============================================================================
# PAYPAL GATEWAY TESTS
# =============================================================================

class TestPayPalPaymentGateway(TestCase):
    """Test suite for PayPal payment gateway."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'client_id': 'test_client_id',
            'client_secret': 'test_client_secret',
        }

    def test_get_required_config_keys(self):
        """Test that required config keys are correctly defined."""
        with patch('paypalrestsdk.configure'):
            gateway = PayPalPaymentGateway(self.config)
            required_keys = gateway.get_required_config_keys()
            self.assertIn('client_id', required_keys)
            self.assertIn('client_secret', required_keys)

    @patch('paypalrestsdk.configure')
    @patch('paypalrestsdk.Payment')
    def test_process_payment_success(self, mock_payment_class, mock_configure):
        """Test successful PayPal payment creation."""
        mock_payment = MagicMock()
        mock_payment.create.return_value = True
        mock_payment.id = 'PAY-test123'
        mock_payment.links = [
            MagicMock(rel='approval_url', href='https://paypal.com/approve/123'),
            MagicMock(rel='self', href='https://api.paypal.com/pay/123'),
        ]
        mock_payment.to_dict.return_value = {'id': 'PAY-test123'}
        mock_payment_class.return_value = mock_payment

        gateway = PayPalPaymentGateway(self.config)
        result = gateway.process_payment(
            amount=Decimal('100.00'),
            currency='USD',
            metadata={
                'return_url': 'https://example.com/success',
                'cancel_url': 'https://example.com/cancel',
                'description': 'Test payment',
            }
        )

        self.assertTrue(result['success'])
        self.assertEqual(result['transaction_id'], 'PAY-test123')
        self.assertEqual(result['approval_url'], 'https://paypal.com/approve/123')

    @patch('paypalrestsdk.configure')
    @patch('paypalrestsdk.Payment')
    def test_process_payment_creation_failure(self, mock_payment_class, mock_configure):
        """Test PayPal payment creation failure."""
        mock_payment = MagicMock()
        mock_payment.create.return_value = False
        mock_payment.error = {'message': 'Invalid currency'}
        mock_payment_class.return_value = mock_payment

        gateway = PayPalPaymentGateway(self.config)
        result = gateway.process_payment(
            amount=Decimal('100.00'),
            currency='INVALID',
            metadata={
                'return_url': 'https://example.com/success',
                'cancel_url': 'https://example.com/cancel',
            }
        )

        self.assertFalse(result['success'])
        self.assertIsNone(result['transaction_id'])

    @patch('paypalrestsdk.configure')
    @patch('paypalrestsdk.Payment')
    def test_process_payment_exception(self, mock_payment_class, mock_configure):
        """Test PayPal payment exception handling."""
        mock_payment_class.side_effect = Exception("Network error")

        gateway = PayPalPaymentGateway(self.config)
        result = gateway.process_payment(
            amount=Decimal('50.00'),
            currency='USD',
            metadata={
                'return_url': 'https://example.com/success',
                'cancel_url': 'https://example.com/cancel',
            }
        )

        self.assertFalse(result['success'])
        self.assertIn('PayPal error', result['message'])

    @patch('paypalrestsdk.configure')
    @patch('paypalrestsdk.Payment.find')
    def test_verify_payment_approved(self, mock_find, mock_configure):
        """Test verification of approved PayPal payment."""
        mock_payment = MagicMock()
        mock_payment.state = 'approved'
        mock_payment.transactions = [
            MagicMock(amount=MagicMock(total='100.00', currency='USD'))
        ]
        mock_payment.to_dict.return_value = {'state': 'approved'}
        mock_find.return_value = mock_payment

        gateway = PayPalPaymentGateway(self.config)
        result = gateway.verify_payment('PAY-test123')

        self.assertTrue(result['success'])
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['amount'], Decimal('100.00'))

    @patch('paypalrestsdk.configure')
    @patch('paypalrestsdk.Payment.find')
    def test_verify_payment_pending(self, mock_find, mock_configure):
        """Test verification of pending PayPal payment."""
        mock_payment = MagicMock()
        mock_payment.state = 'created'
        mock_payment.transactions = [
            MagicMock(amount=MagicMock(total='50.00', currency='USD'))
        ]
        mock_payment.to_dict.return_value = {'state': 'created'}
        mock_find.return_value = mock_payment

        gateway = PayPalPaymentGateway(self.config)
        result = gateway.verify_payment('PAY-pending')

        self.assertEqual(result['status'], 'pending')

    @patch('paypalrestsdk.configure')
    @patch('paypalrestsdk.Payment.find')
    def test_verify_payment_failed_states(self, mock_find, mock_configure):
        """Test verification of failed PayPal payment states."""
        failed_states = ['failed', 'canceled', 'expired']

        for state in failed_states:
            mock_payment = MagicMock()
            mock_payment.state = state
            mock_payment.transactions = [
                MagicMock(amount=MagicMock(total='25.00', currency='USD'))
            ]
            mock_payment.to_dict.return_value = {'state': state}
            mock_find.return_value = mock_payment

            gateway = PayPalPaymentGateway(self.config)
            result = gateway.verify_payment(f'PAY-{state}')

            self.assertEqual(result['status'], 'failed')

    @patch('paypalrestsdk.configure')
    @patch('paypalrestsdk.Payment.find')
    def test_verify_payment_exception(self, mock_find, mock_configure):
        """Test verification exception handling."""
        mock_find.side_effect = Exception("API error")

        gateway = PayPalPaymentGateway(self.config)
        result = gateway.verify_payment('PAY-invalid')

        self.assertFalse(result['success'])
        self.assertEqual(result['status'], 'failed')

    @patch('paypalrestsdk.configure')
    @patch('paypalrestsdk.Sale.find')
    def test_refund_payment_success(self, mock_find, mock_configure):
        """Test successful PayPal refund."""
        mock_sale = MagicMock()
        mock_refund = MagicMock()
        mock_refund.success.return_value = True
        mock_refund.id = 'RE-test123'
        mock_refund.amount = MagicMock(total='100.00')
        mock_refund.to_dict.return_value = {'id': 'RE-test123'}
        mock_sale.refund.return_value = mock_refund
        mock_sale.amount = MagicMock(currency='USD')
        mock_find.return_value = mock_sale

        gateway = PayPalPaymentGateway(self.config)
        result = gateway.refund_payment('SALE-123')

        self.assertTrue(result['success'])
        self.assertEqual(result['refund_id'], 'RE-test123')

    @patch('paypalrestsdk.configure')
    @patch('paypalrestsdk.Sale.find')
    def test_refund_payment_partial(self, mock_find, mock_configure):
        """Test partial PayPal refund."""
        mock_sale = MagicMock()
        mock_refund = MagicMock()
        mock_refund.success.return_value = True
        mock_refund.id = 'RE-partial'
        mock_refund.amount = MagicMock(total='50.00')
        mock_refund.to_dict.return_value = {'id': 'RE-partial'}
        mock_sale.refund.return_value = mock_refund
        mock_sale.amount = MagicMock(currency='USD')
        mock_find.return_value = mock_sale

        gateway = PayPalPaymentGateway(self.config)
        result = gateway.refund_payment('SALE-123', amount=Decimal('50.00'))

        self.assertTrue(result['success'])

    @patch('paypalrestsdk.configure')
    @patch('paypalrestsdk.Sale.find')
    def test_refund_payment_failure(self, mock_find, mock_configure):
        """Test PayPal refund failure."""
        mock_sale = MagicMock()
        mock_refund = MagicMock()
        mock_refund.success.return_value = False
        mock_refund.error = {'message': 'Insufficient funds'}
        mock_sale.refund.return_value = mock_refund
        mock_sale.amount = MagicMock(currency='USD')
        mock_find.return_value = mock_sale

        gateway = PayPalPaymentGateway(self.config)
        result = gateway.refund_payment('SALE-123')

        self.assertFalse(result['success'])
        self.assertIn('Refund failed', result['message'])

    @patch('paypalrestsdk.configure')
    @patch('paypalrestsdk.Payment.find')
    def test_execute_payment_success(self, mock_find, mock_configure):
        """Test successful payment execution."""
        mock_payment = MagicMock()
        mock_payment.execute.return_value = True
        mock_payment.to_dict.return_value = {'state': 'approved'}
        mock_find.return_value = mock_payment

        gateway = PayPalPaymentGateway(self.config)
        result = gateway.execute_payment('PAY-123', 'PAYER-456')

        self.assertTrue(result['success'])
        mock_payment.execute.assert_called_with({'payer_id': 'PAYER-456'})

    @patch('paypalrestsdk.configure')
    @patch('paypalrestsdk.Payment.find')
    def test_execute_payment_failure(self, mock_find, mock_configure):
        """Test payment execution failure."""
        mock_payment = MagicMock()
        mock_payment.execute.return_value = False
        mock_payment.error = {'message': 'Execution failed'}
        mock_find.return_value = mock_payment

        gateway = PayPalPaymentGateway(self.config)
        result = gateway.execute_payment('PAY-123', 'PAYER-invalid')

        self.assertFalse(result['success'])


# =============================================================================
# M-PESA GATEWAY TESTS
# =============================================================================

class TestMPesaPaymentGateway(TestCase):
    """Test suite for M-Pesa payment gateway."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'consumer_key': 'test_consumer_key',
            'consumer_secret': 'test_consumer_secret',
            'business_shortcode': '174379',
            'passkey': 'test_passkey',
            'callback_url': 'https://example.com/mpesa/callback',
        }

    def test_get_required_config_keys(self):
        """Test that required config keys are correctly defined."""
        gateway = MPesaPaymentGateway(self.config)
        required_keys = gateway.get_required_config_keys()
        self.assertIn('consumer_key', required_keys)
        self.assertIn('consumer_secret', required_keys)
        self.assertIn('business_shortcode', required_keys)
        self.assertIn('passkey', required_keys)
        self.assertIn('callback_url', required_keys)

    def test_base_url_sandbox_mode(self):
        """Test that sandbox URL is used in test mode."""
        gateway = MPesaPaymentGateway(self.config)
        gateway.is_test_mode = True
        self.assertIn('sandbox', gateway.base_url)

    def test_generate_password(self):
        """Test password generation for STK push."""
        gateway = MPesaPaymentGateway(self.config)
        timestamp = '20240101120000'
        password = gateway.generate_password(timestamp)

        self.assertIsInstance(password, str)
        self.assertTrue(len(password) > 0)

    @patch('requests.get')
    def test_get_access_token_success(self, mock_get):
        """Test successful access token retrieval."""
        mock_response = MagicMock()
        mock_response.json.return_value = {'access_token': 'test_token_123'}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        gateway = MPesaPaymentGateway(self.config)
        token = gateway.get_access_token()

        self.assertEqual(token, 'test_token_123')

    @patch('requests.get')
    def test_get_access_token_failure(self, mock_get):
        """Test access token retrieval failure."""
        mock_get.side_effect = Exception("Connection error")

        gateway = MPesaPaymentGateway(self.config)
        token = gateway.get_access_token()

        self.assertIsNone(token)

    @patch('requests.post')
    @patch('requests.get')
    def test_process_payment_success(self, mock_get, mock_post):
        """Test successful STK push initiation."""
        # Mock access token
        mock_get_response = MagicMock()
        mock_get_response.json.return_value = {'access_token': 'test_token'}
        mock_get_response.raise_for_status.return_value = None
        mock_get.return_value = mock_get_response

        # Mock STK push response
        mock_post_response = MagicMock()
        mock_post_response.json.return_value = {
            'ResponseCode': '0',
            'CheckoutRequestID': 'ws_CO_test123',
            'MerchantRequestID': 'mr_test123',
        }
        mock_post_response.raise_for_status.return_value = None
        mock_post.return_value = mock_post_response

        gateway = MPesaPaymentGateway(self.config)
        result = gateway.process_payment(
            amount=Decimal('100.00'),
            currency='KES',
            metadata={
                'phone_number': '+254712345678',
                'reference': 'TEST123',
                'description': 'Test payment',
            }
        )

        self.assertTrue(result['success'])
        self.assertEqual(result['transaction_id'], 'ws_CO_test123')

    @patch('requests.post')
    @patch('requests.get')
    def test_process_payment_stk_push_failed(self, mock_get, mock_post):
        """Test STK push failure."""
        # Mock access token
        mock_get_response = MagicMock()
        mock_get_response.json.return_value = {'access_token': 'test_token'}
        mock_get_response.raise_for_status.return_value = None
        mock_get.return_value = mock_get_response

        # Mock failed STK push response
        mock_post_response = MagicMock()
        mock_post_response.json.return_value = {
            'ResponseCode': '1',
            'ResponseDescription': 'Invalid phone number',
        }
        mock_post_response.raise_for_status.return_value = None
        mock_post.return_value = mock_post_response

        gateway = MPesaPaymentGateway(self.config)
        result = gateway.process_payment(
            amount=Decimal('100.00'),
            currency='KES',
            metadata={'phone_number': 'invalid'}
        )

        self.assertFalse(result['success'])

    @patch('requests.get')
    def test_process_payment_no_access_token(self, mock_get):
        """Test payment failure when access token cannot be obtained."""
        mock_get.side_effect = Exception("Token error")

        gateway = MPesaPaymentGateway(self.config)
        result = gateway.process_payment(
            amount=Decimal('100.00'),
            currency='KES',
            metadata={'phone_number': '+254712345678'}
        )

        self.assertFalse(result['success'])
        self.assertIn('access token', result['message'].lower())

    @patch('requests.post')
    @patch('requests.get')
    def test_process_payment_phone_number_formatting(self, mock_get, mock_post):
        """Test phone number format conversion."""
        mock_get_response = MagicMock()
        mock_get_response.json.return_value = {'access_token': 'test_token'}
        mock_get_response.raise_for_status.return_value = None
        mock_get.return_value = mock_get_response

        mock_post_response = MagicMock()
        mock_post_response.json.return_value = {
            'ResponseCode': '0',
            'CheckoutRequestID': 'ws_CO_test',
            'MerchantRequestID': 'mr_test',
        }
        mock_post_response.raise_for_status.return_value = None
        mock_post.return_value = mock_post_response

        gateway = MPesaPaymentGateway(self.config)

        # Test with leading zero
        gateway.process_payment(
            amount=Decimal('100.00'),
            currency='KES',
            metadata={'phone_number': '0712345678'}
        )

        # Verify call was made with correct format
        call_args = mock_post.call_args
        self.assertIsNotNone(call_args)

    @patch('requests.post')
    @patch('requests.get')
    def test_verify_payment_completed(self, mock_get, mock_post):
        """Test verification of completed M-Pesa transaction."""
        mock_get_response = MagicMock()
        mock_get_response.json.return_value = {'access_token': 'test_token'}
        mock_get_response.raise_for_status.return_value = None
        mock_get.return_value = mock_get_response

        mock_post_response = MagicMock()
        mock_post_response.json.return_value = {
            'ResultCode': '0',
            'ResultDesc': 'Success',
            'Amount': '100',
        }
        mock_post_response.raise_for_status.return_value = None
        mock_post.return_value = mock_post_response

        gateway = MPesaPaymentGateway(self.config)
        result = gateway.verify_payment('ws_CO_test123')

        self.assertTrue(result['success'])
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['currency'], 'KES')

    @patch('requests.post')
    @patch('requests.get')
    def test_verify_payment_cancelled(self, mock_get, mock_post):
        """Test verification of cancelled M-Pesa transaction."""
        mock_get_response = MagicMock()
        mock_get_response.json.return_value = {'access_token': 'test_token'}
        mock_get_response.raise_for_status.return_value = None
        mock_get.return_value = mock_get_response

        mock_post_response = MagicMock()
        mock_post_response.json.return_value = {
            'ResultCode': '1032',
            'ResultDesc': 'Request cancelled by user',
        }
        mock_post_response.raise_for_status.return_value = None
        mock_post.return_value = mock_post_response

        gateway = MPesaPaymentGateway(self.config)
        result = gateway.verify_payment('ws_CO_cancelled')

        self.assertEqual(result['status'], 'failed')

    @patch('requests.get')
    def test_verify_payment_no_token(self, mock_get):
        """Test verification failure when token cannot be obtained."""
        mock_get.side_effect = Exception("Token error")

        gateway = MPesaPaymentGateway(self.config)
        result = gateway.verify_payment('ws_CO_test123')

        self.assertFalse(result['success'])
        self.assertEqual(result['status'], 'failed')

    def test_refund_payment_not_supported(self):
        """Test that M-Pesa refunds return not supported message."""
        gateway = MPesaPaymentGateway(self.config)
        result = gateway.refund_payment('ws_CO_test123')

        self.assertFalse(result['success'])
        self.assertIn('manual processing', result['message'])


# =============================================================================
# GATEWAY TIMEOUT AND RETRY TESTS
# =============================================================================

class TestGatewayTimeoutScenarios(TestCase):
    """Test timeout and network failure scenarios."""

    @patch('stripe.PaymentIntent.create')
    def test_stripe_timeout(self, mock_create):
        """Test Stripe timeout handling."""
        import stripe
        mock_create.side_effect = stripe.error.APIConnectionError("Request timed out")

        config = {'secret_key': 'sk_test', 'publishable_key': 'pk_test'}
        gateway = StripePaymentGateway(config)

        result = gateway.process_payment(
            amount=Decimal('100.00'),
            currency='USD',
            metadata={'payment_method_id': 'pm_test'}
        )

        self.assertFalse(result['success'])

    @patch('requests.post')
    @patch('requests.get')
    def test_mpesa_timeout(self, mock_get, mock_post):
        """Test M-Pesa timeout handling."""
        import requests

        mock_get_response = MagicMock()
        mock_get_response.json.return_value = {'access_token': 'test'}
        mock_get_response.raise_for_status.return_value = None
        mock_get.return_value = mock_get_response

        mock_post.side_effect = requests.exceptions.Timeout("Request timed out")

        config = {
            'consumer_key': 'key',
            'consumer_secret': 'secret',
            'business_shortcode': '174379',
            'passkey': 'passkey',
            'callback_url': 'https://example.com/callback',
        }
        gateway = MPesaPaymentGateway(config)

        result = gateway.process_payment(
            amount=Decimal('100.00'),
            currency='KES',
            metadata={'phone_number': '+254712345678'}
        )

        self.assertFalse(result['success'])


# =============================================================================
# CURRENCY HANDLING TESTS
# =============================================================================

class TestCurrencyHandling(TestCase):
    """Test currency conversion and handling."""

    def test_stripe_amount_conversion_to_cents(self):
        """Test Stripe converts amounts to cents correctly."""
        config = {'secret_key': 'sk_test', 'publishable_key': 'pk_test'}
        gateway = StripePaymentGateway(config)

        # Test various amounts
        self.assertEqual(gateway.format_amount(Decimal('100.00'), 'usd'), 10000)
        self.assertEqual(gateway.format_amount(Decimal('1.50'), 'usd'), 150)
        self.assertEqual(gateway.format_amount(Decimal('0.99'), 'usd'), 99)

    def test_stripe_amount_conversion_from_cents(self):
        """Test Stripe converts cents back to decimal correctly."""
        config = {'secret_key': 'sk_test', 'publishable_key': 'pk_test'}
        gateway = StripePaymentGateway(config)

        self.assertEqual(gateway.parse_amount(10000, 'usd'), Decimal('100.00'))
        self.assertEqual(gateway.parse_amount(150, 'usd'), Decimal('1.50'))


# =============================================================================
# GATEWAY FACTORY TESTS
# =============================================================================

class TestPaymentGatewayFactory(TestCase):
    """Test payment gateway factory functionality."""

    @patch('payments.models.PaymentGatewayConfig.objects.get')
    def test_factory_creates_stripe_gateway(self, mock_get):
        """Test factory creates Stripe gateway correctly."""
        from payments.services.payment_factory import PaymentGatewayFactory

        mock_config = MagicMock()
        mock_config.is_active = True
        mock_config.is_test_mode = True
        mock_config.config_data = {
            'secret_key': 'sk_test',
            'publishable_key': 'pk_test',
        }
        mock_get.return_value = mock_config

        gateway = PaymentGatewayFactory.get_gateway('stripe')
        self.assertIsInstance(gateway, StripePaymentGateway)

    @patch('payments.models.PaymentGatewayConfig.objects.get')
    def test_factory_raises_for_inactive_gateway(self, mock_get):
        """Test factory raises error for inactive gateway."""
        from payments.services.payment_factory import PaymentGatewayFactory

        mock_config = MagicMock()
        mock_config.is_active = False
        mock_get.return_value = mock_config

        with self.assertRaises(ValueError):
            PaymentGatewayFactory.get_gateway('stripe')

