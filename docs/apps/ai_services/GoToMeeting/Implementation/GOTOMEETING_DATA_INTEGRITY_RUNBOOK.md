# GoToMeeting Data Integrity Fix - Runbook

**Branch:** 25.12_CODA_DEV_CM  
**Date:** 2024-12-30

## Overview

This runbook documents the fixes for GoToMeeting identifier and persistence problems:
1. **Schema changes**: Fixed uniqueness constraints to allow same meeting_id across services and sessions
2. **Upsert logic**: Updated to use composite key (service_name, meeting_id, session_id)
3. **Provider not found tracking**: Added 404 tracking to exclude failed meetings from sync
4. **Backfill**: Enhanced to populate session_id and provider_meeting_instance_key

---

## Step 1: Run Migration

**⚠️ IMPORTANT**: This migration will:
- Drop the unique constraint on `meeting_id`
- Handle duplicate meetings (keep newest or keep record with session_id/provider_meeting_instance_key)
- Add new unique constraints based on (service_name, meeting_id, session_id)

```bash
# Run migration
poetry run python coda/manage.py migrate ai_services

# Verify migration succeeded
poetry run python coda/manage.py showmigrations ai_services | grep 0007
```

**Expected output**: Migration `0007_fix_meeting_uniqueness_constraints` should show as applied.

---

## Step 2: Backfill session_id for Existing Meetings

Backfill `session_id` from historicalMeetings API for meetings that are missing it.

### For External Service

```bash
poetry run python coda/manage.py backfill_meeting_instance_keys \
  --service external \
  --days 260 \
  --limit 100 \
  --verbose
```

### For Internal Service

```bash
poetry run python coda/manage.py backfill_meeting_instance_keys \
  --service internal \
  --days 260 \
  --limit 100 \
  --verbose
```

### For Both Services

```bash
poetry run python coda/manage.py backfill_meeting_instance_keys \
  --service all \
  --days 260 \
  --limit 100 \
  --verbose
```

**Options**:
- `--days`: Number of days to look back (default: 120)
- `--limit`: Maximum meetings to process per service (default: 50)
- `--tolerance-minutes`: Time tolerance for matching (default: 5 minutes)
- `--force`: Force selection even when ambiguous (use with caution)
- `--verbose`: Show detailed output

---

## Step 3: Sync Attendees

After backfilling session_id, sync attendees for both services.

### External Service

```bash
poetry run python coda/manage.py sync_meeting_attendees \
  --service external \
  --days 260 \
  --verbose
```

### Internal Service

```bash
poetry run python coda/manage.py sync_meeting_attendees \
  --service internal \
  --days 260 \
  --verbose
```

**Note**: Meetings marked as `provider_not_found=True` will be automatically skipped unless forced.

---

## Step 4: Verify Data Integrity

### Check session_id Coverage

```bash
poetry run python coda/manage.py shell
```

```python
from ai_services.models import Meeting
from django.utils import timezone
from datetime import timedelta

# Check external meetings
external = Meeting.objects.filter(service_name="gotomeeting_external")
total_external = external.count()
with_session_id = external.exclude(session_id__isnull=True).exclude(session_id='').count()
print(f"External: {with_session_id}/{total_external} have session_id ({with_session_id/total_external*100:.1f}%)")

# Check internal meetings
internal = Meeting.objects.filter(service_name="gotomeeting_internal")
total_internal = internal.count()
with_session_id = internal.exclude(session_id__isnull=True).exclude(session_id='').count()
print(f"Internal: {with_session_id}/{total_internal} have session_id ({with_session_id/total_internal*100:.1f}%)")
```

### Check provider_not_found Counts

```python
# Count provider_not_found by service
from django.db.models import Count

provider_not_found = Meeting.objects.filter(provider_not_found=True).values('service_name').annotate(
    count=Count('id')
)
for item in provider_not_found:
    print(f"{item['service_name']}: {item['count']} meetings marked as provider_not_found")

# Top recent 404 meetingIds
recent_404 = Meeting.objects.filter(
    provider_not_found=True
).order_by('-provider_not_found_at')[:10]

for m in recent_404:
    print(f"{m.meeting_id} (service={m.service_name}, marked_at={m.provider_not_found_at})")
```

### Check Attendee Coverage

```python
# Attendee coverage by service
from django.db.models import Count, Q
from datetime import timedelta

start_date = timezone.now() - timedelta(days=260)

for service_name in ['gotomeeting_internal', 'gotomeeting_external']:
    meetings = Meeting.objects.filter(
        service_name=service_name,
        start_time__gte=start_date
    )
    total = meetings.count()
    with_attendees = meetings.filter(attendees__isnull=False).distinct().count()
    coverage = (with_attendees / total * 100) if total > 0 else 0
    print(f"{service_name}: {with_attendees}/{total} meetings have attendees ({coverage:.1f}%)")
```

### Run Diagnostic Command

