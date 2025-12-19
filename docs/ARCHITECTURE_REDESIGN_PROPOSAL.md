# 🏗️ Architecture Redesign Proposal - Solving Dependency Hell Once and For All

## 🎯 Executive Summary

**Problem**: Despite creating `shared_core`, we still have tight coupling between apps, making lightweight branches difficult and creating architectural debt.

**Root Cause**: We've been treating symptoms (import paths) rather than the disease (architectural boundaries and communication patterns).

**Solution**: Implement proper architectural patterns: Domain Boundaries, Dependency Inversion, Event-Driven Communication, and Service Layer Abstraction.

---

## 📊 Current State: The Real Problems

### Problem 1: No Clear Domain Boundaries

**Current Reality:**
```
management/ → imports DSU from professional_services
management/ → imports LoanApplication from finance  
management/ → imports GotoMeetings from ai_services
management/ → imports RealAIService from ai_services
```

**Why This Is Bad:**
- Management app **owns** task management domain
- But it **depends on** professional_services, finance, and ai_services domains
- This creates a **web of dependencies** that makes extraction impossible
- Each app thinks it "needs" other apps' models directly

**The Question We Should Ask:**
> Does management **need** DSU, or does it **need to know about** daily standups?

### Problem 2: Direct Model Imports = Tight Coupling

**Current Pattern:**
```python
# management/views.py
from professional_services.models import DSU
from finance.models import LoanApplication
from ai_services.models import GotoMeetings

def some_view(request):
    dsu = DSU.objects.get(...)  # Direct dependency
    loan = LoanApplication.objects.get(...)  # Direct dependency
```

**Why This Is Bad:**
- Management app **cannot exist** without professional_services, finance, ai_services
- Changes in those apps **break** management app
- Testing management requires **all apps** to be present
- **No way to extract** management as standalone

### Problem 3: shared_core Only Handles Infrastructure

**What shared_core Currently Does:**
- ✅ Base model mixins (TimeStampedModel, etc.)
- ✅ Utility functions (path_values, dates_functionality)
- ✅ User models (CustomerUser, Department)
- ✅ View mixins, filters

**What shared_core Does NOT Do:**
- ❌ Cross-app communication patterns
- ❌ Service abstractions
- ❌ Event system
- ❌ Domain interfaces

**Result**: `shared_core` helps with **import paths** but doesn't solve **architectural coupling**.

### Problem 4: No Communication Patterns

**Current Approach:**
- Apps **directly import** models from other apps
- No abstraction layer
- No event system
- No service interfaces

**What We Need:**
- **Interfaces/Abstractions** for cross-app services
- **Event-driven** communication for loose coupling
- **Service layer** for cross-app operations
- **API layer** for cross-app data access

---

## 📦 Comprehensive App Dependency Analysis

### All Apps in the System

Based on codebase analysis, the following apps exist:

1. **accounts** - User management, authentication, profiles
2. **ai_services** - AI integration, meeting services, OAuth
3. **analytics** - Analytics dashboards and reporting
4. **application** - Application workflow, KCC dashboard
5. **finance** - Budget, loans, payments, transactions
6. **investing** - Trading accounts, positions, signals, managed trading
7. **main** - Core utilities, services, company info
8. **management** - Task management, employee tasks, requirements
9. **marketing** - Marketing features
10. **platform_services** - Platform-level services
11. **portfolio** - Portfolio management
12. **professional_services** - DSU, client assessments, background checks
13. **unified_dashboard** - Unified dashboard views
14. **shared_core** - Infrastructure (models, utils, users, mixins, filters)

### Dependency Matrix: Cross-App Imports Analysis

#### 1. **management** App Dependencies

**Imports From:**
- `professional_services.models` → DSU, ClientAssessment, BackgroundCheck, FeaturedCategory, FeaturedSubCategory, FeaturedActivity
- `finance.models` → LoanApplication, PayslipConfig, Payment_History
- `finance.services` → AIBudgetSuggestionService
- `ai_services.models` → GotoMeetings, ReplyMail
- `ai_services.services` → RealAIService, OAuth functions
- `accounts.models` → CustomerUser (via shared_core)
- `main.utils` → Various utilities (via shared_core)

