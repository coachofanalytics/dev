# Autolink Verification Note

**Branch:** 25.12_CODA_DEV_CM  
**Date:** 2024-12-30  
**Target User:** Eunice (user_id=495)  
**Service:** Internal (gotomeeting_internal)

---

## Verification Steps

### Step 1: Run Pattern Analysis

```bash
poetry run python coda/manage.py analyze_meeting_task_patterns --user-id 495 --days 90 --service internal --out eunice_patterns.csv --verbose
```

**Expected Output:**
- Shows tasks found (meeting-required activities only)
- Shows meetings found in date range
- Shows attendees found with names
- For each task, shows top 10 candidate meetings with:
  - meeting_id
  - start_time
  - subject
  - score (0.0-1.0)
  - signals_hit (time_window, subject_keyword_X, attendee_name_X, recurring_boost_X)
  - explanation string

**Key Verification Points:**
- ✅ Attendee names are loaded from MeetingAttendee.attendee_name
- ✅ Keyword dictionaries exist for INTERNAL_TRAINING_SESSION, DAILY_UPDATE_SESSION, BUDGETING_FORECASTING_SESSION
- ✅ Time windows use task.submission (matches DAF evaluation), not created_at
- ✅ CSV output shows meaningful top candidates with non-zero scores

---

### Step 2: Run Autolink Diagnose

```bash
poetry run python coda/manage.py autolink_meeting_evidence --diagnose --user-id 495 --days 90 --limit 50 --service internal --verbose
```

**Expected Output Format:**

```
================================================================================
Task 123: INTERNAL_TRAINING_SESSION
Employee: eunice

Policy:
  meeting_required: True
  meeting_room_id expected: 616024597
  sessions_required: 5
  requirement_required: False

Candidate Meeting Query Parameters:
  service filter: gotomeeting_internal
  date window: 2 days
  start_date: 2024-12-28
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
     Start: 2024-12-29T10:00:00+00:00
     Duration: 60 minutes
     Signals Hit: attendee_name_inference_0.85, subject_keyword_0.60, meeting_room_id
     Score: 0.85
     
  2. Meeting ID: 708385093
     Service: gotomeeting_internal
     Start: 2024-12-28T14:00:00+00:00
     Duration: 45 minutes
     Signals Hit: subject_keyword_0.40
     Score: 0.40
     Rejection Reason: Score too low (<0.5)

  3. Meeting ID: 616024597
     Service: gotomeeting_internal
     Start: 2024-12-27T09:00:00+00:00
     Duration: 30 minutes
     Signals Hit: meeting_room_id
     Score: 0.85

Final Decision: WOULD LINK
Reason: Match found: attendee_name_inference, confidence: 0.85
================================================================================
```

**Key Verification Points:**
- ✅ Shows launch intent status (has_launch_intent: False)
- ✅ Shows whether room filter applied (meeting_room_id filter applied: False)
- ✅ Shows candidate counts BEFORE/AFTER each filter stage
- ✅ Shows top 3 candidates with:
  - meeting_id, service_name, start_time, duration
  - signals_hit (non-empty list or explicitly states why missing)
  - score (0.0-1.0)
  - rejection_reason (if score < 0.5)

---

### Step 3: Run Autolink Dry-Run

```bash
poetry run python coda/manage.py autolink_meeting_evidence --user-id 495 --days 90 --limit 50 --service internal --dry-run --verbose
```

**Expected Output:**

```
================================================================================
Task ID    User            Activity                  Req Code    Meeting ID       Match             Conf   Action         
================================================================================
123        eunice          INTERNAL_TRAINING_SESSION  None        123530685        attendee_name_inference 0.85  CREATE
124        eunice          DAILY_UPDATE_SESSION       None        708385093        attendee_name_inference 0.80  CREATE
125        eunice          BUDGETING_FORECASTING_SESSION None      616024597        meeting_room_id   0.85  CREATE
```

**Key Verification Points:**
- ✅ Shows matches it would create
- ✅ Match types include: attendee_name_inference, meeting_room_id, attendee_email, etc.
- ✅ Confidence scores >= 0.5
- ✅ Action is CREATE (new TaskLink) or UPDATE (existing TaskLink)

---

### Step 4: Run Autolink Actual (Create TaskLinks)

```bash
poetry run python coda/manage.py autolink_meeting_evidence --user-id 495 --days 90 --limit 50 --service internal --verbose
```

**Expected Output:**

```
📋 Found 15 candidate task(s)

📝 Processing Task 123: INTERNAL_TRAINING_SESSION
   Employee: eunice
   ✅ Matched Meeting 456: Internal Training Session (type: attendee_name_inference, confidence: 0.85)
   ✅ Created TaskLink: task=123, meeting_id=123530685, is_auto_generated=True

📝 Processing Task 124: DAILY_UPDATE_SESSION
   Employee: eunice
   ✅ Matched Meeting 457: Daily Update (type: attendee_name_inference, confidence: 0.80)
   ✅ Created TaskLink: task=124, meeting_id=708385093, is_auto_generated=True

...

📊 Summary:
   Tasks scanned: 15
   Tasks matched: 12
   TaskLinks created: 10
   TaskLinks updated: 2
   Tasks skipped: 3
```

**Key Verification Points:**
- ✅ TaskLinks created with `is_auto_generated=True`
- ✅ TaskLinks.meeting_id populated
- ✅ At least 1 Eunice meeting-required task linked

---

### Step 5: Verify TaskLinks in Database

```sql
-- Check TaskLinks created for Eunice
SELECT 
    tl.id,
    tl.task_id,
    t.activity_name,
    tl.meeting_id,
    m.topic,
    m.start_time,
    tl.is_auto_generated,
    tl.created_at
FROM management_tasklinks tl
JOIN management_task t ON tl.task_id = t.id
LEFT JOIN ai_services_meeting m ON tl.meeting_id = m.meeting_id
WHERE t.employee_id = 495
  AND tl.is_auto_generated = True
  AND tl.created_at >= NOW() - INTERVAL '1 hour'
ORDER BY tl.created_at DESC;
```

**Expected Results:**
- At least 1 row returned
- `is_auto_generated = True`
- `meeting_id` is populated
- `meeting.topic` shows meeting subject
- `meeting.start_time` is within task time window

---

## Success Criteria

✅ **Pattern Analysis:**
- Outputs meaningful top candidates with non-zero scores
- Attendee names loaded from DB
- Keyword dictionaries work for all meeting-required activities
- Time windows match DAF evaluation (use submission date)

✅ **Autolink Diagnose:**
- Shows launch intent status
- Shows whether room filter applied
- Shows candidate counts BEFORE/AFTER each filter
- Shows top 3 candidates with signals (or explains why missing)

✅ **Autolink Dry-Run:**
- Reports matches it would create
- Shows match types and confidence scores

✅ **Autolink Actual:**
- Creates TaskLinks with `is_auto_generated=True`
- At least 1 Eunice meeting-required task linked
- TaskLinks.meeting_id populated

---

## Notes

- **No GoToMeeting API calls** - all analysis is DB-only
- **No new models/tables** - uses existing Meeting and MeetingAttendee
- **Minimal changes** - focused on autolink matching and diagnose output
- **Meeting room filter** - only applied when launch intent exists, otherwise used as boost signal

