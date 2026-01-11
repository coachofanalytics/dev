# GoToMeeting Integration vs Task / DAF / Evidence - Technical Analysis

**Branch:** 25.12_CODA_DEV_CM  
**Date:** 2024-12-26  
**Focus:** Understanding current GoToMeeting integration with Task Management + Evidence + DAF system

---

## A. Current GoTo / Meeting Integration Map

### A.1 Models

#### Meeting Models (in `coda/ai_services/models.py`)

**`GotoMeetings` (Legacy, DEPRECATED)**
- **File:** `coda/ai_services/models.py` (lines 98-122)
- **Status:** Marked as DEPRECATED, kept for backward compatibility
- **Key Fields:**
  - `meeting_id`, `meeting_topic`, `meeting_type`
  - `recording` (CharField, max_length=500) - URL to recording
  - `meeting_start_time`, `meeting_end_time`, `meeting_duration` (CharField)
  - `attendee_name`, `attendee_email`, `attendee_duration`
  - `download_url`
- **DB Table:** `getdata_gotomeetings`
- **Usage:** Still referenced in some legacy code (`coda_project/task.py:auto_uplaod_evidence`)

**`Meeting` (Normalized, ACTIVE)**
- **File:** `coda/ai_services/models.py` (lines 126-206)
- **Status:** ✅ ACTIVE - Replaces denormalized GotoMeetings
- **Key Fields:**
  - `meeting_id` (CharField, unique, indexed) - Unique GoToMeeting ID
  - `topic` (CharField, max_length=500) - Meeting subject
  - `start_time`, `end_time` (DateTimeField)
  - `duration_minutes` (IntegerField) - ⭐ **Total meeting duration in minutes**
  - `recording_url` (URLField, max_length=1000) - URL to meeting recording
  - `download_url` (URLField) - Direct download URL
  - `is_recorded` (BooleanField)
- **DB Table:** `gotomeeting_meeting`
- **Relationships:** Has reverse relation `attendees` → `MeetingAttendee`

**`MeetingAttendee` (Normalized, ACTIVE)**
- **File:** `coda/ai_services/models.py` (lines 209-274)
- **Status:** ✅ ACTIVE - Stores individual attendee records
- **Key Fields:**
  - `meeting` (ForeignKey → Meeting)
  - `user` (ForeignKey → CustomerUser, nullable)
  - `attendee_name`, `attendee_email`
  - `duration_minutes` (IntegerField) - ⭐ **How long this attendee stayed (minutes)**
  - `task_points_awarded` (BooleanField)
- **DB Table:** `gotomeeting_attendee`
- **Unique Constraint:** (`meeting`, `attendee_email`)

**`MeetingActivityMapping` (Configuration)**
- **File:** `coda/ai_services/models.py` (lines 340-380)
- **Status:** ✅ ACTIVE - Configurable mapping between meetings and task activities
- **Key Fields:**
  - `meeting_id_pattern` (CharField, unique)
  - `activity_name` (CharField)
  - `min_duration_minutes` (IntegerField, default=3)
  - `task_points` (IntegerField, default=0)
- **Purpose:** Maps meeting IDs to task activity names for auto-linking

**`TaskLinks` (Evidence Storage)**
- **File:** `coda/management/models.py` (lines 875-916)
- **Status:** ✅ ACTIVE - Stores evidence uploads
- **Key Fields:**
  - `task` (ForeignKey → Task)
  - `added_by` (ForeignKey → User)
  - `link` (CharField, max_length=1000) - ⭐ **URL to evidence (e.g., GoToMeeting recording)**
  - `drive_link` (URLField, max_length=2000) - Google Drive link
  - `link_name`, `description`
  - `doc` (FileField) - Uploaded document
  - `is_active`, `is_featured`
- **Relationship:** No explicit FK to Meeting model - only stores URL as string

### A.2 Services

**`MeetingLinkingService`**
- **File:** `coda/management/services/meeting_linking_service.py`
- **Status:** ✅ Implemented but **NOT currently invoked from evidence upload flow**
- **Purpose:** Intelligent matching of GoToMeeting meetings to tasks
- **Methods:**
  - `link_meeting_to_tasks(meeting_id, attendee, attendee_duration)` - Links a meeting to tasks with confidence scoring
  - `_find_task_matches()` - Uses multiple strategies (exact mapping, keyword matching, historical patterns, category matching)
  - `_create_task_link()` - Creates TaskLinks record for meeting-task connection
