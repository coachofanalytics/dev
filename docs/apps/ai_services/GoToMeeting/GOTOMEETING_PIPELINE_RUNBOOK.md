# GoToMeeting → Meetings/Attendees → TaskLinks → DAF Gate Pipeline

**Branch:** 26.01_CODA_DEV_CM  
**Last Updated:** 2025-01-02

---

## A) Commands Found

| Command | Path | Purpose | Key Args | Example (2 days) | Example (7 days) | Verbose | Dry-run |
|---------|------|---------|----------|------------------|-------------------|---------|---------|
| `sync_gotomeetings` | `coda/ai_services/management/commands/sync_gotomeetings.py` | Sync meetings from GoToMeeting API → `Meeting` table | `--start YYYY-MM-DD`, `--end YYYY-MM-DD`, `--days N`, `--service internal\|external\|all` | `poetry run python manage.py sync_gotomeetings --days 2 --service internal` | `poetry run python manage.py sync_gotomeetings --days 7 --service internal` | ❌ No | ❌ No |
| `sync_meeting_attendees` | `coda/ai_services/management/commands/sync_meeting_attendees.py` | Sync attendees from GoToMeeting API → `MeetingAttendee` table | `--service internal\|external\|all`, `--days N`, `--limit N`, `--max-age-hours N`, `--verbose`, `--reconcile` | `poetry run python manage.py sync_meeting_attendees --service internal --days 2 --verbose` | `poetry run python manage.py sync_meeting_attendees --service internal --days 7 --verbose` | ✅ `--verbose` | ❌ No |
| `reconcile_meeting_task_links` | `coda/management/management/commands/reconcile_meeting_task_links.py` | Link meetings to tasks → create/update `TaskLinks` | `--days N`, `--since YYYY-MM-DD`, `--until YYYY-MM-DD`, `--window-days N`, `--dry-run` | `poetry run python manage.py reconcile_meeting_task_links --days 2 --dry-run` | `poetry run python manage.py reconcile_meeting_task_links --days 7` | ❌ No | ✅ `--dry-run` |
| **DAF Gate Refresh** | **Not found** | No dedicated command - computed on-demand | N/A | N/A | N/A | N/A | N/A |

---

## B) Detailed Command Reference

### 1. Meeting Sync: `sync_gotomeetings`

**Canonical Command** (most referenced in docs)

**File:** `coda/ai_services/management/commands/sync_gotomeetings.py`

**Service Used:** `ai_services.services.meeting_sync_service.sync_meetings_for_range`

**Arguments:**
- `--start YYYY-MM-DD` - Start date (optional, defaults to 7 days ago)
- `--end YYYY-MM-DD` - End date (optional, defaults to today)
- `--days N` - Number of days back from today (default: 7, ignored if --start provided)
- `--service internal|external|all` - Service name (default: `gotomeeting_internal`)

**Examples:**

```bash
# Last 2 days (internal account)
poetry run python manage.py sync_gotomeetings --days 2 --service internal

# Last 7 days (internal account)
poetry run python manage.py sync_gotomeetings --days 7 --service internal

# Custom date range (internal)
poetry run python manage.py sync_gotomeetings --start 2024-12-01 --end 2024-12-31 --service internal

# Sync both services
poetry run python manage.py sync_gotomeetings --days 7 --service all
```

**Expected Output:**
```
🔄 Syncing GoToMeeting meetings from 2024-12-26 to 2024-12-28...

📡 Syncing gotomeeting_internal...

✅ Synced gotomeeting_internal: 15 fetched, 10 created, 5 updated

📊 Summary: 15 meetings fetched, 10 created, 5 updated, 0 attendees created, 0 attendees updated
```

**Note:** This command does NOT sync attendees (attendees are synced separately via `sync_meeting_attendees`).

---

### 2. Attendee Sync: `sync_meeting_attendees`

**File:** `coda/ai_services/management/commands/sync_meeting_attendees.py`

**Service Used:** `ai_services.services.attendee_sync_service`

