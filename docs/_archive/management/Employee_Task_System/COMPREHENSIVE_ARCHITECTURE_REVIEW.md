# Management App Comprehensive Architecture Review & Reorganization Proposal

**Date:** December 30, 2025  
**Status:** Review Complete - Proposal Ready  
**Scope:** `coda/management` app only (unless dependencies required to explain coupling)

---

## A. Executive Summary

### Current State
The management app is a **1,842-line monolithic models file**, **5,975-line legacy_views.py monolith**, **772-line forms.py**, **37 service files**, **84 templates**, **123 URL patterns**, and **37 test files**. The app has grown organically over time, resulting in:

- **Scattered organization**: Views split between `legacy_views.py` (5,975 lines) and 7 root-level `views_*.py` files
- **Monolithic models**: All 23 model classes in a single 1,842-line `models.py` file
- **Mixed concerns**: Business logic in views, models, utils, and services inconsistently
- **Template sprawl**: 84 templates across 16 directories with potential duplicates
- **Inconsistent patterns**: Some features use interfaces/adapters (AI, Finance, Pro Services), others use direct imports
- **Test coverage gaps**: 37 test files but many domains untested

### Key Problems
1. **Maintainability**: Hard to find code, understand relationships, make changes
2. **Testability**: Large files hard to test in isolation
3. **Coupling**: Direct model imports from other apps (professional_services, finance, ai_services)
4. **Code duplication**: Similar logic in multiple places (utils.py, services/, legacy_views.py)
5. **Architectural drift**: Current state diverges significantly from intended architecture (03_ARCHITECTURE.md)

### Proposed Solution
**Incremental refactoring** in 4 phases:
- **Phase 0**: Inventory + safety checks + regression test suite
- **Phase 1**: Low-risk reorganizations (file moves, compatibility shims, import rewires)
- **Phase 2**: Domain extractions (models split, views organized, services consolidated)
- **Phase 3**: Removals + documentation + hardening tests

**Estimated Total Effort:** 40-60 hours over multiple sessions  
**Risk Level:** Medium (mitigated by incremental approach and compatibility shims)

---

## B. Current State Inventory

### File Tree Snapshot

```
coda/management/
├── __init__.py
├── admin.py                          # 329 lines - Admin registrations
├── apps.py
├── forms.py                          # 772 lines - 20 form classes
├── legacy_views.py                   # 5,975 lines ⚠️ MASSIVE MONOLITH
├── models.py                         # 1,842 lines ⚠️ ALL MODELS IN ONE FILE
├── urls.py                           # 283 lines - 123 URL patterns
├── utils.py                          # 1,314 lines - Mixed utilities
├── signals.py
├── permission.py
├── context_processors.py
├── cron.py
│
├── models/
│   └── base_models.py                # 649 lines - Base model mixins
│
├── views/
│   ├── __init__.py                   # Re-exports from legacy_views + modular views
│   ├── base_views.py                 # 649 lines ✅ Good
│   ├── api_views.py                  # 432 lines ✅ Good
│   ├── task_assignment_views.py      # 253 lines ✅ Good
│   ├── meeting_review_views.py       # 201 lines ✅ Good
│   ├── budget_integration_views.py   # 524 lines ✅ Good
│   ├── forecasting_views.py          # 206 lines ✅ Good
│   ├── trend_analysis_views.py       # 182 lines ✅ Good
│   ├── compliance_kpi_views.py       # 173 lines ✅ Good
│   ├── anomaly_detection_views.py    # (size unknown)
│   ├── analytics_dashboard_views.py  # 258 lines ✅ Good
│   ├── insights_views.py             # 184 lines ✅ Good
│   └── user_testing_views.py         # 315 lines ✅ Good
│
├── views_employee_groups.py          # 264 lines ⚠️ Should be in views/
├── views_debug.py                    # 478 lines ⚠️ Should be in views/
├── views_enhanced_dashboard.py       # 482 lines ⚠️ Should be in views/
├── views_goto_ops.py                 # (small) ⚠️ Should be in views/
├── views_meeting_launch.py           # 119 lines ⚠️ Should be in views/
├── views_performance_report.py       # 224 lines ⚠️ Should be in views/
└── views_task_reset_selective.py    # 346 lines ⚠️ Should be in views/
│
├── services/                         # 37 service files ✅ Well organized
│   ├── base_service.py
│   ├── utilities_service.py
│   ├── daf_summary_service.py
│   ├── evidence_summary_service.py
│   ├── task_standardization_service.py
│   ├── intelligent_assignment_service.py
│   ├── meeting_linking_service.py
│   ├── compliance_calculator.py
│   ├── checklist_evaluation_service.py
│   ├── policy_resolver.py
│   ├── employee_group_service.py
│   ├── employee_filter_service.py
│   ├── finance_service_helper.py
│   ├── pro_services_helper.py
│   ├── ai_service_helper.py
│   └── [22 more service files]
│
├── templates/management/             # 84 templates across 16 directories
│   ├── daf/                          # DAF templates (10 files)
│   ├── contracts/                    # Contract templates (12 files)
│   ├── departments/                  # Department templates (8 files)
│   ├── background/                   # Background check templates (2 files)
│   ├── components/                   # Reusable components
│   ├── doc_templates/                # Document templates
│   ├── email/                        # Email templates
│   ├── insights/                     # Insights templates
│   └── reports/                      # Report templates
│
├── static/management/                # Image assets only (14 .jpg files)
│   └── img/
│       ├── background/               # 5 files
│       ├── home/                     # 5 files
│       ├── icons/                    # 3 files
│       └── Models/                     # 2 files
│
├── management/commands/              # 16 management commands
│   ├── analyze_task_history.py
│   ├── diagnose_daf.py
│   ├── seed_daf_checklists.py
│   ├── validate_data_quality.py
│   └── [12 more commands]
│
├── tests/                            # 37 test files
│   ├── test_daf_v2_view.py
│   ├── test_requirement_enforcement.py
│   ├── test_evidence_workflow_v2.py
│   ├── test_oauth_views.py
│   └── [33 more test files]
│
├── checklist_utils_pkg/              # Checklist utilities package
│   └── checklist_utils.py
│
└── templatetags/
    ├── task_tags.py
    └── url_validation.py
```

### Counts Summary

| Category | Count | Notes |
|----------|-------|-------|
| **Models** | 23 classes | All in single `models.py` (1,842 lines) |
| **Forms** | 20 classes | All in single `forms.py` (772 lines) |
| **View modules** | 19 files | 12 in `views/`, 7 at root level, 1 legacy monolith |
| **View functions/classes** | ~100+ | Estimated from legacy_views.py + modular views |
| **URL patterns** | 123 | All in `urls.py` |
| **Templates** | 84 | Across 16 directories |
| **Services** | 37 files | Well organized in `services/` |
| **Management commands** | 16 | In `management/commands/` |
| **Test files** | 37 | Various test coverage |
| **Static assets** | 14 images | Only images, no JS/CSS |

**Total Lines of Code (estimated):**
- Models: ~1,842 lines
- Views: ~11,642 lines (legacy_views: 5,975 + others: ~5,667)
- Forms: ~772 lines
- Services: ~8,000+ lines (estimated)
- Utils: ~1,314 lines
- **Total: ~23,570+ lines**

---

## C. Key Problems and Root Causes

### 1. Models Organization

#### Problem: Monolithic models.py
- **Current:** All 23 model classes in single 1,842-line file
- **Issues:**
  - Hard to navigate and find specific models
  - Merge conflicts when multiple developers work on different models
  - No clear domain boundaries
  - Mixed concerns (Tasks, Requirements, Contracts, Grievances, etc.)

#### Model Inventory (23 classes):

**Task Domain (5 models):**
- `Task` - Main task model (319 lines)
- `TaskHistory` - Historical task records (208 lines)
- `TaskLinks` - Task-evidence links (69 lines)
- `TaskCategory` - Task categories (46 lines)
- `TaskSubcategory` - Task subcategories (18 lines)

**DAF Domain (3 models):**
- `TaskReviewComment` - Manager review comments (83 lines)
- `TaskAIReviewSuggestion` - AI review suggestions (90 lines)
- `RequirementMatchCheck` - Requirement matching checks (90 lines)

