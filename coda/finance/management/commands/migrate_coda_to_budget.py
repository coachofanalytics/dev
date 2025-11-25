"""
CodaBudget to Budget Migration Script

Phase 1 Task 1.4: Migrate all CodaBudget data to Budget model
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from finance.models import Budget, CodaBudget
from shared_core.users import CustomerUser
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Migrate CodaBudget data to Budget model - Phase 1 of consolidation"
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate migration without making changes'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed migration information'
        )
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            help='Skip records that have already been migrated'
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']
        skip_existing = options['skip_existing']
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        if dry_run:
            self.stdout.write(self.style.WARNING('CODABUDGET → BUDGET MIGRATION (DRY RUN)'))
        else:
            self.stdout.write(self.style.SUCCESS('CODABUDGET → BUDGET MIGRATION'))
        self.stdout.write(self.style.SUCCESS(f'Started: {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))
        
        # Get all CodaBudget records
        coda_budgets = CodaBudget.objects.all().select_related(
            'company', 'department', 'category', 'subcategory', 'budget_lead'
        )
        
        total_count = coda_budgets.count()
        self.stdout.write(f"Total CodaBudget records to migrate: {total_count}\n")
        
        if total_count == 0:
            self.stdout.write(self.style.WARNING("No CodaBudget records found to migrate."))
            return
        
        # Migration statistics
        stats = {
            'migrated': 0,
            'skipped': 0,
            'errors': 0,
            'warnings': []
        }
        
        # Process each CodaBudget record
        for i, coda_budget in enumerate(coda_budgets, 1):
            if verbose:
                self.stdout.write(f"\n[{i}/{total_count}] Processing CodaBudget ID: {coda_budget.id}")
            
            try:
                # Check if similar record already exists (skip exact duplicates)
                if skip_existing:
                    existing = Budget.objects.filter(
                        company=coda_budget.company,
                        department=coda_budget.department,
                        category=coda_budget.category,
                        subcategory=coda_budget.subcategory,
                        item_name=coda_budget.item,
                        quantity=coda_budget.qty,
                        unit_price=coda_budget.unit_price
                    ).first()
                    
                    if existing:
                        if verbose:
                            self.stdout.write(f"  → Already exists (Budget ID: {existing.id})")
                        stats['skipped'] += 1
                        continue
                
                # budget_lead from CodaBudget is already a User (CustomerUser extends AbstractUser)
                # Just use it directly
                budget_lead = coda_budget.budget_lead
                
                # Try to cast to CustomerUser if needed
                try:
                    budget_lead = CustomerUser.objects.get(id=budget_lead.id)
                except:
                    # If conversion fails, use the user directly
                    pass
                
                # Prepare Budget data
                budget_data = {
                    'company': coda_budget.company,
                    'department': coda_budget.department,
                    'budget_lead': budget_lead,
                    'category': coda_budget.category,
                    'subcategory': coda_budget.subcategory,
                    'item_name': coda_budget.item or f'Migrated from CodaBudget {coda_budget.id}',
                    'quantity': coda_budget.qty or Decimal('0.00'),
                    'unit_price': coda_budget.unit_price or Decimal('0.00'),
                    'description': coda_budget.description or f'Migrated from CodaBudget {coda_budget.id}',
                    'receipt_link': coda_budget.receipt_link or '',
                    'is_active': True,
                    
                    # Set created/updated timestamps
                    'created_at': coda_budget.created_at,
                    'updated_at': coda_budget.updated_at,
                    
                    # Set dates (default to creation date if not specified)
                    'start_date': coda_budget.created_at,
                    'end_date': coda_budget.created_at + timezone.timedelta(days=30),
                    
                    # Enhanced fields with defaults
                    'budget_type': 'general',
                    'timeframe': 'monthly',
                    'estimation_method': 'manual',
                    
                    # Additional fields
                    'cases': coda_budget.cases or 1,
                    'status': 'active',
                    'notes': f'Migrated from CodaBudget #{coda_budget.id} on {timezone.now().date()}',
                }
                
                if not dry_run:
                    with transaction.atomic():
                        # Create Budget record
                        new_budget = Budget.objects.create(**budget_data)
                        stats['migrated'] += 1
                        
                        if verbose:
                            self.stdout.write(self.style.SUCCESS(
                                f"  ✓ Migrated → Budget ID: {new_budget.id} "
                                f"(Amount: ${new_budget.total_amount:,.2f})"
                            ))
                else:
                    # Dry run - just show what would be done
                    stats['migrated'] += 1
                    if verbose:
                        amount = (coda_budget.qty or 0) * (coda_budget.unit_price or 0)
                        self.stdout.write(
                            f"  → Would migrate: {coda_budget.item} "
                            f"(Amount: ${amount:,.2f})"
                        )
                
                # Progress indicator
                if i % 10 == 0 and not verbose:
                    self.stdout.write(f"Progress: {i}/{total_count} records processed...")
                    
            except Exception as e:
                stats['errors'] += 1
                error_msg = f"CodaBudget {coda_budget.id}: {str(e)}"
                stats['warnings'].append(error_msg)
                self.stdout.write(self.style.ERROR(f"  ✗ Error: {error_msg}"))
                logger.error(f"Migration error for CodaBudget {coda_budget.id}: {e}", exc_info=True)
        
        # Print summary
        self._print_summary(stats, total_count, dry_run)
    
# Removed - CustomerUser IS the User model, no separate lookup needed
    
    def _print_summary(self, stats, total_count, dry_run):
        """Print migration summary"""
        self.stdout.write('\n' + '='*80)
        if dry_run:
            self.stdout.write(self.style.WARNING('MIGRATION SUMMARY (DRY RUN)'))
        else:
            self.stdout.write(self.style.SUCCESS('MIGRATION SUMMARY'))
        self.stdout.write('='*80)
        
        self.stdout.write(f"\nTotal CodaBudget records: {total_count}")
        self.stdout.write(self.style.SUCCESS(f"Successfully migrated:    {stats['migrated']}"))
        
        if stats['skipped'] > 0:
            self.stdout.write(self.style.WARNING(f"Skipped (already exist): {stats['skipped']}"))
        
        if stats['errors'] > 0:
            self.stdout.write(self.style.ERROR(f"Errors encountered:      {stats['errors']}"))
        
        # Print warnings
        if stats['warnings']:
            self.stdout.write(self.style.WARNING(f"\nWarnings ({len(stats['warnings'])}):"))
            for warning in stats['warnings'][:10]:  # Show first 10 warnings
                self.stdout.write(f"  ⚠️  {warning}")
            if len(stats['warnings']) > 10:
                self.stdout.write(f"  ... and {len(stats['warnings']) - 10} more warnings")
        
        # Success rate
        if total_count > 0:
            success_rate = (stats['migrated'] / total_count) * 100
            self.stdout.write(f"\nSuccess rate: {success_rate:.1f}%")
        
        # Next steps
        if dry_run:
            self.stdout.write('\n' + '-'*80)
            self.stdout.write('This was a DRY RUN - no changes were made.')
            self.stdout.write('To perform actual migration, run without --dry-run flag:')
            self.stdout.write('  python manage.py migrate_coda_to_budget')
        else:
            self.stdout.write('\n' + '-'*80)
            self.stdout.write(self.style.SUCCESS('MIGRATION COMPLETE!'))
            self.stdout.write('\nNext steps:')
            self.stdout.write('  1. Verify migrated data in Budget model')
            self.stdout.write('  2. Run: python manage.py audit_budget_usage')
            self.stdout.write('  3. Update code references to use Budget model')
            self.stdout.write('  4. Mark CodaBudget model as deprecated')
        
        self.stdout.write('='*80 + '\n')

