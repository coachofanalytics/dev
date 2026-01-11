# Analyze Meeting-Task Patterns: Cohort Analysis

**Branch:** 25.12_CODA_DEV_CM  
**Date:** 2024-12-30  
**Status:** ✅ Complete

---

## Summary

Fixed crash and expanded `analyze_meeting_task_patterns` command to support cohort analysis (not just single user). All changes are DB-only, no API calls.

---

## Changes Made

### 1. Fixed Crash: Queryset Slicing Issue

**Problem:** `AssertionError: Cannot filter a query once a slice has been taken.`

**Root Cause:** Queryset was sliced (`[:limit]`) before later `.filter()` calls.

**Solution:**
- Apply all filters first, materialize list, then filter in Python
- Changed `meetings = meetings_query.order_by('-start_time')[:limit]` to materialize first
- Filter candidate meetings in Python using list comprehension

**Files Changed:**
- `coda/ai_services/management/commands/analyze_meeting_task_patterns.py`

---

### 2. Added Cohort Analysis Support

**New Flags:**
- `--group <A|B|C>`: Analyze all employees in specified group
- `--department-id <int>`: Analyze all employees in specified department
- `--limit-users <int>`: Limit number of users in cohort (optional)

**Behavior:**
- If `--user-id` provided: Single user mode (backward compatible)
- If `--group` or `--department-id` provided: Cohort mode
- Uses `get_filtered_employees_queryset()` to get candidate employees
- Processes each user's tasks and scores meetings

---

### 3. Enhanced Scoring Signals

**Added:**
- `meeting_room_id` boost signal (only when matches, not hard filter unless launch intent exists)
- Attendee-name inference (match employee name against `attendee_name`)
- Window mode support (recent_window vs submission_window from ActivityPolicy)

**Scoring Weights:**
- Time window: 20% (base)
- Meeting room ID match: 15% (boost)
- Subject keyword: 30%
- Attendee name: 50%
- Recurring boost: 0-20%

---

### 4. Updated CSV Output Format

**New Columns:**
- `user_id`: User ID (for cohort analysis)
- `task_id`: Task ID
- `activity_slug`: Activity type slug
- `task_submission`: Task submission date
- `candidate_meeting_id`: Meeting ID
- `meeting_start`: Meeting start time
- `meeting_topic`: Meeting topic/subject
- `score`: Match score (0.0-1.0)
- `signals_hit`: Comma-separated list of signals
- `explanation`: Human-readable explanation

**Format:** One row per task-meeting candidate (top 10 per task)

---

### 5. Enhanced Summary Statistics

**New Metrics:**
- `% tasks with top score >= 0.8`: High confidence matches
- `% tasks with top score >= 0.6`: Medium confidence matches
- `% unmatched`: Tasks with no candidate meetings

**Output:**
```
Score Distribution:
  Top score >= 0.8: 45 (32.1%)
  Top score >= 0.6: 78 (55.7%)
  Unmatched: 17 (12.1%)
```

---

### 6. Verbose Stdout Report

**When `--verbose` is used:**
- Shows processing progress per user
- Displays sample tasks and meetings
- Shows top 3 candidates per task (first 20 tasks)
- Includes detailed summary statistics

---

## Usage Examples

### Single User Mode (Backward Compatible)
```bash
poetry run python coda/manage.py analyze_meeting_task_patterns \
  --user-id 495 \
  --days 90 \
  --service internal \
  --out eunice_patterns.csv \
  --verbose
```

### Cohort Mode: Group B
```bash
poetry run python coda/manage.py analyze_meeting_task_patterns \
  --group B \
  --days 120 \
  --service internal \
  --out group_b_patterns.csv \
  --verbose
```

### Cohort Mode: Department
```bash
poetry run python coda/manage.py analyze_meeting_task_patterns \
  --department-id 5 \
  --days 90 \
  --service internal \
  --limit-users 20 \
  --out dept5_patterns.csv \
  --verbose
```

### Cohort Mode: Group B with Limit
```bash
poetry run python coda/manage.py analyze_meeting_task_patterns \
  --group B \
  --days 120 \
  --service internal \
  --limit-users 50 \
  --out group_b_sample.csv \
  --verbose
```

---

## CSV Output Format

```csv
user_id,task_id,activity_slug,task_submission,candidate_meeting_id,meeting_start,meeting_topic,score,signals_hit,explanation
495,123,INTERNAL_TRAINING_SESSION,2024-12-15,123530685,2024-12-15T10:00:00+00:00,Internal Training Session,0.850,time_window attendee_name_0.85 subject_keyword_0.60,attendee name match (0.85); subject keywords match (0.60)
495,123,INTERNAL_TRAINING_SESSION,2024-12-15,616024597,2024-12-14T14:00:00+00:00,Training Workshop,0.650,time_window meeting_room_id subject_keyword_0.40,subject keywords match (0.40); recurring meeting pattern
495,124,DAILY_UPDATE_SESSION,2024-12-16,708385093,2024-12-16T09:00:00+00:00,Daily Update,0.750,time_window attendee_name_0.70,attendee name match (0.70)
```

---

## Summary Statistics Output

```
================================================================================
📈 Summary Statistics
================================================================================
Total tasks analyzed: 140
Tasks with candidate meetings: 123
Tasks without candidates: 17

Score Distribution:
  Top score >= 0.8: 45 (32.1%)
  Top score >= 0.6: 78 (55.7%)
  Unmatched: 17 (12.1%)

Most common meeting_ids:
  616024597: 23 matches (Internal Training Session)
  123530685: 18 matches (DAF Session)
  708385093: 15 matches (Daily Update)
```

---

## Key Features

✅ **DB-Only**: No GoToMeeting API calls  
✅ **Cohort Analysis**: Support for groups and departments  
✅ **Window Mode**: Respects ActivityPolicy window_mode (recent vs submission)  
✅ **Attendee-Name Inference**: Matches employee names against attendee_name  
✅ **Meeting Room Boost**: Uses meeting_room_id as boost signal (not hard filter)  
✅ **Comprehensive Scoring**: Multi-signal approach with explainable scores  
✅ **Summary Statistics**: Shows match quality distribution  

---

## Files Modified

1. **`coda/ai_services/management/commands/analyze_meeting_task_patterns.py`**
   - Fixed queryset slicing crash
   - Added cohort analysis support (--group, --department-id, --limit-users)
   - Enhanced scoring with meeting_room_id boost and attendee-name inference
   - Updated CSV output format
   - Added summary statistics (% tasks with top score >= 0.8, >=0.6, unmatched)
   - Added verbose stdout report

---

## Testing

Run the command with Group B to verify:

```bash
poetry run python coda/manage.py analyze_meeting_task_patterns \
  --group B \
  --days 120 \
  --service internal \
  --out group_b_patterns.csv \
  --verbose
```

**Expected Output:**
- No crash (queryset slicing fixed)
- Processes all Group B employees
- Shows progress per user
- Outputs CSV with correct columns
- Shows summary statistics with score distribution

---

## Notes

- **Backward Compatible**: `--user-id` still works for single user mode
- **Performance**: Materializes meetings list to avoid queryset slicing issues
- **Scalability**: Use `--limit-users` for large cohorts
- **Window Mode**: Automatically uses `recent_window` or `submission_window` based on ActivityPolicy