**Requirement Domain (3 models):**
- `Requirement` - Requirements (114 lines)
- `ProcessJustification` - Requirement justifications (8 lines)
- `ProcessBreakdown` - Requirement breakdowns (8 lines)

**Activity Type Domain (2 models):**
- `ActivityType` - Canonical activity types (143 lines)
- `ActivityDefinition` - Activity definitions (78 lines)

**Training Domain (1 model):**
- `Training` - Training sessions (84 lines) - **Depends on professional_services**

**Contract Domain (1 model):**
- `BaseContract` - Base contract model (38 lines)

**Grievance Domain (2 models):**
- `Grievance` - Grievances (45 lines)
- `Conflict_Resolution` - Conflict resolutions (46 lines)

**Admin/HR Domain (4 models):**
- `Policy` - Company policies (75 lines)
- `Meetings` - Internal meetings (39 lines)
- `Advertisement` - Advertisements (28 lines)
- `SubCategory` - Department subcategories (7 lines)
- `Link` - Department links (14 lines)

**Employee Domain (2 models):**
- `EmployeeCareerState` - Career state tracking (81 lines)
- `PerformanceWarning` - Performance warnings (74 lines)

**Assignment Domain (1 model):**
- `Assignment` - Assignment uploads (25 lines)

#### Anti-Patterns Identified:

1. **Fat Models:**
   - `Task` model has 319 lines with many properties and methods
   - `TaskHistory` has complex date calculations in properties
   - Business logic mixed with data definitions

2. **Inconsistent Naming:**
   - `Conflict_Resolution` uses underscore (should be `ConflictResolution`)
   - `TaskLinks` vs `TaskLink` (inconsistent pluralization)
   - `SubCategory` vs `TaskSubcategory` (inconsistent casing)

3. **Inconsistent FK Usage:**
   - Some models use `on_delete=models.CASCADE`, others use `RESTRICT` or `SET_NULL`
   - No consistent pattern for related_name
   - Some FKs have `limit_choices_to`, others don't

4. **Missing Constraints:**
   - No unique constraints on natural keys (e.g., requirement codes)
   - No check constraints for status fields
   - Missing indexes on frequently queried fields

5. **Duplicated Choice Enums:**
   - `Policy.DEPARTMENT_CHOICES` vs similar choices in other models
   - `Requirement.STATUS_CHOICES` vs similar status fields
   - No shared constants module

6. **Cross-App Dependencies:**
   - `Training` model depends on `professional_services.models` (FeaturedCategory, FeaturedSubCategory, FeaturedActivity)
   - Should use interface/feature gating instead

#### Migration Risks:

1. **Large Tables:**
   - `Task` table likely has thousands of records
   - `TaskHistory` table likely has tens of thousands of records
   - `Requirement` table may have hundreds of records

2. **Risky Schema Changes:**
   - Adding NOT NULL constraints to existing nullable fields (requires data backfill)
   - Changing FK relationships (requires data migration)
   - Splitting models into separate files (no schema change, but import changes)

3. **Data Backfills Likely Needed:**
   - If adding constraints to existing data
   - If normalizing duplicated data
   - If fixing inconsistent FK relationships

### 2. Views + URLs Organization

#### Problem: Scattered Views
- **Current:** Views split across:
  - `legacy_views.py` (5,975 lines) - 49+ functions/classes
  - 7 root-level `views_*.py` files
  - 12 organized files in `views/` directory
- **Issues:**
  - Hard to find specific views
  - Inconsistent import patterns
  - Circular import risks
  - No clear domain boundaries

#### View Inventory:

**From legacy_views.py (49+ functions/classes):**
- Dashboard: `home()`, `score_report()`
- Tasks: `newtaskcreation()`, `TaskListView`, `TaskDetailView`, `TaskUpdateView`, `TaskDeleteView`, `UsertaskUpdateView`, `tasklist()`, `filterbycategory()`, `gettasksuggestions()`, `verifytaskgroupexists()`, `getaveragetargets()`, `reset_task()`
- DAF: `payslip()`, `daf_v2_view()`, `daf_review_view()`, `daf_review_comment_view()`, `daf_review_ai_generate()`, `daf_review_ai_ops_run()`, `get_user_data()`, `bulk_update_daf_date()`
- Evidence: `newevidence()`, `process_evidence_submission()`, `userevidence()`, `evidence_update_view()`
- Requirements: `requirements()`, `active_requirements()`, `newrequirement()`, `RequirementUpdateView`, `RequirementDetailView`, `RequirementDeleteView`, `videolink()`, `form_submission_view()`, `justification()`, `add_requirement_justification()`
- Meetings: `meetings()`, `newmeeting()`, `MeetingUpdateView`, `get_attendee_duration()`
- Contracts: `contract()`, `employee_contract()`, `read_employee_contract()`, `confirm_employee_contract()`
- Grievances: `grievance_form()`, `grievance_file()`, `GrievanceUpdateView`, `ResolutionUpdateView`
- Training: `sessions()`, `usersession()`, `SessionCreateView`, `SessionUpdateView`
- Admin: `assess()`, `AssessUpdateView`, `DSUListView`, `clientassessment()`, `ClientAssessmentListView`, `AssessmentUpdateView`, `add_background_info()`, `BackgroundCheckListView`, `newdepartment()`, `department()`, `DepartmentUpdateView`, `companyagenda()`, `companyagenda_improved()`, `updatelinks_companyagenda()`, `policy()`, `policies()`, `PolicyUpdateView`, `benefits()`
- Assignments: `assignment_upload()`, `assignment_list()`, `assignment_detail()`, `delete_assignment()`
- OAuth: `oauth_login()`, `oauth_callback()`
- Misc: `get_attendee_duration()`, `AdsContent`, `AdsCreateView`, `AdsUpdateView`

**From root-level views_*.py files:**
- `views_employee_groups.py`: `employee_groups_view()`, `bulk_update_employee_groups()`, `update_single_employee_group()`
- `views_debug.py`: `daf_runtime_debug()` + helpers
- `views_enhanced_dashboard.py`: `enhanced_task_dashboard()`, `refresh_dashboard()`, `export_my_data()`, `request_help()`, `report_issue()`, `load_more_tasks()`, `submit_evidence()`, `task_leaderboard()`, `task_history_view()`, `tier_analytics()`
- `views_goto_ops.py`: `goto_ops_refresh_view()`, `goto_ops_reauth_redirect_view()`
- `views_meeting_launch.py`: `launch_meeting()`, `get_launch_intent()`
- `views_performance_report.py`: `performance_report()`
- `views_task_reset_selective.py`: `reset_tasks_select()`, `reset_all_tasks()`

**From views/ directory (organized):**
- API views: `activity_summary_api()`, `activity_analytics_api()`, `daf_summary_api()`
- Task assignment: `get_intelligent_assignment_suggestions()`
- Meeting review: `meeting_link_review_dashboard()`, `approve_meeting_link()`, etc.
- Budget integration: `budget_activity_totals_api()`, `budget_evidence_validation_api()`
- Forecasting: `activity_forecast_api()`, `budget_forecast_api()`
- Trend analysis: `trend_analysis_api()`, `employee_trend_analysis_api()`
- Compliance: `compliance_kpis_api()`, `compliance_history_api()`
- Anomaly detection: `anomaly_detection_api()`
- Analytics dashboards: `analytics_dashboard()`, `activity_forecast_dashboard()`, etc.

#### Import Patterns:

**Current import sources in urls.py:**
1. `from management import views` (re-exports from legacy_views)
2. `from management import views_employee_groups` (direct import)
3. `from management.views_enhanced_dashboard import ...` (direct import)
4. `from management.views_task_reset_selective import ...` (direct import)
5. `from management.views import ...` (modular views)

**Circular Import Risks:**
- `views/__init__.py` imports from `legacy_views.py`
- `legacy_views.py` imports from various services
- Services may import from views (need to verify)
- `urls.py` imports from multiple view sources

#### Entry Points (Top Pages):