- **Integration:** Uses `MeetingServiceInterface` (adapter pattern)
- **Current Usage:** Designed for batch/automated linking, not called from `newevidence()` view

**`ChecklistEvaluationService`**
- **File:** `coda/management/services/checklist_evaluation_service.py`
- **Status:** ✅ ACTIVE - Uses meeting duration for quality scoring
- **Key Method:** `_get_meeting_duration_minutes(task, task_links)` (lines 333-392)
  - **Strategy:** Tries to match `TaskLinks.link` to `Meeting.recording_url` or `Meeting.download_url` (exact match only)
  - **Returns:** Sum of `Meeting.duration_minutes` for matched meetings
  - **Limitation:** Only works if URL in TaskLinks exactly matches Meeting.recording_url (no partial matching, no meeting ID extraction from URL)
- **Integration Points:**
  - Called from `get_task_quality_score()` to compute `duration_factor`
  - Used in `DAFSummaryService._get_activities_data()` (line 674)

**`MeetingServiceInterface` (Abstract Interface)**
- **File:** `coda/shared_core/interfaces/meeting_service.py`
- **Status:** ✅ ACTIVE - Defines contract for meeting services
- **Implementations:**
  - `MeetingServiceAdapter` (in ai_services app) - wraps Meeting model
  - `NoOpMeetingServiceAdapter` (fallback) - returns empty results
- **Methods:**
  - `get_meeting_by_id(meeting_id)`
  - `find_meeting_by_topic(topic, date_range, user_id)`
  - `find_exact_mapping(meeting_id_pattern)`
  - `get_meetings_in_date_range(start_date, end_date, user_id)`

**GoToMeeting API Integration**
- **File:** `coda/ai_services/views.py`
- **Functions:**
  - `getmeetingresponse(startDate, endDate)` (lines 235-356) - Fetches meetings from GoToMeeting API
  - `save_meeting_data(meeting_data)` (lines 358-564) - Persists meeting data to `Meeting` + `MeetingAttendee` models
- **API Endpoints Used:**
  - `https://api.getgo.com/G2M/rest/historicalMeetings?startDate={}&endDate={}` - List meetings
  - `https://api.getgo.com/G2M/rest/meetings/{meeting_id}/attendees` - Get attendee details
- **Authentication:** OAuth tokens stored in `OAuthToken` model
- **Current Usage:** Called from `meetingFormView()` when admin fetches meetings manually (not automatic)

### A.3 Commands & Scheduled Jobs

**Management Commands:**
- `migrate_gotomeeting_data.py` - Migrates data from GotoMeetings to Meeting model
- `populate_meeting_mappings.py` - Populates MeetingActivityMapping records

**Celery Tasks:**
- `auto_uplaod_evidence` (in `coda/coda_project/task.py`, lines 309-330)
  - **Status:** ⚠️ **COMMENTED OUT** in celery.py (line 52-57)
  - **Logic:** Uses legacy `GotoMeetings` model, matches by username, creates TaskLinks
  - **Not Active:** Not scheduled in `celery.py`

### A.4 Views & Templates

**Evidence Upload Flow:**
- **View:** `newevidence(request, taskid)` - `coda/management/views.py` (lines 1772-1843)
- **Form:** `EvidenceForm` - `coda/management/forms.py` (lines 209-254)
- **Template:** `management/daf/evidence_form.html`
- **Processing:** `process_evidence_submission()` (lines 1846-1888) - Creates TaskLinks record
- **Current Behavior:** Simply saves link as string in `TaskLinks.link` - **NO meeting lookup or linking**

**Meeting Management Views:**
- `meetingFormView()` - `coda/ai_services/views.py` (lines 567-682) - Manual fetch from GoToMeeting API
- `get_attendee_duration()` - `coda/management/views.py` (lines 3180-3274) - Displays attendee duration for specific meeting IDs

### A.5 Integration Connections

**Current State:**

```
┌─────────────────┐
│  GoToMeeting    │
│      API        │
└────────┬────────┘
         │
         │ Manual fetch via meetingFormView()
         ▼
┌─────────────────┐
│   Meeting       │  ✅ Has duration_minutes, recording_url
│   (Normalized)  │  ✅ Has MeetingAttendee records
└─────────────────┘
         │
         │ ❌ NO AUTOMATIC LINK
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│   TaskLinks     │     │      Task       │
│  (Evidence)     │────▶│  (User Task)    │
│  link: <URL>    │ FK  └─────────────────┘
└─────────────────┘
         │
         │ ⚠️ Exact URL match only
         │ (if URL happens to match Meeting.recording_url)
         ▼
┌──────────────────────────┐
│ ChecklistEvaluation      │
│ Service                  │
│ _get_meeting_duration()  │
└──────────────────────────┘
```

