# DAF / My DAF UAT Checklist

This document provides a manual verification flow for testing the DAF (Development, Activity, Finance) system, specifically the My DAF page and payslip functionality.

## Prerequisites

1. **Database Setup**
   - Cloned production database (`coda_prod_clone`) is available
   - Migrations are up to date
   - The `eunice` user exists with password `MANAGER2030` (local UAT only)

2. **Environment**
   - Development server can be started
   - Poetry environment is activated

## Setup Steps

### 1. Run Migrations

```bash
poetry run python coda/manage.py migrate
```

### 2. Seed Demo Data

Seed demo tasks and TaskHistory for the target month (typically October, the latest month with data):

```bash
# For October 2024 (adjust year as needed)
poetry run python coda/manage.py seed_daf_demo_tasks \
  --username eunice \
  --year=2024 \
  --month=10
```

This command:
- Creates ActivityType records for representative activities (Recruitment, BI Training Session, Daily Update Session, Sprint Planning, Web Sessions)
- Creates Task records linked to those ActivityTypes
- Creates TaskHistory records for the specified month with realistic points/amounts
- Is idempotent (safe to run multiple times)

### 3. Verify Seeded Data

Run the diagnostics command to verify the data was created correctly:

```bash
poetry run python coda/manage.py diagnose_daf \
  --username eunice \
  --year=2024 \
  --month=10
```

Expected output:
- Non-zero `Points Earned` and `Target Points`
- Non-zero `Target Amount`, `Released Total`, `Net Income`
- `Total TaskHistory rows` > 0
- Activity breakdown showing the seeded activities

## Manual Verification Flow

### 4. Start Development Server

```bash
poetry run python coda/manage.py runserver
```

### 5. Login as Eunice

1. Navigate to the login page
2. Login with:
   - Username: `eunice`
   - Password: `MANAGER2030` (local UAT only, never commit or reuse)

### 6. Test My DAF Page

Navigate to:
```
/management/payroll/?username=eunice&pay_type=usertasks
```

**Verify:**

✅ **My DAF (Current Tasks) Summary Cards**
- **Target**: Sum of `mxearning` from all current active tasks (Task model) for that employee
  - Example: If employee has 3 active tasks with mxearning values 2500, 1800, 1200, Target should show Ksh. 5,500.00
- **Earned**: Computed from current active tasks using `(point / mxpoint) * mxearning` per task, summed across all active tasks
- **Pending**: Target - Earned (difference between target amount and earned amount)
- **Points**: Sum of `point` vs. sum of `mxpoint` for active tasks (e.g., "65 / 67")
- **Net Income**: Same as Earned for the current DAF view

**Note**: Cards are computed server-side using `get_current_daf_summary()` from `daf_current_summary_service`. Legacy `/management/api/daf/summary/` is intentionally blocked on this page to prevent overwriting the cards with historical snapshots (which would show zeros).

✅ **Task Table (Current Active Tasks)**
- Table displays current active tasks for eunice (Task model with `is_active=True`)
- Activity names use **canonical names** from ActivityType (e.g., "BI Training Session", "Daily Update Session", "Recruitment") rather than legacy `activity_name` field
- Tasks show points, earnings, evidence status
- Edit/Update links work correctly

✅ **Page Loads Without Errors**
- No 500 errors
- No ModuleNotFoundError
- Page renders completely

### 7. Test Payslip Page

Navigate to:
```
/management/payroll/?username=eunice&pay_type=payslip
```

**Verify:**

✅ **Page Loads Successfully**
- Returns HTTP 200 (not 500)
- No `ModuleNotFoundError: No module named 'management.services.pay_calculation_service'`
- Template renders correctly

✅ **Payslip Data**
- Shows payslip for previous month (legacy behavior)
- If PayCalculationService is available: shows calculated payslip data
- If PayCalculationService is not available: shows empty/zeroed payslip (graceful degradation)

### 8. Test Diagnostics Command

For debugging, run diagnostics for different months:

```bash
# Previous month (typically November if today is December)
poetry run python coda/manage.py diagnose_daf --username eunice

# Specific month with data (October)
poetry run python coda/manage.py diagnose_daf --username eunice --year=2024 --month=10

# Month without data (should show zeros)
poetry run python coda/manage.py diagnose_daf --username eunice --year=2024 --month=11
```

**Expected Results:**
- October (with seeded data): Non-zero metrics
- November (without data): Zero metrics, but no errors
- Summary metrics match what My DAF page shows

## Troubleshooting

### Summary Cards Show Zeros

**Possible Causes:**
1. No TaskHistory data for the previous month
   - **Solution**: Run `seed_daf_demo_tasks` for the target month
   - **Verify**: Use `diagnose_daf` command to check TaskHistory count

2. DAFSummaryService is not finding TaskHistory
   - **Check**: `diagnose_daf` output shows TaskHistory rows
   - **Verify**: `daf_date` field matches the target month/year

3. PayCalculationService is not available
   - **Expected**: Summary should still work (uses TaskHistory directly)
   - **Check**: Logs for warnings about PayCalculationService

### Task Table Shows Legacy Activity Names

**Possible Causes:**
1. Tasks are not linked to ActivityType
   - **Solution**: Run `seed_daf_demo_tasks` which creates tasks with `activity_type` FK
   - **Verify**: Check that Task records have `activity_type` set

2. ActivityType records don't exist
   - **Solution**: `seed_daf_demo_tasks` creates ActivityType records automatically

### Payslip Raises ModuleNotFoundError

**Solution:**
- Verify that `get_pay_service()` helper is used (not direct imports)
- Check that payslip view handles `None` return from `get_pay_service()`
- Review logs for fallback warnings

### Cannot Login as Eunice

**Possible Causes:**
1. User doesn't exist in test DB
   - **Solution**: Ensure you're using cloned production DB, not fresh test DB
   - **Note**: Integration tests use real credentials; unit tests use fixtures

2. Password is incorrect
   - **Verify**: Password is `MANAGER2030` (local UAT only)
   - **Note**: Never commit or reuse these credentials

## Summary

After completing this checklist, you should have verified:

1. ✅ My DAF page loads and shows non-zero summary cards for months with data
2. ✅ Task table displays canonical activity names from ActivityType taxonomy
3. ✅ Payslip page loads without ModuleNotFoundError
4. ✅ Diagnostics command shows correct data aggregation
5. ✅ All functionality works with real user (eunice) from cloned production DB

## Notes

- **Credentials**: The `eunice` / `MANAGER2030` credentials are for **local UAT only**. Never commit these, log them, or reuse them elsewhere.
- **Data Persistence**: Seeded demo data persists in the database. To reset, manually delete TaskHistory/Task records or use database fixtures.
- **My DAF Logic**: My DAF (`pay_type='usertasks'`) uses **current active tasks** (Task model with `is_active=True`) for all summary cards. The cards reflect the current DAF status, not historical snapshots. This differs from Payslip/MyLastDAF which use TaskHistory for historical month-based data.

