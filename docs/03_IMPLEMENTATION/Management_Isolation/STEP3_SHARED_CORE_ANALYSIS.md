# Step 3: Shared Core Analysis - What Exists vs What's Missing

**Date:** December 2025  
**Branch:** `25.12_CODA_DEV_CM`  
**Purpose:** Identify what's already in `shared_core`, what's missing, and what can be safely moved

---

## 1. Shared Core Current Inventory

### `shared_core/models.py` (Re-exports from `main.models`)

| Symbol | Source | Status |
|--------|--------|--------|
| `TimeStampedModel` | `main.models` | ✅ Re-export |
| `ContractBase` | `main.models` | ✅ Re-export |
| `DocumentMixin` | `main.models` | ✅ Re-export |
| `StatusMixin` | `main.models` | ✅ Re-export |
| `UserReferenceMixin` | `main.models` | ✅ Re-export |
| `Company` | `main.models` | ✅ Re-export |

**Pattern:** All re-exports (no migrations needed)

---

### `shared_core/users.py` (Re-exports from `accounts`)

| Symbol | Source | Status |
|--------|--------|--------|
| `CustomerUser` | `accounts.models` | ✅ Re-export |
| `Department` | `accounts.models` | ✅ Re-export |
| `UserCategory` | `accounts.choices` | ✅ Re-export |

**Pattern:** All re-exports (no migrations needed)

**Missing (Step 2 identified these):**
- ❌ `UserProfile` - Still only in `accounts.models`
- ❌ `Tracker` - Still only in `accounts.models`
- ❌ `TaskGroups` - Still only in `accounts.models`

---

### `shared_core/utils.py` (Re-exports from `main.utils` + additions)

| Symbol | Source | Status |
|--------|--------|--------|
| `path_values` | `main.utils` | ✅ Re-export |
| `dates_functionality` | `main.utils` | ✅ Re-export |
| `generate_chatbot_response` | `main.utils` | ✅ Re-export |
| `today_date` | `main.utils` | ✅ Re-export |
| `date_converter` | `main.utils` | ✅ Re-export |
| `countdown_in_month` | `main.utils` | ✅ Re-export |
| `detect_organization_from_request` | **NEW** (defined here) | ✅ Original |
| `get_company_logo_url` | **NEW** (defined here) | ✅ Original |
| `get_company_receipt_data` | **NEW** (defined here) | ✅ Original |

**Missing (Step 2 identified these):**
- ❌ `generate_password` - Still only in `core.utils`
- ❌ `send_verification_email` - Still only in `accounts.utils`
- ❌ `calculate_login_bonus` - Still only in `accounts.utils`

---

### `shared_core/mixins.py` (Re-exports from `accounts.mixins`)

| Symbol | Source | Status |
|--------|--------|--------|
| `FilteredListViewMixin` | `accounts.mixins` | ✅ Re-export |

**Pattern:** Re-export (no migrations needed)

---

### `shared_core/filters.py` (Re-exports from `main.filters`)

| Symbol | Source | Status |
|--------|--------|--------|
| `ReturnsFilter` | `main.filters` | ✅ Re-export |
| `CredentialFilter` | `main.filters` | ✅ Re-export |
| `FoodFilter` | `main.filters` | ✅ Re-export |

**Missing (Step 2 identified these):**
- ❌ `RequirementFilter` - Still only in `main.filters`
- ❌ `TaskHistoryFilter` - Still only in `main.filters`

**Note:** Both `RequirementFilter` and `TaskHistoryFilter` depend on `management.models` (Requirement, TaskHistory), so they're app-specific filters, not truly shared. However, they're used by multiple apps, so re-exporting them might be acceptable if management app is always present.

---

### `shared_core/interfaces/` (Abstract Interfaces - NEW)

