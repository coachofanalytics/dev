# Meeting Data Hygiene & Match Quality Report

## Overview

This document describes how to analyze meeting data hygiene and match quality using the new operational tooling commands.

## Commands Available

### 1. Sample Meetings (`sample_meetings`)

Analyzes existing meeting data in the database and exports normalized fields.

**Usage:**
```bash
# Basic analysis (last 14 days, 25 samples)
poetry run python coda/manage.py sample_meetings

# Extended analysis (last 30 days, 50 samples)
poetry run python coda/manage.py sample_meetings --days 30 --limit 50

# Export to CSV with all normalized fields
poetry run python coda/manage.py sample_meetings --days 30 --limit 100 --export /tmp/meetings_sample.csv
```

**Output includes:**
- Total meetings, recorded percentage, URL availability
- Top 20 normalized topic patterns
- Candidate activity tags distribution
- Sample rows with:
  - `meeting_id`, `start_time`, `duration_minutes`
  - `topic` (raw), `topic_normalized` (computed/stored)
  - `service_name` (gotomeeting_external/internal or null)
  - `has_recording_url`, `has_download_url`, `is_recorded`
  - `candidate_tags` (comma-separated activity tags)

**CSV Export Fields:**
- `meeting_id`
- `start_time` (ISO format)
- `duration_minutes`
- `topic` (raw)
- `topic_normalized` (normalized)
- `service_name`
- `has_recording_url` (boolean)
- `has_download_url` (boolean)
- `is_recorded` (boolean)
- `attendee_count`
- `candidate_tags` (comma-separated)

### 2. Match Quality Report (`match_quality_report`)

Shows match rates by activity type and service, plus top unmatched patterns.

**Usage:**
```bash
# Basic report (last 30 days)
poetry run python coda/manage.py match_quality_report

# Filter by service
poetry run python coda/manage.py match_quality_report --service external
poetry run python coda/manage.py match_quality_report --service internal

# Extended date range
poetry run python coda/manage.py match_quality_report --days 60

# Export to CSV
poetry run python coda/manage.py match_quality_report --days 30 --export /tmp/match_quality.csv
```

**Output includes:**
- Overall match rate (matched tasks / total tasks)
- Match rate by activity type (top 20):
  - Total tasks
  - Matched tasks
  - URL matches vs topic matches
  - Match rate percentage
- Match rate by service (if applicable):
  - Service name (gotomeeting_external/internal)
  - Total tasks, matched tasks, match rate
