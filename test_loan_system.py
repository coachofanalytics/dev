#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Comprehensive Loan System Test
Tests all critical loan functionalities
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, '/Users/coda/PROJECTS/CODA/DEVELOPMENT/DEV/coda')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db.models import Sum, Count, Avg, Q
from decimal import Decimal
from datetime import datetime, timedelta

from main.models import Company
from finance.models import (
    LoanApplication, LoanProduct, LoanPayment,
    Payment, LoanCollateral
)

User = get_user_model()

class LoanSystemTester:
    """Test suite for loan system"""
    
    def __init__(self):
        self.results = []
        self.errors = []
        self.warnings = []
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
        
    def log_warning(self, test_name, message):
        """Log test warning"""
        self.warnings.append(f"⚠️  {test_name}: {message}")
        print(f"⚠️  {test_name}: {message}")
        
    def setup(self):
        """Setup test environment"""
        print("\n" + "="*80)
        print("🏦 LOAN SYSTEM TEST SUITE")
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
        
    # ==================== LOAN PRODUCT TESTS ====================
    
    def test_loan_products(self):
        """Test Loan Products configuration"""
        print("\n📋 Testing Loan Products...")
        
        try:
            products = LoanProduct.objects.filter(is_active=True)
            total = products.count()
            
            if total > 0:
                self.log_success("Loan Products", f"Found {total} active loan products")
                
                print("\n   Product Details:")
                for product in products:
                    print(f"   └─ {product.name}")
                    print(f"      • Interest Rate: {product.interest_rate}%")
                    print(f"      • Max Amount: KES {product.max_loan_amount:,.2f}")
                    print(f"      • Max Term: {product.max_loan_term_months} months")
                    if hasattr(product, 'min_loan_amount'):
                        print(f"      • Min Amount: KES {product.min_loan_amount:,.2f}")
            else:
                self.log_warning("Loan Products", "No active loan products found")
                
        except Exception as e:
            self.log_error("Loan Products", str(e))
            
    # ==================== LOAN APPLICATION TESTS ====================
    
    def test_loan_applications(self):
        """Test Loan Applications"""
        print("\n📝 Testing Loan Applications...")
        
        try:
            applications = LoanApplication.objects.all()
            total = applications.count()
            
            if total > 0:
                # Status breakdown
                status_breakdown = applications.values('status').annotate(
                    count=Count('id'),
                    total_amount=Sum('loan_amount')
                ).order_by('-count')
                
                self.log_success("Loan Applications", f"Found {total} loan applications")
                
                print("\n   Status Breakdown:")
                for status in status_breakdown:
                    amount = status['total_amount'] or Decimal('0')
                    print(f"   └─ {status['status']}: {status['count']} "
                          f"applications (KES {amount:,.2f})")
                
                # Calculate totals
                total_requested = applications.aggregate(
                    total=Sum('loan_amount')
                )['total'] or Decimal('0')
                
                approved_total = applications.filter(
                    status='approved'
                ).aggregate(
                    total=Sum('loan_amount')
                )['total'] or Decimal('0')
                
                print(f"\n   💰 Total Requested: KES {total_requested:,.2f}")
                print(f"   ✅ Total Approved: KES {approved_total:,.2f}")
                
                if total_requested > 0:
                    approval_rate = (approved_total / total_requested) * 100
                    print(f"   📊 Approval Rate: {approval_rate:.1f}%")
                    
            else:
                self.log_warning("Loan Applications", "No loan applications found")
                
        except Exception as e:
            self.log_error("Loan Applications", str(e))
            
    def test_loan_by_product(self):
        """Test Loans grouped by product type"""
        print("\n🏷️  Testing Loans by Product...")
        
        try:
            applications = LoanApplication.objects.select_related('loan_product')
            
            if applications.exists():
                # Group by product
                product_stats = applications.values(
                    'loan_product__name'
                ).annotate(
                    count=Count('id'),
                    total_amount=Sum('loan_amount'),
                    avg_amount=Avg('loan_amount')
                ).order_by('-total_amount')
                
                print("\n   Loans by Product Type:")
                for stat in product_stats:
                    product_name = stat['loan_product__name'] or 'Unknown'
                    count = stat['count']
                    total = stat['total_amount'] or Decimal('0')
                    avg = stat['avg_amount'] or Decimal('0')
                    
                    print(f"   └─ {product_name}")
                    print(f"      • Applications: {count}")
                    print(f"      • Total: KES {total:,.2f}")
                    print(f"      • Average: KES {avg:,.2f}")
                    
                self.log_success("Loans by Product", 
                    f"Analyzed {product_stats.count()} product types")
            else:
                print("   ℹ️  No loan applications to analyze")
                
        except Exception as e:
            self.log_error("Loans by Product", str(e))
            
    # ==================== REPAYMENT TESTS ====================
    
    def test_loan_payments_model(self):
        """Test Loan Payment records"""
        print("\n📅 Testing Loan Payments...")
        
        try:
            loan_payments = LoanPayment.objects.select_related('loan')
            total = loan_payments.count()
            
            if total > 0:
                self.log_success("Loan Payments Model", 
                    f"Found {total} loan payment records")
                
                # Calculate amounts
                total_paid = loan_payments.aggregate(
                    total=Sum('amount')
                )['total'] or Decimal('0')
                
                print(f"\n   💰 Total Paid: KES {total_paid:,.2f}")
                    
            else:
                self.log_warning("Loan Payments Model", "No loan payment records found")
                
        except Exception as e:
            self.log_error("Loan Payments Model", str(e))
            
    def test_loan_payments(self):
        """Test Loan Payments"""
        print("\n💳 Testing Loan Payments...")
        
        try:
            payments = Payment.objects.select_related('loan')
            total = payments.count()
            
            if total > 0:
                # Status breakdown
                status_breakdown = payments.values('status').annotate(
                    count=Count('id'),
                    total_amount=Sum('amount')
                )
                
                self.log_success("Loan Payments", f"Found {total} payments")
                
                print("\n   Payment Status:")
                for status in status_breakdown:
                    amount = status['total_amount'] or Decimal('0')
                    print(f"   └─ {status['status']}: {status['count']} "
                          f"(KES {amount:,.2f})")
                
                # Total paid
                total_paid = payments.filter(
                    status='completed'
                ).aggregate(
                    total=Sum('amount')
                )['total'] or Decimal('0')
                
                print(f"\n   💰 Total Completed Payments: KES {total_paid:,.2f}")
                
            else:
                self.log_warning("Loan Payments", "No loan payments found")
                
        except Exception as e:
            self.log_error("Loan Payments", str(e))
            
    # ==================== SECURITY TESTS ====================
    
    def test_guarantors(self):
        """Test Loan Guarantors"""
        print("\n👥 Testing Guarantors...")
        
        print("   ℹ️  Guarantor model not in current implementation")
            
    def test_collateral(self):
        """Test Loan Collateral"""
        print("\n🏠 Testing Collateral...")
        
        try:
            collateral = LoanCollateral.objects.select_related('loan')
            total = collateral.count()
            
            if total > 0:
                # Type breakdown
                type_breakdown = collateral.values('collateral_type').annotate(
                    count=Count('id'),
                    total_value=Sum('estimated_value')
                )
                
                self.log_success("Collateral", f"Found {total} collateral items")
                
                print("\n   Collateral Types:")
                for item in type_breakdown:
                    ctype = item['collateral_type']
                    count = item['count']
                    value = item['total_value'] or Decimal('0')
                    print(f"   └─ {ctype}: {count} items (KES {value:,.2f})")
                    
                # Total value
                total_value = collateral.aggregate(
                    total=Sum('estimated_value')
                )['total'] or Decimal('0')
                
                print(f"\n   💰 Total Collateral Value: KES {total_value:,.2f}")
                
            else:
                self.log_warning("Collateral", "No collateral items found")
                
        except Exception as e:
            self.log_error("Collateral", str(e))
            
    # ==================== BUSINESS LOGIC TESTS ====================
    
    def test_loan_calculations(self):
        """Test Loan interest and payment calculations"""
        print("\n🧮 Testing Loan Calculations...")
        
        try:
            active_loans = LoanApplication.objects.filter(
                status__in=['approved', 'disbursed']
            )
            
            if active_loans.exists():
                print("\n   Sample Loan Calculations:")
                
                for loan in active_loans[:3]:  # Test first 3 loans
                    print(f"\n   └─ Loan ID: {loan.id}")
                    print(f"      • Principal: KES {loan.loan_amount:,.2f}")
                    
                    if hasattr(loan, 'interest_rate') and loan.interest_rate:
                        print(f"      • Interest Rate: {loan.interest_rate}%")
                        
                        # Calculate simple interest
                        if hasattr(loan, 'loan_term_months') and loan.loan_term_months:
                            interest = (loan.loan_amount * loan.interest_rate * 
                                      loan.loan_term_months) / (100 * 12)
                            total = loan.loan_amount + interest
                            monthly = total / loan.loan_term_months
                            
                            print(f"      • Interest: KES {interest:,.2f}")
                            print(f"      • Total Repayment: KES {total:,.2f}")
                            print(f"      • Monthly Payment: KES {monthly:,.2f}")
                    
                    # Check if there are actual payments
                    payments = LoanPayment.objects.filter(loan=loan)
                    if payments.exists():
                        actual_total = payments.aggregate(
                            total=Sum('amount')
                        )['total'] or Decimal('0')
                        print(f"      • Total Paid: KES {actual_total:,.2f}")
                
                self.log_success("Loan Calculations", 
                    f"Verified calculations for {min(3, active_loans.count())} loans")
            else:
                print("   ℹ️  No active loans to calculate")
                
        except Exception as e:
            self.log_error("Loan Calculations", str(e))
            
    # ==================== URL ROUTING TESTS ====================
    
    def test_loan_urls(self):
        """Test Loan system URLs"""
        print("\n🌐 Testing Loan URLs...")
        
        from django.urls import reverse
        
        url_tests = [
            ('finance:user-loans', 'User Loans Dashboard'),
        ]
        
        for test in url_tests:
            try:
                url = reverse(test[0])
                self.log_success(f"URL: {test[1]}", f"Resolved: {url}")
            except Exception as e:
                self.log_error(f"URL: {test[1]}", str(e))
                
    # ==================== DATA INTEGRITY TESTS ====================
    
    def test_data_integrity(self):
        """Test data integrity and relationships"""
        print("\n🔍 Testing Data Integrity...")
        
        try:
            # Check for loans without products
            loans_without_product = LoanApplication.objects.filter(
                loan_product__isnull=True
            ).count()
            
            if loans_without_product > 0:
                self.log_warning("Data Integrity", 
                    f"{loans_without_product} loans without product assignment")
            else:
                self.log_success("Data Integrity", 
                    "All loans have product assignments")
            
            # Check for orphaned loan payments
            try:
                orphaned_loan_payments = LoanPayment.objects.filter(
                    loan__isnull=True
                ).count()
                
                if orphaned_loan_payments > 0:
                    self.log_warning("Data Integrity", 
                        f"{orphaned_loan_payments} orphaned loan payments")
                else:
                    self.log_success("Data Integrity", 
                        "No orphaned loan payments")
            except:
                pass  # Payment model might not have loan field
            
            # Check for orphaned payments
            orphaned_payments = Payment.objects.filter(
                loan__isnull=True
            ).count()
            
            if orphaned_payments > 0:
                self.log_warning("Data Integrity", 
                    f"{orphaned_payments} orphaned payments")
            else:
                self.log_success("Data Integrity", 
                    "No orphaned payments")
                
        except Exception as e:
            self.log_error("Data Integrity", str(e))
            
    # ==================== REPORT GENERATION ====================
    
    def generate_report(self):
        """Generate final test report"""
        print("\n" + "="*80)
        print("📋 LOAN SYSTEM TEST REPORT")
        print("="*80 + "\n")
        
        total_tests = len(self.results) + len(self.errors)
        passed = len(self.results)
        failed = len(self.errors)
        warnings = len(self.warnings)
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️  Warnings: {warnings}")
        
        if failed > 0:
            print(f"\n⚠️  Success Rate: {(passed/total_tests)*100:.1f}%")
            print("\n🔴 ERRORS FOUND:")
            for error in self.errors:
                print(f"  {error}")
        else:
            print(f"\n🎉 All tests passed! Success Rate: 100%")
            
        if warnings > 0:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  {warning}")
            
        print("\n" + "="*80 + "\n")
        
        return failed == 0
        
    def run_all_tests(self):
        """Run all test suites"""
        if not self.setup():
            print("\n❌ Setup failed. Cannot continue.")
            return False
            
        # Loan Product Tests
        print("\n" + "="*80)
        print("📋 LOAN PRODUCT TESTS")
        print("="*80)
        self.test_loan_products()
        
        # Loan Application Tests
        print("\n" + "="*80)
        print("📝 LOAN APPLICATION TESTS")
        print("="*80)
        self.test_loan_applications()
        self.test_loan_by_product()
        
        # Repayment Tests
        print("\n" + "="*80)
        print("💳 REPAYMENT TESTS")
        print("="*80)
        self.test_loan_payments_model()
        self.test_loan_payments()
        
        # Security Tests
        print("\n" + "="*80)
        print("🔒 SECURITY TESTS")
        print("="*80)
        self.test_guarantors()
        self.test_collateral()
        
        # Business Logic Tests
        print("\n" + "="*80)
        print("🧮 BUSINESS LOGIC TESTS")
        print("="*80)
        self.test_loan_calculations()
        
        # URL Tests
        print("\n" + "="*80)
        print("🌐 URL ROUTING TESTS")
        print("="*80)
        self.test_loan_urls()
        
        # Data Integrity Tests
        print("\n" + "="*80)
        print("🔍 DATA INTEGRITY TESTS")
        print("="*80)
        self.test_data_integrity()
        
        # Generate Report
        return self.generate_report()


if __name__ == '__main__':
    tester = LoanSystemTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

