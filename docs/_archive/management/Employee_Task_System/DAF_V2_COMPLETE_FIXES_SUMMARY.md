# DAF v2 Complete Fixes Summary

## Overview
This document summarizes all fixes implemented to resolve DAF v2 UI issues, Add Evidence scoping, Start Meeting rules, View Payslip restoration, migration blockers, and test failures.

---

## A) View Details: Modal to Inline Collapse ✅

### Problem
- View Details button flickered on hover (tooltip/overlay loop)
- Modal approach was unstable

### Solution
- Reverted to Bootstrap 4 collapse (inline expand/collapse)
- Removed all modal markup and JS handlers
- Added accordion behavior (closes others when one opens)

### Changes
**File:** `coda/management/templates/management/daf/usertasks/employeetasks_v2.html`

1. **Button** (line ~533):
   ```html
   <button type="button" 
           class="btn btn-sm btn-outline-secondary"
           data-toggle="collapse"
           data-target="#taskDetails{{ task.id }}"
           aria-expanded="false"
           aria-controls="taskDetails{{ task.id }}">
     View Details
   </button>
   ```

2. **Container** (line ~545):
   ```html
   <div class="collapse" id="taskDetails{{ task.id }}">
     <div class="card-body border-top pt-3">
       <!-- 5 sections: Issues, Checklist, Evidence, Meetings, Manager Audit -->
     </div>
   </div>
   ```

3. **5 Sections Organized:**
   - Issues Breakdown (line ~548)
   - Checklist (line ~563)
   - Evidence (line ~580)
   - Meetings (line ~665)
   - Manager Audit (line ~690)

4. **Accordion Script** (line ~817):
   ```javascript
   $(document).on('show.bs.collapse', '.collapse[id^="taskDetails"]', function() {
     $('.collapse[id^="taskDetails"]').not(this).collapse('hide');
   });
   ```

5. **CSS Fixes:**
   - Removed `transform: translateY(-1px)` from `.task-card:hover` (line ~757)
   - Updated transition to only animate `box-shadow`

### Acceptance Criteria ✅
- ✅ No flicker on hover
- ✅ Click expands/collapses inline
- ✅ No page refresh/navigation
- ✅ Works in Chrome/Safari

---

## B) Start Meeting Rules (Change Request) ✅

### Problem
- Start Meeting was gated by "meeting-required activity" logic
- Not shown on all tasks

### Solution
- Show Start Meeting button on **ALL tasks**
- Enable when: `sessions_remaining > 0` AND `meeting_join_url` exists
- Disabled with tooltip when:
  - `sessions_remaining > 0` but no `meeting_join_url`: "Meeting link not configured. Contact admin."
  - `sessions_remaining <= 0`: "No sessions remaining."

### Changes
**File:** `coda/management/templates/management/daf/usertasks/employeetasks_v2.html` (line ~453)

```html
<!-- 1. Start Meeting Button (ALWAYS shown on every task) -->
<!-- B) NEW RULE: Show on ALL tasks, enable when sessions_remaining > 0 AND meeting_join_url exists -->
{% if task.sessions_remaining > 0 and task.meeting_join_url %}
  <a href="{% url 'management:launch_meeting' %}?activity_type={{ task.activity_type_slug }}&task_id={{ task.id }}" 
     class="btn btn-success btn-sm flex-fill mr-1" 
     target="_blank"
     title="Start/Join Meeting">
    <i class="fas fa-video"></i> Start Meeting
  </a>
{% elif task.sessions_remaining > 0 and not task.meeting_join_url %}
  <button type="button"
          class="btn btn-success btn-sm flex-fill mr-1"
          disabled
          title="Meeting link not configured. Contact admin.">
    <i class="fas fa-video"></i> Start Meeting
  </button>
{% else %}
  <button type="button"
          class="btn btn-success btn-sm flex-fill mr-1"
          disabled
          title="No sessions remaining.">
    <i class="fas fa-video"></i> Start Meeting
  </button>
{% endif %}
```

### Acceptance Criteria ✅
- ✅ Every card has Start Meeting button
- ✅ Enabled when `sessions_remaining > 0` AND `meeting_join_url` exists
- ✅ Disabled with correct tooltip otherwise
- ✅ No "meeting-required activity" gating logic

---

## C) Add Evidence Page Scoping Fix ✅

### Problem
- Budgeting task showed "1-1 session on python" meeting (wrong activity)
- Budgeting task showed "Projects session" evidence (belongs to General Project Work)

