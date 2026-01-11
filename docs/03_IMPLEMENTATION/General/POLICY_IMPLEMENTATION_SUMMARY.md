# Policy Implementation Summary

## Overview

Implemented Group A vs Group B policy enforcement layer with deterministic explainability and meeting source consistency.

## Files Changed

### 1. Policy Resolver Service (NEW)
**File:** `coda/management/services/policy_resolver.py`

**Purpose:** Single source of truth for policy configuration based on employee group.

**Key Features:**
- `PolicyResolver.for_user(user)` → Returns `PolicyConfig` for user's group
- `PolicyConfig` includes:
  - `meeting_required_activity_types` (set)
  - `requirement_required_activity_types` (set)
  - `evidence_minimum_by_activity_type` (dict)
  - `quality_threshold` (default 0.80)

**Policy Differences:**
- **Group A (Stricter):**
  - Meeting required for: INTERNAL_TRAINING_SESSION, SELF_TRAINING_SESSION, CLIENT_TRAINING_SESSION, PRODUCT_BACKLOG_REFINEMENT, PBR_SESSION
  - Evidence minimum: 2 items for training sessions
  - Quality threshold: 0.80

- **Group B (Lighter):**
  - Meeting required for: CLIENT_TRAINING_SESSION, PRODUCT_BACKLOG_REFINEMENT only
  - Evidence minimum: 1 item (default)
  - Quality threshold: 0.80

### 2. Updated Compliance Function
**File:** `coda/management/legacy_views.py:2899`

**Changes:**
- `compute_task_compliance()` now accepts `user` and `policy` parameters
- Uses `PolicyResolver.for_user()` to get policy if not provided
- All compliance checks are now policy-driven:
  - `requires_meeting` from `policy.requires_meeting()`
  - `requires_requirement` from `policy.requires_requirement()`
  - `evidence_minimum` from `policy.get_evidence_minimum()`
  - `quality_threshold` from `policy.quality_threshold`

**Returns:**
- Added `needs_attention_reason_code` (deterministic enum-like string)
- Added `needs_attention_reason_text` (human-readable explanation)
- Added `policy_group` (Group A, Group B, or Group C)

### 3. Deterministic Reason Helper
**File:** `coda/management/legacy_views.py:3092`

**Function:** `_determine_needs_attention_reason()`

**Priority Order:**
1. REQUIREMENT_MISSING
2. EVIDENCE_MISSING
3. EVIDENCE_COUNT_INSUFFICIENT
4. MEETING_REQUIRED
5. CHECKLIST_INCOMPLETE
6. DURATION_MISSING
7. QUALITY_FAIL

**Reason Codes:**
- `REQUIREMENT_MISSING`: "Select the requirement this task is fulfilling."
- `EVIDENCE_MISSING`: "Upload at least 1 evidence item (link or file) with a short description."
- `EVIDENCE_COUNT_INSUFFICIENT`: "Upload at least {N} evidence item(s). Currently have {M}."
- `MEETING_REQUIRED`: "This activity requires meeting proof. Link a meeting or paste the meeting recording URL."
- `CHECKLIST_INCOMPLETE`: "Complete all required checklist items for this activity."
- `DURATION_MISSING`: "Meeting duration is missing or too short. Ensure meeting recording includes duration."
- `QUALITY_FAIL`: "Quality score is below threshold. Review evidence quality and completeness."

### 4. Template Updates
**File:** `coda/management/templates/management/daf/usertasks/employeetasks_v2.html`

**Changes:**
- Shows deterministic `needs_attention_reason_text` on Needs Attention cards
- Shows policy group badge (staff-only): "Policy: Group A" or "Policy: Group B"
- Falls back to `attention_reasons` for backward compatibility

### 5. View Integration
**File:** `coda/management/legacy_views.py:1813`

**Changes:**
- Calls `compute_task_compliance()` with `user=employee_user`
- Passes `needs_attention_reason_code` and `needs_attention_reason_text` to template
- Passes `policy_group` to template

### 6. Meeting Source Consistency
**File:** `coda/management/legacy_views.py:2848`

**Changes:**
- `_safe_meeting_query()` now uses `Meeting._meta.db_table` (dynamic, not hardcoded)
- Actual table: `ai_services_meeting` (Django default)
- All compliance code uses `ai_services.models.Meeting` (canonical)

**File:** `coda/ai_services/models.py:203`

