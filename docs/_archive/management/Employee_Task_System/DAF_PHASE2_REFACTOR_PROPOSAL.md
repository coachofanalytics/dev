# DAF Module Refactor Phase 2 Proposal

**Date:** January 1, 2026  
**Branch:** 25.12_CODA_DEV_CM  
**Status:** Proposal Only (NO IMPLEMENTATION)

---

## Executive Summary

This document provides a validated inventory of the DAF module and proposes a Phase 2 refactoring plan to:
1. Tighten module boundaries (DAF as orchestration layer only)
2. Reduce coupling in `legacy_views.py`
3. Introduce clean interfaces between DAF and foreign domains
4. Define a safe, incremental migration path

---

## Part 1: Validated Inventory Report

### 1A) Views + URLs — Verified

| URL Pattern | View Function | Location | Template(s) | Responsibilities | Foreign Dependencies |
|------------|--------------|----------|-------------|------------------|---------------------|
| `/management/payroll/` | `payslip()` | `legacy_views.py:1099` | `payslip.html`, `payslip_modern.html`, `usertasks.html`, `tasklist.html`, `taskhistory.html` | Multi-purpose view with 6 `pay_type` branches | Finance (paytime, paymentconfigurations, deductions, loan_computation), Tasks (Task, TaskHistory), DAF services |
| `/management/daf/v2/` | `daf_v2_view()` | `legacy_views.py:1678` | `usertasks/employeetasks_v2.html` | Modern DAF v2 UI (employee view) | Tasks (Task, TaskLinks), Evidence (TaskLinks), Meetings (Meeting, MeetingEvidenceMatcher), Compliance (Requirement), DAF services |
| `/management/daf/review/` | `daf_review_view()` | `legacy_views.py:2553` | `review.html` | Manager review page (staff only) | Tasks (Task), Evidence (TaskLinks), AI Services (TaskAIReviewSuggestion, AIOperationsRun), DAF services |
| `/management/daf/review/comment/<int:task_id>/` | `daf_review_comment_view()` | `legacy_views.py:2798` | (redirect) | Add review comment to task | Tasks (Task), DAF models (TaskReviewComment) |
| `/management/daf/review/ai/<int:task_id>/` | `daf_review_ai_generate()` | `legacy_views.py:2831` | (redirect) | Generate AI review suggestion | Tasks (Task), DAF services (TaskAIReviewService) |
| `/management/daf/review/ai-ops-run/` | `daf_review_ai_ops_run()` | `legacy_views.py:2865` | (redirect) | Trigger AI daily operations | AI Services (AIOperationsService) |
| `/management/api/daf/summary/` | `daf_summary_api()` | `views/api_views.py:344` | (JSON) | DAF summary JSON API | DAF services (DAFSummaryService) |
| `/management/debug/daf-runtime/` | `daf_runtime_debug()` | `views_debug.py:39` | `debug/daf_runtime_debug.html` | Debug endpoint for DAF runtime | DAF services |

#### `payslip()` View Branches (Verified)

The `payslip()` view handles 6 different `pay_type` values:

1. **`pay_type='usertasks'`** (Line 1130-1467)
   - Uses `get_current_daf_summary()` for current active tasks
   - Template: `usertasks.html`
   - Returns current DAF view (My DAF)

2. **`pay_type in ['payslip', 'task_payslip']`** (Line 1474-1663)
   - Uses `PayCalculationService` or `DAFSummaryService` for historical data
   - Period: `get_latest_daf_period_for_employee()`
   - Templates: `payslip_modern.html` (primary), `payslip.html` (fallback)
   - Returns historical payslip

3. **`pay_type='usertaskhistory'`** (Line 1665-1666)
   - Template: `usertasks.html`
   - Returns user task history view

4. **`pay_type='tasks'`** (Line 1668-1670)
   - Template: `tasklist.html`
   - Returns task list view

5. **`pay_type='taskhistory'`** (Line 1668-1672)
   - Template: `taskhistory.html`
   - Returns task history view

6. **Default** (Line 1673-1675)
   - Redirects to `main:layout`

### 1B) DAF-Owned Models — Verified

