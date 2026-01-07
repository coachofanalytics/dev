"""
Celery Tasks for Payments App
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Transaction, UserSubscription
from .services.retry_service import PaymentRetryService
from .services.subscription_service import SubscriptionService
import logging

logger = logging.getLogger(__name__)


@shared_task(name='payments.tasks.retry_failed_payment')
def retry_failed_payment(transaction_id: int):
    """
    Retry a failed payment transaction.

    Args:
        transaction_id: ID of the transaction to retry
    """
    try:
        transaction = Transaction.objects.get(id=transaction_id)
        logger.info(f"Retrying transaction {transaction.transaction_id}")

        result = PaymentRetryService.retry_transaction(transaction)

        if result['success']:
            logger.info(f"Transaction {transaction.transaction_id} retry successful")
        else:
            logger.warning(f"Transaction {transaction.transaction_id} retry failed: {result['message']}")

            # Schedule next retry if eligible
            if result.get('will_retry_again'):
                next_retry_time = PaymentRetryService.get_next_retry_time(transaction)
                if next_retry_time:
                    # Schedule task for next retry
                    retry_failed_payment.apply_async(
                        args=[transaction_id],
                        eta=next_retry_time
                    )
                    logger.info(f"Scheduled next retry for {next_retry_time}")

        return result

    except Transaction.DoesNotExist:
        logger.error(f"Transaction {transaction_id} not found")
        return {'success': False, 'message': 'Transaction not found'}
    except Exception as e:
        logger.error(f"Error retrying transaction {transaction_id}: {str(e)}")
        return {'success': False, 'message': str(e)}


@shared_task(name='payments.tasks.check_pending_transactions_task')
def check_pending_transactions_task():
    """
    Check for pending transactions that need retry.
    This task runs periodically (every 30 minutes).
    """
    try:
        logger.info("Checking for transactions to retry...")

        transactions_to_retry = PaymentRetryService.get_transactions_to_retry()

        logger.info(f"Found {len(transactions_to_retry)} transactions to retry")

        for transaction in transactions_to_retry:
            # Queue retry task
            retry_failed_payment.delay(transaction.id)
            logger.info(f"Queued retry for transaction {transaction.transaction_id}")

        return {
            'success': True,
            'transactions_queued': len(transactions_to_retry)
        }

    except Exception as e:
        logger.error(f"Error checking pending transactions: {str(e)}")
        return {'success': False, 'message': str(e)}


@shared_task(name='payments.tasks.expire_subscriptions_task')
def expire_subscriptions_task():
    """
    Expire subscriptions that have passed their end date.
    This task runs daily at 2 AM.
    """
    try:
        logger.info("Checking for subscriptions to expire...")

        # Get active subscriptions past their end date
        expired_subscriptions = UserSubscription.objects.filter(
            status='active',
            end_date__lt=timezone.now()
        )

        count = 0
        for subscription in expired_subscriptions:
            if SubscriptionService.expire_subscription(subscription):
                count += 1
                logger.info(f"Expired subscription {subscription.id} for user {subscription.user.username}")

        logger.info(f"Expired {count} subscriptions")

        return {
            'success': True,
            'subscriptions_expired': count
        }

    except Exception as e:
        logger.error(f"Error expiring subscriptions: {str(e)}")
        return {'success': False, 'message': str(e)}


@shared_task(name='payments.tasks.cancel_old_pending_transactions')
def cancel_old_pending_transactions():
    """
    Cancel pending transactions older than the timeout period.
    """
    try:
        from django.conf import settings

        timeout_seconds = getattr(settings, 'TRANSACTION_TIMEOUT_SECONDS', 300)
        cutoff_time = timezone.now() - timedelta(seconds=timeout_seconds)

        old_pending = Transaction.objects.filter(
            status='pending',
            created_at__lt=cutoff_time
        )

        count = old_pending.update(status='cancelled')
        logger.info(f"Cancelled {count} old pending transactions")

        return {
            'success': True,
            'transactions_cancelled': count
        }

    except Exception as e:
        logger.error(f"Error cancelling old transactions: {str(e)}")
        return {'success': False, 'message': str(e)}
