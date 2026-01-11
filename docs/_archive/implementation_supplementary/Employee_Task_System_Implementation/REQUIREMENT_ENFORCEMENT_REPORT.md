# Requirement Enforcement Implementation Report

**Date:** December 2025  
**Status:** ✅ Complete

---

## Overview

Implemented business rule enforcement: certain activity types (SELF_TRAINING_SESSION, INTERNAL_TRAINING_SESSION, CLIENT_TRAINING_SESSION, PRODUCT_BACKLOG_REFINEMENT) MUST be linked to a Requirement before evidence can be submitted.

---

## Changes Made

### 1. Model Changes

**File:** `coda/management/models.py`

- Added `requirement` ForeignKey field to `Task` model:
  ```python
  requirement = models.ForeignKey(
      'Requirement',  # String reference to avoid forward reference
      on_delete=models.SET_NULL,
      null=True,
      blank=True,
      related_name='tasks',
      help_text=_("Linked requirement for training/PBR activities (required for certain activity types)."),
  )
  ```

**Migration Created:**
- `coda/management/migrations/0003_add_task_requirement_field.py`

### 2. View Changes

**File:** `coda/management/views.py`

- Added constant for activity types requiring requirement:
  ```python
  REQUIREMENT_REQUIRED_ACTIVITY_TYPES = [
      'SELF_TRAINING_SESSION',
      'INTERNAL_TRAINING_SESSION',
      'CLIENT_TRAINING_SESSION',
      'PRODUCT_BACKLOG_REFINEMENT',
      'PBR',  # Alternative name for PBR
  ]
  ```

- **`newevidence()` view:**
  - Added requirement enforcement check before evidence submission
  - Validates that requirement is set for required activity types
  - Shows clear error message if requirement is missing
  - Only superuser can bypass (default policy: no bypass)
  - Updates `task.requirement` if provided in form

- **`process_evidence_submission()` function:**
  - Added double-check enforcement in async thread
  - Prevents TaskLinks creation if requirement is required but missing

### 3. Form Changes

**File:** `coda/management/forms.py`

- **`EvidenceForm.__init__()`:**
  - Accepts `task` parameter to check if requirement is needed
  - Filters requirements: only active, excludes invalid rows (blank `what` field)
  - Makes requirement field required if activity type requires it
  - Pre-selects requirement if task already has one
  - Shows requirement ID and description in dropdown: `CODA000{id} - {what[:50]}`

### 4. Template Changes

**File:** `coda/management/templates/management/daf/evidence_form.html`

- Added info alert when requirement is required:
  ```html
  {% if requires_requirement %}
  <div class="alert alert-info py-2 mb-2">
    <small><i class="fas fa-info-circle"></i> This activity must be linked to a Requirement before evidence can be submitted.</small>
  </div>
  {% endif %}
  ```
- Requirement dropdown shows selected value if task already has requirement

### 5. Tests

**File:** `coda/management/tests/test_requirement_enforcement.py`

- `test_self_training_requires_requirement()` - Verifies SELF_TRAINING_SESSION requires requirement
- `test_internal_training_requires_requirement()` - Verifies INTERNAL_TRAINING_SESSION requires requirement
- `test_client_training_requires_requirement()` - Verifies CLIENT_TRAINING_SESSION requires requirement
- `test_pbr_requires_requirement()` - Verifies PRODUCT_BACKLOG_REFINEMENT requires requirement
- `test_requirement_enforcement_success()` - Verifies success when requirement is provided
- `test_regular_activity_no_requirement_needed()` - Verifies regular activities don't require requirement
- `test_superuser_can_bypass()` - Verifies superuser bypass (current policy)

---

## Business Logic

### Activity Types Requiring Requirement

1. **SELF_TRAINING_SESSION**
2. **INTERNAL_TRAINING_SESSION**
3. **CLIENT_TRAINING_SESSION**
4. **PRODUCT_BACKLOG_REFINEMENT** (or **PBR**)

### Enforcement Points

1. **Evidence Form Validation:**
   - Form field is required for these activity types
   - User cannot submit without selecting requirement

2. **View-Level Validation:**
   - `newevidence()` checks requirement before processing
   - Shows error message if missing
   - Only superuser can bypass

3. **Async Thread Double-Check:**
   - `process_evidence_submission()` validates again
   - Prevents TaskLinks creation if requirement missing

### Requirement Filtering

- Only shows active requirements (`is_active=True`)
- Excludes requirements with blank `what` field
- Ordered by newest first (`-created_at`)

---

## Manual Verification Steps

### 1. Test Requirement Enforcement

1. Create a task with activity type `SELF_TRAINING_SESSION` (or one of the 4 types)
2. Navigate to `/management/newevidence/<task_id>/`
3. ✅ Verify requirement dropdown is shown and required (red asterisk)
4. ✅ Verify info alert: "This activity must be linked to a Requirement..."
5. Try to submit evidence without selecting requirement
6. ✅ Verify error message appears
7. ✅ Verify TaskLinks is NOT created

### 2. Test Success Path

1. Create a task with activity type `SELF_TRAINING_SESSION`
2. Navigate to evidence form
3. Select a requirement from dropdown
4. Submit evidence
5. ✅ Verify evidence is submitted successfully
6. ✅ Verify `task.requirement` is set

### 3. Test Regular Activity

1. Create a task with regular activity type (not in the 4 types)
2. Navigate to evidence form
3. ✅ Verify requirement dropdown is optional (no asterisk)
4. Submit evidence without requirement
5. ✅ Verify evidence is submitted successfully

### 4. Test Superuser Bypass

1. Login as superuser
2. Create a task with `SELF_TRAINING_SESSION`
3. Try to submit evidence without requirement
4. ✅ Verify superuser can bypass (current policy)

---

## Test Execution

```bash
# Run requirement enforcement tests
poetry run python coda/manage.py test management.tests.test_requirement_enforcement -v 2

# Run all management tests
poetry run python coda/manage.py test management -v 2

# Run Django checks
poetry run python coda/manage.py check

# Run migrations
poetry run python coda/manage.py migrate
```

---

## Files Modified

1. `coda/management/models.py` - Added `requirement` field to Task
2. `coda/management/views.py` - Added enforcement logic
3. `coda/management/forms.py` - Updated EvidenceForm
4. `coda/management/templates/management/daf/evidence_form.html` - Added requirement UI
5. `coda/management/tests/test_requirement_enforcement.py` - New test file
6. `coda/management/migrations/0003_add_task_requirement_field.py` - New migration

---

## Breaking Changes

**None** - All changes are backward compatible:
- Existing tasks without requirement continue to work
- Only the 4 specified activity types require requirement
- Regular activities are unaffected
- Legacy DAF unchanged

---

## Status

✅ **Implementation Complete**
✅ **Tests Added**
✅ **Migration Created**
✅ **Ready for Production**

---

**Report Generated:** December 2025

