# Import Sanity Check - Step 4 Round 4

## Summary

This document analyzes imports across the codebase to ensure consistency with the new shared_core/interfaces architecture introduced in Steps 4 R1-R4.

---

## 1. Django System Check

**Status**: Unable to run full check due to missing dependencies (dotenv, django, etc. in test environment)

**Recommendation**: Run manually with proper virtual environment:
```bash
cd /Users/coda/Projects/uat/coda
python manage.py check
```

---

## 2. Stray Imports Analysis

### Category A: accounts.models imports

#### ✅ Expected / Allowed (within accounts app or admin-only)
1. **`coda/accounts/views.py:50`** - `from accounts.models import UserProfile`
   - **Reason**: Within accounts app itself
   - **Action**: Keep as-is

#### ⚠️ Needs Update (should use shared_core.users)

2. **`coda/main/views.py:25`** - `from accounts.models import UserProfile`
   - **Current**: Direct import
   - **Should be**: `from shared_core.users import UserProfile`
   - **Reason**: Cross-app import should use shared_core

3. **`coda/application/views.py:26`** - `from accounts.models import UserProfile`
   - **Current**: Direct import
   - **Should be**: `from shared_core.users import UserProfile`
   - **Reason**: Cross-app import should use shared_core

4. **`coda/application/services.py:14`** - `from accounts.models import UserProfile`
   - **Current**: Direct import
   - **Should be**: `from shared_core.users import UserProfile`
   - **Reason**: Cross-app import should use shared_core

5. **`coda/application/forms.py:5`** - `from accounts.models import UserProfile`
   - **Current**: Direct import
   - **Should be**: `from shared_core.users import UserProfile`
   - **Reason**: Cross-app import should use shared_core

6. **`coda/main/management/commands/verify_team_members.py:10`** - `from accounts.models import UserProfile, CustomerUser`
   - **Current**: Direct import
   - **Should be**: `from shared_core.users import UserProfile, CustomerUser`
   - **Reason**: Cross-app import should use shared_core

7. **`coda/application/management/commands/manage_kcc.py:11`** - `from accounts.models import UserProfile`
   - **Current**: Direct import
   - **Should be**: `from shared_core.users import UserProfile`
   - **Reason**: Cross-app import should use shared_core

8. **`coda/application/admin_kcc_dashboard.py:18`** - `from accounts.models import UserProfile`
   - **Current**: Direct import
   - **Should be**: `from shared_core.users import UserProfile`
   - **Reason**: Admin code, but should use shared_core for consistency

9. **`coda/application/admin_kcc.py:16`** - `from accounts.models import UserProfile`
   - **Current**: Direct import
   - **Should be**: `from shared_core.users import UserProfile`
   - **Reason**: Admin code, but should use shared_core for consistency

#### ⚠️ Needs Update (TaskGroups/Tracker)

10. **`coda/ai_services/views.py:11`** - `from accounts.models import TaskGroups`
    - **Current**: Direct import
    - **Should be**: `from shared_core.users import TaskGroups`
    - **Reason**: Should use shared_core

11. **`coda/coda_project/task.py:19`** - `from accounts.models import TaskGroups`
    - **Current**: Direct import
    - **Should be**: `from shared_core.users import TaskGroups`
    - **Reason**: Should use shared_core

---

### Category B: accounts.utils / core.utils imports

#### ✅ Expected / Allowed (within shared_core/utils itself)
1. **`coda/shared_core/utils/__init__.py:42`** - `from accounts.utils import send_verification_email, calculate_login_bonus`
   - **Reason**: This is the re-export mechanism in shared_core
   - **Action**: Keep as-is (already wrapped in try/except)

2. **`coda/shared_core/utils/__init__.py:50`** - `from core.utils import generate_password`
   - **Reason**: This is the re-export mechanism in shared_core
   - **Action**: Keep as-is (already wrapped in try/except)

**No other direct imports found** - Good! ✅

---

### Category C: main.filters imports

**Status**: ✅ No stray imports found
- All imports should now go through `shared_core.filters`

---

### Category D: AI Services imports

#### ✅ Expected / Allowed (within ai_services app itself)
1. **`coda/ai_services/tasks.py:42,223`** - `from ai_services.views import getmeetingresponse, save_meeting_data`
   - **Reason**: Within ai_services app itself
   - **Action**: Keep as-is

#### ⚠️ Needs Update (should use interface)

2. **`coda/finance/services/smart_data_correction_service.py:18`** - `from ai_services.ai_integration_service import RealAIService`
   - **Current**: Direct import
   - **Should be**: Use `get_ai_service()` helper (if finance needs AI service) OR create finance-specific helper
   - **Recommendation**: Create `finance/services/ai_helper.py` similar to `management/services/ai_service_helper.py`, or use shared helper

