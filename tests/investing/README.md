# Investing App Tests

## Test Organization

### 01_unit/
Unit tests for investing models, services, and forms.

**To Create:**
- `test_models_managed_account.py` - ManagedTradingAccount model tests
- `test_services_trading.py` - ManagedTradingService tests
- `test_forms_account.py` - ManagedAccountForm tests
- `test_user_querysets.py` - User filtering tests

### 02_integration/
Integration tests for investing views, workflows, and API.

**To Create:**
- `test_views_accounts.py` - Account CRUD views
- `test_views_positions.py` - Position management views
- `test_api_endpoints.py` - API endpoints

### 03_performance/
Performance and load testing.

### 04_regression/
Regression tests for known bugs.

**To Create:**
- `test_none_value_bug.py` - TypeError bug (Nov 5, 2025)
- `test_user_filtering_bug.py` - User dropdown bug (Nov 5, 2025)

### 05_system/
End-to-end system tests.

### 06_security/
Security and authorization tests.

### 07_manual/
Manual test plans and checklists.

**To Create:**
- `ACCOUNT_CREATION_TEST_PLAN.md` - Account creation flow
- `USER_FILTERING_TEST_PLAN.md` - User dropdown validation
- `POSITION_MANAGEMENT_TEST_PLAN.md` - Position workflow

## Running Tests

```bash
# All investing tests
python coda/manage.py test investing --settings=coda_project.coda_settings.local_settings

# Specific category
python coda/manage.py test investing.01_unit --settings=coda_project.coda_settings.local_settings
```

---
*See: [Testing Standards](../docs/TESTING_STANDARDS_AND_STRUCTURE.md)*
