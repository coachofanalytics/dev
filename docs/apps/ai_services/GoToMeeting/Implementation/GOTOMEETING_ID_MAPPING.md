# GoToMeeting Identifier Mapping

**Branch:** 25.12_CODA_DEV_CM  
**Date:** 2024-12-30  
**Purpose:** Document GoToMeeting API identifier semantics and how we use them for attendee fetching

---

## Problem Statement

The GoToMeeting API has multiple identifier types that serve different purposes:

1. **`meetingId`** (9-digit code, e.g., "698057837")
   - This is the **meeting room ID** (recurring meeting identifier)
   - Used to identify a meeting room that can host multiple sessions
   - Stored in `Meeting.meeting_id` field

2. **`sessionId`** (long numeric string, e.g., "6646212891239945264")
   - This is the **specific meeting instance/session ID**
   - Identifies a single occurrence of a recurring meeting
   - Available in `historicalMeetings` API response
   - Stored in `Meeting.session_id` field

3. **`meetingInstanceKey`** (long numeric string, e.g., "9876543210987654321")
   - This is the **session-scoped identifier for attendee fetching**
   - Available in attendee API response (each attendee has this field)
   - Used to filter attendees for a specific session
   - Stored in `Meeting.provider_meeting_instance_key` field

---

## API Endpoint Behavior

### `/meetings/{meetingId}/attendees`

**Behavior:**
- Returns **ALL historical attendees** for that meeting room across all sessions
- Does NOT filter by session automatically
- Each attendee object includes `meetingInstanceKey` field

**Example:**
- Meeting room `698057837` has 100 sessions
- Calling `/meetings/698057837/attendees` returns attendees from ALL 100 sessions
- We must filter by `meetingInstanceKey` to get only session-specific attendees

**HTTP Status Codes:**
- `200 OK`: Meeting room exists, returns all historical attendees
- `404 Not Found`: Meeting room does not exist (or wrong account/service)

---

## Solution: Session-Scoped Attendee Fetching

### Step 1: Store Identifiers During Meeting Sync

When ingesting meetings from `historicalMeetings` API:

```python
# Extract from API response
meeting_id = meeting.get('meetingId')  # "698057837"
session_id = meeting.get('sessionId')  # "6646212891239945264"

# Store in Meeting model
Meeting.objects.create(
    meeting_id=meeting_id,
    session_id=session_id,
    # ... other fields
)
```

### Step 2: Extract `meetingInstanceKey` from Attendee Response

When fetching attendees, extract `meetingInstanceKey` from the first attendee:

```python
attendees_data, extracted_instance_key = fetch_attendees_for_meeting(
    meeting_id="698057837",
    access_token=token,
    session_id="6646212891239945264",
    meeting_instance_key=None  # Not known yet
)

# extracted_instance_key = "9876543210987654321" (from first attendee)
```

### Step 3: Filter Attendees by `meetingInstanceKey`

Filter the attendee list to only include attendees matching the session:

```python
# Filter attendees
filtered_attendees = [
    att for att in attendees_data
    if att.get('meetingInstanceKey') == meeting_instance_key
]
```

### Step 4: Store `meetingInstanceKey` for Future Use

Store the extracted `meetingInstanceKey` on the Meeting model:

```python
if extracted_instance_key and not meeting.provider_meeting_instance_key:
    meeting.provider_meeting_instance_key = extracted_instance_key
    meeting.save(update_fields=['provider_meeting_instance_key', 'updated_at'])
```

---

## Database Schema

### `Meeting` Model Fields

```python
meeting_id = CharField(max_length=100, unique=True)
    # GoToMeeting meeting room ID (9-digit code)
    # Example: "698057837"

session_id = CharField(max_length=100, null=True, blank=True)
    # GoToMeeting session ID (specific meeting instance)
    # Example: "6646212891239945264"
    # Available from historicalMeetings API

provider_meeting_instance_key = CharField(max_length=100, null=True, blank=True)
    # GoToMeeting meetingInstanceKey (for session-scoped attendee filtering)
    # Example: "9876543210987654321"
    # Extracted from attendee API response
```

### Indexes

- `session_id` (indexed for fast lookups)
- `provider_meeting_instance_key` (indexed for fast lookups)

---

## Implementation Details

### Meeting Sync (`goto_meeting_sync_service.py`)

**Changes:**
- Extract `sessionId` from `historicalMeetings` API response
- Store `sessionId` in `Meeting.session_id` field

**Code:**
```python
meeting_dict = {
    'meetingId': meeting_id,
    'sessionId': meeting.get('sessionId', ''),  # NEW
    # ... other fields
}
```

### Attendee Sync (`attendee_sync_service.py`)

**Changes:**
- `fetch_attendees_for_meeting()` now:
  - Accepts `meeting_instance_key` parameter
  - Filters attendees by `meetingInstanceKey` if provided
  - Returns `(attendees_list, extracted_instance_key)` tuple
  - Extracts `meetingInstanceKey` from first attendee if not provided

**Code:**
```python
def fetch_attendees_for_meeting(
    meeting_id: str,
    access_token: str,
    session_id: Optional[str] = None,
    meeting_instance_key: Optional[str] = None,  # NEW
    verbose: bool = False
) -> Tuple[List[Dict], Optional[str]]:  # Returns instance key
    # ... fetch attendees
    # ... filter by meetingInstanceKey if provided
    # ... extract instance key from first attendee
    return attendees, extracted_instance_key
```

