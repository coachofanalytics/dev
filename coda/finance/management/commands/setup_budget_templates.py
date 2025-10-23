"""
Setup Budget Templates

Convert sample budget entries into reusable templates for future budget planning.
Templates can be cloned to create new budget periods quickly.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from finance.models import Budget, BudgetCategory
from datetime import datetime


class Command(BaseCommand):
    help = 'Convert sample budgets to reusable templates'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--sample-ids',
            type=str,
            default='976,977,978,979,980,981,982,983,984',
            help='Comma-separated list of budget IDs to convert to templates'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without saving'
        )
    
    def handle(self, *args, **options):
        sample_ids_str = options['sample_ids']
        dry_run = options['dry_run']
        
        # Parse sample IDs
        sample_ids = [int(id.strip()) for id in sample_ids_str.split(',') if id.strip()]
        
        self.stdout.write("="*80)
        self.stdout.write("BUDGET TEMPLATE SETUP")
        self.stdout.write("="*80)
        
        if dry_run:
            self.stdout.write(self.style.WARNING("\n⚠️  DRY RUN MODE - No changes will be saved"))
        
        # Get sample budgets
        sample_budgets = Budget.objects.filter(id__in=sample_ids)
        
        if not sample_budgets.exists():
            self.stdout.write(self.style.ERROR(f"\n❌ No budgets found with IDs: {sample_ids}"))
            return
        
        self.stdout.write(f"\nFound {sample_budgets.count()} sample budgets to convert:")
        for budget in sample_budgets:
            self.stdout.write(
                f"  ID {budget.id}: {budget.item_name} - ${budget.total_amount} "
                f"({budget.category.name if budget.category else 'No category'})"
            )
        
        if not dry_run:
            # Update budgets to be templates
            updated_count = sample_budgets.update(
                status='template',
                is_active=False,
                budget_type='general',
                timeframe='monthly',
                notes='Template budget - Clone for new periods. Auto-converted from sample data.',
                updated_at=timezone.now()
            )
            
            self.stdout.write(
                self.style.SUCCESS(f"\n✅ Successfully converted {updated_count} budgets to templates")
            )
            
            # Show how to use templates
            self.stdout.write("\n" + "="*80)
            self.stdout.write("HOW TO USE TEMPLATES")
            self.stdout.write("="*80)
            self.stdout.write("\n1. List available templates:")
            self.stdout.write("   Budget.objects.filter(status='template')")
            
            self.stdout.write("\n2. Clone a template for new period:")
            self.stdout.write("""
   template = Budget.objects.get(id=976)
   new_budget = Budget.objects.create(
       company=template.company,
       department=template.department,
       budget_lead=template.budget_lead,
       category=template.category,
       subcategory=template.subcategory,
       item_name=template.item_name,
       quantity=template.quantity,
       unit_price=template.unit_price,
       cases=template.cases,
       description=f"Budget for Jan 2026 (from template {template.id})",
       start_date=datetime(2026, 1, 1),
       end_date=datetime(2026, 1, 31),
       status='draft',
       is_active=True,
       budget_type=template.budget_type
   )
            """)
            
            self.stdout.write("\n3. Or use the new clone_template command:")
            self.stdout.write("   python manage.py clone_budget_template --template-id 976 --start-date 2026-01-01")
            
        else:
            self.stdout.write(
                self.style.WARNING(f"\n⚠️  Would convert {sample_budgets.count()} budgets to templates")
            )
            self.stdout.write("Run without --dry-run to apply changes")
        
        # Show template statistics
        if not dry_run:
            self.stdout.write("\n" + "="*80)
            self.stdout.write("TEMPLATE STATISTICS")
            self.stdout.write("="*80)
            
            templates = Budget.objects.filter(status='template')
            self.stdout.write(f"\nTotal templates: {templates.count()}")
            
            # Group by category
            self.stdout.write("\nBy Category:")
            for category in BudgetCategory.objects.all():
                cat_templates = templates.filter(category=category)
                if cat_templates.exists():
                    self.stdout.write(f"  {category.name}: {cat_templates.count()} templates")


