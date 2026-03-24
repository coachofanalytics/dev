# QA Test Execution Action Plan - Main App

## Current Status: Test Files Created ✓
## Next Steps: Execute & Fix

---

## 1. ENVIRONMENT SETUP (REQUIRED BEFORE TESTS)

### Step 1: Install Missing Dependencies
```cmd
cd C:\Users\PC\Desktop\dc48k_train
dc_venv\Scripts\activate.bat
pip install -r dev\requirements.txt
pip install feedparser pyfeed sgmllib3k
```

### Step 2: Verify Django Setup
```cmd
cd dev
python manage.py check
```

**Expected Output**: 0 errors, 0 warnings

### Step 3: Apply Migrations
```cmd
python manage.py migrate
python manage.py migrate --run-syncdb
```

---

## 2. TEST EXECUTION SEQUENCE

### Phase 1: Unit Tests (Local, No External Calls)
```cmd
python manage.py test main.tests.unit.test_models_all --verbosity=2
```

**Expected**: 34 tests
**Duration**: ~30 seconds
**Success Rate Target**: 100%

**If Failures Occur**:
- Check model definitions match test expectations
- Verify slug generation logic
- Confirm JSON field handling
- Check Decimal field support

### Phase 2: Integration Tests (API/Views)
```cmd
python manage.py test main.tests.integration.test_views_all --verbosity=2
```

**Expected**: 15+ tests
**Duration**: ~60 seconds
**Success Rate Target**: 100%

**If Failures Occur**:
- Verify CSRF exemption on quick_add_user
- Check session-based rate limiting implementation
- Confirm honeypot validation in forms
- Verify email mock patches work

### Phase 3: Regression Tests (Edge Cases)
```cmd
python manage.py test main.tests.regression.test_regression_all --verbosity=2
```

**Expected**: 18+ tests
**Duration**: ~45 seconds
**Success Rate Target**: 100%

**If Failures Occur**:
- Check state persistence in model saves
- Verify mutually exclusive field validation
- Confirm honeypot requires actual empty string
- Check rate limit reset implementation

### Phase 4: System Tests (End-to-End)
```cmd
python manage.py test main.tests.system.test_system_all --verbosity=2
```

**Expected**: 10+ tests
**Duration**: ~90 seconds
**Success Rate Target**: 100%

**If Failures Occur**:
- Verify complete workflows work
- Check all model relationships in flows
- Confirm email notifications sent in workflows

### Phase 5: Performance Tests (SLA Validation)
```cmd
python manage.py test main.tests.performance.test_performance_all --verbosity=2
```

**Expected**: 15+ tests
**Duration**: ~120 seconds (includes timing measurements)
**Success Rate Target**: 100%

**If Failures Occur**:
- Optimize database queries (add select_related/prefetch_related)
- Reduce external API calls
- Add caching where appropriate
- Check for N+1 query problems

---

## 3. RUN ALL TESTS (Final Check)

```cmd
python manage.py test main.tests --verbosity=2 --parallel
```

**Expected Results**:
- Total Tests: 90+
- Expected Duration: 4-5 minutes
- Success Rate: 100%
- Coverage: >80% of main app code

---

## 4. FAILURE RESPONSE PROTOCOL

### When a Test Fails:

#### Step A: Read the Error Message
```
FAIL: [test_name]
AssertionError: [specific error]
Traceback: [file:line]
```

#### Step B: Identify Category
- **Model Issue**: Changes to production
- **View Issue**: Changes to views.py
- **Form Issue**: Changes to forms.py
- **Timing Issue**: Performance optimization
- **Setup Issue**: Test environment problem

#### Step C: Fix Strategy

#### Model Issues
```
⚠️ CODE MODIFICATION REQUIRED
File: main/models.py
Line: XXX
Reason: [why test failed]
Before: [current code]
After: [fixed code]
```

Example:
```python
# Before
def save(self):
    super().save()

# After
def save(self):
    if self.deadline < timezone.now():
        self.status = Scholarship.Status.CLOSED
    super().save()
```

#### View Issues
```
Fix: Update main/views.py
- Add CSRF exemption: @csrf_exempt
- Add rate limiting: check session['attempt_count']
- Add validation: form.is_valid()
```

#### Form Issues
```
Fix: Update main/forms.py
- Add clean_members() method for mutual exclusivity
- Add clean_honeypot() for spam check
- Add clean_preferred_date() for future check
```

#### Performance Issues
```
Fix: Optimize in main/views.py
- Add: .select_related('foreign_key')
- Add: .prefetch_related('reverse_relation')
- Cache with: @cache_page(60)
```

#### Skip Only If:
```
@unittest.skip("Feature not implemented yet - depends on external service")
```

**NEVER** skip without documentation and approval.

---

## 5. COMMON ISSUES & SOLUTIONS