**Arguments:**
- `--service internal|external|all` - Service to sync (default: `internal`)
- `--days N` - Number of days to look back (default: 120)
- `--limit N` - Maximum number of meetings to process (optional)
- `--max-age-hours N` - Maximum age of attendee data before considered stale (default: 24)
- `--no-split-names` - Disable splitting combined attendee names
- `--verbose` - Show detailed output
- `--reconcile` - Run meeting-task reconciliation after attendee sync (creates TaskLinks)

**Examples:**

```bash
# Last 2 days with verbose logging
poetry run python manage.py sync_meeting_attendees --service internal --days 2 --verbose

# Last 7 days with reconciliation
poetry run python manage.py sync_meeting_attendees --service internal --days 7 --reconcile

# Last 30 days, limit to 50 meetings, verbose
poetry run python manage.py sync_meeting_attendees --service internal --days 30 --limit 50 --verbose

# Sync both services
poetry run python manage.py sync_meeting_attendees --service all --days 7
```

**Expected Output:**
```
🔄 Syncing Meeting Attendees (DB-First Selection)
Service: internal
Days: 2
Max age (stale threshold): 24 hours
Split combined names: True

Found 12 meetings needing attendee sync

Processing meeting 1/12: 123-456-789
✅ Fetched 5 attendees for meeting 123-456-789 (filtered by instance key: 12345)
✅ Synced attendees for meeting 123-456-789: 5 created, 0 updated

📊 Summary: 12 meetings processed, 12 succeeded, 0 failed, 0 quarantined, 60 attendees created, 0 updated
```

---

### 3. Reconciliation: `reconcile_meeting_task_links`

**File:** `coda/management/management/commands/reconcile_meeting_task_links.py`

**Service Used:** `management.services.meeting_task_reconciliation_service.MeetingTaskReconciliationService`

**Arguments:**
- `--days N` - Number of days back to reconcile (default: 30)
- `--since YYYY-MM-DD` - Start date (optional)
- `--until YYYY-MM-DD` - End date (optional)
- `--window-days N` - Time window for task matching in days (default: 7)
- `--dry-run` - Simulate reconciliation without creating/updating TaskLinks

**Examples:**

```bash
# Last 2 days (dry-run)
poetry run python manage.py reconcile_meeting_task_links --days 2 --dry-run

# Last 7 days
poetry run python manage.py reconcile_meeting_task_links --days 7

# Custom date range
poetry run python manage.py reconcile_meeting_task_links --since 2024-12-01 --until 2024-12-31

# Wider time window (14 days)
poetry run python manage.py reconcile_meeting_task_links --days 30 --window-days 14
```

**Expected Output:**
```
Reconciling meetings from 2024-12-26 to 2024-12-28
Time window: ±7 days

Meeting XXX (Topic...): NO TASK MATCH - no employee match: no attendees found
Meeting YYY (Topic...): ✅ Created TaskLink: meeting_id=AAA, task_id=BBB, employee=username

================================================================================
RECONCILIATION RESULTS
================================================================================
Meetings processed: 15
Meetings linked: 12
TaskLinks created: 10
TaskLinks updated: 2
Tasks affected: 8

Recomputing meeting counts...
Tasks processed: 8
Tasks with meetings: 8
Total meetings linked: 12
```

---

### 4. DAF Quality Gate Status

**Status:** No dedicated refresh command found

**Computed On-Demand:**
- Service: `management.services.task_quality_gate_service.TaskQualityGateService`
- Method: `get_task_gate_status(task)`
- Used by: DAF v2 view, evidence upload page, manager review queue

**Gate Status Includes:**
- `meetings_completed_count` - Distinct meeting_ids from TaskLinks
- `required_meeting_count` - From ActivityPolicy or task.mxpoint
- `meeting_ok` - `meetings_completed_count >= required_meeting_count`

**Note:** Gate status is computed dynamically when tasks are viewed. No refresh command needed - reconciliation updates TaskLinks, which are then counted by the gate service.

---

## C) Celery Beat / Periodic Scheduling

### Scheduled Tasks

**File:** `coda/celeryapp.py` (lines 87-118)

**Daily Meeting Sync:**
- **Task:** `ai_services.tasks.daily_meeting_sync_task`
- **Schedule:** `crontab(hour=1, minute=0)` - Daily at 1 AM UTC
- **Function:** Syncs yesterday's meetings using `meeting_sync_service.sync_meetings_for_range`
- **Manual Execution:**
  ```python
  from ai_services.tasks import daily_meeting_sync_task
  daily_meeting_sync_task.delay()  # Async
  daily_meeting_sync_task()  # Sync
  ```

