# CODA Django Codebase – Full-System Architectural Analysis for AI Integration

**Generated:** December 2025  
**Purpose:** AI Integration Blueprint for CODA V1  
**Scope:** Complete architectural analysis of ai_services, task system, DAF generation, Pay & Compliance, and all AI integration points

---

## SECTION 1 — High-Level Architecture

### Major Apps and Their Purposes

CODA is structured as a Django monolith with 14+ apps organized by domain:

1. **`ai_services`** – AI integration, meeting services, OAuth token management
   - Handles GoToMeeting integration, meeting-to-task linking
   - Provides AI service facade for centralized AI operations
   - Contains diaspora analysis platform models

2. **`management`** – Employee Task System (DAF)
   - Core task tracking, TaskHistory snapshots
   - Pay calculation, compliance tracking
   - Career ladder management, performance metrics
   - DAF summary generation

3. **`finance`** – Budget, loans, payments, transactions
   - PayslipConfig for per-employee pay rules
   - Loan management and calculations
   - Budget integration with TaskHistory

4. **`accounts`** – User management, authentication, profiles
   - CustomerUser, Department models
   - TaskGroups for employee leveling
   - UserProfile with pay-related fields

5. **`professional_services`** – DSU, client assessments, background checks
   - FeaturedCategory, FeaturedSubCategory, FeaturedActivity
   - Used by management app for activity definitions

6. **`investing`** – Trading accounts, positions, signals, managed trading
   - Position scoring and ranking services
   - AI analysis for trade outcomes
   - Performance reporting

7. **`main`** – Core utilities, services, company info
   - Legacy AI utilities (being migrated to ai_services)
   - Chatbot integration
   - Service definitions

8. **`shared_core`** – Infrastructure layer
   - Base model mixins (TimeStampedModel)
   - User models re-exports
   - Service interfaces (AIServiceInterface, MeetingServiceInterface)
   - NoOp adapters for testing

### Cross-App Data Flows

**Task → Pay Flow:**
```
Task (current month) 
  → TaskHistory (monthly snapshot via TaskResetService)
    → PayCalculationService (uses EarningsEngine)
      → ReleaseEngine (compliance check, stipend calculation)
        → DAFSummaryService (aggregates for UI)
```

**Meeting → Task Linking:**
```
ai_services.Meeting (GoToMeeting data)
  → MeetingLinkingService (multi-strategy matcher)
    → Task (auto-created with evidence links)
```

**Evidence Validation:**
```
TaskLinks (evidence docs/URLs)
  → EvidenceValidationService
    → ChecklistEvaluationService (quality scoring)
      → PerformanceMetricsService (aggregate metrics)
```

### Where Business Rules Live

- **Pay Rules:** `management/services/pay_calculation_service.py`, `release_engine.py`
- **Compliance Rules:** `management/services/compliance_calculator.py` (33% rule)
- **Career Ladder Rules:** `management/services/career_level_service.py`, `config/pay_policy.py`
- **Activity Definitions:** `management/models.py` (ActivityType), `config/activity_checklists.py`
- **Stipend/Safety Net:** `release_engine.py` (Group B, tenured employees)

### Where Presentation Logic Lives

- **DAF UI:** `management/services/daf_summary_service.py` (aggregates all data)
- **Payslip Views:** `management/views.py` (payslip view uses PayCalculationService)
- **Analytics Dashboards:** `management/views/analytics_dashboard_views.py`
- **API Endpoints:** `management/views/api_views.py` (activity_summary_api, daf_summary_api)

---

## SECTION 2 — ai_services Deep Analysis

### Existing Abstractions

**1. AIServiceFacade (`ai_services/services/ai_service_facade.py`)**
- Centralized facade consolidating AI operations
- Replaces duplicate implementations in `main/utils.py`, `main/views.py`
- Provides: `generate_response()`, `generate_chatbot_response()`, `parse_user_query()`
- Uses: `RealAIService`, `AIAnalyticsService`, `AIConfigurationService`

**2. RealAIService (`ai_services/ai_integration_service.py`)**
- Multi-provider support (OpenAI GPT-4, GPT-3.5, Claude-3)
- Fallback chain: GPT-4 → GPT-3.5 → Claude-3 → Local offline
- Configuration via `AIModelConfiguration` model (database-driven)
- Automatic fallback to realistic dummy data when AI unavailable

**3. AIServiceInterface (`shared_core/interfaces/ai_service.py`)**
- Abstract base class defining AI service contract
- Implemented by: `NoOpAIServiceAdapter` (testing), future real implementations
- Methods: `generate_response()`, `extract_keywords()`, `get_health_status()`

### How Prompts Are Currently Built

**Current Pattern (Scattered):**
```python
# main/utils.py - openai_user_message()
context_str = (
    f"Question: {openai_context.expert_question}. "
    f"Topic: {openai_context.topic}. "
    f"Domain/Role: {openai_context.role}. "
    f"Description: {openai_context.context_description}. "
    f"Clarification: {openai_context.clarification_description}. "
    f"Words: {openai_context.words}."
)

# ai_integration_service.py - _build_analysis_prompt()
prompts = {
    'remittance_analysis': f"""
    Analyze this remittance data for a Kenyan diaspora member:
    Amount: ${input_data.get('amount', 'N/A')}
    ...
    """
}
```

**Issues:**
- Hard-coded f-strings scattered across codebase
- No template registry
- No versioning or A/B testing capability
- Mixed prompt styles (some structured, some free-form)

### How Responses Are Parsed

**Current Parsing (Basic):**
```python
# ai_integration_service.py - _parse_ai_response()
lines = content.split('\n')
assessment_score = 7.0  # Default
recommendations = []
# Simple regex extraction for scores
# Section-based parsing for recommendations/risks
```

**Weaknesses:**
- No structured output (JSON schema) enforcement
- Regex-based parsing is brittle
- No validation of extracted data
- Default fallbacks mask parsing failures

### Attempts at Structured Output

**Existing:**
- `DiasporaAnalysisData` model stores `ai_prediction` as JSONField
- `AIModelConfiguration` allows model selection
- No Pydantic/JSON schema validation

**Missing:**
- No output schema registry
- No validation layer
- No type-safe response models

### Prompt Engineering

**Current State:**
- System prompts in `_get_system_prompt()` are hard-coded strings
- No prompt versioning
- No prompt testing framework
- No chain-of-thought prompting for complex reasoning

**Example System Prompt:**
```python
f"""
You are an expert AI analyst specializing in {analysis_type.replace('_', ' ')} for the Kenyan diaspora.
Provide detailed, actionable insights with:
- Assessment scores (1-10 scale)
- Specific recommendations
- Risk factors and mitigation strategies
- Clear next steps
"""
```

