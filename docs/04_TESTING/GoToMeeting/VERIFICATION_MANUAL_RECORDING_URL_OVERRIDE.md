# Verification: Manual Recording URL Override

## Overview
This document provides verification steps to confirm that manual override support for `Meeting.recording_url` is working correctly with source tracking and sync precedence rules.

## Changes Made

### 1. Source Tracking Fields
- **File**: `coda/ai_services/models.py`
- Added fields:
  - `recording_url_source`: choices `['provider', 'manual']` (default null)
  - `recording_url_updated_by`: FK to User (nullable)
  - `recording_url_updated_at`: DateTimeField (auto-set when recording_url changes)

### 2. Validation
- **File**: `coda/ai_services/models.py` (`clean()` method)
- Validates: if URL is `transcripts.gotomeeting.com` it must be canonical (`#/s/<token>`)
- Rejects non-canonical transcripts URLs with clear error message
- Allows non-transcripts URLs (e.g., Google Drive)

### 3. Admin Support
- **File**: `coda/ai_services/admin.py`
- Added fields to admin interface
- `save_model()` override tracks manual edits and sets source='manual'
- Validates canonical format before saving

### 4. Sync Precedence Rules
- **File**: `coda/ai_services/services/goto_meeting_sync_service.py`
- Sets `recording_url_source='provider'` when canonical URL is available
  
- **File**: `coda/ai_services/views.py` (`save_meeting_data`)
- **Rule 1**: If canonical URL available from provider → update recording_url and set source='provider' (even if previously manual, but logs when overwriting)
- **Rule 2**: If canonical URL NOT available → do NOT overwrite existing non-empty recording_url when source='manual'
- **Rule 3**: Never write bare host / non-canonical

### 5. Tests
- **File**: `coda/ai_services/tests/test_recording_url_manual_override.py`
- Tests for all scenarios

## Verification Steps

### Step 1: Run Migration
```bash
cd /Users/coda/Projects/uat/coda && poetry run python manage.py migrate ai_services
```

**Expected Output:**
```
Operations to perform:
  Apply all migrations: ai_services
Running migrations:
  Applying ai_services.0010_add_recording_url_source_tracking... OK
```

### Step 2: Test Manual Override in Admin
```bash
# Start Django shell and create a test meeting
cd /Users/coda/Projects/uat/coda && poetry run python manage.py shell -c "
from ai_services.models import Meeting
from django.utils import timezone
from datetime import datetime
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.first()

# Create test meeting
meeting = Meeting.objects.create(
    meeting_id='test_manual_override',
    topic='Test Manual Override',
    start_time=timezone.make_aware(datetime(2026, 1, 1, 10, 0)),
    end_time=timezone.make_aware(datetime(2026, 1, 1, 11, 0)),
    duration_minutes=60,
)

print(f'Created meeting: {meeting.meeting_id}')
print(f'Initial recording_url: {meeting.recording_url}')
print(f'Initial recording_url_source: {meeting.recording_url_source}')
"
```

**Then manually edit in Django admin:**
1. Go to `/admin/ai_services/meeting/test_manual_override/change/`
2. Set `recording_url` to: `https://transcripts.gotomeeting.com/#/s/manual123`
3. Save

**Verify:**
```bash
cd /Users/coda/Projects/uat/coda && poetry run python manage.py shell -c "
from ai_services.models import Meeting

meeting = Meeting.objects.get(meeting_id='test_manual_override')
print(f'recording_url: {meeting.recording_url}')
print(f'recording_url_source: {meeting.recording_url_source}')
print(f'recording_url_updated_by: {meeting.recording_url_updated_by}')
print(f'recording_url_updated_at: {meeting.recording_url_updated_at}')
"
```

**Expected Output:**
```
recording_url: https://transcripts.gotomeeting.com/#/s/manual123
recording_url_source: manual
recording_url_updated_by: <User: ...>
recording_url_updated_at: 2026-01-XX ...
```