**Dependency Count:** 59 references across 8 files

**Critical Dependencies:**
- ❌ **professional_services** - DSU forms, client assessments
- ❌ **finance** - Loan applications, payment history, budget suggestions
- ❌ **ai_services** - Meeting linking, AI predictions, OAuth

**Migration Priority:** HIGH (used as pilot in original proposal)

---

#### 2. **investing** App Dependencies

**Imports From:**
- `finance.models` → Payment_Information, Transaction (optional, already handled with try/except)
- `ai_services.models` → Editable (optional, already handled)
- `ai_services.services` → TokenEncryptionService (optional, already handled)
- `accounts.models` → CustomerUser (via shared_core)
- `main.models` → TimeStampedModel, ContractBase (via shared_core)

**Dependency Count:** ~15 references, mostly optional

**Critical Dependencies:**
- ✅ **finance** - Optional (payment info, transactions)
- ✅ **ai_services** - Optional (token encryption, editable content)

**Migration Priority:** MEDIUM (already has some optional handling)

**Current State:** Already uses `shared_core` for base models. Has try/except for optional dependencies.

---

#### 3. **main** App Dependencies

**Imports From:**
- `professional_services.models` → ClientAssessment, ActivityLinks, FeaturedActivity, FeaturedCategory, FeaturedSubCategory, DSU, Training_Responses
- `investing.models` → InvestmentContent
- `management.models` → Task, TaskHistory, Requirement, Training, Meeting, Advertisement
- `management.utils` → task_assignment_random, employee_group_level, increment_in_graduation_of_employee, loan_computation, paymentconfigurations, unique_slug_generator
- `finance.models` → BudgetRequest, Transaction, Budget, Payment_History, Food
- `ai_services.models` → Editable
- `ai_services.services` → ai_service_facade (3 references)
- `unified_dashboard.views` → get_dashboard_config, get_user_role

**Dependency Count:** ~25+ references across multiple files

**Critical Dependencies:**
- ❌ **professional_services** - Client assessments, featured content
- ❌ **investing** - Investment content
- ❌ **management** - Tasks, requirements, training
- ❌ **finance** - Budget, transactions
- ❌ **ai_services** - AI services facade
- ❌ **unified_dashboard** - Dashboard configuration

**Migration Priority:** HIGH (core app with many dependencies)

**Note:** `main` is a core app that provides utilities to other apps, but also depends on many apps. This creates circular dependency concerns.

---

#### 4. **accounts** App Dependencies

**Imports From:**
- `management.models` → Task
- `finance.models` → Payment_History, Payment_Information, LoanApplication
- `finance.utils` → Various finance utilities
- `ai_services.services` → TokenEncryptionService
- `management.utils` → unique_slug_generator

**Dependency Count:** ~10 references

**Critical Dependencies:**
- ⚠️ **management** - Task references
- ⚠️ **finance** - Payment history, loan applications
- ⚠️ **ai_services** - Token encryption

**Migration Priority:** MEDIUM (core app, but dependencies are manageable)

---

#### 5. **finance** App Dependencies

**Imports From:**
- `management.models` → Task, TaskHistory (likely)
- `accounts.models` → CustomerUser (via shared_core)
- `main.models` → Base models (via shared_core)

**Dependency Count:** Low (needs verification)

**Critical Dependencies:**
- ⚠️ **management** - Task-related features (if any)

**Migration Priority:** MEDIUM (likely depends on management for task points)

---

#### 6. **professional_services** App Dependencies

**Imports From:**
- `accounts.models` → CustomerUser (via shared_core)
- `main.models` → Base models (via shared_core)

**Dependency Count:** Low

**Critical Dependencies:**
- ✅ Minimal dependencies

**Migration Priority:** LOW (relatively independent)

---

#### 7. **ai_services** App Dependencies

**Imports From:**
- `accounts.models` → CustomerUser (via shared_core)
- `main.models` → Base models (via shared_core)

**Dependency Count:** Low

