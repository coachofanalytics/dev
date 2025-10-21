"""
Production Database Discovery - Robust Version
Handles import errors gracefully
"""

import os
import sys

# Setup Django
sys.path.insert(0, '/app/coda')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda_project.settings')

import django
django.setup()

from django.db.models import Count, Sum

print('\n' + '='*70)
print(' PRODUCTION DATABASE DISCOVERY REPORT')
print('='*70)

# Import models with error handling
print('\n📦 Importing Models...')

# Try different import paths
try:
    from main.models import Company
    print('✓ Company model imported')
except ImportError as e:
    print(f'✗ Company import failed: {e}')
    Company = None

try:
    from main.models import Department
    print('✓ Department model imported')
except ImportError:
    try:
        from accounts.models import Department
        print('✓ Department model imported (from accounts)')
    except ImportError as e:
        print(f'✗ Department import failed: {e}')
        Department = None

try:
    from finance.models import Budget
    print('✓ Budget model imported')
except ImportError as e:
    print(f'✗ Budget import failed: {e}')
    Budget = None

try:
    from finance.models import BudgetCategory
    print('✓ BudgetCategory model imported')
except ImportError as e:
    print(f'✗ BudgetCategory import failed: {e}')
    BudgetCategory = None

try:
    from finance.models import BudgetSubcategory
    print('✓ BudgetSubcategory model imported')
except ImportError as e:
    print(f'✗ BudgetSubcategory import failed: {e}')
    BudgetSubcategory = None

try:
    from finance.models import Transaction
    print('✓ Transaction model imported')
except ImportError as e:
    print(f'✗ Transaction import failed: {e}')
    Transaction = None

try:
    from finance.models import BudgetRequest
    print('✓ BudgetRequest model imported')
except ImportError as e:
    print(f'✗ BudgetRequest import failed: {e}')
    BudgetRequest = None

# Check basic counts
print('\n' + '='*70)
print(' DATABASE COUNTS')
print('='*70)

if Company:
    try:
        count = Company.objects.count()
        print(f'\n✓ Companies: {count}')
        if count > 0:
            companies = Company.objects.all()[:5]
            for c in companies:
                slug = getattr(c, 'slug', 'N/A')
                name = getattr(c, 'name', 'N/A')
                print(f'  - {name} (slug: {slug})')
    except Exception as e:
        print(f'✗ Companies ERROR: {e}')

if Department:
    try:
        count = Department.objects.count()
        print(f'\n✓ Departments: {count}')
        if count > 0:
            depts = Department.objects.all()[:10]
            for d in depts:
                name = getattr(d, 'name', 'N/A')
                print(f'  - {name}')
    except Exception as e:
        print(f'\n✗ Departments ERROR: {e}')
else:
    print('\n⚠️  Department model not available')

if Budget:
    try:
        total = Budget.objects.count()
        active = Budget.objects.filter(is_active=True).count()
        print(f'\n✓ Budget Items: {total}')
        print(f'  - Active: {active}')
        
        if total > 0:
            # Calculate total budget amount
            from django.db.models import F
            total_budget = Budget.objects.aggregate(
                total=Sum(F('unit_price') * F('quantity') * F('cases'))
            )['total'] or 0
            print(f'  - Total Budget Value: ${total_budget:,.2f}')
    except Exception as e:
        print(f'\n✗ Budget Items ERROR: {e}')
else:
    print('\n⚠️  Budget model not available')

if BudgetCategory:
    try:
        count = BudgetCategory.objects.count()
        print(f'\n✓ Budget Categories: {count}')
        if count > 0:
            cats = BudgetCategory.objects.all()
            for cat in cats:
                name = getattr(cat, 'name', 'N/A')
                print(f'  - {name}')
    except Exception as e:
        print(f'\n✗ Categories ERROR: {e}')
else:
    print('\n⚠️  BudgetCategory model not available')

if BudgetSubcategory:
    try:
        count = BudgetSubcategory.objects.count()
        print(f'\n✓ Budget Subcategories: {count}')
    except Exception as e:
        print(f'\n✗ Subcategories ERROR: {e}')
else:
    print('\n⚠️  BudgetSubcategory model not available')

if Transaction:
    try:
        count = Transaction.objects.count()
        print(f'\n✓ Transactions: {count}')
        
        if count > 0:
            # Total amount
            total_amount = Transaction.objects.aggregate(Sum('amount'))['amount__sum'] or 0
            print(f'  - Total Value: ${total_amount:,.2f}')
            
            # Categorization rate
            categorized = Transaction.objects.exclude(category__isnull=True).count()
            cat_rate = (categorized / count * 100) if count > 0 else 0
            print(f'  - Categorized: {categorized} ({cat_rate:.1f}%)')
            
            # Date range
            from django.db.models import Min, Max
            date_range = Transaction.objects.aggregate(
                earliest=Min('transaction_date'),
                latest=Max('transaction_date')
            )
            print(f'  - Date Range: {date_range["earliest"]} to {date_range["latest"]}')
    except Exception as e:
        print(f'\n✗ Transactions ERROR: {e}')
else:
    print('\n⚠️  Transaction model not available')

if BudgetRequest:
    try:
        count = BudgetRequest.objects.count()
        print(f'\n✓ Budget Requests: {count}')
    except Exception as e:
        print(f'\n✗ Budget Requests ERROR: {e}')

# Recommendations
print('\n' + '='*70)
print(' RECOMMENDATIONS')
print('='*70)

if BudgetCategory and BudgetCategory.objects.count() == 0:
    print('\n🎯 PHASE 1: CREATE BUDGET CATEGORIES')
    print('   Status: No categories found')
    print('   Action: Create 14 standard budget categories')
    print('   Time: 1-2 hours')
    print('\n   Next Step:')
    print('   1. Create categories via Django admin')
    print('   2. Or run: python manage.py setup_budget_categories')

elif Transaction and Transaction.objects.count() > 100:
    print('\n🎯 PHASE 2: ANALYZE TRANSACTION DATA')
    print(f'   Status: {Transaction.objects.count()} transactions found')
    print('   Action: Analyze historical spending patterns')
    print('   Time: 30 minutes')
    print('\n   Next Step:')
    print('   1. Run transaction analysis')
    print('   2. Auto-categorize transactions')
    print('   3. Generate AI budget from historical data')

elif Budget and Budget.objects.count() == 0:
    print('\n🎯 PHASE 3: CREATE BUDGET')
    print('   Status: No budgets found')
    print('   Action: Create FY 2025 budget')
    print('   Time: 2-4 hours (manual) or 30 min (AI-generated)')
    print('\n   Next Step:')
    print('   1. Access budget dashboard')
    print('   2. Create budget items by category')

else:
    print('\n✅ SYSTEM APPEARS CONFIGURED')
    print('   Review existing data and dashboards')

print('\n' + '='*70)
print(' END OF REPORT')
print('='*70 + '\n')