### Hidden Assumptions

1. **API Keys:** Assumes `OPENAI_API_KEY` in environment, no key rotation logic
2. **Model Availability:** Assumes GPT-4 is always primary, no health checks before calling
3. **Response Format:** Assumes free-form text responses, no structured JSON mode
4. **Caching:** `AIServiceFacade` caches responses for 1 hour, no cache invalidation strategy
5. **Error Handling:** Falls back to dummy data silently, no alerting

### Coupling with Business Logic

**Tight Coupling Points:**
- `main/utils.py` directly imports `ai_service_facade` (circular dependency risk)
- `generate_openai_description()` in `main/views.py` hard-codes ClientAssessment field names
- No dependency injection, services instantiate AI services directly

### Areas Violating DRY

1. **Duplicate AI Functions:**
   - `main/utils.py`: `generate_chatbot_response()`, `openai_user_message()`
   - `main/utilities/ai_utils.py`: `AIUtils.generate_chatbot_response()`
   - `ai_services/services/ai_service_facade.py`: Same functions (consolidation in progress)

2. **Repeated Prompt Construction:**
   - Multiple places build similar prompts for different analysis types
   - No shared prompt template library

3. **Response Parsing:**
   - Each analysis type has custom parsing logic
   - No unified parser abstraction

---

## SECTION 3 — All Points Where AI Is Called or Will Be Needed

### Current AI Call Points

**1. Chatbot/General AI (`main/views.py`, `main/utils.py`)**
- `get_respos()` – General chatbot responses
- `generate_chatbot_response()` – OpenAI chat completions
- `generate_openai_description()` – User profile descriptions from ClientAssessment

**2. Diaspora Analysis Platform (`ai_services/ai_integration_service.py`)**
- `get_prediction()` – Remittance, trade facilitation, investment, education, healthcare analysis
- Uses `_build_analysis_prompt()` with type-specific prompts

**3. Investing App (`investing/services/position_history_collector.py`)**
- `_generate_ai_analysis()` – Post-trade analysis (currently template-based, TODO: integrate RealAIService)
- Generates explanations for why positions won/lost

**4. Database Query AI (`main/utils.py`)**
- `langchainModelForAnswer()` – SQL agent for database queries
- Uses LangChain SQLDatabaseToolkit

### Places That Should Use AI (Not Yet Implemented)

**1. Task System:**
- **IntelligentAssignmentService** – Currently uses pattern matching, should use AI for skill-based assignment
- **TaskStandardizationService** – Activity name standardization (currently rule-based)
- **Evidence Validation** – Should use AI to validate evidence quality (photos, documents)

**2. DAF Generation:**
- **DAFSummaryService** – Should generate personalized coaching messages
- **Focus/Recommendations** – Currently template-based, should be AI-generated
- **Activity Explanations** – Why tasks were assigned, what to focus on

**3. Pay & Compliance:**
- **Pay Explanation Text** – Currently hard-coded in `release_engine.py._build_explanations()`
- **Compliance Coaching** – Should generate personalized messages for non-compliant employees
- **Stipend Reasoning** – Explain why stipend is 0% vs 50% vs 100%

**4. Career Progression:**
- **CareerLevelService** – Should generate progress explanations
- **Promotion Recommendations** – AI-powered promotion readiness assessment
- **Blockers Analysis** – Explain what's blocking promotion

**5. Quality & Evidence:**
- **ChecklistEvaluationService** – Should use AI to evaluate evidence quality
- **Evidence Reminder Messages** – Personalized reminders based on task type
- **Quality Feedback** – Explain quality scores to employees

### Places That Could Benefit from Validation or Coaching

**1. Employee-Facing Text:**
- All explanation strings in `release_engine.py._build_explanations()`
- DAF focus recommendations in `daf_summary_service.py._get_focus_data()`
- Quality feedback messages

**2. Manager-Facing Reports:**
- Compliance dashboard explanations
- Anomaly detection alerts
- Forecasting insights

### Places That Should Be Transformed into Templates or Chains

**1. Prompt Templates Needed:**
- Task assignment prompts (activity type, employee skills, workload)
- DAF summary generation prompts (career state, pay, metrics)
- Pay explanation prompts (compliance, stipend, safety net)
- Quality feedback prompts (checklist scores, evidence gaps)
- Career progression prompts (blockers, next steps)

**2. Chain-of-Thought Needed:**
- Pay calculation reasoning (why earned vs released differs)
- Compliance gate decisions (33% rule evaluation)
- Stipend calculation (compliance factor, quality cap)
- Career level progression (months at level, blockers)

---

## SECTION 4 — Data Models That AI Must Understand

### Task System Models

**Task (`management/models.py`)**
- Fields for AI: `activity_name`, `description`, `point`, `mxpoint`, `mxearning`, `employee`, `category`, `activity_type`, `submission`, `is_active`
- AI needs: Activity type context, completion status, pay calculation inputs

**TaskHistory (`management/models.py`)**
- Fields for AI: `daf_date`, `point`, `mxpoint`, `mxearning`, `activity_name`, `employee`, `category`
- AI needs: Historical patterns, monthly snapshots for compliance, pay calculations

**ActivityType (`management/models.py`)**
- Fields for AI: `name`, `slug`, `description`, `unit_type`, `unit_rate`, `monthly_target_units`, `points_per_unit`, `is_billable`, `department`, `category`
- AI needs: Canonical activity definitions, pay calculation rules, target setting

**TaskLinks (`management/models.py`)**
- Fields for AI: `link_name`, `description`, `doc`, `link`, `drive_link`, `created_at`
- AI needs: Evidence quality assessment, completeness checking

### Pay & Compliance Models

**EmployeeCareerState (`management/models.py`)**
- Fields for AI: `group` (A/B/C), `current_level_code`, `is_tenured`, `date_at_level`
- AI needs: Career progression context, stipend eligibility, safety net eligibility

**PayslipConfig (`finance/models.py`)**
- Fields for AI: Loan %, holiday pay rules, EOM bonus rules, other deductions
- AI needs: Per-employee pay policy, explanation generation

### Meeting Models

**Meeting (`ai_services/models.py`)**
- Fields for AI: `topic`, `meeting_type`, `start_time`, `duration_minutes`, `recording_url`
- AI needs: Meeting-to-task linking, attendance validation

**MeetingAttendee (`ai_services/models.py`)**
- Fields for AI: `attendee_email`, `duration_minutes`, `is_organizer`
- AI needs: Attendance quality, task point eligibility

### Performance Models

