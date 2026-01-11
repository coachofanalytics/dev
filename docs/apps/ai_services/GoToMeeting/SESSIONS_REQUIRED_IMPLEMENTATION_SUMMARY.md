# Sessions Required Per Activity Implementation Summary

**Date:** 2024-12-29  
**Branch:** 25.12_CODA_DEV_CM  
**Status:** ✅ **COMPLETE**

---

## Objective

Implement "sessions_required per activity" policy to drive DAF v2 Start Meeting button visibility. The button should disappear once the required number of sessions is met.

---

## Implementation Summary

### 1. ActivityPolicy Field ✅

**File:** `coda/config/activity_definitions.py`

**Status:** Field already exists (line 70)
- `sessions_required: int = 1` (default: 1)
- Backward compatible - defaults to 1 if not specified

**Examples:**
- `INTERNAL_TRAINING_SESSION`: `sessions_required=5` (5 sessions required)
- `CLIENT_TRAINING_SESSION`: `sessions_required=1` (1 session required)
- `UAT_TESTING_SUPPORT`: `sessions_required=1` (1 session required)

---

### 2. DAF v2 View - Task Dict Fields ✅

**File:** `coda/management/legacy_views.py` (daf_v2_view function)

**Computed Fields Added:**
- `sessions_required`: From activity policy (default: 1, fallback to task.mxpoint/point)
- `sessions_completed`: Count of distinct `meeting_id` values in TaskLinks (where `meeting_id` is not null, includes both auto and manual links)
- `sessions_remaining`: `max(0, sessions_required - sessions_completed)`

**Logic:**
1. Get `sessions_required` from `ActivityPolicy.sessions_required` (preferred)
2. Fallback to `ActivityPolicy.required_meeting_count` if `sessions_required` not set
3. Fallback to `task.mxpoint` or `task.point` if policy doesn't specify
4. Count distinct `meeting_id` values from active TaskLinks
5. Calculate `sessions_remaining = max(0, sessions_required - sessions_completed)`

**Key Code (lines 2005-2048):**
```python
if gate_status['requires_meeting']:
    # Get sessions_required from activity policy
    meeting_required_count = 1  # Default
    if activity_policy:
        if hasattr(activity_policy, 'sessions_required') and activity_policy.sessions_required > 0:
            meeting_required_count = activity_policy.sessions_required
        elif hasattr(activity_policy, 'required_meeting_count') and activity_policy.required_meeting_count > 0:
            meeting_required_count = activity_policy.required_meeting_count
    
    # Fallback to task.mxpoint (or point) if policy doesn't specify
    if meeting_required_count == 1 and (task.mxpoint or task.point):
        meeting_required_count = int(task.mxpoint or task.point or 1)
    
    # Count distinct meeting_ids (include both auto and manual links)
    distinct_meeting_ids = set()
    for link in task_links_list:
        if link.is_active:
            meeting_id = getattr(link, 'meeting_id', None)
            if meeting_id:
                distinct_meeting_ids.add(meeting_id)
    meetings_completed_count = len(distinct_meeting_ids)
    
    # Calculate remaining
    meetings_remaining_count = max(0, meeting_required_count - meetings_completed_count)
    
    # Show button if: requires_meeting AND meeting_join_url exists AND sessions_remaining > 0
    show_start_meeting_button = bool(meeting_join_url) and meetings_remaining_count > 0
```

**Task Dict Fields (lines 2050-2052):**
```python
'sessions_required': meeting_required_count,
'sessions_completed': meetings_completed_count,
'sessions_remaining': meetings_remaining_count,
```

---

### 3. DAF v2 Template Updates ✅

**File:** `coda/management/templates/management/daf/usertasks/employeetasks_v2.html`

**Button Visibility Logic:**
- Show "Start Meeting" button when:
  - `task.requires_meeting == True` AND
  - `task.meeting_join_url` exists AND
  - `task.sessions_remaining > 0`

**Progress Indicator:**
- Shows "Meetings: {sessions_completed}/{sessions_required}" next to the button
- Example: "Meetings: 2/5"

**Warning Message:**
- If `requires_meeting == True` but `meeting_join_url` is missing:
  - Shows "Link Meeting" button
  - Shows warning: "Meeting room not configured — contact admin."

**Template Code (lines 397-416):**
```django
{% elif task.needs_attention_reason_code == 'MEETING_REQUIRED' %}
  {% if task.requires_meeting and task.meeting_join_url and task.sessions_remaining > 0 %}
    <div class="d-flex align-items-center">
      <a href="{% url 'management:launch_meeting' %}?activity_type={{ task.activity_type_slug }}&task_id={{ task.id }}" 
         class="btn btn-success btn-sm flex-fill mr-1" 
         target="_blank"
         title="Start/Join Meeting">
        <i class="fas fa-video"></i> Start Meeting
      </a>
      {% if task.sessions_required > 0 %}
      <small class="text-muted ml-2">Meetings: {{ task.sessions_completed }}/{{ task.sessions_required }}</small>
      {% endif %}
    </div>
  {% elif task.requires_meeting and not task.meeting_join_url %}
    <div class="d-flex align-items-center">
      <a href="{% url 'management:new_evidence' task.id %}" class="btn btn-warning btn-sm flex-fill mr-1">
        <i class="fas fa-video"></i> Link Meeting
      </a>
      <small class="text-warning ml-2"><i class="fas fa-exclamation-triangle"></i> Meeting room not configured — contact admin.</small>
    </div>
  {% endif %}
```

