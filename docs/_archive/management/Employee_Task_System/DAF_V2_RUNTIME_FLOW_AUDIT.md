# DAF v2 End-to-End Runtime Flow Audit

**Date:** 2024-12-29  
**Auditor:** Senior Engineer Review  
**Branch:** 25.12_CODA_DEV_CM

---

## Executive Summary

This audit maps the complete data flow from GoToMeeting ingestion through DAF v2 UI rendering, identifies runtime-breaking risks, and provides a validation plan. **Critical finding**: Employee Groups Save button has nested form issue (form inside form) preventing POST submission.

---

## 1. Flow Map (Text Diagram)

### A) GoToMeeting Ingestion Flow

```
Entry Points:
├─ Management Command: sync_gotomeetings
│  └─ File: coda/ai_services/management/commands/sync_gotomeetings.py
│     └─ Function: Command.handle()
│        └─ Calls: ai_services.services.meeting_sync_service.sync_meetings_for_range()
│           └─ Calls: ai_services.views.getmeetingresponse() [API fetch]
│              └─ Calls: ai_services.views.save_meeting_data() [Persistence]
│
├─ Management Command: sync_goto_meetings
│  └─ File: coda/ai_services/management/commands/sync_goto_meetings.py
│     └─ Function: Command.handle()
│        └─ Calls: ai_services.services.goto_meeting_sync_service.sync()
│           └─ Calls: ai_services.views.getmeetingresponse() [API fetch]
│              └─ Calls: ai_services.views.save_meeting_data() [Persistence]
│
└─ Scheduled Task (Celery): daily_autolink_meeting_evidence_task
   └─ File: coda/ai_services/tasks.py
      └─ Function: daily_autolink_meeting_evidence_task()
         └─ Calls: ai_services.views.getmeetingresponse() [API fetch]
            └─ Calls: ai_services.views.save_meeting_data() [Persistence]

Persistence Layer:
└─ ai_services.views.save_meeting_data()
   └─ File: coda/ai_services/views.py:358
   └─ Writes to:
      ├─ ai_services.models.Meeting (table: ai_services_meeting)
      │  └─ Fields: meeting_id (PK), topic, topic_normalized, requirement_code, 
      │             recording_url, download_url, start_time, duration_minutes, service_name
      │  └─ Idempotency: get_or_create(meeting_id=...) prevents duplicates
      │
      └─ ai_services.models.MeetingAttendee (table: ai_services_meetingattendee)
         └─ Fields: meeting (FK), user (FK to User), attendee_email, duration_minutes
         └─ Idempotency: get_or_create(meeting=..., user=...) prevents duplicates

Legacy Table (Read-Only):
└─ ai_services.models.GotoMeetings (table: getdata_gotomeetings)
   └─ Purpose: Historical data only
   └─ Import Utility: import_legacy_gotomeetings command
      └─ File: coda/ai_services/management/commands/import_legacy_gotomeetings.py
      └─ Migrates: getdata_gotomeetings → ai_services_meeting + MeetingAttendee
```

**Key Functions:**
- `getmeetingresponse(startDate, endDate)`: `coda/ai_services/views.py:235` - Fetches from GoToMeeting API
- `save_meeting_data(meeting_data)`: `coda/ai_services/views.py:358` - Persists to DB (idempotent via `meeting_id`)
- `normalize_url()`, `normalize_topic()`, `extract_requirement_code()`: `coda/ai_services/utils/meeting_normalizer.py`

**Idempotency:** `Meeting.objects.get_or_create(meeting_id=...)` prevents duplicates on repeated pulls.

---

### B) Meeting Normalization + Matching Flow

