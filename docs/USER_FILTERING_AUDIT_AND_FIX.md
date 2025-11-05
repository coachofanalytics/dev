# User Filtering Audit & Fix Plan
**CRITICAL UX & SECURITY ISSUE**

## Problem Statement

**Current State:**  
Forms across the CODA platform are showing **ALL users** in dropdown/select fields, regardless of user category or active status. This creates:

1. **Poor UX**: Users see hundreds of irrelevant options (applicants, inactive users, students, etc.)
2. **Security Risk**: Exposes user information to unauthorized viewers
3. **Business Logic Errors**: Allows incorrect user assignments (e.g., assigning a student as an account manager)
4. **Performance Issues**: Loading 100+ users in every dropdown slows page rendering

**Example from Production:**  
`/investing/managed/onboarding/application/add/` shows ~100+ users in "Account Manager" dropdown, including:
- Inactive users
- Students (category=2)
- Applicants (category=1)  
- Explorers (category=5)
- Former employees

**Expected Behavior:**
- **Investing App**: `client` field → Active Investors only | `account_manager` field → Active Staff only
- **Professional Services**: `student` field → Active Students only | `instructor` field → Active Staff only
- **Management**: `employee` field → Active Staff only | `manager` field → Active Managers/Executives only
- **Finance**: Similar category-based filtering

---

## User Categorization System

### Primary Categories (from `accounts.choices.UserCategory`)

```python
class UserCategory(models.IntegerChoices):
    APPLICANT = 1   # Want to work for CODA
    STUDENT = 2     # Taking courses
    CONSULTANT = 3  # Professionals, advisors, service providers
    INVESTOR = 4    # Financial, strategic, KCC members
    EXPLORER = 5    # Visitors, researchers, networkers
```

### Key User States

1. **Active Staff**: `is_staff=True` AND `is_active=True`
2. **Active Investor**: `category=4` AND `is_active=True`
3. **Active Student**: `category=2` AND `is_active=True`
4. **Active Consultant**: `category=3` AND `is_active=True`
5. **Active Applicant**: `category=1` AND `is_active=True`

### Staff Levels (from `accounts.models.UserProfile.StaffLevel`)

```python
class StaffLevel(models.TextChoices):
    JUNIOR = 'junior'
    SENIOR = 'senior'
    MANAGER = 'manager'
    EXECUTIVE = 'executive'
```

---

## Audit Results by App

### 1. **INVESTING APP** 🔴 CRITICAL

#### Forms with Unfiltered User Fields

| Form | Field | Current | Should Be |
|------|-------|---------|-----------|
| `ManagedAccountForm` | `client` | All users | Active Investors (`category=4`, `is_active=True`) |
| `ManagedAccountForm` | `account_manager` | All users | Active Staff (`is_staff=True`, `is_active=True`) |
| `ManagedTradingApplicationForm` | `preferred_manager` | ✅ **FILTERED** `is_staff=True` | ✅ Already correct (line 229) |
| `OptionsPositionForm` | `managed_account` | All accounts | Active accounts only |
| `QuickPositionEntryForm` | `account` | ✅ **FILTERED** `status='active'` | ✅ Already correct |
| `InvestorForm` | (model) `investor` FK | All users | Active Investors |
| `Investor_Information` model | `investor` FK | All users | Active Investors |
| `ManagedTradingAccount` model | `client` FK | All users | Active Investors |
| `ManagedTradingAccount` model | `account_manager` FK | All users | Active Staff |

**Admin Interface:**  
- `ManagedTradingAccountAdmin`: Needs queryset filtering in `formfield_for_foreignkey()`

#### Files to Fix
1. ✅ `forms.py` → `ManagedAccountForm.__init__()` - **NEEDS FIX**
2. ✅ `forms.py` → `OptionsPositionForm.__init__()` - **NEEDS FIX**
3. ✅ `admin.py` → `ManagedTradingAccountAdmin.formfield_for_foreignkey()` - **NEEDS FIX**
4. ✅ `forms_onboarding.py` → `ManagedTradingApplicationForm.__init__()` - Already has filtering (line 229)

---

### 2. **PROFESSIONAL SERVICES APP** 🔴 CRITICAL

#### Expected Filtering Rules
- **Instructor/Teacher**: Active Staff
- **Student**: `category=2` AND `is_active=True`
- **Consultant**: `category=3` AND `is_active=True`

#### Files to Audit
- `professional_services/forms.py`
- `professional_services/admin.py`
- `professional_services/models.py` (ForeignKey definitions)

