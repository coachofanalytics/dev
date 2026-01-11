# Meeting → Task Reconciliation Verification

**Branch:** 26.01_CODA_DEV_CM  
**Date:** 2025-01-02  
**Status:** ✅ Implementation complete

---

## Overview

After meeting sync + attendee sync, meetings must be linked to tasks via TaskLinks so DAF can accurately count `meetings_completed`. This document provides verification steps.

---

## Implementation Summary

### 1. Reconciliation Service

**File:** `coda/management/services/meeting_task_reconciliation_service.py`

**Features:**
- Links meetings to tasks based on:
  - Employee attribution (organizer or attendee)
  - Time window matching (±7 days default)
  - Requirement code matching (if available)
- Creates/updates TaskLinks with `meeting_id`
- Idempotent (safe to run multiple times)

### 2. Management Command

**File:** `coda/management/management/commands/reconcile_meeting_task_links.py`

**Usage:**
```bash
# Reconcile last 30 days
poetry run python manage.py reconcile_meeting_task_links

# Reconcile last 90 days
poetry run python manage.py reconcile_meeting_task_links --days 90

# Dry run (no changes)
poetry run python manage.py reconcile_meeting_task_links --dry-run

# Custom date range
poetry run python manage.py reconcile_meeting_task_links --since 2024-01-01 --until 2024-12-31

# Adjust time window
poetry run python manage.py reconcile_meeting_task_links --window-days 14
```

### 3. Approval Logic Fix

**File:** `coda/management/services/task_quality_gate_service.py`

**Changes:**
- `meeting_ok` now checks if `meetings_completed >= required_meetings`
- Counts distinct `meeting_id` values from TaskLinks (same logic as DAF view)
- Returns `meetings_completed_count` and `required_meeting_count` in gate status

### 4. Optional Hook in Attendee Sync

**File:** `coda/ai_services/management/commands/sync_meeting_attendees.py`

**New flag:** `--reconcile` - Runs reconciliation after attendee sync

---

## Verification Steps

### Clean-Slate Simulation

```bash
# 1. Delete meetings and attendees in test window (optional, for clean test)
# Note: Only do this in dev/test environment!

# 2. Sync meetings
poetry run python manage.py sync_meetings_for_range --start 2024-12-01 --end 2024-12-31 --service gotomeeting_internal

# 3. Sync attendees
poetry run python manage.py sync_meeting_attendees --service internal --days 30

# 4. Run reconciliation
poetry run python manage.py reconcile_meeting_task_links --days 30

# 5. Verify DAF counts
# (See SQL queries below)
```

### SQL Queries for Validation

#### a) Meetings linked per task

```sql
SELECT 
    t.id AS task_id,
    t.activity_name,
    t.employee_id,
    u.username,
    COUNT(DISTINCT tl.meeting_id) AS meetings_linked
FROM management_task t
JOIN auth_user u ON t.employee_id = u.id
LEFT JOIN management_tasklinks tl ON tl.task_id = t.id 
    AND tl.is_active = TRUE 
    AND tl.meeting_id IS NOT NULL 
    AND tl.meeting_id != ''
WHERE t.is_active = TRUE
GROUP BY t.id, t.activity_name, t.employee_id, u.username
HAVING COUNT(DISTINCT tl.meeting_id) > 0
ORDER BY meetings_linked DESC
LIMIT 20;
```

#### b) Meetings completed per DAF activity

```sql
-- For a specific task (replace TASK_ID)
SELECT 
    t.id AS task_id,
    t.activity_name,
    u.username,
    COUNT(DISTINCT tl.meeting_id) AS meetings_completed,
    -- Get required count from policy (simplified - check activity_definitions.py for actual values)
    CASE 
        WHEN t.activity_name LIKE '%Training%' THEN 5
        ELSE 1
    END AS required_meetings,
    CASE 
        WHEN COUNT(DISTINCT tl.meeting_id) >= CASE 
            WHEN t.activity_name LIKE '%Training%' THEN 5
            ELSE 1
        END THEN 'APPROVED'
        ELSE 'IN_PROGRESS'
    END AS status
FROM management_task t
JOIN auth_user u ON t.employee_id = u.id
LEFT JOIN management_tasklinks tl ON tl.task_id = t.id 
    AND tl.is_active = TRUE 
    AND tl.meeting_id IS NOT NULL 
    AND tl.meeting_id != ''
WHERE t.id = TASK_ID  -- Replace with actual task ID
GROUP BY t.id, t.activity_name, u.username;
```

#### c) Status logic validation

