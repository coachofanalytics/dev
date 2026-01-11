# AI Operations Runbook

**AI-4: AI Operations + Observability + "Visible Behavior" Loop**

This document provides operational guidance for running and monitoring AI operations in the CODA DAF system.

## Overview

AI Operations orchestrates daily runs of:
- **AI-1**: Meeting activity tagging (shadow mode)
- **AI-2**: Requirement match verification (shadow mode)
- **AI-3**: Manager review suggestions (shadow mode)

All operations are **shadow mode only** - they never auto-approve or change data. Results are stored in `AIOperationsRun` for observability.

## Feature Flags

### Required Flags
- `AI_ENABLED`: Master flag (must be `True` for AI calls)
- `AI_OPS_ENABLED`: Enable AI operations service (default: `False`)

### Optional Flags
- `AI_REQUIREMENT_MATCH_ENABLED`: Enable AI-2 requirement matching
- `AI_REVIEW_ASSIST_ENABLED`: Enable AI-3 review suggestions
- `AI_SHADOW_MODE`: Always `True` for operations (advisory only)

## Commands

### 1. Check AI Settings

Verify AI configuration before running operations:

```bash
poetry run python coda/manage.py check_ai_settings
```

**Output:**
- OpenAI API key presence (last 4 chars only)
- Claude API key presence
- Active `AIModelConfiguration` rows
- LangChain installation status
- Feature flag values

**Safety:** Never prints full API keys.

### 2. Run AI Daily Operations

Run daily AI operations for meetings and tasks:

```bash
poetry run python coda/manage.py run_ai_daily_ops [options]
```

**Options:**
- `--days N`: Number of days to look back (default: 1)
- `--limit N`: Optional limit on number of items to process
- `--service NAME`: Optional service filter (e.g., "external", "internal")
- `--dry-run`: Count only, no actual changes
- `--export PATH`: Export results to CSV file

**Examples:**

```bash
# Run for last 24 hours
poetry run python coda/manage.py run_ai_daily_ops

# Run for last 7 days, limit to 100 items
poetry run python coda/manage.py run_ai_daily_ops --days 7 --limit 100

# Dry run (no changes)
poetry run python coda/manage.py run_ai_daily_ops --dry-run

# Export results to CSV
poetry run python coda/manage.py run_ai_daily_ops --export /tmp/ai_ops_$(date +%Y%m%d).csv
```

**Output:**
- Summary table with counts for AI-1, AI-2, AI-3
- Run ID for tracking
- Error counts and samples

**Behavior:**
- If `AI_OPS_ENABLED=False`: Returns "skipped" status, creates no run record
- If `AI_ENABLED=False`: Uses rule-based fallback, still creates run record
- Never raises uncaught exceptions; stores errors in `AIOperationsRun`

### 3. Generate KPI Report

Generate CSV report with coverage metrics and failure analysis:

```bash
poetry run python coda/manage.py ai_kpi_report --days 30 --export /path/to/report.csv
```

**Required Arguments:**
- `--days N`: Number of days to analyze (default: 30)
- `--export PATH`: Export path for CSV file (required)

**Output CSV Columns:**
- Date range (start, end, days)
- AI-1 metrics: total meetings, tagged meetings, coverage %, avg confidence, confidence distribution
- AI-3 metrics: tasks in queue, tasks with suggestions, coverage %
- AI-2 metrics: tasks with requirements, tasks with checks, coverage %
- Operations runs: total, failed, partial
- Top 10 failure reasons

**Console Output:**
- Summary of all metrics
- Top 10 failure reasons

**Example:**

```bash
poetry run python coda/manage.py ai_kpi_report --days 30 --export /tmp/ai_kpi_$(date +%Y%m%d).csv
```

## Scheduling

### Recommended: Daily at 7am

**Cron:**
```bash
0 7 * * * cd /path/to/uat/coda && poetry run python manage.py run_ai_daily_ops --days 1 >> /var/log/ai_ops.log 2>&1
```

**Celery Beat:**
```python
# In celerybeat_schedule
'run-ai-daily-ops': {
    'task': 'ai_services.tasks.run_ai_daily_ops_task',
    'schedule': crontab(hour=7, minute=0),
},
```

### Weekly KPI Report

Generate weekly KPI report every Monday:

```bash
0 8 * * 1 cd /path/to/uat/coda && poetry run python manage.py ai_kpi_report --days 7 --export /tmp/ai_kpi_weekly_$(date +\%Y\%m\%d).csv
```

