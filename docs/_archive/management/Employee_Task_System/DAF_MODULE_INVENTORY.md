# DAF Module Refactor (Phase 1) — Inventory + Boundary Definition

**Date:** January 1, 2026  
**Scope:** `coda/management` DAF module only  
**Status:** Analysis and Proposal Preparation (NO IMPLEMENTATION)

---

## 1. DAF Module Boundary Statement

### 1.1 What DAF Owns

The DAF (Daily Activity Form) module is responsible for:

1. **DAF UI Views & Workflows**
   - Employee-facing DAF views (My DAF, DAF v2)
   - Manager review workflows (DAF Review, Review Comments, AI Review Suggestions)
   - Payslip views (historical and current period)
   - Task status tracking and compliance visualization

2. **DAF-Specific Models**
   - `TaskReviewComment`: Manager review comments on tasks
   - `TaskAIReviewSuggestion`: AI-generated review suggestions for tasks
   - `RequirementMatchCheck`: AI-generated requirement match verification results

3. **DAF Summary & Aggregation Services**
   - `DAFSummaryService`: Historical DAF summaries (TaskHistory-based)
   - `DAFCurrentSummaryService`: Current DAF summaries (Task-based)
   - `DAFPeriodService`: Period determination logic (latest month with TaskHistory data)
   - `PayrollSummaryService`: Payroll/DAF summary calculations (single source of truth)

4. **DAF Compliance & Quality Services**
   - `ChecklistEvaluationService`: Task quality evaluation (evidence, duration, checklist)
   - `EvidenceSummaryService`: Evidence existence and status checks (single source of truth)
   - `PolicyResolver`: Policy-driven compliance evaluation (Group A vs Group B)
   - `TaskQualityGateService`: Unified gate status for evidence/quality checks

5. **DAF Helper Functions**
   - `compute_task_compliance()`: Unified compliance status computation
   - `_calculate_approval_readiness()`: Approval readiness calculation
   - `_get_meeting_match_info()`: Meeting match information for tasks
   - `get_previous_month_reference_date()`: Date normalization helpers
   - `normalize_period()`, `prefix_zero()`: Period formatting helpers
   - `bulk_update_daf_date()`: TaskHistory daf_date field updates

6. **DAF Templates**
   - All templates under `templates/management/daf/`
   - DAF-specific UI components and partials

### 1.2 What DAF Must NOT Own (Belongs to Other Modules)

1. **Task Domain** (Core Task Management)
   - `Task` model: Core task entity (owned by Tasks module)
   - `TaskHistory` model: Historical task snapshots (owned by Tasks module)
   - `TaskLinks` model: Evidence links (owned by Evidence module)
   - Task assignment, creation, update logic (owned by Tasks module)

2. **Evidence Domain** (Evidence Management)
   - Evidence upload/creation workflows (owned by Evidence module)
   - Evidence validation and storage (owned by Evidence module)
   - Evidence form views (`new_evidence`, `evidence_form`) (owned by Evidence module)

3. **Meetings Domain** (Meeting Management)
   - `Meeting` model (from `ai_services.models`) (owned by AI Services/Meetings module)
   - Meeting matching logic (`MeetingEvidenceMatcher`) (owned by AI Services module)
   - Meeting room configuration (owned by AI Services module)
   - Meeting launch workflows (owned by Meetings module)

4. **Compliance Domain** (Compliance Rules)
   - `Requirement` model: Requirements (owned by Compliance/Requirements module)
   - Requirement assignment and validation (owned by Compliance module)
   - Policy definitions (owned by Compliance module)

5. **Payroll Domain** (Payroll Calculations)
   - `PayslipConfig` model (from `finance.models`) (owned by Finance module)
   - Pay calculation services (`PayCalculationService`, `ReleaseEngine`) (owned by Finance module)
   - Loan computation and management (owned by Finance module)
   - Deductions and bonuses calculation (owned by Finance module)

6. **Activity Type Domain** (Activity Taxonomy)
   - `ActivityType` model: Activity type definitions (owned by Activity Types module)
   - `ActivityDefinition` model: Activity metadata and AI definitions (owned by Activity Types module)
   - Activity checklist definitions (owned by Activity Types module)

