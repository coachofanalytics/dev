# Meeting Button Fix Verification

**Branch:** 25.12_CODA_DEV_CM  
**Date:** 2024-12-29  
**Status:** ✅ Fixes applied

---

## Problem

Eunice (user_id=495) does not see "Start Meeting" buttons in DAF v2 for meeting-required tasks because:
- DAILY_UPDATE_SESSION and BUDGETING_FORECASTING_SESSION are meeting_required=True but missing meeting_room_id and meeting_join_url
- APP_DATA_ENTRY_TESTING_SUPPORT (legacy) has no policy entry
- MAKUTANO_SUPERVISOR and FARMING_COORDINATOR have no policy entries

---

## Solution

### ✅ TASK 1: Added meeting_room_id + meeting_join_url for DAILY_UPDATE_SESSION and BUDGETING_FORECASTING_SESSION

**File:** `coda/config/activity_definitions.py`

**Changes:**
- **DAILY_UPDATE_SESSION** (line 505-527): Added `meeting_room_id="616024597"` and `meeting_join_url="https://global.gotomeeting.com/join/616024597"` (shared with INTERNAL_TRAINING_SESSION)
- **BUDGETING_FORECASTING_SESSION** (line 338-358): Added `meeting_room_id="616024597"` and `meeting_join_url="https://global.gotomeeting.com/join/616024597"` (shared with INTERNAL_TRAINING_SESSION)

---

### ✅ TASK 2: Added legacy alias mapping for APP_DATA_ENTRY_TESTING_SUPPORT

**File:** `coda/config/activity_definitions.py` (function: `get_activity_policy`)

**Changes:**
- Added `LEGACY_ALIASES` dict mapping `APP_DATA_ENTRY_TESTING_SUPPORT` -> `DATA_ENTRY`
- Modified `get_activity_policy()` to check legacy aliases before looking up in `ACTIVITY_POLICIES`
- No DB migration required - pure code-level mapping

**Code Location:** Lines 536-551

---

### ✅ TASK 3: Added policy entries for MAKUTANO_SUPERVISOR and FARMING_COORDINATOR

**File:** `coda/config/activity_definitions.py`

**Changes:**
- **MAKUTANO_SUPERVISOR** (new entry): Added policy with `meeting_required=False`, `requirement_required=False`
- **FARMING_COORDINATOR** (new entry): Added policy with `meeting_required=False`, `requirement_required=False`
- Both have evidence requirements: `["doc_or_drive_link", "description"]`

**Code Location:** Lines 528-560 (after DAILY_UPDATE_SESSION, before closing brace)

---

## Files Modified

**`coda/config/activity_definitions.py`**
- Lines 338-358: Added `meeting_room_id` and `meeting_join_url` to BUDGETING_FORECASTING_SESSION
- Lines 505-527: Added `meeting_room_id` and `meeting_join_url` to DAILY_UPDATE_SESSION
- Lines 536-551: Enhanced `get_activity_policy()` with legacy alias mapping
- Lines 528-560: Added MAKUTANO_SUPERVISOR and FARMING_COORDINATOR policy entries

---

## Verification

### 1) Django Check
```bash
poetry run python coda/manage.py check
```

**Expected:** ✅ No errors

---

### 2) Shell Command: Verify Policy Coverage for Eunice