**PerformanceMetrics (computed, not stored)**
- AI needs: `compliance`, `checklist_quality_score`, `attendance_days`, `evidence_coverage`
- Used for: Stipend calculation, quality gates, coaching messages

---

## SECTION 5 — Task System Integration Points

### Where Activity Types Are Referenced

**1. Task Model (`management/models.py:626`)**
- `Task.get_pay()` prefers `activity_type` if set, falls back to legacy `mxpoint/mxearning`
- `Task.activity_type` ForeignKey to `ActivityType`

**2. TaskStandardizationService (`management/services/task_standardization_service.py`)**
- Standardizes activity names, should map to ActivityType
- Currently rule-based, should use AI for fuzzy matching

**3. ActivityTypeService (`management/services/activity_type_service.py`)**
- Manages ActivityType CRUD
- Should provide AI with activity definitions for prompt context

### Where Employee Free-Text Input Goes

**1. Task.description (`management/models.py:524`)**
- Employee-entered task description
- Default: "Add description on this activity"
- AI needs: Extract activity type, validate completeness

**2. TaskLinks.description (`management/models.py:791`)**
- Evidence description
- AI needs: Validate evidence relevance, quality assessment

**3. Task.activity_name (`management/models.py:518`)**
- Activity name (may be free-text before standardization)
- AI needs: Standardize to ActivityType, detect duplicates

### Where Evidence Is Validated

**1. EvidenceValidationService (`management/services/evidence_validation_service.py`)**
- Validates TaskLinks completeness
- Should use AI to assess evidence quality (photos, documents)

**2. ChecklistEvaluationService (`management/services/checklist_evaluation_service.py`)**
- Evaluates checklist completion per activity type
- Uses `config/activity_checklists.py` for checklist definitions
- Should use AI to assess evidence quality beyond checklist items

**3. MeetingLinkingService (`management/services/meeting_linking_service.py`)**
- Links meetings to tasks using date, attendees, titles
- Should use AI for semantic matching (topic similarity)

### Weaknesses in Current Activity Model

**1. No ActivityDefinition Schema Registry:**
- ActivityType exists but no structured schema for AI prompts
- No validation rules, quality criteria, or coaching templates per activity

**2. Weak Standardization:**
- TaskStandardizationService is rule-based, not AI-powered
- Activity names vary (e.g., "one on one", "one-on-one", "1-on-1")

**3. No Activity-Specific Prompts:**
- All activities use generic prompts
- No activity-specific coaching or quality feedback

### Gaps Where ActivityDefinition Schema Must Plug In

**1. Prompt Template Registry:**
- Need: `ActivityDefinition.prompt_template` for AI-generated task assignments
- Need: `ActivityDefinition.quality_criteria` for AI quality assessment
- Need: `ActivityDefinition.coaching_template` for personalized feedback

**2. Validation Rules:**
- Need: `ActivityDefinition.evidence_requirements` (what evidence is required)
- Need: `ActivityDefinition.quality_thresholds` (minimum quality scores)

**3. AI Context:**
- Need: `ActivityDefinition.ai_context` (description for AI prompts)
- Need: `ActivityDefinition.skill_requirements` (for intelligent assignment)

---

## SECTION 6 — DAF Integration Points

### Services That Summarize Behavior

**1. DAFSummaryService (`management/services/daf_summary_service.py`)**
- Aggregates pay, career, quality, performance into single summary
- Uses: PayCalculationService, CareerLevelService, PerformanceMetricsService, ChecklistEvaluationService
- **AI Gap:** Focus/recommendations are template-based, should be AI-generated

**2. TaskHistoryAnalyzer (`management/services/taskhistory_analyzer.py`)**
- Analyzes historical task patterns
- **AI Gap:** Should use AI to detect patterns, predict future performance

**3. PerformanceMetricsService (`management/services/performance_metrics_service.py`)**
- Computes compliance, quality, attendance metrics
- **AI Gap:** Should generate personalized coaching based on metrics

### Functions That Assemble Monthly/Weekly Views

**1. `daf_summary_service._get_activities_data()`**
- Assembles activity list with quality scores
- **AI Gap:** Should generate activity-specific explanations

**2. `daf_summary_service._get_focus_data()`**
- Generates focus/recommendations (currently template-based)
- **AI Gap:** Should be AI-generated based on career state, metrics, pay

**3. `activity_summary_api()` (`management/views/api_views.py`)**
- Returns activity summary with window-based queries
- **AI Gap:** Should include AI-generated insights per window

### Places Where Explanation Text Is Generated

**1. ReleaseEngine._build_explanations() (`management/services/release_engine.py:422`)**
- Hard-coded explanation strings for:
  - Compliance status
  - Stipend amount/percentage
  - Safety net top-up
  - Locked amount
- **AI Gap:** Should be AI-generated, personalized, multilingual (Swahili for Group B)

**2. DAFSummaryService._get_focus_data() (`management/services/daf_summary_service.py:250`)**
- Template-based focus messages:
  - "Focus on completing more tasks this month"
  - "Improve your quality score by adding evidence"
- **AI Gap:** Should be AI-generated, context-aware, actionable

**3. ComplianceCalculator (no explanations currently)**
- Returns compliance data but no explanation text
- **AI Gap:** Should generate coaching messages for non-compliant employees

### Current Weaknesses or Duplication

**1. Duplicate Explanation Logic:**
- `release_engine.py._build_explanations()` builds explanations
- `daf_summary_service.py` may duplicate some explanation logic
- No centralized explanation service

**2. Template-Based Text:**
- All explanations are hard-coded strings
- No personalization, no context awareness
- No multilingual support (Group B needs Swahili)

**3. No Chain-of-Thought:**
- Explanations don't show reasoning (why stipend is 0% vs 50%)
- No step-by-step breakdown of pay calculations

### Where AIInsightService Should Hook In

**1. DAFSummaryService.get_summary()**
- After aggregating data, call `AIInsightService.generate_insights()`
- Replace template-based focus with AI-generated insights

**2. ReleaseEngine.compute_release()**
- After calculating release, call `AIInsightService.generate_pay_explanation()`
- Replace hard-coded explanations with AI-generated, personalized text

**3. PerformanceMetricsService.get_month_metrics()**
- After computing metrics, call `AIInsightService.generate_coaching()`
- Generate personalized coaching based on compliance, quality, attendance

**4. CareerLevelService.get_progress_to_next_level()**
- After computing progress, call `AIInsightService.generate_career_advice()`
- Explain blockers, next steps, estimated time to promotion

---

## SECTION 7 — Pay & Compliance Integration Points

### Methods That Compute Stipend, Safety Net, Locked Pay

