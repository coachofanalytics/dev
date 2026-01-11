# GoToMeeting Integration Analysis - Focused Report

**Branch:** 25.12_CODA_DEV_CM  
**Date:** 2024-12-26  
**Purpose:** Concrete analysis of GoToMeeting data flow and integration with Task/DAF system

---

## 1. GoToMeeting → DB Ingestion (What Happens Today)

### 1.1 API Integration Functions

**Primary Function:** `getmeetingresponse(startDate, endDate)`  
**File:** `coda/ai_services/views.py` (lines 235-356)

**API Endpoints Called:**
1. `https://api.getgo.com/G2M/rest/historicalMeetings?startDate={}&endDate={}` (line 259)
   - Fetches list of meetings for date range
   - Returns JSON with meeting details (meetingId, subject, startTime, endTime, duration, recording info)

2. `https://api.getgo.com/G2M/rest/meetings/{meeting_id}/attendees` (line 298)
   - Fetches attendee details for each meeting
   - Returns attendee names, emails, durations, join/leave times

**Authentication:** Uses OAuth token from `get_access_token()` (line 251)

### 1.2 Data Persistence Function

**Function:** `save_meeting_data(meeting_data)`  
**File:** `coda/ai_services/views.py` (lines 358-564)

**Models Populated:**
- ✅ **`Meeting`** (normalized model) - `coda/ai_services/models.py` (lines 126-206)
  - Fields: `meeting_id`, `topic`, `start_time`, `end_time`, `duration_minutes`, `recording_url`, `download_url`
  - DB Table: `gotomeeting_meeting`
  - Created via `Meeting.objects.get_or_create(meeting_id=meeting_id, ...)` (line 426)

- ✅ **`MeetingAttendee`** (normalized model) - `coda/ai_services/models.py` (lines 209-274)
  - Fields: `meeting` (FK), `user` (FK to CustomerUser), `attendee_name`, `attendee_email`, `duration_minutes`
  - DB Table: `gotomeeting_attendee`
  - Created via `MeetingAttendee.objects.get_or_create(meeting=meeting, attendee_email=attendee_email, ...)` (line 482)

- ⚠️ **`GotoMeetings`** (legacy, DEPRECATED) - `coda/ai_services/models.py` (lines 98-122)
  - Still referenced in some legacy code but marked as DEPRECATED
  - DB Table: `getdata_gotomeetings`

**Additional Behavior:**
- If attendee duration > 3 minutes and not already awarded, automatically creates `TaskLinks` records (lines 504-556)
- Uses `MeetingActivityMapping` to map meetings to task activities (lines 508-512)
- Awards task points automatically (lines 541-545)

### 1.3 Manual Trigger View

**View:** `meetingFormView(request)`  
**File:** `coda/ai_services/views.py` (lines 567-682)

**Flow:**
1. Admin accesses view (likely via URL pattern in `ai_services/urls.py`)
2. POST request with `startDate` and `endDate` from `MeetingForm` (line 575)
3. Checks if meetings already exist in DB for date range (lines 584-587)
4. If not found, calls `getmeetingresponse(startDate, endDate)` (line 624)
5. Then calls `save_meeting_data(allDataJsons)` (line 632)
6. Displays results in template `ai_services/meetingList.html`

**Answer:** This ingestion is **MANUAL ONLY** - requires admin to:
- Navigate to the meeting form view
- Enter start and end dates
- Submit the form
- No automatic/scheduled fetching occurs

### 1.4 Background/Scheduled Tasks

**Celery Configuration:** `coda/coda_project/celery.py`

**Meeting-Related Tasks:**
- ❌ **`auto_uplaod_evidence`** - **COMMENTED OUT** (lines 52-57)
  - Task definition exists in `coda/coda_project/task.py` (lines 309-330)
  - Uses **legacy `GotoMeetings` model** (line 313)
  - Logic: Matches `GotoMeetings` records to users by username, creates `TaskLinks`
  - **Status:** Not scheduled, not active

**Other Tasks:**
- No other meeting-related celery tasks found in `celery.py`
- No meeting sync tasks in `ai_services/tasks.py` (only has `@shared_task` decorators but no meeting sync logic)

**Answer:** **TODAY, if nothing is manually triggered, NO new GoToMeeting meetings are automatically fetched into the DB.**

**Manual Process Required:**
1. Admin must access `meetingFormView` (URL pattern not confirmed but likely `/ai_services/meeting-form/` or similar)
2. Enter `startDate` and `endDate` in the form
3. Submit POST request
4. System fetches from API and saves to `Meeting` + `MeetingAttendee` tables

---

## 2. Evidence Upload (TaskLinks) – What Happens Today

### 2.1 TaskLinks Model

**File:** `coda/management/models.py` (lines 875-916)

**Key Fields:**
- `task` (ForeignKey → Task)
- `added_by` (ForeignKey → User)
- `link` (CharField, max_length=1000) - ⭐ **Stores URL as plain string**
- `drive_link` (URLField, max_length=2000)
- `doc` (FileField)
- `link_name`, `description`
- `is_active`, `is_featured`

