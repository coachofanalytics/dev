"""
Django management command to investigate budget data discrepancy
"""
from django.core.management.base import BaseCommand
from django.db.models import Sum, Count
from finance.models import Budget, CodaBudget


class Command(BaseCommand):
    help = 'Investigate budget data discrepancy between UI and database'

    def handle(self, *args, **options):
        self.stdout.write("="*60)
        self.stdout.write("BUDGET DATA INVESTIGATION")
        self.stdout.write("="*60)

        # Budget model stats (uses 'estimated_amount' field)
        self.stdout.write("\n=== Budget Model (New) ===")
        budget_stats = Budget.objects.aggregate(
            count=Count('id'),
            sum_amount=Sum('estimated_amount')
        )
        self.stdout.write(f"Total Count: {budget_stats['count']}")
        if budget_stats['sum_amount']:
            self.stdout.write(f"Total Amount: ${budget_stats['sum_amount']:,.2f}")
        else:
            self.stdout.write("Total Amount: $0.00")

        # Status breakdown for Budget
        self.stdout.write("\n--- Budget by Status ---")
        status_breakdown = Budget.objects.values('status').annotate(
            count=Count('id'),
            sum_amount=Sum('estimated_amount')
        ).order_by('-sum_amount')
        for item in status_breakdown:
            amount = item['sum_amount'] if item['sum_amount'] else 0
            self.stdout.write(f"  {item['status']}: {item['count']} budgets, ${amount:,.2f}")

        # Category breakdown for Budget
        self.stdout.write("\n--- Budget by Category (Top 10) ---")
        category_breakdown = Budget.objects.filter(
            category__isnull=False
        ).values('category__name').annotate(
            count=Count('id'),
            sum_amount=Sum('estimated_amount')
        ).order_by('-sum_amount')[:10]
        for item in category_breakdown:
            amount = item['sum_amount'] if item['sum_amount'] else 0
            self.stdout.write(f"  {item['category__name']}: {item['count']} budgets, ${amount:,.2f}")

        # Check for NULL categories
        null_category_count = Budget.objects.filter(category__isnull=True).count()
        self.stdout.write(f"\nBudgets with NULL category: {null_category_count}")

        self.stdout.write("\n" + "="*60)
        self.stdout.write("=== CodaBudget Model (Legacy) ===")
        
        # Calculate totals in Python since amount is a property
        coda_budgets = CodaBudget.objects.all()
        coda_count = coda_budgets.count()
        coda_total = sum(b.amount for b in coda_budgets)
        
        self.stdout.write(f"Total Count: {coda_count}")
        self.stdout.write(f"Total Amount: ${coda_total:,.2f}")

        # Category breakdown for CodaBudget (calculated in Python)
        self.stdout.write("\n--- CodaBudget by Category (Top 10) ---")
        from collections import defaultdict
        category_totals = defaultdict(lambda: {'count': 0, 'total': 0})
        
        for budget in coda_budgets:
            if budget.category:
                category_totals[budget.category.name]['count'] += 1
                category_totals[budget.category.name]['total'] += budget.amount
        
        # Sort by total amount
        sorted_categories = sorted(category_totals.items(), key=lambda x: x[1]['total'], reverse=True)[:10]
        for cat_name, data in sorted_categories:
            self.stdout.write(f"  {cat_name}: {data['count']} budgets, ${data['total']:,.2f}")

        # Combined totals
        self.stdout.write("\n" + "="*60)
        self.stdout.write("COMBINED TOTALS")
        self.stdout.write("="*60)
        budget_est_total = budget_stats['sum_amount'] if budget_stats['sum_amount'] else 0
        combined_total = budget_est_total + coda_total
        self.stdout.write(f"Budget.estimated_amount:     ${budget_est_total:,.2f}")
        self.stdout.write(f"CodaBudget.amount (calc):    ${coda_total:,.2f}")
        self.stdout.write(f"COMBINED TOTAL:              ${combined_total:,.2f}")
        self.stdout.write("="*60)
        
        # Note about calculated properties
        self.stdout.write("\n" + "="*60)
        self.stdout.write("IMPORTANT NOTES")
        self.stdout.write("="*60)
        self.stdout.write("Budget model also has a calculated property:")
        self.stdout.write("  total_amount = unit_price * quantity * cases")
        self.stdout.write("\nThis property cannot be aggregated in SQL.")
        self.stdout.write("The dashboard likely calculates this in Python.")
        self.stdout.write("="*60)
        
        self.stdout.write(self.style.SUCCESS('\nInvestigation complete!'))

