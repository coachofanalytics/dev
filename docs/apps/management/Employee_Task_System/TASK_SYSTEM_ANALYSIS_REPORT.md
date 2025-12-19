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
- Google Drive links
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
    
    # Calculate max earning for full target
    max_earning_for_type = activity_type.max_earning_per_month
    
    # Proportional pay: max_earning * (points_earned / points_for_full_target)
    if task.point >= expected_points_for_full_target:
        earning = max_earning_for_type
    else:
        earning = max_earning_for_type * (task.point / expected_points_for_full_target)
    
    # Apply late penalty
    return earning * late_penalty

def _get_pay_legacy(self):
    """Legacy pay calculation using mxpoint and mxearning."""
    if self.point > self.mxpoint:
        return Decimal('0')
    else:
        Earning = round((self.point / self.mxpoint) * self.mxearning, 2)
        compute_pay = Earning * Decimal(self.late_penalty)
        return round(compute_pay, 2)
```

**Summary:**
> Today, an employee's pay for a Task is computed as:
> - **If ActivityType exists:** Proportional pay based on `(points_earned / points_for_full_target) × max_earning_per_month × late_penalty`
> - **If no ActivityType:** Legacy `(point / mxpoint) × mxearning × late_penalty`
> - **Late penalty:** 0.98 if submitted after month-end deadline, else 1.0

**Issues:**
- ❌ **No evidence check:** Pay calculated regardless of evidence
- ❌ **No billable validation:** `is_billable=True` tasks can have pay without evidence
- ⚠️ **Dual logic:** ActivityType vs legacy creates inconsistency

---

### 3.2 TaskHistory.get_pay Implementation

**File:** `coda/management/models.py` (lines 1034-1044)

**Current Logic (LEGACY ONLY):**

```python
@property
def get_pay(self):
    if self.point > self.mxpoint:
        return 0
    else:
        try:
            Earning = round(Decimal(self.point / self.mxpoint) * self.mxearning, 2)
        except Exception as ZeroDivisionError:
            Earning = 0.0
        compute_pay = Decimal(Earning) * Decimal(self.late_penalty)
        pay = round(compute_pay, 2)
        return pay
```

**Summary:**
> TaskHistory pay is **always** calculated using legacy formula: `(point / mxpoint) × mxearning × late_penalty`

**Issues:**
- ❌ **No ActivityType support:** TaskHistory doesn't store `activity_type` FK
- ❌ **No evidence check:** Historical pay calculated regardless of evidence
- ⚠️ **Inconsistency:** Task uses ActivityType, TaskHistory uses legacy

---

### 3.3 From Task/TaskHistory to Finance

#### Integration Point 1: Compliance Calculator
**File:** `coda/management/services/compliance_calculator.py`

**What It Does:**
- Calculates 33% compliance rule: `(total_points / total_max_points) × 100 ≥ 33`
- Filters compliant employees for salary inclusion
- Uses `TaskHistory` with `daf_date` filtering

**Key Method:**
```python
def calculate_compliance(employee, target_month, target_year):
    tasks = TaskHistory.objects.filter(
        employee=employee,
        daf_date__month=target_month,
        daf_date__year=target_year
    )
    
    totals = tasks.aggregate(
        total_points=Sum('point'),
        total_max_points=Sum('mxpoint'),
        total_earnings=Sum(F('point') / F('mxpoint') * F('mxearning'))
    )
    
    completion_rate = (total_points / total_max_points) * 100
    is_compliant = completion_rate >= 33.0
