# GoToMeeting OAuth Configuration Refactor - Audit Report

**Date:** 2024-12-26  
**Auditor:** Senior Django Engineer (Cursor AI)  
**Refactor Status:** ✅ **PASS** (with minor recommendations)

---

## Executive Summary

**Overall Status:** ✅ **PASS**

The GoToMeeting OAuth configuration refactor successfully moves all configuration from import-time environment variable reads to Django settings-driven configuration. The implementation is correct, safe, and maintains backward compatibility. 

**Key Findings:**
- ✅ All settings correctly defined in base + environment-specific files
- ✅ OAuth helper module correctly refactored with no import-time side effects
- ✅ Backward compatibility maintained via `__getattr__`
- ⚠️ **1 Medium Issue:** Hard-coded token URL in `token_encryption_service.py`
- ⚠️ **1 Low Issue:** Static OAuth state parameter (security consideration)
- ✅ No remaining direct `os.environ.get()` calls for OAuth config
- ✅ All call sites properly updated

**Risks:**
- **Low:** Hard-coded token URL in `token_encryption_service.py` should use settings
- **Low:** OAuth state parameter is static (should be random/session-based for CSRF protection)

---

## 1. Settings Correctness ✅

### 1.1 Base Settings (`base_settings.py`)

**Status:** ✅ **CORRECT**

All required `GOTO_OAUTH_*` keys are defined:

```python
# Lines 433-452
GOTO_OAUTH_CLIENT_ID = os.getenv("GOTO_OAUTH_CLIENT_ID") or os.getenv("API_CLIENT_ID")
GOTO_OAUTH_CLIENT_SECRET = os.getenv("GOTO_OAUTH_CLIENT_SECRET") or os.getenv("API_CLIENT_SECRET")
GOTO_OAUTH_AUTH_URL = os.getenv("GOTO_OAUTH_AUTH_URL", "https://authentication.logmeininc.com/oauth/authorize")
GOTO_OAUTH_TOKEN_URL = os.getenv("GOTO_OAUTH_TOKEN_URL", "https://authentication.logmeininc.com/oauth/token")
GOTO_OAUTH_TOKEN_CACHE_KEY = os.getenv("GOTO_OAUTH_TOKEN_CACHE_KEY", "api_access_token")
GOTO_OAUTH_REFRESH_TOKEN_CACHE_KEY = os.getenv("GOTO_OAUTH_REFRESH_TOKEN_CACHE_KEY", "api_refresh_token")
GOTO_OAUTH_REFRESH_TOKEN_TTL = int(os.getenv("GOTO_OAUTH_REFRESH_TOKEN_TTL", "86400"))
```

**Findings:**
- ✅ All required keys present
- ✅ Environment variable override support via `os.getenv()` 
- ✅ Backward compatibility: Supports both `GOTO_OAUTH_CLIENT_ID` and `API_CLIENT_ID`
- ✅ Sensible defaults provided for URLs and cache keys

### 1.2 Environment-Specific Redirect URIs

**Status:** ✅ **CORRECT**

**Local Settings** (`local_settings.py`, line 432-435):
```python
GOTO_OAUTH_REDIRECT_URI = os.getenv(
    "GOTO_OAUTH_REDIRECT_URI",
    "http://localhost:8000/management/oauth/callback/",
)
```

**Staging Settings** (`heroku_settings.py`, line 177-180):
```python
GOTO_OAUTH_REDIRECT_URI = os.getenv(
    "GOTO_OAUTH_REDIRECT_URI",
    "https://codamakutano.herokuapp.com/management/oauth/callback/",
)
```

**Production Settings** (`prod_settings.py`, line 164-167):
```python
GOTO_OAUTH_REDIRECT_URI = os.getenv(
    "GOTO_OAUTH_REDIRECT_URI",
    "https://www.codanalytics.net/management/oauth/callback/",
)
```

**Findings:**
- ✅ All environments have redirect URI defined
- ✅ Environment variable override supported
- ✅ Correct URLs per environment

### 1.3 Environment Selection

**Status:** ✅ **CORRECT**

