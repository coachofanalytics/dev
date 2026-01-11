# Phase 0: Meeting → Employee → Activity Attribution Diagnostic Report

**Branch:** 26.01_CODA_DEV_CM  
**Date:** [Date of audit]  
**Scope:** [Start date] to [End date] (last [N] days)  
**Status:** Read-only diagnostic (no changes made)

---

## Executive Summary

**What was measured:**
- GoToMeeting Meetings and their attribution to Employees
- Employee → DAF Activity/Task mapping
- Evidence (TaskLinks) presence validation
- Attribution success rates by method
- Failure modes and outliers

**Scope:**
- Time period: Last [N] days (since [date])
- Meetings analyzed: [count]
- Staff users: [count]
- Tasks in scope: [count]

**Key Findings:**
- [Summary of most important findings]
- [Most common attribution method]
- [Unattributed percentage]
- [Evidence missing percentage]

---

## A) Source Trace

### Meeting Model Fields

**File:** `coda/ai_services/models.py::Meeting`

**Total fields:** [count]

**Key fields:**
- `meeting_id`: CharField(100, unique) - Unique GoToMeeting ID
- `topic`: CharField(500) - Meeting subject/topic (raw)
- `topic_normalized`: CharField(500) - Normalized topic for matching
- `start_time`: DateTimeField - Meeting start time (UTC)
- `recording_url`: URLField(1000) - URL to meeting recording
- `requirement_code`: CharField(20) - Extracted REQ-#### code
- `service_name`: CharField(100) - Service name
- `attendees`: RelatedManager → MeetingAttendee

### Employee Identifier Fields

**Status:** [✓ Direct employee/user FK found] OR [✗ NO DIRECT EMPLOYEE IDENTIFIER FIELD FOUND]

**Attribution Method:**
- If no direct FK: Using `MeetingAttendee` relationship for attribution
- `MeetingAttendee.user`: ForeignKey → CustomerUser (if matched)
- `MeetingAttendee.attendee_email`: EmailField - Attendee's email
- `MeetingAttendee.attendee_name`: CharField(200) - Attendee's display name
- `MeetingAttendee.is_organizer`: BooleanField - Whether attendee was organizer

### Meeting Sync & Processing

**Sync Function:**
- `coda/ai_services/views.py::save_meeting_data()`

**Sync Service:**
- `coda/ai_services/services/meeting_sync_service.py::sync_meetings_for_range()`

**Topic Normalization:**
- `coda/ai_services/utils/meeting_normalizer.py::normalize_topic()`

**Requirement Extraction:**
- `coda/ai_services/utils/meeting_normalizer.py::extract_requirement_code()`

---

## B) Scope & Counts

**Date range:** [Start date] to [End date]  
**Time window for task inference:** ±[N] days

**Meetings in scope:** [count]  
**Active staff users:** [count]  
**Tasks in scope (submission window):** [count]

---

## C) Attribution Pipeline (Meeting → Employee)

### Attribution Methods (in order)

1. **Direct field match** (if Meeting has employee/user FK) → HIGH confidence
2. **Organizer match** (MeetingAttendee.is_organizer=True) → HIGH confidence
3. **Email/organizer parsing** (from attendee_email) → MED confidence
4. **Topic parsing** for staff username/name tokens → MED confidence
5. **Time-window inference** (match to staff with DAF submissions) → LOW confidence
6. **UNATTRIBUTED**

### Attribution Distribution

| Method | Count | Percentage |
|--------|-------|------------|
| direct_field | [count] | [X]% |
| organizer | [count] | [X]% |
| email_match | [count] | [X]% |
| topic_parse | [count] | [X]% |
| time_window | [count] | [X]% |
| unattributed | [count] | [X]% |
| **Total** | **[count]** | **100%** |

### Unattributed Samples

[Top N samples with meeting_id, start_time, topic]

---

## D) Activity Mapping (Meeting → DAF Activity)

### Mapping Configuration

**Status:** MAPPING IS PLACEHOLDER; NEEDS BUSINESS CONFIG

**Placeholder mapping dictionary (read-only):**
- "One on one sessions" → "Self-training / Internal Training"
- "Training" → "Self-training / Internal Training"
- "1:1" → "Self-training / Internal Training"

### Mapping Results

For meetings that are attributed to an employee, activity mapping outcomes:

**Sample of [N] attributed meetings:**
- **Matched task (high confidence):** [count]
  - Exact mapped activity_name match
  - Single candidate within time window
  
- **Ambiguous (multiple candidates):** [count]
  - Multiple tasks match within time window
  - Requires additional disambiguation logic
  
- **No task candidate found:** [count]
  - No tasks for employee within time window
  - Possible causes: task not submitted yet, outside window, different activity type

### Candidate Scoring (Proposed)

