# Comprehensive Testing Strategy for CODA Project
**Created:** October 13, 2025  
**Purpose:** Prevent regressions, ensure quality, reduce debugging time

---

## 🎯 THE PROBLEM

We've spent significant time fixing:
- ✅ Template errors (missing fields, wrong paths)
- ✅ View errors (import issues, missing methods)
- ✅ Model mismatches (schema alignment)
- ✅ Business logic bugs (approval permissions, aggregation)

**Root Cause:** Deploying without comprehensive testing!

---

## 🧪 TESTING PYRAMID STRATEGY

```
           /\
          /  \  E2E Tests (5%)
         /    \  - Critical user journeys
        /------\  - Full system integration
       /        \
      / System   \ Integration Tests (15%)
     /            \ - Feature integration
    /  Unit Tests  \ - API contracts
   /________________\
        (80%)
   - Models, Services
   - Utilities, Helpers
   - Business logic
```

**Philosophy:**
- **80% Unit Tests** - Fast, isolated, catch logic errors
- **15% Integration Tests** - Verify components work together
- **5% E2E Tests** - Critical user paths work end-to-end

---

## 📋 TEST TYPES & IMPLEMENTATION

### 1. UNIT TESTS (80% Coverage Target)

**What:** Test individual functions/methods in isolation

**Framework:** Django's built-in TestCase + pytest

**Location:** `coda/[app]/tests/test_*.py`

#### 1.1 Model Tests
```python
# coda/finance/tests/test_models.py

from django.test import TestCase
from finance.models import BudgetRequest, LoanProduct
from decimal import Decimal

class BudgetRequestModelTest(TestCase):
    """Test BudgetRequest model"""
    
    def setUp(self):
        self.user = create_test_user()
        self.category = create_test_category()
    
    def test_budget_request_creation(self):
        """Test creating a budget request"""
        request = BudgetRequest.objects.create(
            requester=self.user,
            amount=Decimal('500.00'),
            purpose="Test budget",
            budget_category=self.category,
            status='pending'
        )
        self.assertEqual(request.status, 'pending')
        self.assertEqual(request.amount, Decimal('500.00'))
    
    def test_budget_approval_sets_fields(self):
        """Test that approving sets approved_by and approved_at"""
        request = create_test_budget_request()
        request.approve(self.user)
        
        self.assertEqual(request.status, 'approved')
        self.assertEqual(request.approved_by, self.user)
        self.assertIsNotNone(request.approved_at)
    
    def test_budget_rejection_requires_reason(self):
        """Test that rejection requires a reason"""
        request = create_test_budget_request()
        with self.assertRaises(ValueError):
            request.reject(self.user, reason='')

class LoanProductModelTest(TestCase):
    """Test LoanProduct model"""
    
    def test_term_months_field_exists(self):
        """Regression: Ensure term_months field exists (not min/max)"""
        product = LoanProduct.objects.create(
            name="Test Loan",
            product_type='fixed',
            interest_rate=Decimal('10.00'),
            term_months=12,
            min_amount=5000,
            max_amount=50000
        )
        self.assertEqual(product.term_months, 12)
        
        # Ensure old fields don't exist
        with self.assertRaises(AttributeError):
            _ = product.min_term_months
```

#### 1.2 Service Tests
```python
# coda/finance/tests/test_services.py

class BudgetApprovalServiceTest(TestCase):
    """Test budget approval business logic"""
    
    def test_can_approve_as_staff(self):
        """Staff users can approve budgets"""
        staff_user = create_staff_user()
        request = create_test_budget_request()
        
        service = BudgetApprovalService()
        self.assertTrue(service.can_approve(staff_user, request))
    
    def test_cannot_approve_as_regular_user(self):
        """Regular users cannot approve budgets"""
        regular_user = create_regular_user()
        request = create_test_budget_request()
        
        service = BudgetApprovalService()
        self.assertFalse(service.can_approve(regular_user, request))
    
    def test_variance_calculation(self):
        """Test variance calculation for anomaly detection"""
        service = IntelligentApprovalEngine()
        
        variance = service._calculate_variance(
            actual=1200,
            typical=1000
        )
        self.assertEqual(variance, 20.0)  # 20% variance

class LoanServiceTest(TestCase):
    """Test loan calculation logic"""
    
    def test_monthly_payment_calculation(self):
        """Test amortization calculation"""
        service = LoanService()
        
        payment = service.calculate_monthly_payment(
            amount=10000,
            rate=10.0,
            term_months=12
        )
        
        # Expected: ~879.16
        self.assertAlmostEqual(payment, 879.16, places=2)
```

