# Current System Snapshot: Meeting → Attendee → Employee → Task → TaskLink → DAF

**Date:** 2026-01-02  
**Branch:** 26.01_CODA_DEV_CM  
**Purpose:** Reconstruct and explain the CURRENT end-to-end logic for meeting → attendee → employee resolution → task matching → tasklink creation → DAF meeting-count updates.

---

## 1. Ingestion: GoToMeeting → Meeting/Attendee Tables

### 1.1 Meeting Sync Flow

**File:** `coda/ai_services/services/goto_meeting_sync_service.py`

**Entry Point:** `sync(start_dt, end_dt, service_name)` (line 216)

**Process:**
1. Gets OAuth token via `get_access_token(service_name)` (line 254)
2. Calls `fetch_meetings(start_dt, end_dt, access_token)` (line 269)
3. Calls `upsert_meetings(meetings_json, service_name)` (line 290)

**Meeting Fetching (`fetch_meetings`, line 19):**
- **API Endpoint:** `GET https://api.getgo.com/G2M/rest/historicalMeetings?startDate={start_str}&endDate={end_str}` (line 45)
- **Fields Extracted:**
  - `meetingId` → `meeting_id` (line 58)
  - `subject` → `topic` (line 136)
  - `meetingType` → `meeting_type` (line 137)
  - `startTime` → `start_time` (line 138)
  - `endTime` → `end_time` (line 139)
  - `duration` → `duration_minutes` (line 140)
  - `sessionId` → `session_id` (line 97)
  - `meetingInstanceKey` → `meeting_instance_key` (line 100, if present)
  - `recording.shareUrl` / `recording.downloadUrl` → normalized to `recording_url` (lines 80-86)
  - `email` → stored in meeting dict (line 141)

**Key Code Snippet:**
```python
# Line 129-144: Meeting dict construction
meeting_dict = {
    'meetingId': meeting_id,
    'sessionId': session_id,
    'meetingInstanceKey': meeting_instance_key,
    'downloadUrl': download_url or '',
    'recording': recording_url_for_dict,  # Only canonical URL or empty
    'recording_url_source': recording_url_source_for_dict,  # 'provider' or None
    'subject': meeting.get('subject', 'Untitled Meeting'),
    'meetingType': meeting.get('meetingType', ''),
    'startTime': meeting.get('startTime', ''),
    'endTime': meeting.get('endTime', ''),
    'duration': meeting.get('duration', 0),
    'email': meeting.get('email', ''),
    'attendeeNames': [],
    'attendee_Info': []  # Empty - attendees synced separately
}
```

**Note:** Attendee fetching is **REMOVED** from meeting sync (line 156-159). Attendees are synced separately via `sync_meeting_attendees` command.

**Meeting Persistence (`upsert_meetings`, line 188):**
- Calls `save_meeting_data(meetings_json)` from `coda/ai_services/views.py` (line 212)
- Adds `service_name` to each meeting dict if provided (lines 206-208)

**File:** `coda/ai_services/views.py` → `save_meeting_data()` (line 414)

**Process:**
1. Parses meeting dicts (supports both camelCase and snake_case, lines 456-465)
2. Extracts `meetingId`, `subject`, `startTime`, `endTime`, `recording`, etc.
3. Normalizes transcript URL via `normalize_gotomeeting_transcript_url()` (line 541)
4. Creates/updates `Meeting` record:
   - **Table:** `ai_services_meeting`
   - **Unique constraint:** `meeting_id` (line 457)
   - **Fields set:**
     - `meeting_id` (line 457)
     - `topic` (line 462)
     - `topic_normalized` (via `normalize_topic()`, line 571)
     - `service_name` (line 568)
     - `meeting_type` (line 463)
     - `start_time` (line 475)
     - `end_time` (line 513)
     - `duration_minutes` (line 520)
     - `recording_url` (only if canonical, line 555-558)
     - `recording_url_source` (line 557)
     - `session_id` (line 572)
     - `meeting_instance_key` (line 574)
     - `requirement_code` (extracted from topic, line 570)

