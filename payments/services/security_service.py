"""
Wallet Security and Fraud Prevention Service

Provides:
- Fraud detection and prevention
- Wallet activity logging
- Spending limits enforcement
- Suspicious activity detection
- Transaction velocity checks
"""

from typing import Dict, Any, Optional, List, Tuple
from django.db import models as django_models
from django.db import transaction as db_transaction
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
from decimal import Decimal
from datetime import timedelta
import logging

from ..models import (
    Wallet, Transaction, WalletActivityLog,
    WalletSpendingLimit, FraudAlert
)

logger = logging.getLogger(__name__)


class WalletSecurityService:
    """
    Service for wallet security and fraud prevention.
    """

    # Default limits (can be overridden in settings)
    DEFAULT_DAILY_LIMIT = Decimal('10000.00')
    DEFAULT_WEEKLY_LIMIT = Decimal('50000.00')
    DEFAULT_MONTHLY_LIMIT = Decimal('200000.00')
    DEFAULT_PER_TRANSACTION_LIMIT = Decimal('5000.00')

    # Fraud detection thresholds
    MAX_TRANSACTIONS_PER_HOUR = 10
    MAX_FAILED_ATTEMPTS_PER_HOUR = 5
    UNUSUAL_AMOUNT_MULTIPLIER = 5  # Flag if amount > 5x average

    @classmethod
    def log_activity(
        cls,
        user: User,
        action_type: str,
        description: str,
        wallet: Optional[Wallet] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        is_suspicious: bool = False
    ) -> WalletActivityLog:
        """
        Log wallet activity for audit trail.
        """
        log_entry = WalletActivityLog.objects.create(
            user=user,
            wallet=wallet,
            action_type=action_type,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {},
            is_suspicious=is_suspicious
        )

        if is_suspicious:
            logger.warning(
                f"Suspicious activity logged for user {user.username}: "
                f"{action_type} - {description}"
            )

        return log_entry

    @classmethod
    def check_transaction_velocity(cls, user: User) -> Tuple[bool, str]:
        """
        Check if user has exceeded transaction velocity limits.

        Returns:
            Tuple of (is_allowed, message)
        """
        one_hour_ago = timezone.now() - timedelta(hours=1)

        recent_transactions = Transaction.objects.filter(
            user=user,
            created_at__gte=one_hour_ago
        ).count()

        if recent_transactions >= cls.MAX_TRANSACTIONS_PER_HOUR:
            cls._create_fraud_alert(
                user=user,
                alert_type='velocity',
                severity='high',
                description=f"User exceeded transaction velocity limit: {recent_transactions} transactions in the last hour"
            )
            return False, f"Transaction limit exceeded. Please wait before making more transactions."

        return True, "OK"

    @classmethod
    def check_spending_limits(
        cls,
        wallet: Wallet,
        amount: Decimal
    ) -> Tuple[bool, str]:
        """
        Check if transaction amount is within spending limits.

        Returns:
            Tuple of (is_allowed, message)
        """
        # Check per-transaction limit
        per_txn_limit = cls._get_limit(wallet, 'per_transaction')
        if amount > per_txn_limit:
            return False, f"Amount exceeds per-transaction limit of {per_txn_limit}"

        # Check daily limit
        daily_spent = cls._get_spent_amount(wallet, days=1)
        daily_limit = cls._get_limit(wallet, 'daily')
        if daily_spent + amount > daily_limit:
            return False, f"Amount would exceed daily spending limit of {daily_limit}"

        # Check weekly limit
        weekly_spent = cls._get_spent_amount(wallet, days=7)
        weekly_limit = cls._get_limit(wallet, 'weekly')
        if weekly_spent + amount > weekly_limit:
            return False, f"Amount would exceed weekly spending limit of {weekly_limit}"

        # Check monthly limit
        monthly_spent = cls._get_spent_amount(wallet, days=30)
        monthly_limit = cls._get_limit(wallet, 'monthly')
        if monthly_spent + amount > monthly_limit:
            return False, f"Amount would exceed monthly spending limit of {monthly_limit}"

        return True, "OK"

    @classmethod
    def _get_limit(cls, wallet: Wallet, limit_type: str) -> Decimal:
        """Get the spending limit for a wallet."""
        try:
            limit = WalletSpendingLimit.objects.get(
                wallet=wallet,
                limit_type=limit_type,
                is_active=True
            )
            return limit.amount
        except WalletSpendingLimit.DoesNotExist:
            # Return default limits
            defaults = {
                'daily': cls.DEFAULT_DAILY_LIMIT,
                'weekly': cls.DEFAULT_WEEKLY_LIMIT,
                'monthly': cls.DEFAULT_MONTHLY_LIMIT,
                'per_transaction': cls.DEFAULT_PER_TRANSACTION_LIMIT,
            }
            return defaults.get(limit_type, cls.DEFAULT_DAILY_LIMIT)

    @classmethod
    def _get_spent_amount(cls, wallet: Wallet, days: int) -> Decimal:
        """Get total spent amount in the specified period."""
        start_date = timezone.now() - timedelta(days=days)

        spent = Transaction.objects.filter(
            wallet=wallet,
            status='completed',
            created_at__gte=start_date,
            transaction_type__in=['subscription_payment', 'invoice_payment', 'withdrawal']
        ).aggregate(total=django_models.Sum('amount'))['total']

        return spent or Decimal('0.00')

    @classmethod
    def check_unusual_amount(cls, user: User, amount: Decimal) -> Tuple[bool, str]:
        """
        Check if transaction amount is unusually high compared to user's history.
        """
        # Get user's average transaction amount
        avg_amount = Transaction.objects.filter(
            user=user,
            status='completed'
        ).aggregate(avg=django_models.Avg('amount'))['avg']

        if avg_amount and amount > (avg_amount * cls.UNUSUAL_AMOUNT_MULTIPLIER):
            cls._create_fraud_alert(
                user=user,
                alert_type='amount',
                severity='medium',
                description=f"Unusual transaction amount: {amount} (average: {avg_amount:.2f})",
                metadata={'amount': str(amount), 'average': str(avg_amount)}
            )
            # Still allow but flag for review
            return True, "Transaction flagged for review due to unusual amount"

        return True, "OK"

    @classmethod
    def check_failed_attempts(cls, user: User) -> Tuple[bool, str]:
        """
        Check for excessive failed transaction attempts.
        """
        one_hour_ago = timezone.now() - timedelta(hours=1)

        failed_count = Transaction.objects.filter(
            user=user,
            status='failed',
            created_at__gte=one_hour_ago
        ).count()

        if failed_count >= cls.MAX_FAILED_ATTEMPTS_PER_HOUR:
            cls._create_fraud_alert(
                user=user,
                alert_type='failed_attempts',
                severity='high',
                description=f"Multiple failed transaction attempts: {failed_count} in the last hour"
            )
            return False, "Too many failed attempts. Please contact support."

        return True, "OK"

    @classmethod
    def _create_fraud_alert(
        cls,
        user: User,
        alert_type: str,
        severity: str,
        description: str,
        wallet: Optional[Wallet] = None,
        transaction: Optional[Transaction] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> FraudAlert:
        """Create a fraud alert."""
        alert = FraudAlert.objects.create(
            user=user,
            wallet=wallet,
            transaction=transaction,
            alert_type=alert_type,
            severity=severity,
            description=description,
            metadata=metadata or {}
        )

        # Send notification
        from .notification_service import PaymentNotificationService
        PaymentNotificationService.send_suspicious_activity_alert(
            user=user,
            activity_type=alert_type,
            details={'description': description, **(metadata or {})}
        )

        logger.warning(f"Fraud alert created: {alert}")
        return alert

    @classmethod
    def perform_security_check(
        cls,
        user: User,
        wallet: Wallet,
        amount: Decimal,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, List[str]]:
        """
        Perform comprehensive security check before a transaction.

        Returns:
            Tuple of (is_allowed, list of warnings/errors)
        """
        messages = []

        # Check transaction velocity
        velocity_ok, velocity_msg = cls.check_transaction_velocity(user)
        if not velocity_ok:
            return False, [velocity_msg]

        # Check spending limits
        limits_ok, limits_msg = cls.check_spending_limits(wallet, amount)
        if not limits_ok:
            return False, [limits_msg]

        # Check failed attempts
        attempts_ok, attempts_msg = cls.check_failed_attempts(user)
        if not attempts_ok:
            return False, [attempts_msg]

        # Check unusual amount (warning only)
        amount_ok, amount_msg = cls.check_unusual_amount(user, amount)
        if amount_msg != "OK":
            messages.append(amount_msg)

        return True, messages

    @classmethod
    def set_spending_limit(
        cls,
        wallet: Wallet,
        limit_type: str,
        amount: Decimal,
        set_by: User
    ) -> WalletSpendingLimit:
        """
        Set or update a spending limit for a wallet.
        """
        limit, created = WalletSpendingLimit.objects.update_or_create(
            wallet=wallet,
            limit_type=limit_type,
            defaults={'amount': amount, 'is_active': True}
        )

        # Log the activity
        cls.log_activity(
            user=wallet.user,
            action_type='limit_change',
            description=f"{limit_type} limit {'set' if created else 'updated'} to {amount}",
            wallet=wallet,
            metadata={
                'limit_type': limit_type,
                'amount': str(amount),
                'set_by': set_by.username
            }
        )

        return limit

    @classmethod
    def get_user_activity_log(
        cls,
        user: User,
        days: int = 30,
        action_type: Optional[str] = None
    ) -> List[WalletActivityLog]:
        """
        Get activity log for a user.
        """
        start_date = timezone.now() - timedelta(days=days)

        queryset = WalletActivityLog.objects.filter(
            user=user,
            created_at__gte=start_date
        )

        if action_type:
            queryset = queryset.filter(action_type=action_type)

        return list(queryset)

    @classmethod
    def get_pending_fraud_alerts(cls, user: Optional[User] = None) -> List[FraudAlert]:
        """
        Get pending fraud alerts for review.
        """
        queryset = FraudAlert.objects.filter(status='pending')

        if user:
            queryset = queryset.filter(user=user)

        return list(queryset)

    @classmethod
    def resolve_fraud_alert(
        cls,
        alert: FraudAlert,
        status: str,
        reviewed_by: User,
        resolution_notes: str
    ) -> FraudAlert:
        """
        Resolve a fraud alert.
        """
        alert.status = status
        alert.reviewed_by = reviewed_by
        alert.reviewed_at = timezone.now()
        alert.resolution_notes = resolution_notes
        alert.save()

        logger.info(
            f"Fraud alert {alert.id} resolved by {reviewed_by.username}: "
            f"{status} - {resolution_notes}"
        )

        return alert