---

### 3. **MANAGEMENT APP** 🟡 MEDIUM PRIORITY

#### Expected Filtering Rules
- **Employee**: Active Staff (`is_staff=True`, `is_active=True`)
- **Manager**: Active Staff + `profile.staff_level='manager'`
- **Department Head**: Active Staff + `profile.staff_level='executive'`

#### Files to Audit
- `management/forms.py`
- `management/admin.py`

---

### 4. **FINANCE APP** 🟡 MEDIUM PRIORITY

#### Expected Filtering Rules
- **Approver**: Active Staff (managers/executives)
- **Purchaser**: Active Staff
- **Budget Owner**: Active Staff (managers/executives)

#### Files to Audit
- `finance/forms.py`
- `finance/forms_improved.py`
- `finance/forms_food.py`
- `finance/forms/budget.py`
- `finance/admin.py`

---

### 5. **ACCOUNTS APP** 🟢 LOW PRIORITY

Most forms here are for user registration/profile editing, so "all users" may be intentional for admin views.

#### Files to Review
- `accounts/forms.py`
- `accounts/admin.py`

---

### 6. **AI SERVICES APP** 🟢 LOW PRIORITY

#### Files to Review
- `ai_services/forms.py`
- `ai_services/admin.py`

---

## Solution Pattern

### Django Form `__init__()` Method

**BEFORE (Wrong):**
```python
class ManagedAccountForm(forms.ModelForm):
    class Meta:
        model = ManagedTradingAccount
        fields = ['client', 'account_manager', ...]
    
    # No __init__ - uses default queryset (ALL users)
```

**AFTER (Correct):**
```python
class ManagedAccountForm(forms.ModelForm):
    class Meta:
        model = ManagedTradingAccount
        fields = ['client', 'account_manager', ...]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter client to active investors only
        if 'client' in self.fields:
            from accounts.choices import UserCategory
            self.fields['client'].queryset = User.objects.filter(
                category=UserCategory.INVESTOR,
                is_active=True
            ).order_by('first_name', 'last_name')
        
        # Filter account_manager to active staff only
        if 'account_manager' in self.fields:
            self.fields['account_manager'].queryset = User.objects.filter(
                is_staff=True,
                is_active=True
            ).order_by('first_name', 'last_name')
```

### Django Admin `formfield_for_foreignkey()` Method

**BEFORE (Wrong):**
```python
@admin.register(ManagedTradingAccount)
class ManagedTradingAccountAdmin(admin.ModelAdmin):
    list_display = ['account_number', 'client', 'account_manager', ...]
    # No formfield_for_foreignkey - uses default (ALL users)
```

**AFTER (Correct):**
```python
@admin.register(ManagedTradingAccount)
class ManagedTradingAccountAdmin(admin.ModelAdmin):
    list_display = ['account_number', 'client', 'account_manager', ...]
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Filter user foreign keys by category and active status"""
        from accounts.choices import UserCategory
        
        if db_field.name == 'client':
            kwargs['queryset'] = User.objects.filter(
                category=UserCategory.INVESTOR,
                is_active=True
            ).order_by('first_name', 'last_name')
        
        elif db_field.name == 'account_manager':
            kwargs['queryset'] = User.objects.filter(
                is_staff=True,
                is_active=True
            ).order_by('first_name', 'last_name')
        
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
```

---

## Reusable Utility Functions

Create `accounts/utilities/user_querysets.py`:

```python
"""
Reusable user queryset filters for forms and admin
Ensures consistent filtering across the entire platform
"""
from django.contrib.auth import get_user_model
from accounts.choices import UserCategory

User = get_user_model()


def get_active_staff_queryset():
    """Get queryset of active staff members (all levels)"""
    return User.objects.filter(
        is_staff=True,
        is_active=True
    ).order_by('first_name', 'last_name')


def get_active_managers_queryset():
    """Get queryset of active managers and executives only"""
    return User.objects.filter(
        is_staff=True,
        is_active=True,
        profile__staff_level__in=['manager', 'executive']
    ).select_related('profile').order_by('first_name', 'last_name')


def get_active_investors_queryset():
    """Get queryset of active investors"""
    return User.objects.filter(
        category=UserCategory.INVESTOR,
        is_active=True
    ).order_by('first_name', 'last_name')


def get_active_students_queryset():
    """Get queryset of active students"""
    return User.objects.filter(
        category=UserCategory.STUDENT,
        is_active=True
    ).order_by('first_name', 'last_name')


def get_active_consultants_queryset():
    """Get queryset of active consultants"""
    return User.objects.filter(
        category=UserCategory.CONSULTANT,
        is_active=True
    ).order_by('first_name', 'last_name')


def get_active_applicants_queryset():
    """Get queryset of active applicants"""
    return User.objects.filter(
        category=UserCategory.APPLICANT,
        is_active=True
    ).order_by('first_name', 'last_name')
```