| Model | Location | Primary Usage Points | Status |
|-------|----------|---------------------|--------|
| `TaskReviewComment` | `models.py:1577` | `daf_review_view()`, `daf_review_comment_view()`, `daf_v2_view()` | ✅ Verified |
| `TaskAIReviewSuggestion` | `models.py:1722` | `daf_review_view()`, `daf_review_ai_generate()`, `daf_v2_view()`, `task_ai_review_service.py` | ✅ Verified |
| `RequirementMatchCheck` | `models.py:1632` | `daf_v2_view()`, `requirement_match_service.py`, `task_ai_review_service.py | ✅ Verified |

**No additional DAF-only models found.**

### 1C) Services Inventory — Verified

| Service | Location | Public API | View Callers | Foreign Dependencies |
|---------|----------|------------|--------------|---------------------|
| `DAFSummaryService` | `services/daf_summary_service.py` | `get_summary(employee, target_month, target_year)` | `payslip()`, `daf_summary_api()` | TaskHistory, EmployeeCareerState, ComplianceCalculator, Finance services (via interface) |
| `get_current_daf_summary()` | `services/daf_current_summary_service.py` | `get_current_daf_summary(employee)` | `payslip()`, `daf_v2_view()`, `PayrollSummaryService` | Task, TaskHistory |
| `get_latest_daf_period_for_employee()` | `services/daf_period_service.py` | `get_latest_daf_period_for_employee(employee, default_today=None)` | `payslip()` | TaskHistory |
| `PayrollSummaryService` | `services/payroll_summary_service.py` | `get_user_pay_summary(employee, period_month, period_year)` | `payslip()`, `daf_v2_view()` | Task, `get_current_daf_summary()`, ComplianceCalculator |
| `ChecklistEvaluationService` | `services/checklist_evaluation_service.py` | `get_task_quality_score(task, task_links)` | `daf_v2_view()`, `daf_review_view()`, `_calculate_approval_readiness()`, `compute_task_compliance()` | Task, TaskLinks, ActivityDefinition, checklist config |
| `get_task_evidence_summary()` | `services/evidence_summary_service.py` | `get_task_evidence_summary(task, task_links, meeting_match_info)` | `daf_v2_view()`, `compute_task_compliance()` | Task, TaskLinks |
| `PolicyResolver` | `services/policy_resolver.py` | `PolicyResolver.for_user(user)` | `compute_task_compliance()` | User (for group resolution) |
| `TaskQualityGateService` | `services/task_quality_gate_service.py` | `get_task_gate_status(task, task_links, user)` | `daf_v2_view()` | ChecklistEvaluationService, EvidenceSummaryService, PolicyResolver |
| `TaskAIReviewService` | `services/task_ai_review_service.py` | `generate_review_suggestion(task, force=False)` | `daf_review_ai_generate()` | Task, TaskLinks, RequirementMatchCheck, AI service interface |

**Dependency Matrix:**

```
DAF Views
  ├─> DAFSummaryService
  │     └─> TaskHistory, EmployeeCareerState, ComplianceCalculator, Finance services
  ├─> get_current_daf_summary()
  │     └─> Task, TaskHistory
  ├─> PayrollSummaryService
  │     ├─> Task
  │     └─> get_current_daf_summary() ──┐
  │                                      │
  ├─> ChecklistEvaluationService         │
  │     └─> Task, TaskLinks, ActivityDefinition
  ├─> get_task_evidence_summary()
  │     └─> Task, TaskLinks
  ├─> PolicyResolver
  │     └─> User
  └─> TaskQualityGateService
        ├─> ChecklistEvaluationService
        ├─> EvidenceSummaryService
        └─> PolicyResolver
