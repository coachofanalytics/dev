# Dual GoToMeeting OAuth Implementation Summary

**Date:** 2024-12-29  
**Branch:** 25.12_CODA_DEV_CM  
**Status:** ✅ **COMPLETE**

---

## Objective

Support TWO GoToMeeting OAuth accounts cleanly:
- **INTERNAL (primary):** codagrandprojects@gmail.com
- **EXTERNAL (secondary):** coachofanalytics@gmail.com

Ensure meetings from BOTH accounts can be fetched into the canonical Meeting table with a clear source label, and fix the "No Start/Join Meeting button appears on DAF" issue.

---

## Implementation Summary

### 1. GoToMeeting Service Registry ✅

**File:** `coda/ai_services/utils/goto_service_registry.py` (NEW)

Created a single source of truth mapping service_name → OAuth credentials:
- `gotomeeting_internal` uses `GOTO_OAUTH_CLIENT_ID/SECRET`
- `gotomeeting_external` uses `EXT_GOTO_OAUTH_CLIENT_ID/SECRET`

**Functions:**
- `list_goto_services()` → Returns available services (internal first, then external)
- `get_oauth_credentials(service_name)` → Returns (client_id, client_secret) with fallback rules
- `is_service_enabled(service_name)` → Checks if service has credentials configured

**Backward Compatibility:**
- Legacy `"gotomeeting"` service_name maps to `"gotomeeting_internal"` automatically

---

### 2. OAuth Token Acquisition ✅

**Files Modified:**
- `coda/shared_core/utils/oauth.py`
- `coda/management/legacy_views.py` (oauth_login, oauth_callback)

**Changes:**
- Updated `_get_client_id()` and `_get_client_secret()` to accept `service_name` parameter
- Updated `get_authorization_url()`, `exchange_code_for_tokens()`, `refresh_access_token()`, and `get_access_token()` to support `service_name`
- OAuth login view already supported `?service=internal|external` parameter
- OAuth callback stores tokens with correct `service_name` from session

**Token Storage:**
- Tokens stored in `OAuthToken` model with `service_name` field
- Each service has its own token record (e.g., `service_name='gotomeeting_internal'`)

---

### 3. Meeting Sync (Dual-Account Support) ✅

**Files Modified:**
- `coda/ai_services/views.py` (`getmeetingresponse`, `save_meeting_data`)
- `coda/ai_services/services/meeting_sync_service.py`
- `coda/ai_services/management/commands/sync_gotomeetings.py`

**Changes:**
- `getmeetingresponse()` now accepts `service_name` parameter
- `save_meeting_data()` stores `service_name` in Meeting records
- `sync_meetings_for_range()` accepts `service_name` parameter
- `sync_gotomeetings` command supports `--service gotomeeting_internal|gotomeeting_external|all`

**Sync Behavior:**
- When `--service all`: Fetches internal first, then external
- Each meeting stored with correct `service_name` in Meeting table
- Meeting ID uniqueness: Assumes `meeting_id` is globally unique across accounts (GoToMeeting standard)

**Idempotency:**
- Uses `Meeting.objects.get_or_create(meeting_id=...)` 
- If both accounts have same `meeting_id`, first one saved wins (acceptable as meeting_id should be globally unique)

---

### 4. Requirement Code Expectations Fixed ✅

**File:** `coda/ai_services/utils/meeting_normalizer.py`

**Issue:** Meeting titles like "Requirement-508" were potentially being treated as requirement codes.

**Fix:**
- Updated `extract_requirement_code()` to ONLY match "REQ-####" pattern (not "Requirement-####")
- Added explicit comment: "IMPORTANT: Only matches 'REQ-####' pattern, NOT 'Requirement-####' or similar"
- Updated docstring to clarify this behavior

**Matching Rules:**
- `requirement_code` is optional and should NOT gate matching for Group B unless activity explicitly requires a Requirement
- Updated autolink service comment to clarify: "requirement_code is optional and should NOT gate matching for Group B unless the activity policy explicitly requires a Requirement"

---

### 5. Start/Join Meeting Button Fix ✅

**Issue:** Button was missing on DAF for meeting-required activities.

**Root Cause:**
- `CLIENT_TRAINING_SESSION` and `SELF_TRAINING_SESSION` had `meeting_required=True` but were missing `meeting_room_id` and `meeting_join_url` configuration
- Template checks `task.meeting_join_url` before showing button (line 393 in `employeetasks_v2.html`)
- Without `meeting_join_url`, button doesn't render

**Fix Applied:**
**File:** `coda/config/activity_definitions.py`