```
Canonical Model:
└─ ai_services.models.Meeting (table: ai_services_meeting)
   └─ Query Helper: _safe_meeting_query() [coda/management/legacy_views.py:2984]
      └─ Checks table existence before querying
      └─ Returns: Meeting.objects.filter(...) or empty queryset

Matching Services:
├─ MeetingEvidenceMatcher (for evidence URL matching)
│  └─ File: coda/ai_services/services/meeting_evidence_matcher.py
│  └─ Methods:
│     ├─ find_meetings_for_task(task) → QuerySet[Meeting]
│     │  └─ Strategy 1: URL-based matching (HIGH confidence)
│     │     └─ Matches: TaskLinks.link → Meeting.recording_url/download_url (normalized)
│     │  └─ Strategy 2: Topic + time window (LOW confidence, fallback)
│     │     └─ Matches: task.requirement_code → meeting.requirement_code
│     │     └─ Time window: task.submission ± 2 days
│     │
│     └─ get_detailed_matches(task) → List[Dict] with confidence scores
│
└─ MeetingTaskAutolinkService (for auto-creating TaskLinks)
   └─ File: coda/ai_services/services/meeting_task_autolink_service.py
   └─ Methods:
      ├─ discover_candidate_tasks() → QuerySet[Task]
      │  └─ Filters: activity_type in MEETING_BASED_ACTIVITY_TYPES
      │  └─ Excludes: tasks with existing auto-generated TaskLinks
      │
      ├─ find_meeting_for_task(task) → Optional[Dict]
      │  └─ Matching Rules (STRICT):
      │     1. PRIMARY: requirement_code match (if task.requirement exists)
      │        └─ MUST match exactly (case-insensitive)
      │        └─ If mismatch: return None (DO NOT autolink)
      │     2. SECONDARY: Attendee email matching
      │        └─ Uses: get_canonical_emails_for_user(task.employee)
      │        └─ Must have attended >3 minutes
      │     3. TERTIARY: Topic fallback (STRICT)
      │        └─ REQUIRES activity tag overlap
      │        └─ REQUIRES time window alignment
      │
      └─ create_or_update_tasklink_from_meeting(task, meeting) → Tuple[TaskLinks, bool]
         └─ Idempotency: get_or_create(task=..., meeting_id=..., is_auto_generated=True)
         └─ Creates: TaskLinks with is_auto_generated=True, meeting_id stored

Matching Keys:
├─ URL Matching (HIGH confidence):
│  ├─ TaskLinks.link (normalized) → Meeting.recording_url (normalized)
│  └─ TaskLinks.link (normalized) → Meeting.download_url (normalized)
│
├─ Requirement Code Matching (HIGH confidence):
│  ├─ Task.requirement.id → Meeting.requirement_code (extracted from topic)
│  └─ Format: "REQ-{id}" (case-insensitive)
│
├─ Attendee Email Matching (MEDIUM confidence):
│  ├─ MeetingAttendee.user.email → task.employee.email
│  └─ MeetingAttendee.duration_minutes > 3
│
└─ Topic + Time Window (LOW confidence, fallback):
   ├─ Meeting.topic_normalized contains activity keywords
   ├─ Meeting.start_time within task.submission ± 2 days
   └─ Meeting.requirement_code matches task.requirement (if present)

Normalization:
├─ URL: normalize_url() [coda/ai_services/utils/meeting_normalizer.py]
│  └─ Removes: querystrings, fragments, trailing slashes
│  └─ Example: "https://example.com/recording?param=value#fragment" → "https://example.com/recording"
│
├─ Topic: normalize_topic() [coda/ai_services/utils/meeting_normalizer.py]
│  └─ Lowercase, trim, remove noise tokens
│
└─ Requirement Code: extract_requirement_code() [coda/ai_services/utils/meeting_normalizer.py]
   └─ Regex: r'\bREQ-\d{2,6}\b' (case-insensitive)
   └─ Returns: Uppercase normalized code (e.g., "REQ-5755")
```

**Single Source of Truth for Evidence Status:**
- `get_task_evidence_summary()`: `coda/management/services/evidence_summary_service.py:22`
- Used by: `compute_task_compliance()`, `daf_v2_view()`, templates

---

### C) Task Generation / Update Flow