| Interface | Methods | No-Op Adapter | Concrete Adapters |
|-----------|---------|---------------|-------------------|
| **`AIServiceInterface`** | 4 methods:<br>- `predict_employee_performance()`<br>- `predict_optimal_task_assignment()`<br>- `get_prediction()`<br>- `predict_department_performance()` | ✅ `NoOpAIServiceAdapter` | ⚠️ `ai_services.adapters.AIServiceAdapter` (referenced, may not exist yet) |
| **`FinanceTaskServiceInterface`** | 5 methods:<br>- `has_active_loan()`<br>- `get_user_loan_summary()`<br>- `has_payment_history()`<br>- `get_payslip_config()`<br>- `get_recent_payments_for_user()` | ✅ `NoOpFinanceTaskServiceAdapter` | ⚠️ `finance.adapters.FinanceTaskAdapter` (referenced, may not exist yet) |
| **`MeetingServiceInterface`** | 5 methods:<br>- `get_meeting_by_id()`<br>- `get_recent_meetings_for_user()`<br>- `find_meeting_by_topic()`<br>- `find_exact_mapping()`<br>- `get_meetings_in_date_range()` | ✅ `NoOpMeetingServiceAdapter` | ⚠️ `ai_services.adapters.MeetingServiceAdapter` (referenced, may not exist yet) |

**Status:** ✅ Interface pattern is well-established with no-op adapters in shared_core

---

### `shared_core/services/adapters/` (No-Op Implementations)

| Adapter | Interface | Status |
|---------|-----------|--------|
| `NoOpAIServiceAdapter` | `AIServiceInterface` | ✅ Complete |
| `NoOpFinanceTaskServiceAdapter` | `FinanceTaskServiceInterface` | ✅ Complete |
| `NoOpMeetingServiceAdapter` | `MeetingServiceInterface` | ✅ Complete |

**Status:** ✅ All no-op adapters exist for graceful degradation

---

## 2. Step 2 "TRUE SHARED" Candidates Comparison

### Accounts Models/Utils

| Symbol | Current Location | shared_core Status | Classification |
|--------|------------------|-------------------|----------------|
| **`UserProfile`** | `accounts.models.UserProfile` | ❌ **Missing** | Should be re-export |
| **`Tracker`** | `accounts.models.Tracker` | ❌ **Missing** | Should be re-export |
| **`TaskGroups`** | `accounts.models.TaskGroups` | ❌ **Missing** | Should be re-export |
| **`send_verification_email`** | `accounts.utils.send_verification_email` | ❌ **Missing** | Should be re-export |
| **`calculate_login_bonus`** | `accounts.utils.calculate_login_bonus` | ❌ **Missing** | Should be re-export |

**Analysis:**
- These are all infrastructure/user-related, not domain-specific
- Should be re-exported from `shared_core.users` (models) or `shared_core.utils` (functions)
- **Risk:** LOW - Re-export only, no migrations needed

---

### Main Filters

| Symbol | Current Location | shared_core Status | Classification |
|--------|------------------|-------------------|----------------|
| **`RequirementFilter`** | `main.filters.RequirementFilter` | ❌ **Missing** | ⚠️ **App-specific** (depends on `management.models.Requirement`) |
| **`TaskHistoryFilter`** | `main.filters.TaskHistoryFilter` | ❌ **Missing** | ⚠️ **App-specific** (depends on `management.models.TaskHistory`) |

**Analysis:**
- Both filters depend on `management.models`
- They're used by multiple apps (main, management)
- **Decision needed:** If management app is always required, re-exporting is fine. Otherwise, these should stay in `main.filters` or move to `management.filters`.

**Recommendation:** Keep in `main.filters` for now (management is core app), but document the dependency.

---

### Core Utils

| Symbol | Current Location | shared_core Status | Classification |
|--------|------------------|-------------------|----------------|
| **`generate_password`** | `core.utils.generate_password` | ❌ **Missing** | Should be re-export |

**Analysis:**
- Pure utility function (no dependencies)
- Used by multiple apps (accounts, management, etc.)
- **Risk:** LOW - Re-export only, no migrations needed

---

### AI Services / OAuth Helpers

| Symbol | Current Location | shared_core Status | Classification |
|--------|------------------|-------------------|----------------|
| **`get_oauth_redirect_uri`** | `ai_services.views.get_oauth_redirect_uri` | ❌ **Missing** | Should move to `shared_core.utils.oauth` |
| **`get_authorization_url`** | `ai_services.views.get_authorization_url` | ❌ **Missing** | Should move to `shared_core.utils.oauth` |
| **`exchange_code_for_tokens`** | `ai_services.views.exchange_code_for_tokens` | ❌ **Missing** | Should move to `shared_core.utils.oauth` |
| **`refresh_access_token`** | `ai_services.views.refresh_access_token` | ❌ **Missing** | Should move to `shared_core.utils.oauth` |

