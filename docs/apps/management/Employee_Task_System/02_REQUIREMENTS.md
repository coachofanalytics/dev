# Employee Activity System (Management) – 02_REQUIREMENTS.md

## Purpose
This document defines all functional and non-functional requirements for the Employee Task Management System, including task assignment, tracking, evidence management, budget integration, and advanced analytics.

---

## Phase 0: DRY Foundation ✅ **COMPLETE**

### Functional Requirements
1. **Code Consolidation**
   - Consolidate scattered utility functions into `services/utilities_service.py`
   - Extract base model mixins to `models/base_models.py`
   - Extract base view classes to `views/base_views.py`
   - Create reusable UI components in `templates/management/components/`
   - Move legacy code to `deprecated/` directory (isolated from main codebase)

2. **Testing Foundation**
   - Provide smoke tests covering consolidated components
   - Verify no functionality broken by consolidation

### Acceptance Criteria
- ✅ All duplicated code removed
- ✅ Tests green for consolidated components
- ✅ Legacy code isolated under `deprecated/`
- ✅ Clean folder structure established
- ✅ Deployed to UAT (v800) - October 2025

---

## Phase 1: Data Pipeline & Evidence Automation ✅ **COMPLETE**

### 1.1 TaskHistory Data Pipeline

**Functional Requirements:**
- Ingest TaskHistory records from monthly task resets
- Ingest meeting metadata from ai_services (GoToMeeting integration)
- Normalize Department → Category → Task relationships
- Expose query/report endpoints for historical analysis
- Support filtering by department, category, employee, date range

**Data Requirements:**
- TaskHistory must include `daf_date` field for monthly filtering
- TaskHistory must be snapshot of Task state at reset time
- Support historical queries for budget calculations

**API Requirements:**
- `GET /management/api/activity/summary/` - Activity summary with window-based queries
- `GET /management/api/activity/analytics/` - Comprehensive analytics using TaskHistoryAnalyzer
- Support query parameters: `window` (month/quarter/year), `department_id`, `category_id`, `start_date`, `end_date`

### 1.2 Evidence Automation

**Functional Requirements:**
- Auto-link meetings to tasks based on:
  - Time proximity (meeting time vs task submission)
  - Participants (meeting attendees vs task employee)
  - Title/keywords (meeting topic vs task activity_name)
  - Historical patterns (past meeting-task links)
- Support multiple linking strategies:
  - Exact mapping (95% confidence) via `MeetingActivityMapping` model
  - Keyword matching (40-90% confidence)
  - Historical patterns (50-85% confidence)
  - Category matching (75% confidence)
- Auto-link threshold: ≥80% confidence auto-links immediately
- Manual review threshold: 60-79% confidence requires review
- Manual review/override UI for mismatches
- Track auto-link vs manual link statistics

**Evidence Requirements:**
- Evidence tracked via `TaskLinks` model
- Evidence types: documents, links, drive links, meeting recordings
- Evidence must be linked to Task (not TaskHistory)
- Support multiple employees uploading same link for group activities (BOG, BI Sessions, DAF Sessions, Project, web sessions)
- Prevent same user from uploading same link twice

**API Requirements:**
- `GET /management/meeting-links/review/` - Review dashboard UI
- `POST /management/api/meeting-links/<id>/approve/` - Approve auto-link
- `POST /management/api/meeting-links/<id>/override/` - Override with manual link
- `POST /management/api/meeting-links/<id>/reject/` - Reject link
- `GET /management/api/meeting-links/<id>/suggestions/` - Get alternative suggestions
- `GET /management/api/meeting-links/statistics/` - Auto-link rate tracking

### 1.3 AI-Assisted Task Assignment

**Functional Requirements:**
- Heuristic + ML ranking of task-employee mapping
- Confidence score output for each assignment suggestion
- Support rule-based fast path (before AI):
  - Department match (if task has department)
  - Category expertise (employees with history in same category)
  - Workload balance (current task count)
  - Availability (placeholder for now)
- Support AI-based assignment (for complex cases):
  - Performance prediction using `SimpleAIService`
  - Workload balancing
  - Skills matching
  - Team dynamics
- Support bulk assignment with workload balancing
- Support department-based assignment

**API Requirements:**
- `POST /management/api/task-assignment/suggestions/` - Get optimal employee assignments
- Request body: `category_id`, `activity_name`, `description`, `mxpoint`, optional `department_id`
- Response: Top 5 candidate suggestions with scores, workload analysis, confidence scores

