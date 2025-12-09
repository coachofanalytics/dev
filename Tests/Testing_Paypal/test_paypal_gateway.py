import unittest
from decimal import Decimal
from unittest.mock import patch, MagicMock

from payments.services.paypal_service import PayPalPaymentGateway


class TestPayPalPaymentGateway(unittest.TestCase):
    def setUp(self):
        self.config = {
            'client_id': 'client_123',
            'client_secret': 'secret_123',
            'is_test_mode': True,
        }
        self.gateway = PayPalPaymentGateway(self.config)

    @patch('payments.services.paypal_service.paypalrestsdk.Payment')
    def test_process_payment_creates_payment(self, mock_payment_cls):
        mock_payment = MagicMock()
        mock_payment.create.return_value = True
        link = MagicMock()
        link.rel = 'approval_url'
        link.href = 'https://paypal/approve'
        mock_payment.links = [link]
        mock_payment.id = 'PAY-123'
        mock_payment.to_dict.return_value = {'id': 'PAY-123'}
        mock_payment_cls.return_value = mock_payment

        result = self.gateway.process_payment(Decimal('5.00'), 'USD', {'return_url': 'https://r', 'cancel_url': 'https://c'})

        self.assertTrue(result['success'])
        self.assertIn('approval_url', result)
        self.assertEqual(result['transaction_id'], 'PAY-123')

    @patch('payments.services.paypal_service.paypalrestsdk.Payment')
    def test_verify_payment(self, mock_payment_cls):
        mock_payment = MagicMock()
        mock_payment.state = 'approved'
        tx = MagicMock()
        tx.amount.total = '5.00'
        tx.amount.currency = 'USD'
        mock_payment.transactions = [tx]
        mock_payment.to_dict.return_value = {'state': 'approved'}
        mock_payment_cls.find.return_value = mock_payment

        # Patch the class find method
        with patch('payments.services.paypal_service.paypalrestsdk.Payment.find', return_value=mock_payment):
            result = self.gateway.verify_payment('PAY-123')

        self.assertTrue(result['success'])
        self.assertEqual(result['status'], 'completed')


if __name__ == '__main__':
    unittest.main()