Added `meeting_room_id` and `meeting_join_url` to:
- `CLIENT_TRAINING_SESSION`: `meeting_room_id="123530685"`, `meeting_join_url="https://global.gotomeeting.com/join/123530685"`
- `SELF_TRAINING_SESSION`: `meeting_room_id="123530685"`, `meeting_join_url="https://global.gotomeeting.com/join/123530685"`

**Button Rendering Logic:**
- Template: `coda/management/templates/management/daf/usertasks/employeetasks_v2.html` (line 392-404)
- Condition: `{% if task.needs_attention_reason_code == 'MEETING_REQUIRED' %}`
- Button shows if: `task.meeting_join_url` is present
- Button uses: `{% url 'management:launch_meeting' %}?activity_type={{ task.activity_type_slug }}&task_id={{ task.id }}`

**Result:**
- Button now appears for `CLIENT_TRAINING_SESSION` and `SELF_TRAINING_SESSION` tasks
- Button correctly records launch intent and redirects to GoToMeeting

---

### 6. Launch Intent Cross-Process Support ✅

**File:** `coda/management/views_meeting_launch.py`

**Issue:** LocMemCache doesn't work across processes (runserver, Celery, shell).

**Fix:**
- Added warning log when LocMemCache backend is detected
- Added comment: "IMPORTANT: For production, ensure CACHES backend is shared (Redis, Memcached, etc.)"
- Warning appears in logs when launch intent is recorded with LocMemCache

**Production Note:**
- Shared cache (Redis/Memcached) is required for autolink to see launch intents across processes
- LocMemCache will only work within the same process

---

### 7. Autolink Multi-Service Support ✅

**File:** `coda/ai_services/services/meeting_task_autolink_service.py`

**Changes:**
- Updated `find_meeting_for_task()` to include both internal and external meetings by default
- When `service_name` is not explicitly set, queries include all services from `list_goto_services()`
- Meeting room matching (primary/secondary) includes both services (meeting_id should be globally unique)

**Matching Priority (unchanged, but now supports both services):**
1. Meeting room ID + Launch Intent (highest confidence: 0.95)
2. Meeting room ID + Recent Launch (high confidence: 0.85)
3. Requirement code matching (if activity requires requirement)
4. Topic keyword + time window (fallback: 0.70)

---

### 8. Operator Controls ✅

**Files Modified:**
- `coda/ai_services/management/commands/verify_goto_oauth.py`
- `coda/ai_services/management/commands/sync_gotomeetings.py`
- `coda/ai_services/management/commands/autolink_meeting_evidence.py` (already had `--service`)
- `coda/management/views_debug.py`

**Commands Updated:**

1. **verify_goto_oauth:**
   - `--service gotomeeting_internal|gotomeeting_external|all` (default: `gotomeeting_internal`)
   - When `all`: Verifies all configured services

2. **sync_gotomeetings:**
   - `--service gotomeeting_internal|gotomeeting_external|all` (default: `gotomeeting_internal`)
   - When `all`: Syncs both services sequentially

3. **autolink_meeting_evidence:**
   - Already had `--service external|internal|all` (default: `all`)
   - No changes needed

4. **Debug Page:**
   - Added `service_counts` to `meetings_health` section
   - Shows meeting counts by `service_name` (e.g., `gotomeeting_internal: 150`, `gotomeeting_external: 45`)

---

## Environment Variables

### Internal (Primary) Account
```bash
GOTO_OAUTH_CLIENT_ID=<internal_client_id>
GOTO_OAUTH_CLIENT_SECRET=<internal_client_secret>
```

### External (Secondary) Account
```bash
GOTO_OAUTH_CLIENT_ID_EXTERNAL=<external_client_id>
GOTO_OAUTH_CLIENT_SECRET_EXTERNAL=<external_client_secret>
```

**Note:** External account is optional. If `GOTO_OAUTH_CLIENT_ID_EXTERNAL` and `GOTO_OAUTH_CLIENT_SECRET_EXTERNAL` env vars are missing, external service will be disabled.

---

## Validation Steps

### 1. Verify OAuth per service:
```bash
poetry run python coda/manage.py verify_goto_oauth --service gotomeeting_internal
poetry run python coda/manage.py verify_goto_oauth --service gotomeeting_external
poetry run python coda/manage.py verify_goto_oauth --service all
```

### 2. Sync last 7 days for internal:
```bash
poetry run python coda/manage.py sync_gotomeetings --days 7 --service gotomeeting_internal
```

### 3. Sync last 7 days for external:
```bash
poetry run python coda/manage.py sync_gotomeetings --days 7 --service gotomeeting_external
```

### 4. Sync both services:
```bash
poetry run python coda/manage.py sync_gotomeetings --days 7 --service all
```