```

### 1D) Template Ownership — Verified

| Template | View(s) | Ownership | Status |
|----------|---------|-----------|--------|
| `payslip.html` | `payslip()` (fallback) | DAF | ✅ Keep |
| `payslip_modern.html` | `payslip()` (primary) | DAF | ✅ Keep |
| `usertasks.html` | `payslip()` (`pay_type='usertasks'`, `'usertaskhistory'`) | DAF | ✅ Keep |
| `usertasks/employeetasks_v2.html` | `daf_v2_view()` | DAF | ✅ Keep |
| `review.html` | `daf_review_view()` | DAF | ✅ Keep |
| `tasklist.html` | `payslip()` (`pay_type='tasks'`) | DAF | ✅ Keep |
| `taskhistory.html` | `payslip()` (`pay_type='taskhistory'`) | DAF | ✅ Keep |
| `evidence_form.html` | `newevidence()` (Evidence module) | **Evidence** | ⚠️ Migrate to Evidence module |
| `evidence_form_v2.html` | `newevidence()` (Evidence module) | **Evidence** | ⚠️ Migrate to Evidence module |
| `evidence_form_old.html` | (unused?) | **Evidence** | ⚠️ Archive |
| `legacy_evidence_form.html` | (unused?) | **Evidence** | ⚠️ Archive |
| `task_detail.html` | `TaskDetailView` (Tasks module) | **Tasks** | ⚠️ Migrate to Tasks module |
| `meeting_link_review.html` | `meeting_link_review_dashboard()` (Meetings module) | **Meetings** | ⚠️ Migrate to Meetings module |
| `employee_tasks.html` | (commented out) | DAF | ⚠️ Archive |
| `userevidence.html` | `userevidence()` (Evidence module) | **Evidence** | ⚠️ Migrate to Evidence module |
| `reset_tasks_select.html` | `reset_tasks_select()` (Tasks module) | **Tasks** | ⚠️ Migrate to Tasks module |
| `usertasks/employeetasks.html` | (legacy, may be referenced) | DAF | ⚠️ Archive if unused |
| `usertasks/contractualtasks.html` | (unknown) | DAF | ⚠️ Verify usage |

**Template Action Plan:**
- **Keep (7):** Core DAF templates
- **Migrate (5):** Evidence and Tasks module templates
- **Archive (4):** Legacy/unused templates

---

## Part 2: Boundary Leaks Identified

### 2.1 Critical Boundary Violations (Ranked by Severity)

#### **Leak #1: Meeting Matching Logic in DAF** (HIGH SEVERITY)
- **File:** `legacy_views.py:3565`
- **Function:** `_get_meeting_match_info(task, link=None)`
- **What it touches:** AI Services/Meetings domain
- **Why it's a leak:**
  - Directly imports `MeetingEvidenceMatcher`, `Meeting`, `meeting_normalizer`, `meeting_room_config` from `ai_services`
  - Implements meeting matching logic (URL matching, topic matching, room validation)
  - This is core Meetings domain logic, not DAF orchestration
- **How to fix:**
  - Move to `ai_services.services.meeting_evidence_service` or create `meetings_gateway.py`
  - DAF should call: `meetings_gateway.get_meeting_match_for_task(task, link)`
  - Gateway returns dict with `has_match`, `meeting`, `confidence`, etc.

#### **Leak #2: Direct Meeting Model Queries in Compliance** (HIGH SEVERITY)
- **File:** `legacy_views.py:3284-3297`
- **Function:** `compute_task_compliance()` (inside function)
- **What it touches:** AI Services/Meetings domain
- **Why it's a leak:**
  - Directly queries `Meeting.objects` to check for manual meeting URL matches
  - Implements meeting evidence validation logic
- **How to fix:**
  - Move meeting evidence check to `meetings_gateway.has_meeting_evidence(task, task_links)`
  - `compute_task_compliance()` should call gateway, not query Meeting model directly

#### **Leak #3: Payroll Computation Logic in DAF Views** (HIGH SEVERITY)
- **File:** `legacy_views.py:1099-1675`
- **Function:** `payslip()`
- **What it touches:** Finance/Payroll domain
- **Why it's a leak:**
  - Directly calls `paytime()`, `paymentconfigurations()`, `deductions()`, `loan_computation()` from `management.utils`
  - These functions contain payroll computation logic (deductions, loans, bonuses)
  - DAF should only orchestrate, not compute payroll
- **How to fix:**
  - Create `finance_gateway.py` with `get_payroll_summary(employee, period_month, period_year)`
  - Gateway calls Finance services (already partially done via `PayrollSummaryService`)
  - `payslip()` should only call gateway, not `management.utils` functions directly

#### **Leak #4: Direct Task/Evidence Model Queries** (MEDIUM SEVERITY)
- **File:** `legacy_views.py` (multiple locations)
- **Functions:** `payslip()`, `daf_v2_view()`, `daf_review_view()`
- **What it touches:** Tasks and Evidence domains
- **Why it's a leak:**
  - Views directly query `Task.objects`, `TaskHistory.objects`, `TaskLinks.objects`
  - DAF should use service interfaces, not query models directly
- **How to fix:**
  - Create `tasks_gateway.py` with:
    - `get_active_tasks_for_employee(employee)`
    - `get_task_history_for_period(employee, month, year)`
  - Create `evidence_gateway.py` with:
    - `get_evidence_for_task(task)`
    - `get_evidence_summary(task)` (already exists as service, but gateway wraps it)

#### **Leak #5: Direct PayslipConfig Import** (MEDIUM SEVERITY)
- **File:** `legacy_views.py:1005-1053`
- **Function:** `get_user_data(employee)`
- **What it touches:** Finance domain
- **Why it's a leak:**
  - Directly imports `PayslipConfig` from `finance.models`
  - Calls `paymentconfigurations()` which also imports `PayslipConfig`
- **How to fix:**
  - `finance_gateway.get_payslip_config(employee)` should return dict, not model
  - Gateway handles Finance model access internally

#### **Leak #6: Evidence Form Views in DAF Module** (MEDIUM SEVERITY)
- **File:** `legacy_views.py:3770-4546`
- **Functions:** `newevidence()`, `userevidence()`, `evidence_update_view()`
- **What it touches:** Evidence domain
- **Why it's a leak:**
  - Evidence creation/update views are in `legacy_views.py` (DAF module)
  - These should be in Evidence module
- **How to fix:**
  - Move to `coda/management/views/evidence_views.py` or separate Evidence app
  - Update URLs to point to Evidence module views

#### **Leak #7: Requirement Queries in DAF** (LOW SEVERITY)
- **File:** `legacy_views.py:3706-3763`
- **Function:** `get_eligible_requirements_for_user()`
- **What it touches:** Compliance/Requirements domain
- **Why it's a leak:**
  - Directly queries `Requirement.objects` with business logic (recency, assignment)
- **How to fix:**
  - Create `requirements_gateway.py` with `get_eligible_requirements_for_user(user, recency_days)`
  - Gateway handles Requirement model access

### 2.2 Boundary Leak Summary

| Severity | Count | Examples |
|----------|-------|----------|
| HIGH | 3 | Meeting matching, Meeting queries, Payroll computation |
| MEDIUM | 3 | Direct model queries, PayslipConfig import, Evidence views |
| LOW | 1 | Requirement queries |

**Total Boundary Violations: 7**

---

## Part 3: Phase 2 Target Architecture Proposal

### 3A) Proposed Package Layout

```
coda/management/
├── daf/                          # NEW: DAF module package
│   ├── __init__.py
│   ├── views/                     # DAF views only
│   │   ├── __init__.py
│   │   ├── daf_v2.py             # daf_v2_view()
│   │   ├── payslip.py            # payslip() (refactored)
│   │   ├── review.py             # daf_review_view(), daf_review_comment_view(), etc.
│   │   └── api.py                # daf_summary_api()
│   ├── services/                 # DAF-owned services
│   │   ├── __init__.py
│   │   ├── daf_summary.py        # DAFSummaryService (move from services/)
│   │   ├── daf_current_summary.py # get_current_daf_summary() (move from services/)
│   │   ├── daf_period.py         # get_latest_daf_period_for_employee() (move from services/)
│   │   ├── payroll_summary.py    # PayrollSummaryService (move from services/)
│   │   └── compliance_orchestrator.py # compute_task_compliance() (extracted from legacy_views.py)
│   ├── integrations/             # NEW: Gateway interfaces to foreign domains
│   │   ├── __init__.py
│   │   ├── tasks_gateway.py      # Tasks domain interface
│   │   ├── evidence_gateway.py    # Evidence domain interface
│   │   ├── meetings_gateway.py   # Meetings/AI Services domain interface
│   │   ├── finance_gateway.py     # Finance/Payroll domain interface
│   │   └── requirements_gateway.py # Compliance/Requirements domain interface
│   ├── models.py                 # DAF-owned models only
│   │   └── (TaskReviewComment, TaskAIReviewSuggestion, RequirementMatchCheck)
│   └── utils.py                  # DAF utilities only
│       └── (normalize_period, prefix_zero, get_previous_month_reference_date)
│
├── services/                     # Shared services (used by multiple modules)
│   ├── checklist_evaluation_service.py  # Keep (used by DAF and other modules)
│   ├── evidence_summary_service.py      # Keep (used by DAF and other modules)
│   ├── policy_resolver.py               # Keep (used by DAF and other modules)
│   ├── task_quality_gate_service.py     # Keep (used by DAF and other modules)
│   └── task_ai_review_service.py        # Keep (used by DAF and other modules)
│
└── views/                        # Other module views
    ├── evidence_views.py        # NEW: Evidence module views (moved from legacy_views.py)
    └── ...
