# Autolink Meeting Evidence Improvements Summary

**Branch:** 25.12_CODA_DEV_CM  
**Date:** 2024-12-30  
**Status:** ✅ Steps B & C Complete, Step D In Progress

---

## Goals

Make autolink actually link meeting-required tasks (starting with Eunice) using a multi-signal approach:
- meeting_room_id mapping (when correct)
- launch intent (when used)
- attendee NAME heuristic as a fallback layer (not email)
- topic keyword fallback (already exists but may need tightening)

Improve diagnose output so we can see exactly WHY no match (e.g., meeting room mismatch, time window mismatch, missing attendee names, candidate meeting count = 0, etc.).

---

## ✅ Step B: Enhanced Diagnose Output

### Changes Made

**File:** `coda/ai_services/services/meeting_task_autolink_service.py`

1. **Added `diagnose_meeting_search()` method:**
   - Returns detailed diagnostic information for a task
   - Shows policy info (meeting_required, meeting_room_id expected, sessions_required, requirement_required)
   - Shows query parameters used (service filter, date window, meeting_room_id filter)
   - Shows candidate meeting counts at each filtering stage
   - Provides specific reasons when zero candidates found

**File:** `coda/ai_services/management/commands/autolink_meeting_evidence.py`

2. **Enhanced diagnose output:**
   - Shows policy information for each task
   - Shows query parameters used
   - Shows candidate counts at each stage (time_window_only, with_service_filter, with_meeting_room_id)
   - Shows zero candidate reasons (e.g., "0 meetings found for service=gotomeeting_internal in last 30 days", "0 meetings match meeting_room_id=616024597")
   - Shows other meeting_ids found if meeting_room_id mismatch detected

### Usage

```bash
# Diagnose for Eunice (internal service)
poetry run python coda/manage.py autolink_meeting_evidence --diagnose --service internal --user-id <EUNICE_ID> --days 30 --limit 50 --verbose
```

### Output Example

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
  meeting_room_id filter: 616024597

Candidate Meeting Counts:
  time_window_only: 45
  with_service_filter: 23
  with_meeting_room_id: 0

Zero Candidate Reasons:
  - 0 meetings match meeting_room_id=616024597
  - Other meeting_ids found in window: 123530685, 708385093

Top 3 Meeting Candidates:
  (No candidates found)