7. **Employee Domain** (Employee Management)
   - `User` model (Django auth) (owned by Accounts module)
   - `UserProfile` model (owned by Accounts module)
   - Employee groups and policy assignments (owned by Employee Groups module)

### 1.3 DAF's Role: Orchestration Layer

DAF acts as an **orchestration layer** that:
- Aggregates data from Tasks, Evidence, Meetings, Compliance, and Payroll domains
- Provides unified UI views for employees and managers
- Computes summary metrics and compliance status
- Coordinates cross-domain workflows (e.g., task → evidence → meeting → compliance)

DAF does NOT own the underlying data models or business logic for these domains.

---

## 2. URL → View Mapping (DAF Endpoints Only)

### 2.1 Primary DAF Views

| URL Pattern | View Function | Template | Purpose |
|------------|---------------|----------|---------|
| `/management/payroll/` | `payslip()` | `management/daf/payslip.html`<br>`management/daf/payslip_modern.html` | Payslip view (supports multiple `pay_type` values) |
| `/management/daf/v2/` | `daf_v2_view()` | `management/daf/usertasks/employeetasks_v2.html` | Modern DAF v2 UI (employee view) |
| `/management/daf/review/` | `daf_review_view()` | `management/daf/review.html` | Manager review page (staff only) |

### 2.2 DAF Review Actions

| URL Pattern | View Function | Purpose |
|------------|---------------|---------|
| `/management/daf/review/comment/<int:task_id>/` | `daf_review_comment_view()` | Add review comment to task |
| `/management/daf/review/ai/<int:task_id>/` | `daf_review_ai_generate()` | Generate AI review suggestion for task |
| `/management/daf/review/ai-ops-run/` | `daf_review_ai_ops_run()` | Trigger AI daily operations run (staff only) |

### 2.3 DAF API Endpoints

| URL Pattern | View Function | Purpose |
|------------|---------------|---------|
| `/management/api/daf/summary/` | `daf_summary_api()` | DAF summary JSON API (GET, authenticated) |

### 2.4 DAF Debug Endpoints

| URL Pattern | View Function | Purpose |
|------------|---------------|---------|
| `/management/debug/daf-runtime/` | `daf_runtime_debug()` | DAF runtime debug info (staff only) |

### 2.5 Payslip View `pay_type` Parameter Values

The `payslip()` view supports multiple `pay_type` values via query parameter:
- `usertasks`: My DAF (current active tasks)
- `payslip`: Historical payslip (latest TaskHistory month)
- `task_payslip`: Task-based payslip (latest TaskHistory month)
- `usertaskhistory`: User task history view
- `tasks`: Task list view
- `taskhistory`: Task history view

---

## 3. View Inventory

### 3.1 DAF Views in `legacy_views.py`

#### 3.1.1 Primary DAF Views

1. **`payslip(request, *args, **kwargs)`** (Line 1099)
   - **Purpose:** Multi-purpose payslip/DAF view with dynamic `pay_type` routing
   - **Key Logic:**
     - For `pay_type='usertasks'`: Uses `get_current_daf_summary()` for current active tasks
     - For `pay_type in ['payslip', 'task_payslip']`: Uses `PayCalculationService` or `DAFSummaryService` for historical data
     - Period determination: `get_latest_daf_period_for_employee()` for payslip types
   - **Templates:** `payslip.html`, `payslip_modern.html`, `usertasks.html`, `tasklist.html`, `taskhistory.html`
   - **Dependencies:**
     - `daf_current_summary_service.get_current_daf_summary()`
     - `daf_period_service.get_latest_daf_period_for_employee()`
     - `daf_summary_service.DAFSummaryService`
     - `payroll_summary_service.get_time_remaining_until_pay_day()`
     - `get_pay_service()` (Finance service helper)
     - `get_user_data()` (helper function)
     - `get_selected_month_year()` (from `management.utils`)

