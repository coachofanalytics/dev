# OAuth Token Exchange Diagnostics - Implementation Summary

**Date:** 2024-12-26  
**Status:** ✅ **COMPLETE**

---

## Summary

Added comprehensive diagnostic logging to the OAuth token exchange flow to help identify root causes of "Failed to obtain access token" errors. Created a management command for quick settings verification.

---

## Files Modified

### 1. `coda/shared_core/utils/oauth.py`

**Change:** Enhanced `exchange_code_for_tokens()` with detailed error logging

**Lines:** 116-218

**Key Changes:**
- Added detailed logging before `raise_for_status()` to capture HTTP error responses
- Logs include: HTTP status code, response body (truncated), redirect_uri, token_url, client_id, secret_last6
- Enhanced error logging in exception handlers with context information
- Improved credential validation logging

**Code Snippet:**
```python
# Log request details (safe - no secrets)
secret_last6 = client_secret[-6:] if client_secret and len(client_secret) >= 6 else '******'
logger.debug("OAuth token exchange request: token_url=%s, redirect_uri=%s, client_id=%s, secret_last6=%s",
             token_url, redirect_uri, client_id, secret_last6)

response = requests.post(token_url, headers=headers, data=data, auth=auth, timeout=10)

# Log response details before raising for status (capture error details)
if not response.ok:
    try:
        response_body = response.text[:500]  # Limit body length for logging
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
```

**Exception Handling:**
```python
except requests.exceptions.HTTPError as e:
    # This is raised by raise_for_status() for non-2xx responses
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
```

### 2. `coda/management/views.py`

**Change:** Improved error message in `oauth_callback()` when token exchange fails

**Lines:** 3201-3206

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

**Purpose:** Management command to quickly verify OAuth settings configuration

**Usage:**
```bash
poetry run python coda/manage.py check_oauth_settings
```

**Output:**
- Client ID (full value)
- Client Secret (masked, shows last 6 characters)
- Redirect URI
- Token URL
- Auth URL
- Configuration warnings if any settings are missing

---

## Diagnostic Logging Details

### Log Levels

**DEBUG:** Request details (before API call)
- token_url
- redirect_uri
- client_id
- secret_last6

**ERROR:** Failure details (non-2xx responses)
- HTTP status code
- Response body (first 500 chars)
- redirect_uri used
- token_url used
- client_id
- secret_last6

**INFO:** Success confirmation
- Includes token_url, redirect_uri, client_id for correlation

### Security Considerations

- ✅ Never logs full `client_secret` - only last 6 characters
- ✅ Never logs full `auth_code` - only response status/body
- ✅ Response body truncated to 500 characters to prevent log bloat
- ✅ All sensitive values masked appropriately

---

## Verification Commands

### 1. Check OAuth Settings
```bash
poetry run python coda/manage.py check_oauth_settings
```

**Expected Output:**
```
============================================================
GoToMeeting OAuth Settings Configuration
============================================================
✓ Client ID: <your-client-id>
✓ Client Secret: ****************<last6>
✓ Redirect URI: http://localhost:8000/management/oauth/callback/
✓ Token URL: https://authentication.logmeininc.com/oauth/token
✓ Auth URL: https://authentication.logmeininc.com/oauth/authorize
============================================================
```

### 2. Verify Tokens in Cache (After Successful Login)

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

### 3. Start Server and Test OAuth Flow

```bash
# Start server on port 8000
poetry run python coda/manage.py runserver 8000

# Then in browser:
# 1. Visit: http://localhost:8000/management/oauth/login/
# 2. Complete GoToMeeting login/consent
# 3. Check server logs for:
#    - "OAuth token exchange failed: HTTP XXX" (if error)
#    - "✅ Successfully exchanged auth code for tokens" (if success)
```

---

## Root Cause Diagnosis Guide

Based on the HTTP status code and error body in logs:

### HTTP 401 (Unauthorized)
**Likely Causes:**
- Wrong `client_secret`
- Wrong `client_id`
- Client credentials invalid/revoked

**Actions:**
1. Verify `GOTO_OAUTH_CLIENT_SECRET` matches GoToMeeting OAuth app
2. Verify `GOTO_OAUTH_CLIENT_ID` matches GoToMeeting OAuth app
3. Check GoToMeeting developer console to confirm credentials are active

### HTTP 400 with `invalid_grant`
**Likely Causes:**
- `redirect_uri` mismatch (most common)
- Authorization code expired
- Authorization code already used

**Actions:**
1. Check log for `redirect_uri=` value
2. Verify GoToMeeting OAuth app has EXACT redirect URI:
   - Must match exactly: `http://localhost:8000/management/oauth/callback/`
   - Check: host, port, path, trailing slash
3. If mismatch found, update GoToMeeting OAuth app settings OR update `GOTO_OAUTH_REDIRECT_URI` in settings

### HTTP 400 with other error
**Check error body in logs** for specific GoToMeeting error message

### HTTP 500/503
**Likely Causes:**
- GoToMeeting API temporarily unavailable
- Network issues

**Actions:**
- Retry after a few minutes
- Check GoToMeeting status page

---

## Expected Log Output Examples

### Successful Exchange
```
INFO ✅ Successfully exchanged auth code for tokens: token_url=https://authentication.logmeininc.com/oauth/token, redirect_uri=http://localhost:8000/management/oauth/callback/, client_id=<client-id>
```

### Failed Exchange (HTTP 400 - invalid_grant)
```
ERROR OAuth token exchange failed: HTTP 400, body={"error":"invalid_grant","error_description":"The authorization code has expired or is invalid."}, redirect_uri=http://localhost:8000/management/oauth/callback/, token_url=https://authentication.logmeininc.com/oauth/token, client_id=<client-id>, secret_last6=XXXXXX
```

### Failed Exchange (HTTP 401 - Unauthorized)
```
ERROR OAuth token exchange HTTP error 401: status=401, body={"error":"invalid_client","error_description":"Client authentication failed."}, redirect_uri=http://localhost:8000/management/oauth/callback/, token_url=https://authentication.logmeininc.com/oauth/token, client_id=<client-id>, secret_last6=XXXXXX
```

### Missing Credentials
```
ERROR OAuth credentials not configured in settings: client_id=None, secret_present=False
```

---

## Next Steps for Diagnosis

1. **Run settings check:**
   ```bash
   poetry run python coda/manage.py check_oauth_settings
   ```
   Verify all required settings are present.

2. **Start server and attempt OAuth flow:**
   ```bash
   poetry run python coda/manage.py runserver 8000
   ```
   Visit `/management/oauth/login/` and complete flow.

3. **Check server logs for error message:**
   Look for log line starting with `ERROR OAuth token exchange failed:` or `ERROR OAuth token exchange HTTP error`

4. **Match error to root cause:**
   - HTTP 401 → Check client credentials
   - HTTP 400 + `invalid_grant` → Check redirect_uri match
   - HTTP 400 + other → Check error body for specific message

5. **Fix and retry:**
   - Update settings/environment variables as needed
   - Restart server
   - Retry OAuth flow

---

## Files Modified Summary

1. ✅ `coda/shared_core/utils/oauth.py` - Enhanced error logging
2. ✅ `coda/management/views.py` - Improved error message
3. ✅ `coda/management/management/commands/check_oauth_settings.py` - New diagnostic command

All changes are minimal, safe, and production-ready.