---

## Implementation Plan

### Phase 1: INVESTING APP (CRITICAL) - **START HERE**

**Goal:** Fix all user filtering issues in the investing app before moving to other apps.

#### Step 1.1: Create Utility Functions
- [ ] Create `accounts/utilities/user_querysets.py` with reusable queryset functions
- [ ] Add tests for each queryset function
- [ ] Document usage in docstrings

#### Step 1.2: Fix `ManagedAccountForm`
- [ ] Add `__init__()` method to `investing/forms.py:ManagedAccountForm`
- [ ] Filter `client` → `get_active_investors_queryset()`
- [ ] Filter `account_manager` → `get_active_staff_queryset()`
- [ ] Test form rendering locally
- [ ] Test form submission locally

#### Step 1.3: Fix `OptionsPositionForm`
- [ ] Add `__init__()` method to `investing/forms.py:OptionsPositionForm`
- [ ] Filter `managed_account` → only active accounts
- [ ] Test form rendering locally

#### Step 1.4: Fix Admin Interface
- [ ] Add `formfield_for_foreignkey()` to `investing/admin.py:ManagedTradingAccountAdmin`
- [ ] Filter `client` and `account_manager` fields
- [ ] Test admin add/edit pages locally
- [ ] Verify dropdown shows only filtered users

#### Step 1.5: Fix Models (if needed)
- [ ] Review `Investor_Information.investor` ForeignKey
- [ ] Consider adding `limit_choices_to` in model definition
- [ ] Document any model changes

#### Step 1.6: Deployment
- [ ] Run all investing app tests
- [ ] Deploy to UAT
- [ ] Test on UAT with real data
- [ ] Deploy to Production
- [ ] Verify in production (screenshot dropdown)

---

### Phase 2: PROFESSIONAL SERVICES APP (CRITICAL)

#### Step 2.1: Audit Forms
- [ ] List all forms with user ForeignKey fields
- [ ] Document current behavior
- [ ] Define correct filtering rules

#### Step 2.2: Implement Fixes
- [ ] Apply same pattern as investing app
- [ ] Use utility functions from `user_querysets.py`
- [ ] Test locally

#### Step 2.3: Deployment
- [ ] Test on UAT
- [ ] Deploy to Production

---

### Phase 3: MANAGEMENT APP (MEDIUM PRIORITY)

#### Step 3.1: Audit Forms
- [ ] Focus on employee assignment forms
- [ ] Check task assignment forms
- [ ] Check payroll forms

#### Step 3.2: Implement Fixes
- [ ] Use `get_active_staff_queryset()`
- [ ] Use `get_active_managers_queryset()` for manager-only fields

#### Step 3.3: Deployment
- [ ] Test on UAT
- [ ] Deploy to Production

---

### Phase 4: FINANCE APP (MEDIUM PRIORITY)

#### Step 4.1: Audit Forms
- [ ] Budget approval forms
- [ ] Purchase request forms
- [ ] Loan application forms

#### Step 4.2: Implement Fixes
- [ ] Filter approvers → active managers
- [ ] Filter purchasers → active staff

#### Step 4.3: Deployment
- [ ] Test on UAT
- [ ] Deploy to Production

---

### Phase 5: OTHER APPS (LOW PRIORITY)

- [ ] AI Services
- [ ] Marketing
- [ ] Accounts (admin only)

---

## Testing Checklist (Per App)

### Manual Testing
- [ ] Form loads without errors
- [ ] Dropdown shows only filtered users
- [ ] User count is significantly reduced (e.g., 100+ → 10-20)
- [ ] Correct users are shown (investors, staff, etc.)
- [ ] Form submission works
- [ ] Saved data is correct

### Automated Testing
- [ ] Unit test: queryset function returns correct users
- [ ] Integration test: form `__init__()` applies correct queryset
- [ ] Admin test: `formfield_for_foreignkey()` applies correct queryset

### Production Verification
- [ ] Take screenshot of dropdown BEFORE fix (shows 100+ users)
- [ ] Take screenshot of dropdown AFTER fix (shows 10-20 filtered users)
- [ ] Document in this file