#### 1.3 Utility/Helper Tests
```python
# coda/finance/tests/test_utils.py

class AggregationUtilsTest(TestCase):
    """Test critical aggregation formulas"""
    
    def test_budget_total_aggregation(self):
        """Regression: Ensure we don't use Sum() * Sum() pattern"""
        # Create test data
        create_budget_with_items([
            {'quantity': 2, 'unit_price': 100},
            {'quantity': 3, 'unit_price': 50},
        ])
        
        # Calculate total
        total = calculate_budget_total(budget_id=1)
        
        # Should be (2*100) + (3*50) = 350
        # NOT (2+3) * (100+50) = 750 (the bug we had!)
        self.assertEqual(total, Decimal('350.00'))
```

---

### 2. INTEGRATION TESTS (15% Coverage)

**What:** Test how components work together

#### 2.1 View Integration Tests
```python
# coda/finance/tests/test_views_integration.py

class BudgetApprovalViewTest(TestCase):
    """Test approval views with database"""
    
    def setUp(self):
        self.client = Client()
        self.staff_user = create_staff_user()
        self.budget_request = create_test_budget_request()
    
    def test_approval_dashboard_loads(self):
        """Test approval dashboard renders correctly"""
        self.client.login(username='staff', password='test123')
        
        response = self.client.get('/finance/budget/coda/approvals/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pending Requests')
        self.assertContains(response, self.budget_request.purpose)
    
    def test_approve_budget_workflow(self):
        """Test complete approval workflow"""
        self.client.login(username='staff', password='test123')
        
        # Approve
        response = self.client.post(
            f'/finance/budget/coda/approve/{self.budget_request.id}/',
            follow=True
        )
        
        # Verify redirect
        self.assertEqual(response.status_code, 200)
        
        # Verify database updated
        self.budget_request.refresh_from_db()
        self.assertEqual(self.budget_request.status, 'approved')
        self.assertEqual(self.budget_request.approved_by, self.staff_user)
    
    def test_reject_budget_workflow(self):
        """Test rejection with reason"""
        self.client.login(username='staff', password='test123')
        
        response = self.client.post(
            f'/finance/budget/coda/reject/{self.budget_request.id}/',
            {'rejection_reason': 'Insufficient justification'},
            follow=True
        )
        
        self.budget_request.refresh_from_db()
        self.assertEqual(self.budget_request.status, 'rejected')
        self.assertEqual(
            self.budget_request.rejection_reason,
            'Insufficient justification'
        )
```

#### 2.2 API Integration Tests
```python
# coda/finance/tests/test_api_integration.py

class CascadingDropdownAPITest(TestCase):
    """Test cascading dropdown APIs"""
    
    def test_subcategories_filter_by_category(self):
        """Test /api/subcategories/{category_id}/"""
        # Create test data
        utilities = BudgetCategory.objects.create(name='Utilities')
        electricity = BudgetSubcategory.objects.create(
            name='Electricity',
            category=utilities
        )
        water = BudgetSubcategory.objects.create(
            name='Water',
            category=utilities
        )
        
        # Other category
        travel = BudgetCategory.objects.create(name='Travel')
        flights = BudgetSubcategory.objects.create(
            name='Flights',
            category=travel
        )
        
        # Call API
        response = self.client.get(f'/finance/api/subcategories/{utilities.id}/')
        data = response.json()
        
        # Should only return utilities subcategories
        self.assertEqual(len(data), 2)
        names = [item['name'] for item in data]
        self.assertIn('Electricity', names)
        self.assertIn('Water', names)
        self.assertNotIn('Flights', names)
```

#### 2.3 Database Integration Tests
```python
# coda/finance/tests/test_database_integration.py

class TransactionCategoryIntegrationTest(TestCase):
    """Test transaction categorization with real data"""
    
    def test_auto_categorization_command(self):
        """Test management command categorizes correctly"""
        # Create uncategorized transactions
        Transaction.objects.create(
            description="KPLC electricity bill",
            amount=1500,
            category=None
        )
        Transaction.objects.create(
            description="Safaricom data bundle",
            amount=500,
            category=None
        )
        
        # Run categorization
        call_command('categorize_transactions')
        
        # Verify
        kplc = Transaction.objects.get(description__icontains='KPLC')
        self.assertEqual(kplc.category.name, 'Utilities')
        
        safaricom = Transaction.objects.get(description__icontains='Safaricom')
        self.assertEqual(safaricom.category.name, 'IT & Software')
```

---

### 3. SYSTEM TESTS (5%)

**What:** Test entire features/workflows end-to-end within the system

