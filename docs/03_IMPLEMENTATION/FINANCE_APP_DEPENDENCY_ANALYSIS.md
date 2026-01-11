# Finance App Dependency Analysis

**Date:** December 2025  
**Branch:** `25.12_CODA_DEV_CM`  
**Purpose:** Analyze `coda/finance/` app dependencies to assess external developer safety and define guardrails for the equity module

---

## Executive Summary

The `finance` app has **moderate coupling** to other CODA apps, primarily through:
- **Management app** (high-risk): Used for employee compliance, task history, and salary calculations
- **Main app** (medium-risk): Used for Service/ServiceCategory models and Company references
- **Investing app** (low-risk): Optional imports with try/except handling
- **AI Services app** (low-risk): Used for AI-powered features (optional)
- **Shared Core** (low-risk): Infrastructure only - safe

**Key Finding:** Approximately **15-20 files** in finance import from `management`, creating a dependency that would require external developers to understand the management app's structure. However, these dependencies are **concentrated in specific services** (compliance, budget integration) that the equity module can avoid.

**Recommendation:** The equity module should be implemented in **isolated sub-modules** within finance that avoid the management-dependent services. External developers can work on equity without understanding management, but would need context on shared_core and basic finance patterns.

---

## 1. Dependency Map: Finance App External Imports

### 1.1 Shared Core (Low Risk - Infrastructure Only)

**Status:** ✅ **SAFE** - Infrastructure layer, no business logic dependencies

| Module | Imports | Files Using |
|--------|---------|-------------|
| `shared_core.models` | `Company`, `TimeStampedModel`, `StatusMixin`, `ContractBase` | `models/core.py`, `models/budget.py`, most views |
| `shared_core.users` | `CustomerUser`, `Department`, `UserCategory` | Most views, services, models |
| `shared_core.utils` | `path_values`, `dates_functionality`, `date_converter`, `countdown_in_month` | `views.py`, `models/core.py` |
| `shared_core.filters` | `FoodFilter` | `views.py` |
| `shared_core.mixins` | `FilteredListViewMixin` | `views.py` |

**Count:** ~40+ files use shared_core imports  
**Risk Level:** **LOW** - Infrastructure only, designed for sharing

---

### 1.2 Management App (High Risk - Business Logic Coupling)

**Status:** ⚠️ **HIGH RISK** - Tight coupling to management's business logic

| Module | Imports | Files Using | Purpose |
|--------|---------|------------|---------|
| `management.models` | `TaskHistory`, `Task`, `Requirement`, `Meeting` | 8 files | Task completion tracking, compliance |
| `management.utils` | `calculate_total_pay`, `paytime`, `emp_average_earnings` | 4 files | Salary calculations |
| `management.services` | `EmployeeComplianceService` | 6 files | Employee compliance (33% rule) |
| `management.views` | `budget_activity_totals_api`, `budget_evidence_validation_api` | 1 file | Budget integration APIs |

**Files with Management Dependencies:**

**Services (High Coupling):**
1. `services/realtime_compliance_service.py` - Full dependency on TaskHistory, Task, EmployeeComplianceService
2. `services/integrated_budget_service.py` - Full dependency on TaskHistory, Task, calculate_total_pay
3. `services/admin_controls_service.py` - Full dependency on TaskHistory, Task, EmployeeComplianceService
4. `services/enhanced_budget_service.py` - Uses EmployeeComplianceService
5. `services/management_integration_service.py` - Calls management views/APIs
6. `services/financial_analytics_service.py` - Uses management.models.Department (likely a mistake, should be shared_core)

**Views (Medium Coupling):**
7. `views/budget/views_salary_dashboard.py` - Uses EmployeeComplianceService
8. `views/budget/views_realtime_compliance.py` - Uses EmployeeComplianceService
9. `views/budget/views_enhanced_approvals.py` - Uses EmployeeComplianceService, TaskHistory
10. `views/budget/views_admin_controls.py` - Uses EmployeeComplianceService (3 times)
11. `views/budget/approvals.py` - Uses EmployeeComplianceService, TaskHistory
12. `views/legacy/views_unified_department.py` - Uses Task, Meeting

**Utils:**
13. `utils.py` - Uses TaskHistory, emp_average_earnings (2 locations)

**Main Views:**
14. `views.py` - Uses management.utils.paytime, management.models.Requirement

**Count:** ~14 files with management dependencies  
**Risk Level:** **HIGH** - These services/views require understanding management's task system, compliance rules, and salary calculations

---

### 1.3 Main App (Medium Risk - Model References)

