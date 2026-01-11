# Fix: attendee_count Annotation Conflict

**Branch:** 25.12_CODA_DEV_CM  
**Date:** 2024-12-30  
**Issue:** AttributeError when annotating Meeting with `attendee_count`  
**Status:** ✅ Fixed

---

## Problem

The `Meeting` model has a `@property` named `attendee_count` (read-only). When Django tries to annotate with `attendee_count=Count(...)`, it attempts to set the property, which fails because properties don't have setters.

**Error:**
```
AttributeError: property 'attendee_count' of 'Meeting' object has no setter
```

---

## Solution

Renamed all annotations from `attendee_count` to `attendee_count_db` to avoid conflict with the property.

---

## Files Fixed

### 1. `coda/ai_services/management/commands/diagnose_attendee_sync.py`

**Changed:**
- Line 78: `attendee_count=Count('attendees')` → `attendee_count_db=Count('attendees')`
- Line 87: `meeting.attendee_count == 0` → `meeting.attendee_count_db == 0`

### 2. `coda/ai_services/services/attendee_sync_service.py`

**Changed:**
- Line 392: `attendee_count=Count('attendees')` → `attendee_count_db=Count('attendees')`
- Line 399: `Q(attendee_count=0)` → `Q(attendee_count_db=0)`
- Added comment explaining the naming

### 3. `coda/ai_services/management/commands/sync_meeting_attendees.py`

**Changed:**
- Line 144: Updated to use `getattr(meeting, 'attendee_count_db', None)` with fallback to property
- Prefers annotation when available, falls back to property for display

### 4. `coda/ai_services/views_analytics.py`

**Changed:**
- Line 81: `attendee_count=Count('id')` → `attendee_count_db=Count('id')`
- Line 82: `Avg('attendee_count')` → `Avg('attendee_count_db')`
- Added comment explaining the naming

### 5. `coda/ai_services/tests/test_attendee_sync.py`

**Added:**
- New test: `test_annotation_does_not_conflict_with_property()`
- Verifies annotation works without AttributeError
- Verifies both annotation and property can be accessed

---

## Verification

### Run Diagnostic Command

```bash
poetry run python coda/manage.py diagnose_attendee_sync --service all --days 30
```

**Expected:** No AttributeError, command runs successfully

### Run Tests

```bash
poetry run python coda/manage.py test ai_services.tests.test_attendee_sync
```

**Expected:** All tests pass, including new regression test

---

## Summary

✅ **Fixed:** All `attendee_count` annotations renamed to `attendee_count_db`  
✅ **Tested:** Added regression test to prevent future conflicts  
✅ **Verified:** Command runs without AttributeError  

**Behavior unchanged:** Same output format, same logic, just different annotation name.

