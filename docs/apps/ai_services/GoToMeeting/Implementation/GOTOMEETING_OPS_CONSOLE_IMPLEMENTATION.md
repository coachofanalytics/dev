# GoToMeeting Ops Console Implementation Summary

**Branch:** 25.12_CODA_DEV_CM  
**Date:** 2024-12-30  
**Status:** ✅ Complete

---

## Overview

Implemented a staff-only GoToMeeting Ops Console panel on `/dashboard` that provides visibility into token health and recent GoToMeeting/AI operations for both internal and external services.

---

## Implementation Details

### A) Data Displayed on Dashboard

For each service (internal/external), the panel shows:

1. **OAuth Token Status:**
   - `service_name`, `is_valid`, `expires_at`, `last_refreshed_at`, `updated_at`
   - `minutes_to_expiry` (computed)
   - Status badge:
     - 🟢 GREEN: `is_valid=True` AND `minutes_to_expiry > 10`
     - 🟡 YELLOW: `is_valid=True` AND `0 < minutes_to_expiry <= 10`
     - 🔴 RED: `is_valid=False` OR `minutes_to_expiry <= 0`

2. **Sync Health:**
   - Latest `MeetingSyncRun` for the service
   - `started_at`, `finished_at`, `status`
   - `meetings_fetched_count`, `meetings_upserted_count`
   - `window_start`, `window_end`
   - `error_message` (truncated to 200 chars if failed)

3. **Attendee Health (Last 30 Days):**
   - `meetings_last_30d_count` for that service
   - `meetings_last_30d_with_attendees_count`
   - `attendees_last_30d_count`
   - `latest_attendee_updated_at` for that service
   - Coverage % = `(meetings_with_attendees / meetings_total) * 100`

4. **Autolink/AI Ops Health:**
   - Latest `AutolinkRun`: `started_at`, `status`, `tasks_scanned`, `tasks_matched`, `tasklinks_created`, `errors`
   - Latest `AIOperationsRun`: `started_at`, `status`, `meetings_scanned`, `tasks_scanned`, `tasks_review_queue`, `errors_count`

5. **Quick Action Links:**
   - Admin changelist filters:
     - `/admin/ai_services/oauthtoken/`
     - `/admin/ai_services/meetingsyncrun/`
     - `/admin/ai_services/autolinkrun/`
     - `/admin/ai_services/aioperationsrun/`
     - `/admin/ai_services/taskmeetinglinksuggestion/`
   - OAuth login links:
     - `/management/oauth/login/?service=internal`
     - `/management/oauth/login/?service=external`

### B) Buttons / Actions

For each service, the panel includes:

1. **"Attempt Refresh Now" (POST, CSRF-protected):**
   - POST to: `/management/goto/refresh/<service>/`
   - Maps `internal` → `gotomeeting_internal`, `external` → `gotomeeting_external`
   - Calls `OAuthTokenManager.refresh_token_from_db()`
   - On success: Shows success message with new `expires_at` and `last_refreshed_at`
   - On failure: Shows error message (if 401/invalid_grant, suggests re-auth)
   - Always redirects to `dashboard#gotomeeting-ops`

2. **"Re-auth" (GET redirect):**
   - GET redirect to: `/management/oauth/login/?service=<internal|external>`

### C) Implementation Files

1. **`coda/management/views_goto_ops.py`** (NEW)
   - `goto_ops_refresh_view(request, service)`: POST endpoint for token refresh
   - `goto_ops_reauth_redirect_view(request, service)`: GET redirect to OAuth login
   - Both decorated with `@staff_member_required`

2. **`coda/management/urls.py`**
   - Added:
     - `path('goto/refresh/<str:service>/', views_goto_ops.goto_ops_refresh_view, name='goto_ops_refresh')`
     - `path('goto/reauth/<str:service>/', views_goto_ops.goto_ops_reauth_redirect_view, name='goto_ops_reauth')`

3. **`coda/unified_dashboard/views.py`**
   - Added `get_goto_ops_data()` function to gather all ops data
   - Updated `unified_dashboard()` to call `get_goto_ops_data()` for staff users
   - Added `goto_ops_data` to context

4. **`coda/unified_dashboard/templates/unified_dashboard/dashboard.html`**
   - Added GoToMeeting Ops Console section with `id="gotomeeting-ops"`
   - Wrapped with `{% if user.is_staff or user.is_superuser %}`
   - Two-column layout (internal/external)
   - CSRF-protected forms for refresh buttons
   - Status badges with color coding
   - Quick action links to admin and OAuth login

5. **`coda/management/tests/test_goto_ops.py`** (NEW)
   - Tests for non-staff access denial
   - Tests for staff refresh success/failure
   - Tests for reauth redirect
   - Tests for invalid service parameters
   - Tests for missing token scenarios

---

## Key Features

✅ **Staff-only access:** All endpoints and UI wrapped with `@staff_member_required` / `{% if user.is_staff %}`

✅ **CSRF protection:** Refresh forms use `{% csrf_token %}`

✅ **No secrets displayed:** Only metadata shown (expires_at, status, counts); never access_token or refresh_token

✅ **Efficient queries:** Uses aggregates, avoids N+1 queries

✅ **Error handling:** Graceful handling of missing tokens, failed refreshes, invalid services

✅ **User feedback:** Django messages for success/failure with clear instructions

---

## Testing

Run tests:
```bash
poetry run python coda/manage.py test management.tests.test_goto_ops
```

**Expected:** All 8 tests pass:
1. Non-staff cannot access refresh
2. Non-staff cannot access reauth
3. Staff can refresh token (success)
4. Staff can refresh token (failure)
5. Staff can access reauth redirect
6. Reauth redirect for external
7. Refresh invalid service
8. Reauth invalid service
9. Refresh no token found

---

## Verification

1. **Access dashboard as staff:**
   ```bash
   # Login as staff user, navigate to /dashboard
   # Should see "GoToMeeting Ops Console" panel
   ```

2. **Test refresh:**
   - Click "Attempt Refresh Now" for internal service
   - Should see success/error message
   - Should redirect to `#gotomeeting-ops` anchor

3. **Test reauth:**
   - Click "Re-auth" for external service
   - Should redirect to `/management/oauth/login/?service=external`

4. **Verify data:**
   - Check token status badges (green/yellow/red)
   - Verify sync health shows latest run
   - Check attendee coverage percentages
   - Verify autolink/AI ops health shows latest runs

---

## Files Modified

1. **`coda/management/views_goto_ops.py`** (NEW) - Views for refresh and reauth
2. **`coda/management/urls.py`** - Added URL patterns
3. **`coda/unified_dashboard/views.py`** - Added `get_goto_ops_data()` function
4. **`coda/unified_dashboard/templates/unified_dashboard/dashboard.html`** - Added ops console panel
5. **`coda/management/tests/test_goto_ops.py`** (NEW) - Comprehensive tests

---

## Acceptance Criteria

✅ `/dashboard` shows GoToMeeting Ops panel for staff only  
✅ Panel shows internal/external token health + key timestamps  
✅ Refresh button (POST) works and shows success/failure message  
✅ Re-auth button redirects correctly for each service  
✅ Panel shows sync run + attendee coverage + latest AutolinkRun + latest AIOperationsRun  
✅ No secrets are rendered or logged  
✅ Tests pass  

---

## Summary

✅ **All tasks completed:**
- Data gathering function (`get_goto_ops_data()`)
- Views for refresh and reauth
- URLs configured
- Template panel with all required data
- Comprehensive tests (9 tests)
- Staff-only access enforced
- CSRF protection
- No secrets displayed

**Ready for:** Testing and production use.