1. **Home/Dashboard:** `home()` → `/management/`
2. **DAF v2:** `daf_v2_view()` → `/management/daf/v2/`
3. **Tasks:** `TaskListView` → `/management/tasks/`
4. **Payroll:** `payslip()` → `/management/payroll/`
5. **Employee Groups:** `employee_groups_view()` → `/management/employee-groups/`
6. **Requirements:** `requirements()` → `/management/requirements/`

#### Suspected Dead/Unreferenced Views:

**Need verification via grep:**
- `score_report()` - May be unused
- `companyagenda()` vs `companyagenda_improved()` - One may be legacy
- `tasklist()` vs `TaskListView` - Duplicate functionality?
- `filterbycategory()` - May be unused
- Various helper functions in legacy_views.py

### 3. Templates Organization

#### Template Inventory (84 files across 16 directories):

**DAF Templates (10 files):**
- `daf/evidence_form.html` (current)
- `daf/evidence_form_old.html` ⚠️ **Likely legacy**
- `daf/evidence_form_v2.html` (v2 version)
- `daf/payslip.html` (current)
- `daf/payslip_modern.html` ⚠️ **May be unused**
- `daf/review.html` (manager review)
- `daf/tasklist.html`
- `daf/usertasks.html` (legacy)
- `daf/usertasks/employeetasks.html` (v1)
- `daf/usertasks/employeetasks_v2.html` (v2) ✅ **Current**
- `daf/usertasks/contractualtasks.html`

**Contract Templates (12 files):**
- `contracts/client_contract.html`
- `contracts/client_investment_contract.html`
- `contracts/contract_error.html`
- `contracts/employee_contract.html`
- `contracts/generalcontract_form.html`
- `contracts/generalcontract_formA.html` ⚠️ **May be duplicate**
- `contracts/my_investor_contract.html`
- `contracts/my_supportcontract_form.html`
- `contracts/my_trainingcontract_form.html`
- `contracts/read_employee_contract.html`
- `contracts/supportcontract_form.html`
- `contracts/trainingcontract_form.html`
- `contracts/loan/client_loan_contract.html`

**Department Templates (8+ files):**
- `departments/agenda/` (multiple files)
- `departments/agenda_backup/` ⚠️ **Backup - likely unused**
- `departments/hr/policy_form.html`

**Other Templates:**
- `background/background_form.html`, `background/backgroundchecklist.html`
- `assignment_detail.html`, `assignment_upload.html`
- `employee_groups.html`
- `task_confirm_delete.html`, `taskcategory_form.html`
- `insights/performance_dashboard.html`
- `components/` (reusable components)
- `doc_templates/` (document templates)
- `email/` (email templates)
- `reports/` (report templates)

#### Template Issues:

1. **Duplicates:**
   - `evidence_form.html` vs `evidence_form_v2.html` vs `evidence_form_old.html`
   - `payslip.html` vs `payslip_modern.html`
   - `usertasks.html` vs `employeetasks.html` vs `employeetasks_v2.html`
   - `generalcontract_form.html` vs `generalcontract_formA.html`

2. **Naming Inconsistencies:**
   - Mix of snake_case and kebab-case
   - Some templates use `_form` suffix, others don't
   - Inconsistent directory structure

3. **Template Inheritance Issues:**
   - Need to verify base template usage
   - May have inconsistent extends patterns

4. **Unused Templates:**
   - `agenda_backup/` directory likely unused
   - `evidence_form_old.html` likely legacy
   - `payslip_modern.html` may be unused if `payslip.html` is current

### 4. Static Assets

**Current State:**
- Only image assets (14 .jpg files)
- No management-owned JS/CSS files
- Images in `static/management/img/` organized by category

**Issues:**
- No JS/CSS for management app (may be in main app or shared)
- Image naming inconsistent (some descriptive, some generic)

### 5. Forms / Serializers / Services / Utils

#### Forms (20 classes in forms.py):

**Current Forms:**
- `GrievanceForm`
- `MeetingForm`
- `DepartmentForm`
- `PolicyForm`
- `ManagementForm` (DSU/Assessment form)
- `ClientAssessmentForm`
- `RequirementForm`
- `EvidenceForm`
- `TaskForm`
- `EmployeeContractForm`
- `BackgroundForm`
- `TagFilterForm`
- `MonthForm`
- `AssignmentUploadForm`
- `OptimizedDepartmentForm`
- `OptimizedEmployeeForm`
- `OptimizedMeetingForm`
- `OptimizedPolicyForm`
- `OptimizedTaskForm`
- `dynamic_agenda_form()` (function, not class)

#### Issues:

1. **"Optimized" Forms:**
   - `Optimized*` forms suggest there are non-optimized versions
   - May be duplicates or legacy forms
   - Need to verify which are actually used

2. **Conditional Imports:**
   - Forms conditionally import from `professional_services.models`
   - Good pattern, but should be consistent

3. **Form Organization:**
   - All forms in single file (772 lines)
   - Should be split by domain

#### Services (37 files):

**Service Organization:** ✅ **Well organized in `services/` directory**

**Service Categories:**

**DAF Services (4):**
- `daf_summary_service.py`
- `daf_current_summary_service.py`
- `daf_period_service.py`
- `evidence_summary_service.py`

**Task Services (6):**
- `task_standardization_service.py`
- `task_quality_gate_service.py`
- `task_ai_review_service.py`
- `taskhistory_analyzer.py`
- `intelligent_assignment_service.py`
- `smart_migration_service.py`

**Compliance Services (3):**
- `compliance_calculator.py`
- `compliance_kpi_service.py`
- `employee_compliance_service.py`
- `checklist_evaluation_service.py`

**Employee Services (5):**
- `employee_group_service.py`
- `employee_filter_service.py`
- `employee_identity_service.py`
- `enhanced_group_service.py`
- `department_optimization_service.py`

**AI Services (4):**
- `ai_prediction_service.py`
- `ai_service_helper.py`
- `simple_ai_service.py`
- `release_engine.py`

**Analytics Services (4):**
- `forecasting_service.py`
- `trend_analysis_service.py`
- `anomaly_detection_service.py`
- `data_validation_service.py`

**Integration Services (3):**
- `finance_service_helper.py`
- `pro_services_helper.py`
- `meeting_linking_service.py`

**Utility Services (4):**
- `utilities_service.py`
- `management_service.py`
- `policy_resolver.py`
- `requirement_match_service.py`
- `payroll_summary_service.py`

**Base Services (1):**
- `base_service.py`

#### Service Issues:

1. **Service Candidates (Logic in Views/Models):**
   - DAF calculations in `legacy_views.py` (`payslip()`, `daf_v2_view()`) - Should be in services
   - Task compliance logic in views - Should be in `compliance_calculator.py`
   - Evidence validation in views - Should be in `evidence_summary_service.py`
   - Meeting matching logic - Partially in `meeting_linking_service.py`, but some in views

2. **Duplicated Helpers:**
   - `utils.py` has 1,314 lines of mixed utilities
   - Some utilities may duplicate service functionality
   - Need to audit and consolidate

3. **Service Patterns:**
   - Most services follow `BaseService` pattern ✅
   - Some services use interfaces/adapters ✅
   - Some services have direct model access (acceptable)

#### Utils (utils.py - 1,314 lines):

**Current Utilities:**
- Payroll calculations: `paytime()`, `payinitial()`, `paymentconfigurations()`, `deductions()`, `loan_computation()`, `updateloantable()`, `addloantable()`
- Task utilities: `get_tasks()`, `task_assignment_random()`, `get_selected_month_year()`
- Employee utilities: `employee_group_level()`, `lap_save_bonus()`, `get_bonus_and_summary()`, `compute_total_points()`
- Link utilities: `defined_links()`
- Review utilities: `split_review_by_sections()`, `suggestions()`, `upload_file_to_drive()`

**Issues:**
- Large file with mixed concerns
- Some utilities may duplicate service functionality
- Should be split by domain or moved to services

### 6. Admin + Management Commands + Tests

#### Admin (admin.py - 329 lines):

**Registered Models:**
- `Training` (TrainingAdmin)
- `TaskHistory` (TaskHistoryAdmin)
- `Task` (TaskAdmin)
- `Policy`
- `Meetings`
- `TaskLinks`
- `TaskCategory`
- `Requirement`
- `Advertisement` (AdsAdmin)
- `ProcessJustification`
- `ProcessBreakdown`
- `TaskGroups`
- `Grievance`
- `Conflict_Resolution`
- `BaseContract`
- `EmployeeCareerState` (EmployeeCareerStateAdmin)
- `SubCategory`
- `Link`