For each candidate task:
- Exact mapped activity_name match: +10 points
- Keyword overlap in task.description/activity_name vs meeting.topic: +5 points per keyword
- Time proximity: +3 points (same day), +2 points (1-2 days), +1 point (3-7 days)

---

## E) Evidence Comparison (Downstream Validation)

For meetings that successfully map to employee+task, check if TaskLinks evidence exists.

### Evidence Status

**Sample of [N] attributed meetings:**
- **Evidence present:** [count]
  - TaskLinks record exists with matching meeting_id OR URL
  
- **Evidence missing (would be created by automation):** [count]
  - No TaskLinks record found
  - Would be created by automated evidence generation

### Missing Evidence Samples

[Top N samples with meeting_id, start_time, topic, recording_url]

---

## F) Outliers / Failure Modes

### 1. Meetings with Recording but Unattributed Employee

**Count:** [count]

**Samples:**
[Meeting ID, start_time, topic, recording_url]

### 2. Meetings Attributed to Employee but No Matching Task Candidates

**Count:** [count]

**Possible causes:**
- Task not submitted yet
- Task submission outside time window
- Activity type doesn't match meeting topic
- Employee doesn't have DAF tasks for this period

### 3. Meetings Mapping to Multiple Tasks (Ambiguity)

**Count:** [count]

**Samples:**
[Meeting ID, start_time, topic, candidate task IDs]

### 4. Requirement Code Extraction Failures

**Meetings with topic:** [count]  
**Meetings with requirement_code:** [count]  
**Potential extraction failures:** [count]

**Samples (topic contains REQ pattern but requirement_code is NULL):**
[Meeting ID, topic snippet, extracted code (if re-run)]

---

## G) Actionable Findings (Hypotheses)

### Finding 1: Missing Employee Identifier in Meeting Model

**Evidence:**
- [X]% of meetings unattributed (sample)
- Meeting model lacks direct employee/user FK
- Relies on MeetingAttendee relationship

**Hypothesis:**
- Meeting model should have optional `organizer` or `created_by` FK to CustomerUser
- Would improve attribution accuracy and reduce reliance on attendee matching

### Finding 2: Topic Normalization Insufficient

**Evidence:**
- Topic parsing found limited matches ([X]%)
- Topic format doesn't consistently include employee identifiers

**Hypothesis:**
- Topic normalization may be removing important employee name/username tokens
- Need to preserve employee identifiers during normalization

### Finding 3: Mapping Table Absent / Inconsistent

**Evidence:**
- MAPPING IS PLACEHOLDER; NEEDS BUSINESS CONFIG
- No canonical mapping from meeting topics to DAF activity names

**Hypothesis:**
- Need business-defined mapping table/config
- Should support fuzzy matching and keyword-based mapping
- May need ML-based topic classification

### Finding 4: DAF Submission Dates Not Aligned with Meeting Times

**Evidence:**
- Time-window inference has low success rate ([X]%)
- Task submission dates may not reflect actual meeting dates

**Hypothesis:**
- Tasks may be submitted days/weeks after meeting occurs
- Need wider time window or different date field (e.g., task.created_at)
- Consider using meeting start_time as anchor instead of task.submission

### Finding 5: Evidence Generation Not Automated

**Evidence:**
- [X]% of attributed meetings have missing TaskLinks evidence
- Evidence would be created by automation (if implemented)

**Hypothesis:**
- Need automated TaskLinks creation for attributed meetings
- Should trigger on meeting sync or attribution completion
- Should link to matched task and include meeting recording URL

---

## Appendix: Manual Test Commands

1. **Run command (default):**
   ```bash
   poetry run python manage.py diagnose_meeting_attribution
   ```

2. **Run for last 180 days:**
   ```bash
   poetry run python manage.py diagnose_meeting_attribution --days 180
   ```

3. **Run for a specific employee:**
   ```bash
   poetry run python manage.py diagnose_meeting_attribution --employee eunice
   ```

4. **Adjust time window:**
   ```bash
   poetry run python manage.py diagnose_meeting_attribution --window-days 7
   ```

5. **Export to Markdown:**
   ```bash
   poetry run python manage.py diagnose_meeting_attribution --export-md docs/_temp_summaries/PHASE0_MEETING_ATTRIBUTION_REPORT.md
   ```

6. **Use custom usernames file:**
   ```bash
   poetry run python manage.py diagnose_meeting_attribution --usernames-file scripts/staff_usernames.txt
   ```

7. **Specify date range:**
   ```bash
   poetry run python manage.py diagnose_meeting_attribution --since 2024-01-01 --until 2024-12-31
   ```

---

**Generated by:** `python manage.py diagnose_meeting_attribution`  
**Report Date:** [Date]  
**Auditor:** [Name]

