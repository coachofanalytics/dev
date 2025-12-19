# Employee Activity System (Management) – 03_ARCHITECTURE.md

## Purpose
This document describes the system architecture, design patterns, integration points, data models, and key flows for the Employee Task Management System.

---

## High-Level Design

### Application Structure
```
management (app)
├─ models/
│  ├─ base_models.py              # Base domain model mixins
│  └─ [task_models.py, hr_models.py, ...]  # Split models (planned)
├─ views/
│  ├─ base_views.py               # Base view classes
│  ├─ dashboard_views.py          # Dashboard & home views
│  ├─ task_views.py               # Task CRUD & evidence views
│  ├─ requirement_views.py        # Requirements management
│  ├─ meeting_views.py             # Meeting management
│  ├─ contract_views.py           # Contract views
│  ├─ grievance_views.py          # Grievance & resolution
│  ├─ training_views.py            # Training & sessions
│  ├─ admin_views.py               # Background, assessment, policy
│  ├─ assignment_views.py          # Assignment upload
│  ├─ api_views.py                 # Phase 1: Activity Summary & Analytics APIs
│  ├─ task_assignment_views.py    # Phase 1: Intelligent Assignment API
│  ├─ meeting_review_views.py      # Phase 1: Meeting Link Review APIs
│  ├─ budget_integration_views.py # Phase 2: Budget Integration APIs
│  ├─ forecasting_views.py         # Phase 3: Forecasting APIs
│  ├─ trend_analysis_views.py      # Phase 3: Trend Analysis APIs
│  ├─ compliance_kpi_views.py     # Phase 3: Compliance KPI APIs
│  └─ anomaly_detection_views.py   # Phase 3: Anomaly Detection APIs
├─ services/                       # Business logic layer
│  ├─ base_service.py              # Base service class with error handling
│  ├─ utilities_service.py         # Shared utilities (DRY consolidation)
│  ├─ management_service.py        # Core management operations
│  ├─ task_standardization_service.py  # Task name standardization
│  ├─ intelligent_assignment_service.py # AI-based task assignment
│  ├─ ai_prediction_service.py     # ML models for performance prediction
│  ├─ taskhistory_analyzer.py      # Historical analysis
│  ├─ meeting_linking_service.py    # Phase 1: Meeting-to-task linking
│  ├─ compliance_calculator.py     # Unified compliance calculation
│  ├─ evidence_validation_service.py # Evidence coverage validation
│  ├─ evidence_reminder_service.py # Weekly evidence reminders
│  ├─ task_reset_service.py        # Transaction-based task reset
│  ├─ data_validation_service.py   # Data integrity checks
│  ├─ forecasting_service.py       # Phase 3: Forecasting
│  ├─ trend_analysis_service.py     # Phase 3: Trend analysis
│  ├─ compliance_kpi_service.py    # Phase 3: Compliance KPIs
│  └─ anomaly_detection_service.py  # Phase 3: Anomaly detection
├─ templates/management/
│  ├─ components/                  # Reusable UI components
│  │  └─ base_components.html
│  ├─ daf/                         # Task & evidence templates
│  ├─ departments/                 # Department-specific templates
│  ├─ contracts/                   # Contract templates
│  ├─ insights/                    # Analytics dashboards
│  └─ email/                       # Email templates
├─ management/commands/
│  ├─ consolidate_management_app.py # Phase 0: Consolidation command
│  ├─ analyze_task_history.py      # Task history analysis
│  ├─ validate_data_quality.py     # Data validation
│  └─ validate_task_data.py        # Task data validation
└─ tests/                          # Test suite
   ├─ 01_unit/                     # Unit tests
   ├─ 02_integration/              # Integration tests
   └─ 07_manual/                    # Manual tests
```

### Service Layer Architecture

**Design Pattern:** Service-Oriented Architecture (SOA)
- Business logic separated from views
- Services return DTOs (Data Transfer Objects), not ORM models
- Consistent error handling via `BaseService`
- Transaction management for data consistency
- Logging and monitoring built-in