```python
# coda/finance/tests/test_budget_system.py

class BudgetSystemTest(TestCase):
    """Test complete budget system workflow"""
    
    def test_complete_budget_lifecycle(self):
        """Test: Create → Submit → Approve → Track"""
        
        # 1. User creates budget request
        requester = create_regular_user()
        self.client.login(username='requester', password='test123')
        
        response = self.client.post('/finance/budget/request/new/', {
            'title': 'Q4 Office Supplies',
            'amount': '500.00',
            'purpose': 'Pens, paper, folders',
            'category': self.office_supplies.id,
            'priority': 'medium'
        })
        
        request_id = BudgetRequest.objects.latest('id').id
        
        # 2. Staff approves
        self.client.logout()
        self.client.login(username='staff', password='test123')
        
        response = self.client.post(
            f'/finance/budget/coda/approve/{request_id}/'
        )
        
        # 3. Verify approval shows in dashboard
        response = self.client.get('/dashboard/')
        self.assertContains(response, 'Q4 Office Supplies')
        
        # 4. Verify budget tracking
        budget = BudgetRequest.objects.get(id=request_id)
        self.assertEqual(budget.status, 'approved')
        self.assertIsNotNone(budget.approved_by)
```

---

### 4. E2E TESTS (Critical User Journeys)

**Framework:** Selenium WebDriver or Playwright

**Location:** `coda/tests/e2e/`

```python
# coda/tests/e2e/test_budget_approval_journey.py

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

class BudgetApprovalE2ETest(LiveServerTestCase):
    """End-to-end test: Complete budget approval journey"""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.driver = webdriver.Chrome()
        cls.driver.implicitly_wait(10)
    
    def test_complete_budget_approval_journey(self):
        """
        User Story: As a staff member, I can approve budget requests
        
        Steps:
        1. Login as staff
        2. Navigate to approval dashboard
        3. See pending requests
        4. Click approve on a request
        5. Verify success message
        6. Verify request removed from pending
        7. Verify request in approved list
        """
        driver = self.driver
        
        # 1. Login
        driver.get(f'{self.live_server_url}/accounts/login/')
        driver.find_element(By.NAME, 'username').send_keys('staff')
        driver.find_element(By.NAME, 'password').send_keys('test123')
        driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        # 2. Navigate to approvals
        driver.get(f'{self.live_server_url}/finance/budget/coda/approvals/')
        
        # 3. Verify page loaded
        assert 'Budget Approvals' in driver.title
        
        # 4. Click approve button
        approve_button = driver.find_element(
            By.CSS_SELECTOR,
            'button[title="Approve"]'
        )
        approve_button.click()
        
        # 5. Verify success message
        WebDriverWait(driver, 10).until(
            lambda d: 'approved successfully' in d.page_source
        )
        
        # 6. Verify removed from pending
        pending_count_before = len(driver.find_elements(
            By.CSS_SELECTOR,
            '.pending-requests-table tbody tr'
        ))
        # Should be one less now
        
        # 7. Verify in approved list
        approved_list = driver.find_element(By.ID, 'recent-approvals')
        assert 'Just now' in approved_list.text
    
    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super().tearDownClass()
```

---

### 5. REGRESSION TESTS (Prevent Known Bugs)

**Purpose:** Ensure fixed bugs don't come back

```python
# coda/finance/tests/test_regressions.py

class RegressionTests(TestCase):
    """Tests for previously fixed bugs"""
    
    def test_dashboard_aggregation_bug_oct2(self):
        """
        Regression Test: Dashboard 177x inflation bug
        
        Bug: Using Sum('quantity') * Sum('unit_price')
        Fix: Use Sum(F('unit_price') * F('quantity'))
        Date Fixed: Oct 2, 2025
        """
        # Create budget with items
        budget = create_budget_with_items([
            {'quantity': 2, 'unit_price': 100},  # 200
            {'quantity': 3, 'unit_price': 50},   # 150
        ])
        
        # Calculate total (should be 350, not 750)
        total = budget.calculate_total()
        
        self.assertEqual(total, Decimal('350.00'))
        self.assertNotEqual(total, Decimal('750.00'))  # The bug value
    
    def test_budget_request_has_approval_fields_oct13(self):
        """
        Regression Test: Missing approval fields
        
        Bug: approved_by, approved_at fields missing
        Fix: Migration 0099 added fields
        Date Fixed: Oct 13, 2025
        """
        request = BudgetRequest.objects.create(
            requester=create_test_user(),
            amount=500,
            status='pending'
        )
        
        # These fields should exist (no AttributeError)
        self.assertIsNone(request.approved_by)
        self.assertIsNone(request.approved_at)
        self.assertIsNone(request.rejected_by)
        self.assertIsNone(request.rejected_at)
    
    def test_loan_product_term_months_field_oct13(self):
        """
        Regression Test: LoanProduct schema mismatch
        
        Bug: Dev had min_term/max_term, prod had term_months
        Fix: Aligned to prod schema (single term_months)
        Date Fixed: Oct 13, 2025
        """
        product = LoanProduct.objects.create(
            name="Test",
            product_type='fixed',
            interest_rate=10,
            term_months=12,  # Single field
            min_amount=5000,
            max_amount=50000
        )
        
        self.assertEqual(product.term_months, 12)
        
        # Old fields should not exist
        with self.assertRaises(AttributeError):
            _ = product.min_term_months
```

