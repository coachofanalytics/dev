# Testing Standards & Structure

**Created:** November 5, 2025  
**Status:** ✅ ACTIVE STANDARD  
**Purpose:** Define clear testing standards and Cursor AI vs Human responsibilities

---

## Standard Test Folder Structure

### Directory Organization

```
tests/
├── {app_name}/
│   ├── 01_unit/
│   │   ├── test_models.py
│   │   ├── test_services.py
│   │   ├── test_forms.py
│   │   └── test_utils.py
│   ├── 02_integration/
│   │   ├── test_views.py
│   │   ├── test_workflows.py
│   │   └── test_api.py
│   ├── 03_performance/
│   │   ├── test_query_performance.py
│   │   ├── test_load_times.py
│   │   └── benchmarks.py
│   ├── 04_regression/
│   │   ├── test_critical_bugs.py
│   │   └── test_known_issues.py
│   ├── 05_system/
│   │   ├── test_end_to_end.py
│   │   └── test_user_flows.py
│   ├── 06_security/
│   │   ├── test_authentication.py
│   │   ├── test_authorization.py
│   │   └── test_data_validation.py
│   ├── 07_manual/
│   │   ├── MANUAL_TEST_PLAN.md
│   │   ├── CHECKLIST.md
│   │   └── test_results/
│   │       └── YYYY-MM-DD_test_session.md
│   ├── fixtures/
│   │   └── {model_name}.json
│   └── README.md
└── README.md
```

---

## Test Categories Explained

### 01_UNIT (Fully Automatable by Cursor) 🤖

**Purpose:** Test individual components in isolation

**What to Test:**
- Model methods and properties
- Service class methods
- Form validation
- Utility functions
- Calculations and logic

**Cursor Can Create:**
- ✅ Model tests (save, validation, methods, properties)
- ✅ Service tests (business logic, calculations)
- ✅ Form tests (validation, cleaning, field behavior)
- ✅ Utility function tests
- ✅ Helper function tests

**Example:**
```python
# tests/investing/01_unit/test_models.py
class ManagedTradingAccountModelTest(TestCase):
    def test_available_buying_power_calculation(self):
        account = ManagedTradingAccount.objects.create(
            cash_available=Decimal('10000.00'),
            cash_reserved=Decimal('2000.00'),
            # ... other fields
        )
        self.assertEqual(account.available_buying_power, Decimal('8000.00'))
    
    def test_available_buying_power_with_none_values(self):
        account = ManagedTradingAccount(cash_available=None, cash_reserved=None)
        self.assertEqual(account.available_buying_power, Decimal('0.00'))
```

**Human Responsibility:** NONE (Cursor creates all unit tests)

---

### 02_INTEGRATION (Mostly Automatable by Cursor) 🤖➕

**Purpose:** Test how components work together

**What to Test:**
- View functions (GET/POST requests)
- URL routing
- Template rendering
- Form submission workflows
- Service integration

**Cursor Can Create:**
- ✅ View tests (basic GET/POST)
- ✅ URL resolution tests
- ✅ Template rendering tests
- ✅ Form submission tests
- ✅ Service integration tests
- ✅ API endpoint tests

**Cursor CANNOT Test:**
- ❌ JavaScript interactions
- ❌ AJAX workflows (requires browser)
- ❌ File uploads (complex)
- ❌ Multi-step wizards (complex state)

**Example:**
```python
# tests/investing/02_integration/test_views.py
class ManagedAccountViewTest(TestCase):
    def test_create_account_view_loads(self):
        self.client.login(username='staff_user', password='password')
        response = self.client.get('/investing/managed/accounts/create/')
        self.assertEqual(response.status_code, 200)
    
    def test_create_account_post_valid_data(self):
        self.client.login(username='staff_user', password='password')
        data = {
            'client': self.investor.id,
            'account_name': 'Test Account',
            'initial_capital': '10000.00',
            # ... other fields
        }
        response = self.client.post('/investing/managed/accounts/create/', data)
        self.assertEqual(response.status_code, 302)  # Redirect on success
        self.assertTrue(ManagedTradingAccount.objects.filter(account_name='Test Account').exists())
```

**Human Responsibility:** 
- ⚠️ Verify complex workflows manually
- ⚠️ Test JavaScript-heavy interactions
- ⚠️ Test file upload edge cases

---

### 03_PERFORMANCE (Partially Automatable) 🤖➕👤

