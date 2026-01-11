# Step 2: Management App Dependency Analysis & Classification

**Date:** December 2025  
**Branch:** `25.12_CODA_DEV_CM`  
**Purpose:** Classify each cross-app dependency in management app and determine refactoring strategy

---

## Dependency Classification System

Each dependency is classified as:

- **TRUE SHARED** - Should move to `shared_core` (infrastructure, common models, utilities)
- **ONE-WAY DEPENDENCY** - Acceptable but needs interface/optional handling (services, optional features)
- **LEAKY/BAD** - Domain-to-domain coupling that should be refactored (direct model imports, tight coupling)

---

## 1. `professional_services` Dependencies

### A. Direct Model Imports (4 files)

#### File 1: `coda/management/models.py:17`
```python
from professional_services.models import FeaturedCategory, FeaturedSubCategory, FeaturedActivity
```

**Usage:**
- `Training` model uses these as ForeignKeys:
  - `category = ForeignKey(FeaturedCategory)`
  - `subcategory = ForeignKey(FeaturedSubCategory)`
  - `topic = ForeignKey(FeaturedActivity)`
- Lines 48-69 in `models.py`

**Classification:** ⚠️ **LEAKY/BAD**

**Reason:**
- Management's `Training` model directly depends on professional_services domain models
- These are used as ForeignKeys, creating database-level coupling
- Management cannot work without professional_services installed

**Refactoring Options:**
1. **Option A (Recommended):** Move `FeaturedCategory`, `FeaturedSubCategory`, `FeaturedActivity` to `shared_core.models` if they're truly shared taxonomy
2. **Option B:** Create management's own `TrainingCategory`, `TrainingSubCategory`, `TrainingActivity` models
3. **Option C:** Make ForeignKeys nullable and optional, use interface pattern

**Recommendation:** Check if these models are used by other apps. If yes → Option A. If no → Option B.

---

#### File 2: `coda/management/views.py:86`
```python
from professional_services.models import DSU, ClientAssessment, BackgroundCheck
```

**Usage:**
- `DSUListView` (line 2019) - Lists DSU records
- `AssessUpdateView` (line 2031) - Updates DSU records
- `ClientAssessmentListView` (line 2214) - Lists client assessments
- `clientassessment()` view (line 2100) - Creates client assessments
- Background check views (referenced in URLs)

**Classification:** ⚠️ **LEAKY/BAD**

**Reason:**
- Management views directly import and use professional_services models
- These are HR/assessment features that management app provides UI for
- Management cannot work without professional_services installed

**Refactoring Options:**
1. **Option A:** Move these models to `shared_core` if they're shared HR infrastructure
2. **Option B:** Create interface pattern (`ProfessionalServicesInterface`) with no-op adapter
3. **Option C:** Make these views optional/conditional (check if app installed)

**Recommendation:** These seem like HR features that management provides UI for. Option B (interface pattern) is safest.

---

#### File 3: `coda/management/forms.py:5`
```python
from professional_services.models import DSU, ClientAssessment, BackgroundCheck
```

**Usage:**
- `ClientAssessmentForm` (line 96) - Form for client assessments
- Forms for DSU and BackgroundCheck (referenced)

**Classification:** ⚠️ **LEAKY/BAD**

**Reason:**
- Forms directly reference professional_services models
- Same issue as views - tight coupling

**Refactoring Options:**
- Same as File 2 (views) - use interface pattern or move to shared

---

#### File 4: `coda/management/signals.py`
```python
from professional_services.models import ClientAssessment
```

**Usage:**
- Signal handlers that react to ClientAssessment changes

**Classification:** ⚠️ **LEAKY/BAD**

**Reason:**
- Signals create tight coupling between apps
- Management signals cannot run without professional_services

**Refactoring Options:**
- Use event system (if implemented) OR make signals conditional

---

**Summary: `professional_services` Dependencies**

| File | Models Used | Classification | Refactoring Priority |
|------|-------------|----------------|---------------------|
| `models.py` | `FeaturedCategory`, `FeaturedSubCategory`, `FeaturedActivity` | **LEAKY/BAD** | HIGH (FK dependencies) |
| `views.py` | `DSU`, `ClientAssessment`, `BackgroundCheck` | **LEAKY/BAD** | HIGH (UI features) |
| `forms.py` | `DSU`, `ClientAssessment`, `BackgroundCheck` | **LEAKY/BAD** | HIGH (form dependencies) |
| `signals.py` | `ClientAssessment` | **LEAKY/BAD** | MEDIUM (signal coupling) |

**Total:** 4 files, all **LEAKY/BAD**

---

## 2. `ai_services` Dependencies

### A. Interface Pattern (✅ GOOD - 5 files)

