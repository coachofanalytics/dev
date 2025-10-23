# Integrations & API - Architecture

**Feature:** External Integrations & APIs  
**Status:** Design Complete  
**Last Updated:** October 22, 2025

---

## 🏗️ OAUTH ARCHITECTURE

### OAuth 2.0 Flow (Authorization Code Grant)

```
User clicks "Login with Google"
    ↓
Redirect to Google with client_id, redirect_uri, state
    ↓
User authorizes
    ↓
Google redirects back with code
    ↓
Exchange code for access_token
    ↓
Get user profile from Google
    ↓
Create/link CODA account
    ↓
Login user
```

---

## 🔌 API ARCHITECTURE

### REST API Endpoints (Planned)
- `POST /api/auth/login` - API login
- `GET /api/users/` - List users
- `POST /api/users/` - Create user
- `GET /api/users/{id}/` - Get user
- `PUT /api/users/{id}/` - Update user
- `DELETE /api/users/{id}/` - Delete user

---

## 📊 SSO ARCHITECTURE (Phase 3)

### SAML 2.0 Flow
```
User accesses CODA
    ↓
Redirect to IdP (Okta/Azure AD)
    ↓
IdP authenticates
    ↓
SAML assertion sent to CODA
    ↓
CODA validates assertion
    ↓
Create session
    ↓
User logged in
```

---

**See:** 04_IMPLEMENTATION.md


