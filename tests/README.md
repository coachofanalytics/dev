# CODA Platform Tests

**Last Updated:** November 5, 2025  
**Standard:** 7-Category Test Structure

## Test Organization

All tests are organized by app, then by test category:

```
tests/
├── {app_name}/
│   ├── 01_unit/          🤖 Cursor creates
│   ├── 02_integration/   🤖 Cursor creates
│   ├── 03_performance/   🤖👤 Cursor + Human
│   ├── 04_regression/    🤖 Cursor creates
│   ├── 05_system/        👤 Human creates
│   ├── 06_security/      🤖👤 Cursor + Human
│   ├── 07_manual/        👤 Human creates
│   └── README.md
└── README.md (this file)
```

## Apps with Tests

### Finance
[Finance App Tests](finance/README.md)
- Payment control tests
- URL resolution tests
- Budget workflow tests

### Investing
[Investing App Tests](investing/README.md)
- User filtering tests (planned)
- Account management tests (planned)
- Position management tests (planned)

### Management
[Management App Tests](management/README.md)
- Task reset tests

## Running All Tests

```bash
# Run ALL tests across entire platform
cd /Users/coda/PROJECTS/CODA/DEVELOPMENT/DEV
python coda/manage.py test tests --settings=coda_project.coda_settings.local_settings

# Run specific app
python coda/manage.py test tests.finance --settings=coda_project.coda_settings.local_settings

# Run with coverage
coverage run --source='coda' coda/manage.py test tests --settings=coda_project.coda_settings.local_settings
coverage report
coverage html  # Generate HTML report
```

## Test Categories Explained

### 🤖 Automated by Cursor

1. **01_unit** - Individual component tests
2. **02_integration** - Component interaction tests
3. **04_regression** - Bug prevention tests

### 🤖👤 Shared Responsibility

1. **03_performance** - Cursor writes basic, human does load testing
2. **06_security** - Cursor writes permission tests, human does audits

### 👤 Manual by Human

1. **05_system** - End-to-end user flows (browser required)
2. **07_manual** - UI/UX validation, cross-browser testing

## Standards & Guidelines

**Complete Documentation:** [Testing Standards & Structure](../docs/TESTING_STANDARDS_AND_STRUCTURE.md)

**Key Points:**
- Every feature must have automated tests
- Critical flows must have manual test plans
- 80%+ code coverage required for new code
- All tests must pass before deployment
- Human approval required for production

## Contributing

### Adding Tests for New Features

1. Create app folder if it doesn't exist: `tests/{app_name}/`
2. Create test file in appropriate category (01-07)
3. Follow naming convention: `test_{component}_{feature}.py`
4. Write tests using AAA pattern (Arrange, Act, Assert)
5. Add docstrings to all test methods
6. Update app's README.md

### Moving Legacy Tests

If you find tests in wrong locations:
1. Move to appropriate app folder
2. Place in correct category (01-07)
3. Update file if needed
4. Update app README
5. Delete old location

---

*See: [Testing Standards](../docs/TESTING_STANDARDS_AND_STRUCTURE.md) for complete guidelines*
