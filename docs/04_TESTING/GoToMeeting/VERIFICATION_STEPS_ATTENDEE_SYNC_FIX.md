# Verification Steps: Attendee Sync Fix

## Overview
This document provides verification steps to confirm that the attendee sync fix is working correctly.

## Changes Made
1. **Meeting Model**: Added `session_id` and `meeting_instance_key` fields back
2. **Meeting Sync**: Persists `sessionId` from `historicalMeetings` API into `Meeting.session_id`
3. **Attendee Sync**: Filters attendees by instance key before persisting
4. **Email Normalization**: Treats "NA", "N/A", "", None, "-", "NONE" as missing
5. **Debug Logging**: Added INFO-level logging for sync operations
6. **Diagnostic Command**: Fixed bug with list responses

## Verification Steps

### Step 1: Delete Test Data (Optional - for clean test)
```bash
# Delete meetings and attendees for Jan 1-2, 2026 for gotomeeting_internal
poetry run python coda/manage.py shell -c "
from django.utils import timezone
from datetime import datetime
from ai_services.models import Meeting, MeetingAttendee

start = timezone.make_aware(datetime(2026, 1, 1))
end = timezone.make_aware(datetime(2026, 1, 3))

meetings = Meeting.objects.filter(
    start_time__gte=start,
    start_time__lt=end,
    service_name='gotomeeting_internal'
)

attendee_count = MeetingAttendee.objects.filter(meeting__in=meetings).count()
print(f'Deleting {meetings.count()} meetings and {attendee_count} attendees')

MeetingAttendee.objects.filter(meeting__in=meetings).delete()
meetings.delete()

print('✅ Deleted')
"
```

### Step 2: Run Meeting Sync
```bash
# Sync meetings for Jan 1-2, 2026 for gotomeeting_internal
poetry run python coda/manage.py shell -c "
from django.utils import timezone
from datetime import datetime, timedelta
from ai_services.services.goto_meeting_sync_service import sync

start = timezone.make_aware(datetime(2026, 1, 1))
end = timezone.make_aware(datetime(2026, 1, 3))

result = sync(start, end, service_name='gotomeeting_internal')
print(f'Result: {result}')
"
```

### Step 3: Check Meeting Counts
```bash
# Check meeting counts and instance key population
poetry run python coda/manage.py shell -c "
from django.utils import timezone
from datetime import datetime
from ai_services.models import Meeting
from django.db.models import Count

start = timezone.make_aware(datetime(2026, 1, 1))
end = timezone.make_aware(datetime(2026, 1, 3))

meetings = Meeting.objects.filter(
    start_time__gte=start,
    start_time__lt=end,
    service_name='gotomeeting_internal'
).annotate(ac=Count('attendees'))

print(f'Total meetings: {meetings.count()}')
print(f'Meetings with session_id: {meetings.exclude(session_id__isnull=True).exclude(session_id="").count()}')
print(f'Meetings with meeting_instance_key: {meetings.exclude(meeting_instance_key__isnull=True).exclude(meeting_instance_key="").count()}')
print(f'Meetings with 0 attendees: {meetings.filter(ac=0).count()}')
print(f'Meetings with >0 attendees: {meetings.filter(ac__gt=0).count()}')
"
```

### Step 4: Run Attendee Sync
```bash
# Sync attendees for meetings in Jan 1-2, 2026
poetry run python coda/manage.py shell -c "
from django.utils import timezone
from datetime import datetime
from ai_services.models import Meeting
from ai_services.services.attendee_sync_service import sync_attendees_for_meetings

start = timezone.make_aware(datetime(2026, 1, 1))
end = timezone.make_aware(datetime(2026, 1, 3))

meetings = Meeting.objects.filter(
    start_time__gte=start,
    start_time__lt=end,
    service_name='gotomeeting_internal',
    provider_not_found=False
)

result = sync_attendees_for_meetings(list(meetings), 'gotomeeting_internal')
print(f'Result: {result}')
"
```

### Step 5: Verify Specific Meetings
```bash
# Check meetings 623828061 and 369139597
poetry run python coda/manage.py diagnose_gotomeeting_attendees --meeting-id 623828061 --check-meeting-list
poetry run python coda/manage.py diagnose_gotomeeting_attendees --meeting-id 369139597 --check-meeting-list
```

### Step 6: Confirm DB Attendee Counts
```bash
# Verify attendee counts in DB
poetry run python coda/manage.py shell -c "
from ai_services.models import Meeting
from django.db.models import Count

meetings = Meeting.objects.filter(
    meeting_id__in=['623828061', '369139597']
).annotate(ac=Count('attendees'))

for m in meetings:
    print(f'Meeting {m.meeting_id}: {m.ac} attendees, session_id={m.session_id}, instance_key={m.meeting_instance_key}')
"
```

## Expected Results

### After Step 2 (Meeting Sync):
- Meetings should have `session_id` populated from `historicalMeetings` API
- Logs should show: `📋 Meeting sync: meeting_id=..., session_id=...`

### After Step 4 (Attendee Sync):
- Meetings 623828061 and 369139597 should have attendees > 0
- Logs should show:
  - `📋 Attendee sync start: meeting_id=..., meeting_instance_key=...`
  - `API attendee_count: X`
  - `Filtered attendee_count: Y`
  - `✅ Attendee sync complete: created=X, updated=Y`

### After Step 6:
- Meeting 623828061: Should have 3+ attendees
- Meeting 369139597: Should have 71+ attendees
- Both meetings should have `meeting_instance_key` populated

## Troubleshooting

### If meetings still have 0 attendees:
1. Check logs for instance key extraction: `grep "meetingInstanceKey" logs/`
2. Check if meeting has instance key: `Meeting.objects.get(meeting_id='623828061').meeting_instance_key`
3. Run diagnostic command to see API response: `diagnose_gotomeeting_attendees --meeting-id 623828061`

### If instance key is not stored:
1. Check if meeting is recurring: `Meeting.objects.get(meeting_id='...').meeting_type`
2. Check if attendees have meetingInstanceKey in API response
3. Check logs for "Ambiguous instance key" warnings

