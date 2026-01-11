# Evidence & Meeting Audit Report

**Date:** 2025-01-XX  
**Goal:** Identify canonical Meeting source, consolidate evidence checks, fix UI contradictions

---

## A. Meeting References Audit

### A.1 Meeting Models Found

| Model | File | DB Table | Status | Purpose |
|-------|------|----------|--------|---------|
| `ai_services.Meeting` | `coda/ai_services/models.py:127` | `ai_services_meeting` | ✅ **CANONICAL** | Normalized meeting model (one record per meeting) |
| `ai_services.GotoMeetings` | `coda/ai_services/models.py:99` | `getdata_gotomeetings` | ⚠️ Legacy | Deprecated denormalized model (kept for backward compatibility) |
| `management.Meetings` | `coda/management/models.py:1318` | `management_meetings` | ❓ Unrelated | Different model (not used for DAF/evidence matching) |

### A.2 Actual DB Tables (from runtime)

```
=== Meeting Models ===
ai_services.Meeting: ai_services_meeting
ai_services.GotoMeetings: getdata_gotomeetings
management.Meetings: management_meetings

=== Actual DB Tables (containing meet) ===
  - ai_services_meeting          ← CANONICAL for DAF/evidence matching
  - ai_services_meetingattendee
  - getdata_gotomeetings          ← Legacy (deprecated)
  - gotomeeting_sync_run
  - management_meetings           ← Unrelated
  - meeting_activity_mapping
  - meeting_activity_tag_suggestion
  - meeting_summary_suggestion
```

### A.3 Meeting Model Usage Locations

| Location | Model Used | Purpose | Status |
|----------|-----------|---------|--------|
| `coda/management/legacy_views.py:2848` | `ai_services.Meeting` | `_safe_meeting_query()` - DAF v2 meeting matching | ✅ Fixed (now checks `ai_services_meeting`) |
| `coda/ai_services/services/meeting_evidence_matcher.py` | `ai_services.Meeting` | Evidence-to-meeting matching | ✅ Correct |
| `coda/ai_services/views.py` | `ai_services.Meeting` | Meeting sync/persistence | ✅ Correct |
| `coda/management/legacy_views.py:2950` | `ai_services.Meeting` | Compliance check for meeting evidence | ✅ Correct |

**Note:** The commented `db_table = 'gotomeeting_meeting'` in `Meeting.Meta` was **never used**. The actual table is `ai_services_meeting` (Django default).

---

## B. Evidence References Audit

### B.1 Evidence Model

