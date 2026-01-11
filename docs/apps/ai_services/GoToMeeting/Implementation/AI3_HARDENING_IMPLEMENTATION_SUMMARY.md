# AI-3 Hardening + OAuth Telemetry Implementation Summary

**Branch:** 25.12_CODA_DEV_CM  
**Date:** 2024-12-30  
**Status:** ✅ Complete

---

## Overview

This implementation addresses three main areas:
1. **TASK A**: Fix external session_id persistence + safe backfill
2. **TASK B**: AI-3 service-fallback aware suggestions (internal → external → both)
3. **TASK C**: OAuth token telemetry + dashboard buttons for both services

---

## TASK A — Fix external session_id persistence + safe backfill

### Changes Made

1. **Verified session_id persistence** (already working):
   - `coda/ai_services/services/goto_meeting_sync_service.py`: Extracts `sessionId` from API response (line 68)
   - `coda/ai_services/views.py`: Extracts and persists `session_id` on create (line 581) and update (lines 591-593)
   - Both `gotomeeting_internal` and `gotomeeting_external` use the same persistence logic

2. **Enhanced backfill command**:
   - `coda/ai_services/management/commands/backfill_meeting_instance_keys.py`:
     - Focuses on `session_id` backfill (line 114: filters for `session_id__isnull=True` or empty)
     - Matches API meetings to DB by `meeting_id` + `start_time` ± tolerance
     - Updates `session_id` from API response
     - Skips ambiguous matches unless `--force` is provided

3. **Tests added**:
   - `coda/ai_services/tests/test_session_id_persistence.py`:
     - `test_external_meeting_sync_persists_session_id`: Verifies external meetings persist session_id
     - `test_internal_meeting_sync_persists_session_id`: Verifies internal meetings persist session_id
     - `test_session_id_update_on_existing_meeting`: Verifies session_id updates on existing meetings

### Verification

```bash
# Backfill session IDs for external
poetry run python coda/manage.py backfill_meeting_instance_keys \
  --service external \
  --days 260 \
  --verbose

# Verify
poetry run python coda/manage.py shell
>>> from ai_services.models import Meeting
>>> external = Meeting.objects.filter(service_name="gotomeeting_external")
>>> missing = external.filter(session_id__isnull=True) | external.filter(session_id='')
>>> print(f"Missing session_id: {missing.count()}")  # Should be 0 after backfill
```

---

## TASK B — AI-3 service-fallback aware suggestions

### Changes Made

1. **Added `--fallback-services` flag** (default: True):
   - `coda/ai_services/management/commands/generate_task_meeting_suggestions.py`:
     - New flag: `--fallback-services` (default True)
     - New flag: `--no-fallback-services` (disables fallback)
     - Logic:
       - If primary service has no candidates above `min_review_confidence`, automatically retry with fallback service
       - If still none, logs cleanly (both services already tried)
       - Marks candidates with `service_source` and `fallback_used` flags

2. **Enhanced signals_json**:
   - Adds `service_scope:{internal|external|both}` to signals
   - Adds `fallback_used` flag when fallback is used
   - Includes in `explanation` text

3. **Tests added**:
   - `coda/ai_services/tests/test_task_meeting_link_suggestions.py`:
     - `ServiceFallbackAwareTest.test_fallback_finds_external_when_internal_empty`: Verifies fallback works
     - `ServiceFallbackAwareTest.test_no_fallback_when_disabled`: Verifies fallback can be disabled

### Verification

```bash
# Run with fallback (default)
poetry run python coda/manage.py generate_task_meeting_suggestions \
  --task-id 230 \
  --days 260 \
  --service internal \
  --fallback-services \
  --verbose

# Check suggestion signals_json includes service_scope and fallback_used
poetry run python coda/manage.py shell
>>> from ai_services.models import TaskMeetingLinkSuggestion
>>> suggestion = TaskMeetingLinkSuggestion.objects.filter(task_id=230).first()
>>> print(suggestion.signals_json.get('service_scope'))
>>> print(suggestion.signals_json.get('fallback_used'))
```

---

## TASK C — OAuth token telemetry + dashboard buttons

### Changes Made

