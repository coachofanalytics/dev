# Meeting Model References Audit

## Summary

This document lists all references to Meeting models in the codebase to identify which model/table is canonical for DAF matching.

## Git Grep Results

### 1. `Meeting.objects` references

```bash
git grep -n "Meeting\." coda/
```

**Results**: Found 30+ references across:
- `coda/ai_services/views.py` - Uses `Meeting.objects.get_or_create()`, `Meeting.objects.filter()`
- `coda/ai_services/tasks.py` - Uses `Meeting.objects.get()`
- `coda/ai_services/tests/` - Test files use `Meeting.objects.create()`, `Meeting.objects.filter()`
- `coda/ai_services/views_analytics.py` - Analytics queries use `Meeting.objects.filter()`
- `coda/management/legacy_views.py` - DAF v2 uses `_safe_meeting_query()` which queries `Meeting.objects`
- `coda/management/services/` - Services use `Meeting.objects.filter()`

**Canonical Model**: `ai_services.models.Meeting`

### 2. `gotomeeting_meeting` table name

```bash
git grep -n "gotomeeting_meeting" coda/
```

**Results**: 
- `coda/ai_services/models.py:204` - **COMMENTED OUT**: `# db_table = 'gotomeeting_meeting'`

**Status**: This table name is NOT used. It was commented out.

### 3. `getdata_gotomeetings` table name

```bash
git grep -n "getdata_gotomeetings" coda/
```

**Results**:
- `coda/ai_services/models.py:122` - `db_table = 'getdata_gotomeetings'` (GotoMeetings legacy model)
- `coda/ai_services/models.py:204` - `db_table = 'getdata_gotomeetings'` (Meeting model - **ACTIVE**)

**Status**: This is the ACTIVE table name for the canonical `Meeting` model.

### 4. `GotoMeetings` legacy model

```bash
git grep -n "GotoMeetings" coda/
```

**Results**:
- `coda/ai_services/models.py:99` - `class GotoMeetings(models.Model):` - Legacy model, deprecated
- `coda/ai_services/admin.py` - Admin registration for legacy model
- `coda/ai_services/management/commands/migrate_gotomeeting_data.py` - Migration command from legacy to new

**Status**: Legacy model, kept for backward compatibility during migration.

## Canonical Model for DAF Matching

**Model**: `ai_services.models.Meeting`
**Table**: `getdata_gotomeetings`
**DB Table Check**: `_safe_meeting_query()` in `coda/management/legacy_views.py` checks for `'getdata_gotomeetings'`

## Code Comments

### In `coda/management/legacy_views.py`:

```python
def _safe_meeting_query(*args, **filter_kwargs):
    """
    Safely query Meeting model, handling case where table doesn't exist.
    
    CANONICAL: Uses ai_services.models.Meeting which maps to 'getdata_gotomeetings' table.
    This is the single source of truth for meeting queries in DAF v2 and evidence matching.
    """
    # ... implementation checks for 'getdata_gotomeetings' table
```

### In `coda/ai_services/models.py`:

```python
class Meeting(models.Model):
    """
    Normalized meeting model - one record per meeting.
    Replaces denormalized GotoMeetings model.
    
    CANONICAL: This is the active model for all meeting-related queries.
    Table: getdata_gotomeetings (legacy table name, kept for compatibility)
    """
    # ... fields ...
    
    class Meta:
        db_table = 'getdata_gotomeetings'  # Active table name
        # Note: 'gotomeeting_meeting' was never used (commented out)
```

## Migration Path

1. **Legacy**: `GotoMeetings` model → `getdata_gotomeetings` table (deprecated)
2. **Current**: `Meeting` model → `getdata_gotomeetings` table (canonical)
3. **Future**: Could migrate to `gotomeeting_meeting` table if needed, but currently NOT in use

## Verification

- ✅ All DAF matching code uses `ai_services.models.Meeting`
- ✅ Table name is `getdata_gotomeetings` (verified in DB)
- ✅ `_safe_meeting_query()` correctly checks for `'getdata_gotomeetings'`
- ✅ No active code references `'gotomeeting_meeting'` table