## UI Integration

### Manager Review Page

Staff/superuser can:
- View latest AI operations run status
- See coverage numbers (meetings tagged, AI reviews created)
- Trigger AI daily ops run via "Run AI Daily Ops" button

**Location:** `/management/daf/review/`

**Panel shows:**
- Last run status (SUCCESS/FAILED/PARTIAL/SKIPPED)
- Last run timestamp
- Meetings tagged counts (created, cached)
- AI reviews counts (created, cached)
- Error count (if any)

## Safety Notes

### No Auto-Approval
- **All operations are shadow mode only**
- AI suggestions are advisory
- No tasks are auto-approved
- No points are auto-awarded
- No data is modified without human review

### Feature Flag Gating
- Operations require `AI_OPS_ENABLED=True`
- AI calls require `AI_ENABLED=True`
- If AI is disabled, operations use rule-based fallback
- Fallback results are still tracked in `AIOperationsRun`

### Error Handling
- Operations never raise uncaught exceptions
- Errors are stored in `AIOperationsRun.error_samples` (capped at 10)
- Run status reflects error count (SUCCESS/PARTIAL/FAILED)

### No Secrets in Logs
- API keys are never logged
- Error messages are truncated to 200 chars
- CSV exports contain no sensitive data

## Monitoring

### Check Run Status

```python
from ai_services.models import AIOperationsRun

# Latest run
latest = AIOperationsRun.objects.order_by('-started_at').first()
print(f"Status: {latest.status}")
print(f"Errors: {latest.errors_count}")
print(f"Meetings tagged: {latest.meetings_tagged_created}")
print(f"AI reviews: {latest.ai_reviews_created}")
```

### Check Coverage

```python
from ai_services.models import Meeting, MeetingActivityTagSuggestion
from management.models import Task, TaskAIReviewSuggestion

# AI-1 coverage
total_meetings = Meeting.objects.filter(start_time__gte=cutoff_date).count()
tagged = MeetingActivityTagSuggestion.objects.filter(
    meeting__start_time__gte=cutoff_date,
    is_active=True
).values('meeting').distinct().count()
coverage = (tagged / total_meetings * 100) if total_meetings > 0 else 0
print(f"AI-1 Coverage: {coverage:.1f}%")
```

## Troubleshooting

### Operations Skipped
- Check `AI_OPS_ENABLED` flag: `python manage.py check_ai_settings`
- Verify flag is set in environment or `base_settings.py`

### All Fallback Results
- Check `AI_ENABLED` flag: `python manage.py check_ai_settings`
- Verify API keys are configured
- Check `AIModelConfiguration` rows are active

### High Error Count
- Check `AIOperationsRun.error_samples` for details
- Review logs for specific error messages
- Verify database migrations are applied
- Check network connectivity for AI API calls

### Missing Data
- Verify migrations are applied: `python manage.py migrate`
- Check that meetings/tasks exist in date range
- Verify service filters match actual data

## Testing

All tests mock AI services - no API keys required:

```bash
# Run AI operations tests
poetry run python coda/manage.py test ai_services.tests.test_ai_operations -v 2

# Run all AI tests
poetry run python coda/manage.py test ai_services.tests management.tests.test_ai_requirement_matching management.tests.test_ai_review_assistant -v 2
```

## Files Modified

- `coda/coda_project/coda_settings/base_settings.py`: Added `AI_OPS_ENABLED` flag
- `coda/ai_services/models.py`: Added `AIOperationsRun` model
- `coda/ai_services/services/ai_operations_service.py`: New service
- `coda/ai_services/management/commands/run_ai_daily_ops.py`: New command
- `coda/ai_services/management/commands/ai_kpi_report.py`: New command
- `coda/management/legacy_views.py`: Added AI ops status to review view
- `coda/management/templates/management/daf/review.html`: Added AI ops panel
- `coda/management/urls.py`: Added AI ops run endpoint

## Verification

After implementation:

```bash
# Check syntax
poetry run python -m py_compile coda/ai_services/services/ai_operations_service.py
poetry run python -m py_compile coda/ai_services/models.py

# Run Django check
poetry run python coda/manage.py check

# Run tests
poetry run python coda/manage.py test ai_services.tests.test_ai_operations -v 2

# Test commands (dry run)
poetry run python coda/manage.py run_ai_daily_ops --dry-run
poetry run python coda/manage.py ai_kpi_report --days 7 --export /tmp/test_kpi.csv
```