**Monthly Task Reset:**
- **Task:** `task_history` (maps to `coda_project.task.dump_data`)
- **Schedule:** `crontab(hour=0, minute=0, day_of_month='1')` - 1st of month at midnight
- **Note:** This is the DAF monthly reset, not meeting-related

**Alternative Scheduled Approach:**
- Use `sync_goto_meetings_if_stale` command via cron/Celery Beat
- **File:** `coda/ai_services/management/commands/sync_goto_meetings_if_stale.py`
- **Example cron:**
  ```bash
  0 * * * * cd /path/to/uat && poetry run python manage.py sync_goto_meetings_if_stale --service external --max-age-minutes 60 --hours 24
  ```

---

## D) Final Copy/Paste Runbook

### Standard Pipeline (Last 2 Days)

```bash
# 1. Sync meetings from GoToMeeting API
poetry run python manage.py sync_gotomeetings --days 2 --service internal

# 2. Sync attendees for those meetings
poetry run python manage.py sync_meeting_attendees --service internal --days 2 --verbose

# 3. Reconcile meetings → tasks (create TaskLinks)
poetry run python manage.py reconcile_meeting_task_links --days 2

# 4. Verify (optional - SQL queries below)
```

### Backfill Pipeline (Last 7 Days)

```bash
# 1. Sync meetings
poetry run python manage.py sync_gotomeetings --days 7 --service internal

# 2. Sync attendees
poetry run python manage.py sync_meeting_attendees --service internal --days 7 --verbose

# 3. Reconcile (with wider window if needed)
poetry run python manage.py reconcile_meeting_task_links --days 7 --window-days 7

# 4. Verify
```

### With Reconciliation Hook (Attendee Sync → Auto Reconcile)

```bash
# 1. Sync meetings
poetry run python manage.py sync_gotomeetings --days 7 --service internal

# 2. Sync attendees + auto-reconcile
poetry run python manage.py sync_meeting_attendees --service internal --days 7 --verbose --reconcile
```

### Dry-Run Verification

```bash
# Test reconciliation without making changes
poetry run python manage.py reconcile_meeting_task_links --days 7 --dry-run
```

---

## E) Verification SQL Queries

### 1. Check Meetings Synced

```sql
-- Count meetings by service (last 7 days)
SELECT 
    service_name,
    COUNT(*) AS meeting_count,
    COUNT(DISTINCT meeting_id) AS unique_meeting_ids
FROM ai_services_meeting
WHERE start_time >= NOW() - INTERVAL '7 days'
GROUP BY service_name;
```

### 2. Check Attendees Persisted

```sql
-- Count attendees by meeting (last 7 days)
SELECT 
    m.meeting_id,
    m.meeting_instance_key,
    COUNT(ma.id) AS attendee_count,
    COUNT(CASE WHEN ma.is_organizer THEN 1 END) AS organizer_count
FROM ai_services_meeting m
LEFT JOIN ai_services_meetingattendee ma ON m.id = ma.meeting_id
WHERE m.start_time >= NOW() - INTERVAL '7 days'
GROUP BY m.meeting_id, m.meeting_instance_key
HAVING COUNT(ma.id) > 0
ORDER BY m.start_time DESC
LIMIT 20;
```

### 3. Check Meetings Linked to Tasks

```sql
-- Meetings linked per task (last 7 days)
SELECT 
    t.id AS task_id,
    t.activity_name,
    u.username,
    COUNT(DISTINCT tl.meeting_id) AS meetings_linked,
    t.mxpoint AS required_meetings
FROM management_task t
JOIN auth_user u ON t.employee_id = u.id
LEFT JOIN management_tasklinks tl ON tl.task_id = t.id 
    AND tl.is_active = TRUE 
    AND tl.meeting_id IS NOT NULL 
    AND tl.meeting_id != ''
WHERE t.is_active = TRUE
    AND t.submission >= NOW() - INTERVAL '7 days'
GROUP BY t.id, t.activity_name, u.username, t.mxpoint
HAVING COUNT(DISTINCT tl.meeting_id) > 0
ORDER BY meetings_linked DESC
LIMIT 20;
```

