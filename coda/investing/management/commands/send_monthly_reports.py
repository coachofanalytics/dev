from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from investing.services.investment_reporting_service import InvestmentReportingService
from investing.models import IndividualInvestment

User = get_user_model()


class Command(BaseCommand):
    help = 'Send monthly investment reports to all investors'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without actually sending emails',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN: No emails will be sent')
            )
        
        # Get all users with active investments
        users_with_investments = User.objects.filter(
            individualinvestment__isnull=False
        ).distinct()
        
        reporting_service = InvestmentReportingService()
        success_count = 0
        error_count = 0
        
        for user in users_with_investments:
            try:
                # Check if user wants monthly reports
                investments = IndividualInvestment.objects.filter(user=user)
                if not any(inv.monthly_reports for inv in investments):
                    self.stdout.write(
                        f'Skipping {user.email} - monthly reports disabled'
                    )
                    continue
                
                if not dry_run:
                    result = reporting_service.generate_monthly_report(user)
                    if result.get('success'):
                        success_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'Report sent to {user.email}')
                        )
                    else:
                        error_count += 1
                        self.stdout.write(
                            self.style.ERROR(f'Failed to send report to {user.email}: {result.get("error")}')
                        )
                else:
                    self.stdout.write(f'Would send report to {user.email}')
                    success_count += 1
                    
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'Error processing {user.email}: {str(e)}')
                )
        
        # Summary
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(f'DRY RUN COMPLETE: Would send {success_count} reports')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'COMPLETE: Sent {success_count} reports, {error_count} errors')
            )