**Settings Selector** (`settings.py`, lines 19-28):
```python
if ENVIRONMENT == 'staging':
    from .coda_settings.heroku_settings import *
elif ENVIRONMENT == 'production':
    from .coda_settings.prod_settings import *
elif ENVIRONMENT == 'local':
    from .coda_settings.local_settings import *
```

**Findings:**
- ✅ Consistent naming: `'staging'` → `heroku_settings.py` (correct mapping)
- ✅ Environment variable: `ENVIRONMENT = os.environ.get('ENVIRONMENT', 'local')`
- ✅ No inconsistent names detected

---

## 2. OAuth Helper Module Correctness ✅

### 2.1 Import-Time Side Effects

**Status:** ✅ **NO ISSUES**

**File:** `coda/shared_core/utils/oauth.py`

**Analysis:**
- ✅ No `os.environ.get()` calls at module level
- ✅ All imports are standard library (`logging`, `requests`, `urllib.parse`) or Django (`django.conf.settings`, `django.core.cache`)
- ✅ No settings-dependent evaluation before `django.setup()`
- ✅ All configuration reads happen at runtime via `getattr(settings, ...)`

**Verification:**
```python
# Lines 19-25: Safe imports only
import logging
import requests
from urllib.parse import urlencode
from django.conf import settings
from django.core.cache import cache
```

### 2.2 Function Implementation

**Status:** ✅ **CORRECT**

#### `get_oauth_redirect_uri()` (lines 28-35)
- ✅ Reads from `settings.GOTO_OAUTH_REDIRECT_URI`
- ✅ Sensible fallback: `"http://localhost:8000/management/oauth/callback/"`

#### `get_authorization_url()` (lines 81-103)
- ✅ Reads `client_id` from settings via `_get_client_id()`
- ✅ Validates `client_id` is not None, raises `ValueError` if missing
- ✅ Uses `get_oauth_redirect_uri()` for redirect URI (consistent)
- ✅ Uses `_get_auth_url()` for authorization endpoint
- ✅ Includes `state` parameter (⚠️ but static - see issue below)

#### `exchange_code_for_tokens()` (lines 106-165)
- ✅ Reads credentials from settings
- ✅ Uses `get_oauth_redirect_uri()` for redirect URI (matches authorization URL)
- ✅ Uses `_get_token_url()` for token endpoint
- ✅ Uses HTTP Basic Auth: `auth = (client_id, client_secret)`
- ✅ Uses settings-derived cache keys
- ✅ Uses `_get_refresh_token_ttl()` for refresh token TTL
- ✅ Proper error handling

#### `refresh_access_token()` (lines 168-230)
- ✅ Reads cache key from settings
- ✅ Reads credentials from settings
- ✅ Uses `_get_token_url()` for token endpoint
- ✅ Uses settings-derived cache keys and TTL
- ✅ Proper error handling

#### `get_access_token()` (lines 233-252)
- ✅ Uses settings-derived cache key
- ✅ Calls `refresh_access_token()` if token missing
- ✅ Returns `None` on failure (expected behavior)

### 2.3 Backward Compatibility

**Status:** ✅ **CORRECT**

**Implementation:** `__getattr__()` (lines 258-282)

**Coverage:**
- ✅ `API_CLIENT_ID`
- ✅ `API_CLIENT_SECRET`
- ✅ `API_AUTHORIZATION_URL`
- ✅ `API_TOKEN_URL`
- ✅ `TOKEN_CACHE_KEY`
- ✅ `REFRESH_TOKEN_CACHE_KEY`
- ✅ `API_REDIRECT_URI`

**Verification:**
- ✅ All legacy names in `__all__` (lines 285-299)
- ✅ No star-imports found in codebase (`from shared_core.utils.oauth import *`)
- ✅ All imports are explicit (verified in `ai_services/views.py` and `management/views.py`)

---

## 3. Codebase-Wide Usage Audit ✅

### 3.1 Remaining References

**Status:** ✅ **CLEAN** (with 1 exception)

#### Direct `os.environ.get()` for OAuth Config

**Found:** None (except in settings files, which is correct)

**Exception:** `gapi/gservices.py` uses `os.environ.get('GAPI_CLIENT_ID')` - **This is unrelated** (Google API, not GoToMeeting)

#### Hard-Coded Redirect URIs

**Found:** None (all use settings or helper functions)