**Purpose:** Test system performance and scalability

**What to Test:**
- Query performance (N+1 queries)
- Page load times
- Database indexing effectiveness
- Memory usage
- API response times

**Cursor Can Create:**
- ✅ Query count tests (django.test.utils.override_settings)
- ✅ Database query logging
- ✅ Basic performance benchmarks
- ✅ Indexing tests

**Cursor CANNOT Test:**
- ❌ Production load testing (requires production environment)
- ❌ Stress testing (requires load generation tools)
- ❌ Real-world performance (requires real data volume)

**Example:**
```python
# tests/investing/03_performance/test_query_performance.py
from django.test import TestCase
from django.test.utils import override_settings
from django.db import connection
from django.test.utils import CaptureQueriesContext

class AccountListPerformanceTest(TestCase):
    def test_account_list_query_count(self):
        """Ensure account list view doesn't have N+1 query issues"""
        # Create 20 accounts
        for i in range(20):
            ManagedTradingAccount.objects.create(...)
        
        with CaptureQueriesContext(connection) as context:
            response = self.client.get('/investing/managed/accounts/')
            # Should be ~3 queries: 1 for accounts, 1 for related clients, 1 for session
            self.assertLess(len(context.captured_queries), 5)
```

**Human Responsibility:**
- 👤 **REQUIRED:** Load testing on production/UAT with real data
- 👤 **REQUIRED:** Stress testing with many concurrent users
- 👤 **REQUIRED:** Performance regression testing (before/after comparisons)
- 👤 **REQUIRED:** Real-world performance validation

---

### 04_REGRESSION (Automatable by Cursor) 🤖

**Purpose:** Prevent previously fixed bugs from reappearing

**What to Test:**
- Known bug fixes
- Edge cases that caused issues
- Critical bugs that were fixed

**Cursor Can Create:**
- ✅ Tests for every bug fix
- ✅ Regression test suite
- ✅ Critical path tests

**Example:**
```python
# tests/investing/04_regression/test_critical_bugs.py
class ManagedAccountBugRegressionTest(TestCase):
    def test_none_values_in_buying_power_calculation(self):
        """
        Regression test for TypeError bug fixed on Nov 5, 2025
        Bug: unsupported operand type(s) for -: 'NoneType' and 'decimal.Decimal'
        URL: /admin/investing/managedtradingaccount/add/
        """
        account = ManagedTradingAccount(
            cash_available=None,
            cash_reserved=None
        )
        # Should not raise TypeError
        result = account.available_buying_power
        self.assertEqual(result, Decimal('0.00'))
```

**Human Responsibility:** NONE (Cursor creates all regression tests)

---

### 05_SYSTEM (Mostly Manual) 👤➕🤖

**Purpose:** Test complete system workflows end-to-end

**What to Test:**
- Complete user journeys
- Multi-page workflows
- Cross-app interactions
- Real-world scenarios

**Cursor Can Create:**
- ✅ Basic end-to-end tests (simple flows)
- ✅ Multi-step workflows (programmatic)
- ✅ Database state verification

**Cursor CANNOT Test:**
- ❌ Complex UI interactions
- ❌ Real user behavior
- ❌ Multi-device testing
- ❌ Browser-specific issues

**Example (Automated Part):**
```python
# tests/investing/05_system/test_end_to_end.py
class ManagedAccountOnboardingFlowTest(TestCase):
    def test_complete_onboarding_workflow(self):
        """Test full onboarding: application → approval → account creation"""
        # Step 1: User submits application
        application = ManagedTradingApplication.objects.create(...)
        
        # Step 2: Staff reviews and approves
        application.status = 'approved'
        application.save()
        
        # Step 3: Account is created
        account = ManagedTradingAccount.objects.create(
            client=application.user,
            initial_capital=application.initial_capital,
            # ...
        )
        
        # Verify complete flow
        self.assertEqual(account.status, 'active')
        self.assertEqual(account.client, application.user)
```

**Human Responsibility:**
- 👤 **REQUIRED:** Manual testing of complete user flows
- 👤 **REQUIRED:** Testing with real browser (Chrome, Safari, Firefox)
- 👤 **REQUIRED:** Mobile device testing
- 👤 **REQUIRED:** Cross-browser compatibility
- 👤 **REQUIRED:** Accessibility testing

---

### 06_SECURITY (Partially Automatable) 🤖➕👤

**Purpose:** Test security controls and data protection

