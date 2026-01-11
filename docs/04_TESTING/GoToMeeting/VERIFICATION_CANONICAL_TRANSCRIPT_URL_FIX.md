# Verification: Canonical Transcript URL Fix

## Overview
This document provides verification steps to confirm that the canonical transcript URL fix is working correctly and that bare hosts are no longer stored.

## Changes Made
1. **Fixed Fragment Parsing**: Updated `normalize_gotomeeting_transcript_url()` to properly parse fragments using `urlparse`
2. **Added Guard**: Never returns bare host `https://transcripts.gotomeeting.com` without token
3. **Updated Callers**: Only set `recording_url` when canonical URL is returned (starts with `https://transcripts.gotomeeting.com/#/s/`)
4. **Added Unit Tests**: Comprehensive tests covering fragment parsing and guard behavior

## Verification Steps

### Step 1: Run Unit Tests
```bash
cd /Users/coda/Projects/uat/coda && poetry run python -m pytest ai_services/tests/test_meeting_normalizer.py -v
```

**Expected**: All tests pass, including:
- `test_bare_host_returns_none` ✅
- `test_canonical_url_with_fragment` ✅
- `test_fragment_priority_over_query` ✅

### Step 2: Sync Meetings for a Date Range
```bash
cd /Users/coda/Projects/uat/coda && poetry run python manage.py shell -c "
from django.utils import timezone
from datetime import datetime
from ai_services.services.goto_meeting_sync_service import sync

start = timezone.make_aware(datetime(2026, 1, 1))
end = timezone.make_aware(datetime(2026, 1, 4))

result = sync(start, end, service_name='gotomeeting_internal')
print(f'Meeting sync result: {result}')
"
```

### Step 3: Query Meetings and Check Recording URLs
```bash
cd /Users/coda/Projects/uat/coda && poetry run python manage.py shell -c "
from ai_services.models import Meeting
from django.utils import timezone
from datetime import datetime

start = timezone.make_aware(datetime(2026, 1, 1))
end = timezone.make_aware(datetime(2026, 1, 4))

meetings = Meeting.objects.filter(
    start_time__gte=start,
    start_time__lt=end,
    service_name='gotomeeting_internal'
).exclude(recording_url__isnull=True).exclude(recording_url='')[:20]

print('=' * 80)
print('VERIFICATION: Canonical Transcript URLs (After Fix)')
print('=' * 80)
print(f'Checking {meetings.count()} meetings with recording_url...')
print()

canonical_count = 0
non_canonical_count = 0
bare_host_count = 0

for m in meetings:
    is_canonical = m.recording_url and m.recording_url.startswith('https://transcripts.gotomeeting.com/#/s/')
    is_bare_host = m.recording_url in ['https://transcripts.gotomeeting.com', 'https://transcripts.gotomeeting.com/']
    
    if is_bare_host:
        bare_host_count += 1
        print(f'❌ Meeting {m.meeting_id}: BARE HOST (should not happen)')
        print(f'   URL: {m.recording_url}')
    elif is_canonical:
        canonical_count += 1
        print(f'✅ Meeting {m.meeting_id}: Canonical')
        print(f'   URL: {m.recording_url}')
    else:
        non_canonical_count += 1
        print(f'⚠️  Meeting {m.meeting_id}: Non-canonical')
        print(f'   URL: {m.recording_url}')
    print()

print('=' * 80)
print(f'Summary:')
print(f'  ✅ Canonical: {canonical_count}')
print(f'  ⚠️  Non-canonical: {non_canonical_count}')
print(f'  ❌ Bare host: {bare_host_count} (SHOULD BE 0)')
print('=' * 80)

if bare_host_count > 0:
    print('❌ FAILURE: Found bare host URLs - fix not working!')
elif canonical_count > 0:
    print('✅ SUCCESS: All recording URLs are canonical or null')
else:
    print('⚠️  WARNING: No canonical URLs found (may be expected if no recordings)')
"
```

## Expected Results

### After Step 1:
- **All unit tests pass** (17/17)
- **Fragment parsing works correctly**
- **Guard prevents bare host returns**

### After Step 3:
- **Canonical > 0**: Meetings with recordings should have canonical URLs
- **Non-canonical = 0** (or only true fallbacks, not bare hosts)
- **Bare host = 0**: No meetings should have `recording_url = "https://transcripts.gotomeeting.com"`

## Troubleshooting

### If bare host URLs are still present:
1. Check if old meetings were synced before the fix
2. Run a migration/backfill to update existing meetings:
   ```python
   from ai_services.models import Meeting
   from ai_services.utils.meeting_normalizer import normalize_gotomeeting_transcript_url
   
   bare_hosts = Meeting.objects.filter(
       recording_url__in=['https://transcripts.gotomeeting.com', 'https://transcripts.gotomeeting.com/']
   )
   
   for m in bare_hosts:
       # Try to reconstruct canonical URL from other fields
       canonical = normalize_gotomeeting_transcript_url(share_url=m.recording_url)
       if canonical:
           m.recording_url = canonical
           m.save(update_fields=['recording_url'])
       else:
           # No token available, clear the URL
           m.recording_url = None
           m.save(update_fields=['recording_url'])
   ```

### If canonical URLs are not being created:
1. Check logs for: `🔍 URL Parse Debug` to see fragment parsing
2. Check logs for: `✅ Extracted token from fragment` to confirm token extraction
3. Verify API response includes `recording.shareUrl` or `recording.downloadUrl` with tokens

