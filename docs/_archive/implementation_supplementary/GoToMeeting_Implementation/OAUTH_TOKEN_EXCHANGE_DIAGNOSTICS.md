# OAuth Token Exchange Diagnostics - Implementation Complete

**Date:** 2024-12-26  
**Status:** ✅ **COMPLETE**

---

## Summary

Added comprehensive diagnostic logging to the OAuth token exchange flow to identify root causes of "Failed to obtain access token" errors. The implementation includes:

1. ✅ Enhanced error logging in `exchange_code_for_tokens()`
2. ✅ Improved error message in `oauth_callback()` view
3. ✅ New management command for settings verification

---

## Files Modified

### 1. `coda/shared_core/utils/oauth.py`

**Changes:** Enhanced `exchange_code_for_tokens()` with diagnostic logging

**Key Features:**
- Logs request details before API call (DEBUG level)
- Logs error details for non-2xx responses BEFORE `raise_for_status()` (captures error body)
- Enhanced exception handlers with context information
- Masks sensitive data (only logs last 6 chars of secret)

**Exact Code Changes:**

```python
# Lines 131-135: Enhanced credential validation logging
if not client_id or not client_secret:
    logger.error("OAuth credentials not configured in settings: client_id=%s, secret_present=%s", 
                 client_id[:8] + '...' if client_id else 'None', 
                 bool(client_secret))
    return False

# Lines 154-157: Request details logging (DEBUG)
secret_last6 = client_secret[-6:] if client_secret and len(client_secret) >= 6 else '******'
logger.debug("OAuth token exchange request: token_url=%s, redirect_uri=%s, client_id=%s, secret_last6=%s",
             token_url, redirect_uri, client_id, secret_last6)

# Lines 160-177: Error logging BEFORE raise_for_status()
response = requests.post(token_url, headers=headers, data=data, auth=auth, timeout=10)

if not response.ok:
    try:
        response_body = response.text[:500]  # Limit body length
    except:
        response_body = "<unable to read response body>"
    
    logger.error(
        "OAuth token exchange failed: HTTP %d, body=%s, redirect_uri=%s, token_url=%s, client_id=%s, secret_last6=%s",
        response.status_code,
        response_body,
        redirect_uri,
        token_url,
        client_id,
        secret_last6
    )

response.raise_for_status()

# Lines 199-217: Enhanced HTTPError handler
except requests.exceptions.HTTPError as e:
    try:
        response_body = e.response.text[:500] if e.response else "<no response body>"
    except:
        response_body = "<unable to read response body>"
    
    logger.error(
        "OAuth token exchange HTTP error %d: status=%d, body=%s, redirect_uri=%s, token_url=%s, client_id=%s, secret_last6=%s",
        e.response.status_code if e.response else 0,
        e.response.status_code if e.response else 0,
        response_body,
        redirect_uri,
        token_url,
        client_id,
        secret_last6,
        exc_info=True
    )
    return False

# Lines 187-189: Enhanced missing tokens logging
if not access_token or not refresh_token:
    logger.error("OAuth response missing tokens: has_access_token=%s, has_refresh_token=%s",
                 bool(access_token), bool(refresh_token))
    return False

# Lines 195-197: Success logging with context
logger.info("✅ Successfully exchanged auth code for tokens: token_url=%s, redirect_uri=%s, client_id=%s",
            token_url, redirect_uri, client_id)
```

### 2. `coda/management/views.py`

**Change:** Improved error message in `oauth_callback()`

**Lines:** 3201-3207

**Code Change:**
```python
# Before:
success = exchange_code_for_tokens(auth_code)
if success:
    return redirect('getdata:meetingFormView')
else:
    return HttpResponse("Failed to obtain access token.", status=400)

# After:
success = exchange_code_for_tokens(auth_code)
if success:
    return redirect('getdata:meetingFormView')
else:
    # Token exchange failed - check server logs for detailed error
    logger.error("OAuth callback: token exchange returned False. Check logs above for HTTP status/body details.")
    return HttpResponse(
        "Failed to obtain access token. Check server logs for OAuth exchange failure details.",
        status=400
    )
```

### 3. `coda/management/management/commands/check_oauth_settings.py` (NEW FILE)

**Purpose:** Quick verification of OAuth settings configuration

**Full Code:** See file contents above

---

## Diagnostic Commands

### Command 1: Check OAuth Settings Configuration

```bash
poetry run python coda/manage.py check_oauth_settings
```

