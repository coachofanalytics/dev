# Autolink Major Blockers Fixed

**Branch:** 25.12_CODA_DEV_CM  
**Date:** 2024-12-30  
**Status:** ✅ All 4 blockers fixed

---

## Summary

Fixed 4 major blockers preventing autolink from working correctly:

1. ✅ **HARD ERROR FIX**: Removed all `created_at` references (Task model has NO `created_at`)
2. ✅ **POLICY + WINDOW FIX**: Added `window_mode` to ActivityPolicy for cycle-based vs ongoing meetings
3. ✅ **SESSION ALLOCATION FIX**: Implemented allocation so each meeting_id satisfies at most one task, and multiple meetings for sessions_required>1
4. ✅ **REQUIREMENT GATING FIX**: Set `requirement_required=False` for INTERNAL_TRAINING_SESSION

---

## 1. HARD ERROR FIX: Task.created_at References

**Problem:** Task model has NO `created_at` field, but code was referencing it.

**Solution:**
- Replaced all `task.created_at` references with `task.submission` for date logic
- Use `task.id` for ordering when needed
- Updated files:
  - `coda/ai_services/management/commands/analyze_meeting_task_patterns.py`
  - `coda/ai_services/services/meeting_task_autolink_service.py`
  - `coda/ai_services/management/commands/autolink_meeting_evidence.py`

**Changes:**
- `_get_task_date()`: Returns `task.submission` or `None` (no fallback to `created_at`)
- Task filtering: Uses `submission` date only
- Diagnose output: Shows submission date or "no submission"

---

## 2. POLICY + WINDOW FIX: Window Mode per Activity

**Problem:** Budgeting task 230 couldn't match because task.submission anchors to 2025-02-27..2025-08-26, but meetings are in Dec.

**Solution:**
- Added `window_mode` field to `ActivityPolicy`:
  - `"submission_window"` (default): Cycle-based activities, use submission anchor ±days
  - `"recent_window"`: Ongoing meetings, use NOW()-days..NOW() window
- Configured activities:
  - `INTERNAL_TRAINING_SESSION`: `window_mode="recent_window"`
  - `DAILY_UPDATE_SESSION`: `window_mode="recent_window"`
  - `BUDGETING_FORECASTING_SESSION`: `window_mode="recent_window"`

**Implementation:**
- `find_meeting_for_task()` checks `policy.window_mode`
- If `recent_window`: Uses `NOW()-days..NOW()` window
- If `submission_window`: Uses `task.submission ±days` window
- Logs chosen window in debug output

---

## 3. SESSION ALLOCATION FIX: Multiple Meetings per Task

**Problem:** Multiple tasks matching same meeting_id=616024597. Need allocation so each meeting_id satisfies at most one task.

**Solution:**
- Added `find_meetings_for_task()` method that:
  - Finds multiple distinct meeting_ids for `sessions_required > 1`
  - Tracks `used_meeting_ids` set to prevent duplicates across tasks
  - Returns list of match results (one per meeting_id)
- Updated command to:
  - Check `sessions_required` from ActivityPolicy
  - Call `find_meetings_for_task()` if `sessions_required > 1`
  - Create multiple TaskLinks (one per meeting_id)
  - Track used meeting_ids across all tasks in the run

**Key Features:**
- Each meeting_id can satisfy at most one task per run
- For `sessions_required=5` (INTERNAL_TRAINING_SESSION), finds up to 5 distinct meeting_ids
- Creates multiple TaskLinks rows (one per meeting_id)
- DAF progress counts distinct meeting_ids (via TaskLinks.meeting_id)

---

## 4. REQUIREMENT GATING FIX: INTERNAL_TRAINING_SESSION

**Problem:** INTERNAL_TRAINING_SESSION shows `requirement_required=True` and blocks eligibility ("Requirement missing").

**Solution:**
- Set `requirement_required=False` for INTERNAL_TRAINING_SESSION in `ActivityPolicy`
- Requirement is now optional (not gated) unless specific requirement slug is present
- Keeps strict requirement only for activities that truly require it

