# Phase 0: Evidence ↔ Meeting Matching Diagnostic Report

**Branch:** 26.01_CODA_DEV_CM  
**Date:** [Date of audit]  
**Scope:** Last [N] days (since [date])  
**Status:** Read-only diagnostic (no changes made)

---

## Executive Summary

**What was measured:**
- Evidence (TaskLinks) records and their matching to Meeting records
- Match outcome classification by method (meeting_id → URL → requirement_code → topic/time → no_match)
- Requirement code extraction and matching behavior
- URL-based and topic-based matching strategies
- Outlier cases and mismatch patterns

**Scope:**
- Time period: Last [N] days (since [date])
- Evidence records analyzed: [count]
- Meeting records analyzed: [count]
- Tasks with evidence: [count]

**Key Findings:**
- [Summary of most important findings]
- [Most common failure mode]
- [Root cause hypothesis]

---

## 1. Source Code Trace

### Matching Implementation Locations

**View:**
- File: `coda/management/legacy_views.py`
- Function: `newevidence(request, taskid)`
- Helper: `_get_meeting_match_info(task, link=None)`

**Services:**
- Old: `coda/ai_services/services/meeting_evidence_matcher.py::MeetingEvidenceMatcher` [✓/✗ available]
- New: `coda/management/services/meeting_match_service.py::MeetingMatchService` [✓/✗ available]

**Templates:**
- `coda/management/templates/management/daf/evidence_form.html`
- `coda/management/templates/management/daf/evidence_form_v2.html`

### Matching Strategy Order (as implemented)

1. **A) Direct meeting_id match:**
   - `Evidence.meeting_id` → `Meeting.meeting_id`
   - Confidence: HIGH

2. **B) URL match:**
   - Normalize `TaskLinks.link` and `TaskLinks.drive_link`
   - Match against `Meeting.recording_url` and `Meeting.download_url`
   - Confidence: HIGH

3. **C) Requirement code match:**
   - Extract `REQ-####` from `Meeting.topic` using `extract_requirement_code()`
   - Compare with `Task.requirement.id` (formatted as `REQ-{id}`)
   - Stored in `Meeting.requirement_code` field
   - Time window: ±[N] days from task submission
   - Confidence: MEDIUM

4. **D) Topic + time window match:**
   - Match by topic similarity within ±[N] days of `Task.submission`
   - Uses `Meeting.topic_normalized` and activity tags
   - Confidence: LOW

5. **E) No match**

### Requirement Code Extraction

**Function:** `coda/ai_services/utils/meeting_normalizer.py::extract_requirement_code()`

**Pattern:** `REQ-####` (3-6 digits, case-insensitive)

**Source field:** `Meeting.topic` (raw text)

**Stored field:** `Meeting.requirement_code` (extracted and normalized)

**Pattern variations:**
- `REQ-1234` (standard)
- `REQ - 1234` (with spaces)
- `REQ 1234` (space, no dash)

---

## 2. Model Inventory

### TaskLinks (Evidence) Model

**File:** `coda/management/models.py::TaskLinks`

**Key Fields:**
- `task`: ForeignKey → Task
- `link`: CharField(1000) - Evidence URL
- `drive_link`: URLField(2000) - Google Drive link
- `meeting_id`: CharField(100) - GoToMeeting meeting_id if auto-generated
- `created_at`: DateTimeField - When evidence was uploaded
- `is_active`: BooleanField - Whether evidence is active
- `is_featured`: BooleanField - Used as approval indicator (no explicit approved field)
- `added_by`: ForeignKey → User

**Total fields:** [count]

### Meeting Model

**File:** `coda/ai_services/models.py::Meeting`

**Key Fields:**
- `meeting_id`: CharField(100, unique) - GoToMeeting ID
- `topic`: CharField(500) - Meeting subject/topic (raw)
- `topic_normalized`: CharField(500) - Normalized topic for matching
- `requirement_code`: CharField(20) - Extracted REQ-#### code
- `recording_url`: URLField(1000) - URL to meeting recording
- `download_url`: URLField(1000) - Direct download URL
- `start_time`: DateTimeField - Meeting start time
- `service_name`: CharField(100) - Service name (gotomeeting_internal, etc.)

**Total fields:** [count]

### Task Model (Relevant Fields)

**File:** `coda/management/models.py::Task`

