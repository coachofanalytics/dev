# Meeting-Task Pattern Analysis Implementation

**Branch:** 25.12_CODA_DEV_CM  
**Date:** 2024-12-30  
**Status:** ✅ Complete

---

## Goals

Stop iterating on GoToMeeting API fetch. Create a DB-first analysis pipeline to discover real matching patterns between Tasks and Meetings, then integrate attendee-name inference into autolink.

**No new database tables/models** - uses existing Meeting and MeetingAttendee models.

---

## Deliverables

### A) New Management Command: `analyze_meeting_task_patterns.py`

**File:** `coda/ai_services/management/commands/analyze_meeting_task_patterns.py`

**Features:**
- DB-only analysis (no GoToMeeting API calls)
- Pulls tasks and meetings from database
- Builds candidate matrix per task with explainable scoring
- Outputs CSV/JSON or prints to stdout

**Usage:**
```bash
# Analyze patterns for Eunice (user_id=495)
poetry run python coda/manage.py analyze_meeting_task_patterns --user-id 495 --days 90 --service internal

# Output to CSV
poetry run python coda/manage.py analyze_meeting_task_patterns --user-id 495 --days 90 --service internal --out patterns.csv

# Verbose output
poetry run python coda/manage.py analyze_meeting_task_patterns --user-id 495 --days 90 --service internal --verbose
```

**Scoring Signals:**
1. `time_window_hit` (bool) - Meeting within task time window
2. `subject_keyword_score` (0-1) - Keyword overlap between meeting subject and activity type
3. `attendee_name_score` (0-1) - Name match between employee and attendee names
4. `meeting_id_recurring_boost` (0-0.2) - Boost if meeting_id repeats (recurring pattern)

**Output Format:**
- Per task: top 10 meetings with meeting_id, start_time, subject, duration, score, signals_hit, explanation
- Summary statistics: most common meeting_ids, tasks with/without candidates

---

### B) Attendee-Name Inference Utility

**File:** `coda/ai_services/utils/meeting_host_inference.py`

**Function:** `infer_probable_host(meeting, employees_queryset) -> (employee_id|None, confidence float, reasons list)`

**Features:**
- Deterministic inference (no AI calls)
- Normalizes names (lowercase, strip punctuation)
- Handles nicknames minimally (first name match + optional last name)
- Confidence heuristics:
  - Exact full-name match: 0.95
  - Unique first-name match: 0.85
  - Partial/approx match: 0.70

**Usage:**
```python
from ai_services.utils.meeting_host_inference import infer_probable_host

result = infer_probable_host(meeting, employees_queryset)
if result[0]:
    employee_id, confidence, reasons = result
    print(f"Probable host: {employee_id} (confidence: {confidence:.2f})")
```

---

### C) Modified Autolink Service

**File:** `coda/ai_services/services/meeting_task_autolink_service.py`

#### Changes Made:

1. **Adjusted Candidate Selection Logic:**
   - **BEFORE:** Strict meeting_room_id filter always applied
   - **AFTER:** Only apply strict meeting_room_id filter if:
     - Launch intent exists for that task/activity, OR
     - ActivityPolicy explicitly marks "must_use_room=True" (future enhancement)
   - **Otherwise:** meeting_room_id is used as boost signal only, not a filter

2. **Added Attendee-Name Inference Scoring:**
   - Integrated `infer_probable_host()` utility
   - Added as TERTIARY matching (after email, before name matching)
   - If inferred_host == task.employee, adds score signal and allows match
   - Confidence threshold: >= 0.70

3. **Enhanced Diagnose Output:**
   - Shows candidate counts **BEFORE and AFTER** each filter
   - Shows launch intent status
   - Shows whether meeting_room_id filter was applied
   - If meeting_room_id filter caused 0 candidates, prints:
     - "⚠️  RECOMMENDATION: Room mapping may be wrong or adoption is low. Consider checking actual meeting_ids used."
   - Shows top 3 candidates with signals hit, scores, and rejection reasons

#### Matching Flow (Updated):

1. **PRIMARY:** Launch intent + meeting_room_id (0.95) - STRICT filter if launch intent exists
2. **SECONDARY:** Attendee email match (0.75-0.9)
3. **TERTIARY:** Attendee-name inference (0.70-0.95) - NEW
4. **QUATERNARY:** Attendee name match (0.6-1.0)
5. **FALLBACK:** Topic keyword match (0.5-0.7)

---

### D) Enhanced Diagnose Output

**File:** `coda/ai_services/management/commands/autolink_meeting_evidence.py`

**New Output Sections:**

1. **Candidate Selection Summary:**
   - User group (A/B/C)
   - Meeting-required activity types (from ActivityPolicy)
   - Exclusion reasons per task

2. **Candidate Meeting Counts (BEFORE/AFTER filters):**
   - Time Window: X → Y
   - Service Filter: X → Y
   - Meeting Room ID Filter: X → Y (only if launch intent exists)
   - Shows if meeting_room_id is available as boost signal

3. **Query Parameters:**
   - meeting_room_id expected
   - has_launch_intent (bool)
   - meeting_room_id_filter_applied (bool)

4. **Top 3 Meeting Candidates:**
   - meeting_id
   - service_name
   - start_time
   - duration_minutes
   - signals_hit (list)
   - score
   - rejection_reason (if applicable)

