# Meeting Sync Verification and Sessions Required Implementation

**Branch:** 25.12_CODA_DEV_CM  
**Date:** 2024-12-29  
**Status:** ✅ Implementation complete

---

## Goals

1. Verify meeting sync truly updates records over time
2. Add "sessions/meetings required per activity" to ActivityPolicy
3. Use sessions_required to control DAF meeting launcher visibility + progress
4. Ensure meeting launcher appears for meeting-required activities with meeting_room_id/join_url

---

## Implementation

### ✅ TASK A: Meeting update verification helpers

**File:** `coda/ai_services/management/commands/verify_meeting_sync.py` (NEW)

**Features:**
- Prints total meetings by service_name
- Prints max(updated_at) by service_name
- Prints count of meetings updated in last N minutes by service_name
- Read-only (no data modifications)
- Status indicators: ✅ Active, ⚠️ Stale, ❌ Very stale

**Usage:**
```bash
poetry run python coda/manage.py verify_meeting_sync
poetry run python coda/manage.py verify_meeting_sync --minutes 30
poetry run python coda/manage.py verify_meeting_sync --service gotomeeting_internal
```

---

### ✅ TASK B: Policy: sessions_required per activity

**File:** `coda/config/activity_definitions.py`

**Changes:**
- **Line 70:** Added `sessions_required: int = 1` to ActivityPolicy dataclass
- **INTERNAL_TRAINING_SESSION** (line 140): `sessions_required=5`
- **DAILY_UPDATE_SESSION** (line 532): `sessions_required=1`
- **CLIENT_TRAINING_SESSION** (line 192): `sessions_required=1`
- **SELF_TRAINING_SESSION** (line 166): `sessions_required=1`
- **UAT_TESTING_SUPPORT** (line 481): `sessions_required=1`

**Code Location:** Lines 70, 140, 166, 192, 481, 532

---

### ✅ TASK C: DAF v2: show meeting progress + hide Start when complete

**File:** `coda/management/legacy_views.py`

**Changes:**
- **Lines 2005-2030:** Updated meeting quota computation:
  - Uses `sessions_required` from ActivityPolicy (preferred) or falls back to `required_meeting_count`
  - Counts completed meetings: `TaskLinks` with `meeting_id` present (NOT relying on attendee_email)
  - Generates `meeting_progress_text`: `"Meetings: X/Y"`
  - Sets `show_start_meeting_button = bool(meeting_join_url) and meetings_completed_count < meeting_required_count`
- **Lines 2036-2040:** Added to task_dict:
  - `meeting_required_count` (new field from sessions_required)
  - `meeting_progress_text` (e.g., "Meetings: 2/5")
  - Kept `required_meeting_count` for backward compatibility

**File:** `coda/management/templates/management/daf/usertasks/employeetasks_v2.html`

**Changes:**
- **Lines 277-280:** Added meeting progress text badge near compliance chips
- **Lines 405-420:** Updated button visibility:
  - Shows "Start Meeting" button when `task.show_start_meeting_button` is true
  - Displays `task.meeting_progress_text` badge on button (e.g., "Meetings: 2/5")
  - Hides button and shows "Meetings complete: X/Y" when `meetings_completed_count >= meeting_required_count`

**Code Location:** 
- `legacy_views.py`: Lines 2005-2040
- `employeetasks_v2.html`: Lines 277-280, 405-420

---

### ✅ TASK D: Meeting room configuration coverage

**File:** `coda/config/activity_definitions.py`

**Status:** ✅ Already configured (from previous task)
- **DAILY_UPDATE_SESSION** (line 530-532): Has `meeting_room_id="616024597"` and `meeting_join_url`
- **BUDGETING_FORECASTING_SESSION** (line 358-360): Has `meeting_room_id="616024597"` and `meeting_join_url`

---

## Files Modified

1. **`coda/ai_services/management/commands/verify_meeting_sync.py`** (NEW)
   - Management command for meeting sync verification

2. **`coda/config/activity_definitions.py`**
   - Line 70: Added `sessions_required: int = 1` to ActivityPolicy
   - Lines 140, 166, 192, 481, 532: Set `sessions_required` values for meeting-required activities

3. **`coda/management/legacy_views.py`**
   - Lines 2005-2030: Updated meeting quota computation to use `sessions_required`
   - Lines 2036-2040: Added `meeting_required_count` and `meeting_progress_text` to task_dict

4. **`coda/management/templates/management/daf/usertasks/employeetasks_v2.html`**
   - Lines 277-280: Added meeting progress text badge
   - Lines 405-420: Updated button visibility and progress display

---

## Verification

### 1) Django Check
```bash
poetry run python coda/manage.py check
```

**Expected:** ✅ No errors

