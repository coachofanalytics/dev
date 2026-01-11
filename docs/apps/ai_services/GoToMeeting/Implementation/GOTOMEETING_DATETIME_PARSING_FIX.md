# GoToMeeting Datetime Parsing Fix

**Branch:** 25.12_CODA_DEV_CM  
**Date:** 2024-12-29  
**Status:** ✅ Fixes applied

---

## Problem

GoToMeeting API returns `startTime` strings like `'2025-12-29T13:03:49.+0000'` which Django's `parse_datetime()` cannot parse, causing `start_time` to become `None` and meetings to be skipped as "missing start_time".

---

## Solution

### ✅ TASK 1: Added `parse_goto_dt()` helper function

**File:** `coda/ai_services/views.py` (lines 360-411)

**Functionality:**
1. **Strips whitespace** from input
2. **Normalizes dangling dot before TZ offset:**
   - Pattern: `r'\.(?=[+-]\d{4}$)'`
   - Example: `'2025-12-29T13:03:49.+0000'` → `'2025-12-29T13:03:49+0000'`
3. **Normalizes timezone offsets without colon:**
   - Pattern: `r'([+-])(\d{2})(\d{2})$'`
   - Examples:
     - `'+0000'` → `'+00:00'`
     - `'-0500'` → `'-05:00'`
4. **Parses with Django's `parse_datetime()`**
5. **Makes naive datetimes aware in UTC**
6. **Returns `None` if parsing fails**

---

### ✅ TASK 2: Updated parsing logic to use `parse_goto_dt()`

**File:** `coda/ai_services/views.py` (lines 468-510)

**Changes:**
- Replaced direct `parse_datetime()` calls with `parse_goto_dt()` for both `start_time` and `end_time`
- Supports both camelCase (`startTime`, `endTime`) and snake_case (`start_time`, `end_time`)

---

### ✅ TASK 3: Improved skip logging with separate counters

**File:** `coda/ai_services/views.py`

**Counters Added:**
- `skipped_missing_start_time` - When `startTime` key doesn't exist
- `skipped_parse_failed_start_time` - When `startTime` exists but parsing fails

**Enhanced Logging:**
- **Parse failed:** Logs `meetingId`, `subject`, `meetingType`, `raw startTime`, and `normalized` value
- **Missing:** Logs `meetingId`, `subject`, `meetingType`, and `available_keys`

**Summary Logging:**
- Updated to show both counters: `"X skipped (missing start_time), Y skipped (parse failed)"`

---

## Files Modified

**`coda/ai_services/views.py`**
- Lines 360-411: Added `parse_goto_dt()` helper function
- Line 436: Added `skipped_parse_failed_start_time = 0` counter
- Lines 468-510: Updated parsing logic to use `parse_goto_dt()` with improved logging
- Lines 693-707: Updated summary logging and return dict

---

## Verification Commands

### 1) Django Check
```bash
poetry run python coda/manage.py check
```

**Expected:** ✅ No errors

---

### 2) Sync GoToMeeting Meetings
```bash
poetry run python coda/manage.py sync_gotomeetings --service gotomeeting_external --days 14
```

**Expected:**
- ✅ Meetings with `startTime` like `'2025-12-29T13:03:49.+0000'` are now parsed successfully
- ✅ Summary shows: `"X created, Y updated, Z skipped (missing start_time), W skipped (parse failed)"`
- ✅ Meetings are saved to database with valid `start_time`

---

### 3) Verify Meeting Rows Created
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

# Show recent external meetings with start_time
recent = Meeting.objects.filter(service_name='gotomeeting_external').order_by('-start_time')[:5]
for m in recent:
    print(f"  {m.meeting_id}: {m.topic[:50]} | {m.start_time}")
EOF
```

**Expected:**
- `External meetings: > 0`
- `Meetings with null start_time: 0`
- Recent meetings show valid `start_time` values

---

## Summary

**Fixes:** 3/3 complete  
**Status:** Ready for testing  
**Breaking Changes:** None  
**Backward Compatible:** Yes

**Key Improvements:**
- ✅ GoToMeeting datetime strings with dangling dots are now parsed correctly
- ✅ Timezone offsets without colons are normalized
- ✅ Separate tracking for missing vs parse-failed startTime
- ✅ Enhanced logging shows raw and normalized values for debugging