```bash
poetry run python coda/manage.py diagnose_attendee_sync \
  --service all \
  --days 260
```

This will show:
- Meeting and attendee counts by service
- Session_id and provider_meeting_instance_key coverage
- Provider not found (404) statistics
- Top recent 404 meetingIds
- Verification SQL queries

---

## Step 5: Verify Uniqueness Constraints

### Test: Same meeting_id Across Services

```python
# This should now work (previously would fail due to unique constraint)
from ai_services.models import Meeting
from django.utils import timezone

meeting1 = Meeting.objects.create(
    meeting_id='123456789',
    service_name='gotomeeting_internal',
    session_id='111111111',
    topic='Internal Meeting',
    start_time=timezone.now(),
    end_time=timezone.now(),
)

meeting2 = Meeting.objects.create(
    meeting_id='123456789',  # Same meeting_id
    service_name='gotomeeting_external',  # Different service
    session_id='222222222',
    topic='External Meeting',
    start_time=timezone.now(),
    end_time=timezone.now(),
)

# Both should exist
assert Meeting.objects.filter(meeting_id='123456789').count() == 2
print("✅ Same meeting_id can exist across services")
```

### Test: Same meeting_id, Different Sessions

```python
# Same meeting_id, same service, different session_id
meeting3 = Meeting.objects.create(
    meeting_id='123456789',
    service_name='gotomeeting_internal',
    session_id='333333333',  # Different session
    topic='Internal Meeting Session 2',
    start_time=timezone.now() + timedelta(days=1),
    end_time=timezone.now() + timedelta(days=1),
)

# Should have 3 meetings with same meeting_id
assert Meeting.objects.filter(meeting_id='123456789').count() == 3
print("✅ Same meeting_id can exist across sessions")
```

---

## End-to-End Smoke Test

Run this complete sequence to verify everything works:

```bash
# 1. Run migration
poetry run python coda/manage.py migrate ai_services

# 2. Run tests
poetry run python coda/manage.py test ai_services.tests.test_meeting_uniqueness_fix -v 2
poetry run python coda/manage.py test ai_services.tests.test_session_id_persistence -v 2

# 3. Backfill session_id (external)
poetry run python coda/manage.py backfill_meeting_instance_keys \
  --service external \
  --days 30 \
  --limit 10 \
  --verbose

# 4. Sync attendees (external)
poetry run python coda/manage.py sync_meeting_attendees \
  --service external \
  --days 30 \
  --verbose

# 5. Diagnose
poetry run python coda/manage.py diagnose_attendee_sync \
  --service external \
  --days 30

# 6. Verify in shell
poetry run python coda/manage.py shell <<EOF
from ai_services.models import Meeting
from django.db.models import Count

# Check session_id coverage
external = Meeting.objects.filter(service_name="gotomeeting_external")
total = external.count()
with_session = external.exclude(session_id__isnull=True).exclude(session_id='').count()
print(f"External session_id coverage: {with_session}/{total} ({with_session/total*100:.1f}%)")

# Check provider_not_found
provider_not_found = Meeting.objects.filter(provider_not_found=True).count()
print(f"Provider not found: {provider_not_found} meetings")

# Check uniqueness (should have multiple meetings with same meeting_id)
duplicates = Meeting.objects.values('meeting_id').annotate(count=Count('id')).filter(count__gt=1)
print(f"Meetings with duplicate meeting_id: {duplicates.count()}")
EOF
```

**Expected Results**:
- ✅ Tests pass
- ✅ session_id coverage > 0% (or 100% if all meetings have session_id)
- ✅ provider_not_found count is reasonable (< 10% of meetings)
- ✅ Duplicate meeting_ids exist (proves uniqueness constraint is fixed)

---

## Troubleshooting

### Migration Fails Due to Duplicates

If migration fails with duplicate key errors:

1. Check for duplicates manually:
```python
from ai_services.models import Meeting
from django.db.models import Count

duplicates = Meeting.objects.values('meeting_id').annotate(
    count=Count('id')
).filter(count__gt=1)

for dup in duplicates:
    meetings = Meeting.objects.filter(meeting_id=dup['meeting_id'])
    print(f"Meeting ID {dup['meeting_id']}: {dup['count']} records")
    for m in meetings:
        print(f"  - ID={m.id}, service={m.service_name}, start_time={m.start_time}, updated_at={m.updated_at}")
```

2. Manually delete older duplicates:
```python
# Keep newest, delete older (same service + start_time)
from django.db.models import Max

for dup in duplicates:
    meetings = Meeting.objects.filter(meeting_id=dup['meeting_id']).order_by('-updated_at')
    if meetings.count() > 1:
        # Keep first (newest), delete rest
        to_keep = meetings.first()
        to_delete = meetings.exclude(id=to_keep.id)
        to_delete.delete()
        print(f"Deleted {to_delete.count()} duplicates for meeting_id {dup['meeting_id']}")
```