**Key Code Snippet:**
```python
# Line 580-610: Meeting creation
meeting, created = Meeting.objects.get_or_create(
    meeting_id=meeting_id,
    defaults={
        'topic': meeting_topic,
        'topic_normalized': topic_normalized,
        'requirement_code': requirement_code,
        'service_name': meeting_service_name,
        'meeting_type': meeting_type,
        'start_time': start_time,
        'end_time': end_time,
        'duration_minutes': duration_minutes,
        'recording_url': recording_normalized,
        'recording_url_source': recording_url_source,
        'download_url': download_url_normalized,
        'is_recorded': bool(recording),
        'session_id': session_id or None,
        'meeting_instance_key': meeting_instance_key or None,
    }
)
```

### 1.2 Attendee Sync Flow

**File:** `coda/ai_services/services/attendee_sync_service.py`

**Entry Point:** `sync_attendees_for_meetings(meetings, service_name, access_token)` (line 739)

**Process:**
1. For each meeting, calls `fetch_attendees_for_meeting()` (line 795)
2. Calls `upsert_attendees_for_meeting()` (line 848)

**Attendee Fetching (`fetch_attendees_for_meeting`, line 197):**
- **API Endpoint:** `GET https://api.getgo.com/G2M/rest/meetings/{meeting_id}/attendees` (line 242)
- **Critical:** This endpoint returns **ALL historical attendees** for the meeting room across all sessions
- **Filtering:** Must filter by `meetingInstanceKey` to get session-specific attendees (lines 292-348)
- **Instance Key Selection:** Uses `determine_meeting_instance_key()` (line 272) to select correct instance:
  - If exactly one distinct `meetingInstanceKey` → use it (line 154)
  - If multiple keys → try timestamp alignment (lines 158-185)
  - If ambiguous → return None (line 194)

**Key Code Snippet:**
```python
# Line 315-348: Instance key filtering
for attendee in attendees_data:
    attendee_instance_key = (
        attendee.get('meetingInstanceKey') or 
        attendee.get('meeting_instance_key')
    )
    
    normalized_attendee_key = normalize_key(attendee_instance_key)
    
    # Filter: if we have a meetingInstanceKey, only include matching attendees
    if normalized_filter_key:
        if normalized_attendee_key and normalized_attendee_key != normalized_filter_key:
            continue  # Skip mismatched attendees
```

**Attendee Persistence (`upsert_attendees_for_meeting`, line 434):**

**Process:**
1. **Deletes existing attendees** for the meeting (line 585) - fresh sync approach
2. Filters attendees by instance key (lines 503-571)
3. For each attendee:
   - Normalizes email via `normalize_attendee_email()` (line 596)
   - **Placeholder Email Generation** (lines 687-697):
     - If email is missing/NA → generates `no-email-{hash}@placeholder.local`
     - Hash includes: `meeting_id + instance_key + name + joinTime`
     - **Purpose:** Satisfy `unique_together(meeting, attendee_email)` constraint
   - Splits combined names (e.g., "EUNICE, JUDY AND NOREEN") via `split_combined_attendee_name()` (line 644)
   - Attempts user matching:
     - By email: `User.objects.filter(email__iexact=attendee_email)` (line 673)
     - By name: `User.objects.filter(username__iexact=name.lower())` (line 680)
   - Creates `MeetingAttendee` record:
     - **Table:** `ai_services_meetingattendee`
     - **Unique constraint:** `(meeting, attendee_email)` (line 700)
     - **Fields:**
       - `meeting` (FK to Meeting)
       - `user` (FK to CustomerUser, nullable)
       - `attendee_name`
       - `attendee_email` (may be placeholder)
       - `duration_minutes`
       - `is_organizer`

**Key Code Snippet:**
```python
# Line 684-697: Placeholder email generation
if not attendee_email:
    import hashlib
    instance_key = meeting.meeting_instance_key or meeting.session_id or ''
    time_key = join_time or leave_time or ''
    unique_key = f"{meeting.meeting_id}-{instance_key}-{name}-{time_key}".encode()
    name_hash = hashlib.md5(unique_key).hexdigest()[:12]
    attendee_email = f"no-email-{name_hash}@placeholder.local"
```