---

## Rollout Strategy

### Step-by-Step Approach

**Why App-by-App?**
1. **Risk Mitigation**: If a fix breaks something, only one app is affected
2. **Incremental Testing**: Easier to verify each fix in production
3. **Rollback Safety**: Can revert one app without affecting others
4. **User Feedback**: Can gather feedback on each app before proceeding

**Order:**
1. ✅ **Investing** (highest visibility, critical business operations)
2. ✅ **Professional Services** (student/instructor management)
3. ✅ **Management** (internal staff operations)
4. ✅ **Finance** (budget/payment approvals)
5. ✅ **Others** (as needed)

### Emergency Rollback Plan

If a fix causes issues in production:
1. Identify the broken form
2. Comment out `__init__()` or `formfield_for_foreignkey()` method
3. Commit with message: `Rollback: Revert user filtering for <FormName>`
4. Deploy immediately
5. Fix locally and redeploy

---

## Expected Impact

### Before Fix
- **100+ users** in every dropdown (all categories, active + inactive)
- Staff sees students, applicants, explorers in "Account Manager" field
- Investors see applicants, students in "Client" field
- Page load time: ~500ms+ (loading 100+ users)

### After Fix
- **10-20 users** in dropdowns (filtered by category + active status)
- Staff sees only active staff in "Account Manager" field
- Investors see only active investors in "Client" field
- Page load time: ~200ms (loading 10-20 users)

### UX Improvement
- **90% reduction** in dropdown clutter
- **Clearer user intent** (only valid options shown)
- **Faster page loads** (fewer DOM elements)
- **Better security** (less user data exposure)

---

## Success Criteria

### For Each App

1. ✅ All user ForeignKey fields are filtered by category + active status
2. ✅ Admin interface uses `formfield_for_foreignkey()` for filtering
3. ✅ Forms use `__init__()` for queryset filtering
4. ✅ Utility functions from `user_querysets.py` are used consistently
5. ✅ Tests pass locally and on UAT
6. ✅ Production deployment successful
7. ✅ User feedback is positive (dropdowns are cleaner)

### Overall Project

- ✅ All 28 files with user ForeignKeys are audited
- ✅ All critical apps (Investing, Professional Services) are fixed
- ✅ Reusable utility functions are created and documented
- ✅ Testing strategy is established and followed
- ✅ Production verification screenshots are captured

---

## Files Affected (Summary)

### To Create (New Files)
1. `accounts/utilities/user_querysets.py` - Reusable queryset functions
2. `tests/test_user_querysets.py` - Tests for queryset functions

### To Modify (Existing Files)

#### Investing App (Phase 1)
1. `investing/forms.py` - Add `__init__()` to `ManagedAccountForm`, `OptionsPositionForm`
2. `investing/admin.py` - Add `formfield_for_foreignkey()` to `ManagedTradingAccountAdmin`

#### Professional Services App (Phase 2)
3. `professional_services/forms.py` - TBD after audit
4. `professional_services/admin.py` - TBD after audit

#### Management App (Phase 3)
5. `management/forms.py` - TBD after audit
6. `management/admin.py` - TBD after audit

#### Finance App (Phase 4)
7. `finance/forms.py` - TBD after audit
8. `finance/forms_improved.py` - TBD after audit
9. `finance/forms_food.py` - TBD after audit
10. `finance/forms/budget.py` - TBD after audit
11. `finance/admin.py` - TBD after audit

#### Other Apps (Phase 5)
12. `ai_services/forms.py` - TBD
13. `ai_services/admin.py` - TBD
14. `accounts/forms.py` - Review only
15. `accounts/admin.py` - Review only
16. `marketing/forms.py` - TBD
17. `marketing/admin.py` - TBD

---

## Notes

- This document will be updated as each phase is completed
- Screenshots of BEFORE/AFTER should be added to `docs/assets/user_filtering/`
- All changes should follow the established pattern for consistency
- Utility functions should be tested independently before use

---

## References

- **User Categories**: `accounts/choices.py:UserCategory`
- **User Model**: `accounts/models.py:CustomerUser`
- **Staff Levels**: `accounts/models.py:UserProfile.StaffLevel`
- **Existing Utility**: `accounts/utils.py:employees()` (line 79) - example of filtering active staff

---

**Document Created:** November 5, 2025  
**Last Updated:** November 5, 2025  
**Status:** Phase 1 (Investing App) - Ready to Begin  
**Next Action:** Create `accounts/utilities/user_querysets.py`