**What to Test:**
- Authentication
- Authorization
- Data validation
- SQL injection prevention
- XSS prevention
- CSRF protection

**Cursor Can Create:**
- ✅ Permission tests (user can/cannot access)
- ✅ Authentication tests (login required)
- ✅ Authorization tests (role-based access)
- ✅ Input validation tests
- ✅ CSRF token tests

**Cursor CANNOT Test:**
- ❌ Real penetration testing
- ❌ Security audits
- ❌ Vulnerability scanning

**Example:**
```python
# tests/investing/06_security/test_authorization.py
class ManagedAccountAuthorizationTest(TestCase):
    def test_investor_cannot_access_staff_dashboard(self):
        """Investors should not access staff-only pages"""
        investor = User.objects.create_user(
            username='investor',
            category=UserCategory.INVESTOR
        )
        self.client.login(username='investor', password='password')
        
        response = self.client.get('/investing/managed/staff/dashboard/')
        self.assertEqual(response.status_code, 403)  # Forbidden
    
    def test_staff_can_access_all_accounts(self):
        """Staff should access all managed accounts"""
        staff = User.objects.create_user(
            username='staff',
            is_staff=True
        )
        self.client.login(username='staff', password='password')
        
        response = self.client.get('/investing/managed/staff/dashboard/')
        self.assertEqual(response.status_code, 200)
```

**Human Responsibility:**
- 👤 **REQUIRED:** Manual penetration testing
- 👤 **REQUIRED:** Security audit reviews
- 👤 **REQUIRED:** OWASP Top 10 vulnerability checks
- 👤 **REQUIRED:** Production security scans

---

### 07_MANUAL (100% Human) 👤

**Purpose:** Tests that cannot be automated

**What to Test:**
- UI/UX validation
- Visual regression
- User experience flows
- Edge cases requiring human judgment
- Accessibility
- Mobile responsiveness

**Cursor CANNOT Create:**
- ❌ Visual appearance tests
- ❌ UX flow validation
- ❌ Accessibility testing
- ❌ Real user behavior simulation
- ❌ Subjective quality assessment

**Format:** Markdown checklists and test plans

**Example:**
```markdown
# tests/investing/07_manual/MANUAL_TEST_PLAN.md

## Managed Account Creation Flow

### Pre-Conditions
- Logged in as staff user
- At least 1 active investor exists

### Test Steps
1. [ ] Navigate to /investing/managed/accounts/create/
2. [ ] Verify form loads correctly
3. [ ] Open "Client" dropdown
4. [ ] ✅ Verify ONLY active investors shown (not students/applicants)
5. [ ] ✅ Verify count: 10-20 users (not 100+)
6. [ ] Open "Account Manager" dropdown
7. [ ] ✅ Verify ONLY active staff shown
8. [ ] Fill in all required fields
9. [ ] Submit form
10. [ ] ✅ Verify redirect to account detail page
11. [ ] ✅ Verify account created in database
12. [ ] ✅ Verify account appears in accounts list

### Expected Results
- Client dropdown: 10-20 active investors only
- Account Manager dropdown: 10-20 active staff only
- Form submission: Success with redirect
- Account created: Visible in list and admin

### Actual Results
- Date: ___________
- Tester: ___________
- Status: PASS / FAIL
- Notes: ___________
```

**Human Responsibility:**
- 👤 **REQUIRED:** Execute all manual test plans
- 👤 **REQUIRED:** Document test results
- 👤 **REQUIRED:** Screenshot critical issues
- 👤 **REQUIRED:** Verify UI appearance
- 👤 **REQUIRED:** Test on real devices

---

## Cursor AI Capabilities vs Human Requirements

### ✅ What Cursor CAN Do (Automated)

#### Unit Tests (01_unit)
- ✅ Model method tests
- ✅ Service logic tests
- ✅ Form validation tests
- ✅ Utility function tests
- ✅ Property/method tests
- ✅ Edge case tests

#### Integration Tests (02_integration)
- ✅ View function tests (GET/POST)
- ✅ URL routing tests
- ✅ Template rendering tests (basic)
- ✅ Form submission tests
- ✅ Database transaction tests
- ✅ Service integration tests

#### Performance Tests (03_performance)
- ✅ Query count tests (N+1 detection)
- ✅ Database indexing tests
- ✅ Basic benchmarks
- ✅ Response time assertions

