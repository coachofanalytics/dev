#!/usr/bin/env python3
"""
Pull Production Data to Local SQLite

Alternative to sync script that doesn't require Heroku CLI.
Uses Django ORM to connect to production PostgreSQL and export to local SQLite.

Usage:
    python scripts/pull_prod_data_to_local.py
    python scripts/pull_prod_data_to_local.py --database-url "postgres://..."
"""

import os
import sys
import django
import argparse
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'coda'))

# Parse arguments
parser = argparse.ArgumentParser(description='Pull production data to local SQLite')
parser.add_argument('--database-url', help='Production database URL (or set HEROKU_POSTGRESQL_MAROON_URL env var)')
args = parser.parse_args()

# Get production database URL
prod_db_url = args.database_url or os.environ.get('DATABASE_URL') or os.environ.get('HEROKU_POSTGRESQL_MAROON_URL')

if not prod_db_url:
    print("Error: Production database URL not provided")
    print("\nOptions:")
    print("  1. Pass as argument: --database-url 'postgres://...'")
    print("  2. Set environment variable: export DATABASE_URL='postgres://...'")
    print("  3. Get from Heroku:")
    print("     heroku config:get DATABASE_URL --app codatrainingapp")
    sys.exit(1)

print("Pulling Production Data to Local SQLite")
print("=" * 50)

# Configure Django to use production database temporarily
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda_project.coda_settings.local_settings')
django.setup()

# Now we can import models
from finance.models import BudgetCategory, BudgetSubcategory
from django.db import connections
import dj_database_url

# Parse database URL
prod_db_config = dj_database_url.parse(prod_db_url)

# Create temporary connection to production database
connections.databases['production'] = {
    'ENGINE': 'django.db.backends.postgresql',
    'NAME': prod_db_config['NAME'],
    'USER': prod_db_config['USER'],
    'PASSWORD': prod_db_config['PASSWORD'],
    'HOST': prod_db_config['HOST'],
    'PORT': prod_db_config['PORT'],
    'OPTIONS': prod_db_config.get('OPTIONS', {}),
}

print(f"Source: {prod_db_config['HOST']}")
print(f"Destination: Local SQLite (coda/db.sqlite3)")

try:
    # Test production connection
    print("\nConnecting to production database...")
    from django.db import connections
    conn = connections['production']
    conn.ensure_connection()
    print("Connected to production")
    
    # Fetch categories from production
    print("\nFetching Budget Categories from production...")
    
    # Use raw SQL to fetch from production
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT id, name, approval_tier, auto_approve_enabled, 
                   typical_monthly_amount, variance_threshold, 
                   is_recurring, last_pattern_analysis, 
                   created_at, updated_at
            FROM finance_budgetcategory
            ORDER BY name
        """)
        prod_categories = cursor.fetchall()
    
    print(f"Fetched {len(prod_categories)} categories")
    
    # Save to local database
    print("\nSaving to local SQLite...")
    
    from django.db import connection as local_conn
    
    # Clear existing categories (optional)
    response = input("Clear existing local categories? (y/N): ")
    if response.lower() == 'y':
        BudgetCategory.objects.all().delete()
        print("   Cleared existing categories")
    
    # Insert categories
    count = 0
    for cat_data in prod_categories:
        cat, created = BudgetCategory.objects.update_or_create(
            id=cat_data[0],
            defaults={
                'name': cat_data[1],
                'approval_tier': cat_data[2],
                'auto_approve_enabled': cat_data[3],
                'typical_monthly_amount': cat_data[4],
                'variance_threshold': cat_data[5],
                'is_recurring': cat_data[6],
                'last_pattern_analysis': cat_data[7],
                'created_at': cat_data[8],
                'updated_at': cat_data[9],
            }
        )
        count += 1
        if created:
            print(f"   + {cat.name} (Tier {cat.approval_tier})")
        else:
            print(f"   ✓ {cat.name} (Tier {cat.approval_tier})")
    
    print(f"\nSaved {count} categories to local database")
    
    # Show summary
    print("\nCategory Summary:")
    total = BudgetCategory.objects.count()
    tier_a = BudgetCategory.objects.filter(approval_tier='A').count()
    tier_b = BudgetCategory.objects.filter(approval_tier='B').count()
    tier_c = BudgetCategory.objects.filter(approval_tier='C').count()
    auto_enabled = BudgetCategory.objects.filter(auto_approve_enabled=True).count()
    with_data = BudgetCategory.objects.exclude(typical_monthly_amount__isnull=True).count()
    
    print(f"   Total: {total}")
    print(f"   - Tier A: {tier_a}")
    print(f"   - Tier B: {tier_b}")
    print(f"   - Tier C: {tier_c}")
    print(f"   Auto-approval enabled: {auto_enabled}")
    print(f"   With transaction data: {with_data}")
    
    # Show Tier A categories
    print("\nTier A Categories (Auto-Approve):")
    for cat in BudgetCategory.objects.filter(approval_tier='A'):
        typical = f"${cat.typical_monthly_amount:,.2f}" if cat.typical_monthly_amount else "N/A"
        print(f"   - {cat.name}: {typical}/mo (variance: {cat.variance_threshold}%)")
    
    # Show top Tier B categories
    print("\nTop Tier B Categories (Priority-Based):")
    for cat in BudgetCategory.objects.filter(approval_tier='B').order_by('-typical_monthly_amount')[:5]:
        typical = f"${cat.typical_monthly_amount:,.2f}" if cat.typical_monthly_amount else "N/A"
        print(f"   - {cat.name}: {typical}/mo")
    
    print("\nSync Complete!")
    print("\nNext Steps:")
    print("   1. Examine data in Django shell:")
    print("      python manage.py shell --settings=coda_project.coda_settings.local_settings")
    print("")
    print("   2. Run tier management UI locally:")
    print("      python manage.py runserver --settings=coda_project.coda_settings.local_settings")
    print("      Visit: http://localhost:8000/finance/tier-management/coda/")
    print("")
    print("   3. Test with real data:")
    print("      python manage.py test finance.tests.test_budget_tier_system --settings=coda_project.coda_settings.local_settings")

except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

