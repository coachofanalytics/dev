# Team Management Reuse Audit Report

## Executive Summary

**Question:** Can `/team-management/` be reused to manage Employee Group A/B/C (policy groups)?

**Answer:** **HYBRID** - Partial reuse possible, but semantic mismatch requires careful design.

**Recommendation:** **Option 2 (Minimal New Page)** - Create a dedicated "Employee Groups" page that reuses UI patterns but keeps data separate.

---

## Quick Reference Table

| Aspect | Team Management | Employee Groups (A/B/C) |
|--------|----------------|------------------------|
| **URL** | `/team-management/` | `/management/employee-groups/` (proposed) |
| **Purpose** | Organizational hierarchy, public display | Policy enforcement (compliance rules) |
| **Storage** | Django `Group` (M2M) | `EmployeeCareerState.group` (CharField) |
| **Model** | `TeamProfile` (OneToOne) | `EmployeeCareerState` (OneToOne) |
| **Values** | "BOG-Leadership", "Elite Team", etc. | "A", "B", "C" |
| **Permissions** | `is_superuser` only | `is_staff` (manager-friendly) |
| **Auto-Assignment** | Points-based | None (manual only) |
| **Current LOC** | ~1,048 lines | 0 (needs implementation) |

---

## 1. What Exists Today

### URL Configuration
- **URL Pattern:** `/team-management/`
- **Route Name:** `main:team_management_dashboard`
- **File:** `coda/main/urls.py:13`
- **Additional Routes:**
  - `/team-management/recalculate-points/` → `recalculate_all_points`
  - `/team-management/assign/<user_id>/<category_name>/` → `assign_member_to_category`
  - `/team-management/remove/<user_id>/<category_name>/` → `remove_member_from_category`
  - `/team-management/update-priority/<user_id>/` → `update_member_priority`
  - `/team-management/<category_name>/` → `team_category_detail`

### View Implementation
- **File:** `coda/main/views_team_management.py`
- **Type:** Function-Based Views (FBV)
- **Functions:**
  - `team_management_dashboard()` - Main dashboard
  - `team_category_detail()` - Category detail page
  - `assign_member_to_category()` - Assign user to team
  - `remove_member_from_category()` - Remove user from team
  - `update_member_priority()` - Update display priority
  - `recalculate_all_points()` - Recalculate points for auto-assignment

### Templates
- **Dashboard:** `coda/main/templates/main/team_management/dashboard.html`
- **Category Detail:** `coda/main/templates/main/team_management/category_detail.html`
- **Base Template:** `main/base_templates/new_base.html`

### Models Used

#### Primary Models:
1. **`auth.Group` (Django built-in)**
   - Stores team category membership (M2M through `user.groups`)
   - Categories: `BOG-Leadership`, `Elite Team`, `Lead Team`, `Support Team`, `Senior Analysts`, `Junior Analysts`, `Senior Trainee`, `Junior Trainee`, `Elementary`, `Available for Hire`
   - **Key Point:** Team categories are stored as Django Groups

2. **`accounts.TeamProfile`**
   - OneToOne to `CustomerUser` (via `user` field)
   - Fields: `priority`, `total_points`, `is_manually_assigned`, `last_promoted`, `promotion_notes`
   - **Key Point:** Metadata about team assignment (not the assignment itself)

3. **`auth.User` / `accounts.CustomerUser`**
   - Uses `get_user_model()` (likely `CustomerUser`)
   - Membership stored via `user.groups` (M2M to `Group`)

#### Related Models (NOT used in team-management):
- **`management.EmployeeCareerState`** - Stores policy group (A/B/C) - **NOT used by team-management**
- **`accounts.UserProfile`** - User profile data (position, education, etc.)

### Service Layer
- **File:** `coda/main/services/team_service.py`
- **Class:** `TeamService`
- **Purpose:** Business logic for team assignment, point calculation, auto-categorization
- **Key Methods:**
  - `get_team_members(category_name)` - Get users in a category
  - `assign_to_category(user, category_name, priority, is_manual, notes)` - Assign user to team
  - `calculate_total_points(user)` - Calculate points from education, tasks, requirements, training, assessments
  - `auto_categorize_by_points(user)` - Auto-assign based on points

---

## 2. Current Purpose and Data Model

### What "Teams" Represent Today

**Team Management** is used for **organizational hierarchy and display**:
- **Leadership:** BOG-Leadership, Elite Team
- **Core Team:** Lead Team, Support Team, Senior Analysts, Junior Analysts
- **Trainees:** Senior Trainee, Junior Trainee, Elementary
- **Special:** Available for Hire

**Purpose:**
- Public-facing team page display (`/members/<title>`)
- Internal team organization
- Promotion tracking (points-based auto-assignment)
- Display priority management

### How Membership is Stored

