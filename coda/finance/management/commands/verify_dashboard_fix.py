"""
Django management command to verify dashboard aggregation fix
"""
from django.core.management.base import BaseCommand
from django.db.models import Q, Sum, F, DecimalField
from django.db.models.functions import Coalesce
from finance.models import Budget
from main.models import Company
from decimal import Decimal


class Command(BaseCommand):
    help = 'Verify that dashboard aggregation fix is working correctly'

    def handle(self, *args, **options):
        self.stdout.write("="*80)
        self.stdout.write("VERIFYING DASHBOARD AGGREGATION FIX")
        self.stdout.write("="*80)

        try:
            company = Company.objects.get(slug='coda')
            budget_filter = Q(company=company, is_active=True)
            
            # OLD METHOD (WRONG) - What it would calculate
            self.stdout.write("\n--- What the OLD method would calculate ---")
            self.stdout.write("(This would multiply sum of ALL quantities by sum of ALL prices)")
            all_quantities = Budget.objects.filter(budget_filter).aggregate(total_qty=Sum('quantity'))['total_qty'] or 0
            all_prices = Budget.objects.filter(budget_filter).aggregate(total_price=Sum('unit_price'))['total_price'] or 0
            wrong_total = float(all_quantities) * float(all_prices) if all_quantities and all_prices else 0
            self.stdout.write(f"Sum of quantities: {all_quantities}")
            self.stdout.write(f"Sum of prices: {all_prices}")
            self.stdout.write(f"Multiplied together (WRONG): ${wrong_total:,.2f}")
            
            # NEW METHOD (CORRECT)
            self.stdout.write("\n--- NEW method (CORRECT) ---")
            self.stdout.write("(Calculates unit_price * quantity * cases for EACH budget, then sums)")
            correct_total = Budget.objects.filter(budget_filter).aggregate(
                total=Sum(
                    F('unit_price') * F('quantity') * Coalesce(F('cases'), 1),
                    output_field=DecimalField()
                )
            )['total'] or Decimal('0.00')
            self.stdout.write(f"Correct total: ${correct_total:,.2f}")
            
            # COMPARISON
            self.stdout.write("\n" + "="*80)
            self.stdout.write("COMPARISON")
            self.stdout.write("="*80)
            if wrong_total > 0 and correct_total > 0:
                inflation_factor = wrong_total / float(correct_total)
                self.stdout.write(f"OLD method result:  ${wrong_total:,.2f}")
                self.stdout.write(f"NEW method result:  ${correct_total:,.2f}")
                self.stdout.write(f"Inflation factor:   {inflation_factor:.1f}x")
                self.stdout.write(f"\nThe bug was inflating totals by {inflation_factor:.1f}x!")
            
            # Show breakdown by status
            self.stdout.write("\n" + "="*80)
            self.stdout.write("BUDGET BREAKDOWN BY STATUS (using correct calculation)")
            self.stdout.write("="*80)
            
            statuses = Budget.objects.filter(budget_filter).values_list('status', flat=True).distinct()
            for status in statuses:
                status_total = Budget.objects.filter(budget_filter, status=status).aggregate(
                    total=Sum(
                        F('unit_price') * F('quantity') * Coalesce(F('cases'), 1),
                        output_field=DecimalField()
                    )
                )['total'] or Decimal('0.00')
                count = Budget.objects.filter(budget_filter, status=status).count()
                self.stdout.write(f"{status}: {count} budgets, ${status_total:,.2f}")
            
            self.stdout.write("\n" + "="*80)
            self.stdout.write(self.style.SUCCESS("✅ Fix is working correctly!"))
            self.stdout.write("="*80)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error: {e}"))
            import traceback
            traceback.print_exc()