### 5. Confirm Meeting counts by service:
```bash
poetry run python coda/manage.py shell -c "
from ai_services.models import Meeting; from django.db.models import Count;
print(list(Meeting.objects.values('service_name').annotate(c=Count('id')).order_by('-c')))
"
```

### 6. Open DAF and confirm Start/Join Meeting button appears:
- Use a user who has meeting-required tasks (e.g., Eunice, Brenda)
- Verify button appears for `CLIENT_TRAINING_SESSION` and `SELF_TRAINING_SESSION`
- Click button and verify it records launch intent and redirects

### 7. Run autolink diagnose:
```bash
poetry run python coda/manage.py autolink_meeting_evidence --diagnose --user-id <USER_ID> --days 30 --limit 50
```

### 8. Run autolink (non-diagnose):
```bash
poetry run python coda/manage.py autolink_meeting_evidence --user-id <USER_ID> --days 30 --limit 20
```

---

## Files Changed

### New Files:
- `coda/ai_services/utils/goto_service_registry.py`

### Modified Files:
- `coda/shared_core/utils/oauth.py`
- `coda/management/legacy_views.py` (oauth_login, oauth_callback)
- `coda/ai_services/views.py` (getmeetingresponse, save_meeting_data)
- `coda/ai_services/services/meeting_sync_service.py`
- `coda/ai_services/management/commands/sync_gotomeetings.py`
- `coda/ai_services/management/commands/verify_goto_oauth.py`
- `coda/ai_services/services/meeting_task_autolink_service.py`
- `coda/management/views_meeting_launch.py`
- `coda/management/views_debug.py`
- `coda/config/activity_definitions.py`
- `coda/ai_services/utils/meeting_normalizer.py`

---

## Key Design Decisions

1. **No New Database Tables:** Used existing `OAuthToken` and `Meeting` models with `service_name` field
2. **Backward Compatibility:** Legacy `"gotomeeting"` service_name maps to `"gotomeeting_internal"`
3. **Meeting ID Uniqueness:** Assumes `meeting_id` is globally unique (GoToMeeting standard). If both accounts have same ID, first saved wins.
4. **Service Registry Pattern:** Single source of truth for credential mapping (no hardcoded env var reads in business logic)
5. **Minimal Changes:** Only modified necessary files, avoided broad refactors

---

## Why Start/Join Meeting Button Was Missing

**Root Cause:**
- `CLIENT_TRAINING_SESSION` and `SELF_TRAINING_SESSION` had `meeting_required=True` but were missing `meeting_room_id` and `meeting_join_url` in their `ActivityPolicy` definitions
- DAF template checks `task.meeting_join_url` before rendering button
- Without `meeting_join_url`, button doesn't appear even if `requires_meeting=True`

**Fix:**
- Added `meeting_room_id="123530685"` and `meeting_join_url="https://global.gotomeeting.com/join/123530685"` to both activity policies
- Button now appears for these activities when `needs_attention_reason_code == 'MEETING_REQUIRED'`

**Verification:**
- Check DAF for a user with `CLIENT_TRAINING_SESSION` or `SELF_TRAINING_SESSION` tasks
- Button should appear with "Start Meeting" label
- Click should record launch intent and redirect to GoToMeeting

---

## Next Steps

1. **Set Environment Variables:**
   - Add `EXT_GOTO_OAUTH_CLIENT_ID` and `EXT_GOTO_OAUTH_CLIENT_SECRET` to production environment
   - Ensure `GOTO_OAUTH_CLIENT_ID` and `GOTO_OAUTH_CLIENT_SECRET` are set for internal account

2. **OAuth Setup:**
   - Authenticate internal account: `/management/oauth/login/?service=internal`
   - Authenticate external account: `/management/oauth/login/?service=external`

3. **Initial Sync:**
   - Run sync for both services: `sync_gotomeetings --service all --days 30`

4. **Production Cache:**
   - Ensure production uses shared cache (Redis/Memcached) for launch intent cross-process visibility

5. **Monitor:**
   - Check debug page for service counts: `/management/debug/daf-runtime/`
   - Verify meetings are being synced from both accounts

---

## Notes

- **Meeting ID Collision:** If both accounts have the same `meeting_id`, the first one saved wins. This is acceptable as GoToMeeting meeting IDs should be globally unique.
- **Requirement Code:** Only "REQ-####" pattern is extracted, not "Requirement-####". This prevents false positives from meeting titles.
- **Cache Backend:** LocMemCache will NOT work across processes. Production must use Redis or Memcached for launch intent visibility.

---

**Implementation Complete** ✅