**Storage Mechanism:**
- **Primary:** Django `Group` model (M2M through `user.groups`)
- **Metadata:** `TeamProfile` model (OneToOne to User)
- **Assignment Method:** 
  - Manual: `is_manually_assigned=True` in `TeamProfile`
  - Auto: Points-based calculation assigns to appropriate group

**Key Characteristics:**
- User can be in **ONE team category** at a time (exclusive)
- `TeamService.assign_to_category()` clears existing team groups before adding new one
- Categories are **global** (not per-department/region)

### Permissions

**Current Access Control:**
- **View/Edit:** `@user_passes_test(lambda u: u.is_superuser)` - **Superuser only**
- **Location:** `coda/main/views_team_management.py:24-25`

**Note:** More restrictive than EmployeeCareerState admin (which allows `is_staff`).

---

## 3. Evaluation: Can We Reuse for Employee Group A/B/C?

### Semantic Mismatch Analysis

| Aspect | Team Management | Employee Group (A/B/C) |
|--------|----------------|----------------------|
| **Purpose** | Organizational hierarchy, public display | Policy enforcement (compliance rules) |
| **Storage** | Django `Group` (M2M) | `EmployeeCareerState.group` (CharField) |
| **Model** | `TeamProfile` (OneToOne) | `EmployeeCareerState` (OneToOne) |
| **Values** | "BOG-Leadership", "Elite Team", etc. | "A", "B", "C" (single char) |
| **Exclusivity** | One team category per user | One policy group per user |
| **Auto-Assignment** | Points-based (education, tasks, etc.) | None (manual only) |
| **Display** | Public-facing team pages | Internal policy enforcement |

### Risks of Reusing Team Management

#### ❌ **HIGH RISK: Semantic Confusion**
- **Problem:** Team categories (BOG, Elite, etc.) are **organizational roles**, not policy groups
- **Impact:** Managers might confuse "assigning to Elite Team" with "setting policy group to A"
- **Example:** User in "Elite Team" (organizational) might need Group B (policy) - these are independent

#### ⚠️ **MEDIUM RISK: Data Model Mismatch**
- **Problem:** Team Management uses Django `Group` (M2M), Employee Groups use `EmployeeCareerState.group` (CharField)
- **Impact:** Would require mapping logic: `Group.name` → `EmployeeCareerState.group`
- **Complexity:** Need to sync two separate systems

#### ⚠️ **MEDIUM RISK: Permission Mismatch**
- **Problem:** Team Management requires `is_superuser`, Employee Groups need `is_staff` (manager-friendly)
- **Impact:** Managers who can edit Employee Groups cannot access Team Management
- **Solution:** Would need to relax permissions (risky for team management)

#### ⚠️ **LOW RISK: Side Effects on Existing Workflows**
- **Problem:** Team Management has auto-assignment logic (`recalculate_all_points`)
- **Impact:** If we add policy groups to Team Management, auto-assignment might interfere
- **Mitigation:** Could disable auto-assignment for policy groups

#### ⚠️ **LOW RISK: Reporting/Filtering Conflicts**
- **Problem:** Team categories are used in public pages and reports
- **Impact:** Mixing policy groups with team categories could break existing queries
- **Mitigation:** Keep data separate, use different field names

### Potential Reuse Approaches

#### Approach A: Map Team Categories to Policy Groups
**Idea:** Create Django Groups "Group A", "Group B", "Group C" and use Team Management UI

**Problems:**
- Semantic confusion (team category ≠ policy group)
- Would pollute team category list with policy groups
- Auto-assignment logic doesn't apply to policy groups
- Permission mismatch (superuser vs staff)

**Verdict:** ❌ **NOT RECOMMENDED**

#### Approach B: Add Policy Group Column to Team Management UI
**Idea:** Add `EmployeeCareerState.group` as a column in the team category detail page

**Problems:**
- UI clutter (mixing two unrelated concepts)
- Still requires separate data model
- Permission mismatch
- Doesn't solve bulk assignment need

**Verdict:** ⚠️ **PARTIAL - Could work but not ideal**

#### Approach C: Hybrid - Separate Section in Team Management
**Idea:** Add a new section "Policy Groups" to Team Management dashboard, but keep data separate

**Problems:**
- Still semantic confusion (why are policy groups in "Team Management"?)
- Permission mismatch
- Requires significant template changes

**Verdict:** ⚠️ **POSSIBLE but not clean**

---

## 4. Solution Options

### Option 1: Reuse /team-management/ (NOT RECOMMENDED)

**Approach:** Add policy groups as special "team categories" in Team Management

**Required Changes:**

1. **Create Django Groups for Policy Groups:**
   - File: `coda/main/services/team_service.py`
   - Add to `ALL_CATEGORIES`: `['Group A', 'Group B', 'Group C']`
   - Add to `MANUAL_CATEGORIES`: `['Group A', 'Group B', 'Group C']` (always manual)

