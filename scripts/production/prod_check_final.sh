#!/bin/bash
# Production Discovery - FIXED VERSION

echo ""
echo "🔍 Checking Production Database..."
echo ""

/usr/local/bin/heroku run 'cd coda && python -c "
import os, sys, django
os.environ.setdefault(\"DJANGO_SETTINGS_MODULE\", \"coda_project.settings\")
django.setup()

from django.db.models import Count, Sum, Min, Max, F

print(\"\\n\" + \"=\"*70)
print(\" PRODUCTION DATABASE - BUDGET SYSTEM\")
print(\"=\"*70)

try:
    from main.models import Company
    from finance.models.budget import Budget, BudgetCategory, BudgetSubCategory
    from finance.models.core import Transaction
    
    print(\"\\n✓ All models imported\\n\")
    
    # Companies
    comp_count = Company.objects.count()
    print(f\"Companies: {comp_count}\")
    for c in Company.objects.all():
        print(f\"  - {c.name} (slug: {c.slug})\")
    
    # Categories
    cat_count = BudgetCategory.objects.count()
    subcat_count = BudgetSubCategory.objects.count()
    print(f\"\\nBudget Categories: {cat_count}\")
    print(f\"Budget Subcategories: {subcat_count}\")
    
    if cat_count > 0:
        print(\"\\nCategories:\")
        for cat in BudgetCategory.objects.all():
            subs = BudgetSubCategory.objects.filter(category=cat).count()
            print(f\"  - {cat.name} ({subs} subcats)\")
    
    # Budgets
    budget_count = Budget.objects.count()
    active_count = Budget.objects.filter(is_active=True).count()
    print(f\"\\nBudget Items: {budget_count}\")
    print(f\"  - Active: {active_count}\")
    
    # TRANSACTIONS - THE KEY DATA
    trans_count = Transaction.objects.count()
    print(f\"\\nTransactions: {trans_count}\")
    
    if trans_count > 0:
        total = Transaction.objects.aggregate(Sum(\"amount\"))[\"amount__sum\"] or 0
        cat_txn = Transaction.objects.exclude(category__isnull=True).count()
        cat_rate = (cat_txn / trans_count * 100) if trans_count > 0 else 0
        
        dates = Transaction.objects.aggregate(
            earliest=Min(\"transaction_date\"),
            latest=Max(\"transaction_date\")
        )
        
        print(f\"  - Total Value: \${total:,.2f}\")
        print(f\"  - Categorized: {cat_txn} ({cat_rate:.1f}%)\")
        print(f\"  - Uncategorized: {trans_count - cat_txn}\")
        print(f\"  - Date Range: {dates[\"earliest\"]} to {dates[\"latest\"]}\")
        
        print(\"\\n💰 Top 10 Categories by Spend:\")
        top_cats = Transaction.objects.values(\"category__name\").annotate(
            total=Sum(\"amount\"),
            count=Count(\"id\")
        ).order_by(\"-total\")[:10]
        
        for cat in top_cats:
            name = cat[\"category__name\"] or \"Uncategorized\"
            print(f\"  {name:30s}: \${cat[\"total\"]:>12,.2f} ({cat[\"count\"]:>4d} txns)\")
    
    # Recommendations
    print(\"\\n\" + \"=\"*70)
    print(\" 🎯 YOUR NEXT STEP\")
    print(\"=\"*70)
    
    if cat_count == 0:
        print(\"\\n→ PHASE 1: Create Budget Categories\")
        print(\"  Time: 30-60 minutes\")
        print(\"  Why: Need foundation for budgeting\")
    elif trans_count > 0 and cat_rate < 90:
        print(f\"\\n→ PHASE 2A: Auto-Categorize {trans_count - cat_txn} Transactions\")
        print(f\"  Current: {cat_rate:.1f}% categorized\")
        print(f\"  Target: 95%+\")
        print(f\"  Time: 15 minutes\")
    elif trans_count > 100 and cat_rate >= 90:
        print(f\"\\n→ PHASE 2B: Generate AI Budget\")
        print(f\"  Based on {trans_count} transactions worth \${total:,.2f}\")
        print(f\"  Data quality: {cat_rate:.1f}% categorized\")
        print(f\"  Time: 30 minutes\")
    elif budget_count == 0:
        print(\"\\n→ PHASE 3: Create Budget\")
        print(\"  Options: AI (30 min) or Manual (2-4 hours)\")
    else:
        print(\"\\n✅ System Ready - Configure workflows\")
    
    print(\"\\n\" + \"=\"*70 + \"\\n\")
    
except Exception as e:
    print(f\"\\nERROR: {e}\")
    import traceback
    traceback.print_exc()
"' --app codatrainingapp

echo ""
echo "✅ Done!"
echo ""