**Connection Summary:**
- ✅ `Meeting` model exists with `duration_minutes`
- ✅ `TaskLinks` stores evidence URLs
- ⚠️ **Gap:** No automatic linking when evidence is uploaded
- ⚠️ **Gap:** `ChecklistEvaluationService` only matches by exact URL (fragile)
- ❌ `MeetingLinkingService` exists but is **NOT called from evidence upload flow**

---

## B. Evidence Flow for a Meeting-Based Task (Eunice Example)

### B.1 What Happens TODAY (Current Real-World Behavior)

**Step 1: User Clicks "Upload Evidence" on DAF**
- Template: `employeetasks.html` (line 377)
- URL: `/management/newevidence/<taskid>`
- Context: Task has `activity_name="Product Backlog Refinement"` (or similar)

**Step 2: User Submits GoToMeeting URL**
- View: `newevidence(request, taskid)` (`coda/management/views.py:1772`)
- Form: `EvidenceForm` - user pastes URL into `link` field
- Validation:
  - Checks if link is accessible (HTTP HEAD request, line 1794)
  - Checks for duplicate links (lines 1803-1814)

**Step 3: TaskLinks Record Created**
- Function: `process_evidence_submission()` (`coda/management/views.py:1846`)
- Action: Creates `TaskLinks` record:
  ```python
  TaskLinks.objects.create(
      task=task,
      added_by=user,
      link=data.get('link'),  # ⚠️ Just stored as plain string
      link_name=data.get('link_name', 'General'),
      description=data.get('description', ''),
      # ... other fields
  )
  ```
- **Result:** URL stored in `TaskLinks.link` as plain string - **NO meeting lookup performed**

**Step 4: Meeting Lookup (What Does NOT Happen)**
- ❌ No code extracts meeting ID from the URL
- ❌ No code calls `Meeting.objects.filter(recording_url=link)`
- ❌ No code calls `MeetingLinkingService.link_meeting_to_tasks()`
- ❌ No duration is fetched or stored

**Step 5: Quality/DAF Evaluation (When DAF Summary is Generated)**
- Service: `ChecklistEvaluationService._get_meeting_duration_minutes()` (`checklist_evaluation_service.py:333`)
- **Attempt:** Tries to match `TaskLinks.link` to `Meeting.recording_url` or `Meeting.download_url`
- **Problem:** 
  - Only works if URL **exactly matches** (character-for-character)
  - GoToMeeting URLs from API: `recording.get('shareUrl')` (from `save_meeting_data`, line 286)
  - URLs pasted by users: May be different format (e.g., `transcripts.gotomeeting.com/#/s/...`)
  - **Result:** Matching usually fails → `total_duration = 0` → `duration_factor = 0.0` → low quality score

**Step 6: Quality Score Calculation**
- Service: `ChecklistEvaluationService.get_task_quality_score()` 
- Formula: `quality_score = 0.5 * duration_factor + 0.3 * evidence_coverage + 0.2 * checklist_completion`
- **Current Outcome:**
  - If duration match fails: `duration_factor = 0.0` → quality score penalized
  - For PBR (min 120 min): Missing duration → quality score capped at low value

### B.2 What the Master Doc Envisions (Target Behavior)

**Expected Flow:**
1. User pastes GoToMeeting URL → System extracts meeting ID from URL
2. System looks up Meeting record by ID or recording URL
3. System retrieves `Meeting.duration_minutes`
4. System uses duration in quality calculation → `duration_factor = min(duration / 120, 1.0)`
5. Quality badge on DAF reflects actual duration compliance

**Current Gap:** Steps 1-3 are missing from evidence upload flow.

---

## C. Gaps vs Target Behaviour

### C.1 Missing Automatic Meeting Lookup on Evidence Upload

**Gap Description:**
When a user submits a GoToMeeting URL via `newevidence()` view, the system does not:
- Extract meeting ID from the URL
- Look up the corresponding `Meeting` record
- Store any link between `TaskLinks` and `Meeting`

**Impact:**
- `ChecklistEvaluationService` cannot find duration because URL matching fails (exact match only)
- Quality scores are inaccurate for meeting-based activities
- Managers cannot automatically verify duration compliance

