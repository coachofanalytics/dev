"""
Classify Budget Category Tiers Management Command

Analyzes $1.49M transaction dataset to classify budget categories into tiers:
- Tier A: Known/Recurring (auto-approve)
- Tier B: Variable/Operational (priority-based)
- Tier C: Strategic/Discretionary (assessment required)

Calculates:
- typical_monthly_amount (average monthly spending)
- variance_threshold (acceptable variation %)
- is_recurring (spending pattern detection)

Usage:
    python manage.py classify_budget_category_tiers --analyze
    python manage.py classify_budget_category_tiers --analyze --save
    python manage.py classify_budget_category_tiers --export tier_classification.csv
"""

from django.core.management.base import BaseCommand
from django.db.models import Sum, Count, Avg, StdDev, Min, Max
from django.db.models.functions import TruncMonth
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta
import csv
import json

from finance.models import Transaction, BudgetCategory
from main.models import Company


class Command(BaseCommand):
    help = 'Analyze transaction data and classify budget categories into approval tiers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--analyze',
            action='store_true',
            help='Run analysis and display tier recommendations',
        )
        parser.add_argument(
            '--save',
            action='store_true',
            help='Save tier classifications to database',
        )
        parser.add_argument(
            '--export',
            type=str,
            help='Export tier classification to CSV file',
        )
        parser.add_argument(
            '--company',
            type=str,
            default='coda',
            help='Company slug to analyze (default: coda)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('BUDGET CATEGORY TIER CLASSIFICATION'))
        self.stdout.write(self.style.SUCCESS('Analyzing $1.49M Transaction Dataset'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))
        
        company_slug = options['company']
        
        try:
            company = Company.objects.get(slug=company_slug)
        except Company.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Company '{company_slug}' not found"))
            return
        
        # Run analysis
        analysis_results = self.analyze_categories(company)
        
        # Display results
        self.display_results(analysis_results)
        
        # Export if requested
        if options.get('export'):
            self.export_results(analysis_results, options['export'])
            self.stdout.write(self.style.SUCCESS(f"\n✅ Exported to {options['export']}"))
        
        # Save to database if requested
        if options.get('save'):
            self.save_classifications(analysis_results)
            self.stdout.write(self.style.SUCCESS("\n✅ Tier classifications saved to database"))
    
    def analyze_categories(self, company):
        """
        Analyze transaction data for each category and determine tier classification.
        
        Returns dict with category analysis including:
        - tier recommendation (A/B/C)
        - typical monthly amount
        - variance threshold
        - is recurring
        - reasoning
        """
        categories = BudgetCategory.objects.all()
        results = []
        
        for category in categories:
            analysis = self.analyze_single_category(category, company)
            results.append(analysis)
        
        return results
    
    def analyze_single_category(self, category, company):
        """Analyze spending patterns for a single category"""
        
        # Get all transactions for this category
        transactions = Transaction.objects.filter(
            budget_category=category,
            company=company
        ).exclude(
            amount__isnull=True
        ).exclude(
            amount=0
        )
        
        total_transactions = transactions.count()
        
        if total_transactions == 0:
            return {
                'category_id': category.id,
                'category_name': category.name,
                'tier': 'C',
                'tier_reason': 'No transaction data available',
                'total_transactions': 0,
                'total_spending': Decimal('0'),
                'typical_monthly_amount': None,
                'variance_threshold': Decimal('20.00'),
                'is_recurring': False,
                'auto_approve_recommended': False,
                'monthly_frequency': 0,
                'amount_variance_pct': 0,
            }
        
        # Calculate statistics
        total_spending = transactions.aggregate(total=Sum('amount'))['total'] or Decimal('0')
        avg_amount = transactions.aggregate(avg=Avg('amount'))['avg'] or Decimal('0')
        min_amount = transactions.aggregate(min=Min('amount'))['min'] or Decimal('0')
        max_amount = transactions.aggregate(max=Max('amount'))['max'] or Decimal('0')
        
        # Calculate monthly statistics
        monthly_data = transactions.annotate(
            month=TruncMonth('date')
        ).values('month').annotate(
            monthly_total=Sum('amount'),
            monthly_count=Count('id')
        ).order_by('month')
        
        # Determine time period
        if transactions.exists():
            earliest = transactions.order_by('date').first().date
            latest = transactions.order_by('-date').first().date
            months_span = ((latest.year - earliest.year) * 12 + latest.month - earliest.month) + 1
        else:
            months_span = 1
        
        # Calculate typical monthly amount
        typical_monthly = total_spending / Decimal(str(max(months_span, 1)))
        
        # Calculate transaction frequency (transactions per month)
        monthly_frequency = total_transactions / max(months_span, 1)
        
        # Calculate amount variance
        if avg_amount > 0:
            amount_variance_pct = ((max_amount - min_amount) / avg_amount * 100) if avg_amount > 0 else 100
        else:
            amount_variance_pct = 100
        
        # Determine if recurring (>0.5 transactions per month on average)
        is_recurring = monthly_frequency >= 0.5
        
        # Calculate months with activity
        months_with_activity = len(monthly_data)
        activity_rate = (months_with_activity / max(months_span, 1)) * 100 if months_span > 0 else 0
        
        # Classify into tier
        tier, tier_reason = self.classify_tier(
            category_name=category.name,
            total_transactions=total_transactions,
            monthly_frequency=monthly_frequency,
            amount_variance_pct=amount_variance_pct,
            is_recurring=is_recurring,
            activity_rate=activity_rate,
            typical_monthly=typical_monthly
        )
        
        # Determine variance threshold based on tier and variance
        variance_threshold = self.calculate_variance_threshold(tier, amount_variance_pct)
        
        # Determine if auto-approve should be recommended
        auto_approve_recommended = (tier == 'A' and is_recurring and amount_variance_pct < 50)
        
        return {
            'category_id': category.id,
            'category_name': category.name,
            'tier': tier,
            'tier_reason': tier_reason,
            'total_transactions': total_transactions,
            'total_spending': total_spending,
            'typical_monthly_amount': typical_monthly,
            'variance_threshold': variance_threshold,
            'is_recurring': is_recurring,
            'auto_approve_recommended': auto_approve_recommended,
            'monthly_frequency': monthly_frequency,
            'amount_variance_pct': amount_variance_pct,
            'activity_rate': activity_rate,
            'months_span': months_span,
            'months_with_activity': months_with_activity,
            'avg_amount': avg_amount,
            'min_amount': min_amount,
            'max_amount': max_amount,
        }
    
    def classify_tier(self, category_name, total_transactions, monthly_frequency, 
                     amount_variance_pct, is_recurring, activity_rate, typical_monthly):
        """
        Classify category into Tier A/B/C based on spending patterns.
        
        Tier A (Known/Recurring):
        - High frequency (>= 0.8 transactions/month)
        - Recurring pattern
        - Low variance (< 30%)
        - Essential/operational
        
        Tier B (Variable/Operational):
        - Medium frequency (0.2-0.8 transactions/month)
        - Operational necessity
        - Medium variance (30-70%)
        
        Tier C (Strategic/Discretionary):
        - Low frequency (< 0.2 transactions/month)
        - High variance (> 70%)
        - Strategic/one-off
        """
        
        # Define known Tier A categories (from REQUIREMENTS.md)
        tier_a_keywords = [
            'utilities', 'rent', 'insurance', 'security', 
            'salaries', 'wages', 'it and software', 'taxes', 
            'compliance', 'regulatory'
        ]
        
        # Define known Tier B categories
        tier_b_keywords = [
            'office supplies', 'inventory', 'facilities', 'equipment',
            'maintenance', 'repairs', 'training', 'travel', 'entertainment',
            'professional services', 'customer service', 'logistics', 'shipping'
        ]
        
        # Define known Tier C categories
        tier_c_keywords = [
            'research', 'development', 'r&d', 'marketing', 'advertising',
            'human resources', 'depreciation', 'amortization', 'operational expenses',
            'miscellaneous', 'other'
        ]
        
        category_lower = category_name.lower()
        
        # Check category name against known tiers
        if any(keyword in category_lower for keyword in tier_a_keywords):
            if monthly_frequency >= 0.8 and is_recurring and amount_variance_pct < 50:
                return 'A', f'High frequency ({monthly_frequency:.2f}/mo), recurring, low variance ({amount_variance_pct:.1f}%)'
            elif monthly_frequency >= 0.3:
                return 'B', f'Medium frequency ({monthly_frequency:.2f}/mo), some recurring pattern'
            else:
                return 'C', f'Low frequency ({monthly_frequency:.2f}/mo) despite being "{category_name}"'
        
        if any(keyword in category_lower for keyword in tier_b_keywords):
            if monthly_frequency >= 0.5:
                return 'B', f'Operational category with medium frequency ({monthly_frequency:.2f}/mo)'
            else:
                return 'C', f'Operational but low frequency ({monthly_frequency:.2f}/mo)'
        
        if any(keyword in category_lower for keyword in tier_c_keywords):
            return 'C', f'Strategic category - requires assessment'
        
        # Data-driven classification if not matched by keywords
        if monthly_frequency >= 1.0 and is_recurring and amount_variance_pct < 30:
            return 'A', f'Data-driven: High frequency ({monthly_frequency:.2f}/mo), very consistent'
        elif monthly_frequency >= 0.5 and amount_variance_pct < 60:
            return 'B', f'Data-driven: Medium frequency ({monthly_frequency:.2f}/mo), moderate variance'
        else:
            return 'C', f'Data-driven: Low frequency ({monthly_frequency:.2f}/mo) or high variance ({amount_variance_pct:.1f}%)'
    
    def calculate_variance_threshold(self, tier, amount_variance_pct):
        """
        Calculate appropriate variance threshold based on tier and observed variance.
        
        Tier A: Tighter control (15-25%)
        Tier B: Medium control (20-35%)
        Tier C: Looser control (30-50%)
        """
        if tier == 'A':
            # Tight control for recurring expenses
            if amount_variance_pct < 15:
                return Decimal('15.00')
            elif amount_variance_pct < 25:
                return Decimal('20.00')
            else:
                return Decimal('25.00')
        elif tier == 'B':
            # Medium control for variable expenses
            if amount_variance_pct < 30:
                return Decimal('25.00')
            elif amount_variance_pct < 50:
                return Decimal('30.00')
            else:
                return Decimal('35.00')
        else:  # Tier C
            # Looser control for strategic expenses
            if amount_variance_pct < 40:
                return Decimal('35.00')
            elif amount_variance_pct < 70:
                return Decimal('40.00')
            else:
                return Decimal('50.00')
    
    def display_results(self, results):
        """Display analysis results in formatted tables"""
        
        # Group by tier
        tier_a = [r for r in results if r['tier'] == 'A']
        tier_b = [r for r in results if r['tier'] == 'B']
        tier_c = [r for r in results if r['tier'] == 'C']
        
        self.stdout.write(self.style.SUCCESS('\n📊 TIER CLASSIFICATION RESULTS\n'))
        
        # Tier A
        self.stdout.write(self.style.SUCCESS(f'\n🔵 TIER A: Known/Recurring ({len(tier_a)} categories)'))
        self.stdout.write(self.style.SUCCESS('Auto-approve if within variance threshold\n'))
        self.display_tier_table(tier_a)
        
        # Tier B
        self.stdout.write(self.style.WARNING(f'\n🟡 TIER B: Variable/Operational ({len(tier_b)} categories)'))
        self.stdout.write(self.style.WARNING('Priority-based approval routing\n'))
        self.display_tier_table(tier_b)
        
        # Tier C
        self.stdout.write(self.style.ERROR(f'\n🔴 TIER C: Strategic/Discretionary ({len(tier_c)} categories)'))
        self.stdout.write(self.style.ERROR('Requires assessment and manual approval\n'))
        self.display_tier_table(tier_c)
        
        # Summary statistics
        self.display_summary(results, tier_a, tier_b, tier_c)
    
    def display_tier_table(self, categories):
        """Display tier results in table format"""
        if not categories:
            self.stdout.write('  (No categories in this tier)\n')
            return
        
        # Header
        self.stdout.write(
            f"  {'Category':<35} {'Txns':>6} {'Typical/Mo':>12} {'Variance':>10} {'Recurring':>10} {'Auto-Approve':>12}"
        )
        self.stdout.write('  ' + '-'*95)
        
        # Rows
        for cat in categories:
            typical = f"${cat['typical_monthly_amount']:,.0f}" if cat['typical_monthly_amount'] else "N/A"
            variance = f"{cat['variance_threshold']:.0f}%"
            recurring = "✅ Yes" if cat['is_recurring'] else "❌ No"
            auto_approve = "✅ Recommend" if cat['auto_approve_recommended'] else "❌ Manual"
            
            self.stdout.write(
                f"  {cat['category_name'][:34]:<35} {cat['total_transactions']:>6} {typical:>12} {variance:>10} {recurring:>10} {auto_approve:>12}"
            )
            self.stdout.write(f"    └─ Reason: {cat['tier_reason']}")
        
        self.stdout.write('')
    
    def display_summary(self, results, tier_a, tier_b, tier_c):
        """Display summary statistics"""
        total_categories = len(results)
        total_with_data = sum(1 for r in results if r['total_transactions'] > 0)
        total_without_data = total_categories - total_with_data
        
        total_spending = sum(r['total_spending'] for r in results)
        tier_a_spending = sum(r['total_spending'] for r in tier_a)
        tier_b_spending = sum(r['total_spending'] for r in tier_b)
        tier_c_spending = sum(r['total_spending'] for r in tier_c)
        
        auto_approve_candidates = sum(1 for r in results if r['auto_approve_recommended'])
        
        self.stdout.write(self.style.SUCCESS('\n📊 SUMMARY STATISTICS\n'))
        self.stdout.write(f"  Total Categories: {total_categories}")
        self.stdout.write(f"  Categories with transaction data: {total_with_data}")
        self.stdout.write(f"  Categories without data (dormant): {total_without_data}")
        self.stdout.write(f"\n  Total Spending Analyzed: ${total_spending:,.2f}")
        self.stdout.write(f"    - Tier A: ${tier_a_spending:,.2f} ({tier_a_spending/total_spending*100 if total_spending > 0 else 0:.1f}%)")
        self.stdout.write(f"    - Tier B: ${tier_b_spending:,.2f} ({tier_b_spending/total_spending*100 if total_spending > 0 else 0:.1f}%)")
        self.stdout.write(f"    - Tier C: ${tier_c_spending:,.2f} ({tier_c_spending/total_spending*100 if total_spending > 0 else 0:.1f}%)")
        
        self.stdout.write(f"\n  Tier Distribution:")
        self.stdout.write(f"    - Tier A (Auto-Approve): {len(tier_a)} categories")
        self.stdout.write(f"    - Tier B (Priority-Based): {len(tier_b)} categories")
        self.stdout.write(f"    - Tier C (Assessment): {len(tier_c)} categories")
        
        self.stdout.write(f"\n  Auto-Approval Candidates: {auto_approve_candidates} categories")
        
        if auto_approve_candidates > 0:
            self.stdout.write(self.style.SUCCESS(f"\n  💡 Estimated Automation: {auto_approve_candidates}/{total_with_data} categories ({auto_approve_candidates/max(total_with_data,1)*100:.1f}%)"))
    
    def save_classifications(self, results):
        """Save tier classifications to database"""
        self.stdout.write(self.style.WARNING('\n💾 Saving tier classifications to database...'))
        
        updated_count = 0
        
        for result in results:
            try:
                category = BudgetCategory.objects.get(id=result['category_id'])
                
                category.approval_tier = result['tier']
                category.typical_monthly_amount = result['typical_monthly_amount']
                category.variance_threshold = result['variance_threshold']
                category.is_recurring = result['is_recurring']
                category.last_pattern_analysis = timezone.now()
                
                # Only enable auto-approve for Tier A categories that are recommended
                if result['tier'] == 'A' and result['auto_approve_recommended']:
                    category.auto_approve_enabled = False  # Start disabled, Finance Manager can enable
                else:
                    category.auto_approve_enabled = False
                
                category.save()
                updated_count += 1
                
                self.stdout.write(f"  ✅ {category.name} → Tier {result['tier']}")
                
            except BudgetCategory.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"  ❌ Category ID {result['category_id']} not found"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ❌ Error saving {result['category_name']}: {e}"))
        
        self.stdout.write(self.style.SUCCESS(f"\n✅ Updated {updated_count} categories"))
    
    def export_results(self, results, filename):
        """Export results to CSV file"""
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = [
                'category_name', 'tier', 'tier_reason', 'total_transactions',
                'total_spending', 'typical_monthly_amount', 'variance_threshold',
                'is_recurring', 'auto_approve_recommended', 'monthly_frequency',
                'amount_variance_pct', 'activity_rate'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in results:
                writer.writerow({
                    'category_name': result['category_name'],
                    'tier': result['tier'],
                    'tier_reason': result['tier_reason'],
                    'total_transactions': result['total_transactions'],
                    'total_spending': f"{result['total_spending']:.2f}",
                    'typical_monthly_amount': f"{result['typical_monthly_amount']:.2f}" if result['typical_monthly_amount'] else '',
                    'variance_threshold': f"{result['variance_threshold']:.2f}",
                    'is_recurring': result['is_recurring'],
                    'auto_approve_recommended': result['auto_approve_recommended'],
                    'monthly_frequency': f"{result['monthly_frequency']:.2f}",
                    'amount_variance_pct': f"{result['amount_variance_pct']:.1f}",
                    'activity_rate': f"{result.get('activity_rate', 0):.1f}",
                })