**No Foreign Key to Meeting Model** - Only stores URL as string

### 2.2 Evidence Upload Flow

**View:** `newevidence(request, taskid)`  
**File:** `coda/management/views.py` (lines 1772-1843)

**Form:** `EvidenceForm`  
**File:** `coda/management/forms.py` (lines 209-254)

**Template:** `management/daf/evidence_form.html`

**Step-by-Step Flow:**

1. **User submits form** (POST request, line 1778)
   - Form validates link/file (lines 1787-1800)
   - Checks for duplicate links (lines 1803-1814)

2. **Processing function:** `process_evidence_submission(...)`  
   **File:** `coda/management/views.py` (lines 1846-1888)

3. **TaskLinks record created** (lines 1858-1868):
   ```python
   TaskLinks.objects.create(
       task=task,
       added_by=user,
       link_name=data.get('link_name', 'General'),
       description=data.get('description', ''),
       link=data.get('link', ''),  # ⚠️ Just stored as plain string
       linkpassword=data.get('linkpassword', 'No Password Needed'),
       drive_link=drive_link,
       is_active=data.get('is_active', True),
       is_featured=data.get('is_featured', False),
   )
   ```

### 2.3 What Does NOT Happen

**Answer to Questions:**

1. **Is any attempt made to parse the GoToMeeting URL to extract a meeting ID?**  
   ❌ **NO** - No URL parsing code in `newevidence()` or `process_evidence_submission()`

2. **Is any attempt made to look up a Meeting record by URL or meeting_id?**  
   ❌ **NO** - No database queries to `Meeting` model in evidence upload flow

3. **Is the TaskLinks row linked to a Meeting row in any way?**  
   ❌ **NO** - No FK, no meeting_id field, no linking logic

**Summary:** When a user pastes a GoToMeeting URL and submits:
- URL is stored as plain string in `TaskLinks.link`
- No meeting lookup occurs
- No meeting ID extraction occurs
- No connection to `Meeting` model is created

---

## 3. Quality & Duration – How Meetings Are Used

### 3.1 ChecklistEvaluationService

**File:** `coda/management/services/checklist_evaluation_service.py`

**Method:** `_get_meeting_duration_minutes(task, task_links)` (lines 333-392)

**Current Implementation:**

```python
# Lines 347-353: Collect URLs from TaskLinks
recording_urls = []
for task_link in task_links:
    if task_link.link:
        recording_urls.append(task_link.link.strip())
    if task_link.drive_link:
        recording_urls.append(task_link.drive_link.strip())

# Lines 360-362: Exact string match only
meetings = Meeting.objects.filter(
    Q(recording_url__in=recording_urls) | Q(download_url__in=recording_urls)
)
```

**Answer to Questions:**

1. **How does it try to find a meeting?**  
   - Collects URLs from `TaskLinks.link` and `TaskLinks.drive_link`
   - Queries `Meeting` model with exact string match: `recording_url__in=recording_urls` OR `download_url__in=recording_urls`
   - No URL parsing, no meeting ID extraction

2. **Does it do any URL parsing or meeting_id extraction?**  
   ❌ **NO** - Lines 365-368 show a comment: "Try matching by meeting_id if URLs contain meeting IDs" but the code is just `pass` (not implemented)

3. **Under what conditions does it return a non-zero duration?**  
   - Only if `TaskLinks.link` **exactly matches** (character-for-character) `Meeting.recording_url` OR `Meeting.download_url`
   - Then sums `Meeting.duration_minutes` for all matched meetings (lines 371-373)

### 3.2 DAFSummaryService Integration

**File:** `coda/management/services/daf_summary_service.py`

**Method:** `_get_activities_data(...)` (lines 625-761)

**Flow:**
1. Calls `calculate_quality_score(task, activity_def)` (line 674)
   - This internally calls `ChecklistEvaluationService.get_task_quality_score(task)`
   - Which calls `_get_meeting_duration_minutes()` to get duration

2. Populates activity data with quality metrics (lines 736-742):
   - `quality_score`
   - `duration_factor` (from `_calculate_duration_factor()`)
   - `evidence_coverage`
   - `evidence_status` ("complete", "partial", "missing")
   - `total_duration_minutes`

### 3.3 Real-World Behavior

**For meeting-based activities (PBR, Client Training, Internal Training, Self-Training):**

**Scenario:** User pastes GoToMeeting URL that does NOT exactly match `Meeting.recording_url`

**What Happens:**
1. `_get_meeting_duration_minutes()` finds no matches (exact match fails)
2. Returns `total_duration = 0` (line 388)
3. `duration_factor = 0.0` (calculated in `_calculate_duration_factor()`, line 430)
4. Quality score is penalized: `quality_score = 0.5 * 0.0 + 0.3 * evidence_coverage + 0.2 * checklist_completion`
5. For high-impact activities, if `duration_factor < 0.5`, quality score is capped at 0.4 (line 529)