**Model:** `coda/ai_services/models.py` → `MeetingAttendee` (line 322)
- `user` field is FK to `'accounts.CustomerUser'` (line 334), **NOT** `auth.User`
- This is a **critical mismatch** with reconciliation service which queries `auth.User`

### 1.3 Conditions for `attendee_count=0`

**Possible Causes:**
1. **No attendees in API response** (meeting genuinely had no attendees)
2. **Instance key mismatch** (all attendees filtered out due to wrong `meetingInstanceKey`)
3. **404 Not Found** (meeting not available in account, marked as `provider_not_found=True`)
4. **Attendee sync not run** (meeting sync creates meeting, but attendee sync is separate)

**Log Messages:**
- `"⚠️  No attendees to persist for meeting {meeting_id}"` (line 574)
- `"⚠️  All {count} attendees filtered out for meeting {meeting_id}"` (line 562)

---

## 2. Reconciliation: Command → Service → Meeting Loop

### 2.1 Management Command

**File:** `coda/management/management/commands/reconcile_meeting_task_links.py`

**Entry Point:** `python manage.py reconcile_meeting_task_links --days 7`

**Command Arguments:**
- `--days` (default: 30) - Number of days back to reconcile
- `--since YYYY-MM-DD` - Start date (overrides --days)
- `--until YYYY-MM-DD` - End date
- `--window-days` (default: 7) - Time window for task matching
- `--dry-run` - Simulate without creating/updating TaskLinks

**Process (`handle()`, line 59):**
1. Calculates date range (lines 67-79)
2. Initializes `MeetingTaskReconciliationService` (lines 90-93)
3. Calls `service.reconcile_meetings(start_date, end_date)` (lines 96-99)
4. Calls `service.recompute_meeting_counts_for_tasks()` (line 118)

### 2.2 Reconciliation Service

**File:** `coda/management/services/meeting_task_reconciliation_service.py`

**Class:** `MeetingTaskReconciliationService` (line 26)

**Main Method:** `reconcile_meetings()` (line 53)

**Meeting Selection:**
- If `meetings` not provided, queries:
  ```python
  Meeting.objects.filter(
      start_time__gte=start_date,
      start_time__lte=end_date
  ).select_related().prefetch_related('attendees', 'attendees__user')
  ```
- **No filtering by service_name, provider_not_found, or attendee_count**

**Per-Meeting Loop (line 110):**
1. **Step 1:** Identify employee via `_identify_employee(meeting)` (line 115)
2. **Step 2:** Find candidate tasks via `_find_candidate_tasks(meeting, employee)` (line 127)
3. **Step 3:** Select best task via `_select_best_task(meeting, candidate_tasks)` (line 143)
4. **Step 4:** Create/update TaskLink via `_create_or_update_tasklink(meeting, best_task, employee)` (line 155)

**Logging:**
- Logs first 10 failures, then samples every 50th (lines 119, 136, 147)
- Log format: `"NO TASK MATCH - no employee match: {reason}"` (line 122)

---

## 3. Employee Resolution Logic (CRITICAL)

**File:** `coda/management/services/meeting_task_reconciliation_service.py`

**Method:** `_identify_employee(meeting)` (line 190)

### 3.1 Resolution Strategy

**Priority Order:**
1. **Organizer with linked user** (lines 204-208):
   - `organizer = meeting.attendees.filter(is_organizer=True).first()`
   - If `organizer.user` exists and `organizer.user.is_staff` → return user
2. **Organizer email match** (lines 209-217):
   - If `organizer.attendee_email` exists:
     - Query: `User.objects.filter(email__iexact=organizer.attendee_email, is_staff=True, is_active=True).first()`
3. **First staff attendee with linked user** (lines 220-223):
   - Loop through first 10 attendees
   - If `attendee.user` exists and `attendee.user.is_staff` → return user
