# Verification Commands for DAF v2 + GoToMeeting Fixes

## Local Verification

### 1. Django System Check
```bash
poetry run python coda/manage.py check
```

### 2. DAF v2 Template Rendering Tests
```bash
poetry run python coda/manage.py test management.tests.test_daf_v2_template_rendering -v 2
```

### 3. Attendee Sync Tests
```bash
poetry run python coda/manage.py test ai_services.tests.test_attendee_sync -v 2
```

### 4. Manual Browser Testing
```bash
# Start server
poetry run python coda/manage.py runserver

# Navigate to:
# http://localhost:8000/management/daf/v2/?user_id=495

# Verify:
# 1. Hover "View Details" - NO FLICKER
# 2. Click "View Details" - Modal opens 100% of the time
# 3. Start Meeting button shows correct enabled/disabled state
# 4. All 3 CTAs are visible on each card
```

## Migration Unblock (if DuplicateColumn error occurs)

### Local Clone DB
```bash
# Step 1: Verify column exists (optional)
poetry run python coda/manage.py dbshell
# In psql: \d accounts_userprofile

# Step 2: Fake the migration
poetry run python coda/manage.py migrate accounts 0003_userprofile_image2 --fake

# Step 3: Continue migrations
poetry run python coda/manage.py migrate
```

### Heroku Production
```bash
# Step 1: Fake the migration
heroku run python coda/manage.py migrate accounts 0003_userprofile_image2 --fake --app <your-app-name>

# Step 2: Continue migrations
heroku run python coda/manage.py migrate --app <your-app-name>
```

## Expected Test Results

### DAF v2 Template Tests
- ✅ All tests pass
- ✅ No FK constraint errors
- ✅ Start Meeting button disabled test passes with mocked mapping

### Attendee Sync Tests
- ✅ All tests pass
- ✅ No "Cannot reorder a query once a slice has been taken" errors
- ✅ Combined name splitting: "A, B, C" → 3 names, "EUNICE, JUDY AND NOREEN" → 3 names
- ✅ Organization names NOT split: "CROWN DATA ANALYSIS..." → 1 name

## Troubleshooting

### If View Details still flickers:
1. Check browser console for JavaScript errors
2. Verify jQuery is loaded before our script
3. Check for multiple Bootstrap versions conflicting
4. Verify `.js-view-details` class is on button (not `.view-details-btn`)

### If tests fail:
1. Check that TaskGroups record exists in test DB
2. Verify `added_by` is set on all TaskLinks
3. Check that mocked `get_meeting_room_for_activity` returns `(None, None)`
