# Attendee Sync End-to-End Runbook

**Branch:** 25.12_CODA_DEV_CM  
**Date:** 2024-12-30  
**Purpose:** Complete validation and hardening of attendee sync pipeline

---

## Pre-Flight Checks

### 1. Diagnose Current State

```bash
# Check attendee sync status (all services, 30 days)
poetry run python coda/manage.py diagnose_attendee_sync --service all --days 30
```

**Expected Output:**
- Meetings count by service
- Attendees count by service
- Latest attendee update timestamps (should be recent, not January)
- Top 10 meetings by attendee count
- Sample attendee names

**Key Metrics to Check:**
- ✅ Attendee `updated_at` timestamps are recent (today/Dec 30)
- ✅ Attendee counts > 0 for meetings that show attendees in GoTo UI
- ⚠️  If timestamps are stale (>7 days), attendees need sync

### 2. Diagnose Employee Cohorts

```bash
# Check why Group B might return 0 users
poetry run python coda/manage.py diagnose_employee_cohorts --group B
```

**Expected Output:**
- EmployeeCareerState counts by group
- Base employee queryset count
- Employees with/without career_state
- Sample employees in Group B

**If Group B = 0:**
- Check if EmployeeCareerState records exist
- Use `--department-id` instead of `--group`
- Seed EmployeeCareerState records via admin

---

## Attendee Sync Execution

### 3. Sync Internal Service Attendees

```bash
# Sync internal service (last 120 days, verbose)
poetry run python coda/manage.py sync_meeting_attendees \
  --service internal \
  --days 120 \
  --verbose
```

**Expected Output:**
```
🔄 Syncing Meeting Attendees (DB-First Selection)
Service: internal
Days: 120
Max age (stale threshold): 24 hours
Split combined names: True

📡 Syncing gotomeeting_internal...

Found 34 meetings needing attendee sync
  - Meeting 123530685: Internal Training Session (attendees: 0, last updated: never)
  - Meeting 616024597: Daily Update (attendees: 2, last updated: 2025-01-15 10:00)
  ... and 32 more

✅ Synced gotomeeting_internal: 34/34 meetings, 45 attendees created, 12 updated

📊 Summary: 34 meetings processed, 34 succeeded, 0 failed, 45 attendees created, 12 updated
```

### 4. Sync External Service Attendees

```bash
# Sync external service (last 120 days, verbose)
poetry run python coda/manage.py sync_meeting_attendees \
  --service external \
  --days 120 \
  --verbose
```

**Expected Output:** Similar to internal, but for external service

### 5. Sync Both Services

```bash
# Sync both services at once
poetry run python coda/manage.py sync_meeting_attendees \
  --service all \
  --days 120 \
  --verbose
```

---

## Post-Sync Verification

### 6. Re-run Diagnostic

```bash
# Verify attendees were updated (shows distribution and instance key status)
poetry run python coda/manage.py diagnose_attendee_sync --service all --days 30
```

**Check:**
- ✅ Latest attendee update timestamps are NOW (today)
- ✅ Attendee counts increased
- ✅ Top meetings show sample attendee names
- ✅ Attendee count distribution shows improvement (fewer 0/1 attendee meetings)
- ✅ Most meetings have `provider_meeting_instance_key` populated

### 7. Backfill Instance Keys (if needed)

```bash
# Backfill instance keys for existing meetings (safe, skips ambiguous)
poetry run python coda/manage.py backfill_meeting_instance_keys \
  --service all \
  --days 120 \
  --verbose

# Force backfill even when ambiguous (use with caution)
poetry run python coda/manage.py backfill_meeting_instance_keys \
  --service all \
  --days 120 \
  --force \
  --verbose
```

**Expected Output:**
- Shows meetings needing backfill
- Matches API meetings to DB meetings by (start_time ± tolerance, topic)
- Uses deterministic instance key selection
- Skips ambiguous matches (unless --force)
- Updates `sessionId` and `provider_meeting_instance_key`

### 8. SQL Verification Queries

Run these in your database to verify:

```sql
-- 1. Count attendees by service (last 120 days)
SELECT 
    m.service_name,
    COUNT(DISTINCT m.id) as meeting_count,
    COUNT(ma.id) as attendee_count,
    MAX(ma.updated_at) as latest_attendee_update
FROM ai_services_meeting m
LEFT JOIN ai_services_meetingattendee ma ON m.id = ma.meeting_id
WHERE m.start_time >= NOW() - INTERVAL '120 days'
GROUP BY m.service_name
ORDER BY m.service_name;

-- 2. Latest attendee update timestamps by service
SELECT 
    m.service_name,
    MAX(ma.updated_at) as latest_attendee_update,
    COUNT(DISTINCT m.id) as meetings_with_recent_attendees
FROM ai_services_meeting m
JOIN ai_services_meetingattendee ma ON m.id = ma.meeting_id
WHERE m.start_time >= NOW() - INTERVAL '120 days'
  AND ma.updated_at >= NOW() - INTERVAL '1 day'
GROUP BY m.service_name;

-- 3. Top 10 meetings by attendee count
SELECT 
    m.meeting_id,
    m.topic,
    m.service_name,
    m.start_time,
    COUNT(ma.id) as attendee_count_db,
    MAX(ma.updated_at) as last_attendee_update
FROM ai_services_meeting m
LEFT JOIN ai_services_meetingattendee ma ON m.id = ma.meeting_id
WHERE m.start_time >= NOW() - INTERVAL '120 days'
GROUP BY m.id, m.meeting_id, m.topic, m.service_name, m.start_time
ORDER BY attendee_count_db DESC
LIMIT 10;

-- 4. Sample attendee names for top meeting
SELECT 
    ma.attendee_name,
    ma.attendee_email,
    ma.duration_minutes,
    ma.updated_at
FROM ai_services_meetingattendee ma
JOIN ai_services_meeting m ON ma.meeting_id = m.id
WHERE m.meeting_id = '<top_meeting_id_from_query_3>'
ORDER BY ma.duration_minutes DESC
LIMIT 10;
```

