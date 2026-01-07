"""
Payment Retry Service
Handles retry logic for failed payment transactions.
"""
from datetime import timedelta
from decimal import Decimal
from typing import Optional, Dict, Any
from django.utils import timezone
from ..models import Transaction
from ..exceptions import InvalidTransactionStateError, PaymentGatewayError
from .payment_factory import PaymentGatewayFactory


class PaymentRetryService:
    """Service for retrying failed payment transactions"""

    # Maximum number of retry attempts
    MAX_RETRY_ATTEMPTS = 3

    # Exponential backoff delays (in hours)
    RETRY_DELAYS = [1, 4, 24]  # 1 hour, 4 hours, 24 hours

    @staticmethod
    def can_retry(transaction: Transaction) -> tuple[bool, str]:
        """
        Check if a transaction can be retried.

        Args:
            transaction: The transaction to check

        Returns:
            Tuple of (can_retry: bool, reason: str)
        """
        # Only retry failed or pending transactions
        if transaction.status not in ['failed', 'pending']:
            return False, "Transaction is not in failed or pending state"

        # Check retry count
        if transaction.retry_count >= PaymentRetryService.MAX_RETRY_ATTEMPTS:
            return False, f"Maximum retry attempts ({PaymentRetryService.MAX_RETRY_ATTEMPTS}) reached"

        # Only retry deposit transactions
        if transaction.transaction_type != 'deposit':
            return False, "Only deposit transactions can be retried"

        # Check if enough time has passed since last attempt
        if transaction.retry_count > 0:
            required_delay_hours = PaymentRetryService.RETRY_DELAYS[transaction.retry_count - 1]
            required_delay = timedelta(hours=required_delay_hours)
            time_since_update = timezone.now() - transaction.updated_at

            if time_since_update < required_delay:
                return False, f"Too soon to retry. Wait {required_delay_hours} hours between attempts"

        return True, "Can retry"

    @staticmethod
    def get_next_retry_time(transaction: Transaction) -> Optional[timezone.datetime]:
        """
        Calculate when the next retry should occur.

        Args:
            transaction: The transaction

        Returns:
            Next retry datetime or None if no more retries
        """
        if transaction.retry_count >= PaymentRetryService.MAX_RETRY_ATTEMPTS:
            return None

        delay_hours = PaymentRetryService.RETRY_DELAYS[transaction.retry_count]
        return transaction.updated_at + timedelta(hours=delay_hours)

    @staticmethod
    def retry_transaction(transaction: Transaction) -> Dict[str, Any]:
        """
        Retry a failed transaction.

        Args:
            transaction: The transaction to retry

        Returns:
            Dict with retry result
        """
        # Check if can retry
        can_retry, reason = PaymentRetryService.can_retry(transaction)
        if not can_retry:
            return {
                'success': False,
                'message': reason,
                'transaction_id': transaction.id
            }

        try:
            # Get payment gateway
            payment_gateway = PaymentGatewayFactory.create_gateway(transaction.payment_gateway)

            # Prepare payment data
            metadata = transaction.metadata.copy() if transaction.metadata else {}
            metadata['retry_attempt'] = transaction.retry_count + 1
            metadata['original_transaction_id'] = transaction.transaction_id

            # Attempt payment
            payment_result = payment_gateway.process_payment(
                amount=transaction.amount,
                currency=transaction.currency,
                metadata=metadata
            )

            # Update transaction
            transaction.retry_count += 1

            if payment_result.get('success'):
                # Payment succeeded
                transaction.status = 'completed'
                transaction.gateway_transaction_id = payment_result.get('transaction_id')

                # Credit wallet if deposit
                if transaction.transaction_type == 'deposit' and transaction.wallet:
                    transaction.wallet.credit(transaction.amount)

                transaction.save()

                return {
                    'success': True,
                    'message': 'Payment retry successful',
                    'transaction_id': transaction.id,
                    'gateway_transaction_id': payment_result.get('transaction_id')
                }
            else:
                # Payment failed again
                transaction.status = 'failed'
                if not transaction.metadata:
                    transaction.metadata = {}
                transaction.metadata['last_retry_error'] = payment_result.get('message', 'Unknown error')
                transaction.metadata['last_retry_at'] = timezone.now().isoformat()
                transaction.save()

                return {
                    'success': False,
                    'message': f"Retry failed: {payment_result.get('message')}",
                    'transaction_id': transaction.id,
                    'will_retry_again': transaction.retry_count < PaymentRetryService.MAX_RETRY_ATTEMPTS
                }

        except Exception as e:
            # Handle unexpected errors
            transaction.retry_count += 1
            transaction.status = 'failed'
            if not transaction.metadata:
                transaction.metadata = {}
            transaction.metadata['last_retry_error'] = str(e)
            transaction.metadata['last_retry_at'] = timezone.now().isoformat()
            transaction.save()

            return {
                'success': False,
                'message': f"Retry error: {str(e)}",
                'transaction_id': transaction.id,
                'will_retry_again': transaction.retry_count < PaymentRetryService.MAX_RETRY_ATTEMPTS
            }

    @staticmethod
    def get_transactions_to_retry():
        """
        Get all transactions that are eligible for retry.

        Returns:
            QuerySet of transactions ready for retry
        """
        transactions_to_retry = []

        # Get failed and pending transactions with retries remaining
        candidates = Transaction.objects.filter(
            status__in=['failed', 'pending'],
            transaction_type='deposit',
            retry_count__lt=PaymentRetryService.MAX_RETRY_ATTEMPTS
        ).order_by('updated_at')

        for transaction in candidates:
            can_retry, _ = PaymentRetryService.can_retry(transaction)
            if can_retry:
                transactions_to_retry.append(transaction)

        return transactions_to_retry

    @staticmethod
    def cancel_retries(transaction: Transaction) -> bool:
        """
        Cancel further retry attempts for a transaction.

        Args:
            transaction: The transaction

        Returns:
            True if successful
        """
        transaction.retry_count = PaymentRetryService.MAX_RETRY_ATTEMPTS
        transaction.status = 'failed'
        if not transaction.metadata:
            transaction.metadata = {}
        transaction.metadata['retries_cancelled'] = True
        transaction.metadata['cancelled_at'] = timezone.now().isoformat()
        transaction.save()
        return True