```bash
poetry run python coda/manage.py shell << 'EOF'
from management.models import Task
from django.contrib.auth import get_user_model
from coda.config.activity_definitions import get_activity_policy
User = get_user_model()

# Get Eunice
eunice = User.objects.get(id=495)
print(f"\nPolicy Coverage for {eunice.username} (ID: {eunice.id})\n")
print("=" * 80)

# Get all active tasks for Eunice
tasks = Task.objects.filter(employee=eunice, is_active=True).order_by('activity_name')[:20]

print(f"\nTotal active tasks: {tasks.count()}\n")

for task in tasks:
    activity_slug = task.activity_type.slug if task.activity_type else None
    activity_name = task.activity_name
    
    # Get policy
    policy = get_activity_policy(activity_slug) if activity_slug else None
    
    if policy:
        meeting_required = policy.meeting_required
        has_room = bool(policy.meeting_room_id)
        has_url = bool(policy.meeting_join_url)
        show_button = meeting_required and has_room and has_url
        status = "✅" if show_button else "⚠️"
    else:
        meeting_required = False
        has_room = False
        has_url = False
        show_button = False
        status = "❌"
    
    print(f"{status} {activity_name[:40]:<40} | slug: {activity_slug or 'N/A':<30} | "
          f"meeting_req: {meeting_required} | room: {has_room} | url: {has_url} | "
          f"show_button: {show_button}")

# Check specific activities
print("\n" + "=" * 80)
print("\nSpecific Activity Checks:\n")

test_slugs = [
    "DAILY_UPDATE_SESSION",
    "BUDGETING_FORECASTING_SESSION",
    "INTERNAL_TRAINING_SESSION",
    "APP_DATA_ENTRY_TESTING_SUPPORT",  # Legacy alias
    "DATA_ENTRY",
    "MAKUTANO_SUPERVISOR",
    "FARMING_COORDINATOR",
]

for slug in test_slugs:
    policy = get_activity_policy(slug)
    if policy:
        print(f"✅ {slug}:")
        print(f"   meeting_required: {policy.meeting_required}")
        print(f"   meeting_room_id: {policy.meeting_room_id}")
        print(f"   meeting_join_url: {bool(policy.meeting_join_url)}")
        if policy.meeting_required and policy.meeting_room_id and policy.meeting_join_url:
            print(f"   → Start Meeting button will show ✅")
        else:
            print(f"   → Start Meeting button will NOT show ⚠️")
    else:
        print(f"❌ {slug}: No policy found")

print("\n" + "=" * 80)
EOF
```

**Expected Output:**
- ✅ DAILY_UPDATE_SESSION: meeting_required=True, meeting_room_id=616024597, meeting_join_url=True → Start Meeting button will show ✅
- ✅ BUDGETING_FORECASTING_SESSION: meeting_required=True, meeting_room_id=616024597, meeting_join_url=True → Start Meeting button will show ✅
- ✅ INTERNAL_TRAINING_SESSION: meeting_required=True, meeting_room_id=616024597, meeting_join_url=True → Start Meeting button will show ✅
- ✅ APP_DATA_ENTRY_TESTING_SUPPORT: Maps to DATA_ENTRY policy (legacy alias working)
- ✅ MAKUTANO_SUPERVISOR: Policy found (meeting_required=False)
- ✅ FARMING_COORDINATOR: Policy found (meeting_required=False)

---

### 3) Manual UI Verification

1. **Start Django server:**
   ```bash
   poetry run python coda/manage.py runserver
   ```

2. **Open DAF v2 for Eunice:**
   - Navigate to: `http://localhost:8000/management/daf/v2/?user_id=495`

3. **Verify Start Meeting buttons appear for:**
   - ✅ Internal Training Session tasks
   - ✅ Daily Update Session tasks
   - ✅ Budgeting & Forecasting Session tasks

4. **Verify no errors for:**
   - ✅ Tasks with activity_type APP_DATA_ENTRY_TESTING_SUPPORT (should map to DATA_ENTRY)
   - ✅ Tasks with activity_type MAKUTANO_SUPERVISOR (should have policy, no meeting required)
   - ✅ Tasks with activity_type FARMING_COORDINATOR (should have policy, no meeting required)

---

## Summary

**Fixes:** 3/3 tasks complete  
**Status:** Ready for testing  
**Breaking Changes:** None  
**Backward Compatible:** Yes (legacy alias mapping preserves existing behavior)

**Key Improvements:**
- ✅ DAILY_UPDATE_SESSION and BUDGETING_FORECASTING_SESSION now have meeting room configuration
- ✅ Legacy APP_DATA_ENTRY_TESTING_SUPPORT maps to DATA_ENTRY (no DB migration)
- ✅ MAKUTANO_SUPERVISOR and FARMING_COORDINATOR have policy entries (no more policy=False)
- ✅ All meeting-required activities with meeting_room_id and meeting_join_url will show "Start Meeting" button


