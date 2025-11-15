import stripe
from decimal import Decimal
from typing import Dict, Any, Optional
from .base import PaymentGateway


class StripePaymentGateway(PaymentGateway):
    """Stripe payment gateway implementation"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        stripe.api_key = self.config.get('secret_key')
        self.publishable_key = self.config.get('publishable_key')

    def get_required_config_keys(self) -> list:
        return ['secret_key', 'publishable_key']

    def process_payment(self, amount: Decimal, currency: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process payment using Stripe Payment Intent API.

        Args:
            amount: Amount to charge
            currency: Currency code (lowercase for Stripe)
            metadata: Must include 'payment_method_id' or 'token'

        Returns:
            Dict with payment result
        """
        try:
            # Convert amount to cents
            amount_cents = self.format_amount(amount, currency)

            # Create Payment Intent
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency.lower(),
                payment_method=metadata.get('payment_method_id'),
                confirm=True,
                metadata={
                    'user_id': str(metadata.get('user_id', '')),
                    'email': metadata.get('email', ''),
                    'description': metadata.get('description', 'Payment'),
                },
                return_url=metadata.get('return_url'),
            )

            return {
                'success': intent.status == 'succeeded',
                'transaction_id': intent.id,
                'status': intent.status,
                'message': f"Payment {intent.status}",
                'data': dict(intent),
            }

        except stripe.error.CardError as e:
            return {
                'success': False,
                'transaction_id': None,
                'message': f"Card error: {e.user_message}",
                'data': {'error': str(e)},
            }

        except stripe.error.StripeError as e:
            return {
                'success': False,
                'transaction_id': None,
                'message': f"Stripe error: {str(e)}",
                'data': {'error': str(e)},
            }

        except Exception as e:
            return {
                'success': False,
                'transaction_id': None,
                'message': f"Payment failed: {str(e)}",
                'data': {'error': str(e)},
            }

    def verify_payment(self, transaction_id: str) -> Dict[str, Any]:
        """
        Verify a Stripe payment using Payment Intent ID.

        Args:
            transaction_id: Stripe Payment Intent ID

        Returns:
            Dict with verification result
        """
        try:
            intent = stripe.PaymentIntent.retrieve(transaction_id)

            status_mapping = {
                'succeeded': 'completed',
                'processing': 'pending',
                'requires_payment_method': 'failed',
                'requires_confirmation': 'pending',
                'requires_action': 'pending',
                'canceled': 'failed',
            }

            return {
                'success': True,
                'status': status_mapping.get(intent.status, 'pending'),
                'amount': self.parse_amount(intent.amount, intent.currency),
                'currency': intent.currency.upper(),
                'message': f"Payment status: {intent.status}",
                'data': dict(intent),
            }

        except stripe.error.StripeError as e:
            return {
                'success': False,
                'status': 'failed',
                'message': f"Verification failed: {str(e)}",
                'data': {'error': str(e)},
            }

    def refund_payment(self, transaction_id: str, amount: Optional[Decimal] = None) -> Dict[str, Any]:
        """
        Refund a Stripe payment.

        Args:
            transaction_id: Stripe Payment Intent ID
            amount: Amount to refund (None for full refund)

        Returns:
            Dict with refund result
        """
        try:
            refund_params = {'payment_intent': transaction_id}

            if amount:
                refund_params['amount'] = self.format_amount(amount)

            refund = stripe.Refund.create(**refund_params)

            return {
                'success': refund.status == 'succeeded',
                'refund_id': refund.id,
                'amount': self.parse_amount(refund.amount, refund.currency),
                'message': f"Refund {refund.status}",
                'data': dict(refund),
            }

        except stripe.error.StripeError as e:
            return {
                'success': False,
                'refund_id': None,
                'message': f"Refund failed: {str(e)}",
                'data': {'error': str(e)},
            }

    def create_customer(self, email: str, name: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create a Stripe customer for recurring payments.

        Args:
            email: Customer email
            name: Customer name
            metadata: Additional customer metadata

        Returns:
            Dict with customer creation result
        """
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata=metadata or {},
            )

            return {
                'success': True,
                'customer_id': customer.id,
                'message': "Customer created successfully",
                'data': dict(customer),
            }

        except stripe.error.StripeError as e:
            return {
                'success': False,
                'customer_id': None,
                'message': f"Customer creation failed: {str(e)}",
                'data': {'error': str(e)},
            }

    def get_publishable_key(self) -> str:
        """Get the publishable key for frontend integration"""
        return self.publishable_key