**Admin Issues:**
- Some models have custom admin classes, others use default
- Inconsistent patterns
- `TrainingAdmin` has complex save logic (should be in service)
- `TaskAdmin` uses `ActivityTypeApplicationService` ✅ Good pattern

#### Management Commands (16 commands):

**Commands:**
- `analyze_task_history.py`
- `check_oauth_settings.py`
- `consolidate_management_app.py`
- `diagnose_daf.py`
- `dump_daf_summary.py`
- `end_to_end_testing.py`
- `enhance_department_relationships.py`
- `fix_taskhistory_dates.py`
- `inspect_daf_test_users.py`
- `list_unmapped_tasks.py`
- `seed_daf_checklists.py`
- `seed_daf_demo_tasks.py`
- `send_performance_warnings.py`
- `smart_migrate_tasks.py`
- `sync_activity_types.py`
- `validate_data_quality.py`

**Command Organization:** ✅ **Well organized in `management/commands/`**

#### Tests (37 test files):

**Test Coverage:**
- DAF tests: 10+ files (good coverage)
- Evidence tests: 4 files
- Requirement tests: 2 files
- OAuth tests: 1 file
- Employee groups tests: 1 file
- Various integration tests

**Test Organization:** ✅ **Tests exist but may need reorganization after refactoring**

**Missing Test Coverage:**
- Contract views (no tests found)
- Grievance views (no tests found)
- Training views (no tests found)
- Assignment views (no tests found)
- Meeting views (limited tests)
- Admin views (no tests found)

### 7. Documentation Alignment

#### Intended Architecture (from 03_ARCHITECTURE.md):

**Planned Structure:**
```
management/
├─ models/
│  ├─ base_models.py
│  └─ [task_models.py, hr_models.py, ...]  # Split models (planned)
├─ views/
│  ├─ dashboard_views.py
│  ├─ task_views.py
│  ├─ requirement_views.py
│  ├─ meeting_views.py
│  ├─ contract_views.py
│  ├─ grievance_views.py
│  ├─ training_views.py
│  ├─ admin_views.py
│  └─ assignment_views.py
```

**Current Reality:**
- Models: ❌ All in single `models.py` (not split)
- Views: ⚠️ Partially organized (some in `views/`, most in `legacy_views.py`)
- Services: ✅ Well organized (matches intended)
- Templates: ⚠️ Organized but has duplicates/legacy files

**Divergences:**
1. Models not split by domain
2. Views not fully organized by domain
3. Forms not split by domain
4. Templates have duplicates/legacy files
5. Utils not consolidated into services

---

## D. Proposed Target Architecture

### D1. Models Organization

#### Option A: Split by Domain (Recommended)

**Proposed Structure:**
```
coda/management/
├── models/
│   ├── __init__.py                    # Re-export all models for backward compatibility
│   ├── base_models.py                 # Base model mixins (existing)
│   │
│   ├── task_models.py                 # Task domain
│   │   ├── Task
│   │   ├── TaskHistory
│   │   ├── TaskLinks
│   │   ├── TaskCategory
│   │   └── TaskSubcategory
│   │
│   ├── daf_models.py                  # DAF domain
│   │   ├── TaskReviewComment
│   │   ├── TaskAIReviewSuggestion
│   │   └── RequirementMatchCheck
│   │
│   ├── requirement_models.py          # Requirement domain
│   │   ├── Requirement
│   │   ├── ProcessJustification
│   │   └── ProcessBreakdown
│   │
│   ├── activity_models.py             # Activity type domain
│   │   ├── ActivityType
│   │   └── ActivityDefinition
│   │
│   ├── training_models.py             # Training domain
│   │   └── Training
│   │
│   ├── contract_models.py            # Contract domain
│   │   └── BaseContract
│   │
│   ├── grievance_models.py           # Grievance domain
│   │   ├── Grievance
│   │   └── Conflict_Resolution
│   │
│   ├── admin_models.py               # Admin/HR domain
│   │   ├── Policy
│   │   ├── Meetings
│   │   ├── Advertisement
│   │   ├── SubCategory
│   │   └── Link
│   │
│   ├── employee_models.py            # Employee domain
│   │   ├── EmployeeCareerState
│   │   └── PerformanceWarning
│   │
│   └── assignment_models.py          # Assignment domain
│       └── Assignment
```

**Migration Strategy:**
1. Create `models/` package with `__init__.py`
2. Split `models.py` into domain files
3. Update `models/__init__.py` to re-export all models
4. Update imports incrementally (start with new code, then legacy)
5. Keep `models.py` as compatibility shim temporarily

**Benefits:**
- Clear domain boundaries
- Easier to find models
- Reduced merge conflicts
- Better testability

**Risks:**
- Import changes required
- Need to update all model imports
- Migration complexity

#### Option B: Keep Single File (Not Recommended)

**Rationale for NOT choosing:**
- File too large (1,842 lines)
- Hard to maintain
- Merge conflicts
- No domain separation

### D2. Views Organization

**Proposed Structure (matches VIEWS_REFACTORING_ANALYSIS.md):**

```
coda/management/
├── views/
│   ├── __init__.py                    # Minimal exports (only what urls.py needs)
│   ├── base_views.py                   # Base view classes (existing)
│   │
│   ├── dashboard_views.py             # Home, score_report, enhanced dashboard
│   ├── task_views.py                   # Task CRUD, evidence, reset
│   ├── daf_views.py                    # DAF v2, payslip, review
│   ├── requirement_views.py            # Requirements management
│   ├── meeting_views.py                # Meetings, GoToMeeting ops, launch
│   ├── contract_views.py               # Contract views
│   ├── grievance_views.py              # Grievance & resolution
│   ├── training_views.py               # Sessions & training
│   ├── admin_views.py                  # Employee groups, assessments, policies, performance
│   ├── assignment_views.py             # Assignment upload
│   ├── oauth_views.py                  # OAuth login/callback
│   │
│   ├── api_views.py                    # Phase 1: Activity Summary & Analytics APIs (existing)
│   ├── task_assignment_views.py        # Phase 1: Intelligent Assignment API (existing)
│   ├── meeting_review_views.py         # Phase 1: Meeting Link Review APIs (existing)
│   ├── budget_integration_views.py     # Phase 2: Budget Integration APIs (existing)
│   ├── forecasting_views.py            # Phase 3: Forecasting APIs (existing)
│   ├── trend_analysis_views.py         # Phase 3: Trend Analysis APIs (existing)
│   ├── compliance_kpi_views.py         # Phase 3: Compliance KPI APIs (existing)
│   ├── anomaly_detection_views.py      # Phase 3: Anomaly Detection APIs (existing)
│   ├── analytics_dashboard_views.py    # Phase 3: Analytics Dashboards (existing)
│   ├── insights_views.py               # Phase 1: Performance Insights (existing)
│   ├── user_testing_views.py           # Phase 2: User Testing (existing)
│   │
│   └── debug_views.py                  # Debug views (dev-only, optional)
```

**See VIEWS_REFACTORING_ANALYSIS.md for detailed migration plan.**

### D3. Templates Organization

**Proposed Structure:**

