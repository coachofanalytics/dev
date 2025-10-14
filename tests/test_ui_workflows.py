#!/usr/bin/env python
"""
UI Workflow Testing Script
Tests the application from a user perspective with different user types
"""

import os
import sys
import django
import requests
from datetime import date, timedelta
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda_project.settings')
django.setup()

from accounts.models import CustomerUser, UserProfile
from django.contrib.auth.hashers import make_password
from finance.models import LoanApplication, LoanProduct

class UIWorkflowTester:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def create_test_users(self):
        """Create test users for different roles"""
        print("=== CREATING TEST USERS ===")
        
        # 1. KCC Loan User
        try:
            kcc_user = CustomerUser.objects.get(email='kcc_loan@example.com')
            print(f"✅ KCC User already exists: {kcc_user.email}")
        except CustomerUser.DoesNotExist:
            kcc_user = CustomerUser.objects.create(
                username='kcc_loan_user',
                email='kcc_loan@example.com',
                password=make_password('kccpass123'),
                first_name='KCC',
                last_name='LoanUser',
                is_active=True
            )
            
            UserProfile.objects.create(
                user=kcc_user,
                country='KE',
                position='KCC Member',
                company='Karen Country Club',
                is_karen_country_club_member=True,
                kcc_membership_number='KCC123456',
                kcc_membership_date=date.today() - timedelta(days=365),
                kcc_membership_expiry=date.today() + timedelta(days=365),
                monthly_income=Decimal('50000.00'),
                credit_score=750
            )
            print(f"✅ Created KCC User: {kcc_user.email}")
        
        # 2. Investor User
        try:
            investor_user = CustomerUser.objects.get(email='investor@example.com')
            print(f"✅ Investor User already exists: {investor_user.email}")
        except CustomerUser.DoesNotExist:
            investor_user = CustomerUser.objects.create(
                username='investor_user',
                email='investor@example.com',
                password=make_password('investpass123'),
                first_name='Investor',
                last_name='User',
                is_active=True
            )
            
            UserProfile.objects.create(
                user=investor_user,
                country='US',
                position='Investment Manager',
                company='Investment Corp',
                monthly_income=Decimal('100000.00'),
                credit_score=800
            )
            print(f"✅ Created Investor User: {investor_user.email}")
        
        # 3. Staff User
        try:
            staff_user = CustomerUser.objects.get(email='staff@example.com')
            print(f"✅ Staff User already exists: {staff_user.email}")
        except CustomerUser.DoesNotExist:
            staff_user = CustomerUser.objects.create(
                username='staff_user',
                email='staff@example.com',
                password=make_password('staffpass123'),
                first_name='Staff',
                last_name='User',
                is_active=True,
                is_staff=True,
                is_superuser=True
            )
            
            UserProfile.objects.create(
                user=staff_user,
                country='KE',
                position='Finance Manager',
                company='CODA Analytics',
                monthly_income=Decimal('80000.00'),
                credit_score=780
            )
            print(f"✅ Created Staff User: {staff_user.email}")
    
    def test_login_workflow(self, username, password, user_type):
        """Test login workflow for a user"""
        print(f"\n=== TESTING LOGIN WORKFLOW FOR {user_type.upper()} ===")
        
        # Get login page
        login_url = f"{self.base_url}/social_accounts/login/"
        response = self.session.get(login_url)
        
        if response.status_code != 200:
            print(f"❌ Failed to get login page: {response.status_code}")
            return False
        
        # Extract CSRF token
        csrf_token = None
        for line in response.text.split('\n'):
            if 'csrfmiddlewaretoken' in line:
                csrf_token = line.split('value="')[1].split('"')[0]
                break
        
        if not csrf_token:
            print("❌ Could not find CSRF token")
            return False
        
        # Attempt login
        login_data = {
            'username': username,
            'password': password,
            'csrfmiddlewaretoken': csrf_token
        }
        
        response = self.session.post(login_url, data=login_data, allow_redirects=True)
        
        if response.status_code == 200 and 'login' not in response.url:
            print(f"✅ Login successful for {user_type}")
            return True
        else:
            print(f"❌ Login failed for {user_type}: {response.status_code}")
            return False
    
    def test_loan_workflow(self, user_type):
        """Test loan workflow for KCC user"""
        print(f"\n=== TESTING LOAN WORKFLOW FOR {user_type.upper()} ===")
        
        # Test loan home page
        loan_url = f"{self.base_url}/finance/loan-home/"
        response = self.session.get(loan_url)
        
        if response.status_code == 200:
            print("✅ Loan home page accessible")
            
            # Check if loan products are displayed
            if 'loan' in response.text.lower() and 'product' in response.text.lower():
                print("✅ Loan products visible on page")
            else:
                print("⚠️  Loan products may not be visible")
            
            # Test loan application form
            apply_url = f"{self.base_url}/finance/apply-for-loan/1/"
            response = self.session.get(apply_url)
            
            if response.status_code == 200:
                print("✅ Loan application form accessible")
            else:
                print(f"⚠️  Loan application form: {response.status_code}")
                
        elif response.status_code == 302:
            print("⚠️  Loan home page redirects to login (expected if not logged in)")
        else:
            print(f"❌ Loan home page error: {response.status_code}")
    
    def test_investment_workflow(self, user_type):
        """Test investment workflow"""
        print(f"\n=== TESTING INVESTMENT WORKFLOW FOR {user_type.upper()} ===")
        
        # Test investment page
        investment_url = f"{self.base_url}/investing/"
        response = self.session.get(investment_url)
        
        if response.status_code == 200:
            print("✅ Investment page accessible")
            
            # Check for investment content
            if 'investment' in response.text.lower() or 'invest' in response.text.lower():
                print("✅ Investment content visible")
            else:
                print("⚠️  Investment content may not be visible")
        else:
            print(f"❌ Investment page error: {response.status_code}")
    
    def test_budget_workflow(self, user_type):
        """Test budget workflow"""
        print(f"\n=== TESTING BUDGET WORKFLOW FOR {user_type.upper()} ===")
        
        # Test budget dashboard
        budget_url = f"{self.base_url}/finance/enhanced-budget-dashboard/coda/"
        response = self.session.get(budget_url)
        
        if response.status_code == 200:
            print("✅ Budget dashboard accessible")
        elif response.status_code == 302:
            print("⚠️  Budget dashboard redirects to login (expected if not logged in)")
        else:
            print(f"❌ Budget dashboard error: {response.status_code}")
        
        # Test automated budget estimation
        auto_budget_url = f"{self.base_url}/finance/automated-budget-estimation/"
        response = self.session.get(auto_budget_url)
        
        if response.status_code == 200:
            print("✅ Automated budget estimation accessible")
        elif response.status_code == 302:
            print("⚠️  Automated budget redirects to login (expected if not logged in)")
        else:
            print(f"❌ Automated budget error: {response.status_code}")
    
    def test_staff_workflow(self, user_type):
        """Test staff-specific workflow"""
        print(f"\n=== TESTING STAFF WORKFLOW FOR {user_type.upper()} ===")
        
        # Test admin loan applications
        admin_url = f"{self.base_url}/finance/admin/loan-applications/"
        response = self.session.get(admin_url)
        
        if response.status_code == 200:
            print("✅ Admin loan applications accessible")
        elif response.status_code == 302:
            print("⚠️  Admin page redirects to login (expected if not logged in)")
        else:
            print(f"❌ Admin page error: {response.status_code}")
        
        # Test automation dashboard
        automation_url = f"{self.base_url}/finance/automation/"
        response = self.session.get(automation_url)
        
        if response.status_code == 200:
            print("✅ Automation dashboard accessible")
        elif response.status_code == 302:
            print("⚠️  Automation dashboard redirects to login (expected if not logged in)")
        else:
            print(f"❌ Automation dashboard error: {response.status_code}")
    
    def run_comprehensive_test(self):
        """Run comprehensive UI workflow tests"""
        print("🚀 STARTING COMPREHENSIVE UI WORKFLOW TESTING")
        print("=" * 60)
        
        # Create test users
        self.create_test_users()
        
        # Test workflows for each user type
        test_cases = [
            {
                'username': 'kcc_loan_user',
                'password': 'kccpass123',
                'user_type': 'KCC Loan User',
                'workflows': ['login', 'loan', 'investment', 'budget']
            },
            {
                'username': 'investor_user', 
                'password': 'investpass123',
                'user_type': 'Investor User',
                'workflows': ['login', 'investment', 'budget']
            },
            {
                'username': 'staff_user',
                'password': 'staffpass123', 
                'user_type': 'Staff User',
                'workflows': ['login', 'loan', 'investment', 'budget', 'staff']
            }
        ]
        
        for test_case in test_cases:
            print(f"\n{'='*20} {test_case['user_type'].upper()} {'='*20}")
            
            # Test login
            if 'login' in test_case['workflows']:
                login_success = self.test_login_workflow(
                    test_case['username'], 
                    test_case['password'], 
                    test_case['user_type']
                )
                
                if login_success:
                    # Test other workflows only if login successful
                    if 'loan' in test_case['workflows']:
                        self.test_loan_workflow(test_case['user_type'])
                    
                    if 'investment' in test_case['workflows']:
                        self.test_investment_workflow(test_case['user_type'])
                    
                    if 'budget' in test_case['workflows']:
                        self.test_budget_workflow(test_case['user_type'])
                    
                    if 'staff' in test_case['workflows']:
                        self.test_staff_workflow(test_case['user_type'])
                else:
                    print("⚠️  Skipping other workflows due to login failure")
            
            # Clear session for next user
            self.session.cookies.clear()
        
        print("\n" + "="*60)
        print("🎉 COMPREHENSIVE UI WORKFLOW TESTING COMPLETED")
        print("="*60)

if __name__ == "__main__":
    tester = UIWorkflowTester()
    tester.run_comprehensive_test()
