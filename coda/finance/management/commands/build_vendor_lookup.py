"""
Build vendor lookup table from existing transaction data

This creates standardized vendor records and identifies common aliases
"""
from django.core.management.base import BaseCommand
from django.db.models import Count, Sum, Avg, Q
from finance.models import Transaction, BudgetCategory
from decimal import Decimal
from collections import defaultdict
import re


class Command(BaseCommand):
    help = 'Build vendor lookup table from transaction data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--min-transactions',
            type=int,
            default=2,
            help='Minimum transactions to create vendor record (default: 2)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without saving',
        )

    def handle(self, *args, **options):
        min_transactions = options['min_transactions']
        dry_run = options['dry_run']
        
        self.stdout.write("="*80)
        self.stdout.write("BUILDING VENDOR LOOKUP TABLE FROM TRANSACTION DATA")
        self.stdout.write("="*80)
        
        # Analyze receiver patterns
        receiver_analysis = self._analyze_receivers(min_transactions)
        
        # Identify aliases (similar names)
        alias_groups = self._identify_aliases(receiver_analysis)
        
        # Display plan
        self._display_vendor_plan(alias_groups)
        
        # Execute if not dry run
        if not dry_run:
            self._create_vendor_records(alias_groups)
        else:
            self.stdout.write(self.style.WARNING("\n[DRY RUN] No changes made"))
        
        # Generate recommendations
        self._generate_recommendations(alias_groups)
    
    def _analyze_receivers(self, min_count):
        """
        Analyze all receivers in transaction data
        """
        self.stdout.write("\n1. Analyzing receiver patterns...")
        
        receivers = Transaction.objects.values('receiver').annotate(
            count=Count('id'),
            total_amount=Sum('amount'),
            avg_amount=Avg('amount')
        ).filter(
            count__gte=min_count,
            receiver__isnull=False
        ).order_by('-count')
        
        self.stdout.write(f"   Found {receivers.count()} receivers with {min_count}+ transactions")
        
        # Get category patterns for each receiver
        receiver_data = []
        for rec in receivers:
            receiver_name = rec['receiver']
            
            # Get most common category
            categories = Transaction.objects.filter(
                receiver=receiver_name,
                category__isnull=False
            ).values('category__name', 'category__id').annotate(
                count=Count('id')
            ).order_by('-count')
            
            primary_category = categories.first() if categories else None
            
            receiver_data.append({
                'name': receiver_name,
                'count': rec['count'],
                'total': rec['total_amount'] or 0,
                'avg': rec['avg_amount'] or 0,
                'primary_category': primary_category,
                'category_count': categories.count()
            })
        
        return receiver_data
    
    def _identify_aliases(self, receiver_data):
        """
        Identify receivers that are likely the same person/entity
        
        Uses:
        - Fuzzy string matching
        - Similar amounts
        - Common categories
        """
        self.stdout.write("\n2. Identifying aliases (similar names)...")
        
        groups = []
        processed = set()
        
        for i, rec1 in enumerate(receiver_data):
            if rec1['name'] in processed:
                continue
            
            group = {
                'primary': rec1['name'],
                'aliases': [],
                'total_count': rec1['count'],
                'total_amount': rec1['total'],
                'avg_amount': rec1['avg'],
                'primary_category': rec1['primary_category'],
                'vendor_type': self._guess_vendor_type(rec1)
            }
            
            # Find similar names
            for j, rec2 in enumerate(receiver_data):
                if i == j or rec2['name'] in processed:
                    continue
                
                similarity = self._calculate_similarity(rec1['name'], rec2['name'])
                
                if similarity > 0.8:  # 80% similar
                    group['aliases'].append({
                        'name': rec2['name'],
                        'similarity': similarity,
                        'count': rec2['count'],
                        'amount': rec2['total']
                    })
                    group['total_count'] += rec2['count']
                    group['total_amount'] += rec2['total']
                    processed.add(rec2['name'])
            
            groups.append(group)
            processed.add(rec1['name'])
        
        # Sort by total transactions
        groups.sort(key=lambda x: x['total_count'], reverse=True)
        
        self.stdout.write(f"   Identified {len(groups)} unique vendors")
        aliases_found = sum(len(g['aliases']) for g in groups)
        self.stdout.write(f"   Found {aliases_found} aliases")
        
        return groups
    
    def _calculate_similarity(self, name1, name2):
        """
        Calculate similarity between two names
        
        Uses:
        - Levenshtein distance
        - Common tokens
        - Case-insensitive comparison
        """
        n1 = name1.lower().strip()
        n2 = name2.lower().strip()
        
        # Exact match
        if n1 == n2:
            return 1.0
        
        # Check if one contains the other
        if n1 in n2 or n2 in n1:
            return 0.9
        
        # Token-based similarity
        tokens1 = set(re.findall(r'\w+', n1))
        tokens2 = set(re.findall(r'\w+', n2))
        
        if not tokens1 or not tokens2:
            return 0.0
        
        common = tokens1 & tokens2
        total = tokens1 | tokens2
        
        return len(common) / len(total) if total else 0.0
    
    def _guess_vendor_type(self, receiver_data):
        """Guess vendor type based on name and patterns"""
        name = receiver_data['name'].lower()
        
        # Known utility companies
        if any(util in name for util in ['kplc', 'safaricom', 'water', 'power']):
            return 'utility'
        
        # Known service providers
        if any(svc in name for svc in ['ltd', 'limited', 'inc', 'company']):
            return 'service_provider'
        
        # If many small transactions, likely employee
        if receiver_data['avg'] < 5000 and receiver_data['count'] > 5:
            return 'employee'
        
        # Default
        return 'other'
    
    def _display_vendor_plan(self, groups):
        """Display what vendors will be created"""
        self.stdout.write("\n" + "="*80)
        self.stdout.write("VENDOR CREATION PLAN")
        self.stdout.write("="*80)
        
        self.stdout.write(f"\nWill create {len(groups)} vendor records")
        
        # Show top 20
        self.stdout.write("\nTop 20 Vendors:")
        self.stdout.write(f"{'Vendor Name':<35} {'Type':<15} {'Txns':>6} {'Total':>12} {'Aliases':>8}")
        self.stdout.write("-"*80)
        
        for group in groups[:20]:
            name = group['primary'][:32]
            vtype = group['vendor_type']
            count = group['total_count']
            total = group['total_amount']
            alias_count = len(group['aliases'])
            
            self.stdout.write(f"{name:<35} {vtype:<15} {count:>6} ${total:>11,.0f} {alias_count:>8}")
            
            # Show aliases if any
            if group['aliases']:
                for alias in group['aliases'][:2]:
                    self.stdout.write(f"  ↳ {alias['name']} ({alias['similarity']:.0%} match)")
        
        # Show statistics
        total_vendors = len(groups)
        total_with_aliases = sum(1 for g in groups if g['aliases'])
        total_aliases = sum(len(g['aliases']) for g in groups)
        
        self.stdout.write(f"\n" + "="*80)
        self.stdout.write(f"Summary:")
        self.stdout.write(f"  Unique vendors: {total_vendors}")
        self.stdout.write(f"  Vendors with aliases: {total_with_aliases}")
        self.stdout.write(f"  Total aliases: {total_aliases}")
        self.stdout.write(f"  Data quality improvement: {total_aliases} inconsistencies will be resolved")
    
    def _create_vendor_records(self, groups):
        """Create Vendor and VendorAlias records"""
        self.stdout.write("\n" + "="*80)
        self.stdout.write("CREATING VENDOR RECORDS...")
        self.stdout.write("="*80)
        
        # Import here to avoid circular dependency
        try:
            from finance.models_vendor import Vendor, VendorAlias
        except ImportError:
            self.stdout.write(self.style.ERROR("Error: Vendor models not found"))
            self.stdout.write("Run migrations first: python manage.py makemigrations finance")
            return
        
        created_vendors = 0
        created_aliases = 0
        
        for group in groups:
            # Create or get vendor
            vendor, created = Vendor.objects.get_or_create(
                name=group['primary'],
                defaults={
                    'vendor_type': group['vendor_type'],
                    'total_transactions': group['total_count'],
                    'total_amount': group['total_amount'],
                    'average_transaction': group['avg_amount'],
                }
            )
            
            if created:
                created_vendors += 1
            
            # Set default category if available
            if group['primary_category'] and not vendor.default_category:
                try:
                    category = BudgetCategory.objects.get(
                        id=group['primary_category']['category__id']
                    )
                    vendor.default_category = category
                    vendor.save()
                except BudgetCategory.DoesNotExist:
                    pass
            
            # Create aliases
            for alias_data in group['aliases']:
                alias, created = VendorAlias.objects.get_or_create(
                    alias=alias_data['name'],
                    defaults={
                        'vendor': vendor,
                        'confidence': 'high' if alias_data['similarity'] > 0.9 else 'medium'
                    }
                )
                if created:
                    created_aliases += 1
        
        self.stdout.write(f"\n  Created {created_vendors} vendors")
        self.stdout.write(f"  Created {created_aliases} aliases")
        self.stdout.write(self.style.SUCCESS("\n✅ Vendor lookup table built successfully!"))
    
    def _generate_recommendations(self, groups):
        """Generate recommendations based on vendor analysis"""
        self.stdout.write("\n" + "="*80)
        self.stdout.write("RECOMMENDATIONS")
        self.stdout.write("="*80)
        
        # Find vendors needing review
        needs_review = []
        high_value = []
        utilities = []
        employees = []
        
        for group in groups:
            if len(group['aliases']) > 3:
                needs_review.append((group['primary'], len(group['aliases'])))
            
            if group['total_amount'] > 50000:
                high_value.append((group['primary'], group['total_amount']))
            
            if group['vendor_type'] == 'utility':
                utilities.append(group['primary'])
            
            if group['vendor_type'] == 'employee':
                employees.append(group['primary'])
        
        if needs_review:
            self.stdout.write(f"\n1. Vendors with Many Aliases (Review for Accuracy):")
            for name, count in sorted(needs_review, key=lambda x: x[1], reverse=True)[:5]:
                self.stdout.write(f"   - {name}: {count} aliases")
        
        if high_value:
            self.stdout.write(f"\n2. High-Value Vendors (Monitor Closely):")
            for name, amount in sorted(high_value, key=lambda x: x[1], reverse=True)[:5]:
                self.stdout.write(f"   - {name}: ${amount:,.2f}")
        
        if utilities:
            self.stdout.write(f"\n3. Utility Vendors (Auto-Categorize as Utilities):")
            for name in utilities[:10]:
                self.stdout.write(f"   - {name}")
        
        if employees:
            self.stdout.write(f"\n4. Employee Payments (Likely Salaries/HR):")
            self.stdout.write(f"   - {len(employees)} employees identified")
            self.stdout.write(f"   - Consider linking to HR/Payroll system")
        
        self.stdout.write(f"\n" + "="*80)
        self.stdout.write("Next Steps:")
        self.stdout.write("1. Review vendor records in admin")
        self.stdout.write("2. Adjust vendor types if needed")
        self.stdout.write("3. Set default categories for vendors")
        self.stdout.write("4. Update transaction form to use vendor lookup")
        self.stdout.write("="*80)


