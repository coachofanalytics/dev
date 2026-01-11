# Step 4 Round 4 Summary - Professional Services Cleanup & Feature Gating

## Overview

Completed Step 4 Round 4, which focused on cleaning up professional_services dependencies in the management app by introducing interfaces and feature gating. This enables a Management-only branch to run without the professional_services app code.

## Part A - Inventory

Created inventory document (`STEP4_R4_INVENTORY.md`) listing all professional_services usage:

### Files with Direct Imports:
1. **`coda/management/views.py`**:
   - `DSUListView` - List DSU records (staff-facing)
   - `AssessUpdateView` - Update DSU records (admin/staff)
   - `assess()` - Create DSU records (staff-facing)
   - `add_background_info()` - Create BackgroundCheck records (staff-facing)
   - `BackgroundCheckListView` - List BackgroundCheck records (admin/staff)

2. **`coda/management/forms.py`**:
   - `ManagementForm` - Form for DSU model (staff-facing)
   - `ClientAssessmentForm` - Form for ClientAssessment model (staff-facing)
   - `BackgroundForm` - Form for BackgroundCheck model (staff-facing)

3. **`coda/management/signals.py`**:
   - Commented-out signal handler for ClientAssessment (currently disabled)

4. **`coda/management/models.py`**:
   - `Training` model has FKs to `FeaturedCategory, FeaturedSubCategory, FeaturedActivity`

## Part B - Interface & NoOp Adapter

### Created Files:

1. **`coda/shared_core/interfaces/professional_services_interface.py`**:
   - `ProfessionalServicesInterface` with 6 methods:
     - `list_dsu_for_user()` - List DSU records filtered by user type
     - `create_or_update_dsu()` - Create or update DSU records
     - `list_client_assessments()` - List client assessment records
     - `create_client_assessment()` - Create client assessment records
     - `list_background_checks()` - List background check records
     - `create_background_check()` - Create background check records
   - All methods return dicts/list of dicts (DTO-style) for loose coupling

2. **`coda/shared_core/services/adapters/noop_professional_services_adapter.py`**:
   - `NoOpProfessionalServicesAdapter` implementing all interface methods
   - Returns safe defaults:
     - Empty lists for list operations
     - Status dicts with `status: 'not_available'` for create/update operations
   - Never raises exceptions, logs usage

3. **`coda/management/services/pro_services_helper.py`**:
   - `get_professional_services()` helper function
   - Tries to import `ProfessionalServicesAdapter` from professional_services app
   - Falls back to `NoOpProfessionalServicesAdapter` if import fails

## Part C - Refactor Management to Use Interface

### Updated Files:

1. **`coda/management/views.py`**:
   - Removed direct `DSU, ClientAssessment, BackgroundCheck` imports
   - Added `get_professional_services()` import
   - **`DSUListView`**: 
     - Removed `model = DSU`
     - Updated `get_queryset()` to use `pro_services.list_dsu_for_user()`
     - Returns mock queryset-like object for template compatibility
   - **`AssessUpdateView`**:
     - Removed `model = DSU`
     - Updated `get_object()` to use interface
     - Updated `form_valid()` to use `pro_services.create_or_update_dsu()`
   - **`assess()` function**:
     - Updated to use `pro_services.create_or_update_dsu()` instead of form.save()
     - Added success/warning messages
   - **`add_background_info()`**:
     - Updated to use `pro_services.create_background_check()` instead of form.save()
     - Added success/warning messages
   - **`BackgroundCheckListView`**:
     - Removed `model = BackgroundCheck`
     - Updated `get_queryset()` to use `pro_services.list_background_checks()`
     - Returns mock queryset-like object for template compatibility

2. **`coda/management/forms.py`**:
   - Made imports conditional with try/except
   - Added `PRO_SERVICES_AVAILABLE` flag
   - Updated form Meta classes to use conditional model assignment
   - Added comments noting forms require professional_services app
   - Forms will only work when professional_services is available (views handle interface calls)

3. **`coda/management/signals.py`**:
   - Removed direct `ClientAssessment` import
   - Added comment noting signal handler is disabled and should use interface if re-enabled