**Root Cause:**
- `process_evidence_submission()` only creates TaskLinks record
- No integration with Meeting model or MeetingLinkingService
- No URL parsing/extraction logic

**Type:** Missing code / Unfinished integration

---

### C.2 Fragile URL Matching in ChecklistEvaluationService

**Gap Description:**
`ChecklistEvaluationService._get_meeting_duration_minutes()` (lines 333-392) only matches by:
- Exact string match of `TaskLinks.link` to `Meeting.recording_url`
- Exact string match of `TaskLinks.link` to `Meeting.download_url`

**Problem:**
- GoToMeeting recording URLs from API: `shareUrl` format (e.g., `https://...`)
- URLs pasted by users: May be `transcripts.gotomeeting.com/#/s/<hash>` format
- Meeting IDs are embedded in URLs but not extracted
- **Result:** Matching fails in most cases → duration = 0

**Code Reference:**
```python
# checklist_evaluation_service.py:360
meetings = Meeting.objects.filter(
    Q(recording_url__in=recording_urls) | Q(download_url__in=recording_urls)
)
# Only exact match - no URL parsing or meeting ID extraction
```

**Impact:**
- Duration lookup fails for most evidence submissions
- Quality scores do not reflect actual meeting duration

**Type:** Incomplete implementation / Missing URL parsing logic

---

### C.3 No Meeting ID Extraction from URLs

**Gap Description:**
There is no utility function to:
- Extract meeting ID from GoToMeeting URLs (e.g., `transcripts.gotomeeting.com/#/s/<hash>`)
- Extract meeting ID from recording share URLs
- Normalize different URL formats to a common meeting identifier

**Impact:**
- Cannot match user-pasted URLs to Meeting records
- Cannot leverage `Meeting.meeting_id` field for matching

**Type:** Missing code / Not designed

---

### C.4 Meeting Data Not Automatically Populated

**Gap Description:**
Meeting data (`Meeting` + `MeetingAttendee`) is only populated when:
- Admin manually fetches via `meetingFormView()` (POST request with date range)
- API is called: `getmeetingresponse(startDate, endDate)` → `save_meeting_data()`

**Not Populated:**
- ❌ Automatically on a schedule (celery task exists but is commented out)
- ❌ On-demand when evidence is uploaded
- ❌ Real-time sync with GoToMeeting API

**Current State:**
- Meeting records may not exist for meetings that users submit as evidence
- Even if URL matching worked, there might be no Meeting record to match against

**Type:** Partially implemented (manual only, not automated)

---

### C.5 MeetingLinkingService Not Integrated with Evidence Upload

**Gap Description:**
`MeetingLinkingService` exists (`coda/management/services/meeting_linking_service.py`) but:
- Is designed for batch/automated linking (takes `meeting_id` as input)
- Is NOT called from `newevidence()` view or `process_evidence_submission()`
- Cannot be invoked from evidence upload flow without refactoring

**Current Usage:**
- No current usage found in evidence upload flow
- Appears to be designed for future batch processing

**Type:** Unfinished integration / Design mismatch

---

### C.6 Attendee Duration vs Meeting Duration Mismatch

**Gap Description:**
- `Meeting.duration_minutes` = Total meeting duration (all attendees)
- `MeetingAttendee.duration_minutes` = How long a specific attendee stayed
- `ChecklistEvaluationService` uses `Meeting.duration_minutes` (total)

**Potential Issue:**
- For quality scoring, we might want to use **attendee-specific duration** (how long the employee stayed)
- Current code uses total meeting duration, which may overestimate if employee left early

**Code Reference:**
```python
# checklist_evaluation_service.py:371-373
for meeting in meetings:
    if meeting.duration_minutes:
        total_duration += meeting.duration_minutes  # Uses total, not attendee duration
```

**Type:** Design decision needed / Potential enhancement

---

## D. Options for Next Steps (Implementation Plan)

### Option 1: Minimal - URL Matching Enhancement (Small)

**Approach:**
Enhance `ChecklistEvaluationService._get_meeting_duration_minutes()` to:
1. Extract meeting ID from URLs (parse GoToMeeting URL formats)
2. Match by `Meeting.meeting_id` if URL contains meeting ID
3. Fall back to exact URL matching if ID extraction fails

**Files to Touch:**
- `coda/management/services/checklist_evaluation_service.py` - Add URL parsing helper, enhance `_get_meeting_duration_minutes()`