---

### 6. PERFORMANCE TESTS

**Purpose:** Ensure system performs well under load

```python
# coda/finance/tests/test_performance.py

from django.test import TestCase
from django.test.utils import override_settings
import time

class PerformanceTests(TestCase):
    """Performance benchmarks"""
    
    def test_approval_dashboard_load_time(self):
        """Dashboard should load in <2 seconds with 100 requests"""
        # Create 100 budget requests
        for i in range(100):
            create_test_budget_request(status='pending')
        
        self.client.login(username='staff', password='test123')
        
        start = time.time()
        response = self.client.get('/finance/budget/coda/approvals/')
        end = time.time()
        
        load_time = end - start
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(load_time, 2.0, f"Page took {load_time:.2f}s to load")
    
    def test_database_query_count(self):
        """Dashboard should use <20 queries (avoid N+1)"""
        create_test_budget_requests(count=50)
        
        self.client.login(username='staff', password='test123')
        
        with self.assertNumQueries(19):  # Set acceptable limit
            response = self.client.get('/finance/budget/coda/approvals/')
```

---

### 7. SECURITY TESTS

```python
# coda/finance/tests/test_security.py

class SecurityTests(TestCase):
    """Security and permission tests"""
    
    def test_cross_company_data_access(self):
        """Users cannot access other companies' data"""
        company_a = create_test_company(name='Company A')
        company_b = create_test_company(name='Company B')
        
        user_a = create_test_user(company=company_a)
        budget_b = create_test_budget_request(company=company_b)
        
        self.client.login(username=user_a.username, password='test123')
        
        # Try to access Company B's budget
        response = self.client.get(
            f'/finance/budget/request/{budget_b.id}/'
        )
        
        # Should be 404 or 403
        self.assertIn(response.status_code, [403, 404])
    
    def test_sql_injection_protection(self):
        """Test SQL injection attempts are blocked"""
        malicious_input = "'; DROP TABLE finance_budgetrequest; --"
        
        response = self.client.post('/finance/budget/request/new/', {
            'title': malicious_input,
            'amount': '500',
            'purpose': 'Test'
        })
        
        # Table should still exist
        self.assertTrue(BudgetRequest.objects.exists())
    
    def test_csrf_protection(self):
        """POST requests require CSRF token"""
        self.client.login(username='staff', password='test123')
        
        # POST without CSRF token
        response = self.client.post(
            '/finance/budget/coda/approve/1/',
            enforce_csrf_checks=True
        )
        
        self.assertEqual(response.status_code, 403)
```

---

## 📁 TESTING STRUCTURE

```
coda/
├── [app]/
│   └── tests/
│       ├── __init__.py
│       ├── test_models.py          # Model unit tests
│       ├── test_services.py        # Service unit tests
│       ├── test_views.py           # View integration tests
│       ├── test_api.py             # API integration tests
│       ├── test_utils.py           # Utility tests
│       └── test_regressions.py     # Regression tests
│
└── tests/
    ├── e2e/
    │   ├── test_budget_journey.py  # E2E tests
    │   └── test_transaction_journey.py
    │
    ├── performance/
    │   └── test_performance.py     # Load tests
    │
    └── security/
        └── test_security.py        # Security tests
```

---

## 🚀 RUNNING TESTS

### Local Development

```bash
# All tests
python manage.py test

# Specific app
python manage.py test finance

# Specific test file
python manage.py test finance.tests.test_models

# Specific test class
python manage.py test finance.tests.test_models.BudgetRequestModelTest

# Specific test method
python manage.py test finance.tests.test_models.BudgetRequestModelTest.test_budget_approval_sets_fields

# With coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Generate HTML report
```

### CI/CD Pipeline