**Unrelated localhost references:**
- Template files with commented-out `localhost:8000` (templates, not OAuth)
- Other services with `localhost` defaults (finance, AI services - unrelated)

#### Hard-Coded Token URLs

**Found:** ⚠️ **1 Instance** - See Issue #1 below

#### Cache Key References

**Status:** ✅ **CORRECT**
- All references use settings or helper functions
- No hard-coded `"api_access_token"` or `"api_refresh_token"` strings in OAuth code

---

## 4. Import Side Effects / Packaging Risks ✅

### 4.1 `shared_core/utils/__init__.py`

**Status:** ✅ **SAFE**

**Analysis:**
- ✅ No heavy imports that affect OAuth module
- ✅ OAuth module (`oauth.py`) does not import from `__init__.py`
- ✅ `oauth.py` only imports: `logging`, `requests`, `urllib.parse`, `django.conf.settings`, `django.core.cache`
- ✅ No risk of circular imports or heavy model loading when importing `shared_core.utils.oauth`

**Note:** `__init__.py` imports from `main.utils`, `accounts.utils`, `core.utils`, but these are separate modules and do not affect OAuth.

### 4.2 Path Casing Issues

**Status:** ✅ **NO ISSUES**

**Verification:**
- All imports use consistent paths: `shared_core.utils.oauth`
- No mixed case detected in import statements
- Project root reference: `~/projects/uat` (lowercase, consistent)

---

## 5. Issues Found

### Issue #1: Hard-Coded Token URL in `token_encryption_service.py` ⚠️ **MEDIUM**

**File:** `coda/ai_services/services/token_encryption_service.py`  
**Line:** 267  
**Severity:** Medium

**Problem:**
```python
response = requests.post(
    "https://authentication.logmeininc.com/oauth/token",  # Hard-coded URL
    headers=headers,
    data=data,
    auth=auth,
    timeout=10
)
```

**Impact:**
- Token refresh in `OAuthTokenManager.refresh_token_from_db()` uses hard-coded URL instead of settings
- Inconsistency with rest of codebase
- Cannot override via environment variable

**Recommendation:**
Replace with settings-based URL:

```python
# Line 266-267: Replace hard-coded URL
from django.conf import settings
token_url = getattr(
    settings,
    "GOTO_OAUTH_TOKEN_URL",
    "https://authentication.logmeininc.com/oauth/token"
)
response = requests.post(
    token_url,  # Use settings
    headers=headers,
    data=data,
    auth=auth,
    timeout=10
)
```

**Fix Location:**
- File: `coda/ai_services/services/token_encryption_service.py`
- Lines: 266-272
- Change: Replace hard-coded URL string with `getattr(settings, "GOTO_OAUTH_TOKEN_URL", ...)`

---

### Issue #2: Static OAuth State Parameter ⚠️ **LOW**

**File:** `coda/shared_core/utils/oauth.py`  
**Line:** 99  
**Severity:** Low (Security consideration)

**Problem:**
```python
'state': 'random_state_string',  # Use a random string for security
```

**Impact:**
- OAuth state parameter is static, not actually random
- Provides no CSRF protection (state should be random and validated)
- Comment suggests it should be random, but implementation is not

**Recommendation:**
For production use, implement proper CSRF state:

```python
import secrets

# In get_authorization_url():
state = secrets.token_urlsafe(32)  # Generate random state
# Store state in session or cache for validation in callback
params = {
    'client_id': client_id,
    'response_type': 'code',
    'redirect_uri': get_oauth_redirect_uri(),
    'state': state,  # Random state
}
```

**Note:** This requires updating `oauth_callback()` to validate state. This is a non-blocking security enhancement.

**Fix Location:**
- File: `coda/shared_core/utils/oauth.py`
- Lines: 95-100 (and callback validation)
- Priority: Low (security best practice, not a functional bug)

---

## 6. Required Fixes

### Fix #1: Update `token_encryption_service.py` to use settings

**File:** `coda/ai_services/services/token_encryption_service.py`

**Change:**
```python
# Line 266-267: Change from:
response = requests.post(
    "https://authentication.logmeininc.com/oauth/token",
    ...

# To:
from django.conf import settings
token_url = getattr(
    settings,
    "GOTO_OAUTH_TOKEN_URL",
    "https://authentication.logmeininc.com/oauth/token"
)
response = requests.post(
    token_url,
    ...
```

