"""
Production Database Discovery - Fixed Version
Handles all import variations
"""

import os
import sys

# Setup Django
sys.path.insert(0, '/app/coda')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda_project.settings')

import django
django.setup()

from django.db.models import Count, Sum, Min, Max, F
from decimal import Decimal

print('\n' + '='*70)
print(' PRODUCTION DATABASE DISCOVERY - BUDGET SYSTEM')
print('='*70)

# Import Company
try:
    from main.models import Company
    print('✓ Company model loaded')
except Exception as e:
    print(f'✗ Company import failed: {e}')
    sys.exit(1)

# Import Department (try multiple locations)
Department = None
try:
    from main.models import Department
    print('✓ Department from main.models')
except ImportError:
    try:
        from accounts.models import Department
        print('✓ Department from accounts.models')
    except ImportError:
        try:
            # Check if it's in django.contrib.auth User profile
            from django.contrib.auth import get_user_model
            User = get_user_model()
            if hasattr(User, 'department'):
                print('⚠️  Department is user attribute, not separate model')
        except Exception as e:
            print(f'⚠️  Department model not found: {e}')

# Import Finance models
print('\n📦 Loading Finance Models...')

try:
    from finance.models.budget import Budget, BudgetCategory, BudgetSubcategory
    print('✓ Budget models loaded from finance.models.budget')
except ImportError:
    try:
        from finance.models import Budget, BudgetCategory, BudgetSubcategory
        print('✓ Budget models loaded from finance.models')
    except ImportError as e:
        print(f'✗ Budget models import failed: {e}')
        Budget = BudgetCategory = BudgetSubcategory = None

try:
    from finance.models.core import Transaction
    print('✓ Transaction from finance.models.core')
except ImportError:
    try:
        from finance.models import Transaction
        print('✓ Transaction from finance.models')
    except ImportError as e:
        print(f'✗ Transaction import failed: {e}')
        Transaction = None

# Basic Counts
print('\n' + '='*70)
print(' DATABASE STATE')
print('='*70)

# Companies
try:
    company_count = Company.objects.count()
    print(f'\n✓ Companies: {company_count}')
    companies = Company.objects.all()
    for c in companies:
        print(f'  - {c.name} (slug: {c.slug})')
except Exception as e:
    print(f'\n✗ Companies ERROR: {e}')

# Departments
if Department:
    try:
        dept_count = Department.objects.count()
        print(f'\n✓ Departments: {dept_count}')
        if dept_count > 0:
            depts = Department.objects.all()[:10]
            for d in depts:
                print(f'  - {d.name}')
    except Exception as e:
        print(f'\n✗ Departments ERROR: {e}')

# Budget Categories
if BudgetCategory:
    try:
        cat_count = BudgetCategory.objects.count()
        print(f'\n✓ Budget Categories: {cat_count}')
        if cat_count > 0:
            cats = BudgetCategory.objects.all()
            for cat in cats:
                subcat_count = BudgetSubcategory.objects.filter(category=cat).count() if BudgetSubcategory else 0
                print(f'  - {cat.name} ({subcat_count} subcategories)')
        else:
            print('  ⚠️  NO CATEGORIES - Need to create!')
    except Exception as e:
        print(f'\n✗ Categories ERROR: {e}')

# Budget Items
if Budget:
    try:
        total_budgets = Budget.objects.count()
        active_budgets = Budget.objects.filter(is_active=True).count()
        print(f'\n✓ Budget Items: {total_budgets}')
        print(f'  - Active: {active_budgets}')
        
        if total_budgets > 0:
            # Calculate total using proper formula
            total_amount = Budget.objects.aggregate(
                total=Sum(F('unit_price') * F('quantity') * F('cases'))
            )['total'] or 0
            print(f'  - Total Budget Value: ${total_amount:,.2f}')
            
            # By category
            print(f'\n  Top 5 Categories by Budget:')
            by_cat = Budget.objects.values('category__name').annotate(
                count=Count('id'),
                total=Sum(F('unit_price') * F('quantity') * F('cases'))
            ).order_by('-total')[:5]
            
            for item in by_cat:
                name = item['category__name'] or 'Uncategorized'
                print(f'    {name:30s}: ${item["total"]:,.2f}')
    except Exception as e:
        print(f'\n✗ Budget Items ERROR: {e}')