5. **Zero Candidate Reasons:**
   - Specific reasons why no candidates found
   - Recommendation message if meeting_room_id mismatch detected

---

## Key Improvements

### 1. Less Strict Meeting Room Filtering

**Problem:** Autolink failed for Eunice because it filtered by meeting_room_id=616024597, but actual meetings had different meeting_ids.

**Solution:** Only apply strict meeting_room_id filter when launch intent exists. Otherwise, use it as a boost signal but don't filter out other meetings.

### 2. Attendee-Name Inference

**Problem:** Employees join meetings with names, not emails (often generic emails).

**Solution:** Added deterministic attendee-name inference utility that:
- Matches normalized names
- Handles uniqueness checks
- Provides confidence scores
- Integrated into autolink matching flow

### 3. Better Diagnose Output

**Problem:** Hard to understand why autolink fails.

**Solution:** Enhanced diagnose output shows:
- Candidate counts before/after each filter
- Launch intent status
- Top 3 candidates with full scoring details
- Specific recommendations when meeting_room_id mismatch detected

---

## Verification Steps

### Step 1: Run Pattern Analysis

```bash
poetry run python coda/manage.py analyze_meeting_task_patterns --user-id 495 --days 90 --service internal --out eunice_patterns.csv
```

**Expected Output:**
- Shows which meeting_ids and subjects are repeatedly associated with Eunice's tasks
- Identifies patterns for INTERNAL_TRAINING_SESSION, DAILY_UPDATE_SESSION, BUDGETING_FORECASTING_SESSION

### Step 2: Review Pattern Analysis Results

- Check CSV/JSON output for most common meeting_ids
- Compare with ActivityPolicy meeting_room_id configurations
- Identify mismatches (e.g., policy says 616024597 but actual meetings use 123530685)

### Step 3: Run Diagnose Command

```bash
poetry run python coda/manage.py autolink_meeting_evidence --diagnose --user-id 495 --days 30 --limit 80 --service internal --verbose
```

**Expected Output:**
- Shows candidate counts before/after each filter
- Shows launch intent status
- Shows top 3 candidates with scores
- If meeting_room_id filter caused 0 candidates, shows recommendation message

### Step 4: Propose Corrected Mappings

Based on pattern analysis results, update ActivityPolicy meeting_room_id values if needed:
- File: `coda/config/activity_definitions.py`
- Update `meeting_room_id` in ActivityPolicy for:
  - INTERNAL_TRAINING_SESSION
  - DAILY_UPDATE_SESSION
  - BUDGETING_FORECASTING_SESSION

---

## Files Created/Modified

### New Files:
1. `coda/ai_services/management/commands/analyze_meeting_task_patterns.py` - Pattern analysis command
2. `coda/ai_services/utils/meeting_host_inference.py` - Attendee-name inference utility

### Modified Files:
1. `coda/ai_services/services/meeting_task_autolink_service.py`
   - Adjusted meeting_room_id filtering logic
   - Added attendee-name inference integration
   - Enhanced diagnose_meeting_search() method

2. `coda/ai_services/management/commands/autolink_meeting_evidence.py`
   - Enhanced diagnose output with BEFORE/AFTER counts
   - Added launch intent status display
   - Improved candidate selection summary

3. `coda/ai_services/views.py`
   - Fixed attendee name persistence (handles null emails)

---

## Constraints Met

✅ **No new models/tables/migrations** - uses existing Meeting and MeetingAttendee models  
✅ **No GoToMeeting API calls** - all analysis is DB-only  
✅ **Explainable logic** - all scoring signals are logged and visible  
✅ **Small, localized changes** - minimal refactoring, focused on specific issues  

---

## Next Steps

1. Run pattern analysis for Eunice (user_id=495)
2. Review results to identify actual meeting_ids used
3. Update ActivityPolicy meeting_room_id values if mismatches found
4. Re-run diagnose command to verify improvements
5. Test autolink end-to-end on clone DB

---

## Example Diagnose Output

```
================================================================================
Task 123: INTERNAL_TRAINING_SESSION
Employee: eunice

Policy:
  meeting_required: True
  meeting_room_id expected: 616024597
  sessions_required: 5
  requirement_required: True

Candidate Meeting Query Parameters:
  service filter: gotomeeting_internal
  date window: 30 days
  start_date: 2024-12-01
  end_date: 2024-12-30
  meeting_room_id expected: 616024597
  has_launch_intent: False
  meeting_room_id filter applied: False

Candidate Meeting Counts (BEFORE/AFTER filters):
  Time Window: 45 → 45
  Service Filter: 45 → 23
  Meeting Room ID Filter: 23 → 23
  Meeting Room ID: Available as boost signal (not filtering)

Top 3 Meeting Candidates:
  1. Meeting ID: 123530685
     Service: gotomeeting_internal
     Start: 2024-12-15T10:00:00+00:00
     Duration: 60 minutes
     Signals Hit: attendee_name_inference_0.85, subject_keyword_0.60
     Score: 0.85
     
  2. Meeting ID: 708385093
     Service: gotomeeting_internal
     Start: 2024-12-14T14:00:00+00:00
     Duration: 45 minutes
     Signals Hit: subject_keyword_0.40
     Score: 0.40
     Rejection Reason: Score too low (<0.5)

Final Decision: WOULD LINK
Reason: Match found: attendee_name_inference, confidence: 0.85
================================================================================
```