```

**Source of Truth:** `TaskHistory.point`, `TaskHistory.mxpoint`, `TaskHistory.mxearning`

**Gaps:**
- ❌ **No evidence validation:** Compliance calculated regardless of evidence
- ❌ **Uses legacy formula:** `(point/mxpoint) × mxearning` (no ActivityType)

---

#### Integration Point 2: Budget Integration Views
**File:** `coda/management/views/budget_integration_views.py`

**What It Does:**
- Exposes API endpoints for Finance app to query activity totals
- Validates evidence coverage
- Returns compliant employees with salary amounts

**Key Endpoints:**
- `GET /management/api/budget/activity-totals/` - Activity totals by department/category
- `GET /management/api/budget/evidence-validation/` - Evidence validation report

**Source of Truth:** `TaskHistory` with `daf_date` filtering

**Gaps:**
- ⚠️ **Evidence validation exists but not enforced:** Reports missing evidence but doesn't block salary

---

#### Integration Point 3: Finance Salary Dashboard
**File:** `coda/finance/views/budget/views_salary_dashboard.py`

**What It Does:**
- Displays salary dashboard with employee breakdowns
- Uses `integrated_service.get_salary_dashboard_data()` (from management)
- Shows compliant vs non-compliant employees

**Source of Truth:** Management API endpoints (which use `TaskHistory`)

**Gaps:**
- ❌ **No evidence enforcement:** Salary calculated regardless of evidence

---

#### Integration Point 4: Finance Enhanced Approvals
**File:** `coda/finance/views/budget/views_enhanced_approvals.py`

**What It Does:**
- Budget approval workflow
- Queries `TaskHistory` directly for salary calculations
- Includes compliance checks

**Key Code:**
```python
from management.models import TaskHistory
task_history = TaskHistory.objects.filter(
    employee=employee,
    daf_date__month=target_month,
    daf_date__year=target_year
)
```

**Source of Truth:** `TaskHistory` with `daf_date` filtering

**Gaps:**
- ❌ **No evidence validation:** Direct TaskHistory queries bypass evidence checks

---

### 3.4 Duplication & Inconsistencies

**1. Pay Calculation Duplication:**
- `Task.get_pay` (ActivityType + legacy)
- `TaskHistory.get_pay` (legacy only)
- `ComplianceCalculator` (legacy formula in aggregate)
- `calculate_total_pay()` in `management/utils.py` (legacy formula)

**2. Formula Inconsistencies:**
- Task uses ActivityType if available
- TaskHistory always uses legacy
- ComplianceCalculator always uses legacy
- Finance views use legacy via TaskHistory

**3. Evidence Validation Not Enforced:**
- `EvidenceValidationService` exists but not called in pay calculations
- Billable activities can have pay without evidence
- No "evidence required" flag in ActivityType

---

## 4. Views & Templates (Legacy UI)

### 4.1 Task-Related Views

| View Function | URL Pattern | Template | Purpose |
|---------------|-------------|----------|---------|
| `TaskListView` | `/management/tasks/` | `management/daf/tasklist.html` | Admin: List all tasks |
| `TaskDetailView` | `/management/tasks/<pk>/` | `management/daf/task_detail.html` | Admin: Task details |
| `TaskUpdateView` | `/management/task/<pk>/update/` | `management/daf/tasknew_form.html` | Admin: Edit task |
| `UsertaskUpdateView` | `/management/usertask/<pk>/update/` | `management/daf/tasknew_form.html` | Employee: Edit own task |
| `payslip` | `/management/payroll/` | `management/daf/payslip.html` | Employee: View payslip |
| `usertasks` | `/management/payroll/?pay_type=usertasks` | `management/daf/usertasks.html` | Employee: My current tasks |
| `usertaskhistory` | `/management/payroll/?pay_type=usertaskhistory` | `management/daf/taskhistory.html` | Employee: My task history |
| `newevidence` | `/management/newevidence/<taskid>` | `management/daf/evidence_form.html` | Employee: Upload evidence |
| `userevidence` | `/management/userevidence/` | `management/daf/userevidence.html` | Employee: My evidence |
| `enhanced_task_dashboard` | `/management/enhanced-dashboard/` | `management/enhanced_task_dashboard.html` | Employee: Enhanced dashboard |
| `meeting_link_review_dashboard` | `/management/meeting-links/review/` | `management/daf/meeting_link_review.html` | Admin: Review meeting links |
| `reset_tasks_select` | `/management/reset_tasks/select/` | `management/daf/reset_tasks_select.html` | Admin: Selective task reset |

---

### 4.2 Core Employee Views (Daily Use)

**These 5 templates should become the new main UX for employees/managers:**

1. **`management/daf/usertasks.html`** - Employee's current month tasks
   - Shows tasks with points, mxpoint, mxearning
   - Links to evidence upload
   - **Candidate for ActivityType redesign**

2. **`management/daf/taskhistory.html`** - Employee's historical tasks
   - Shows TaskHistory records by month
   - Used for payslip calculation
   - **Candidate for ActivityType + evidence integration**

3. **`management/daf/evidence_form.html`** - Evidence upload form
   - Upload links, files, Drive links
   - **Keep as-is, enhance with ActivityType suggestions**

4. **`management/enhanced_task_dashboard.html`** - Enhanced dashboard
   - Modern UI with analytics
   - **Good foundation for AI-driven features**

5. **`management/daf/meeting_link_review.html`** - Meeting link review
   - Review auto-linked meetings
   - **Keep as-is, enhance with AI confidence scores**

---

### 4.3 Admin Views (Can Stay Mostly As-Is)

**These admin templates can stay mostly as-is or be simplified:**

1. **`management/daf/tasklist.html`** - Admin task list
   - Bulk operations, filters
   - **Simplify: Remove free-text activity_name, use ActivityType dropdown**

2. **`management/daf/tasknew_form.html`** - Task creation/edit form
   - **CRITICAL:** Migrate from free-text `activity_name` to ActivityType FK

3. **`management/daf/reset_tasks_select.html`** - Selective task reset
   - **Keep as-is:** Already uses TaskResetService

---

## 5. DRY Analysis: Reusable vs Replace

### 5.1 Reusable Building Blocks

**✅ Keep As-Is or Lightly Refactor:**

1. **TaskResetService** (`coda/management/services/task_reset_service.py`)
   - ✅ Solid monthly reset pipeline
   - ✅ Proper transaction handling
   - ✅ Department snapshot logic
   - **Action:** Keep, add ActivityType snapshot to TaskHistory

2. **ComplianceCalculator** (`coda/management/services/compliance_calculator.py`)
   - ✅ Single source of truth for 33% rule
   - ✅ Point-based calculation
   - **Action:** Keep, add evidence validation integration

3. **EvidenceValidationService** (`coda/management/services/evidence_validation_service.py`)
   - ✅ Evidence coverage calculation
   - ✅ Missing evidence identification
   - **Action:** Keep, integrate into pay calculation pipeline

4. **MeetingLinkingService** (`coda/management/services/meeting_linking_service.py`)
   - ✅ Multi-strategy linking (exact, keyword, historical, category)
   - ✅ Confidence scoring
   - ✅ Uses MeetingServiceInterface (decoupled)
   - **Action:** Keep, enhance with ActivityType matching

5. **TaskLinks Model** (Evidence)
   - ✅ Solid evidence storage
   - **Action:** Keep, add optional FK to TaskHistory for historical queries

6. **ActivityType Model**
   - ✅ Master data structure
   - ✅ Already seeded
   - **Action:** Keep, migrate all tasks to use ActivityType

---

### 5.2 Things We Should Wrap, Not Bypass

**✅ Extend Existing Services:**

1. **Monthly Reset Pipeline** (`TaskResetService`)
   - ✅ Already correct
   - **Action:** Hang new ActivityType logic off it instead of writing a second reset

2. **Compliance Calculation** (`ComplianceCalculator`)
   - ✅ Already correct formula
   - **Action:** Add evidence validation as a filter, not a separate calculation

3. **Evidence Validation** (`EvidenceValidationService`)
   - ✅ Already correct coverage calculation
   - **Action:** Integrate into pay calculation, don't create parallel validation

---

### 5.3 Things That Should Be Deprecated or Replaced

**❌ Replace:**

1. **Legacy Free-Text `activity_name` Forms**
   - **Location:** `management/daf/tasknew_form.html`
   - **Issue:** Allows arbitrary activity names, creates data quality issues
   - **Action:** Replace with ActivityType dropdown, migrate existing tasks

2. **Duplicate Pay Calculations**
   - **Locations:**
     - `Task.get_pay` (ActivityType + legacy)
     - `TaskHistory.get_pay` (legacy only)
     - `calculate_total_pay()` in `utils.py` (legacy)
   - **Issue:** Inconsistent formulas, no evidence check
   - **Action:** Create unified `PayCalculationService` with:
     - ActivityType support
     - Evidence validation
     - Single source of truth

3. **Legacy `auto_uplaod_evidence` Task**
   - **Location:** `coda/coda_project/task.py` (lines 309-330)
   - **Issue:** Fragile string matching, no ActivityType integration
   - **Action:** Deprecate, use `MeetingLinkingService` instead

4. **TaskHistory.get_pay (Legacy Only)**
   - **Issue:** No ActivityType support, inconsistent with Task.get_pay
   - **Action:** Add ActivityType snapshot to TaskHistory, use same calculation as Task

---

### 5.4 Extension Points for AI

**🎯 Best Spots to Plug AI:**

1. **ActivityType Mapping from Free-Text**
   - **Service:** `TaskStandardizationService` (already exists)
   - **Enhancement:** Add AI classifier to map free-text `activity_name` → ActivityType
   - **Location:** `coda/management/services/task_standardization_service.py`
   - **Hook:** `_get_standardized_name()` method

2. **AI-Suggested ActivityTypes**
   - **Service:** New `ActivityTypeSuggestionService`
   - **Location:** `coda/management/services/activity_type_suggestion_service.py`
   - **Hook:** Analyze TaskHistory patterns, suggest new ActivityTypes
   - **Trigger:** When new activity patterns detected in TaskHistory

3. **Evidence Validation with AI**
   - **Service:** `EvidenceValidationService` (already exists)
   - **Enhancement:** Add AI validation for evidence quality (e.g., meeting recording duration, document relevance)
   - **Location:** `coda/management/services/evidence_validation_service.py`
   - **Hook:** `get_evidence_coverage()` method

4. **Anomaly Detection for Fraud Risk**
   - **Service:** `AnomalyDetectionService` (already exists)
   - **Enhancement:** Add risk scoring for tasks without evidence, high pay without evidence
   - **Location:** `coda/management/services/anomaly_detection_service.py`
   - **Hook:** Add `risk_score` field to Task/TaskHistory models

5. **Meeting-Task Linking with AI**
   - **Service:** `MeetingLinkingService` (already exists)
   - **Enhancement:** Improve confidence scoring with ML models
   - **Location:** `coda/management/services/meeting_linking_service.py`
   - **Hook:** `_find_task_matches()` method

6. **Budget Suggestions with AI**
   - **Service:** `ForecastingService` (already exists)
   - **Enhancement:** Generate budget suggestions based on ActivityType patterns
   - **Location:** `coda/management/services/forecasting_service.py`
   - **Hook:** Add `generate_budget_suggestions()` method

---

## 6. New Feature Hooks: AI-Suggested Activities & Evidence-Driven Automation

### 6.1 AI-Suggested ActivityTypes

**Where to Implement:**

**Service:** `coda/management/services/activity_type_suggestion_service.py` (NEW)

**Key Methods:**
```python
def suggest_new_activity_types_from_patterns(
    min_occurrences: int = 10,
    min_employees: int = 3
) -> List[Dict[str, Any]]:
    """
    Analyze TaskHistory patterns to suggest new ActivityTypes.
    
    Looks for:
    - Frequent activity_name patterns not in ActivityType
    - Similar activities that could be consolidated
    - Department-specific patterns
    """
    # Query TaskHistory for unique activity_name patterns
    # Group by department, category
    # Calculate frequency, employee count
    # Return suggestions with confidence scores
