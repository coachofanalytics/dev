# Verification Steps: Attendee Sync Fix (V2 - Pipeline Fix)

## Overview
This document provides verification steps to confirm that the attendee sync pipeline fix is working correctly without manual intervention.

## Changes Made
1. **Meeting Sync**: Removed attendee fetching/persistence - now only persists meeting metadata and instance identifiers
2. **Instance Identifier Persistence**: Meeting sync now persists `sessionId` and `meetingInstanceKey` from API into DB
3. **Placeholder Email Generation**: Improved to include `meeting_instance_key` + `joinTime` to prevent "NA" email deduplication
4. **Attendee Sync**: Handles all attendee persistence with proper filtering and normalization

## Verification Steps

### Step 1: Delete Test Data (Jan 1-3, 2026 for gotomeeting_internal)
```bash
cd /Users/coda/Projects/uat/coda && poetry run python manage.py shell -c "
from django.utils import timezone
from datetime import datetime
from ai_services.models import Meeting, MeetingAttendee

start = timezone.make_aware(datetime(2026, 1, 1))
end = timezone.make_aware(datetime(2026, 1, 4))

meetings = Meeting.objects.filter(
    start_time__gte=start,
    start_time__lt=end,
    service_name='gotomeeting_internal'
)

attendee_count = MeetingAttendee.objects.filter(meeting__in=meetings).count()
print(f'Deleting {meetings.count()} meetings and {attendee_count} attendees')

MeetingAttendee.objects.filter(meeting__in=meetings).delete()
deleted_meetings = meetings.delete()
print(f'✅ Deleted {deleted_meetings[0]} meetings and {attendee_count} attendees')
"
```

### Step 2: Run Meeting Sync (2026-01-01 to 2026-01-02)
```bash
cd /Users/coda/Projects/uat/coda && poetry run python manage.py shell -c "
from django.utils import timezone
from datetime import datetime
from ai_services.services.goto_meeting_sync_service import sync

start = timezone.make_aware(datetime(2026, 1, 1))
end = timezone.make_aware(datetime(2026, 1, 3))

result = sync(start, end, service_name='gotomeeting_internal')
print(f'Meeting sync result: {result}')
"
```

### Step 3: Check Meeting Counts and Instance Identifiers
```bash
cd /Users/coda/Projects/uat/coda && poetry run python manage.py shell -c "
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

# Check specific meetings
for m in meetings.filter(meeting_id__in=['623828061', '369139597']):
    print(f'Meeting {m.meeting_id}: {m.ac} attendees, session_id={m.session_id}, instance_key={m.meeting_instance_key}')
"
```

### Step 4: Run Attendee Sync
```bash
cd /Users/coda/Projects/uat/coda && poetry run python manage.py shell -c "
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

print(f'Syncing attendees for {meetings.count()} meetings...')
result = sync_attendees_for_meetings(list(meetings), 'gotomeeting_internal')
print(f'Attendee sync result: {result}')
"
```

### Step 5: Verify Specific Meetings Have Attendees
```bash
cd /Users/coda/Projects/uat/coda && poetry run python manage.py shell -c "
from ai_services.models import Meeting
from django.db.models import Count

meetings = Meeting.objects.filter(
    meeting_id__in=['623828061', '369139597']
).annotate(ac=Count('attendees'))

print('=' * 80)
print('VERIFICATION: Meeting Attendee Counts')
print('=' * 80)
for m in meetings:
    print(f'Meeting {m.meeting_id}:')
    print(f'  Attendee count: {m.ac}')
    print(f'  session_id: {m.session_id or \"None\"}')
    print(f'  meeting_instance_key: {m.meeting_instance_key or \"None\"}')
    print(f'  meeting_type: {m.meeting_type or \"N/A\"}')
    print()

if all(m.ac > 0 for m in meetings):
    print('✅ SUCCESS: Both meetings have non-zero attendees')
else:
    print('❌ FAILURE: Some meetings still have 0 attendees')
    for m in meetings:
        if m.ac == 0:
            print(f'  - Meeting {m.meeting_id} has 0 attendees')
"
```

### Step 6: Verify Placeholder Email Uniqueness (for "NA" emails)
```bash
cd /Users/coda/Projects/uat/coda && poetry run python manage.py shell -c "
from ai_services.models import Meeting, MeetingAttendee

meetings = Meeting.objects.filter(meeting_id__in=['623828061', '369139597'])

print('=' * 80)
print('VERIFICATION: Placeholder Email Uniqueness')
print('=' * 80)
for m in meetings:
    attendees = MeetingAttendee.objects.filter(meeting=m)
    placeholder_emails = attendees.filter(attendee_email__startswith='no-email-')
    
    print(f'Meeting {m.meeting_id}:')
    print(f'  Total attendees: {attendees.count()}')
    print(f'  Placeholder emails: {placeholder_emails.count()}')
    
    # Check for duplicates
    email_counts = {}
    for att in placeholder_emails:
        email_counts[att.attendee_email] = email_counts.get(att.attendee_email, 0) + 1
    
    duplicates = {email: count for email, count in email_counts.items() if count > 1}
    if duplicates:
        print(f'  ⚠️  WARNING: Found {len(duplicates)} duplicate placeholder emails:')
        for email, count in list(duplicates.items())[:5]:
            print(f'    - {email}: {count} occurrences')
    else:
        print(f'  ✅ All placeholder emails are unique')
    print()
"
```

## Expected Results

### After Step 2 (Meeting Sync):
- Meetings should have `session_id` populated from `historicalMeetings` API
- Logs should show: `📋 Meeting sync: meeting_id=..., session_id=..., meeting_instance_key=...`
- **No attendees should be created** (attendee sync removed from meeting sync)

### After Step 4 (Attendee Sync):
- Meetings 623828061 and 369139597 should have attendees > 0
- Logs should show:
  - `📋 Attendee sync start: meeting_id=..., meeting_instance_key=...`
  - `API attendee_count: X`
  - `Filtered attendee_count: Y`
  - `✅ Attendee sync complete: created=X, updated=Y`

### After Step 5:
- Meeting 623828061: Should have 3+ attendees
- Meeting 369139597: Should have 71+ attendees
- Both meetings should have `meeting_instance_key` populated

### After Step 6:
- All placeholder emails should be unique (no duplicates)
- Each "NA" email attendee should have a unique placeholder email based on `meeting_id + instance_key + name + joinTime`

## Troubleshooting

### If meetings still have 0 attendees:
1. Check logs for instance key extraction: `grep "meetingInstanceKey\|session_id" logs/`
2. Check if meeting has instance key: `Meeting.objects.get(meeting_id='623828061').meeting_instance_key`
3. Run diagnostic command: `poetry run python manage.py diagnose_gotomeeting_attendees --meeting-id 623828061`

### If instance key is not stored:
1. Check if meeting is recurring: `Meeting.objects.get(meeting_id='...').meeting_type`
2. Check if attendees have meetingInstanceKey in API response
3. Check logs for "Ambiguous instance key" warnings

### If placeholder emails are duplicated:
1. Check if `meeting_instance_key` is populated
2. Check if `joinTime` is present in attendee data
3. Verify the hash includes all components: `meeting_id + instance_key + name + joinTime`