2. **`daf_v2_view(request)`** (Line 1678)
   - **Purpose:** Modern DAF v2 UI for employees
   - **Key Logic:**
     - Gets current DAF summary via `get_current_daf_summary()`
     - Enriches tasks with quality scores, compliance status, evidence summaries
     - Uses `PayrollSummaryService` for consistent metrics with payslip
     - Supports `user_id` parameter for staff viewing other users' DAF
   - **Template:** `management/daf/usertasks/employeetasks_v2.html`
   - **Dependencies:**
     - `daf_current_summary_service.get_current_daf_summary()`
     - `checklist_evaluation_service.ChecklistEvaluationService`
     - `evidence_summary_service.get_task_evidence_summary()`
     - `payroll_summary_service.PayrollSummaryService`
     - `task_quality_gate_service.TaskQualityGateService`
     - `compute_task_compliance()` (helper function)
     - `_get_meeting_match_info()` (helper function)
     - `_calculate_approval_readiness()` (helper function, used indirectly)

3. **`daf_review_view(request)`** (Line 2553)
   - **Purpose:** Manager review page for tasks needing attention
   - **Key Logic:**
     - Finds tasks needing review (quality < 0.8, missing evidence, incomplete checklist, etc.)
     - Groups by employee or sorts by severity
     - Shows AI review suggestions and anomaly flags (staff only)
   - **Template:** `management/daf/review.html`
   - **Dependencies:**
     - `checklist_evaluation_service.ChecklistEvaluationService`
     - `TaskReviewComment` model
     - `TaskAIReviewSuggestion` model
     - `AIOperationsRun` model (from `ai_services.models`)

4. **`daf_review_comment_view(request, task_id)`** (Line 2798)
   - **Purpose:** Add review comment to a task
   - **Key Logic:**
     - Creates `TaskReviewComment` record
     - Redirects back to review page
   - **Dependencies:**
     - `TaskReviewComment` model

5. **`daf_review_ai_generate(request, task_id)`** (Line 2831)
   - **Purpose:** Generate AI review suggestion for a task
   - **Key Logic:**
     - Calls `TaskAIReviewService.generate_review_suggestion()`
     - Creates `TaskAIReviewSuggestion` record
   - **Dependencies:**
     - `task_ai_review_service.TaskAIReviewService`

6. **`daf_review_ai_ops_run(request)`** (Line 2865)
   - **Purpose:** Trigger AI daily operations run
   - **Key Logic:**
     - Calls `AIOperationsService.run_daily_ops()`
     - Redirects back to review page
   - **Dependencies:**
     - `ai_services.services.ai_operations_service.AIOperationsService`

#### 3.1.2 DAF Helper Functions in `legacy_views.py`

1. **`get_user_data(employee)`** (Line 1005)
   - Retrieves `UserProfile`, loan data, and `PayslipConfig` for an employee
   - Uses `finance_service_helper.get_finance_task_service()` for loan data
   - Returns tuple: `(userprofile, user_data, payslip_config)`

2. **`bulk_update_daf_date()`** (Line 1055)
   - Updates `daf_date` field for existing `TaskHistory` records
   - Sets `daf_date` to same day of last month for tasks created this month

3. **`get_previous_month_reference_date(today=None)`** (Line 119)
   - Calculates reference date for previous month
   - Used for period normalization

4. **`normalize_period(year:int, month:int) -> str`** (Line 2912)
   - Formats year/month as normalized string (e.g., "2025-12")

5. **`prefix_zero(month:int) -> str`** (Line 2909)
   - Formats month with leading zero (e.g., "01", "12")

6. **`_calculate_approval_readiness(task, requires_requirement=False, task_links=None)`** (Line 3085)
   - Calculates approval readiness status for a task
   - Returns dict with: `requirement_present`, `evidence_complete`, `checklist_complete`, `duration_ok`, `quality_pass`, `overall_ready`, `quality_metrics`
   - Uses `ChecklistEvaluationService` for quality metrics

7. **`compute_task_compliance(task, task_links, checklist_eval, meeting_match_info=None, user=None, policy=None)`** (Line 3209)
   - **Single source of truth** for all compliance checks
   - Returns unified compliance status dict with:
     - `requires_requirement`, `requirement_ok`
     - `evidence_status` ('missing' | 'partial' | 'complete' | 'auto_pending')
     - `evidence_ok`, `evidence_count`, `evidence_coverage`
     - `checklist_ok`, `checklist_completion`
     - `duration_ok`, `duration_factor`
     - `quality_ok`, `quality_score`
     - `gate_pass` (AND of all checks)
     - `policy_group` (Group A, B, or C)
   - Uses `PolicyResolver` for policy-driven compliance
   - Uses `EvidenceSummaryService` for evidence status