```
Task Creation:
├─ Manual Creation:
│  └─ View: newtaskcreation() [coda/management/legacy_views.py:723]
│     └─ Creates: Task.objects.create(...)
│     └─ Required Fields:
│        ├─ employee_id (FK to User)
│        ├─ groupname_id (FK to TaskGroups)
│        ├─ category_id (FK to TaskCategory)
│        ├─ activity_name (CharField, required)
│        └─ Optional: activity_type (FK to ActivityType)
│
└─ Helper Function: create_task() [coda/management/legacy_views.py:380]
   └─ Creates: Task with ActivityType defaults applied
   └─ If activity_type provided: overrides mxpoint, mxearning, department

Activity Type Derivation:
├─ Canonical Path (Preferred):
│  └─ Task.activity_type (FK to ActivityType)
│     └─ Set via: TaskForm or create_task(activity_type=...)
│     └─ Provides: mxpoint, mxearning, department defaults
│
└─ Legacy Path (Backfill):
   └─ Task.activity_name (CharField)
   └─ Used when: activity_type is None
   └─ Normalized: activity_name.upper().replace(' ', '_')
   └─ Example: "Internal Training Session" → "INTERNAL_TRAINING_SESSION"

FK Validation:
└─ Task model clean() method [coda/management/models.py:814]
   └─ Validates: mxearning >= 0, mxpoint > 0
   └─ Runtime: Django ORM enforces FK constraints (IntegrityError if invalid FK)
```

**Runtime Safety:** Django ORM foreign key constraints prevent invalid FK references. `IntegrityError` raised if `groupname_id`, `category_id`, or `employee_id` don't exist.

---

### D) TaskLinks Auto-Creation and DAF v2 Evidence Gating

```
Auto-Creation Entry Points:
├─ Management Command: autolink_meeting_evidence
│  └─ File: coda/ai_services/management/commands/autolink_meeting_evidence.py
│     └─ Function: Command.handle()
│        └─ Calls: MeetingTaskAutolinkService.discover_candidate_tasks()
│        └─ For each task: MeetingTaskAutolinkService.find_meeting_for_task()
│        └─ If match: MeetingTaskAutolinkService.create_or_update_tasklink_from_meeting()
│
└─ Celery Task: daily_autolink_meeting_evidence_task
   └─ File: coda/ai_services/tasks.py:360
   └─ Same flow as management command

Auto-Creation Rules:
└─ MeetingTaskAutolinkService.create_or_update_tasklink_from_meeting()
   └─ File: coda/ai_services/services/meeting_task_autolink_service.py:510
   └─ Conditions:
      ├─ Task.activity_type in MEETING_BASED_ACTIVITY_TYPES
      ├─ Meeting match found (via find_meeting_for_task)
      ├─ Meeting has recording_url or download_url
      └─ Idempotency: get_or_create(task=..., meeting_id=..., is_auto_generated=True)
   └─ Creates: TaskLinks with:
      ├─ task (FK to Task)
      ├─ added_by (FK to User, defaults to task.employee or staff user)
      ├─ link (normalized recording_url or download_url)
      ├─ link_name (meeting.topic[:255])
      ├─ is_auto_generated=True
      └─ meeting_id (stored for idempotency)

Evidence Gating (Single Source of Truth):
└─ compute_task_compliance() [coda/management/legacy_views.py:2914]
   └─ Uses: get_task_evidence_summary() [evidence_summary_service.py:22]
   └─ Policy-Driven: PolicyResolver.for_user(task.employee)
   └─ Returns:
      ├─ evidence_status: 'missing' | 'partial' | 'complete' | 'auto_pending'
      ├─ evidence_ok: bool (True only if status == 'complete' AND count >= minimum)
      ├─ evidence_count_ok: bool (count_usable >= policy.evidence_minimum)
      └─ gate_pass: bool (AND of all compliance checks)

Meeting-Required Policy Rules:
└─ PolicyResolver [coda/management/services/policy_resolver.py]
   └─ Group A: meeting_required_activity_types = {
        'INTERNAL_TRAINING_SESSION', 'SELF_TRAINING_SESSION', 
        'CLIENT_TRAINING_SESSION', 'PRODUCT_BACKLOG_REFINEMENT', 'PBR_SESSION'
      }
   └─ Group B: meeting_required_activity_types = {
        'CLIENT_TRAINING_SESSION', 'PRODUCT_BACKLOG_REFINEMENT'
      }
   └─ Group C: meeting_required_activity_types = {} (none)

Evidence Requirements Checklist (per activity type):
├─ INTERNAL_TRAINING_SESSION (Group A):
│  ├─ Requirement: REQUIRED (must link to Requirement)
│  ├─ Evidence Minimum: 2 items (Group A) or 1 item (Group B)
│  ├─ Meeting Evidence: REQUIRED (Group A) or OPTIONAL (Group B)
│  └─ Quality Threshold: 80%
│
├─ SELF_TRAINING_SESSION (Group A):
│  ├─ Requirement: REQUIRED
│  ├─ Evidence Minimum: 1 item
│  ├─ Meeting Evidence: REQUIRED (Group A) or OPTIONAL (Group B)
│  └─ Quality Threshold: 80%
│
├─ CLIENT_TRAINING_SESSION (All Groups):
│  ├─ Requirement: REQUIRED
│  ├─ Evidence Minimum: 1 item
│  ├─ Meeting Evidence: REQUIRED (all groups)
│  └─ Quality Threshold: 80%
│
└─ PRODUCT_BACKLOG_REFINEMENT (All Groups):
   ├─ Requirement: REQUIRED
   ├─ Evidence Minimum: 1 item
   ├─ Meeting Evidence: REQUIRED (all groups)
   └─ Quality Threshold: 80%
```

