#!/usr/bin/env python
"""
Test script for IntegratedBudgetService
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append('/Users/coda/PROJECTS/CODA/DEVELOPMENT/DEV')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda_project.settings')
django.setup()

from finance.services.integrated_budget_service import IntegratedBudgetService
from management.services.employee_compliance_service import EmployeeComplianceService

def test_integrated_budget_service():
    print("=== TESTING INTEGRATED BUDGET SERVICE ===\n")
    
    try:
        # Initialize service
        service = IntegratedBudgetService()
        compliance_service = EmployeeComplianceService()
        
        # Get current target month/year
        target_month, target_year = compliance_service.get_current_target_month_year()
        print(f"Testing with period: {target_month}/{target_year}")
        
        # Test 1: Monthly Budget Summary
        print("\n1. Testing Monthly Budget Summary...")
        budget_summary = service.get_monthly_budget_summary(target_month, target_year)
        
        if 'error' in budget_summary:
            print(f"❌ Error: {budget_summary['error']}")
        else:
            print(f"✅ Monthly Budget Summary Generated")
            print(f"   Period: {budget_summary['period']}")
            print(f"   Total Salaries: ${budget_summary['totals']['total_salaries']}")
            print(f"   Total Budget Items: ${budget_summary['totals']['total_budget_items']}")
            print(f"   Grand Total: ${budget_summary['totals']['grand_total']}")
            print(f"   Compliant Employees: {budget_summary['salary_data']['compliant_count']}")
            print(f"   Non-Compliant Employees: {budget_summary['salary_data']['non_compliant_count']}")
        
        # Test 2: Salary Dashboard Data
        print("\n2. Testing Salary Dashboard Data...")
        salary_data = service.get_salary_dashboard_data(target_month, target_year)
        
        if 'error' in salary_data:
            print(f"❌ Error: {salary_data['error']}")
        else:
            print(f"✅ Salary Dashboard Data Generated")
            print(f"   Total Salary Amount: ${salary_data['salary_data']['total_amount']}")
            print(f"   Compliant Count: {salary_data['salary_data']['compliant_count']}")
            print(f"   Non-Compliant Count: {salary_data['salary_data']['non_compliant_count']}")
        
        # Test 3: Compliance Status Update
        print("\n3. Testing Compliance Status Update...")
        compliance_update = service.update_compliance_status(target_month, target_year)
        
        if 'error' in compliance_update:
            print(f"❌ Error: {compliance_update['error']}")
        else:
            print(f"✅ Compliance Status Updated")
            print(f"   Updated At: {compliance_update['updated_at']}")
            print(f"   Total Employees: {compliance_update['compliance_summary']['total_employees']}")
            print(f"   Compliance Rate: {compliance_update['compliance_summary']['compliance_rate']:.2f}%")
        
        print("\n=== ALL TESTS COMPLETED ===")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_integrated_budget_service()
    sys.exit(0 if success else 1)