### Issue: ImportError: No module named 'cloudinary_storage'
**Solution**: 
```cmd
pip install django-storages
```

### Issue: ImportError: No module named 'feedparser'
**Solution**:
```cmd
pip install feedparser sgmllib3k
```

### Issue: Database error "no such table"
**Solution**:
```cmd
python manage.py migrate
python manage.py migrate --run-syncdb
```

### Issue: Test database already exists
**Solution**:
```cmd
rm db.sqlite3  # or delete the test database file
python manage.py test --keepdb  # if you want to reuse
```

### Issue: Port already in use (if testing servers)
**Solution**:
```cmd
# Kill process on port 8000
netstat -ano | findstr :8000
taskkill /PID [PID] /F
```

### Issue: Permission denied on file operations
**Solution**:
```cmd
# Run CMD as Administrator
# Or check media folder permissions
cacls C:\path\to\media /grant Everyone:F
```

---

## 6. TEST CATEGORIES TO WATCH

### High Priority (Fix First)
- [ ] Authentication tests (critical security)
- [ ] Honeypot validation (spam prevention)
- [ ] Rate limiting (DoS protection)
- [ ] Status auto-update logic (data integrity)

### Medium Priority (Fix Second)
- [ ] API response formats (integration)
- [ ] Form validation (UX quality)
- [ ] Relationship integrity (data consistency)
- [ ] Search/filter logic (feature correctness)

### Low Priority (Fix Last)
- [ ] Performance (optimization only)
- [ ] Display methods (__str__)
- [ ] Edge cases (robustness)
- [ ] Error messages (polish)

---

## 7. SUCCESS CRITERIA

### Unit Tests
- ✓ All 34 tests pass
- ✓ No warnings or deprecation errors
- ✓ All model fields behave as expected
- ✓ All auto-generated fields work

### Integration Tests
- ✓ All 15+ tests pass
- ✓ All API endpoints return correct status codes
- ✓ All form validations work correctly
- ✓ CSRF exemptions work as designed
- ✓ Mocks are properly applied

### Regression Tests
- ✓ All 18+ tests pass
- ✓ No state persistence issues
- ✓ All edge cases handled gracefully
- ✓ Security constraints enforced

### System Tests
- ✓ All 10+ tests pass
- ✓ All workflows complete successfully
- ✓ All relationships maintained through flows
- ✓ Email notifications sent

### Performance Tests
- ✓ All 15+ tests pass
- ✓ All endpoints < SLA threshold
- ✓ Bulk operations complete efficiently
- ✓ Concurrent access safe

### Overall
- ✓ 90+ tests pass (100% pass rate)
- ✓ 0 skipped tests
- ✓ Code coverage > 80%
- ✓ No production bugs found

---

## 8. REPORTING

### During Test Runs
```cmd
# Capture full output
python manage.py test main.tests --verbosity=2 > test_run.txt 2>&1

# Run with coverage
coverage run --source='main' manage.py test main.tests
coverage report -m
coverage html
```

### Generate Test Report
```cmd
# Summary statistics
pytest --verbose --tb=line main/tests/ > test_summary.txt

# HTML report
pytest -v --html=report.html main/tests/

# Coverage report
coverage html  # generates htmlcov/index.html
```

### Create Final Report
- Paste test output into TEST_RESULTS.md
- Summarize: X tests passed, Y failed, Z skipped
- List all fixes applied
- Note any deferred items
- Get sign-off

---

## 9. POST-TESTING CHECKLIST

After All Tests Pass:
- [ ] All test files verified
- [ ] All test output captured
- [ ] All failures documented
- [ ] All fixes implemented
- [ ] All fixes verified working
- [ ] Coverage report generated
- [ ] Performance report generated
- [ ] Final sign-off obtained

---

## 10. QUICK START (ONE COMMAND)

### Run Everything
```cmd
cd C:\Users\PC\Desktop\dc48k_train\dev && ^
python manage.py test main.tests.unit ^
main.tests.integration ^
main.tests.regression ^
main.tests.system ^
main.tests.performance ^
--verbosity=2 --parallel
```

**Expected Output**:
```
Ran 90+ tests in ~5 minutes

OK
```

---

## Appendix: Test File Locations

```
main/
├── tests/
│   ├── unit/
│   │   └── test_models_all.py ✓ (34 tests)
│   ├── integration/
│   │   └── test_views_all.py ✓ (15+ tests)
│   ├── regression/
│   │   └── test_regression_all.py ✓ (18+ tests)
│   ├── system/
│   │   └── test_system_all.py ✓ (10+ tests)
│   ├── performance/
│   │   └── test_performance_all.py ✓ (15+ tests)
│   └── TEST_SUITE_COMPREHENSIVE.md ✓ (This report)
```

---

**Generated**: March 25, 2026
**Version**: 1.0
**Status**: Ready for Execution
**Next Action**: Follow Step 1 in Environment Setup