#### Regression Tests (04_regression)
- ✅ Bug fix validation
- ✅ Known issue prevention
- ✅ Critical path tests

#### Security Tests (06_security)
- ✅ Permission tests
- ✅ Authentication tests
- ✅ Authorization tests
- ✅ Input validation tests
- ✅ CSRF protection tests

**Total Automation:** ~70% of all tests

---

### ❌ What Cursor CANNOT Do (Requires Human)

#### System Tests (05_system)
- ❌ Real browser interactions (Selenium/Playwright needed)
- ❌ JavaScript execution testing
- ❌ AJAX/async behavior
- ❌ Complex multi-page workflows
- ❌ Third-party service integration (real APIs)

#### Performance Tests (03_performance)
- ❌ Load testing (requires load generation tools)
- ❌ Stress testing (requires production-like environment)
- ❌ Real-world performance validation
- ❌ Concurrent user testing

#### Security Tests (06_security)
- ❌ Penetration testing
- ❌ Vulnerability scanning
- ❌ Security audits
- ❌ OWASP Top 10 validation

#### Manual Tests (07_manual)
- ❌ Visual regression testing
- ❌ UI/UX validation
- ❌ Cross-browser testing
- ❌ Mobile device testing
- ❌ Accessibility testing (WCAG compliance)
- ❌ User experience flows
- ❌ Real user behavior simulation

**Total Manual Testing:** ~30% of all tests

---

## Standard Test File Naming

### Pattern
`test_{component}_{specific_feature}.py`

### Examples
- `test_models_managed_account.py` - ManagedTradingAccount model
- `test_services_position_ranking.py` - PositionRankingService
- `test_forms_account_creation.py` - ManagedAccountForm
- `test_views_account_list.py` - Account list view
- `test_api_position_endpoints.py` - Position API endpoints

### Bad Examples (Don't Use)
- ❌ `test1.py` - Not descriptive
- ❌ `my_test.py` - Too vague
- ❌ `test_everything.py` - Too broad
- ❌ `testing_stuff.py` - Not following convention

---

## Test Writing Standards

### 1. Test Method Naming

**Pattern:** `test_{what}_{condition}_{expected}`

**Good Examples:**
```python
def test_buying_power_with_none_values_returns_zero(self):
def test_form_validation_rejects_capital_below_minimum(self):
def test_investor_filter_excludes_inactive_users(self):
def test_staff_dashboard_requires_staff_permission(self):
```

**Bad Examples:**
```python
def test_it_works(self):  # Too vague
def test_account(self):  # Not specific
def test1(self):  # Meaningless
```

### 2. Test Structure (AAA Pattern)

```python
def test_something(self):
    # ARRANGE - Set up test data
    account = ManagedTradingAccount.objects.create(...)
    
    # ACT - Perform the action being tested
    result = account.available_buying_power
    
    # ASSERT - Verify the expected outcome
    self.assertEqual(result, Decimal('8000.00'))
```

### 3. Test Documentation

Every test should have a docstring explaining:
- What is being tested
- Why it's important
- What bug it prevents (for regression tests)

```python
def test_user_filter_shows_only_active_investors(self):
    """
    Test that ManagedAccountForm filters client field to active investors only.
    
    This prevents the dropdown from showing 100+ users including students,
    applicants, and inactive users.
    
    Regression: User reported seeing all users in dropdown (Nov 5, 2025)
    Fix: Added user_querysets.get_active_investors_queryset()
    """
    # ... test code
```

---

## Cursor vs Human Workflow

### When Creating a New Feature

**Step 1: Development (Cursor)**
1. Cursor implements feature code
2. Cursor writes unit tests (01_unit)
3. Cursor writes integration tests (02_integration)
4. Cursor writes regression tests (04_regression)
5. Cursor runs tests locally
6. Cursor fixes any test failures

**Step 2: Code Review (Human)**
1. Human reviews code changes
2. Human reviews test coverage
3. Human approves or requests changes

**Step 3: Manual Testing (Human)**
1. Human creates manual test plan (07_manual/MANUAL_TEST_PLAN.md)
2. Human executes manual tests on UAT
3. Human documents results
4. Human approves for production OR reports issues

**Step 4: Deployment (Cursor + Human)**
1. Cursor deploys to UAT
2. Human tests on UAT (manual test plan)
3. Human approves deployment
4. Cursor deploys to Production
5. Human verifies on Production