**1. ReleaseEngine._calculate_stipend() (`management/services/release_engine.py:276`)**
- Formula: `base_stipend * compliance_factor * quality_cap`
- Compliance factor: <33% → 0%, 33-66.5% → 50%, ≥66.5% → 100%
- Quality cap: if quality < 0.5, stipend_factor <= 0.5
- **AI Gap:** Explanation text is hard-coded, should be AI-generated with reasoning

**2. ReleaseEngine._calculate_safety_net() (`management/services/release_engine.py:356`)**
- Group B only, attendance-based minimum (default 1500 KES)
- **AI Gap:** Explanation should explain why safety net applies/doesn't apply

**3. ReleaseEngine.compute_release() (`management/services/release_engine.py:71`)**
- Orchestrates: base_release, stipend, safety_net, locked_remaining
- **AI Gap:** Should generate chain-of-thought explanation showing all calculations

### Where Explanation Text Is (or Should Be) Generated

**1. ReleaseEngine._build_explanations() (`management/services/release_engine.py:422`)**
- Current: Hard-coded strings
- Should be: AI-generated, personalized, multilingual
- Needs: Compliance context, career state, metrics, pay amounts

**2. PayCalculationService.calculate_payslip() (`management/services/pay_calculation_service.py:84`)**
- Returns structured data but no explanation text
- Should generate: "Why your pay is X", "What bonuses/deductions apply"

**3. ComplianceCalculator.calculate_compliance() (`management/services/compliance_calculator.py:50`)**
- Returns compliance data but no explanation
- Should generate: "You're at X% completion, need Y% more to unlock pay"

### Exactly Where Pay Reasoning Needs Chain-of-Thought

**1. Stipend Calculation Reasoning:**
```
Input: compliance_rate=45%, quality_score=0.6, is_tenured=True, group=B
Chain-of-Thought:
  - Compliance factor: 45% is between 33% and 66.5% → factor = 0.5 (50%)
  - Quality cap: 0.6 >= 0.5 → no quality cap applied
  - Final stipend: 2500 * 0.5 = 1250 KES
Output: "You're receiving 50% stipend (1250 KES) because your compliance is 45%, which qualifies for the 50% tier. Your quality score of 60% is above the threshold, so no quality cap applies."
```

**2. Release Decision Reasoning:**
```
Input: earned=5000, compliance=40%, rule_active=True
Chain-of-Thought:
  - Compliance check: 40% >= 33% → compliant
  - Rule active: Yes (after 15th)
  - Base release: 5000 KES (full earned amount)
  - Stipend: calculated separately
  - Total released: base_release + stipend
Output: "You've unlocked 5000 KES from last month because you reached 40% completion this month, exceeding the 33% threshold."
```

**3. Safety Net Reasoning:**
```
Input: released=800, attendance_days=12, group=B
Chain-of-Thought:
  - Attendance check: 12 >= 10 → eligible
  - Current total: 800 KES
  - Minimum: 1500 KES
  - Top-up needed: 1500 - 800 = 700 KES
Output: "Safety net top-up: 700 KES (you attended 12 days, ensuring minimum pay of 1500 KES)."
```

### How to Pull Real Numbers for MCP Tools

**MCP Tools Needed:**
1. **get_employee_pay_breakdown(employee_id, month, year)**
   - Returns: earned, released, locked, stipend, safety_net, explanations
   - Source: `PayCalculationService.calculate_payslip()` with `include_release_breakdown=True`

2. **get_compliance_status(employee_id, month, year)**
   - Returns: completion_rate, is_compliant, total_points, total_max_points
   - Source: `ComplianceCalculator.calculate_compliance()`

3. **get_career_state(employee_id)**
   - Returns: group, current_level, next_level, progress, blockers
   - Source: `CareerLevelService.get_state()` + `get_progress_to_next_level()`

4. **get_task_history(employee_id, month, year)**
   - Returns: tasks with points, earnings, quality scores
   - Source: `TaskHistory.objects.filter(employee=employee, daf_date__month=month, daf_date__year=year)`

---

## SECTION 8 — Candidate Prompts in Existing Code

### Explanation Strings

**1. ReleaseEngine._build_explanations() (`management/services/release_engine.py:422`)**
```python
# Compliance explanation
f"Your current month compliance is {compliance_rate:.1f}%, so you unlocked {base_release:,.0f} KES from last month's earnings."

f"You are at {compliance_rate:.1f}% completion. You need at least {self.COMPLIANCE_THRESHOLD}% to unlock the rest of your earnings."

# Stipend explanation
f"Stipend: {stipend_release:,.0f} KES ({stipend_percentage:.0f}% of maximum) based on your current compliance and quality."

"Stipend: 0 KES (you need at least 33% compliance to receive a stipend)."

# Safety net explanation
f"Safety net top-up: {safety_net_topup:,.0f} KES (ensures minimum pay when you show up regularly)."

# Locked amount explanation
f"You have {locked_remaining:,.0f} KES locked from last month. Reach {self.COMPLIANCE_THRESHOLD}% completion this month to unlock more."
```

**2. DAFSummaryService._get_focus_data() (`management/services/daf_summary_service.py:250`)**
```python
# Focus messages (template-based)
"Focus on completing more tasks this month"
"Improve your quality score by adding evidence"
"Add photos/summary to improve your quality score"
```

**3. PositionHistoryCollector._generate_ai_analysis() (`investing/services/position_history_collector.py:249`)**
```python
# Trade analysis (template-based, TODO: use AI)
f"🎯 EXCELLENT TRADE: {roi:.1f}% return in {days_held} days. Position closed profitably..."
f"✅ GOOD TRADE: {roi:.1f}% return. Position performed as expected..."
f"❌ LOSS: {roi:.1f}% return. Position closed at loss..."
```

### Guidance Messages

**1. Evidence Reminder Messages (EvidenceReminderService)**
- Should generate personalized reminders based on task type, deadline, evidence gaps

**2. Quality Feedback Messages (ChecklistEvaluationService)**
- Should explain quality scores, what's missing, how to improve

**3. Career Progression Messages (CareerLevelService)**
- Should explain blockers, next steps, estimated time to promotion

### Coaching Text

**1. Compliance Coaching (ComplianceCalculator)**
- Should generate: "You're at X% completion. To unlock your pay, complete Y more tasks by the 15th."

**2. Quality Coaching (ChecklistEvaluationService)**
- Should generate: "Your quality score is X. To improve, add evidence for tasks A, B, C."

**3. Career Coaching (CareerLevelService)**
- Should generate: "You're at level B5. To reach B6, you need to complete 3 more high-quality tasks this month."

### Evidence Feedback