**Status:** ⚠️ **MEDIUM RISK** - Some business logic dependencies

| Module | Imports | Files Using | Purpose |
|--------|---------|------------|---------|
| `main.models` | `Service`, `ServiceCategory`, `Pricing`, `Company` | 5 files | Service definitions, company references |
| `main.utils` | `PayChoices` | 1 file | Pay-related choices |

**Files with Main Dependencies:**

1. `models/core.py` - Uses Service, ServiceCategory (optional with try/except)
2. `views.py` - Uses Service, ServiceCategory, Pricing
3. `views/payment/stripe_views.py` - Uses main.models.Company (3 times, likely should use shared_core)
4. `services/unified_budget_estimation_service.py` - Type hint for 'main.Company'
5. `models/budget.py` - ForeignKey to 'main.Company' (string reference for migrations)

**Note:** Most `Company` references should use `shared_core.models.Company` instead of `main.models.Company`. The string reference in `models/budget.py` is correct for migrations.

**Count:** ~5 files  
**Risk Level:** **MEDIUM** - Some files reference main models, but most are optional or should be migrated to shared_core

---

### 1.4 Investing App (Low Risk - Optional)

**Status:** ✅ **LOW RISK** - Optional imports with graceful degradation

| Module | Imports | Files Using | Purpose |
|--------|---------|------------|---------|
| `investing.models` | `Investment_rates`, `Investor_Information` | 2 files | Investment data (optional) |
| `investing.utils` | `calculate_investor_returns` | 1 file | Investment calculations (optional) |

**Files with Investing Dependencies:**

1. `models/core.py` - Uses Investment_rates (optional with try/except)
2. `views.py` - Uses Investment_rates, Investor_Information, calculate_investor_returns

**Count:** ~2 files  
**Risk Level:** **LOW** - Already uses try/except pattern, graceful degradation

---

### 1.5 AI Services App (Low Risk - Optional)

**Status:** ✅ **LOW RISK** - Optional AI features

| Module | Imports | Files Using | Purpose |
|--------|---------|------------|---------|
| `ai_services.models` | `Editable`, `DiasporaAnalysisData`, `AIModelTypes` | 3 files | AI-powered features |
| `ai_services.ai_integration_service` | `RealAIService` | 2 files | AI service integration |

**Files with AI Services Dependencies:**

1. `views.py` - Uses Editable
2. `services/smart_data_correction_service.py` - Uses RealAIService, DiasporaAnalysisData, AIModelTypes
3. `services/ai_budget_suggestion_service.py` - Uses RealAIService, DiasporaAnalysisData, AIModelTypes

**Count:** ~3 files  
**Risk Level:** **LOW** - Optional AI features, not core to finance functionality

---

### 1.6 Other Apps (Minimal)

- **accounts**: No direct imports (uses shared_core.users instead) ✅
- **professional_services**: No imports ✅
- **application**: No imports ✅
- **unified_dashboard**: No imports ✅

---

## 2. Risk Classification Summary

### Low Risk Dependencies (Safe for External Developers)

| App | Risk Level | Reason |
|-----|------------|--------|
| **shared_core** | ✅ LOW | Infrastructure only, designed for sharing |
| **investing** | ✅ LOW | Optional imports with try/except, graceful degradation |
| **ai_services** | ✅ LOW | Optional AI features, not core functionality |

**External Developer Impact:** Can work with these dependencies without understanding the full monolith.

---

### Medium Risk Dependencies (Requires Some Context)

| App | Risk Level | Reason |
|-----|------------|--------|
| **main** | ⚠️ MEDIUM | Some model references, but most should migrate to shared_core. Company references should use shared_core. |

**External Developer Impact:** Needs to understand that `Company` should come from `shared_core`, not `main`. Some service definitions may reference main models, but these are optional.

---

### High Risk Dependencies (Requires Full Context)

| App | Risk Level | Reason |
|-----|------------|--------|
| **management** | ❌ HIGH | ~14 files depend on management's task system, compliance rules, and salary calculations. External developers would need to understand: Task/TaskHistory models, 33% compliance rule, EmployeeComplianceService, salary calculation logic. |

**External Developer Impact:** Cannot work on management-dependent services without understanding the entire management app's business logic.

**Concentrated Areas:**
- Budget-salary integration services (realtime_compliance, integrated_budget, admin_controls)
- Compliance-related views (salary_dashboard, realtime_compliance, enhanced_approvals)
- Legacy views (unified_department)

---

## 3. Impact on Equity Module

### 3.1 Safe Neighborhoods for Equity Module

**Recommended Locations (Low Coupling):**