---

## Pattern Analysis with Real Cohort

### 8. Run Pattern Analysis for Group B

```bash
# If Group B has employees
poetry run python coda/manage.py analyze_meeting_task_patterns \
  --group B \
  --days 120 \
  --service internal \
  --out group_b_patterns.csv \
  --verbose
```

**If Group B = 0, use department instead:**

```bash
# Find a department ID first
poetry run python coda/manage.py diagnose_employee_cohorts

# Then use department-id
poetry run python coda/manage.py analyze_meeting_task_patterns \
  --department-id <DEPARTMENT_ID> \
  --days 120 \
  --service internal \
  --out dept_patterns.csv \
  --verbose
```

**Or use single user:**

```bash
# Use specific user ID
poetry run python coda/manage.py analyze_meeting_task_patterns \
  --user-id 495 \
  --days 120 \
  --service internal \
  --out eunice_patterns.csv \
  --verbose
```

---

## Service Scoping Verification

### Safety Check: Verify No Cross-Service Collision

```sql
-- Check if any meetings share meeting_id across services
SELECT 
    meeting_id,
    COUNT(DISTINCT service_name) as service_count,
    STRING_AGG(DISTINCT service_name, ', ') as services
FROM ai_services_meeting
WHERE start_time >= NOW() - INTERVAL '120 days'
GROUP BY meeting_id
HAVING COUNT(DISTINCT service_name) > 1;

-- If this returns rows, there's a collision risk
-- Expected: 0 rows (meeting_id should be unique per service)
```

**Result:** If 0 rows, service scoping is safe (MeetingAttendee is scoped via Meeting FK, which has service_name).

---

## Acceptance Criteria

✅ **After running sync:**
- Attendee `updated_at` timestamps are recent (today, not January)
- Attendee counts increased for meetings that show attendees in GoTo UI
- No duplicate attendees for same meeting
- Combined names are split (e.g., "EUNICE, JUDY AND NOREEN" → 3 attendees)
- Works for both internal and external services

✅ **Cohort selection:**
- Group B returns > 0 users (or actionable error message)
- Department-id works as fallback
- Diagnostic shows why cohort is empty

✅ **Service scoping:**
- No cross-service collision (verified via SQL)
- Attendees are scoped correctly via Meeting.service_name

---

## Troubleshooting

### Issue: Group B returns 0 users

**Diagnosis:**
```bash
poetry run python coda/manage.py diagnose_employee_cohorts --group B
```

**Solutions:**
1. Check EmployeeCareerState: `SELECT COUNT(*) FROM management_employeecareerstate WHERE group = 'B';`
2. Use `--department-id` instead
3. Seed EmployeeCareerState records via admin UI

### Issue: Attendees still stale after sync

**Check:**
1. OAuth token valid: `poetry run python coda/manage.py check_goto_tokens`
2. API endpoint works: Check logs for "Failed to fetch attendees"
3. Meeting IDs correct: Verify meeting_id format matches API expectations

### Issue: Service collision detected

**If SQL query shows meetings with same meeting_id across services:**
- This should not happen (meeting_id should be globally unique)
- If it does, add service_name to MeetingAttendee model (requires migration)
- For now, scoping via Meeting FK is safe

---

## Files Modified

1. **`coda/ai_services/management/commands/diagnose_attendee_sync.py`**
   - Added DB verification statistics (meetings/attendees counts, latest updates, top meetings)
   - Uses `attendee_count_db` annotation (not `attendee_count`)

2. **`coda/ai_services/services/attendee_sync_service.py`**
   - Added service scoping safety comment
   - Confirmed scoping is safe (MeetingAttendee scoped via Meeting FK)

3. **`coda/ai_services/management/commands/analyze_meeting_task_patterns.py`**
   - Enhanced cohort selection with debug output
   - Shows EmployeeCareerState counts
   - Provides actionable error messages when cohort is empty
   - Falls back gracefully

4. **`coda/ai_services/management/commands/diagnose_employee_cohorts.py`** (NEW)
   - Diagnostic command for employee cohort selection
   - Shows counts by group, department, base queryset
   - Provides SQL queries for verification

---

## Quick Reference Commands

```bash
# 1. Diagnose attendees
poetry run python coda/manage.py diagnose_attendee_sync --service all --days 30

# 2. Diagnose cohorts
poetry run python coda/manage.py diagnose_employee_cohorts --group B

# 3. Sync internal attendees
poetry run python coda/manage.py sync_meeting_attendees --service internal --days 120 --verbose

# 4. Sync external attendees
poetry run python coda/manage.py sync_meeting_attendees --service external --days 120 --verbose

# 5. Pattern analysis (Group B)
poetry run python coda/manage.py analyze_meeting_task_patterns --group B --days 120 --service internal --out group_b_patterns.csv --verbose

# 6. Pattern analysis (Department fallback)
poetry run python coda/manage.py analyze_meeting_task_patterns --department-id <ID> --days 120 --service internal --out dept_patterns.csv --verbose
```

---

## Success Indicators

✅ **Attendee sync successful if:**
- Latest attendee update is today (not January)
- Attendee counts match GoTo UI
- No duplicate attendees
- Combined names split correctly

✅ **Cohort selection working if:**
- Group B returns > 0 users OR clear error message
- Department-id works as fallback
- Diagnostic shows actionable guidance

✅ **Service scoping safe if:**
- SQL query shows 0 meetings with same meeting_id across services
- Attendees correctly linked to meetings with matching service_name

