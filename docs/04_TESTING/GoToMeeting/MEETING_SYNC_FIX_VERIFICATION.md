# Meeting Sync Fix Verification

**Branch:** 25.12_CODA_DEV_CM  
**Date:** 2024-12-29  
**Status:** ✅ Fixes applied

---

## Fixes Applied

### ✅ TASK 1: Fix Meeting Save Mapping

**File:** `coda/ai_services/views.py` (function: `save_meeting_data`)

**Changes:**
1. **Support both camelCase and snake_case:**
   - `meetingId` OR `meeting_id`
   - `startTime` OR `start_time`
   - `endTime` OR `end_time`
   - `subject` OR `topic`
   - `downloadUrl` OR `download_url`
   - `meetingType` OR `meeting_type`

2. **Robust ISO8601 timestamp parsing:**
   - Wrapped `parse_datetime` in try-except
   - Handles `None`, empty strings, and invalid formats
   - Makes timezone-aware if naive

3. **Guard for missing start_time:**
   - If `start_time` is still `None` after parsing, SKIP the meeting
   - Logs warning with: `meetingId`, `subject`, `meetingType`, and available keys
   - Increments `skipped_missing_start_time` counter

4. **Summary logging:**
   - Added `skipped_missing_start_time` to return dict
   - Logs summary including skipped count

**Code Location:** Lines 402-450 in `coda/ai_services/views.py`

---

### ✅ TASK 2: Fix DAF Start/Join Meeting Button Visibility

**File:** `coda/management/templates/management/daf/usertasks/employeetasks_v2.html`

**Changes:**
- Added new condition to show button when:
  - `task.requires_meeting == True` AND
  - `task.meeting_join_url` is present
- Button shows even if task is NOT in "Needs Attention" state
- Uses same button styling and URL as existing button

**Code Location:** Lines 404-411 in template (after existing MEETING_REQUIRED condition)

**Note:** `task_dict` already includes `requires_meeting` and `meeting_join_url` (verified in `legacy_views.py` lines 2006-2008)

---

## Verification Commands

### 1) Verify GoToMeeting OAuth
```bash
poetry run python coda/manage.py verify_goto_oauth --service gotomeeting_external
```

**Expected:** OAuth token is valid and accessible

---

### 2) Sync GoToMeeting Meetings
```bash
poetry run python coda/manage.py sync_gotomeetings --service gotomeeting_external --days 14
```

**Expected:**
- No crashes (no IntegrityError for null start_time)
- Summary shows: `X created, Y updated, Z skipped (missing start_time)`
- Meetings with valid `startTime` are saved
- Meetings with missing/invalid `startTime` are skipped with warning

---

### 3) Django Shell Checks
```bash
poetry run python coda/manage.py shell << 'EOF'
from ai_services.models import Meeting
from django.db.models import Q

# Count external meetings
external_count = Meeting.objects.filter(service_name='gotomeeting_external').count()
print(f"External meetings: {external_count}")

# Count meetings with null start_time (should be 0)
null_start_count = Meeting.objects.filter(Q(start_time__isnull=True) | Q(start_time='')).count()
print(f"Meetings with null start_time: {null_start_count}")

# Show recent external meetings
recent = Meeting.objects.filter(service_name='gotomeeting_external').order_by('-start_time')[:5]
for m in recent:
    print(f"  {m.meeting_id}: {m.topic[:50]} | {m.start_time}")
EOF
```

**Expected:**
- `External meetings: > 0`
- `Meetings with null start_time: 0`
- Recent meetings show valid `start_time`

---

### 4) DAF v2 UI Verification
1. Start server: `poetry run python coda/manage.py runserver`
2. Open: `/management/daf/v2/?user_id=<EUNICE_ID>` (or any user with meeting-required tasks)
3. Verify:
   - "Start Meeting" button appears on meeting-required tasks
   - Button appears even if task is NOT in "Needs Attention" state
   - Button only appears when `meeting_join_url` is present

---

### 5) Autolink Diagnose
```bash
poetry run python coda/manage.py autolink_meeting_evidence --diagnose --user-id <EUNICE_ID> --days 30
```

**Expected:**
- Command completes without errors
- Shows candidate tasks for meeting-required activities
- Shows meeting candidates with valid `start_time`

---

## Test Results

**Status:** ⏳ PENDING (requires manual execution)

**Expected Outcomes:**
1. ✅ Sync no longer crashes with IntegrityError
2. ✅ Meetings with valid `startTime` are saved
3. ✅ Meetings with missing `startTime` are skipped with warning
4. ✅ DAF v2 shows "Start Meeting" button for all meeting-required tasks with `meeting_join_url`
5. ✅ Autolink can match meetings using `start_time`

---

## Files Modified

1. `coda/ai_services/views.py` - Fixed meeting save mapping (lines 402-450, 655-665)
2. `coda/management/templates/management/daf/usertasks/employeetasks_v2.html` - Fixed button visibility (lines 404-411)

---

## Summary

**Fixes:** 2/2 complete  
**Status:** Ready for verification  
**Breaking Changes:** None  
**Backward Compatible:** Yes (supports both camelCase and snake_case)


