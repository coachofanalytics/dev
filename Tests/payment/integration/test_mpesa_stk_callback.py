"""
Integration test for M-Pesa STK callback handler.

This test constructs a realistic STK callback payload and posts it to the
`mpesa_webhook` view function using Django's RequestFactory. The payment
handler `handle_mpesa_payment_success` is patched to ensure the webhook
parses and forwards the expected values correctly.
"""
import json
from decimal import Decimal
from django.test import RequestFactory, TestCase
from unittest.mock import patch

from payments import webhooks


class MPesaSTKCallbackIntegrationTest(TestCase):
    """Ensure mpesa_webhook parses STK callback JSON and invokes handler."""

    def setUp(self):
        self.factory = RequestFactory()

    def test_stk_success_invokes_handler(self):
        """A success STK callback should call `handle_mpesa_payment_success` with parsed values."""
        sample_payload = {
            "Body": {
                "stkCallback": {
                    "MerchantRequestID": "123456",
                    "CheckoutRequestID": "ABC123DEF",
                    "ResultCode": 0,
                    "ResultDesc": "The service request is processed successfully.",
                    "CallbackMetadata": {
                        "Item": [
                            {"Name": "Amount", "Value": 1500},
                            {"Name": "MpesaReceiptNumber", "Value": "MPESA12345"},
                            {"Name": "PhoneNumber", "Value": 254712345678}
                        ]
                    }
                }
            }
        }

        request = self.factory.post('/', data=json.dumps(sample_payload), content_type='application/json')

        with patch('payments.webhooks.handle_mpesa_payment_success') as mock_success:
            response = webhooks.mpesa_webhook(request)

            # The view should return HTTP 200 with ResultCode 0 JSON
            self.assertEqual(response.status_code, 200)
            self.assertIn('ResultCode', json.loads(response.content))
            self.assertEqual(json.loads(response.content)['ResultCode'], 0)

            # Ensure handler called with expected normalized values
            mock_success.assert_called_once()
            called_args = mock_success.call_args[0]
            # Expected: checkout_request_id, Decimal(amount), receipt, phone
            self.assertEqual(called_args[0], 'ABC123DEF')
            # Amount passed from JSON is converted to Decimal in the handler
            self.assertEqual(called_args[1], Decimal('1500'))
            self.assertEqual(called_args[2], 'MPESA12345')
            # Phone number provided as integer in sample becomes an int/str depending on JSON; compare substring
            self.assertTrue('2547123' in str(called_args[3]))
