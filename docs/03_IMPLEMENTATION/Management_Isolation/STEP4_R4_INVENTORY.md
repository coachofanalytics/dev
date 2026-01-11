# Step 4 Round 4 - Professional Services Usage Inventory

## Part A - Inventory of professional_services Usage in Management App

### Files with Direct Imports

#### 1. `coda/management/views.py`
- **Imports**: `from professional_services.models import DSU, ClientAssessment, BackgroundCheck`
- **Usage**:
  - `DSUListView` (line 2025) - List DSU records filtered by user_type (Staff/Client)
    - **Type**: Staff-facing view
    - **Purpose**: Display DSU (Daily Standup) records for HR/staff review
  - `AssessUpdateView` (line 2037) - Update DSU records
    - **Type**: Admin/staff-only view
    - **Purpose**: Edit existing DSU records
  - `assess()` function (line 2005) - Create DSU records
    - **Type**: Staff-facing view
    - **Purpose**: Create new DSU/assessment records via form
  - `add_background_info()` (line 2267) - Create BackgroundCheck records
    - **Type**: Staff-facing view
    - **Purpose**: Add background check information
  - `BackgroundCheckListView` (line 2277) - List BackgroundCheck records
    - **Type**: Admin/staff-facing view
    - **Purpose**: Display background checks with status filtering

#### 2. `coda/management/forms.py`
- **Imports**: `from professional_services.models import DSU, ClientAssessment, BackgroundCheck`
- **Usage**:
  - `ManagementForm` (line 70) - Form for DSU model
    - **Type**: Staff-facing form
    - **Purpose**: Create/edit DSU records with fields: trained_by, client_name, type, category, task, plan, challenge, uploaded
  - `ClientAssessmentForm` (line 96) - Form for ClientAssessment model
    - **Type**: Staff-facing form
    - **Purpose**: Create/edit client assessments with skills, experience, education fields
  - `BackgroundForm` - Form for BackgroundCheck model
    - **Type**: Staff-facing form
    - **Purpose**: Create/edit background check records

#### 3. `coda/management/signals.py`
- **Imports**: `from professional_services.models import ClientAssessment`
- **Usage**:
  - Commented-out signal handler (lines 11-35)
    - **Type**: Background signal (currently disabled)
    - **Purpose**: Would create CustomerUser when ClientAssessment is created (currently commented out)

#### 4. `coda/management/models.py`
- **Imports**: `from professional_services.models import FeaturedCategory, FeaturedSubCategory, FeaturedActivity`
- **Usage**:
  - `Training` model (line 26) - ForeignKey relationships
    - **Type**: Model definition (affects Training feature)
    - **Purpose**: Training model has FKs to FeaturedCategory, FeaturedSubCategory, FeaturedActivity
    - **Impact**: Training feature requires professional_services app

### Summary by Feature Type

**DSU (Daily Standup) Features:**
- List view (staff-facing)
- Create view (staff-facing)
- Update view (admin/staff)
- Form for create/edit

**Client Assessment Features:**
- Form for create/edit (staff-facing)
- Signal handler (commented out, would create users)

**Background Check Features:**
- List view (admin/staff)
- Create view (staff-facing)
- Form for create/edit

**Training Features:**
- Training model depends on FeaturedCategory/SubCategory/Activity
- Requires feature gating for Management-only branch

### Access Patterns

- **Staff-facing**: DSU list/create, ClientAssessment form, BackgroundCheck create
- **Admin-only**: DSU update, BackgroundCheck list
- **Model dependencies**: Training model (requires professional_services for taxonomy)

