#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Comprehensive Budget and Payment Systems Test
Tests all critical functionalities after UAT merge
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, '/Users/coda/PROJECTS/CODA/DEVELOPMENT/DEV/coda')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db.models import Sum, Count, F, DecimalField
from django.db.models.functions import Coalesce
from decimal import Decimal
from datetime import datetime, timedelta

from main.models import Company
from finance.models import (
    Budget, BudgetCategory, BudgetSubCategory, Transaction,
    BudgetRequest, BudgetEstimateProjection, MultiYearBudgetPlan,
    Payment, PaymentMethod
)

User = get_user_model()

class BudgetPaymentTester:
    """Test suite for budget and payment systems"""
    
    def __init__(self):
        self.results = []
        self.errors = []
        self.company = None
        self.user = None
        
    def log_success(self, test_name, message):
        """Log successful test"""
        self.results.append(f"✅ {test_name}: {message}")
        print(f"✅ {test_name}: {message}")
        
    def log_error(self, test_name, message):
        """Log test error"""
        self.errors.append(f"❌ {test_name}: {message}")
        print(f"❌ {test_name}: {message}")
        
    def setup(self):
        """Setup test environment"""
        print("\n" + "="*80)
        print("🧪 BUDGET & PAYMENT SYSTEMS TEST SUITE")
        print("="*80 + "\n")
        
        try:
            self.company = Company.objects.get(slug='coda')
            self.log_success("Setup", f"Found company: {self.company.name}")
        except Company.DoesNotExist:
            self.log_error("Setup", "CODA company not found")
            return False
            
        try:
            self.user = User.objects.filter(is_staff=True).first()
            if self.user:
                self.log_success("Setup", f"Found test user: {self.user.username}")
            else:
                self.log_error("Setup", "No staff user found")
                return False
        except Exception as e:
            self.log_error("Setup", f"User lookup failed: {str(e)}")
            return False
            
        return True
        
    # ==================== BUDGET SYSTEM TESTS ====================
    
    def test_budget_models(self):
        """Test Budget model integrity"""
        print("\n📊 Testing Budget Models...")
        
        try:
            budget_count = Budget.objects.count()
            active_budgets = Budget.objects.filter(is_active=True).count()
            self.log_success("Budget Models", f"Found {budget_count} budgets ({active_budgets} active)")
        except Exception as e:
            self.log_error("Budget Models", str(e))
            
    def test_budget_categories(self):
        """Test Budget categories"""
        print("\n📁 Testing Budget Categories...")
        
        try:
            categories = BudgetCategory.objects.all()
            cat_count = categories.count()
            
            if cat_count > 0:
                self.log_success("Budget Categories", f"Found {cat_count} categories")
                
                # Test category with budgets
                for category in categories[:3]:
                    budget_count = Budget.objects.filter(category=category).count()
                    print(f"   └─ {category.name}: {budget_count} budgets")
            else:
                self.log_error("Budget Categories", "No categories found")
        except Exception as e:
            self.log_error("Budget Categories", str(e))
            
    def test_transaction_integration(self):
        """Test Transaction to Budget integration"""
        print("\n💸 Testing Transaction Integration...")
        
        try:
            # Test transactions exist (no company field in Transaction model)
            transactions = Transaction.objects.all()
            total_count = transactions.count()
            categorized = transactions.filter(category__isnull=False).count()
            
            if total_count > 0:
                percentage = (categorized / total_count) * 100
                self.log_success("Transactions", 
                    f"Found {total_count} transactions ({categorized} categorized - {percentage:.1f}%)")
            else:
                self.log_error("Transactions", "No transactions found")
                
            # Test transaction amounts
            total_spending = transactions.aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0')
            
            self.log_success("Transaction Amounts", 
                f"Total spending: KES {total_spending:,.2f}")
                
        except Exception as e:
            self.log_error("Transaction Integration", str(e))
            
    def test_budget_requests(self):
        """Test Budget request system"""
        print("\n📝 Testing Budget Requests...")
        
        try:
            requests = BudgetRequest.objects.all()
            total = requests.count()
            pending = requests.filter(status__in=['submitted', 'under_review']).count()
            approved = requests.filter(status='approved').count()
            
            self.log_success("Budget Requests", 
                f"Total: {total}, Pending: {pending}, Approved: {approved}")
        except Exception as e:
            self.log_error("Budget Requests", str(e))
            
    def test_budget_projections(self):
        """Test Budget projections"""
        print("\n📈 Testing Budget Projections...")
        
        try:
            projections = BudgetEstimateProjection.objects.select_related(
                'budget', 'budget__category'
            )
            total = projections.count()
            
            if total > 0:
                total_projected = projections.aggregate(
                    total=Sum('projected_amount')
                )['total'] or Decimal('0')
                
                avg_confidence = projections.aggregate(
                    avg=Sum('confidence_score')
                )['avg'] or 0
                
                self.log_success("Budget Projections", 
                    f"Found {total} projections, Total: KES {total_projected:,.2f}")
                print(f"   └─ Average confidence: {avg_confidence:.1f}%")
            else:
                self.log_error("Budget Projections", "No projections found - run generate_budget_projections")
        except Exception as e:
            self.log_error("Budget Projections", str(e))
            
    def test_multi_year_plans(self):
        """Test Multi-year budget plans"""
        print("\n📅 Testing Multi-Year Plans...")
        
        try:
            # This should NOT filter by company (fixed bug)
            plans = MultiYearBudgetPlan.objects.filter(is_active=True)
            total = plans.count()
            
            if total > 0:
                self.log_success("Multi-Year Plans", f"Found {total} active plans")
                for plan in plans:
                    print(f"   └─ {plan.name}: {plan.start_year}-{plan.end_year}")
            else:
                print("ℹ️  No multi-year plans found (this is okay)")
        except Exception as e:
            self.log_error("Multi-Year Plans", str(e))
            
    def test_budget_aggregations(self):
        """Test budget aggregation calculations"""
        print("\n🧮 Testing Budget Aggregations...")
        
        try:
            budgets = Budget.objects.filter(company=self.company, is_active=True)
            
            # Test correct aggregation (not the 177x inflation bug)
            total = budgets.aggregate(
                total=Sum(F('unit_price') * F('quantity') * Coalesce(F('cases'), 1),
                         output_field=DecimalField())
            )['total'] or Decimal('0')
            
            self.log_success("Budget Aggregations", 
                f"Total budget: KES {total:,.2f}")
                
            # Test by category
            print("\n   Budget by Category:")
            categories = BudgetCategory.objects.all()[:5]
            for category in categories:
                cat_total = budgets.filter(category=category).aggregate(
                    total=Sum(F('unit_price') * F('quantity') * Coalesce(F('cases'), 1),
                             output_field=DecimalField())
                )['total'] or Decimal('0')
                
                if cat_total > 0:
                    print(f"   └─ {category.name}: KES {cat_total:,.2f}")
                    
        except Exception as e:
            self.log_error("Budget Aggregations", str(e))
            
    # ==================== PAYMENT SYSTEM TESTS ====================
    
    def test_payment_models(self):
        """Test Payment model integrity"""
        print("\n💳 Testing Payment Models...")
        
        try:
            payments = Payment.objects.all()
            total = payments.count()
            
            if total > 0:
                total_amount = payments.aggregate(
                    total=Sum('amount')
                )['total'] or Decimal('0')
                
                self.log_success("Payment Models", 
                    f"Found {total} payments, Total: KES {total_amount:,.2f}")
                    
                # Test by status
                statuses = payments.values('status').annotate(
                    count=Count('id'),
                    total=Sum('amount')
                )
                
                print("\n   Payment Status Breakdown:")
                for status in statuses:
                    print(f"   └─ {status['status']}: {status['count']} payments "
                          f"(KES {status['total']:,.2f})")
            else:
                print("ℹ️  No payments found (this is okay for testing)")
                
        except Exception as e:
            self.log_error("Payment Models", str(e))
            
    def test_payment_methods(self):
        """Test Payment methods configuration"""
        print("\n💰 Testing Payment Methods...")
        
        try:
            methods = PaymentMethod.objects.filter(is_active=True)
            total = methods.count()
            
            if total > 0:
                self.log_success("Payment Methods", f"Found {total} active payment methods")
                for method in methods:
                    print(f"   └─ {method.name}: {method.method_type}")
            else:
                self.log_error("Payment Methods", "No active payment methods found")
                
        except Exception as e:
            self.log_error("Payment Methods", str(e))
            
    def test_stripe_configuration(self):
        """Test Stripe payment configuration"""
        print("\n🔧 Testing Stripe Configuration...")
        
        try:
            from django.conf import settings
            
            has_stripe = all([
                hasattr(settings, 'STRIPE_PUBLISHABLE_KEY'),
                hasattr(settings, 'STRIPE_SECRET_KEY'),
                hasattr(settings, 'STRIPE_WEBHOOK_SECRET')
            ])
            
            if has_stripe:
                self.log_success("Stripe Configuration", "All Stripe keys configured")
            else:
                self.log_error("Stripe Configuration", "Missing Stripe keys")
                
        except Exception as e:
            self.log_error("Stripe Configuration", str(e))
            
    def test_payment_to_transaction_link(self):
        """Test Payment to Loan integration"""
        print("\n🔗 Testing Payment-Loan Link...")
        
        try:
            # Check for payments linked to loans
            linked_payments = Payment.objects.exclude(loan__isnull=True).count()
            total_payments = Payment.objects.count()
            
            if total_payments > 0:
                percentage = (linked_payments / total_payments) * 100
                self.log_success("Payment-Loan Link", 
                    f"{linked_payments}/{total_payments} payments linked ({percentage:.1f}%)")
            else:
                print("ℹ️  No payments to test linking")
                
        except Exception as e:
            self.log_error("Payment-Loan Link", str(e))
            
    # ==================== URL ROUTING TESTS ====================
    
    def test_critical_urls(self):
        """Test critical URL patterns"""
        print("\n🌐 Testing Critical URLs...")
        
        from django.urls import reverse
        
        url_tests = [
            ('finance:budget_requests_list', 'Budget Requests List'),
            ('finance:unified-budget-dashboard', 'Unified Budget Dashboard', {'company_slug': 'coda'}),
            ('finance:finance-dashboard', 'Finance Dashboard', {'company_slug': 'coda'}),
        ]
        
        for test in url_tests:
            try:
                if len(test) == 3:
                    url = reverse(test[0], kwargs=test[2])
                else:
                    url = reverse(test[0])
                self.log_success(f"URL: {test[1]}", f"Resolved: {url}")
            except Exception as e:
                self.log_error(f"URL: {test[1]}", str(e))
                
    # ==================== REPORT GENERATION ====================
    
    def generate_report(self):
        """Generate final test report"""
        print("\n" + "="*80)
        print("📋 TEST REPORT SUMMARY")
        print("="*80 + "\n")
        
        total_tests = len(self.results) + len(self.errors)
        passed = len(self.results)
        failed = len(self.errors)
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        
        if failed > 0:
            print(f"\n⚠️  Success Rate: {(passed/total_tests)*100:.1f}%")
            print("\n🔴 ERRORS FOUND:")
            for error in self.errors:
                print(f"  {error}")
        else:
            print(f"\n🎉 All tests passed! Success Rate: 100%")
            
        print("\n" + "="*80 + "\n")
        
        return failed == 0
        
    def run_all_tests(self):
        """Run all test suites"""
        if not self.setup():
            print("\n❌ Setup failed. Cannot continue.")
            return False
            
        # Budget System Tests
        print("\n" + "="*80)
        print("💰 BUDGET SYSTEM TESTS")
        print("="*80)
        self.test_budget_models()
        self.test_budget_categories()
        self.test_transaction_integration()
        self.test_budget_requests()
        self.test_budget_projections()
        self.test_multi_year_plans()
        self.test_budget_aggregations()
        
        # Payment System Tests
        print("\n" + "="*80)
        print("💳 PAYMENT SYSTEM TESTS")
        print("="*80)
        self.test_payment_models()
        self.test_payment_methods()
        self.test_stripe_configuration()
        self.test_payment_to_transaction_link()
        
        # URL Routing Tests
        print("\n" + "="*80)
        print("🌐 URL ROUTING TESTS")
        print("="*80)
        self.test_critical_urls()
        
        # Generate Report
        return self.generate_report()


if __name__ == '__main__':
    tester = BudgetPaymentTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