```

**Key Principles:**
1. **DAF module is self-contained** (views, services, models, utils)
2. **Gateways are thin interfaces** (no business logic, just adapters)
3. **Shared services remain in `services/`** (used by multiple modules)
4. **Templates stay in `templates/management/daf/`** (but ownership clarified)

### 3B) Gateway Interface Definitions

#### **Tasks Gateway** (`daf/integrations/tasks_gateway.py`)

```python
"""
Tasks Gateway - Interface to Tasks domain.

DAF uses this gateway to fetch tasks and task histories.
Gateway handles all Task/TaskHistory model access.
"""

def get_active_tasks_for_employee(employee, include_related=True):
    """
    Get active tasks for an employee.
    
    Args:
        employee: User instance
        include_related: If True, use select_related/prefetch_related
    
    Returns:
        QuerySet of Task objects (or list if include_related=False)
    
    Allowed imports:
        - management.models.Task
        - management.models.TaskHistory (for context only)
    
    Must NOT import:
        - Evidence models (TaskLinks)
        - Meeting models
        - Finance models
    """

def get_task_history_for_period(employee, month, year):
    """
    Get TaskHistory records for a specific period.
    
    Args:
        employee: User instance
        month: int (1-12)
        year: int (YYYY)
    
    Returns:
        QuerySet of TaskHistory objects
    
    Allowed imports:
        - management.models.TaskHistory
    
    Must NOT import:
        - Task model (unless for FK resolution)
        - Evidence models
        - Finance models
    """

def get_task_by_id(task_id):
    """
    Get a single task by ID.
    
    Args:
        task_id: int
    
    Returns:
        Task instance or None
    
    Allowed imports:
        - management.models.Task
    """
```

#### **Evidence Gateway** (`daf/integrations/evidence_gateway.py`)

```python
"""
Evidence Gateway - Interface to Evidence domain.

DAF uses this gateway to fetch evidence summaries and status.
Gateway wraps EvidenceSummaryService and handles TaskLinks access.
"""

def get_evidence_for_task(task, active_only=True):
    """
    Get evidence links for a task.
    
    Args:
        task: Task instance
        active_only: If True, filter is_active=True
    
    Returns:
        QuerySet of TaskLinks objects (or list)
    
    Allowed imports:
        - management.models.TaskLinks
        - management.services.evidence_summary_service (for get_task_evidence_summary)
    
    Must NOT import:
        - Meeting models
        - Finance models
    """

def get_evidence_summary(task, task_links=None, meeting_match_info=None):
    """
    Get evidence summary for a task (wraps EvidenceSummaryService).
    
    Args:
        task: Task instance
        task_links: Optional pre-fetched list of TaskLinks
        meeting_match_info: Optional dict from meetings_gateway
    
    Returns:
        dict with: count_active, count_usable, items_qs, has_minimum, status, etc.
    
    Allowed imports:
        - management.services.evidence_summary_service.get_task_evidence_summary
    
    Must NOT import:
        - Meeting models (meeting_match_info is passed in)
        - Finance models
    """
```

#### **Meetings Gateway** (`daf/integrations/meetings_gateway.py`)

```python
"""
Meetings Gateway - Interface to Meetings/AI Services domain.

DAF uses this gateway to get meeting matches and meeting room info.
Gateway handles all Meeting model and MeetingEvidenceMatcher access.
"""

