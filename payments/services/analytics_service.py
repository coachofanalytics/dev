"""
Financial Analytics Service

Provides:
- Monthly deposits and spending summaries
- Balance change trends
- Transaction analytics
- Admin reporting
"""

from typing import Dict, Any, List, Optional
from django.db import models as django_models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta, date
import logging

from ..models import (
    Wallet, Transaction, UserSubscription,
    FinancialAnalytics, PaymentDispute
)

logger = logging.getLogger(__name__)


class FinancialAnalyticsService:
    """
    Service for financial analytics and reporting.
    """

    @classmethod
    def get_user_summary(cls, user: User, days: int = 30) -> Dict[str, Any]:
        """
        Get financial summary for a user.

        Args:
            user: User to get summary for
            days: Number of days to include

        Returns:
            Dictionary with financial summary
        """
        start_date = timezone.now() - timedelta(days=days)

        transactions = Transaction.objects.filter(
            user=user,
            status='completed',
            created_at__gte=start_date
        )

        # Calculate deposits
        deposits = transactions.filter(
            transaction_type='deposit'
        ).aggregate(
            total=django_models.Sum('amount'),
            count=django_models.Count('id')
        )

        # Calculate spending
        spending = transactions.filter(
            transaction_type__in=['subscription_payment', 'invoice_payment']
        ).aggregate(
            total=django_models.Sum('amount'),
            count=django_models.Count('id')
        )

        # Get wallet balance
        try:
            wallet = user.wallet
            current_balance = wallet.balance
        except Wallet.DoesNotExist:
            current_balance = Decimal('0.00')

        return {
            'period_days': days,
            'total_deposits': deposits['total'] or Decimal('0.00'),
            'deposit_count': deposits['count'] or 0,
            'total_spending': spending['total'] or Decimal('0.00'),
            'spending_count': spending['count'] or 0,
            'net_change': (deposits['total'] or Decimal('0.00')) - (spending['total'] or Decimal('0.00')),
            'current_balance': current_balance,
            'average_transaction': transactions.aggregate(avg=django_models.Avg('amount'))['avg'] or Decimal('0.00'),
        }

    @classmethod
    def get_monthly_breakdown(cls, user: User, months: int = 6) -> List[Dict[str, Any]]:
        """
        Get monthly breakdown of deposits and spending.

        Args:
            user: User to get breakdown for
            months: Number of months to include

        Returns:
            List of monthly summaries
        """
        results = []
        today = timezone.now().date()

        for i in range(months):
            # Calculate month boundaries
            if i == 0:
                month_end = today
            else:
                month_end = date(today.year, today.month, 1) - timedelta(days=1)
                for _ in range(i - 1):
                    month_end = date(month_end.year, month_end.month, 1) - timedelta(days=1)

            month_start = date(month_end.year, month_end.month, 1)

            transactions = Transaction.objects.filter(
                user=user,
                status='completed',
                created_at__date__gte=month_start,
                created_at__date__lte=month_end
            )

            deposits = transactions.filter(
                transaction_type='deposit'
            ).aggregate(total=django_models.Sum('amount'))['total'] or Decimal('0.00')

            spending = transactions.filter(
                transaction_type__in=['subscription_payment', 'invoice_payment']
            ).aggregate(total=django_models.Sum('amount'))['total'] or Decimal('0.00')

            results.append({
                'month': month_start.strftime('%B %Y'),
                'month_start': month_start,
                'month_end': month_end,
                'deposits': deposits,
                'spending': spending,
                'net': deposits - spending,
            })

        return results

    @classmethod
    def get_transaction_breakdown_by_type(cls, user: User, days: int = 30) -> Dict[str, Any]:
        """
        Get transaction breakdown by type.
        """
        start_date = timezone.now() - timedelta(days=days)

        transactions = Transaction.objects.filter(
            user=user,
            status='completed',
            created_at__gte=start_date
        ).values('transaction_type').annotate(
            total=django_models.Sum('amount'),
            count=django_models.Count('id')
        )

        return {item['transaction_type']: {
            'total': item['total'],
            'count': item['count']
        } for item in transactions}

    @classmethod
    def get_payment_method_breakdown(cls, user: User, days: int = 30) -> Dict[str, Any]:
        """
        Get transaction breakdown by payment method.
        """
        start_date = timezone.now() - timedelta(days=days)

        transactions = Transaction.objects.filter(
            user=user,
            status='completed',
            created_at__gte=start_date
        ).values('payment_gateway').annotate(
            total=django_models.Sum('amount'),
            count=django_models.Count('id')
        )

        return {item['payment_gateway']: {
            'total': item['total'],
            'count': item['count']
        } for item in transactions}

    @classmethod
    def calculate_and_store_analytics(cls, user: User, period_type: str = 'monthly') -> FinancialAnalytics:
        """
        Calculate and store financial analytics for a user.
        """
        today = timezone.now().date()

        if period_type == 'daily':
            period_start = today - timedelta(days=1)
            period_end = today - timedelta(days=1)
        elif period_type == 'weekly':
            period_start = today - timedelta(days=7)
            period_end = today - timedelta(days=1)
        else:  # monthly
            period_start = date(today.year, today.month, 1) - timedelta(days=1)
            period_start = date(period_start.year, period_start.month, 1)
            period_end = date(today.year, today.month, 1) - timedelta(days=1)

        transactions = Transaction.objects.filter(
            user=user,
            status='completed',
            created_at__date__gte=period_start,
            created_at__date__lte=period_end
        )

        deposits = transactions.filter(
            transaction_type='deposit'
        ).aggregate(total=django_models.Sum('amount'))['total'] or Decimal('0.00')

        spending = transactions.filter(
            transaction_type__in=['subscription_payment', 'invoice_payment']
        ).aggregate(total=django_models.Sum('amount'))['total'] or Decimal('0.00')

        total_count = transactions.count()
        avg_amount = transactions.aggregate(avg=django_models.Avg('amount'))['avg'] or Decimal('0.00')

        # Get wallet balance
        try:
            closing_balance = user.wallet.balance
        except Wallet.DoesNotExist:
            closing_balance = Decimal('0.00')

        opening_balance = closing_balance - deposits + spending

        analytics, created = FinancialAnalytics.objects.update_or_create(
            user=user,
            period_type=period_type,
            period_start=period_start,
            defaults={
                'period_end': period_end,
                'total_deposits': deposits,
                'total_spending': spending,
                'total_transactions': total_count,
                'average_transaction': avg_amount,
                'opening_balance': opening_balance,
                'closing_balance': closing_balance,
            }
        )

        return analytics

    @classmethod
    def get_admin_dashboard_stats(cls) -> Dict[str, Any]:
        """
        Get statistics for admin dashboard.
        """
        today = timezone.now()
        start_of_day = today.replace(hour=0, minute=0, second=0, microsecond=0)
        start_of_week = start_of_day - timedelta(days=today.weekday())
        start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Today's transactions
        today_transactions = Transaction.objects.filter(
            created_at__gte=start_of_day
        )
        today_completed = today_transactions.filter(status='completed')
        today_failed = today_transactions.filter(status='failed')

        # This week
        week_transactions = Transaction.objects.filter(
            created_at__gte=start_of_week
        )
        week_completed = week_transactions.filter(status='completed')

        # This month
        month_transactions = Transaction.objects.filter(
            created_at__gte=start_of_month
        )
        month_completed = month_transactions.filter(status='completed')

        # Active subscriptions
        active_subscriptions = UserSubscription.objects.filter(status='active').count()
        expiring_soon = UserSubscription.objects.filter(
            status='active',
            end_date__lte=today + timedelta(days=7),
            end_date__gt=today
        ).count()

        # Disputes
        open_disputes = PaymentDispute.objects.filter(
            status__in=['open', 'under_review']
        ).count()

        return {
            'today': {
                'total_transactions': today_transactions.count(),
                'completed': today_completed.count(),
                'failed': today_failed.count(),
                'volume': today_completed.aggregate(total=django_models.Sum('amount'))['total'] or Decimal('0.00'),
            },
            'this_week': {
                'total_transactions': week_transactions.count(),
                'completed': week_completed.count(),
                'volume': week_completed.aggregate(total=django_models.Sum('amount'))['total'] or Decimal('0.00'),
            },
            'this_month': {
                'total_transactions': month_transactions.count(),
                'completed': month_completed.count(),
                'volume': month_completed.aggregate(total=django_models.Sum('amount'))['total'] or Decimal('0.00'),
            },
            'subscriptions': {
                'active': active_subscriptions,
                'expiring_soon': expiring_soon,
            },
            'disputes': {
                'open': open_disputes,
            },
        }

    @classmethod
    def get_revenue_by_period(cls, period: str = 'daily', count: int = 30) -> List[Dict[str, Any]]:
        """
        Get revenue data for charting.

        Args:
            period: 'daily', 'weekly', or 'monthly'
            count: Number of periods to include
        """
        results = []
        today = timezone.now().date()

        for i in range(count):
            if period == 'daily':
                period_end = today - timedelta(days=i)
                period_start = period_end
                label = period_end.strftime('%Y-%m-%d')
            elif period == 'weekly':
                period_end = today - timedelta(weeks=i)
                period_start = period_end - timedelta(days=6)
                label = f"Week of {period_start.strftime('%Y-%m-%d')}"
            else:  # monthly
                month_date = today - timedelta(days=30 * i)
                period_start = date(month_date.year, month_date.month, 1)
                if month_date.month == 12:
                    period_end = date(month_date.year + 1, 1, 1) - timedelta(days=1)
                else:
                    period_end = date(month_date.year, month_date.month + 1, 1) - timedelta(days=1)
                label = period_start.strftime('%B %Y')

            revenue = Transaction.objects.filter(
                status='completed',
                transaction_type__in=['subscription_payment', 'invoice_payment'],
                created_at__date__gte=period_start,
                created_at__date__lte=period_end
            ).aggregate(total=django_models.Sum('amount'))['total'] or Decimal('0.00')

            deposits = Transaction.objects.filter(
                status='completed',
                transaction_type='deposit',
                created_at__date__gte=period_start,
                created_at__date__lte=period_end
            ).aggregate(total=django_models.Sum('amount'))['total'] or Decimal('0.00')

            results.append({
                'period': label,
                'period_start': period_start,
                'period_end': period_end,
                'revenue': revenue,
                'deposits': deposits,
            })

        return list(reversed(results))

    @classmethod
    def get_subscription_analytics(cls) -> Dict[str, Any]:
        """
        Get subscription-related analytics.
        """
        from ..models import SubscriptionPlan

        total_subscriptions = UserSubscription.objects.count()
        active_subscriptions = UserSubscription.objects.filter(status='active').count()
        cancelled_subscriptions = UserSubscription.objects.filter(status='cancelled').count()
        expired_subscriptions = UserSubscription.objects.filter(status='expired').count()

        # Subscriptions by plan
        by_plan = UserSubscription.objects.filter(
            status='active'
        ).values('plan__name').annotate(
            count=django_models.Count('id')
        )

        # Monthly recurring revenue (MRR)
        mrr = UserSubscription.objects.filter(
            status='active'
        ).aggregate(
            total=django_models.Sum('plan__price')
        )['total'] or Decimal('0.00')

        # Churn rate (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        churned = UserSubscription.objects.filter(
            status='cancelled',
            updated_at__gte=thirty_days_ago
        ).count()

        active_30_days_ago = active_subscriptions + churned
        churn_rate = (churned / active_30_days_ago * 100) if active_30_days_ago > 0 else 0

        return {
            'total': total_subscriptions,
            'active': active_subscriptions,
            'cancelled': cancelled_subscriptions,
            'expired': expired_subscriptions,
            'by_plan': {item['plan__name']: item['count'] for item in by_plan},
            'mrr': mrr,
            'churn_rate': round(churn_rate, 2),
        }