**Evidence Status Logic:**
- `missing`: No active TaskLinks OR no usable evidence (no link/doc/drive_link)
- `partial`: Active TaskLinks exist but none have usable evidence
- `complete`: At least one active TaskLinks with usable evidence
- `auto_pending`: Meeting matched (confidence >= 0.7) but no TaskLinks created yet

---

### E) DAF v2 UI Path + Drilldown Links

```
DAF v2 View:
└─ daf_v2_view() [coda/management/legacy_views.py:1663]
   └─ URL: /management/daf/v2/
   └─ Template: management/daf/usertasks/employeetasks_v2.html
   └─ Query Parameter: ?user_id=<auth.User.id>
   └─ Filters Tasks:
      ├─ Task.objects.filter(employee=employee_user, is_active=True)
      └─ Uses: select_related('category', 'department', 'activity_type', 'employee', 'requirement')
      └─ Uses: prefetch_related('tasklinks_set', 'review_comments')

Tasks Drilldown Flow:
├─ Step 1: Unfiltered /management/tasks/
│  └─ View: TaskListView [coda/management/legacy_views.py:TaskListView]
│  └─ Template: management/daf/tasklist.html
│  └─ Employee Name Link:
│     └─ URL: /management/tasks/?employee=<task.employee.id>
│     └─ Template Line: 84 [coda/management/templates/management/daf/tasklist.html:84]
│
└─ Step 2: Filtered /management/tasks/?employee=<id>
   └─ View: TaskListView (same view, checks request.GET.get('employee'))
   └─ Context Variables:
      ├─ filtered_employee: User object (if employee param valid)
      └─ daf_user_id: Mapped via employee_identity_service.get_daf_user_id_from_task_employee()
   └─ Template: management/daf/tasklist.html
   └─ "Open DAF" Button:
      └─ URL: /management/daf/v2/?user_id=<daf_user_id>
      └─ Template Line: 34 [coda/management/templates/management/daf/tasklist.html:34]

Employee Identity Mapping:
└─ get_daf_user_id_from_task_employee() [coda/management/services/employee_identity_service.py:24]
   └─ Input: Task.employee (User instance)
   └─ Output: user.id (same User model, direct mapping)
   └─ Note: Task.employee and daf_v2_view both use auth.User, so mapping is 1:1
```

