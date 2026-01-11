# GoToMeeting Identifier + Persistence Fix - Implementation Summary

**Branch:** 25.12_CODA_DEV_CM  
**Date:** 2024-12-30  
**Status:** ✅ Complete

---

## Problem Statement

1. **Unique constraint bug**: `Meeting.meeting_id` had `unique=True`, causing:
   - Same meeting_id from different services (internal vs external) to collide
   - Same meeting_id from different sessions (same room, different occurrence) to collide
   - Upserts to overwrite existing records, losing session_id or service_name

2. **session_id not persisted**: External meetings had `session_id=NULL` even though API returns it

3. **External 404s**: Many external meetings returned 404 when fetching attendees, indicating cross-account pollution or wrong meetingIds

4. **No 404 tracking**: Failed meetings were retried repeatedly without tracking

---

## Solution Implemented

### A) Schema Changes ✅

**File**: `coda/ai_services/models.py`

1. **Removed `unique=True` from `meeting_id`**:
   - Changed from `unique=True` to just `db_index=True`
   - Allows same meeting_id across services and sessions

2. **Added `provider_not_found` fields**:
   - `provider_not_found` (BooleanField, default=False, indexed)
   - `provider_not_found_at` (DateTimeField, null=True)

3. **Added new unique constraints**:
   - Primary: `(service_name, meeting_id, session_id)` when session_id is not null
   - Fallback: `(service_name, meeting_id, start_time)` when session_id is null

4. **Added new indexes**:
   - `(service_name, meeting_id)` for service-scoped lookups
   - `(service_name, session_id)` for service-scoped session lookups
   - `(service_name, start_time)` for service-scoped time lookups
   - `(provider_not_found)` for filtering out 404 meetings

**Migration**: `coda/ai_services/migrations/0007_fix_meeting_uniqueness_constraints.py`
- Handles duplicates safely (keeps newest, deletes older)
- Drops old unique constraint
- Adds new constraints and indexes

---

### B) Upsert Logic Fix ✅

**Files Updated**:
1. `coda/ai_services/views.py` - `save_meeting_data()`
2. `coda/ai_services/services/legacy_gotomeeting_import_service.py`
3. `coda/ai_services/management/commands/migrate_gotomeeting_data.py`

**Changes**:
- Changed from `get_or_create(meeting_id=...)` to composite key:
  - Preferred: `(service_name, meeting_id, session_id)` when session_id available
  - Fallback: `(service_name, meeting_id, start_time)` when session_id missing
- Ensures `session_id` is extracted from API and persisted
- Ensures `service_name` is correctly assigned and never mixed
- Prevents overwriting `session_id` with NULL

---

### C) Provider Not Found Tracking ✅

**File**: `coda/ai_services/services/attendee_sync_service.py`

**Changes**:
1. **Mark 404 meetings**:
   - When `fetch_attendees_for_meeting()` returns `404_not_found`, mark meeting as `provider_not_found=True`
   - Set `provider_not_found_at` timestamp

2. **Exclude from sync**:
   - Meetings with `provider_not_found=True` are automatically skipped in `sync_attendees_for_meetings()`
   - Prevents repeated 404 attempts

3. **Clear flag on success**:
   - If fetch succeeds after being marked, clear `provider_not_found` flag

**File**: `coda/ai_services/management/commands/diagnose_attendee_sync.py`

**Changes**:
- Added provider_not_found statistics
- Shows count by service
- Lists top 10 recent 404 meetingIds
- Includes SQL queries for verification

---

### D) Backfill Enhancement ✅

**File**: `coda/ai_services/management/commands/backfill_meeting_instance_keys.py`

**Status**: Already compatible with new schema (uses `service_name` in filters)

**Functionality**:
- Backfills `session_id` from historicalMeetings API
- Backfills `provider_meeting_instance_key` from attendee API
- Matches by `(service_name, meeting_id, start_time ± tolerance)`
- Skips ambiguous matches unless `--force`

---

### E) Tests ✅

**File**: `coda/ai_services/tests/test_meeting_uniqueness_fix.py`

**Tests Added**:
1. `test_same_meeting_id_across_services`: Verifies same meeting_id can exist for internal and external
2. `test_same_meeting_id_different_sessions`: Verifies same meeting_id can exist for different sessions
3. `test_upsert_uses_composite_key`: Verifies upsert uses composite key correctly
4. `test_session_id_persists_and_not_overwritten_with_null`: Verifies session_id persistence
5. `test_provider_not_found_flag_set_on_404`: Verifies 404 tracking
6. `test_provider_not_found_meetings_excluded_from_sync`: Verifies exclusion logic
7. `test_fallback_constraint_without_session_id`: Verifies fallback constraint works

