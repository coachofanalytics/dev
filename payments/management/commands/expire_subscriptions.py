"""
Management command to expire subscriptions that have passed their end date.
Run this daily to clean up expired subscriptions.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from payments.models import UserSubscription
from payments.services.subscription_service import SubscriptionService


class Command(BaseCommand):
    help = 'Expire subscriptions that have passed their end date'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Perform a dry run without actually expiring subscriptions'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        self.stdout.write(self.style.SUCCESS('Starting subscription expiration process...'))

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No subscriptions will be expired'))

        # Find active subscriptions past their end date
        expired_subscriptions = UserSubscription.objects.filter(
            status='active',
            end_date__lt=timezone.now()
        ).select_related('user', 'plan')

        total_subscriptions = expired_subscriptions.count()
        self.stdout.write(f'Found {total_subscriptions} subscriptions to expire')

        if total_subscriptions == 0:
            self.stdout.write(self.style.SUCCESS('No subscriptions to expire'))
            return

        expired_count = 0

        for subscription in expired_subscriptions:
            days_past = (timezone.now() - subscription.end_date).days

            self.stdout.write(
                f'\nSubscription {subscription.id} for {subscription.user.username} '
                f'({subscription.plan.name}) - {days_past} days past expiry'
            )

            if dry_run:
                self.stdout.write(self.style.WARNING('  [DRY RUN] Would expire this subscription'))
                continue

            try:
                if SubscriptionService.expire_subscription(subscription):
                    expired_count += 1
                    self.stdout.write(self.style.SUCCESS('  ✓ Expired successfully'))
                    # TODO: Send expiration notification email
                else:
                    self.stdout.write(self.style.WARNING('  Already expired or invalid state'))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Error: {str(e)}'))

        # Summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('Expiration process completed'))
        if not dry_run:
            self.stdout.write(f'  Subscriptions expired: {expired_count}')
            self.stdout.write(f'  Total processed: {total_subscriptions}')
