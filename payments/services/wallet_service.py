from decimal import Decimal
from typing import Dict, Any
from django.db import transaction as db_transaction
from ..models import Wallet, Transaction


class WalletService:
    """Service for managing wallet operations"""

    @staticmethod
    def credit_wallet(wallet: Wallet, amount: Decimal, transaction_type: str, metadata: Dict[str, Any] = None) -> Transaction:
        """
        Credit amount to wallet and create transaction record.

        Args:
            wallet: Wallet instance
            amount: Amount to credit
            transaction_type: Type of transaction
            metadata: Additional transaction data

        Returns:
            Transaction instance
        """
        with db_transaction.atomic():
            wallet.credit(amount)

            trans = Transaction.objects.create(
                user=wallet.user,
                wallet=wallet,
                transaction_type=transaction_type,
                amount=amount,
                currency=wallet.currency,
                payment_gateway='wallet',
                status='completed',
                metadata=metadata or {},
            )

            return trans

    @staticmethod
    def debit_wallet(wallet: Wallet, amount: Decimal, transaction_type: str, metadata: Dict[str, Any] = None) -> Transaction:
        """
        Debit amount from wallet and create transaction record.

        Args:
            wallet: Wallet instance
            amount: Amount to debit
            transaction_type: Type of transaction
            metadata: Additional transaction data

        Returns:
            Transaction instance
        """
        with db_transaction.atomic():
            if not wallet.has_sufficient_balance(amount):
                raise ValueError("Insufficient wallet balance")

            wallet.debit(amount)

            trans = Transaction.objects.create(
                user=wallet.user,
                wallet=wallet,
                transaction_type=transaction_type,
                amount=amount,
                currency=wallet.currency,
                payment_gateway='wallet',
                status='completed',
                metadata=metadata or {},
            )

            return trans

    @staticmethod
    def get_balance(wallet: Wallet) -> Decimal:
        """Get current wallet balance"""
        return wallet.balance

    @staticmethod
    def check_sufficient_balance(wallet: Wallet, amount: Decimal) -> bool:
        """Check if wallet has sufficient balance"""
        return wallet.has_sufficient_balance(amount)