```sql
-- Check tasks with meeting requirements
SELECT 
    t.id,
    t.activity_name,
    u.username,
    COUNT(DISTINCT tl.meeting_id) AS meetings_completed,
    t.mxpoint AS required_meetings_fallback,
    CASE 
        WHEN COUNT(DISTINCT tl.meeting_id) >= COALESCE(t.mxpoint, 1) THEN 'APPROVED'
        ELSE 'IN_PROGRESS'
    END AS computed_status
FROM management_task t
JOIN auth_user u ON t.employee_id = u.id
LEFT JOIN management_tasklinks tl ON tl.task_id = t.id 
    AND tl.is_active = TRUE 
    AND tl.meeting_id IS NOT NULL 
    AND tl.meeting_id != ''
WHERE t.is_active = TRUE
    AND t.activity_name IN (
        'Internal Training Session',
        'Product Backlog Refinement',
        'UAT Testing Support'
    )
GROUP BY t.id, t.activity_name, u.username, t.mxpoint
ORDER BY meetings_completed DESC;
```

### Django Shell Queries

```python
from management.models import Task, TaskLinks
from ai_services.models import Meeting
from django.contrib.auth import get_user_model
User = get_user_model()

# 1. Check meetings linked per task
task = Task.objects.get(id=TASK_ID)  # Replace with actual task ID
task_links = TaskLinks.objects.filter(
    task=task,
    is_active=True
).exclude(Q(meeting_id__isnull=True) | Q(meeting_id=''))

distinct_meeting_ids = set(link.meeting_id for link in task_links if link.meeting_id)
print(f"Task {task.id}: {len(distinct_meeting_ids)} meetings linked")
print(f"Meeting IDs: {distinct_meeting_ids}")

# 2. Check meetings_completed for DAF activity
from management.services.task_quality_gate_service import TaskQualityGateService
service = TaskQualityGateService()
gate_status = service.get_task_gate_status(task)

print(f"Meetings completed: {gate_status['meetings_completed_count']}")
print(f"Required meetings: {gate_status['required_meeting_count']}")
print(f"Meeting OK: {gate_status['meeting_ok']}")
print(f"Overall ready: {gate_status['overall_ready']}")

# 3. Verify reconciliation created TaskLinks
meeting = Meeting.objects.get(meeting_id=MEETING_ID)  # Replace with actual meeting_id
tasklinks = TaskLinks.objects.filter(meeting_id=meeting.meeting_id, is_active=True)
print(f"Meeting {meeting.meeting_id} linked to {tasklinks.count()} tasks")
for tl in tasklinks:
    print(f"  - Task {tl.task.id}: {tl.task.activity_name}")
```

### End-to-End Test: 5/5 Meetings Required

```bash
# 1. Find a task requiring 5 meetings (e.g., Internal Training Session)
# 2. Ensure 5 meetings exist for that employee in the time window
# 3. Run reconciliation
poetry run python manage.py reconcile_meeting_task_links --days 30

# 4. Check DAF view - should show "5/5" and status should be "Approved"
# 5. Verify via SQL:
SELECT 
    t.id,
    t.activity_name,
    COUNT(DISTINCT tl.meeting_id) AS meetings_completed
FROM management_task t
LEFT JOIN management_tasklinks tl ON tl.task_id = t.id 
    AND tl.is_active = TRUE 
    AND tl.meeting_id IS NOT NULL
WHERE t.id = TASK_ID  -- Replace with task ID
GROUP BY t.id, t.activity_name;
```

---

## Expected Behavior

### Before Reconciliation
- Meetings synced but not linked to tasks
- DAF shows "0/5" or "1/5" even when 5 meetings exist
- Status shows "In Progress" even when requirement met

### After Reconciliation
- Meetings linked to tasks via TaskLinks with `meeting_id`
- DAF shows accurate count (e.g., "5/5")
- Status shows "Approved" when `meetings_completed >= required_meetings`
- Status shows "In Progress" with "X/N" when requirement not met

---

## Debug Logging

The reconciliation service logs:
- How many meetings were processed
- How many meetings were linked to tasks
- How many TaskLinks were created/updated
- Per-task meeting counts (via `recompute_meeting_counts_for_tasks`)

Check logs for:
```
🔄 Starting meeting reconciliation: N meetings, time_window=7 days
✅ Created TaskLink: meeting_id=XXX, task_id=YYY, employee=username
📊 Meeting counts: N tasks processed, M with meetings, K total meetings linked
```

---

## Files Changed

1. **NEW:** `coda/management/services/meeting_task_reconciliation_service.py`
2. **NEW:** `coda/management/management/commands/reconcile_meeting_task_links.py`
3. **UPDATED:** `coda/management/services/task_quality_gate_service.py`
4. **UPDATED:** `coda/ai_services/management/commands/sync_meeting_attendees.py` (optional --reconcile flag)

---

## Commands Summary

```bash
# Reconcile meetings with tasks
poetry run python manage.py reconcile_meeting_task_links --days 30

# Sync attendees and auto-reconcile
poetry run python manage.py sync_meeting_attendees --service internal --days 30 --reconcile

# Dry run (test without changes)
poetry run python manage.py reconcile_meeting_task_links --dry-run
```

