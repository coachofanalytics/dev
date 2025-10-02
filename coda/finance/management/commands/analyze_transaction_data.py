"""
Django management command to analyze Transaction data quality
This is the SOURCE data that should inform budget creation
"""
from django.core.management.base import BaseCommand
from django.db.models import Sum, Count, Avg, Q
from django.db.models.functions import TruncMonth, TruncYear
from finance.models import Transaction, BudgetCategory, Budget, CodaBudget
from accounts.models import Department
from decimal import Decimal
from collections import defaultdict
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Analyze Transaction data quality and patterns for budget planning'

    def handle(self, *args, **options):
        self.stdout.write("="*80)
        self.stdout.write("TRANSACTION DATA ANALYSIS - SOURCE FOR BUDGET PLANNING")
        self.stdout.write("="*80)

        # 1. OVERALL TRANSACTION STATS
        self.stdout.write("\n" + "="*80)
        self.stdout.write("1. OVERALL TRANSACTION STATISTICS")
        self.stdout.write("="*80)
        
        total_transactions = Transaction.objects.count()
        total_amount = Transaction.objects.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        total_amount_usd = Transaction.objects.aggregate(
            total=Sum('amount_usd')
        )['total'] or Decimal('0.00')
        
        self.stdout.write(f"Total Transactions: {total_transactions:,}")
        self.stdout.write(f"Total Amount (original currency): ${total_amount:,.2f}")
        self.stdout.write(f"Total Amount (USD): ${total_amount_usd:,.2f}")
        
        # Date range
        if total_transactions > 0:
            first_transaction = Transaction.objects.order_by('transaction_date').first()
            last_transaction = Transaction.objects.order_by('transaction_date').last()
            self.stdout.write(f"Date Range: {first_transaction.transaction_date.date()} to {last_transaction.transaction_date.date()}")
            
            days_span = (last_transaction.transaction_date - first_transaction.transaction_date).days
            self.stdout.write(f"Days Span: {days_span} days ({days_span/365.25:.1f} years)")

        # 2. DATA QUALITY ISSUES
        self.stdout.write("\n" + "="*80)
        self.stdout.write("2. DATA QUALITY ISSUES")
        self.stdout.write("="*80)
        
        # NULL/Missing data
        null_department = Transaction.objects.filter(department__isnull=True).count()
        null_category = Transaction.objects.filter(category__isnull=True).count()
        null_amount = Transaction.objects.filter(Q(amount__isnull=True) | Q(amount=0)).count()
        null_description = Transaction.objects.filter(Q(description__isnull=True) | Q(description='')).count()
        
        self.stdout.write(f"Missing Department: {null_department} ({null_department/total_transactions*100:.1f}%)")
        self.stdout.write(f"Missing Category: {null_category} ({null_category/total_transactions*100:.1f}%)")
        self.stdout.write(f"Missing/Zero Amount: {null_amount} ({null_amount/total_transactions*100:.1f}%)")
        self.stdout.write(f"Missing Description: {null_description} ({null_description/total_transactions*100:.1f}%)")
        
        # Currency analysis
        currency_breakdown = Transaction.objects.values('currency').annotate(
            count=Count('id'),
            total=Sum('amount')
        ).order_by('-count')
        
        self.stdout.write("\nCurrency Breakdown:")
        for curr in currency_breakdown:
            currency = curr['currency'] or 'NULL'
            self.stdout.write(f"  {currency}: {curr['count']} transactions (${curr['total']:,.2f})")

        # 3. DEPARTMENT ANALYSIS
        self.stdout.write("\n" + "="*80)
        self.stdout.write("3. SPENDING BY DEPARTMENT")
        self.stdout.write("="*80)
        
        dept_analysis = Transaction.objects.values('department__name').annotate(
            count=Count('id'),
            total_amount=Sum('amount'),
            avg_amount=Avg('amount')
        ).order_by('-total_amount')
        
        self.stdout.write(f"{'Department':<30} {'Transactions':>12} {'Total':>15} {'Avg':>12}")
        self.stdout.write("-"*80)
        for dept in dept_analysis:
            dept_name = dept['department__name'] or 'NULL'
            count = dept['count']
            total = dept['total_amount'] or 0
            avg = dept['avg_amount'] or 0
            self.stdout.write(f"{dept_name:<30} {count:>12,} ${total:>14,.2f} ${avg:>11,.2f}")

        # 4. CATEGORY ANALYSIS
        self.stdout.write("\n" + "="*80)
        self.stdout.write("4. SPENDING BY CATEGORY")
        self.stdout.write("="*80)
        
        cat_analysis = Transaction.objects.values('category__name').annotate(
            count=Count('id'),
            total_amount=Sum('amount'),
            avg_amount=Avg('amount')
        ).order_by('-total_amount')[:15]
        
        self.stdout.write(f"{'Category':<30} {'Transactions':>12} {'Total':>15} {'Avg':>12}")
        self.stdout.write("-"*80)
        for cat in cat_analysis:
            cat_name = cat['category__name'] or 'NULL'
            count = cat['count']
            total = cat['total_amount'] or 0
            avg = cat['avg_amount'] or 0
            self.stdout.write(f"{cat_name:<30} {count:>12,} ${total:>14,.2f} ${avg:>11,.2f}")

        # 5. LOCATION DATA QUALITY (Matunda, Makutano issue)
        self.stdout.write("\n" + "="*80)
        self.stdout.write("5. LOCATION/RECEIVER DATA ANALYSIS")
        self.stdout.write("="*80)
        
        # Check receiver field for location names
        receiver_analysis = Transaction.objects.values('receiver').annotate(
            count=Count('id'),
            total=Sum('amount')
        ).order_by('-count')[:20]
        
        self.stdout.write("\nTop 20 Receivers:")
        self.stdout.write(f"{'Receiver':<40} {'Count':>10} {'Total':>15}")
        self.stdout.write("-"*80)
        
        location_keywords = ['matunda', 'makutano', 'office', 'coda', 'nairobi']
        location_found = []
        
        for rec in receiver_analysis:
            receiver = rec['receiver'] or 'NULL'
            count = rec['count']
            total = rec['total'] or 0
            self.stdout.write(f"{receiver:<40} {count:>10,} ${total:>14,.2f}")
            
            # Check if receiver looks like a location
            if any(keyword in receiver.lower() for keyword in location_keywords):
                location_found.append(receiver)
        
        if location_found:
            self.stdout.write("\n⚠️  POTENTIAL LOCATION DATA IN RECEIVER FIELD:")
            for loc in location_found:
                self.stdout.write(f"  - {loc}")
            self.stdout.write("\n  These might be CODA office locations, not actual receivers!")

        # 6. MONTHLY TRENDS
        self.stdout.write("\n" + "="*80)
        self.stdout.write("6. MONTHLY SPENDING TRENDS (Last 12 Months)")
        self.stdout.write("="*80)
        
        twelve_months_ago = datetime.now() - timedelta(days=365)
        monthly_trends = Transaction.objects.filter(
            transaction_date__gte=twelve_months_ago
        ).annotate(
            month=TruncMonth('transaction_date')
        ).values('month').annotate(
            count=Count('id'),
            total=Sum('amount')
        ).order_by('month')
        
        self.stdout.write(f"{'Month':<15} {'Transactions':>12} {'Total':>15} {'Daily Avg':>12}")
        self.stdout.write("-"*80)
        for trend in monthly_trends:
            month = trend['month'].strftime('%Y-%m')
            count = trend['count']
            total = trend['total'] or 0
            days_in_month = 30  # Approximation
            daily_avg = total / days_in_month
            self.stdout.write(f"{month:<15} {count:>12,} ${total:>14,.2f} ${daily_avg:>11,.2f}")

        # 7. BUDGET COMPARISON
        self.stdout.write("\n" + "="*80)
        self.stdout.write("7. TRANSACTION vs BUDGET COMPARISON")
        self.stdout.write("="*80)
        
        # Get budgets total
        budget_calculated_total = sum(
            (b.unit_price or 0) * (b.quantity or 0) * (b.cases or 1) 
            for b in Budget.objects.all()
        )
        
        coda_budgets = CodaBudget.objects.all()
        coda_total = sum(b.amount for b in coda_budgets)
        
        total_budgeted = budget_calculated_total + coda_total
        
        # Get last 12 months of transactions
        last_12_months_total = Transaction.objects.filter(
            transaction_date__gte=twelve_months_ago
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        self.stdout.write(f"Total Budgeted (all time):        ${total_budgeted:,.2f}")
        self.stdout.write(f"Actual Spent (last 12 months):    ${last_12_months_total:,.2f}")
        self.stdout.write(f"Total Transactions (all time):    ${total_amount:,.2f}")
        
        if total_budgeted > 0:
            budget_utilization = (last_12_months_total / total_budgeted * 100)
            self.stdout.write(f"\nBudget Utilization (12mo):        {budget_utilization:.1f}%")

        # 8. RECOMMENDATIONS
        self.stdout.write("\n" + "="*80)
        self.stdout.write("8. DATA CLEANING RECOMMENDATIONS")
        self.stdout.write("="*80)
        
        recommendations = []
        
        if null_category > total_transactions * 0.1:
            recommendations.append(f"Fix {null_category} transactions missing categories")
        
        if null_department > 0:
            recommendations.append(f"Assign departments to {null_department} transactions")
        
        if location_found:
            recommendations.append(f"Clean up location data in receiver field ({len(location_found)} patterns found)")
        
        if null_amount > 0:
            recommendations.append(f"Review {null_amount} transactions with missing/zero amounts")
        
        recommendations.append("Add validation to prevent NULL categories in future transactions")
        recommendations.append("Create data entry guidelines for receiver field (person vs location)")
        recommendations.append("Implement category auto-suggestion based on description")
        
        for i, rec in enumerate(recommendations, 1):
            self.stdout.write(f"{i}. {rec}")

        # 9. BUDGET ESTIMATION POTENTIAL
        self.stdout.write("\n" + "="*80)
        self.stdout.write("9. BUDGET ESTIMATION INSIGHTS")
        self.stdout.write("="*80)
        
        # Calculate average monthly spend by category
        self.stdout.write("\nAverage Monthly Spend by Category (last 12 months):")
        self.stdout.write(f"{'Category':<30} {'Monthly Avg':>15} {'Suggested Budget':>18}")
        self.stdout.write("-"*80)
        
        category_monthly = Transaction.objects.filter(
            transaction_date__gte=twelve_months_ago,
            category__isnull=False
        ).values('category__name').annotate(
            total=Sum('amount')
        ).order_by('-total')
        
        for cat in category_monthly:
            cat_name = cat['category__name']
            total = cat['total'] or Decimal('0.00')
            monthly_avg = total / Decimal('12')
            suggested_budget = monthly_avg * Decimal('1.1')  # Add 10% buffer
            self.stdout.write(f"{cat_name:<30} ${monthly_avg:>14,.2f} ${suggested_budget:>17,.2f}")

        self.stdout.write("\n" + "="*80)
        self.stdout.write("ANALYSIS COMPLETE")
        self.stdout.write("="*80)
        self.stdout.write("\nKey Takeaways:")
        self.stdout.write("1. Transaction data is the SOURCE TRUTH for budget planning")
        self.stdout.write("2. Clean transaction data → Better budget estimates")
        self.stdout.write("3. Use historical transaction patterns to inform future budgets")
        self.stdout.write("4. Budget system should REFERENCE transaction data, not duplicate it")
        self.stdout.write("="*80)
        
        self.stdout.write(self.style.SUCCESS('\n✓ Transaction analysis complete!'))