**1. EvidenceValidationService**
- Should generate: "Your evidence for task X is incomplete. Please add: [specific requirements]"

**2. MeetingLinkingService**
- Should generate: "Meeting 'Y' was linked to task 'X' because [reasoning]"

### All Candidate Prompts Should Become Templates

**Template Registry Structure Needed:**
```python
PROMPT_TEMPLATES = {
    'pay_explanation': {
        'compliance_unlocked': "Your current month compliance is {compliance_rate:.1f}%, so you unlocked {base_release:,.0f} KES from last month's earnings.",
        'compliance_locked': "You are at {compliance_rate:.1f}% completion. You need at least {threshold}% to unlock the rest of your earnings.",
        'stipend_full': "Stipend: {stipend_release:,.0f} KES (100% of maximum) based on your compliance of {compliance_rate:.1f}% and quality score of {quality_score:.0%}.",
        'stipend_partial': "Stipend: {stipend_release:,.0f} KES ({stipend_percentage:.0f}% of maximum) because your compliance is {compliance_rate:.1f}%, which qualifies for the 50% tier.",
        'stipend_zero': "Stipend: 0 KES (you need at least 33% compliance to receive a stipend).",
        'safety_net': "Safety net top-up: {safety_net_topup:,.0f} KES (ensures minimum pay when you show up regularly).",
        'locked_amount': "You have {locked_remaining:,.0f} KES locked from last month. Reach {threshold}% completion this month to unlock more.",
    },
    'daf_focus': {
        'low_compliance': "Focus on completing more tasks this month to unlock your pay.",
        'low_quality': "Improve your quality score by adding evidence to your tasks.",
        'missing_evidence': "Add photos/summary to improve your quality score.",
        'career_blocker': "You're blocked from promotion because {blocker_reason}. Focus on {action_items}.",
    },
    'career_coaching': {
        'progress_update': "You're at level {current_level}. You've completed {progress:.0%} of the requirements for {next_level}.",
        'blockers': "To reach {next_level}, you need to: {blocker_list}",
        'estimated_time': "At your current pace, you should reach {next_level} in approximately {months} months.",
    },
    'quality_feedback': {
        'high_quality': "Great work! Your quality score of {score:.0%} shows excellent evidence and completion.",
        'medium_quality': "Your quality score is {score:.0%}. To improve, add evidence for: {missing_items}",
        'low_quality': "Your quality score is {score:.0%}. Please add evidence for tasks: {task_list}",
    },
}
```

---

## SECTION 9 — DRY Violations and Refactor Targets

### Repeated Logic

**1. Pay Calculation Logic:**
- `management/utils.py`: `calculate_total_pay()`, `payinitial()`, `bonus()`, `deductions()`
- `management/services/pay_calculation_service.py`: Wraps above functions
- `management/services/earnings_engine.py`: Pure calculation engine
- **Refactor:** Consolidate into EarningsEngine, remove legacy utils

**2. Compliance Calculation:**
- `ComplianceCalculator.calculate_compliance()` – Single source of truth
- `EmployeeComplianceService.check_33_percent_compliance()` – Wrapper
- **Status:** Already consolidated, but some views may call directly

**3. AI Response Generation:**
- `main/utils.py`: `generate_chatbot_response()`, `openai_user_message()`
- `main/utilities/ai_utils.py`: `AIUtils.generate_chatbot_response()`
- `ai_services/services/ai_service_facade.py`: Consolidated version
- **Refactor:** Remove duplicates, migrate all calls to facade

### Repeated Explanations

**1. Pay Explanations:**
- `release_engine.py._build_explanations()` – Hard-coded strings
- `daf_summary_service.py` may duplicate some logic
- **Refactor:** Create `ExplanationService` with AI-powered generation

**2. Quality Feedback:**
- Scattered in `ChecklistEvaluationService`, `EvidenceValidationService`
- **Refactor:** Centralize in `QualityFeedbackService` with AI

### Hard-Coded Text

**1. All Explanation Strings:**
- `release_engine.py`: 10+ hard-coded explanation strings
- `daf_summary_service.py`: Template-based focus messages
- **Refactor:** Move to prompt templates, generate via AI

**2. Error Messages:**
- Scattered across services
- **Refactor:** Centralize in `ErrorMessageService` with AI for user-friendly messages

### Poorly Structured Prompts

**1. F-String Concatenation:**
- `main/utils.py`: `openai_user_message()` builds prompts via f-strings
- `ai_integration_service.py`: `_build_analysis_prompt()` uses dict of f-strings
- **Refactor:** Use Jinja2 templates or Pydantic prompt models

**2. No Prompt Versioning:**
- Prompts are code, not data
- **Refactor:** Store prompts in database or config files, version them

### Missing Abstractions

**1. No Prompt Template Registry:**
- Each service builds prompts ad-hoc
- **Refactor:** Create `PromptTemplateRegistry` with versioning, A/B testing

**2. No Output Schema Registry:**
- Each service parses AI responses differently
- **Refactor:** Create `OutputSchemaRegistry` with Pydantic models

**3. No Chain Library:**
- No LangChain/LlamaIndex integration for complex reasoning
- **Refactor:** Create `ChainLibrary` for chain-of-thought, multi-step reasoning

### Poor Separation of Concerns (SOC)

**1. AI Logic in Business Services:**
- `ReleaseEngine._build_explanations()` mixes business logic with text generation
- **Refactor:** Extract to `AIInsightService.generate_pay_explanation()`

**2. Prompt Construction in Views:**
- `main/views.py`: `generate_openai_description()` builds prompts in view
- **Refactor:** Move to service layer, use prompt templates

**3. Response Parsing in Integration Layer:**
- `ai_integration_service.py._parse_ai_response()` mixes parsing with API calls
- **Refactor:** Extract to `ResponseParser` service with schema validation

---

## SECTION 10 — Recommended Abstractions

### AIInsightService Boundaries

**Purpose:** Centralized service for all AI-generated insights, explanations, and coaching.

**Methods:**
```python
class AIInsightService:
    def generate_pay_explanation(
        self,
        employee: User,
        pay_breakdown: Dict,
        compliance_data: Dict,
        career_state: EmployeeCareerState
    ) -> Dict[str, str]:  # Returns {'kes': '...', 'swahili': '...'}
    
    def generate_daf_focus(
        self,
        employee: User,
        career_data: Dict,
        money_data: Dict,
        metrics_data: Dict,
        activities_data: List[Dict]
    ) -> Dict[str, Any]:  # Returns focus areas, recommendations, action items
    
    def generate_career_coaching(
        self,
        employee: User,
        career_state: Dict,
        progress: Dict,
        blockers: List[str]
    ) -> Dict[str, str]:  # Returns coaching messages
    
    def generate_quality_feedback(
        self,
        employee: User,
        task: Task,
        quality_score: float,
        missing_items: List[str]
    ) -> str:  # Returns personalized feedback
    
    def generate_compliance_coaching(
        self,
        employee: User,
        compliance_data: Dict,
        target_month: int,
        target_year: int
    ) -> Dict[str, str]:  # Returns coaching messages
```

