"""
Venmo Payment Gateway Service
Implements Venmo payments through Braintree API (PayPal owns Venmo)
"""
import requests
import base64
import uuid
from decimal import Decimal
from typing import Dict, Any, Optional
from .base import PaymentGateway


class VenmoPaymentGateway(PaymentGateway):
    """
    Venmo Payment Gateway implementation.
    Uses Braintree API for processing Venmo payments.

    Venmo is owned by PayPal and integrated through Braintree SDK.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.merchant_id = config.get('merchant_id')
        self.public_key = config.get('public_key')
        self.private_key = config.get('private_key')

        # API endpoints
        if self.is_test_mode:
            self.base_url = 'https://api.sandbox.braintreegateway.com'
        else:
            self.base_url = 'https://api.braintreegateway.com'

    def get_required_config_keys(self) -> list:
        """Return required configuration keys."""
        return ['merchant_id', 'public_key', 'private_key']

    def _get_auth_header(self) -> str:
        """Get Basic Auth header for Braintree API."""
        credentials = f"{self.public_key}:{self.private_key}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    def _get_headers(self) -> Dict[str, str]:
        """Get API headers with authentication."""
        return {
            'Authorization': self._get_auth_header(),
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

    def generate_client_token(self) -> Dict[str, Any]:
        """
        Generate a client token for Braintree Drop-in UI.
        This token is used in the frontend to initialize Venmo payment.

        Returns:
            Dict with client token
        """
        try:
            url = f'{self.base_url}/merchants/{self.merchant_id}/client_token'
            response = requests.post(
                url,
                json={},
                headers=self._get_headers(),
                timeout=30
            )

            if response.status_code == 201:
                return {
                    'success': True,
                    'client_token': response.json().get('clientToken'),
                    'message': 'Client token generated successfully'
                }
            else:
                return {
                    'success': False,
                    'client_token': None,
                    'message': 'Failed to generate client token'
                }

        except Exception as e:
            return {
                'success': False,
                'client_token': None,
                'message': f'Error generating token: {str(e)}'
            }

    def process_payment(self, amount: Decimal, currency: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a Venmo payment using Braintree.

        Args:
            amount: Payment amount
            currency: Currency code (USD)
            metadata: Additional data (payment_method_nonce, user_id, etc.)

        Returns:
            Dict with payment result
        """
        try:
            # Payment method nonce from frontend (Braintree Drop-in)
            payment_method_nonce = metadata.get('payment_method_nonce')

            if not payment_method_nonce:
                return {
                    'success': False,
                    'transaction_id': None,
                    'message': 'Payment method nonce is required',
                    'data': {}
                }

            # Create transaction
            payload = {
                'transaction': {
                    'type': 'sale',
                    'amount': str(amount),
                    'payment_method_nonce': payment_method_nonce,
                    'options': {
                        'submit_for_settlement': True,
                        'venmo': {
                            'profile_id': metadata.get('venmo_profile_id')
                        }
                    },
                    'merchant_account_id': metadata.get('merchant_account_id'),
                    'order_id': metadata.get('order_id'),
                    'customer': {
                        'id': metadata.get('customer_id'),
                        'email': metadata.get('email'),
                        'first_name': metadata.get('first_name', ''),
                        'last_name': metadata.get('last_name', ''),
                    }
                }
            }

            # Remove None values
            def remove_none(d):
                if isinstance(d, dict):
                    return {k: remove_none(v) for k, v in d.items() if v is not None}
                return d

            payload = remove_none(payload)

            url = f'{self.base_url}/merchants/{self.merchant_id}/transactions'
            response = requests.post(
                url,
                json=payload,
                headers=self._get_headers(),
                timeout=30
            )

            response_data = response.json()

            if response.status_code in [200, 201] and response_data.get('transaction'):
                transaction = response_data['transaction']
                status = transaction.get('status')

                return {
                    'success': status in ['authorized', 'submitted_for_settlement', 'settling', 'settled'],
                    'transaction_id': transaction.get('id'),
                    'message': f'Payment {status}',
                    'data': transaction,
                    'status': status,
                }
            else:
                error_message = response_data.get('message', 'Payment failed')
                return {
                    'success': False,
                    'transaction_id': None,
                    'message': error_message,
                    'data': response_data
                }

        except requests.RequestException as e:
            return {
                'success': False,
                'transaction_id': None,
                'message': f'Network error: {str(e)}',
                'data': {}
            }
        except Exception as e:
            return {
                'success': False,
                'transaction_id': None,
                'message': f'Error processing payment: {str(e)}',
                'data': {}
            }

    def verify_payment(self, transaction_id: str) -> Dict[str, Any]:
        """
        Verify a Venmo payment transaction.

        Args:
            transaction_id: Braintree transaction ID

        Returns:
            Dict with payment status
        """
        try:
            url = f'{self.base_url}/merchants/{self.merchant_id}/transactions/{transaction_id}'
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=30
            )

            if response.status_code == 200:
                transaction = response.json().get('transaction', {})
                status = transaction.get('status', '')

                # Map Braintree statuses to our standard statuses
                status_map = {
                    'authorized': 'completed',
                    'submitted_for_settlement': 'completed',
                    'settling': 'completed',
                    'settled': 'completed',
                    'authorization_expired': 'failed',
                    'gateway_rejected': 'failed',
                    'processor_declined': 'failed',
                    'settlement_declined': 'failed',
                    'failed': 'failed',
                    'voided': 'failed',
                }

                return {
                    'success': True,
                    'status': status_map.get(status, 'pending'),
                    'amount': Decimal(transaction.get('amount', '0')),
                    'message': f'Transaction status: {status}',
                    'data': transaction
                }
            else:
                return {
                    'success': False,
                    'status': 'failed',
                    'amount': Decimal('0'),
                    'message': 'Transaction not found',
                    'data': {}
                }

        except Exception as e:
            return {
                'success': False,
                'status': 'failed',
                'amount': Decimal('0'),
                'message': f'Error verifying payment: {str(e)}',
                'data': {}
            }

    def refund_payment(self, transaction_id: str, amount: Optional[Decimal] = None) -> Dict[str, Any]:
        """
        Refund a Venmo payment.

        Args:
            transaction_id: Braintree transaction ID
            amount: Amount to refund (None for full refund)

        Returns:
            Dict with refund result
        """
        try:
            url = f'{self.base_url}/merchants/{self.merchant_id}/transactions/{transaction_id}/refund'

            payload = {}
            if amount is not None:
                payload['amount'] = str(amount)

            response = requests.post(
                url,
                json=payload if payload else None,
                headers=self._get_headers(),
                timeout=30
            )

            response_data = response.json()

            if response.status_code in [200, 201] and response_data.get('transaction'):
                refund_transaction = response_data['transaction']
                return {
                    'success': True,
                    'refund_id': refund_transaction.get('id'),
                    'message': 'Refund processed successfully',
                    'data': refund_transaction
                }
            else:
                error_message = response_data.get('message', 'Refund failed')
                return {
                    'success': False,
                    'refund_id': None,
                    'message': error_message,
                    'data': response_data
                }

        except Exception as e:
            return {
                'success': False,
                'refund_id': None,
                'message': f'Error processing refund: {str(e)}',
                'data': {}
            }

    def create_customer(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a customer in Braintree for Venmo payments.

        Args:
            user_data: User information (email, name, etc.)

        Returns:
            Dict with customer ID
        """
        try:
            payload = {
                'customer': {
                    'email': user_data.get('email'),
                    'first_name': user_data.get('first_name', ''),
                    'last_name': user_data.get('last_name', ''),
                    'phone': user_data.get('phone'),
                }
            }

            # Remove None/empty values
            def remove_none(d):
                if isinstance(d, dict):
                    return {k: remove_none(v) for k, v in d.items() if v is not None and v != ''}
                return d

            payload = remove_none(payload)

            url = f'{self.base_url}/merchants/{self.merchant_id}/customers'
            response = requests.post(
                url,
                json=payload,
                headers=self._get_headers(),
                timeout=30
            )

            response_data = response.json()

            if response.status_code in [200, 201] and response_data.get('customer'):
                customer = response_data['customer']
                return {
                    'success': True,
                    'customer_id': customer.get('id'),
                    'message': 'Customer created successfully',
                    'data': customer
                }
            else:
                error_message = response_data.get('message', 'Customer creation failed')
                return {
                    'success': False,
                    'customer_id': None,
                    'message': error_message,
                    'data': response_data
                }

        except Exception as e:
            return {
                'success': False,
                'customer_id': None,
                'message': f'Error creating customer: {str(e)}',
                'data': {}
            }