#### File 1: `coda/management/services/intelligent_assignment_service.py:45`
```python
from ai_services.adapters.ai_service_adapter import AIServiceAdapter
```

**Usage:**
- Uses `AIServiceInterface` via adapter
- Has graceful fallback to `NoOpAIServiceAdapter`
- Lines 37-50

**Classification:** ✅ **ONE-WAY DEPENDENCY** (Good Pattern)

**Status:** ✅ Already using interface pattern correctly

---

#### File 2: `coda/management/services/meeting_linking_service.py:53`
```python
from ai_services.adapters.meeting_service_adapter import MeetingServiceAdapter
```

**Usage:**
- Uses `MeetingServiceInterface` via adapter
- Has graceful fallback to `NoOpMeetingServiceAdapter`
- Lines 45-58

**Classification:** ✅ **ONE-WAY DEPENDENCY** (Good Pattern)

**Status:** ✅ Already using interface pattern correctly

---

#### File 3: `coda/management/services/ai_prediction_service.py`
```python
from ai_services.adapters.ai_service_adapter import AIServiceAdapter
```

**Usage:**
- Uses interface pattern for AI predictions

**Classification:** ✅ **ONE-WAY DEPENDENCY** (Good Pattern)

**Status:** ✅ Already using interface pattern correctly

---

#### File 4: `coda/management/services/utilities_service.py`
```python
from ai_services.adapters.ai_service_adapter import AIServiceAdapter
```

**Usage:**
- Uses interface pattern for AI utilities

**Classification:** ✅ **ONE-WAY DEPENDENCY** (Good Pattern)

**Status:** ✅ Already using interface pattern correctly

---

#### File 5: `coda/management/models/base_models.py`
```python
from ai_services.adapters.ai_service_adapter import AIServiceAdapter
```

**Usage:**
- Uses interface pattern in models

**Classification:** ✅ **ONE-WAY DEPENDENCY** (Good Pattern)

**Status:** ✅ Already using interface pattern correctly

---

### B. Direct Service Imports (⚠️ NEEDS CLEANUP - 5 files)

#### File 6: `coda/management/services/daf_summary_service.py` (4 locations)
```python
from ai_services.services.ai_insight_service import AIInsightService
```

**Locations:**
- Line 787 (in method)
- Line 828 (in method)
- Line 868 (in method)
- Line 911 (in method)

**Usage:**
- Direct import of `AIInsightService` (not using interface)
- Used for AI insights in DAF summary

**Classification:** ⚠️ **ONE-WAY DEPENDENCY** (Needs Interface Pattern)

**Refactoring:**
- Should use `AIServiceInterface` via adapter pattern
- Add try/except with fallback to no-op adapter

**Priority:** MEDIUM (works but not graceful degradation)

---

#### File 7: `coda/management/services/release_engine.py`
```python
from ai_services.services.ai_insight_service import AIInsightService
```

**Usage:**
- Direct import for AI insights in release engine

**Classification:** ⚠️ **ONE-WAY DEPENDENCY** (Needs Interface Pattern)

**Refactoring:** Same as File 6

---

#### File 8: `coda/management/views/base_views.py`
```python
from ai_services.ai_integration_service import RealAIService
```

**Usage:**
- Direct import of `RealAIService` (legacy pattern)

**Classification:** ⚠️ **ONE-WAY DEPENDENCY** (Legacy Pattern)

**Refactoring:** Migrate to interface pattern

---

#### File 9: `coda/management/services/taskhistory_analyzer.py`
```python
from ai_services.ai_integration_service import RealAIService
```

**Usage:**
- Direct import for task history analysis

**Classification:** ⚠️ **ONE-WAY DEPENDENCY** (Legacy Pattern)

**Refactoring:** Migrate to interface pattern

---

### C. OAuth Helpers (⚠️ NEEDS MOVING - 1 file)

#### File 10: `coda/management/views.py:159`
```python
from ai_services.views import (
    get_oauth_redirect_uri,
    get_authorization_url,
    exchange_code_for_tokens,
    # ... more OAuth helpers
)
```

**Usage:**
- OAuth helper functions for Google/other OAuth providers
- Used in management views for OAuth flows

**Classification:** ⚠️ **TRUE SHARED** (Should Move)

**Reason:**
- OAuth helpers are utility functions, not domain-specific
- Should be in `shared_core.utils` or `shared_core.services.oauth`

**Refactoring:**
- Move OAuth helpers to `shared_core.utils.oauth` or `shared_core.services.oauth`
- Update imports in management and ai_services

**Priority:** MEDIUM (works but not ideal location)

---

### D. Test Files (3 files)

#### Files: `coda/management/tests/test_*.py`
```python
from ai_services.services.ai_insight_service import AIInsightService
```