1. **`finance/models/equity.py`** ✅
   - Can import: `shared_core.models`, `shared_core.users`, `django.db.models`
   - Should avoid: `management.*`, `main.*` (except via shared_core)

2. **`finance/services/equity/`** ✅
   - Can import: `finance.utils.currency_converter`, `finance.models.*` (other finance models), `shared_core.*`
   - Should avoid: `management.*`, services that import management

3. **`finance/views/equity/`** ✅
   - Can import: `finance.models.equity.*`, `finance.services.equity.*`, `shared_core.*`
   - Should avoid: Views that import management

4. **`finance/templates/finance/equity/`** ✅
   - No Python imports, safe

**Isolated Services (Can Be Used by Equity):**
- `finance/utils/currency_converter.py` - Pure utility, no external dependencies ✅
- `finance/services/automation_service.py` - Approval patterns (check for management deps)
- `finance/services/credit_scoring_service.py` - Scoring patterns (check for management deps)
- Most finance models (budget, payment, loan) - Check individual files for management imports

---

### 3.2 Equity Module Allowed Dependencies

**✅ ALLOWED (Phase 1):**

1. **Django Core:**
   - `django.db.models`, `django.contrib.auth`, `django.utils`, etc.

2. **Shared Core:**
   - `shared_core.models` (Company, TimeStampedModel, StatusMixin, etc.)
   - `shared_core.users` (CustomerUser, Department)
   - `shared_core.utils` (if needed)
   - `shared_core.mixins` (FilteredListViewMixin, etc.)

3. **Finance Utilities (Same App):**
   - `finance.utils.currency_converter.CurrencyConverter` ✅
   - `finance.utils.*` (other utilities, check for management deps)
   - `finance.utilities.*` (check for management deps)

4. **Finance Models (Same App, Check Dependencies):**
   - `finance.models.budget.ApprovalPolicy` (check for management deps)
   - Other finance models that don't import management

5. **Settings:**
   - `settings.AUTH_USER_MODEL`

---

### 3.3 Equity Module Dependencies to AVOID (Phase 1)

**❌ AVOID (Phase 1):**

1. **Management App (High Risk):**
   - `management.models.Task`, `management.models.TaskHistory`
   - `management.utils.*`
   - `management.services.*`
   - **Rationale:** Would require external developer to understand management's entire task system, compliance rules, and salary calculations.

2. **Main App (Medium Risk):**
   - `main.models.Service`, `main.models.ServiceCategory`, `main.models.Pricing`
   - `main.utils.*`
   - **Rationale:** Not needed for equity. Use `shared_core.models.Company` instead of `main.models.Company`.

3. **Management-Dependent Finance Services:**
   - `finance.services.realtime_compliance_service.RealtimeComplianceService`
   - `finance.services.integrated_budget_service.IntegratedBudgetService`
   - `finance.services.admin_controls_service.AdminControlsService`
   - `finance.services.enhanced_budget_service.EnhancedBudgetService`
   - **Rationale:** These services have deep management dependencies.

4. **Management-Dependent Finance Views:**
   - Views in `finance/views/budget/` that import `EmployeeComplianceService`
   - **Rationale:** These views require management context.

---

### 3.4 Future Integration (Phase 2+)

**⏳ FUTURE (Phase 2+):**

1. **Task Integration (Optional):**
   - If equity Time/Work ledgers need to integrate with `management.Task`/`TaskHistory`:
     - Create adapter service: `finance/services/equity/task_adapter.py`
     - Use thin interface, not direct imports
     - Mark clearly as Phase 2 enhancement

2. **Approval Patterns (If Needed):**
   - Can reference `finance.models.budget.ApprovalPolicy` patterns
   - Implement equity-specific approval logic
   - Avoid importing management-dependent approval services

---

## 4. Proposed Guardrails for Equity Module

### 4.1 Import Rules

**Rule 1: Equity Models (`finance/models/equity.py`)**
```python
# ALLOWED imports:
from django.db import models
from django.conf import settings
from shared_core.models import Company, TimeStampedModel, StatusMixin
from shared_core.users import CustomerUser, Department

# FORBIDDEN imports:
# from management.models import Task, TaskHistory  # NO
# from main.models import Service  # NO
# from investing.models import Investment_rates  # NO (unless optional with try/except)
```

**Rule 2: Equity Services (`finance/services/equity/*.py`)**
```python
# ALLOWED imports:
from finance.utils.currency_converter import CurrencyConverter
from finance.models.equity import EquityDeal, CashContribution
from shared_core.models import Company
from shared_core.users import CustomerUser

# FORBIDDEN imports:
# from management.models import Task, TaskHistory  # NO
# from management.services.employee_compliance_service import EmployeeComplianceService  # NO
# from finance.services.realtime_compliance_service import RealtimeComplianceService  # NO (has management deps)
```