**Critical Dependencies:**
- ✅ Minimal dependencies

**Migration Priority:** LOW (provides services to others, but doesn't depend on them)

---

#### 8. **application** App Dependencies

**Imports From:**
- `accounts.models` → CustomerUser (via shared_core)
- `main.models` → Base models (via shared_core)

**Dependency Count:** Low (needs verification)

**Critical Dependencies:**
- ⚠️ Unknown (needs analysis)

**Migration Priority:** MEDIUM (needs analysis)

---

#### 9. **unified_dashboard** App Dependencies

**Imports From:**
- `accounts.models` → CustomerUser (via shared_core)
- `main.models` → Base models (via shared_core)
- Potentially other apps for dashboard data

**Dependency Count:** Low (needs verification)

**Critical Dependencies:**
- ⚠️ Likely depends on multiple apps for dashboard data

**Migration Priority:** MEDIUM (aggregates data from multiple apps)

---

### Dependency Summary Table

| App | Dependencies | Dependency Count | Migration Priority | Status |
|-----|-------------|------------------|-------------------|--------|
| **management** | professional_services, finance, ai_services | 59 references | HIGH | Needs migration |
| **main** | professional_services, investing, management, finance, ai_services, unified_dashboard | 25+ references | HIGH | Core app, complex |
| **investing** | finance (optional), ai_services (optional) | ~15 references | MEDIUM | Partially migrated |
| **accounts** | management, finance, ai_services | ~10 references | MEDIUM | Core app |
| **finance** | management (likely) | Low | MEDIUM | Needs analysis |
| **professional_services** | Minimal | Low | LOW | Relatively independent |
| **ai_services** | Minimal | Low | LOW | Service provider |
| **application** | Unknown | Unknown | MEDIUM | Needs analysis |
| **unified_dashboard** | Multiple (likely) | Unknown | MEDIUM | Aggregator |

### Key Findings

1. **management** and **main** have the highest dependency counts
2. **investing** already has some optional dependency handling (good example)
3. **professional_services** and **ai_services** are relatively independent
4. **main** is both a provider (utilities) and consumer (depends on many apps) - circular dependency risk
5. Most apps depend on **accounts** and **main** via `shared_core` (good)

### Migration Strategy by App

#### Phase 1: High Priority Apps (Weeks 1-4)
1. **management** - Pilot app (already analyzed)
2. **main** - Core app, needs careful handling

#### Phase 2: Medium Priority Apps (Weeks 5-8)
3. **accounts** - Core app, manageable dependencies
4. **investing** - Already partially migrated, complete the work
5. **finance** - Complete dependency analysis first
6. **unified_dashboard** - Aggregator pattern needed

#### Phase 3: Low Priority Apps (Weeks 9-12)
7. **professional_services** - Minimal work needed
8. **ai_services** - Service provider, create adapters
9. **application** - Complete analysis first

---

## 🏛️ Proposed Architecture: Domain-Driven Design + Dependency Inversion

### Core Principles

1. **Domain Boundaries**: Each app owns its domain completely
2. **Dependency Inversion**: Apps depend on abstractions, not concretions
3. **Event-Driven**: Cross-app communication via events, not direct calls
4. **Service Layer**: Abstract services for cross-app operations
5. **Progressive Enhancement**: Features work standalone, enhanced when dependencies available

---

## 🎨 Architecture Layers

### Layer 1: Domain Apps (Independent)

Each app is a **bounded context** with its own models, services, and business logic.

```
management/          # Task management domain
├── models/          # Task, TaskHistory, TaskCategory (OWN domain)
├── services/        # TaskStandardizationService, IntelligentAssignmentService
├── views/           # Task views
└── NO imports from other apps' models

finance/             # Finance domain
├── models/          # LoanApplication, Payment_History (OWN domain)
├── services/        # AIBudgetSuggestionService
└── NO imports from other apps' models

professional_services/  # Professional services domain
├── models/          # DSU, ClientAssessment (OWN domain)
└── NO imports from other apps' models
```

**Rule**: Apps **never** import business models from other apps.

### Layer 2: shared_core (Infrastructure + Interfaces)

**Expanded shared_core Structure:**

```
shared_core/
├── models.py           # Base model mixins (existing)
├── utils.py            # Utility functions (existing)
├── users.py            # User models (existing)
├── mixins.py           # View mixins (existing)
├── filters.py          # Django filters (existing)
│
├── interfaces/         # NEW: Service interfaces
│   ├── __init__.py
│   ├── ai_service.py   # AIServiceInterface
│   ├── finance_service.py  # FinanceServiceInterface
│   └── ps_service.py   # ProfessionalServicesInterface
│
├── events/             # NEW: Event system
│   ├── __init__.py
│   ├── publisher.py    # EventPublisher
│   ├── subscriber.py   # EventSubscriber
│   └── events.py       # Event definitions
│
└── services/           # NEW: Abstract service implementations
    ├── credential_store.py  # (existing)
    └── adapters/       # Adapters that implement interfaces
        ├── ai_adapter.py
        ├── finance_adapter.py
        └── ps_adapter.py
```

### Layer 3: App Adapters (Optional Dependencies)

Each app can **optionally** provide adapters that implement shared_core interfaces:

```
ai_services/
├── adapters/           # NEW: Implements shared_core interfaces
│   └── ai_service_adapter.py
│       class AIServiceAdapter(AIServiceInterface):
│           def predict(self, data):
│               return RealAIService().predict(data)

finance/
├── adapters/
│   └── finance_service_adapter.py
│       class FinanceServiceAdapter(FinanceServiceInterface):
│           def get_loan_info(self, user_id):
│               return LoanApplication.objects.filter(...)
```

### Layer 4: Cross-App Communication

**Pattern 1: Service Interface (For Services)**

```python
# shared_core/interfaces/ai_service.py
class AIServiceInterface:
    """Abstract interface for AI services"""
    def predict_performance(self, task_history: List[Dict]) -> Dict:
        """Predict employee performance based on task history"""
        raise NotImplementedError
    
    def suggest_assignment(self, task: Dict, employees: List[Dict]) -> Dict:
        """Suggest best employee for task assignment"""
        raise NotImplementedError

# management/services/intelligent_assignment_service.py
from shared_core.interfaces.ai_service import AIServiceInterface

class IntelligentAssignmentService:
    def __init__(self):
        # Try to get concrete implementation
        try:
            from ai_services.adapters.ai_service_adapter import AIServiceAdapter
            self.ai_service: AIServiceInterface = AIServiceAdapter()
        except ImportError:
            # Fallback to no-op implementation
            from shared_core.services.adapters.noop_ai_adapter import NoOpAIServiceAdapter
            self.ai_service: AIServiceInterface = NoOpAIServiceAdapter()
    
    def assign_task(self, task, employees):
        # Use interface, not concrete class
        suggestions = self.ai_service.suggest_assignment(task, employees)
        # ... rest of logic
```

**Pattern 2: Event-Driven (For Data Changes)**

```python
# shared_core/events/events.py
class TaskCompletedEvent:
    """Event published when a task is completed"""
    def __init__(self, task_id: int, user_id: int, points: int):
        self.task_id = task_id
        self.user_id = user_id
        self.points = points

# management/services/task_reset_service.py
from shared_core.events.publisher import EventPublisher

class TaskResetService:
    def complete_task(self, task):
        # ... complete task logic ...
        
        # Publish event (loose coupling)
        EventPublisher.publish(
            TaskCompletedEvent(
                task_id=task.id,
                user_id=task.assigned_to.id,
                points=task.points
            )
        )

# finance/services/task_points_handler.py (optional subscriber)
from shared_core.events.subscriber import EventSubscriber
from shared_core.events.events import TaskCompletedEvent

@EventSubscriber.subscribe(TaskCompletedEvent)
def handle_task_completed(event: TaskCompletedEvent):
    """Update finance records when task is completed"""
    # This only runs if finance app is installed
    # Management app doesn't know or care about this
    update_payment_history(event.user_id, event.points)
```

**Pattern 3: Query Interface (For Data Access)**

```python
# shared_core/interfaces/finance_service.py
class FinanceServiceInterface:
    """Abstract interface for finance data access"""
    def get_user_loan_status(self, user_id: int) -> Optional[Dict]:
        """Get user's loan application status"""
        raise NotImplementedError
    
    def has_active_loan(self, user_id: int) -> bool:
        """Check if user has active loan"""
        raise NotImplementedError

# management/views.py
from shared_core.interfaces.finance_service import FinanceServiceInterface

def task_assignment_view(request):
    # Get finance service (optional)
    try:
        from finance.adapters.finance_service_adapter import FinanceServiceAdapter
        finance_service: FinanceServiceInterface = FinanceServiceAdapter()
    except ImportError:
        finance_service = None
    
    # Use interface
    if finance_service and finance_service.has_active_loan(user.id):
        # Show loan-related tasks
        pass
```

---

## 🔄 Comprehensive Migration Strategy (All Apps)

### Phase 1: Foundation & Infrastructure (Weeks 1-2)

#### Week 1: Create Interfaces and Event System

1. **Create shared_core/interfaces/**
   - `AIServiceInterface` - AI prediction, assignment, meeting analysis
   - `FinanceServiceInterface` - Loan status, payment history, budget
   - `ProfessionalServicesInterface` - DSU, client assessments
   - `ManagementServiceInterface` - Task queries, task history
   - `InvestingServiceInterface` - Position data, account info
   - `ApplicationServiceInterface` - Application workflow data

2. **Create Event System**
   - `shared_core/events/publisher.py` - EventPublisher class
   - `shared_core/events/subscriber.py` - EventSubscriber decorator
   - `shared_core/events/events.py` - Event definitions:
     - `TaskCompletedEvent`
     - `TaskCreatedEvent`
     - `LoanApplicationCreatedEvent`
     - `PositionApprovedEvent`
     - `PaymentProcessedEvent`
     - `UserCreatedEvent`

3. **Create No-Op Implementations**
   - `NoOpAIServiceAdapter`
   - `NoOpFinanceServiceAdapter`
   - `NoOpProfessionalServicesAdapter`
   - `NoOpManagementServiceAdapter`
   - `NoOpInvestingServiceAdapter`
   - `NoOpApplicationServiceAdapter`

#### Week 2: Create App Adapters

1. **Create adapters for service-providing apps**
   - `ai_services/adapters/ai_service_adapter.py`
   - `finance/adapters/finance_service_adapter.py`
   - `professional_services/adapters/ps_service_adapter.py`
   - `management/adapters/management_service_adapter.py`
   - `investing/adapters/investing_service_adapter.py`
   - `application/adapters/application_service_adapter.py`

2. **Implement interfaces in adapters**
   - Each adapter wraps existing services/models
   - Maintains backward compatibility

---

### Phase 2: High-Priority Apps Migration (Weeks 3-6)

#### Week 3-4: Migrate **management** App (Pilot)

1. **Audit all imports**
   - Document all cross-app imports
   - Categorize by type (model, service, view)

2. **Replace with interfaces**
   - Replace `professional_services.models` imports → `ProfessionalServicesInterface`
   - Replace `finance.models` imports → `FinanceServiceInterface`
   - Replace `ai_services.services` imports → `AIServiceInterface`

3. **Add event publishing**
   - Publish `TaskCompletedEvent` when tasks complete
   - Publish `TaskCreatedEvent` when tasks created

4. **Test standalone**
   - Verify management works without other apps
   - Test graceful degradation

#### Week 5-6: Migrate **main** App

1. **Audit dependencies**
   - Document all cross-app imports (25+ references)
   - Identify circular dependency risks

2. **Create service interfaces for main**
   - `MainServiceInterface` - Core utilities, company info
   - Other apps can optionally use main services

3. **Replace imports**
   - Replace `professional_services.models` → `ProfessionalServicesInterface`
   - Replace `investing.models` → `InvestingServiceInterface`
   - Replace `management.models` → `ManagementServiceInterface`
   - Replace `finance.models` → `FinanceServiceInterface`
   - Replace `ai_services.services` → `AIServiceInterface`

4. **Handle circular dependencies**
   - Main provides utilities (via shared_core)
   - Main consumes services (via interfaces)
   - Clear separation of concerns

---

### Phase 3: Medium-Priority Apps Migration (Weeks 7-10)

#### Week 7-8: Migrate **accounts** and **investing** Apps

**accounts App:**
1. Replace `management.models` → `ManagementServiceInterface`
2. Replace `finance.models` → `FinanceServiceInterface`
3. Replace `ai_services.services` → `AIServiceInterface`
4. Publish `UserCreatedEvent` when users created

**investing App:**
1. Complete optional dependency handling
2. Replace `finance.models` → `FinanceServiceInterface` (if needed)
3. Replace `ai_services.services` → `AIServiceInterface` (if needed)
4. Create `InvestingServiceAdapter` for other apps
5. Publish `PositionApprovedEvent`, `PositionCreatedEvent`

#### Week 9-10: Migrate **finance** and **unified_dashboard** Apps

**finance App:**
1. Complete dependency analysis
2. Replace `management.models` → `ManagementServiceInterface` (if any)
3. Create `FinanceServiceAdapter`
4. Subscribe to `TaskCompletedEvent` (if needed)
5. Publish `PaymentProcessedEvent`, `LoanApplicationCreatedEvent`

**unified_dashboard App:**
1. Create aggregator pattern
   - Use interfaces to query data from multiple apps
   - No direct model imports
2. Replace all cross-app imports with interfaces
3. Handle missing apps gracefully

---

### Phase 4: Low-Priority Apps & Cleanup (Weeks 11-12)

#### Week 11: Migrate **professional_services** and **ai_services** Apps

**professional_services App:**
1. Create `ProfessionalServicesServiceAdapter`
2. Publish events for DSU, assessments
3. Minimal work (already independent)

**ai_services App:**
1. Create `AIServiceAdapter` (already planned)
2. Publish events for meeting analysis
3. Service provider role

#### Week 12: Final Cleanup & Testing

1. **Remove all direct model imports**
   - Audit all apps for remaining direct imports
   - Replace with interfaces/events

2. **Comprehensive testing**
   - Test each app standalone
   - Test with all apps present
   - Test graceful degradation
   - Performance testing

3. **Documentation**
   - Document all interfaces
   - Document event system
   - Create migration guide
   - Update developer guidelines

---

### Migration Checklist by App

#### management App
- [ ] Audit 59 cross-app references
- [ ] Create interfaces for professional_services, finance, ai_services
- [ ] Replace direct imports with interfaces
- [ ] Add event publishing (TaskCompletedEvent, TaskCreatedEvent)
- [ ] Test standalone operation
- [ ] Test graceful degradation

#### main App
- [ ] Audit 25+ cross-app references
- [ ] Create MainServiceInterface for utilities
- [ ] Replace all cross-app imports
- [ ] Handle circular dependencies
- [ ] Test standalone operation

#### accounts App
- [ ] Audit ~10 cross-app references
- [ ] Replace management, finance, ai_services imports
- [ ] Add UserCreatedEvent publishing
- [ ] Test standalone operation

#### investing App
- [ ] Complete optional dependency handling
- [ ] Create InvestingServiceAdapter
- [ ] Add PositionApprovedEvent, PositionCreatedEvent
- [ ] Test standalone operation

#### finance App
- [ ] Complete dependency analysis
- [ ] Create FinanceServiceAdapter
- [ ] Subscribe to TaskCompletedEvent (if needed)
- [ ] Add PaymentProcessedEvent, LoanApplicationCreatedEvent
- [ ] Test standalone operation

#### unified_dashboard App
- [ ] Create aggregator pattern
- [ ] Replace all cross-app imports with interfaces
- [ ] Test with missing apps

#### professional_services App
- [ ] Create ProfessionalServicesServiceAdapter
- [ ] Add event publishing
- [ ] Test standalone operation

#### ai_services App
- [ ] Create AIServiceAdapter
- [ ] Add event publishing
- [ ] Test standalone operation

---

## 📋 Implementation Plan

### Step 1: Expand shared_core

```bash
mkdir -p coda/shared_core/interfaces
mkdir -p coda/shared_core/events
mkdir -p coda/shared_core/services/adapters
```

### Step 2: Define Interfaces

**File: `coda/shared_core/interfaces/ai_service.py`**
```python
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

class AIServiceInterface(ABC):
    """Abstract interface for AI services"""
    
    @abstractmethod
    def predict_performance(self, task_history: List[Dict]) -> Dict:
        """Predict employee performance based on task history"""
        pass
    
    @abstractmethod
    def suggest_assignment(self, task: Dict, employees: List[Dict]) -> Dict:
        """Suggest best employee for task assignment"""
        pass
    
    @abstractmethod
    def analyze_meeting(self, meeting_data: Dict) -> Dict:
        """Analyze meeting and suggest task links"""
        pass
```

**File: `coda/shared_core/services/adapters/noop_ai_adapter.py`**
```python
from shared_core.interfaces.ai_service import AIServiceInterface

class NoOpAIServiceAdapter(AIServiceInterface):
    """No-op implementation when AI services not available"""
    
    def predict_performance(self, task_history: List[Dict]) -> Dict:
        return {"prediction": None, "confidence": 0.0}
    
    def suggest_assignment(self, task: Dict, employees: List[Dict]) -> Dict:
        return {"suggested_employee": None, "score": 0.0}
    
    def analyze_meeting(self, meeting_data: Dict) -> Dict:
        return {"suggested_tasks": [], "confidence": 0.0}
```

### Step 3: Update Management to Use Interfaces

**File: `coda/management/services/intelligent_assignment_service.py`**
```python
from shared_core.interfaces.ai_service import AIServiceInterface
from shared_core.services.adapters.noop_ai_adapter import NoOpAIServiceAdapter

class IntelligentAssignmentService:
    def __init__(self):
        # Try to get concrete implementation
        try:
            from ai_services.adapters.ai_service_adapter import AIServiceAdapter
            self.ai_service: AIServiceInterface = AIServiceAdapter()
        except ImportError:
            # Fallback to no-op
            self.ai_service: AIServiceInterface = NoOpAIServiceAdapter()
    
    def assign_task(self, task, employees):
        # Use interface - doesn't know about RealAIService
        suggestions = self.ai_service.suggest_assignment(
            task.to_dict(),
            [emp.to_dict() for emp in employees]
        )
        # ... rest of logic
```

### Step 4: Create App Adapters

**File: `coda/ai_services/adapters/ai_service_adapter.py`**
```python
from shared_core.interfaces.ai_service import AIServiceInterface
from ai_services.ai_integration_service import RealAIService

class AIServiceAdapter(AIServiceInterface):
    """Concrete implementation using RealAIService"""
    
    def __init__(self):
        self._service = RealAIService()
    
    def predict_performance(self, task_history: List[Dict]) -> Dict:
        return self._service.predict_performance(task_history)
    
    def suggest_assignment(self, task: Dict, employees: List[Dict]) -> Dict:
        return self._service.suggest_assignment(task, employees)
    
    def analyze_meeting(self, meeting_data: Dict) -> Dict:
        return self._service.analyze_meeting(meeting_data)
```

---

## ✅ Benefits of This Architecture

### 1. True Independence
- Each app can work **standalone**
- Management doesn't need ai_services, finance, professional_services
- Features gracefully degrade when dependencies missing

### 2. Clear Boundaries
- Each app owns its domain completely
- Cross-app communication via **interfaces**, not models
- Easy to understand what depends on what

### 3. Easy Testing
- Test management app without other apps
- Mock interfaces for unit tests
- Test adapters separately

### 4. Easy Extraction
- To extract management: copy `management/` + `shared_core/`
- No need to copy other apps
- Interfaces ensure compatibility

### 5. Progressive Enhancement
- Apps work **basically** without dependencies
- Apps work **better** with dependencies
- No all-or-nothing approach

### 6. Future-Proof
- Add new apps without breaking existing ones
- Change implementations without breaking interfaces
- Scale horizontally (microservices-ready)

---

## 🎯 Decision Points

### Question 1: How Strict Should We Be?

**Option A: Strict (Recommended)**
- **Zero** direct model imports between apps
- **All** cross-app communication via interfaces/events
- **Maximum** independence, but more refactoring

**Option B: Pragmatic**
- Allow **read-only** model imports (no writes)
- Use interfaces for **services**
- Use events for **writes/triggers**
- **Balance** between independence and refactoring effort

**Recommendation**: Start with **Option B**, migrate to **Option A** over time.

### Question 2: What Goes in shared_core?

**Current**: Infrastructure only (models, utils, users)

**Proposed**: Infrastructure + Interfaces + Events

**Decision**: 
- ✅ **Interfaces** - Yes, these are shared contracts
- ✅ **Events** - Yes, these are shared communication patterns
- ❌ **Business Models** - No, these stay in domain apps
- ❌ **Concrete Services** - No, these stay in domain apps

### Question 3: How to Handle Existing Code?

**Strategy**: Gradual Migration
1. **New code** uses interfaces/events from day 1
2. **Existing code** migrates gradually
3. **Critical paths** migrate first
4. **Low-priority paths** can wait

---

## 📊 Comparison: Before vs After

### Before (Current)
```
management/
├── imports DSU from professional_services ❌
├── imports LoanApplication from finance ❌
├── imports GotoMeetings from ai_services ❌
└── Cannot work without 3 other apps ❌
```

### After (Proposed)
```
management/
├── uses AIServiceInterface (from shared_core) ✅
├── uses FinanceServiceInterface (from shared_core) ✅
├── uses ProfessionalServicesInterface (from shared_core) ✅
└── Works standalone, enhanced with dependencies ✅
```

---

## 🚀 Next Steps

### Immediate Actions (Week 1)

1. **Review this proposal** - Discuss and refine with team
2. **Decide on strictness level** - Option A (strict) or Option B (pragmatic)
3. **Approve migration timeline** - 12-week plan for all apps
4. **Assign app owners** - Each app needs a migration owner

### Phase 1: Foundation (Weeks 1-2)

5. **Create interfaces** - All service interfaces in shared_core
6. **Create event system** - Publisher, subscriber, event definitions
7. **Create no-op adapters** - Fallback implementations
8. **Create app adapters** - Service-providing apps create adapters

### Phase 2: High-Priority Migration (Weeks 3-6)

9. **Migrate management app** - Use as pilot, document learnings
10. **Migrate main app** - Handle circular dependencies carefully
11. **Test standalone** - Verify both apps work independently
12. **Document patterns** - Create guide based on pilot experience

### Phase 3: Medium-Priority Migration (Weeks 7-10)

13. **Migrate accounts app** - Core app, manageable dependencies
14. **Migrate investing app** - Complete optional dependency work
15. **Migrate finance app** - Complete analysis, then migrate
16. **Migrate unified_dashboard** - Aggregator pattern

### Phase 4: Low-Priority & Cleanup (Weeks 11-12)

17. **Migrate professional_services** - Minimal work
18. **Migrate ai_services** - Service provider
19. **Final cleanup** - Remove all direct imports
20. **Comprehensive testing** - All apps standalone and together
21. **Update documentation** - Complete migration guide

### Success Metrics

- ✅ All apps work standalone
- ✅ Zero direct model imports between apps
- ✅ All cross-app communication via interfaces/events
- ✅ Features gracefully degrade when dependencies missing
- ✅ Performance maintained or improved
- ✅ Test coverage maintained or improved

---

## 📚 References

- **Domain-Driven Design** - Bounded contexts, domain boundaries
- **Dependency Inversion Principle** - Depend on abstractions, not concretions
- **Event-Driven Architecture** - Loose coupling via events
- **Service Layer Pattern** - Abstract service interfaces
- **Hexagonal Architecture** - Ports and adapters

---

**Created**: December 2025  
**Status**: 📋 Proposal - Awaiting Review and Decision  