**Step 5: Production Validation (Human)**
1. Human performs smoke tests
2. Human monitors logs
3. Human validates with real users
4. Human approves or initiates rollback

---

## Test Coverage Requirements

### Minimum Coverage by Test Type

| Test Type | Target Coverage | Who Creates | Who Executes |
|-----------|----------------|-------------|--------------|
| Unit | 80%+ | Cursor 🤖 | Cursor 🤖 |
| Integration | 60%+ | Cursor 🤖 | Cursor 🤖 |
| Performance | 20%+ | Cursor 🤖 | Both 🤖👤 |
| Regression | 100% of bugs | Cursor 🤖 | Cursor 🤖 |
| System | 50%+ | Cursor 🤖 | Human 👤 |
| Security | 80%+ | Cursor 🤖 | Both 🤖👤 |
| Manual | 100% critical flows | Human 👤 | Human 👤 |

### Critical Flows (Must Have Manual Tests)

Every app should have manual test plans for:
1. User registration/login
2. Main feature workflow (e.g., create account → add position → close position)
3. Admin operations (create, edit, delete)
4. Edge cases (error handling, validation)
5. Security scenarios (unauthorized access, data protection)

---

## Test Execution

### Local Development (Cursor)

```bash
# Run all tests for an app
python coda/manage.py test investing --settings=coda_project.coda_settings.local_settings

# Run specific test category
python coda/manage.py test investing.01_unit --settings=coda_project.coda_settings.local_settings

# Run specific test file
python coda/manage.py test investing.01_unit.test_models --settings=coda_project.coda_settings.local_settings

# Run with coverage
coverage run --source='investing' coda/manage.py test investing --settings=coda_project.coda_settings.local_settings
coverage report
```

### UAT Testing (Human)

**Before Deployment:**
1. Cursor runs automated tests locally
2. Cursor deploys to UAT
3. Human executes manual test plan
4. Human documents results in `test_results/YYYY-MM-DD_test_session.md`
5. Human approves or rejects for production

### Production Testing (Human)

**After Deployment:**
1. Human performs smoke tests (critical paths only)
2. Human monitors error logs
3. Human validates key functionality
4. Human approves deployment OR initiates rollback

---

## Manual Test Plan Template

### File: `tests/{app_name}/07_manual/MANUAL_TEST_PLAN.md`

```markdown
# {Feature Name} - Manual Test Plan

**Version:** 1.0  
**Created:** YYYY-MM-DD  
**Last Updated:** YYYY-MM-DD

## Test Overview
Brief description of what's being tested

## Pre-Conditions
- User must be logged in as [role]
- System must have [data/state]
- Environment: UAT / Production

## Test Cases

### TC-001: {Test Case Name}
**Priority:** High / Medium / Low  
**Type:** Functional / UI / UX / Security

**Steps:**
1. [ ] Navigate to [URL]
2. [ ] Click on [element]
3. [ ] Fill in [field] with [value]
4. [ ] Click [button]

**Expected Results:**
- Field shows [expected value]
- Page redirects to [URL]
- Database updated with [data]

**Actual Results:**
- Date: ___________
- Tester: ___________
- Status: PASS / FAIL
- Screenshots: [link]
- Notes: ___________

---

### TC-002: {Next Test Case}
...
```

---

## Responsibilities Matrix

### Clear Division of Labor

| Task | Cursor 🤖 | Human 👤 | Notes |
|------|----------|---------|-------|
| Write unit tests | ✅ Primary | Review | Cursor writes, human reviews |
| Write integration tests | ✅ Primary | Review | Cursor writes, human reviews |
| Write performance tests | ✅ Basic | ✅ Advanced | Cursor writes basic, human does load testing |
| Write regression tests | ✅ Always | Review | Cursor writes for every bug fix |
| Write system tests | ✅ Basic | ✅ Advanced | Cursor writes programmatic, human does browser testing |
| Write security tests | ✅ Primary | ✅ Audit | Cursor writes permission tests, human does security audits |
| Create manual test plans | ❌ Never | ✅ Always | Human creates all manual test plans |
| Execute automated tests | ✅ Always | Optional | Cursor runs all automated tests |
| Execute manual tests | ❌ Never | ✅ Always | Only human can execute manual tests |
| Review test results | ❌ Never | ✅ Always | Human reviews and approves |
| Approve for UAT | ❌ Never | ✅ Always | Human decision |
| Approve for Production | ❌ Never | ✅ Always | Human decision |

