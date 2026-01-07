# Document Request Feature - Test Report

## 1. Introduction
This report documents the testing strategy, implementation, and results for the newly implemented Document Request feature. The testing suite covers Unit, Regression, and Performance aspects to ensure reliability, correctness, and efficiency.

**Target Features:**
- `DocumentRequest` Model
- `DocumentRequestForm`
- `services_spa` View (SPA Page)
- `submit_request` View (API Endpoint)

---

## 2. Test Suite Breakdown

### A. Unit Tests
**File:** `main/tests/unit/test_document_request_unit.py`

*   **Model Testing (`DocumentRequestModelTest`)**:
    *   Verified creation of `DocumentRequest` instances.
    *   Validated default values (e.g., `status='Pending'`).
    *   Checked string representation (`__str__`).
*   **Form Testing (`DocumentRequestFormTest`)**:
    *   **Valid Case**: Confirmed the form accepts correct data dictionaries.
    *   **Invalid Case (Missing Consent)**: Ensured the form fails effectively when the mandatory 'consent' checkbox is unchecked.
    *   **Invalid Case (Empty Data)**: validated required field enforcement.

### B. Regression Tests
**File:** `main/tests/regression/test_document_request_regression.py`

These tests ensure that the views return the correct status codes and JSON structures, preventing future code changes from breaking existing functionality.

*   **SPA View (`test_services_spa_view_status_code`)**:
    *   Verified `services_spa` returns **HTTP 200**.
    *   Confirmed the correct template (`main/index.html`) is used.
    *   Ensured the `form` context variable is present.
*   **API Submission - Valid (`test_submit_request_valid_post`)**:
    *   Simulated a POST request with valid data.
    *   Verified **HTTP 200** response.
    *   Checked for `success: True` in the JSON response.
    *   Confirmed data persistence in the database.
*   **API Submission - Invalid (`test_submit_request_invalid_post`)**:
    *   Simulated a POST request with missing fields (Consent).
    *   Verified **HTTP 400** response.
    *   Checked for `success: False` and error details in the JSON response.
    *   Confirmed no data was saved to the database.

### C. Performance Tests
**File:** `main/tests/performance/test_document_request_performance.py`

*   **Response Time Checks**:
    *   Measured the execution time for rendering the `services_spa` page.
    *   Measured the execution time for processing `submit_request`.
    *   **Threshold**: Asserted that responses occur within **1.0 second** (safe upper bound for test environments; actual performance is typically much faster).

---

## 3. Execution Results
**Date:** 2026-01-07
**Status:** ✅ Passed

The test suite was executed successfully using the Django test runner.

```text
Found 10 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
..........
----------------------------------------------------------------------      
Ran 10 tests in 0.500s

OK
Destroying test database for alias 'default'...
```

**Summary:**
- **Total Tests:** 10
- **Passed:** 10
- **Failed:** 0

---

## 4. How to Run Tests
To execute these specific tests again, ensure your virtual environment is active and run:

```bash
python manage.py test main.tests.unit.test_document_request_unit main.tests.regression.test_document_request_regression main.tests.performance.test_document_request_performance
```
