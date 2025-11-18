# Fix: NULL daf_date for Tasks Moved on November 4th

## Problem
Tasks moved to TaskHistory on November 4th, 2025 had `daf_date` set to NULL. This caused them not to appear when viewing October's payroll data (last month).

## Root Cause
The `dump_data()` function in `coda_project/task.py` was not setting `daf_date` when creating TaskHistory records. The `daf_date` field represents when the task was actually performed (not when it was moved to history).

## Solution

### 1. Fixed `dump_data()` function
Updated `coda/coda_project/task.py` to set `daf_date` when creating TaskHistory records:
- For tasks submitted this month: Set `daf_date` to same day of last month (e.g., Nov 4 → Oct 4)
- For older tasks: Set `daf_date` to submission date - 1 month

### 2. Enhanced `bulk_update_daf_date()` function
Updated `coda/management/views.py` to fix existing NULL `daf_date` records:
- Handles tasks created this month (sets to same day of last month)
- Handles older tasks (uses submission - 1 month)
- Falls back to `created_at` if `submission` is not available

### 3. Updated Filter Logic
Updated `coda/management/utils.py` `get_tasks()` function to include:
- Tasks with NULL `daf_date` created this month (when viewing last month)
- Tasks with `daf_date` matching selected month/year

## How to Fix Existing Data

### Option 1: Run the bulk update function
```python
from management.views import bulk_update_daf_date
bulk_update_daf_date()
```

### Option 2: Run SQL directly (if needed)
```sql
-- Set daf_date to Oct 4th for tasks created on Nov 4th
UPDATE management_taskhistory
SET daf_date = '2025-10-04'
WHERE created_at >= '2025-11-04 00:00:00'
  AND created_at < '2025-11-05 00:00:00'
  AND daf_date IS NULL;
```

### Option 3: Use the fix script
```bash
python fix_daf_date_nov4.py
```

## Verification
After running the fix, verify:
1. Tasks created on Nov 4th now have `daf_date = 2025-10-04`
2. Payroll page for October shows these tasks
3. Future task moves will have `daf_date` set correctly

## Files Changed
- `coda/coda_project/task.py` - Fixed `dump_data()` to set `daf_date`
- `coda/management/views.py` - Enhanced `bulk_update_daf_date()`
- `coda/management/utils.py` - Updated filter to handle NULL `daf_date`

## Date: November 6, 2025