**Key Fields for Matching:**
- `id`: Primary key
- `employee`: ForeignKey → User
- `requirement`: ForeignKey → Requirement
- `submission`: DateTimeField - Task submission date
- `activity_name`: CharField - Activity name
- `description`: TextField - Task description
- `group`: CharField - Employee group (Group H/I are SPECIAL)

### Requirement Model

**File:** `coda/management/models.py::Requirement`

**Key:** `id` (used to format `REQ-{id}`)

---

## 3. Approved / Counts Toward Matching

**Definition of which TaskLinks "count" in the audit:**

- **Default:** Include only `is_active=True` unless `--include-inactive` flag is set
- **Approval field:** No explicit `approved` or `is_approved` field found
- **Proxy:** Using `is_active` as proxy for "approved evidence"
- **Note:** `is_featured` is used as approval indicator in some views, but not consistently

**Evidence in scope:**
- Total: [count]
- Active (is_active=True): [count]
- Inactive (is_active=False): [count]

---

## 4. Integrity & Null Findings

### Evidence (TaskLinks) Integrity

**Total records (last N days):** [count]

**Breakdown:**
- Active: [count]
- Inactive: [count]
- With link URL: [count] ([X]%)
- With drive_link: [count] ([X]%)
- With meeting_id: [count] ([X]%)

**Null/Empty Checks:**
- Evidence with NULL/empty link: [count]
- Evidence with NULL/empty drive_link: [count]
- Evidence with NULL/empty meeting_id: [count]
- Evidence with NULL/empty both link and drive_link: [count]

### Meeting Integrity

**Total records (last N days):** [count]

**Breakdown:**
- With recording URL: [count] ([X]%)
- With requirement_code: [count] ([X]%)
- With topic: [count] ([X]%)

**Null/Empty Checks:**
- Meetings with NULL/empty recording URLs: [count]
- Meetings with NULL/empty requirement_code: [count]
- Meetings with NULL/empty topic: [count]
- Meetings with NULL/empty both recording_url and download_url: [count]

### Task Integrity

**Total records (last N days):** [count]

**Breakdown:**
- With requirement: [count] ([X]%)
- With submission: [count] ([X]%)

**Null/Empty Checks:**
- Task missing submission: [count]
- Task missing requirement: [count]

---

## 5. Match Outcome Classification

**Classification order (as implemented):**
1. A) Direct meeting_id match
2. B) URL match
3. C) Requirement code match
4. D) Topic + time window match
5. E) No match

### Match Method Distribution

| Method | Count | Percentage |
|--------|-------|------------|
| meeting_id | [count] | [X]% |
| url | [count] | [X]% |
| requirement_code | [count] | [X]% |
| topic_time | [count] | [X]% |
| no_match | [count] | [X]% |
| **Total** | **[count]** | **100%** |

---

## 6. Behavioral Distributions

### Match Method Distribution

[Distribution by match method: meeting_id, URL, requirement_code, topic_time, no_match]

### Service Name Distribution

[Distribution by service_name: gotomeeting_internal, gotomeeting_external, etc.]

### Requirement Code Match Outcomes

- **Matched:** [count] - Requirement code present and matches task requirement
- **Missing:** [count] - Requirement code not present in meeting
- **Parse Failed:** [count] - Topic present but code extraction failed
- **Mismatch:** [count] - Requirement code present but doesn't match task requirement
- **Not Applicable:** [count] - Task has no requirement

### Time Delta Distribution

[Distribution of time differences between evidence submission and meeting date]

**Buckets:**
- Same day: [count]
- 1-2 days: [count]
- 3-7 days: [count]
- >7 days: [count]

---

## 7. Outliers + Samples

### A) Evidence with Missing Meeting Records

**Definition:** Evidence with meeting_id but no matching Meeting record

**Count:** [count]

**Samples (top 25):**
[Evidence ID, Task ID, Employee, Meeting ID, Evidence Link]

### B) URL Normalization Near-Misses

**Definition:** Evidence URL exists but no match after normalization

**Count:** [count]

**Samples (top 25):**
[Evidence ID, Evidence URL (canonical), Meeting ID, Meeting URL (canonical)]

### C) Requirement Code Parse Failures

**Definition:** Meetings with topic but no requirement_code, where topic contains REQ pattern

**Count:** [count]