**Success Metrics:**
- ≥80% auto-link rate for meetings (target achieved via tracking)
- 70% improvement in task-employee matching (measured via assignment accuracy)
- Manual review UI functional and accessible

---

## Phase 2: Budget Integration & Validation ✅ **COMPLETE**

### 2.1 Budget Integration APIs

**Functional Requirements:**
- Provide validated activity totals to Finance for budget estimation
- Expose APIs consumed by Budget services (monthly/quarterly/yearly windows)
- Support department and category filtering
- Include evidence counts and validation status
- Support compliance checking (33% threshold)

**API Requirements:**
- `GET /management/api/budget/activity-totals/`
  - Query parameters: `month`, `year`, `department_id`, `category_id`, `include_evidence`, `include_validation`
  - Returns: Activity totals, department/category breakdowns, evidence summary, validation status
  - Calculation: `Sum((point / mxpoint) × mxearning)` for earnings
- `GET /management/api/budget/evidence-validation/`
  - Query parameters: `month`, `year`, `department_id`, `category_id`, `min_confidence`
  - Returns: Evidence statistics, anomalies, approval trails, evidence type breakdown

**Integration Requirements:**
- Finance app consumes via `ManagementIntegrationService`
- Support both direct service calls (same Django project) and HTTP API calls (separate services)
- Error handling with retry logic and fallback
- Response caching (1 hour default, configurable)
- Data completeness validation
- Stale data detection (warn if >24 hours old)

**Success Metrics:**
- 60% reduction in budget variances (measured via Finance app)
- 75% accuracy in budget predictions (measured via forecast accuracy)
- Evidence validation ≥90% accuracy (measured via evidence coverage)

### 2.2 Validation & Auditing

**Functional Requirements:**
- Track evidence presence, anomalies, and approval trails
- Evidence completeness tracking:
  - High coverage: ≥80% of tasks have evidence
  - Medium coverage: 50-79% of tasks have evidence
  - Low coverage: <50% of tasks have evidence
  - Critical: 0% evidence (mandatory action required)
- Anomaly detection:
  - High points but no evidence
  - Low confidence auto-links
  - Tasks without evidence for high-value activities
- Approval trail tracking:
  - Who approved/rejected/overrode meeting links
  - When actions were taken
  - Confidence scores at time of action
- Evidence type breakdown: meetings, documents, other

**Compliance Requirements:**
- 33% compliance rule: `(total_points / total_max_points) × 100 ≥ 33`
- Point-based calculation (not task count-based)
- Handle employees who left company (include_inactive parameter)
- Identify trainees (0 tasks - not employees)
- Evidence mandatory for compliance (80% minimum coverage)

**Services Required:**
- `ComplianceCalculator` - Single source of truth for compliance calculation
- `EvidenceValidationService` - Evidence coverage validation
- `EvidenceReminderService` - Weekly email reminders (Friday 5 PM)
- `DataValidationService` - Data integrity checks

---

## Phase 3: Advanced Analytics ✅ **COMPLETE**

### 3.1 Forecasting

**Functional Requirements:**
- Activity trend forecasting (3+ months ahead)
- Budget prediction based on historical patterns
- Task completion rate forecasting
- Department capacity forecasting
- Confidence scoring (0-1 scale)
- Trend-based predictions with growth rate calculations

**API Requirements:**
- `GET /management/api/forecast/activity/`
  - Query parameters: `months_ahead` (1-12, default: 3), `department_id`, `category_id`, `historical_months` (3-24, default: 12)
  - Returns: Historical data, forecasted data, trends, confidence, insights
- `GET /management/api/forecast/budget/`
  - Query parameters: `months_ahead` (1-12, default: 3), `department_id`, `historical_months` (3-24, default: 12)
  - Returns: Total forecasted earnings, monthly forecasts, trends, confidence, insights

**Success Metrics:**
- 80% accuracy in 3-month forecasts (measured via confidence scores and actual vs predicted)

### 3.2 Trend Analysis

**Functional Requirements:**
- Historical trend analysis (12+ months)
- Department/category performance trends
- Employee performance trends
- Seasonal pattern detection
- Anomaly detection in trends
- Overall trend direction and strength

**API Requirements:**
- `GET /management/api/trends/analysis/`
  - Query parameters: `months_back` (1-24, default: 12), `department_id`, `category_id`, `employee_id`
  - Returns: Monthly trends, category/department trends, seasonal patterns, anomalies, overall trends
