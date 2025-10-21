#!/usr/bin/env python
"""
Production Database Discovery Script
Run this to check the state of budget-related tables in production

Usage:
    heroku run "cd coda && python ../check_production_state.py" --app codatrainingapp
    
Or copy this script to the server and run:
    cd /app/coda && python check_production_state.py
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda_project.settings')
django.setup()

from finance.models import *
from main.models import *
from django.db.models import Count, Sum, Avg, Min, Max
from datetime import datetime, timedelta


def print_section(title):
    """Print a section header"""
    print(f"\n{'='*80}")
    print(f" {title}")
    print('='*80)


def check_basic_counts():
    """Check basic table counts"""
    print_section("BASIC TABLE COUNTS")
    
    tables = [
        ('Companies', Company),
        ('Departments', Department),
        ('Budget Categories', BudgetCategory),
        ('Budget Subcategories', BudgetSubcategory),
        ('Budget Items', Budget),
        ('Budget Requests', BudgetRequest),
        ('Transactions', Transaction),
        ('Budget Estimate Projections', BudgetEstimateProjection),
    ]
    
    for name, model in tables:
        try:
            count = model.objects.count()
            print(f"✓ {name:30s}: {count:6d} records")
        except Exception as e:
            print(f"✗ {name:30s}: ERROR - {str(e)[:50]}")


def check_budget_data():
    """Check budget data details"""
    print_section("BUDGET DATA ANALYSIS")
    
    try:
        total_budgets = Budget.objects.count()
        active_budgets = Budget.objects.filter(is_active=True).count()
        
        print(f"\nTotal Budget Items: {total_budgets}")
        print(f"Active Budget Items: {active_budgets}")
        
        if total_budgets > 0:
            # Budget by department
            print(f"\n📊 Budget by Department:")
            dept_budgets = Budget.objects.values('department__name').annotate(
                count=Count('id'),
                total=Sum('unit_price')
            ).order_by('-total')[:10]
            
            for dept in dept_budgets:
                dept_name = dept['department__name'] or 'N/A'
                print(f"  {dept_name:30s}: {dept['count']:4d} items, ${dept['total']:,.2f}")
            
            # Budget by category
            print(f"\n📊 Budget by Category:")
            cat_budgets = Budget.objects.values('category__name').annotate(
                count=Count('id'),
                total=Sum('unit_price')
            ).order_by('-total')[:10]
            
            for cat in cat_budgets:
                cat_name = cat['category__name'] or 'N/A'
                print(f"  {cat_name:30s}: {cat['count']:4d} items, ${cat['total']:,.2f}")
            
            # Date range
            date_range = Budget.objects.aggregate(
                earliest=Min('date_from'),
                latest=Max('date_to')
            )
            print(f"\n📅 Budget Date Range:")
            print(f"  From: {date_range['earliest']}")
            print(f"  To: {date_range['latest']}")
        else:
            print("\n⚠️  No budget data found in production!")
            
    except Exception as e:
        print(f"\n✗ Error analyzing budget data: {e}")


def check_transaction_data():
    """Check transaction data details"""
    print_section("TRANSACTION DATA ANALYSIS")
    
    try:
        total_transactions = Transaction.objects.count()
        
        print(f"\nTotal Transactions: {total_transactions}")
        
        if total_transactions > 0:
            # Categorization rate
            categorized = Transaction.objects.exclude(category__isnull=True).count()
            cat_rate = (categorized / total_transactions * 100) if total_transactions > 0 else 0
            print(f"Categorized: {categorized} ({cat_rate:.1f}%)")
            
            # Total amount
            total_amount = Transaction.objects.aggregate(total=Sum('amount'))['total'] or 0
            print(f"Total Transaction Value: ${total_amount:,.2f}")
            
            # Date range
            date_range = Transaction.objects.aggregate(
                earliest=Min('transaction_date'),
                latest=Max('transaction_date')
            )
            print(f"\n📅 Transaction Date Range:")
            print(f"  From: {date_range['earliest']}")
            print(f"  To: {date_range['latest']}")
            
            # By category
            print(f"\n💰 Top 10 Categories by Spend:")
            by_category = Transaction.objects.values('category__name').annotate(
                count=Count('id'),
                total=Sum('amount')
            ).order_by('-total')[:10]
            
            for cat in by_category:
                cat_name = cat['category__name'] or 'Uncategorized'
                print(f"  {cat_name:30s}: ${cat['total']:,.2f} ({cat['count']:4d} txns)")
            
            # By department
            print(f"\n🏢 Top 10 Departments by Spend:")
            by_dept = Transaction.objects.values('department__name').annotate(
                count=Count('id'),
                total=Sum('amount')
            ).order_by('-total')[:10]
            
            for dept in by_dept:
                dept_name = dept['department__name'] or 'No Department'
                print(f"  {dept_name:30s}: ${dept['total']:,.2f} ({dept['count']:4d} txns)")
            
            # Top vendors
            print(f"\n🏪 Top 10 Vendors by Spend:")
            by_vendor = Transaction.objects.values('receiver_name').annotate(
                count=Count('id'),
                total=Sum('amount')
            ).order_by('-total')[:10]
            
            for vendor in by_vendor:
                vendor_name = vendor['receiver_name'] or 'Unknown'
                print(f"  {vendor_name:30s}: ${vendor['total']:,.2f} ({vendor['count']:4d} txns)")
                
        else:
            print("\n⚠️  No transaction data found in production!")
            
    except Exception as e:
        print(f"\n✗ Error analyzing transaction data: {e}")


def check_categories():
    """Check category setup"""
    print_section("CATEGORY SETUP")
    
    try:
        categories = BudgetCategory.objects.all().order_by('name')
        
        print(f"\nTotal Categories: {categories.count()}")
        
        if categories.exists():
            print(f"\n📋 Categories:")
            for cat in categories:
                subcat_count = cat.budgetsubcategory_set.count() if hasattr(cat, 'budgetsubcategory_set') else 0
                print(f"  {cat.name:35s} ({subcat_count} subcategories)")
        else:
            print("\n⚠️  No categories found - need to create!")
            print("\nRecommended action: Load category fixture or run setup script")
            
    except Exception as e:
        print(f"\n✗ Error checking categories: {e}")


def check_recent_activity():
    """Check recent budget activity"""
    print_section("RECENT ACTIVITY (Last 30 Days)")
    
    try:
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        # Recent budgets
        recent_budgets = Budget.objects.filter(created_at__gte=thirty_days_ago).count()
        print(f"\nNew Budget Items: {recent_budgets}")
        
        # Recent transactions
        recent_transactions = Transaction.objects.filter(
            transaction_date__gte=thirty_days_ago.date()
        ).count()
        print(f"Recent Transactions: {recent_transactions}")
        
        # Recent requests
        if hasattr(BudgetRequest, 'objects'):
            recent_requests = BudgetRequest.objects.filter(created_at__gte=thirty_days_ago).count()
            print(f"Budget Requests: {recent_requests}")
            
    except Exception as e:
        print(f"\n✗ Error checking recent activity: {e}")


def recommend_next_steps():
    """Recommend next steps based on current state"""
    print_section("RECOMMENDED NEXT STEPS")
    
    try:
        budget_count = Budget.objects.count()
        transaction_count = Transaction.objects.count()
        category_count = BudgetCategory.objects.count()
        
        print("\nBased on current state:\n")
        
        if category_count == 0:
            print("🎯 START WITH: Phase 1.1 - Create Budget Categories")
            print("   Command: python manage.py setup_budget_categories")
            print("   Why: Categories are the foundation for budgets\n")
            
        elif transaction_count > 100:
            print("🎯 START WITH: Phase 2 - Transaction Data Analysis")
            print("   Command: python manage.py analyze_transaction_data")
            print("   Why: You have historical data to learn from\n")
            
            if transaction_count > 0:
                categorized = Transaction.objects.exclude(category__isnull=True).count()
                cat_rate = (categorized / transaction_count * 100)
                
                if cat_rate < 90:
                    print("⚠️  THEN: Auto-categorize transactions")
                    print("   Command: python manage.py categorize_transactions --auto-assign")
                    print(f"   Why: Only {cat_rate:.1f}% are categorized\n")
                    
        elif budget_count == 0 and transaction_count < 100:
            print("🎯 START WITH: Phase 3.2 - Create FY 2025 Budget Manually")
            print("   Access: /finance/budget-dashboard/coda/")
            print("   Why: Limited historical data, manual budgeting recommended\n")
            
        if budget_count > 0:
            print("✅ NEXT: Phase 4 - Set Up Approval Workflows")
            print("   Configure approval tiers based on budget amounts\n")
            
    except Exception as e:
        print(f"\n✗ Error generating recommendations: {e}")


def main():
    """Main discovery function"""
    print("\n" + "="*80)
    print(" PRODUCTION DATABASE DISCOVERY REPORT")
    print(f" Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(" Environment: codatrainingapp (PRODUCTION)")
    print("="*80)
    
    check_basic_counts()
    check_categories()
    check_budget_data()
    check_transaction_data()
    check_recent_activity()
    recommend_next_steps()
    
    print("\n" + "="*80)
    print(" END OF DISCOVERY REPORT")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()