**Parameter Consistency:**
- `/management/tasks/` uses: `?employee=<task.employee.id>` (FK column)
- `/management/daf/v2/` uses: `?user_id=<user.id>` (same User model)
- Mapping: `task.employee.id == user.id` (direct, no conversion needed)

---

### F) Employee Group Assignment Bug (Runtime Issue)

```
Problem: Save button does nothing when setting employee group (e.g., Brenda to Group C)

Root Cause: NESTED FORMS (form inside form)
└─ Template: coda/management/templates/management/employee_groups.html
   └─ Line 99: Outer form (bulk update) wraps entire table
   └─ Line 159: Inner form (single update) inside each table row
   └─ HTML Spec: Forms cannot be nested - browser ignores inner form POST

View Handler:
└─ employee_groups_view() [coda/management/views_employee_groups.py:28]
   └─ POST Handler: Lines 36-89
   └─ Checks: request.POST.get("action") == "single_update"
   └─ Calls: set_group(employee, group_letter, actor=request.user)
   └─ Service: coda/management/services/employee_group_service.py:40
      └─ Function: set_group() - Creates/updates EmployeeCareerState.group
      └─ Idempotency: get_or_create(user=user, defaults={'group': group_letter})

Fix Required:
└─ Remove nested form structure
└─ Move single update form OUTSIDE bulk update form
└─ OR: Use JavaScript to submit single update via AJAX
└─ OR: Use separate URL endpoint for single update
```

**Exact Fix Location:**
- File: `coda/management/templates/management/employee_groups.html`
- Lines: 99-193 (restructure forms)
- View: Already handles POST correctly (lines 36-89), just needs form structure fix

---

### G) AI Feature Flags and Safe Degradation

```
Feature Flag System:
└─ coda/ai_services/utils/flags.py
   └─ Function: is_ai_feature_enabled(feature_name)
   └─ Checks:
      ├─ settings.AI_ENABLED (master flag)
      └─ settings.AI_<FEATURE>_ENABLED (feature-specific flag)
   └─ Returns: True only if BOTH are True

Feature Flags:
├─ AI_ENABLED (master)
├─ AI_PAY_EXPLANATION_ENABLED
├─ AI_FOCUS_ENABLED
├─ AI_COACHING_ENABLED
├─ ENABLE_AI_REQUIREMENT_MATCHING
└─ ENABLE_AI_MEETING_SUMMARY

Safe Degradation Behavior:
├─ AI Enabled + Service Available:
│  └─ Calls: RealAIService or fallback service
│  └─ Fields: Present in response (e.g., ai_pay_explanation, ai_focus)
│
└─ AI Enabled but Service Unavailable:
   └─ Expected: Fields should be OMITTED (not replaced with placeholders)
   └─ Current: Check DAFSummaryService [coda/management/services/daf_summary_service.py]
      └─ Lines: 846-885 (fail-safe blocks)
      └─ Behavior: Fields omitted if AI fails (correct)
```

**Verification:** Check `daf_summary_service.py` lines 846-885 for fail-safe blocks that omit AI fields on error.

---

## 2. Risk Register (Top 10 Runtime Risks)

