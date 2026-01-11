# Meeting Data Hygiene Quick Start

This guide covers utilities for maintaining clean, normalized meeting data in the CODA system.

## Overview

The meeting system uses normalized models:
- **Meeting**: One record per meeting (normalized)
- **MeetingAttendee**: One record per attendee per meeting
- **GotoMeetings**: Legacy denormalized table (read-only, for historical data)

## Import Legacy GoToMeetings Data (No API Calls)

If you have historical meeting data in the legacy `GotoMeetings` table and want to import it into the normalized `Meeting` and `MeetingAttendee` tables without calling GoToMeeting APIs, use the import utility.

### Basic Usage

```bash
# Import all legacy meetings with default service name
poetry run python coda/manage.py import_legacy_gotomeetings

# Import with custom service name
poetry run python coda/manage.py import_legacy_gotomeetings --service gotomeeting_internal

# Import with limit (useful for testing)
poetry run python coda/manage.py import_legacy_gotomeetings --limit 100

# Import meetings created after a specific date
poetry run python coda/manage.py import_legacy_gotomeetings --since 2024-01-01

# Dry run (see what would be imported without saving)
poetry run python coda/manage.py import_legacy_gotomeetings --dry-run
```

### What It Does

1. **Reads from legacy table**: Queries `GotoMeetings` (db_table='getdata_gotomeetings') where `is_active=True`
2. **Groups by meeting_id**: Combines multiple attendee rows into one Meeting record
3. **Normalizes data**:
   - URLs: Removes querystrings and fragments (e.g., `https://example.com/recording?param=value#fragment` → `https://example.com/recording`)
   - Topics: Normalizes topic text (lowercase, trim, remove noise tokens)
   - Datetimes: Best-effort parsing of various date formats
   - Durations: Parses duration strings (minutes, hours:minutes, etc.)
4. **Upserts safely**: 
   - Creates new Meeting/MeetingAttendee records if they don't exist
   - Updates existing records if they do (idempotent - safe to run multiple times)

### Example Output

```
============================================================
Legacy GoToMeeting Import
============================================================
Service name: gotomeeting_external
Limit: 100 rows

============================================================
Import Results
============================================================
Legacy rows scanned: 100
Meetings created: 25
Meetings updated: 0
Attendees created: 75
Attendees updated: 0
Rows skipped: 0
Parse failures: 2

✅ Successfully processed 100 records
```

### After Import

Once imported, you can use the normalized data for:

```bash
# Sample meetings (no API calls needed)
poetry run python coda/manage.py sample_meetings --days 365 --limit 50

# Generate match quality report
poetry run python coda/manage.py match_quality_report --days 365

# Match task links to meetings
poetry run python coda/manage.py match_tasklinks_to_meetings
```

## Normalization Rules

### URL Normalization

- Removes fragment (everything after `#`)
- Removes querystring (everything after `?`)
- Removes trailing slashes
- Example: `https://example.com/recording?param=value#fragment` → `https://example.com/recording`

### Topic Normalization

- Lowercase
- Trim whitespace
- Collapse multiple spaces to single space
- Remove noise tokens: "recording", "session", "meeting", "gotomeeting", "g2m"
- Strip repeated punctuation
- Example: `  Test Meeting RECORDING  ` → `test`

## Best Practices

1. **Always use `--dry-run` first** to see what would be imported
2. **Import in batches** using `--limit` for large datasets
3. **Use `--since`** to import only recent data if needed
4. **Run multiple times safely** - the import is idempotent (won't create duplicates)
5. **Check parse failures** - some legacy data may have unparseable dates/durations

## Troubleshooting

### Parse Failures

If you see parse failures, the import will still proceed but:
- Datetimes may fall back to `created_at` timestamp
- Durations may default to 0
- URLs and topics will still be normalized correctly

### Duplicate Meetings

The import uses `meeting_id` as the unique key. If you have duplicate `meeting_id` values with different data, the import will:
- Use the first non-empty topic found
- Use the first non-empty URL found
- Update existing records if they already exist

### Missing Attendee Emails

Rows without `attendee_email` are skipped for attendee creation, but the meeting will still be created if it has a valid `meeting_id`.