**Classification:** ✅ **ONE-WAY DEPENDENCY** (Test Dependencies OK)

**Status:** ✅ Tests can depend on external apps (acceptable)

---

**Summary: `ai_services` Dependencies**

| File | Pattern | Classification | Status |
|------|---------|----------------|--------|
| `services/intelligent_assignment_service.py` | Interface | ✅ ONE-WAY | ✅ Good |
| `services/meeting_linking_service.py` | Interface | ✅ ONE-WAY | ✅ Good |
| `services/ai_prediction_service.py` | Interface | ✅ ONE-WAY | ✅ Good |
| `services/utilities_service.py` | Interface | ✅ ONE-WAY | ✅ Good |
| `models/base_models.py` | Interface | ✅ ONE-WAY | ✅ Good |
| `services/daf_summary_service.py` | Direct | ⚠️ ONE-WAY | ⚠️ Needs cleanup |
| `services/release_engine.py` | Direct | ⚠️ ONE-WAY | ⚠️ Needs cleanup |
| `views/base_views.py` | Direct (legacy) | ⚠️ ONE-WAY | ⚠️ Needs cleanup |
| `services/taskhistory_analyzer.py` | Direct (legacy) | ⚠️ ONE-WAY | ⚠️ Needs cleanup |
| `views.py` (OAuth) | Direct (helpers) | ⚠️ TRUE SHARED | ⚠️ Should move |
| `tests/*.py` (3 files) | Direct | ✅ ONE-WAY | ✅ OK for tests |

**Total:** 11 files
- ✅ 5 files using interface pattern correctly
- ⚠️ 5 files need cleanup (migrate to interface)
- ⚠️ 1 file (OAuth helpers) should move to shared

---

## 3. `finance` Dependencies

### A. Interface Pattern (✅ GOOD - 1 file)

#### File 1: `coda/management/services/finance_service_helper.py:65`
```python
from finance.adapters.finance_task_adapter import FinanceTaskAdapter
```

**Usage:**
- Uses `FinanceTaskServiceInterface` via adapter
- Has graceful fallback to `NoOpFinanceTaskServiceAdapter`
- Lines 64-73

**Classification:** ✅ **ONE-WAY DEPENDENCY** (Good Pattern)

**Status:** ✅ Already using interface pattern correctly

---

### B. Direct Model Import (⚠️ NEEDS CLEANUP - 1 file)

#### File 2: `coda/management/views.py:968`
```python
from finance.models import PayslipConfig
```

**Usage:**
- Used in `get_user_data()` function (line 965)
- Accesses `PayslipConfig` model directly

**Classification:** ⚠️ **LEAKY/BAD**

**Reason:**
- Direct model import creates tight coupling
- Management cannot work without finance app installed
- However, `paymentconfigurations()` in `utils.py` already uses interface pattern

**Refactoring:**
- Should use `FinanceTaskServiceInterface.get_payslip_config()` instead
- Already has interface pattern available in `finance_service_helper.py`

**Priority:** HIGH (inconsistent - utils.py uses interface, views.py uses direct import)

---

### C. Direct Service Import (⚠️ NEEDS CLEANUP - 2 files)

#### File 3: `coda/management/services/utilities_service.py`
```python
from finance.services.ai_budget_suggestion_service import AIBudgetSuggestionService
```

**Usage:**
- Direct import for budget suggestions

**Classification:** ⚠️ **ONE-WAY DEPENDENCY** (Needs Interface)

**Refactoring:**
- Should use interface pattern or make optional

---

#### File 4: `coda/management/views/base_views.py`
```python
from finance.services.ai_budget_suggestion_service import AIBudgetSuggestionService
```

**Usage:**
- Direct import for budget suggestions in views

**Classification:** ⚠️ **ONE-WAY DEPENDENCY** (Needs Interface)

**Refactoring:**
- Should use interface pattern or make optional

---

**Summary: `finance` Dependencies**

| File | Pattern | Classification | Status |
|------|---------|----------------|--------|
| `services/finance_service_helper.py` | Interface | ✅ ONE-WAY | ✅ Good |
| `views.py` (PayslipConfig) | Direct model | ⚠️ LEAKY/BAD | ⚠️ Needs cleanup |
| `services/utilities_service.py` | Direct service | ⚠️ ONE-WAY | ⚠️ Needs cleanup |
| `views/base_views.py` | Direct service | ⚠️ ONE-WAY | ⚠️ Needs cleanup |

**Total:** 4 files
- ✅ 1 file using interface pattern correctly
- ⚠️ 1 file with direct model import (LEAKY)
- ⚠️ 2 files with direct service imports (needs interface)

---

## 4. Other Dependencies (Infrastructure)

### `accounts` Dependencies