3. **`coda/finance/services/ai_budget_suggestion_service.py:20`** - `from ai_services.ai_integration_service import RealAIService`
   - **Current**: Direct import
   - **Should be**: Use `get_ai_service()` helper
   - **Note**: This service is already being accessed via FinanceTaskServiceInterface.get_budget_suggestion(), so this import might be internal to the service implementation
   - **Recommendation**: If this is the implementation of the finance adapter, it's acceptable. Otherwise, should use interface.

---

### Category E: Finance imports

#### ✅ Expected / Allowed (within finance app itself)
1. **`coda/finance/views/budget/views_detailed_budget.py:21`** - `from finance.services.ai_budget_suggestion_service import AIBudgetSuggestionService`
   - **Reason**: Within finance app itself
   - **Action**: Keep as-is

#### ✅ Already Fixed (conditional import)
2. **`coda/management/views.py:1009`** - `from finance.models import PayslipConfig` (inside try/except)
   - **Reason**: Already wrapped in try/except for backward compatibility in get_user_data()
   - **Action**: Keep as-is (temporary bridge)

3. **`coda/management/services/utilities_service.py:54`** - `from finance.services.ai_budget_suggestion_service import AIBudgetSuggestionService`
   - **Status**: ⚠️ This was supposed to be removed in R3
   - **Current**: Still has direct import (but marked as deprecated)
   - **Should be**: Should use `get_finance_task_service().get_budget_suggestion()` instead
   - **Action**: **Needs fix** - Remove this import, use finance interface

4. **`coda/coda_project/task.py:19`** - `from finance.models import LoanApplication,PayslipConfig`
   - **Current**: Direct import
   - **Recommendation**: If this is admin/background task code, could be acceptable. Otherwise, should use finance interface.
   - **Action**: Review context - if not admin-only, should use interface

5. **`coda/application/management/commands/manage_kcc.py:11`** - `from finance.models import LoanApplication`
   - **Current**: Direct import
   - **Recommendation**: Management command - could be acceptable, but should ideally use interface

6. **`coda/application/admin_kcc_dashboard.py:18`** - `from finance.models import LoanApplication, LoanPayment`
   - **Current**: Direct import
   - **Reason**: Admin-only code
   - **Action**: Keep as-is (admin code acceptable)

7. **`coda/application/admin_kcc.py:16`** - `from finance.models import LoanApplication, LoanPayment`
   - **Current**: Direct import
   - **Reason**: Admin-only code
   - **Action**: Keep as-is (admin code acceptable)

---

### Category F: Professional Services imports

#### ✅ Already Fixed / Expected
1. **`coda/management/views.py:87`** - Commented out, using interface ✅
2. **`coda/management/signals.py:5`** - Commented out ✅
3. **`coda/management/forms.py:8`** - Conditional import (try/except) ✅
4. **`coda/management/models.py:20`** - Conditional import (try/except) ✅

#### ✅ Expected / Allowed (within professional_services app or other apps using it)
5. **`coda/main/views.py:20,61`** - `from professional_services.models import ClientAssessment`
   - **Reason**: main app using professional_services directly (not management app)
   - **Action**: Keep as-is (main app is separate from management isolation goal)

6. **`coda/main/services/team_service.py:247`** - `from professional_services.models import ClientAssessment` (inside try/except)
   - **Reason**: Conditional import in main app
   - **Action**: Keep as-is

7. **`coda/main/management/commands/show_promotion_candidates.py:108`** - `from professional_services.models import ClientAssessment` (inside try/except)
   - **Reason**: Conditional import in management command
   - **Action**: Keep as-is

8. **`coda/main/forms.py:8`** - `from professional_services.models import DSU`
   - **Reason**: main app using professional_services directly
   - **Action**: Keep as-is

9. **`coda/application/permission.py:1`** - `from professional_services.models import ClientAssessment`
   - **Reason**: application app using professional_services directly
   - **Action**: Keep as-is (application is separate from management)

10. **`coda/api/viewsets.py:20`** - `from professional_services.models import ClientAssessment, JobRoles`
    - **Reason**: API layer using professional_services directly
    - **Action**: Keep as-is

11. **`coda/api/serializers.py:16`** - `from professional_services.models import ClientAssessment, JobRoles`
    - **Reason**: API layer using professional_services directly
    - **Action**: Keep as-is

12. **`coda/main/context_processors.py:5`** - `from professional_services.models import FeaturedCategory,FeaturedSubCategory, Training_Responses`
    - **Reason**: main app using professional_services directly
    - **Action**: Keep as-is

13. **`coda/application/utils.py:1`** - `from professional_services.models import FeaturedCategory`
    - **Reason**: application app using professional_services directly
    - **Action**: Keep as-is

---

## 3. Files That Need Import Updates

### High Priority (Management app isolation goal)

1. **`coda/main/views.py:25`**
   - Change: `from accounts.models import UserProfile` → `from shared_core.users import UserProfile`