**Rationale:** Consistency with rest of codebase, allows environment variable override.

---

## 7. Recommended Improvements (Non-Blocking)

### Improvement #1: Implement proper OAuth state parameter

**Priority:** Low  
**Effort:** Medium  
**Benefit:** Security (CSRF protection)

Implement random state generation and validation in callback. This requires:
- Generating random state in `get_authorization_url()`
- Storing state in session/cache
- Validating state in `oauth_callback()`

### Improvement #2: Consider database-backed token storage

**Priority:** Low  
**Effort:** High  
**Benefit:** Token persistence across server restarts

The codebase already has `OAuthTokenManager` in `token_encryption_service.py` that supports database storage. Consider migrating from cache-based storage to database storage for production environments.

---

## 8. Verification Commands

### Command 1: Django Configuration Check
```bash
poetry run python coda/manage.py check
```
**Expected:** `System check identified no issues (0 silenced).`

### Command 2: Settings Verification
```bash
poetry run python coda/manage.py shell -c "from django.conf import settings; print('GOTO_OAUTH_REDIRECT_URI:', getattr(settings, 'GOTO_OAUTH_REDIRECT_URI', 'NOT SET')); print('GOTO_OAUTH_CLIENT_ID:', 'SET' if getattr(settings, 'GOTO_OAUTH_CLIENT_ID', None) else 'NOT SET'); print('GOTO_OAUTH_AUTH_URL:', getattr(settings, 'GOTO_OAUTH_AUTH_URL', 'NOT SET'))"
```
**Expected Output (local):**
```
GOTO_OAUTH_REDIRECT_URI: http://localhost:8000/management/oauth/callback/
GOTO_OAUTH_CLIENT_ID: SET (or NOT SET if not configured)
GOTO_OAUTH_AUTH_URL: https://authentication.logmeininc.com/oauth/authorize
```

### Command 3: OAuth Helper Function Test
```bash
poetry run python coda/manage.py shell -c "from shared_core.utils.oauth import get_oauth_redirect_uri, API_REDIRECT_URI, TOKEN_CACHE_KEY; print('get_oauth_redirect_uri():', get_oauth_redirect_uri()); print('API_REDIRECT_URI:', API_REDIRECT_URI); print('TOKEN_CACHE_KEY:', TOKEN_CACHE_KEY)"
```
**Expected Output (local):**
```
get_oauth_redirect_uri(): http://localhost:8000/management/oauth/callback/
API_REDIRECT_URI: http://localhost:8000/management/oauth/callback/
TOKEN_CACHE_KEY: api_access_token
```

### Command 4: Authorization URL Test (requires credentials)
```bash
poetry run python coda/manage.py shell -c "from shared_core.utils.oauth import get_authorization_url; print(get_authorization_url())"
```
**Expected:** URL string starting with `https://authentication.logmeininc.com/oauth/authorize?client_id=...`  
**Note:** Will raise `ValueError` if `GOTO_OAUTH_CLIENT_ID` is not set (expected behavior)

### Command 5: Token Cache Keys Test
```bash
poetry run python coda/manage.py shell -c "from django.core.cache import cache; from shared_core.utils.oauth import TOKEN_CACHE_KEY, REFRESH_TOKEN_CACHE_KEY; print('Access token cache key:', TOKEN_CACHE_KEY); print('Refresh token cache key:', REFRESH_TOKEN_CACHE_KEY); print('Has access token:', bool(cache.get(TOKEN_CACHE_KEY))); print('Has refresh token:', bool(cache.get(REFRESH_TOKEN_CACHE_KEY)))"
```
**Expected Output:**
```
Access token cache key: api_access_token
Refresh token cache key: api_refresh_token
Has access token: False (or True if authenticated)
Has refresh token: False (or True if authenticated)
```

---

## 9. GoTo Developer Portal Alignment Checklist

### Environment: Local Development

**Redirect URI in Settings:**
- `http://localhost:8000/management/oauth/callback/`

