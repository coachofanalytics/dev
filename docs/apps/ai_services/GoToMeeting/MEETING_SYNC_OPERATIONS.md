# Meeting Sync Operations Guide

## Overview

This document describes the CODA meeting sync system architecture, operations, and best practices for maintaining meeting data freshness.

**Phase 2C**: Professional meeting sync system with:
- DB-first approach (no API calls from DAF views)
- Scheduled execution support
- Multi-account support (internal/external GoToMeeting accounts)
- Freshness tracking and monitoring

## Architecture

### Components

1. **MeetingSyncRun Model** (`ai_services.models.MeetingSyncRun`)
   - Tracks each sync execution
   - Records service_name, timestamps, counts, status, errors
   - Enables freshness checks

2. **GoToMeeting Sync Service** (`ai_services.services.goto_meeting_sync_service`)
   - `sync(start_dt, end_dt, service_name)`: Orchestrates sync
   - `get_last_successful_sync(service_name)`: Gets most recent successful sync
   - `is_meeting_data_fresh(service_name, max_age_minutes)`: Checks if data is fresh

3. **OAuth Multi-Account Support** (`shared_core.utils.oauth`)
   - `get_access_token(service_name)`: Retrieves token for specific service
   - `exchange_code_for_tokens(auth_code, service_name)`: Exchanges code for tokens
   - `refresh_access_token(service_name)`: Refreshes token

4. **Management Commands**
   - `sync_goto_meetings`: Manual sync (always runs)
   - `sync_goto_meetings_if_stale`: Conditional sync (skips if fresh)

### Service Names

The system supports multiple GoToMeeting accounts:

- `gotomeeting_external`: External/client-facing meetings (default)
- `gotomeeting_internal`: Internal/company meetings

**Backward Compatibility**: Code using `service_name="gotomeeting"` will automatically use `gotomeeting_external` if it exists, otherwise fall back to `gotomeeting`.

## Operations

### Initial Setup

#### 1. Authenticate GoToMeeting Accounts

**External Account** (default):
```bash
# User visits:
/management/oauth/login/?service=external

# After OAuth callback, token is stored as service_name='gotomeeting_external'
```

**Internal Account** (optional):
```bash
# User visits:
/management/oauth/login/?service=internal

# After OAuth callback, token is stored as service_name='gotomeeting_internal'
```

#### 2. Verify Token Storage

```bash
poetry run python coda/manage.py shell -c "
from ai_services.models import OAuthToken
tokens = OAuthToken.objects.all()
for t in tokens:
    print(f'{t.service_name}: expires={t.expires_at}, valid={t.is_valid}')
"
```

### Manual Sync

**Sync last 24 hours (default)**:
```bash
poetry run python coda/manage.py sync_goto_meetings
```

**Sync specific date range**:
```bash
poetry run python coda/manage.py sync_goto_meetings --start 2025-12-01 --end 2025-12-31
```

**Sync specific service**:
```bash
# Note: sync_goto_meetings currently uses 'gotomeeting_external' by default
# For internal account, use sync_goto_meetings_if_stale with --force
```

### Scheduled Sync (Recommended)

**Using `sync_goto_meetings_if_stale`**:

This command is designed for cron/Heroku Scheduler/Celery Beat. It checks freshness before syncing.

**Basic usage** (syncs external account, max age 24 hours):
```bash
poetry run python coda/manage.py sync_goto_meetings_if_stale --service external --max-age-minutes 1440 --hours 24
```

**For internal account**:
```bash
poetry run python coda/manage.py sync_goto_meetings_if_stale --service internal --max-age-minutes 1440 --hours 24
```

**Force sync** (ignore freshness check):
```bash
poetry run python coda/manage.py sync_goto_meetings_if_stale --service external --force --hours 24
```

**Example cron job** (runs hourly, syncs if data is older than 60 minutes):
```bash
# In crontab:
0 * * * * cd /path/to/uat && poetry run python coda/manage.py sync_goto_meetings_if_stale --service external --max-age-minutes 60 --hours 24
```

**Example Heroku Scheduler**:
```bash
# Add to Heroku Scheduler:
poetry run python coda/manage.py sync_goto_meetings_if_stale --service external --max-age-minutes 1440 --hours 24
# Schedule: Daily at 1:00 AM UTC
```

### Freshness Monitoring

**Check last successful sync**:
```bash
poetry run python coda/manage.py shell -c "
from ai_services.services.goto_meeting_sync_service import get_last_successful_sync
sync = get_last_successful_sync('gotomeeting_external')
if sync:
    age_minutes = (timezone.now() - sync.finished_at).total_seconds() / 60
    print(f'Last sync: {age_minutes:.1f} minutes ago')
    print(f'Fetched: {sync.meetings_fetched_count}, Upserted: {sync.meetings_upserted_count}')
else:
    print('No successful sync found')
"
```

**Check if data is fresh**:
```bash
poetry run python coda/manage.py shell -c "
from ai_services.services.goto_meeting_sync_service import is_meeting_data_fresh
fresh = is_meeting_data_fresh('gotomeeting_external', max_age_minutes=1440)
print(f'Data is fresh: {fresh}')
"
```

**View sync run history**:
```bash
poetry run python coda/manage.py shell -c "
from ai_services.models import MeetingSyncRun
runs = MeetingSyncRun.objects.filter(service_name='gotomeeting_external').order_by('-started_at')[:10]
for r in runs:
    print(f'{r.started_at}: {r.status} - {r.meetings_fetched_count} fetched, {r.meetings_upserted_count} upserted')
"
```

## Best Practices

### 1. Default Behavior (DB-First)

