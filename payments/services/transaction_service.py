"""
Transaction Service
Handles all transaction-related business logic.
"""
from decimal import Decimal
from typing import Dict, Any, Optional
from django.contrib.auth.models import User
from django.db import transaction as db_transaction
from ..models import Transaction, Wallet


class TransactionService:
    """Service for managing wallet transactions"""

    @staticmethod
    def create_transaction(
        user: User,
        wallet: Wallet,
        amount: Decimal,
        transaction_type: str,
        payment_gateway: str,
        status: str = 'pending',
        gateway_transaction_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Transaction:
        """
        Create a new transaction record.

        Args:
            user: User making the transaction
            wallet: User's wallet
            amount: Transaction amount
            transaction_type: Type of transaction (deposit, withdrawal, payment, refund)
            payment_gateway: Payment gateway used (stripe, paypal, mpesa, wallet)
            status: Transaction status (pending, completed, failed, cancelled)
            gateway_transaction_id: External transaction ID from payment gateway
            metadata: Additional transaction metadata

        Returns:
            Created Transaction instance
        """
        transaction = Transaction.objects.create(
            user=user,
            wallet=wallet,
            amount=amount,
            transaction_type=transaction_type,
            payment_gateway=payment_gateway,
            status=status,
            gateway_transaction_id=gateway_transaction_id,
            metadata=metadata or {}
        )
        return transaction

    @staticmethod
    @db_transaction.atomic
    def complete_deposit(transaction: Transaction) -> bool:
        """
        Complete a deposit transaction and credit wallet.

        Args:
            transaction: The pending deposit transaction

        Returns:
            True if successful, False otherwise
        """
        if transaction.status != 'pending':
            return False

        if transaction.transaction_type != 'deposit':
            return False

        # Credit wallet
        wallet = transaction.wallet
        if wallet.credit(transaction.amount):
            transaction.status = 'completed'
            transaction.save()
            return True

        return False

    @staticmethod
    @db_transaction.atomic
    def fail_transaction(transaction: Transaction, error_message: str = '') -> bool:
        """
        Mark a transaction as failed.

        Args:
            transaction: The transaction to fail
            error_message: Optional error message

        Returns:
            True if successful
        """
        transaction.status = 'failed'
        if error_message:
            if not transaction.metadata:
                transaction.metadata = {}
            transaction.metadata['error'] = error_message
        transaction.save()
        return True

    @staticmethod
    @db_transaction.atomic
    def cancel_transaction(transaction: Transaction, reason: str = '') -> bool:
        """
        Cancel a transaction.

        Args:
            transaction: The transaction to cancel
            reason: Optional cancellation reason

        Returns:
            True if successful
        """
        if transaction.status == 'completed':
            return False  # Cannot cancel completed transactions

        transaction.status = 'cancelled'
        if reason:
            if not transaction.metadata:
                transaction.metadata = {}
            transaction.metadata['cancellation_reason'] = reason
        transaction.save()
        return True

    @staticmethod
    @db_transaction.atomic
    def process_refund(
        original_transaction: Transaction,
        refund_amount: Optional[Decimal] = None
    ) -> Optional[Transaction]:
        """
        Process a refund for a completed transaction.

        Args:
            original_transaction: The original transaction to refund
            refund_amount: Amount to refund (None for full refund)

        Returns:
            Created refund Transaction or None if failed
        """
        if original_transaction.status != 'completed':
            return None

        if original_transaction.transaction_type != 'deposit':
            return None

        # Determine refund amount
        amount = refund_amount or original_transaction.amount
        if amount > original_transaction.amount:
            return None

        # Check if wallet has sufficient balance
        wallet = original_transaction.wallet
        if wallet.balance < amount:
            return None

        # Debit wallet
        if wallet.debit(amount):
            # Create refund transaction
            refund_transaction = Transaction.objects.create(
                user=original_transaction.user,
                wallet=wallet,
                amount=amount,
                transaction_type='refund',
                payment_gateway=original_transaction.payment_gateway,
                status='completed',
                gateway_transaction_id=original_transaction.gateway_transaction_id,
                metadata={
                    'original_transaction_id': original_transaction.id,
                    'refund_type': 'partial' if amount < original_transaction.amount else 'full'
                }
            )
            return refund_transaction

        return None

    @staticmethod
    def update_gateway_transaction_id(
        transaction: Transaction,
        gateway_transaction_id: str
    ) -> bool:
        """
        Update the gateway transaction ID for a transaction.

        Args:
            transaction: The transaction to update
            gateway_transaction_id: The gateway transaction ID

        Returns:
            True if successful
        """
        transaction.gateway_transaction_id = gateway_transaction_id
        transaction.save(update_fields=['gateway_transaction_id'])
        return True

    @staticmethod
    def increment_retry_count(transaction: Transaction) -> int:
        """
        Increment the retry count for a failed transaction.

        Args:
            transaction: The transaction to update

        Returns:
            New retry count
        """
        if not hasattr(transaction, 'retry_count'):
            transaction.retry_count = 0

        transaction.retry_count += 1
        transaction.save(update_fields=['retry_count'])
        return transaction.retry_count
