# CODA Test Scripts

This directory contains all test scripts for the CODA project.

## Test Scripts

### `run_tests.sh` ⭐ Main Test Runner
**Purpose:** Run comprehensive test suite before deployment  
**Usage:**
```bash
# Run all tests
./tests/run_tests.sh

# Run only regression tests (critical)
./tests/run_tests.sh --regression

# Run with verbose output
./tests/run_tests.sh --verbose
```

**IMPORTANT:** Always run regression tests before deploying!

---

### `test_budget_workflow.py`
**Purpose:** Test budget creation and approval workflow  
**Usage:**
```bash
cd coda
python ../tests/test_budget_workflow.py
```

---

### `test_payment_control.py`
**Purpose:** Test payment control middleware  
**Usage:**
```bash
python tests/test_payment_control.py
```

---

### `test_uat_urls.sh`
**Purpose:** Test all critical URLs in UAT environment  
**Usage:**
```bash
./tests/test_uat_urls.sh
```

**Tests:**
- Dashboard URLs
- Budget approval URLs
- Loan URLs
- API endpoints

---

## Django Unit Tests

Django unit tests are located in each app's `tests/` directory:

```
coda/finance/tests/
├── __init__.py
├── test_models.py
├── test_services.py
├── test_views.py
├── test_api.py
└── test_regressions.py  ⭐ Critical regression tests
```

**Run Django tests:**
```bash
cd coda
python manage.py test finance
```

---

## Test Strategy

See comprehensive testing documentation:
- **[COMPREHENSIVE_TESTING_STRATEGY.md](../coda/docs/COMPREHENSIVE_TESTING_STRATEGY.md)** - Full testing framework
- **[Feature Testing Docs](../coda/docs/apps/finance/)** - Feature-specific test guides

---

## Pre-Deployment Checklist

Before deploying to UAT or Production:

- [ ] Run `./tests/run_tests.sh` (all tests pass)
- [ ] Run regression tests specifically
- [ ] Test critical user journeys manually
- [ ] Check browser console for errors
- [ ] Verify database migrations
- [ ] Review deployment logs

---

**Last Updated:** October 13, 2025

