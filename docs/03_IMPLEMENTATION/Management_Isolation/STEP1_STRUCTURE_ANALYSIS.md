# Step 1: Repository Structure & Shared Module Analysis

**Date:** December 2025  
**Branch:** `25.12_CODA_DEV_CM`  
**Purpose:** Map current structure and identify shared code for Management app isolation

---

## 1. Project Structure

### Project Root
- **Path:** `/Users/coda/Projects/uat/`
- **manage.py location:** `coda/manage.py`
- **Django project package:** `coda_project/` (settings at `coda/coda_project/settings.py`)

### Django Apps (Found via `apps.py` files)

| App Name | Path | Status |
|----------|------|--------|
| **shared_core** | `coda/shared_core/` | ✅ Shared infrastructure |
| **main** | `coda/main/` | Domain app |
| **accounts** | `coda/accounts/` | Domain app |
| **application** | `coda/application/` | Domain app |
| **professional_services** | `coda/professional_services/` | Domain app |
| **ai_services** | `coda/ai_services/` | Domain app |
| **investing** | `coda/investing/` | Domain app |
| **management** | `coda/management/` | **TARGET APP** |
| **finance** | `coda/finance/` | Domain app |
| **marketing** | `coda/marketing/` | Domain app |
| **unified_dashboard** | `coda/unified_dashboard/` | Domain app |
| **portfolio** | `coda/portfolio/` | Domain app |
| **core** | `coda/core/` | Infrastructure app |
| **api** | `coda/api/` | API app |
| **analytics** | `coda/analytics/` | Analytics module (no apps.py) |

**Total Django Apps:** 13 apps with `apps.py` + 1 analytics module

---

## 2. Shared Module: `shared_core/`

### Location
- **Path:** `coda/shared_core/`
- **App Config:** `shared_core.apps.SharedCoreConfig`
- **INSTALLED_APPS Position:** First (line 44 in `base_settings.py`)

### Structure

```
coda/shared_core/
├── __init__.py                    # Package initialization
├── apps.py                        # AppConfig
├── admin.py                       # Admin registrations
├── models.py                      # Re-exports base models from main.models
├── users.py                       # Re-exports CustomerUser, Department, UserCategory from accounts
├── utils.py                       # Re-exports utilities from main.utils + org detection
├── mixins.py                      # View mixins (FilteredListViewMixin, etc.)
├── filters.py                     # Django filters
├── interfaces/                    # Service interfaces (NEW - decoupling work)
│   ├── ai_service.py
│   ├── finance_task_service.py
│   └── meeting_service.py
└── services/                      # Service adapters (NEW - decoupling work)
    ├── credential_store.py
    └── adapters/
        ├── noop_ai_adapter.py
        ├── noop_finance_task_adapter.py
        └── noop_meeting_adapter.py
```

### What's in `shared_core`

#### `shared_core.models` (Re-exports from `main.models`)
- `TimeStampedModel` - Abstract base with `created_at`, `updated_at`
- `ContractBase` - Contract-related fields
- `DocumentMixin` - Document storage mixin
- `StatusMixin` - Status tracking mixin
- `UserReferenceMixin` - User reference mixin
- `Company` - Company model

#### `shared_core.users` (Re-exports from `accounts`)
- `CustomerUser` - Custom user model (AUTH_USER_MODEL)
- `Department` - Department model
- `UserCategory` - User category choices/enum

#### `shared_core.utils` (Re-exports from `main.utils` + additions)
- `path_values` - Extract values from path
- `dates_functionality` - Date utility functions
- `generate_chatbot_response` - Chatbot response generation
- `today_date` - Get today's date
- `date_converter` - Convert date strings
- `countdown_in_month` - Countdown utility
- **Plus:** Organization detection utilities (domain → Company mapping)

#### `shared_core.mixins`
- `FilteredListViewMixin` - List view with filtering

#### `shared_core.filters`
- Django filter classes

#### `shared_core.interfaces` (NEW - Decoupling Infrastructure)
- `AIServiceInterface` - Abstract interface for AI services
- `FinanceTaskServiceInterface` - Abstract interface for finance task operations
- `MeetingServiceInterface` - Abstract interface for meeting services

#### `shared_core.services.adapters` (NEW - No-Op Implementations)
- `NoOpAIServiceAdapter` - Fallback when AI services unavailable
- `NoOpFinanceTaskServiceAdapter` - Fallback when finance unavailable
- `NoOpMeetingServiceAdapter` - Fallback when meeting services unavailable

---

## 3. Management App Location & Size

- **Path:** `coda/management/`
- **Python Files:** ~76 files (based on directory listing)
- **Templates:** ~75 HTML files
- **Key Files:**
  - `coda/management/models.py` - Main models
  - `coda/management/views.py` - Main views (large file)
  - `coda/management/services/` - Service layer
  - `coda/management/admin.py` - Admin configuration

---

## 4. Management App Cross-App Imports

### Imports from `shared_core` (✅ GOOD - Using shared infrastructure)

