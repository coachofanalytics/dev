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

        # Budget model stats (uses 'total' field, not 'amount')
        self.stdout.write("\n=== Budget Model (New) ===")
        budget_stats = Budget.objects.aggregate(
            count=Count('id'),
            sum_total=Sum('total')
        )
        self.stdout.write(f"Total Count: {budget_stats['count']}")
        if budget_stats['sum_total']:
            self.stdout.write(f"Total Amount: ${budget_stats['sum_total']:,.2f}")
        else:
            self.stdout.write("Total Amount: $0.00")

        # Status breakdown for Budget
        self.stdout.write("\n--- Budget by Status ---")
        status_breakdown = Budget.objects.values('status').annotate(
            count=Count('id'),
            sum_total=Sum('total')
        ).order_by('-sum_total')
        for item in status_breakdown:
            amount = item['sum_total'] if item['sum_total'] else 0
            self.stdout.write(f"  {item['status']}: {item['count']} budgets, ${amount:,.2f}")

        # Category breakdown for Budget
        self.stdout.write("\n--- Budget by Category (Top 10) ---")
        category_breakdown = Budget.objects.filter(
            category__isnull=False
        ).values('category__name').annotate(
            count=Count('id'),
            sum_total=Sum('total')
        ).order_by('-sum_total')[:10]
        for item in category_breakdown:
            amount = item['sum_total'] if item['sum_total'] else 0
            self.stdout.write(f"  {item['category__name']}: {item['count']} budgets, ${amount:,.2f}")

        # Check for NULL categories
        null_category_count = Budget.objects.filter(category__isnull=True).count()
        self.stdout.write(f"\nBudgets with NULL category: {null_category_count}")

        self.stdout.write("\n" + "="*60)
        self.stdout.write("=== CodaBudget Model (Legacy) ===")
        coda_stats = CodaBudget.objects.aggregate(
            total=Count('id'),
            sum_amount=Sum('amount')
        )
        self.stdout.write(f"Total Count: {coda_stats['total']}")
        if coda_stats['sum_amount']:
            self.stdout.write(f"Total Amount: ${coda_stats['sum_amount']:,.2f}")
        else:
            self.stdout.write("Total Amount: $0.00")

        # Status breakdown for CodaBudget
        self.stdout.write("\n--- CodaBudget by Status ---")
        coda_status_breakdown = CodaBudget.objects.values('status').annotate(
            count=Count('id'),
            total=Sum('amount')
        ).order_by('-total')
        for item in coda_status_breakdown:
            amount = item['total'] if item['total'] else 0
            self.stdout.write(f"  {item['status']}: {item['count']} budgets, ${amount:,.2f}")

        # Combined totals
        self.stdout.write("\n" + "="*60)
        self.stdout.write("COMBINED TOTALS")
        self.stdout.write("="*60)
        budget_total = budget_stats['sum_total'] if budget_stats['sum_total'] else 0
        coda_total = coda_stats['sum_amount'] if coda_stats['sum_amount'] else 0
        combined_total = budget_total + coda_total
        self.stdout.write(f"Budget Model Total:     ${budget_total:,.2f}")
        self.stdout.write(f"CodaBudget Model Total: ${coda_total:,.2f}")
        self.stdout.write(f"COMBINED TOTAL:         ${combined_total:,.2f}")
        self.stdout.write("="*60)
        
        self.stdout.write(self.style.SUCCESS('\nInvestigation complete!'))

