# Architecture Refactor Roadmap (Cursor-Guided) - ENHANCED
**Goal:** Decouple management from other apps using interfaces + adapters  
**Target App:** `management`  
**Approach:** App-by-app, starting with management as pilot

---

## 🎯 High-Level Goal for This Round

Before we change Task / TaskHistory / ActivityType, we want:

**`management` can run and be tested without importing models/services from finance, ai_services, or professional_services directly.**

We'll achieve that by:

1. ✅ Adding interfaces in shared_core (ports)
2. ✅ Adding adapters in provider apps (ai_services, finance, professional_services)
3. ✅ Refactoring management to depend on interfaces, not concrete models
4. ✅ Keeping behavior identical (guarded by tests)

**Success Criteria:**
- Management app passes `python manage.py check` without finance/ai_services/professional_services installed
- All existing tests pass
- Features gracefully degrade when dependencies missing (use NoOp adapters)

---

## 🧱 Phase A – Analyze and Map Dependencies in management

### 🎯 Goal
Get a precise list of where management depends on other apps, and what those dependencies are for.

---

### 🔹 Prompt A1 – Find all cross-app imports inside management

**Task:** Scan the codebase and produce a Markdown report showing all imports inside the `management` app that reference OTHER apps' models or services.

**Focus on imports in `coda/management/` that reference:**
- `professional_services` (DSU, ClientAssessment, BackgroundCheck, FeaturedCategory, etc.)
- `finance` (LoanApplication, PayslipConfig, Payment_History, AIBudgetSuggestionService)
- `ai_services` (GotoMeetings, MeetingActivityMapping, RealAIService, OAuth functions)
- `accounts` (TaskGroups, UserProfile, choices, utils, permissions - **Note:** Most already via shared_core)
- `main` (filters: RequirementFilter, TaskHistoryFilter - **Note:** Should move to shared_core)

**For each import, list:**
- File path (relative to `coda/management/`)
- Line number
- Full import statement
- A brief note on how it's used (e.g., "fetch DSU records for dashboard", "link GoToMeeting", "get loan status", etc.)
- Whether it's already using try/except pattern (optional dependency)

**Known Files to Check** (from codebase analysis):
- `views.py` - Lines 85-86, 120-124 (DSU, LoanApplication, ai_services OAuth)
- `services/meeting_linking_service.py` - Line 20 (GotoMeetings, MeetingActivityMapping)
- `services/ai_prediction_service.py` - Line 23 (RealAIService)
- `services/intelligent_assignment_service.py` - Currently uses SimpleAIService (check if RealAIService needed)
- `views/meeting_review_views.py` - Line 21 (GotoMeetings)
- `models.py` - Lines 16-17 (TaskGroups, FeaturedCategory/SubCategory/Activity)
- `forms.py` - Line 5 (DSU, ClientAssessment, BackgroundCheck)
- `permission.py` - Line 2 (Payment_History)
- `signals.py` - Line 4 (ClientAssessment)

**Format the output as tables grouped by external app:**

```markdown
## ai_services dependencies
| File | Line | Import | Usage Summary | Optional? |
|------|------|--------|---------------|-----------|
| services/meeting_linking_service.py | 20 | `from ai_services.models import GotoMeetings, MeetingActivityMapping` | Link meetings to tasks for evidence | ❌ Direct |
| services/ai_prediction_service.py | 23 | `from ai_services.ai_integration_service import RealAIService` | AI predictions for tasks | ❌ Direct |
| views.py | 120 | `from ai_services.views import get_oauth_redirect_uri, ...` | OAuth helper functions | ❌ Direct |

## finance dependencies
| File | Line | Import | Usage Summary | Optional? |
|------|------|--------|---------------|-----------|
| views.py | 86 | `from finance.models import LoanApplication, PayslipConfig` | Check loan status for task assignment | ❌ Direct |
| permission.py | 2 | `from finance.models import Payment_History` | Check payment history permissions | ❌ Direct |
...

## professional_services dependencies
...
```

**This will be our starting "dependency inventory" for the management app.**

---

### 🔹 Prompt A2 – Classify each dependency by purpose

**Task:** Using the dependency inventory from Prompt A1, classify each dependency by *purpose*, not just by module.

**For each external dependency (ai_services, finance, professional_services, etc.):**

1. **Group usage into high-level purposes:**
   - AI-based assignment / predictions
   - Meeting/evidence linking (GotoMeeting, recordings)
   - Loan / finance status (for task assignment logic)
   - DSU / client assessments (for dashboards/forms)
   - OAuth / authentication helpers
   - Budget suggestions
   - Feature flags / permissions
   - Misc utilities

