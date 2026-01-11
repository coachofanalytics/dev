# DAF v2 Final Fixes - Complete Implementation

## Summary
Fixed View Details hover flicker by reverting to Bootstrap collapse (inline expand/collapse) and fixed Add Evidence page scoping to prevent cross-task/activity contamination.

## Part A: Modal to Inline Collapse Revert ✅

### Changes Made

1. **Button Markup** (line ~468)
   - Changed from modal trigger to Bootstrap collapse toggle
   - Uses `data-toggle="collapse"` and `data-target="#taskDetails{{ task.id }}"`
   - Removed `title` attribute (prevents native tooltip)
   - Added `aria-controls` for accessibility

2. **Container** (line ~480)
   - Changed from `<div class="modal fade">` to `<div class="collapse">`
   - Placed directly under CTA row within the card
   - All 5 content sections preserved (Issues, Checklist, Evidence, Meetings, Manager Audit)

3. **CSS Fixes**
   - Removed `transform: translateY(-1px)` from `.task-card:hover` (line ~710)
   - Updated transition to only animate `box-shadow` (line ~707)
   - Removed custom inline styles (Bootstrap handles collapse)

4. **JavaScript**
   - Added accordion behavior: closes other collapses when one opens (line ~758)
   - Uses Bootstrap's `show.bs.collapse` event
   - No custom hover handlers, no tooltip interference

### Files Changed
- `coda/management/templates/management/daf/usertasks/employeetasks_v2.html`

---

## Part B: Add Evidence Scoping Fix ✅

### Problem
Add Evidence page was showing:
- Evidence from other tasks (e.g., "Projects session" on Budgeting task)
- Meeting matches from other activities (e.g., "1-1 session on python" on Budgeting task)

### Root Cause
1. **Evidence scoping:** Already correct - `get_user_evidence_for_task()` filters by `task=task_obj`
2. **Meeting match scoping:** `_get_meeting_match_info()` was NOT filtering by activity/meeting room

### Fix Applied

**File:** `coda/management/legacy_views.py` (line ~3512)

**Changes to `_get_meeting_match_info()`:**

1. **Get expected meeting room for task's activity:**
   ```python
   activity_type_slug = task.activity_type.slug or task.activity_type.name
   expected_meeting_room_id, _ = get_meeting_room_for_activity(activity_type_slug)
   ```

2. **Validate URL matches by meeting room:**
   - If task has a meeting room mapping, matched meeting MUST use that room
   - If room mismatch, return no match (don't show wrong activity's meeting)

3. **Filter topic-based matches by meeting room:**
   - If task has room mapping: only accept matches using that room
   - If no room mapping: require confidence >= 0.8 to avoid cross-activity matches

**Evidence scoping:** Already correct - `TaskLinks.objects.filter(task=task_obj, ...)` ensures strict task scoping.

### Files Changed
- `coda/management/legacy_views.py` - `_get_meeting_match_info()` function (line ~3512)
- Removed duplicate function definition (line ~3716)

---

## Part C: AI Canonicalization (Conceptual)

**Current State:**
- Canonicalization should be done during ingestion or periodic reconciliation
- Store mappings in DB (Editable, MeetingActivityMapping, or Python dict)
- DAF runtime uses stored canonical fields, not OpenAI calls per request

**Implementation:** Already exists in `MeetingActivityMapping` and `ActivityPolicy` models. No changes needed.

---

## Part D: Migration Blocker

**Documented in:** `MIGRATION_REPAIR_RUNBOOK.md`

**Commands:**
```bash
# Local clone
poetry run python coda/manage.py migrate accounts 0003_userprofile_image2 --fake
poetry run python coda/manage.py migrate

# Heroku
heroku run python coda/manage.py migrate accounts 0003_userprofile_image2 --fake --app <APP_NAME>
heroku run python coda/manage.py migrate --app <APP_NAME>
```

---

## Tests Updated

1. **`coda/management/tests/test_daf_v2_template_rendering.py`**
   - Updated to check for Bootstrap collapse instead of modal
   - Tests button attributes: `data-toggle="collapse"`, `data-target`, `aria-controls`
   - Tests inline container: `collapse` class, `taskDetails` ID

2. **`coda/management/tests/test_add_evidence_scoping.py`** (NEW)
   - Tests evidence list scoping to task
   - Tests meeting match scoping to activity/meeting room
   - Verifies cross-task/activity contamination is prevented

---

## Verification Commands

### Automated Tests
```bash
# DAF v2 template tests
poetry run python coda/manage.py test management.tests.test_daf_v2_template_rendering -v 2

# Add Evidence scoping tests
poetry run python coda/manage.py test management.tests.test_add_evidence_scoping -v 2

# System check
poetry run python coda/manage.py check
```

### Manual Testing

1. **View Details (No Flicker):**
   - Navigate to `/management/daf/v2/?user_id=2908`
   - Hover over "View Details" button while moving mouse → **NO FLICKER**
   - Click "View Details" → Inline content expands
   - Click again → Collapses
   - Open another task's details → Previous one closes (accordion)

2. **Add Evidence Scoping:**
   - Open Add Evidence for Budgeting task
   - Verify: Only shows budgeting evidence, only matches budgeting meetings
   - Open Add Evidence for General Project Work task
   - Verify: Only shows project evidence, only matches project meetings
   - Verify: "Projects session" evidence only appears under Project task
   - Verify: "1-1 session on python" meeting only appears under Training task

---

## Files Changed Summary

1. **`coda/management/templates/management/daf/usertasks/employeetasks_v2.html`**
   - Button: Modal → Bootstrap collapse (line ~468)
   - Container: Modal → Inline collapse (line ~480)
   - CSS: Removed transform from hover (line ~710)
   - JS: Added accordion behavior (line ~758)

2. **`coda/management/legacy_views.py`**
   - `_get_meeting_match_info()`: Added activity/meeting room scoping (line ~3512)
   - Removed duplicate function definition (line ~3716)

3. **`coda/management/tests/test_daf_v2_template_rendering.py`**
   - Updated tests for Bootstrap collapse

4. **`coda/management/tests/test_add_evidence_scoping.py`** (NEW)
   - Tests for evidence and meeting match scoping

---

## Acceptance Criteria Status

### Part A ✅
- ✅ Hovering "View Details" while moving mouse: **NO FLICKER**
- ✅ Clicking "View Details": Inline content toggles reliably
- ✅ No page refresh/navigation
- ✅ Accordion behavior: only one open at a time

### Part B ✅
- ✅ Evidence list scoped strictly to task (already correct)
- ✅ Meeting match scoped to task's activity + meeting room
- ✅ Cross-task/activity contamination prevented
- ✅ Tests added to verify scoping

### Part C ✅
- ✅ Conceptual: AI canonicalization should be DB-based, not per-request
- ✅ Implementation already exists (MeetingActivityMapping, ActivityPolicy)

### Part D ✅
- ✅ Migration runbook documented

---

## Key Improvements

1. **No Flicker:** Bootstrap collapse is stable, no tooltip/overlay interactions
2. **Correct Scoping:** Meeting matches filtered by activity/meeting room
3. **Better UX:** Inline expansion keeps context visible
4. **Deterministic:** Meeting room mapping ensures correct activity matching

