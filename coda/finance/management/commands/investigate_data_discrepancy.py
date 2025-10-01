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
        coda_stats = CodaBudget.objects.aggregate(
            count=Count('id'),
            sum_total=Sum('total')
        )
        self.stdout.write(f"Total Count: {coda_stats['count']}")
        if coda_stats['sum_total']:
            self.stdout.write(f"Total Amount: ${coda_stats['sum_total']:,.2f}")
        else:
            self.stdout.write("Total Amount: $0.00")

        # CodaBudget doesn't have status field, show category breakdown instead
        self.stdout.write("\n--- CodaBudget by Category (Top 10) ---")
        coda_category_breakdown = CodaBudget.objects.filter(
            category__isnull=False
        ).values('category__name').annotate(
            count=Count('id'),
            sum_total=Sum('total')
        ).order_by('-sum_total')[:10]
        for item in coda_category_breakdown:
            amount = item['sum_total'] if item['sum_total'] else 0
            self.stdout.write(f"  {item['category__name']}: {item['count']} budgets, ${amount:,.2f}")

        # Combined totals
        self.stdout.write("\n" + "="*60)
        self.stdout.write("COMBINED TOTALS (from database fields)")
        self.stdout.write("="*60)
        budget_total = budget_stats['sum_amount'] if budget_stats['sum_amount'] else 0
        coda_total = coda_stats['sum_total'] if coda_stats['sum_total'] else 0
        combined_total = budget_total + coda_total
        self.stdout.write(f"Budget.estimated_amount:     ${budget_total:,.2f}")
        self.stdout.write(f"CodaBudget.total:            ${coda_total:,.2f}")
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