4. **First staff attendee email match** (lines 224-232):
   - If `attendee.attendee_email` exists:
     - Query: `User.objects.filter(email__iexact=attendee.attendee_email, is_staff=True, is_active=True).first()`

**Key Code Snippet:**
```python
# Line 204-217: Organizer priority
organizer = meeting.attendees.filter(is_organizer=True).first()
if organizer:
    if organizer.user and organizer.user.is_staff:
        return organizer.user
    elif organizer.attendee_email:
        user = User.objects.filter(
            email__iexact=organizer.attendee_email,
            is_staff=True,
            is_active=True
        ).first()
        if user:
            return user
```

### 3.2 Critical Issues

**Issue 1: Model Mismatch**
- `MeetingAttendee.user` is FK to `'accounts.CustomerUser'` (not `auth.User`)
- Reconciliation queries `auth.User` directly
- **Result:** `organizer.user` and `attendee.user` will be `None` if linked to CustomerUser
- **Workaround:** Email matching still works (queries `auth.User` directly)

**Issue 2: Placeholder Emails**
- Attendees with `no-email-{hash}@placeholder.local` cannot match `auth.User.email`
- **Result:** Email matching fails for attendees without real emails
- **Log:** `"no employee match: organizer email not matched to staff user ({email})"` (line 252)

**Issue 3: No Fallback to Meeting Host/Organizer**
- Does not check `Meeting.organizer_email` (if stored)
- Does not check meeting room mapping
- **Result:** Meetings with no matching attendees fail employee resolution

### 3.3 Failure Reasons

**Method:** `_get_no_employee_reason(meeting)` (line 236)

**Reasons:**
- `"no attendees found"` (line 242) - `meeting.attendees.count() == 0`
- `"no organizer found ({count} attendees)"` (line 244) - No organizer in attendees
- `"organizer has no user or email ({count} attendees)"` (line 248) - Organizer missing both
- `"organizer user is not staff ({username})"` (line 250) - User exists but not staff
- `"organizer email not matched to staff user ({email})"` (line 252) - Email doesn't match staff user

**Log Message:** `"NO TASK MATCH - no employee match: {reason}"` (line 122)

---

## 4. Task Candidate Selection and Matching Logic

**File:** `coda/management/services/meeting_task_reconciliation_service.py`

**Method:** `_find_candidate_tasks(meeting, employee)` (line 296)

### 4.1 Task Filtering

**Base Query (lines 321-325):**
```python
base_tasks = Task.objects.filter(
    employee=employee,
    is_active=True,
    mxpoint__gt=0  # Meeting-required tasks
)
```

**Key Points:**
- **NO date filtering** (tasks are not filtered by `submission` or `created_at` relative to meeting)
- Only filters by: `employee`, `is_active=True`, `mxpoint > 0`

### 4.2 Topic Matching Strategy

**Requires:** `meeting.topic` must exist (line 328)

**Process:**
1. Normalizes meeting topic via `_normalize_text()` (line 332):
   - Lowercase, strip punctuation, collapse whitespace (lines 278-288)
2. Gets all candidate tasks (no date filter, line 337)
3. For each task:
   - Normalizes `task.activity_name` (line 358)
   - Calculates similarity:
     - **Exact match:** `score = 1.0` (line 365)
     - **Fuzzy match:** Uses `difflib.SequenceMatcher` (line 369)
     - **Threshold:** `similarity >= 0.90` (line 370)
   - **Requirement code boost:** If `meeting.requirement_code` matches `task.requirement_id`, adds 0.05 to score (lines 377-379)
4. Sorts by score (descending, line 384)
5. **Ambiguity check:** If multiple tasks tie for top score → returns `[]` with reason `'ambiguous'` (lines 391-397)

**Key Code Snippet:**
```python
# Line 363-374: Topic similarity matching
if meeting_topic_normalized == task_name_normalized:
    score = 1.0
    match_type = 'exact_match'
else:
    similarity = self._calculate_similarity(meeting_topic_normalized, task_name_normalized)
    if similarity >= 0.90:
        score = similarity
        match_type = 'fuzzy_match'
    else:
        continue  # Below threshold, skip
```

