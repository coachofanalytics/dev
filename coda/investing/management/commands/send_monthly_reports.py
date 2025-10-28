"""
Monthly Performance Reports
Send performance reports to all managed trading clients

Run monthly via Heroku Scheduler (1st of each month):
heroku addons:open scheduler --app codamakutano
Add job: cd coda && python manage.py send_monthly_reports
Frequency: Monthly (1st day, 09:00 UTC)
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from investing.services.performance_reporting_service import PerformanceReportingService


class Command(BaseCommand):
    help = 'Send monthly performance reports to all managed trading clients'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--month',
            type=int,
            help='Month number (1-12), defaults to last month'
        )
        parser.add_argument(
            '--year',
            type=int,
            help='Year, defaults to current year'
        )
    
    def handle(self, *args, **options):
        month = options.get('month')
        year = options.get('year')
        
        if not month or not year:
            # Default to last month
            last_month = timezone.now().replace(day=1) - timezone.timedelta(days=1)
            month = last_month.month
            year = last_month.year
        
        self.stdout.write(self.style.SUCCESS(
            f"Sending monthly reports for {month}/{year}"
        ))
        
        service = PerformanceReportingService()
        result = service.send_all_monthly_reports(month, year)
        
        self.stdout.write(self.style.SUCCESS(
            f"\n✅ Monthly report distribution complete:\n"
            f"   Reports Sent: {result['sent']}\n"
            f"   Failed: {result['failed']}\n"
            f"   Total Accounts: {result['total']}\n"
        ))
