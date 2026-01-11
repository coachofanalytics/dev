# OAuth Token Refresh Fix Summary

**Branch:** 25.12_CODA_DEV_CM  
**Date:** 2024-12-29  
**Status:** ✅ Fixes applied

---

## Problem

GoToMeeting external token refresh fails with 401 and then the system reports "No refresh token available", causing sync to skip. The system was losing stored refresh_tokens and had poor failure handling.

---

## Fixes Applied

### ✅ TASK 1: Preserve refresh_token if response doesn't include new one

**Files:**
- `coda/shared_core/utils/oauth.py` (function: `refresh_access_token`)
- `coda/ai_services/services/token_encryption_service.py` (method: `refresh_token_from_db`)

**Changes:**
- **Before:** `new_refresh_token = token_data.get('refresh_token', refresh_token)` - Always used existing as fallback
- **After:** Only update `refresh_token` if response explicitly returns a non-empty `refresh_token`
- If response doesn't include `refresh_token` or it's empty, preserve the existing one
- Added debug logging to indicate when refresh_token is preserved vs updated

**Code Location:**
- `oauth.py` lines 347-356
- `token_encryption_service.py` lines 291-300

---

### ✅ TASK 2: Handle 401 errors gracefully

**Files:**
- `coda/shared_core/utils/oauth.py` (function: `refresh_access_token`)
- `coda/ai_services/services/token_encryption_service.py` (method: `refresh_token_from_db`)

**Changes:**
1. **Catch HTTPError specifically:**
   - Check for `response.status_code == 401`
   - Mark `OAuthToken.is_valid = False`
   - Log clear re-auth message with URL

2. **Improved error messages:**
   - Log: `"OAuth refresh failed (401) for '<service>'. Re-auth required: /management/oauth/login/?service=<type>"`
   - Determine service type (`external` vs `internal`) for correct re-auth URL

3. **Avoid misleading "No refresh token" messages:**
   - In `refresh_access_token`, check if token exists but is invalid
   - If invalid, log: `"OAuth token is invalid for service '<service>'. Re-auth required: <url>"`
   - Only log "No refresh token" if token truly doesn't exist

**Code Location:**
- `oauth.py` lines 363-384 (HTTPError handling)
- `oauth.py` lines 318-333 (refresh_token check with invalid token detection)
- `token_encryption_service.py` lines 301-320 (HTTPError handling)

---

### ✅ TASK 3: Update verify_goto_oauth for operator-friendly output

**File:** `coda/ai_services/management/commands/verify_goto_oauth.py`

**Changes:**
1. **Check token status before attempting acquisition:**
   - Query `OAuthToken` to check if token exists and is valid
   - Determine service type for re-auth URL

2. **Enhanced failure messages:**
   - If no token: `"No token found for service '<service>'"` + re-auth URL
   - If token invalid: `"Token exists but is marked as invalid"` + re-auth URL
   - Always show re-auth URL: `/management/oauth/login/?service=<type>`

**Code Location:**
- `verify_goto_oauth.py` lines 65-91

---

## Files Modified

1. **`coda/shared_core/utils/oauth.py`**
   - Lines 318-333: Improved refresh_token check with invalid token detection
   - Lines 343-384: Enhanced error handling with 401-specific logic and refresh_token preservation

2. **`coda/ai_services/services/token_encryption_service.py`**
   - Lines 291-300: Refresh_token preservation logic
   - Lines 301-320: Enhanced HTTPError handling with 401-specific logic

3. **`coda/ai_services/management/commands/verify_goto_oauth.py`**
   - Lines 65-91: Operator-friendly output with re-auth URLs

---

## Verification

### 1) Django Check
```bash
poetry run python coda/manage.py check
```

**Expected:** ✅ No errors

---

### 2) Verify OAuth Command
```bash
poetry run python coda/manage.py verify_goto_oauth --service gotomeeting_external
```

**Expected Output (if token missing/invalid):**
```
Service: gotomeeting_external

Attempting token acquisition...
❌ Token acquisition FAILED
   No token found for service 'gotomeeting_external'
   Re-authenticate at: /management/oauth/login/?service=external
```

**Expected Output (if token valid):**
```
Service: gotomeeting_external

Attempting token acquisition...
✅ Token acquisition OK (refreshed=no)
   Expires at: 2024-12-30 10:00:00+00:00
   Token length: 1234 characters (not displayed for security)
```

---

## Summary

**Fixes:** 3/3 complete  
**Status:** Ready for testing  
**Breaking Changes:** None  
**Backward Compatible:** Yes

**Key Improvements:**
- ✅ Refresh tokens are preserved if API doesn't return new one
- ✅ 401 errors are handled gracefully with clear re-auth instructions
- ✅ Token invalidation is properly tracked
- ✅ Operator-friendly error messages with re-auth URLs