**Integration Points:**
- Called by `DAFSummaryService` for focus/recommendations
- Called by `ReleaseEngine` for pay explanations
- Called by `PerformanceMetricsService` for coaching
- Called by `CareerLevelService` for career advice

### Provider Abstraction

**Current:** `RealAIService` supports multiple providers but is tightly coupled.

**Recommended:**
```python
class AIProviderInterface(ABC):
    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: str,
        schema: Optional[Dict] = None,
        temperature: float = 0.3
    ) -> Dict[str, Any]
    
    @abstractmethod
    def health_check(self) -> Dict[str, Any]

class OpenAIProvider(AIProviderInterface): ...
class ClaudeProvider(AIProviderInterface): ...
class LocalProvider(AIProviderInterface): ...

class AIProviderRegistry:
    def get_provider(self, model_name: str) -> AIProviderInterface
    def get_fallback_chain(self) -> List[AIProviderInterface]
```

### Prompt Template Registry

**Structure:**
```python
class PromptTemplate:
    name: str
    version: str
    template: str  # Jinja2 template
    variables: List[str]  # Required variables
    output_schema: Optional[Dict]  # JSON schema for structured output
    system_prompt: Optional[str]
    temperature: float = 0.3

class PromptTemplateRegistry:
    def get_template(self, name: str, version: str = "latest") -> PromptTemplate
    def render(self, name: str, context: Dict, version: str = "latest") -> str
    def list_templates(self) -> List[PromptTemplate]
```

**Templates Needed:**
- `pay_explanation.compliance_unlocked`
- `pay_explanation.stipend_calculation`
- `daf_focus.low_compliance`
- `career_coaching.progress_update`
- `quality_feedback.medium_quality`
- `compliance_coaching.below_threshold`

### Output Schema Registry

**Structure:**
```python
from pydantic import BaseModel

class PayExplanationOutput(BaseModel):
    kes_explanation: str
    swahili_explanation: str
    reasoning_steps: List[str]
    key_numbers: Dict[str, float]

class DAFFocusOutput(BaseModel):
    focus_areas: List[str]
    recommendations: List[str]
    action_items: List[str]
    estimated_impact: str

class OutputSchemaRegistry:
    def get_schema(self, output_type: str) -> Type[BaseModel]
    def validate(self, output_type: str, data: Dict) -> BaseModel
```

### Chain Library

**Purpose:** Multi-step reasoning, chain-of-thought, tool use.

**Structure:**
```python
class ChainStep:
    name: str
    prompt_template: str
    tools: List[str]  # MCP tools to call
    output_schema: Type[BaseModel]

class ChainLibrary:
    def create_chain(self, steps: List[ChainStep]) -> Chain
    def execute_chain(self, chain: Chain, initial_context: Dict) -> Dict

# Example: Pay explanation chain
pay_explanation_chain = ChainLibrary().create_chain([
    ChainStep(
        name="get_pay_data",
        tools=["get_employee_pay_breakdown"],
        output_schema=PayBreakdownOutput
    ),
    ChainStep(
        name="generate_explanation",
        prompt_template="pay_explanation.stipend_calculation",
        output_schema=PayExplanationOutput
    )
])
```

### Where LaneGraph and MCP Tools Will Integrate

**LaneGraph Integration:**
- LaneGraph will orchestrate multi-step AI workflows
- Each `ChainStep` becomes a LaneGraph node
- MCP tools are LaneGraph tools

**MCP Tools Integration:**
- MCP tools provide real-time data access:
  - `get_employee_pay_breakdown()` → Calls `PayCalculationService`
  - `get_compliance_status()` → Calls `ComplianceCalculator`
  - `get_career_state()` → Calls `CareerLevelService`
  - `get_task_history()` → Queries `TaskHistory` model

**Integration Points:**
1. **AIInsightService** uses MCP tools to fetch data before generating insights
2. **ChainLibrary** orchestrates MCP tool calls in sequence
3. **LaneGraph** provides visual workflow for complex reasoning chains

---

## SECTION 11 — Risk Areas

### Places Where AI Could Break Determinism

**1. Pay Calculations:**
- **Risk:** AI-generated explanations could contradict actual pay calculations
- **Mitigation:** AI only generates explanations, never calculates pay. All pay calculations remain deterministic in `EarningsEngine`, `ReleaseEngine`.

**2. Compliance Decisions:**
- **Risk:** AI could generate incorrect compliance coaching
- **Mitigation:** AI only generates coaching text. Compliance calculation remains deterministic in `ComplianceCalculator`.

**3. Career Progression:**
- **Risk:** AI could suggest incorrect promotion readiness
- **Mitigation:** AI only generates coaching. Career level calculation remains deterministic in `CareerLevelService`.

### Areas Where Data Is Ambiguous

**1. Activity Name Standardization:**
- **Risk:** "one on one" vs "one-on-one" vs "1-on-1" → ambiguous mapping to ActivityType
- **Mitigation:** Use AI for fuzzy matching but validate against ActivityType registry. Store canonical name in Task.

**2. Meeting-to-Task Linking:**
- **Risk:** Multiple tasks could match a meeting (date, attendees, topic similarity)
- **Mitigation:** Use AI for semantic matching but require confidence threshold. Manual review for low-confidence matches.

**3. Evidence Quality Assessment:**
- **Risk:** Subjective quality scores (what is "good" evidence?)
- **Mitigation:** Use AI to assess quality but validate against checklist requirements. Store AI score separately from checklist score.

### Unsafe Points Where Employee-Facing Text Is Generated

**1. Pay Explanations:**
- **Risk:** Incorrect explanations could cause confusion, disputes
- **Mitigation:** 
  - Always show actual numbers alongside AI explanations
  - Validate explanations against deterministic calculations
  - Provide "Show calculation details" link to raw data

**2. Compliance Coaching:**
- **Risk:** Incorrect coaching could lead to employees missing compliance deadlines
- **Mitigation:**
  - Always show actual compliance percentage
  - Provide clear action items with deadlines
  - Send reminders via multiple channels (email, DAF UI, SMS)

**3. Career Progression Advice:**
- **Risk:** Overly optimistic or pessimistic advice could demotivate employees
- **Mitigation:**
  - Base advice on actual metrics, not AI speculation
  - Provide ranges ("3-6 months") not exact dates
  - Include disclaimers ("estimates based on current performance")

