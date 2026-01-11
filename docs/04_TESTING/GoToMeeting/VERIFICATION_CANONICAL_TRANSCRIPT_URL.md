# Verification: Canonical Transcript URL

## Overview
This document provides verification steps to confirm that GoToMeeting transcript URLs are stored in canonical format: `https://transcripts.gotomeeting.com/#/s/<token>`

## Changes Made
1. **New Function**: `normalize_gotomeeting_transcript_url()` in `coda/ai_services/utils/meeting_normalizer.py`
   - Extracts tokens from various URL formats
   - Constructs canonical URL: `https://transcripts.gotomeeting.com/#/s/<token>`
   - Handles shareUrl, downloadUrl, shareId, and token parameters

2. **Meeting Sync**: Updated to use canonical URL normalization
   - File: `coda/ai_services/services/goto_meeting_sync_service.py`
   - Extracts canonical URL from API response
   - Stores in `recording` field (which maps to `recording_url` in DB)

3. **Save Meeting Data**: Updated to prefer canonical transcript URL
   - File: `coda/ai_services/views.py`
   - Uses canonical URL if available, falls back to normalized recording URL

## Verification Steps

### Step 1: Sync Meetings for a Date Range
```bash
cd /Users/coda/Projects/uat/coda && poetry run python manage.py shell -c "
from django.utils import timezone
from datetime import datetime
from ai_services.services.goto_meeting_sync_service import sync

# Sync meetings for a known date range (e.g., Jan 1-3, 2026)
start = timezone.make_aware(datetime(2026, 1, 1))
end = timezone.make_aware(datetime(2026, 1, 4))

result = sync(start, end, service_name='gotomeeting_internal')
print(f'Meeting sync result: {result}')
"
```

### Step 2: Query Meetings and Check Recording URLs
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
).exclude(recording_url__isnull=True).exclude(recording_url='')[:10]

print('=' * 80)
print('VERIFICATION: Canonical Transcript URLs')
print('=' * 80)
print(f'Checking {meetings.count()} meetings with recording_url...')
print()

canonical_count = 0
non_canonical_count = 0

for m in meetings:
    is_canonical = m.recording_url and m.recording_url.startswith('https://transcripts.gotomeeting.com/#/s/')
    
    if is_canonical:
        canonical_count += 1
        print(f'✅ Meeting {m.meeting_id}:')
        print(f'   URL: {m.recording_url}')
        print(f'   Topic: {m.topic[:60]}...' if len(m.topic) > 60 else f'   Topic: {m.topic}')
    else:
        non_canonical_count += 1
        print(f'⚠️  Meeting {m.meeting_id}:')
        print(f'   URL: {m.recording_url}')
        print(f'   Topic: {m.topic[:60]}...' if len(m.topic) > 60 else f'   Topic: {m.topic}')
    print()

print('=' * 80)
print(f'Summary: {canonical_count} canonical, {non_canonical_count} non-canonical')
print('=' * 80)
"
```

### Step 3: Check Specific Meetings (if known)
```bash
cd /Users/coda/Projects/uat/coda && poetry run python manage.py shell -c "
from ai_services.models import Meeting

# Check specific meetings (replace with actual meeting_ids from your sync)
meeting_ids = ['623828061', '369139597']  # Example IDs

meetings = Meeting.objects.filter(meeting_id__in=meeting_ids)

print('=' * 80)
print('VERIFICATION: Specific Meeting Transcript URLs')
print('=' * 80)

for m in meetings:
    print(f'Meeting {m.meeting_id}:')
    print(f'  Topic: {m.topic}')
    print(f'  Recording URL: {m.recording_url or \"None\"}')
    
    if m.recording_url:
        is_canonical = m.recording_url.startswith('https://transcripts.gotomeeting.com/#/s/')
        if is_canonical:
            print(f'  ✅ Canonical format')
            # Extract token
            token = m.recording_url.replace('https://transcripts.gotomeeting.com/#/s/', '')
            print(f'  Token: {token}')
        else:
            print(f'  ⚠️  Non-canonical format')
    else:
        print(f'  ⚠️  No recording URL')
    print()
"
```

### Step 4: Test URL Normalization Function Directly
```bash
cd /Users/coda/Projects/uat/coda && poetry run python manage.py shell -c "
from ai_services.utils.meeting_normalizer import normalize_gotomeeting_transcript_url

# Test various URL formats
test_cases = [
    {
        'name': 'Canonical URL (already correct)',
        'share_url': 'https://transcripts.gotomeeting.com/#/s/abc123xyz',
        'expected': 'https://transcripts.gotomeeting.com/#/s/abc123xyz'
    },
    {
        'name': 'Share URL with token',
        'share_url': 'https://global.gotomeeting.com/share/abc123xyz',
        'expected': 'https://transcripts.gotomeeting.com/#/s/abc123xyz'
    },
    {
        'name': 'Share URL with /s/ path',
        'share_url': 'https://gotomeeting.com/s/abc123xyz',
        'expected': 'https://transcripts.gotomeeting.com/#/s/abc123xyz'
    },
    {
        'name': 'Token provided directly',
        'token': 'abc123xyz',
        'expected': 'https://transcripts.gotomeeting.com/#/s/abc123xyz'
    },
    {
        'name': 'Share ID provided',
        'share_id': 'abc123xyz',
        'expected': 'https://transcripts.gotomeeting.com/#/s/abc123xyz'
    },
    {
        'name': 'Download URL with token',
        'download_url': 'https://gotomeeting.com/download?token=abc123xyz',
        'expected': 'https://transcripts.gotomeeting.com/#/s/abc123xyz'
    },
]

print('=' * 80)
print('TESTING: URL Normalization Function')
print('=' * 80)

for test in test_cases:
    result = normalize_gotomeeting_transcript_url(
        share_url=test.get('share_url'),
        download_url=test.get('download_url'),
        share_id=test.get('share_id'),
        token=test.get('token')
    )
    
    print(f\"Test: {test['name']}\")
    print(f\"  Input: share_url={test.get('share_url')}, token={test.get('token')}, share_id={test.get('share_id')}\")
    print(f\"  Result: {result}\")
    print(f\"  Expected: {test['expected']}\")
    
    if result == test['expected']:
        print(f\"  ✅ PASS\")
    else:
        print(f\"  ❌ FAIL\")
    print()
"
```

## Expected Results

### After Step 2:
- **Most meetings should have canonical URLs**: `https://transcripts.gotomeeting.com/#/s/<token>`
- **Non-canonical URLs should be rare** (only if no token can be extracted from API response)
- **All canonical URLs should be clickable** and open the transcript viewer directly

### After Step 3:
- **Specific meetings should have canonical URLs** if they have recordings
- **Token should be extracted** and visible in the URL

### After Step 4:
- **All test cases should pass** (normalization function works correctly)

## Troubleshooting

### If meetings don't have canonical URLs:
1. Check if API response includes `recording.shareUrl` or `recording.downloadUrl`
2. Check logs for: `📹 Canonical transcript URL: ...`
3. Verify the normalization function is being called: add debug logging

### If canonical URLs are not clickable:
1. Verify the URL format: should start with `https://transcripts.gotomeeting.com/#/s/`
2. Check if token is valid (not empty, not just whitespace)
3. Test the URL manually in a browser

### If normalization function fails:
1. Check regex patterns in `normalize_gotomeeting_transcript_url()`
2. Add debug logging to see what tokens are being extracted
3. Test with actual API responses from GoToMeeting