def get_meeting_match_for_task(task, link=None):
    """
    Get meeting match information for a task.
    
    Args:
        task: Task instance
        link: Optional evidence link URL to match
    
    Returns:
        dict with:
            - has_match: bool
            - meeting: Meeting instance or None
            - match_type: 'url' | 'topic' | None
            - confidence: float or None
            - requirement_code_match: bool or None
            - meeting_requirement_code: str or None
            - task_requirement_code: str or None
    
    Allowed imports:
        - ai_services.services.meeting_evidence_matcher.MeetingEvidenceMatcher
        - ai_services.models.Meeting
        - ai_services.utils.meeting_normalizer.normalize_url
        - ai_services.utils.meeting_room_config.get_meeting_room_for_activity
    
    Must NOT import:
        - Task models (task is passed in)
        - Evidence models (link is passed in)
        - Finance models
    """

def has_meeting_evidence(task, task_links):
    """
    Check if task has meeting evidence (autolink or manual match).
    
    Args:
        task: Task instance
        task_links: List of TaskLinks instances
    
    Returns:
        dict with:
            - has_meeting_evidence: bool
            - has_autolink: bool
            - has_manual_match: bool
            - meeting_ids: List[int] (distinct meeting IDs)
    
    Allowed imports:
        - ai_services.models.Meeting
        - ai_services.services.meeting_evidence_matcher.MeetingEvidenceMatcher
    
    Must NOT import:
        - Task models (task is passed in)
        - Evidence models (task_links is passed in)
        - Finance models
    """

def get_meeting_room_for_activity(activity_type_slug):
    """
    Get meeting room configuration for an activity type.
    
    Args:
        activity_type_slug: str (activity type slug)
    
    Returns:
        tuple: (meeting_room_id, meeting_join_url) or (None, None)
    
    Allowed imports:
        - ai_services.utils.meeting_room_config.get_meeting_room_for_activity
    
    Must NOT import:
        - Task models
        - Evidence models
        - Finance models
    """
```

#### **Finance Gateway** (`daf/integrations/finance_gateway.py`)

```python
"""
Finance Gateway - Interface to Finance/Payroll domain.

DAF uses this gateway to get payroll summaries and payslip config.
Gateway handles all Finance model and service access.
"""

def get_payroll_summary(employee, period_month=None, period_year=None):
    """
    Get payroll summary for an employee (wraps PayrollSummaryService).
    
    Args:
        employee: User instance
        period_month: Optional int (1-12), defaults to current month
        period_year: Optional int (YYYY), defaults to current year
    
    Returns:
        dict with:
            - target_amount: Decimal
            - earned_amount_provisional: Decimal
            - approved_earned_amount: Decimal
            - pending_approval_amount: Decimal
            - remaining_amount: Decimal
            - points_earned_provisional: Decimal
            - approved_earned_points: Decimal
            - target_points: Decimal
            - approval_percentage: float
            - pay_day_date: date
            - pay_day_formatted: str
            - time_remaining: dict
            - net_income: Decimal
    
    Allowed imports:
        - management.services.payroll_summary_service.PayrollSummaryService
        - management.services.finance_service_helper.get_finance_task_service (for PayCalculationService)
    
    Must NOT import:
        - finance.models.PayslipConfig (directly)
        - management.utils.paytime, payinitial, deductions, loan_computation (directly)
        - Task models (PayrollSummaryService handles this)
    """

def get_payslip_config(employee):
    """
    Get payslip configuration for an employee.
    
    Args:
        employee: User instance
    
    Returns:
        dict with payslip config fields (not model instance)
    
    Allowed imports:
        - management.services.finance_service_helper.get_finance_task_service
        - finance.models.PayslipConfig (only as fallback)
    
    Must NOT import:
        - Task models
        - Evidence models
        - Meeting models
    """

def get_historical_payslip_data(employee, month, year):
    """
    Get historical payslip data for a specific period.
    
    Args:
        employee: User instance
        month: int (1-12)
        year: int (YYYY)
    
    Returns:
        dict with payslip data structure (tasks, base_pay, bonuses, deductions, summary)
    
    Allowed imports:
        - management.services.finance_service_helper.get_pay_service
        - management.services.daf_summary_service.DAFSummaryService (fallback)
    
    Must NOT import:
        - TaskHistory models (DAFSummaryService handles this)
        - Finance models directly
    """
```

#### **Requirements Gateway** (`daf/integrations/requirements_gateway.py`)

```python
"""
Requirements Gateway - Interface to Compliance/Requirements domain.

DAF uses this gateway to check requirement status and get eligible requirements.
Gateway handles all Requirement model access.
"""

def get_eligible_requirements_for_user(user, recency_days=90, use_assigned_to_only=False):
    """
    Get eligible requirements for a user.
    
    Args:
        user: User instance
        recency_days: int (default: 90)
        use_assigned_to_only: bool (default: False)
    
    Returns:
        QuerySet of Requirement objects
    
    Allowed imports:
        - management.models.Requirement
    
    Must NOT import:
        - Task models
        - Evidence models
        - Finance models
    """

def check_requirement_status(task, requirement):
    """
    Check if task's requirement is valid (wraps RequirementMatchService if available).
    
    Args:
        task: Task instance
        requirement: Requirement instance
    
    Returns:
        dict with:
            - is_valid: bool
            - match_status: 'pass' | 'review' | 'fail' | None
            - confidence: float or None
            - reason: str or None
    
    Allowed imports:
        - management.models.RequirementMatchCheck (for latest check)
        - management.services.requirement_match_service.RequirementMatchService (optional)
    
    Must NOT import:
        - Task models (task is passed in)
        - Evidence models
        - Finance models
    """
