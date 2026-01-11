# Meeting Launcher Integration Summary

**Branch:** 25.12_CODA_DEV_CM  
**Date:** 2024-12-29  
**Status:** ✅ Implementation Complete

---

## Summary

Wired the old meeting launcher into DAF v2 with multi-pronged matching that works with generic attendee emails. Employees can now launch meetings directly from DAF, and the system matches meetings using meeting room/code + launch intent + time windows instead of relying on unreliable attendee email matching.

---

## Implementation Steps Completed

### A) Meeting Room Mapping Extracted to Config

**Files Created:**
- `coda/ai_services/utils/meeting_room_config.py` - Meeting room configuration utility

**Files Modified:**
- `coda/config/activity_definitions.py` - Added `meeting_room_id` and `meeting_join_url` to ActivityPolicy

**Changes:**
1. Created `meeting_room_config.py` with:
   - `get_meeting_room_for_activity(activity_slug)` - Returns (meeting_id, join_url)
   - `get_activity_for_meeting_id(meeting_id)` - Reverse lookup
   - `ACTIVITY_TO_MEETING_ROOM` mapping dict
   - Legacy mapping support

2. Updated ActivityPolicy dataclass to include:
   - `meeting_room_id: Optional[str] = None`
   - `meeting_join_url: Optional[str] = None`

3. Added meeting room configs to:
   - `INTERNAL_TRAINING_SESSION`: meeting_id="123530685"
   - `PRODUCT_BACKLOG_REFINEMENT`: meeting_id="708385093"
   - `UAT_TESTING_SUPPORT`: meeting_id="123530685"

---

### B) Meeting Launch in DAF v2 (Employee UX)

**Files Modified:**
- `coda/management/legacy_views.py` - Added meeting room config to task_dict
- `coda/management/templates/management/daf/usertasks/employeetasks_v2.html` - Added Start Meeting buttons

**Changes:**
1. In `daf_v2_view()`:
   - Added logic to get meeting room config for meeting-required activities
   - Added `requires_meeting`, `meeting_room_id`, `meeting_join_url` to task_dict

2. In template:
   - Added "Start/Join Meeting" button for meeting-required tasks (when meeting_join_url is configured)
   - Button appears in compliance chips row and as primary action button
   - Opens in new tab, deep-links to correct meeting room

---

### C) Launch Intent Recording (Cache-Based)

**Files Created:**
- `coda/management/views_meeting_launch.py` - Launch intent endpoint

**Files Modified:**
- `coda/management/urls.py` - Added `/management/meeting/launch/` route

**Changes:**
1. Created `launch_meeting()` view:
   - Validates user authentication
   - Records launch intent in Django cache:
     - Key: `meeting_launch:{user_id}:{activity_type_code}`
     - Value: `{meeting_id, activity_type_code, timestamp_iso, user_id, username, task_id}`
     - TTL: 24 hours
   - Redirects to GoToMeeting join URL

2. Created `get_launch_intent()` helper:
   - Retrieves launch intent from cache
   - Used by autolink service for matching

---

### D) Improved Autolink Matching (Multi-Pronged)

**Files Modified:**
- `coda/ai_services/services/meeting_task_autolink_service.py` - Updated `find_meeting_for_task()`

**Changes:**
1. **PRIMARY Matching (Highest Confidence - 0.95):**
   - Match `Meeting.meeting_id` to configured room for task's activity_type
   - Check launch intent cache: user launched this activity_type with this meeting_id
   - Require `meeting.start_time` within ±6 hours of launch intent time OR within command window
   - Match type: `'meeting_room_launch'`

2. **SECONDARY Matching (High Confidence - 0.85):**
   - Match `Meeting.meeting_id` to configured room AND `meeting.start_time` in command window
   - Assign to user who launched it most recently for that activity_type (from cache)
   - Must be within ±6 hours of launch intent
   - Match type: `'meeting_room_recent'`

