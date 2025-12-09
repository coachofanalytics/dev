import unittest
from decimal import Decimal
from unittest.mock import patch, MagicMock

from payments.services.stripe_service import StripePaymentGateway


class TestStripePaymentGateway(unittest.TestCase):
    def setUp(self):
        self.config = {
            'secret_key': 'sk_test_123',
            'publishable_key': 'pk_test_123',
            'is_test_mode': True,
        }
        self.gateway = StripePaymentGateway(self.config)

    @patch('payments.services.stripe_service.stripe.PaymentIntent.create')
    def test_process_payment_success(self, mock_create):
        # Mock intent object
        intent = MagicMock()
        intent.status = 'succeeded'
        intent.id = 'pi_123'
        intent.amount = 1000
        intent.currency = 'usd'
        mock_create.return_value = intent

        result = self.gateway.process_payment(Decimal('10.00'), 'USD', {'payment_method_id': 'pm_1'})

        self.assertTrue(result['success'])
        self.assertEqual(result['transaction_id'], 'pi_123')

    @patch('payments.services.stripe_service.stripe.PaymentIntent.retrieve')
    def test_verify_payment(self, mock_retrieve):
        intent = MagicMock()
        intent.status = 'succeeded'
        intent.amount = 1000
        intent.currency = 'usd'
        mock_retrieve.return_value = intent

        result = self.gateway.verify_payment('pi_123')

        self.assertTrue(result['success'])
        self.assertEqual(result['status'], 'completed')


if __name__ == '__main__':
    unittest.main()