| File | Import | Purpose |
|------|--------|---------|
| `views.py:34` | `from shared_core.users import UserCategory` | User category choices |
| `views.py:45` | `from shared_core.mixins import FilteredListViewMixin` | View mixin |
| `views.py:87` | `from shared_core.users import CustomerUser, Department` | User models |
| `views.py:101` | `from shared_core.utils import countdown_in_month, generate_chatbot_response, path_values` | Utilities |
| `admin.py:5` | `from shared_core.users import CustomerUser` | User model |
| `services/finance_service_helper.py:16-17` | `from shared_core.interfaces.finance_task_service` | Interface usage |

**Status:** ✅ Management is already using `shared_core` for infrastructure

---

### Imports from Domain Apps (⚠️ NEEDS ANALYSIS)

#### A. `professional_services` (3 files)

| File | Import | Purpose | Classification |
|------|--------|---------|----------------|
| `views.py:86` | `from professional_services.models import DSU, ClientAssessment, BackgroundCheck` | Professional services models | **LEAKY** - Domain coupling |
| `forms.py` | `from professional_services.models import DSU, ClientAssessment, BackgroundCheck` | Form fields | **LEAKY** - Domain coupling |
| `models.py` | `from professional_services.models import FeaturedCategory, FeaturedSubCategory, FeaturedActivity` | Activity taxonomy | **LEAKY** - Should be in shared or management |
| `signals.py` | `from professional_services.models import ClientAssessment` | Signal handlers | **LEAKY** - Domain coupling |

**Count:** 4 files with direct model imports

---

#### B. `ai_services` (8+ files)

| File | Import | Purpose | Classification |
|------|--------|---------|----------------|
| `views.py:159` | `from ai_services.views import (...)` | OAuth helper functions | **ONE-WAY** - Service dependency (acceptable) |
| `services/daf_summary_service.py` | `from ai_services.services.ai_insight_service import AIInsightService` (4 locations) | AI insights for DAF | **ONE-WAY** - Optional AI feature |
| `services/intelligent_assignment_service.py` | `from ai_services.adapters.ai_service_adapter import AIServiceAdapter` | AI task assignment | **ONE-WAY** - Uses interface pattern |
| `services/meeting_linking_service.py` | `from ai_services.adapters.meeting_service_adapter import MeetingServiceAdapter` | Meeting linking | **ONE-WAY** - Uses interface pattern |
| `services/utilities_service.py` | `from ai_services.adapters.ai_service_adapter import AIServiceAdapter` | AI utilities | **ONE-WAY** - Uses interface pattern |
| `services/ai_prediction_service.py` | `from ai_services.adapters.ai_service_adapter import AIServiceAdapter` | AI predictions | **ONE-WAY** - Uses interface pattern |
| `services/release_engine.py` | `from ai_services.services.ai_insight_service import AIInsightService` | AI insights | **ONE-WAY** - Optional AI feature |
| `views/base_views.py` | `from ai_services.ai_integration_service import RealAIService` | AI integration | **ONE-WAY** - Direct service (legacy?) |
| `models/base_models.py` | `from ai_services.adapters.ai_service_adapter import AIServiceAdapter` | AI in models | **ONE-WAY** - Uses interface pattern |
| `tests/*.py` (3 files) | `from ai_services.services.ai_insight_service import AIInsightService` | Test imports | **ONE-WAY** - Test dependencies |

**Count:** ~10+ files with AI service imports

**Pattern:** Most use **interface pattern** (good!), some use direct imports (legacy?)

---

#### C. `finance` (3 files)

| File | Import | Purpose | Classification |
|------|--------|---------|----------------|
| `views.py:968` | `from finance.models import PayslipConfig` | Payslip configuration | **ONE-WAY** - Config dependency |
| `services/finance_service_helper.py:65` | `from finance.adapters.finance_task_adapter import FinanceTaskAdapter` | Finance task adapter | **ONE-WAY** - Uses interface pattern |
| `services/utilities_service.py` | `from finance.services.ai_budget_suggestion_service import AIBudgetSuggestionService` | Budget suggestions | **ONE-WAY** - Optional feature |
| `views/base_views.py` | `from finance.services.ai_budget_suggestion_service import AIBudgetSuggestionService` | Budget suggestions | **ONE-WAY** - Optional feature |

**Count:** 4 files with finance imports

**Pattern:** Uses **interface pattern** for adapters (good!)

---

#### D. Other Domain Apps

| App | Files | Status |
|-----|-------|--------|
| `investing` | 0 | ✅ No imports |
| `portfolio` | 0 | ✅ No imports |
| `marketing` | 0 | ✅ No imports |

---

## 5. Summary: What's Already Done

### ✅ Completed Isolation Work

1. **`shared_core` Module Created**
   - ✅ Base models extracted (`TimeStampedModel`, `StatusMixin`, etc.)
   - ✅ User models extracted (`CustomerUser`, `Department`, `UserCategory`)
   - ✅ Utilities extracted (`path_values`, `dates_functionality`, etc.)
   - ✅ View mixins extracted (`FilteredListViewMixin`)
   - ✅ Filters extracted

