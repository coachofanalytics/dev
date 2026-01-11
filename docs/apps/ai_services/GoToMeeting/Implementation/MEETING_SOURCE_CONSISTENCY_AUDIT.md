# Meeting Source Consistency Audit

## Summary

**Canonical Meeting Model:** `ai_services.models.Meeting`  
**Canonical Table:** `ai_services_meeting` (Django default, not `gotomeeting_meeting`)

## Meeting Models Found

| Model | File | DB Table | Status | Purpose |
|-------|------|----------|--------|---------|
| `ai_services.Meeting` | `coda/ai_services/models.py:127` | `ai_services_meeting` | ✅ **CANONICAL** | Normalized meeting model (one record per meeting) |
| `ai_services.GotoMeetings` | `coda/ai_services/models.py:99` | `getdata_gotomeetings` | ⚠️ Legacy | Deprecated denormalized model (kept for backward compatibility) |
| `management.Meetings` | `coda/management/models.py:1318` | `management_meetings` | ❓ Unrelated | Different model (not used for DAF/evidence matching) |

## Compliance Code Usage

### ✅ Correct Usage (ai_services.Meeting)

| Location | Usage | Status |
|----------|-------|--------|
| `coda/management/legacy_views.py:2848` | `_safe_meeting_query()` - DAF v2 meeting matching | ✅ Fixed (now checks `Meeting._meta.db_table`) |
| `coda/ai_services/services/meeting_evidence_matcher.py` | Evidence-to-meeting matching | ✅ Correct |
| `coda/ai_services/views.py` | Meeting sync/persistence | ✅ Correct |
| `coda/management/legacy_views.py:2961` | Compliance check for meeting evidence | ✅ Correct |

### ⚠️ Legacy References (getdata_gotomeetings)

| Location | Usage | Action |
|----------|-------|--------|
| `coda/ai_services/services/legacy_gotomeeting_import_service.py` | One-time import from legacy table | ✅ OK (explicit migration tool) |
| `coda/management/legacy_views.py:2865` | Old table check (now fixed) | ✅ Fixed |

## Enforcement

**Rule:** All compliance/UI logic MUST query only `ai_services.Meeting` (through `Meeting._meta.db_table` implicitly).

**Implementation:**
- `_safe_meeting_query()` now uses `Meeting._meta.db_table` (dynamic, not hardcoded)
- All meeting queries in compliance code use `ai_services.models.Meeting`
- Legacy `getdata_gotomeetings` is only used for one-time migration commands

## Migration Command (Optional)

If `ai_services.Meeting` is empty but `getdata_gotomeetings` has rows:
- Use existing command: `import_legacy_gotomeetings`
- Location: `coda/ai_services/management/commands/import_legacy_gotomeetings.py`
- This is explicit, not automatic

## Verification

```bash
# Check actual table names
poetry run python coda/manage.py shell -c "
from ai_services.models import Meeting, GotoMeetings
print(f'Meeting table: {Meeting._meta.db_table}')
print(f'GotoMeetings table: {GotoMeetings._meta.db_table}')
"
# Expected: ai_services_meeting, getdata_gotomeetings
```