**Analysis:**
- OAuth helpers are utility functions, not domain-specific
- Used by management app (OAuth flows)
- **Risk:** MEDIUM - Moving functions from views module (may need to handle imports/circular deps)

**Recommendation:** Create `shared_core/utils/oauth.py` and move these functions there. Update imports in management and ai_services.

---

## 3. Low-Risk vs High-Risk Moves

### ✅ Low-Risk Moves (Re-export Only - No Migrations)

These can be added to `shared_core` immediately via re-exports:

| Symbol | Current Module | Target Module | Risk | Effort |
|--------|---------------|---------------|------|--------|
| `UserProfile` | `accounts.models` | `shared_core.users` | **LOW** | 1 line re-export |
| `Tracker` | `accounts.models` | `shared_core.users` | **LOW** | 1 line re-export |
| `TaskGroups` | `accounts.models` | `shared_core.users` | **LOW** | 1 line re-export |
| `send_verification_email` | `accounts.utils` | `shared_core.utils` | **LOW** | 1 line re-export |
| `calculate_login_bonus` | `accounts.utils` | `shared_core.utils` | **LOW** | 1 line re-export |
| `generate_password` | `core.utils` | `shared_core.utils` | **LOW** | 1 line re-export |
| `RequirementFilter` | `main.filters` | `shared_core.filters` | **LOW** | 1 line re-export (but depends on management) |
| `TaskHistoryFilter` | `main.filters` | `shared_core.filters` | **LOW** | 1 line re-export (but depends on management) |

**Total:** 8 symbols, all low-risk re-exports

---

### ⚠️ Medium-Risk Moves (Function Moves - May Need Import Updates)

These require moving code (not just re-exporting):

| Symbol | Current Module | Target Module | Risk | Effort | Notes |
|--------|---------------|---------------|------|--------|-------|
| `get_oauth_redirect_uri` | `ai_services.views` | `shared_core.utils.oauth` | **MEDIUM** | Move function + update imports | May have dependencies on `ai_services` constants |
| `get_authorization_url` | `ai_services.views` | `shared_core.utils.oauth` | **MEDIUM** | Move function + update imports | Depends on OAuth constants |
| `exchange_code_for_tokens` | `ai_services.views` | `shared_core.utils.oauth` | **MEDIUM** | Move function + update imports | Depends on cache, requests, logging |
| `refresh_access_token` | `ai_services.views` | `shared_core.utils.oauth` | **MEDIUM** | Move function + update imports | Depends on cache |

**Total:** 4 OAuth helper functions

**Considerations:**
- These functions depend on environment variables (`API_CLIENT_ID`, `API_CLIENT_SECRET`)
- They use Django cache and requests library
- They're not domain-specific, so moving is appropriate
- Need to ensure all dependencies are available in shared_core context

---

### ❌ High-Risk Moves (Model/Schema Changes - Require Migrations)

These would require database migrations and are **NOT recommended** for Management-only branch:

| Symbol | Current Module | Why Risky | Recommendation |
|--------|---------------|-----------|----------------|
| `FeaturedCategory` | `professional_services.models` | FK dependency in `Training` model | **Better as interface** or leave in professional_services |
| `FeaturedSubCategory` | `professional_services.models` | FK dependency in `Training` model | **Better as interface** or leave in professional_services |
| `FeaturedActivity` | `professional_services.models` | FK dependency in `Training` model | **Better as interface** or leave in professional_services |
| `DSU` | `professional_services.models` | Domain model, used by management views | **Better as interface** (ProfessionalServicesInterface) |
| `ClientAssessment` | `professional_services.models` | Domain model, used by management views | **Better as interface** (ProfessionalServicesInterface) |
| `BackgroundCheck` | `professional_services.models` | Domain model, used by management views | **Better as interface** (ProfessionalServicesInterface) |
| `PayslipConfig` | `finance.models` | Domain model, already has interface | ✅ **Already has interface** - use `FinanceTaskServiceInterface.get_payslip_config()` |

**Recommendation:** Use interface pattern for these, not full moves.

---

## 4. Concrete Adapter Status

### AIServiceAdapter