```
coda/management/templates/management/
├── base.html                          # Base template (if not in main app)
├── components/                        # Reusable components
│   ├── base_components.html
│   ├── task_card.html
│   ├── evidence_form.html
│   └── [other components]
│
├── daf/                               # DAF templates
│   ├── usertasks/
│   │   ├── employeetasks_v2.html     # Current (keep)
│   │   └── employeetasks.html         # Legacy (archive)
│   ├── evidence_form_v2.html          # Current (keep)
│   ├── evidence_form.html             # Legacy (archive)
│   ├── payslip.html                   # Current (keep)
│   ├── review.html                    # Current (keep)
│   └── tasklist.html                  # Current (keep)
│
├── tasks/                             # Task templates
│   ├── task_list.html
│   ├── task_detail.html
│   ├── task_form.html
│   └── task_confirm_delete.html
│
├── requirements/                      # Requirement templates
│   ├── requirement_list.html
│   ├── requirement_detail.html
│   └── requirement_form.html
│
├── meetings/                          # Meeting templates
│   └── meeting_form.html
│
├── contracts/                         # Contract templates (keep as-is)
│   ├── employee_contract.html
│   ├── client_contract.html
│   └── [other contract templates]
│
├── grievances/                        # Grievance templates
│   ├── grievance_form.html
│   └── grievance_detail.html
│
├── training/                          # Training templates
│   └── session_form.html
│
├── admin/                             # Admin templates
│   ├── employee_groups.html           # Current (keep)
│   ├── policy_form.html
│   ├── background/
│   │   ├── background_form.html
│   │   └── backgroundchecklist.html
│   └── departments/
│       └── agenda/
│           └── [agenda templates]
│
├── assignments/                       # Assignment templates
│   ├── assignment_list.html
│   ├── assignment_detail.html
│   └── assignment_upload.html
│
├── insights/                          # Insights templates (keep as-is)
│   └── performance_dashboard.html
│
├── email/                             # Email templates (keep as-is)
│   └── [email templates]
│
├── reports/                           # Report templates (keep as-is)
│   └── [report templates]
│
└── _archive/                          # Archived templates
    ├── evidence_form_old.html
    ├── payslip_modern.html
    ├── usertasks.html
    ├── generalcontract_formA.html
    └── agenda_backup/
```

**Naming Conventions:**
- Use snake_case for template names
- Use descriptive names: `task_list.html`, `requirement_detail.html`
- Use `_form.html` suffix for forms
- Use `_confirm_delete.html` for delete confirmations

**Template Inheritance:**
- All templates should extend a base template
- Use consistent block names
- Document template inheritance hierarchy

### D4. Services/Utils Organization

**Current State:** ✅ **Services well organized**

**Proposed Improvements:**

1. **Consolidate Utils into Services:**
   - Move payroll utilities from `utils.py` to `payroll_summary_service.py`
   - Move task utilities to `task_standardization_service.py` or new `task_utils_service.py`
   - Move employee utilities to `employee_group_service.py` or new `employee_utils_service.py`
   - Keep only truly generic utilities in `utils.py`

2. **Service Patterns:**
   - **Fat Service, Thin View:** Business logic in services, views only handle HTTP
   - **Shared Selectors:** Common query patterns in service methods
   - **Centralized Constants:** Move choice enums to `constants.py` or service modules

3. **New Service Candidates:**
   - `template_service.py` - Template rendering helpers
   - `notification_service.py` - Email/notification sending
   - `export_service.py` - Data export functionality

### D5. Forms Organization

**Proposed Structure:**

```
coda/management/
├── forms/
│   ├── __init__.py                    # Re-export all forms
│   │
│   ├── task_forms.py                  # Task-related forms
│   │   ├── TaskForm
│   │   ├── EvidenceForm
│   │   └── OptimizedTaskForm
│   │
│   ├── requirement_forms.py           # Requirement forms
│   │   └── RequirementForm
│   │
│   ├── contract_forms.py              # Contract forms
│   │   └── EmployeeContractForm
│   │
│   ├── grievance_forms.py             # Grievance forms
│   │   └── GrievanceForm
│   │
│   ├── admin_forms.py                 # Admin forms
│   │   ├── PolicyForm
│   │   ├── DepartmentForm
│   │   ├── MeetingForm
│   │   ├── ManagementForm
│   │   ├── ClientAssessmentForm
│   │   ├── BackgroundForm
│   │   └── Optimized* forms
│   │
│   ├── assignment_forms.py            # Assignment forms
│   │   └── AssignmentUploadForm
│   │
│   └── common_forms.py                # Common forms
│       ├── TagFilterForm
│       ├── MonthForm
│       └── dynamic_agenda_form()
```

**Migration Strategy:**
1. Create `forms/` package
2. Split `forms.py` by domain
3. Update `forms/__init__.py` to re-export
4. Update imports incrementally
5. Keep `forms.py` as compatibility shim temporarily

### D6. Tests Organization

**Proposed Structure:**

```
coda/management/tests/
├── __init__.py
│
├── unit/                              # Unit tests
│   ├── test_models/
│   │   ├── test_task_models.py
│   │   ├── test_daf_models.py
│   │   └── [other model tests]
│   │
│   ├── test_services/
│   │   ├── test_daf_summary_service.py
│   │   ├── test_task_standardization_service.py
│   │   └── [other service tests]
│   │
│   └── test_forms/
│       ├── test_task_forms.py
│       └── [other form tests]
│
├── integration/                       # Integration tests
│   ├── test_daf_workflow.py
│   ├── test_evidence_workflow.py
│   ├── test_requirement_workflow.py
│   └── [other workflow tests]
│
├── views/                             # View tests
│   ├── test_daf_views.py
│   ├── test_task_views.py
│   ├── test_requirement_views.py
│   └── [other view tests]
│
└── fixtures/                          # Test fixtures
    ├── task_fixtures.json
    └── [other fixtures]
```

**Test Coverage Plan:**
1. **Must-Have Regression Tests (before refactoring):**
   - DAF v2 view smoke test
   - Task CRUD smoke test
   - Evidence submission smoke test
   - Requirement workflow smoke test
   - Employee groups smoke test

2. **Missing Test Coverage (after refactoring):**
   - Contract views
   - Grievance views
   - Training views
   - Assignment views
   - Meeting views (expand coverage)
   - Admin views

---

## E. De-duplication and Archiving Plan

### E1. Models De-duplication

**No model duplicates identified** - All 23 models are unique.

**Actions:**
- None required for models

### E2. Views De-duplication

**Suspected Duplicates (need verification):**
- `tasklist()` vs `TaskListView` - Verify if both used
- `score_report()` - Verify if used
- `companyagenda()` vs `companyagenda_improved()` - Verify which is current
- `filterbycategory()` - Verify if used

**Actions:**
1. Use grep to find all references to suspected duplicates
2. Check URL patterns to see which are actually wired
3. Archive unused views (move to `views/_archive/` or mark as deprecated)
4. Consolidate duplicates into single implementation

### E3. Templates De-duplication

**Confirmed Duplicates:**
- `evidence_form.html` vs `evidence_form_v2.html` vs `evidence_form_old.html`
- `payslip.html` vs `payslip_modern.html`
- `usertasks.html` vs `employeetasks.html` vs `employeetasks_v2.html`
- `generalcontract_form.html` vs `generalcontract_formA.html`

**Actions:**
1. **Archive to `templates/management/_archive/`:**
   - `evidence_form_old.html`
   - `payslip_modern.html` (if `payslip.html` is current)
   - `usertasks.html` (if `employeetasks_v2.html` is current)
   - `generalcontract_formA.html` (if `generalcontract_form.html` is current)
   - `agenda_backup/` directory (entire directory)

2. **Keep current versions:**
   - `evidence_form_v2.html` (if this is current)
   - `payslip.html` (if this is current)
   - `employeetasks_v2.html` (confirmed current)
   - `generalcontract_form.html` (if this is current)

3. **Verification Steps:**
   - Grep for template references in views
   - Check which templates are actually rendered
   - Archive only after confirming unused

### E4. Forms De-duplication

**Suspected Duplicates:**
- `Optimized*` forms vs non-optimized forms
   - `OptimizedDepartmentForm` vs `DepartmentForm`
   - `OptimizedEmployeeForm` vs (no non-optimized version found)
   - `OptimizedMeetingForm` vs `MeetingForm`
   - `OptimizedPolicyForm` vs `PolicyForm`
   - `OptimizedTaskForm` vs `TaskForm`

**Actions:**
1. Verify which optimized forms are actually used
2. If optimized forms are used, remove non-optimized versions
3. If non-optimized are used, remove optimized versions
4. Consolidate into single implementation

### E5. Services/Utils De-duplication

**Suspected Duplicates:**
- Utilities in `utils.py` may duplicate service functionality
- Need to audit and consolidate

**Actions:**
1. Audit `utils.py` functions against services
2. Move utilities to appropriate services
3. Remove duplicated utilities
4. Keep only truly generic utilities in `utils.py`