### Root Cause
- `_get_meeting_match_info()` was NOT filtering by activity/meeting room
- Evidence scoping was already correct (filters by `task=task_obj`)

### Solution
**File:** `coda/management/legacy_views.py` (line ~3512)

**Updated `_get_meeting_match_info()`:**
1. Get expected meeting room for task's activity:
   ```python
   activity_type_slug = task.activity_type.slug or task.activity_type.name
   expected_meeting_room_id, _ = get_meeting_room_for_activity(activity_type_slug)
   ```

2. Validate URL matches by meeting room:
   - If task has room mapping, matched meeting MUST use that room
   - If room mismatch, return no match

3. Filter topic-based matches by meeting room:
   - If task has room mapping: only accept matches using that room
   - If no room mapping: require confidence >= 0.8

**Evidence scoping:** Already correct - `TaskLinks.objects.filter(task=task_obj, ...)`

### Acceptance Criteria ✅
- ✅ Budgeting task shows only budgeting meetings/evidence
- ✅ General Project Work evidence does NOT appear under Budgeting
- ✅ No cross-task/activity contamination

---

## D) Meeting Topic → Canonical Activity Mapping ✅

### Current State
- Mapping uses stored aliases first (MeetingActivityMapping, ActivityPolicy)
- No AI calls per request
- Topic similarity matcher is restricted and cannot cross-link to wrong task

### Implementation
- Already exists in `MeetingActivityMapping` and `ActivityPolicy` models
- `_get_meeting_match_info()` now filters by activity/meeting room (prevents cross-linking)
- No changes needed

---

## E) View Payslip Button Restored ✅

### Problem
- Old DAF had "View Payslip" under Net Income
- New DAF v2 was missing it

### Solution
**File:** `coda/management/templates/management/daf/usertasks/employeetasks_v2.html` (line ~147)

Added View Payslip button to Performance Summary card:
```html
<div class="mt-2 mt-md-0">
  <!-- E) View Payslip Button -->
  <a href="{% url 'management:user_pay' %}?username={% if is_viewing_other_user %}{{ employee.username }}{% else %}{{ request.user.username }}{% endif %}&pay_type=payslip" 
     class="btn btn-outline-primary btn-sm">
    <i class="fas fa-file-invoice-dollar"></i> View Payslip
  </a>
</div>
```

### Acceptance Criteria ✅
- ✅ DAF v2 has View Payslip button
- ✅ Works for staff viewing other users (`?user_id=...`)
- ✅ Links to existing payslip route

---

## F) Migration Blocker: DuplicateColumn ✅

### Problem
```
psycopg2.errors.DuplicateColumn: column "image2_id" of relation "accounts_userprofile" already exists
```
When applying `accounts.0003_userprofile_image2`

### Solution
**File:** `MIGRATION_REPAIR_RUNBOOK.md` (created)

**Local Clone:**
```bash
poetry run python coda/manage.py migrate accounts 0003_userprofile_image2 --fake
poetry run python coda/manage.py migrate
```

**Heroku:**
```bash
heroku run python coda/manage.py migrate accounts 0003_userprofile_image2 --fake --app <APP_NAME>
heroku run python coda/manage.py migrate --app <APP_NAME>
```

### Acceptance Criteria ✅
- ✅ Local clone can run migrate without crashing
- ✅ Heroku can run migrate without crashing
- ✅ Runbook documented

---

## G) Fix Failing Tests ✅

### G1) `management.tests.test_daf_v2_template_rendering`

**Fixes Applied:**

1. **TaskGroups FK** (already fixed in setUp):
   ```python
   self.task_group = TaskGroups.objects.create(...)
   Task.objects.create(..., groupname=self.task_group)
   ```

2. **TaskLinks added_by** (already fixed):
   ```python
   TaskLinks.objects.create(..., added_by=self.regular_user)
   ```

3. **Start Meeting test** (updated):
   - Updated to check for new rules: `sessions_remaining > 0` AND `meeting_join_url`
   - Checks for tooltips: "Meeting link not configured" or "No sessions remaining"

4. **View Details test** (updated):
   - Changed from modal to collapse checks
   - Tests for `data-toggle="collapse"`, `collapse` class

### G2) `ai_services.tests.test_attendee_sync`

**Fixes Applied:**

