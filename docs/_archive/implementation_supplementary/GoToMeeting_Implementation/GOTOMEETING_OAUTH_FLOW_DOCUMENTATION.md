# GoToMeeting OAuth Flow Documentation

**Date:** 2024-12-26  
**Purpose:** Document the existing OAuth authentication flow for GoToMeeting API access

---

## 1. OAuth Token Model and Helper

### Model: `OAuthToken`

**File:** `coda/ai_services/models.py` (lines 277-337)

**Fields:**
- `service_name` (CharField, max_length=50, default='gotomeeting', unique=True)
- `access_token` (TextField, encrypted)
- `refresh_token` (TextField, encrypted)
- `token_type` (CharField, default='Bearer')
- `expires_at` (DateTimeField)
- `scope` (TextField, blank=True)
- `is_valid` (BooleanField, default=True)
- `last_refreshed_at` (DateTimeField, nullable)
- `created_at` (DateTimeField, auto_now_add)
- `updated_at` (DateTimeField, auto_now)

**Database Table:** `oauth_token`

**Note:** There is also a `OAuthTokenManager` class in `coda/ai_services/services/token_encryption_service.py` that can store tokens in the database with encryption, but the **current active implementation uses Django cache** (see below).

### Helper Function: `get_access_token()`

**File:** `coda/shared_core/utils/oauth.py` (lines 181-196)

**Signature:**
```python
def get_access_token():
    """
    Retrieves a valid access token, refreshing it if necessary.
    
    Returns:
        str: Access token if available, None if refresh failed
    """
```

**Current Implementation:**
- Uses **Django cache** (not database) to store tokens
- Cache keys: `'api_access_token'` and `'api_refresh_token'`
- If access token not in cache, attempts to refresh using refresh token
- Returns `None` if no token available or refresh fails

**Warning Message Location:**
- `coda/shared_core/utils/oauth.py` line 139: `"No refresh token available - user needs to re-authenticate"`

**Error Message Location:**
- `coda/ai_services/management/commands/sync_gotomeetings.py` line 53: `"❌ No OAuth access token available. Please authenticate first via OAuth login."`

---

## 2. OAuth Login and Callback Views

### Login View: `oauth_login`

**File:** `coda/management/views.py` (lines 3153-3158)

**Function:**
```python
def oauth_login(request):
    """
    Redirects the user to the OAuth2 provider's authorization URL.
    """
    auth_url = get_authorization_url()
    return redirect(auth_url)
```

**Description:** Initiates OAuth flow by redirecting to GoToMeeting authorization URL

### Callback View: `oauth_callback`

**File:** `coda/management/views.py` (lines 3160-3178)

**Function:**
```python
def oauth_callback(request):
    """
    Handles the OAuth2 provider's callback with the authorization code.
    """
    auth_code = request.GET.get('code')
    state = request.GET.get('state')
    error = request.GET.get('error')

    if error:
        return HttpResponse(f"Error during authentication: {error}")

    if not auth_code:
        return HttpResponse("No authorization code provided.", status=400)

    success = exchange_code_for_tokens(auth_code)
    if success:
        return redirect('getdata:meetingFormView')  # Redirect to the main view after successful authentication
    else:
        return HttpResponse("Failed to obtain access token.", status=400)
```

**Description:** Handles OAuth callback, exchanges authorization code for tokens, stores in cache

---

## 3. URL Configuration

**File:** `coda/management/urls.py` (lines 165-166)

**URL Patterns:**
```python
path('oauth/login/', views.oauth_login, name='oauth_login'),
path('oauth/callback/', views.oauth_callback, name='oauth_callback'),
```

**Full URLs (assuming server runs on port 8080):**
- **Login URL:** `http://localhost:8080/management/oauth/login/`
- **Callback URL:** `http://localhost:8080/management/oauth/callback/`

**⚠️ IMPORTANT PORT MISMATCH:**
The `get_oauth_redirect_uri()` function in `coda/shared_core/utils/oauth.py` (line 51) returns:
```python
return "http://localhost:8000/management/oauth/callback/"
```

But you're running the server on port **8080**, not 8000. This will cause the OAuth callback to fail because GoToMeeting will redirect to port 8000, which won't be listening.

**Solution:** You need to either:
1. Run the server on port 8000: `poetry run python coda/manage.py runserver 8000`
2. Or update the redirect URI in GoToMeeting OAuth app settings to use port 8080
3. Or modify `get_oauth_redirect_uri()` to detect the port from settings

---

## 4. End-to-End Token Flow

### Step-by-Step Flow:

1. **User visits login URL:**
   - Opens `http://localhost:8080/management/oauth/login/` in browser
   - `oauth_login` view calls `get_authorization_url()`

2. **Authorization URL Construction:**
   - `get_authorization_url()` in `coda/shared_core/utils/oauth.py` (lines 58-74)
   - Builds URL: `https://authentication.logmeininc.com/oauth/authorize?client_id=...&response_type=code&redirect_uri=...&state=...`
   - Redirects user to GoToMeeting authorization page

3. **User authenticates with GoToMeeting:**
   - User logs in with GoToMeeting credentials
   - Grants permissions to CODA app
   - GoToMeeting redirects back to callback URL with `code` parameter

4. **Callback receives authorization code:**
   - `oauth_callback` view extracts `code` from `request.GET.get('code')`
   - Calls `exchange_code_for_tokens(auth_code)`