2. **Add Sync Logic:**
   - File: `coda/main/views_team_management.py`
   - In `assign_member_to_category()`: If category is "Group A/B/C", also update `EmployeeCareerState.group`
   - In `remove_member_from_category()`: If category is "Group A/B/C", set `EmployeeCareerState.group = 'B'` (default)

3. **Relax Permissions:**
   - File: `coda/main/views_team_management.py`
   - Change `@user_passes_test(lambda u: u.is_superuser)` to `@user_passes_test(lambda u: u.is_staff)`
   - **RISK:** This allows staff to edit ALL team categories (not just policy groups)

4. **Update Templates:**
   - File: `coda/main/templates/main/team_management/dashboard.html`
   - Add visual distinction for policy groups vs team categories
   - File: `coda/main/templates/main/team_management/category_detail.html`
   - Show `EmployeeCareerState.group` value alongside team category

**Problems:**
- ❌ Semantic confusion (policy groups ≠ team categories)
- ❌ Permission risk (staff can edit all team categories)
- ❌ Data sync complexity (two systems to keep in sync)
- ❌ UI clutter (mixing unrelated concepts)

**Verdict:** ❌ **NOT RECOMMENDED**

---

### Option 2: Minimal New Page (RECOMMENDED) ✅

**Approach:** Create a dedicated "Employee Groups" page that reuses UI patterns but keeps data separate

**Required Changes:**

1. **New URL Route:**
   - File: `coda/management/urls.py`
   - Add: `path('employee-groups/', views.employee_groups_view, name='employee_groups')`

2. **New View:**
   - File: `coda/management/views.py` (or create `coda/management/views_employee_groups.py`)
   - Function: `employee_groups_view(request)` - List employees with group assignment
   - Function: `update_employee_group(request, user_id)` - Update `EmployeeCareerState.group`
   - Function: `bulk_update_employee_groups(request)` - Bulk assign groups

3. **New Template:**
   - File: `coda/management/templates/management/employee_groups.html`
   - **Reuse patterns from:** `team_management/category_detail.html`
   - Show: User list, current group (A/B/C), dropdown to change, bulk actions

4. **Reuse Existing Admin:**
   - File: `coda/management/admin.py` (already exists: `EmployeeCareerStateAdmin`)
   - Keep Django admin as fallback for complex edits

**Advantages:**
- ✅ Clear semantic separation (policy groups ≠ team categories)
- ✅ Appropriate permissions (`is_staff` for managers)
- ✅ No data sync complexity (single source of truth: `EmployeeCareerState`)
- ✅ Clean UI (focused on policy groups only)
- ✅ Reuses UI patterns (similar to team management)
- ✅ Minimal code duplication (can import helper functions)

**Implementation Steps:**
1. Create `coda/management/views_employee_groups.py` (new file)
2. Add URL route in `coda/management/urls.py`
3. Create template `coda/management/templates/management/employee_groups.html` (reuse team management patterns)
4. Add bulk action view for setting multiple users to same group
5. Add tests in `coda/management/tests/test_employee_groups_view.py`

**Estimated LOC:** ~200 lines (view) + ~150 lines (template) = ~350 lines total

---

## 5. Recommended Approach

**RECOMMENDATION: Option 2 (Minimal New Page)**

### Rationale:
1. **Semantic Clarity:** Policy groups (A/B/C) are fundamentally different from team categories (BOG, Elite, etc.)
2. **Permission Alignment:** Managers need `is_staff` access, not `is_superuser`
3. **Data Integrity:** Single source of truth (`EmployeeCareerState.group`) avoids sync issues
4. **Maintainability:** Separate concerns = easier to maintain
5. **User Experience:** Dedicated page is clearer than mixing concepts

### Implementation Plan

#### Phase 1: Core View and Template
1. Create `coda/management/views_employee_groups.py`:
   ```python
   @login_required
   @user_passes_test(lambda u: u.is_staff)
   def employee_groups_view(request):
       # List all active staff employees with their current group
       # Show filter/search
       # Show bulk actions
   ```

2. Create `coda/management/templates/management/employee_groups.html`:
   - Reuse card layout from `team_management/dashboard.html`
   - Show three cards: "Group A", "Group B", "Group C" with member counts
   - Click card → detail page with user list and group assignment UI

3. Add URL route in `coda/management/urls.py`

#### Phase 2: Detail Page and Actions
4. Create detail view: `employee_group_detail(request, group_letter)`:
   - Show all employees in selected group
   - Show employees not in any group (default to B)
   - Add/remove employees from group
   - Bulk assign action

5. Create action views:
   - `assign_employee_to_group(request, user_id, group_letter)`
   - `bulk_assign_employees_to_group(request)` (POST with user_ids list)

