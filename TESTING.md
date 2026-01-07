# Comprehensive Testing Guide

This project includes a suite of automated tests to ensure the stability and functionality of critical features, particularly the new **Dynamic Services** and **Expert Request** workflows.

## 🧪 Test Suite Overview

The primary test suite is located in the `main/test/` directory, organized by test type:

- `main/test/unit/`: Model logic and core unit checks.
- `main/test/intergration/`: View rendering and AJAX workflow integration.
- `main/test/regression/`: Smoke tests for critical site paths.
- `main/test/performance/`: Database query optimization checks.

It encompasses the following levels of testing:

| Test Type | Scope | Description |
|-----------|-------|-------------|
| **Unit** | Models | Verifies `Service`, `SubService`, `ExpertServiceRequest` creation and constraints. |
| **Integration** | Views & Forms | Tests the `contact_expert` AJAX flow and `our_service` page rendering. |
| **Regression** | Critical Paths | Smoke tests for Home, Crisis, and Document Service pages to prevent regressions. |
| **Performance** | DB Optimization | Verifies efficient query usage (e.g., `prefetch_related`) on the dynamic services loop. |

---

## 🚀 How to Run Tests

### Run the Comprehensive Suite
To run only the new comprehensive tests (Recommended):
```bash
python manage.py test main.tests.test_comprehensive_suite
```

### Run All Tests
To run the full project test suite (including legacy tests):
```bash
python manage.py test
```
*Note: Some legacy tests in `main/tests/unit/` relating to Scholarships may fail due to pre-existing schema issues. The comprehensive suite above focuses on active development.*

---

## 🔍 Test Scenarios Covered

### 1. Dynamic Services (Frontend & Admin)
- **Model**: Verifies that `Service` objects are correctly linked to `SubService` (bullet points).
- **View**: Ensures the `our_service` view loads correctly and passes the `services` context.
- **Performance**: Checks that the page load does not trigger N+1 database queries when looping through services and bullet points.

### 2. Expert Service Requests (Backend Persistence)
- **Persistence**: Verifies that submitting the "Contact Our Experts" form (via AJAX) creates a saved `ExpertServiceRequest` record in the database.
- **API Response**: Checks that the server returns a valid JSON `200 OK` response upon success.

### 3. Critical Page Availability
- **Smoke Tests**: Automates visiting the following URLs to ensure they return HTTP 200:
  - Homepage (`/`)
  - Crisis Management (`/crisis/`)
  - Document Services (`/services/document-services/`)

---

## 🛠 Troubleshooting

**Error: "Missing staticfiles manifest entry"**
- The test settings have been configured to automatically switch `STATICFILES_STORAGE` to the default storage during testing.
- If you see this error, ensure your `settings.py` includes the test override block at the end of the file.

**Error: "NameError: ExpertServiceRequest"**
- Ensure `main/views.py` imports `ExpertServiceRequest` from `main.models`.