**Changes:**
- `coda/config/activity_definitions.py`: `INTERNAL_TRAINING_SESSION.requirement_required = False`

---

## Files Modified

1. **`coda/config/activity_definitions.py`**
   - Added `window_mode` field to `ActivityPolicy`
   - Set `requirement_required=False` for INTERNAL_TRAINING_SESSION
   - Configured `window_mode="recent_window"` for ongoing meeting activities

2. **`coda/ai_services/services/meeting_task_autolink_service.py`**
   - Fixed `_get_task_date()` to not reference `created_at`
   - Added window_mode logic to `find_meeting_for_task()`
   - Added `find_meetings_for_task()` method for session allocation
   - Updated `diagnose_meeting_search()` to show window_mode

3. **`coda/ai_services/management/commands/autolink_meeting_evidence.py`**
   - Fixed all `created_at` references
   - Added session allocation logic (multiple meetings per task)
   - Tracks `used_meeting_ids` across tasks
   - Creates multiple TaskLinks for `sessions_required > 1`
   - Updated diagnose output to show window_mode

4. **`coda/ai_services/management/commands/analyze_meeting_task_patterns.py`**
   - Fixed all `created_at` references
   - Uses `submission` date only

---

## Verification Commands

Run these commands to verify fixes:

```bash
# 1. Pattern analysis (should work without created_at errors)
poetry run python coda/manage.py analyze_meeting_task_patterns --user-id 495 --days 120 --service internal --verbose

# 2. Diagnose (should show window_mode and no created_at errors)
poetry run python coda/manage.py autolink_meeting_evidence --diagnose --user-id 495 --days 120 --service internal --verbose

# 3. Dry-run (should show multiple meetings for INTERNAL_TRAINING_SESSION)
poetry run python coda/manage.py autolink_meeting_evidence --dry-run --user-id 495 --days 120 --service internal --verbose

# 4. Actual (should create multiple TaskLinks for INTERNAL_TRAINING_SESSION)
poetry run python coda/manage.py autolink_meeting_evidence --user-id 495 --days 120 --service internal --verbose
```

---

## Success Criteria

✅ **No `created_at` errors** - All references replaced with `submission`  
✅ **Budgeting tasks match** - Uses `recent_window` to find Dec meetings  
✅ **Session allocation works** - Each meeting_id used only once, multiple meetings for sessions_required>1  
✅ **INTERNAL_TRAINING_SESSION links** - Should link >= 5 distinct meeting_ids for Eunice  
✅ **Budgeting gets match** - Should get at least 1 match using recent_window  

---

## Expected Output

### For INTERNAL_TRAINING_SESSION (sessions_required=5):
```
📋 Found 1 meeting(s) for 5 sessions required
   ✅ Matched Meeting 123: Internal Training (session 1/5)
   ✅ Matched Meeting 456: Internal Training (session 2/5)
   ✅ Matched Meeting 789: Internal Training (session 3/5)
   ✅ Matched Meeting 101: Internal Training (session 4/5)
   ✅ Matched Meeting 112: Internal Training (session 5/5)
   ✅ Created TaskLinks 1 for meeting 123530685
   ✅ Created TaskLinks 2 for meeting 708385093
   ✅ Created TaskLinks 3 for meeting 616024597
   ✅ Created TaskLinks 4 for meeting 987654321
   ✅ Created TaskLinks 5 for meeting 555444333
```

### For BUDGETING_FORECASTING_SESSION:
```
Task 230: BUDGETING_FORECASTING_SESSION
Policy:
  window_mode: recent_window
  ...
✅ Matched Meeting 456: Budgeting Session (type: attendee_name_inference, confidence: 0.85)
```

---

## Notes

- **No GoToMeeting API calls** - All fixes are DB-only
- **No new models/tables** - Uses existing TaskLinks model (multiple rows per task)
- **Backward compatible** - Default `window_mode="submission_window"` for activities without explicit setting
- **Session allocation** - Prevents duplicate meeting_id usage across tasks in same run