```

**Hook Points:**
1. **Monthly Reset:** After `TaskResetService.reset_tasks()`, analyze new TaskHistory records
2. **Admin Dashboard:** Add "Suggest New Activities" button
3. **Task Creation:** When employee creates task with new activity_name, suggest ActivityType

**Integration:**
- Use `TaskHistoryAnalyzer` to identify patterns
- Use `TaskStandardizationService` to normalize names
- Create ActivityType suggestions with confidence scores

---

### 6.2 Automatic GoToMeeting Fetching & Linking

**Where to Implement:**

**Service:** `coda/management/services/meeting_automation_service.py` (NEW)

**Key Methods:**
```python
def fetch_and_link_meetings_automatically(
    start_date: date,
    end_date: date,
    auto_link_threshold: float = 0.8
) -> Dict[str, Any]:
    """
    Fetch meetings from GoToMeeting via MeetingServiceInterface,
    link to tasks automatically if confidence >= threshold.
    """
    # 1. Fetch meetings via MeetingServiceInterface
    meetings = meeting_service.get_meetings_in_date_range(start_date, end_date)
    
    # 2. For each meeting, use MeetingLinkingService to find matches
    for meeting in meetings:
        for attendee in meeting.attendees:
            user = match_user_by_email(attendee.email)
            if user:
                result = meeting_linking_service.link_meeting_to_tasks(
                    meeting_id=meeting.id,
                    attendee=user,
                    attendee_duration=attendee.duration
                )
                
                # 3. Auto-link if confidence >= threshold
                if result['confidence'] >= auto_link_threshold:
                    # Create TaskLinks evidence automatically
                    create_evidence_from_meeting(meeting, user, result['best_match']['task'])
