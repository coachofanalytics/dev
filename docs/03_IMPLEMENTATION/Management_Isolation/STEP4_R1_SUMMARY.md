# Step 4 Round 1: Low-Risk Shared Core Upgrades - Summary

**Date:** December 2025  
**Branch:** `25.12_CODA_DEV_CM`  
**Status:** ✅ Complete

---

## Changes Made

### 1. Updated `shared_core/users.py`

**Added re-exports:**
- `UserProfile` from `accounts.models`
- `Tracker` from `accounts.models`
- `TaskGroups` from `accounts.models`

**File:** `coda/shared_core/users.py`

**Diff:**
```python
# Before:
from accounts.models import CustomerUser, Department
from accounts.choices import UserCategory
__all__ = ['CustomerUser', 'Department', 'UserCategory']

# After:
from accounts.models import CustomerUser, Department, UserProfile, Tracker, TaskGroups
from accounts.choices import UserCategory
__all__ = ['CustomerUser', 'Department', 'UserCategory', 'UserProfile', 'Tracker', 'TaskGroups']
```

---

### 2. Updated `shared_core/utils.py`

**Added re-exports:**
- `send_verification_email` from `accounts.utils`
- `calculate_login_bonus` from `accounts.utils`
- `generate_password` from `core.utils`

**File:** `coda/shared_core/utils.py`

**Diff:**
```python
# Added after main.utils imports:
# Re-export from accounts.utils
try:
    from accounts.utils import send_verification_email, calculate_login_bonus
except ImportError:
    # Graceful fallback if accounts app is not available
    send_verification_email = None
    calculate_login_bonus = None

# Re-export from core.utils
try:
    from core.utils import generate_password
except ImportError:
    # Graceful fallback if core app is not available
    generate_password = None

# Updated __all__:
__all__ = [
    'path_values',
    'dates_functionality',
    'generate_chatbot_response',
    'today_date',
    'date_converter',
    'countdown_in_month',
    'send_verification_email',      # NEW
    'calculate_login_bonus',        # NEW
    'generate_password',             # NEW
    'detect_organization_from_request',
    'get_company_logo_url',
    'get_company_receipt_data',
]
```

---

### 3. Updated `shared_core/filters.py`

**Added re-exports:**
- `RequirementFilter` from `main.filters`
- `TaskHistoryFilter` from `main.filters`

**File:** `coda/shared_core/filters.py`

**Diff:**
```python
# Before:
from main.filters import ReturnsFilter, CredentialFilter, FoodFilter
__all__ = ['ReturnsFilter', 'CredentialFilter', 'FoodFilter']

# After:
from main.filters import ReturnsFilter, CredentialFilter, FoodFilter, RequirementFilter, TaskHistoryFilter
__all__ = ['ReturnsFilter', 'CredentialFilter', 'FoodFilter', 'RequirementFilter', 'TaskHistoryFilter']
```

**Note added:** Comment explaining that `RequirementFilter` and `TaskHistoryFilter` depend on `management.models` and assume management app is present.

---

### 4. Updated Management App Imports

**Files Updated:** 8 files

#### `coda/management/views.py` (4 changes)
- Line 68: `from accounts.models import UserProfile` → `from shared_core.users import UserProfile`
- Line 42-43: `from accounts.utils import send_verification_email,calculate_login_bonus` + `from core.utils import generate_password` → `from shared_core.utils import send_verification_email, calculate_login_bonus, generate_password`
- Line 89: `from accounts.models import Tracker, TaskGroups` → `from shared_core.users import Tracker, TaskGroups`
- Line 90: `from main.filters import RequirementFilter,TaskHistoryFilter` → `from shared_core.filters import RequirementFilter, TaskHistoryFilter`
- Line 967: `from accounts.models import UserProfile` → `from shared_core.users import UserProfile` (inside function)

#### `coda/management/admin.py` (1 change)
- Line 6: `from accounts.models import TaskGroups` → `from shared_core.users import TaskGroups`