**Service Hierarchy:**
```
BaseService (abstract)
├─ BaseManagementService
│  ├─ ManagementService
│  ├─ TaskStandardizationService
│  ├─ IntelligentAssignmentService
│  └─ TaskHistoryAnalyzer
├─ ComplianceCalculator
├─ EvidenceValidationService
├─ EvidenceReminderService
├─ TaskResetService
├─ DataValidationService
├─ ForecastingService
├─ TrendAnalysisService
├─ ComplianceKPIService
└─ AnomalyDetectionService
```

---

## Data Model

### Core Models

#### Task Model
```python
Task
├─ employee (ForeignKey → User)
├─ category (ForeignKey → TaskCategory)
├─ department (ForeignKey → Department)  # Phase 4: To be added
├─ activity_name (CharField)             # Standardized via TaskStandardizationService
├─ description (TextField)
├─ point (DecimalField)                  # Current completion (0 to mxpoint)
├─ mxpoint (DecimalField)                 # Maximum points required
├─ mxearning (DecimalField)               # Maximum earning potential
├─ duration (IntegerField)
├─ group (CharField)                     # Group title (e.g., "Group H")
├─ groupname (ForeignKey → TaskGroups)
├─ submission (DateField)
├─ is_active (BooleanField)
├─ featured (BooleanField)
└─ Properties:
   ├─ get_pay: (point / mxpoint) × mxearning × late_penalty
   ├─ deadline: submission + duration days
   └─ time_remaining: deadline - today
```

**Indexes:**
- `(employee, is_active, category)`
- `(is_active, featured)`
- `(category, is_active)`

**Validations:**
- `point ≤ mxpoint` (enforced in `clean()`)
- `mxpoint > 0`
- `point ≥ 0`
- `mxearning ≥ 0`

#### TaskHistory Model
```python
TaskHistory
├─ employee (ForeignKey → User)
├─ category (ForeignKey → TaskCategory)
├─ department (ForeignKey → Department)  # Phase 4: To be added
├─ activity_name (CharField)
├─ description (TextField)
├─ point (DecimalField)                  # Snapshot at reset time
├─ mxpoint (DecimalField)
├─ mxearning (DecimalField)
├─ daf_date (DateField)                  # Date for Daily Activity Form (monthly filtering)
├─ submission (DateField)                 # auto_now=True (updates on every save)
├─ created_at (DateTimeField)            # When TaskHistory record was created
└─ Properties:
   └─ submitted: submission date calculation
```

**Indexes:**
- `(daf_date, employee)` - Critical for monthly budget queries
- `(daf_date, category)` - For category-based analytics
- `(employee, daf_date)` - For employee history queries