```

**Hook Points:**
1. **Scheduled Task:** Daily Celery task to fetch and link meetings
2. **Manual Trigger:** Admin "Fetch Meetings" button
3. **After Meeting Created:** Webhook from GoToMeeting (if available)

**Integration:**
- Use `MeetingServiceInterface` (already decoupled)
- Use `MeetingLinkingService` (already exists)
- Use `TaskLinks` model for evidence storage

---

### 6.3 Evidence-Driven Automation & Enforcement

**Where to Implement:**

**Service:** `coda/management/services/evidence_enforcement_service.py` (NEW)

**Key Methods:**
```python
def enforce_evidence_requirements(
    target_month: int,
    target_year: int,
    enforce_billable: bool = True
) -> Dict[str, Any]:
    """
    Enforce evidence requirements for salary inclusion.
    
    Rules:
    - Billable activities (is_billable=True) MUST have evidence
    - Activities with high pay (>$100) SHOULD have evidence
    - Non-compliant tasks excluded from salary calculations
    """
    # 1. Get all TaskHistory for target month
    tasks = TaskHistory.objects.filter(
        daf_date__month=target_month,
        daf_date__year=target_year
    )
    
    # 2. Check evidence coverage
    for task in tasks:
        has_evidence = TaskLinks.objects.filter(task_id=task.id).exists()
        
        # 3. Apply rules
        if task.is_billable and not has_evidence:
            # Exclude from salary
            task.excluded_from_salary = True
            task.exclusion_reason = "Billable activity without evidence"
        
        if task.get_pay > 100 and not has_evidence:
            # Flag for review
            task.requires_review = True
    
    # 4. Return compliance report
    return {
        'total_tasks': tasks.count(),
        'excluded_tasks': tasks.filter(excluded_from_salary=True).count(),
        'flagged_tasks': tasks.filter(requires_review=True).count()
    }