**Samples (top 25):**
[Meeting ID, Topic Snippet, Extracted Code (if re-run), Stored requirement_code]

### D) Multiple Candidate Meetings

**Definition:** Evidence/task could match multiple meetings within tight window

**Count:** [count]

**Samples (top 25):**
[Evidence ID, Task ID, Candidate Meeting IDs, Topics, Start Times]

---

## 8. Root Cause Hypotheses

### Hypothesis 1: Requirement Code Not Extracted During Sync

**Observation:** Meetings have topics with REQ codes but requirement_code field is NULL

**Evidence:**
- [Count] meetings (sample of 100) have REQ code in topic but requirement_code is NULL
- [Count] of those could be parsed if re-run

**Possible Causes:**
- Extraction function not called during meeting sync
- Extraction function called but failed silently
- Topic format doesn't match expected pattern

### Hypothesis 2: URL Normalization Mismatch

**Observation:** Evidence URLs don't match meeting recording URLs even when they should

**Evidence:**
- [Count] evidence records with URLs that don't match any meeting
- [Count] URL normalization mismatches detected

**Possible Causes:**
- Normalization logic differs between evidence and meeting storage
- URL format changed over time
- Multiple URL formats for same recording

### Hypothesis 3: Time Window Too Narrow

**Observation:** Matches fail because meeting date is outside ±[N] day window

**Evidence:**
- [Count] potential matches outside current window
- [Count] candidates exist just outside ±[N] days

**Possible Causes:**
- Task submission date is inaccurate
- Meeting date is inaccurate
- Window should be wider (e.g., ±7 days)

### Hypothesis 4: Metadata Insufficient

**Observation:** Topic-based matching fails even when topics are similar

**Evidence:**
- [Count] meetings in time window but not matched
- [Count] high similarity but rejected due to rule constraints

**Possible Causes:**
- Activity tag overlap requirement too strict
- Topic normalization loses important information
- Employee name matching not enabled

---

## 9. Next Proposed Fix Tracks

### Track 1: Fix Requirement Code Extraction

**Goal:** Ensure all meetings with REQ codes in topic have requirement_code populated

**Approach:**
- Re-run extraction on existing meetings
- Fix extraction logic if needed
- Add validation during meeting sync

### Track 2: Improve URL Matching

**Goal:** Increase URL match success rate

**Approach:**
- Audit URL normalization consistency
- Support multiple URL formats
- Add fuzzy URL matching

### Track 3: Expand Time Window

**Goal:** Catch more matches by widening time window

**Approach:**
- Increase from ±2 days to ±7 days
- Make window configurable
- Add time-based confidence scoring

### Track 4: Enhance Topic Matching

**Goal:** Improve topic-based matching accuracy

**Approach:**
- Relax activity tag overlap requirement
- Improve topic normalization
- Add employee name matching

---

## Appendix: Manual Test Commands

1. **Run script (default):**
   ```bash
   cd ~/Projects/uat
   poetry run python coda/manage.py shell -c "$(cat scripts/phase0_evidence_meeting_matching_audit.py)"
   ```

2. **Run command (default):**
   ```bash
   poetry run python coda/manage.py diagnose_evidence_matching
   ```

3. **Run for last 90 days:**
   ```bash
   poetry run python coda/manage.py diagnose_evidence_matching --days 90
   ```

4. **Run for a specific employee:**
   ```bash
   poetry run python coda/manage.py diagnose_evidence_matching --employee eunice
   ```

5. **Run for specific task:**
   ```bash
   poetry run python coda/manage.py diagnose_evidence_matching --task-id 77
   ```

6. **Compare matchers (if both exist):**
   ```bash
   poetry run python coda/manage.py diagnose_evidence_matching --service both
   ```

7. **Include inactive evidence:**
   ```bash
   poetry run python coda/manage.py diagnose_evidence_matching --include-inactive
   ```

8. **Wider time window:**
   ```bash
   poetry run python coda/manage.py diagnose_evidence_matching --window-days 14
   ```

9. **Export to Markdown:**
   ```bash
   poetry run python coda/manage.py diagnose_evidence_matching --export-md docs/_temp_summaries/PHASE0_EVIDENCE_MATCHING_REPORT.md
   ```

---

**Generated by:** `python manage.py diagnose_evidence_matching`  
**Report Date:** [Date]  
**Auditor:** [Name]