**Reuses:**
- Existing `Meeting` model
- Existing `TaskLinks` structure
- No schema changes

**Complexity:** Low  
**Risk:** Low - Only enhances existing logic, doesn't change evidence upload flow

**Limitations:**
- Still requires Meeting records to exist in DB (manual fetch or batch job)
- Doesn't auto-populate meetings on evidence upload
- Relies on URL format consistency

---

### Option 2: Medium - On-Demand Meeting Lookup on Evidence Upload (Medium)

**Approach:**
1. Add URL parsing helper to extract meeting ID from GoToMeeting URLs
2. In `process_evidence_submission()`, when link is a GoToMeeting URL:
   - Extract meeting ID
   - Look up `Meeting` record by `meeting_id`
   - If not found, optionally fetch from GoToMeeting API (on-demand)
   - Store optional FK or meeting_id reference (if schema allows, or use a separate linking table)
3. Enhance `ChecklistEvaluationService` to use meeting ID matching

**Files to Touch:**
- `coda/management/views.py` - Enhance `process_evidence_submission()`
- `coda/management/services/checklist_evaluation_service.py` - Add meeting ID matching
- `coda/management/utils.py` or new `management/services/meeting_url_parser.py` - URL parsing utility
- Potentially: `coda/management/models.py` - Add optional FK or meeting_id field to TaskLinks (if schema change acceptable)

**Reuses:**
- Existing `Meeting` model
- Existing GoToMeeting API integration (`getmeetingresponse`, `save_meeting_data`)
- Existing `TaskLinks` structure (with optional enhancement)

**Complexity:** Medium  
**Risk:** Medium - Adds API calls to evidence upload flow (could slow down or fail)

**Benefits:**
- Automatically populates meetings when evidence is uploaded
- Works even if meetings weren't pre-fetched
- Closes the gap for new evidence submissions

**Limitations:**
- Requires GoToMeeting API access/credentials
- Adds latency to evidence upload (API call)
- May fail if API is down (need graceful fallback)

---

### Option 3: Hybrid - Batch Meeting Sync + Enhanced Matching (Medium-Large)

**Approach:**
1. **Batch Sync:** Re-enable or create celery task to periodically sync meetings from GoToMeeting API (e.g., daily)
2. **URL Matching Enhancement:** Implement Option 1 (URL parsing + meeting ID matching)
3. **Optional On-Demand Fetch:** If meeting not found in DB during quality evaluation, log warning but don't block (graceful degradation)

**Files to Touch:**
- `coda/coda_project/celery.py` - Add/enable meeting sync task
- `coda/ai_services/tasks.py` or new task - Create `sync_meetings_from_api()` celery task
- `coda/management/services/checklist_evaluation_service.py` - Enhance matching (Option 1)
- `coda/management/services/meeting_url_parser.py` (new) - URL parsing utility

**Reuses:**
- Existing `Meeting` model
- Existing `getmeetingresponse()` and `save_meeting_data()` functions
- Existing celery infrastructure

**Complexity:** Medium-Large  
**Risk:** Medium - Adds background job, requires monitoring

**Benefits:**
- Most meetings pre-populated (better performance)
- Graceful degradation if meeting missing
- No impact on evidence upload flow (async)

**Limitations:**
- Requires celery worker running
- Delayed sync (meetings may not be immediately available)
- Still need URL matching logic (Option 1)

---

### Option 4: Large - Full Integration with MeetingLinkingService (Large)

**Approach:**
1. Refactor `MeetingLinkingService` to work with evidence upload flow (accept URL instead of meeting_id)
2. Add URL parsing to extract meeting ID
3. In `process_evidence_submission()`, call `MeetingLinkingService` to:
   - Find or fetch meeting
   - Optionally auto-link to task (if confidence high)
   - Store meeting reference in TaskLinks
4. Use meeting data for quality scoring

**Files to Touch:**
- `coda/management/services/meeting_linking_service.py` - Refactor to accept URLs
- `coda/management/views.py` - Integrate MeetingLinkingService in `process_evidence_submission()`
- `coda/management/models.py` - Potentially add FK or meeting_id to TaskLinks
- `coda/management/services/checklist_evaluation_service.py` - Use meeting data

**Reuses:**
- Existing `MeetingLinkingService` (with refactoring)
- Existing `Meeting` model
- Existing matching strategies

**Complexity:** Large  
**Risk:** High - Significant refactoring, more moving parts

