#!/bin/bash
# Production Discovery - Inline Version

echo ""
echo "🔍 Discovering Production Database State..."
echo ""

/usr/local/bin/heroku run 'cd coda && python -c "
import os, sys, django
os.environ.setdefault(\"DJANGO_SETTINGS_MODULE\", \"coda_project.settings\")
django.setup()

from django.db.models import Count, Sum, Min, Max, F

print(\"\\n\" + \"=\"*70)
print(\" PRODUCTION DATABASE DISCOVERY\")
print(\"=\"*70)

# Import models with error handling
try:
    from main.models import Company
    from finance.models.budget import Budget, BudgetCategory, BudgetSubcategory
    from finance.models.core import Transaction
    
    print(\"\\n✓ All models imported successfully\\n\")
    
    # Companies
    comp_count = Company.objects.count()
    print(f\"Companies: {comp_count}\")
    for c in Company.objects.all():
        print(f\"  - {c.name} (slug: {c.slug})\")
    
    # Categories
    cat_count = BudgetCategory.objects.count()
    subcat_count = BudgetSubcategory.objects.count()
    print(f\"\\nBudget Categories: {cat_count}\")
    print(f\"Budget Subcategories: {subcat_count}\")
    
    if cat_count > 0:
        print(\"\\nCategories:\")
        for cat in BudgetCategory.objects.all():
            print(f\"  - {cat.name}\")
    
    # Budgets
    budget_count = Budget.objects.count()
    active_count = Budget.objects.filter(is_active=True).count()
    print(f\"\\nBudget Items: {budget_count}\")
    print(f\"  - Active: {active_count}\")
    
    # TRANSACTIONS - KEY DATA
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
        
        print(\"\\n💰 Top 10 Spending Categories:\")
        top_cats = Transaction.objects.values(\"category__name\").annotate(
            total=Sum(\"amount\"),
            count=Count(\"id\")
        ).order_by(\"-total\")[:10]
        
        for cat in top_cats:
            name = cat[\"category__name\"] or \"Uncategorized\"
            print(f\"  {name:30s}: \${cat[\"total\"]:>12,.2f} ({cat[\"count\"]:>4d} txns)\")
    
    # Recommendations
    print(\"\\n\" + \"=\"*70)
    print(\" NEXT STEPS\")
    print(\"=\"*70)
    
    if cat_count == 0:
        print(\"\\n🎯 PHASE 1: Create Budget Categories (30-60 min)\")
    elif trans_count > 0 and cat_rate < 90:
        print(f\"\\n🎯 PHASE 2A: Auto-Categorize Transactions (15 min)\")
        print(f\"   Current: {cat_rate:.1f}% categorized\")
        print(f\"   Target: 95%+\")
    elif trans_count > 100 and cat_rate >= 90:
        print(f\"\\n🎯 PHASE 2B: Generate AI Budget from Transaction Data (30 min)\")
        print(f\"   Data Ready: {trans_count} transactions, {cat_rate:.1f}% categorized\")
    elif budget_count == 0:
        print(\"\\n🎯 PHASE 3: Create Budget (Manual 2-4 hours or AI 30 min)\")
    else:
        print(\"\\n✅ System configured - Review and enhance\")
    
    print(\"\\n\" + \"=\"*70 + \"\\n\")
    
except Exception as e:
    print(f\"\\nERROR: {e}\")
    import traceback
    traceback.print_exc()
"' --app codatrainingapp