### 4.3 Requirement Code Handling

**Extraction (lines 342-349):**
- Parses `meeting.requirement_code` (e.g., "REQ-5755") → extracts ID (5755)
- Used as **boost signal only** (not a gate)

**Boost Logic (lines 377-379):**
- If `task.requirement_id == req_id` → adds 0.05 to score

### 4.4 Best Task Selection

**Method:** `_select_best_task(meeting, candidate_tasks)` (line 408)

**Scoring (lines 432-452):**
- **Requirement code match:** +10 points (lines 437-440)
- **Time proximity:**
  - Same day: +5 points (line 446)
  - 1-2 days: +3 points (line 448)
  - 3-7 days: +1 point (line 450)

**Note:** Time proximity uses `task.submission` (not `task.created_at`)

---

## 5. TaskLink Write Logic: Create/Update/Dedupe Rules

**File:** `coda/management/services/meeting_task_reconciliation_service.py`

**Method:** `_create_or_update_tasklink(meeting, task, employee)` (line 458)

### 5.1 Deduplication

**Check (lines 476-480):**
```python
existing_link = TaskLinks.objects.filter(
    task=task,
    meeting_id=meeting.meeting_id,
    is_active=True
).first()
```

**Key Points:**
- Dedupes by `(task, meeting_id, is_active=True)`
- **Does NOT dedupe by URL** (multiple TaskLinks can have same `meeting_id` if `is_active=False`)

### 5.2 Update Logic

**If existing link found (lines 482-489):**
- Updates: `link`, `drive_link`, `is_auto_generated`
- **Does NOT update:** `task`, `meeting_id`, `added_by`
- Returns `(False, True)` (created=False, updated=True)

### 5.3 Create Logic

**If no existing link (lines 490-503):**
- Creates new `TaskLinks` record:
  - **Table:** `management_tasklinks`
  - **Fields:**
    - `task` (FK to Task)
    - `added_by` (employee user)
    - `link_name` = "Meeting Recording"
    - `description` = f"Auto-generated from meeting: {meeting.topic}"
    - `link` = `meeting.recording_url` or ''
    - `meeting_id` = `meeting.meeting_id`
    - `is_active` = True
    - `is_auto_generated` = True

**Model:** `coda/management/models.py` → `TaskLinks` (line 789)
- `task` = FK to `Task` (line 791)
- `added_by` = FK to `User` (line 792)
- `meeting_id` = CharField (line 812)
- `is_auto_generated` = BooleanField (line 807)

---

## 6. DAF Meeting Counts: How "Meetings: x/y" is Computed

**File:** `coda/management/legacy_views.py`

**View:** `daf_v2_view()` (around line 2085)

### 6.1 Meeting Count Calculation

**Location:** Lines 2109-2117

**Process:**
1. Gets `task_links_list` (TaskLinks for the task, already filtered)
2. Builds set of distinct `meeting_id`s:
   ```python
   distinct_meeting_ids = set()
   for link in task_links_list:
       if link.is_active:
           meeting_id = getattr(link, 'meeting_id', None)
           if meeting_id:
               distinct_meeting_ids.add(meeting_id)
   meetings_completed_count = len(distinct_meeting_ids)
   ```
3. **Data Source:** `TaskLinks.meeting_id` (NOT `Meeting` table directly)
4. **Counts:** Distinct `meeting_id` values where `is_active=True`

### 6.2 Required Count

**Location:** Lines 2097-2107

**Sources (priority order):**
1. `activity_policy.sessions_required` (line 2101)
2. `activity_policy.required_meeting_count` (line 2102)
3. `task.mxpoint` (or `task.point`) (line 2107)
4. Default: 1 (line 2098)

### 6.3 Display

**Location:** Line 2123

**Format:** `f"Meetings: {meetings_completed_count}/{meeting_required_count}"`

**Key Point:** Count is **recomputed on each page load** (not cached)

### 6.4 Reconciliation Count Recompute

**File:** `coda/management/services/meeting_task_reconciliation_service.py`

