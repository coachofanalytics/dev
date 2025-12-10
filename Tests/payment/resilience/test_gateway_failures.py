from django.test import TestCase
from unittest import mock
import requests
from payments.webhooks import verify_paypal_ipn


class TestGatewayFailureModes(TestCase):
    """
    Tests that simulate network failures for gateway verification and ensure
    the application handles them gracefully.
    """

    @mock.patch('payments.webhooks.requests.post')
    def test_paypal_verify_timeout(self, mock_post):
        # Simulate a timeout when attempting to contact PayPal verification endpoint
        mock_post.side_effect = requests.exceptions.Timeout()
        result = verify_paypal_ipn({'txn_id': 'x'})
        self.assertFalse(result)

    @mock.patch('payments.webhooks.requests.post')
    def test_paypal_verify_bad_response(self, mock_post):
        # Simulate PayPal returning unexpected content
        resp = mock.Mock()
        resp.text = 'INVALID'
        mock_post.return_value = resp
        result = verify_paypal_ipn({'txn_id': 'x'})
        self.assertFalse(result)