- Top unmatched patterns (evidence URL patterns that didn't match)

**CSV Export Fields:**
- `activity_name`
- `total_tasks`
- `matched_tasks`
- `url_matches`
- `topic_matches`
- `match_rate_pct`

### 3. Match TaskLinks to Meetings (`match_tasklinks_to_meetings`)

Detailed matching analysis for specific tasks or users (enhanced with verbose output).

**Usage:**
```bash
# Analyze specific task
poetry run python coda/manage.py match_tasklinks_to_meetings --task-id 123 --verbose

# Analyze user's recent tasks
poetry run python coda/manage.py match_tasklinks_to_meetings --user-id 5 --days 14 --verbose

# Show URL normalization and match reasons
poetry run python coda/manage.py match_tasklinks_to_meetings --task-id 123 --verbose
```

**Verbose Output Includes:**
- Match type (url/topic)
- Confidence score (0.0-1.0)
- Service name
- Match reason (for topic matches):
  - Tag overlap details
  - Common words
  - Employee/department matches
- Normalized evidence URLs

## Data Hygiene Checks

### Check Topic Normalization Coverage

```bash
poetry run python coda/manage.py shell -c "
from ai_services.models import Meeting
from ai_services.utils.meeting_normalizer import normalize_topic

total = Meeting.objects.count()
with_normalized = Meeting.objects.exclude(topic_normalized='').count()
coverage = (with_normalized / total * 100) if total > 0 else 0

print(f'Total meetings: {total}')
print(f'With normalized topic: {with_normalized} ({coverage:.1f}%)')
print(f'Missing normalized topic: {total - with_normalized}')
"
```

### Check Service Name Distribution

```bash
poetry run python coda/manage.py shell -c "
from ai_services.models import Meeting
from django.db.models import Count

distribution = Meeting.objects.values('service_name').annotate(count=Count('id')).order_by('-count')
print('Service Name Distribution:')
for item in distribution:
    service = item['service_name'] or '(null)'
    print(f'  {service}: {item[\"count\"]} meetings')
"
```

### Check Candidate Tags Coverage

```bash
poetry run python coda/manage.py shell -c "
from ai_services.models import Meeting
from ai_services.utils.meeting_normalizer import extract_candidate_activity_tags

total = Meeting.objects.count()
with_tags = 0

for meeting in Meeting.objects.all()[:1000]:  # Sample first 1000
    if meeting.topic:
        tags = extract_candidate_activity_tags(meeting.topic)
        if tags:
            with_tags += 1

print(f'Sample size: 1000 meetings')
print(f'With candidate tags: {with_tags} ({with_tags/10:.1f}%)')
"
```

## Match Quality Analysis Workflow

### Step 1: Sample Meeting Data

```bash
# Get overview of meeting data quality
poetry run python coda/manage.py sample_meetings --days 30 --export /tmp/meetings_sample.csv
```

**Review:**
- Are topics normalized consistently?
- Are service_names populated correctly?
- Do candidate tags align with activity types?

### Step 2: Generate Match Quality Report

```bash
# Analyze match rates
poetry run python coda/manage.py match_quality_report --days 30 --export /tmp/match_quality.csv
```

**Review:**
- Which activity types have low match rates?
- Are URL matches more reliable than topic matches?
- What are the top unmatched patterns?

### Step 3: Deep Dive on Unmatched Tasks

```bash
# For a specific activity type with low match rate, find sample tasks
poetry run python coda/manage.py shell -c "
from management.models import Task
tasks = Task.objects.filter(activity_name='Your Activity Name', is_active=True)[:10]
for task in tasks:
    print(f'Task {task.id}: {task.activity_name} (submitted: {task.submission})')
"
```

```bash
# Analyze specific task matching
poetry run python coda/manage.py match_tasklinks_to_meetings --task-id <task_id> --verbose
```

**Review:**
- Why didn't URL matching work? (check URL normalization)
- Why didn't topic matching work? (check tag overlap, time window)
- What match reason was given?

### Step 4: Fix Data Issues

Based on analysis, you might need to:

1. **Backfill topic_normalized** for existing meetings:
   ```bash
   poetry run python coda/manage.py shell -c "
   from ai_services.models import Meeting
   from ai_services.utils.meeting_normalizer import normalize_topic
   
   meetings = Meeting.objects.filter(Q(topic_normalized='') | Q(topic_normalized__isnull=True))
   print(f'Backfilling {meetings.count()} meetings...')
   
   for meeting in meetings:
       if meeting.topic:
           meeting.topic_normalized = normalize_topic(meeting.topic)
           meeting.save(update_fields=['topic_normalized'])
   
   print('Done!')
   "
   ```

2. **Backfill service_name** for existing meetings (if you can infer from meeting patterns):
   ```bash
   # Example: Set service_name based on meeting patterns
   poetry run python coda/manage.py shell -c "
   from ai_services.models import Meeting
   
   # This is just an example - adjust logic based on your data
   Meeting.objects.filter(service_name__isnull=True).update(service_name='gotomeeting_external')
   "
   ```

3. **Re-run sync** to populate normalized fields for new meetings:
   ```bash
   poetry run python coda/manage.py sync_goto_meetings_if_stale --service external --force --hours 24
   ```

## Interpreting Results

### High Match Rate (>80%)
- ✅ Good data quality
- ✅ URLs/topics are consistent
- ✅ Normalization working correctly

### Medium Match Rate (50-80%)
- ⚠️ Some data quality issues
- Check unmatched patterns for common issues
- Consider improving normalization rules

### Low Match Rate (<50%)
- ❌ Significant data quality issues
- Review:
  - URL normalization (are evidence URLs in expected format?)
  - Topic normalization (are topics too noisy?)
  - Activity tag extraction (are tags being generated correctly?)
  - Service name tagging (are meetings tagged correctly?)

### URL Match Rate vs Topic Match Rate

- **High URL match rate**: Evidence URLs are consistent, normalization working well
- **High topic match rate, low URL match rate**: Evidence URLs vary, but topics align well
- **Both low**: Data quality issues or normalization needs improvement

## Best Practices

1. **Run sample_meetings weekly** to monitor data quality trends
2. **Run match_quality_report monthly** to track match rate improvements
3. **Backfill missing normalized fields** after schema changes
4. **Use verbose output** when debugging specific unmatched tasks
5. **Review top unmatched patterns** to identify systematic issues

## Troubleshooting

### Issue: topic_normalized is empty for existing meetings

**Solution**: Run backfill script (see Step 4 above)

### Issue: service_name is null for all meetings

**Solution**: 
- New syncs will populate service_name automatically
- For existing meetings, backfill if you can infer from patterns
- Or leave as null for backward compatibility (matcher handles this)

### Issue: Match rate is lower than expected

**Possible causes:**
1. Evidence URLs don't match normalized meeting URLs
2. Activity tags don't overlap (stricter matching requires overlap)
3. Time window too narrow (default ±2 days)
4. Service name mismatch (external vs internal)

**Diagnosis:**
- Run `match_tasklinks_to_meetings --verbose` on sample tasks
- Review match reasons to see why matches failed
- Check URL normalization in sample_meetings output