**Purpose:**
- Historical snapshot of Task state at monthly reset
- Used for budget calculations (last month's data)
- Used for compliance tracking
- Used for analytics and forecasting

#### TaskCategory Model
```python
TaskCategory
├─ title (CharField)                      # PBR, Data Analysis, Website Development, etc.
├─ description (TextField)
└─ Relationships:
   ├─ tasks (reverse FK from Task)
   └─ taskhistory (reverse FK from TaskHistory)
```

**Current Categories:**
- Other (96 tasks - 32% - needs better classification)
- Department (72 tasks)
- PBR (62 tasks)
- Data Analysis (39 tasks)
- Website Development (34 tasks)
- Meetings (various)

#### TaskLinks Model (Evidence)
```python
TaskLinks
├─ task (ForeignKey → Task)               # Links to Task, not TaskHistory
├─ added_by (ForeignKey → User)
├─ link (URLField)                        # Evidence URL
├─ doc (FileField)                        # Document upload
├─ drive_link (URLField)                  # Google Drive link
├─ created_at (DateTimeField)
└─ Relationships:
   └─ Used for evidence validation and compliance tracking
```

**Evidence Types:**
- Meeting recordings (GoToMeeting links)
- Documents (file uploads)
- Drive links (Google Drive)
- Other links (external URLs)

**Restrictions:**
- Same user cannot upload same link twice (always blocked)
- Different users can upload same link for: BOG, BI Sessions, DAF Sessions, Project, web sessions
- Different users blocked for all other activities (unless temporary override)

#### TaskGroups Model
```python
TaskGroups
├─ name (CharField)                       # Group name (e.g., "Group H", "Group I")
└─ Relationships:
   └─ tasks (reverse FK from Task)
```

**Group Logic:**
- **Group H:** Contractual employees - increments `mxearning` after 30 hours: `mxearning += (total_point // 3)`
- **Group I:** Interns - no earning (`mxearning = 0`)
- **Other Groups:** Trigger `mxearning` increment via `increment_in_graduation_of_employee()` when group changes

### Supporting Models

#### Training Model
- Tracks employee training sessions
- Links to Department, FeaturedCategory
- Calculated expiry dates

#### Policy Model
- Company policies by department
- Version tracking

#### BaseContract Model
- Generic contract management
- Uses ContentType for polymorphic relationships

#### Requirement Model
- Requirements tracking
- Links to creator and assigned_to employees
- ProcessJustification and ProcessBreakdown relationships

#### Meetings Model
- Meeting management
- Links to Department, TaskCategory
- SubCategory and Link relationships

#### Grievance Model
- Employee grievance tracking
- Conflict_Resolution relationships

#### Assignment Model
- Student assignment tracking
- Drive file integration

---

## Integration Architecture

### 1. Finance App Integration

**Purpose:** Provide validated activity totals and evidence data for budget estimation

**Integration Service:** `ManagementIntegrationService` (in Finance app)
- Location: `coda/finance/services/management_integration_service.py`
- Methods:
  - `get_activity_totals()` - Get validated activity totals
  - `get_evidence_validation()` - Get evidence validation data
  - `get_validated_budget_data()` - Combined method

**Integration Methods:**
1. **Direct Service Calls** (Same Django Project) - Default
   - Uses Django's RequestFactory
   - No HTTP overhead
   - Faster and more efficient
2. **HTTP API Calls** (Separate Services) - Fallback
   - Uses `requests` library
   - Works when services deployed separately
   - Requires `requests` library

**APIs Exposed:**
- `GET /management/api/budget/activity-totals/`
- `GET /management/api/budget/evidence-validation/`

**Data Flow:**
```
Task (Current Month)
  ↓
TaskHistory (Month End Reset)
  ↓
Finance App Requests Last Month's Data
  ↓
Management API Queries TaskHistory (daf_date filter)
  ↓
Calculate Earnings: Sum((point / mxpoint) × mxearning)
  ↓
Check Compliance: (total_points / total_max_points) × 100 ≥ 33
  ↓
Return Validated Data to Finance
  ↓
Finance Includes Compliant Salaries in Budget
```

**Error Handling:**
- Retry logic with exponential backoff (1s, 2s, 4s delays)
- Maximum 3 retries
- No retry on auth/permission errors
- Response caching (1 hour default, configurable)
- Data completeness validation
- Stale data detection (warn if >24 hours old)

**Finance Views Integration:**
- Unified Budget Dashboard: `/finance/budget-dashboard/<company_slug>/?tab=overview`
- Management activity data automatically included in Overview tab
- No duplicate views created (follows reusability principle)

### 2. AI Services Integration

**Purpose:** Meeting metadata, AI predictions, health monitoring

**GoToMeeting Integration:**
- Meeting metadata collection
- Recording links
- Participant tracking
- Topic/keyword extraction

**AI Provider Layer:**
- `RealAIService` - AI service wrapper
- `AIConfigurationService` - AI configuration management
- `AIHealthChecker` - Service health monitoring

**Services Used:**
- `SimpleAIService` - Basic AI operations
- `AIPredictionService` - ML models for performance prediction
- `IntelligentAssignmentService` - AI-based task assignment

**Integration Flow:**
```
GoToMeeting → Meeting Metadata → Management.Meetings
  ↓
AI Service → Task-Meeting Linking → TaskLinks
  ↓
Health Checker → Monitoring → Logs/Admin
```

### 3. Accounts App Integration

**Models Used:**
- `CustomerUser` (Employee) - User management
- `Department` - 8 departments (HR, IT, Marketing, Finance, Security, Management, Health, Other)
- `TaskGroups` - Employee grouping
- `UserProfile` - Additional employee data

**Department Model:**
- 8 predefined departments
- **IMPORTANT:** Use existing Department model, do NOT create new departments
- Location: `coda/accounts/models.py:464`

### 4. Professional Services Integration

**Models Used:**
- `DSU` (Daily Stand-Up)
- `ClientAssessment`
- `BackgroundCheck`

---

## Key Flows

### 1. Task Lifecycle Flow

```
Task Creation
  ↓
Task Assignment (Intelligent Assignment Service)
  ↓
Employee Completes Task (point updates)
  ↓
Evidence Upload (TaskLinks)
  ↓
Month End → TaskHistory Created (with daf_date)
  ↓
Task Reset (point = 0, group/mxearning updated if needed)
  ↓
Finance Requests Last Month's Data
  ↓
Budget Calculation (earnings, compliance)
```

### 2. Meeting Auto-Linking Flow

```
GoToMeeting Recording Available
  ↓
MeetingLinkingService Analyzes:
  ├─ Exact Mapping (95% confidence) via MeetingActivityMapping
  ├─ Keyword Matching (40-90% confidence)
  ├─ Historical Patterns (50-85% confidence)
  └─ Category Matching (75% confidence)
  ↓
Confidence Score Calculated
  ↓
≥80% Confidence → Auto-Link Immediately
  ↓
60-79% Confidence → Require Manual Review
  ↓
<60% Confidence → Not Linked, Available for Manual Review
  ↓
Manual Review UI → Approve/Override/Reject
  ↓
TaskLinks Created
```

### 3. Monthly Budget Calculation Flow

```
Current Month: Employees Complete Tasks
  ↓
Month End: TaskHistory Records Created
  ├─ daf_date = Last Day of Previous Month (if reset on 1st)
  ├─ Snapshot of Task State (point, mxpoint, mxearning)
  └─ Department copied from Task (Phase 4)
  ↓
Next Month: Finance Requests Last Month's Data
  ↓
Management API Queries TaskHistory:
  ├─ Filter: daf_date__month=target_month, daf_date__year=target_year
  ├─ Filter: employee__is_active=True, employee__is_staff=True
  └─ Calculate: Sum((point / mxpoint) × mxearning)
  ↓
Compliance Check:
  ├─ Formula: (total_points / total_max_points) × 100 ≥ 33
  ├─ Only compliant employees included
  └─ Non-compliant employees excluded
  ↓
Evidence Validation:
  ├─ Check TaskLinks for matching Tasks
  ├─ Calculate evidence coverage
  └─ Flag anomalies (high points, no evidence)
  ↓
Return Validated Data to Finance
  ↓
Finance Includes Compliant Salaries in Budget
```

### 4. Task Reset Flow

```
Monthly Reset Triggered (1st of month, 00:00)
  ↓
TaskResetService.reset_tasks():
  ├─ Step 1: Create TaskHistory Records (bulk_create)
  │   ├─ Calculate daf_date (last day of previous month)
  │   ├─ Copy all Task fields to TaskHistory
  │   └─ Validate all records created
  ├─ Step 2: Process Each Employee
  │   ├─ Get all current tasks for employee
  │   ├─ Get TaskHistory for this employee
  │   ├─ Calculate group level (employee_group_level)
  │   ├─ Update group/mxearning if needed:
  │   │   ├─ Group H: Increment mxearning if total_point > 30
  │   │   ├─ Group I: Set mxearning = 0
  │   │   └─ Group Changed: Increment mxearning
  │   └─ Reset point = 0
  ├─ Step 3: Bulk Update Tasks
  └─ Step 4: Log Success/Failure
  ↓
Transaction Safety:
  ├─ @transaction.atomic decorator
  ├─ Rollback on any failure
  └─ Admin notification on failure
  ↓
Manual Override Available:
  └─ TaskResetService.manual_reset() for edge cases
```

### 5. Evidence Validation Flow

```
Employee Completes Task
  ↓
Evidence Upload (TaskLinks)
  ↓
EvidenceValidationService.get_evidence_coverage():
  ├─ Get all tasks for employee (month/year)
  ├─ Get TaskLinks for matching Tasks
  ├─ Calculate coverage: (tasks_with_evidence / total_tasks) × 100
  └─ Classify: High (≥80%), Medium (50-79%), Low (<50%), Critical (0%)
  ↓
Weekly Reminder Check (Friday 5 PM):
  ├─ EvidenceReminderService.send_weekly_reminders()
  ├─ Find employees with <80% coverage
  ├─ Generate personalized messages
  └─ Send email reminders
  ↓
Compliance Check:
  ├─ Evidence coverage affects compliance confidence
  ├─ High coverage: High confidence
  ├─ Low coverage: Low confidence
  └─ Critical: Mandatory action required
```

---

## API Architecture

### API Response Format

**Standard JSON Envelope:**
```json
{
  "data": {
    // Response data
  },
  "meta": {
    "month": 10,
    "year": 2025,
    "generated_at": "2025-12-01T10:00:00Z",
    "source": "direct_call" | "http_api"
  },
  "errors": []
}
```

**Error Response:**
```json
{
  "success": false,
  "data": {},
  "meta": {},
  "errors": ["Error message here"]
}
```

### API Endpoints

#### Phase 1 APIs
- `GET /management/api/activity/summary/` - Activity summary
- `GET /management/api/activity/analytics/` - Comprehensive analytics
- `POST /management/api/task-assignment/suggestions/` - Intelligent assignment
- `GET /management/meeting-links/review/` - Review dashboard
- `POST /management/api/meeting-links/<id>/approve/` - Approve link
- `POST /management/api/meeting-links/<id>/override/` - Override link
- `POST /management/api/meeting-links/<id>/reject/` - Reject link
- `GET /management/api/meeting-links/<id>/suggestions/` - Get suggestions
- `GET /management/api/meeting-links/statistics/` - Auto-link statistics

#### Phase 2 APIs
- `GET /management/api/budget/activity-totals/` - Activity totals
- `GET /management/api/budget/evidence-validation/` - Evidence validation

#### Phase 3 APIs
- `GET /management/api/forecast/activity/` - Activity forecast
- `GET /management/api/forecast/budget/` - Budget forecast
- `GET /management/api/trends/analysis/` - Trend analysis
- `GET /management/api/trends/employee/<employee_id>/` - Employee trends
- `GET /management/api/compliance/kpis/` - Compliance KPIs
- `GET /management/api/compliance/history/` - Compliance history
- `GET /management/api/anomalies/detect/` - Anomaly detection

---

## Navigation Architecture

### User Navigation Flow

```
Main Dashboard (/dashboard)
  ↓
Enhanced Dashboard (/management/enhanced-dashboard/)
  ├─ User tier status and progress
  ├─ Monthly statistics
  ├─ Recent tasks
  └─ Phase 3 Analytics Navigation Section:
      ├─ 📈 Activity Forecast
      ├─ 💰 Budget Forecast
      ├─ 📊 Historical Trends
      ├─ 👤 My Performance Trends
      ├─ 📋 Real-time Compliance KPIs
      ├─ 📜 Compliance History
      ├─ 🔍 Detect Anomalies
      └─ 🎯 All Analytics Dashboard
  ↓
Analytics Hub (/management/analytics/)
  ├─ Quick overview of all analytics
  └─ Navigation buttons to all features
  ↓
Specific Analytics Dashboards:
  ├─ Activity Forecast Dashboard (/management/analytics/forecast/activity/)
  ├─ Trend Analysis Dashboard (/management/analytics/trends/)
  ├─ Compliance Dashboard (/management/analytics/compliance/)
  └─ Anomaly Detection Dashboard (/management/analytics/anomalies/)
```

---

## Boundaries & Contracts

### Service Layer Contracts
- **Services return DTOs** (Data Transfer Objects), not ORM models
- **No cross-app ORM leakage** - Services don't expose internal models
- **Consistent error handling** via `BaseService`
- **Transaction management** for data consistency
- **Logging and monitoring** built-in

### API Contracts
- **Stable JSON envelopes** with `data`, `meta`, `errors`
- **Versioning** via URL paths (e.g., `/api/v1/`)
- **Authentication required** for all endpoints
- **Rate limiting** (future consideration)
- **Documentation** via OpenAPI/Swagger (future consideration)

### Database Contracts
- **Foreign keys** enforce referential integrity
- **Indexes** for performance
- **Constraints** for data validation
- **Migrations** for schema changes

---

## Performance Considerations

### Query Optimization
- **Use `select_related`** for ForeignKey relationships
- **Use `prefetch_related`** for ManyToMany and reverse ForeignKey
- **Add indexes** on frequently queried fields:
  - `TaskHistory`: `(daf_date, employee)`, `(daf_date, category)`, `(employee, daf_date)`
  - `Task`: `(employee, is_active, category)`, `(is_active, featured)`
  - `TaskLinks`: `(link)` if needed for duplicate checks

### Caching Strategy
- **Response caching** for API endpoints (1 hour default, configurable)
- **Cache key** based on function name and parameters
- **Only cache successful responses**
- **Cache invalidation** on data updates

### Performance Targets
- **Dashboard load time:** < 2s for 10k TaskHistory rows
- **Bulk operations:** 100 tasks assignment < 10 seconds
- **API response time:** < 500ms for standard queries
- **Database queries:** Minimize N+1 queries

### Bulk Operations
- **Bulk create** for TaskHistory records (monthly reset)
- **Bulk update** for Task records (point reset)
- **Transaction safety** for atomic operations

---

## Security Architecture

### Authentication & Authorization
- **Role-based access control:**
  - Staff/manager roles for write operations
  - Read limited by department (where applicable)
  - API authentication required for all endpoints

### Data Protection
- **PII protected** - Employee data access controlled
- **Least-privilege** for API keys
- **External credentials** housed in environment variables (never in repo)
- **Input validation** on all user inputs
- **SQL injection prevention** via Django ORM

### API Security
- **Authentication required** for all endpoints
- **Rate limiting** (future consideration)
- **CORS configuration** for cross-origin requests
- **HTTPS only** in production

---

## Error Handling Architecture

### Service Layer Error Handling
- **BaseService** provides consistent error handling
- **Try-catch blocks** with proper exception handling
- **Logging** for all errors
- **Admin notifications** for critical failures

### API Error Handling
- **Retry logic** with exponential backoff (1s, 2s, 4s delays)
- **Maximum 3 retries** (no retry on auth/permission errors)
- **Error responses** in standard JSON format
- **Error logging** for debugging

### Transaction Safety
- **@transaction.atomic** decorator for critical operations
- **Rollback on failure** for data consistency
- **Validation before commit** to prevent bad data

---

## Monitoring & Observability

### Logging
- **Structured logs** (replaced all `print()` statements)
- **Log levels:** DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Log rotation** to prevent disk space issues
- **Centralized logging** (future consideration)

### Metrics Collection
- **Task completion rates**
- **API call counts**
- **Error rates**
- **Auto-link rates**
- **Performance metrics**

### Health Checks
- **Service health checks** via `AIHealthChecker`
- **Database connectivity** checks
- **API endpoint health** checks
- **Background job status** monitoring

### Alerts
- **Automated alerts** for:
  - Task reset failures
  - API failures
  - Low compliance rates
  - Missing evidence
  - Anomaly detection

---

## Deployment Architecture

### Environment Configuration
- **Development:** Local Django server
- **UAT:** Heroku staging environment
- **Production:** Heroku production environment

### Background Jobs
- **Celery** for asynchronous tasks
- **Celery Beat** for scheduled tasks:
  - Monthly task reset (1st of month, 00:00)
  - Weekly evidence reminders (Friday, 17:00)
- **Task queue** for long-running operations

### Database
- **PostgreSQL** for production
- **Migrations** for schema changes
- **Backups** scheduled regularly
- **Cloning** for local development (via scripts)

---

## Future Architecture Considerations

### Phase 4 Enhancements
- **Department field** on Task and TaskHistory models
- **TaskStandardizationService** enhancement with department classification
- **Task management dashboard** (similar to team-management)
- **Enhanced auto-assignment** with rule-based fast path
- **ActivityType model** for template-based task creation (optional)

### Scalability Considerations
- **Horizontal scaling** via load balancers
- **Database replication** for read-heavy workloads
- **Caching layer** (Redis) for frequently accessed data
- **CDN** for static assets

### Microservices Consideration
- **Current:** Monolithic Django app
- **Future:** Could split into microservices:
  - Task Management Service
  - Analytics Service
  - Evidence Service
  - Assignment Service

---

**Last Updated:** December 2025  
**Status:** Phases 0-3 Complete, Phase 4 Planned