**Method:** `recompute_meeting_counts_for_tasks()` (line 505)

**Process:**
- Queries all active tasks (line 521)
- For each task, counts distinct `meeting_id`s in TaskLinks (lines 533-543)
- **Purpose:** Logging/debugging only (does not update any cached field)

**Key Code Snippet:**
```python
# Line 533-543: Count distinct meeting_ids
task_links = TaskLinks.objects.filter(
    task=task,
    is_active=True
).exclude(
    Q(meeting_id__isnull=True) | Q(meeting_id='')
)

distinct_meeting_ids = set(
    link.meeting_id for link in task_links if link.meeting_id
)
meeting_count = len(distinct_meeting_ids)
```

---

## 7. Evidence Page: Why Edwin Evidence Appears on Eunice Task

**File:** `coda/management/legacy_views.py`

**View:** `newevidence(request, taskid)` (line 3778)

### 7.1 Evidence Query

**Method:** `get_user_evidence_for_task(task_obj, user, is_staff=False)` (line 3792)

**For Staff (lines 3827-3832):**
```python
task_evidence_qs = TaskLinks.objects.filter(
    task=task_obj  # Strictly filter to this task_id
).select_related('added_by').order_by('-created_at')
```

**For Non-Staff (lines 3833-3840):**
```python
task_evidence_qs = TaskLinks.objects.filter(
    task=task_obj,  # Strictly filter to this task_id
    added_by__in=[user, task_obj.employee],  # Current user OR task owner
    is_active=True  # Non-staff only see active evidence
).select_related('added_by').order_by('-created_at')
```

### 7.2 Filtering Logic

**Key Filters:**
1. **`task=task_obj`** - Always filters by task_id (lines 3831, 3837)
2. **`added_by__in=[user, task_obj.employee]`** - For non-staff only (line 3838)
3. **`is_active=True`** - For non-staff only (line 3839)

### 7.3 Root Cause Analysis

**Hypothesis:** Evidence uploaded by EDWIN appears under Eunice's task because:

1. **TaskLink.task FK is correct** (filtered by `task=task_obj`)
2. **BUT:** If `TaskLinks.added_by` is set incorrectly, or if evidence was manually linked to wrong task, it will appear

**Possible Scenarios:**
- **Scenario A:** Evidence was created with `task=Eunice's task` but `added_by=EDWIN`
  - **Result:** Appears on Eunice's task (filtered by task_id)
  - **Fix:** Should also filter by `task.employee` OR `added_by` ownership
- **Scenario B:** Evidence was created for different task, then task_id was changed
  - **Result:** Appears on new task
  - **Fix:** Audit TaskLinks creation/update logic
- **Scenario C:** Evidence is associated by `activity_name` instead of `task_id`
  - **Result:** If multiple tasks share same activity_name, evidence leaks
  - **Fix:** Ensure TaskLinks always uses `task` FK (not activity_name)

**Current Code:** Evidence query **DOES filter by task_id** (line 3831, 3837), so leakage should not occur unless:
- TaskLinks.task FK is incorrect
- Evidence was manually created with wrong task
- Multiple tasks share same ID (unlikely due to unique constraint)

**Missing Filter:** Evidence query does **NOT** filter by `task.employee` to ensure evidence belongs to task owner. This could allow cross-employee evidence if TaskLinks.task is set incorrectly.

---

## 8. Observed Failure Points Mapped to Logs

### 8.1 "NO TASK MATCH - no employee match: no attendees found"

**Location:** `coda/management/services/meeting_task_reconciliation_service.py:122`

**Emitted By:** `reconcile_meetings()` → `_identify_employee()` → `_get_no_employee_reason()`

**Cause:** `meeting.attendees.count() == 0` (line 242)

**Possible Reasons:**
1. Attendee sync not run for this meeting
2. All attendees filtered out due to instance key mismatch
3. Meeting genuinely had no attendees
4. Meeting marked as `provider_not_found=True` (attendee sync skipped)

### 8.2 "NO TASK MATCH - no employee match: organizer email not matched to staff user"