### 4. Check DAF Approval Status

```sql
-- Tasks with meeting requirements and completion status
SELECT 
    t.id,
    t.activity_name,
    u.username,
    COUNT(DISTINCT tl.meeting_id) AS meetings_completed,
    t.mxpoint AS required_meetings,
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
    AND t.submission >= NOW() - INTERVAL '7 days'
GROUP BY t.id, t.activity_name, u.username, t.mxpoint
ORDER BY meetings_completed DESC;
```

---

## F) Django Shell Verification

```python
from management.models import Task, TaskLinks
from management.services.task_quality_gate_service import TaskQualityGateService
from ai_services.models import Meeting, MeetingAttendee

# 1. Check meetings synced
meetings = Meeting.objects.filter(start_time__gte=timezone.now() - timedelta(days=7))
print(f"Meetings synced (last 7 days): {meetings.count()}")

# 2. Check attendees
attendees = MeetingAttendee.objects.filter(meeting__start_time__gte=timezone.now() - timedelta(days=7))
print(f"Attendees synced (last 7 days): {attendees.count()}")

# 3. Check TaskLinks with meetings
tasklinks = TaskLinks.objects.filter(
    is_active=True,
    meeting_id__isnull=False
).exclude(meeting_id='')
print(f"TaskLinks with meetings: {tasklinks.count()}")

# 4. Check DAF gate status for a task
task = Task.objects.filter(is_active=True, mxpoint__gt=0).first()
if task:
    service = TaskQualityGateService()
    gate_status = service.get_task_gate_status(task)
    print(f"Task {task.id}: {gate_status['meetings_completed_count']}/{gate_status['required_meeting_count']} meetings")
    print(f"Meeting OK: {gate_status['meeting_ok']}")
```

---

## G) Missing Components

### DAF Gate Refresh Command

**Status:** Not found in repo

**Recommendation:** No dedicated command needed - gate status is computed on-demand by `TaskQualityGateService.get_task_gate_status()`. Reconciliation updates TaskLinks, which are then counted automatically.

**If refresh is needed:** Create a management command that:
- Iterates through active tasks
- Calls `TaskQualityGateService.get_task_gate_status()` for each
- Optionally caches results or updates task metadata

**Suggested Location:** `coda/management/management/commands/refresh_daf_gate_status.py`

---

## H) Command Comparison

### Meeting Sync Commands

| Command | Service | Default Service | Use Case |
|---------|---------|-----------------|----------|
| `sync_gotomeetings` | `meeting_sync_service` | `gotomeeting_internal` | **Canonical** - Most referenced in docs |
| `sync_goto_meetings` | `goto_meeting_sync_service` | `gotomeeting_external` | Legacy/alternative |
| `sync_goto_meetings_if_stale` | `goto_meeting_sync_service` | `gotomeeting_external` | Scheduled execution with freshness checks |

**Recommendation:** Use `sync_gotomeetings` for manual syncs (supports both services, most flexible).

---

## I) Troubleshooting

### No OAuth Token

**Error:** `⚠️ No OAuth access token available for gotomeeting_internal. Skipping...`

**Fix:** Authenticate via UI:
```
Visit: /management/oauth/login/?service=internal
```

### Attendees Not Persisting

**Check:** Instance key matching logs (with `--verbose` flag)

**Fix:** Ensure `meeting_instance_key` is set on Meeting model before attendee sync.

### No Task Matches

**Check:** Reconciliation diagnostic logs (first 10 meetings logged)

**Common Reasons:**
- No employee match (no attendees/organizer)
- No eligible tasks in window
- Requirement/topic mismatch

---

## J) Expected Output Summary

### Meeting Sync
- `N meetings fetched, X created, Y updated`

### Attendee Sync
- `N meetings processed, X succeeded, Y failed, Z attendees created`

### Reconciliation
- `Meetings processed: N`
- `Meetings linked: X`
- `TaskLinks created: Y`
- `TaskLinks updated: Z`

### DAF Gate (on-demand)
- `meetings_completed_count: N`
- `required_meeting_count: M`
- `meeting_ok: True/False`

---

**End of Runbook**

