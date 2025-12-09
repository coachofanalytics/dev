import unittest
from decimal import Decimal
from unittest.mock import patch, MagicMock

from payments.services.mpesa_service import MPesaPaymentGateway


class TestMPesaPaymentGateway(unittest.TestCase):
    def setUp(self):
        self.config = {
            'consumer_key': 'ck_123',
            'consumer_secret': 'cs_123',
            'business_shortcode': '123456',
            'passkey': 'passkey123',
            'callback_url': 'https://example.com/callback',
            'is_test_mode': True,
        }
        self.gateway = MPesaPaymentGateway(self.config)

    @patch('payments.services.mpesa_service.requests.get')
    @patch('payments.services.mpesa_service.requests.post')
    def test_process_payment_success(self, mock_post, mock_get):
        # Mock access token response
        mock_get.return_value = MagicMock(status_code=200, json=lambda: {'access_token': 'token123'})

        # Mock STK Push response
        mock_post.return_value = MagicMock(status_code=200, json=lambda: {'ResponseCode': '0', 'CheckoutRequestID': 'checkout123', 'MerchantRequestID': 'mreq123'})

        result = self.gateway.process_payment(Decimal('100'), 'KES', {'phone_number': '+254712345678'})

        self.assertTrue(result['success'])
        self.assertEqual(result['transaction_id'], 'checkout123')

    @patch('payments.services.mpesa_service.requests.get')
    @patch('payments.services.mpesa_service.requests.post')
    def test_verify_payment(self, mock_post, mock_get):
        mock_get.return_value = MagicMock(status_code=200, json=lambda: {'access_token': 'token123'})
        # Mock query response
        mock_post.return_value = MagicMock(status_code=200, json=lambda: {'ResultCode': '0', 'ResultDesc': 'Success', 'Amount': '100'})

        result = self.gateway.verify_payment('checkout123')

        self.assertTrue(result['success'])
        self.assertEqual(result['status'], 'completed')


if __name__ == '__main__':
    unittest.main()