3. Re-run migration:
```bash
poetry run python coda/manage.py migrate ai_services
```

### Backfill Finds No Matches

If backfill finds no API matches:

1. Verify API returns sessionId:
```bash
# Test API directly (requires valid token)
curl -H "Authorization: Bearer $TOKEN" \
  "https://api.getgo.com/G2M/rest/historicalMeetings?startDate=2024-01-01T00:00:00Z&endDate=2024-12-30T23:59:59Z" \
  | jq '.[0] | {meetingId, sessionId, startTime}'
```

2. Check service_name matches:
```python
# Verify meetings have correct service_name
from ai_services.models import Meeting

for service in ['gotomeeting_internal', 'gotomeeting_external']:
    count = Meeting.objects.filter(service_name=service).count()
    print(f"{service}: {count} meetings")
```

3. Increase tolerance:
```bash
poetry run python coda/manage.py backfill_meeting_instance_keys \
  --service external \
  --days 260 \
  --tolerance-minutes 10 \
  --verbose
```

### External 404s Persist

If external meetings still get 404:

1. Check if meetings are marked as provider_not_found:
```python
from ai_services.models import Meeting

external_404 = Meeting.objects.filter(
    service_name='gotomeeting_external',
    provider_not_found=True
).count()
print(f"External meetings with 404: {external_404}")
```

2. Verify meeting_id format:
```python
# Check meeting_id format
external = Meeting.objects.filter(service_name='gotomeeting_external')[:10]
for m in external:
    print(f"{m.meeting_id} (format: {'9-digit' if len(m.meeting_id) == 9 else 'other'})")
```

3. Force retry (clears provider_not_found flag):
```python
# Clear provider_not_found flag to force retry
from django.utils import timezone

meetings = Meeting.objects.filter(
    service_name='gotomeeting_external',
    provider_not_found=True
)
meetings.update(provider_not_found=False, provider_not_found_at=None)
print(f"Cleared provider_not_found flag for {meetings.count()} meetings")
```

Then re-run attendee sync:
```bash
poetry run python coda/manage.py sync_meeting_attendees --service external --days 260
```

---

## Verification Queries

### SQL Queries for Manual Verification

```sql
-- Count meetings with session_id by service
SELECT 
    service_name,
    COUNT(*) as total,
    COUNT(session_id) as with_session_id,
    ROUND(COUNT(session_id) * 100.0 / COUNT(*), 1) as coverage_pct
FROM ai_services_meeting
WHERE start_time >= NOW() - INTERVAL '260 days'
GROUP BY service_name;

-- Provider not found counts
SELECT 
    service_name,
    COUNT(*) as provider_not_found_count
FROM ai_services_meeting
WHERE provider_not_found = TRUE
GROUP BY service_name;

-- Attendee coverage by service
SELECT 
    m.service_name,
    COUNT(DISTINCT m.id) as total_meetings,
    COUNT(DISTINCT CASE WHEN ma.id IS NOT NULL THEN m.id END) as meetings_with_attendees,
    COUNT(ma.id) as total_attendees,
    ROUND(COUNT(DISTINCT CASE WHEN ma.id IS NOT NULL THEN m.id END) * 100.0 / COUNT(DISTINCT m.id), 1) as coverage_pct
FROM ai_services_meeting m
LEFT JOIN ai_services_meetingattendee ma ON m.id = ma.meeting_id
WHERE m.start_time >= NOW() - INTERVAL '260 days'
GROUP BY m.service_name;

-- Top recent 404 meetingIds
SELECT 
    meeting_id,
    service_name,
    topic,
    provider_not_found_at
FROM ai_services_meeting
WHERE provider_not_found = TRUE
ORDER BY provider_not_found_at DESC
LIMIT 10;

-- Verify uniqueness constraints work (should show multiple rows with same meeting_id)
SELECT 
    meeting_id,
    service_name,
    session_id,
    COUNT(*) as count
FROM ai_services_meeting
GROUP BY meeting_id, service_name, session_id
HAVING COUNT(*) > 1;
```

---

## Summary

After completing all steps:

1. ✅ Migration applied: Unique constraints updated
2. ✅ session_id backfilled: Meetings have session_id from API
3. ✅ Attendees synced: Meetings have attendees (where available)
4. ✅ Provider not found tracked: 404 meetings marked and excluded
5. ✅ Data integrity verified: Same meeting_id can exist across services/sessions

**Expected Results**:
- External meetings: >90% have session_id
- Internal meetings: >90% have session_id
- Provider not found: <5% of meetings (or 0% if all meetings are valid)
- Attendee coverage: >70% of meetings have attendees

---

## Related Commands

- `backfill_meeting_instance_keys`: Backfill session_id and provider_meeting_instance_key
- `sync_meeting_attendees`: Sync attendees for meetings
- `diagnose_attendee_sync`: Diagnostic command with provider_not_found stats
- `generate_task_meeting_suggestions`: AI-3 suggestions (uses new schema)