**Action Required:**
1. ✅ Verify GoToMeeting OAuth app has redirect URI: `http://localhost:8000/management/oauth/callback/`
2. ⚠️ **Important:** If you run server on port 8080, either:
   - Run server on port 8000: `poetry run python coda/manage.py runserver 8000`
   - OR set environment variable: `GOTO_OAUTH_REDIRECT_URI=http://localhost:8080/management/oauth/callback/`
   - OR update GoToMeeting app redirect URI to port 8080

### Environment: Staging (Heroku UAT)

**Redirect URI in Settings:**
- `https://codamakutano.herokuapp.com/management/oauth/callback/`

**Action Required:**
1. ✅ Verify GoToMeeting OAuth app has redirect URI: `https://codamakutano.herokuapp.com/management/oauth/callback/`
2. ⚠️ **Recommendation:** Create separate OAuth client for staging (see below)

### Environment: Production

**Redirect URI in Settings:**
- `https://www.codanalytics.net/management/oauth/callback/`

**Action Required:**
1. ✅ Verify GoToMeeting OAuth app has redirect URI: `https://www.codanalytics.net/management/oauth/callback/`
2. ✅ Ensure production OAuth client ID/secret are set in production environment variables

### Best Practice Recommendation

**Create 3 Separate OAuth Clients:**

1. **Local Development Client**
   - Redirect URI: `http://localhost:8000/management/oauth/callback/`
   - Client ID: Store in `dev.env` or local environment
   - Purpose: Local development only

2. **Staging/UAT Client**
   - Redirect URI: `https://codamakutano.herokuapp.com/management/oauth/callback/`
   - Client ID: Store in Heroku config vars as `GOTO_OAUTH_CLIENT_ID`
   - Purpose: Testing before production

3. **Production Client**
   - Redirect URI: `https://www.codanalytics.net/management/oauth/callback/`
   - Client ID: Store in production environment variables
   - Purpose: Live production system

**Benefits:**
- Isolation between environments
- Easier credential management
- Can revoke/rotate credentials per environment independently

---

## 10. Files Reviewed

### Settings Files
- ✅ `coda/coda_project/settings.py`
- ✅ `coda/coda_project/coda_settings/base_settings.py`
- ✅ `coda/coda_project/coda_settings/local_settings.py`
- ✅ `coda/coda_project/coda_settings/heroku_settings.py`
- ✅ `coda/coda_project/coda_settings/prod_settings.py`

### OAuth Implementation Files
- ✅ `coda/shared_core/utils/oauth.py`
- ✅ `coda/ai_services/services/token_encryption_service.py`
- ✅ `coda/ai_services/views.py`
- ✅ `coda/management/views.py`

### Utility Files
- ✅ `coda/shared_core/utils/__init__.py`

### Configuration Files
- ✅ `coda/dev.env` (checked for remaining references)

---

## 11. Summary

### ✅ What's Working

1. **Settings Configuration:** All required `GOTO_OAUTH_*` settings correctly defined
2. **Environment Separation:** Correct redirect URIs per environment
3. **OAuth Helper Module:** No import-time side effects, all config reads from settings
4. **Backward Compatibility:** `__getattr__()` correctly implements legacy constant access
5. **Call Sites:** All call sites updated to use settings or helper functions
6. **Codebase Clean:** No remaining direct `os.environ.get()` for OAuth config

### ⚠️ Issues to Address

1. **Medium:** Hard-coded token URL in `token_encryption_service.py` (Fix #1)
2. **Low:** Static OAuth state parameter (Improvement #1)

### 📋 Action Items

1. **Required:** Fix hard-coded token URL in `token_encryption_service.py` (5 minutes)
2. **Recommended:** Verify GoToMeeting OAuth app redirect URIs match settings values
3. **Optional:** Implement proper OAuth state parameter for CSRF protection
4. **Optional:** Consider database-backed token storage for production

---

## Conclusion

The GoToMeeting OAuth configuration refactor is **production-ready** with one minor fix recommended. The implementation correctly moves all configuration to Django settings, maintains backward compatibility, and eliminates import-time side effects. 

**Recommendation:** Apply Fix #1 before deploying to production for consistency. All other issues are non-blocking improvements.

---

**Report Generated:** 2024-12-26  
**Next Review:** After Fix #1 applied

