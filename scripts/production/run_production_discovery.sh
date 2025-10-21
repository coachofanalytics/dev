#!/bin/bash
# Production Database Discovery Script
# Run this to check the state of your production database

echo "=================================================="
echo " PRODUCTION BUDGET SYSTEM DISCOVERY"
echo " Environment: codatrainingapp (PRODUCTION)"
echo "=================================================="
echo ""

# Check if logged into Heroku
if ! heroku auth:whoami >/dev/null 2>&1; then
    echo "⚠️  Not logged into Heroku. Logging in..."
    heroku login
fi

echo "🔍 Checking production database state..."
echo ""

# Run discovery script
heroku run "cd coda && python -c \"
import os, sys, django
sys.path.insert(0, '/app/coda')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda_project.settings')
django.setup()

from finance.models import *
from main.models import *
from django.db.models import Count, Sum

print('\\n=== PRODUCTION DATABASE STATE ===\\n')

# Basic counts
print(f'Companies: {Company.objects.count()}')
print(f'Departments: {Department.objects.count()}')

try:
    print(f'Budget Items: {Budget.objects.count()}')
    print(f'  - Active: {Budget.objects.filter(is_active=True).count()}')
except Exception as e:
    print(f'Budget Items: ERROR - {str(e)[:50]}')

try:
    cat_count = BudgetCategory.objects.count()
    subcat_count = BudgetSubcategory.objects.count()
    print(f'Categories: {cat_count}')
    print(f'Subcategories: {subcat_count}')
except Exception as e:
    print(f'Categories: ERROR - {str(e)[:50]}')

try:
    trans_count = Transaction.objects.count()
    print(f'Transactions: {trans_count}')
    if trans_count > 0:
        trans_total = Transaction.objects.aggregate(Sum('amount'))['amount__sum'] or 0
        categorized = Transaction.objects.exclude(category__isnull=True).count()
        cat_rate = (categorized / trans_count * 100) if trans_count > 0 else 0
        print(f'  - Total Value: \${trans_total:,.2f}')
        print(f'  - Categorized: {categorized} ({cat_rate:.1f}%)')
except Exception as e:
    print(f'Transactions: ERROR - {str(e)[:50]}')

print('\\n=== RECOMMENDATIONS ===\\n')

# Recommend next steps
budget_count = Budget.objects.count()
transaction_count = Transaction.objects.count()
category_count = BudgetCategory.objects.count()

if category_count == 0:
    print('🎯 START: Phase 1 - Create Budget Categories')
    print('   Run: heroku run \\\"cd coda && python manage.py setup_budget_categories\\\" --app codatrainingapp')
elif transaction_count > 100:
    print('🎯 START: Phase 2 - Analyze Transaction Data')
    print('   Run: heroku run \\\"cd coda && python manage.py analyze_transaction_data\\\" --app codatrainingapp')
elif budget_count == 0:
    print('🎯 START: Phase 3 - Create FY 2025 Budget')
    print('   Access: https://codatrainingapp.herokuapp.com/finance/budget-dashboard/coda/')
else:
    print('✅ System appears configured - review dashboard')
    print('   URL: https://codatrainingapp.herokuapp.com/finance/budget-dashboard/coda/')

print('\\n')
\"" --app codatrainingapp

echo ""
echo "=================================================="
echo " Discovery complete!"
echo " Review output above for next steps"
echo "=================================================="

