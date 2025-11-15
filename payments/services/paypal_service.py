from decimal import Decimal
from typing import Dict, Any, Optional
from .base import PaymentGateway
import paypalrestsdk


class PayPalPaymentGateway(PaymentGateway):
    """PayPal payment gateway implementation"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        # Configure PayPal SDK
        paypalrestsdk.configure({
            'mode': 'sandbox' if self.is_test_mode else 'live',
            'client_id': self.config.get('client_id'),
            'client_secret': self.config.get('client_secret'),
        })

    def get_required_config_keys(self) -> list:
        return ['client_id', 'client_secret']

    def process_payment(self, amount: Decimal, currency: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a PayPal payment.

        Args:
            amount: Amount to charge
            currency: Currency code
            metadata: Must include 'return_url' and 'cancel_url'

        Returns:
            Dict with payment result including approval_url for redirect
        """
        try:
            payment = paypalrestsdk.Payment({
                'intent': 'sale',
                'payer': {'payment_method': 'paypal'},
                'redirect_urls': {
                    'return_url': metadata.get('return_url'),
                    'cancel_url': metadata.get('cancel_url'),
                },
                'transactions': [{
                    'amount': {
                        'total': str(amount),
                        'currency': currency,
                    },
                    'description': metadata.get('description', 'Payment'),
                }],
            })

            if payment.create():
                # Find the approval URL
                approval_url = None
                for link in payment.links:
                    if link.rel == 'approval_url':
                        approval_url = link.href
                        break

                return {
                    'success': True,
                    'transaction_id': payment.id,
                    'approval_url': approval_url,
                    'message': "Payment created. Redirect user to approval_url",
                    'data': payment.to_dict(),
                }
            else:
                return {
                    'success': False,
                    'transaction_id': None,
                    'message': f"Payment creation failed: {payment.error}",
                    'data': {'error': payment.error},
                }

        except Exception as e:
            return {
                'success': False,
                'transaction_id': None,
                'message': f"PayPal error: {str(e)}",
                'data': {'error': str(e)},
            }

    def verify_payment(self, transaction_id: str) -> Dict[str, Any]:
        """
        Verify PayPal payment status.

        Args:
            transaction_id: PayPal payment ID

        Returns:
            Dict with verification result
        """
        try:
            payment = paypalrestsdk.Payment.find(transaction_id)

            status_mapping = {
                'created': 'pending',
                'approved': 'completed',
                'failed': 'failed',
                'canceled': 'failed',
                'expired': 'failed',
            }

            amount = Decimal('0.00')
            if payment.transactions:
                amount = Decimal(payment.transactions[0].amount.total)

            return {
                'success': True,
                'status': status_mapping.get(payment.state, 'pending'),
                'amount': amount,
                'currency': payment.transactions[0].amount.currency if payment.transactions else 'USD',
                'message': f"Payment status: {payment.state}",
                'data': payment.to_dict(),
            }

        except Exception as e:
            return {
                'success': False,
                'status': 'failed',
                'message': f"Verification failed: {str(e)}",
                'data': {'error': str(e)},
            }

    def refund_payment(self, transaction_id: str, amount: Optional[Decimal] = None) -> Dict[str, Any]:
        """
        Refund a PayPal payment.

        Args:
            transaction_id: PayPal sale transaction ID
            amount: Amount to refund (None for full refund)

        Returns:
            Dict with refund result
        """
        try:
            sale = paypalrestsdk.Sale.find(transaction_id)

            refund_params = {}
            if amount:
                refund_params['amount'] = {
                    'total': str(amount),
                    'currency': sale.amount.currency,
                }

            refund = sale.refund(refund_params)

            if refund.success():
                return {
                    'success': True,
                    'refund_id': refund.id,
                    'amount': Decimal(refund.amount.total) if refund.amount else amount,
                    'message': "Refund processed successfully",
                    'data': refund.to_dict(),
                }
            else:
                return {
                    'success': False,
                    'refund_id': None,
                    'message': f"Refund failed: {refund.error}",
                    'data': {'error': refund.error},
                }

        except Exception as e:
            return {
                'success': False,
                'refund_id': None,
                'message': f"Refund failed: {str(e)}",
                'data': {'error': str(e)},
            }

    def execute_payment(self, payment_id: str, payer_id: str) -> Dict[str, Any]:
        """
        Execute an approved PayPal payment.

        Args:
            payment_id: PayPal payment ID
            payer_id: PayPal payer ID from return URL

        Returns:
            Dict with execution result
        """
        try:
            payment = paypalrestsdk.Payment.find(payment_id)

            if payment.execute({'payer_id': payer_id}):
                return {
                    'success': True,
                    'transaction_id': payment_id,
                    'message': "Payment executed successfully",
                    'data': payment.to_dict(),
                }
            else:
                return {
                    'success': False,
                    'message': f"Payment execution failed: {payment.error}",
                    'data': {'error': payment.error},
                }

        except Exception as e:
            return {
                'success': False,
                'message': f"Execution failed: {str(e)}",
                'data': {'error': str(e)},
            }
