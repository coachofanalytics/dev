"""
Cleanup duplicate CodaBudget entries that were created by the sync signal
"""
from django.core.management.base import BaseCommand
from django.db.models import Count
from finance.models import CodaBudget


class Command(BaseCommand):
    help = 'Remove duplicate CodaBudget entries, keeping the most recent one'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        self.stdout.write("="*80)
        self.stdout.write("CLEANUP DUPLICATE CODABUDGET ENTRIES")
        self.stdout.write("="*80)
        
        # Find duplicates based on the unique combination used in the signal
        # Group by all the fields that should be unique together
        duplicates_query = CodaBudget.objects.values(
            'budget_lead', 'company', 'department', 'category', 'subcategory', 'item'
        ).annotate(count=Count('id')).filter(count__gt=1)
        
        total_duplicate_groups = duplicates_query.count()
        total_to_delete = 0
        
        self.stdout.write(f"\nFound {total_duplicate_groups} groups with duplicates")
        
        if total_duplicate_groups == 0:
            self.stdout.write(self.style.SUCCESS("\n✓ No duplicates found!"))
            return
        
        # Process each duplicate group
        for group in duplicates_query:
            # Get all CodaBudget entries in this duplicate group
            filters = {k: v for k, v in group.items() if k != 'count'}
            
            # Get all entries, ordered by most recent first
            entries = CodaBudget.objects.filter(**filters).order_by('-created_at', '-id')
            
            # Keep the first one (most recent), delete the rest
            entries_to_delete = list(entries[1:])  # Skip first (most recent)
            total_to_delete += len(entries_to_delete)
            
            if entries_to_delete:
                item_name = group.get('item', 'Unknown')[:30]
                dept_name = entries.first().department.name if entries.first().department else 'No Dept'
                
                self.stdout.write(
                    f"  {dept_name} | {item_name} | "
                    f"Keeping 1, removing {len(entries_to_delete)} duplicates"
                )
                
                if not dry_run:
                    for entry in entries_to_delete:
                        entry.delete()
        
        self.stdout.write("\n" + "="*80)
        if dry_run:
            self.stdout.write(self.style.WARNING(
                f"[DRY RUN] Would delete {total_to_delete} duplicate entries"
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"✓ Deleted {total_to_delete} duplicate entries"
            ))
        self.stdout.write("="*80)