**Output Example:**
```
============================================================
GoToMeeting OAuth Settings Configuration
============================================================
✓ Client ID: 2c0844ca-b4e2-4c4e-887f-393bb69bed59
✓ Client Secret: ****************XXXXXX
✓ Redirect URI: http://localhost:8000/management/oauth/callback/
✓ Token URL: https://authentication.logmeininc.com/oauth/token
✓ Auth URL: https://authentication.logmeininc.com/oauth/authorize
============================================================

✓ All required settings are configured

Note: Ensure the redirect URI in GoToMeeting OAuth app settings
      matches exactly (including port and trailing slash):
      http://localhost:8000/management/oauth/callback/
```

### Command 2: Verify Tokens in Cache (After Successful Login)

```bash
poetry run python coda/manage.py shell -c "
from django.core.cache import cache
from shared_core.utils.oauth import TOKEN_CACHE_KEY, REFRESH_TOKEN_CACHE_KEY

access_token = cache.get(TOKEN_CACHE_KEY)
refresh_token = cache.get(REFRESH_TOKEN_CACHE_KEY)

print('Access token present:', bool(access_token))
print('Refresh token present:', bool(refresh_token))
if access_token:
    print('Access token (first 20 chars):', access_token[:20] + '...')
if refresh_token:
    print('Refresh token (first 20 chars):', refresh_token[:20] + '...')
"
```

**Expected Output (After Successful OAuth):**
```
Access token present: True
Refresh token present: True
Access token (first 20 chars): eyJhbGciOiJSUzI1NiI...
Refresh token (first 20 chars): eyJhbGciOiJSUzI1NiI...
```

**Expected Output (Before OAuth / After Failure):**
```
Access token present: False
Refresh token present: False
```

### Command 3: Django Health Check

```bash
poetry run python coda/manage.py check
```

**Expected:** `System check identified no issues (0 silenced).`

---

## OAuth Flow Testing Steps

### Step 1: Verify Settings

```bash
poetry run python coda/manage.py check_oauth_settings
```

Verify:
- ✅ Client ID is set
- ✅ Client Secret is set (shows last 6 chars)
- ✅ Redirect URI matches GoToMeeting OAuth app settings EXACTLY

### Step 2: Start Server

```bash
poetry run python coda/manage.py runserver 8000
```

**Important:** Server must run on port 8000 (or update `GOTO_OAUTH_REDIRECT_URI` to match your port)

### Step 3: Initiate OAuth Flow

1. Open browser to: `http://localhost:8000/management/oauth/login/`
2. You'll be redirected to GoToMeeting authorization page
3. Complete login and consent
4. You'll be redirected back to `/management/oauth/callback/`

### Step 4: Check Server Logs

**Look for one of these log lines:**

**Success:**
```
INFO ✅ Successfully exchanged auth code for tokens: token_url=https://authentication.logmeininc.com/oauth/token, redirect_uri=http://localhost:8000/management/oauth/callback/, client_id=<client-id>
```

**Failure - HTTP 400 (invalid_grant):**
```
ERROR OAuth token exchange failed: HTTP 400, body={"error":"invalid_grant","error_description":"The authorization code has expired or is invalid."}, redirect_uri=http://localhost:8000/management/oauth/callback/, token_url=https://authentication.logmeininc.com/oauth/token, client_id=<client-id>, secret_last6=XXXXXX
```

**Failure - HTTP 401 (Unauthorized):**
```
ERROR OAuth token exchange HTTP error 401: status=401, body={"error":"invalid_client","error_description":"Client authentication failed."}, redirect_uri=http://localhost:8000/management/oauth/callback/, token_url=https://authentication.logmeininc.com/oauth/token, client_id=<client-id>, secret_last6=XXXXXX
```

### Step 5: Verify Tokens Cached

```bash
poetry run python coda/manage.py shell -c "
from django.core.cache import cache
from shared_core.utils.oauth import TOKEN_CACHE_KEY, REFRESH_TOKEN_CACHE_KEY
print('Has access token:', bool(cache.get(TOKEN_CACHE_KEY)))
print('Has refresh token:', bool(cache.get(REFRESH_TOKEN_CACHE_KEY)))
"
```

---

## Root Cause Diagnosis Guide

### HTTP 401 (Unauthorized)

**Error Body:** `{"error":"invalid_client","error_description":"Client authentication failed."}`

**Root Causes:**
1. Wrong `client_secret` in settings
2. Wrong `client_id` in settings
3. Client credentials revoked in GoToMeeting

**Fix:**
1. Run `check_oauth_settings` to verify current values
2. Verify `GOTO_OAUTH_CLIENT_ID` and `GOTO_OAUTH_CLIENT_SECRET` match GoToMeeting OAuth app
3. Check GoToMeeting developer console to confirm credentials are active
4. Update environment variables and restart server