8. **`_get_meeting_match_info(task, link=None)`** (Line 3565)
   - Gets meeting match information for a task
   - Returns dict with: `has_match`, `meeting`, `match_type`, `confidence`, `requirement_code_match`, etc.
   - Uses `MeetingEvidenceMatcher` from `ai_services.services`
   - Validates meeting room matches task's activity mapping (PART B FIX)

9. **`_safe_meeting_query(*args, **filter_kwargs)`** (Line 3168)
   - Safely queries `Meeting` model, handling case where table doesn't exist
   - Returns `QuerySet` or `None` if table doesn't exist

### 3.2 DAF API Views

1. **`daf_summary_api(request)`** (in `coda/management/views/api_views.py`, Line 344)
   - **Purpose:** JSON API endpoint for DAF summary
   - **Method:** GET only
   - **Query Parameters:** `year` (optional), `month` (optional)
   - **Returns:** JSON with DAF summary data
   - **Dependencies:**
     - `daf_summary_service.DAFSummaryService`

### 3.3 DAF Debug Views

1. **`daf_runtime_debug(request)`** (in `coda/management/views_debug.py`, Line 39)
   - **Purpose:** Debug endpoint for DAF runtime information (staff only)
   - **Template:** `management/debug/daf_runtime_debug.html`

---

## 4. Template Inventory

### 4.1 DAF Templates Directory Structure

```
templates/management/daf/
├── employee_tasks.html
├── evidence_form.html
├── evidence_form_old.html
├── evidence_form_v2.html
├── legacy_evidence_form.html
├── meeting_link_review.html
├── payslip.html
├── payslip_modern.html
├── reset_tasks_select.html
├── review.html
├── task_detail.html
├── taskhistory.html
├── tasklist.html
├── userevidence.html
├── usertasks.html
└── usertasks/
    ├── contractualtasks.html
    ├── employeetasks.html
    └── employeetasks_v2.html
```

### 4.2 Template → View Mapping

| Template | View(s) | Purpose |
|----------|---------|---------|
| `management/daf/payslip.html` | `payslip()` (fallback) | Legacy payslip template |
| `management/daf/payslip_modern.html` | `payslip()` (primary) | Modern payslip template |
| `management/daf/usertasks.html` | `payslip()` (`pay_type='usertasks'` or `'usertaskhistory'`) | My DAF (current active tasks) |
| `management/daf/usertasks/employeetasks_v2.html` | `daf_v2_view()` | DAF v2 modern UI |
| `management/daf/usertasks/employeetasks.html` | (Legacy, may be referenced) | Legacy employee tasks view |
| `management/daf/review.html` | `daf_review_view()` | Manager review page |
| `management/daf/tasklist.html` | `payslip()` (`pay_type='tasks'`) | Task list view |
| `management/daf/taskhistory.html` | `payslip()` (`pay_type='taskhistory'`) | Task history view |
| `management/daf/evidence_form.html` | `new_evidence()` (Evidence module) | Evidence form (NOT DAF-owned) |
| `management/daf/evidence_form_v2.html` | `new_evidence()` (Evidence module) | Evidence form v2 (NOT DAF-owned) |
| `management/daf/task_detail.html` | `TaskDetailView` (Tasks module) | Task detail view (NOT DAF-owned) |
| `management/daf/meeting_link_review.html` | `meeting_link_review_dashboard()` (Meetings module) | Meeting link review (NOT DAF-owned) |

### 4.3 DAF-Owned Templates (Core)

**Primary DAF Templates:**
1. `payslip.html` / `payslip_modern.html` - Payslip views
2. `usertasks.html` - My DAF (current active tasks)
3. `usertasks/employeetasks_v2.html` - DAF v2 modern UI
4. `review.html` - Manager review page

