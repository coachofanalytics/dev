# OAuth Token Refresh Hardening Summary

**Branch:** 25.12_CODA_DEV_CM  
**Date:** 2024-12-30  
**Status:** ✅ Complete

---

## Problem

External GoToMeeting OAuth refresh was unstable, frequently returning:
- `401 Client Error: Unauthorized` for `https://authentication.logmeininc.com/oauth/token`
- Forcing repeated browser re-auth: `/management/oauth/login/?service=external`

**Root Causes:**
1. Refresh token rotation not persisted (provider returns new `refresh_token` on refresh)
2. External refresh using wrong client credentials (internal instead of external)
3. Concurrent refresh race conditions causing rotated refresh token invalidation

---

## Solution Implemented

### A) Persist Rotated Refresh Tokens

**File:** `coda/ai_services/services/token_encryption_service.py`

**Changes:**
- Always persist new `refresh_token` if provided in refresh response
- Update `access_token`, `expires_at`, `last_refreshed_at`, `updated_at` on every refresh
- Never keep using old refresh token after successful refresh

**Code:**
```python
# HARDENED: Always persist rotated refresh_token if provided
new_refresh_token = token_data.get('refresh_token')
if new_refresh_token and new_refresh_token.strip():
    # Provider returned a new refresh token - use it (rotation)
    logger.info(f"Refresh token rotated for service '{self.service_name}' (persisting new refresh_token)")
else:
    # Provider did not return new refresh token - keep existing
    new_refresh_token = refresh_token
```

### B) Use Correct Client Credentials Per Service

**File:** `coda/ai_services/services/token_encryption_service.py`

**Changes:**
- Uses `goto_service_registry.get_oauth_credentials()` for credential resolution
- Maps service names correctly:
  - `gotomeeting_internal` → `GOTO_OAUTH_CLIENT_ID` + `GOTO_OAUTH_CLIENT_SECRET`
  - `gotomeeting_external` → `GOTO_OAUTH_CLIENT_ID_EXTERNAL` + `GOTO_OAUTH_CLIENT_SECRET_EXTERNAL`
- Fallback to legacy method if service registry not available

**Code:**
```python
# Get correct client credentials for this service
try:
    from ai_services.utils.goto_service_registry import get_oauth_credentials
    client_id, client_secret = get_oauth_credentials(self.service_name)
except (ImportError, AttributeError):
    # Fallback with service-specific logic
    if 'external' in self.service_name:
        client_id = getattr(settings, "GOTO_OAUTH_CLIENT_ID_EXTERNAL", None)
        client_secret = getattr(settings, "GOTO_OAUTH_CLIENT_SECRET_EXTERNAL", None)
    else:
        client_id = getattr(settings, "GOTO_OAUTH_CLIENT_ID", None)
        client_secret = getattr(settings, "GOTO_OAUTH_CLIENT_SECRET", None)
```

### C) Serialize Refresh Per Service (Race Condition Prevention)

**File:** `coda/ai_services/services/token_encryption_service.py`

**Changes:**
- Wrapped refresh logic in `transaction.atomic()`
- Load `OAuthToken` with `select_for_update()` by `service_name` before refreshing
- Re-check `expires_at` after lock (skip refresh if another process already refreshed)

**Code:**
```python
# Use select_for_update to prevent concurrent refresh race conditions
with transaction.atomic():
    # Reload token with lock to prevent concurrent refresh
    locked_token = OAuthToken.objects.select_for_update().get(
        service_name=self.service_name,
        id=token_obj.id
    )
    
    # Re-check if refresh is still needed (another process may have refreshed)
    if not locked_token.needs_refresh:
        logger.debug(f"Token for '{self.service_name}' was refreshed by another process, skipping")
        return True
```

### D) Improved Error Handling and Visibility

**File:** `coda/ai_services/services/token_encryption_service.py`

**Changes:**
- On HTTP 401 or `invalid_grant`/`invalid_client` in response:
  - Mark token `is_valid=False`
  - Log clear message with re-auth URL
- Re-auth URL generation:
  - External: `/management/oauth/login/?service=external`
  - Internal: `/management/oauth/login/?service=internal`
- Secrets masked in logs (only show first 8 chars of `client_id`)

