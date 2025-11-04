# Employee Activity System (Management) – 06_MAINTENANCE.md

## Operations (How to maintain)
- Monitor background jobs and AI health via `AIHealthChecker` logs.
- Review activity linking accuracy weekly; tune heuristics/keywords.
- Keep `deprecated/` clean; remove once safely unused.

## Runbooks
### Re‑index TaskHistory
```bash
python manage.py shell -c "from management.services import maintenance; maintenance.rebuild_indexes()"
```

### Reprocess Links for a Date Range
```bash
python manage.py reprocess_links --from 2025-10-01 --to 2025-10-31
```

## Known Issues
- Meeting vendor rate limits can delay evidence ingestion → batch + backoff.
- Historical gaps from manual entries → run backfill job before analytics.

## Recent Fixes (November 2025)

### ✅ Task List Pagination Missing (Fixed Nov 4, 2025)
**Symptom:** Users could only see 4 employees in task list, despite 16 employees having 375 total tasks.

**Root Cause:**
- View (`TaskListView`) paginated to 20 tasks per page
- Template (`tasklist.html`) had NO pagination controls
- Result: Only first 20 tasks visible (happened to be from 4 employees)

**Fix Applied:**
- Added Bootstrap pagination controls to template
- Shows: Previous/Next, page numbers, First/Last buttons
- Displays: "Page X of Y (Showing start-end of total tasks)"

**Files Changed:**
- `coda/management/templates/management/daf/tasklist.html` (lines 117-178)

**Verification:**
```bash
# Production has 375 tasks across 16 employees
# Now accessible via 19 pages (20 tasks per page)
```

**Deployment:**
- UAT: commit 57e3bb758
- Production: v1776 (www.codanalytics.net)

**Impact:** All employees with tasks now visible and accessible ✅

## Backups & Data Safety
- Never run experiments on production DB. Use cloned DB per CURSOR_AI_GUIDE.
- Ensure env vars for vendor APIs are present in UAT/Prod before enabling jobs.

## Upgrade Notes
- When updating AI providers, validate through `AIConfigurationService` staging keys first.