**Benefits:**
- Leverages existing intelligent matching logic
- Can auto-link meetings to tasks
- Most comprehensive solution

**Limitations:**
- Most complex to implement
- Requires careful integration testing
- May introduce new edge cases

---

## E. Recommendation (Short)

### Recommended Approach: **Option 2 (Medium) with Option 1 Enhancement**

**Rationale:**
1. **Minimal Schema Changes:** Can work with existing `TaskLinks` structure (no FK needed initially - just parse URL and look up Meeting)
2. **Immediate Value:** Solves the problem for new evidence uploads (Eunice's case)
3. **Reuses Existing Infrastructure:** Leverages `Meeting` model, `getmeetingresponse()`, `save_meeting_data()`
4. **Graceful Degradation:** If API call fails, evidence still saves (just no duration lookup)
5. **Testable on Real User:** Can test with Eunice's actual PBR/training tasks immediately

**Implementation Steps:**

**Step 1: URL Parsing Utility**
- Create `coda/management/services/meeting_url_parser.py`
- Function: `extract_meeting_id_from_url(url: str) -> Optional[str]`
- Handles formats:
  - `transcripts.gotomeeting.com/#/s/<hash>`
  - `https://api.getgo.com/G2M/rest/meetings/<meeting_id>`
  - Recording share URLs (extract ID if embedded)

**Step 2: Enhance Evidence Upload**
- In `process_evidence_submission()` (`coda/management/views.py:1846`):
  - After creating TaskLinks, check if link looks like GoToMeeting URL
  - Extract meeting ID using parser
  - Look up `Meeting.objects.filter(meeting_id=extracted_id).first()`
  - If not found AND API available, optionally fetch on-demand (async or background)
  - Log meeting_id or store in TaskLinks.description for future lookup

**Step 3: Enhance ChecklistEvaluationService**
- In `_get_meeting_duration_minutes()` (`checklist_evaluation_service.py:333`):
  - Try meeting ID extraction from URLs first
  - Match by `Meeting.meeting_id` (more robust than URL matching)
  - Fall back to exact URL matching if ID extraction fails

**Step 4: Testing**
- Use Eunice's existing PBR/training tasks
- Upload a GoToMeeting URL as evidence
- Verify duration is found and quality score reflects it
- Verify quality badge shows correct status on DAF

**Files to Modify:**
1. `coda/management/services/meeting_url_parser.py` (NEW)
2. `coda/management/views.py` - `process_evidence_submission()` function
3. `coda/management/services/checklist_evaluation_service.py` - `_get_meeting_duration_minutes()` method

**Estimated Complexity:** Medium (2-3 focused files, ~200-300 lines of code)

**Risk:** Low-Medium (adds API dependency to upload flow, but with graceful fallback)

**Alternative if API Calls are Concern:**
- Start with Option 1 only (URL matching enhancement)
- Add Option 2 later as Phase 2 (on-demand fetch)

---

## F. Additional Notes

### F.1 Meeting Population Status

**Question:** Are Meeting records currently populated in the cloned DB?

**Answer:** Likely partially populated:
- `Meeting` records exist if admin has manually run `meetingFormView()` with date ranges
- May not exist for all meetings that users have submitted as evidence
- Legacy `GotoMeetings` records may exist but are deprecated

**Recommendation:** Check DB to see coverage:
```sql
SELECT COUNT(*) FROM gotomeeting_meeting;
SELECT COUNT(*) FROM management_tasklinks WHERE link LIKE '%gotomeeting%' OR link LIKE '%transcripts.gotomeeting%';
```

### F.2 URL Format Variations

**GoToMeeting URLs observed in codebase:**
- `transcripts.gotomeeting.com/#/s/<hash>` (most common in templates)
- Recording share URLs (from API: `recording.get('shareUrl')`)
- Download URLs (from API: `recording.get('downloadUrl')`)
- Meeting join URLs (from API)

**Challenge:** Different formats need different parsing logic.

**Recommendation:** Start with most common format (`transcripts.gotomeeting.com/#/s/<hash>`) and expand.

### F.3 Attendee Duration Consideration

**Current:** Uses `Meeting.duration_minutes` (total meeting duration)

**Question:** Should we use `MeetingAttendee.duration_minutes` (employee-specific duration) instead?

**Recommendation:** For v1, use `Meeting.duration_minutes` (simpler, already implemented). Consider attendee-specific duration in Phase 2 if needed.

---

**End of Analysis Report**

