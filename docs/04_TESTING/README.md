# 04 - Testing

**Purpose:** Testing strategy, guidelines, and test execution

---

## 📚 Documents in This Section

### ⭐ [COMPREHENSIVE_TESTING_STRATEGY.md](COMPREHENSIVE_TESTING_STRATEGY.md)
**Complete testing framework for CODA project**

**Contains:**
- Testing pyramid (Unit 80%, Integration 15%, E2E 5%)
- Test types (Unit, Integration, System, E2E, Regression, Performance, Security)
- Test structure and organization
- Running tests (local, CI/CD)
- Test coverage targets (80% overall)
- Pre-deployment checklist

**Use This:** Before implementing any tests or deploying

---

## 🧪 Quick Testing Guide

### Run Tests:
```bash
# All regression tests (MANDATORY before deployment)
./tests/run_tests.sh --regression

# All Django tests
cd coda && python manage.py test finance

# Specific test
cd coda && python manage.py test finance.tests.test_regressions

# With coverage
cd coda && coverage run manage.py test finance
cd coda && coverage report
```

### Test Locations:
- **Django Unit Tests:** `coda/finance/tests/`
- **Regression Tests:** `coda/finance/tests/test_regressions.py`
- **Integration Tests:** `tests/`
- **UAT URL Tests:** `tests/test_uat_urls.sh`

---

## ⚠️ Critical Regression Tests

**These MUST pass before any deployment:**
1. Budget approval fields exist
2. Loan product schema correct (`term_months`)
3. Staff permission logic works
4. Dashboard aggregation correct

**Run:** `./tests/run_tests.sh --regression`

---

**Last Updated:** October 13, 2025

