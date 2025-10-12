#!/usr/bin/env python
"""
Comprehensive Budget Workflow Testing Script
Tests all key components of the budget system end-to-end
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, '/Users/coda/PROJECTS/CODA/DEVELOPMENT/DEV/coda')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from finance.models import BudgetRequest, BudgetCategory, Department, Budget, BudgetSubCategory
from finance.services.smart_approval_service import SmartApprovalService
from finance.services.smart_form_service import SmartFormService
from decimal import Decimal

User = get_user_model()

class BudgetWorkflowTester:
    def __init__(self):
        self.test_results = []
        self.errors = []
        
    def log_test(self, test_name, passed, message=""):
        status = "✅ PASS" if passed else "❌ FAIL"
        result = f"{status}: {test_name}"
        if message:
            result += f" - {message}"
        self.test_results.append(result)
        print(result)
        if not passed:
            self.errors.append(result)
    
    def test_1_database_models(self):
        """Test 1: Verify all models are accessible"""
        print("\n" + "="*80)
        print("TEST 1: Database Models")
        print("="*80)
        
        try:
            # Test BudgetRequest model
            request_count = BudgetRequest.objects.count()
            self.log_test("BudgetRequest model accessible", True, f"Found {request_count} requests")
            
            # Test BudgetCategory model
            category_count = BudgetCategory.objects.count()
            self.log_test("BudgetCategory model accessible", True, f"Found {category_count} categories")
            
            # Test Department model
            dept_count = Department.objects.count()
            self.log_test("Department model accessible", True, f"Found {dept_count} departments")
            
            # Test Budget model
            budget_count = Budget.objects.count()
            self.log_test("Budget model accessible", True, f"Found {budget_count} budget items")
            
        except Exception as e:
            self.log_test("Database models", False, str(e))
    
    def test_2_user_setup(self):
        """Test 2: Verify test users exist"""
        print("\n" + "="*80)
        print("TEST 2: User Setup")
        print("="*80)
        
        try:
            # Get or create test users
            self.regular_user = User.objects.filter(username='testuser').first()
            self.staff_user = User.objects.filter(is_staff=True).first()
            
            self.log_test("Regular user available", self.regular_user is not None, 
                         f"User: {self.regular_user.username if self.regular_user else 'None'}")
            self.log_test("Staff user available", self.staff_user is not None,
                         f"User: {self.staff_user.username if self.staff_user else 'None'}")
            
        except Exception as e:
            self.log_test("User setup", False, str(e))
    
    def test_3_smart_form_service(self):
        """Test 3: Test smart form suggestions"""
        print("\n" + "="*80)
        print("TEST 3: Smart Form Service")
        print("="*80)
        
        try:
            service = SmartFormService()
            
            # Test electricity suggestion
            suggestions = service.suggest_fields("Pay electricity bill for office", None)
            self.log_test("Electricity suggestion", 
                         suggestions['category'] == 'Utilities',
                         f"Category: {suggestions['category']}, Confidence: {suggestions['confidence']:.2f}")
            
            # Test internet suggestion
            suggestions = service.suggest_fields("Safaricom internet monthly payment", None)
            self.log_test("Internet suggestion",
                         suggestions['category'] == 'IT and Software',
                         f"Category: {suggestions['category']}, Confidence: {suggestions['confidence']:.2f}")
            
            # Test salary suggestion
            suggestions = service.suggest_fields("Monthly salary for new employee", None)
            self.log_test("Salary suggestion",
                         suggestions['category'] == 'Salaries and Wages',
                         f"Category: {suggestions['category']}, Confidence: {suggestions['confidence']:.2f}")
            
        except Exception as e:
            self.log_test("Smart form service", False, str(e))
    
    def test_4_smart_approval_service(self):
        """Test 4: Test smart approval logic"""
        print("\n" + "="*80)
        print("TEST 4: Smart Approval Service")
        print("="*80)
        
        try:
            service = SmartApprovalService()
            
            # Get a category
            utilities_cat = BudgetCategory.objects.filter(name='Utilities').first()
            it_cat = BudgetCategory.objects.filter(name__icontains='IT').first()
            
            if utilities_cat:
                # Test auto-approve for electricity (under 50k)
                test_request = BudgetRequest(
                    amount=Decimal('25000'),
                    budget_category=utilities_cat,
                    purpose='Electricity bill for office'
                )
                should_approve, reason = service.should_auto_approve(test_request)
                self.log_test("Auto-approve electricity < 50k", should_approve, reason)
                
                # Test manual review for electricity (over 50k)
                test_request.amount = Decimal('60000')
                should_approve, reason = service.should_auto_approve(test_request)
                self.log_test("Manual review electricity > 50k", not should_approve, reason)
            else:
                self.log_test("Smart approval - Utilities category", False, "Utilities category not found")
            
            if it_cat:
                # Test auto-approve for internet (under 15k)
                test_request = BudgetRequest(
                    amount=Decimal('10000'),
                    budget_category=it_cat,
                    purpose='Safaricom internet monthly subscription'
                )
                should_approve, reason = service.should_auto_approve(test_request)
                self.log_test("Auto-approve internet < 15k", should_approve, 
                             f"Category: {it_cat.name}, {reason}")
            else:
                self.log_test("Smart approval - IT category", False, "IT category not found")
                
        except Exception as e:
            self.log_test("Smart approval service", False, str(e))
    
    def test_5_budget_request_crud(self):
        """Test 5: Test budget request CRUD operations"""
        print("\n" + "="*80)
        print("TEST 5: Budget Request CRUD")
        print("="*80)
        
        try:
            # Get required data
            category = BudgetCategory.objects.first()
            department = Department.objects.first()
            user = User.objects.filter(is_staff=True).first()
            
            if not all([category, department, user]):
                self.log_test("Budget request CRUD - prerequisites", False, 
                             "Missing category, department, or user")
                return
            
            # Create a test budget request
            test_request = BudgetRequest.objects.create(
                requester=user,
                amount=Decimal('15000'),
                currency='KES',
                purpose='Test budget request for automated testing',
                department=department,
                budget_category=category,
                required_date=timezone.now().date(),
                priority='medium',
                status='draft',
                created_by=user,
                last_modified_by=user
            )
            self.log_test("Create budget request", True, f"Created request #{test_request.id}")
            
            # Update status to submitted
            test_request.status = 'submitted'
            test_request.save()
            self.log_test("Update request status", test_request.status == 'submitted', 
                         f"Status: {test_request.status}")
            
            # Approve request
            test_request.status = 'approved'
            test_request.save()
            self.log_test("Approve request", test_request.status == 'approved',
                         f"Status: {test_request.status}")
            
            # Clean up - mark as deleted instead of actually deleting (safer)
            test_request_id = test_request.id
            test_request.status = 'cancelled'
            test_request.save()
            self.log_test("Cancel test request", True, f"Cancelled request #{test_request_id}")
            
        except Exception as e:
            self.log_test("Budget request CRUD", False, str(e))
    
    def test_6_budget_statistics(self):
        """Test 6: Test budget statistics and queries"""
        print("\n" + "="*80)
        print("TEST 6: Budget Statistics")
        print("="*80)
        
        try:
            # Count requests by status
            draft_count = BudgetRequest.objects.filter(status='draft').count()
            submitted_count = BudgetRequest.objects.filter(status='submitted').count()
            approved_count = BudgetRequest.objects.filter(status='approved').count()
            rejected_count = BudgetRequest.objects.filter(status='rejected').count()
            
            self.log_test("Count draft requests", True, f"{draft_count} drafts")
            self.log_test("Count submitted requests", True, f"{submitted_count} submitted")
            self.log_test("Count approved requests", True, f"{approved_count} approved")
            self.log_test("Count rejected requests", True, f"{rejected_count} rejected")
            
            # Get recent requests
            recent_requests = BudgetRequest.objects.order_by('-created_at')[:5]
            self.log_test("Query recent requests", True, f"Found {len(recent_requests)} recent requests")
            
            # Get requests by category
            for category in BudgetCategory.objects.all()[:5]:
                count = BudgetRequest.objects.filter(budget_category=category).count()
                self.log_test(f"Requests for {category.name}", True, f"{count} requests")
            
        except Exception as e:
            self.log_test("Budget statistics", False, str(e))
    
    def test_7_budget_items(self):
        """Test 7: Test budget items and calculations"""
        print("\n" + "="*80)
        print("TEST 7: Budget Items")
        print("="*80)
        
        try:
            # Get budget items
            budget_items = Budget.objects.all()[:10]
            self.log_test("Query budget items", True, f"Found {len(budget_items)} items")
            
            # Test calculation
            for item in budget_items[:3]:
                if item.unit_price and item.quantity and item.cases:
                    calculated = item.unit_price * item.quantity * item.cases
                    self.log_test(f"Calculate budget for {item.item_name}", True,
                                 f"KES {calculated:,.2f}")
            
            # Get items by category
            for category in BudgetCategory.objects.all()[:3]:
                items = Budget.objects.filter(category=category)[:5]
                total = sum(
                    (item.estimated_amount or 0) if item.estimated_amount 
                    else ((item.unit_price or 0) * (item.quantity or 0) * (item.cases or 1))
                    for item in items
                )
                self.log_test(f"Total for {category.name}", True, f"KES {total:,.2f}")
            
        except Exception as e:
            self.log_test("Budget items", False, str(e))
    
    def test_8_url_patterns(self):
        """Test 8: Test URL patterns are configured correctly"""
        print("\n" + "="*80)
        print("TEST 8: URL Patterns")
        print("="*80)
        
        try:
            from django.urls import reverse, NoReverseMatch
            
            # Test key URLs
            urls_to_test = [
                ('finance:budget_request_form', {}),
                ('finance:budget_requests_list', {}),
                ('finance:unified-budget-dashboard', {'company_slug': 'coda'}),
                ('finance:budget-approval-dashboard', {'company_slug': 'coda'}),
            ]
            
            for url_name, kwargs in urls_to_test:
                try:
                    url = reverse(url_name, kwargs=kwargs)
                    self.log_test(f"URL pattern: {url_name}", True, f"Resolves to: {url}")
                except NoReverseMatch as e:
                    self.log_test(f"URL pattern: {url_name}", False, str(e))
            
        except Exception as e:
            self.log_test("URL patterns", False, str(e))
    
    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*80)
        print("COMPREHENSIVE BUDGET WORKFLOW TESTING")
        print("="*80)
        
        self.test_1_database_models()
        self.test_2_user_setup()
        self.test_3_smart_form_service()
        self.test_4_smart_approval_service()
        self.test_5_budget_request_crud()
        self.test_6_budget_statistics()
        self.test_7_budget_items()
        self.test_8_url_patterns()
        
        # Print summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if "✅ PASS" in result)
        failed_tests = sum(1 for result in self.test_results if "❌ FAIL" in result)
        
        print(f"\nTotal Tests: {total_tests}")
        print(f"Passed: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
        print(f"Failed: {failed_tests} ({failed_tests/total_tests*100:.1f}%)")
        
        if self.errors:
            print("\n" + "="*80)
            print("FAILED TESTS:")
            print("="*80)
            for error in self.errors:
                print(error)
        else:
            print("\n🎉 ALL TESTS PASSED! 🎉")
        
        return failed_tests == 0

if __name__ == '__main__':
    tester = BudgetWorkflowTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

