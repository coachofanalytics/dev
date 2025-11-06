# Finance App Tests

## Test Organization

### 01_unit/
Unit tests for finance models, services, and forms.

### 02_integration/
Integration tests for finance views, workflows, and API.

**Current Tests:**
- `test_payment_control.py` - Payment processing tests
- `test_all_finance_urls.py` - URL resolution tests
- `test_budget_workflow.py` - Budget request workflow tests

### 03_performance/
Performance and load testing.

### 04_regression/
Regression tests for known bugs.

### 05_system/
End-to-end system tests.

### 06_security/
Security and authorization tests.

### 07_manual/
Manual test plans and checklists.

## Running Tests

```bash
# All finance tests
python coda/manage.py test finance --settings=coda_project.coda_settings.local_settings

# Specific category
python coda/manage.py test finance.01_unit --settings=coda_project.coda_settings.local_settings

# With coverage
coverage run --source='coda/finance' coda/manage.py test finance
coverage report
```

---
*See: [Testing Standards](../docs/TESTING_STANDARDS_AND_STRUCTURE.md)*
