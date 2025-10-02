"""
Detailed analysis of remaining uncategorized transactions
Helps identify patterns to create better categorization rules
"""
from django.core.management.base import BaseCommand
from django.db.models import Count, Sum, Avg
from finance.models import Transaction
from collections import defaultdict


class Command(BaseCommand):
    help = 'Analyze remaining uncategorized transactions to create better rules'

    def handle(self, *args, **options):
        self.stdout.write("="*80)
        self.stdout.write("DETAILED ANALYSIS OF UNCATEGORIZED TRANSACTIONS")
        self.stdout.write("="*80)
        
        uncategorized = Transaction.objects.filter(category__isnull=True)
        total = uncategorized.count()
        total_amount = uncategorized.aggregate(total=Sum('amount'))['total'] or 0
        
        self.stdout.write(f"\nTotal Uncategorized: {total} transactions")
        self.stdout.write(f"Total Amount: ${total_amount:,.2f}")
        self.stdout.write(f"Percentage of all transactions: {total/366*100:.1f}%")
        
        # 1. BY RECEIVER
        self.stdout.write("\n" + "="*80)
        self.stdout.write("1. BY RECEIVER (Top 15)")
        self.stdout.write("="*80)
        
        by_receiver = uncategorized.values('receiver').annotate(
            count=Count('id'),
            total=Sum('amount'),
            avg=Avg('amount')
        ).order_by('-count')[:15]
        
        self.stdout.write(f"{'Receiver':<35} {'Count':>6} {'Total':>12} {'Avg':>10}")
        self.stdout.write("-"*80)
        for rec in by_receiver:
            name = (rec['receiver'] or 'NULL')[:32]
            self.stdout.write(
                f"{name:<35} {rec['count']:>6} "
                f"${rec['total']:>11,.2f} ${rec['avg']:>9,.2f}"
            )
        
        # 2. BY DEPARTMENT
        self.stdout.write("\n" + "="*80)
        self.stdout.write("2. BY DEPARTMENT")
        self.stdout.write("="*80)
        
        by_dept = uncategorized.values('department__name').annotate(
            count=Count('id'),
            total=Sum('amount')
        ).order_by('-count')
        
        for dept in by_dept:
            dept_name = dept['department__name'] or 'NULL'
            self.stdout.write(f"{dept_name}: {dept['count']} transactions, ${dept['total']:,.2f}")
        
        # 3. BY AMOUNT RANGE
        self.stdout.write("\n" + "="*80)
        self.stdout.write("3. BY AMOUNT RANGE")
        self.stdout.write("="*80)
        
        ranges = [
            (0, 100, 'Under $100'),
            (100, 500, '$100-$500'),
            (500, 1000, '$500-$1,000'),
            (1000, 5000, '$1,000-$5,000'),
            (5000, 10000, '$5,000-$10,000'),
            (10000, float('inf'), 'Over $10,000'),
        ]
        
        for min_amt, max_amt, label in ranges:
            if max_amt == float('inf'):
                count = uncategorized.filter(amount__gte=min_amt).count()
                total = uncategorized.filter(amount__gte=min_amt).aggregate(
                    total=Sum('amount'))['total'] or 0
            else:
                count = uncategorized.filter(
                    amount__gte=min_amt, amount__lt=max_amt
                ).count()
                total = uncategorized.filter(
                    amount__gte=min_amt, amount__lt=max_amt
                ).aggregate(total=Sum('amount'))['total'] or 0
            
            if count > 0:
                self.stdout.write(f"{label:<20}: {count:>6} transactions, ${total:>12,.2f}")
        
        # 4. SAMPLE TRANSACTIONS FOR MANUAL REVIEW
        self.stdout.write("\n" + "="*80)
        self.stdout.write("4. SAMPLE TRANSACTIONS FOR PATTERN IDENTIFICATION")
        self.stdout.write("="*80)
        
        # Group by similar amounts to find patterns
        self.stdout.write("\nHigh-frequency receivers needing rules:")
        top_receivers = uncategorized.values('receiver').annotate(
            count=Count('id')
        ).filter(count__gte=3).order_by('-count')
        
        for rec in top_receivers:
            receiver = rec['receiver']
            count = rec['count']
            
            # Get sample transactions
            samples = uncategorized.filter(receiver=receiver)[:3]
            self.stdout.write(f"\n{receiver} ({count} transactions):")
            
            for txn in samples:
                dept = txn.department.name if hasattr(txn, 'department') and txn.department else 'No Dept'
                desc = (txn.description or 'No description')[:50]
                self.stdout.write(f"  - ${txn.amount:,.2f} | {dept} | {desc}")
        
        # 5. SUGGESTED NEW RULES
        self.stdout.write("\n" + "="*80)
        self.stdout.write("5. SUGGESTED NEW CATEGORIZATION RULES")
        self.stdout.write("="*80)
        
        suggestions = self._generate_rule_suggestions(uncategorized)
        
        for i, suggestion in enumerate(suggestions, 1):
            self.stdout.write(f"\n{i}. {suggestion['rule_name']}")
            self.stdout.write(f"   Matches: {suggestion['count']} transactions (${suggestion['amount']:,.2f})")
            self.stdout.write(f"   Pattern: {suggestion['pattern']}")
            self.stdout.write(f"   Suggested Category: {suggestion['category']}")
            if suggestion.get('confidence'):
                self.stdout.write(f"   Confidence: {suggestion['confidence']}")
        
        self.stdout.write("\n" + "="*80)
        self.stdout.write(self.style.SUCCESS("Analysis complete!"))
        self.stdout.write("\nNext steps:")
        self.stdout.write("1. Review suggested rules above")
        self.stdout.write("2. Add rules to categorize_transactions.py")
        self.stdout.write("3. Run categorize_transactions --dry-run to test")
        self.stdout.write("4. Execute categorization")
        self.stdout.write("="*80)
    
    def _generate_rule_suggestions(self, uncategorized):
        """Generate suggested categorization rules"""
        suggestions = []
        
        # Analyze patterns
        # Rule 1: Health Department transactions
        health_txns = uncategorized.filter(department__name='Health Department')
        if health_txns.exists():
            count = health_txns.count()
            amount = health_txns.aggregate(total=Sum('amount'))['total']
            suggestions.append({
                'rule_name': 'Health Department Expenses',
                'pattern': 'department == "Health Department"',
                'category': 'Operational Expenses or Health Services',
                'count': count,
                'amount': amount,
                'confidence': 'medium'
            })
        
        # Rule 2: Small amounts (<$500) to individuals
        small_individual = uncategorized.filter(
            amount__lt=500,
            department__name='HR Department'
        )
        if small_individual.exists():
            count = small_individual.count()
            amount = small_individual.aggregate(total=Sum('amount'))['total']
            suggestions.append({
                'rule_name': 'Small HR Payments',
                'pattern': 'department == "HR" AND amount < $500',
                'category': 'Human Resources or Miscellaneous',
                'count': count,
                'amount': amount,
                'confidence': 'medium'
            })
        
        # Rule 3: Management Department expenses
        mgmt_txns = uncategorized.filter(department__name='Management Department')
        if mgmt_txns.exists():
            count = mgmt_txns.count()
            amount = mgmt_txns.aggregate(total=Sum('amount'))['total']
            suggestions.append({
                'rule_name': 'Management Expenses',
                'pattern': 'department == "Management Department"',
                'category': 'Operational Expenses or Professional Services',
                'count': count,
                'amount': amount,
                'confidence': 'medium'
            })
        
        # Rule 4: Medium amounts ($500-$3000) to individuals
        medium_amounts = uncategorized.filter(
            amount__gte=500,
            amount__lt=3000
        )
        if medium_amounts.exists():
            count = medium_amounts.count()
            amount = medium_amounts.aggregate(total=Sum('amount'))['total']
            suggestions.append({
                'rule_name': 'Medium Individual Payments',
                'pattern': 'amount between $500-$3,000',
                'category': 'Operational Expenses or Salaries',
                'count': count,
                'amount': amount,
                'confidence': 'low'
            })
        
        return suggestions