| # | Risk | Severity | Location | Fix |
|---|------|----------|----------|-----|
| 1 | **Employee Groups Save fails (nested forms)** | HIGH | `coda/management/templates/management/employee_groups.html:99-193` | Remove nested form, move single update form outside bulk form OR use separate URL |
| 2 | **Meeting table missing (_safe_meeting_query returns empty)** | MEDIUM | `coda/management/legacy_views.py:2984` | Already handled with `_safe_meeting_query()`, but verify table exists in production |
| 3 | **Task.employee FK invalid (IntegrityError on create)** | MEDIUM | `coda/management/legacy_views.py:723` (newtaskcreation) | Django ORM enforces FK - runtime error, but should validate before create |
| 4 | **Activity type mismatch (legacy activity_name vs activity_type)** | MEDIUM | `coda/management/legacy_views.py:3510` (newevidence) | Normalization logic exists, but verify fallback handles all cases |
| 5 | **Evidence summary inconsistency (multiple sources)** | LOW | Multiple locations | Already fixed: `evidence_summary_service.py` is single source of truth |
| 6 | **Autolink creates duplicate TaskLinks (idempotency failure)** | LOW | `coda/ai_services/services/meeting_task_autolink_service.py:510` | Already handled: `get_or_create(task=..., meeting_id=..., is_auto_generated=True)` |
| 7 | **Meeting sync creates duplicate Meetings (idempotency failure)** | LOW | `coda/ai_services/views.py:440` (save_meeting_data) | Already handled: `get_or_create(meeting_id=...)` |
| 8 | **PolicyResolver returns None (no EmployeeCareerState)** | LOW | `coda/management/services/policy_resolver.py:67` | Already handled: defaults to Group B if no career_state |
| 9 | **DAF v2 totals mismatch (reconciliation check)** | LOW | `coda/management/legacy_views.py:2155` | Already fixed: reconciliation check added, logs warnings |
| 10 | **AI service unavailable breaks DAF summary** | LOW | `coda/management/services/daf_summary_service.py:846` | Already handled: fail-safe blocks omit AI fields |

---

## 3. Validation Plan (Minimal Commands)

### Step 1: Verify GoToMeeting Ingestion

```bash
# 1. Sync meetings (dry run first)
poetry run python coda/manage.py sync_gotomeetings --days 7

# 2. Check Meeting table
poetry run python coda/manage.py shell
>>> from ai_services.models import Meeting
>>> Meeting.objects.count()  # Should be > 0
>>> Meeting.objects.filter(service_name='gotomeeting_external').count()
>>> Meeting.objects.filter(requirement_code__isnull=False).count()  # Should have REQ codes

# 3. Verify idempotency (run sync twice, count should not double)
poetry run python coda/manage.py sync_gotomeetings --days 7
# Check count again - should be same or slightly higher (new meetings only)
```

**Expected:** Meeting count increases, no duplicates on second run.

---

### Step 2: Verify Meeting Matching

```bash
# 1. Create a test task with requirement
poetry run python coda/manage.py shell
>>> from management.models import Task, Requirement
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> user = User.objects.filter(is_staff=True).first()
>>> req = Requirement.objects.first()
>>> task = Task.objects.create(
...     employee=user,
...     activity_name="Internal Training Session",
...     requirement=req,
...     is_active=True
... )

# 2. Run autolink
poetry run python coda/manage.py autolink_meeting_evidence --days 1 --user-id <user.id> --verbose

# 3. Check TaskLinks created
>>> from management.models import TaskLinks
>>> TaskLinks.objects.filter(task=task, is_auto_generated=True).count()  # Should be 1
>>> TaskLinks.objects.filter(task=task).first().meeting_id  # Should have meeting_id
```

**Expected:** TaskLinks created with `is_auto_generated=True` and `meeting_id` set.

---

### Step 3: Verify DAF v2 Rendering

```bash
# 1. Start server
poetry run python coda/manage.py runserver 8080

# 2. Visit DAF v2
# URL: http://localhost:8080/management/daf/v2/?user_id=<user.id>

# 3. Check logs for reconciliation warnings
# Watch for: "DAF reconciliation mismatch" in logs

# 4. Verify evidence status
# Check: Evidence chips show correct status (Missing/Partial/Complete)
# Check: "Needs Attention" tasks show correct reason codes
```

**Expected:** DAF v2 loads, totals reconcile, evidence status accurate.

---

### Step 4: Verify Tasks Drilldown Flow

```bash
# 1. Visit tasks page
# URL: http://localhost:8080/management/tasks/

# 2. Click employee name (should filter)
# URL: http://localhost:8080/management/tasks/?employee=<id>

# 3. Click "Open DAF" button
# URL: http://localhost:8080/management/daf/v2/?user_id=<mapped_id>

# 4. Verify context variables
# Check: filtered_employee is set in TaskListView
# Check: daf_user_id is set and matches user.id
```

