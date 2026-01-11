# Evidence & Meeting Fixes Summary

## Changes Implemented

### 1. Created Evidence Summary Service (Single Source of Truth)

**File:** `coda/management/services/evidence_summary_service.py` (NEW)

**Purpose:** Provides unified API for all evidence checks to prevent contradictions.

**Key Function:**
```python
get_task_evidence_summary(task, task_links=None, meeting_match_info=None) -> dict
```

**Returns:**
- `count_active`: Number of active TaskLinks
- `count_usable`: Number of active TaskLinks with usable evidence (link/doc/drive_link)
- `items_qs`: QuerySet/list of active TaskLinks
- `has_minimum`: bool (True if at least one usable evidence exists)
- `status`: 'missing' | 'partial' | 'complete' | 'auto_pending'
- `reasons_if_fail`: List of reasons why evidence is missing/partial
- `has_auto_generated`: bool

### 2. Updated `compute_task_compliance` to Use Evidence Summary

**File:** `coda/management/legacy_views.py:2888`

**Changes:**
- Replaced inline evidence checks with `get_task_evidence_summary()` call
- Uses evidence summary status as base for compliance determination
- Ensures consistent evidence status across all compliance checks

### 3. Fixed Meeting Table Check

**File:** `coda/management/legacy_views.py:2848`

**Changes:**
- Updated `_safe_meeting_query()` to check `Meeting._meta.db_table` instead of hardcoded `'getdata_gotomeetings'`
- Actual table name: `ai_services_meeting` (Django default)
- Added comment explaining canonical Meeting model

### 4. Fixed Template Contradiction

**File:** `coda/management/templates/management/daf/usertasks/employeetasks_v2.html`

**Changes:**
- Badge (line 259-267): Uses `task.compliance_chips.evidence.status` ✅
- Body (line 415-429): Now also uses `task.compliance_chips.evidence.status` ✅
- Removed contradictory checks using `task.gate_status.has_evidence` or `task.evidence_list|length`
- Ensures badge and body always show consistent state

### 5. Updated Evidence List Building

**File:** `coda/management/legacy_views.py:1813`

**Changes:**
- Uses `get_task_evidence_summary()` to build evidence list
- Ensures only active, usable evidence is included
- Consistent with evidence status determination

### 6. Updated Task Dict to Use Evidence Summary

**File:** `coda/management/legacy_views.py:1990`

**Changes:**
- `has_evidence`: Now uses `evidence_summary['has_minimum']`
- `evidence_count`: Now uses `evidence_summary['count_usable']`
- `evidence_status`: Now uses `evidence_summary['status']`

### 7. Added Model Comment

**File:** `coda/ai_services/models.py:203`

**Changes:**
- Added comment explaining that `db_table = 'gotomeeting_meeting'` was never used
- Actual table: `ai_services_meeting` (Django default)

---

## Verification Commands

```bash
# 1. System check
poetry run python coda/manage.py check
# Expected: "System check identified no issues (0 silenced)."

# 2. Run tests (if available)
poetry run python coda/manage.py test management.tests.test_daf_v2_truthfulness -v 2

# 3. Manual verification (see scenarios below)
```

---

## Manual Verification Scenarios

### Scenario 1: Task with 0 evidence

**Steps:**
1. Navigate to `/management/daf/v2/`
2. Find a task with no evidence uploaded
3. Check task card

**Expected Results:**
- ✅ Badge shows: `Evidence: ✗` (red badge)
- ✅ Body shows: "No evidence uploaded yet."
- ✅ CTA button shows: "Upload Evidence"
- ✅ NO contradiction (badge and body match)

### Scenario 2: Task with evidence but inactive

**Steps:**
1. Create a task with evidence where `is_active=False`
2. Navigate to `/management/daf/v2/`
3. Check task card

**Expected Results:**
- ✅ Badge shows: `Evidence: ✗` (red badge)
- ✅ Body shows: "No evidence uploaded yet."
- ✅ Reason: Evidence exists but is inactive (not shown in UI, but handled by service)

### Scenario 3: Task with valid evidence

**Steps:**
1. Create a task with active evidence (link, doc, or drive_link)
2. Navigate to `/management/daf/v2/`
3. Check task card

**Expected Results:**
- ✅ Badge shows: `Evidence: ✓` (green badge)
- ✅ Body shows: "Evidence: N item(s)" (where N > 0)
- ✅ NO "No evidence uploaded yet" warning
- ✅ Evidence list shows all active evidence items

### Scenario 4: Task with partial evidence (description only, no link/file)

**Steps:**
1. Create a task with evidence that has only description (no link/doc/drive_link)
2. Navigate to `/management/daf/v2/`
3. Check task card

**Expected Results:**
- ✅ Badge shows: `Evidence: Partial` (yellow badge)
- ✅ Body shows: "Evidence: Partial (missing required link/file)"
- ✅ Evidence list may be empty (if no usable evidence)

### Scenario 5: Task with auto-pending evidence

**Steps:**
1. Create a task where meeting is matched but TaskLinks not yet created
2. Navigate to `/management/daf/v2/`
3. Check task card

**Expected Results:**
- ✅ Badge shows: `Evidence: Auto Pending` (blue badge)
- ✅ Body shows: "Auto evidence pending sync. Meeting matched."
- ✅ NO "No evidence uploaded yet" warning

---

## Files Changed Summary

| File | Lines Changed | Purpose |
|------|---------------|---------|
| `coda/management/services/evidence_summary_service.py` | NEW (115 lines) | Single source of truth for evidence checks |
| `coda/management/legacy_views.py` | ~20 lines | Use evidence_summary_service, fix meeting table check |
| `coda/management/templates/management/daf/usertasks/employeetasks_v2.html` | ~15 lines | Fix badge/body contradiction |
| `coda/ai_services/models.py` | 2 lines | Add comment about table name |
| `EVIDENCE_AUDIT_REPORT.md` | NEW | Comprehensive audit report |

---

## Before/After Behavior

### Before (Contradictory)

- Badge: `Evidence: ✓` (from `compliance_chips.evidence.status`)
- Body: "No evidence uploaded yet" (from `gate_status.has_evidence`)
- **Result:** User confusion, trust issues

### After (Consistent)

- Badge: `Evidence: ✓` (from `compliance_chips.evidence.status`)
- Body: "Evidence: N item(s)" (from `compliance_chips.evidence.status`)
- **Result:** Consistent UI, single source of truth

---

## Remaining Work (Future)

1. **Migrate Legacy DAF:** Update `coda/management/services/daf_summary_service.py` to use `evidence_summary_service`
2. **Refactor TaskQualityGateService:** Consider using `evidence_summary_service` instead of duplicating logic
3. **Add Tests:** Create tests for `evidence_summary_service` covering all scenarios

---

## Notes

- ✅ No breaking changes to existing functionality
- ✅ All changes are backward compatible
- ✅ Evidence summary service is the single source of truth going forward
- ✅ Meeting model table check now uses `Meeting._meta.db_table` (dynamic, not hardcoded)
- ✅ Template contradiction fixed (badge and body now use same source)

