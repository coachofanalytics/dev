# Verification: Bare Host Recording URL Fix

## Overview
This document provides verification steps to confirm that bare host recording URLs are never stored and existing ones are cleaned up.

## Changes Made

### 1. Hard Rule Enforcement
- **File**: `coda/ai_services/services/goto_meeting_sync_service.py`
  - Never sets `recording_url` to bare host
  - Only stores canonical URLs starting with `https://transcripts.gotomeeting.com/#/s/`
  
- **File**: `coda/ai_services/views.py` (`save_meeting_data`)
  - Never sets `recording_url` to bare host on create
  - Clears existing bare host URLs when updating with non-canonical value
  - Preserves existing canonical URLs if new value is not canonical

### 2. INFO Logging
- **File**: `coda/ai_services/services/goto_meeting_sync_service.py`
  - Logs recording dict keys and values
  - Logs inputs to `normalize_gotomeeting_transcript_url()`
  - Logs normalized output

### 3. Cleanup Command
- **File**: `coda/ai_services/management/commands/cleanup_bare_host_recording_urls.py`
  - Cleans up existing bare host URLs
  - Supports `--dry-run` and `--service-name` filters

### 4. Tests
- **File**: `coda/ai_services/tests/test_meeting_normalizer.py`
  - Added test for caller behavior expectations
  
- **File**: `coda/ai_services/tests/test_recording_url_persistence.py`
  - Tests that `save_meeting_data` never stores bare host
  - Tests that existing bare host is cleared on update

## Verification Steps

### Step 1: Clean Up Existing Bare Host URLs
```bash
cd /Users/coda/Projects/uat/coda && poetry run python manage.py cleanup_bare_host_recording_urls --dry-run
```

**Expected Output:**
```
================================================================================
BARE HOST RECORDING URL CLEANUP
================================================================================
Found 43 meetings with bare host or non-canonical recording URLs

🔍 DRY RUN MODE - No changes will be made

  Would clear: meeting_id=..., recording_url=https://transcripts.gotomeeting.com, ...
  ...
```

**Then run for real:**
```bash
cd /Users/coda/Projects/uat/coda && poetry run python manage.py cleanup_bare_host_recording_urls
```

**Expected Output:**
```
================================================================================
BARE HOST RECORDING URL CLEANUP
================================================================================
Found 43 meetings with bare host or non-canonical recording URLs

  ✅ Cleared: meeting_id=..., old_url=https://transcripts.gotomeeting.com
  ...

✅ Successfully cleared 43 bare host recording URLs
================================================================================
```

### Step 2: Verify Cleanup
```bash
cd /Users/coda/Projects/uat/coda && poetry run python manage.py shell -c "
from ai_services.models import Meeting

bare_hosts = Meeting.objects.filter(
    recording_url__in=['https://transcripts.gotomeeting.com', 'https://transcripts.gotomeeting.com/']
)

non_canonical = Meeting.objects.filter(
    recording_url__startswith='https://transcripts.gotomeeting.com'
).exclude(
    recording_url__startswith='https://transcripts.gotomeeting.com/#/s/'
).exclude(recording_url__isnull=True)

print('=' * 80)
print('VERIFICATION: Bare Host Recording URLs')
print('=' * 80)
print(f'Bare host URLs: {bare_hosts.count()} (should be 0)')
print(f'Non-canonical transcripts URLs: {non_canonical.count()} (should be 0)')

if bare_hosts.count() == 0 and non_canonical.count() == 0:
    print('✅ SUCCESS: No bare host or non-canonical URLs found')
else:
    print('❌ FAILURE: Found bare host or non-canonical URLs')
    if bare_hosts.count() > 0:
        print(f'  Bare hosts: {list(bare_hosts.values_list(\"meeting_id\", \"recording_url\")[:5])}')
    if non_canonical.count() > 0:
        print(f'  Non-canonical: {list(non_canonical.values_list(\"meeting_id\", \"recording_url\")[:5])}')
print('=' * 80)
"
```

**Expected Output:**
```
================================================================================
VERIFICATION: Bare Host Recording URLs
================================================================================
Bare host URLs: 0 (should be 0)
Non-canonical transcripts URLs: 0 (should be 0)
✅ SUCCESS: No bare host or non-canonical URLs found
================================================================================
```

### Step 3: Run Meeting Sync and Verify
```bash
cd /Users/coda/Projects/uat/coda && poetry run python manage.py shell -c "
from django.utils import timezone
from datetime import datetime
from ai_services.services.goto_meeting_sync_service import sync

start = timezone.make_aware(datetime(2026, 1, 1))
end = timezone.make_aware(datetime(2026, 1, 5))

result = sync(start, end, service_name='gotomeeting_internal')
print(f'Meeting sync result: {result}')
"
```