```

---

## Part 4: View Refactor Plan

### 4.1 `payslip()` View Refactoring Strategy

**Current State:**
- Single function handling 6 `pay_type` branches (598 lines)
- Direct imports from `management.utils` (paytime, paymentconfigurations, deductions, loan_computation)
- Direct queries to Task, TaskHistory models
- Mixed responsibilities (payslip, DAF, task list, task history)

**Target State:**
- Router pattern: `payslip()` becomes a thin router
- Focused handlers: Each `pay_type` gets its own view function
- Gateway usage: All foreign domain access via gateways
- URL stability: `/management/payroll/` endpoint remains unchanged

**Proposed Structure:**

```python
# coda/management/daf/views/payslip.py

@login_required
def payslip(request, *args, **kwargs):
    """
    Router view for payroll/DAF endpoints.
    
    Maintains backward compatibility with existing URL patterns.
    Routes to focused handlers based on pay_type parameter.
    """
    pay_type = request.GET.get('pay_type', None)
    username = request.GET.get('username', None)
    
    # Route to focused handlers
    if pay_type == 'usertasks':
        return _handle_usertasks(request, username)
    elif pay_type in ['payslip', 'task_payslip']:
        return _handle_payslip(request, username, pay_type)
    elif pay_type == 'usertaskhistory':
        return _handle_usertaskhistory(request, username)
    elif pay_type == 'tasks':
        return _handle_tasklist(request, username)
    elif pay_type == 'taskhistory':
        return _handle_taskhistory(request, username)
    else:
        return redirect("main:layout")


def _handle_usertasks(request, username):
    """Handle My DAF view (current active tasks)."""
    from ..services.daf_current_summary_service import get_current_daf_summary
    from ..integrations.tasks_gateway import get_active_tasks_for_employee
    from ..integrations.finance_gateway import get_payroll_summary
    
    employee = _get_employee(request, username)
    summary = get_current_daf_summary(employee)
    active_tasks = get_active_tasks_for_employee(employee, include_related=True)
    payroll_summary = get_payroll_summary(employee)
    
    # Build context and render
    context = _build_usertasks_context(employee, summary, active_tasks, payroll_summary)
    return render(request, "management/daf/usertasks.html", context)


def _handle_payslip(request, username, pay_type):
    """Handle historical payslip view."""
    from ..services.daf_period_service import get_latest_daf_period_for_employee
    from ..integrations.finance_gateway import get_historical_payslip_data, get_payroll_summary
    
    employee = _get_employee(request, username)
    year, month, _ = get_latest_daf_period_for_employee(employee)
    
    # Get payslip data via gateway (no direct Finance model access)
    payslip_data = get_historical_payslip_data(employee, month, year)
    payroll_summary = get_payroll_summary(employee, month, year)
    
    # Build context and render
    context = _build_payslip_context(employee, payslip_data, payroll_summary, month, year)
    
    # Try modern template first, fallback to legacy
    try:
        return render(request, "management/daf/payslip_modern.html", context)
    except:
        return render(request, "management/daf/payslip.html", context)


def _handle_usertaskhistory(request, username):
    """Handle user task history view."""
    # Similar pattern - use gateways
    pass


def _handle_tasklist(request, username):
    """Handle task list view."""
    # Similar pattern - use gateways
    pass


def _handle_taskhistory(request, username):
    """Handle task history view."""
    # Similar pattern - use gateways
    pass


def _get_employee(request, username):
    """Helper to get employee user with permission checks."""
    # Security logic
    pass


def _build_usertasks_context(employee, summary, active_tasks, payroll_summary):
    """Build context for usertasks template."""
    # Context building logic
    pass


def _build_payslip_context(employee, payslip_data, payroll_summary, month, year):
    """Build context for payslip template."""
    # Context building logic
    pass