**Secondary DAF Templates:**
5. `tasklist.html` - Task list view (via payslip view)
6. `taskhistory.html` - Task history view (via payslip view)

### 4.4 Templates Referenced by DAF (NOT DAF-Owned)

- `evidence_form.html`, `evidence_form_v2.html` - Evidence module
- `task_detail.html` - Tasks module
- `meeting_link_review.html` - Meetings module

---

## 5. Model Inventory (DAF-Related Only)

### 5.1 DAF-Owned Models

These models are defined in `coda/management/models.py` and are owned by the DAF module:

1. **`TaskReviewComment`** (Line 1577)
   - **Purpose:** Review comments from managers/staff on tasks
   - **Fields:**
     - `task` (FK to `Task`)
     - `employee` (FK to `User`)
     - `reviewer` (FK to `User`)
     - `comment` (TextField)
     - `status` (CharField: 'NEEDS_FIX', 'APPROVED', 'INFO')
     - `created_at`, `updated_at`
   - **Used by:** `daf_review_view()`, `daf_review_comment_view()`, `daf_v2_view()`

2. **`TaskAIReviewSuggestion`** (Line 1722)
   - **Purpose:** AI-generated review suggestions for tasks needing attention
   - **Fields:**
     - `task` (FK to `Task`)
     - `suggestion_json` (JSONField)
     - `provider`, `model`, `confidence`
     - `input_hash` (for deduplication)
     - `is_active`, `created_at`, `expires_at`
   - **Used by:** `daf_review_view()`, `daf_review_ai_generate()`, `daf_v2_view()`

3. **`RequirementMatchCheck`** (Line 1632)
   - **Purpose:** Stores AI-generated requirement match verification results
   - **Fields:**
     - `task` (FK to `Task`)
     - `requirement` (FK to `Requirement`)
     - `created_by` (FK to `User`)
     - `status` (CharField: 'pass', 'review', 'fail')
     - `confidence`, `reason`, `result_json`
     - `provider`, `model`, `fallback_used`
     - `input_hash`, `created_at`
   - **Used by:** `daf_v2_view()` (for requirement match status display)

### 5.2 Foreign Models Used Heavily by DAF (NOT DAF-Owned)

1. **Task Domain Models** (Owned by Tasks module)
   - `Task` - Core task entity
   - `TaskHistory` - Historical task snapshots
   - `TaskLinks` - Evidence links (owned by Evidence module, but heavily used by DAF)

2. **Evidence Domain Models** (Owned by Evidence module)
   - `TaskLinks` - Evidence links (FK to `Task`)

3. **Meetings Domain Models** (Owned by AI Services/Meetings module)
   - `Meeting` (from `ai_services.models`) - Meeting records
   - `MeetingActivityTagSuggestion` (from `ai_services.models`) - AI meeting activity tag suggestions
   - `TaskAnomalyFlag` (from `ai_services.models`) - AI anomaly flags for tasks
   - `AIOperationsRun` (from `ai_services.models`) - AI operations run status

4. **Compliance Domain Models** (Owned by Compliance/Requirements module)
   - `Requirement` - Requirements

5. **Activity Type Domain Models** (Owned by Activity Types module)
   - `ActivityType` - Activity type definitions
   - `ActivityDefinition` - Activity metadata and AI definitions

6. **Employee Domain Models** (Owned by Accounts module)
   - `User` (Django auth) - User/employee records
   - `UserProfile` (from `shared_core.users`) - User profile data

7. **Payroll Domain Models** (Owned by Finance module)
   - `PayslipConfig` (from `finance.models`) - Payslip configuration

---

## 6. Service/Utils Dependency Map

### 6.1 DAF-Owned Services

Located in `coda/management/services/`:

1. **`daf_summary_service.py`**
   - **Class:** `DAFSummaryService`
   - **Purpose:** Historical DAF summaries (TaskHistory-based)
   - **Used by:** `payslip()` (for historical payslip data), `daf_summary_api()`
   - **Dependencies:**
     - `TaskHistory` model
     - `EmployeeCareerState` model
     - `ComplianceCalculator` service
     - `PayCalculationService` (via interface)
     - `CareerLevelService` (via interface)
     - `PerformanceMetricsService` (via interface)
     - `LoyaltyFundService` (via interface)