### Step 3: Test Validation (Non-Canonical Rejection)
```bash
cd /Users/coda/Projects/uat/coda && poetry run python manage.py shell -c "
from ai_services.models import Meeting
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime

meeting = Meeting.objects.get(meeting_id='test_manual_override')

# Try to set non-canonical transcripts URL
meeting.recording_url = 'https://transcripts.gotomeeting.com'
meeting.recording_url_source = 'manual'

try:
    meeting.full_clean()
    print('❌ FAILURE: Validation should have rejected non-canonical URL')
except ValidationError as e:
    print('✅ SUCCESS: Validation rejected non-canonical URL')
    print(f'Error: {e.message_dict}')
"
```

**Expected Output:**
```
✅ SUCCESS: Validation rejected non-canonical URL
Error: {'recording_url': ['If recording_url is a transcripts.gotomeeting.com URL, it must be in canonical format: https://transcripts.gotomeeting.com/#/s/<token>. Received: https://transcripts.gotomeeting.com']}
```

### Step 4: Test Sync Precedence - Manual Preserved When Provider Has No Token
```bash
cd /Users/coda/Projects/uat/coda && poetry run python manage.py shell -c "
from ai_services.models import Meeting
from ai_services.views import save_meeting_data
from django.utils import timezone
from datetime import datetime

# Ensure meeting has manual canonical URL
meeting = Meeting.objects.get(meeting_id='test_manual_override')
meeting.recording_url = 'https://transcripts.gotomeeting.com/#/s/manual123'
meeting.recording_url_source = 'manual'
meeting.save()

print(f'Before sync: recording_url={meeting.recording_url}, source={meeting.recording_url_source}')

# Sync with no canonical URL from provider
meeting_data = [{
    'meetingId': 'test_manual_override',
    'subject': 'Test Meeting',
    'meetingType': 'scheduled',
    'startTime': '2026-01-01T10:00:00Z',
    'endTime': '2026-01-01T11:00:00Z',
    'duration': 60,
    'recording': '',  # No recording URL from provider
    'downloadUrl': '',
}]

save_meeting_data(meeting_data)

# Refresh from DB
meeting.refresh_from_db()

print(f'After sync: recording_url={meeting.recording_url}, source={meeting.recording_url_source}')

if meeting.recording_url == 'https://transcripts.gotomeeting.com/#/s/manual123' and meeting.recording_url_source == 'manual':
    print('✅ SUCCESS: Manual URL preserved when provider has no token')
else:
    print('❌ FAILURE: Manual URL should have been preserved')
"
```

**Expected Output:**
```
Before sync: recording_url=https://transcripts.gotomeeting.com/#/s/manual123, source=manual
After sync: recording_url=https://transcripts.gotomeeting.com/#/s/manual123, source=manual
✅ SUCCESS: Manual URL preserved when provider has no token
```

### Step 5: Test Sync Precedence - Provider Overwrites Manual
```bash
cd /Users/coda/Projects/uat/coda && poetry run python manage.py shell -c "
from ai_services.models import Meeting
from ai_services.views import save_meeting_data

# Ensure meeting has manual canonical URL
meeting = Meeting.objects.get(meeting_id='test_manual_override')
meeting.recording_url = 'https://transcripts.gotomeeting.com/#/s/manual123'
meeting.recording_url_source = 'manual'
meeting.save()

print(f'Before sync: recording_url={meeting.recording_url}, source={meeting.recording_url_source}')

# Sync with canonical URL from provider
meeting_data = [{
    'meetingId': 'test_manual_override',
    'subject': 'Test Meeting',
    'meetingType': 'scheduled',
    'startTime': '2026-01-01T10:00:00Z',
    'endTime': '2026-01-01T11:00:00Z',
    'duration': 60,
    'recording': 'https://transcripts.gotomeeting.com/#/s/provider456',  # Provider canonical URL
    'downloadUrl': '',
}]

save_meeting_data(meeting_data)

# Refresh from DB
meeting.refresh_from_db()

print(f'After sync: recording_url={meeting.recording_url}, source={meeting.recording_url_source}')

if meeting.recording_url == 'https://transcripts.gotomeeting.com/#/s/provider456' and meeting.recording_url_source == 'provider':
    print('✅ SUCCESS: Provider URL overwrote manual URL')
else:
    print('❌ FAILURE: Provider URL should have overwritten manual URL')
"
```

