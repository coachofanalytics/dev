# AI-3 Hardening + OAuth Telemetry Runbook

**Branch:** 25.12_CODA_DEV_CM  
**Date:** 2024-12-30

## Quick Commands

### A) Backfill session IDs for external meetings

```bash
# Backfill session_id for external meetings (last 260 days)
poetry run python coda/manage.py backfill_meeting_instance_keys \
  --service external \
  --days 260 \
  --verbose

# Verify backfill worked
poetry run python coda/manage.py shell
>>> from ai_services.models import Meeting
>>> external = Meeting.objects.filter(service_name="gotomeeting_external")
>>> print(f"Total external: {external.count()}")
>>> print(f"With session_id: {external.exclude(session_id__isnull=True).exclude(session_id='').count()}")
```

### B) Run attendee sync for external

```bash
# Sync attendees for external meetings (uses session_id for better matching)
poetry run python coda/manage.py sync_meeting_attendees \
  --service external \
  --days 260 \
  --verbose
```

### C) Run AI-3 suggestions with fallback enabled

```bash
# Generate suggestions for Task 230 with fallback (default: enabled)
poetry run python coda/manage.py generate_task_meeting_suggestions \
  --task-id 230 \
  --days 260 \
  --service internal \
  --fallback-services \
  --verbose

# Or disable fallback explicitly
poetry run python coda/manage.py generate_task_meeting_suggestions \
  --task-id 230 \
  --days 260 \
  --service internal \
  --no-fallback-services \
  --verbose
```

## Verification Steps

### 1. Verify session_id persistence

```bash
# Check external meetings have session_id
poetry run python coda/manage.py shell
>>> from ai_services.models import Meeting
>>> external = Meeting.objects.filter(service_name="gotomeeting_external")
>>> missing = external.filter(session_id__isnull=True) | external.filter(session_id='')
>>> print(f"External meetings missing session_id: {missing.count()}")
>>> # Should be 0 after backfill
```

### 2. Verify OAuth telemetry

```bash
# Check telemetry fields
poetry run python coda/manage.py shell
>>> from ai_services.models import OAuthToken
>>> token = OAuthToken.objects.get(service_name='gotomeeting_external')
>>> print(f"Last refresh attempt: {token.last_refresh_attempt_at}")
>>> print(f"Last refresh status: {token.last_refresh_status}")
>>> print(f"Last refresh error: {token.last_refresh_error}")
```

### 3. Verify dashboard telemetry display

1. Navigate to `/dashboard/` as staff user
2. Scroll to "GoToMeeting Ops Console" panel
3. Verify both internal and external services show:
   - Last Refresh Attempt timestamp
   - Last Refresh Status (SUCCESS/FAILED badge)
   - Last Refresh Error (if failed, sanitized)
4. Click "Attempt Refresh Now" for external service
5. Verify telemetry updates immediately after refresh

### 4. Verify AI-3 fallback

```bash
# Run with verbose to see fallback messages
poetry run python coda/manage.py generate_task_meeting_suggestions \
  --task-id 230 \
  --days 260 \
  --service internal \
  --fallback-services \
  --verbose 2>&1 | grep -i "fallback\|candidates"
```

Expected output should show:
- "No candidates above threshold from internal, trying fallback gotomeeting_external"
- "Found X candidates from fallback gotomeeting_external"

## Troubleshooting

### External meetings still missing session_id

1. Check if API returns sessionId:
   ```bash
   # Test API directly (requires valid token)
   curl -H "Authorization: Bearer $TOKEN" \
     "https://api.getgo.com/G2M/rest/historicalMeetings?startDate=2024-01-01T00:00:00Z&endDate=2024-12-30T23:59:59Z" \
     | jq '.[0].sessionId'
   ```

2. Re-run backfill with --force if ambiguous matches:
   ```bash
   poetry run python coda/manage.py backfill_meeting_instance_keys \
     --service external \
     --days 260 \
     --force \
     --verbose
   ```

### OAuth telemetry not updating

1. Check token refresh is being called:
   ```bash
   # Check logs for refresh attempts
   tail -f logs/django.log | grep "refreshing token"
   ```

2. Verify OAuthToken model has telemetry fields:
   ```bash
   poetry run python coda/manage.py shell
   >>> from ai_services.models import OAuthToken
   >>> token = OAuthToken.objects.first()
   >>> hasattr(token, 'last_refresh_attempt_at')
   True
   ```

### AI-3 fallback not working

1. Check fallback flag is enabled (default: True):
   ```bash
   poetry run python coda/manage.py generate_task_meeting_suggestions --help | grep fallback
   ```

2. Verify both services have meetings:
   ```bash
   poetry run python coda/manage.py shell
   >>> from ai_services.models import Meeting
   >>> from django.utils import timezone
   >>> from datetime import timedelta
   >>> start = timezone.now() - timedelta(days=260)
   >>> Meeting.objects.filter(service_name='gotomeeting_external', start_time__gte=start).count()
   >>> Meeting.objects.filter(service_name='gotomeeting_internal', start_time__gte=start).count()
   ```