Final Decision: NO LINK
Reason: No match found
================================================================================
```

---

## ✅ Step C: Attendee NAME Matching (Safe Fallback)

### Changes Made

**File:** `coda/ai_services/services/meeting_task_autolink_service.py`

1. **Added `_normalize_name()` method:**
   - Normalizes names for matching: lowercase, strip punctuation, collapse whitespace

2. **Added `_calculate_name_match_score()` method:**
   - Scoring system:
     - 1.0 = full-name exact match (case-insensitive, punctuation stripped)
     - 0.8 = first name + last initial match
     - 0.6 = first-name-only match (uniqueness checked separately)
     - 0.0 = no match

3. **Added `_is_first_name_unique()` method:**
   - Checks if first name is unique among active employees
   - Uses same employee filter as Employee Groups page
   - Conservative: assumes not unique if check fails

4. **Added `_match_by_attendee_name_safe()` method:**
   - Conservative heuristics:
     - Prefers full-name matches (score >= 0.8)
     - Allows first-name-only (0.6) ONLY if unique AND with additional constraints
     - Requires meeting_room_id match or single candidate meeting for first-name-only
     - Rejects ambiguous matches (e.g., multiple "Eunice" without last name)
   - Integrated as TERTIARY matching (after email, before topic)

5. **Integrated into main matching flow:**
   - Added to `find_meeting_for_task()` as fallback layer
   - Returns match with `match_type='attendee_name'` and confidence based on score

### Features

- ✅ No database migration needed - uses existing `attendee_name` field
- ✅ Conservative matching - avoids false positives
- ✅ Handles ambiguity - rejects matches when multiple employees share first name
- ✅ Additional constraints - requires meeting_room_id match or single candidate for weak matches
- ✅ Logging - includes `name_match_reason` in match results

### Matching Rules

1. **Full name match (1.0):** "Eunice Smith" matches "Eunice Smith" → Auto-link
2. **First + last initial (0.8):** "Eunice S" matches "Eunice Smith" → Auto-link
3. **Unique first name (0.6):** "Eunice" matches "Eunice" (only if unique) → Auto-link ONLY if:
   - Single candidate meeting, OR
   - meeting_room_id matches
4. **Ambiguous first name (0.6):** "Eunice" matches "Eunice" (multiple employees) → NO auto-link

---

## 🔄 Step D: Meeting Room ID Mapping Check

### Changes Made

**File:** `coda/ai_services/management/commands/check_meeting_room_mapping.py` (NEW)

1. **Created diagnostic command:**
   - Shows meeting_ids actually used in database (last N days)
   - Shows ActivityPolicy configurations
   - Shows what `get_meeting_room_for_activity()` returns
   - Identifies mismatches between policy and actual usage

### Usage

```bash
# Check meeting room mappings
poetry run python coda/manage.py check_meeting_room_mapping --service internal --days 30
```

### Enhanced Diagnose Output

- Now shows other meeting_ids found if meeting_room_id mismatch detected
- Helps identify if policy meeting_room_id doesn't match actual meetings

---

## 📋 Next Steps

### Step D (In Progress)
1. Run `check_meeting_room_mapping` command to identify actual meeting_ids in database
2. Compare with ActivityPolicy configurations
3. Update ActivityPolicy or meeting_room_config if mismatch found
4. Verify with diagnose command

### Step E (Pending)
1. Test diagnose command with Eunice user_id
2. Verify name matching works with real data
3. Run autolink (non-diagnose) on clone DB
4. Verify TaskLinks created for meeting-required tasks
5. Confirm DAF progress updates accordingly

### Testing Commands

```bash
# 1. Check meeting room mappings
poetry run python coda/manage.py check_meeting_room_mapping --service internal --days 30

# 2. Diagnose for Eunice
poetry run python coda/manage.py autolink_meeting_evidence --diagnose --service internal --user-id <EUNICE_ID> --days 30 --limit 50 --verbose

# 3. Run autolink (clone DB only)
poetry run python coda/manage.py autolink_meeting_evidence --service internal --user-id <EUNICE_ID> --days 30 --limit 20

# 4. Verify meeting sync (DB only)
poetry run python coda/manage.py verify_meeting_sync --service gotomeeting_internal --minutes 60
```

---

## 🎯 Deliverables

### Completed
- ✅ Enhanced diagnose output with detailed query parameters and candidate counts
- ✅ Attendee NAME matching as safe fallback layer
- ✅ Meeting room mapping diagnostic command

### In Progress
- 🔄 Meeting room ID mapping verification and fixes

### Pending
- ⏳ End-to-end testing with Eunice
- ⏳ TaskLinks creation verification
- ⏳ DAF progress update verification

---

## 📝 Notes

- **No database migrations required** - all changes use existing fields
- **Conservative matching** - name matching requires high confidence or additional constraints
- **Diagnose mode is read-only** - safe to run on production data
- **Focus on TaskLinks creation** - stop re-running sync as proof, focus on linking meetings → TaskLinks

---

## 🔍 Key Files Modified

1. `coda/ai_services/services/meeting_task_autolink_service.py`
   - Added `diagnose_meeting_search()` method
   - Added name matching methods (`_normalize_name`, `_calculate_name_match_score`, `_is_first_name_unique`, `_match_by_attendee_name_safe`)
   - Enhanced matching flow to include name matching

2. `coda/ai_services/management/commands/autolink_meeting_evidence.py`
   - Enhanced diagnose output to show policy, query parameters, candidate counts, and zero candidate reasons

3. `coda/ai_services/management/commands/check_meeting_room_mapping.py` (NEW)
   - Diagnostic command to check meeting room ID mappings