3. **TERTIARY Matching (Existing):**
   - Requirement code matching (if task requires requirement)
   - Confidence: 0.95 if attendee match, 0.85 otherwise

4. **FALLBACK Matching (Lowest Confidence - 0.70):**
   - Topic keyword mapping to activity type
   - Time window alignment
   - Never require requirement_code

**Key Improvements:**
- ✅ No longer relies on attendee_email (generic emails unreliable)
- ✅ Uses meeting_id + launch intent as primary signal
- ✅ Time windows: ±6 hours from launch OR command window (--days)
- ✅ Does NOT filter candidate tasks by Task.submission recency

---

### E) Numeric, Actionable Reasons

**Files Modified:**
- `coda/management/legacy_views.py` - Updated `_determine_needs_attention_reason()`

**Changes:**
1. **Meeting Required Reason:**
   - If meeting room configured: `"No meeting detected for {activity_type} in last 14 days. Use 'Start Meeting' from DAF so the system can match it."`
   - Otherwise: Generic message

2. **Duration Reason (Already Numeric):**
   - `"Meeting duration: {actual} min; required: {required} min (need {diff} more)"`

3. **Evidence Reason (Already Numeric):**
   - `"Evidence items: {count}/{minimum} (need {diff} more)"`

4. **Quality Reason (Already Numeric):**
   - `"Quality: {score}% / required {threshold}% (need {diff}% more)"`

---

### F) Admin Visibility (Debug Page)

**Files Modified:**
- `coda/management/views_debug.py` - Added meeting room mappings and launch intents
- `coda/management/templates/management/debug/daf_runtime_debug.html` - Added section F

**Changes:**
1. Added `_get_meeting_room_mappings()`:
   - Lists all activity_type -> meeting_id mappings
   - Shows join URL presence
   - Shows source (ActivityPolicy vs Config)

2. Added `_get_recent_launch_intents()`:
   - Shows launch intents for specified user (if user_id provided)
   - Shows activity_type, meeting_id, timestamp, present/absent status
   - Safe: no sensitive URLs exposed

3. Added Section F to debug template:
   - Meeting Room Mappings table
   - Recent Launch Intents table (per user)

---

## Files Changed/Created

### Created:
1. `coda/ai_services/utils/meeting_room_config.py` - Meeting room configuration
2. `coda/management/views_meeting_launch.py` - Launch intent endpoint

### Modified:
3. `coda/config/activity_definitions.py` - Added meeting_room_id/join_url to ActivityPolicy
4. `coda/management/legacy_views.py` - Added meeting room config to task_dict, updated reason text
5. `coda/management/templates/management/daf/usertasks/employeetasks_v2.html` - Added Start Meeting buttons
6. `coda/management/urls.py` - Added launch_meeting route
7. `coda/ai_services/services/meeting_task_autolink_service.py` - Updated matching logic
8. `coda/management/views_debug.py` - Added meeting room mappings and launch intents
9. `coda/management/templates/management/debug/daf_runtime_debug.html` - Added Section F

---

## Verification Steps

### 1. Start Server and Open DAF
```bash
poetry run python coda/manage.py runserver 8080
```

**Steps:**
1. Log in as a current employee (e.g., Brenda, ID: 372)
2. Visit: `/management/daf/v2/`
3. Find a meeting-required task (e.g., UAT_TESTING_SUPPORT, INTERNAL_TRAINING_SESSION)
4. Verify "Start/Join Meeting" button appears
5. Click button - should open GoToMeeting in new tab

**Expected:**
- ✅ Button visible for meeting-required tasks
- ✅ Button opens GoToMeeting join URL
- ✅ Launch intent recorded in cache

---

### 2. Run Meeting Sync
```bash
# Sync meetings for last 7 days
poetry run python coda/manage.py sync_gotomeetings --days 7
```

**Expected:**
- ✅ Command completes without errors
- ✅ New meetings appear in `Meeting` table

---