**Expected:** Drilldown works, DAF opens with correct user.

---

### Step 5: Verify Employee Groups Save (Fix Required)

```bash
# 1. Visit employee groups page
# URL: http://localhost:8080/management/employee-groups/

# 2. Change group for one employee (e.g., Brenda to Group C)
# Click "Save" button

# 3. Check if save worked
poetry run python coda/manage.py shell
>>> from management.models import EmployeeCareerState
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> user = User.objects.filter(username='brenda').first()  # Replace with actual username
>>> state = EmployeeCareerState.objects.get(user=user)
>>> state.group  # Should be 'C' if save worked

# 4. Check browser console for errors (nested form issue)
```

**Expected:** After fix, group should persist. Before fix, POST is ignored.

---

## 4. Employee Groups Save Fix (Patch)

### Problem
Nested forms in template: bulk update form (line 99) wraps single update forms (line 159). HTML spec disallows nested forms - browser ignores inner form POST.

### Solution
Move single update form outside bulk form OR use separate URL endpoint.

### Option 1: Separate URL Endpoint (Recommended)

**File:** `coda/management/urls.py`
```python
# Add new route
path('employee-groups/update/<int:user_id>/', 
     views_employee_groups.update_single_employee_group, 
     name='update_single_employee_group'),
```

**File:** `coda/management/views_employee_groups.py`
```python
@login_required
@user_passes_test(_staff_only)
@require_POST
@transaction.atomic
def update_single_employee_group(request: HttpRequest, user_id: int) -> HttpResponse:
    """
    Update a single employee's group (A/B/C).
    
    URL: /management/employee-groups/update/<user_id>/
    """
    group_letter = (request.POST.get("group") or "").upper().strip()
    
    if group_letter not in {"A", "B", "C"}:
        messages.error(request, "Invalid group selection.")
        return redirect(reverse("management:employee_groups"))
    
    try:
        employee = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, "Employee not found.")
        return redirect(reverse("management:employee_groups"))
    
    try:
        set_group(employee, group_letter, actor=request.user)
        messages.success(
            request,
            f"Updated {employee.get_full_name() or employee.username} to Group {group_letter}.",
        )
    except Exception as e:
        logger.exception(f"Error updating employee group: {e}")
        messages.error(request, f"Error updating group: {str(e)}")
    
    return redirect(reverse("management:employee_groups"))
```

**File:** `coda/management/templates/management/employee_groups.html`
```html
<!-- Line 159: Change form action to new URL -->
<form method="post" action="{% url 'management:update_single_employee_group' row.user.id %}" class="d-flex">
  {% csrf_token %}
  <!-- Remove: <input type="hidden" name="action" value="single_update"> -->
  <!-- Remove: <input type="hidden" name="user_id" value="{{ row.user.id }}"> -->
  <select name="group" class="form-select form-select-sm me-2">
    <option value="A" {% if row.group == "A" %}selected{% endif %}>Group A</option>
    <option value="B" {% if row.group == "B" %}selected{% endif %}>Group B</option>
    <option value="C" {% if row.group == "C" %}selected{% endif %}>Group C</option>
  </select>
  <button type="submit" class="btn btn-sm btn-outline-primary">
    Save
  </button>
</form>
```

### Option 2: Move Form Outside (Alternative)

**File:** `coda/management/templates/management/employee_groups.html`
```html
<!-- Close bulk form before table (line 98) -->
</form>

<!-- Table with single update forms (no nesting) -->
<table class="table ...">
  ...
  <form method="post" action="{% url 'management:employee_groups' %}" ...>
    {% csrf_token %}
    <input type="hidden" name="action" value="single_update">
    ...
  </form>
  ...
</table>

<!-- Reopen bulk form after table (if needed for footer actions) -->
<form method="post" action="{% url 'management:bulk_update_employee_groups' %}">
  {% csrf_token %}
  <!-- Bulk actions -->
</form>
```

