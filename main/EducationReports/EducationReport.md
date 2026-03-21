# EducationTest — General Report

- **Author:** Serge
- **Date:** 2026-03-21

## Summary

This report summarizes the `main/tests/educationTest` test tree (unit, integration, performance, regression, system) after recreation and execution.

All tests under `main/tests/educationTest` completed successfully during verification.

## Results (by folder)

- `unit`: 2 passed
- `integration`: 1 passed
- `performance`: 1 passed
- `regression`: 2 passed
- `system`: 2 passed

**Total:** 8 passed, 0 failed

## Files added/modified during work

- Added tests:
  - `main/tests/educationTest/unit/test_unit_models.py`
  - `main/tests/educationTest/integration/test_integration_models.py`
  - `main/tests/educationTest/performance/test_performance_models.py`
  - `main/tests/educationTest/regression/test_regression_models.py`
  - `main/tests/educationTest/system/test_system_models.py` (unchanged if already present)

- Template/URL fixes (to support AI course discovery):
  - `main/templates/main/education/training_skills.html` (JS: fetch URL and class typos)
  - `main/urls.py` (added `ai-courses/` route)

## Commands to run tests (workspace root)

- Unit:
```
pytest -q main/tests/educationTest/unit
```
- Integration:
```
pytest -q main/tests/educationTest/integration
```
- Performance:
```
pytest -q main/tests/educationTest/performance
```
- Regression:
```
pytest -q main/tests/educationTest/regression
```
- System:
```
pytest -q main/tests/educationTest/system
```
- Full educationTest tree:
```
pytest -q main/tests/educationTest
```

## Notes & Recommendations

- All education tests pass in the current environment (virtualenv active). Warnings are non-blocking (third-party deprecations).
- Consider adding a `conftest.py` to centralize fixtures (e.g., `today = timezone.now().date()`), reduce duplication, and make tests easier to maintain.
- If you want the entire project test suite run, I can run it and help triage unrelated failures.

---
Generated automatically as part of test maintenance and verification.