2. **`coda/application/views.py:26`**
   - Change: `from accounts.models import UserProfile` → `from shared_core.users import UserProfile`

3. **`coda/application/services.py:14`**
   - Change: `from accounts.models import UserProfile` → `from shared_core.users import UserProfile`

4. **`coda/application/forms.py:5`**
   - Change: `from accounts.models import UserProfile` → `from shared_core.users import UserProfile`

5. **`coda/ai_services/views.py:11`**
   - Change: `from accounts.models import TaskGroups` → `from shared_core.users import TaskGroups`

6. **`coda/management/services/utilities_service.py:54`**
   - **Remove**: `from finance.services.ai_budget_suggestion_service import AIBudgetSuggestionService`
   - **Already using**: finance interface via `get_finance_task_service().get_budget_suggestion()`
   - **Action**: Remove deprecated import and any references

### Medium Priority (Consistency, but lower impact)

7. **`coda/main/management/commands/verify_team_members.py:10`**
   - Change: `from accounts.models import UserProfile, CustomerUser` → `from shared_core.users import UserProfile, CustomerUser`

8. **`coda/application/management/commands/manage_kcc.py:11`**
   - Change: `from accounts.models import UserProfile` → `from shared_core.users import UserProfile`

9. **`coda/application/admin_kcc_dashboard.py:18`**
   - Change: `from accounts.models import UserProfile` → `from shared_core.users import UserProfile`

10. **`coda/application/admin_kcc.py:16`**
    - Change: `from accounts.models import UserProfile` → `from shared_core.users import UserProfile`

11. **`coda/coda_project/task.py:19`**
    - Change: `from accounts.models import TaskGroups` → `from shared_core.users import TaskGroups`
    - **Note**: This is a background task file - review if it should use interfaces

### Low Priority (Review needed - may be acceptable)

12. **`coda/finance/services/smart_data_correction_service.py:18`**
    - Review: `from ai_services.ai_integration_service import RealAIService`
    - **Recommendation**: If this is internal to finance service implementation, acceptable. Otherwise, should use AI interface.

13. **`coda/finance/services/ai_budget_suggestion_service.py:20`**
    - Review: `from ai_services.ai_integration_service import RealAIService`
    - **Recommendation**: If this is the implementation of the finance adapter for budget suggestions, acceptable. Otherwise, should use AI interface.

14. **`coda/coda_project/task.py:19`**
    - Review: `from finance.models import LoanApplication,PayslipConfig`
    - **Recommendation**: Background task - review if should use finance interface

---

## 4. Circular Import Check

**Status**: Unable to verify without running full Django check

**Recommendation**: Run `python manage.py check` in proper environment to detect any circular imports

**Known potential cycles to watch for**:
- `shared_core` ↔ `management` ↔ `finance` ↔ `ai_services`
- Interface helpers should break cycles (they use try/except imports)

---

## 5. Summary & Recommendations

### ✅ Good News

1. **Management app is clean**: All professional_services imports in management app are either:
   - Using interfaces (DSU, ClientAssessment, BackgroundCheck)
   - Conditional imports with try/except (forms, models)

2. **Shared core re-exports working**: `shared_core.utils` and `shared_core.users` are properly set up

3. **Filter imports clean**: No stray `main.filters` imports found

4. **Most cross-app imports identified**: Clear list of what needs updating

### ⚠️ Issues Found

1. **11 files need UserProfile import updates** (should use `shared_core.users`)
2. **2 files need TaskGroups import updates** (should use `shared_core.users`)
3. **1 file still has deprecated AIBudgetSuggestionService import** (`management/services/utilities_service.py`)
4. **2 finance services have RealAIService imports** (need review)

### 🎯 Recommended Actions

#### Immediate (High Priority)
1. Update all `from accounts.models import UserProfile` → `from shared_core.users import UserProfile` (11 files)
2. Update all `from accounts.models import TaskGroups` → `from shared_core.users import TaskGroups` (2 files)
3. Remove deprecated `AIBudgetSuggestionService` import from `utilities_service.py`

#### Next Steps
1. Run full Django check in proper environment: `python coda/manage.py check`
2. Review finance services AI imports (may be acceptable if internal implementation)
3. Review background task imports (`coda_project/task.py`) - decide if should use interfaces

#### Future Considerations
- Consider creating a shared AI helper in `shared_core` for use by finance and other apps
- Document which imports are acceptable in admin-only code vs. core app code
- Consider interface for LoanApplication if needed by management app

---

## 6. Test Checklist

Once fixes are applied, verify:

- [ ] `python coda/manage.py check` passes without ImportError
- [ ] No circular import warnings
- [ ] Management app can import without finance/ai_services/professional_services apps
- [ ] All management views/forms/services use shared_core/interfaces correctly
- [ ] Admin code still works (may use direct imports if acceptable)