2. **For each purpose:**
   - List which models/services are involved
   - List which files use them
   - Summarize what `management` needs conceptually:
     - ✅ Good: "`management` needs: suggest best employee for task assignment"
     - ❌ Bad: "`management` needs RealAIService"

3. **Output a Markdown section:**

```markdown
## 1. AI / Assignment
- **Uses:** RealAIService in `services/ai_prediction_service.py`, `services/intelligent_assignment_service.py`
- **Conceptual need:** Get assignment suggestion for a task and a list of employees
- **Current state:** Some services use try/except, some don't
- **Files affected:** 2-3 service files

## 2. Meetings / Evidence Linking
- **Uses:** GotoMeetings, MeetingActivityMapping in `services/meeting_linking_service.py`, `views/meeting_review_views.py`
- **Conceptual need:** Find meeting recordings and link them to tasks as evidence
- **Current state:** Direct imports, no optional handling
- **Files affected:** 2 files

## 3. Finance / Loan Status
- **Uses:** LoanApplication, PayslipConfig, Payment_History in `views.py`, `permission.py`
- **Conceptual need:** Check if user has active loan (for task filtering), check payment history permissions
- **Current state:** Direct imports
- **Files affected:** 2-3 files

## 4. Professional Services / DSU
- **Uses:** DSU, ClientAssessment, BackgroundCheck, FeaturedCategory/SubCategory/Activity in `views.py`, `forms.py`, `models.py`
- **Conceptual need:** Display DSU records, client assessments in dashboards/forms, featured content
- **Current state:** Direct imports
- **Files affected:** 3-4 files

## 5. OAuth / Authentication
- **Uses:** OAuth helper functions from `ai_services.views` in `views.py`
- **Conceptual need:** OAuth redirect URI, authorization URLs, token exchange
- **Current state:** Direct imports (but already extracted to ai_services.views)
- **Files affected:** 1 file
```

**This will help us define very focused interfaces next.**

---

### 🔹 Prompt A3 – Identify accounts and main dependencies (shared_core candidates)

**Task:** Identify imports from `accounts` and `main` that should be moved to `shared_core` or handled differently.

**Note:** Many already use `shared_core`, but some direct imports remain:

- `accounts.models.TaskGroups` - Used in multiple files. **Question:** Should this move to shared_core?
- `accounts.choices` - Used for category checks. **Question:** Should choices move to shared_core?
- `main.filters` - RequirementFilter, TaskHistoryFilter. **Question:** Should filters move to shared_core?