**Expected Output:**
```
Before sync: recording_url=https://transcripts.gotomeeting.com/#/s/manual123, source=manual
After sync: recording_url=https://transcripts.gotomeeting.com/#/s/provider456, source=provider
✅ SUCCESS: Provider URL overwrote manual URL
```

**Check logs for overwrite warning:**
```bash
grep "Overwriting manual recording_url" logs/*.log | tail -5
```

**Expected:** Log message: `⚠️  Overwriting manual recording_url for meeting_id=test_manual_override (old=..., new=...)`

### Step 6: Run Unit Tests
```bash
cd /Users/coda/Projects/uat/coda && poetry run python -m pytest ai_services/tests/test_recording_url_manual_override.py -v
```

**Expected Output:**
```
test_manual_canonical_url_is_preserved_when_provider_has_no_token PASSED
test_manual_non_canonical_is_rejected_by_validation PASSED
test_manual_non_transcripts_url_is_allowed PASSED
test_provider_canonical_url_overwrites_manual PASSED
test_sync_never_persists_bare_host PASSED
```

### Step 7: Verify Sync Never Persists Bare Host
```bash
cd /Users/coda/Projects/uat/coda && poetry run python manage.py shell -c "
from ai_services.models import Meeting
from ai_services.views import save_meeting_data

# Sync with bare host URL (should be rejected)
meeting_data = [{
    'meetingId': 'test_bare_host_rejection',
    'subject': 'Test Meeting',
    'meetingType': 'scheduled',
    'startTime': '2026-01-01T10:00:00Z',
    'endTime': '2026-01-01T11:00:00Z',
    'duration': 60,
    'recording': 'https://transcripts.gotomeeting.com',  # Bare host
    'downloadUrl': '',
}]

save_meeting_data(meeting_data)

# Check that meeting was created
meeting = Meeting.objects.get(meeting_id='test_bare_host_rejection')

print(f'recording_url: {meeting.recording_url}')
print(f'recording_url_source: {meeting.recording_url_source}')

if meeting.recording_url in ['https://transcripts.gotomeeting.com', 'https://transcripts.gotomeeting.com/']:
    print('❌ FAILURE: Bare host URL was persisted')
else:
    print('✅ SUCCESS: Bare host URL was not persisted')
    if meeting.recording_url:
        print(f'  (recording_url is: {meeting.recording_url})')
    else:
        print('  (recording_url is None)')
"
```

**Expected Output:**
```
recording_url: None
recording_url_source: None
✅ SUCCESS: Bare host URL was not persisted
  (recording_url is None)
```

## Acceptance Criteria

### ✅ Manual Override:
- Employees/admins can manually add/edit `Meeting.recording_url` in admin
- Validation rejects non-canonical transcripts URLs with clear message
- Non-transcripts URLs (e.g., Google Drive) are allowed

### ✅ Source Tracking:
- `recording_url_source` is set to 'manual' when user edits
- `recording_url_updated_by` and `recording_url_updated_at` are populated

### ✅ Sync Precedence:
- Manual canonical URL is preserved when provider has no token
- Provider canonical URL overwrites manual (and logs)
- Sync never persists bare host

### ✅ Tests:
- All tests pass

## Troubleshooting

### If validation doesn't work:
1. Check that `clean()` method is called (should be automatic in admin)
2. Verify `full_clean()` is called in `save()` method
3. Check admin `save_model()` override

### If manual URL is overwritten when provider has no token:
1. Check sync logic in `views.py` - should check `recording_url_source == 'manual'`
2. Verify logs show: `ℹ️  Preserving manual recording_url for meeting_id=...`

### If provider URL doesn't overwrite manual:
1. Check sync logic - should always overwrite if canonical URL available
2. Verify logs show: `⚠️  Overwriting manual recording_url for meeting_id=...`