**Location:** `coda/management/services/meeting_task_reconciliation_service.py:122, 252`

**Emitted By:** `_get_no_employee_reason()`

**Cause:** Organizer email exists but doesn't match any `auth.User` with `is_staff=True` (line 252)

**Possible Reasons:**
1. Email is placeholder (`no-email-{hash}@placeholder.local`)
2. Email doesn't match any staff user in `auth_user` table
3. User exists but `is_staff=False` or `is_active=False`

### 8.3 "NO TASK MATCH - ambiguous topic match"

**Location:** `coda/management/services/meeting_task_reconciliation_service.py:131`

**Emitted By:** `reconcile_meetings()` → `_find_candidate_tasks()`

**Cause:** Multiple tasks tie for best similarity score (lines 391-397)

**Result:** Returns `[]` with reason `'ambiguous'` (line 397)

### 8.4 "NO TASK MATCH - no eligible tasks for employee"

**Location:** `coda/management/services/meeting_task_reconciliation_service.py:133`

**Emitted By:** `reconcile_meetings()` → `_find_candidate_tasks()`

**Cause:** No tasks match topic similarity threshold (>= 0.90) (line 370)

**Possible Reasons:**
1. No tasks for employee with `mxpoint > 0`
2. Topic similarity < 0.90
3. Meeting topic is empty (line 329)

### 8.5 "⚠️  No attendees to persist for meeting {meeting_id}"

**Location:** `coda/ai_services/services/attendee_sync_service.py:574`

**Emitted By:** `upsert_attendees_for_meeting()`

**Cause:** `len(filtered_attendees) == 0` (line 573)

**Possible Reasons:**
1. All attendees filtered out due to instance key mismatch
2. API returned empty attendees list
3. Meeting instance key missing (line 506)

### 8.6 "⚠️  All {count} attendees filtered out for meeting {meeting_id}"

**Location:** `coda/ai_services/services/attendee_sync_service.py:562`

**Emitted By:** `upsert_attendees_for_meeting()`

**Cause:** All attendees have mismatched `meetingInstanceKey` (lines 551-568)

**Result:** Includes all attendees to prevent data loss (line 568)

---

## Summary of Critical Issues

1. **Model Mismatch:** `MeetingAttendee.user` is FK to `CustomerUser`, but reconciliation queries `auth.User` directly
2. **Placeholder Emails:** Attendees with `no-email-{hash}@placeholder.local` cannot match staff users
3. **No Date Filtering:** Task candidate selection does NOT filter by date proximity (only by topic similarity)
4. **Instance Key Filtering:** Attendees may be filtered out if `meetingInstanceKey` doesn't match
5. **Evidence Leakage Risk:** Evidence query doesn't filter by `task.employee`, allowing cross-employee evidence if TaskLinks.task is incorrect

---

## Code References Summary

| Component | File | Key Functions |
|-----------|------|---------------|
| Meeting Sync | `coda/ai_services/services/goto_meeting_sync_service.py` | `sync()`, `fetch_meetings()`, `upsert_meetings()` |
| Meeting Persistence | `coda/ai_services/views.py` | `save_meeting_data()` |
| Attendee Sync | `coda/ai_services/services/attendee_sync_service.py` | `sync_attendees_for_meetings()`, `fetch_attendees_for_meeting()`, `upsert_attendees_for_meeting()` |
| Reconciliation Command | `coda/management/management/commands/reconcile_meeting_task_links.py` | `Command.handle()` |
| Reconciliation Service | `coda/management/services/meeting_task_reconciliation_service.py` | `reconcile_meetings()`, `_identify_employee()`, `_find_candidate_tasks()`, `_create_or_update_tasklink()` |
| DAF Meeting Counts | `coda/management/legacy_views.py` | `daf_v2_view()` (lines 2085-2155) |
| Evidence View | `coda/management/legacy_views.py` | `newevidence()` (line 3778) |
| Models | `coda/ai_services/models.py` | `Meeting`, `MeetingAttendee` |
| Models | `coda/management/models.py` | `Task`, `TaskLinks` |

---

**End of Report**

