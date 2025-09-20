#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CODA Finance App - Comprehensive Functionality Test

This script tests the Loan and Payment methods functionality
to ensure they are working as expected.

Run this script from the project root directory.
"""

import os
import sys
import django
from decimal import Decimal
from datetime import datetime, timedelta

# Setup Django environment
sys.path.append('/Users/coda/PROJECTS/CODA/DEVELOPMENT/DEV/coda')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import AnonymousUser
from django.db import transaction

# Import models and services
from finance.models import (
    LoanProduct, LoanApplication, LoanPayment, Payment_Information, 
    Payment_History, PayslipConfig
)
from finance.services import LoanService, PaymentService
from accounts.models import CustomerUser

User = get_user_model()

class FinanceFunctionalityTest:
    """Comprehensive test suite for finance functionality"""
    
    def __init__(self):
        self.client = Client()
        self.loan_service = LoanService()
        self.payment_service = PaymentService()
        self.test_user = None
        self.test_loan_product = None
        self.test_results = []
        
    def log_test_result(self, test_name, status, message=""):
        """Log test result"""
        result = {
            'test': test_name,
            'status': status,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        status_icon = "PASS" if status == "PASS" else "FAIL"
        print(f"[{status_icon}] {test_name}: {message}")
        
    def setup_test_data(self):
        """Setup test data"""
        try:
            print("\n[SETUP] Setting up test data...")
            
            # Create test user
            self.test_user, created = CustomerUser.objects.get_or_create(
                username='test_finance_user',
                defaults={
                    'email': 'test@finance.com',
                    'first_name': 'Test',
                    'last_name': 'User',
                    'category': 1,  # Applicant
                    'is_active': True
                }
            )
            self.log_test_result("Setup Test User", "PASS", f"User {'created' if created else 'found'}")
            
            # Create test loan product
            self.test_loan_product, created = LoanProduct.objects.get_or_create(
                name='Test Personal Loan',
                defaults={
                    'description': 'Test loan product for functionality testing',
                    'min_amount': Decimal('100.00'),
                    'max_amount': Decimal('10000.00'),
                    'interest_rate': Decimal('15.00'),
                    'term_months': 12,
                    'fees': Decimal('50.00'),
                    'is_active': True,
                    'product_type': 'personal'
                }
            )
            self.log_test_result("Setup Test Loan Product", "PASS", f"Product {'created' if created else 'found'}")
            
            return True
            
        except Exception as e:
            self.log_test_result("Setup Test Data", "FAIL", str(e))
            return False
    
    def test_loan_product_creation(self):
        """Test loan product creation and validation"""
        try:
            # Test loan product properties
            assert self.test_loan_product.min_amount == Decimal('100.00')
            assert self.test_loan_product.max_amount == Decimal('10000.00')
            assert self.test_loan_product.interest_rate == Decimal('15.00')
            
            # Test calculation methods
            monthly_payment = self.test_loan_product.calculate_monthly_payment(Decimal('1000.00'), 12)
            assert monthly_payment > 0, "Monthly payment should be positive"
            
            total_payable = self.test_loan_product.calculate_total_payable(Decimal('1000.00'), term_months=12)
            assert total_payable > Decimal('1000.00'), "Total payable should include interest"
            
            self.log_test_result("Loan Product Creation", "PASS", f"Monthly payment: ${monthly_payment}, Total: ${total_payable}")
            
        except Exception as e:
            self.log_test_result("Loan Product Creation", "FAIL", str(e))
    
    def test_loan_application_creation(self):
        """Test loan application creation"""
        try:
            # Test data
            loan_data = {
                'loan_amount': '5000.00',
                'loan_product_id': self.test_loan_product.id,
                'purpose': 'Test loan application',
                'employment_status': 'employed',
                'monthly_income': '3000.00'
            }
            
            # Create loan application using service
            result = self.loan_service.create_loan_application(self.test_user, loan_data)
            
            if result['success']:
                loan_id = result['data']['loan_application_id']
                loan_app = LoanApplication.objects.get(id=loan_id)
                
                # Verify application properties
                assert loan_app.borrower == self.test_user
                assert loan_app.amount_requested == Decimal('5000.00')
                assert loan_app.purpose == 'Test loan application'
                assert loan_app.status == 'pending'
                
                self.log_test_result("Loan Application Creation", "PASS", f"Application ID: {loan_id}")
                return loan_app
            else:
                raise Exception(f"Service returned error: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            self.log_test_result("Loan Application Creation", "FAIL", str(e))
            return None
    
    def test_loan_approval_process(self):
        """Test loan approval process"""
        try:
            # Create a loan application first
            loan_app = self.test_loan_application_creation()
            if not loan_app:
                raise Exception("No loan application to test approval")
            
            # Create admin user for approval
            admin_user, created = CustomerUser.objects.get_or_create(
                username='test_admin',
                defaults={
                    'email': 'admin@test.com',
                    'first_name': 'Test',
                    'last_name': 'Admin',
                    'category': 2,  # Staff
                    'is_active': True,
                    'is_staff': True
                }
            )
            
            # Test approval
            approval_data = {'notes': 'Test approval'}
            result = self.loan_service.approve_loan_application(loan_app.id, admin_user, approval_data)
            
            if result['success']:
                # Refresh from database
                loan_app.refresh_from_db()
                assert loan_app.status == 'approved'
                assert loan_app.approved_by == admin_user
                
                self.log_test_result("Loan Approval Process", "PASS", f"Approved by {admin_user.username}")
            else:
                raise Exception(f"Approval failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            self.log_test_result("Loan Approval Process", "FAIL", str(e))
    
    def test_loan_payment_creation(self):
        """Test loan payment creation"""
        try:
            # Create a loan application first
            loan_app = self.test_loan_application_creation()
            if not loan_app:
                raise Exception("No loan application to test payment")
            
            # Create loan payment
            payment = LoanPayment.objects.create(
                loan_application=loan_app,
                payment_date=datetime.now().date(),
                amount=Decimal('500.00'),
                payment_type='regular',
                notes='Test payment'
            )
            
            # Verify payment properties
            assert payment.loan_application == loan_app
            assert payment.amount == Decimal('500.00')
            assert payment.payment_type == 'regular'
            assert payment.reference_number is not None
            
            # Test loan application payment tracking
            total_paid = loan_app.total_paid
            assert total_paid == Decimal('500.00')
            
            balance = loan_app.balance_amount
            assert balance == (loan_app.total_payable - total_paid)
            
            self.log_test_result("Loan Payment Creation", "PASS", f"Payment: ${payment.amount}, Balance: ${balance}")
            
        except Exception as e:
            self.log_test_result("Loan Payment Creation", "FAIL", str(e))
    
    def test_payment_information_creation(self):
        """Test payment information creation"""
        try:
            # Create payment information
            payment_info = Payment_Information.objects.create(
                customer_id=self.test_user,
                payment_fees=2000,
                down_payment=500,
                student_bonus=250,
                plan=1,
                payment_method='PayPal',
                description='Test payment information',
                is_active=True
            )
            
            # Test calculated properties
            fee_balance = payment_info.fee_balance
            expected_balance = 2000 - (500 + 250)  # 1250
            
            assert fee_balance == expected_balance, f"Expected {expected_balance}, got {fee_balance}"
            
            self.log_test_result("Payment Information Creation", "PASS", f"Balance: ${fee_balance}")
            return payment_info
            
        except Exception as e:
            self.log_test_result("Payment Information Creation", "FAIL", str(e))
            return None
    
    def test_payment_methods_functionality(self):
        """Test payment methods functionality"""
        try:
            # Test payment method constants from payment_views
            from finance.payment_views import PAYMENT_METHODS
            
            expected_methods = ['mpesa', 'paypal', 'cashapp', 'zelle', 'venmo', 'stripe']
            
            for method in expected_methods:
                assert method in PAYMENT_METHODS, f"Payment method {method} not found"
                
                method_info = PAYMENT_METHODS[method]
                required_fields = ['name', 'display_name', 'icon', 'color', 'description']
                
                for field in required_fields:
                    assert field in method_info, f"Field {field} missing from {method}"
            
            self.log_test_result("Payment Methods Functionality", "PASS", f"All {len(expected_methods)} methods available")
            
        except Exception as e:
            self.log_test_result("Payment Methods Functionality", "FAIL", str(e))
    
    def test_loan_eligibility_validation(self):
        """Test loan eligibility validation"""
        try:
            # Create loan application
            loan_app = self.test_loan_application_creation()
            if not loan_app:
                raise Exception("No loan application to test eligibility")
            
            # Test eligibility validation
            is_eligible, message = loan_app.validate_eligibility()
            
            # For test user with employed status, should be eligible
            if loan_app.employment_status == 'employed':
                assert is_eligible, f"Employed user should be eligible: {message}"
            
            self.log_test_result("Loan Eligibility Validation", "PASS", message)
            
        except Exception as e:
            self.log_test_result("Loan Eligibility Validation", "FAIL", str(e))
    
    def test_kcc_benefits_calculation(self):
        """Test KCC benefits calculation"""
        try:
            # Create a KCC member user
            kcc_user, created = CustomerUser.objects.get_or_create(
                username='test_kcc_user',
                defaults={
                    'email': 'kcc@test.com',
                    'first_name': 'KCC',
                    'last_name': 'User',
                    'category': 1,  # Applicant
                    'is_active': True
                }
            )
            
            # Create loan application for KCC user
            loan_data = {
                'loan_amount': '3000.00',
                'loan_product_id': self.test_loan_product.id,
                'purpose': 'KCC test loan',
                'employment_status': 'employed',
                'monthly_income': '2500.00'
            }
            
            result = self.loan_service.create_loan_application(kcc_user, loan_data)
            
            if result['success']:
                loan_id = result['data']['loan_application_id']
                loan_app = LoanApplication.objects.get(id=loan_id)
                
                # Test KCC benefits calculation
                benefits = loan_app.calculate_kcc_benefits()
                
                # Should return benefits structure even if user is not KCC member
                assert 'interest_rate_discount' in benefits
                assert 'processing_fee_discount' in benefits
                assert 'max_loan_increase' in benefits
                assert 'total_benefits' in benefits
                
                self.log_test_result("KCC Benefits Calculation", "PASS", f"Benefits calculated: {benefits}")
            else:
                raise Exception(f"KCC loan creation failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            self.log_test_result("KCC Benefits Calculation", "FAIL", str(e))
    
    def test_url_patterns(self):
        """Test URL patterns are working"""
        try:
            # Test key URL patterns
            url_tests = [
                ('finance:loan-home', 'Loan home page'),
                ('finance:unified_method_selection', 'Payment method selection'),
                ('finance:payments', 'Payments history'),
            ]
            
            for url_name, description in url_tests:
                try:
                    url = reverse(url_name)
                    assert url is not None, f"URL for {url_name} is None"
                    self.log_test_result(f"URL Pattern: {description}", "PASS", f"URL: {url}")
                except Exception as e:
                    self.log_test_result(f"URL Pattern: {description}", "FAIL", str(e))
                    
        except Exception as e:
            self.log_test_result("URL Patterns Test", "FAIL", str(e))
    
    def run_all_tests(self):
        """Run all tests"""
        print("STARTING CODA Finance App Functionality Tests")
        print("=" * 60)
        
        # Setup
        if not self.setup_test_data():
            print("[ERROR] Test setup failed. Aborting tests.")
            return
        
        # Run tests
        test_methods = [
            self.test_loan_product_creation,
            self.test_loan_application_creation,
            self.test_loan_approval_process,
            self.test_loan_payment_creation,
            self.test_payment_information_creation,
            self.test_payment_methods_functionality,
            self.test_loan_eligibility_validation,
            self.test_kcc_benefits_calculation,
            self.test_url_patterns,
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                self.log_test_result(test_method.__name__, "FAIL", f"Unexpected error: {str(e)}")
        
        # Summary
        self.print_test_summary()
    
    def print_test_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"[PASS] Passed: {passed_tests}")
        print(f"[FAIL] Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n[FAIL] FAILED TESTS:")
            for result in self.test_results:
                if result['status'] == 'FAIL':
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\n" + "=" * 60)
        
        if failed_tests == 0:
            print("[SUCCESS] ALL TESTS PASSED! Finance functionality is working correctly.")
        else:
            print("[WARNING] Some tests failed. Please review the issues above.")
        
        return failed_tests == 0

def main():
    """Main function"""
    try:
        tester = FinanceFunctionalityTest()
        success = tester.run_all_tests()
        return 0 if success else 1
    except Exception as e:
        print(f"[ERROR] Test runner failed: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())
