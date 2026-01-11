# Requirement Enforcement Usability Improvements Report

**Date:** December 2025  
**Status:** ✅ Complete

---

## Overview

Improved usability and business effectiveness of requirement enforcement without re-architecting. Enhanced requirement dropdown, DAF v2 visibility, and manager review queue.

---

## Changes Made

### A) Improved Requirement Dropdown (EvidenceForm)

**File:** `coda/management/forms.py`

**Improvements:**
1. **Better Filtering:**
   - Excludes requirements with blank `what` field (invalid rows)
   - Only shows active requirements (`is_active=True`)
   - Capped queryset to 500 most recent to avoid huge dropdowns

2. **Better Ordering:**
   - Orders by `-created_at` (newest first)

3. **Better Option Labels:**
   - Format: `REQ-{id} — {what truncated to 80 chars}`
   - Example: `REQ-123 — Build dashboard for client reporting`

4. **Helper Text:**
   - Shows "Can't find it? Create a requirement first." with link

### B) Evidence Template Improvements

**File:** `coda/management/templates/management/daf/evidence_form.html`

**Improvements:**
1. **Visual Prominence:**
   - Requirement section has border and background when required
   - Warning alert (instead of info) when required
   - Bold label when required

2. **Current Requirement Display:**
   - Shows selected requirement in success alert if task already has one
   - Format: `REQ-{id} — {what truncated}`

3. **Create Requirement Link:**
   - Added "Create Requirement" button linking to `/management/requirement/new`
   - Opens in new tab

### C) DAF v2 Visibility (Employee)

**File:** `coda/management/views.py` + `coda/management/templates/management/daf/usertasks/employeetasks_v2.html`

**Improvements:**
1. **Requirement Chips:**
   - Shows "Requirement Missing" badge (red) if requirement is missing for required activity types
   - Shows "Requirement: REQ-{id}" badge (green) if requirement is present

2. **Needs Attention Logic:**
   - Added `requirement_missing` to `needs_attention` calculation
   - Added "Requirement missing: must link to a Requirement" to `attention_reasons`

3. **Primary CTA Update:**
   - If requirement missing: Shows "Select Requirement" button (red, highest priority)
   - Links to evidence page for that task
   - Otherwise follows existing logic (Upload Evidence / Complete Checklist / View Details)

4. **Issue Chips:**
   - Added `requirement_missing` to `issue_chips` dict

### D) Manager Review Queue

**File:** `coda/management/views.py` (`daf_review_view`)

**Improvements:**
1. **Requirement Missing in Severity:**
   - Added `requirement_missing` check for each task
   - Included in `issue_count` calculation (affects severity ordering)
   - Added `requirement_missing` to task data dict

2. **Query Optimization:**
   - Added `select_related('requirement')` to avoid N+1 queries

---

## Technical Details

### Requirement Detection Logic

```python
# Check if requirement is required and missing
activity_type_slug = None
if task.activity_type:
    activity_type_slug = task.activity_type.slug or task.activity_type.name
elif task.activity_name:
    activity_type_slug = task.activity_name.upper().replace(' ', '_')

requires_requirement = False
requirement_missing = False
if activity_type_slug:
    requires_requirement = activity_type_slug.upper() in [a.upper() for a in REQUIREMENT_REQUIRED_ACTIVITY_TYPES]
    if requires_requirement:
        requirement_missing = task.requirement is None
```

### Needs Attention Update

```python
needs_attention = (
    quality_score < 0.8 or
    evidence_status != 'complete' or
    bool(missing_checklist_items) or
    duration_factor < 1.0 or
    requirement_missing  # NEW
)
```

### Attention Reasons Update

```python
if requirement_missing:
    attention_reasons.append("Requirement missing: must link to a Requirement")
```

---

## Tests Added

**File:** `coda/management/tests/test_requirement_enforcement.py`

1. `test_daf_v2_shows_requirement_missing_chip()` - Verifies "Requirement Missing" chip appears
2. `test_daf_v2_shows_requirement_chip_when_present()` - Verifies requirement chip when set
3. `test_daf_v2_cta_select_requirement()` - Verifies CTA becomes "Select Requirement"
4. `test_evidence_form_excludes_blank_requirements()` - Verifies blank requirements are filtered

---

## Files Modified

1. `coda/management/forms.py` - Improved requirement dropdown
2. `coda/management/templates/management/daf/evidence_form.html` - Enhanced requirement UI
3. `coda/management/views.py` - Added requirement visibility to DAF v2 and manager review
4. `coda/management/templates/management/daf/usertasks/employeetasks_v2.html` - Added requirement chips and CTA
5. `coda/management/tests/test_requirement_enforcement.py` - Added new tests

---

## Manual Verification Steps

### 1. Requirement Dropdown

1. Navigate to evidence form for a task requiring requirement
2. ✅ Verify dropdown shows "REQ-{id} — {description}" format
3. ✅ Verify only active requirements with valid `what` field appear
4. ✅ Verify "Create Requirement" button appears
5. ✅ Verify "Can't find it? Create a requirement first." text appears

### 2. DAF v2 Requirement Visibility

1. Create task with `SELF_TRAINING_SESSION` without requirement
2. Navigate to `/management/daf/v2/`
3. ✅ Verify "Requirement Missing" red badge appears
4. ✅ Verify "Select Requirement" button appears (red, highest priority)
5. ✅ Verify task appears in "Needs Attention" tab
6. ✅ Verify attention reason shows "Requirement missing: must link to a Requirement"

### 3. DAF v2 with Requirement

1. Create task with `SELF_TRAINING_SESSION` with requirement
2. Navigate to `/management/daf/v2/`
3. ✅ Verify "Requirement: REQ-{id}" green badge appears
4. ✅ Verify "Requirement Missing" badge does NOT appear

### 4. Manager Review

1. Login as manager
2. Navigate to `/management/daf/review/`
3. ✅ Verify tasks with missing requirement appear
4. ✅ Verify `requirement_missing` is included in issue count
5. ✅ Verify severity ordering includes requirement missing

---

## Test Execution

```bash
# Run requirement enforcement tests
poetry run python coda/manage.py test management.tests.test_requirement_enforcement -v 2

# Run all management tests
poetry run python coda/manage.py test management -v 2

# Run Django checks
poetry run python coda/manage.py check
```

---

## Performance Considerations

- Added `select_related('requirement')` to avoid N+1 queries
- Capped requirement queryset to 500 most recent
- Requirement check is done once per task in view loop

---

## Breaking Changes

**None** - All changes are backward compatible:
- Existing tasks continue to work
- Only affects the 4 specified activity types
- Legacy DAF unchanged

---

## Status

✅ **Implementation Complete**
✅ **Tests Added**
✅ **No Breaking Changes**
✅ **Ready for Production**

---

**Report Generated:** December 2025

