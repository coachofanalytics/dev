# Meeting Model Truth Report

## A. Code References (Imports + Query Usage)

### Import Pattern
All code consistently imports: `from ai_services.models import Meeting`

**Total references**: 34 imports across 21 files

**Key files using Meeting**:
- `coda/management/legacy_views.py` (8 references) - DAF v2, evidence workflow
- `coda/ai_services/services/meeting_evidence_matcher.py` (1 reference) - Core matching service
- `coda/ai_services/services/meeting_task_autolink_service.py` (1 reference) - Auto-linking
- `coda/management/services/checklist_evaluation_service.py` (1 reference) - Compliance checks
- `coda/ai_services/services/ai_operations_service.py` (2 references) - Daily ops
- Plus 16 other files for various services/commands

**Fields commonly referenced**:
- `start_time`, `end_time`, `duration_minutes`
- `recording_url`, `download_url`
- `topic`, `topic_normalized`
- `requirement_code`
- `meeting_id`
- `service_name`

**Usage contexts**:
- DAF v2 evidence matching
- Meeting evidence matcher service
- Auto-linking meeting evidence to tasks
- AI operations (tagging, summaries)
- Compliance evaluation

## B. Django Model Truth (What Django Expects)

**Model Definition**: `coda/ai_services/models.py` line 127-214

```python
class Meeting(models.Model):
    # ... fields ...
    
    class Meta:
        db_table = 'getdata_gotomeetings'  # Line 204
        ordering = ['-meeting_start_time']
        # ... indexes ...
```

**Django Shell Verification**:
```
Model: <class 'ai_services.models.Meeting'>
App label: ai_services
DB table: getdata_gotomeetings  ← CORRECT TABLE NAME
Managed: True
```

**Migrations Status**:
- `ai_services.0001_initial`: APPLIED
- `ai_services.0002_oauthtoken`: APPLIED
- `ai_services.0002_auto_20250918_2043`: APPLIED
- `ai_services.0003_auto_20251229_0011`: APPLIED

**Note**: No migrations directory found in `coda/ai_services/` - migrations may be in a different location or auto-generated.

## C. Database Truth (Actual Tables Present)

**Database Query Results**:
```
Meeting-related tables:
  - getdata_gotomeetings  ← EXISTS
  - gotomeeting_sync_run
  - management_meetings

Has gotomeeting_meeting: False  ← DOES NOT EXIST
Has getdata_gotomeetings: True   ← EXISTS
```

**Conclusion**: The table `getdata_gotomeetings` exists and matches Django's expectation. The table `gotomeeting_meeting` does NOT exist.

## D. Resolution Options with Recommendation

### Root Cause Identified

**The Bug**: `coda/management/legacy_views.py` line 2829

The `_safe_meeting_query()` function checks for the wrong table name:
```python
if 'gotomeeting_meeting' not in table_names:  # ❌ WRONG TABLE NAME
    logger.debug("Meeting table 'gotomeeting_meeting' does not exist. Skipping query.")
    return None
```

**Should be**:
```python
if 'getdata_gotomeetings' not in table_names:  # ✅ CORRECT TABLE NAME
    logger.debug("Meeting table 'getdata_gotomeetings' does not exist. Skipping query.")
    return None
```

### Resolution: Option A (RECOMMENDED) - Fix Table Name Check

**Why this is correct**:
- Django model already points to correct table (`getdata_gotomeetings`)
- Database has the correct table
- All imports are consistent (`ai_services.models.Meeting`)
- Single source of truth already established
- Minimal change (1 line fix)

**Risks**: None - this is a bug fix, not a refactor

**What to change**:
- File: `coda/management/legacy_views.py`
- Line: 2829
- Change: `'gotomeeting_meeting'` → `'getdata_gotomeetings'`
- Line: 2830 (log message)
- Change: `'gotomeeting_meeting'` → `'getdata_gotomeetings'`

**Why NOT Option B** (change model db_table):
- Would require migration
- Would break existing data/queries
- No evidence that `gotomeeting_meeting` was ever intended
- The current setup (`getdata_gotomeetings`) is working correctly

## Implementation

### Step 1: Fix the table name check

**File**: `coda/management/legacy_views.py`
**Lines**: 2829-2830

**Change**:
```python
# BEFORE:
if 'gotomeeting_meeting' not in table_names:
    logger.debug("Meeting table 'gotomeeting_meeting' does not exist. Skipping query.")

# AFTER:
if 'getdata_gotomeetings' not in table_names:
    logger.debug("Meeting table 'getdata_gotomeetings' does not exist. Skipping query.")
```

### Step 2: Verification Commands

```bash
# 1. System check
poetry run python coda/manage.py check

# 2. Test the function in shell
poetry run python coda/manage.py shell -c "
from management.legacy_views import _safe_meeting_query
result = _safe_meeting_query()
print('Query result:', 'None' if result is None else f'QuerySet with {result.count()} items')
"

# 3. Test DAF v2 view (where error occurs)
poetry run python coda/manage.py runserver 8000
# Navigate to /management/daf/v2/ and verify no errors

# 4. Test evidence workflow
# Navigate to /management/newevidence/<task_id>/ and verify meeting matching works
```

## Verification Checklist

- [ ] Fix applied in `coda/management/legacy_views.py` line 2829-2830
- [ ] `poetry run python coda/manage.py check` passes
- [ ] `_safe_meeting_query()` returns QuerySet (not None) when table exists
- [ ] DAF v2 view loads without `ProgrammingError`
- [ ] Evidence workflow can query meetings successfully
- [ ] No other references to `'gotomeeting_meeting'` string found (verified via grep)

## Summary

**Issue**: Hardcoded wrong table name in safety check function
**Fix**: Change `'gotomeeting_meeting'` → `'getdata_gotomeetings'` (2 lines)
**Risk**: None (bug fix only)
**Impact**: Fixes runtime error, enables meeting queries to work correctly