### E6. Archiving Strategy

**Archive Location:** `templates/management/_archive/`

**Rules for Archiving:**
1. **Archive (don't delete) if:**
   - Template/file is suspected unused but not confirmed
   - Template/file is legacy but may be referenced
   - Template/file is duplicate but unsure which is current

2. **Delete (only if confidently unused):**
   - After 6 months in archive with no references
   - After confirming via grep/search that no code references it
   - After checking git history for last usage

3. **Never delete:**
   - Files referenced in migrations
   - Files with recent git history
   - Files that may be used by external systems

---

## F. Incremental Migration Strategy

### Phase 0: Inventory + Safety Checks

**Goal:** Establish baseline and safety net before any changes.

**Steps:**
1. **Create comprehensive inventory:**
   - Document all models, views, templates, forms
   - Map all URL patterns to views
   - List all imports and dependencies
   - Create checklist of all functionality

2. **Run safety checks:**
   - Run full test suite and document results
   - Run Django system check: `python manage.py check`
   - Verify all URLs work (manual smoke test)
   - Document current behavior

3. **Create regression test suite:**
   - Must-have smoke tests for critical flows:
     - DAF v2 view loads
     - Task CRUD works
     - Evidence submission works
     - Requirement workflow works
     - Employee groups work
   - Run and document test results

4. **Document current state:**
   - Create baseline documentation
   - Document known issues
   - Create migration checklist

**Estimated Effort:** 4-6 hours  
**Risk:** Very Low (read-only operations)

---

### Phase 1: Low-Risk Reorganizations

**Goal:** Move files and update imports with minimal code changes.

**Sub-phases (from VIEWS_REFACTORING_ANALYSIS.md):**

#### Phase 1A: Minimal-Diff Relocations
- Move root-level `views_*.py` files to `views/` directory
- Update relative imports within moved files
- No logic changes, no merges

#### Phase 1B: Compatibility Shims
- Add compatibility shims at old paths
- Re-export from new module paths
- Prevent hidden imports from breaking

#### Phase 1C: Standardize Imports
- Update `urls.py` to use `management.views.<module>` pattern
- Update all imports to new paths
- Keep `views/__init__.py` exports minimal

#### Phase 1D: Verification
- Compile checks
- Django system check
- Manual smoke testing

**Estimated Effort:** 3.5-5.5 hours  
**Risk:** Low (incremental, testable steps)

**Additional Phase 1 Tasks (if time permits):**
- Archive duplicate templates to `_archive/`
- Create `forms/` package structure (no moves yet)
- Create `models/` package structure (no moves yet)

---

### Phase 2: Domain Extractions and Consolidation

**Goal:** Split monolithic files and organize by domain.

#### Phase 2A: Split Models (if approved)

**Steps:**
1. Create `models/` package with domain files
2. Split `models.py` one domain at a time:
   - Start with lowest coupling: `assignment_models.py`
   - Then: `grievance_models.py`, `contract_models.py`, `training_models.py`
   - Then: `requirement_models.py`, `activity_models.py`
   - Then: `admin_models.py`, `employee_models.py`
   - Then: `daf_models.py`
   - Finally: `task_models.py` (highest coupling)
3. Update `models/__init__.py` to re-export all
4. Update imports incrementally
5. Keep `models.py` as compatibility shim
6. Test after each domain extraction

**Estimated Effort:** 8-12 hours  
**Risk:** Medium (import changes required)

#### Phase 2B: Split Forms

**Steps:**
1. Create `forms/` package with domain files
2. Split `forms.py` by domain
3. Update `forms/__init__.py` to re-export
4. Update imports incrementally
5. Keep `forms.py` as compatibility shim
6. Test after split

**Estimated Effort:** 2-3 hours  
**Risk:** Low (similar to models split)

#### Phase 2C: Extract Views from legacy_views.py

**Steps:**
1. Extract one domain at a time (from VIEWS_REFACTORING_ANALYSIS.md):
   - Start with lowest coupling: `oauth_views.py`
   - Then: `assignment_views.py`, `grievance_views.py`, `contract_views.py`
   - Then: `training_views.py`, `requirement_views.py`
   - Then: `meeting_views.py`, `task_views.py`
   - Then: `daf_views.py`
   - Finally: `dashboard_views.py`, `admin_views.py` (highest coupling)
2. In `legacy_views.py`, replace moved code with re-exports
3. Update `views/__init__.py` minimally
4. Test after each extraction
5. Commit after each extraction

**Estimated Effort:** 8-12 hours  
**Risk:** Medium (need to ensure all imports work)

#### Phase 2D: Consolidate Utils into Services

**Steps:**
1. Audit `utils.py` functions
2. Move payroll utilities to `payroll_summary_service.py`
3. Move task utilities to appropriate task services
4. Move employee utilities to employee services
5. Keep only generic utilities in `utils.py`
6. Update imports incrementally
7. Test after each consolidation

**Estimated Effort:** 4-6 hours  
**Risk:** Low (moving code, not changing logic)

---

### Phase 3: Removals + Documentation + Hardening

**Goal:** Remove compatibility shims, update documentation, add tests.

**Steps:**
1. **Remove compatibility shims:**
   - Remove `legacy_views.py` (after all imports updated)
   - Remove root-level `views_*.py` shims (after imports updated)
   - Remove `models.py` shim (after imports updated)
   - Remove `forms.py` shim (after imports updated)

2. **Update documentation:**
   - Update `03_ARCHITECTURE.md` to reflect new structure
   - Update `04_IMPLEMENTATION.md` with migration notes
   - Update `06_MAINTENANCE.md` with new file locations
   - Create migration guide for developers

3. **Add hardening tests:**
   - Add tests for newly organized modules
   - Add integration tests for critical flows
   - Add regression tests to prevent future drift

4. **Final verification:**
   - Run full test suite
   - Run Django system check
   - Manual smoke testing
   - Performance check (should be same or better)

**Estimated Effort:** 4-6 hours  
**Risk:** Low (if Phase 2 done correctly)

---

### Phase Summary

| Phase | Effort | Risk | Dependencies |
|-------|--------|------|--------------|
| Phase 0 | 4-6 hours | Very Low | None |
| Phase 1 | 3.5-5.5 hours | Low | Phase 0 |
| Phase 2A (Models) | 8-12 hours | Medium | Phase 1 |
| Phase 2B (Forms) | 2-3 hours | Low | Phase 1 |
| Phase 2C (Views) | 8-12 hours | Medium | Phase 1 |
| Phase 2D (Utils) | 4-6 hours | Low | Phase 1 |
| Phase 3 | 4-6 hours | Low | Phase 2 |
| **Total** | **34.5-49.5 hours** | **Medium** | - |

**Note:** Phases can be done incrementally over multiple sessions. Each phase should be tested and committed before proceeding.

---

## G. "Targeted Views Refactor" Compatibility Check

### How Views-Only Plan Fits

The **VIEWS_REFACTORING_ANALYSIS.md** plan (Phase 1A-1D + 1.5 + Phase 2 views extraction) is **fully compatible** with this comprehensive plan:

1. **Phase 1 views work** is **Phase 1** in comprehensive plan ✅
2. **Phase 2 views extraction** is **Phase 2C** in comprehensive plan ✅
3. Views refactor can proceed **independently** of models/forms refactoring ✅

### Recommended Integration

**Option A: Do Views First (Recommended)**
- Complete views refactor (Phase 1A-1D + 1.5 + Phase 2C from views plan)
- Then proceed with models/forms refactoring (Phase 2A, 2B)
- Benefits: Views are most problematic, quick wins, lower risk

**Option B: Do All Phase 2 Together**
- Complete all Phase 2 work together (models + forms + views + utils)
- More comprehensive but higher coordination needed

**Recommendation:** **Option A** - Views refactor first, then models/forms.

### Changes to Views Plan

**No changes needed** - The views refactoring plan is sound and compatible.

**Additional considerations from comprehensive review:**
1. **Template path updates:** When moving views, verify template paths still work
2. **Form imports:** Views import forms, so form refactoring (Phase 2B) should happen after views or coordinate imports
3. **Model imports:** Views import models, so model refactoring (Phase 2A) should use compatibility shims to avoid breaking views

---

## H. Appendices

### H1. URL → View Mapping Table

**Complete URL pattern inventory (123 patterns):**

| URL Pattern | View Function/Class | Module | Domain |
|-------------|---------------------|--------|--------|
| `/` | `home()` | legacy_views | Dashboard |
| `/companyagenda/` | `companyagenda()` | legacy_views | Admin |
| `/companyagenda-improved/` | `companyagenda_improved()` | legacy_views | Admin |
| `/update-agenda/<str:title>/<int:pk>/` | `updatelinks_companyagenda()` | legacy_views | Admin |
| `/policy/` | `policy()` | legacy_views | Admin |
| `/policies/` | `policies()` | legacy_views | Admin |
| `/policy/<int:pk>/update/` | `PolicyUpdateView` | legacy_views | Admin |
| `/benefits/` | `benefits()` | legacy_views | Admin |
| `/employee_contract/` | `employee_contract()` | legacy_views | Contract |
| `/read_employee_contract/` | `read_employee_contract()` | legacy_views | Contract |
| `/confirm_employee_contract/` | `confirm_employee_contract()` | legacy_views | Contract |
| `/tasks/` | `TaskListView` | legacy_views | Task |
| `/payroll/` | `payslip()` | legacy_views | DAF |
| `/daf/v2/` | `daf_v2_view()` | legacy_views | DAF |
| `/daf/review/` | `daf_review_view()` | legacy_views | DAF |
| `/daf/review/comment/<int:task_id>/` | `daf_review_comment_view()` | legacy_views | DAF |
| `/daf/review/ai/<int:task_id>/` | `daf_review_ai_generate()` | legacy_views | DAF |
| `/daf/review/ai-ops-run/` | `daf_review_ai_ops_run()` | legacy_views | DAF |
| `/reset_tasks/select/` | `reset_tasks_select()` | views_task_reset_selective | Task |
| `/reset_tasks/` | `reset_all_tasks()` | views_task_reset_selective | Task |
| `/score_report/` | `score_report()` | legacy_views | Dashboard |
| `/tasks/<int:pk>/` | `TaskDetailView` | legacy_views | Task |
| `/newevidence/<int:taskid>` | `newevidence()` | legacy_views | Evidence |
| `/userevidence/` | `userevidence()` | legacy_views | Evidence |
| `/<id>/update` | `evidence_update_view()` | legacy_views | Evidence |
| `/getaveragetargets/` | `getaveragetargets()` | legacy_views | Task |
| `/newtask/` | `newtaskcreation()` | legacy_views | Task |
| `/gettasksuggestions/` | `gettasksuggestions()` | legacy_views | Task |
| `/verifytaskgroupexists/` | `verifytaskgroupexists()` | legacy_views | Task |
| `/task/<int:pk>/update/` | `TaskUpdateView` | legacy_views | Task |
| `/usertask/<int:pk>/update/` | `UsertaskUpdateView` | legacy_views | Task |
| `/task/<int:pk>/delete/` | `TaskDeleteView` | legacy_views | Task |
| `/newcategory/` | `TaskCategoryCreateView` | legacy_views | Task |
| `/newtaskgroup/` | `TaskGroupCreateView` | legacy_views | Task |
| `/contract/` | `contract()` | legacy_views | Contract |
| `/newclient/` | `clientassessment()` | legacy_views | Admin |
| `/clientassessment/` | `ClientAssessmentListView` | legacy_views | Admin |
| `/backgroundcheckadd/` | `add_background_info()` | legacy_views | Admin |
| `/backgroundchecklist/` | `BackgroundCheckListView` | legacy_views | Admin |
| `/new_grievance/` | `grievance_form()` | legacy_views | Grievance |
| `/grievance_file/<str:slug>` | `grievance_file()` | legacy_views | Grievance |
| `/update_grievance/<int:pk>/` | `GrievanceUpdateView` | legacy_views | Grievance |
| `/update_resolution/<int:pk>/` | `ResolutionUpdateView` | legacy_views | Grievance |
| `/update_assessment/<int:pk>/` | `AssessmentUpdateView` | legacy_views | Admin |
| `/assess/` | `assess()` | legacy_views | Admin |
| `/assessment/<str:user_type>` | `DSUListView` | legacy_views | Admin |
| `/update_dsu/<int:pk>/` | `AssessUpdateView` | legacy_views | Admin |
| `/session/` | `SessionCreateView` | legacy_views | Training |
| `/session/<int:pk>/` | `SessionUpdateView` | legacy_views | Training |
| `/sessions/<str:slug>` | `sessions()` | legacy_views | Training |
| `/usersession/<str:username>/` | `usersession()` | legacy_views | Training |
| `/newdepartment/` | `newdepartment()` | legacy_views | Admin |
| `/departments/` | `department()` | legacy_views | Admin |
| `/department/<int:pk>/` | `DepartmentUpdateView` | legacy_views | Admin |
| `/newmeeting/` | `newmeeting()` | legacy_views | Meeting |
| `/meetings/<str:status>` | `meetings()` | legacy_views | Meeting |
| `/meeting/<int:pk>/` | `MeetingUpdateView` | legacy_views | Meeting |
| `/requirement/new` | `newrequirement()` | legacy_views | Requirement |
| `/form_submission_view/` | `form_submission_view()` | legacy_views | Requirement |
| `/requirements/` | `requirements()` | legacy_views | Requirement |
| `/activerequirements/` | `active_requirements()` | legacy_views | Requirement |
| `/client_requirements/` | `requirements()` | legacy_views | Requirement |
| `/coda_requirements/` | `requirements()` | legacy_views | Requirement |
| `/dyc_requirements/` | `requirements()` | legacy_views | Requirement |
| `/reviewed/` | `requirements()` | legacy_views | Requirement |
| `/tested/` | `requirements()` | legacy_views | Requirement |
| `/requirement/<int:pk>/update/` | `RequirementUpdateView` | legacy_views | Requirement |
| `/requirement/<int:pk>/delete/` | `RequirementDeleteView` | legacy_views | Requirement |
| `/requirement/<int:pk>/` | `RequirementDetailView` | legacy_views | Requirement |
| `/requirementvideo/<int:detail_id>/` | `videolink()` | legacy_views | Requirement |
| `/justification/<int:pk>/` | `justification()` | legacy_views | Requirement |
| `/add_justification/` | `add_requirement_justification()` | legacy_views | Requirement |
| `/attendee-duration/` | `get_attendee_duration()` | legacy_views | Meeting |
| `/create_advertisement/` | `AdsCreateView` | legacy_views | Admin |
| `/advertisement/` | `AdsContent` | legacy_views | Admin |
| `/update_advertisement/<int:pk>/` | `AdsUpdateView` | legacy_views | Admin |
| `/upload/` | `assignment_upload()` | legacy_views | Assignment |
| `/assignments/` | `assignment_list()` | legacy_views | Assignment |
| `/assignments/<int:assignment_id>/` | `assignment_detail()` | legacy_views | Assignment |
| `/assignments/<int:assignment_id>/delete/` | `delete_assignment()` | legacy_views | Assignment |
| `/oauth/login/` | `oauth_login()` | legacy_views | OAuth |
| `/oauth/callback/` | `oauth_callback()` | legacy_views | OAuth |
| `/employee-groups/` | `employee_groups_view()` | views_employee_groups | Admin |
| `/employee-groups/update/<int:user_id>/` | `update_single_employee_group()` | views_employee_groups | Admin |
| `/employee-groups/bulk-update/` | `bulk_update_employee_groups()` | views_employee_groups | Admin |
| `/debug/daf-runtime/` | `daf_runtime_debug()` | views_debug | Debug |
| `/reports/performance/` | `performance_report()` | views_performance_report | Admin |
| `/meeting/launch/` | `launch_meeting()` | views_meeting_launch | Meeting |
| `/api/activity/summary/` | `activity_summary_api()` | views/api_views | API |
| `/api/activity/analytics/` | `activity_analytics_api()` | views/api_views | API |
| `/api/daf/summary/` | `daf_summary_api()` | views/api_views | API |
| `/api/task-assignment/suggestions/` | `get_intelligent_assignment_suggestions()` | views/task_assignment_views | API |
| `/meeting-links/review/` | `meeting_link_review_dashboard()` | views/meeting_review_views | API |
| `/api/meeting-links/<int:link_id>/approve/` | `approve_meeting_link()` | views/meeting_review_views | API |
| `/api/meeting-links/<int:link_id>/override/` | `override_meeting_link()` | views/meeting_review_views | API |
| `/api/meeting-links/<int:link_id>/reject/` | `reject_meeting_link()` | views/meeting_review_views | API |
| `/api/meeting-links/<int:link_id>/suggestions/` | `get_meeting_link_suggestions()` | views/meeting_review_views | API |
| `/api/budget/activity-totals/` | `budget_activity_totals_api()` | views/budget_integration_views | API |
| `/api/budget/evidence-validation/` | `budget_evidence_validation_api()` | views/budget_integration_views | API |
| `/api/forecast/activity/` | `activity_forecast_api()` | views/forecasting_views | API |
| `/api/forecast/budget/` | `budget_forecast_api()` | views/forecasting_views | API |
| `/api/trends/analysis/` | `trend_analysis_api()` | views/trend_analysis_views | API |
| `/api/trends/employee/<int:employee_id>/` | `employee_trend_analysis_api()` | views/trend_analysis_views | API |
| `/api/compliance/kpis/` | `compliance_kpis_api()` | views/compliance_kpi_views | API |
| `/api/compliance/history/` | `compliance_history_api()` | views/compliance_kpi_views | API |
| `/api/anomalies/detect/` | `anomaly_detection_api()` | views/anomaly_detection_views | API |
| `/analytics/` | `analytics_dashboard()` | views/analytics_dashboard_views | Dashboard |
| `/analytics/forecast/activity/` | `activity_forecast_dashboard()` | views/analytics_dashboard_views | Dashboard |
| `/analytics/trends/` | `trend_analysis_dashboard()` | views/analytics_dashboard_views | Dashboard |
| `/analytics/compliance/` | `compliance_dashboard()` | views/analytics_dashboard_views | Dashboard |
| `/analytics/anomalies/` | `anomaly_detection_dashboard()` | views/analytics_dashboard_views | Dashboard |
| `/enhanced-dashboard/` | `enhanced_task_dashboard()` | views_enhanced_dashboard | Dashboard |
| `/api/refresh-dashboard/` | `refresh_dashboard()` | views_enhanced_dashboard | Dashboard |
| `/api/export-my-data/` | `export_my_data()` | views_enhanced_dashboard | Dashboard |
| `/api/request-help/` | `request_help()` | views_enhanced_dashboard | Dashboard |
| `/api/report-issue/` | `report_issue()` | views_enhanced_dashboard | Dashboard |
| `/api/load-more-tasks/` | `load_more_tasks()` | views_enhanced_dashboard | Dashboard |
| `/api/submit-evidence/` | `submit_evidence()` | views_enhanced_dashboard | Dashboard |
| `/leaderboard/` | `task_leaderboard()` | views_enhanced_dashboard | Dashboard |
| `/task-history/` | `task_history_view()` | views_enhanced_dashboard | Dashboard |
| `/tier-analytics/` | `tier_analytics()` | views_enhanced_dashboard | Dashboard |
| `/button-testing/` | (lambda render) | - | Debug |

**Total: 123 URL patterns**

### H2. Model List by Domain

**Task Domain (5 models):**
- `Task` - Main task model
- `TaskHistory` - Historical task records
- `TaskLinks` - Task-evidence links
- `TaskCategory` - Task categories
- `TaskSubcategory` - Task subcategories

**DAF Domain (3 models):**
- `TaskReviewComment` - Manager review comments
- `TaskAIReviewSuggestion` - AI review suggestions
- `RequirementMatchCheck` - Requirement matching checks

**Requirement Domain (3 models):**
- `Requirement` - Requirements
- `ProcessJustification` - Requirement justifications
- `ProcessBreakdown` - Requirement breakdowns

**Activity Type Domain (2 models):**
- `ActivityType` - Canonical activity types
- `ActivityDefinition` - Activity definitions

**Training Domain (1 model):**
- `Training` - Training sessions (depends on professional_services)

**Contract Domain (1 model):**
- `BaseContract` - Base contract model

**Grievance Domain (2 models):**
- `Grievance` - Grievances
- `Conflict_Resolution` - Conflict resolutions

**Admin/HR Domain (4 models):**
- `Policy` - Company policies
- `Meetings` - Internal meetings
- `Advertisement` - Advertisements
- `SubCategory` - Department subcategories
- `Link` - Department links

**Employee Domain (2 models):**
- `EmployeeCareerState` - Career state tracking
- `PerformanceWarning` - Performance warnings

**Assignment Domain (1 model):**
- `Assignment` - Assignment uploads

**Total: 23 model classes**

### H3. Template List by Domain

**DAF Templates (10 files):**
- `daf/evidence_form.html`
- `daf/evidence_form_old.html` ⚠️ **Likely legacy**
- `daf/evidence_form_v2.html`
- `daf/payslip.html`
- `daf/payslip_modern.html` ⚠️ **May be unused**
- `daf/review.html`
- `daf/tasklist.html`
- `daf/usertasks.html` ⚠️ **Likely legacy**
- `daf/usertasks/employeetasks.html`
- `daf/usertasks/employeetasks_v2.html` ✅ **Current**
- `daf/usertasks/contractualtasks.html`

**Contract Templates (12 files):**
- `contracts/client_contract.html`
- `contracts/client_investment_contract.html`
- `contracts/contract_error.html`
- `contracts/employee_contract.html`
- `contracts/generalcontract_form.html`
- `contracts/generalcontract_formA.html` ⚠️ **May be duplicate**
- `contracts/my_investor_contract.html`
- `contracts/my_supportcontract_form.html`
- `contracts/my_trainingcontract_form.html`
- `contracts/read_employee_contract.html`
- `contracts/supportcontract_form.html`
- `contracts/trainingcontract_form.html`
- `contracts/loan/client_loan_contract.html`

**Department Templates (8+ files):**
- `departments/agenda/` (multiple files)
- `departments/agenda_backup/` ⚠️ **Backup - likely unused**
- `departments/hr/policy_form.html`

**Other Templates:**
- `background/background_form.html`, `background/backgroundchecklist.html`
- `assignment_detail.html`, `assignment_upload.html`
- `employee_groups.html`
- `task_confirm_delete.html`, `taskcategory_form.html`
- `insights/performance_dashboard.html`
- `components/` (reusable components)
- `doc_templates/` (document templates)
- `email/` (email templates)
- `reports/` (report templates)

**Total: 84 templates**

### H4. Suspected Unused/Dead Code List

**Views (need verification via grep):**
- `score_report()` - May be unused
- `companyagenda()` vs `companyagenda_improved()` - One may be legacy
- `tasklist()` vs `TaskListView` - Duplicate functionality?
- `filterbycategory()` - May be unused

**Templates (need verification via grep):**
- `evidence_form_old.html` - Likely legacy
- `payslip_modern.html` - May be unused if `payslip.html` is current
- `usertasks.html` - Likely legacy if `employeetasks_v2.html` is current
- `generalcontract_formA.html` - May be duplicate
- `agenda_backup/` directory - Likely unused

**Forms (need verification via grep):**
- `Optimized*` forms vs non-optimized forms - Need to verify which are used

**Evidence:**
- Use `grep -r "score_report" coda/management` to find references
- Use `grep -r "evidence_form_old" coda/management` to find template references
- Check URL patterns to see which views are actually wired
- Check git history for last usage

---

## Conclusion

The management app requires comprehensive refactoring to align with intended architecture and improve maintainability. The proposed incremental migration strategy minimizes risk while achieving significant organizational improvements.

**Recommended Next Steps:**
1. Review and approve this proposal
2. Start with Phase 0 (inventory + safety checks)
3. Proceed with views refactoring (Phase 1 + Phase 2C)
4. Then proceed with models/forms refactoring (Phase 2A, 2B)
5. Complete with Phase 3 (cleanup + documentation)

**Status:** ✅ Review Complete - Proposal Ready for Approval