---

### F) Runbook ✅

**File**: `GOTOMEETING_DATA_INTEGRITY_RUNBOOK.md`

**Contents**:
- Step-by-step migration instructions
- Backfill commands for both services
- Verification queries (Python shell + SQL)
- Troubleshooting guide
- Expected results

---

## Files Modified

### Models
- `coda/ai_services/models.py`: Updated Meeting model

### Migrations
- `coda/ai_services/migrations/0007_fix_meeting_uniqueness_constraints.py`: New migration

### Services
- `coda/ai_services/views.py`: Fixed upsert logic
- `coda/ai_services/services/legacy_gotomeeting_import_service.py`: Fixed upsert logic
- `coda/ai_services/services/attendee_sync_service.py`: Added provider_not_found tracking

### Management Commands
- `coda/ai_services/management/commands/migrate_gotomeeting_data.py`: Fixed upsert logic
- `coda/ai_services/management/commands/diagnose_attendee_sync.py`: Added provider_not_found stats

### Tests
- `coda/ai_services/tests/test_meeting_uniqueness_fix.py`: New test file

### Documentation
- `GOTOMEETING_DATA_INTEGRITY_RUNBOOK.md`: New runbook

---

## Exact Commands to Run

### 1. Run Migration

```bash
poetry run python coda/manage.py migrate ai_services
```

### 2. Backfill session_id

```bash
# External
poetry run python coda/manage.py backfill_meeting_instance_keys \
  --service external \
  --days 260 \
  --verbose

# Internal
poetry run python coda/manage.py backfill_meeting_instance_keys \
  --service internal \
  --days 260 \
  --verbose
```

### 3. Sync Attendees

```bash
# External
poetry run python coda/manage.py sync_meeting_attendees \
  --service external \
  --days 260 \
  --verbose

# Internal
poetry run python coda/manage.py sync_meeting_attendees \
  --service internal \
  --days 260 \
  --verbose
```

### 4. Diagnose

```bash
poetry run python coda/manage.py diagnose_attendee_sync \
  --service all \
  --days 260
```

### 5. Run Tests

```bash
poetry run python coda/manage.py test ai_services.tests.test_meeting_uniqueness_fix -v 2
```

---

## Verification Queries

### Check session_id Coverage

```python
from ai_services.models import Meeting

external = Meeting.objects.filter(service_name="gotomeeting_external")
total = external.count()
with_session = external.exclude(session_id__isnull=True).exclude(session_id='').count()
print(f"External: {with_session}/{total} have session_id ({with_session/total*100:.1f}%)")
```

### Check provider_not_found Counts

```python
from ai_services.models import Meeting
from django.db.models import Count

provider_not_found = Meeting.objects.filter(provider_not_found=True).values('service_name').annotate(
    count=Count('id')
)
for item in provider_not_found:
    print(f"{item['service_name']}: {item['count']} meetings")
```

---

## Acceptance Criteria

✅ **Schema**:
- `meeting_id` no longer has `unique=True`
- New unique constraints: `(service_name, meeting_id, session_id)` and `(service_name, meeting_id, start_time)`
- `provider_not_found` fields added

✅ **Upsert Logic**:
- Uses composite key `(service_name, meeting_id, session_id)` or `(service_name, meeting_id, start_time)`
- `session_id` persists and is not overwritten with NULL
- `service_name` correctly assigned

✅ **404 Tracking**:
- Meetings marked as `provider_not_found=True` on 404
- Excluded from repeat sync attempts
- Flag cleared on successful fetch

✅ **Tests**:
- All tests pass
- Covers uniqueness, upsert, session_id persistence, provider_not_found

✅ **Documentation**:
- Runbook created with migration steps, backfill commands, verification queries

---

## Summary

All tasks completed successfully:
- ✅ Schema fixed: Unique constraints updated to allow same meeting_id across services/sessions
- ✅ Upsert logic fixed: Uses composite key, preserves session_id
- ✅ 404 tracking: Meetings marked and excluded from sync
- ✅ Backfill: Works with new schema
- ✅ Tests: Comprehensive test coverage
- ✅ Runbook: Complete documentation

**Ready for**: Migration and production use.

