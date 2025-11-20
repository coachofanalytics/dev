"""
Management command to process subscription renewals.
Run this daily to check and process auto-renewals.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction as db_transaction
from datetime import timedelta
from payments.models import UserSubscription, Wallet, Transaction
from payments.services.subscription_service import SubscriptionService
from payments.services.transaction_service import TransactionService
from payments.services.payment_factory import PaymentGatewayFactory


class Command(BaseCommand):
    help = 'Process subscription auto-renewals'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days-before',
            type=int,
            default=1,
            help='Process renewals for subscriptions expiring within this many days (default: 1)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Perform a dry run without actually processing renewals'
        )

    def handle(self, *args, **options):
        days_before = options['days_before']
        dry_run = options['dry_run']

        self.stdout.write(self.style.SUCCESS(f'Starting subscription renewal process...'))
        self.stdout.write(f'Looking for subscriptions expiring within {days_before} days')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No actual renewals will be processed'))

        # Find subscriptions that need renewal
        renewal_date = timezone.now() + timedelta(days=days_before)

        subscriptions_to_renew = UserSubscription.objects.filter(
            status='active',
            auto_renew=True,
            end_date__lte=renewal_date,
            end_date__gte=timezone.now()
        ).select_related('user', 'plan')

        total_subscriptions = subscriptions_to_renew.count()
        self.stdout.write(f'Found {total_subscriptions} subscriptions to renew')

        if total_subscriptions == 0:
            self.stdout.write(self.style.SUCCESS('No subscriptions to renew'))
            return

        renewed_count = 0
        failed_count = 0

        for subscription in subscriptions_to_renew:
            self.stdout.write(f'\nProcessing subscription {subscription.id} for user {subscription.user.username}')

            if dry_run:
                self.stdout.write(self.style.WARNING(f'  [DRY RUN] Would renew for ${subscription.plan.price}'))
                continue

            try:
                # Attempt renewal
                success = self.process_renewal(subscription)

                if success:
                    renewed_count += 1
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Renewed successfully'))
                else:
                    failed_count += 1
                    self.stdout.write(self.style.ERROR(f'  ✗ Renewal failed'))

            except Exception as e:
                failed_count += 1
                self.stdout.write(self.style.ERROR(f'  ✗ Error: {str(e)}'))

        # Summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS(f'Renewal process completed'))
        if not dry_run:
            self.stdout.write(f'  Successfully renewed: {renewed_count}')
            self.stdout.write(f'  Failed: {failed_count}')
            self.stdout.write(f'  Total processed: {renewed_count + failed_count}')

    @db_transaction.atomic
    def process_renewal(self, subscription: UserSubscription) -> bool:
        """
        Process a single subscription renewal.

        Returns:
            True if successful, False otherwise
        """
        user = subscription.user
        plan = subscription.plan
        amount = plan.price

        # Get or create wallet
        wallet, _ = Wallet.objects.get_or_create(user=user)

        # Check wallet balance first
        if subscription.payment_method == 'wallet':
            if wallet.balance < amount:
                self.stdout.write(f'  Insufficient wallet balance (${wallet.balance} < ${amount})')
                # TODO: Send notification to user
                return False

        # Create transaction
        transaction = TransactionService.create_transaction(
            user=user,
            wallet=wallet,
            amount=amount,
            transaction_type='subscription_payment',
            payment_gateway=subscription.payment_method,
            status='pending',
            metadata={
                'subscription_id': subscription.id,
                'plan_id': plan.id,
                'auto_renewal': True
            }
        )

        # Process payment
        try:
            if subscription.payment_method == 'wallet':
                # Debit wallet
                if wallet.debit(amount):
                    transaction.status = 'completed'
                    transaction.save()
                else:
                    transaction.status = 'failed'
                    transaction.save()
                    return False
            else:
                # Use payment gateway
                # Note: This requires stored payment method - not fully implemented
                self.stdout.write(f'  Payment gateway renewal not yet implemented for {subscription.payment_method}')
                transaction.status = 'failed'
                transaction.save()
                return False

            # Renew subscription
            success, invoice = SubscriptionService.renew_subscription(subscription, transaction)

            if success:
                self.stdout.write(f'  New end date: {subscription.end_date}')
                # TODO: Send renewal confirmation email
                return True
            else:
                return False

        except Exception as e:
            self.stdout.write(f'  Payment error: {str(e)}')
            transaction.status = 'failed'
            transaction.save()
            return False
