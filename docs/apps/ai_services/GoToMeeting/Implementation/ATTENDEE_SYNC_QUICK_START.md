# Attendee Sync Quick Start Guide

**Branch:** 25.12_CODA_DEV_CM  
**Date:** 2024-12-30

---

## Quick Start

### 1. Diagnose Current State

```bash
poetry run python coda/manage.py diagnose_attendee_sync --service all --days 30
```

This will show:
- How many meetings have stale/no attendees
- Sample meetings with issues
- Root cause analysis
- Verification SQL queries

### 2. Run Attendee Sync

```bash
# Sync internal service (last 120 days)
poetry run python coda/manage.py sync_meeting_attendees --service internal --days 120 --verbose

# Sync external service
poetry run python coda/manage.py sync_meeting_attendees --service external --days 120 --verbose

# Sync both services
poetry run python coda/manage.py sync_meeting_attendees --service all --days 120 --verbose
```

### 3. Verify Results

```sql
-- Check attendee counts increased
SELECT 
    m.service_name,
    COUNT(DISTINCT m.id) as meeting_count,
    COUNT(ma.id) as attendee_count,
    MAX(ma.updated_at) as latest_update
FROM ai_services_meeting m
LEFT JOIN ai_services_meetingattendee ma ON m.id = ma.meeting_id
WHERE m.start_time >= NOW() - INTERVAL '120 days'
GROUP BY m.service_name;

-- Check timestamps are recent (not stuck at January)
SELECT 
    m.service_name,
    MAX(ma.updated_at) as latest_attendee_update,
    COUNT(DISTINCT m.id) as meetings_with_recent_attendees
FROM ai_services_meeting m
JOIN ai_services_meetingattendee ma ON m.id = ma.meeting_id
WHERE m.start_time >= NOW() - INTERVAL '120 days'
  AND ma.updated_at >= NOW() - INTERVAL '1 day'
GROUP BY m.service_name;
```

---

## What Was Fixed

1. **Removed incorrect filter** in `getmeetingresponse()` that was filtering out all attendees
2. **Created dedicated attendee sync service** with DB-first selection
3. **Added combined name splitting** ("EUNICE, JUDY AND NOREEN" → 3 attendees)
4. **Implemented idempotent upsert** (delete & recreate for freshness)

---

## Files Changed

- ✅ `coda/ai_services/views.py` - Fixed attendee fetching bug
- ✅ `coda/ai_services/services/attendee_sync_service.py` - New service
- ✅ `coda/ai_services/management/commands/sync_meeting_attendees.py` - New command
- ✅ `coda/ai_services/management/commands/diagnose_attendee_sync.py` - New diagnostic command
- ✅ `coda/ai_services/tests/test_attendee_sync.py` - Tests

---

## Expected Results

After running sync:
- ✅ Attendee counts increase
- ✅ Attendee `updated_at` timestamps are recent (today/Dec 30)
- ✅ Meetings that show attendees in GoTo UI have corresponding DB rows
- ✅ No duplicate attendees for same meeting
- ✅ Combined names are split into individual attendees

---

## Troubleshooting

**If attendees still not syncing:**
1. Check OAuth token: `poetry run python coda/manage.py check_goto_tokens`
2. Check API endpoint: Verify `https://api.getgo.com/G2M/rest/meetings/{meeting_id}/attendees` works
3. Check logs: Look for "Failed to fetch attendees" warnings
4. Run diagnostic: `poetry run python coda/manage.py diagnose_attendee_sync --service all`

**If wrong identifier:**
- The API might require `session_id` instead of `meeting_id`
- Check GoToMeeting API docs for correct endpoint format
- May need to add `session_id` field to Meeting model