**Rule 3: Equity Views (`finance/views/equity/*.py`)**
```python
# ALLOWED imports:
from finance.models.equity import EquityDeal
from finance.services.equity.equity_scoring_engine import EquityScoringEngine
from shared_core.models import Company
from shared_core.users import CustomerUser

# FORBIDDEN imports:
# from management.models import Task  # NO
# from finance.views.budget.views_salary_dashboard import ...  # NO (has management deps)
```

---

### 4.2 File Organization Rules

**Rule 4: Clear Separation**
- All equity code lives in clearly marked sub-modules:
  - `finance/models/equity.py` (or `finance/models/equity/` if it grows)
  - `finance/services/equity/` (directory)
  - `finance/views/equity/` (directory)
  - `finance/templates/finance/equity/` (directory)

**Rule 5: Phase 2 Integration Files**
- Any future integration with `management.Task` must:
  - Live in a separate file: `finance/services/equity/task_adapter.py`
  - Be clearly marked with `# PHASE 2: Task Integration` comment
  - Use adapter pattern, not direct imports
  - Have a TODO comment explaining the integration approach

---

### 4.3 Code Review Checklist

**Rule 6: Pre-Commit Checks**
Before committing equity code, verify:
- [ ] No imports from `management.*` (except in Phase 2 adapter files)
- [ ] No imports from `main.*` (use `shared_core.models.Company` instead)
- [ ] All equity models use `shared_core.models` base mixins
- [ ] All equity services use `finance.utils.currency_converter` (not management-dependent services)
- [ ] All equity views follow finance app patterns (not management-dependent patterns)

---

### 4.4 Documentation Rules

**Rule 7: Dependency Documentation**
- Each equity service file should have a docstring listing its dependencies:
  ```python
  """
  Equity Scoring Engine
  
  Dependencies:
  - shared_core.models (Company, TimeStampedModel)
  - shared_core.users (CustomerUser)
  - finance.utils.currency_converter (CurrencyConverter)
  - finance.models.equity (EquityDeal, CashContribution, etc.)
  
  Does NOT depend on:
  - management.* (to maintain modularity)
  - main.* (uses shared_core instead)
  """
  ```

---

## 5. External Developer Safety Assessment

### 5.1 What External Developers Can Safely Work On

**✅ SAFE (No Management Context Needed):**

1. **Equity Models** (`finance/models/equity.py`)
   - All equity model definitions
   - Relationships between equity entities
   - Model methods and properties
   - **Dependencies:** Only Django, shared_core, settings

2. **Equity Services** (`finance/services/equity/*.py`)
   - Scoring engine
   - Config service (FX, weights, multipliers)
   - Snapshot service
   - Export service
   - **Dependencies:** finance.utils, shared_core, finance.models.equity

3. **Equity Views** (`finance/views/equity/*.py`)
   - Deal setup views
   - Ledger entry views
   - Cap table views
   - Export views
   - **Dependencies:** finance.models.equity, finance.services.equity, shared_core

4. **Equity Templates** (`finance/templates/finance/equity/*.html`)
   - All template files
   - **Dependencies:** None (templates only)

---

### 5.2 What External Developers Should NOT Touch

**❌ AVOID (Requires Management Context):**

1. **Management-Dependent Services:**
   - `finance/services/realtime_compliance_service.py`
   - `finance/services/integrated_budget_service.py`
   - `finance/services/admin_controls_service.py`
   - `finance/services/enhanced_budget_service.py`

2. **Management-Dependent Views:**
   - `finance/views/budget/views_salary_dashboard.py`
   - `finance/views/budget/views_realtime_compliance.py`
   - `finance/views/budget/views_enhanced_approvals.py`
   - `finance/views/budget/views_admin_controls.py`

3. **Legacy Views:**
   - `finance/views/legacy/views_unified_department.py`

---

### 5.3 External Developer Boundary Summary

**Working Area:** `coda/finance/` (entire finance app)

**Safe Sub-Areas:**
- `finance/models/equity.py` ✅
- `finance/services/equity/` ✅
- `finance/views/equity/` ✅
- `finance/templates/finance/equity/` ✅
- `finance/utils/currency_converter.py` ✅
- Most other finance models/services (check individual files)

**Avoid These Sub-Areas:**
- Services/views that import `management.*` ❌
- Services/views that have deep management dependencies ❌