| File | Import | Classification | Status |
|------|--------|----------------|--------|
| `views.py:42` | `from accounts.utils import send_verification_email, calculate_login_bonus` | ⚠️ TRUE SHARED | Should move to shared_core |
| `views.py:44` | `from accounts.views import create_profile` | ⚠️ ONE-WAY | Acceptable (view dependency) |
| `views.py:69` | `from accounts.models import UserProfile` | ⚠️ TRUE SHARED | Should move to shared_core |
| `views.py:89` | `from accounts.models import Tracker, TaskGroups` | ⚠️ TRUE SHARED | Should move to shared_core |
| `forms.py:9` | `from accounts.models import UserProfile` | ⚠️ TRUE SHARED | Should move to shared_core |
| `models.py:16` | `from accounts.models import TaskGroups` | ⚠️ TRUE SHARED | Should move to shared_core |

**Note:** Some of these might already be in `shared_core.users` - need to verify.

---

### `main` Dependencies

| File | Import | Classification | Status |
|------|--------|----------------|--------|
| `views.py:90` | `from main.filters import RequirementFilter, TaskHistoryFilter` | ⚠️ TRUE SHARED | Should move to shared_core.filters |

**Note:** `shared_core.filters` exists but doesn't include these yet.

---

### `core` Dependencies

| File | Import | Classification | Status |
|------|--------|----------------|--------|
| `views.py:43` | `from core.utils import generate_password` | ⚠️ TRUE SHARED | Should move to shared_core.utils |

---

## 5. Complete Dependency Classification Table

### Summary by Classification

| Classification | Count | Files | Priority |
|----------------|-------|-------|----------|
| **LEAKY/BAD** | 6 files | `models.py`, `views.py` (2x), `forms.py`, `signals.py`, `views.py` (PayslipConfig) | **HIGH** |
| **ONE-WAY (Needs Cleanup)** | 7 files | `daf_summary_service.py`, `release_engine.py`, `base_views.py` (2x), `taskhistory_analyzer.py`, `utilities_service.py` (2x) | **MEDIUM** |
| **ONE-WAY (Good Pattern)** | 6 files | `intelligent_assignment_service.py`, `meeting_linking_service.py`, `ai_prediction_service.py`, `utilities_service.py`, `base_models.py`, `finance_service_helper.py` | ✅ **DONE** |
| **TRUE SHARED** | 8+ files | OAuth helpers, accounts utils/models, main filters, core utils | **MEDIUM** |

---

## 6. Refactoring Recommendations

### Priority 1: Fix LEAKY/BAD Dependencies (HIGH)

1. **`professional_services` Models:**
   - **Option A:** Move `FeaturedCategory`, `FeaturedSubCategory`, `FeaturedActivity` to `shared_core.models` if shared
   - **Option B:** Create management's own training taxonomy models
   - **Option C:** Make ForeignKeys nullable, use interface pattern

2. **`professional_services` Views/Forms:**
   - Create `ProfessionalServicesInterface` in `shared_core.interfaces`
   - Create no-op adapter
   - Update views/forms to use interface

3. **`finance.models.PayslipConfig`:**
   - Use `FinanceTaskServiceInterface.get_payslip_config()` instead
   - Already has interface available in `finance_service_helper.py`

### Priority 2: Clean Up Direct Imports (MEDIUM)

1. **AI Services Direct Imports:**
   - Migrate `daf_summary_service.py` to use `AIServiceInterface`
   - Migrate `release_engine.py` to use `AIServiceInterface`
   - Migrate `base_views.py` to use `AIServiceInterface`
   - Migrate `taskhistory_analyzer.py` to use `AIServiceInterface`

2. **Finance Services Direct Imports:**
   - Migrate `utilities_service.py` to use interface pattern
   - Migrate `base_views.py` to use interface pattern

### Priority 3: Move TRUE SHARED (MEDIUM)

1. **OAuth Helpers:**
   - Move from `ai_services.views` to `shared_core.utils.oauth`
   - Update imports in management and ai_services

2. **Accounts Utils/Models:**
   - Move `UserProfile`, `Tracker`, `TaskGroups` to `shared_core.users` (if not already)
   - Move `send_verification_email`, `calculate_login_bonus` to `shared_core.utils`

3. **Main Filters:**
   - Move `RequirementFilter`, `TaskHistoryFilter` to `shared_core.filters`

4. **Core Utils:**
   - Move `generate_password` to `shared_core.utils`

---

## 7. Next Steps for Step 3

Step 3 will:
1. Identify what's already in `shared_core` vs what's missing
2. Check if models like `FeaturedCategory` are truly shared or management-specific
3. Design concrete refactoring plan for each dependency
4. Create step-by-step implementation plan

---

**Report Generated:** December 2025  
**Next:** Step 3 - Identify what "shared folder" work already exists