**For each, determine:**
1. Can it move to shared_core? (if it's infrastructure)
2. Does it need an interface? (if it's business logic)
3. Can we remove the dependency? (if it's not essential)

**Output format:**
```markdown
## accounts dependencies (potential shared_core candidates)

### TaskGroups
- **Files:** models.py, views/task_assignment_views.py, services/*.py (5 files)
- **Purpose:** Group tasks/employees
- **Decision:** [ ] Move to shared_core OR [ ] Create interface OR [ ] Remove dependency

### choices (UserCategory, ApplicantSubCategoryChoices)
- **Files:** permission.py, utils.py, views.py
- **Purpose:** Category/type checking
- **Decision:** [ ] Move to shared_core OR [ ] Already in shared_core?

## main dependencies

### Filters (RequirementFilter, TaskHistoryFilter)
- **Files:** views.py
- **Purpose:** Filtering querysets
- **Decision:** [ ] Move to shared_core/filters.py OR [ ] Create interface
```

---

## 🧩 Phase B – Define Interfaces in shared_core (Ports)

### 🎯 Goal
Create minimal, clean interfaces in shared_core that express what management needs, without referencing other apps directly.

**We'll start with 3-4 interfaces:**
1. `AIServiceInterface`
2. `MeetingServiceInterface`
3. `FinanceTaskServiceInterface`
4. `ProfessionalServicesInterface` (only if truly needed)

---

### 🔹 Prompt B1 – Create AIServiceInterface

**Context:** 
- `IntelligentAssignmentService` currently uses `SimpleAIService` (internal)
- `AIPredictionService` uses `RealAIService` from ai_services
- Some services already have try/except patterns

**Task:**
1. Read `coda/management/services/intelligent_assignment_service.py` to see what AI methods are actually used
2. Read `coda/management/services/ai_prediction_service.py` to see RealAIService usage
3. Read `coda/ai_services/ai_integration_service.py` to understand RealAIService interface

4. Create a new file: `coda/shared_core/interfaces/ai_service.py`

5. Define an abstract class `AIServiceInterface` (using ABC) that contains ONLY the methods `management` actually needs:
   - `predict_performance(task_history: List[Dict]) -> Dict` (if used)
   - `suggest_assignment(task_data: Dict, employees: List[Dict]) -> Dict`
   - Any other AI-related method actually used by management code
   - **Use type hints and clear docstrings**

6. **Do NOT import from ai_services here.** The interface must be completely independent and live only in `shared_core`.

7. Create a `NoOpAIServiceAdapter` in `coda/shared_core/services/adapters/noop_ai_adapter.py` that:
   - Implements `AIServiceInterface`
   - Returns safe defaults (e.g., no suggestions, confidence: 0.0, empty dicts)

8. Add `shared_core/__init__.py` exports if needed

**Provide the complete code for:**
- `AIServiceInterface` (with docstrings explaining each method's purpose)
- `NoOpAIServiceAdapter` (with docstrings explaining when it's used)

**We will later wire `management` to depend on this interface and use the NoOp adapter when ai_services is not installed.**

---

### 🔹 Prompt B2 – Create MeetingServiceInterface

**Context:**
- `MeetingLinkingService` uses `GotoMeetings` and `MeetingActivityMapping` models directly
- Used for auto-linking meetings to tasks as evidence
- Need to find meetings by user, topic, date range

**Task:**
1. Read `coda/management/services/meeting_linking_service.py` to understand:
   - How GotoMeetings is queried
   - What fields are needed
   - How meetings are linked to tasks

2. Read `coda/ai_services/models.py` to see GotoMeetings model structure

3. Create a new file: `coda/shared_core/interfaces/meeting_service.py`

4. Define an abstract class `MeetingServiceInterface` that exposes ONLY what `management` needs:
   - `get_recent_meetings_for_user(user_id: int, since: datetime) -> List[Dict]`
   - `find_meeting_by_topic(topic: str, date_range: Tuple[date, date]) -> Optional[Dict]`
   - `get_meeting_by_id(meeting_id: int) -> Optional[Dict]` (if needed)
   - Any other methods actually used

5. **Design methods to work with simple dicts** (id, topic, start_time, link, recording_url, attendees, etc.), NOT Django models

6. Create `NoOpMeetingServiceAdapter` in `coda/shared_core/services/adapters/noop_meeting_adapter.py`:
   - Returns empty lists `[]` or `None`
   - No errors thrown

**Provide concrete code for:**
- `MeetingServiceInterface` (with method signatures matching actual usage)
- `NoOpMeetingServiceAdapter`

---

### 🔹 Prompt B3 – Create FinanceTaskServiceInterface

**Context:**
- `views.py` imports `LoanApplication, PayslipConfig` for task assignment logic
- `permission.py` imports `Payment_History` for permission checks
- Need to check loan status, payment history

**Task:**
1. Search `coda/management/` for all usage of finance models to understand:
   - What data is needed?
   - How is it queried?
   - What's the minimal interface?

2. Create `coda/shared_core/interfaces/finance_task_service.py`

3. Define `FinanceTaskServiceInterface` with minimal necessary methods:
   - `get_user_loan_summary(user_id: int) -> Optional[Dict]` (status, amount, etc.)
   - `has_active_loan(user_id: int) -> bool`
   - `get_recent_payments_for_user(user_id: int, limit: int = 10) -> List[Dict]`
   - Any budget suggestion methods (if AIBudgetSuggestionService is used)

4. Create `NoOpFinanceTaskServiceAdapter` that returns:
   - `None` for loan summary
   - `False` for has_active_loan
   - `[]` for payment lists

**Provide code for interface + noop adapter. Do NOT import from `finance` in shared_core.**

---

### 🔹 Prompt B4 – (Optional) ProfessionalServicesInterface

**Context:**
- Management imports DSU, ClientAssessment, BackgroundCheck, FeaturedCategory/SubCategory/Activity
- Used in views, forms, models

**Task:** Determine if this is truly necessary for core task logic, or just UI/dashboard features.

**Analysis:**
1. Review usage in `coda/management/`:
   - Is it used in task assignment logic? (core)
   - Is it only used in dashboards/forms? (UI - can be optional)

2. **If essential for core logic:**
   - Create `coda/shared_core/interfaces/professional_services_interface.py`
   - Define minimal methods:
     - `get_recent_dsu_for_user(user_id: int) -> List[Dict]`
     - `get_client_assessment_status(user_id: int) -> Optional[Dict]`
     - `get_featured_content(category: str) -> List[Dict]` (if needed)
   - Create `NoOpProfessionalServicesAdapter`

3. **If only for UI:**
   - Keep direct imports with try/except for now
   - Can refactor later

**Provide decision rationale and code if creating interface.**

---

## 🧱 Phase C – Implement Adapters in Provider Apps

### 🎯 Goal
Have real implementations of those interfaces that wrap existing models/services, but live inside the provider apps, not in management.

---

### 🔹 Prompt C1 – Adapter in ai_services for AIServiceInterface

**Task:**
1. Create `coda/ai_services/adapters/__init__.py` (if doesn't exist)

2. Create `coda/ai_services/adapters/ai_service_adapter.py`

3. Implement `AIServiceAdapter(AIServiceInterface)`:
   - Import `RealAIService` from `ai_services.ai_integration_service`
   - Wrap it to implement all methods from `AIServiceInterface`
   - Convert between RealAIService's actual interface and our interface
   - Handle any data format differences (Dict conversions, etc.)

4. **Ensure:**
   - No changes to business logic
   - Adapter lives in `ai_services` and imports from `ai_services` only + shared_core interfaces
   - Does NOT import from `management`

**Provide the full code for the adapter class with proper error handling.**

---

### 🔹 Prompt C2 – Adapter in ai_services for MeetingServiceInterface

**Task:**
1. Create `coda/ai_services/adapters/meeting_service_adapter.py`

2. Implement `MeetingServiceAdapter(MeetingServiceInterface)`:
   - Import `GotoMeetings`, `MeetingActivityMapping` from `ai_services.models`
   - Implement all interface methods by querying these models
   - Convert Django model instances to dicts:
     ```python
     {
         'id': meeting.id,
         'topic': meeting.topic,
         'start_time': meeting.start_time,
         'join_link': meeting.join_link,
         'recording_url': meeting.recording_url,
         'attendees': [...],  # if needed
         # ... other fields used by management
     }
     ```

3. **Ensure:**
   - Adapter only uses ai_services models/services + shared_core interfaces
   - Does NOT import from `management`
   - Handles missing/None values gracefully

**Provide the full implementation with proper type conversions.**

---

### 🔹 Prompt C3 – Adapter in finance for FinanceTaskServiceInterface

**Task:**
1. Create `coda/finance/adapters/__init__.py` (if doesn't exist)

2. Create `coda/finance/adapters/finance_task_adapter.py`

3. Implement `FinanceTaskAdapter(FinanceTaskServiceInterface)`:
   - Import `LoanApplication`, `Payment_History`, `PayslipConfig` from `finance.models`
   - Import `AIBudgetSuggestionService` from `finance.services` (if needed)
   - Implement all interface methods
   - Convert models to dicts with clear keys

4. **Ensure:**
   - Adapter returns dicts with clear structure
   - Does NOT import from `management`
   - Handles edge cases (no loans, no payments, etc.)

**Provide the adapter code with example dict structures in docstrings.**

---

## 🔄 Phase D – Refactor management to Use Interfaces

### 🎯 Goal
Replace direct dependencies in management with interface-based resolution + adapters, without changing behavior.

---

### 🔹 Prompt D1 – Refactor IntelligentAssignmentService

**Task:**
1. Read current `coda/management/services/intelligent_assignment_service.py`
   - Note: Currently uses `SimpleAIService` (internal)
   - Check if it also needs RealAIService

2. Refactor to use `AIServiceInterface`:

   **At the top, import:**
   ```python
   from shared_core.interfaces.ai_service import AIServiceInterface
   from shared_core.services.adapters.noop_ai_adapter import NoOpAIServiceAdapter
   ```

   **In `__init__`, implement adapter resolution:**
   ```python
   def __init__(self):
       # Try to get concrete implementation
       try:
           from ai_services.adapters.ai_service_adapter import AIServiceAdapter
           self.ai_service: AIServiceInterface = AIServiceAdapter()
       except ImportError:
           # Fallback to no-op
           self.ai_service: AIServiceInterface = NoOpAIServiceAdapter()
   ```

3. Replace any direct references to RealAIService or ai_services AI functions with:
   - `self.ai_service.suggest_assignment(...)`
   - `self.ai_service.predict_performance(...)`

4. **Ensure:**
   - All existing public methods remain unchanged
   - Behavior matches current implementation
   - Service works with both adapters (real + NoOp)

5. **Write/update tests** in `coda/management/tests/`:
   - Test with AIServiceAdapter available
   - Test with only NoOpAIServiceAdapter
   - Verify graceful degradation

**Provide:**
- Updated `IntelligentAssignmentService` code
- Updated tests

---

### 🔹 Prompt D2 – Refactor meeting linking to use MeetingServiceInterface

**Task:**
1. Read `coda/management/services/meeting_linking_service.py`
2. Read `coda/management/views/meeting_review_views.py`

3. Identify all places where `GotoMeetings` or `MeetingActivityMapping` are:
   - Imported
   - Queried
   - Used

4. Replace with interface-based approach:

   **Add adapter resolution in `MeetingLinkingService.__init__`:**
   ```python
   from shared_core.interfaces.meeting_service import MeetingServiceInterface
   from shared_core.services.adapters.noop_meeting_adapter import NoOpMeetingServiceAdapter

   def __init__(self):
       try:
           from ai_services.adapters.meeting_service_adapter import MeetingServiceAdapter
           self.meeting_service: MeetingServiceInterface = MeetingServiceAdapter()
       except ImportError:
           self.meeting_service: MeetingServiceInterface = NoOpMeetingServiceAdapter()
   ```

5. Rewrite meeting-linking logic to:
   - Use `self.meeting_service.get_recent_meetings_for_user(...)` instead of `GotoMeetings.objects.filter(...)`
   - Use `self.meeting_service.find_meeting_by_topic(...)` instead of direct queries
   - Convert dicts from interface to TaskLinks/Task.point updates

6. **Ensure:**
   - When ai_services is present: behavior matches current behavior
   - When ai_services is missing: system doesn't crash, just skips auto-linking

**Provide:**
- Refactored `MeetingLinkingService` code
- Refactored `meeting_review_views.py` if needed
- Tests for both scenarios

---

### 🔹 Prompt D3 – Refactor finance-related calls to use FinanceTaskServiceInterface

**Task:**
1. Find all places in `coda/management/` where finance models are imported/used:
   - `views.py` - LoanApplication, PayslipConfig
   - `permission.py` - Payment_History
   - Any other files

2. Replace direct imports with interface-based approach:

   **Create a helper or service class that resolves the adapter:**
   ```python
   from shared_core.interfaces.finance_task_service import FinanceTaskServiceInterface
   from shared_core.services.adapters.noop_finance_task_adapter import NoOpFinanceTaskServiceAdapter

   def get_finance_service() -> FinanceTaskServiceInterface:
       try:
           from finance.adapters.finance_task_adapter import FinanceTaskAdapter
           return FinanceTaskAdapter()
       except ImportError:
           return NoOpFinanceTaskServiceAdapter()
   ```

3. Refactor views/services to:
   - Use `finance_service.has_active_loan(user_id)` instead of `LoanApplication.objects.filter(...)`
   - Use `finance_service.get_recent_payments_for_user(user_id)` instead of direct queries
   - Handle None/empty results gracefully

4. **Ensure:**
   - If finance app is installed: behavior matches current
   - If finance app is not installed: code still runs (assumes no loans, no extra data)

**Provide:**
- Refactored views/services code
- Tests for both scenarios

---

### 🔹 Prompt D4 – Refactor professional_services calls (if interface created)

**Task:** Similar to D1-D3, but for professional_services dependencies.

**Only proceed if Prompt B4 decided to create the interface.**

**Provide:**
- Refactored code
- Tests

---

### 🔹 Prompt D5 – Handle accounts/main dependencies

**Task:** For remaining `accounts` and `main` dependencies identified in Prompt A3:

1. **TaskGroups:**
   - If it's infrastructure: Move to `shared_core.models` or `shared_core.users`
   - If it's business logic: Create minimal interface OR keep optional import

2. **main.filters:**
   - Move `RequirementFilter`, `TaskHistoryFilter` to `shared_core/filters.py`
   - Update imports in management

3. **accounts.choices:**
   - If not already in shared_core: Move to `shared_core/choices.py` or keep optional

**Provide:**
- Migration plan
- Code changes
- Tests

---

## 🧪 Phase E – Testing & Validation

### 🎯 Goal
Ensure all architectural work hasn't changed actual behavior of task, reset, pay, or assignment.

---

### 🔹 Prompt E1 – Add comprehensive tests for interfaces

**Task:** Create `coda/management/tests/test_cross_app_interfaces.py`

**Write tests that verify:**

1. **IntelligentAssignmentService:**
   - ✅ When AIServiceAdapter is present (mock it):
     - `assign_task_optimally` delegates to adapter
     - Returns expected results
   - ✅ When only NoOpAIServiceAdapter is available:
     - Service doesn't crash
     - Returns results with low/zero confidence scores
     - Still functions (graceful degradation)

2. **MeetingLinkingService:**
   - ✅ When MeetingServiceAdapter is present (mock it to return meetings):
     - Auto evidence linking creates TaskLinks
     - Task.point increments accordingly
     - Behavior matches current implementation
   - ✅ When only NoOpMeetingServiceAdapter:
     - No TaskLinks created
     - No errors thrown
     - Service continues normally

3. **Finance integration (views/services):**
   - ✅ When FinanceTaskAdapter is present (mock finance data):
     - Views/services behave as before
     - Loan checks work correctly
     - Payment history checks work
   - ✅ When only NoOpFinanceTaskServiceAdapter:
     - Views/services handle gracefully
     - No loans assumed (safe default)
     - No crashes

4. **Integration tests:**
   - ✅ Test management app with all apps present
   - ✅ Test management app with only shared_core (missing finance/ai_services/professional_services)
   - ✅ Verify no import errors
   - ✅ Verify graceful degradation

**Provide:**
- Complete test file
- Instructions for running tests
- Expected test results

---

### 🔹 Prompt E2 – Run regression tests

**Task:** Run existing management app tests to ensure nothing broke.

1. Run Django test suite:
   ```bash
   cd coda
   python manage.py test management --keepdb
   ```

2. Run system check:
   ```bash
   python manage.py check
   ```

3. Test with missing apps (temporarily rename or mock):
   - Test with ai_services unavailable
   - Test with finance unavailable
   - Test with professional_services unavailable

4. Document any failures and fix them.

**Provide:**
- Test results
- Any failures and fixes
- Confirmation that all tests pass

---

### 🔹 Prompt E3 – Create standalone test setup

**Task:** Create a way to test management app standalone (without other apps).

**Options:**
1. Create a test settings file that excludes finance/ai_services/professional_services
2. Use mocking/patching to simulate missing apps
3. Create a Docker/test environment with only management + shared_core

**Provide:**
- Test setup instructions
- Configuration files
- Documentation on how to run standalone tests

---

## 📋 Phase F – Documentation & Cleanup

### 🎯 Goal
Document the changes and ensure code is clean and maintainable.

---

### 🔹 Prompt F1 – Update documentation

**Task:** Update management app documentation to reflect the new architecture.

1. **Update `docs/apps/management/04_IMPLEMENTATION.md`:**
   - Document the interface-based approach
   - List which interfaces are used
   - Document graceful degradation behavior

2. **Create architecture diagram:**
   - Show management app dependencies on interfaces
   - Show adapter pattern
   - Show NoOp fallbacks

3. **Update README or development guide:**
   - Explain how to add new cross-app dependencies
   - Document the interface + adapter pattern
   - Show examples

**Provide:**
- Updated documentation
- Architecture diagram (text or mermaid)

---

### 🔹 Prompt F2 – Remove old direct imports (final cleanup)

**Task:** After all tests pass and everything works:

1. Remove any remaining direct imports that were replaced
2. Remove commented-out code
3. Clean up any temporary workarounds

**Ensure:**
- No direct imports from finance/ai_services/professional_services remain
- All imports go through interfaces or shared_core
- Code is clean and maintainable

**Provide:**
- List of files cleaned up
- Confirmation that no direct imports remain

---

## ✅ Success Criteria

**Phase Complete When:**
- [ ] Management app passes `python manage.py check` without finance/ai_services/professional_services
- [ ] All existing tests pass
- [ ] New interface tests pass
- [ ] Features gracefully degrade when dependencies missing
- [ ] Documentation updated
- [ ] No direct imports remain (except via interfaces/shared_core)

---

## 🚀 Next Steps After Management App

Once management app is complete:

1. **Review and document learnings:**
   - What worked well?
   - What was challenging?
   - What patterns to reuse?

2. **Move to next app** (e.g., main, accounts) following the same pattern

3. **Update architecture redesign proposal** with actual implementation details

---

**Status:** 📋 Ready to start with Prompt A1  
**Branch:** `25.12_CODA_DEV_CM`  
**Date:** December 2025
