# Phase 2A+1: Meeting Analysis & Normalization Summary

**Date:** 2024-12-28  
**Status:** ✅ **COMPLETE**

---

## Summary

Implemented meeting analysis and normalization utilities to:
1. ✅ Analyze existing Meeting data from the database (no API calls)
2. ✅ Normalize meeting topics and URLs for better matching
3. ✅ Extract candidate activity tags using keyword matching
4. ✅ Apply URL normalization in persistence path for cleaner future ingests

---

## Files Created/Modified

### 1. `coda/ai_services/utils/meeting_normalizer.py` (NEW)

**Purpose:** Utilities for normalizing meeting topics, URLs, and extracting activity tags

**Functions:**
- `normalize_topic(topic: str) -> str`
  - Lowercase, trim, collapse whitespace
  - Removes noise tokens (recording, session, meeting, gotomeeting)
  - Strips repeated punctuation
  - Conservative approach: preserves meaning

- `normalize_url(url: str) -> Optional[str]`
  - Strips querystring and fragments
  - Removes trailing slashes
  - Returns None for empty/invalid input

- `extract_candidate_activity_tags(topic: str) -> List[str]`
  - Rule-based keyword matching
  - Returns tags like: ["pbr", "client_training", "internal_training", "self_training", "daily_update", "sprint", "demo", "review", "planning", "job_support"]
  - Not a final mapping engine; helps analyze naming patterns

### 2. `coda/ai_services/management/commands/sample_meetings.py` (NEW)

**Purpose:** Analyze existing meetings in the database (no API calls)

**Usage:**
```bash
# Default: last 14 days, limit 25
poetry run python coda/manage.py sample_meetings

# Custom options
poetry run python coda/manage.py sample_meetings --days 30 --limit 50
poetry run python coda/manage.py sample_meetings --since "2025-12-01" --limit 100
poetry run python coda/manage.py sample_meetings --export /tmp/meetings_sample.csv
```

**Output Report:**
- Total meetings in range
- % recorded
- Top 20 topic patterns (normalized)
- Count with recording_url/download_url
- Candidate activity tags (keyword-based)
- Sample rows with key fields

### 3. `coda/ai_services/views.py` (MODIFIED)

**Changes:**
- Added URL normalization in `save_meeting_data()` function
- Applies `normalize_url()` to `recording_url` and `download_url` before saving
- Both create and update paths normalize URLs
- Safe improvement: no schema changes, improves matching quality

**Locations:**
- Line ~427: Normalize URLs in `get_or_create` defaults
- Line ~447: Normalize URLs in `update` call

### 4. `coda/ai_services/tests/test_meeting_normalizer.py` (NEW)

**Purpose:** Comprehensive tests for normalization utilities

**Test Coverage:**
- ✅ `TestNormalizeTopic`: 7 test methods
  - Lowercase and trim
  - Whitespace collapsing
  - Noise token removal
  - Meaning preservation
  - Empty input handling
  - Punctuation handling
  - Leading/trailing punctuation removal

- ✅ `TestNormalizeUrl`: 6 test methods
  - Fragment removal
  - Querystring removal
  - Trailing slash removal
  - Combined normalization
  - Empty input handling
  - Valid URL preservation

- ✅ `TestExtractCandidateActivityTags`: 10 test methods
  - PBR tags
  - Training tags (client, internal, self)
  - Daily update tags
  - Sprint tags
  - Demo tags
  - Multiple tags
  - Case-insensitive matching
  - Empty input
  - No matches

---

## Test Results

```bash
poetry run python coda/manage.py test ai_services.tests.test_meeting_normalizer -v 2
```

**Result:** ✅ **All tests PASSING**

- 23 test methods covering all normalization functions
- Edge cases and error handling tested
- No network dependencies

---

## How to Use

### 1. Analyze Existing Meetings

```bash
# Analyze last 14 days (default)
poetry run python coda/manage.py sample_meetings

# Analyze last 30 days with more samples
poetry run python coda/manage.py sample_meetings --days 30 --limit 50

# Analyze since specific date
poetry run python coda/manage.py sample_meetings --since "2025-12-01" --limit 100

# Export to CSV for further analysis
poetry run python coda/manage.py sample_meetings --days 60 --export /tmp/meetings_analysis.csv
```

### 2. Example Output Format

