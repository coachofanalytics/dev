# DAF v2 + GoToMeeting Production Deployment Checklist

**Branch:** 25.12_CODA_DEV_CM  
**Date:** 2024-12-30

---

## Pre-Deployment Verification (Local)

### 1. Django System Check

```bash
cd /Users/coda/Projects/uat/coda
poetry run python manage.py check
```

**Expected:** No errors or warnings

### 2. Run Critical Tests

```bash
# DAF v2 template rendering tests
poetry run python manage.py test management.tests.test_daf_v2_template_rendering -v 2

# Attendee sync tests
poetry run python manage.py test ai_services.tests.test_attendee_sync -v 2

# Meeting uniqueness tests
poetry run python manage.py test ai_services.tests.test_meeting_uniqueness_fix -v 2
```

**Expected:** All tests pass

### 3. Verify No Import Errors

```bash
# Start server and check for import errors
poetry run python manage.py runserver --noreload 2>&1 | grep -i "error\|import\|circular" | head -20
```

**Expected:** No import or circular import errors

### 4. Verify Migrations Status

```bash
# Check migration status
poetry run python manage.py showmigrations ai_services management

# Check for unapplied migrations
poetry run python manage.py migrate --plan
```

**Expected:** All migrations applied or ready to apply

---

## Heroku Deployment Steps

### Step 1: Run Migrations

```bash
heroku run python coda/manage.py migrate --app codamakutano
```

**Expected:** All migrations apply successfully

**Note:** If you see errors about `duration_minutes is ambiguous`, check for raw SQL queries and ensure columns are qualified with table aliases (e.g., `m.duration_minutes` for Meeting, `ma.duration_minutes` for MeetingAttendee).

### Step 2: Collect Static Files

```bash
heroku run python coda/manage.py collectstatic --noinput --app codamakutano
```

**Expected:** Static files collected successfully

### Step 3: Verify Attendee Sync

```bash
heroku run python coda/manage.py diagnose_attendee_sync --service all --days 30 --app codamakutano
```

**Expected:** Report shows sync status, no critical errors

### Step 4: Generate Meeting Room Mapping Report

```bash
heroku run python coda/manage.py report_activity_meeting_candidates --service internal --days 60 --app codamakutano
```

**Expected:** Report shows activity → meeting ID candidates

**Optional:** If you want to seed mappings (dry-run first):

```bash
# Dry run
heroku run python coda/manage.py report_activity_meeting_candidates --service internal --days 60 --seed-mapping --dry-run --app codamakutano

# Actual seeding (if dry-run looks good)
heroku run python coda/manage.py report_activity_meeting_candidates --service internal --days 60 --seed-mapping --no-dry-run --app codamakutano
```

---

## Post-Deployment Verification

### 1. Check DAF v2 UI

1. Navigate to `/management/daf/v2/` on Heroku
2. Verify:
   - ✅ Cards render without flicker
   - ✅ "View Details" button opens modal (no hover flicker)
   - ✅ Density toggle works (Compact/Comfortable)
   - ✅ Start Meeting button shows correct state
   - ✅ Staff users see "Meeting Config" in modal

### 2. Verify Meeting Room Mapping

1. Check a few activities that require meetings
2. Verify Start Meeting button is enabled/disabled correctly
3. For staff: Check "Meeting Config" section in modal shows correct mapping source

### 3. Check Attendee Sync

```bash
heroku run python coda/manage.py diagnose_attendee_sync --service all --days 7 --app codamakutano
```

**Expected:** Recent meetings have attendees synced

---

## Rollback Plan

If issues occur:

1. **Revert migrations** (if needed):
   ```bash
   heroku run python coda/manage.py migrate ai_services <previous_migration> --app codamakutano
   ```

2. **Check logs**:
   ```bash
   heroku logs --tail --app codamakutano | grep -i "error\|exception"
   ```

3. **Verify database state**:
   ```bash
   heroku run python coda/manage.py shell --app codamakutano
   # Then in shell:
   from ai_services.models import Meeting, MeetingAttendee
   print(f"Meetings: {Meeting.objects.count()}")
   print(f"Attendees: {MeetingAttendee.objects.count()}")
   ```

---

## Known Issues & Fixes

### Issue: "duration_minutes is ambiguous" SQL Error

**Fix:** Ensure all raw SQL queries qualify column names:
- Use `m.duration_minutes` for Meeting table
- Use `ma.duration_minutes` for MeetingAttendee table

**Status:** ✅ Fixed in Django ORM queries (no raw SQL found with this issue)

### Issue: View Details Button Flicker

**Fix:** 
- Removed `title` attribute from modal trigger buttons
- Initialized tooltips once on page load
- Prevented tooltip/modal conflicts

**Status:** ✅ Fixed

### Issue: Circular Import (management/utils)

**Fix:** Renamed `management/utils.py` to `management/utils/` package structure

**Status:** ✅ Fixed

---

## Quick Reference Commands

```bash
# Local checks
poetry run python manage.py check
poetry run python manage.py test management.tests.test_daf_v2_template_rendering -v 2

# Heroku deployment
heroku run python coda/manage.py migrate --app codamakutano
heroku run python coda/manage.py collectstatic --noinput --app codamakutano
heroku run python coda/manage.py diagnose_attendee_sync --service all --days 30 --app codamakutano
heroku run python coda/manage.py report_activity_meeting_candidates --service internal --days 60 --app codamakutano
```

---

**End of Checklist**

