"""
Weekly Batch Creation
Creates position batches for all active accounts

Run weekly via Heroku Scheduler (e.g., every Friday at 5 PM):
heroku addons:open scheduler --app codamakutano
Add job: cd coda && python manage.py create_weekly_batches
Frequency: Weekly (Friday 17:00 UTC)
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from investing.services.batch_approval_service import BatchApprovalService


class Command(BaseCommand):
    help = 'Create weekly position batches for all active managed accounts'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(
            f"Creating weekly batches at {timezone.now()}"
        ))
        
        service = BatchApprovalService()
        result = service.create_batches_for_all_accounts()
        
        self.stdout.write(self.style.SUCCESS(
            f"\n✅ Weekly batch creation complete:\n"
            f"   Total Accounts: {result['total_accounts']}\n"
            f"   Accounts with Positions: {result['accounts_with_positions']}\n"
            f"   Batches Created: {result['batches_created']}\n"
        ))
        
        if result['batches_created'] > 0:
            self.stdout.write(self.style.SUCCESS(
                f"📧 {result['batches_created']} notification emails sent to clients"
            ))