**Model:** `management.models.TaskLinks`  
**File:** `coda/management/models.py:874`  
**Key Fields:**
- `task` (ForeignKey → Task)
- `link` (CharField, max_length=1000) - URL to evidence
- `doc` (FileField) - Uploaded file
- `drive_link` (URLField) - Google Drive link
- `is_active` (BooleanField) - Active flag
- `is_auto_generated` (BooleanField) - Auto-created from meeting
- `meeting_id` (CharField) - GoToMeeting meeting_id if auto-generated
- `link_name` (CharField) - Display name (NOT `topic_name` - that field doesn't exist)

### B.2 Evidence Existence Checks (Before Fix)

| Location | Check Method | Issue |
|----------|--------------|-------|
| `coda/management/legacy_views.py:1256` | `TaskLinks.objects.filter(task=task, is_active=True).exists()` | Ad-hoc query |
| `coda/management/legacy_views.py:1792` | `gate_status['has_evidence']` | Uses TaskQualityGateService (inconsistent) |
| `coda/management/legacy_views.py:2931` | `any(link.is_active for link in task_links)` | Inline check in `compute_task_compliance` |
| `coda/management/services/daf_summary_service.py:688` | `task.tasklinks.exists()` | Ad-hoc check |
| `coda/management/templates/.../employeetasks_v2.html:421` | `task.gate_status.has_evidence` | Template check (contradicts badge) |

### B.3 Invalid Field Usage

**Error:** `Cannot resolve keyword 'topic_name' into field`

| Location | Usage | Fix |
|----------|-------|-----|
| `coda/management/legacy_views.py:1822` | ✅ Already fixed: `link.link_name or 'Evidence'` | No change needed |

---

## C. UI Contradictions Found

### C.1 Evidence Badge vs Evidence Body

**Location:** `coda/management/templates/management/daf/usertasks/employeetasks_v2.html`

**Problem:**
- Line 259-267: Badge shows `Evidence: ✓` (complete) based on `task.compliance_chips.evidence.status`
- Line 420-428: Body shows "No evidence uploaded yet" based on `task.gate_status.has_evidence` or `task.evidence_list|length`

**Root Cause:** Two different sources of truth:
1. `compliance_chips.evidence.status` (from `compute_task_compliance`)
2. `gate_status.has_evidence` / `evidence_list` (from `TaskQualityGateService`)

**Fix:** Use `compliance_chips.evidence.status` as single source of truth in template.

---

## D. Implementation Plan

### D.1 Create Shared Evidence Summary Service

**File:** `coda/management/services/evidence_summary_service.py` (NEW)

**Function:** `get_task_evidence_summary(task, task_links=None, meeting_match_info=None) -> dict`

**Returns:**
- `count_active`: int
- `count_usable`: int (has link/doc/drive_link)
- `items_qs`: QuerySet/list of active TaskLinks
- `has_minimum`: bool
- `status`: 'missing' | 'partial' | 'complete' | 'auto_pending'
- `reasons_if_fail`: List[str]
- `has_auto_generated`: bool

### D.2 Update `compute_task_compliance` to Use Evidence Summary

**File:** `coda/management/legacy_views.py:2888`

**Change:** Replace inline evidence checks with `get_task_evidence_summary()` call.

### D.3 Fix Template Contradiction

**File:** `coda/management/templates/management/daf/usertasks/employeetasks_v2.html`

**Change:** Use `task.compliance_chips.evidence.status` consistently for both badge and body.

### D.4 Fix Meeting Table Check

**File:** `coda/management/legacy_views.py:2848`

**Change:** Check `Meeting._meta.db_table` (which is `ai_services_meeting`) instead of hardcoded `'getdata_gotomeetings'`.

---

## E. Files Changed

1. ✅ `coda/management/services/evidence_summary_service.py` (NEW)
2. ✅ `coda/management/legacy_views.py` (Updated `compute_task_compliance`, `_safe_meeting_query`, evidence list building)
3. ✅ `coda/management/templates/management/daf/usertasks/employeetasks_v2.html` (Fixed contradiction)
4. ✅ `coda/ai_services/models.py` (Added comment about table name)

---

## F. Verification Commands

```bash
# 1. System check
poetry run python coda/manage.py check

# 2. Run tests
poetry run python coda/manage.py test management.tests.test_daf_v2_truthfulness -v 2

# 3. Manual verification scenarios
```

### Manual Verification Scenarios

**Scenario 1: Task with 0 evidence**
- Expected: Badge shows `Evidence: ✗`, body shows "No evidence uploaded yet", CTA shows "Upload Evidence"

**Scenario 2: Task with evidence but inactive**
- Expected: Badge shows `Evidence: ✗`, body shows "No evidence uploaded yet", reason: "evidence inactive"

**Scenario 3: Task with valid evidence**
- Expected: Badge shows `Evidence: ✓`, body shows "Evidence: N item(s)", NO "No evidence uploaded" warning

---

## G. Remaining Risks

1. **Legacy DAF:** May still use ad-hoc evidence checks. Should migrate to `evidence_summary_service` in future.
2. **TaskQualityGateService:** Duplicates some logic. Should be refactored to use `evidence_summary_service` in future.
3. **DAF Summary Service:** Uses `task.tasklinks.exists()` - should use `evidence_summary_service` for consistency.

---

## H. Summary

✅ **Canonical Meeting Model:** `ai_services.Meeting` → `ai_services_meeting` table  
✅ **Evidence Summary Service:** Created as single source of truth  
✅ **Template Contradiction:** Fixed (badge and body now use same source)  
✅ **Meeting Table Check:** Fixed (uses `Meeting._meta.db_table`)  
✅ **Invalid Field Usage:** No `topic_name` usage found (already using `link_name`)

**Next Steps:**
1. Run verification commands
2. Test manual scenarios
3. Consider migrating legacy DAF to use `evidence_summary_service`

