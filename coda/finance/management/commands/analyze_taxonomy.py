"""
Analyze budget taxonomy: categories, subcategories, and transaction types/items
"""
from django.core.management.base import BaseCommand
from django.db.models import Count, Sum, Avg, Q
from finance.models import BudgetCategory, BudgetSubCategory, Transaction


class Command(BaseCommand):
    help = 'Analyze categories, subcategories, and transaction types'

    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write("CODA BUDGET SYSTEM - TAXONOMY ANALYSIS")
        self.stdout.write("=" * 80)
        self.stdout.write("")

        # 1. CATEGORIES
        self.stdout.write("-" * 80)
        self.stdout.write("1. BUDGET CATEGORIES")
        self.stdout.write("-" * 80)

        categories = BudgetCategory.objects.all().annotate(
            subcategory_count=Count('subcategories', distinct=True),
            transaction_count=Count('transaction_category', distinct=True)
        ).order_by('id')

        self.stdout.write(f"Total Categories: {categories.count()}")
        self.stdout.write("")
        self.stdout.write(f"{'ID':<4} {'Category Name':<40} {'Subcats':<8} {'Trans':<8}")
        self.stdout.write("-" * 80)

        for cat in categories:
            self.stdout.write(f"{cat.id:<4} {cat.name:<40} {cat.subcategory_count:<8} {cat.transaction_count:<8}")

        self.stdout.write("")
        self.stdout.write("")

        # 2. SUBCATEGORIES by CATEGORY
        self.stdout.write("-" * 80)
        self.stdout.write("2. SUBCATEGORIES (Grouped by Category)")
        self.stdout.write("-" * 80)
        self.stdout.write("")

        for cat in categories:
            subcats = BudgetSubCategory.objects.filter(category=cat).annotate(
                transaction_count=Count('transaction_subcategory')
            ).order_by('id')
            
            if subcats.exists():
                self.stdout.write(f"[{cat.name}] (ID: {cat.id})")
                self.stdout.write(f"   Total Subcategories: {subcats.count()}")
                self.stdout.write("")
                for sub in subcats:
                    self.stdout.write(f"   - [{sub.id}] {sub.name} ({sub.transaction_count} transactions)")
                self.stdout.write("")
            else:
                self.stdout.write(f"[{cat.name}] (ID: {cat.id})")
                self.stdout.write(f"   WARNING: NO SUBCATEGORIES DEFINED")
                self.stdout.write("")

        self.stdout.write("")

        # 3. TRANSACTION TYPES (Items) by CATEGORY
        self.stdout.write("-" * 80)
        self.stdout.write("3. TRANSACTION TYPES/ITEMS (From Actual Transactions)")
        self.stdout.write("-" * 80)
        self.stdout.write("")

        for cat in categories:
            types = Transaction.objects.filter(
                category=cat
            ).exclude(
                type__isnull=True
            ).exclude(
                type=''
            ).values('type').annotate(
                count=Count('id'),
                total=Sum('amount'),
                avg=Avg('amount')
            ).order_by('-count')[:20]
            
            if types:
                self.stdout.write(f"[{cat.name}] (ID: {cat.id})")
                self.stdout.write(f"   Distinct Items: {types.count()}")
                self.stdout.write("")
                self.stdout.write(f"   {'Item/Type':<40} {'Count':<8} {'Total $':<12} {'Avg $':<10}")
                self.stdout.write(f"   {'-'*70}")
                for item in types[:10]:
                    type_name = (item['type'][:40] if item['type'] else '(empty)') or '(empty)'
                    self.stdout.write(f"   {type_name:<40} {item['count']:<8} ${item['total']:>10,.2f} ${item['avg']:>8,.2f}")
                
                if types.count() > 10:
                    self.stdout.write(f"   ... and {types.count() - 10} more items")
                self.stdout.write("")
            else:
                self.stdout.write(f"[{cat.name}] (ID: {cat.id})")
                self.stdout.write(f"   NO TRANSACTION TYPES RECORDED")
                self.stdout.write("")

        self.stdout.write("")

        # 4. SUMMARY STATISTICS
        self.stdout.write("-" * 80)
        self.stdout.write("4. SUMMARY STATISTICS")
        self.stdout.write("-" * 80)
        self.stdout.write("")

        total_categories = BudgetCategory.objects.count()
        total_subcategories = BudgetSubCategory.objects.count()
        categories_with_subcats = BudgetCategory.objects.annotate(
            subcat_count=Count('subcategories')
        ).filter(subcat_count__gt=0).count()

        total_transactions = Transaction.objects.count()
        categorized_transactions = Transaction.objects.exclude(category__isnull=True).count()
        with_types = Transaction.objects.exclude(type__isnull=True).exclude(type='').count()
        distinct_types = Transaction.objects.exclude(type__isnull=True).exclude(type='').values('type').distinct().count()

        self.stdout.write(f"Categories:               {total_categories}")
        self.stdout.write(f"Categories with subcats:  {categories_with_subcats} ({categories_with_subcats/total_categories*100:.1f}%)")
        self.stdout.write(f"Total Subcategories:      {total_subcategories}")
        self.stdout.write(f"Avg subcats per category: {total_subcategories/total_categories:.1f}")
        self.stdout.write("")
        self.stdout.write(f"Total Transactions:       {total_transactions}")
        self.stdout.write(f"Categorized:              {categorized_transactions} ({categorized_transactions/total_transactions*100:.1f}%)")
        self.stdout.write(f"With type/item:           {with_types} ({with_types/total_transactions*100:.1f}%)")
        self.stdout.write(f"Distinct types:           {distinct_types}")
        self.stdout.write("")

        # 5. GAPS & RECOMMENDATIONS
        self.stdout.write("-" * 80)
        self.stdout.write("5. GAPS & RECOMMENDATIONS")
        self.stdout.write("-" * 80)
        self.stdout.write("")

        cats_no_subs = BudgetCategory.objects.annotate(
            subcat_count=Count('subcategories')
        ).filter(subcat_count=0)

        if cats_no_subs.exists():
            self.stdout.write("Categories WITHOUT Subcategories:")
            for cat in cats_no_subs:
                trans_count = Transaction.objects.filter(category=cat).count()
                self.stdout.write(f"   - {cat.name} ({trans_count} transactions)")
            self.stdout.write("")

        self.stdout.write("Data Quality Insights:")
        self.stdout.write("")
        uncategorized = Transaction.objects.filter(category__isnull=True).count()
        self.stdout.write(f"   - Uncategorized transactions: {uncategorized} ({uncategorized/total_transactions*100:.1f}%)")

        no_type = Transaction.objects.filter(category__isnull=False).filter(
            Q(type__isnull=True) | Q(type='')
        ).count()
        self.stdout.write(f"   - Categorized but no type: {no_type} ({no_type/categorized_transactions*100 if categorized_transactions > 0 else 0:.1f}%)")
        self.stdout.write("")

        self.stdout.write("=" * 80)
        self.stdout.write("Analysis Complete!")
        self.stdout.write("=" * 80)

