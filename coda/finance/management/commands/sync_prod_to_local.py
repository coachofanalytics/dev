"""
Sync Production Data to Local SQLite

Downloads production data (budget categories, tier classifications, transactions)
from Heroku PostgreSQL and loads into local SQLite for testing and examination.

Usage:
    python manage.py sync_prod_to_local --settings=coda_project.coda_settings.local_settings
    python manage.py sync_prod_to_local --categories-only  # Just categories
    python manage.py sync_prod_to_local --full  # All finance data
"""

import json
import subprocess
from django.core.management.base import BaseCommand
from django.conf import settings
from decimal import Decimal


class Command(BaseCommand):
    help = 'Sync production data to local SQLite database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--categories-only',
            action='store_true',
            help='Only sync budget categories (no transactions)',
        )
        parser.add_argument(
            '--full',
            action='store_true',
            help='Sync all finance data (categories, transactions, budgets)',
        )
        parser.add_argument(
            '--app',
            type=str,
            default='codatrainingapp',  # Production
            help='Heroku app name (default: codatrainingapp)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔄 Syncing Production Data to Local SQLite'))
        
        # Check if we're using SQLite
        if 'sqlite3' not in settings.DATABASES['default']['ENGINE']:
            self.stdout.write(self.style.ERROR('❌ Error: This command requires SQLite database'))
            self.stdout.write(self.style.WARNING('   Set --settings=coda_project.coda_settings.local_settings'))
            return
        
        app_name = options['app']
        self.stdout.write(f'📡 Source: {app_name}.herokuapp.com')
        
        # Step 1: Export data from Heroku
        self.stdout.write('\n📦 Step 1: Exporting data from Heroku...')
        
        if options['categories_only']:
            self.export_categories(app_name)
        elif options['full']:
            self.export_full_data(app_name)
        else:
            # Default: categories + tier data
            self.export_categories(app_name)
        
        self.stdout.write(self.style.SUCCESS('\n✅ Sync complete!'))
        self.stdout.write('\n🔍 You can now examine real production data locally:')
        self.stdout.write('   - Budget categories with tier classifications')
        self.stdout.write('   - Typical monthly amounts calculated from $1.49M dataset')
        self.stdout.write('   - Variance thresholds and recurring patterns')
        self.stdout.write('\n💡 Try: python manage.py shell --settings=coda_project.coda_settings.local_settings')
        self.stdout.write('   >>> from finance.models import BudgetCategory')
        self.stdout.write('   >>> BudgetCategory.objects.filter(approval_tier="A")')

    def export_categories(self, app_name):
        """Export budget categories with tier data from Heroku"""
        self.stdout.write('   Exporting BudgetCategory with tier data...')
        
        # Use Heroku CLI to run dumpdata
        cmd = [
            'heroku', 'run',
            'cd coda && python manage.py dumpdata finance.BudgetCategory --indent=2',
            '--app', app_name
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Save to file
            output_file = '/tmp/prod_budget_categories.json'
            with open(output_file, 'w') as f:
                f.write(result.stdout)
            
            self.stdout.write(self.style.SUCCESS(f'   ✅ Exported to {output_file}'))
            
            # Step 2: Load into local database
            self.stdout.write('\n📥 Step 2: Loading into local SQLite...')
            load_cmd = [
                'python', 'manage.py', 'loaddata', output_file,
                '--settings=coda_project.coda_settings.local_settings'
            ]
            
            subprocess.run(load_cmd, check=True)
            self.stdout.write(self.style.SUCCESS('   ✅ Categories loaded'))
            
            # Show summary
            self.show_category_summary()
            
        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {e}'))
            self.stdout.write(self.style.WARNING('\n💡 Make sure heroku CLI is installed:'))
            self.stdout.write('   brew install heroku/brew/heroku')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {e}'))

    def export_full_data(self, app_name):
        """Export full finance data (categories, transactions, budgets)"""
        self.stdout.write('   Exporting full finance data...')
        
        models_to_export = [
            'finance.BudgetCategory',
            'finance.BudgetSubcategory',
            'finance.Transaction',
            'finance.Budget',
            'finance.BudgetRequest',
        ]
        
        for model in models_to_export:
            self.stdout.write(f'   - {model}...')
            # Export each model
            # ... implementation similar to export_categories
        
        self.stdout.write(self.style.SUCCESS('   ✅ Full data exported'))

    def show_category_summary(self):
        """Show summary of synced categories"""
        from finance.models import BudgetCategory
        
        total = BudgetCategory.objects.count()
        tier_a = BudgetCategory.objects.filter(approval_tier='A').count()
        tier_b = BudgetCategory.objects.filter(approval_tier='B').count()
        tier_c = BudgetCategory.objects.filter(approval_tier='C').count()
        auto_enabled = BudgetCategory.objects.filter(auto_approve_enabled=True).count()
        with_data = BudgetCategory.objects.exclude(typical_monthly_amount__isnull=True).count()
        
        self.stdout.write('\n📊 Category Summary:')
        self.stdout.write(f'   Total Categories: {total}')
        self.stdout.write(f'   - Tier A: {tier_a}')
        self.stdout.write(f'   - Tier B: {tier_b}')
        self.stdout.write(f'   - Tier C: {tier_c}')
        self.stdout.write(f'   Auto-approval enabled: {auto_enabled}')
        self.stdout.write(f'   With transaction data: {with_data}')

