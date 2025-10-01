"""
Analyze CodaBudget Categories

Understand what categories CodaBudget uses and which are missing
"""

from django.core.management.base import BaseCommand
from finance.models import CodaBudget, BudgetCategory, BudgetSubCategory
from collections import Counter


class Command(BaseCommand):
    help = "Analyze CodaBudget records to understand category usage"
    
    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('CODABUDGET CATEGORY ANALYSIS'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))
        
        # 1. Get all existing categories
        existing_categories = {cat.id: cat.name for cat in BudgetCategory.objects.all()}
        
        self.stdout.write(self.style.WARNING('1. EXISTING BUDGET CATEGORIES'))
        self.stdout.write('-' * 80)
        for cat_id, cat_name in sorted(existing_categories.items()):
            self.stdout.write(f"  ID {cat_id:>3}: {cat_name}")
        
        # 2. Get all category IDs used in CodaBudget
        used_category_ids = set(
            CodaBudget.objects.exclude(category__isnull=True)
            .values_list('category_id', flat=True)
            .distinct()
        )
        
        # 3. Find missing categories
        missing_category_ids = used_category_ids - set(existing_categories.keys())
        
        self.stdout.write(self.style.WARNING('\n2. MISSING CATEGORIES'))
        self.stdout.write('-' * 80)
        if missing_category_ids:
            self.stdout.write(self.style.ERROR(f"Missing Category IDs: {sorted(missing_category_ids)}"))
            
            # Count records per missing category
            for cat_id in sorted(missing_category_ids):
                count = CodaBudget.objects.filter(category_id=cat_id).count()
                self.stdout.write(f"  Category ID {cat_id}: {count} records")
        else:
            self.stdout.write(self.style.SUCCESS("No missing categories!"))
        
        # 4. Sample CodaBudget records
        self.stdout.write(self.style.WARNING('\n3. SAMPLE CODABUDGET RECORDS'))
        self.stdout.write('-' * 80)
        
        # Get sample from different categories
        samples = CodaBudget.objects.select_related('category', 'subcategory')[:20]
        
        self.stdout.write(f"{'Item':<40} {'Cat ID':<8} {'Qty':<8} {'Price':<10} {'Amount':<12}")
        self.stdout.write('-' * 80)
        
        for record in samples:
            item = (record.item or 'N/A')[:38]
            cat_id = record.category_id if record.category_id else 'NULL'
            qty = record.qty if record.qty else 0
            price = record.unit_price if record.unit_price else 0
            amount = record.amount
            
            self.stdout.write(
                f"{item:<40} {str(cat_id):<8} {str(qty):<8} ${str(price):<9} ${str(amount):<11}"
            )
        
        # 5. Analyze what's in missing categories
        if missing_category_ids:
            self.stdout.write(self.style.WARNING('\n4. RECORDS IN MISSING CATEGORIES (Sample)'))
            self.stdout.write('-' * 80)
            
            for cat_id in sorted(missing_category_ids)[:5]:  # First 5 missing categories
                records = CodaBudget.objects.filter(category_id=cat_id)[:5]
                
                self.stdout.write(f"\nCategory ID {cat_id} ({records.count()} total records):")
                for record in records:
                    self.stdout.write(f"  - {record.item}: {record.description[:60] if record.description else 'No description'}")
        
        # 6. Check if these are web development related
        self.stdout.write(self.style.WARNING('\n5. WEB DEVELOPMENT INDICATORS'))
        self.stdout.write('-' * 80)
        
        # Count records with web-related keywords
        web_keywords = ['web', 'website', 'frontend', 'backend', 'api', 'template', 'view', 'form']
        web_related_count = 0
        
        for keyword in web_keywords:
            count = CodaBudget.objects.filter(item__icontains=keyword).count()
            if count > 0:
                self.stdout.write(f"  Records with '{keyword}': {count}")
                web_related_count += count
        
        total_records = CodaBudget.objects.count()
        self.stdout.write(f"\nTotal CodaBudget records: {total_records}")
        self.stdout.write(f"Web development related: {web_related_count}")
        
        if web_related_count > 0:
            percentage = (web_related_count / total_records) * 100
            self.stdout.write(f"Percentage: {percentage:.1f}%")
        
        # 7. Recommendations
        self.stdout.write(self.style.WARNING('\n6. RECOMMENDATIONS'))
        self.stdout.write('-' * 80)
        
        if missing_category_ids:
            self.stdout.write(self.style.WARNING("ACTION REQUIRED: Fix missing categories before migration"))
            self.stdout.write("\nOptions:")
            self.stdout.write("  A) Create missing categories with placeholder names")
            self.stdout.write("  B) Map orphaned records to existing categories")
            self.stdout.write("  C) Set category to NULL for orphaned records")
            self.stdout.write("\nRecommendation: Option A - Create missing categories")
            self.stdout.write("  This preserves data integrity and allows proper migration")
        
        if web_related_count > total_records * 0.5:
            self.stdout.write(self.style.SUCCESS("\n✓ CodaBudget appears to be web development focused"))
            self.stdout.write("  Consider keeping separate OR migrating with budget_type='website_development'")
        else:
            self.stdout.write(self.style.SUCCESS("\n✓ CodaBudget appears to be general purpose"))
            self.stdout.write("  Safe to migrate to Budget model")
        
        self.stdout.write('\n' + '='*80)
        self.stdout.write(self.style.SUCCESS('ANALYSIS COMPLETE'))
        self.stdout.write('='*80 + '\n')