### Areas Where Hallucination Risk Must Be Controlled

**1. Pay Amount Hallucination:**
- **Risk:** AI could generate incorrect pay amounts in explanations
- **Mitigation:** Never let AI generate numbers. Always pass actual numbers from `PayCalculationService` to AI as context. AI only generates text explanations.

**2. Compliance Status Hallucination:**
- **Risk:** AI could generate incorrect compliance percentages
- **Mitigation:** Always pass actual compliance data from `ComplianceCalculator` to AI. AI only generates coaching text.

**3. Historical Data Hallucination:**
- **Risk:** AI could make up historical task data
- **Mitigation:** Always pass actual `TaskHistory` data to AI. Use MCP tools to fetch real data, never let AI infer from context alone.

**4. Policy Rule Hallucination:**
- **Risk:** AI could generate incorrect policy explanations
- **Mitigation:** Store policy rules in code/config, pass to AI as context. AI only generates user-friendly explanations, never invents rules.

---

## SECTION 12 — "Missing Pieces" Needed for CODA AI V1

### ActivityDefinition Registry

**Current State:** `ActivityType` model exists but no structured schema for AI.

**Needed:**
```python
class ActivityDefinition:
    activity_type: ActivityType  # FK
    prompt_template: str  # For AI task assignment
    quality_criteria: Dict  # What constitutes "good" evidence
    coaching_template: str  # For AI-generated feedback
    ai_context: str  # Description for AI prompts
    skill_requirements: List[str]  # For intelligent assignment
    evidence_requirements: List[str]  # Required evidence types
    quality_thresholds: Dict  # Minimum scores for promotion
```

**Implementation:**
- Extend `ActivityType` model or create separate `ActivityDefinition` model
- Populate via admin or migration
- Use in `AIInsightService` for activity-specific prompts

### Prompt Templates for Each Activity

**Needed Templates:**
1. **Task Assignment Prompts:**
   - `activity.{slug}.assignment_prompt` – Why this task was assigned
   - `activity.{slug}.coaching_prompt` – How to complete this task well

2. **Quality Feedback Prompts:**
   - `activity.{slug}.quality_feedback.high` – High quality feedback
   - `activity.{slug}.quality_feedback.medium` – Medium quality feedback
   - `activity.{slug}.quality_feedback.low` – Low quality feedback

3. **Evidence Validation Prompts:**
   - `activity.{slug}.evidence_validation` – What evidence is missing/needed

**Implementation:**
- Store in `PromptTemplateRegistry` (database or config files)
- Version control via `version` field
- A/B testing via `variant` field

### Structured Schemas for DAF Summaries

**Current State:** `DAFSummaryService` returns unstructured dict.

**Needed:**
```python
class DAFSummaryOutput(BaseModel):
    employee: EmployeeInfo
    career: CareerData
    money: MoneyData
    metrics: MetricsData
    activities: List[ActivityData]
    focus: FocusData
    meta: MetaData

class FocusData(BaseModel):
    focus_areas: List[str]
    recommendations: List[str]
    action_items: List[Dict[str, str]]  # {task: "...", deadline: "..."}
    estimated_impact: str
    reasoning: List[str]  # Chain-of-thought steps
```

**Implementation:**
- Use Pydantic models for validation
- Store in `OutputSchemaRegistry`
- Validate AI outputs against schemas

### RAG Retrieval Layer

**Purpose:** Provide AI with relevant context from historical data, policies, examples.

**Needed Components:**
1. **Vector Store:**
   - Embeddings of: TaskHistory, ActivityType descriptions, policy documents, coaching examples
   - Use: ChromaDB, Pinecone, or PostgreSQL with pgvector

2. **Retrieval Service:**
   ```python
   class RAGRetrievalService:
       def retrieve_relevant_context(
           self,
           query: str,
           context_type: str,  # "task_history", "policy", "coaching_example"
           limit: int = 5
       ) -> List[Dict]
   ```

3. **Integration Points:**
   - `AIInsightService` uses RAG to fetch relevant examples before generating insights
   - `PromptTemplateRegistry` includes RAG context in prompts

**Implementation:**
- Set up vector store (ChromaDB recommended for simplicity)
- Create embeddings for: TaskHistory descriptions, ActivityType descriptions, policy docs
- Integrate retrieval into `AIInsightService`

### Model Selection Abstraction

**Current State:** `RealAIService` hard-codes model selection logic.

**Needed:**
```python
class ModelSelector:
    def select_model(
        self,
        task_type: str,  # "pay_explanation", "daf_focus", "quality_feedback"
        complexity: str,  # "simple", "medium", "complex"
        budget: str = "default"  # "low", "default", "high"
    ) -> str:  # Returns model name
    
    def get_fallback_chain(self, primary_model: str) -> List[str]
```

**Implementation:**
- Store model selection rules in config
- Use cost/quality trade-offs to select models
- Integrate with `AIModelConfiguration` for database-driven config

### Validation & Fallback Logic

**Current State:** Basic error handling, falls back to dummy data.

**Needed:**
```python
class AIResponseValidator:
    def validate_output(
        self,
        output: Dict,
        schema: Type[BaseModel],
        context: Dict  # For consistency checks
    ) -> ValidationResult:
        # Returns: valid, errors, warnings
    
    def check_consistency(
        self,
        ai_output: Dict,
        deterministic_data: Dict  # From PayCalculationService, etc.
    ) -> ConsistencyResult:
        # Returns: consistent, inconsistencies (list of mismatches)

class FallbackStrategy:
    def get_fallback_response(
        self,
        task_type: str,
        error: Exception,
        context: Dict
    ) -> Dict:
        # Returns: fallback response (template-based or cached)
```

**Implementation:**
- Validate all AI outputs against Pydantic schemas
- Check consistency with deterministic calculations
- Provide graceful fallbacks (templates, cached responses, human review queue)

---

## SECTION 13 — Final Engineering Recommendations

### What Should Be Built

**1. AIInsightService (`ai_services/services/ai_insight_service.py`)**
- Centralized service for all AI-generated insights
- Methods: `generate_pay_explanation()`, `generate_daf_focus()`, `generate_career_coaching()`, etc.
- Uses: `PromptTemplateRegistry`, `OutputSchemaRegistry`, `RAGRetrievalService`, MCP tools

**2. PromptTemplateRegistry (`ai_services/registry/prompt_template_registry.py`)**
- Stores all prompt templates with versioning
- Supports Jinja2 templating, A/B testing
- Templates for: pay explanations, DAF focus, career coaching, quality feedback

