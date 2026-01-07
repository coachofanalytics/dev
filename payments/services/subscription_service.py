"""
Subscription Service
Handles all subscription-related business logic.
"""
from decimal import Decimal
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.db import transaction as db_transaction
from django.utils import timezone
from ..models import SubscriptionPlan, UserSubscription, Invoice, Wallet, Transaction


class SubscriptionService:
    """Service for managing subscriptions"""

    @staticmethod
    @db_transaction.atomic
    def create_subscription(
        user: User,
        plan: SubscriptionPlan,
        payment_method: str,
        auto_renew: bool = True
    ) -> tuple[UserSubscription, Invoice]:
        """
        Create a new subscription for a user.

        Args:
            user: User subscribing
            plan: Subscription plan
            payment_method: Payment method used
            auto_renew: Whether to auto-renew

        Returns:
            Tuple of (UserSubscription, Invoice)
        """
        # Calculate dates
        start_date = timezone.now()
        end_date = start_date + timedelta(days=plan.duration_days)

        # Create subscription
        subscription = UserSubscription.objects.create(
            user=user,
            plan=plan,
            start_date=start_date,
            end_date=end_date,
            status='active',
            auto_renew=auto_renew,
            payment_method=payment_method
        )

        # Create invoice
        invoice = Invoice.objects.create(
            user=user,
            subscription=subscription,
            amount=plan.price,
            status='paid',
            payment_method=payment_method,
            paid_at=timezone.now()
        )

        return subscription, invoice

    @staticmethod
    @db_transaction.atomic
    def renew_subscription(
        subscription: UserSubscription,
        payment_transaction: Transaction
    ) -> tuple[bool, Optional[Invoice]]:
        """
        Renew an existing subscription.

        Args:
            subscription: The subscription to renew
            payment_transaction: The completed payment transaction

        Returns:
            Tuple of (success: bool, invoice: Optional[Invoice])
        """
        if payment_transaction.status != 'completed':
            return False, None

        # Extend subscription
        old_end_date = subscription.end_date
        new_end_date = old_end_date + timedelta(days=subscription.plan.duration_days)

        subscription.end_date = new_end_date
        subscription.status = 'active'
        subscription.save()

        # Create invoice
        invoice = Invoice.objects.create(
            user=subscription.user,
            subscription=subscription,
            amount=subscription.plan.price,
            status='paid',
            payment_method=payment_transaction.payment_gateway,
            paid_at=timezone.now(),
            metadata={
                'transaction_id': payment_transaction.id,
                'renewal': True,
                'previous_end_date': old_end_date.isoformat()
            }
        )

        return True, invoice

    @staticmethod
    def expire_subscription(subscription: UserSubscription) -> bool:
        """
        Mark a subscription as expired.

        Args:
            subscription: The subscription to expire

        Returns:
            True if successful
        """
        if subscription.status == 'active' and subscription.end_date < timezone.now():
            subscription.status = 'expired'
            subscription.save(update_fields=['status'])
            return True
        return False

    @staticmethod
    def cancel_subscription(subscription: UserSubscription, reason: str = '') -> bool:
        """
        Cancel a subscription.

        Args:
            subscription: The subscription to cancel
            reason: Optional cancellation reason

        Returns:
            True if successful
        """
        if subscription.status in ['cancelled', 'expired']:
            return False

        subscription.status = 'cancelled'
        subscription.auto_renew = False
        if reason:
            if not subscription.metadata:
                subscription.metadata = {}
            subscription.metadata['cancellation_reason'] = reason
            subscription.metadata['cancelled_at'] = timezone.now().isoformat()
        subscription.save()
        return True

    @staticmethod
    def get_active_subscription(user: User) -> Optional[UserSubscription]:
        """
        Get user's active subscription if any.

        Args:
            user: The user

        Returns:
            Active UserSubscription or None
        """
        return UserSubscription.objects.filter(
            user=user,
            status='active',
            end_date__gt=timezone.now()
        ).first()

    @staticmethod
    def needs_renewal(subscription: UserSubscription, days_before: int = 1) -> bool:
        """
        Check if subscription needs renewal.

        Args:
            subscription: The subscription to check
            days_before: Days before expiry to consider renewal

        Returns:
            True if needs renewal
        """
        if not subscription.auto_renew:
            return False

        if subscription.status != 'active':
            return False

        renewal_date = timezone.now() + timedelta(days=days_before)
        return subscription.end_date <= renewal_date

    @staticmethod
    @db_transaction.atomic
    def upgrade_subscription(
        subscription: UserSubscription,
        new_plan: SubscriptionPlan,
        payment_transaction: Transaction
    ) -> tuple[bool, Optional[UserSubscription], Optional[Invoice]]:
        """
        Upgrade subscription to a new plan with proration.

        Args:
            subscription: Current subscription
            new_plan: New plan to upgrade to
            payment_transaction: Payment transaction for upgrade

        Returns:
            Tuple of (success, new_subscription, invoice)
        """
        if payment_transaction.status != 'completed':
            return False, None, None

        if new_plan.price <= subscription.plan.price:
            return False, None, None  # Not an upgrade

        # Calculate prorated refund for unused time
        now = timezone.now()
        days_remaining = (subscription.end_date - now).days
        total_days = subscription.plan.duration_days

        if days_remaining > 0 and total_days > 0:
            refund_amount = (subscription.plan.price * days_remaining) / total_days
        else:
            refund_amount = Decimal('0.00')

        # Cancel old subscription
        subscription.status = 'cancelled'
        subscription.auto_renew = False
        subscription.save()

        # Create new subscription
        start_date = now
        end_date = start_date + timedelta(days=new_plan.duration_days)

        new_subscription = UserSubscription.objects.create(
            user=subscription.user,
            plan=new_plan,
            start_date=start_date,
            end_date=end_date,
            status='active',
            auto_renew=subscription.auto_renew,
            payment_method=payment_transaction.payment_gateway
        )

        # Create invoice
        invoice = Invoice.objects.create(
            user=subscription.user,
            subscription=new_subscription,
            amount=new_plan.price - refund_amount,
            status='paid',
            payment_method=payment_transaction.payment_gateway,
            paid_at=now,
            metadata={
                'transaction_id': payment_transaction.id,
                'upgrade': True,
                'old_plan_id': subscription.plan.id,
                'prorated_refund': float(refund_amount)
            }
        )

        # If there's a refund, credit it to wallet
        if refund_amount > 0:
            try:
                wallet = Wallet.objects.get(user=subscription.user)
                wallet.credit(refund_amount)
            except Wallet.DoesNotExist:
                pass

        return True, new_subscription, invoice

    @staticmethod
    @db_transaction.atomic
    def downgrade_subscription(
        subscription: UserSubscription,
        new_plan: SubscriptionPlan
    ) -> tuple[bool, str]:
        """
        Schedule downgrade to a new plan at end of current period.

        Args:
            subscription: Current subscription
            new_plan: New plan to downgrade to

        Returns:
            Tuple of (success, message)
        """
        if new_plan.price >= subscription.plan.price:
            return False, "Not a downgrade"

        if subscription.status != 'active':
            return False, "Subscription not active"

        # Schedule downgrade for end of period
        if not subscription.metadata:
            subscription.metadata = {}

        subscription.metadata['scheduled_downgrade'] = {
            'new_plan_id': new_plan.id,
            'scheduled_at': timezone.now().isoformat(),
            'effective_date': subscription.end_date.isoformat()
        }
        subscription.auto_renew = False  # Prevent auto-renewal
        subscription.save()

        return True, f"Downgrade scheduled for {subscription.end_date.strftime('%Y-%m-%d')}"
