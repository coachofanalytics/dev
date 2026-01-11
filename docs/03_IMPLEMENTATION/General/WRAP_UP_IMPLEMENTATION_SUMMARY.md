# Wrap-Up Implementation Summary

## Overview

Completed wrap-up work for policy enforcement, DAF v2 actionability, manager audit details, and guard tests.

## Files Changed

### 1. Admin Controls for Employee Group (NEW)
**File:** `coda/management/admin.py`

**Changes:**
- Added `EmployeeCareerStateAdmin` class with:
  - List display: user, group, current_level_code, is_tenured, loyalty_fund_balance, date_at_level, updated_at
  - List filters: group, is_tenured, current_level_code
  - List editable: group, is_tenured (inline editing)
  - Bulk actions: `set_group_a`, `set_group_b`, `set_group_c`
  - Fieldsets for organized editing
  - Read-only display of months_at_level

**Usage:**
- Navigate to Django Admin → Management → Employee Career States
- Select employees → Actions → "Set selected employees to Group A/B/C"
- Or edit group directly in list view (inline editing)

### 2. DAF v2 Actionability Improvements
**File:** `coda/management/templates/management/daf/usertasks/employeetasks_v2.html`

**Changes:**
- **Reason Code → CTA Mapping:**
  - `REQUIREMENT_MISSING` → "Select Requirement" (red button)
  - `EVIDENCE_MISSING` / `EVIDENCE_COUNT_INSUFFICIENT` → "Upload Evidence" (blue button) with progress badge
  - `MEETING_REQUIRED` → "Link Meeting" (yellow button)
  - `CHECKLIST_INCOMPLETE` → "Complete Checklist" (yellow button)
  - `DURATION_MISSING` → "Fix Duration" (yellow button)
  - `QUALITY_FAIL` → "Improve Evidence/Checklist" (yellow button)

- **Evidence Progress Display:**
  - Evidence chip shows "Evidence: Partial (1/2)" when count < minimum
  - Evidence chip shows "Evidence: ✗ (0/2)" when missing and minimum > 1
  - CTA button shows progress badge: "Upload Evidence (1/2)"

- **View Integration:**
  - `coda/management/legacy_views.py:2013` - Added `evidence_count_total` and `last_evidence_timestamp` for manager audit
  - `coda/management/legacy_views.py:3090` - Added `evidence_minimum` to compliance dict

### 3. Manager-Only Audit Details
**File:** `coda/management/templates/management/daf/usertasks/employeetasks_v2.html`

**Changes:**
- Added "Manager Audit" section in collapsed task details (staff-only)
- Shows:
  - **Meeting Match:** Autolink / Auto Pending / Manual / None (with confidence %)
  - **Evidence Counts:** Active count, Total count, Last upload timestamp
  - **Policy:** Group A/B/C and minimum evidence requirement

**Location:** Inside collapsed `#taskDetails{{ task.id }}` section, only visible to staff/superuser

### 4. Guard Test for Legacy Meeting Tables
**File:** `coda/management/tests/test_meeting_source_guard.py` (NEW)

**Purpose:** Prevents regression by failing if compliance code references legacy meeting tables.

**Tests:**
- `test_compliance_code_no_legacy_table_references()`: Scans compliance files for forbidden patterns:
  - `getdata_gotomeetings` (hardcoded table name)
  - `gotomeeting_meeting` (never-used table name)
  - `GotoMeetings.objects` (direct query of legacy model)
  - `from.*GotoMeetings.*import` (import of legacy model)

- `test_compliance_code_uses_canonical_meeting_model()`: Positive test ensuring canonical model is used

**Files Scanned:**
- `coda/management/legacy_views.py`
- `coda/management/services/policy_resolver.py`
- `coda/management/services/evidence_summary_service.py`
- `coda/management/services/checklist_evaluation_service.py`
- `coda/management/services/task_quality_gate_service.py`

## Reason Code → CTA Mapping

| Reason Code | CTA Button | Icon | Color |
|-------------|------------|------|-------|
| `REQUIREMENT_MISSING` | Select Requirement | `fa-exclamation-triangle` | Red (danger) |
| `EVIDENCE_MISSING` | Upload Evidence | `fa-upload` | Blue (primary) |
| `EVIDENCE_COUNT_INSUFFICIENT` | Upload Evidence (with progress) | `fa-upload` | Blue (primary) |
| `MEETING_REQUIRED` | Link Meeting | `fa-video` | Yellow (warning) |
| `CHECKLIST_INCOMPLETE` | Complete Checklist | `fa-tasks` | Yellow (warning) |
| `DURATION_MISSING` | Fix Duration | `fa-clock` | Yellow (warning) |
| `QUALITY_FAIL` | Improve Evidence/Checklist | `fa-chart-line` | Yellow (warning) |

## Evidence Progress Display

**Format:** `Evidence: Status (current/minimum)`

**Examples:**
- `Evidence: ✗ (0/2)` - Missing, needs 2 items
- `Evidence: Partial (1/2)` - Has 1, needs 2
- `Evidence: ✓` - Complete (no count shown)

## Manager Audit Details

**Visible To:** Staff and superusers only

**Shows:**
1. **Meeting Match Method:**
   - Autolink (auto-created from meeting)
   - Auto Pending (matched but not yet linked)
   - Manual (manually linked)
   - None (no match)