```

**Migration Steps:**
1. **Step 1:** Create `payslip.py` with router function (no logic changes)
2. **Step 2:** Extract `_handle_usertasks()` (move logic, use gateways)
3. **Step 3:** Extract `_handle_payslip()` (move logic, use gateways)
4. **Step 4:** Extract remaining handlers one by one
5. **Step 5:** Update `urls.py` to import from `daf.views.payslip` (URL unchanged)
6. **Step 6:** Remove old `payslip()` from `legacy_views.py`

### 4.2 Helper Function Extraction

**Functions to Extract from `legacy_views.py`:**

1. **`compute_task_compliance()`** → `daf/services/compliance_orchestrator.py`
   - Already well-isolated
   - Update to use gateways instead of direct model queries

2. **`_get_meeting_match_info()`** → `daf/integrations/meetings_gateway.py`
   - Move to Meetings gateway (not DAF service)

3. **`_calculate_approval_readiness()`** → `daf/services/compliance_orchestrator.py`
   - Helper for compliance calculation

4. **`get_user_data()`** → `daf/integrations/finance_gateway.py`
   - Move to Finance gateway

5. **`get_previous_month_reference_date()`** → `daf/utils.py`
   - DAF utility

6. **`normalize_period()`, `prefix_zero()`** → `daf/utils.py`
   - DAF utilities

7. **`bulk_update_daf_date()`** → `daf/services/daf_period.py` or management command
   - Data migration utility

### 4.3 Single Source of Truth for Metrics

**Current State:**
- `daf_v2_view()` computes metrics locally
- `payslip()` computes metrics via `PayrollSummaryService`
- Both should match but may drift

**Target State:**
- **Single Source:** `PayrollSummaryService.get_user_pay_summary()`
- **Both views use:** `finance_gateway.get_payroll_summary()`
- **No local computation:** Views only format service output

**Verification:**
- `PayrollSummaryService` already uses `get_current_daf_summary()` internally
- `PayrollSummaryService` is the canonical source for:
  - `target_amount`
  - `earned_amount_provisional`
  - `approved_earned_amount`
  - `pending_approval_amount`
  - `remaining_amount`
  - `approval_percentage`
  - `pay_day_date`
  - `time_remaining`

**Action:**
- Update `daf_v2_view()` to use `finance_gateway.get_payroll_summary()` exclusively
- Remove local metric computation from `daf_v2_view()`
- Ensure `payslip()` also uses `finance_gateway.get_payroll_summary()` for consistency

---

## Part 5: Incremental Migration Plan

### Phase 2.1: Gateway Creation (Week 1)
**Goal:** Create gateway interfaces without changing existing code

1. Create `daf/integrations/` package
2. Implement `tasks_gateway.py` (wrap existing Task queries)
3. Implement `evidence_gateway.py` (wrap EvidenceSummaryService)
4. Implement `meetings_gateway.py` (move `_get_meeting_match_info()`)
5. Implement `finance_gateway.py` (wrap PayrollSummaryService and Finance services)
6. Implement `requirements_gateway.py` (wrap Requirement queries)

**Deliverable:** All gateways exist and are tested (no view changes yet)

### Phase 2.2: Service Extraction (Week 2)
**Goal:** Extract DAF services and helpers from `legacy_views.py`

1. Create `daf/services/` package
2. Move `compute_task_compliance()` → `compliance_orchestrator.py`
3. Move `_calculate_approval_readiness()` → `compliance_orchestrator.py`
4. Move DAF summary services to `daf/services/` (from `services/`)
5. Update imports in `legacy_views.py` to use new locations

**Deliverable:** Services extracted, `legacy_views.py` imports updated

### Phase 2.3: View Refactoring - `payslip()` (Week 3)
**Goal:** Refactor `payslip()` view to use gateways

1. Create `daf/views/payslip.py` with router function
2. Extract `_handle_usertasks()` (use gateways)
3. Extract `_handle_payslip()` (use gateways)
4. Extract remaining handlers
5. Update `urls.py` to import from `daf.views.payslip`
6. Test all `pay_type` branches
7. Remove old `payslip()` from `legacy_views.py`

**Deliverable:** `payslip()` refactored, URLs stable, tests passing

### Phase 2.4: View Refactoring - `daf_v2_view()` (Week 4)
**Goal:** Refactor `daf_v2_view()` to use gateways

1. Move `daf_v2_view()` to `daf/views/daf_v2.py`
2. Replace direct model queries with gateway calls
3. Replace local metric computation with `finance_gateway.get_payroll_summary()`
4. Update `urls.py`
5. Test DAF v2 functionality

**Deliverable:** `daf_v2_view()` refactored, metrics consistent with payslip

### Phase 2.5: View Refactoring - Review Views (Week 5)
**Goal:** Refactor review views to use gateways

1. Move review views to `daf/views/review.py`
2. Replace direct model queries with gateway calls
3. Update `urls.py`
4. Test review functionality

**Deliverable:** Review views refactored

### Phase 2.6: Template Migration (Week 6)
**Goal:** Move non-DAF templates to their proper modules

1. Move `evidence_form*.html` to Evidence module templates
2. Move `task_detail.html` to Tasks module templates
3. Move `meeting_link_review.html` to Meetings module templates
4. Archive unused templates
5. Update template references in views

**Deliverable:** Templates properly organized

### Phase 2.7: Cleanup (Week 7)
**Goal:** Remove legacy code and finalize boundaries

1. Remove unused imports from `legacy_views.py`
2. Archive or remove evidence views from `legacy_views.py` (moved to Evidence module)
3. Update documentation
4. Run full test suite
5. Code review and merge

**Deliverable:** Clean codebase, all tests passing, documentation updated

---

## Part 6: Risk Mitigation

### 6.1 Risks and Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| Breaking existing URLs | HIGH | Router pattern maintains URL stability |
| Metric calculation drift | HIGH | Single source of truth (PayrollSummaryService) |
| Gateway performance | MEDIUM | Gateways are thin wrappers, minimal overhead |
| Circular import | MEDIUM | Careful import structure, gateways don't import views |
| Test coverage gaps | MEDIUM | Incremental testing at each phase |
| Template path changes | LOW | Templates stay in same location, only ownership changes |

### 6.2 Testing Strategy

1. **Unit Tests:**
   - Gateway interfaces (mock foreign domains)
   - Service extraction (test moved functions)
   - View refactoring (test each handler independently)

2. **Integration Tests:**
   - End-to-end DAF workflows
   - Payslip calculation accuracy
   - DAF v2 metrics consistency

3. **Regression Tests:**
   - All `pay_type` branches in `payslip()`
   - DAF v2 view functionality
   - Review workflows
   - API endpoints

### 6.3 Rollback Plan

- Each phase is a separate PR
- Can rollback individual phases without affecting others
- Gateway pattern allows gradual migration (old code can coexist)

---

## Part 7: Success Criteria

### 7.1 Phase 2 Complete When:

1. ✅ All DAF views use gateways (no direct foreign model queries)
2. ✅ `payslip()` is refactored into focused handlers
3. ✅ `daf_v2_view()` uses `finance_gateway.get_payroll_summary()` exclusively
4. ✅ All helper functions extracted from `legacy_views.py`
5. ✅ Templates properly organized by ownership
6. ✅ No boundary leaks (all foreign domain access via gateways)
7. ✅ All tests passing
8. ✅ Documentation updated

### 7.2 Metrics to Track:

- **Code Reduction:** `legacy_views.py` should shrink by ~800 lines (DAF-related code)
- **Coupling Reduction:** DAF views should have 0 direct imports from `finance.models`, `ai_services.models` (except via gateways)
- **Test Coverage:** Maintain or improve test coverage
- **Performance:** No performance regression (gateways are thin wrappers)

---

## Appendix A: Gateway Implementation Examples

### Example: Tasks Gateway

```python
# coda/management/daf/integrations/tasks_gateway.py

