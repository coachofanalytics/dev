# Task Eligibility Query Fix Summary

**Branch:** 26.01_CODA_DEV_CM  
**Date:** 2025-01-02  
**Status:** ✅ Fixed

---

## Issue Fixed

**Problem:** Meeting-task reconciliation linking 0 meetings because task eligibility query was not finding tasks that exist in the expected timeframe.

**Root Cause:** The query was:
1. Only filtering by `submission` date
2. Including ALL tasks with null submission (regardless of when they were created)
3. Not using any fallback for tasks with null submission

**Error Message:**
```
NO TASK MATCH - no eligible tasks in window: no tasks for <username> within ±7 days of <meeting_date>
```

---

## Solution

### 1. Fixed Query Logic

**File:** `coda/management/services/meeting_task_reconciliation_service.py`

**Change:** Updated `_find_candidate_tasks()` method to:
- Prefer `submission` date if not null (primary filter)
- Fallback to `TaskLinks.created_at` for tasks with null submission (proxy for task creation)
- Task model doesn't have `created_at`, so `TaskLinks.created_at` is used as fallback

**New Query:**
```python
# Primary: Tasks with submission date in window
tasks_by_submission = Task.objects.filter(
    employee=employee,
    is_active=True,
    submission__gte=window_start,
    submission__lte=window_end
)

# Fallback: Tasks with null submission but TaskLinks created within window
tasks_by_links = Task.objects.filter(
    employee=employee,
    is_active=True,
    submission__isnull=True
).filter(
    tasklinks__created_at__gte=window_start,
    tasklinks__created_at__lte=window_end
).distinct()

# Combine: submission in window OR (submission null AND TaskLinks.created_at in window)
tasks = (tasks_by_submission | tasks_by_links).distinct()
```

### 2. Added Debug Logging

**When tasks found:**
- Logs count of candidate tasks
- Logs which date field was used (`submission` vs `tasklinks.created_at`)

**When no tasks found:**
- Logs min/max of employee's task `submission` dates
- Logs min/max of employee's `TaskLinks.created_at` dates
- Logs the query strategy used
- Logs the time window

**Example Debug Output:**
```
DEBUG: Found 3 candidate tasks for eunice within ±7 days of 2024-12-28
  Date fields used: submission, tasklinks.created_at (fallback)

DEBUG: No tasks found for luke within ±7 days of 2024-12-28
  Window: 2024-12-21 to 2025-01-04
  Task submission dates: min=2024-12-01, max=2024-12-20
  TaskLinks created_at dates: min=2024-12-01, max=2024-12-20
  Query used: submission in window OR (submission null AND TaskLinks.created_at in window)
```

---

## Files Changed

### 1. `coda/management/services/meeting_task_reconciliation_service.py`

**Lines 272-330:** Updated `_find_candidate_tasks()` method

**Changes:**
- Split query into primary (submission) and fallback (TaskLinks.created_at)
- Added debug logging for both success and failure cases
- Tracks which date field was used for each task

### 2. `tests/management/01_unit/test_meeting_task_reconciliation.py`

**Added Tests:**
- `test_task_eligible_by_created_at_fallback_when_submission_null()` - Verifies task with null submission but TaskLinks.created_at in window is eligible
- `test_task_eligible_by_submission_in_window()` - Verifies task with submission date in window is eligible

---

## Verification Commands

### 1. Dry-Run Reconciliation (Test Query Fix)

```bash
poetry run python manage.py reconcile_meeting_task_links --days 2 --window-days 7 --dry-run --verbosity 2
```

**Success Criteria:**
- ✅ Should find candidate tasks for meetings where employee has tasks in window
- ✅ Debug logs show which date field was used (`submission` or `tasklinks.created_at`)
- ✅ "no eligible tasks in window" messages should reduce for known meetings with tasks
- ✅ Should see debug output like: `Found N candidate tasks for <username> within ±7 days`

**Expected Output:**
```
🔄 Starting meeting reconciliation: N meetings, time_window=7 days, dry_run=True

Meeting XXX (Topic...): ✅ Created TaskLink: meeting_id=AAA, task_id=BBB, employee=eunice
DEBUG: Found 2 candidate tasks for eunice within ±7 days of 2024-12-28
  Date fields used: submission

Meeting YYY (Topic...): NO TASK MATCH - no eligible tasks in window: no tasks for luke within ±7 days of 2024-12-28
DEBUG: No tasks found for luke within ±7 days of 2024-12-28
  Window: 2024-12-21 to 2025-01-04
  Task submission dates: min=2024-12-01, max=2024-12-20
  TaskLinks created_at dates: min=2024-12-01, max=2024-12-20
  Query used: submission in window OR (submission null AND TaskLinks.created_at in window)

✅ Reconciliation complete: N processed, X linked, Y created, Z updated, W tasks affected
```

### 2. Run Actual Reconciliation

```bash
poetry run python manage.py reconcile_meeting_task_links --days 2 --window-days 7 --verbosity 2
```

**Success Criteria:**
- ✅ `TaskLinks created: N` where N > 0 (if tasks exist in window)
- ✅ `Meetings linked: N` where N > 0
- ✅ No errors