### 3. Run Autolink Diagnose
```bash
# For employee who launched meeting
poetry run python coda/manage.py autolink_meeting_evidence --diagnose --user-id 372 --days 7 --limit 50
```

**Expected:**
- ✅ No crashes
- ✅ Candidate tasks found
- ✅ Output shows `match_type: 'meeting_room_launch'` or `'meeting_room_recent'` for matched meetings
- ✅ UAT_TESTING_SUPPORT tasks included if present

---

### 4. Run Autolink (Non-Diagnose)
```bash
# On clone DB only
poetry run python coda/manage.py autolink_meeting_evidence --user-id 372 --days 7 --limit 10
```

**Expected:**
- ✅ TaskLinks created with `meeting_id` set
- ✅ `is_auto_generated=True`
- ✅ No errors in logs

---

### 5. Verify Numeric Reasons
**Steps:**
1. Open DAF v2 for employee with meeting-required task
2. If meeting missing, verify reason shows: `"No meeting detected for UAT_TESTING_SUPPORT in last 14 days. Use 'Start Meeting' from DAF so the system can match it."`
3. If meeting exists but duration < 60 min, verify: `"Meeting duration: 45 min; required: 60 min (need 15 more)"`
4. If evidence insufficient, verify: `"Evidence items: 1/2 (need 1 more)"`

**Expected:**
- ✅ All reasons are numeric and actionable
- ✅ Meeting reason mentions "Start Meeting" button when room configured

---

### 6. Verify Admin Debug Page
**Steps:**
1. Log in as staff/superuser
2. Visit: `/management/debug/daf-runtime/`
3. Scroll to Section F: "Meeting Room Mappings & Launch Intents"
4. Verify:
   - Meeting room mappings table shows activity types with meeting_id
   - Launch intents section shows "Specify user_id to see launch intents"
5. Add `?user_id=372` to URL
6. Verify launch intents table shows activity types with present/absent status

**Expected:**
- ✅ Section F visible
- ✅ Mappings table populated
- ✅ Launch intents show for specified user

---

## Verification Log Template

```
STEP 1: Start Server and Open DAF
- [ ] Server starts without errors
- [ ] DAF v2 loads for employee
- [ ] "Start/Join Meeting" button visible for meeting-required tasks
- [ ] Button click opens GoToMeeting in new tab
- [ ] Launch intent recorded (check cache or debug page)

STEP 2: Run Meeting Sync
- [ ] Command completes successfully
- [ ] Meeting.objects.count() increased

STEP 3: Run Autolink Diagnose
- [ ] No crashes
- [ ] Candidates found > 0
- [ ] Match type shows 'meeting_room_launch' or 'meeting_room_recent'
- [ ] UAT_TESTING_SUPPORT tasks included

STEP 4: Run Autolink (Non-Diagnose)
- [ ] TaskLinks created
- [ ] meeting_id set correctly
- [ ] is_auto_generated=True

STEP 5: Verify Numeric Reasons
- [ ] Meeting reason mentions "Start Meeting" when room configured
- [ ] Duration reason shows actual vs required
- [ ] Evidence reason shows count vs minimum
- [ ] Quality reason shows percentage

STEP 6: Verify Admin Debug Page
- [ ] Section F visible
- [ ] Mappings table populated
- [ ] Launch intents show for user_id
```

---

## Key Features

1. ✅ **No Database Tables Created** - Uses Django cache for launch intents
2. ✅ **No Migrations Required** - Uses existing models and cache
3. ✅ **Minimal Changes** - Targeted updates, no large refactors
4. ✅ **Works with Generic Emails** - Matching uses meeting_id + launch intent, not attendee_email
5. ✅ **Actionable Reasons** - Numeric, specific guidance for employees
6. ✅ **Admin Visibility** - Debug page shows mappings and launch intents

---

## Status

✅ **All implementation steps complete**  
✅ **Code compiles without errors**  
✅ **Ready for runtime verification**

**Next:** Run verification steps above to confirm end-to-end flow works.