---

### 2) Meeting Sync Verification

**Step 1: Run sync twice to verify updates**
```bash
# First sync
poetry run python coda/manage.py sync_gotomeetings --service gotomeeting_internal --days 7

# Wait 2-3 minutes

# Second sync (should update existing records)
poetry run python coda/manage.py sync_gotomeetings --service gotomeeting_internal --days 7

# Verify updates
poetry run python coda/manage.py verify_meeting_sync --service gotomeeting_internal --minutes 5
```

**Expected Output:**
```
📊 Meeting Sync Verification Report
Time window: Last 5 minutes
================================================================================

📋 Service: gotomeeting_internal
   Total meetings: <count>
   Most recent update: 2024-12-29 14:30:15 UTC (2.5 minutes ago)
   Updated in last 5 min: <count>
   ✅ Status: Active (recent updates detected)
```

**Step 2: Query updated_at deltas**
```bash
poetry run python coda/manage.py shell << 'EOF'
from ai_services.models import Meeting
from django.utils import timezone
from datetime import timedelta

# Get meetings updated in last 10 minutes
cutoff = timezone.now() - timedelta(minutes=10)
recent = Meeting.objects.filter(updated_at__gte=cutoff).order_by('-updated_at')[:5]

print(f"\nMeetings updated in last 10 minutes: {recent.count()}\n")
for m in recent:
    age_min = (timezone.now() - m.updated_at).total_seconds() / 60
    print(f"  {m.meeting_id}: {m.topic[:50]} | Updated {age_min:.1f} min ago")
EOF
```

**Expected:** Shows meetings with recent `updated_at` timestamps

---

### 3) DAF v2 Meeting Progress Display

**Shell Command: Verify sessions_required values**
```bash
poetry run python coda/manage.py shell << 'EOF'
from coda.config.activity_definitions import get_activity_policy

test_activities = [
    "INTERNAL_TRAINING_SESSION",
    "DAILY_UPDATE_SESSION",
    "CLIENT_TRAINING_SESSION",
    "SELF_TRAINING_SESSION",
    "UAT_TESTING_SUPPORT",
]

print("\nSessions Required per Activity:\n")
print("=" * 80)

for slug in test_activities:
    policy = get_activity_policy(slug)
    if policy:
        sessions_req = getattr(policy, 'sessions_required', 1)
        meeting_req = policy.meeting_required
        has_room = bool(policy.meeting_room_id)
        has_url = bool(policy.meeting_join_url)
        print(f"✅ {slug}:")
        print(f"   sessions_required: {sessions_req}")
        print(f"   meeting_required: {meeting_req}")
        print(f"   has_meeting_room: {has_room}")
        print(f"   has_join_url: {has_url}")
        if meeting_req and has_room and has_url:
            print(f"   → Start Meeting button will show until {sessions_req} meetings completed ✅")
    else:
        print(f"❌ {slug}: No policy found")

print("\n" + "=" * 80)
EOF
```

**Expected Output:**
- ✅ INTERNAL_TRAINING_SESSION: sessions_required=5
- ✅ DAILY_UPDATE_SESSION: sessions_required=1
- ✅ CLIENT_TRAINING_SESSION: sessions_required=1
- ✅ SELF_TRAINING_SESSION: sessions_required=1
- ✅ UAT_TESTING_SUPPORT: sessions_required=1

---

### 4) Manual UI Verification

1. **Start Django server:**
   ```bash
   poetry run python coda/manage.py runserver
   ```

2. **Open DAF v2 for a user with meeting-required tasks:**
   - Navigate to: `http://localhost:8000/management/daf/v2/?user_id=<USER_ID>`

3. **Verify:**
   - ✅ "Start Meeting" button appears for meeting-required activities with `meeting_join_url`
   - ✅ Progress badge shows on button: "Meetings: X/Y" (e.g., "Meetings: 2/5")
   - ✅ Progress text appears near compliance chips: "Meetings: X/Y"
   - ✅ Button hides when `meetings_completed_count >= meeting_required_count`
   - ✅ "Meetings complete: X/Y" badge shows when quota is met

---

## Summary

**Implementation:** 4/4 tasks complete  
**Status:** Ready for testing  
**Breaking Changes:** None  
**Backward Compatible:** Yes (kept `required_meeting_count` for compatibility)

**Key Features:**
- ✅ Meeting sync verification command shows update status by service
- ✅ `sessions_required` field in ActivityPolicy (config-driven, easy to edit)
- ✅ DAF v2 shows meeting progress: "Meetings: X/Y"
- ✅ Start Meeting button hides when quota is met
- ✅ Meeting progress text appears near compliance chips
- ✅ Only counts TaskLinks with `meeting_id` present (not attendee_email)


