# Integrations & API - Implementation

**Feature:** External Integrations & APIs  
**Status:** Not Implemented  
**Last Updated:** October 22, 2025

---

## 📂 TO BE IMPLEMENTED

### OAuth Views (Phase 2)
**Location:** `coda/accounts/views_oauth.py`

**Functions:**
- `oauth_login(provider)` - Initiate OAuth
- `oauth_callback(provider)` - Handle callback
- `oauth_disconnect(provider)` - Remove connection

### API Views (Phase 2)
**Location:** `coda/accounts/api/views.py`

**ViewSets:**
- `UserViewSet` - User CRUD API
- `AuthenticationViewSet` - Login/logout API

### SSO Views (Phase 3)
**Location:** `coda/accounts/views_sso.py`

**Functions:**
- `saml_login()` - Initiate SAML
- `saml_acs()` - Assertion Consumer Service
- `saml_metadata()` - SP metadata

---

**See:** 05_TESTING.md