2. **`daf_current_summary_service.py`**
   - **Function:** `get_current_daf_summary(employee)`
   - **Purpose:** Current DAF summaries (Task-based, current active tasks only)
   - **Used by:** `payslip()` (`pay_type='usertasks'`), `daf_v2_view()`
   - **Dependencies:**
     - `Task` model
     - `TaskHistory` model (for historical context)

3. **`daf_period_service.py`**
   - **Function:** `get_latest_daf_period_for_employee(employee, *, default_today=None)`
   - **Purpose:** Determines latest year/month with TaskHistory data for an employee
   - **Used by:** `payslip()` (for payslip period determination)
   - **Dependencies:**
     - `TaskHistory` model

4. **`payroll_summary_service.py`**
   - **Class:** `PayrollSummaryService`
   - **Function:** `get_time_remaining_until_pay_day()`
   - **Purpose:** Single source of truth for payroll/DAF summary calculations
   - **Used by:** `payslip()`, `daf_v2_view()`
   - **Dependencies:**
     - `Task` model
     - `countdown_in_month()` utility (from `shared_core.utils`)

5. **`checklist_evaluation_service.py`**
   - **Class:** `ChecklistEvaluationService`
   - **Purpose:** Task quality evaluation (evidence, duration, checklist completion)
   - **Used by:** `daf_v2_view()`, `daf_review_view()`, `_calculate_approval_readiness()`, `compute_task_compliance()`
   - **Dependencies:**
     - `Task` model
     - `TaskLinks` model
     - `ActivityDefinition` model
     - `coda.config.activity_checklists` (checklist config)

6. **`evidence_summary_service.py`**
   - **Function:** `get_task_evidence_summary(task, task_links, meeting_match_info)`
   - **Purpose:** Single source of truth for evidence existence and status checks
   - **Used by:** `daf_v2_view()`, `compute_task_compliance()`
   - **Dependencies:**
     - `Task` model
     - `TaskLinks` model

7. **`policy_resolver.py`**
   - **Class:** `PolicyResolver`
   - **Purpose:** Policy-driven compliance evaluation (Group A vs Group B)
   - **Used by:** `compute_task_compliance()`
   - **Dependencies:**
     - `User` model (for group resolution)

8. **`task_quality_gate_service.py`**
   - **Class:** `TaskQualityGateService`
   - **Purpose:** Unified gate status for evidence/quality checks
   - **Used by:** `daf_v2_view()`
   - **Dependencies:**
     - `ChecklistEvaluationService`
     - `EvidenceSummaryService`
     - `PolicyResolver`

9. **`task_ai_review_service.py`**
   - **Class:** `TaskAIReviewService`
   - **Purpose:** AI review suggestion generation for tasks
   - **Used by:** `daf_review_ai_generate()`
   - **Dependencies:**
     - `Task` model
     - `TaskAIReviewSuggestion` model
     - AI service interface (via `ai_service_helper`)

### 6.2 Foreign Services Used by DAF (NOT DAF-Owned)

1. **Finance Services** (Owned by Finance module)
   - `PayCalculationService` (via `get_pay_service()` helper)
   - `ReleaseEngine` (via `get_pay_service()` helper)
   - Finance service interface (via `finance_service_helper.get_finance_task_service()`)

2. **AI Services** (Owned by AI Services module)
   - `MeetingEvidenceMatcher` (from `ai_services.services.meeting_evidence_matcher`)
   - `AIOperationsService` (from `ai_services.services.ai_operations_service`)
   - AI service interface (via `ai_service_helper.get_ai_service()`)

3. **Meeting Services** (Owned by AI Services/Meetings module)
   - `get_meeting_room_for_activity()` (from `ai_services.utils.meeting_room_config`)

4. **Utils from `management.utils`** (Owned by Management Utils)
   - `paytime()` - Pay period calculation
   - `payinitial()` - Initial pay calculation
   - `paymentconfigurations()` - Payslip configuration retrieval
   - `deductions()` - Deductions calculation
   - `loan_computation()` - Loan computation
   - `get_tasks()` - Task retrieval
   - `get_selected_month_year()` - Month/year selection from form
   - `compute_total_points()` - Total points calculation
   - `get_bonus_and_summary()` - Bonus and summary calculation

