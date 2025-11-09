"""
Batch Approval Cron Job
Processes batch timeouts and sends reminders

Run hourly via Heroku Scheduler:
heroku addons:create scheduler:standard --app codamakutano
heroku addons:open scheduler --app codamakutano
Add job: cd coda && python manage.py process_batch_approvals
Frequency: Every hour
"""

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from investing.models import SuggestedPosition
from investing.services.batch_approval_service import BatchApprovalService
from investing.services.notification_service import NotificationService
from investing.services.position_ranking_service import PositionRankingService


class Command(BaseCommand):
    help = 'Process batch approvals: check for expired batches and send reminders'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(
            f"Starting batch approval processing at {timezone.now()}"
        ))
        
        service = BatchApprovalService()
        notification_service = NotificationService()
        
        # 1. Process expired batches (24-hour timeout)
        self.stdout.write("Checking for expired batches...")
        result = service.process_expired_batches()
        
        if result['auto_approved_batches'] > 0:
            self.stdout.write(self.style.SUCCESS(
                f"🤖 Auto-approved {result['auto_approved_batches']} batches "
                f"({result['positions_auto_approved']} positions) after client timeout"
            ))
        else:
            self.stdout.write("✓ No batches needed auto-approval this cycle")
        
        if result['expired_batches'] > 0:
            self.stdout.write(self.style.WARNING(
                f"⚠️  Expired {result['expired_batches']} batches, "
                f"rejected {result['positions_rejected']} positions"
            ))
        else:
            self.stdout.write("✓ No expired batches")

        # 2. Auto-approve top ranked suggestions
        self.stdout.write("Selecting top ranked suggestions for auto-approval...")
        ranker = PositionRankingService()
        auto_positions, remaining = ranker.auto_approve_top_positions(
            SuggestedPosition.objects.filter(review_status='pending'),
            n=getattr(settings, 'AUTO_APPROVE_TOP_N', 2),
        )
        if auto_positions:
            notification_service.send_auto_suggestion_summary(auto_positions, remaining)
            self.stdout.write(self.style.SUCCESS(
                f"🤖 Auto-approved {len(auto_positions)} suggestion(s)"
            ))
        else:
            self.stdout.write("✓ No suggestions auto-approved this cycle")
        
        # 3. Send reminders (12 hours before deadline)
        self.stdout.write("Checking for batches needing reminders...")
        reminders_sent = service.send_batch_reminders()
        
        if reminders_sent > 0:
            self.stdout.write(self.style.SUCCESS(
                f"📧 Sent {reminders_sent} reminder notifications"
            ))
        else:
            self.stdout.write("✓ No reminders needed")
        
        # Summary
        self.stdout.write(self.style.SUCCESS(
            f"\n✅ Batch processing complete at {timezone.now()}\n"
            f"   Auto Approved: {result['auto_approved_batches']}\n"
            f"   Expired: {result['expired_batches']}\n"
            f"   Reminders: {reminders_sent}\n"
            f"   Suggestions Auto-Approved: {len(auto_positions)}\n"
        ))

