# Phase 0: Evidence ↔ Meeting Matching Diagnostic Report

**Branch:** 26.01_CODA_DEV_CM  
**Date:** [Date of audit]  
**Scope:** Last [N] days  
**Status:** Read-only diagnostic (no changes made)

---

## Executive Summary

**What was measured:**
- Evidence (TaskLinks) records and their matching to Meeting records
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
- Old: `coda/ai_services/services/meeting_evidence_matcher.py::MeetingEvidenceMatcher`
- New: `coda/management/services/meeting_match_service.py::MeetingMatchService`

**Templates:**
- `coda/management/templates/management/daf/evidence_form.html`
- `coda/management/templates/management/daf/evidence_form_v2.html`

### Matching Strategies

1. **URL-based matching:**
   - Normalize `TaskLinks.link` and `TaskLinks.drive_link`
   - Match against `Meeting.recording_url` and `Meeting.download_url`
   - Confidence: HIGH (0.9-1.0)

2. **Topic + time window:**
   - Match by topic similarity within ±2 days of `Task.submission`
   - Uses `Meeting.topic_normalized` and activity tags
   - Confidence: LOW-MEDIUM (0.3-0.7)

3. **Requirement code matching:**
   - Extract `REQ-####` from `Meeting.topic` using `extract_requirement_code()`
   - Compare with `Task.requirement.id` (formatted as `REQ-{id}`)
   - Stored in `Meeting.requirement_code` field

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

**File:** `coda/management/models.py`

**Key Fields:**
- `task`: ForeignKey → Task
- `link`: CharField(1000) - Evidence URL
- `drive_link`: URLField(2000) - Google Drive link
- `meeting_id`: CharField(100) - GoToMeeting meeting_id if auto-generated
- `created_at`: DateTimeField - When evidence was uploaded
- `is_active`: BooleanField - Whether evidence is active
- `added_by`: ForeignKey → User

**Total fields:** [count]

### Meeting Model

**File:** `coda/ai_services/models.py`

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

**Key Fields for Matching:**
- `id`: Primary key
- `employee`: ForeignKey → User
- `requirement`: ForeignKey → Requirement
- `submission`: DateTimeField - Task submission date
- `activity_name`: CharField - Activity name
- `description`: TextField - Task description

---

## 3. Integrity & Null Findings

### Evidence (TaskLinks) Integrity

**Total records (last N days):** [count]

**Breakdown:**
- Active: [count]
- With link URL: [count]
- With drive_link: [count]
- With meeting_id: [count]

**Null/Empty Checks:**
- Evidence with NULL/empty link: [count]
- Evidence with NULL/empty drive_link: [count]

### Meeting Integrity

**Total records (last N days):** [count]

**Breakdown:**
- With recording URL: [count]
- With requirement_code: [count]
- With topic: [count]

**Null/Empty Checks:**
- Meetings with NULL/empty recording URLs: [count]
- Meetings with NULL/empty requirement_code: [count]
- Meetings with NULL/empty topic: [count]

---

## 4. Behavioral Distributions

### Match Method Distribution

[Distribution by match method: URL, topic, requirement_code, etc.]

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

---

## 5. Outliers + Samples

### Suspicious Matches

**Definition:** Matches where |meeting_date - task/evidence_date| > 7 days

**Samples:**
[Top 25 samples with details]

### Evidence with Missing Meeting Records

**Definition:** Evidence with meeting_id but no matching Meeting record

**Count:** [count]

**Samples:**
[Top 25 samples]

### Requirement Code Parse Failures

**Definition:** Meetings with topic but no requirement_code, where topic contains REQ pattern

**Count:** [count]

**Samples:**
[Top 25 samples with topic snippets and extracted codes]

### Multiple Candidate Meetings

**Definition:** Evidence that could match multiple meetings within tight window

**Count:** [count]

**Samples:**
[Top 25 samples]

---

## 6. Candidate Root Causes (Hypotheses)

### Hypothesis 1: Requirement Code Not Extracted During Sync

**Observation:** Meetings have topics with REQ codes but requirement_code field is NULL

**Possible Causes:**
- Extraction function not called during meeting sync
- Extraction function called but failed silently
- Topic format doesn't match expected pattern

**Evidence:**
- [Count] meetings with topic but no requirement_code
- [Count] of those could be parsed if re-run

### Hypothesis 2: URL Normalization Mismatch

**Observation:** Evidence URLs don't match meeting recording URLs even when they should

**Possible Causes:**
- Normalization logic differs between evidence and meeting storage
- URL format changed over time
- Multiple URL formats for same recording

**Evidence:**
- [Count] evidence records with URLs that don't match any meeting

### Hypothesis 3: Time Window Too Narrow

**Observation:** Matches fail because meeting date is outside ±2 day window

**Possible Causes:**
- Task submission date is inaccurate
- Meeting date is inaccurate
- Window should be wider (e.g., ±7 days)

**Evidence:**
- [Count] potential matches outside current window

### Hypothesis 4: Topic Matching Too Strict

**Observation:** Topic-based matching fails even when topics are similar

**Possible Causes:**
- Activity tag overlap requirement too strict
- Topic normalization loses important information
- Employee name matching not enabled

**Evidence:**
- [Count] meetings in time window but not matched

---

## 7. Next Proposed Fix Tracks

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

## Appendix: Sample Output

[Paste output from `diagnose_evidence_matching` command here]

---

**Generated by:** `python manage.py diagnose_evidence_matching`  
**Report Date:** [Date]  
**Auditor:** [Name]