# Transactions - THE KEY DATA SOURCE
if Transaction:
    try:
        trans_count = Transaction.objects.count()
        print(f'\n✓ Transactions: {trans_count}')
        
        if trans_count > 0:
            # Total amount
            total_amount = Transaction.objects.aggregate(Sum('amount'))['amount__sum'] or 0
            print(f'  - Total Value: ${total_amount:,.2f}')
            
            # Categorization rate
            categorized = Transaction.objects.exclude(category__isnull=True).count()
            uncategorized = trans_count - categorized
            cat_rate = (categorized / trans_count * 100) if trans_count > 0 else 0
            print(f'  - Categorized: {categorized} ({cat_rate:.1f}%)')
            print(f'  - Uncategorized: {uncategorized} ({100-cat_rate:.1f}%)')
            
            # Date range
            date_range = Transaction.objects.aggregate(
                earliest=Min('transaction_date'),
                latest=Max('transaction_date')
            )
            print(f'  - Date Range: {date_range["earliest"]} to {date_range["latest"]}')
            
            # Monthly average
            from datetime import datetime
            if date_range['earliest'] and date_range['latest']:
                days_diff = (date_range['latest'] - date_range['earliest']).days
                months = max(1, days_diff / 30)
                monthly_avg = total_amount / months
                print(f'  - Monthly Average: ${monthly_avg:,.2f}')
            
            # Top 10 categories by spend
            print(f'\n  💰 Top 10 Categories by Actual Spend:')
            by_category = Transaction.objects.values('category__name').annotate(
                count=Count('id'),
                total=Sum('amount')
            ).order_by('-total')[:10]
            
            for cat in by_category:
                cat_name = cat['category__name'] or 'Uncategorized'
                print(f'    {cat_name:30s}: ${cat["total"]:>12,.2f} ({cat["count"]:>4d} txns)')
            
            # Top 10 vendors
            print(f'\n  🏪 Top 10 Vendors by Spend:')
            by_vendor = Transaction.objects.values('receiver_name').annotate(
                count=Count('id'),
                total=Sum('amount')
            ).order_by('-total')[:10]
            
            for vendor in by_vendor:
                vendor_name = vendor['receiver_name'] or 'Unknown'
                print(f'    {vendor_name:30s}: ${vendor["total"]:>12,.2f} ({vendor["count"]:>4d} txns)')
                
        else:
            print('  ⚠️  NO TRANSACTION DATA!')
    except Exception as e:
        print(f'\n✗ Transactions ERROR: {e}')

# Recommendations
print('\n' + '='*70)
print(' 🎯 RECOMMENDED NEXT STEPS')
print('='*70)

cat_count = BudgetCategory.objects.count() if BudgetCategory else 0
trans_count = Transaction.objects.count() if Transaction else 0
budget_count = Budget.objects.count() if Budget else 0

print(f'\nCurrent State: {cat_count} categories, {trans_count} transactions, {budget_count} budgets')

if cat_count == 0:
    print('\n📍 START: PHASE 1 - Create Budget Categories')
    print('   Why: Categories are foundation for everything')
    print('   Time: 30-60 minutes')
    print('   Method: Copy from UAT or create fresh')
    
elif trans_count > 100:
    categorized_pct = 0
    if Transaction:
        try:
            categorized = Transaction.objects.exclude(category__isnull=True).count()
            categorized_pct = (categorized / trans_count * 100) if trans_count > 0 else 0
        except:
            pass
    
    if categorized_pct < 90:
        print('\n📍 START: PHASE 2A - Auto-Categorize Transactions')
        print(f'   Why: Only {categorized_pct:.1f}% are categorized')
        print('   Time: 15 minutes')
        print('   Command: python manage.py categorize_transactions --auto-assign')
    else:
        print('\n📍 START: PHASE 2B - Generate AI Budget')
        print(f'   Why: {trans_count} transactions, {categorized_pct:.1f}% categorized')
        print('   Time: 30 minutes')
        print('   Command: python manage.py generate_budget_projections --months 12 --save')

elif budget_count == 0:
    print('\n📍 START: PHASE 3 - Create Budget')
    print('   Why: No budget exists yet')
    print('   Time: 2-4 hours manual or 30 min AI')
    print('   Access: /finance/budget-dashboard/coda/')

else:
    print('\n✅ SYSTEM READY')
    print('   Categories: ✓')
    print('   Transactions: ✓')
    print('   Budgets: ✓')
    print('   Next: Configure approval workflow (Phase 4)')

print('\n' + '='*70)
print(' END OF DISCOVERY')
print('='*70 + '\n')

