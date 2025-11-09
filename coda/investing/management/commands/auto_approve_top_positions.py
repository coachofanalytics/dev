"""
Automatically approve top-ranked suggested positions.

Run via scheduler:
heroku addons:open scheduler --app <app>
Add job: cd coda && python manage.py auto_approve_top_positions
Frequency: hourly (or as needed)
"""

from django.core.management.base import BaseCommand

from investing.models import SuggestedPosition
from investing.services.notification_service import NotificationService
from investing.services.position_ranking_service import PositionRankingService


class Command(BaseCommand):
    help = 'Automatically approve the top N ranked suggested positions using the AI ranking engine.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=2,
            help='Number of top-ranked positions to auto-approve (default: 2).',
        )

    def handle(self, *args, **options):
        count = options['count']
        self.stdout.write(self.style.SUCCESS("🤖 Starting auto-approve of top ranked suggestions"))

        pending = SuggestedPosition.objects.filter(review_status='pending')
        if not pending.exists():
            self.stdout.write("✓ No pending suggestions found.")
            return

        ranker = PositionRankingService()
        auto_positions, remaining = ranker.auto_approve_top_positions(pending, n=count)

        if not auto_positions:
            self.stdout.write("✓ No new suggestions met auto-approval criteria.")
            return

        NotificationService().send_auto_suggestion_summary(auto_positions, remaining)

        self.stdout.write(self.style.SUCCESS(
            f"✅ Auto-approved {len(auto_positions)} suggestion(s). "
            f"{len(remaining)} additional suggestions remain for review."
        ))

