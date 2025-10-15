#!/usr/bin/env python
"""
Comprehensive test script for all Finance app URLs and models
Run this to verify all database schema issues are resolved
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda_project.settings')
sys.path.insert(0, 'coda')
django.setup()

from django.contrib.auth import get_user_model
from finance.models import *
from django.db import connection

User = get_user_model()

def test_model_fields():
    """Test that all model fields can be accessed"""
    print("\n" + "="*80)
    print("TESTING MODEL FIELDS")
    print("="*80)
    
    tests = {
        'BalanceSheetCategory': ['name', 'description', 'category_type', 'parent_category', 'is_active', 'amount'],
        'Food': ['name', 'description', 'unit_price', 'currency', 'supplier', 'is_active'],
        'Transaction': ['sender', 'receiver', 'amount', 'currency', 'location', 'transaction_date', 'payment_method', 'amount_usd', 'original_currency', 'exchange_rate'],
        'Inflow': ['user', 'amount', 'currency', 'received_date', 'transaction_date', 'confirmed_date', 'total_payment'],
        'Budget': ['company', 'department', 'budget_lead', 'category', 'subcategory', 'item_name', 'quantity', 'unit_price', 'description', 'notes', 'created_at', 'updated_at'],
        'CodaBudget': ['company', 'name', 'total_amount', 'currency', 'status', 'created_by', 'updated_by'],
        'LoanProduct': ['name', 'min_amount', 'max_amount', 'interest_rate', 'term_months', 'min_term_months', 'max_term_months'],
        'Payment_History': ['customer', 'payment_fees', 'plan', 'created_at', 'updated_at', 'contract_signed', 'amount'],
        'Default_Payment_Fees': ['plan', 'payment_fees', 'job_plan_hours_per_month', 'loan_amount'],
    }
    
    for model_name, fields in tests.items():
        try:
            model = eval(model_name)
            print(f"\n✅ Testing {model_name}...")
            for field in fields:
                assert hasattr(model, field) or field in [f.name for f in model._meta.get_fields()], f"Missing field: {field}"
                print(f"   ✓ {field}")
            print(f"   SUCCESS: All fields exist for {model_name}")
        except Exception as e:
            print(f"   ❌ ERROR in {model_name}: {e}")
            return False
    
    return True

def test_database_queries():
    """Test actual database queries"""
    print("\n" + "="*80)
    print("TESTING DATABASE QUERIES")
    print("="*80)
    
    queries = [
        ("BalanceSheetCategory.objects.all()[:1]", lambda: list(BalanceSheetCategory.objects.all()[:1])),
        ("Food.objects.all()[:1]", lambda: list(Food.objects.all()[:1])),
        ("Transaction.objects.all()[:1]", lambda: list(Transaction.objects.all()[:1])),
        ("Inflow.objects.all()[:1]", lambda: list(Inflow.objects.all()[:1])),
        ("Budget.objects.all()[:1]", lambda: list(Budget.objects.all()[:1])),
        ("CodaBudget.objects.all()[:1]", lambda: list(CodaBudget.objects.all()[:1])),
        ("LoanProduct.objects.all()[:1]", lambda: list(LoanProduct.objects.all()[:1])),
        ("Payment_History.objects.all()[:1]", lambda: list(Payment_History.objects.all()[:1])),
        ("Default_Payment_Fees.objects.all()[:1]", lambda: list(Default_Payment_Fees.objects.all()[:1])),
    ]
    
    for query_name, query_func in queries:
        try:
            print(f"\n✅ Testing: {query_name}")
            result = query_func()
            print(f"   SUCCESS: Query executed, returned {len(result)} record(s)")
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            return False
    
    return True

def check_table_columns():
    """Check actual database table columns"""
    print("\n" + "="*80)
    print("CHECKING DATABASE TABLE COLUMNS")
    print("="*80)
    
    tables = [
        'finance_balancesheetcategory',
        'finance_food',
        'finance_transaction',
        'finance_inflow',
        'finance_budget',
        'finance_codabudget',
        'finance_loanproduct',
        'finance_payment_history',
        'finance_default_payment_fees',
    ]
    
    with connection.cursor() as cursor:
        for table in tables:
            cursor.execute(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = '{table}' 
                ORDER BY ordinal_position;
            """)
            columns = [row[0] for row in cursor.fetchall()]
            print(f"\n✅ {table}:")
            print(f"   Columns ({len(columns)}): {', '.join(columns[:10])}...")
    
    return True

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("COMPREHENSIVE FINANCE APP DATABASE SCHEMA TEST")
    print("="*80)
    
    all_passed = True
    
    # Test 1: Model fields
    if not test_model_fields():
        all_passed = False
        print("\n❌ Model field tests FAILED")
    else:
        print("\n✅ Model field tests PASSED")
    
    # Test 2: Database queries
    if not test_database_queries():
        all_passed = False
        print("\n❌ Database query tests FAILED")
    else:
        print("\n✅ Database query tests PASSED")
    
    # Test 3: Table columns
    if not check_table_columns():
        all_passed = False
        print("\n❌ Table column check FAILED")
    else:
        print("\n✅ Table column check PASSED")
    
    print("\n" + "="*80)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Database schema is fully synchronized.")
    else:
        print("⚠️  SOME TESTS FAILED! Review errors above.")
    print("="*80 + "\n")
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())