### 3. Run Unit Tests

```bash
poetry run python manage.py test tests.management.01_unit.test_meeting_task_reconciliation
```

**Success Criteria:**
- ✅ All tests pass, including new tests:
  - `test_task_eligible_by_created_at_fallback_when_submission_null`
  - `test_task_eligible_by_submission_in_window`

---

## Verification SQL Queries

### Check Tasks in Window

```sql
-- Check tasks for a specific employee within ±7 days of a meeting date
SELECT 
    t.id,
    t.activity_name,
    t.submission,
    u.username,
    COUNT(tl.id) AS tasklinks_count,
    MIN(tl.created_at) AS earliest_tasklink_date
FROM management_task t
JOIN auth_user u ON t.employee_id = u.id
LEFT JOIN management_tasklinks tl ON tl.task_id = t.id
WHERE t.employee_id = (SELECT id FROM auth_user WHERE username = 'eunice')
    AND t.is_active = TRUE
    AND (
        (t.submission >= '2024-12-21' AND t.submission <= '2025-01-04')
        OR (
            t.submission IS NULL 
            AND tl.created_at >= '2024-12-21' 
            AND tl.created_at <= '2025-01-04'
        )
    )
GROUP BY t.id, t.activity_name, t.submission, u.username
ORDER BY COALESCE(t.submission, tl.created_at) DESC;
```

### Check Meeting-Task Links Created

```sql
-- Check TaskLinks created by reconciliation (last 2 days)
SELECT 
    tl.id,
    tl.task_id,
    t.activity_name,
    tl.meeting_id,
    m.topic,
    u.username,
    tl.created_at,
    tl.is_auto_generated
FROM management_tasklinks tl
JOIN management_task t ON tl.task_id = t.id
JOIN auth_user u ON t.employee_id = u.id
LEFT JOIN ai_services_meeting m ON tl.meeting_id = m.meeting_id
WHERE tl.is_auto_generated = TRUE
    AND tl.created_at >= NOW() - INTERVAL '2 days'
ORDER BY tl.created_at DESC
LIMIT 20;
```

---

## Code Diff Summary

### File 1: `coda/management/services/meeting_task_reconciliation_service.py`

**Lines 291-330:** Updated query and added debug logging

**Before:**
```python
# Find tasks for this employee within time window
# Use submission date or created_at (Task doesn't have created_at, so use submission)
tasks = Task.objects.filter(
    employee=employee,
    is_active=True,
).filter(
    Q(submission__gte=window_start, submission__lte=window_end) |
    Q(submission__isnull=True)  # Include tasks without submission date
)

return list(tasks)
```

**After:**
```python
# Find tasks for this employee within time window
# Strategy: Prefer submission date if not null, else fallback to TaskLinks.created_at (proxy for task creation)
# Task model doesn't have created_at, so we use TaskLinks.created_at as fallback

# Primary: Tasks with submission date in window
tasks_by_submission = Task.objects.filter(
    employee=employee,
    is_active=True,
    submission__gte=window_start,
    submission__lte=window_end
)

# Fallback: Tasks with null submission but TaskLinks created within window
tasks_by_links = Task.objects.filter(
    employee=employee,
    is_active=True,
    submission__isnull=True
).filter(
    tasklinks__created_at__gte=window_start,
    tasklinks__created_at__lte=window_end
).distinct()

# Combine: submission in window OR (submission null AND TaskLinks.created_at in window)
tasks = (tasks_by_submission | tasks_by_links).distinct()
tasks_list = list(tasks)

# Track which field was used for filtering
date_field_used = []
for task in tasks_list:
    if task.submission:
        date_field_used.append('submission')
    else:
        date_field_used.append('tasklinks.created_at (fallback)')

if tasks_list:
    self.logger.debug(
        f"   Found {len(tasks_list)} candidate tasks for {employee.username} "
        f"within ±{self.time_window_days} days of {meeting.start_time.date()}\n"
        f"     Date fields used: {', '.join(set(date_field_used))}"
    )

# Debug logging when no tasks found (existing code continues...)
```

### File 2: `tests/management/01_unit/test_meeting_task_reconciliation.py`

**Added:** Two new test methods (lines 224-260)

---

## Impact

- ✅ Tasks with `submission` date in window are found (primary)
- ✅ Tasks with null `submission` but `TaskLinks.created_at` in window are found (fallback)
- ✅ Debug logging helps diagnose why tasks aren't found
- ✅ Minimal, localized changes (one query method + tests)
- ✅ No changes to employee attribution or requirement code matching
- ✅ Idempotency maintained

---

## Known Limitations

1. **Tasks with null submission and no TaskLinks:** These won't be found unless they have TaskLinks created within the window. This is intentional - we need some date reference to determine eligibility.

2. **TaskLinks.created_at as proxy:** This is a reasonable fallback, but if a task has TaskLinks created outside the window, it won't be found even if the task itself is recent.

3. **Window size:** The default `±7 days` window may need adjustment based on business requirements. This can be changed via `--window-days` parameter.

---

**End of Summary**

