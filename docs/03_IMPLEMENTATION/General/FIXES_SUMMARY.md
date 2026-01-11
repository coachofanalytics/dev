# DAF v2 Fixes Summary

## Problems Fixed

### A) Requirement Locked vs Missing Contradiction ✅

**Issue**: Requirement was locked if `task.requirement OR has_evidence`, but compliance check showed "Requirement Missing" when requirement was null.

**Fix**: Changed locking logic to only lock if `task.requirement AND has_evidence`. If requirement is missing, it's NOT locked and user can set it.

**Files Changed**:
- `coda/management/legacy_views.py` (lines 3524, 3929)
- `coda/management/forms.py` (line 309)

**Behavior**:
- If requirement is missing: User can select requirement (not locked)
- If requirement is set AND evidence exists: Requirement is locked (non-staff cannot change)
- If requirement is set but no evidence: Requirement is NOT locked (allows correction before first evidence)

---

### B) Evidence Topic Standardization ⚠️ (Partially Implemented)

**Issue**: `link_name` field was free text, leading to inconsistent topic names.

**Fix**: Added dropdown with known topics from ActivityType names and Requirements, with "Other" option for custom topics.

**Files Changed**:
- `coda/management/forms.py` (lines 330-356)

**Behavior**:
- Dropdown populated with ActivityType names (up to 50 most recent)
- If task has requirement, requirement title is added to dropdown
- "Other" option allows custom topic entry
- Falls back to CharField if no known topics available

**Note**: Template update needed to handle ChoiceField vs CharField rendering and show custom input when "Other" is selected.

---

### C) Existing Evidence Scoping ✅

**Issue**: "Existing Evidence" panel showed evidence from other employees.

**Fix**: Already implemented correctly in `get_user_evidence_for_task()`:
- Non-staff: Only shows evidence where `added_by=user` (current user)
- Staff: Shows all evidence for task + admin section with cross-requirement evidence

**Files Verified**:
- `coda/management/legacy_views.py` (lines 3417-3497)
- `coda/management/templates/management/daf/evidence_form.html` (lines 470-540)

**Behavior**:
- Non-staff users see only their own evidence for the task
- Staff users see all task evidence + separate admin section (if task has requirement)
- Template correctly separates `evidence_list` from `admin_evidence`

---

### D) DAF Header Totals Reconciliation ✅

**Issue**: Target units, provisional, approved, pending numbers didn't reconcile.

**Fix**: Added reconciliation check that recomputes totals from raw task data and logs warnings if mismatch detected.

**Files Changed**:
- `coda/management/legacy_views.py` (lines 2146-2160)

**Behavior**:
- Recomputes `target_amount` from sum of `mxearning` for all tasks
- Rounds all amounts to 2 decimal places for currency precision
- Logs warning if reconciliation mismatch > 0.01
- Provides debugging information for investigation

**Metrics Definitions**:
- `target_amount`: Sum of `mxearning` from all active tasks
- `provisional_earned_amount`: Sum of `earning` for tasks with status 'submitted' or 'approved'
- `approved_earned_amount`: Sum of `earning_approved` for tasks where `gate_pass == True`
- `pending_amount`: `target_amount - provisional_earned_amount` (from `money.locked_total`)

---

### E) Amount/Progress Calculation Rounding ✅

**Issue**: Formula `(task.point / task.mxpoint * task.mxearning)` didn't explicitly round to 2 decimal places.

**Fix**: Added explicit rounding to 2 decimal places for all earning calculations.

**Files Changed**:
- `coda/management/legacy_views.py` (lines 2000-2007, 2148-2149, 2152-2153)

**Behavior**:
- Formula: `round((point / mxpoint * mxearning), 2)` for currency precision
- Applied to: `earning_provisional`, `earning_approved`, `earning`
- Applied to: `approved_earned_amount`, `provisional_earned_amount`
- Edge cases handled: Division by zero (mxpoint == 0) returns 0.0

**Examples**:
- 5/5 = 500: `round((5/5 * 500), 2) = 500.00` ✅
- 1/1 = 500: `round((1/1 * 500), 2) = 500.00` ✅
- 9/10 = 450: `round((9/10 * 500), 2) = 450.00` ✅

---

## Testing Checklist

### Manual QA

1. **Requirement Locking (A)**:
   - [ ] Create task with requirement-required activity type, no requirement set
   - [ ] Navigate to evidence page → Requirement dropdown should be enabled
   - [ ] Set requirement and submit evidence → Requirement should be locked
   - [ ] Verify DAF v2 shows correct reason code (not "Requirement Missing" when locked)

2. **Evidence Topic (B)**:
   - [ ] Navigate to evidence page → Topic field should show dropdown
   - [ ] Select topic from dropdown → Should save correctly
   - [ ] Select "Other" → Custom input should appear
   - [ ] Enter custom topic → Should save correctly

3. **Existing Evidence (C)**:
   - [ ] As non-staff user, upload evidence for task
   - [ ] Verify "Existing Evidence" shows only your evidence
   - [ ] As staff user, verify admin section shows cross-requirement evidence (if applicable)

4. **DAF Totals (D)**:
   - [ ] View DAF v2 → Check target, provisional, approved amounts
   - [ ] Verify: `target_amount = sum(mxearning)` for all tasks
   - [ ] Verify: `approved_earned_amount <= provisional_earned_amount`
   - [ ] Check logs for reconciliation warnings

5. **Amount Calculation (E)**:
   - [ ] Create task with point=9, mxpoint=10, mxearning=500
   - [ ] Verify earning shows 450.00 (not 450.0 or 450)
   - [ ] Test edge cases: mxpoint=0, point=0, mxearning=0

### Automated Tests

Run:
```bash
poetry run python coda/manage.py check
poetry run python coda/manage.py test management.tests -v 2
```

---

## Files Changed Summary

1. `coda/management/legacy_views.py`:
   - Line 3524: Fixed requirement locking logic (POST handler)
   - Line 3929: Fixed requirement locking logic (GET handler)
   - Lines 2000-2007: Added rounding to earning calculations
   - Lines 2148-2149: Added rounding to approved earned amounts
   - Lines 2152-2153: Added rounding to provisional earned amounts
   - Lines 2155-2160: Added reconciliation check

2. `coda/management/forms.py`:
   - Line 309: Fixed requirement locking logic
   - Lines 330-356: Added topic dropdown with known topics + "Other" option

---

## Remaining Work

1. **Template Update for Topic Dropdown (B)**:
   - Update `coda/management/templates/management/daf/evidence_form.html` to:
     - Render ChoiceField as dropdown
     - Show custom input field when "Other" is selected
     - Handle form submission to use custom value when "Other" selected

2. **Form Clean Method (B)**:
   - Add `clean()` method to EvidenceForm to:
     - If `link_name == '__OTHER__'`, use `link_name_custom` value
     - Validate custom topic is provided when "Other" selected

3. **Tests**:
   - Add test for requirement locking behavior
   - Add test for topic dropdown
   - Add test for reconciliation check
   - Add test for earning calculation rounding

---

## Verification Commands

```bash
# Syntax check
python3 -m py_compile coda/management/legacy_views.py
python3 -m py_compile coda/management/forms.py

# Django check
poetry run python coda/manage.py check

# Run tests
poetry run python coda/manage.py test management.tests.test_daf_v2_truthfulness -v 2
```

---

**Status**: Core fixes implemented. Template update and form validation needed for complete Problem B solution.