from typing import Optional, List
from django.contrib.auth import get_user_model
from management.models import Task, TaskHistory

User = get_user_model()


def get_active_tasks_for_employee(employee, include_related=True):
    """
    Get active tasks for an employee.
    
    Gateway function - DAF should use this instead of Task.objects directly.
    """
    queryset = Task.objects.filter(employee=employee, is_active=True)
    
    if include_related:
        queryset = queryset.select_related(
            'category', 'department', 'activity_type', 'employee', 'requirement'
        ).prefetch_related('tasklinks_set', 'review_comments')
    
    return queryset.order_by('id')


def get_task_history_for_period(employee, month, year):
    """
    Get TaskHistory records for a specific period.
    
    Gateway function - DAF should use this instead of TaskHistory.objects directly.
    """
    return TaskHistory.objects.filter(
        employee=employee,
        daf_date__month=month,
        daf_date__year=year
    ).order_by('-daf_date')


def get_task_by_id(task_id):
    """
    Get a single task by ID.
    
    Gateway function - DAF should use this instead of Task.objects.get() directly.
    """
    try:
        return Task.objects.select_related(
            'category', 'department', 'activity_type', 'employee', 'requirement'
        ).prefetch_related('tasklinks_set', 'review_comments').get(id=task_id)
    except Task.DoesNotExist:
        return None
```

### Example: Finance Gateway

```python
# coda/management/daf/integrations/finance_gateway.py

from typing import Optional, Dict, Any
from decimal import Decimal
from management.services.payroll_summary_service import PayrollSummaryService
from management.services.finance_service_helper import get_finance_task_service


def get_payroll_summary(employee, period_month=None, period_year=None):
    """
    Get payroll summary for an employee.
    
    Gateway function - DAF should use this instead of PayrollSummaryService directly.
    This is the SINGLE SOURCE OF TRUTH for payroll metrics.
    """
    service = PayrollSummaryService()
    return service.get_user_pay_summary(employee, period_month, period_year)


def get_payslip_config(employee):
    """
    Get payslip configuration for an employee.
    
    Gateway function - DAF should use this instead of PayslipConfig.objects directly.
    """
    finance_service = get_finance_task_service()
    if finance_service:
        config_dict = finance_service.get_payslip_config(employee.id)
        if config_dict:
            return config_dict
    
    # Fallback to direct model access (temporary bridge)
    try:
        from finance.models import PayslipConfig
        config = PayslipConfig.objects.get(user=employee)
        return {
            'loan_amount': config.loan_amount,
            'loan_repayment_percentage': config.loan_repayment_percentage,
            # ... other fields
        }
    except:
        return None


def get_historical_payslip_data(employee, month, year):
    """
    Get historical payslip data for a specific period.
    
    Gateway function - DAF should use this instead of PayCalculationService directly.
    """
    pay_service = get_finance_task_service()
    
    if pay_service and hasattr(pay_service, 'calculate_payslip'):
        try:
            return pay_service.calculate_payslip(
                employee=employee,
                target_month=month,
                target_year=year,
                pay_type='payslip',
                enforce_evidence=False,
            )
        except Exception:
            pass
    
    # Fallback to DAFSummaryService
    from management.services.daf_summary_service import DAFSummaryService
    daf_service = DAFSummaryService()
    summary = daf_service.get_summary(employee, target_month=month, target_year=year)
    
    # Map to payslip_data structure
    return {
        'tasks': summary.get('activities', []),
        'base_pay': {
            'total': summary.get('money', {}).get('released_total', Decimal('0')),
            'goal_amount': summary.get('money', {}).get('target_amount', Decimal('0')),
            # ... other fields
        },
        'summary': {
            'net_pay': summary.get('money', {}).get('net_income', Decimal('0')),
        },
        'bonuses': {},
        'deductions': {},
    }
```

---

**End of Phase 2 Proposal**

