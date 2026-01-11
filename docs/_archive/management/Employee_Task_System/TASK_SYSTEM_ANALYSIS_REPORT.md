# CODA Task & Activities System - Comprehensive Analysis Report

**Date:** December 2025  
**Branch:** `25.12_CODA_DEV_CM`  
**Purpose:** Detailed, DRY-focused analysis of current task system to guide AI-driven pay system design

---

## Executive Summary
a
This report maps the current "Task & Activities" system in the CODA monolith, focusing on:
- **Reusable components** that should be preserved
- **Messy areas** requiring careful refactoring
- **Duplicate flows** to avoid
- **Extension points** for AI-driven, evidence-based pay system

**Key Finding:** The system has a solid foundation with `Task`, `TaskHistory`, `TaskLinks` (evidence), and `ActivityType` models. However, pay calculation logic is duplicated, evidence validation is not enforced for salary inclusion, and there are legacy free-text activity forms that should migrate to `ActivityType`.

---

## 1. Current Task System Models

### 1.1 Core Task Models

#### Task Model
**File:** `coda/management/models.py` (lines 476-779)

| Field | Type | Purpose | Notes |
|-------|------|---------|-------|
| `employee` | ForeignKey → User | Employee assigned to task | `is_staff=True, is_active=True` |
| `department` | ForeignKey → Department | Department snapshot | Added Dec 2024, nullable |
| `activity_type` | ForeignKey → ActivityType | **NEW:** Canonical activity | Optional, nullable |
| `is_client_project` | BooleanField | Billable work flag | Default: False |
| `activity_name` | CharField(255) | **LEGACY:** Free-text activity | Still used, should migrate to ActivityType |
| `category` | ForeignKey → TaskCategory | High-level category | PBR, Data Analysis, etc. |
| `point` | DecimalField(10,2) | Current completion (0 to mxpoint) | Incremented as work progresses |
| `mxpoint` | DecimalField(10,2) | Maximum points required | Used in pay calculation |
| `mxearning` | DecimalField(10,2) | Maximum earning potential | **LEGACY:** Used if no ActivityType |
| `submission` | DateTimeField | Last update timestamp | `auto_now=True` |
| `is_active` | BooleanField | Task active status | Default: True |
| `featured` | BooleanField | Featured task flag | Default: True |

**Key Properties:**
- `get_pay`: **DUAL LOGIC** - Uses `ActivityType` if available, else falls back to legacy `(point/mxpoint) × mxearning × late_penalty`
- `late_penalty`: 0.98 if submitted after deadline, else 1.0
- `deadline`: End of current month

**Domain Concept:** Current month's active task template. Points accumulate during the month, then snapshot to `TaskHistory` on monthly reset.

---

#### TaskHistory Model
**File:** `coda/management/models.py` (lines 839-1044)

| Field | Type | Purpose | Notes |
|-------|------|---------|-------|
| `employee` | ForeignKey → User | Employee snapshot | Same as Task |
| `department` | ForeignKey → Department | Department snapshot | Added Dec 2024 |
| `activity_name` | CharField(255) | Activity name snapshot | Copied from Task |
| `point`, `mxpoint`, `mxearning` | DecimalField | Snapshot values | Copied at reset time |
| `daf_date` | DateField | **CRITICAL:** Monthly filter date | Used for budget/salary queries |
| `submission` | DateTimeField | Snapshot timestamp | `auto_now=True` |
| `created_at` | DateTimeField | When TaskHistory created | Used for migration tracking |

**Key Properties:**
- `get_pay`: **LEGACY ONLY** - Always uses `(point/mxpoint) × mxearning × late_penalty` (no ActivityType support)