5. **Utils from `shared_core.utils`** (Owned by Shared Core)
   - `countdown_in_month()` - Countdown to end of month
   - `generate_chatbot_response()` - Chatbot response generation (used indirectly)

6. **Utils from `main.utils`** (Owned by Main app)
   - `countdown_in_month()` - Countdown utility (alternative implementation)

7. **Checklist Utils** (Owned by Checklist Utils package)
   - `get_checklist_with_completion()` (from `management.checklist_utils_pkg.checklist_utils`)

### 6.3 Helper Functions in `legacy_views.py` (DAF-Specific)

1. **`get_user_data(employee)`** - User data retrieval (uses Finance service)
2. **`bulk_update_daf_date()`** - TaskHistory daf_date updates
3. **`get_previous_month_reference_date(today=None)`** - Date normalization
4. **`normalize_period(year, month)`** - Period formatting
5. **`prefix_zero(month)`** - Month formatting
6. **`_calculate_approval_readiness(task, ...)`** - Approval readiness calculation
7. **`compute_task_compliance(task, ...)`** - Unified compliance computation
8. **`_get_meeting_match_info(task, link=None)`** - Meeting match information
9. **`_safe_meeting_query(...)`** - Safe Meeting model query

---

## 7. Summary Statistics

### 7.1 Code Metrics

- **Total DAF Views:** 8 (6 in `legacy_views.py`, 1 API view, 1 debug view)
- **Total DAF Helper Functions:** 9
- **Total DAF-Owned Models:** 3 (`TaskReviewComment`, `TaskAIReviewSuggestion`, `RequirementMatchCheck`)
- **Total DAF-Owned Services:** 9
- **Total DAF Templates:** 18 (4 primary, 14 secondary/legacy)
- **Total DAF URLs:** 7 endpoints

### 7.2 Dependencies

- **Foreign Models Used:** 7+ (Task, TaskHistory, TaskLinks, Requirement, Meeting, ActivityType, User, etc.)
- **Foreign Services Used:** 5+ (Finance services, AI services, Meeting services, Utils)
- **Cross-App Dependencies:** Finance, AI Services, Accounts, Main

---

## 8. Key Observations

### 8.1 Boundary Clarity

- **Clear Ownership:** DAF owns review workflows, summary aggregation, and compliance orchestration
- **Clear Non-Ownership:** DAF does NOT own Task, Evidence, Meeting, Requirement, or Payroll models
- **Orchestration Role:** DAF acts as an orchestration layer, not a data owner

### 8.2 Coupling Points

1. **Heavy Dependency on Task Model:** DAF views query `Task` and `TaskHistory` extensively
2. **Evidence Integration:** DAF uses `TaskLinks` for evidence status but doesn't own evidence creation
3. **Meeting Integration:** DAF uses `Meeting` model and `MeetingEvidenceMatcher` but doesn't own meeting management
4. **Finance Integration:** DAF uses Finance services for pay calculations but doesn't own payroll logic
5. **Compliance Integration:** DAF uses `Requirement` model but doesn't own requirement management

### 8.3 Refactoring Opportunities

1. **Service Extraction:** Helper functions in `legacy_views.py` could be moved to dedicated service modules
2. **Template Consolidation:** Multiple evidence form templates suggest legacy code paths
3. **View Consolidation:** `payslip()` view handles multiple `pay_type` values - could be split
4. **Dependency Injection:** Direct model imports could be replaced with service interfaces

---

## 9. Next Steps (Phase 2 Planning)

Based on this inventory, Phase 2 should focus on:

1. **Service Layer Extraction:** Move helper functions to dedicated service modules
2. **Interface Definition:** Define clear interfaces for cross-domain dependencies
3. **View Refactoring:** Split multi-purpose views (`payslip()`) into focused views
4. **Template Cleanup:** Archive or consolidate legacy templates
5. **Dependency Injection:** Replace direct model imports with service calls

---

**End of Inventory Report**

