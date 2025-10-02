"""
Clean location data from receiver field

Finds transactions where receiver contains location names (Matunda, Makutano, etc.)
and moves them to the location field
"""
from django.core.management.base import BaseCommand
from finance.models import Transaction


class Command(BaseCommand):
    help = 'Clean location data from receiver field'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write("="*80)
        self.stdout.write("CLEANING LOCATION DATA FROM RECEIVER FIELD")
        self.stdout.write("="*80)
        
        # Define location patterns
        location_patterns = {
            'matunda': 'matunda',
            'makutano': 'makutano',
            'nairobi': 'nairobi_hq',
            'coda office': 'nairobi_hq',
            'office': 'remote',  # Generic, need manual review
        }
        
        fixes = []
        
        # Find transactions with location keywords in receiver
        self.stdout.write("\nSearching for location data in receiver field...")
        
        for keyword, location_value in location_patterns.items():
            transactions = Transaction.objects.filter(
                receiver__icontains=keyword
            )
            
            for txn in transactions:
                fixes.append({
                    'transaction': txn,
                    'old_receiver': txn.receiver,
                    'suggested_location': location_value,
                    'keyword': keyword
                })
        
        # Display findings
        self._display_findings(fixes)
        
        # Execute if not dry run
        if not dry_run and fixes:
            self._execute_cleanup(fixes)
        elif dry_run:
            self.stdout.write(self.style.WARNING("\n[DRY RUN] No changes made"))
        else:
            self.stdout.write(self.style.SUCCESS("\n✅ No location data found in receiver field!"))
    
    def _display_findings(self, fixes):
        """Display what will be cleaned"""
        self.stdout.write(f"\nFound {len(fixes)} transactions with location data in receiver field")
        
        if len(fixes) == 0:
            return
        
        self.stdout.write("\nProposed Changes:")
        self.stdout.write(f"{'Current Receiver':<40} {'Detected':<15} {'→ Location':>15}")
        self.stdout.write("-"*80)
        
        for fix in fixes[:20]:  # Show first 20
            self.stdout.write(
                f"{fix['old_receiver']:<40} "
                f"{fix['keyword']:<15} "
                f"→ {fix['suggested_location']:>15}"
            )
        
        if len(fixes) > 20:
            self.stdout.write(f"... and {len(fixes) - 20} more")
        
        # Group by keyword
        self.stdout.write(f"\nBreakdown by Location:")
        from collections import Counter
        location_counts = Counter(fix['keyword'] for fix in fixes)
        for keyword, count in location_counts.most_common():
            self.stdout.write(f"  {keyword}: {count} transactions")
    
    def _execute_cleanup(self, fixes):
        """Execute the location data cleanup"""
        self.stdout.write("\n" + "="*80)
        self.stdout.write("EXECUTING CLEANUP...")
        self.stdout.write("="*80)
        
        updated = 0
        needs_manual = []
        
        for fix in fixes:
            txn = fix['transaction']
            
            # Check if this looks like a clean case
            if fix['keyword'] in ['matunda', 'makutano']:
                # High confidence - auto-fix
                txn.location = fix['suggested_location']
                
                # Try to extract actual receiver from the string
                receiver_clean = txn.receiver
                for location_word in ['matunda', 'makutano', 'office', 'coda']:
                    receiver_clean = receiver_clean.replace(location_word, '').strip()
                
                # If we extracted something meaningful, use it
                if receiver_clean and len(receiver_clean) > 3:
                    txn.receiver = receiver_clean.title()
                else:
                    # Needs manual review - what's the actual receiver?
                    needs_manual.append(txn)
                
                txn.save()
                updated += 1
                
            else:
                # Lower confidence - flag for manual review
                needs_manual.append(txn)
        
        self.stdout.write(f"\n  ✅ Updated {updated} transactions")
        
        if needs_manual:
            self.stdout.write(f"\n  ⚠️  {len(needs_manual)} transactions need manual review:")
            for txn in needs_manual[:10]:
                self.stdout.write(f"     Transaction #{txn.id}: {txn.receiver}")
        
        self.stdout.write(self.style.SUCCESS(f"\n✅ Cleanup complete!"))