**Required Knowledge:**
- Django ORM and models
- `shared_core.models` (Company, base mixins)
- `shared_core.users` (CustomerUser, Department)
- `finance.utils.currency_converter` (FX conversion)
- Basic finance app patterns (approvals, configs, exports)

**NOT Required:**
- Management app's task system
- Management app's compliance rules
- Management app's salary calculations
- Main app's service definitions

---

## 6. Recommendations

### 6.1 For Equity Module Implementation

1. **Start with Isolated Models:**
   - Create `finance/models/equity.py` with only Django + shared_core dependencies
   - Verify no management imports needed

2. **Build Services Incrementally:**
   - Start with `equity_config_service.py` (uses CurrencyConverter only)
   - Then `equity_scoring_engine.py` (uses equity models only)
   - Then `equity_snapshot_service.py` (uses equity models + scoring engine)
   - Avoid any service that would need management imports

3. **Follow Finance Patterns:**
   - Reference `finance.models.budget.ApprovalPolicy` for approval patterns
   - Reference `finance.services.automation_service` for approval workflows
   - Use `finance.utils.currency_converter` for FX
   - Follow finance view patterns (class-based views, decorators)

4. **Document Dependencies:**
   - Add docstrings listing allowed dependencies
   - Add comments for any Phase 2 integration points

---

### 6.2 For Code Review Process

1. **Pre-Commit Hook (Future):**
   - Add check to prevent `management.*` imports in `finance/models/equity.py` and `finance/services/equity/*.py`
   - Add check to prevent `main.*` imports (except via shared_core)

2. **Code Review Checklist:**
   - Verify equity code follows import rules
   - Verify equity code doesn't pull in management dependencies
   - Verify equity code uses shared_core, not main

3. **Documentation:**
   - Update equity technical analysis with these guardrails
   - Add dependency map to equity module README (if created)

---

### 6.3 For Future Refactoring (Optional)

1. **Migrate Company References:**
   - Update `finance/views/payment/stripe_views.py` to use `shared_core.models.Company` instead of `main.models.Company`
   - Update `finance/models/core.py` to use `shared_core.models.Company` consistently

2. **Extract Management Dependencies:**
   - Consider creating adapter services for management integration
   - Move management-dependent services to a separate module: `finance/services/integration/`
   - This would make it clearer which services require management context

---

## 7. Summary

### Key External Dependencies of Finance

1. **shared_core** (✅ LOW RISK): ~40+ files - Infrastructure only, safe
2. **management** (❌ HIGH RISK): ~14 files - Task system, compliance, salary calculations
3. **main** (⚠️ MEDIUM RISK): ~5 files - Service definitions, some Company references
4. **investing** (✅ LOW RISK): ~2 files - Optional, graceful degradation
5. **ai_services** (✅ LOW RISK): ~3 files - Optional AI features

### Where Equity Should Live Inside Finance

**Recommended Structure:**
```
coda/finance/
├── models/
│   └── equity.py                    # ✅ Isolated, only Django + shared_core
├── services/
│   └── equity/                        # ✅ Isolated, uses finance.utils only
│       ├── equity_config_service.py
│       ├── equity_scoring_engine.py
│       ├── equity_snapshot_service.py
│       └── equity_export_service.py
├── views/
│   └── equity/                      # ✅ Isolated, uses equity models/services
│       ├── deal_views.py
│       ├── ledger_views.py
│       └── snapshot_views.py
└── templates/
    └── finance/
        └── equity/                  # ✅ Isolated, templates only
```

**Avoid These Areas:**
- `finance/services/realtime_compliance_service.py` (has management deps)
- `finance/services/integrated_budget_service.py` (has management deps)
- `finance/views/budget/views_salary_dashboard.py` (has management deps)

### What External Developers Can Safely Work On

**✅ SAFE:**
- All equity module code (`models/equity.py`, `services/equity/`, `views/equity/`, `templates/finance/equity/`)
- Finance utilities that don't import management (`utils/currency_converter.py`)
- Most finance models (check individual files)
- Finance services that don't import management

**Required Knowledge:**
- Django ORM
- `shared_core.models` and `shared_core.users`
- `finance.utils.currency_converter`
- Basic finance patterns (approvals, configs)

**NOT Required:**
- Management app's task system
- Management app's compliance rules
- Management app's salary calculations

**Conclusion:** External developers can safely implement the equity module within the finance app, working in isolated sub-modules that avoid management dependencies. The finance app is **mostly safe** for external development, with clear boundaries around management-dependent services.

---

**Document Status:** ✅ Complete  
**Next Steps:** Apply guardrails during equity module implementation