**Filtering Logic:**
```python
# Filter attendees by meetingInstanceKey
for attendee in attendees_data:
    attendee_instance_key = attendee.get('meetingInstanceKey')
    
    if filter_key and attendee_instance_key and attendee_instance_key != filter_key:
        continue  # Skip attendee from different session
    
    # Process attendee
    attendees.append(attendee)
```

### Backfill Command (`backfill_meeting_instance_keys.py`)

**Purpose:**
- Populate `sessionId` and `provider_meeting_instance_key` for existing meetings
- DB-first: matches existing meetings to API response by (start_time ± tolerance, topic, service_name)
- Extracts `meetingInstanceKey` from attendee response

**Usage:**
```bash
poetry run python coda/manage.py backfill_meeting_instance_keys \
  --service internal \
  --days 120 \
  --limit 50 \
  --verbose
```

---

## Verification

### Check Which Identifier Works

```bash
poetry run python coda/manage.py audit_goto_identifiers \
  --service both \
  --days 7 \
  --limit 5
```

**Output shows:**
- Which fields are available in `historicalMeetings` response
- Which identifier works for `/meetings/{X}/attendees` endpoint
- HTTP status codes for each identifier

### Verify Instance Keys Are Stored

```sql
-- Check meetings with instance keys
SELECT 
    meeting_id,
    session_id,
    provider_meeting_instance_key,
    topic,
    start_time
FROM ai_services_meeting
WHERE provider_meeting_instance_key IS NOT NULL
ORDER BY start_time DESC
LIMIT 10;
```

### Verify Attendee Filtering Works

```sql
-- Check attendee counts per meeting
SELECT 
    m.meeting_id,
    m.provider_meeting_instance_key,
    COUNT(ma.id) as attendee_count
FROM ai_services_meeting m
LEFT JOIN ai_services_meetingattendee ma ON m.id = ma.meeting_id
WHERE m.provider_meeting_instance_key IS NOT NULL
GROUP BY m.id, m.meeting_id, m.provider_meeting_instance_key
ORDER BY attendee_count DESC
LIMIT 10;
```

---

## Troubleshooting

### Issue: External Service Returns 404 for All Meetings

**Root Cause:**
- `meetingId` may not work for external service
- May need `meetingInstanceKey` instead

**Solution:**
1. Run audit: `audit_goto_identifiers --service external`
2. Check if `meetingInstanceKey` works
3. Backfill instance keys: `backfill_meeting_instance_keys --service external`
4. Re-run attendee sync

### Issue: Too Many Attendees (All Historical)

**Root Cause:**
- Not filtering by `meetingInstanceKey`
- Getting attendees from all sessions

**Solution:**
1. Ensure `provider_meeting_instance_key` is populated
2. Verify `fetch_attendees_for_meeting()` filters by instance key
3. Check logs for filtering messages

### Issue: Only 1 Attendee Stored When API Returns Many

**Root Cause:**
- Bug in attendee processing loop
- May be breaking early or not iterating correctly

**Solution:**
- Check `upsert_attendees_for_meeting()` function
- Verify it processes all attendees in the list
- Check for exceptions that might stop processing

---

## Summary

**Identifier Types:**
- `meetingId`: Meeting room ID (9-digit, stored in `meeting_id`)
- `sessionId`: Specific session ID (from `historicalMeetings`, stored in `session_id`)
- `meetingInstanceKey`: Session-scoped identifier (from attendee response, stored in `provider_meeting_instance_key`)

**Attendee Fetching:**
- Endpoint: `/meetings/{meetingId}/attendees`
- Returns: ALL historical attendees for that room
- Filter: By `meetingInstanceKey` to get session-specific attendees

**Implementation:**
- Store `sessionId` during meeting sync
- Extract `meetingInstanceKey` from attendee response
- Filter attendees by `meetingInstanceKey`
- Store `meetingInstanceKey` for future use

**Backfill:**
- Use `backfill_meeting_instance_keys` command to populate existing meetings
- Matches by (start_time ± tolerance, topic, service_name)
- Extracts `meetingInstanceKey` from attendee response

---

## Files Modified

1. **`coda/ai_services/models.py`**
   - Added `session_id` field
   - Added `provider_meeting_instance_key` field
   - Added indexes

2. **`coda/ai_services/services/goto_meeting_sync_service.py`**
   - Extract `sessionId` from API response
   - Store in `Meeting.session_id`

3. **`coda/ai_services/views.py`**
   - Extract `sessionId` from API response
   - Store in `Meeting.session_id`

4. **`coda/ai_services/services/attendee_sync_service.py`**
   - Updated `fetch_attendees_for_meeting()` to filter by `meetingInstanceKey`
   - Extract and return `meetingInstanceKey`
   - Store on Meeting model

5. **`coda/ai_services/management/commands/backfill_meeting_instance_keys.py`** (NEW)
   - Backfill command for existing meetings

6. **`coda/ai_services/management/commands/audit_goto_identifiers.py`** (NEW)
   - Diagnostic command to audit API identifiers

7. **`coda/ai_services/tests/test_attendee_sync.py`**
   - Added tests for instance key storage and filtering

