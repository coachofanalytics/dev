# Management App Tests

## Test Organization

### 01_unit/
Unit tests for management models and services.

### 02_integration/
Integration tests for management views and workflows.

### 07_manual/
Manual test plans and scripts.

**Current:**
- `test_task_reset_manual.py` - Manual task reset testing

## Running Tests

```bash
# All management tests
python coda/manage.py test management --settings=coda_project.coda_settings.local_settings
```

---
*See: [Testing Standards](../docs/TESTING_STANDARDS_AND_STRUCTURE.md)*