**Domain Concept:** Immutable monthly snapshot of Task state. Used for:
- Budget calculations (last month's data)
- Compliance tracking (33% rule)
- Salary calculations
- Historical analytics

**Critical Index:** `(daf_date, employee)` - Essential for monthly budget queries

---

#### TaskLinks Model (Evidence)
**File:** `coda/management/models.py` (lines 782-837)

| Field | Type | Purpose | Notes |
|-------|------|---------|-------|
| `task` | ForeignKey → Task | Links to Task (not TaskHistory) | **GAP:** No direct link to TaskHistory |
| `added_by` | ForeignKey → User | Who uploaded evidence | Staff/admin only |
| `link_name` | CharField(255) | Evidence name | Default: "General" |
| `description` | TextField | Evidence description | Optional |
| `link` | CharField(1000) | URL to evidence | GoToMeeting recordings, docs |
| `doc` | FileField | Uploaded document | Stored in `evidence/docs/` |
| `drive_link` | URLField(2000) | Google Drive link | For large files |
| `linkpassword` | CharField(255) | Password if needed | Default: "No Password Needed" |
| `is_active` | BooleanField | Evidence active status | Default: True |
| `is_featured` | BooleanField | Featured evidence flag | Default: False |

**Domain Concept:** Evidence layer attached to Tasks. Used for:
- Meeting recordings (GoToMeeting links)
- Documents (file uploads)
- Drive links (Google Drive)
- External URLs

**Restrictions:**
- Same user cannot upload same link twice (always blocked)
- Different users can upload same link for: BOG, BI Sessions, DAF Sessions, Project, web sessions
- Different users blocked for all other activities (unless temporary override)

**Gap:** Evidence links to `Task`, not `TaskHistory`. This creates a disconnect when querying historical evidence for salary calculations.

---

#### ActivityType Model
**File:** `coda/management/models.py` (lines 299-418)

| Field | Type | Purpose | Notes |
|-------|------|---------|-------|
| `name` | CharField(255) | Canonical activity name | Unique |
| `slug` | SlugField(255) | URL-friendly identifier | Auto-generated |
| `department` | ForeignKey → Department | Department assignment | Optional |
| `category` | ForeignKey → TaskCategory | Category assignment | Optional |
| `subcategory` | ForeignKey → TaskSubcategory | Subcategory | Optional |
| `unit_type` | CharField(32) | Unit type | session, hour, meeting, etc. |
| `unit_rate` | DecimalField(10,2) | Earning per unit | Default: 0 |
| `monthly_target_units` | PositiveIntegerField | Target units per month | Default: 0 |
| `points_per_unit` | DecimalField(10,2) | Points per unit | Default: 0 |
| `is_billable` | BooleanField | Billable client work | Default: False |
| `is_active` | BooleanField | Activity active status | Default: True |

**Key Properties:**
- `max_points_per_month`: `monthly_target_units × points_per_unit`
- `max_earning_per_month`: `monthly_target_units × unit_rate`

**Domain Concept:** Master data for standardized activities. Replaces free-text `activity_name` with canonical definitions.

**Status:** ✅ Already seeded. Tasks can reference via `activity_type` FK, but many still use legacy `activity_name`.

---

### 1.2 Supporting Models

#### TaskCategory Model
**File:** `coda/management/models.py` (lines 235-278)

| Field | Type | Purpose |
|-------|------|---------|
| `title` | CharField(55) | Category name (PBR, Data Analysis, etc.) |
| `description` | TextField | Category description |

**Current Categories:**
- Other (32% - needs better classification)
- Department
- PBR
- Data Analysis
- Website Development

**Domain Concept:** High-level activity categorization.

---

#### TaskSubcategory Model
**File:** `coda/management/models.py` (lines 281-296)

| Field | Type | Purpose |
|-------|------|---------|
| `category` | ForeignKey → TaskCategory | Parent category |
| `name` | CharField(255) | Subcategory name |
| `description` | TextField | Optional description |

**Domain Concept:** Second-level categorization under TaskCategory.

---

#### TaskGroups Model
**File:** `coda/accounts/models.py` (lines 752-768)

| Field | Type | Purpose |
|-------|------|---------|
| `title` | CharField | Group name (e.g., "Group H", "Group I") |

**Group Logic:**
- **Group H:** Contractual employees - increments `mxearning` after 30 hours: `mxearning += (total_point // 3)`
- **Group I:** Interns - no earning (`mxearning = 0`)
- **Other Groups:** Trigger `mxearning` increment via `increment_in_graduation_of_employee()` when group changes

**Domain Concept:** Employee leveling system that affects earnings.

---

### 1.3 Related Activity Models

#### Training Model
**File:** `coda/management/models.py` (lines 26-107)

Represents training sessions with:
- `presenter` (User), `department`, `category`, `subcategory`, `topic`
- `level` (1-5), `session`, `session_link`
- `created_date`, `expiration_date`, `is_active`, `is_mock`

**Domain Concept:** Training session records (not directly linked to Task/TaskHistory).

---

#### Requirement Model
**File:** `coda/management/models.py` (lines 1046-1157)

Represents requirements tracking with:
- `category` (Reporting, Website, ETL, Database, Other)
- `requestor` (Management, Client, Other)
- `status` (Critical, High, Medium, Low)
- `creator`, `assigned_to`, `duration`, `delivery_date`
- `what`, `why`, `how`, `comments`
- `doc`, `pptlink`, `videolink`

**Domain Concept:** Requirements management (not directly linked to Task/TaskHistory).

---

#### Meetings Model
**File:** `coda/management/models.py` (lines 1213-1250)

Represents scheduled meetings with:
- `department`, `category`, `group` (clients, internal, external)
- `meeting_topic`, `meeting_id`, `meeting_type`, `meeting_link`
- `meeting_time`, `frequency` (Daily, Weekly, Bi_Weekly, Monthly, Yearly)
- `is_active`, `is_featured`

**Domain Concept:** Meeting templates/schedules (not directly linked to Task/TaskHistory).

---

## 2. Evidence & GoToMeeting Integration

### 2.1 Evidence Models and Flows

#### TaskLinks (Primary Evidence Model)
**Location:** `coda/management/models.py` (lines 782-837)

**What It Stores:**
- URLs (meeting recordings, external links)
- File uploads (documents)
-,Google Drive links
- Passwords for protected content

**How It Links:**
- **Direct:** `task` FK → `Task` (not `TaskHistory`)
- **Indirect:** Via `added_by` → `User` (employee)

**Gap:** No direct link to `TaskHistory`, making historical evidence queries complex.

---

### 2.2 GoToMeeting Integration

#### GotoMeetings Model
**Location:** `coda/ai_services/models.py` (referenced in docs)

**Current Structure (Phase 1 - Denormalized):**
- One record per attendee (duplicates meeting info)
- `meeting_topic`, `meeting_id`, `attendee_name`, `attendee_email`
- `attendee_duration` (minutes)
- `recording` (URL to recording)

**Issues:**
- ❌ CharField for dates (should be DateTimeField)
- ❌ No unique constraints (creates duplicates)
- ❌ One record per attendee (denormalized)

---

#### Meeting Linking Flow

**1. How GoToMeeting Records Enter System:**

**Location:** `coda/coda_project/task.py` (lines 309-330)

```python
@shared_task(name="auto_uplaod_evidence")
def auto_uplaod_evidence():
    # Fetches GotoMeetings records created after last TaskLinks
    goto_data = GotoMeetings.objects.filter(created_at__gte=links.created_at)
    
    # For each meeting with attendee_duration > 5 minutes:
    for goto_meet in goto_data:
        # Match attendee to user by username (case-insensitive)
        if user.username.casefold() == goto_meet.attendee_name.casefold():
            # Find task by activity_name matching meeting_topic
            task_obj = Task.objects.filter(
                employee=user,
                activity_name=goto_meet.meeting_topic
            ).first()
            
            # Fallback to "General Meeting" if no match
            if not task_obj:
                task_obj = Task.objects.filter(activity_name='General Meeting').first()
            
            # Award point if not at max and not job support
            if points != maxpoints and task_obj.activity_name.lower() not in JOB_SUPPORTS:
                Task.objects.filter(id=task_obj.id).update(point=points + 1)
            
            # Create TaskLinks evidence
            TaskLinks.objects.create(
                task=task_obj,
                added_by=user,
                link_name=goto_meet.meeting_topic,
                description=goto_meet.meeting_topic,
                link=goto_meet.recording
            )
```

**Issues:**
- ❌ **Fragile string matching:** `activity_name == meeting_topic` (case-sensitive, exact match)
- ❌ **Hardcoded fallback:** "General Meeting" if no match
- ❌ **No ActivityType integration:** Uses legacy `activity_name`
- ❌ **No confidence scoring:** Binary match/no-match
- ❌ **No manual review:** Auto-links without validation

---

**2. How Meetings Are Linked to Tasks Today:**

**Service:** `coda/management/services/meeting_linking_service.py`

**Strategies (in order of confidence):**
1. **Exact mapping** (95% confidence) - `MeetingActivityMapping` model (if exists)
2. **Keyword matching** (40-90% confidence) - Meeting topic → task activity name
3. **Historical patterns** (50-85% confidence) - User's past meeting-task links
4. **Category matching** (75% confidence) - Meeting type → task category
5. **Participant-based matching** (not implemented)

**Auto-Link Threshold:** 80% confidence → automatic linking  
**Review Threshold:** 60-80% confidence → requires manual review

**Current Status:**
- ✅ Service exists and uses `MeetingServiceInterface` (decoupled)
- ⚠️ **Gap:** Many meetings still linked via legacy `auto_uplaod_evidence` task
- ⚠️ **Gap:** Evidence not required for salary inclusion

---

**3. How Evidence Is Used:**

**Compliance:**
- ✅ `EvidenceValidationService` checks coverage (target: 80%)
- ❌ **Not enforced:** Tasks without evidence still included in salary calculations

**Pay:**
- ❌ **Not used:** Evidence not checked in `Task.get_pay` or `TaskHistory.get_pay`
- ❌ **No validation:** Billable activities (`is_billable=True`) can have pay without evidence

**Reporting:**
- ✅ `EvidenceValidationService.get_evidence_coverage()` provides coverage stats
- ✅ `EvidenceValidationService.get_tasks_without_evidence()` identifies gaps
- ⚠️ **Gap:** Evidence reports not integrated into salary dashboard

---

### 2.3 Gaps & Weaknesses

1. **Evidence Not Required for Salary:**
   - Tasks without evidence still included in pay calculations
   - No enforcement of "billable activities must have evidence" rule

2. **Fragile String Matching:**
   - Legacy `auto_uplaod_evidence` uses exact string match
   - No fuzzy matching or ActivityType integration

3. **TaskLinks → TaskHistory Disconnect:**
   - Evidence links to `Task`, not `TaskHistory`
   - Historical evidence queries require complex joins

4. **Manual Review Not Enforced:**
   - Low-confidence links should require review, but system doesn't block salary inclusion

5. **MeetingServiceInterface Integration:**
   - ✅ Already wired via adapters
   - ⚠️ Legacy `auto_uplaod_evidence` still runs in parallel

---

## 3. Current Pay / Salary Logic and Finance Integration

### 3.1 Task.get_pay Implementation

**File:** `coda/management/models.py` (lines 626-690)

**Current Logic (DUAL PATH):**

```python
@property
def get_pay(self):
    # Prefer ActivityType-based calculation if available
    if self.activity_type and self.activity_type.is_active:
        return self._get_pay_from_activity_type()
    
    # Fall back to legacy calculation
    return self._get_pay_legacy()

def _get_pay_from_activity_type(self):
    """Calculate pay using ActivityType configuration."""
    # Calculate expected points for full target
    expected_points_for_full_target = (
        activity_type.monthly_target_units * activity_type.points_per_unit
    )
```

*(truncated – see original report for full details)*