**3. OutputSchemaRegistry (`ai_services/registry/output_schema_registry.py`)**
- Pydantic models for all AI outputs
- Validation layer for AI responses
- Schemas for: PayExplanationOutput, DAFFocusOutput, CareerCoachingOutput

**4. RAGRetrievalService (`ai_services/services/rag_retrieval_service.py`)**
- Vector store for historical data, policies, examples
- Retrieval methods for relevant context
- Integration with `AIInsightService`

**5. ChainLibrary (`ai_services/chains/chain_library.py`)**
- Multi-step reasoning chains
- Chain-of-thought for complex explanations
- Integration with LaneGraph, MCP tools

**6. MCP Tools (`ai_services/mcp_tools/`)**
- `get_employee_pay_breakdown()` – Wraps `PayCalculationService`
- `get_compliance_status()` – Wraps `ComplianceCalculator`
- `get_career_state()` – Wraps `CareerLevelService`
- `get_task_history()` – Queries `TaskHistory`

**7. ActivityDefinition Extension**
- Extend `ActivityType` model or create `ActivityDefinition` model
- Add: `prompt_template`, `quality_criteria`, `coaching_template`, `ai_context`, `skill_requirements`

### What Should Be Removed

**1. Duplicate AI Functions:**
- Remove `main/utils.py`: `generate_chatbot_response()`, `openai_user_message()` (migrate to `ai_service_facade`)
- Remove `main/utilities/ai_utils.py`: `AIUtils` class (consolidate into `ai_services`)

**2. Hard-Coded Explanation Strings:**
- Remove hard-coded strings from `release_engine.py._build_explanations()`
- Remove template-based focus messages from `daf_summary_service.py._get_focus_data()`
- Replace with AI-generated text via `AIInsightService`

**3. Ad-Hoc Prompt Construction:**
- Remove f-string prompt building from `main/utils.py`, `ai_integration_service.py`
- Replace with `PromptTemplateRegistry.render()`

### What Should Be Refactored

**1. AI Service Architecture:**
- Refactor `RealAIService` to use `AIProviderInterface` abstraction
- Extract response parsing to `ResponseParser` service
- Move prompt construction to `PromptTemplateRegistry`

**2. Explanation Generation:**
- Extract explanation logic from `ReleaseEngine` to `AIInsightService`
- Extract focus generation from `DAFSummaryService` to `AIInsightService`
- Centralize all text generation in `AIInsightService`

**3. Pay Calculation Service:**
- Keep `PayCalculationService` as orchestrator (no changes)
- Keep `EarningsEngine`, `ReleaseEngine` deterministic (no AI)
- Add `AIInsightService` call after calculations to generate explanations

### What Should Be Centralized

**1. All AI Operations:**
- Centralize in `ai_services` app
- Use `AIServiceFacade` as single entry point
- Migrate all AI calls from `main`, `investing`, `management` to `ai_services`

**2. All Prompt Templates:**
- Store in `PromptTemplateRegistry` (database or config)
- Version control, A/B testing
- Single source of truth for all prompts

**3. All Output Schemas:**
- Store in `OutputSchemaRegistry` (Pydantic models)
- Single source of truth for AI output validation

**4. All Explanation Generation:**
- Centralize in `AIInsightService`
- Single service for all employee-facing text generation

### What Should Be Delegated to AI

**1. Text Generation (Not Calculations):**
- Pay explanations (why stipend is X%, why pay is locked)
- DAF focus recommendations (what to focus on this month)
- Career coaching (how to reach next level, what's blocking)
- Quality feedback (what evidence is missing, how to improve)
- Compliance coaching (how to reach 33% threshold)

**2. Semantic Matching:**
- Activity name standardization (fuzzy matching to ActivityType)
- Meeting-to-task linking (semantic similarity)
- Evidence quality assessment (beyond checklist)

**3. Pattern Detection:**
- Historical task patterns (for intelligent assignment)
- Performance trends (for forecasting)
- Anomaly detection (for alerts)

### What Should Remain Deterministic

**1. All Pay Calculations:**
- `EarningsEngine.calculate()` – Pure calculation, no AI
- `ReleaseEngine.compute_release()` – Deterministic logic, AI only for explanations
- `PayCalculationService.calculate_payslip()` – Orchestrator, no AI

**2. All Compliance Calculations:**
- `ComplianceCalculator.calculate_compliance()` – Deterministic formula
- `EmployeeComplianceService` – Wrapper, no AI

**3. All Career Level Calculations:**
- `CareerLevelService.get_state()` – Deterministic ladder logic
- `CareerLevelService.get_progress_to_next_level()` – Deterministic progress calculation

**4. All Quality Scoring:**
- `ChecklistEvaluationService` – Deterministic checklist scoring
- AI only for evidence quality assessment (subjective), not checklist completion

### Where AI Is Allowed

**1. Text Generation:**
- Employee-facing explanations, coaching, feedback
- Manager-facing insights, alerts, recommendations
- All text that explains deterministic calculations

**2. Semantic Operations:**
- Activity name matching, meeting linking, evidence quality assessment
- Pattern detection, anomaly detection, trend analysis

**3. Personalization:**
- Tailoring explanations to employee group (A/B/C), language (KES/Swahili), context

### Where AI Is Forbidden

**1. Financial Calculations:**
- Never calculate pay amounts, bonuses, deductions
- Never calculate compliance percentages, career levels
- Never modify financial data

**2. Business Rule Decisions:**
- Never decide if employee is compliant (use `ComplianceCalculator`)
- Never decide if employee should be promoted (use `CareerLevelService`)
- Never decide pay amounts (use `EarningsEngine`, `ReleaseEngine`)

**3. Data Modifications:**
- Never create, update, or delete Task, TaskHistory, PaySlip records
- Never modify employee career state, compliance status
- AI is read-only for data, write-only for generated text

---

## Conclusion

This architectural analysis provides a comprehensive blueprint for integrating AI into CODA V1. The key principles are:

1. **Separation of Concerns:** AI generates text and insights, but never calculates pay, compliance, or career levels. All calculations remain deterministic.

2. **Centralization:** All AI operations, prompts, and schemas are centralized in `ai_services` app with clear abstractions.

3. **Safety First:** AI outputs are validated against schemas, checked for consistency with deterministic data, and have graceful fallbacks.

4. **Incremental Integration:** Start with text generation (explanations, coaching), then add semantic operations (matching, quality assessment), then pattern detection.

5. **MCP Tools Integration:** Use MCP tools to provide AI with real-time data access, ensuring AI never hallucinates numbers or status.

The recommended architecture provides a clear path forward while maintaining backward compatibility and system reliability.