- **Location:** `ai_services.adapters.AIServiceAdapter`
- **Status:** ⚠️ **Referenced but directory doesn't exist** - May need to be created
- **Implements:** `AIServiceInterface`
- **Used by:** `intelligent_assignment_service.py`, `ai_prediction_service.py`, `utilities_service.py`, `base_models.py`
- **Note:** Code tries to import this, but `coda/ai_services/adapters/` directory doesn't exist yet

---

### FinanceTaskAdapter

- **Location:** `finance.adapters.FinanceTaskAdapter`
- **Status:** ⚠️ **Referenced but directory doesn't exist** - May need to be created
- **Implements:** `FinanceTaskServiceInterface`
- **Used by:** `finance_service_helper.py` (via interface resolution)
- **Note:** Code tries to import this, but `coda/finance/adapters/` directory doesn't exist yet

---

### MeetingServiceAdapter

- **Location:** `ai_services.adapters.MeetingServiceAdapter`
- **Status:** ⚠️ **Referenced but directory doesn't exist** - May need to be created
- **Implements:** `MeetingServiceInterface`
- **Used by:** `meeting_linking_service.py` (via interface resolution)
- **Note:** Code tries to import this, but `coda/ai_services/adapters/` directory doesn't exist yet

---

### Missing: ProfessionalServicesAdapter