- `GET /management/api/trends/employee/<employee_id>/`
  - Query parameters: `months_back` (1-24, default: 12)
  - Returns: Employee-specific trend analysis, performance patterns, historical performance tracking

### 3.3 Compliance KPIs

**Functional Requirements:**
- Real-time compliance monitoring
- Department-level compliance breakdowns
- Historical compliance tracking
- Automated compliance alerts
- Compliance trend analysis
- At-risk employee identification

**API Requirements:**
- `GET /management/api/compliance/kpis/`
  - Query parameters: `department_id`, `month`, `year`
  - Returns: Overall metrics, employee details, department breakdowns, trends, alerts
- `GET /management/api/compliance/history/`
  - Query parameters: `months_back` (1-24, default: 12), `department_id`
  - Returns: Historical compliance trends, compliance rate tracking, trend direction analysis

### 3.4 Anomaly Detection

**Functional Requirements:**
- Automated anomaly detection
- Activity volume anomalies
- Performance anomalies
- Compliance anomalies
- Evidence coverage anomalies
- Severity classification (critical, high, medium, low)
- Automated alert generation

**API Requirements:**
- `GET /management/api/anomalies/detect/`
  - Query parameters: `month`, `year`, `department_id`
  - Returns: Detected anomalies classified by severity, summary statistics

**Success Metrics:**
- 95% process automation (measured via automation rate)
- Automated detection of anomalies with severity classification

---

## Phase 4: Task System Enhancements 📅 **PLANNED**

### 4.1 Task Cleaning & Classification

**Functional Requirements:**
- Add `department` ForeignKey to Task model (nullable initially, then required)
- Add `department` ForeignKey to TaskHistory model (for historical data)
- Enhance `TaskStandardizationService` with department classification:
  - Use employee's department as default
  - Add keyword-based department matching
  - Support activity name standardization
  - Auto-apply standardization on Task save (via Django signal)
- Support subcategory classification (optional, can add later)
- Activity name variation handling:
  - "BI session" vs "BI Session" vs "BI Sessions" → canonical "BI Session"
  - Auto-standardization dictionary
  - Confidence scores for mappings

**Classification Rules:**
- Department keywords mapping:
  - IT Department: developer, dev, coding, programming, website, web, software
  - HR Department: recruitment, hiring, interview, onboarding, hr
  - Finance Department: cashflow, budget, financial, payment, receipt
  - Marketing Department: marketing, social media, video, presentation, promotion
  - Management Department: meeting, pbr, sprint, planning, management, bog
  - Security Department: security, access, credentials
  - Health Department: health, medical, wellness

**Data Migration Requirements:**
- Backfill department from `employee.department` for existing Tasks
- Backfill department for TaskHistory records
- Update TaskResetService to copy department to TaskHistory
- Create ActivityType model (optional, for template-based task creation)

### 4.2 Enhanced Auto-Assignment

**Functional Requirements:**
- Enhance existing `IntelligentAssignmentService` with:
  - Rule-based assignment (fast path before AI)
  - Department-based assignment
  - Bulk assignment capability
  - Enhanced workload balancing
- Rule-based assignment priority:
  1. Department match (if task has department)
  2. Category expertise (employees with history in same category)
  3. Workload balance (current task count)
  4. Availability (placeholder for now)
- Fallback to AI if no clear rule match
- Manual override always available

### 4.3 Task Management Interface

**Functional Requirements:**
- Create `/task-management/` dashboard (similar to `/team-management/`)
- View tasks by department/category/employee
- Add/remove tasks (similar to team member add/remove)
- Bulk operations
- Auto-assign interface
- Search and filter capabilities

**URL Structure:**
- `/task-management/` - Dashboard
- `/task-management/department/<dept_id>/` - By department
- `/task-management/category/<cat_id>/` - By category
- `/task-management/employee/<user_id>/` - Employee tasks
- `/task-management/assign/<task_id>/<user_id>/` - Assign task
- `/task-management/remove/<task_id>/` - Remove task
- `/task-management/auto-assign/` - Bulk auto-assign

---

## Non-Functional Requirements

### Reliability
- Background jobs retried and monitored
- Service health checks via `AIHealthChecker`
- Transaction-based task reset with rollback on failure
- Admin notifications on critical failures
- Error recovery with exponential backoff for API calls