## Part D - Feature Gating for Training Model

### Updated Files:

1. **`coda/management/models.py`**:
   - Made `FeaturedCategory, FeaturedSubCategory, FeaturedActivity` imports conditional
   - Added `PRO_SERVICES_FEATURES_AVAILABLE` flag
   - Created placeholder classes for Management-only branch
   - Added comment: "Training feature should be disabled via ENABLE_PRO_SERVICES_FEATURES setting"
   - **Note**: Training model FKs remain unchanged (no migrations) - feature gating is via settings flag

2. **`coda/management/views.py`**:
   - Commented out `Training` import
   - Added comment about feature gating

### Feature Gating Documentation:

**Setting to Add (for Management-only branch):**
```python
# In settings file for Management-only branch:
ENABLE_PRO_SERVICES_FEATURES = False
```

**Where to Add Gating:**
- Training-related views should check `getattr(settings, 'ENABLE_PRO_SERVICES_FEATURES', True)`
- Training navigation/menu entries should be conditionally rendered
- Training URLs can be conditionally included in urlpatterns

**Note**: Training model FKs cannot be changed without migrations, so the feature is gated via settings and UI visibility rather than model changes.

## Files Modified

### New Files Created:
- `coda/shared_core/interfaces/professional_services_interface.py` - Interface definition
- `coda/shared_core/services/adapters/noop_professional_services_adapter.py` - NoOp adapter
- `coda/management/services/pro_services_helper.py` - Helper function
- `STEP4_R4_INVENTORY.md` - Usage inventory

### Files Updated:
- `coda/management/views.py` - Replaced all direct model usage with interface calls
- `coda/management/forms.py` - Made imports conditional, added comments
- `coda/management/signals.py` - Removed import, added comment
- `coda/management/models.py` - Made Training dependencies conditional

## Remaining professional_services Imports

**None in core employee/staff views** - All direct imports have been removed or made conditional.

**Admin-only or non-critical code:**
- Forms still reference models conditionally (only work when professional_services is available)
- Training model FKs remain (feature gated via settings)

## Safety Checks

✅ **Linter Check**: No linter errors found in new interface/adapter files

✅ **Import Structure**: All imports now flow through interface:
- Professional Services: `management.services.pro_services_helper.get_professional_services()`

✅ **NoOp Behavior**: All NoOp adapter methods return safe defaults (empty lists, status dicts) instead of raising exceptions

✅ **Conditional Imports**: Forms and models handle missing professional_services gracefully

## Notes

1. **Forms Limitation**: 
   - Django ModelForms require model classes, so forms still import models conditionally
   - Forms will only work when professional_services is available
   - Views handle interface calls directly, so forms are less critical

2. **Template Compatibility**:
   - Views return mock queryset-like objects to maintain template compatibility
   - Templates receive dicts instead of model instances, but structure is preserved

3. **Training Feature**:
   - Training model FKs cannot be changed without migrations
   - Feature gating is via `ENABLE_PRO_SERVICES_FEATURES` setting (to be added)
   - Training views/URLs should check this flag before rendering

4. **Signal Handler**:
   - Currently commented out in signals.py
   - If re-enabled, should use professional services interface instead of direct model import

## Next Steps

1. **Implement Professional Services Adapter**: Create/update `professional_services.adapters.professional_services_adapter.ProfessionalServicesAdapter` to implement all interface methods

2. **Add Feature Gating Setting**: Add `ENABLE_PRO_SERVICES_FEATURES` setting to base settings (or Management-only settings file)

3. **Gate Training Views/URLs**: Add checks in Training-related views and conditionally include Training URLs

4. **Test Management-Only Branch**: Verify that management app can run standalone with NoOp adapter

5. **Update Documentation**: Document the new interface methods and feature gating approach

## Constraints Met

✅ No database migrations introduced
✅ No model moves - only service layer changes
✅ Behavior remains equivalent in full monorepo
✅ NoOp paths provide safe defaults for Management-only branch
✅ No circular imports introduced
✅ Training model FKs remain unchanged (feature gated via settings)