---

## When to Create Tests

### ✅ ALWAYS (Cursor Creates Automatically)

1. **New Model Created** → Create unit tests for:
   - Model creation
   - Field validation
   - Model methods
   - Model properties
   - String representation

2. **New Service Created** → Create unit tests for:
   - All public methods
   - Business logic
   - Calculations
   - Edge cases

3. **New Form Created** → Create unit tests for:
   - Form validation
   - Clean methods
   - Field filtering
   - Error messages

4. **New View Created** → Create integration tests for:
   - GET request
   - POST request (valid data)
   - POST request (invalid data)
   - Permission requirements

5. **Bug Fixed** → Create regression test:
   - Reproduce the bug
   - Verify the fix
   - Prevent recurrence

### ⚠️ SOMETIMES (Cursor Creates on Request)

1. **Performance Optimization** → Create performance tests
2. **Security Enhancement** → Create security tests
3. **Complex Workflow** → Create system tests (basic)

### ❌ NEVER (Human Creates)

1. **Manual Test Plans** → Always created by human
2. **Browser-Based Tests** → Require Selenium/Playwright (human decision)
3. **Load/Stress Tests** → Require external tools (human decision)
4. **Security Audits** → Require penetration testing expertise

---

## Test Failure Protocol

### When Automated Tests Fail

**Cursor Handles:**
1. Cursor runs tests before deployment
2. If tests fail, Cursor identifies the failure
3. Cursor fixes the code OR test (if test is wrong)
4. Cursor re-runs tests
5. Cursor continues only when ALL tests pass

**Human Never Approves Deployment with Failing Tests**

### When Manual Tests Fail

**Human Handles:**
1. Human executes manual test plan
2. If test fails, human documents:
   - What failed
   - Steps to reproduce
   - Screenshots
   - Expected vs actual
3. Human reports to Cursor for fix
4. Cursor fixes the issue
5. Cursor deploys to UAT
6. Human re-tests
7. Repeat until all tests pass

---

## Testing Checklist (Per Deployment)

### Before Deploying to UAT

**Cursor Responsibilities:**
- [x] All unit tests pass (01_unit)
- [x] All integration tests pass (02_integration)
- [x] All regression tests pass (04_regression)
- [x] Code coverage meets minimum (80% for new code)
- [x] No linter errors
- [x] All migrations created
- [x] Documentation updated

**Human Responsibilities:**
- [ ] Code review completed
- [ ] Test coverage reviewed and approved
- [ ] Manual test plan created (07_manual)

### Before Deploying to Production

**Cursor Responsibilities:**
- [x] All automated tests pass on UAT
- [x] No errors in UAT logs
- [x] Performance tests pass (if applicable)

**Human Responsibilities:**
- [ ] Manual test plan executed on UAT
- [ ] All manual tests PASS
- [ ] UI/UX verified
- [ ] Cross-browser tested (if UI changes)
- [ ] Mobile tested (if UI changes)
- [ ] Security validated (if security changes)
- [ ] Stakeholder approval obtained

### After Production Deployment

**Human Responsibilities:**
- [ ] Smoke tests completed
- [ ] Critical paths verified
- [ ] Error logs monitored (first 30 minutes)
- [ ] Real user feedback gathered
- [ ] Deployment documented

---

## Example: Complete Test Coverage for a Feature

### Feature: User Filtering System (Phase 1 - Investing)

#### Automated Tests (Cursor Creates) 🤖

**01_unit/test_user_querysets.py**
```python
class UserQuerysetTests(TestCase):
    def test_get_active_investors_excludes_inactive(self):
        # Create active investor
        active = User.objects.create(category=4, is_active=True)
        # Create inactive investor
        inactive = User.objects.create(category=4, is_active=False)
        
        result = get_active_investors_queryset()
        
        self.assertIn(active, result)
        self.assertNotIn(inactive, result)
    
    def test_get_active_staff_excludes_non_staff(self):
        # Create staff
        staff = User.objects.create(is_staff=True, is_active=True)
        # Create non-staff
        investor = User.objects.create(category=4, is_active=True)
        
        result = get_active_staff_queryset()
        
        self.assertIn(staff, result)
        self.assertNotIn(investor, result)
```