2. **Interface Pattern Started**
   - ✅ `shared_core.interfaces` created with 3 interfaces:
     - `AIServiceInterface`
     - `FinanceTaskServiceInterface`
     - `MeetingServiceInterface`
   - ✅ No-op adapters created for graceful degradation
   - ✅ Management uses interfaces in some services:
     - `finance_service_helper.py` uses `FinanceTaskServiceInterface`
     - `intelligent_assignment_service.py` uses `AIServiceAdapter` (via interface)
     - `meeting_linking_service.py` uses `MeetingServiceAdapter` (via interface)

3. **Management Uses `shared_core`**
   - ✅ Imports user models from `shared_core.users`
   - ✅ Imports utilities from `shared_core.utils`
   - ✅ Imports mixins from `shared_core.mixins`
   - ✅ Uses interfaces for optional dependencies

---

## 6. What's Still Missing / Half-Done

### ⚠️ Direct Domain Model Imports (Leaky Coupling)

1. **`professional_services` Models** (4 files)
   - `DSU`, `ClientAssessment`, `BackgroundCheck` imported directly
   - `FeaturedCategory`, `FeaturedSubCategory`, `FeaturedActivity` imported directly
   - **Issue:** Management depends on professional_services domain models
   - **Solution:** Move to shared_core OR create interface OR make optional

2. **Direct AI Service Imports** (Legacy Pattern)
   - Some files still import `ai_services.services.ai_insight_service` directly
   - Some files import `ai_services.views` directly (OAuth helpers)
   - **Issue:** Not using interface pattern consistently
   - **Solution:** Migrate to interface pattern or move OAuth helpers to shared

3. **Finance Model Import** (1 file)
   - `PayslipConfig` imported directly in `views.py`
   - **Issue:** Management depends on finance domain model
   - **Solution:** Move to shared_core OR create interface OR make optional

---

## 7. INSTALLED_APPS Current State

From `coda/coda_project/coda_settings/base_settings.py`:

```python
INSTALLED_APPS = [
    "shared_core.apps.SharedCoreConfig",  # ✅ First - shared infrastructure
    "main.apps.MainConfig",                # Infrastructure
    "accounts.apps.AccountsConfig",        # User management
    "application.apps.ApplicationConfig",   # Application workflow
    "professional_services.apps.ProfessionalServicesConfig",  # ⚠️ Used by management
    "ai_services.apps.AiServicesConfig",  # ⚠️ Used by management
    "investing.apps.InvestingConfig",      # ❌ Not used by management
    "management.apps.ManagementConfig",    # ✅ TARGET APP
    "finance.apps.FinanceConfig",          # ⚠️ Used by management
    "marketing.apps.MarketingConfig",      # ❌ Not used by management
    "unified_dashboard.apps.UnifiedDashboardConfig",  # ❓ Unknown
    "portfolio.apps.PortfolioConfig",      # ❌ Not used by management
    # ... Django contrib apps ...
]
```

---

## 8. Key Findings

### ✅ Good News

1. **`shared_core` exists and is being used** - Infrastructure extraction is working
2. **Interface pattern started** - Some services use interfaces for optional dependencies
3. **Management uses `shared_core`** - Already importing from shared module
4. **No circular dependencies detected** - Management doesn't import from investing/portfolio/marketing

### ⚠️ Issues to Address

1. **Direct model imports from `professional_services`** - 4 files need refactoring
2. **Direct model import from `finance`** - 1 file (`PayslipConfig`)
3. **Inconsistent interface usage** - Some AI services use interfaces, some don't
4. **OAuth helpers in `ai_services.views`** - Should be in shared or management

### 📊 Dependency Summary

| Dependency Type | Count | Status |
|----------------|-------|--------|
| **shared_core** (infrastructure) | 6+ files | ✅ Good |
| **professional_services** (models) | 4 files | ⚠️ Leaky |
| **ai_services** (services/adapters) | 10+ files | ⚠️ Mixed (some interface, some direct) |
| **finance** (models/services) | 4 files | ⚠️ Mixed (some interface, some direct) |
| **investing/portfolio/marketing** | 0 files | ✅ Clean |

---

## 9. Next Steps (Preview for Step 2)

For Step 2, we need to:

1. **Classify each dependency:**
   - TRUE SHARED - Should move to `shared_core`
   - ONE-WAY DEPENDENCY - Acceptable but needs interface/optional handling
   - LEAKY/BAD - Needs refactoring

2. **Analyze specific imports:**
   - What models/services are imported?
   - Why are they needed?
   - Can they be moved to shared?
   - Can they be made optional?

3. **Create dependency table:**
   - File-by-file breakdown
   - Import-by-import classification
   - Refactoring recommendations

---

**Report Generated:** December 2025  
**Next:** Step 2 - Detailed dependency analysis and classification