---

### 4. Compliance Reason Formatting ✅

**File:** `coda/management/legacy_views.py`

**Updated Functions:**
- `_determine_needs_attention_reason()`: Now accepts `meetings_completed_count` and `required_meeting_count` parameters
- Uses numeric format: "Meetings: {sessions_completed}/{sessions_required} (need {sessions_remaining} more)."

**Code (lines 3368-3391):**
```python
# Priority 4: Meeting required but missing
if requires_meeting and not has_meeting_evidence:
    # Use numeric format if counts are available
    if required_meeting_count > 0 and meetings_completed_count >= 0:
        sessions_remaining = max(0, required_meeting_count - meetings_completed_count)
        if sessions_remaining > 0:
            return (
                "MEETING_REQUIRED",
                f"Meetings: {meetings_completed_count}/{required_meeting_count} (need {sessions_remaining} more)."
            )
    # ... fallback messages
```

**Attention Reasons Update (lines 2039-2045):**
- Replaces generic "Meeting evidence required but not found" with numeric format
- Format: "Meetings: {sessions_completed}/{sessions_required} (need {sessions_remaining} more)."

---

## Files Changed

### Modified Files:
- `coda/management/legacy_views.py` (daf_v2_view, _determine_needs_attention_reason, compute_task_compliance)
- `coda/management/templates/management/daf/usertasks/employeetasks_v2.html`
- `coda/ai_services/management/commands/analyze_meeting_task_patterns.py` (fixed AttributeError)

### No Changes Needed:
- `coda/config/activity_definitions.py` (sessions_required field already exists)

---

## How to Verify

### 1. Create a Task Requiring Multiple Sessions

**Option A: Use existing activity with sessions_required > 1**
- `INTERNAL_TRAINING_SESSION` has `sessions_required=5`
- Create a task with this activity type

**Option B: Set sessions_required in ActivityPolicy**
- Edit `coda/config/activity_definitions.py`
- Set `sessions_required=3` for an activity (e.g., `CLIENT_TRAINING_SESSION`)
- Create a task with that activity

### 2. Verify Button Appears Initially

1. Open DAF v2 for the user who owns the task
2. Locate the task in the task list
3. **Expected:** "Start Meeting" button should be visible
4. **Expected:** Progress indicator shows "Meetings: 0/5" (or your configured number)

### 3. Link a Meeting and Verify Progress

**Option A: Use autolink (if meeting exists)**
```bash
poetry run python coda/manage.py autolink_meeting_evidence --user-id <USER_ID> --days 30
```

**Option B: Manually link via Django shell**
```python
from management.models import Task, TaskLinks
from ai_services.models import Meeting

task = Task.objects.get(id=<TASK_ID>)
meeting = Meeting.objects.first()  # Or create one

TaskLinks.objects.create(
    task=task,
    link_name="Test Meeting",
    link_url="https://example.com/meeting",
    meeting_id=meeting.meeting_id if meeting else "123456789",
    is_active=True
)
```

### 4. Verify Button Disappears When Requirement Met

1. Link enough meetings to meet `sessions_required`
2. Refresh DAF v2 page
3. **Expected:** "Start Meeting" button should disappear
4. **Expected:** Badge shows "Meetings complete: 5/5" (or your configured number)

### 5. Verify Compliance Reason Format

1. For a task with `sessions_required=5` and `sessions_completed=2`:
2. **Expected:** Reason text: "Meetings: 2/5 (need 3 more)."
3. Check `task.needs_attention_reason_text` in DAF v2

### 6. Verify Meeting Room Warning

1. Create a task with `meeting_required=True` but no `meeting_join_url` configured
2. **Expected:** Shows "Link Meeting" button with warning: "Meeting room not configured — contact admin."

---

## Example Test Case

**Setup:**
- Activity: `INTERNAL_TRAINING_SESSION` (sessions_required=5)
- Task: Create task with this activity
- User: Eunice (ID: 495)

**Steps:**
1. Open DAF v2 for Eunice
2. Find the `INTERNAL_TRAINING_SESSION` task
3. **Verify:** Button shows "Start Meeting" with "Meetings: 0/5"
4. Link 2 meetings (via autolink or manual)
5. **Verify:** Button still shows with "Meetings: 2/5"
6. Link 3 more meetings (total 5)
7. **Verify:** Button disappears, badge shows "Meetings complete: 5/5"

---

## Key Design Decisions

1. **Distinct Meeting IDs:** Counts distinct `meeting_id` values, not total TaskLinks (prevents double-counting same meeting)
2. **Backward Compatibility:** Falls back to `task.mxpoint` or `task.point` if policy doesn't specify `sessions_required`
3. **Default Value:** `sessions_required=1` if not specified (backward compatible)
4. **Button Logic:** Button shows only when `sessions_remaining > 0` (not just `sessions_completed < sessions_required`)
5. **Progress Display:** Shows progress indicator next to button for clarity

---

## Notes

- **Meeting ID Uniqueness:** Assumes each meeting has a unique `meeting_id`. If the same meeting is linked multiple times, it's counted once.
- **Auto vs Manual Links:** Both auto-generated and manually created TaskLinks are counted (as long as they have `meeting_id`)
- **Active Links Only:** Only counts `is_active=True` TaskLinks
- **Template Compatibility:** Template checks both `needs_attention_reason_code == 'MEETING_REQUIRED'` and `show_start_meeting_button` for backward compatibility

---

**Implementation Complete** ✅