**02_integration/test_forms_account_creation.py**
```python
class ManagedAccountFormTest(TestCase):
    def test_client_field_queryset_filtered(self):
        # Create users of different categories
        investor = User.objects.create(category=4, is_active=True)
        student = User.objects.create(category=2, is_active=True)
        
        form = ManagedAccountForm()
        
        # Client field should only show investors
        self.assertIn(investor, form.fields['client'].queryset)
        self.assertNotIn(student, form.fields['client'].queryset)
```

#### Manual Tests (Human Creates & Executes) 👤

**07_manual/USER_FILTERING_TEST_PLAN.md**
```markdown
## TC-001: Verify Client Dropdown Filtering

**Priority:** HIGH  
**Type:** UI/UX

**Pre-Conditions:**
- 10 active investors
- 20 active students
- 15 inactive users
- Total: 100+ users in database

**Steps:**
1. [ ] Login as staff user
2. [ ] Navigate to /investing/managed/accounts/create/
3. [ ] Open "Client" dropdown
4. [ ] Count visible options
5. [ ] Verify user categories shown

**Expected Results:**
- Dropdown shows ~10 users (active investors only)
- NO students visible
- NO inactive users visible
- NO applicants visible
- Dropdown label: "--- Select Client (Investor) ---"

**Actual Results:**
- Date: November 5, 2025
- Tester: [Your Name]
- Count: _____ users (expected: ~10)
- Categories: _____ (expected: investors only)
- Status: PASS / FAIL
- Screenshot: [attach]
```

---

## Standard Test Data (Fixtures)

### Create Reusable Fixtures

**File:** `tests/{app_name}/fixtures/users.json`

```json
[
  {
    "model": "accounts.customeruser",
    "pk": 1,
    "fields": {
      "username": "test_investor",
      "category": 4,
      "is_active": true,
      "email": "investor@test.com"
    }
  },
  {
    "model": "accounts.customeruser",
    "pk": 2,
    "fields": {
      "username": "test_staff",
      "is_staff": true,
      "is_active": true,
      "email": "staff@test.com"
    }
  }
]
```

**Usage in Tests:**
```python
class MyTestCase(TestCase):
    fixtures = ['users.json', 'accounts.json']
    
    def test_something(self):
        investor = User.objects.get(pk=1)
        # ... test code
```

---

## Continuous Integration (Future)

### GitHub Actions / CI/CD

**Automated on Every Push:**
1. Run linter (flake8, black)
2. Run all unit tests
3. Run all integration tests
4. Check code coverage
5. Report results

**Manual Gate:**
- Human must approve deployment to production
- Manual test plan must be completed
- Test results must be documented

---

## Documentation Requirements

### For Every Feature

When creating a new feature, Cursor should:

1. **Write Code** ✅
2. **Write Automated Tests** ✅
   - Unit tests (01_unit)
   - Integration tests (02_integration)
   - Regression tests (04_regression)
3. **Create Manual Test Plan Template** ✅
   - File: `tests/{app}/07_manual/{feature}_TEST_PLAN.md`
   - Checklist format
   - Clear expected results
4. **Update Documentation** ✅
   - Feature documentation (7-doc structure)
   - Test coverage in 05_TESTING.md
   - Deployment notes in 07_DEPLOYMENT.md

Then human:
1. **Reviews** code and tests
2. **Executes** manual test plan
3. **Documents** results
4. **Approves** for deployment

---

## Best Practices

### DO ✅

1. **Test Early** - Write tests alongside code, not after
2. **Test Often** - Run tests before every commit
3. **Test Thoroughly** - Aim for 80%+ coverage
4. **Test Edge Cases** - None values, empty strings, boundary conditions
5. **Test Failures** - Test that errors are handled correctly
6. **Document Tests** - Every test has a docstring
7. **Use Fixtures** - Reuse test data across tests
8. **Isolate Tests** - Each test is independent
9. **Keep Tests Fast** - Unit tests should run in milliseconds
10. **Update Tests** - When code changes, update tests

### DON'T ❌

1. **Don't Skip Tests** - Never deploy untested code
2. **Don't Test Implementation** - Test behavior, not internal details
3. **Don't Test Framework** - Don't test Django's built-in functionality
4. **Don't Write Brittle Tests** - Tests should not break on minor UI changes
5. **Don't Ignore Failures** - Fix failing tests immediately
6. **Don't Commit Commented Tests** - Either fix or delete
7. **Don't Duplicate Tests** - Use parameterized tests for similar cases
8. **Don't Mock Everything** - Use real database for integration tests
9. **Don't Test External APIs** - Mock external services
10. **Don't Assume Data Exists** - Create all test data in setUp()