---

### HTTP 400 with `invalid_grant`

**Error Body:** `{"error":"invalid_grant","error_description":"..."}`

**Root Causes:**
1. **Redirect URI mismatch** (most common) - `redirect_uri` in token request doesn't match GoToMeeting OAuth app settings
2. Authorization code expired (codes expire quickly, usually within minutes)
3. Authorization code already used (codes are single-use)

**Fix for Redirect URI Mismatch:**
1. Check log line for `redirect_uri=` value
2. Verify GoToMeeting OAuth app has EXACT redirect URI:
   - Must match exactly: `http://localhost:8000/management/oauth/callback/`
   - Check: protocol (http/https), host (localhost), port (8000), path, trailing slash
3. If mismatch:
   - **Option A:** Update GoToMeeting OAuth app redirect URI to match settings
   - **Option B:** Update `GOTO_OAUTH_REDIRECT_URI` in settings/environment to match GoToMeeting app
4. Restart server and retry

**Fix for Expired/Used Code:**
- Codes expire quickly - simply retry the OAuth flow from `/management/oauth/login/`
- Each login generates a new authorization code

---

### HTTP 400 with Other Error

**Check error body in logs** for specific GoToMeeting error message and follow their guidance.

---

### HTTP 500/503

**Root Cause:** GoToMeeting API temporarily unavailable or network issues

**Fix:**
- Wait a few minutes and retry
- Check GoToMeeting status page
- Verify network connectivity

---

## Expected Log Output Examples

### Successful Token Exchange

```
DEBUG OAuth token exchange request: token_url=https://authentication.logmeininc.com/oauth/token, redirect_uri=http://localhost:8000/management/oauth/callback/, client_id=2c0844ca-b4e2-4c4e-887f-393bb69bed59, secret_last6=XXXXXX
INFO ✅ Successfully exchanged auth code for tokens: token_url=https://authentication.logmeininc.com/oauth/token, redirect_uri=http://localhost:8000/management/oauth/callback/, client_id=2c0844ca-b4e2-4c4e-887f-393bb69bed59
```

### Failed Token Exchange - Redirect URI Mismatch

```
ERROR OAuth token exchange failed: HTTP 400, body={"error":"invalid_grant","error_description":"The redirect_uri does not match the redirect_uri from the authorization request."}, redirect_uri=http://localhost:8000/management/oauth/callback/, token_url=https://authentication.logmeininc.com/oauth/token, client_id=2c0844ca-b4e2-4c4e-887f-393bb69bed59, secret_last6=XXXXXX
ERROR OAuth callback: token exchange returned False. Check logs above for HTTP status/body details.
```

**Action:** Verify `redirect_uri` in log matches GoToMeeting OAuth app settings EXACTLY.

### Failed Token Exchange - Wrong Credentials

```
ERROR OAuth token exchange HTTP error 401: status=401, body={"error":"invalid_client","error_description":"Client authentication failed."}, redirect_uri=http://localhost:8000/management/oauth/callback/, token_url=https://authentication.logmeininc.com/oauth/token, client_id=2c0844ca-b4e2-4c4e-887f-393bb69bed59, secret_last6=XXXXXX
ERROR OAuth callback: token exchange returned False. Check logs above for HTTP status/body details.
```

**Action:** Verify `client_id` and `client_secret` are correct in settings.

### Missing Credentials

```
ERROR OAuth credentials not configured in settings: client_id=None, secret_present=False
ERROR OAuth callback: token exchange returned False. Check logs above for HTTP status/body details.
```

**Action:** Set `GOTO_OAUTH_CLIENT_ID` and `GOTO_OAUTH_CLIENT_SECRET` environment variables.

---

## Summary

### Changes Made

1. ✅ **Enhanced Error Logging:** `exchange_code_for_tokens()` now logs detailed error information including HTTP status, response body, redirect_uri, token_url, and masked credentials
2. ✅ **Improved Error Message:** `oauth_callback()` view now provides clearer guidance to check server logs
3. ✅ **Settings Verification Command:** New `check_oauth_settings` command for quick configuration verification

### Security

- ✅ Never logs full `client_secret` - only last 6 characters
- ✅ Never logs `auth_code` - only response status/body
- ✅ Response body truncated to 500 characters
- ✅ All sensitive values masked appropriately

### Next Steps

1. Run `check_oauth_settings` to verify configuration
2. Start server and attempt OAuth flow
3. Check server logs for detailed error messages
4. Match error to root cause using diagnosis guide above
5. Fix configuration and retry

All changes are minimal, safe, and production-ready.

