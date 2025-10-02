"""
Intelligent transaction categorization script
Uses patterns, keywords, and machine learning to auto-assign categories
"""
from django.core.management.base import BaseCommand
from django.db.models import Q
from finance.models import Transaction, BudgetCategory
from accounts.models import Department
from decimal import Decimal
from collections import defaultdict
import re


class Command(BaseCommand):
    help = 'Intelligently categorize uncategorized transactions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )
        parser.add_argument(
            '--auto-assign',
            action='store_true',
            help='Automatically assign categories based on patterns (no confirmation)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        auto_assign = options['auto_assign']
        
        self.stdout.write("="*80)
        self.stdout.write("INTELLIGENT TRANSACTION CATEGORIZATION")
        self.stdout.write("="*80)
        
        # Get uncategorized transactions
        uncategorized = Transaction.objects.filter(category__isnull=True)
        total_uncategorized = uncategorized.count()
        
        self.stdout.write(f"\nFound {total_uncategorized} uncategorized transactions")
        
        if total_uncategorized == 0:
            self.stdout.write(self.style.SUCCESS("✓ All transactions are categorized!"))
            return
        
        # Define categorization rules
        category_patterns = self._build_categorization_rules()
        
        # Analyze and categorize
        categorization_plan = self._analyze_transactions(uncategorized, category_patterns)
        
        # Display plan
        self._display_categorization_plan(categorization_plan)
        
        # Execute if not dry run
        if not dry_run:
            if auto_assign or self._confirm_execution():
                self._execute_categorization(categorization_plan)
                self.stdout.write(self.style.SUCCESS("\n✓ Categorization complete!"))
            else:
                self.stdout.write(self.style.WARNING("\n⚠ Categorization cancelled"))
        else:
            self.stdout.write(self.style.WARNING("\n[DRY RUN] No changes made"))
        
        # Generate learnings report
        self._generate_learnings_report(categorization_plan)
    
    def _build_categorization_rules(self):
        """
        Build intelligent categorization rules based on patterns
        
        This teaches us what makes good categorization:
        1. Receiver name patterns
        2. Description keywords
        3. Amount ranges
        4. Department associations
        5. Transaction frequency
        """
        
        rules = {
            'Utilities': {
                'keywords': ['electricity', 'water', 'power', 'kplc', 'utility', 'bill payment'],
                'receivers': ['kplc', 'nairobi water'],
                'amount_range': (500, 10000),
                'confidence': 'high',
            },
            'IT and Software': {
                'keywords': ['software', 'hardware', 'computer', 'internet', 'hosting', 'domain', 'tech', 
                           'data bundles', 'subscription', 'safaricom'],
                'receivers': ['safaricom'],  # All variations handled in receiver matching
                'amount_range': (500, 50000),
                'confidence': 'high',
            },
            'Salaries and Wages': {
                'keywords': ['salary', 'wage', 'payroll', 'allowance', 'bonus', 'overtime'],
                'receivers': ['idah wairimu', 'george ndalo', 'edwin kimtai', 'collins makokha', 
                            'david musiitwa', 'sylvia jelante'],
                'amount_range': (1000, 50000),  # Typical salary range
                'departments': ['HR Department'],
                'confidence': 'high',
            },
            'Human Resources': {
                'keywords': ['recruitment', 'training', 'hr', 'personnel', 'cleaning', 'labor', 'labour'],
                'receivers': ['idah wairimu', 'nicodemus libindu'],
                'amount_range': (500, 10000),
                'departments': ['HR Department'],
                'confidence': 'high',  # Upgraded from medium
            },
            'Operational Expenses': {
                'keywords': ['supplies', 'materials', 'equipment', 'office', 'stationery', 
                           'food', 'vegetables', 'polyfilla', 'varnish', 'glue', 'nails',
                           'timber', 'matunda', 'makutano'],  # Food and facilities supplies
                'receivers': ['magaisi', 'philip', 'eunice', 'maxwel ikhuluru', 'geogre ndalo'],
                'amount_range': (100, 15000),  # Expanded range
                'confidence': 'high',  # Upgraded - clear patterns
            },
            'Travel and Entertainment': {
                'keywords': ['transport', 'fuel', 'taxi', 'flight', 'hotel', 'accommodation', 'boda',
                           'butere', 'refund'],
                'receivers': ['boda', 'uber', 'bolt'],
                'amount_range': (100, 5000),
                'confidence': 'high',  # Upgraded - boda is clear
            },
            'Professional Services': {
                'keywords': ['consultant', 'legal', 'accounting', 'audit', 'professional', 
                           'pavement', 'labour cost'],
                'receivers': ['nicodemus libindu'],
                'amount_range': (1000, 20000),
                'confidence': 'high',  # Upgraded - labor/pavement clear
            },
            'Maintenance and Repairs': {
                'keywords': ['repair', 'maintenance', 'fix', 'service', 'trimming', 'grooving'],
                'receivers': [],
                'amount_range': (200, 5000),
                'confidence': 'medium',
            },
            'Facilities and Equipment': {
                'keywords': ['furniture', 'facility', 'building', 'renovation', 'construction'],
                'receivers': [],
                'amount_range': (1000, 50000),
                'confidence': 'medium',
            },
            'Rent': {
                'keywords': ['rent', 'lease', 'rental'],
                'receivers': [],
                'amount_range': (5000, 100000),
                'confidence': 'high',
            },
        }
        
        return rules
    
    def _analyze_transactions(self, transactions, category_patterns):
        """
        Analyze each transaction and suggest categorization
        """
        categorization_plan = defaultdict(list)
        unmatched = []
        
        for txn in transactions:
            matched = False
            match_details = {
                'transaction': txn,
                'confidence': 0,
                'reasons': [],
            }
            
            # Check each category pattern
            for category_name, pattern in category_patterns.items():
                confidence = 0
                reasons = []
                
                # Check receiver name
                if txn.receiver:
                    receiver_lower = txn.receiver.lower()
                    for receiver_pattern in pattern.get('receivers', []):
                        if receiver_pattern.lower() in receiver_lower:
                            confidence += 40
                            reasons.append(f"Receiver matches: {receiver_pattern}")
                
                # Check description keywords
                if txn.description:
                    desc_lower = txn.description.lower()
                    for keyword in pattern.get('keywords', []):
                        if keyword.lower() in desc_lower:
                            confidence += 30
                            reasons.append(f"Description contains: {keyword}")
                
                # Check department (handle missing department gracefully)
                try:
                    if txn.department and pattern.get('departments'):
                        if txn.department.name in pattern['departments']:
                            confidence += 20
                            reasons.append(f"Department: {txn.department.name}")
                except Transaction.department.RelatedObjectDoesNotExist:
                    pass  # Transaction has no department
                
                # Check amount range
                if txn.amount and pattern.get('amount_range'):
                    min_amt, max_amt = pattern['amount_range']
                    if min_amt <= float(txn.amount) <= max_amt:
                        confidence += 10
                        reasons.append(f"Amount in range: ${min_amt}-${max_amt}")
                
                # If confidence is high enough, suggest this category
                if confidence > match_details['confidence']:
                    match_details['category'] = category_name
                    match_details['confidence'] = confidence
                    match_details['reasons'] = reasons
                    matched = True
            
            # Add to appropriate list
            if matched and match_details['confidence'] >= 30:  # Threshold
                categorization_plan[match_details['category']].append(match_details)
            else:
                unmatched.append(match_details)
        
        categorization_plan['UNMATCHED'] = unmatched
        
        return categorization_plan
    
    def _display_categorization_plan(self, plan):
        """
        Display the categorization plan for review
        """
        self.stdout.write("\n" + "="*80)
        self.stdout.write("CATEGORIZATION PLAN")
        self.stdout.write("="*80)
        
        total_matched = 0
        
        for category, matches in plan.items():
            if category == 'UNMATCHED':
                continue
            
            count = len(matches)
            total_matched += count
            total_amount = sum(m['transaction'].amount or 0 for m in matches)
            avg_confidence = sum(m['confidence'] for m in matches) / count if count > 0 else 0
            
            self.stdout.write(f"\n{category}:")
            self.stdout.write(f"  Transactions: {count}")
            self.stdout.write(f"  Total Amount: ${total_amount:,.2f}")
            self.stdout.write(f"  Avg Confidence: {avg_confidence:.0f}%")
            
            # Show top 3 examples
            if count > 0:
                self.stdout.write("  Examples:")
                for match in matches[:3]:
                    txn = match['transaction']
                    self.stdout.write(f"    - {txn.receiver} | ${txn.amount} | {match['confidence']}% | {', '.join(match['reasons'][:2])}")
        
        # Show unmatched
        unmatched = plan.get('UNMATCHED', [])
        self.stdout.write(f"\n{'='*80}")
        self.stdout.write(f"SUMMARY:")
        self.stdout.write(f"  Will categorize: {total_matched} transactions")
        self.stdout.write(f"  Cannot match: {len(unmatched)} transactions (need manual review)")
        
        if len(unmatched) > 0:
            self.stdout.write(f"\n  Unmatched examples (need rules or manual categorization):")
            for match in unmatched[:5]:
                txn = match['transaction']
                try:
                    dept_name = txn.department.name if txn.department else 'No Dept'
                except:
                    dept_name = 'No Dept'
                self.stdout.write(f"    - {txn.receiver} | ${txn.amount} | Dept: {dept_name}")
    
    def _confirm_execution(self):
        """Ask for confirmation before making changes"""
        response = input("\nProceed with categorization? (yes/no): ")
        return response.lower() in ['yes', 'y']
    
    def _execute_categorization(self, plan):
        """Execute the categorization plan"""
        self.stdout.write("\n" + "="*80)
        self.stdout.write("EXECUTING CATEGORIZATION...")
        self.stdout.write("="*80)
        
        updated_count = 0
        
        for category_name, matches in plan.items():
            if category_name == 'UNMATCHED':
                continue
            
            # Get or create category
            try:
                category = BudgetCategory.objects.get(name=category_name)
            except BudgetCategory.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"  ⚠ Category '{category_name}' not found, skipping..."))
                continue
            
            # Update transactions
            for match in matches:
                txn = match['transaction']
                txn.category = category
                txn.save()
                updated_count += 1
            
            self.stdout.write(f"  ✓ Updated {len(matches)} transactions → {category_name}")
        
        self.stdout.write(f"\n  Total updated: {updated_count} transactions")
    
    def _generate_learnings_report(self, plan):
        """
        Generate report on what we learned for system improvement
        """
        self.stdout.write("\n" + "="*80)
        self.stdout.write("LEARNINGS FOR SYSTEM IMPROVEMENT")
        self.stdout.write("="*80)
        
        # Analyze patterns
        all_matches = []
        for category, matches in plan.items():
            if category != 'UNMATCHED':
                all_matches.extend(matches)
        
        unmatched = plan.get('UNMATCHED', [])
        
        # Calculate success rate
        total = len(all_matches) + len(unmatched)
        success_rate = (len(all_matches) / total * 100) if total > 0 else 0
        
        self.stdout.write(f"\n1. PATTERN MATCHING SUCCESS RATE: {success_rate:.1f}%")
        self.stdout.write(f"   - Successfully matched: {len(all_matches)}")
        self.stdout.write(f"   - Could not match: {len(unmatched)}")
        
        # Most reliable patterns
        self.stdout.write(f"\n2. MOST RELIABLE CATEGORIZATION SIGNALS:")
        signal_scores = defaultdict(int)
        for match in all_matches:
            for reason in match['reasons']:
                if 'Receiver matches' in reason:
                    signal_scores['receiver_name'] += 1
                elif 'Description contains' in reason:
                    signal_scores['keywords'] += 1
                elif 'Department' in reason:
                    signal_scores['department'] += 1
                elif 'Amount' in reason:
                    signal_scores['amount_range'] += 1
        
        for signal, count in sorted(signal_scores.items(), key=lambda x: x[1], reverse=True):
            self.stdout.write(f"   - {signal}: {count} matches")
        
        # Suggest UI improvements
        self.stdout.write(f"\n3. SUGGESTED UI/UX IMPROVEMENTS:")
        self.stdout.write("   a. Auto-suggest category based on:")
        self.stdout.write("      - Receiver name (most reliable)")
        self.stdout.write("      - Description keywords")
        self.stdout.write("      - Department context")
        self.stdout.write("      - Amount range")
        
        self.stdout.write("\n   b. Required fields:")
        self.stdout.write("      - Category (MUST be selected)")
        self.stdout.write("      - Department (MUST be assigned)")
        self.stdout.write("      - Description (at least 10 characters)")
        
        self.stdout.write("\n   c. Data entry helpers:")
        self.stdout.write("      - Receiver dropdown with common names/vendors")
        self.stdout.write("      - Category pre-populated based on context")
        self.stdout.write("      - Warning if unusual amount for category")
        self.stdout.write("      - 'Same as last transaction' quick button")
        
        self.stdout.write("\n   d. Validation rules:")
        self.stdout.write("      - Prevent submission without category")
        self.stdout.write("      - Flag transactions >$10,000 for review")
        self.stdout.write("      - Suggest split if multiple categories detected")
        
        # Common unmatched patterns
        if len(unmatched) > 0:
            self.stdout.write(f"\n4. UNMATCHED TRANSACTION PATTERNS (Need Manual Rules):")
            
            # Group by receiver
            receiver_groups = defaultdict(list)
            for match in unmatched:
                txn = match['transaction']
                if txn.receiver:
                    receiver_groups[txn.receiver].append(txn)
            
            # Show top unmatched receivers
            top_unmatched = sorted(
                receiver_groups.items(),
                key=lambda x: len(x[1]),
                reverse=True
            )[:5]
            
            for receiver, txns in top_unmatched:
                count = len(txns)
                total_amt = sum(t.amount or 0 for t in txns)
                self.stdout.write(f"   - {receiver}: {count} transactions, ${total_amt:,.2f}")
                self.stdout.write(f"     → Create rule or add to lookup table")
        
        self.stdout.write("\n" + "="*80)