---

## Migration Guide: Reorganizing Existing Tests

### Current State
```
tests/
├── test_budget_workflow.py
├── test_ui_workflows.py
├── test_task_reset_manual.py
└── finance/
    ├── test_all_finance_urls.py
    └── test_payment_control.py
```

### Target State
```
tests/
├── investing/
│   ├── 01_unit/
│   ├── 02_integration/
│   ├── 07_manual/
│   └── README.md
├── finance/
│   ├── 01_unit/
│   ├── 02_integration/
│   ├── 07_manual/
│   └── README.md
└── README.md
```

### Migration Steps

1. **Create app-specific folders**
   ```bash
   mkdir -p tests/finance/01_unit
   mkdir -p tests/finance/02_integration
   mkdir -p tests/finance/07_manual
   ```

2. **Move existing tests**
   ```bash
   mv tests/finance/test_payment_control.py tests/finance/02_integration/
   mv tests/finance/test_all_finance_urls.py tests/finance/02_integration/
   ```

3. **Create README**
   - Document test organization
   - Link to this standards document

4. **Create manual test plans**
   - Convert manual testing notes to structured plans
   - Add to 07_manual/ folder

---

## Quick Reference

### For Cursor AI

**When implementing a feature:**
1. Write the feature code
2. Write unit tests (models, services, forms)
3. Write integration tests (views, URLs)
4. Write regression tests (for bugs fixed)
5. Run all tests locally
6. Ensure all tests pass
7. Create manual test plan template
8. Update documentation

**DO NOT:**
- Deploy with failing tests
- Skip test creation
- Write tests that require browser interaction
- Approve deployment to production

### For Human Developers

**Before approving deployment:**
1. Review code changes
2. Review test coverage
3. Execute manual test plan on UAT
4. Document test results
5. Verify UI/UX
6. Check error logs
7. Approve OR reject

**DO NOT:**
- Approve deployment without manual testing
- Skip manual test plan
- Assume automated tests are sufficient
- Deploy to production without UAT validation

---

## Examples by App

### Investing App Testing

**01_unit/**
- `test_models_managed_account.py` - ManagedTradingAccount model
- `test_services_trading.py` - ManagedTradingService
- `test_forms_account.py` - ManagedAccountForm
- `test_user_querysets.py` - User filtering functions

**02_integration/**
- `test_views_accounts.py` - Account CRUD views
- `test_views_positions.py` - Position management views
- `test_api_endpoints.py` - API endpoints

**07_manual/**
- `ACCOUNT_CREATION_TEST_PLAN.md` - Manual testing checklist
- `USER_FILTERING_TEST_PLAN.md` - Dropdown filtering validation

### Finance App Testing

**01_unit/**
- `test_models_budget.py` - Budget models
- `test_services_approval.py` - SmartApprovalService
- `test_forms_budget_request.py` - BudgetRequestForm

**02_integration/**
- `test_views_budget_workflow.py` - Budget request workflow
- `test_payment_processing.py` - Payment integration

**07_manual/**
- `BUDGET_APPROVAL_FLOW.md` - Complete approval workflow
- `TIER_MANAGEMENT_TEST_PLAN.md` - Tier control testing

---

## Success Metrics

### Code Quality
- ✅ 80%+ test coverage for new code
- ✅ All tests pass before deployment
- ✅ No linter errors
- ✅ All regression tests exist for known bugs

### Process Quality
- ✅ Manual test plan exists for every feature
- ✅ Manual tests executed on UAT before production
- ✅ Test results documented
- ✅ No production bugs from untested code

### Documentation Quality
- ✅ All test files follow naming convention
- ✅ All tests have docstrings
- ✅ README exists for each app's tests
- ✅ Manual test plans are up-to-date

---

## Conclusion

This testing standard ensures:

1. **Clear Responsibilities** - Cursor does automated, human does manual
2. **High Quality** - 80%+ coverage with both automated and manual
3. **Fast Feedback** - Automated tests catch most issues
4. **User Validation** - Manual tests ensure real-world usability
5. **No Surprises** - Comprehensive testing before production

**Key Principle:**  
Cursor writes code and tests. Human validates and approves.

---

**Document Created:** November 5, 2025  
**Last Updated:** November 5, 2025  
**Status:** ✅ ACTIVE STANDARD  
**Next Review:** December 2025