#### Phase 3: Integration
6. Add link from Django admin `EmployeeCareerStateAdmin` to new page
7. Add link from `/management/tasks/` page (for managers)
8. Add tests

---

## 6. Implementation Steps (Option 2)

### Step-by-Step Implementation

1. **Create View File:**
   - File: `coda/management/views_employee_groups.py` (NEW)
   - Functions:
     - `employee_groups_view(request)` - Dashboard
     - `employee_group_detail(request, group_letter)` - Detail page
     - `assign_employee_to_group(request, user_id, group_letter)` - Assign action
     - `bulk_assign_employees_to_group(request)` - Bulk action

2. **Add URL Routes:**
   - File: `coda/management/urls.py`
   - Add:
     ```python
     path('employee-groups/', views_employee_groups.employee_groups_view, name='employee_groups'),
     path('employee-groups/<str:group_letter>/', views_employee_groups.employee_group_detail, name='employee_group_detail'),
     path('employee-groups/assign/<int:user_id>/<str:group_letter>/', views_employee_groups.assign_employee_to_group, name='assign_employee_to_group'),
     path('employee-groups/bulk-assign/', views_employee_groups.bulk_assign_employees_to_group, name='bulk_assign_employees_to_group'),
     ```

3. **Create Template:**
   - File: `coda/management/templates/management/employee_groups.html` (NEW)
   - Reuse patterns from `team_management/dashboard.html` and `team_management/category_detail.html`
   - Show: Group cards, member counts, search/filter, bulk actions

4. **Reuse Service Logic:**
   - File: `coda/management/services/policy_resolver.py` (already exists)
   - Use `PolicyResolver.for_group(group_letter)` to get policy config for display

5. **Add Tests:**
   - File: `coda/management/tests/test_employee_groups_view.py` (NEW)
   - Test: Staff can access, non-staff cannot, bulk assignment works, group changes persist

---

## 7. Verification Steps

### Manual QA Checklist

1. **Access Control:**
   - [ ] Navigate to `/management/employee-groups/` as staff user → Should load
   - [ ] Navigate as non-staff user → Should return 403 or redirect
   - [ ] Navigate as superuser → Should load

2. **Dashboard Display:**
   - [ ] See three cards: "Group A", "Group B", "Group C"
   - [ ] Each card shows member count
   - [ ] Click card → Navigate to detail page

3. **Detail Page:**
   - [ ] Shows list of employees in selected group
   - [ ] Shows "Available Employees" section (not in group or in different group)
   - [ ] Search/filter works
   - [ ] "Assign to Group X" button works

4. **Bulk Actions:**
   - [ ] Select multiple employees → Bulk assign to Group A → All updated
   - [ ] Verify in Django admin that `EmployeeCareerState.group` is updated

5. **Policy Integration:**
   - [ ] Assign user to Group A → Navigate to their DAF v2 → See "Policy: Group A" badge
   - [ ] Verify policy rules apply (e.g., Group A requires meeting for internal training)

### Test Command

```bash
# Run tests
poetry run python coda/manage.py test management.tests.test_employee_groups_view -v 2

# System check
poetry run python coda/manage.py check
```

---

## 8. Files Summary

### Current Team Management Files
- **URLs:** `coda/main/urls.py:13-19`
- **Views:** `coda/main/views_team_management.py` (238 lines)
- **Service:** `coda/main/services/team_service.py` (333 lines)
- **Templates:** 
  - `coda/main/templates/main/team_management/dashboard.html` (214 lines)
  - `coda/main/templates/main/team_management/category_detail.html` (267 lines)
- **Models:** `auth.Group`, `accounts.TeamProfile`, `auth.User`

### Proposed Employee Groups Files (Option 2)
- **URLs:** `coda/management/urls.py` (add 4 routes)
- **Views:** `coda/management/views_employee_groups.py` (NEW, ~200 lines)
- **Templates:** `coda/management/templates/management/employee_groups.html` (NEW, ~150 lines)
- **Models:** `management.EmployeeCareerState` (already exists)
- **Service:** `coda/management/services/policy_resolver.py` (already exists, reuse)

---

## 9. Final Recommendation

**✅ RECOMMEND: Option 2 (Minimal New Page)**

**Rationale:**
- Clear semantic separation
- Appropriate permissions
- Single source of truth
- Reuses UI patterns without mixing concepts
- Minimal code (~350 lines total)
- Easy to maintain and extend

**Next Steps:**
1. Review this audit with stakeholders
2. If approved, implement Option 2
3. Add link from Django admin and `/management/tasks/` page
4. Test and deploy

---

**Report Generated:** 2024-12-29  
**Auditor:** AI Assistant  
**Branch:** 25.12_CODA_DEV_CM

