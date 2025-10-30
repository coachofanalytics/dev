"""
Batch Approval Cron Job
Processes batch timeouts and sends reminders

Run hourly via Heroku Scheduler:
heroku addons:create scheduler:standard --app codamakutano
heroku addons:open scheduler --app codamakutano
Add job: cd coda && python manage.py process_batch_approvals
Frequency: Every hour
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from investing.services.batch_approval_service import BatchApprovalService


class Command(BaseCommand):
    help = 'Process batch approvals: check for expired batches and send reminders'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(
            f"Starting batch approval processing at {timezone.now()}"
        ))
        
        service = BatchApprovalService()
        
        # 1. Process expired batches (24-hour timeout)
        self.stdout.write("Checking for expired batches...")
        expired_result = service.process_expired_batches()
        
        if expired_result['expired_batches'] > 0:
            self.stdout.write(self.style.WARNING(
                f"⚠️  Expired {expired_result['expired_batches']} batches, "
                f"rejected {expired_result['positions_rejected']} positions"
            ))
        else:
            self.stdout.write("✓ No expired batches")
        
        # 2. Send reminders (12 hours before deadline)
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
            f"   Expired: {expired_result['expired_batches']}\n"
            f"   Reminders: {reminders_sent}\n"
        ))