- **Interface:** ❌ `ProfessionalServicesInterface` does NOT exist yet
- **No-Op Adapter:** ❌ `NoOpProfessionalServicesAdapter` does NOT exist yet
- **Concrete Adapter:** ❌ Would be in `professional_services.adapters` (doesn't exist)

**Recommendation:** Create interface + adapters for professional_services if we want management to work standalone.

---

## 5. Refactor Cheat-Sheet

### ✅ Already in shared_core & Used Correctly (LEAVE ALONE)

| Symbol | shared_core Location | Used By | Status |
|--------|---------------------|---------|--------|
| `CustomerUser` | `shared_core.users` | Management ✅ | ✅ Good |
| `Department` | `shared_core.users` | Management ✅ | ✅ Good |
| `UserCategory` | `shared_core.users` | Management ✅ | ✅ Good |
| `TimeStampedModel` | `shared_core.models` | Management ✅ | ✅ Good |
| `StatusMixin` | `shared_core.models` | Management ✅ | ✅ Good |
| `Company` | `shared_core.models` | Management ✅ | ✅ Good |
| `FilteredListViewMixin` | `shared_core.mixins` | Management ✅ | ✅ Good |
| `path_values` | `shared_core.utils` | Management ✅ | ✅ Good |
| `countdown_in_month` | `shared_core.utils` | Management ✅ | ✅ Good |
| `AIServiceInterface` | `shared_core.interfaces` | Management ✅ | ✅ Good |
| `FinanceTaskServiceInterface` | `shared_core.interfaces` | Management ✅ | ✅ Good |
| `MeetingServiceInterface` | `shared_core.interfaces` | Management ✅ | ✅ Good |

**Action:** No changes needed

---

### ✅ Recommended to Add via Re-Export (No Migration - LOW RISK)

| Symbol | Current Module | New shared_core Module | Apps to Update | Priority |
|--------|---------------|------------------------|----------------|----------|
| **`UserProfile`** | `accounts.models` | `shared_core.users` | management (views.py, forms.py) | HIGH |
| **`Tracker`** | `accounts.models` | `shared_core.users` | management (views.py) | HIGH |
| **`TaskGroups`** | `accounts.models` | `shared_core.users` | management (models.py, views.py) | HIGH |
| **`send_verification_email`** | `accounts.utils` | `shared_core.utils` | management (signals.py), accounts | MEDIUM |
| **`calculate_login_bonus`** | `accounts.utils` | `shared_core.utils` | management (views.py), accounts | MEDIUM |
| **`generate_password`** | `core.utils` | `shared_core.utils` | management (signals.py), accounts, core | MEDIUM |
| **`RequirementFilter`** | `main.filters` | `shared_core.filters` | management (views.py), main | LOW* |
| **`TaskHistoryFilter`** | `main.filters` | `shared_core.filters` | management (views.py), main | LOW* |

**\*Note:** `RequirementFilter` and `TaskHistoryFilter` depend on `management.models`, so re-exporting is only safe if management is always present. Otherwise, keep them in `main.filters`.

**Action:** Add re-exports to `shared_core.users` and `shared_core.utils`, update management imports

---

### ⚠️ Recommended to Move (Function Move - MEDIUM RISK)

| Symbol | Current Module | New shared_core Module | Apps to Update | Priority |
|--------|---------------|------------------------|----------------|----------|
| **`get_oauth_redirect_uri`** | `ai_services.views` | `shared_core.utils.oauth` | management (views.py), ai_services (views.py) | MEDIUM |
| **`get_authorization_url`** | `ai_services.views` | `shared_core.utils.oauth` | management (views.py), ai_services (views.py) | MEDIUM |
| **`exchange_code_for_tokens`** | `ai_services.views` | `shared_core.utils.oauth` | management (views.py), ai_services (views.py) | MEDIUM |
| **`refresh_access_token`** | `ai_services.views` | `shared_core.utils.oauth` | management (views.py), ai_services (views.py) | MEDIUM |

**Action:** Create `shared_core/utils/oauth.py`, move functions, update imports

**Dependencies to handle:**
- Environment variables (`API_CLIENT_ID`, `API_CLIENT_SECRET`)
- Django cache
- `requests` library
- `urlencode` from `urllib.parse`

---

### ❌ Needs Design Decision / Interface Pattern (HIGH RISK - Don't Move Models)

| Symbol | Current Module | Why Risky | Suggested Approach |
|--------|---------------|-----------|-------------------|
| **`FeaturedCategory`** | `professional_services.models` | FK in `Training` model | **Option A:** Create `ProfessionalServicesInterface` + adapter<br>**Option B:** Make FK nullable, use interface for lookups<br>**Option C:** Keep in professional_services, accept dependency |
| **`FeaturedSubCategory`** | `professional_services.models` | FK in `Training` model | Same as FeaturedCategory |
| **`FeaturedActivity`** | `professional_services.models` | FK in `Training` model | Same as FeaturedCategory |
| **`DSU`** | `professional_services.models` | Domain model, used by management views | **Create `ProfessionalServicesInterface`** with methods:<br>- `get_dsu_list(user_type)`<br>- `create_dsu(data)`<br>- `update_dsu(id, data)`<br>+ NoOp adapter in shared_core<br>+ Concrete adapter in professional_services |
| **`ClientAssessment`** | `professional_services.models` | Domain model, used by management views | Add to `ProfessionalServicesInterface`:<br>- `get_client_assessments()`<br>- `create_client_assessment(data)`<br>- `update_client_assessment(id, data)` |
| **`BackgroundCheck`** | `professional_services.models` | Domain model, used by management views | Add to `ProfessionalServicesInterface`:<br>- `get_background_checks()`<br>- `create_background_check(data)` |
| **`PayslipConfig`** | `finance.models` | Domain model | ✅ **Already has interface!**<br>Use `FinanceTaskServiceInterface.get_payslip_config()`<br>**Action:** Update `views.py:968` to use interface instead of direct import |

**Action:** 
1. For `PayslipConfig`: Update management to use existing interface
2. For professional_services models: Create `ProfessionalServicesInterface` (new interface) OR keep dependency if acceptable for Management-only branch

---

## 6. Summary for Management-Only Branch

### What We Have ✅

1. **Core infrastructure:** `CustomerUser`, `Department`, `TimeStampedModel`, etc. - all re-exported correctly
2. **Interface pattern:** 3 interfaces with no-op adapters - graceful degradation works
3. **No-op adapters:** All exist in `shared_core.services.adapters` - allows management to run standalone
4. **Concrete adapters:** Referenced in code but directories don't exist yet - management falls back to no-op adapters (this is OK for standalone mode)

### What's Missing (Can Add Easily) ✅

1. **User models/utils:** `UserProfile`, `Tracker`, `TaskGroups`, `send_verification_email`, `calculate_login_bonus` - all re-export candidates
2. **Core utils:** `generate_password` - re-export candidate
3. **OAuth helpers:** 4 functions - move to `shared_core.utils.oauth`

### What Needs Decision ⚠️

1. **Professional Services models:** Create interface OR keep dependency
2. **Finance PayslipConfig:** Use existing interface (already available!)

### What NOT to Do ❌

1. **Don't move models** that have FK dependencies (FeaturedCategory, etc.)
2. **Don't create migrations** for Management-only branch
3. **Don't break existing functionality** - use re-exports and interfaces

---

**Report Generated:** December 2025  
**Next:** Step 4 - Design concrete plan for minimal management branch