- **DAF views never call sync services** - they only read from DB
- Meeting data should be fresh within 24 hours (acceptable delay)
- Users update tasks within 24 hours, so freshness window is sufficient

### 2. Sync Frequency

- **Recommended**: Hourly or daily sync for active accounts
- **Maximum acceptable age**: 24 hours (1440 minutes)
- **Minimum recommended**: 60 minutes for real-time needs

### 3. Multi-Account Strategy

- Use `gotomeeting_external` for client-facing meetings (default)
- Use `gotomeeting_internal` for internal company meetings
- Store tokens separately (automatic via service_name)
- Sync each account independently

### 4. Error Handling

- Failed syncs are logged in `MeetingSyncRun` with error_message
- Check sync status regularly via `MeetingSyncRun.status='failed'`
- Set up alerts for consecutive failures

### 5. Token Management

- Tokens are stored encrypted in `OAuthToken` table
- Tokens auto-refresh when expired
- If refresh fails, user must re-authenticate via `/management/oauth/login/?service=external`

## Troubleshooting

### Issue: "OAuth token not available"

**Solution**: Re-authenticate:
```
Visit: /management/oauth/login/?service=external
```

### Issue: Sync runs but no meetings found

**Possible causes**:
1. No meetings in the date range
2. OAuth token has insufficient permissions
3. GoToMeeting API rate limiting

**Diagnosis**:
```bash
# Check sync run records
poetry run python coda/manage.py shell -c "
from ai_services.models import MeetingSyncRun
runs = MeetingSyncRun.objects.filter(status='success').order_by('-started_at')[:5]
for r in runs:
    print(f'{r.started_at}: {r.meetings_fetched_count} fetched, error: {r.error_message}')
"
```

### Issue: Data appears stale but sync shows fresh

**Check**:
1. Verify `max_age_minutes` parameter matches your expectations
2. Check `MeetingSyncRun.finished_at` is recent
3. Verify timezone settings (all timestamps are UTC)

### Issue: Multiple accounts mixing meetings

**Solution**: Ensure `Meeting` records are tagged by `service_name` (if implemented) or sync to separate databases/databases with proper filtering.

**Note**: Current implementation does not tag `Meeting` records with `service_name`. If mixing is an issue, consider:
- Adding `service_name` field to `Meeting` model (requires migration)
- Or using separate databases/table prefixes per account

## Integration with Celery Beat

If using Celery Beat for scheduled execution:

```python
# In coda/coda_project/celery.py or similar:
from celery.schedules import crontab

app.conf.beat_schedule = {
    'sync-external-meetings': {
        'task': 'ai_services.tasks.daily_meeting_sync_task',
        'schedule': crontab(hour=1, minute=0),  # Daily at 1 AM
        'args': (1,),  # days_back
        'kwargs': {'service_name': 'gotomeeting_external'},
    },
    'sync-internal-meetings': {
        'task': 'ai_services.tasks.daily_meeting_sync_task',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
        'args': (1,),  # days_back
        'kwargs': {'service_name': 'gotomeeting_internal'},
    },
}
```

Or use management command via Celery:
```python
from django.core.management import call_command

@shared_task
def sync_meetings_if_stale_task():
    call_command('sync_goto_meetings_if_stale', '--service', 'external', '--max-age-minutes', '1440', '--hours', '24')
```

## Security Considerations

1. **OAuth tokens are encrypted** in database (`OAuthToken` model)
2. **No tokens logged** - only masked values (last 6 chars)
3. **State parameter** used for CSRF protection in OAuth flow
4. **Service isolation** - each service_name has separate token storage

## API Reference

### MeetingSyncRun Model

```python
from ai_services.models import MeetingSyncRun

# Fields:
- service_name: str (e.g., 'gotomeeting_external')
- started_at: datetime
- finished_at: datetime (nullable)
- status: str ('success', 'failed', 'in_progress')
- meetings_fetched_count: int
- meetings_upserted_count: int
- window_start: datetime
- window_end: datetime
- error_message: str (nullable)
```

### Sync Service Functions

```python
from ai_services.services.goto_meeting_sync_service import sync, get_last_successful_sync, is_meeting_data_fresh

# Sync meetings
result = sync(start_dt, end_dt, service_name='gotomeeting_external')
# Returns: {'meetings_fetched': int, 'meetings_created': int, 'success': bool, ...}

# Get last successful sync
last_sync = get_last_successful_sync('gotomeeting_external')
# Returns: MeetingSyncRun instance or None

# Check freshness
is_fresh = is_meeting_data_fresh('gotomeeting_external', max_age_minutes=1440)
# Returns: bool
```

### OAuth Helper Functions

```python
from shared_core.utils.oauth import get_access_token, exchange_code_for_tokens, refresh_access_token

# Get access token
token = get_access_token(service_name='gotomeeting_external')
# Returns: str (access token) or None

# Exchange auth code (used in callback)
success = exchange_code_for_tokens(auth_code, service_name='gotomeeting_external')
# Returns: bool

# Refresh token
success = refresh_access_token(service_name='gotomeeting_external')
# Returns: bool
```

## Summary

- ✅ **DB-first approach**: DAF views never call sync services
- ✅ **Scheduled execution**: Use `sync_goto_meetings_if_stale` for cron/Celery
- ✅ **Freshness tracking**: `MeetingSyncRun` records enable monitoring
- ✅ **Multi-account support**: Separate tokens for external/internal accounts
- ✅ **Safe defaults**: 24-hour freshness window is acceptable
- ✅ **Backward compatible**: Existing code using `service_name="gotomeeting"` continues to work


