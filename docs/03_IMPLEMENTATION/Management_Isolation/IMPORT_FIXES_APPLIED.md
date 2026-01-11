# Import Fixes Applied - Step 4 Round 4

## Files Updated

### High Priority Fixes ✅

1. **`coda/main/views.py`**
   - ✅ Changed: `from accounts.models import UserProfile` → `from shared_core.users import UserProfile`

2. **`coda/application/views.py`**
   - ✅ Changed: `from accounts.models import UserProfile` → `from shared_core.users import UserProfile`

3. **`coda/application/services.py`**
   - ✅ Changed: `from accounts.models import UserProfile` → `from shared_core.users import UserProfile`

4. **`coda/application/forms.py`**
   - ✅ Changed: `from accounts.models import UserProfile` → `from shared_core.users import UserProfile`

5. **`coda/ai_services/views.py`**
   - ✅ Changed: `from accounts.models import TaskGroups` → `from shared_core.users import TaskGroups`

6. **`coda/coda_project/task.py`**
   - ✅ Changed: `from accounts.models import TaskGroups` → `from shared_core.users import TaskGroups`

7. **`coda/main/management/commands/verify_team_members.py`**
   - ✅ Changed: `from accounts.models import UserProfile, CustomerUser` → `from shared_core.users import UserProfile, CustomerUser`

8. **`coda/application/management/commands/manage_kcc.py`**
   - ✅ Changed: `from accounts.models import UserProfile` → `from shared_core.users import UserProfile`

9. **`coda/application/admin_kcc_dashboard.py`**
   - ✅ Changed: `from accounts.models import UserProfile` → `from shared_core.users import UserProfile`

10. **`coda/application/admin_kcc.py`**
    - ✅ Changed: `from accounts.models import UserProfile` → `from shared_core.users import UserProfile`

11. **`coda/management/services/utilities_service.py`**
    - ✅ Removed deprecated `AIBudgetSuggestionService` import and references
    - ✅ Updated comment to note budget suggestions use finance interface

## Summary

✅ **11 files updated** to use `shared_core.users` instead of direct `accounts.models` imports
✅ **1 file cleaned up** (removed deprecated import from utilities_service.py)

All cross-app imports for UserProfile, CustomerUser, and TaskGroups now flow through `shared_core.users` for better app isolation.

## Next Steps

1. Run `python coda/manage.py check` to verify no import errors
2. Review finance services AI imports (may be acceptable if internal implementation)
3. Test Management-only branch scenario

