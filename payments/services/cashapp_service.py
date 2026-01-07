"""
CashApp Payment Gateway Service
Implements Cash App Pay API for payment processing
"""
import requests
import uuid
from decimal import Decimal
from typing import Dict, Any, Optional
from .base import PaymentGateway


class CashAppPaymentGateway(PaymentGateway):
    """
    CashApp Payment Gateway implementation.
    Uses Cash App Pay API for processing payments.

    Note: CashApp (Square) uses OAuth 2.0 for authentication
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.app_id = config.get('app_id')
        self.client_id = config.get('client_id')
        self.client_secret = config.get('client_secret')
        self.location_id = config.get('location_id')

        # API endpoints
        if self.is_test_mode:
            self.base_url = 'https://connect.squareupsandbox.com/v2'
        else:
            self.base_url = 'https://connect.squareup.com/v2'

    def get_required_config_keys(self) -> list:
        """Return required configuration keys."""
        return ['app_id', 'client_id', 'client_secret', 'location_id']

    def _get_headers(self) -> Dict[str, str]:
        """Get API headers with authentication."""
        # In production, you would get an access token using OAuth 2.0
        # For this implementation, we'll use the access token directly
        access_token = self.config.get('access_token', '')
        return {
            'Square-Version': '2024-11-20',
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
        }

    def process_payment(self, amount: Decimal, currency: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a payment using Cash App Pay.

        Cash App Pay creates a payment request that the user completes in their Cash App.

        Args:
            amount: Payment amount
            currency: Currency code (USD)
            metadata: Additional data (user_id, email, description, etc.)

        Returns:
            Dict with payment result
        """
        try:
            # Generate unique idempotency key
            idempotency_key = str(uuid.uuid4())

            # Convert amount to cents (smallest currency unit)
            amount_cents = self.format_amount(amount, currency)

            # Create payment request
            payload = {
                'idempotency_key': idempotency_key,
                'amount_money': {
                    'amount': amount_cents,
                    'currency': currency
                },
                'source_id': metadata.get('source_id', 'CASH'),  # CASH for Cash App Pay
                'autocomplete': True,
                'location_id': self.location_id,
                'reference_id': metadata.get('reference_id', ''),
                'note': metadata.get('description', 'Payment via Biashara Bridges'),
                'customer_id': metadata.get('customer_id'),
            }

            # Remove None values
            payload = {k: v for k, v in payload.items() if v is not None}

            # Make API request
            url = f'{self.base_url}/payments'
            response = requests.post(
                url,
                json=payload,
                headers=self._get_headers(),
                timeout=30
            )

            response_data = response.json()

            if response.status_code == 200 and 'payment' in response_data:
                payment = response_data['payment']
                return {
                    'success': True,
                    'transaction_id': payment['id'],
                    'message': 'Payment processed successfully',
                    'data': payment,
                    'status': payment.get('status', 'PENDING'),
                }
            else:
                error_message = response_data.get('errors', [{}])[0].get('detail', 'Payment failed')
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
        Verify a Cash App payment transaction.

        Args:
            transaction_id: Square payment ID

        Returns:
            Dict with payment status
        """
        try:
            url = f'{self.base_url}/payments/{transaction_id}'
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=30
            )

            response_data = response.json()

            if response.status_code == 200 and 'payment' in response_data:
                payment = response_data['payment']
                status = payment.get('status', 'PENDING')

                # Map Square statuses to our standard statuses
                status_map = {
                    'COMPLETED': 'completed',
                    'APPROVED': 'completed',
                    'PENDING': 'pending',
                    'CANCELED': 'failed',
                    'FAILED': 'failed',
                }

                return {
                    'success': True,
                    'status': status_map.get(status, 'pending'),
                    'amount': self.parse_amount(
                        payment['amount_money']['amount'],
                        payment['amount_money']['currency']
                    ),
                    'message': f'Payment status: {status}',
                    'data': payment
                }
            else:
                return {
                    'success': False,
                    'status': 'failed',
                    'amount': Decimal('0'),
                    'message': 'Payment not found',
                    'data': response_data
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
        Refund a Cash App payment.

        Args:
            transaction_id: Square payment ID
            amount: Amount to refund (None for full refund)

        Returns:
            Dict with refund result
        """
        try:
            # Generate unique idempotency key
            idempotency_key = str(uuid.uuid4())

            payload = {
                'idempotency_key': idempotency_key,
                'payment_id': transaction_id,
            }

            # If partial refund, specify amount
            if amount is not None:
                payload['amount_money'] = {
                    'amount': self.format_amount(amount, 'USD'),
                    'currency': 'USD'
                }

            url = f'{self.base_url}/refunds'
            response = requests.post(
                url,
                json=payload,
                headers=self._get_headers(),
                timeout=30
            )

            response_data = response.json()

            if response.status_code == 200 and 'refund' in response_data:
                refund = response_data['refund']
                return {
                    'success': True,
                    'refund_id': refund['id'],
                    'message': 'Refund processed successfully',
                    'data': refund
                }
            else:
                error_message = response_data.get('errors', [{}])[0].get('detail', 'Refund failed')
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
        Create a customer in Square for Cash App payments.

        Args:
            user_data: User information (email, name, etc.)

        Returns:
            Dict with customer ID
        """
        try:
            idempotency_key = str(uuid.uuid4())

            payload = {
                'idempotency_key': idempotency_key,
                'email_address': user_data.get('email'),
                'given_name': user_data.get('first_name', ''),
                'family_name': user_data.get('last_name', ''),
                'phone_number': user_data.get('phone'),
            }

            # Remove None values
            payload = {k: v for k, v in payload.items() if v is not None and v != ''}

            url = f'{self.base_url}/customers'
            response = requests.post(
                url,
                json=payload,
                headers=self._get_headers(),
                timeout=30
            )

            response_data = response.json()

            if response.status_code == 200 and 'customer' in response_data:
                customer = response_data['customer']
                return {
                    'success': True,
                    'customer_id': customer['id'],
                    'message': 'Customer created successfully',
                    'data': customer
                }
            else:
                error_message = response_data.get('errors', [{}])[0].get('detail', 'Customer creation failed')
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