### Performance
- Queries optimized with indexes and `select_related`/`prefetch_related`
- Dashboard loads < 2s for 10k TaskHistory rows (with indexes)
- Database indexes on:
  - `TaskHistory`: `(daf_date, employee)`, `(daf_date, category)`, `(employee, daf_date)`
  - `Task`: `(employee, is_active, category)`, `(is_active, featured)`
  - `TaskLinks`: `(link)` if needed
- Response caching for API endpoints (1 hour default, configurable)
- Bulk operations performance: 100 tasks assignment < 10 seconds

### Observability
- Structured logs (replaced all `print()` statements)
- Admin reports for system health
- Metrics collection:
  - Task completion rates
  - API call counts
  - Error rates
  - Auto-link rates
- Automated alerts for:
  - Task reset failures
  - API failures
  - Low compliance rates
  - Missing evidence

### Security
- Role-based access control (staff/manager roles for write, read limited by department)
- PII protected
- Least-privilege for API keys
- External credentials housed in environment variables (never in repo)
- API authentication required for all endpoints

### Data Integrity
- Model validations:
  - `point ≤ mxpoint` (enforced in `clean()`)
  - `mxpoint > 0`
  - `point ≥ 0`
  - `mxearning ≥ 0`
  - `daf_date` is required (cannot be null)
  - `daf_date` cannot be in future
- Database constraints where appropriate
- Data validation service for integrity checks
- Orphaned record detection

### Usability
- User-friendly task management dashboard (not just admin interface)
- Clear error messages
- Real-time progress indicators
- Compliance status visibility
- Evidence reminder notifications (weekly emails, Friday 5 PM)
- Warning notifications 3 days before month-end

---

## Acceptance Criteria (Phase Checkpoints)

### Phase 0 ✅ **COMPLETE**
- ✅ All duplicated code removed
- ✅ Tests green for consolidated components
- ✅ Legacy placed under `deprecated/`
- ✅ Deployed to UAT (v800) - October 2025

### Phase 1 ✅ **COMPLETE**
- ✅ ≥80% auto-link rate for meetings (tracked via statistics endpoint)
- ✅ Manual review UI functional and accessible
- ✅ Basic analytics delivered (Activity Summary & Analytics APIs)
- ✅ Intelligent assignment API functional
- ✅ Meeting linking service with ML/heuristics implemented

### Phase 2 ✅ **COMPLETE**
- ✅ Budget API consumed by Finance (via `ManagementIntegrationService`)
- ✅ 60% variance reduction (measured via Finance app)
- ✅ Evidence validation ≥90% accuracy (tracked via evidence coverage metrics)
- ✅ Compliance validation (33% threshold) implemented
- ✅ Anomaly detection functional

### Phase 3 ✅ **COMPLETE**
- ✅ Forecast dashboards live (Activity & Budget Forecast APIs)
- ✅ Trend analysis functional (Trend Analysis & Employee Trend APIs)
- ✅ Compliance KPIs real-time monitoring (Compliance KPIs & History APIs)
- ✅ Anomaly detection automated (Anomaly Detection API)
- ✅ 95% process automation (measured via automation rate)

### Phase 4 📅 **PLANNED**
- [ ] Department field added to Task and TaskHistory models
- [ ] TaskStandardizationService enhanced with department classification
- [ ] Task management dashboard created
- [ ] Enhanced auto-assignment with rule-based fast path
- [ ] Bulk assignment capability
- [ ] Activity name auto-standardization on save

---

## Business Rules

### Task Earning Calculation
- **Formula:** `Earnings = (point / mxpoint) × mxearning × late_penalty`
- **Late Penalty:** 0.98 if late, else 1.0
- **Point Validation:** `point ≤ mxpoint`, `mxpoint > 0`, `point ≥ 0`, `mxearning ≥ 0`

### Compliance Rule
- **Formula:** `(total_points / total_max_points) × 100 ≥ 33`
- **Purpose:** Ensure employees meet minimum performance threshold
- **Effect:** Only compliant employees included in budget salaries
- **Calculation:** Point-based (not task count-based)
- **Location:** `ComplianceCalculator` service (single source of truth)

### Evidence Requirements
- **Minimum Coverage:** 80% of tasks must have evidence
- **Evidence Types:** Documents, links, drive links, meeting recordings
- **Evidence Tracking:** Via `TaskLinks` model (linked to Task, not TaskHistory)
- **Reminders:** Weekly email reminders (Friday 5 PM) for missing evidence
- **Validation:** Evidence validation affects compliance confidence