**Answer:** **In practice, for most real user submissions, `duration_minutes` is likely to be ZERO** because:
- Users paste URLs like `transcripts.gotomeeting.com/#/s/<hash>`
- API stores URLs as `recording.get('shareUrl')` (different format)
- Exact string matching fails
- No URL normalization or meeting ID extraction exists

---

## 4. Are Meeting Records Actually Used End-to-End?

### 4.1 Current State Assessment

**Answer:** **Meeting records are PARTIALLY WIRED but NOT reliably used end-to-end.**

### 4.2 End-to-End Path Analysis (Eunice Example)

**Scenario:** Eunice has a PBR task, uploads GoToMeeting URL as evidence

**Step 1: Evidence Upload**
- Eunice clicks "Upload Evidence" on DAF
- Pastes URL: `https://transcripts.gotomeeting.com/#/s/abc123...`
- `newevidence()` view saves to `TaskLinks.link` as plain string
- ❌ **No meeting lookup occurs**

**Step 2: Meeting Record Existence**
- **Question:** Does a `Meeting` record exist for this meeting?
  - **Answer:** Only if admin has manually run `meetingFormView()` for the date range containing this meeting
  - If not manually fetched, **no Meeting record exists**

**Step 3: Quality Evaluation (When DAF Summary is Generated)**
- `ChecklistEvaluationService._get_meeting_duration_minutes()` is called
- Tries to match `TaskLinks.link` to `Meeting.recording_url` (exact match)
- **Most likely outcome:** Match fails because:
  - URL format mismatch (user pasted `transcripts.gotomeeting.com` vs API stored `shareUrl` format)
  - Or Meeting record doesn't exist (not manually fetched)
- Returns `total_duration = 0`

**Step 4: Quality Score Calculation**
- `duration_factor = 0.0` (because `total_duration = 0`)
- Quality score penalized (50% weight on duration)
- Evidence status shows "missing" or "partial"

### 4.3 Conclusion

**Will the quality engine see `duration_minutes > 0`?**  
❌ **NO, in most cases** - because:
1. Meeting records may not exist (not automatically populated)
2. URL matching fails (exact match only, different URL formats)
3. No meeting ID extraction from URLs

**Will quality be calculated as if there is no reliable duration data?**  
✅ **YES** - Quality is calculated with `duration_factor = 0.0`, effectively treating it as if duration data is missing

**Is the normalized Meeting model realistically used?**  
⚠️ **PARTIALLY** - The model exists and is populated (manually), but:
- Evidence upload doesn't link to it
- Quality evaluation can't reliably find it
- Most evidence submissions result in `duration = 0` despite Meeting records potentially existing

---

## 5. Concrete Gaps & Risks (Bullet List)

- **There is no automatic job that regularly fetches meetings from the GoToMeeting API into the Meeting table.** The only way to populate meetings is via manual admin action through `meetingFormView()`.

- **Evidence upload (`newevidence` view, `process_evidence_submission` function) never calls any meeting service or lookup logic; it simply stores the URL as a plain string in `TaskLinks.link`.**

- **`ChecklistEvaluationService._get_meeting_duration_minutes()` only does exact string matching against `Meeting.recording_url` and `Meeting.download_url`; it does not parse or normalize GoToMeeting URLs, and does not extract meeting IDs from URLs.**

- **There is no utility function to extract meeting IDs from GoToMeeting URLs** (e.g., from `transcripts.gotomeeting.com/#/s/<hash>` format or from recording share URLs).

- **`MeetingLinkingService` exists (`coda/management/services/meeting_linking_service.py`) but is not invoked anywhere in the evidence upload flow or DAF quality evaluation path.**

- **The celery task `auto_uplaod_evidence` is commented out in `celery.py` (lines 52-57) and uses the deprecated `GotoMeetings` model, not the normalized `Meeting` model.**

- **Even if Meeting records exist in the DB, the quality engine cannot reliably find them** because URL formats differ between what users paste and what the API stores, and there is no URL normalization or meeting ID extraction.

- **For meeting-based activities (PBR, training sessions), quality scores are typically calculated with `duration_factor = 0.0`**, penalizing the overall quality score despite meetings potentially having occurred.

---

## 6. Suggested Next Step (ONE short paragraph)

**Recommended immediate action:** Enhance `ChecklistEvaluationService._get_meeting_duration_minutes()` to extract meeting IDs from GoToMeeting URLs (parse common formats like `transcripts.gotomeeting.com/#/s/<hash>` and recording share URLs) and match by `Meeting.meeting_id` instead of exact URL string matching. This requires creating a URL parsing utility function (`extract_meeting_id_from_url()`) and updating the matching logic in `checklist_evaluation_service.py` lines 358-368. This is a minimal, low-risk change that reuses existing `Meeting` model infrastructure and will immediately improve duration lookup success rate for evidence submissions, even if meetings were manually fetched. As a Phase 2 enhancement, consider adding on-demand meeting lookup in `process_evidence_submission()` to automatically fetch and populate meetings when evidence is uploaded, but start with the URL parsing enhancement first.

---

**End of Analysis Report**