**Check logs for INFO messages:**
```bash
# Look for recording data logs
grep "📹 Recording data" logs/*.log | tail -10

# Look for normalized URL logs
grep "📹 Normalized transcript URL" logs/*.log | tail -10

# Look for canonical URL usage
grep "✅ Using canonical transcript URL" logs/*.log | tail -10

# Look for skipped non-canonical URLs
grep "⚠️  Skipping non-canonical URL" logs/*.log | tail -10
```

### Step 4: Verify No New Bare Host URLs After Sync
```bash
cd /Users/coda/Projects/uat/coda && poetry run python manage.py shell -c "
from ai_services.models import Meeting
from django.utils import timezone
from datetime import datetime

start = timezone.make_aware(datetime(2026, 1, 1))
end = timezone.make_aware(datetime(2026, 1, 5))

# Check meetings in date range
meetings = Meeting.objects.filter(
    start_time__gte=start,
    start_time__lt=end,
    service_name='gotomeeting_internal'
)

bare_hosts = meetings.filter(
    recording_url__in=['https://transcripts.gotomeeting.com', 'https://transcripts.gotomeeting.com/']
)

non_canonical = meetings.filter(
    recording_url__startswith='https://transcripts.gotomeeting.com'
).exclude(
    recording_url__startswith='https://transcripts.gotomeeting.com/#/s/'
).exclude(recording_url__isnull=True)

canonical = meetings.filter(
    recording_url__startswith='https://transcripts.gotomeeting.com/#/s/'
)

print('=' * 80)
print('VERIFICATION: Recording URLs After Sync (Jan 1-4, 2026)')
print('=' * 80)
print(f'Total meetings: {meetings.count()}')
print(f'Meetings with recording_url: {meetings.exclude(recording_url__isnull=True).exclude(recording_url=\"\").count()}')
print(f'  ✅ Canonical URLs: {canonical.count()}')
print(f'  ❌ Bare host URLs: {bare_hosts.count()} (should be 0)')
print(f'  ⚠️  Non-canonical URLs: {non_canonical.count()} (should be 0)')
print('=' * 80)

if bare_hosts.count() == 0 and non_canonical.count() == 0:
    print('✅ SUCCESS: No bare host or non-canonical URLs after sync')
else:
    print('❌ FAILURE: Found bare host or non-canonical URLs after sync')
"
```

**Expected Output:**
```
================================================================================
VERIFICATION: Recording URLs After Sync (Jan 1-4, 2026)
================================================================================
Total meetings: X
Meetings with recording_url: Y
  ✅ Canonical URLs: Y (or 0 if API doesn't provide tokens)
  ❌ Bare host URLs: 0 (should be 0)
  ⚠️  Non-canonical URLs: 0 (should be 0)
================================================================================
✅ SUCCESS: No bare host or non-canonical URLs after sync
```

### Step 5: Run Unit Tests
```bash
cd /Users/coda/Projects/uat/coda && poetry run python -m pytest ai_services/tests/test_meeting_normalizer.py::TestNormalizeGoToMeetingTranscriptURL::test_callers_do_not_persist_bare_host -v
```

**Expected Output:**
```
test_callers_do_not_persist_bare_host PASSED
```

## Acceptance Criteria

### ✅ After cleanup:
- Query for bare host URLs returns **0**

### ✅ After meeting sync:
- Query for bare host URLs returns **0**
- Canonical URLs are stored correctly (if API provides tokens)
- Non-canonical URLs are not stored

### ✅ Tests:
- All tests pass

## Troubleshooting

### If bare host URLs still exist after cleanup:
1. Check if cleanup command ran successfully
2. Verify the query matches the exact URLs:
   ```python
   Meeting.objects.filter(recording_url__in=['https://transcripts.gotomeeting.com', 'https://transcripts.gotomeeting.com/'])
   ```

### If new bare host URLs appear after sync:
1. Check logs for: `📹 Recording data` to see what API returns
2. Check logs for: `📹 Normalized transcript URL` to see normalization result
3. Check logs for: `⚠️  Skipping non-canonical URL` to confirm rejection
4. Verify the hard rule is being enforced in both `goto_meeting_sync_service.py` and `views.py`

### If API doesn't provide tokens:
- Check logs for `📹 Recording data` to see what keys are in the recording dict
- If `shareId` or `token` are missing, the normalizer will return `None`
- This is expected behavior - we don't store bare host URLs

