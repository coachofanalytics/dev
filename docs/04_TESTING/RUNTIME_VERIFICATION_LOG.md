# Runtime Verification Log

**Branch:** 25.12_CODA_DEV_CM  
**Date:** 2024-12-29  
**Purpose:** Complete remaining runtime/manual verification steps

---

## 1) Shared Cache Production Readiness

**Status:** ✅ COMPLETE

**Changes:**
- Added Redis cache support to all environment settings files
- Added `CACHE_BACKEND` environment variable switch
- Default: LocMemCache for local, Redis for production/UAT
- Added clear warnings when LocMemCache is used in production

**Files Modified:**
- `coda/coda_project/coda_settings/local_settings.py`
- `coda/coda_project/coda_settings/prod_settings.py`
- `coda/coda_project/coda_settings/heroku_settings.py`

**Verification:**
```bash
# Test local settings (should default to LocMemCache)
poetry run python coda/manage.py shell -c "
from django.conf import settings
print('Cache backend:', settings.CACHES['default']['BACKEND'])
"
```

**Result:** ✅ PASS - Settings files updated, syntax verified

---

## 2) Manual UI Verification: DAF v2 Launcher

**Status:** ⏳ PENDING (requires web server + manual test)

**Checks:**
1. DAF v2 task cards show "Start/Join Meeting" ONLY when `meeting_join_url` exists
2. Button URL: `/management/meeting/launch/?activity_type=...&task_id=...`
3. Clicking button:
   - (a) Hits `/management/meeting/launch/` endpoint ✅ (verified in code)
   - (b) Records launch intent into cache with TTL 24h ✅ (verified in code)
   - (c) Redirects to join URL ✅ (verified in code)

**Code Verification:**
- ✅ Template: `employeetasks_v2.html` line 394 - button only shows if `meeting_join_url` exists
- ✅ View: `views_meeting_launch.py` - validates task access, records intent, redirects
- ✅ URL: `urls.py` - route exists for `launch_meeting`

**Manual Test Steps:**
1. Start web server: `poetry run python coda/manage.py runserver`
2. Open `/management/daf/v2/?user_id=372` (or any employee with meeting-required task)
3. Find task with meeting requirement
4. Click "Start Meeting" button
5. Verify redirect to GoToMeeting
6. Check cache: `poetry run python coda/manage.py shell -c "from management.views_meeting_launch import get_launch_intent; print(get_launch_intent(372, 'UAT_TESTING_SUPPORT'))"`

**Result:** ⏳ PENDING - requires manual UI test

---

## 3) Manual UI Verification: Debug Page

**Status:** ✅ FIXED

**Issue Found:**
- Debug page was ordering Task objects by `created_at` field, but Task model doesn't have this field
- Task model has `submission` field for date, but for ordering we should use `id` (descending)

**Fix Applied:**
- Changed `order_by('-created_at')` to `order_by('-id')` in `views_debug.py` lines 346 and 354

**Code Verification:**
- ✅ View: `views_debug.py` - helpers exist for meeting room mappings and launch intents
- ✅ Template: `daf_runtime_debug.html` - sections F and G exist
- ✅ Task ordering fixed (no longer references non-existent `created_at` field)

**Manual Test Steps:**
1. Start web server: `poetry run python coda/manage.py runserver`
2. Open `/management/debug/daf-runtime/` as staff user
3. Verify Section F (Meeting Room Mappings) shows:
   - Activity type -> meeting_room_id mappings
   - Join URL presence indicator (not full URL)
4. Verify Section G (Recent Launch Intents) shows:
   - User, activity type, meeting_id, timestamp
   - No sensitive join URLs

**Result:** ⏳ PENDING - requires manual UI test (code fix complete)

**Checks:**
1. `/management/debug/daf-runtime/` loads without errors
2. Meeting room mappings section renders correctly
3. Recent launch intents section renders correctly
4. No sensitive join URLs printed in full

**Code Verification:**
- ✅ View: `views_debug.py` - helpers exist for meeting room mappings and launch intents
- ✅ Template: `daf_runtime_debug.html` - sections F and G exist
- ✅ No Task ordering by `created_at` (Task model doesn't have this field)

**Manual Test Steps:**
1. Start web server: `poetry run python coda/manage.py runserver`
2. Open `/management/debug/daf-runtime/` as staff user
3. Verify Section F (Meeting Room Mappings) shows:
   - Activity type -> meeting_room_id mappings
   - Join URL presence indicator (not full URL)
4. Verify Section G (Recent Launch Intents) shows:
   - User, activity type, meeting_id, timestamp
   - No sensitive join URLs

**Result:** ⏳ PENDING - requires manual UI test

---

## 4) Runtime Verification: Autolink Non-Diagnose

**Status:** ⏳ PENDING (requires launch intent in cache + meeting sync)

**Steps:**
1. Ensure employee has meeting-required task
2. Click "Start Meeting" from DAF v2 (creates launch intent in cache)
3. Run meeting sync: `poetry run python coda/manage.py sync_gotomeetings --days 7`
4. Run autolink: `poetry run python coda/manage.py autolink_meeting_evidence --user-id <ID> --days 7 --limit 20`
5. Verify TaskLinks created:
   ```bash
   poetry run python coda/manage.py shell -c "
   from management.models import TaskLinks
   print('Auto TaskLinks:', TaskLinks.objects.filter(is_auto_generated=True).count())
   print('With meeting_id:', TaskLinks.objects.filter(is_auto_generated=True).exclude(meeting_id__isnull=True).count())
   "
   ```
6. Verify DAF v2 shows evidence/compliance chips updated

**Expected:**
- TaskLinks created with `is_auto_generated=True`
- TaskLinks have `meeting_id` populated
- DAF v2 compliance chips reflect new TaskLinks

**Result:** ⏳ PENDING - requires manual test with launch intent + meeting sync

---

## Summary

**Completed:**
- ✅ 1) Shared cache production readiness (Redis support added)
- ✅ 3) Debug page fix (Task ordering issue resolved)
- ✅ URL route added for `launch_meeting`

**Pending (Manual Tests):**
- ⏳ 2) DAF v2 launcher UI verification
- ⏳ 3) Debug page manual verification
- ⏳ 4) Autolink non-diagnose verification

**Files Modified:**
1. `coda/coda_project/coda_settings/local_settings.py` - Added Redis support
2. `coda/coda_project/coda_settings/prod_settings.py` - Added Redis support
3. `coda/coda_project/coda_settings/heroku_settings.py` - Added Redis support
4. `coda/management/views_debug.py` - Fixed Task ordering (changed `created_at` to `id`)
5. `coda/management/urls.py` - Added missing `launch_meeting` URL route
6. `coda/management/views_meeting_launch.py` - Fixed incomplete line (missing function call)
7. `PRODUCTION_CACHE_NOTE.md` - Documentation for production deployment

**Next Steps:**
1. Deploy to staging/UAT with Redis configured
2. Run manual UI tests (steps 2-4 above)
3. Verify end-to-end flow: Launch → Sync → Autolink → TaskLinks