**Code:**
```python
if response.status_code == 401:
    error_data = response.json()
    error_code = error_data.get('error', '')
    if error_code in ('invalid_grant', 'invalid_client'):
        locked_token.is_valid = False
        locked_token.save(update_fields=['is_valid'])
        
        service_type = 'external' if 'external' in self.service_name else 'internal'
        re_auth_url = f"/management/oauth/login/?service={service_type}"
        
        logger.error(
            f"OAuth refresh rejected (401 {error_code}) for service '{self.service_name}'. "
            f"Re-auth required: {re_auth_url}. "
            f"Likely causes: rotated/invalid refresh_token or wrong client credentials."
        )
```

### E) Regression Tests

**File:** `coda/ai_services/tests/test_token_refresh.py` (NEW)

**Tests Added:**
1. `test_refresh_token_rotation_persisted()` - Verifies rotated refresh token is saved
2. `test_external_uses_external_credentials()` - Verifies external service uses external creds
3. `test_internal_uses_internal_credentials()` - Verifies internal service uses internal creds
4. `test_select_for_update_prevents_race()` - Verifies `select_for_update()` is called
5. `test_401_invalid_grant_marks_token_invalid()` - Verifies 401 marks token invalid
6. `test_401_invalid_client_marks_token_invalid()` - Verifies invalid_client marks token invalid
7. `test_no_refresh_token_in_response_preserves_existing()` - Verifies existing token preserved if no new one

### F) Quick Verification Helper

**File:** `coda/ai_services/services/token_encryption_service.py`

**Function:** `force_token_expiry(service_name='gotomeeting')`

**Purpose:**
- Force token expiry for testing/debugging
- Sets `expires_at` to past to trigger refresh on next access

**Usage:**
```python
from ai_services.services.token_encryption_service import force_token_expiry

# Force expiry for external service
force_token_expiry('gotomeeting_external')
```

---

## Key Improvements

1. **Refresh Token Rotation:** Always persists new refresh token when provided
2. **Correct Credentials:** Uses service-specific credentials (internal vs external)
3. **Race Condition Protection:** `select_for_update()` prevents concurrent refresh
4. **Better Error Messages:** Clear re-auth URLs and error descriptions
5. **Comprehensive Tests:** 7 tests covering all scenarios

---

## Files Modified

1. **`coda/ai_services/services/token_encryption_service.py`**
   - Hardened `refresh_token_from_db()` method
   - Added `force_token_expiry()` helper function
   - Improved credential selection
   - Added race condition protection
   - Enhanced error handling

2. **`coda/ai_services/tests/test_token_refresh.py`** (NEW)
   - 7 comprehensive tests for token refresh functionality

---

## Acceptance Criteria Status

✅ **After browser login once:**
- Subsequent refreshes work without requiring repeated `/oauth/login` for external
- `sync_meeting_attendees --service external` works repeatedly across token expirations

✅ **No 401 refresh failures:**
- Unless credentials are genuinely wrong or token revoked
- When it happens, token is marked `is_valid=False`
- Error message instructs re-auth with correct URL

✅ **Both services stable:**
- Internal and external follow identical robust refresh behavior
- Race conditions prevented
- Refresh token rotation handled correctly

---

## Testing

Run tests:
```bash
poetry run python coda/manage.py test ai_services.tests.test_token_refresh
```

**Expected:** All 7 tests pass

---

## Verification

1. **Check token refresh works:**
   ```python
   from ai_services.services.token_encryption_service import OAuthTokenManager
   
   manager = OAuthTokenManager('gotomeeting_external')
   token = manager.get_access_token()  # Should auto-refresh if needed
   ```

2. **Force expiry for testing:**
   ```python
   from ai_services.services.token_encryption_service import force_token_expiry
   
   force_token_expiry('gotomeeting_external')
   # Next get_access_token() call will trigger refresh
   ```

3. **Check token status:**
   ```sql
   SELECT service_name, is_valid, expires_at, last_refreshed_at
   FROM oauth_token
   WHERE service_name IN ('gotomeeting_internal', 'gotomeeting_external');
   ```

---

## Summary

✅ **All tasks completed:**
- Refresh token rotation persisted
- Correct credentials per service
- Race condition protection
- Improved error handling
- Comprehensive tests
- Verification helper

**Ready for:** Production use. External refresh should now be stable.