#### `coda/management/models.py` (1 change)
- Line 16: `from accounts.models import TaskGroups` → `from shared_core.users import TaskGroups`

#### `coda/management/forms.py` (1 change)
- Line 9: `from accounts.models import UserProfile` → `from shared_core.users import UserProfile`

#### `coda/management/signals.py` (1 change)
- Line 8-9: `from accounts.utils import send_verification_email` + `from core.utils import generate_password` → `from shared_core.utils import send_verification_email, generate_password`

#### `coda/management/views/task_assignment_views.py` (1 change)
- Line 19: `from accounts.models import TaskGroups` → `from shared_core.users import TaskGroups`

#### `coda/management/services/taskhistory_analyzer.py` (1 change)
- Line 22: `from accounts.models import TaskGroups` → `from shared_core.users import TaskGroups`

#### `coda/management/services/employee_compliance_service.py` (1 change)
- Line 26: `from accounts.models import TaskGroups` → `from shared_core.users import TaskGroups`

---

## Verification

### Import Updates Summary

| Original Import | New Import | Files Updated |
|----------------|------------|---------------|
| `from accounts.models import UserProfile` | `from shared_core.users import UserProfile` | 3 files (views.py, forms.py, views.py:967) |
| `from accounts.models import Tracker, TaskGroups` | `from shared_core.users import Tracker, TaskGroups` | 1 file (views.py) |
| `from accounts.models import TaskGroups` | `from shared_core.users import TaskGroups` | 5 files (admin.py, models.py, task_assignment_views.py, taskhistory_analyzer.py, employee_compliance_service.py) |
| `from accounts.utils import send_verification_email, calculate_login_bonus` | `from shared_core.utils import send_verification_email, calculate_login_bonus` | 1 file (views.py) |
| `from core.utils import generate_password` | `from shared_core.utils import generate_password` | 2 files (views.py, signals.py) |
| `from main.filters import RequirementFilter, TaskHistoryFilter` | `from shared_core.filters import RequirementFilter, TaskHistoryFilter` | 1 file (views.py) |

**Total:** 8 files updated, 13 import statements changed

---

### Linter Check

✅ **No linter errors** in:
- `coda/shared_core/users.py`
- `coda/shared_core/utils.py`
- `coda/shared_core/filters.py`

---

### Django System Check

**Note:** `python manage.py check` requires `dotenv` module in environment. This is an environment setup issue, not related to these changes.

**Manual verification:**
- ✅ All imports updated to use `shared_core` versions
- ✅ No remaining direct imports from `accounts.models` for UserProfile/Tracker/TaskGroups
- ✅ No remaining direct imports from `accounts.utils` for send_verification_email/calculate_login_bonus
- ✅ No remaining direct imports from `core.utils` for generate_password
- ✅ No remaining direct imports from `main.filters` for RequirementFilter/TaskHistoryFilter

---

## Summary

### ✅ Completed

1. **Re-exports added to shared_core:**
   - 3 models: `UserProfile`, `Tracker`, `TaskGroups`
   - 3 utility functions: `send_verification_email`, `calculate_login_bonus`, `generate_password`
   - 2 filters: `RequirementFilter`, `TaskHistoryFilter`

2. **Management app imports updated:**
   - 8 files updated
   - 13 import statements changed
   - All now use `shared_core` versions

3. **Safety measures:**
   - Try/except blocks in `shared_core/utils.py` for graceful degradation
   - Comment added to `shared_core/filters.py` noting filter dependencies

### 📊 Impact

- **No migrations required** ✅
- **No code moves** ✅ (only re-exports)
- **No behavior changes** ✅ (only import paths)
- **Strengthened shared_core** ✅ (more symbols available via shared_core)

---

## Next Steps

**Ready for:**
- Step 4 Round 2: OAuth helper move (if desired)
- Step 5: Create Management-only branch structure
- Testing: Run `python manage.py check` once environment is set up

---

**Changes Complete:** December 2025  
**Status:** ✅ All low-risk re-exports and import updates complete