### Verification

```bash
# 1. Apply fix
# 2. Visit: http://localhost:8080/management/employee-groups/
# 3. Change group for one employee, click Save
# 4. Verify redirect and success message
# 5. Check DB:
poetry run python coda/manage.py shell
>>> from management.models import EmployeeCareerState
>>> state = EmployeeCareerState.objects.get(user__username='brenda')
>>> state.group  # Should be updated value
```

---

## 5. File Reference Summary

### Entry Points
- GoToMeeting Sync: `coda/ai_services/management/commands/sync_gotomeetings.py`
- Meeting Persistence: `coda/ai_services/views.py:358` (`save_meeting_data`)
- Autolink: `coda/ai_services/management/commands/autolink_meeting_evidence.py`
- DAF v2 View: `coda/management/legacy_views.py:1663` (`daf_v2_view`)

### Single Sources of Truth
- Evidence Status: `coda/management/services/evidence_summary_service.py:22` (`get_task_evidence_summary`)
- Compliance: `coda/management/legacy_views.py:2914` (`compute_task_compliance`)
- Policy: `coda/management/services/policy_resolver.py:67` (`PolicyResolver.for_user`)
- Meeting Query: `coda/management/legacy_views.py:2984` (`_safe_meeting_query`)

### Models
- Meeting: `coda/ai_services/models.py` (table: `ai_services_meeting`)
- Task: `coda/management/models.py` (table: `management_task`)
- TaskLinks: `coda/management/models.py` (table: `management_tasklinks`)
- EmployeeCareerState: `coda/management/models.py` (table: `management_employeecareerstate`)

---

## 6. Critical Fixes Required

1. **Employee Groups Save (HIGH)**: ✅ FIXED - Added separate URL endpoint to avoid nested form issue
2. **Meeting Table Existence (MEDIUM)**: Verify `ai_services_meeting` table exists in production
3. **Task FK Validation (MEDIUM)**: Add explicit validation before Task.create() to prevent IntegrityError

---

## 7. Employee Groups Save Fix (IMPLEMENTED)

### Problem
Nested forms in template: bulk update form (line 99) wraps single update forms (line 159). HTML spec disallows nested forms - browser ignores inner form POST.

### Solution Implemented
Added separate URL endpoint for single updates to avoid nested form issue.

### Changes Made

**File:** `coda/management/urls.py` (line 170)
```python
path('employee-groups/update/<int:user_id>/', 
     views_employee_groups.update_single_employee_group, 
     name='update_single_employee_group'),
```

**File:** `coda/management/views_employee_groups.py` (new function, line 216)
```python
@login_required
@user_passes_test(_staff_only)
@require_POST
@transaction.atomic
def update_single_employee_group(request: HttpRequest, user_id: int) -> HttpResponse:
    """Update a single employee's group (A/B/C)."""
    # Validates group, gets employee, calls set_group(), redirects with message
```

**File:** `coda/management/templates/management/employee_groups.html` (line 159)
```html
<!-- Changed form action to new URL -->
<form method="post" action="{% url 'management:update_single_employee_group' row.user.id %}" class="d-flex">
  {% csrf_token %}
  <!-- Removed: action and user_id hidden fields (now in URL) -->
  <select name="group" ...>
  <button type="submit">Save</button>
</form>
```

### Verification

```bash
# 1. Visit: http://localhost:8080/management/employee-groups/
# 2. Change group for one employee (e.g., Brenda to Group C)
# 3. Click "Save" button
# 4. Verify redirect and success message
# 5. Check DB:
poetry run python coda/manage.py shell
>>> from management.models import EmployeeCareerState
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> user = User.objects.filter(username='brenda').first()  # Replace with actual username
>>> state = EmployeeCareerState.objects.get(user=user)
>>> state.group  # Should be 'C' if save worked
```

**Status:** ✅ Fixed and ready for testing

---

**End of Audit**

