# Tests Directory - Final Structure

**Date:** December 2025  
**Status:** ✅ Organized

## 📁 Directory Layout

```
tests/
├── README.md              # Main test documentation
├── docs/                  # Test-specific docs (NEW)
│   └── FINAL_STRUCTURE.md
├── fixtures/              # Shared test data (reserved)
├── utils/                 # Shared test utilities
│   ├── test_uat_scoring.py       # UAT scoring verification (investing)
│   ├── test_ui_workflows.py      # UI workflow smoke tests
│   └── test_uat_urls.sh          # UAT endpoint checks
├── results/               # Test outputs / reports
│   └── test_categorization_results.txt
├── run_tests.sh           # Test runner
├── accounts/              # 01–07 test categories
├── ai_services/
├── finance/
├── investing/
│   ├── 01_unit/
│   ├── 02_integration/
│   ├── 03_performance/
│   ├── 04_regression/
│   ├── 05_system/         # Consolidated system tests
│   ├── 06_security/
│   └── 07_manual/
├── main/
├── management/
├── marketing/
├── platform_services/
└── portfolio/
```

## ✅ Changes Applied

1. **Root-Level Tests Moved**
   - `test_uat_scoring.py` → `utils/test_uat_scoring.py`
   - `test_ui_workflows.py` → `utils/test_ui_workflows.py`
   - `test_uat_urls.sh` → `utils/test_uat_urls.sh`
   - `test_categorization_results.txt` → `results/test_categorization_results.txt`

2. **Investing System Tests Normalized**
   - Moved `investing/03_system/test_managed_income_scheduler.py` → `investing/05_system/test_managed_income_scheduler.py`
   - Removed empty `investing/03_system/` directory

3. **apps/investing Consolidated**
   - `apps/investing/01_unit/test_income_summary_helper.py` → `investing/01_unit/`
   - `apps/investing/01_unit/test_notification_service.py` → `investing/01_unit/`
   - `apps/investing/02_integration/test_account_limit_controls.py` → `investing/02_integration/`
   - Removed `tests/apps/investing/`

4. **Organization Directories Added**
   - `fixtures/` for shared data
   - `utils/` for shared utilities and UAT helpers
   - `results/` for output artifacts
   - `docs/` for test documentation

## 🎯 Standards

- All app tests live under `tests/{app_name}/01–07_category/`
- Shared helpers/utilities live in `tests/utils/`
- Output artifacts live in `tests/results/`
- No root-level `test_*.py` files

