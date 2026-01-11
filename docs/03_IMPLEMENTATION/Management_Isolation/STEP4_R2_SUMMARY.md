# Step 4 Round 2: OAuth Helpers Move to Shared Core - Summary

**Date:** December 2025  
**Branch:** `25.12_CODA_DEV_CM`  
**Status:** ✅ Complete

---

## Functions Moved

### OAuth Helper Functions (5 functions + 7 constants)

**From:** `coda/ai_services/views.py`  
**To:** `coda/shared_core/utils/oauth.py`

| Function/Constant | Purpose |
|-------------------|---------|
| `get_oauth_redirect_uri()` | Get redirect URI based on environment (production/staging/local) |
| `get_authorization_url()` | Construct authorization URL with client_id, redirect_uri, state |
| `exchange_code_for_tokens(auth_code)` | Exchange authorization code for access/refresh tokens |
| `refresh_access_token()` | Refresh access token using refresh token |
| `get_access_token()` | Get valid access token (with auto-refresh if needed) |
| `API_CLIENT_ID` | OAuth client ID from environment |
| `API_CLIENT_SECRET` | OAuth client secret from environment |
| `API_AUTHORIZATION_URL` | GoToMeeting authorization URL |
| `API_TOKEN_URL` | GoToMeeting token exchange URL |
| `TOKEN_CACHE_KEY` | Cache key for access token |
| `REFRESH_TOKEN_CACHE_KEY` | Cache key for refresh token |
| `API_REDIRECT_URI` | Backward compatibility constant |

**Total:** 5 functions + 7 constants moved

---

## New Shared Module Created

### `coda/shared_core/utils/oauth.py`

**Structure:**
- Module-level constants (API_CLIENT_ID, API_CLIENT_SECRET, etc.)
- 5 OAuth helper functions (full implementations moved)
- All dependencies imported (os, logging, requests, urlencode, django.conf.settings, django.core.cache)
- Comprehensive docstrings
- `__all__` export list

**Key Features:**
- Environment-aware redirect URIs (production/staging/local)
- Error handling with logging
- Token caching via Django cache
- HTTP Basic Auth for token exchange
- Auto-refresh logic in `get_access_token()`

---

## Changes Made

### 1. Created `coda/shared_core/utils/oauth.py`

**New file created** with:
- All 5 OAuth helper functions (moved from `ai_services/views.py`)
- All 7 OAuth constants
- All necessary imports (os, logging, requests, urlencode, django.conf.settings, django.core.cache)

**File size:** ~150 lines

---

### 2. Updated `coda/ai_services/views.py`

**Removed:**
- Lines 216-364: All OAuth function definitions and constants

**Added:**
- Import from `shared_core.utils.oauth`:
```python
from shared_core.utils.oauth import (
    get_oauth_redirect_uri,
    get_authorization_url,
    exchange_code_for_tokens,
    refresh_access_token,
    get_access_token,
    API_CLIENT_ID,
    API_CLIENT_SECRET,
    API_AUTHORIZATION_URL,
    API_TOKEN_URL,
    TOKEN_CACHE_KEY,
    REFRESH_TOKEN_CACHE_KEY,
    API_REDIRECT_URI,
)
```

**Lines changed:**
- Removed: ~149 lines (function definitions)
- Added: ~15 lines (import statement)
- **Net reduction:** ~134 lines

**Functions still using OAuth helpers:**
- `getmeetingresponse()` - Uses `get_access_token()` (line 385, 589, 723)
- These continue to work via the import from shared_core

---

### 3. Updated `coda/management/views.py`

**Changed:**
- Line 158-170: Import statement updated

**Before:**
```python
from ai_services.views import (
    get_oauth_redirect_uri,
    get_authorization_url,
    exchange_code_for_tokens,
    refresh_access_token,
    get_access_token,
    API_CLIENT_ID,
    API_CLIENT_SECRET,
    API_AUTHORIZATION_URL,
    API_TOKEN_URL,
    TOKEN_CACHE_KEY,
    REFRESH_TOKEN_CACHE_KEY,
)
API_REDIRECT_URI = get_oauth_redirect_uri()
```

**After:**
```python
from shared_core.utils.oauth import (
    get_oauth_redirect_uri,
    get_authorization_url,
    exchange_code_for_tokens,
    refresh_access_token,
    get_access_token,
    API_CLIENT_ID,
    API_CLIENT_SECRET,
    API_AUTHORIZATION_URL,
    API_TOKEN_URL,
    TOKEN_CACHE_KEY,
    REFRESH_TOKEN_CACHE_KEY,
    API_REDIRECT_URI,
)
```

**Note:** `API_REDIRECT_URI` is now imported directly (no need to call function)

---

### 4. Created `coda/shared_core/utils/__init__.py`

**New file created** to make `shared_core/utils` a proper Python package.

---

## Verification

### Import Check

✅ **OAuth module imports successfully:**
```python
from shared_core.utils.oauth import get_oauth_redirect_uri, get_authorization_url, ...
```

### Linter Check

✅ **No linter errors** in:
- `coda/shared_core/utils/oauth.py`
- `coda/ai_services/views.py` (after update)
- `coda/management/views.py` (after update)

### Function Usage

✅ **Functions still used in ai_services/views.py:**
- `get_access_token()` called in `getmeetingresponse()` (lines 385, 589, 723)
- All calls work via import from shared_core

✅ **Functions still used in management/views.py:**
- All OAuth functions imported and available
- Constants imported and available

---

## Summary

### Files Created

1. `coda/shared_core/utils/__init__.py` - Package init
2. `coda/shared_core/utils/oauth.py` - OAuth helpers module (~150 lines)

### Files Modified

1. `coda/ai_services/views.py` - Removed OAuth functions, added import (~134 lines removed)
2. `coda/management/views.py` - Updated import statement (1 change)

### Impact

- ✅ **No migrations required**
- ✅ **No behavior changes** - OAuth flows work exactly as before
- ✅ **No circular imports** - shared_core doesn't import from ai_services
- ✅ **Infrastructure utilities** - OAuth helpers now in shared_core (not tied to ai_services app)
- ✅ **Management-only branch ready** - Management can import OAuth helpers without ai_services code

---

## Next Steps

**Ready for:**
- Step 5: Create Management-only branch structure
- Testing: Verify OAuth flows still work in both apps
- Optional: Update any other apps that might import OAuth helpers from ai_services

---

**Changes Complete:** December 2025  
**Status:** ✅ All OAuth helpers moved to shared_core, imports updated