```
================================================================================
Meeting Analysis Report
================================================================================

Date Range: 2025-12-14 to 2025-12-28
Total Meetings: 45
Recorded: 32 (71.1%)
With Recording URL: 28
With Download URL: 25

--------------------------------------------------------------------------------
Top 20 Topic Patterns (Normalized)
--------------------------------------------------------------------------------
   12 ( 26.7%): pbr                                            [sample: 123456789]
    8 ( 17.8%): client training: django                        [sample: 987654321]
    6 ( 13.3%): internal training session                      [sample: 456789012]
    5 ( 11.1%): daily update                                   [sample: 345678901]
    4 (  8.9%): sprint planning                                [sample: 234567890]
    ...

--------------------------------------------------------------------------------
Candidate Activity Tags (Keyword-Based)
--------------------------------------------------------------------------------
  pbr                  :   12 meetings ( 26.7%)
  client_training      :    8 meetings ( 17.8%)
  internal_training    :    6 meetings ( 13.3%)
  daily_update         :    5 meetings ( 11.1%)
  sprint               :    4 meetings (  8.9%)
  ...

--------------------------------------------------------------------------------
Sample Rows (showing up to 25)
--------------------------------------------------------------------------------
Meeting ID      Start Time           Duration    Topic                                  Has Recording  Has Download
-------------------------------------------------------------------------------------------------------------------
123456789       2025-12-27 14:30     60 min     PBR Session                            ✓              ✓
987654321       2025-12-27 10:00     90 min     Client Training: Django Best Practices ✓              ✓
456789012       2025-12-26 15:00     45 min     Internal Training Session              ✓              ✗
...

================================================================================
Analysis Complete
================================================================================
```

### 3. CSV Export Format

The exported CSV includes:
- `meeting_id`
- `start_time` (ISO format)
- `duration_minutes`
- `topic` (raw)
- `topic_normalized`
- `has_recording_url` (boolean)
- `has_download_url` (boolean)
- `is_recorded` (boolean)
- `attendee_count`
- `candidate_tags` (comma-separated)

---

## Architecture Decisions

### URL Normalization in Persistence

**Why:** URLs often come with querystrings, fragments, and trailing slashes that can cause matching issues. Normalizing at persistence ensures:
- Consistent storage format
- Better matching in later phases
- No schema changes required (safe improvement)

**Implementation:**
- Applied in `save_meeting_data()` before `get_or_create` and `update`
- Uses `normalize_url()` utility
- Preserves existing behavior if URL is None/empty

### Topic Normalization (Analysis Only)

**Why:** Meeting topics vary widely in format. Normalization helps:
- Group similar meetings for analysis
- Identify naming patterns
- Prepare for Phase 2B matching logic

**Implementation:**
- Used in analysis command only (not persisted)
- Conservative approach: preserves meaning while removing noise
- Helps identify patterns without destroying data

### Candidate Activity Tags

**Why:** Keyword-based tagging helps:
- Identify which meetings might map to which activities
- Understand naming conventions
- Prepare mapping rules for Phase 2B

**Implementation:**
- Rule-based, simple keyword matching
- Not a final mapping engine
- Helps with analysis and pattern identification

---

## Constraints Met

✅ **No GoToMeeting API calls** (uses existing DB data only)  
✅ **No changes to checklist/quality scoring logic**  
✅ **No modifications to TaskLinks**  
✅ **Minimal changes** (3 new files, small modifications to views.py)  
✅ **URL normalization in persistence** (safe, no schema changes)  
✅ **All tests passing**

---

## Next Steps (Phase 2B)

Use the analysis output to:
1. Identify naming patterns that will affect TaskLinks → Meeting matching
2. Design matching rules based on normalized topics and candidate tags
3. Implement automatic linking between meetings and tasks
4. Handle edge cases and ambiguous matches

---

## Files Summary

**Created:**
1. `coda/ai_services/utils/meeting_normalizer.py` (139 lines)
2. `coda/ai_services/management/commands/sample_meetings.py` (173 lines)
3. `coda/ai_services/tests/test_meeting_normalizer.py` (176 lines)

**Modified:**
1. `coda/ai_services/views.py` (added URL normalization in 2 locations)

**Total:** 3 new files, 1 modified file, ~488 lines of new code

---

**Implementation Complete** ✅