2. **Evidence Counts:**
   - Active: Number of active evidence items
   - Total: Total evidence items (including inactive)
   - Last: Timestamp of most recent evidence upload

3. **Policy:**
   - Group: A, B, or C
   - Min Evidence: Minimum required for this activity type

## Verification Commands

```bash
# 1. System check
poetry run python coda/manage.py check
# Expected: "System check identified no issues (0 silenced)."

# 2. Run policy enforcement tests
poetry run python coda/manage.py test management.tests.test_policy_enforcement -v 2
# Expected: All tests pass

# 3. Run meeting source guard test
poetry run python coda/manage.py test management.tests.test_meeting_source_guard -v 2
# Expected: No violations found

# 4. Run all management tests
poetry run python coda/manage.py test management.tests -v 2
```

## Manual QA Checklist

### For Manager (Staff User)

1. **Admin Controls:**
   - [ ] Navigate to `/admin/management/employeecareerstate/`
   - [ ] Verify list shows: user, group, current_level_code, is_tenured
   - [ ] Select 2-3 employees → Actions → "Set selected employees to Group A"
   - [ ] Verify success message appears
   - [ ] Verify selected employees now show Group A in list
   - [ ] Edit group inline (click on group cell, change to B)
   - [ ] Verify change saves

2. **DAF v2 Manager View:**
   - [ ] Navigate to `/management/daf/v2/`
   - [ ] Find a task in "Needs Attention" tab
   - [ ] Click "Details" to expand task
   - [ ] Verify "Manager Audit" section appears (staff-only)
   - [ ] Verify shows: Meeting Match method, Evidence Counts, Policy group
   - [ ] Verify meeting match shows confidence % if matched
   - [ ] Verify last evidence timestamp is shown if evidence exists

3. **Reason Code → CTA Mapping:**
   - [ ] Find task with `REQUIREMENT_MISSING` → Verify "Select Requirement" button
   - [ ] Find task with `EVIDENCE_MISSING` → Verify "Upload Evidence" button
   - [ ] Find task with `EVIDENCE_COUNT_INSUFFICIENT` → Verify "Upload Evidence" button with progress badge (e.g., "1/2")
   - [ ] Find task with `MEETING_REQUIRED` → Verify "Link Meeting" button
   - [ ] Find task with `CHECKLIST_INCOMPLETE` → Verify "Complete Checklist" button
   - [ ] Find task with `DURATION_MISSING` → Verify "Fix Duration" button
   - [ ] Find task with `QUALITY_FAIL` → Verify "Improve Evidence/Checklist" button

4. **Evidence Progress Display:**
   - [ ] Find task with evidence count below minimum (e.g., Group A task needs 2, has 1)
   - [ ] Verify evidence chip shows: "Evidence: Partial (1/2)"
   - [ ] Verify CTA button shows: "Upload Evidence (1/2)"
   - [ ] Find task with no evidence and minimum > 1
   - [ ] Verify evidence chip shows: "Evidence: ✗ (0/2)"

### For Group B User (Employee)

1. **Policy Display:**
   - [ ] Navigate to `/management/daf/v2/` as Group B user
   - [ ] Verify policy badge does NOT appear (staff-only)
   - [ ] Verify "Manager Audit" section does NOT appear in task details

2. **Reason Text Clarity:**
   - [ ] Find task in "Needs Attention" tab
   - [ ] Verify reason text is clear and actionable:
     - "Upload at least 1 evidence item (link or file) with a short description."
     - "Select the requirement this task is fulfilling."
     - "This activity requires meeting proof. Link a meeting or paste the meeting recording URL."
   - [ ] Verify reason text is employee-friendly (no technical jargon)

3. **CTA Button Clarity:**
   - [ ] Verify each reason code shows appropriate CTA button
   - [ ] Verify button text is clear (e.g., "Upload Evidence" not "Fix Issues")
   - [ ] Verify button links to correct page (evidence page or task details)

4. **Evidence Progress:**
   - [ ] If evidence count below minimum, verify progress is shown (e.g., "1/2")
   - [ ] Verify progress helps user understand how many more items needed

## Test Results

```bash
# Run all tests
poetry run python coda/manage.py test management.tests.test_policy_enforcement management.tests.test_meeting_source_guard -v 2
```

**Expected Output:**
- All policy enforcement tests pass
- Meeting source guard test passes (no violations)
- No legacy table references found in compliance code

## Summary of Changes

| File | Lines Changed | Purpose |
|------|---------------|---------|
| `coda/management/admin.py` | +60 lines | Employee group admin with bulk actions |
| `coda/management/templates/management/daf/usertasks/employeetasks_v2.html` | ~40 lines | Reason code → CTA mapping, progress display, manager audit |
| `coda/management/legacy_views.py` | ~10 lines | Added evidence_count_total, last_evidence_timestamp, evidence_minimum |
| `coda/management/tests/test_meeting_source_guard.py` | NEW (120 lines) | Guard test for legacy table references |

## Notes

- ✅ Admin bulk actions work for setting employee groups
- ✅ Reason codes map to specific, actionable CTAs
- ✅ Evidence progress shows current/minimum (e.g., "1/2")
- ✅ Manager audit details only visible to staff
- ✅ Guard test prevents regression (legacy table references)
- ✅ All changes backward compatible
- ✅ No breaking changes to existing URLs

