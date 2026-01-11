# Meeting Quota Implementation Summary

**Branch:** 25.12_CODA_DEV_CM  
**Date:** 2024-12-29  
**Status:** ✅ Implementation complete

---

## Goal

Make the "Start Meeting" button in DAF v2 always visible for meeting-required activities, and automatically hide/disable it once the employee has completed the required number of meetings for that activity (quota).

---

## Implementation

### ✅ TASK 1: Extended ActivityPolicy with `required_meeting_count`

**File:** `coda/config/activity_definitions.py`

**Changes:**
- `required_meeting_count` field already exists in `ActivityPolicy` dataclass (line 69)
- Set `required_meeting_count=0` for meeting-required activities:
  - `INTERNAL_TRAINING_SESSION` (line 137)
  - `PRODUCT_BACKLOG_REFINEMENT` (line 215)
  - `UAT_TESTING_SUPPORT` (line 477)
- Value `0` means "use default" (task.mxpoint or task.point)

**Code Location:** Lines 113-137, 190-215, 453-477

---

### ✅ TASK 2: Compute meeting quota progress in DAF v2 task_dict

**File:** `coda/management/legacy_views.py` (daf_v2_view task_dict builder)

**Changes:**
- **Lines 1999-2024:** Added meeting quota computation:
  - `required_meeting_count`: From `activity_policy.required_meeting_count` or default to `task.mxpoint` (or `task.point`)
  - `meetings_completed_count`: Count of `TaskLinks` with `is_active=True` AND (`meeting_id` is not null OR `is_auto_generated=True`)
  - `meetings_remaining_count`: `max(0, required - completed)`
  - `show_start_meeting_button`: `requires_meeting AND meeting_join_url AND meetings_remaining_count > 0`
- Added these fields to `task_dict` (lines 2026-2029)

**Code Location:** Lines 1999-2024, 2026-2029

---

### ✅ TASK 3: Updated DAF v2 template to use `show_start_meeting_button`

**File:** `coda/management/templates/management/daf/usertasks/employeetasks_v2.html`

**Changes:**
- **Lines 405-417:** Updated button visibility logic:
  - Show "Start Meeting" button when `task.show_start_meeting_button` is true (not tied to Needs Attention)
  - Show quota progress badge on button: `{{ task.meetings_completed_count }}/{{ task.required_meeting_count }}`
  - When quota met (`meetings_remaining_count == 0`), show status label: "Meeting quota met (X/Y)"
  - Button is always visible for meeting-required activities (not just when in "Needs Attention")

**Code Location:** Lines 405-417

---

### ✅ TASK 4: Updated reason strings to mention meeting quota

**File:** `coda/management/legacy_views.py` (function: `_determine_needs_attention_reason`)

**Changes:**
- **Lines 3269-3289:** Added parameters:
  - `meetings_completed_count: int = 0`
  - `required_meeting_count: int = 0`
  - `**kwargs` for backward compatibility
- **Lines 3329-3365:** Enhanced MEETING_REQUIRED reason text:
  - If quota info available: `"Meetings completed: X/Y (need Z more). Use 'Start Meeting' from DAF so the system can match it."`
  - Falls back to generic message if quota not available

**Code Location:** Lines 3269-3289, 3329-3365

---

## Files Modified

1. **`coda/config/activity_definitions.py`**
   - Lines 113-137: Added `required_meeting_count=0` to `INTERNAL_TRAINING_SESSION`
   - Lines 190-215: Added `required_meeting_count=0` to `PRODUCT_BACKLOG_REFINEMENT`
   - Lines 453-477: Added `required_meeting_count=0` to `UAT_TESTING_SUPPORT`

2. **`coda/management/legacy_views.py`**
   - Lines 1999-2024: Added meeting quota computation logic
   - Lines 2026-2029: Added quota fields to `task_dict`
   - Lines 3269-3289: Updated `_determine_needs_attention_reason` signature
   - Lines 3329-3365: Enhanced MEETING_REQUIRED reason text with quota info

3. **`coda/management/templates/management/daf/usertasks/employeetasks_v2.html`**
   - Lines 405-417: Updated button visibility and quota display

---

## Verification

### 1) Django Check
```bash
poetry run python coda/manage.py check
```

**Expected:** ✅ No errors

---

### 2) Shell Command: Verify Meeting Quota for Sample User

```bash
poetry run python coda/manage.py shell << 'EOF'
from management.models import Task, TaskLinks
from django.contrib.auth import get_user_model
User = get_user_model()

# Pick a user with meeting-required tasks
user = User.objects.filter(is_active=True).first()
if not user:
    print("No active users found")
    exit()

# Get meeting-required tasks for this user
tasks = Task.objects.filter(
    employee=user,
    is_active=True,
    activity_type__slug__in=['UAT_TESTING_SUPPORT', 'INTERNAL_TRAINING_SESSION', 'PRODUCT_BACKLOG_REFINEMENT']
)[:5]

print(f"\nMeeting Quota Status for {user.username} (ID: {user.id})\n")
print("=" * 80)

for task in tasks:
    activity_slug = task.activity_type.slug if task.activity_type else 'N/A'
    
    # Get required count (from policy or default)
    from coda.config.activity_definitions import ACTIVITY_POLICIES
    policy = ACTIVITY_POLICIES.get(activity_slug)
    required = 0
    if policy and hasattr(policy, 'required_meeting_count'):
        required = policy.required_meeting_count
    if required == 0:
        required = int(task.mxpoint or task.point or 0)
    
    # Count completed meetings
    completed = TaskLinks.objects.filter(
        task=task,
        is_active=True
    ).filter(
        Q(meeting_id__isnull=False) | Q(is_auto_generated=True)
    ).count()
    
    remaining = max(0, required - completed)
    show_button = required > 0 and remaining > 0
    
    print(f"\nTask ID: {task.id}")
    print(f"  Activity: {activity_slug}")
    print(f"  Required: {required}")
    print(f"  Completed: {completed}")
    print(f"  Remaining: {remaining}")
    print(f"  Show Button: {show_button}")
    print(f"  Max Points: {task.mxpoint}, Points: {task.point}")

print("\n" + "=" * 80)
EOF
```

**Expected Output:**
```
Meeting Quota Status for <username> (ID: <id>)

================================================================================

Task ID: <id>
  Activity: UAT_TESTING_SUPPORT
  Required: <count>
  Completed: <count>
  Remaining: <count>
  Show Button: True/False
  Max Points: <value>, Points: <value>
...
```

---

## Summary

**Implementation:** 4/4 tasks complete  
**Status:** Ready for testing  
**Breaking Changes:** None  
**Backward Compatible:** Yes (defaults to task.mxpoint/point if policy doesn't specify)

**Key Features:**
- ✅ "Start Meeting" button always visible for meeting-required activities (not just in "Needs Attention")
- ✅ Button automatically hides when quota is met
- ✅ Quota progress shown on button: "X/Y"
- ✅ Status label when quota met: "Meeting quota met (X/Y)"
- ✅ Reason strings include quota info: "Meetings completed: X/Y (need Z more)"
- ✅ Config-driven: `required_meeting_count` in ActivityPolicy (0 = use default)