### Monthly Task Reset
- **Schedule:** Automated on 1st of each month at midnight (00:00)
- **Process:**
  1. Create TaskHistory records first (with `daf_date` calculation)
  2. Validate all records created
  3. Only then reset Task points to 0
  4. Update group/mxearning if needed (Group H, Group I logic)
  5. Log success/failure
  6. Send notification on failure
- **daf_date Logic:**
  - Automated reset on 1st: Last day of previous month
  - Manual reset: Same day of last month
- **Transaction Safety:** Uses `@transaction.atomic` for rollback on failure
- **Manual Override:** Support manual reset via `/management/reset_tasks/`

### Budget Integration
- **Data Source:** Last month's TaskHistory records (not current month)
- **Example:** December budget uses November's task completion data
- **Filtering:** Support department and category filtering
- **Validation:** Only compliant employees (≥33%) included in budget
- **Evidence:** Evidence coverage affects budget confidence

### Group Logic
- **Group H:** Increments `mxearning` after 30 hours: `mxearning += (total_point // 3)`
- **Group I:** Interns - no earning (`mxearning = 0`)
- **Group Changes:** Trigger `mxearning` increment via `increment_in_graduation_of_employee()`
- **Group Determination:** Based on total points in TaskHistory

### Evidence Upload Restrictions
- **Same User, Same Link:** Always blocked (prevents accidental duplicates)
- **Different User, Same Link:**
  - **Allowed for:** BOG, BI Sessions, DAF Sessions, Project, web sessions
  - **Blocked for:** All other activities
- **Temporary Override:** Can allow multiple employees to upload same link for all activities (temporary, for testing)

---

## Out of Scope (Current Phase)

### Not Included Now
- Financial transactions storage (owned by Finance app)
- Vendor-specific meeting transcription ML (we consume via ai_services)
- Real-time collaboration features
- Mobile app (web-only for now)
- Advanced reporting dashboards (beyond Phase 3 analytics)
- Multi-tenant support (single organization)

### Future Considerations
- TaskTemplate model for reusable task creation
- Subcategory classification (can add later if needed)
- Advanced workflow automation
- Integration with external project management tools
- Real-time notifications (beyond email reminders)

---

## Success Metrics Summary

| Phase | Metric | Target | Status |
|-------|--------|--------|--------|
| **Phase 1** | Auto-link rate | ≥80% | ✅ Tracked |
| **Phase 1** | Task-employee matching improvement | 70% | ✅ Measured |
| **Phase 2** | Budget variance reduction | 60% | ✅ Measured |
| **Phase 2** | Budget prediction accuracy | 75% | ✅ Measured |
| **Phase 2** | Evidence validation accuracy | ≥90% | ✅ Tracked |
| **Phase 3** | Forecast accuracy (3-month) | 80% | ✅ Measured |
| **Phase 3** | Process automation | ≥95% | ✅ Achieved |
| **Performance** | Dashboard load time | < 2s (10k rows) | ✅ Target |
| **Performance** | Bulk assignment (100 tasks) | < 10s | ✅ Target |
| **Compliance** | Evidence coverage | ≥80% | ✅ Enforced |
| **Compliance** | Compliance rate | ≥33% | ✅ Enforced |

---

## Integration Requirements

### Finance App Integration
- **Service:** `ManagementIntegrationService` in Finance app
- **APIs Consumed:**
  - Activity Totals API
  - Evidence Validation API
- **Integration Methods:**
  - Direct service calls (same Django project) - default
  - HTTP API calls (separate services) - fallback
- **Error Handling:** Retry logic with exponential backoff, response caching, data completeness validation

### AI Services Integration
- **GoToMeeting Integration:** Meeting metadata, recordings
- **AI Provider Layer:** `RealAIService`, configuration, health checker
- **Services Used:**
  - `SimpleAIService` for performance predictions
  - `AIConfigurationService` for AI configuration
  - `AIHealthChecker` for service monitoring

### Accounts App Integration
- **User Management:** `CustomerUser` (Employee) model
- **Department Model:** `Department` model (8 departments)
- **Task Groups:** `TaskGroups` model for employee grouping
- **User Profile:** `UserProfile` for additional employee data

---

**Last Updated:** December 2025  
**Status:** Phases 0-3 Complete, Phase 4 Planned