```

**Hook Points:**
1. **Before Salary Calculation:** Call `enforce_evidence_requirements()` before calculating pay
2. **Monthly Reset:** After `TaskResetService.reset_tasks()`, enforce evidence for last month
3. **Budget Integration:** Filter out non-compliant tasks in `budget_activity_totals_api`

**Integration:**
- Use `EvidenceValidationService` (already exists)
- Add `excluded_from_salary` flag to TaskHistory model
- Modify `ComplianceCalculator` to respect evidence requirements

---

### 6.4 TODOs / Refactors Needed First

**Before Implementing New Features:**

1. **Migrate TaskHistory to Support ActivityType**
   - Add `activity_type` FK to TaskHistory model
   - Update `TaskResetService` to copy ActivityType from Task
   - Migrate existing TaskHistory records (backfill from Task.activity_name)

2. **Unify Pay Calculation**
   - Create `PayCalculationService` with single source of truth
   - Support ActivityType and legacy formulas
   - Add evidence validation integration

3. **Add Evidence Link to TaskHistory**
   - Add optional `task_history` FK to TaskLinks model
   - Or create `TaskHistoryLinks` model for historical evidence
   - Migrate existing evidence to link to TaskHistory

4. **Deprecate Legacy `auto_uplaod_evidence`**
   - Remove or disable Celery task
   - Migrate to `MeetingLinkingService`
   - Update documentation

5. **Add Evidence Requirements to ActivityType**
   - Add `evidence_required` BooleanField to ActivityType
   - Add `evidence_required_for_billable` BooleanField
   - Seed existing ActivityTypes with appropriate flags

---

## Conclusion

The current task system has a **solid foundation** with:
- ✅ Well-structured models (Task, TaskHistory, TaskLinks, ActivityType)
- ✅ Service layer architecture (TaskResetService, ComplianceCalculator, etc.)
- ✅ Evidence validation infrastructure
- ✅ Meeting linking service with AI hooks

**However, critical gaps exist:**
- ❌ Evidence not enforced for salary inclusion
- ❌ Pay calculation duplication and inconsistency
- ❌ Legacy free-text activity_name still in use
- ❌ TaskHistory doesn't support ActivityType

**Recommended Approach:**
1. **Reuse:** TaskResetService, ComplianceCalculator, EvidenceValidationService, MeetingLinkingService
2. **Wrap:** Add ActivityType support to existing services, don't bypass
3. **Replace:** Legacy pay calculations, free-text forms, `auto_uplaod_evidence` task
4. **Extend:** Add AI hooks to existing services, create new services for automation

**Next Steps:**
1. Migrate TaskHistory to support ActivityType
2. Create unified PayCalculationService
3. Add evidence enforcement to salary calculations
4. Implement AI-suggested ActivityTypes
5. Automate GoToMeeting fetching and linking

---

**Report Generated:** December 2025  
**Branch:** `25.12_CODA_DEV_CM`  
**Status:** Ready for AI-driven pay system design