5. **Token Exchange:**
   - `exchange_code_for_tokens()` in `coda/shared_core/utils/oauth.py` (lines 77-125)
   - POSTs to `https://authentication.logmeininc.com/oauth/token` with:
     - `grant_type=authorization_code`
     - `code` (authorization code)
     - `redirect_uri` (must match what was sent in step 2)
   - Uses HTTP Basic Auth with `API_CLIENT_ID` and `API_CLIENT_SECRET`

6. **Token Storage:**
   - **Currently uses Django cache** (lines 114-115):
     ```python
     cache.set(TOKEN_CACHE_KEY, access_token, timeout=expires_in)
     cache.set(REFRESH_TOKEN_CACHE_KEY, refresh_token, timeout=86400)
     ```
   - **Note:** There is a database-backed `OAuthTokenManager` available, but it's not currently used by the OAuth flow

7. **Token Retrieval:**
   - `get_access_token()` checks cache for `'api_access_token'`
   - If missing, calls `refresh_access_token()` which:
     - Gets refresh token from cache
     - POSTs to token endpoint with `grant_type=refresh_token`
     - Updates cache with new access token
   - Returns access token string or `None`

---

## 5. Local Authentication Steps

### Prerequisites:
- Server running: `poetry run python coda/manage.py runserver 8080`
- Environment variables set: `API_CLIENT_ID` and `API_CLIENT_SECRET`
- GoToMeeting OAuth app configured with correct redirect URI

### ⚠️ CRITICAL: Port Mismatch Issue

The redirect URI in code is hardcoded to `http://localhost:8000/management/oauth/callback/`, but you're running on port 8080.

**Option A: Run on port 8000 (Easiest)**
```bash
poetry run python coda/manage.py runserver 8000
```

**Option B: Update redirect URI in GoToMeeting OAuth app settings**
- Go to GoToMeeting developer console
- Update redirect URI to: `http://localhost:8080/management/oauth/callback/`
- Also update `get_oauth_redirect_uri()` in `coda/shared_core/utils/oauth.py` line 51

### Step-by-Step Authentication:

1. **Start the server:**
   ```bash
   poetry run python coda/manage.py runserver 8000
   # OR if you fix the redirect URI:
   poetry run python coda/manage.py runserver 8080
   ```

2. **Open login URL in browser:**
   ```
   http://localhost:8000/management/oauth/login/
   # OR if using port 8080:
   http://localhost:8080/management/oauth/login/
   ```

3. **Complete GoToMeeting authentication:**
   - You'll be redirected to GoToMeeting login page
   - Enter your GoToMeeting credentials
   - Grant permissions to the CODA app
   - You'll be redirected back to the callback URL

4. **Verify successful authentication:**
   - You should be redirected to `getdata:meetingFormView` (meeting form page)
   - Check server logs for: `"✅ Successfully exchanged auth code for tokens"`

5. **Verify token in cache (Django shell):**
   ```python
   poetry run python coda/manage.py shell
   ```
   ```python
   from django.core.cache import cache
   access_token = cache.get('api_access_token')
   refresh_token = cache.get('api_refresh_token')
   print(f"Access token: {access_token[:20] if access_token else 'None'}...")
   print(f"Refresh token: {refresh_token[:20] if refresh_token else 'None'}...")
   ```

6. **Test meeting sync:**
   ```bash
   poetry run python coda/manage.py sync_gotomeetings --start 2024-12-01 --end 2024-12-31
   ```
   - Should no longer show "No OAuth access token available" error

---

## 6. Token Storage: Cache vs Database

### Current Implementation (Cache-Based):
- **Storage:** Django cache (in-memory or Redis, depending on `CACHES` setting)
- **Lifetime:** Access token expires based on `expires_in` from API, refresh token cached for 24 hours
- **Persistence:** **Tokens are lost on server restart** (unless using Redis with persistence)
- **Location:** `coda/shared_core/utils/oauth.py`

### Alternative Implementation (Database-Based):
- **Storage:** `OAuthToken` model in database (encrypted)
- **Location:** `coda/ai_services/services/token_encryption_service.py`
- **Status:** Code exists but **not currently used** by the OAuth flow
- **Advantage:** Tokens persist across server restarts

**To use database storage instead of cache:**
- Modify `exchange_code_for_tokens()` to call `save_tokens_to_db()` instead of `cache.set()`
- Modify `get_access_token()` to call `get_token_from_db()` instead of `cache.get()`

---

## 7. Environment Variables Required

Make sure these are set in your environment:
```bash
API_CLIENT_ID=<your_gotomeeting_client_id>
API_CLIENT_SECRET=<your_gotomeeting_client_secret>
```

Check if they're set:
```bash
poetry run python coda/manage.py shell
```
```python
import os
print(f"CLIENT_ID: {os.environ.get('API_CLIENT_ID', 'NOT SET')}")
print(f"CLIENT_SECRET: {os.environ.get('API_CLIENT_SECRET', 'NOT SET')}")
```

---

## Summary: Quick Authentication Checklist

1. ✅ **Fix port mismatch:** Either run on port 8000 OR update redirect URI in code and GoToMeeting app
2. ✅ **Start server:** `poetry run python coda/manage.py runserver 8000`
3. ✅ **Open login URL:** `http://localhost:8000/management/oauth/login/`
4. ✅ **Complete GoToMeeting auth:** Login and grant permissions
5. ✅ **Verify token:** Check cache or run sync command
6. ✅ **Test sync:** `poetry run python coda/manage.py sync_gotomeetings --start 2024-12-01 --end 2024-12-31`

---

**Note:** The current implementation uses cache, so tokens will be lost on server restart. For production, consider migrating to the database-backed `OAuthTokenManager` implementation.