**Changes:**
- Added comment explaining that `db_table = 'gotomeeting_meeting'` was never used
- Actual table is `ai_services_meeting` (Django default)

### 7. Tests (NEW)
**File:** `coda/management/tests/test_policy_enforcement.py`

**Test Coverage:**
- Policy differences between Group A and Group B
- Deterministic reason strings for all failure scenarios
- Reason priority order
- Policy defaults to Group B if no career_state

## Policy Matrix

| Rule | Group A | Group B |
|------|---------|---------|
| **Meeting Required For:** | INTERNAL_TRAINING_SESSION, SELF_TRAINING_SESSION, CLIENT_TRAINING_SESSION, PRODUCT_BACKLOG_REFINEMENT, PBR_SESSION | CLIENT_TRAINING_SESSION, PRODUCT_BACKLOG_REFINEMENT |
| **Requirement Required For:** | SELF_TRAINING_SESSION, INTERNAL_TRAINING_SESSION, CLIENT_TRAINING_SESSION, PRODUCT_BACKLOG_REFINEMENT | SELF_TRAINING_SESSION, INTERNAL_TRAINING_SESSION, CLIENT_TRAINING_SESSION, PRODUCT_BACKLOG_REFINEMENT |
| **Evidence Minimum (INTERNAL_TRAINING_SESSION):** | 2 items | 1 item |
| **Evidence Minimum (Default):** | 1 item | 1 item |
| **Quality Threshold:** | 0.80 | 0.80 |

## Meeting Source Consistency

**Canonical Model:** `ai_services.models.Meeting`  
**Canonical Table:** `ai_services_meeting` (Django default)

**Enforcement:**
- All compliance code uses `ai_services.models.Meeting`
- `_safe_meeting_query()` checks `Meeting._meta.db_table` (dynamic)
- Legacy `getdata_gotomeetings` only used for one-time migration commands

## Verification Commands

```bash
# 1. System check
poetry run python coda/manage.py check
# Expected: "System check identified no issues (0 silenced)."

# 2. Run tests
poetry run python coda/manage.py test management.tests.test_policy_enforcement -v 2
# Expected: All tests pass

# 3. Manual verification (see scenarios below)
```

## Manual Verification Scenarios

### Scenario 1: Group B User - Internal Training Task
**Steps:**
1. Create user with `EmployeeCareerState(group='B')`
2. Create task with `activity_name='INTERNAL_TRAINING_SESSION'`
3. Navigate to `/management/daf/v2/`
4. Check task card

**Expected:**
- Policy badge (staff): "Policy: Group B"
- Meeting NOT required (no meeting chip warning)
- Evidence minimum: 1 item
- If evidence missing: Reason shows "EVIDENCE_MISSING"

### Scenario 2: Group A User - Same Task
**Steps:**
1. Change user's `EmployeeCareerState.group` to 'A'
2. Refresh DAF page
3. Check same task card

**Expected:**
- Policy badge (staff): "Policy: Group A"
- Meeting REQUIRED (meeting chip shows warning if missing)
- Evidence minimum: 2 items
- If evidence count = 1: Reason shows "EVIDENCE_COUNT_INSUFFICIENT: Upload at least 2 evidence item(s). Currently have 1."

### Scenario 3: Needs Attention Reason Display
**Steps:**
1. Create task with missing requirement (required activity type)
2. Navigate to `/management/daf/v2/`
3. Check Needs Attention tab

**Expected:**
- Task shows in Needs Attention tab
- Card shows: "⚠ Reason: Select the requirement this task is fulfilling."
- Next action button: "Select Requirement"

## Remaining Work (Future)

1. **Migrate Legacy DAF:** Update legacy DAF to use `compute_task_compliance()` with policy
2. **Refactor TaskQualityGateService:** Consider using policy resolver instead of hardcoded constants
3. **Add Policy Admin UI:** Allow managers to configure policy rules via admin interface
4. **Add Group C Policy:** Currently Group C uses Group B config (can be customized later)

## Notes

- ✅ No breaking changes to existing URLs
- ✅ Backward compatible (falls back to Group B if no career_state)
- ✅ Policy-driven compliance (no ad-hoc booleans)
- ✅ Deterministic explainability (one reason per task)
- ✅ Meeting source consistent (only ai_services.Meeting in compliance)
- ✅ Tests cover policy differences and reason strings