1. **Added telemetry fields to OAuthToken model**:
   - `coda/ai_services/models.py`:
     - `last_refresh_attempt_at` (DateTimeField, null=True, indexed)
     - `last_refresh_status` (CharField, choices: SUCCESS/FAILED, null=True)
     - `last_refresh_error` (TextField, null=True, blank=True, sanitized)
   - Migration: `coda/ai_services/migrations/0006_add_oauth_token_telemetry.py`

2. **Updated token refresh logic**:
   - `coda/ai_services/services/token_encryption_service.py`:
     - Sets `last_refresh_attempt_at` at start of refresh attempt
     - On success: `last_refresh_status='SUCCESS'`, `last_refresh_error=None`
     - On failure: `last_refresh_status='FAILED'`, `last_refresh_error=sanitized_error`
     - Error sanitization: Removes secrets, limits length, includes HTTP status codes

3. **Updated dashboard UI**:
   - `coda/unified_dashboard/views.py`: Includes telemetry fields in `get_goto_ops_data()`
   - `coda/unified_dashboard/templates/unified_dashboard/dashboard.html`:
     - Displays `last_refresh_attempt_at`
     - Displays `last_refresh_status` with badge (SUCCESS=green, FAILED=red)
     - Displays `last_refresh_error` (truncated, sanitized)
     - Refresh and Re-auth buttons already exist for both services

4. **Tests added**:
   - `coda/ai_services/tests/test_oauth_token_telemetry.py`:
     - `test_refresh_success_sets_telemetry`: Verifies success telemetry
     - `test_refresh_failure_sets_telemetry`: Verifies failure telemetry with sanitized error

### Verification

1. **Check telemetry fields exist**:
   ```bash
   poetry run python coda/manage.py shell
   >>> from ai_services.models import OAuthToken
   >>> token = OAuthToken.objects.get(service_name='gotomeeting_external')
   >>> hasattr(token, 'last_refresh_attempt_at')
   True
   ```

2. **Trigger refresh and verify telemetry**:
   - Navigate to `/dashboard/` as staff user
   - Click "Attempt Refresh Now" for external service
   - Verify telemetry updates immediately:
     - `last_refresh_attempt_at` shows current timestamp
     - `last_refresh_status` shows SUCCESS or FAILED badge
     - `last_refresh_error` shows sanitized error (if failed)

---

## Files Modified

### Models
- `coda/ai_services/models.py`: Added OAuthToken telemetry fields

### Services
- `coda/ai_services/services/token_encryption_service.py`: Updated refresh logic to set telemetry
- `coda/ai_services/management/commands/backfill_meeting_instance_keys.py`: Focused on session_id backfill
- `coda/ai_services/management/commands/generate_task_meeting_suggestions.py`: Added fallback logic

### Views/Templates
- `coda/unified_dashboard/views.py`: Added telemetry to `get_goto_ops_data()`
- `coda/unified_dashboard/templates/unified_dashboard/dashboard.html`: Display telemetry fields

### Tests
- `coda/ai_services/tests/test_session_id_persistence.py`: New test file
- `coda/ai_services/tests/test_oauth_token_telemetry.py`: New test file
- `coda/ai_services/tests/test_task_meeting_link_suggestions.py`: Added fallback tests

### Migrations
- `coda/ai_services/migrations/0006_add_oauth_token_telemetry.py`: New migration

---

## Acceptance Criteria

✅ **TASK A**:
- External meeting sync persists session_id when API includes it
- Backfill command updates session_id for missing records
- Backfill skips ambiguous matches by default
- Tests pass

✅ **TASK B**:
- `--fallback-services` flag added (default: True)
- Fallback logic: internal → external → both
- `signals_json` includes `service_scope` and `fallback_used`
- `explanation` mentions fallback attempt path
- Tests pass

✅ **TASK C**:
- OAuthToken telemetry fields added
- Token refresh sets telemetry (attempt_at, status, error)
- Dashboard displays telemetry for both services
- Refresh and Re-auth buttons work for both services
- No secrets displayed or stored
- Tests pass

---

## Runbook

See `AI3_HARDENING_RUNBOOK.md` for detailed commands and troubleshooting.

---

## Summary

All three tasks completed successfully:
- ✅ Session_id persistence verified and backfill command enhanced
- ✅ AI-3 fallback logic implemented with proper logging and signals
- ✅ OAuth telemetry added with dashboard integration
- ✅ Tests added for all new functionality
- ✅ No secrets exposed in UI or logs

**Ready for:** Testing and production use.