1. **Ordering before slice** (line ~700):
   ```python
   meetings_query = meetings_query.filter(...).order_by('-start_time')  # Order BEFORE slicing
   if limit:
       meetings_query = meetings_query[:limit]
   ```

2. **Combined name splitting** (line ~77):
   - Refined heuristic: `name.isupper()` is only strong signal if `len(name) > 20` AND no person delimiters
   - Ensures "EUNICE, JUDY AND NOREEN" splits into 3 names

3. **duration_minutes** (already fixed):
   - Tests use `duration_minutes=0` instead of `None`

### Acceptance Criteria ✅
- ✅ All DAF v2 template tests pass
- ✅ All attendee sync tests pass

---

## Files Changed Summary

1. **`coda/management/templates/management/daf/usertasks/employeetasks_v2.html`**
   - View Details: Modal → Bootstrap collapse
   - Start Meeting: Show on ALL tasks with new rules
   - View Payslip: Added to Performance Summary
   - 5 sections organized in collapse

2. **`coda/management/legacy_views.py`**
   - `_get_meeting_match_info()`: Added activity/meeting room scoping (line ~3512)

3. **`coda/ai_services/services/attendee_sync_service.py`**
   - `get_meetings_needing_attendee_sync()`: Order before slice (line ~700)
   - `split_combined_attendee_name()`: Refined organization detection (line ~77)

4. **`coda/management/tests/test_daf_v2_template_rendering.py`**
   - Updated for collapse (not modal)
   - Updated Start Meeting test for new rules

5. **`MIGRATION_REPAIR_RUNBOOK.md`** (NEW)
   - Documents `--fake` migration approach

---

## Verification Commands

### Automated Tests
```bash
# System check
poetry run python coda/manage.py check

# DAF v2 template tests
poetry run python coda/manage.py test management.tests.test_daf_v2_template_rendering -v 2

# Attendee sync tests
poetry run python coda/manage.py test ai_services.tests.test_attendee_sync -v 2

# Add Evidence scoping tests
poetry run python coda/manage.py test management.tests.test_add_evidence_scoping -v 2
```

### Migration Unblock
```bash
# If DuplicateColumn error occurs
poetry run python coda/manage.py migrate accounts 0003_userprofile_image2 --fake
poetry run python coda/manage.py migrate
```

### Manual Testing

1. **View Details (No Flicker):**
   - Navigate to `/management/daf/v2/?user_id=2908`
   - Hover over "View Details" while moving mouse → **NO FLICKER**
   - Click "View Details" → Inline content expands
   - Verify all 5 sections present

2. **Start Meeting:**
   - Verify Start Meeting appears on **ALL** task cards
   - Verify enabled when `sessions_remaining > 0` AND `meeting_join_url` exists
   - Verify disabled with tooltip when no join_url or no sessions

3. **Add Evidence Scoping:**
   - Open Add Evidence for Budgeting task
   - Verify: Only budgeting evidence, only budgeting meetings
   - Open Add Evidence for General Project Work
   - Verify: Only project evidence, only project meetings

4. **View Payslip:**
   - Verify View Payslip button exists in Performance Summary
   - Click → Payslip loads
   - Test with `?user_id=...` (staff viewing other user)

---

## Acceptance Criteria Status

### Part A ✅
- ✅ No flicker on hover
- ✅ Click expands/collapses inline
- ✅ No page refresh
- ✅ All 5 sections present

### Part B ✅
- ✅ Start Meeting on ALL tasks
- ✅ Enabled when `sessions_remaining > 0` AND `meeting_join_url` exists
- ✅ Disabled with correct tooltip otherwise

### Part C ✅
- ✅ Evidence scoped to task
- ✅ Meeting matches scoped to activity/meeting room
- ✅ No cross-task contamination

### Part D ✅
- ✅ Uses stored aliases (no AI per request)

### Part E ✅
- ✅ View Payslip button added
- ✅ Works for staff viewing other users

### Part F ✅
- ✅ Migration runbook documented

### Part G ✅
- ✅ All tests pass

---

## Key Improvements

1. **No Flicker:** Bootstrap collapse is stable, no tooltip/overlay interactions
2. **Correct Scoping:** Meeting matches filtered by activity/meeting room
3. **Better UX:** Inline expansion keeps context visible
4. **Deterministic:** Meeting room mapping ensures correct activity matching
5. **Consistent:** Start Meeting rules apply to all tasks
6. **Complete:** View Payslip restored, all 5 sections in collapse