```bash
# .github/workflows/tests.yml

name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.12
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install coverage
      
      - name: Run tests with coverage
        run: |
          cd coda
          coverage run manage.py test
          coverage report --fail-under=80
      
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

---

## 📊 TEST COVERAGE TARGETS

### By Component:
- **Models:** 90%+ (critical data layer)
- **Services:** 85%+ (business logic)
- **Views:** 70%+ (harder to test, focus on critical paths)
- **Templates:** Manual/E2E (automated template testing limited)
- **Utils:** 95%+ (should be pure functions)

### By Test Type:
- **Unit Tests:** 80% of total tests
- **Integration Tests:** 15% of total tests
- **E2E Tests:** 5% of total tests (critical paths only)

### Overall Target: **80% code coverage**

---

## 🎯 TESTING CHECKLIST (Pre-Deployment)

### Unit Tests
- [ ] All models have test coverage
- [ ] All services have test coverage
- [ ] Critical utilities tested
- [ ] Edge cases covered

### Integration Tests
- [ ] View workflows tested
- [ ] API endpoints tested
- [ ] Database operations tested

### Regression Tests
- [ ] All known bugs have regression tests
- [ ] Oct 2 dashboard bug
- [ ] Oct 13 approval fields bug
- [ ] Oct 13 loan schema bug

### System Tests
- [ ] Budget lifecycle tested
- [ ] Transaction categorization tested
- [ ] Loan application tested

### E2E Tests
- [ ] Login → Dashboard → Approve workflow
- [ ] Transaction entry workflow
- [ ] Loan application workflow

### Performance Tests
- [ ] Dashboard loads <2s with 100 items
- [ ] No N+1 query problems
- [ ] Database queries optimized

### Security Tests
- [ ] Cross-company access blocked
- [ ] SQL injection protected
- [ ] CSRF protection working
- [ ] XSS protection working

### Manual UAT Tests
- [ ] Theme switcher works
- [ ] All buttons functional
- [ ] Mobile responsive
- [ ] Browser compatibility (Chrome, Firefox, Safari)

---

## 🔄 TEST-DRIVEN DEVELOPMENT WORKFLOW

### For New Features:
1. **Write test first** (fails - feature doesn't exist yet)
2. **Write minimal code** to make test pass
3. **Refactor** while keeping tests green
4. **Add more tests** for edge cases
5. **Update documentation**

### For Bug Fixes:
1. **Write regression test** (reproduces bug)
2. **Verify test fails** (bug exists)
3. **Fix the bug**
4. **Verify test passes**
5. **Add to regression test suite**

---

## 📝 DOCUMENTATION REQUIREMENTS

Every test file should have:
```python
"""
Tests for [Component Name]

Test Coverage:
- [Feature 1]: test_feature_1()
- [Feature 2]: test_feature_2()
- Regression: test_bug_oct13()

Last Updated: [Date]
"""
```

---

## 🎯 IMMEDIATE ACTION PLAN

### Week 1 (This Week):
1. **Set up test structure** (directories, base classes)
2. **Write regression tests** for all Oct bugs
3. **Critical model tests** (BudgetRequest, LoanProduct, Transaction)
4. **Critical view tests** (approval workflow)
5. **Run tests before deployment**

### Week 2:
6. **Service layer tests** (approval engine, loan calculations)
7. **API integration tests** (cascading dropdowns)
8. **Performance benchmarks** (dashboard load time)
9. **Security tests** (permissions, SQL injection)

### Week 3:
10. **E2E tests** (critical user journeys with Selenium)
11. **Coverage report** (aim for 80%)
12. **CI/CD setup** (automated testing on push)

### Week 4:
13. **Full test suite** runs before every deployment
14. **Code review** includes test review
15. **Monthly regression** test all known bugs

---

## 💡 TESTING BEST PRACTICES

### DO:
- ✅ Write tests for every bug fix
- ✅ Test edge cases and error conditions
- ✅ Use descriptive test names
- ✅ Keep tests independent (no shared state)
- ✅ Mock external services
- ✅ Test one thing per test

### DON'T:
- ❌ Skip tests because "it's just a small change"
- ❌ Write tests that depend on specific data
- ❌ Test framework code (Django itself)
- ❌ Have flaky tests (random failures)
- ❌ Commit failing tests

---

## 📊 METRICS TO TRACK

- **Code Coverage:** Target 80%
- **Test Execution Time:** <5 minutes for full suite
- **Bug Escape Rate:** Bugs found in production vs testing
- **Test Failures:** Should trend to zero
- **Regression Rate:** Fixed bugs that come back

---

**Status:** Strategy Complete  
**Next:** Implement Week 1 action plan  
**Timeline:** 4 weeks to full test coverage

