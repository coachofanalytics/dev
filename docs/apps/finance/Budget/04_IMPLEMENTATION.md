# Budget System - Implementation

**Last Updated:** October 22, 2025  
**Version:** Phase 2 Complete (Data-Driven Tier System) ✅  
**Purpose:** Technical implementation details, code locations, and developer reference

---

## 📁 FILE STRUCTURE

```
coda/finance/
├── models/
│   └── budget.py                    # All budget models (1,355 lines)
│
├── views/
│   └── budget/
│       ├── approvals.py            # Approval dashboard & actions
│       ├── editing.py              # Create/edit budget requests
│       ├── views_unified_budget.py # Main dashboard
│       └── views_tier_management.py # Finance Manager tier control
│
├── services/
│   └── budget/
│       ├── smart_approval_service.py    # Tier-based routing (Phase 2)
│       ├── automation_service.py        # Auto-approval logic
│       └── budget_service.py            # Business logic (future)
│
├── management/commands/
│   ├── generate_budget_projections.py   # AI budget forecasting
│   ├── classify_budget_category_tiers.py # Tier classification
│   ├── analyze_transaction_data.py      # Spending analysis
│   └── verify_dashboard_fix.py          # Regression testing
│
├── templates/finance/budgets/
│   ├── unified_budget_dashboard.html    # Main dashboard
│   ├── budget_approvals.html            # Approval interface
│   ├── budget_request_form.html         # Request creation
│   ├── tier_management_dashboard.html   # Tier control (Phase 2)
│   └── auto_approval_log.html           # Auto-approval history
│
├── forms_improved.py                # Budget forms with smart features
├── urls.py                          # URL configuration
└── admin.py                         # Django admin registration
```

---

## 🗄️ KEY MODELS

### 1. Budget
**File:** `coda/finance/models/budget.py` (lines 230-468)  
**Purpose:** Core budget planning model - individual budget line items

**Key Fields:**
- `company`, `department`, `category`, `subcategory` - Organization
- `item_name`, `quantity`, `unit_price`, `cases` - Item details
- `budget_lead`, `date_from`, `date_to` - Ownership & timeline
- `is_active` - Status flag

**Critical Property:**
```python
@property
def total_amount(self):
    """Formula: unit_price * quantity * cases"""
    return (self.unit_price or 0) * (self.quantity or 0) * (self.cases or 1)
```

**Current Data:** 266 active items, $837K total budget

---

### 2. BudgetCategory
**File:** `coda/finance/models/budget.py` (lines 34-138)  
**Purpose:** Budget category classification with tier-based approval

**Phase 1 Fields:**
- `name`, `description` - Basic info
- `parent_category` - Hierarchy

**Phase 2 Fields (Added Oct 16):**
- `approval_tier` - A/B/C classification
- `auto_approve_enabled` - Finance Manager toggle
- `typical_monthly_amount` - From $1.49M data analysis
- `variance_threshold` - Anomaly detection %
- `is_recurring` - Pattern detected
- `last_pattern_analysis` - Analysis timestamp

**Key Methods:**
```python
def should_auto_approve(self, amount):
    """Check if amount qualifies for auto-approval"""
    if not self.auto_approve_enabled or self.approval_tier != 'A':
        return False
    return self.is_within_variance(amount)

def is_within_variance(self, amount):
    """Check if amount within acceptable variance"""
    if not self.typical_monthly_amount:
        return False
    variance = abs(amount - self.typical_monthly_amount) / self.typical_monthly_amount * 100
    return variance <= self.variance_threshold
```

---

### 3. BudgetRequest
**File:** `coda/finance/models/budget.py` (lines 540-717)  
**Purpose:** Budget request submission and approval workflow

**Core Fields:**
- `requester`, `amount`, `purpose` - Request details
- `department`, `budget_category`, `priority` - Classification
- `status` - draft/submitted/pending/approved/rejected

**Approval Tracking (Oct 13 - Migration 0099):**
- `approved_by`, `approved_at` - Approval audit
- `rejected_by`, `rejected_at`, `rejection_reason` - Rejection audit
- `current_approver`, `approval_chain` - Workflow tracking

**Key Methods:**
```python
def approve(self, user, notes=''):
    """Approve budget request"""
    self.status = 'approved'
    self.approved_by = user
    self.approved_at = timezone.now()
    self.save()
    send_budget_approval_email(self)  # Notification

def reject(self, user, reason):
    """Reject budget request"""
    self.status = 'rejected'
    self.rejected_by = user
    self.rejected_at = timezone.now()
    self.rejection_reason = reason
    self.save()
    send_budget_rejection_email(self)  # Notification
```

---

### 4. ApprovalPolicy
**File:** `coda/finance/models/budget.py` (lines 719-841)  
**Purpose:** Configurable approval rules and routing

**Fields:**
- `name`, `description` - Policy identification
- `min_amount`, `max_amount` - Amount thresholds
- `approver_roles` - JSONField with role list
- `approval_chain` - JSONField with sequential steps
- `auto_approve` - Boolean flag
- `applicable_departments`, `applicable_categories` - M2M applicability
- `priority` - Policy matching order

---

### 5. BudgetEstimateProjection
**File:** `coda/finance/models/budget.py` (lines 498-515)  
**Purpose:** AI-generated budget forecasts

**Fields:**
- `company`, `department` - Scope
- `method` - transaction_analysis/historical_avg/trend_forecast
- `horizon` - monthly/quarterly/yearly
- `estimates` - JSONField with category breakdowns
- `total_estimate` - Total projected budget
- `status` - draft/active/archived

**Generated by:** `generate_budget_projections` command  
**Current Data:** 13 projections, $722K recommended annual budget

---

## 🎯 KEY VIEWS

### 1. unified_budget_dashboard
**File:** `coda/finance/views_unified_budget.py` (lines 23-201)  
**URL:** `/finance/budget-dashboard/{company_slug}/`

**Purpose:** Main budget dashboard with 5 tabs

**Key Functions:**
```python
def unified_budget_dashboard(request, company_slug):
    """Main budget dashboard"""
    company = get_object_or_404(Company, slug=company_slug)
    active_tab = request.GET.get('tab', 'overview')
    
    context = {
        'company': company,
        'active_tab': active_tab,
    }
    
    if active_tab == 'overview':
        context.update(_get_overview_tab_data(company))
    elif active_tab == 'estimation':
        context.update(_get_estimation_tab_data(company))
    # ... other tabs
    
    return render(request, 'finance/budgets/unified_budget_dashboard.html', context)
```

**Critical Fix (Oct 1):**
```python
# Dashboard aggregation - MUST use F() expressions
total = Transaction.objects.filter(
    company=company,
    is_categorized=True
).aggregate(
    total=Sum(
        F('unit_price') * F('quantity') * Coalesce(F('cases'), 1),
        output_field=DecimalField()
    )
)['total'] or 0
```

---

### 2. budget_approval_dashboard
**File:** `coda/finance/views/budget/approvals.py` (lines 15-84)  
**URL:** `/finance/budget/{company_slug}/approvals/`

**Purpose:** Dedicated approval management interface

**Query Optimization:**
```python
pending_requests = BudgetRequest.objects.filter(
    status='pending',
    department__company=company
).select_related(           # Prevent N+1
    'requester',
    'budget_category',
    'department'
).order_by('-created_at')
```

**Statistics Calculated:**
- Total pending count
- Approved this month
- Rejected this month
- Average approval time

---

### 3. approve_budget_request
**File:** `coda/finance/views/budget/approvals.py` (lines 86-125)  
**URL:** `POST /finance/budget/{company}/approve/{request_id}/`

**Permission Check:**
```python
def _can_approve_request(user, budget_request):
    """Phase 1 simple logic"""
    return user.is_staff or user.is_superuser
```

**Phase 2 Enhancement (Planned):**
```python
def _can_approve_request_v2(user, budget_request):
    """Tier-based permission check"""
    category = budget_request.budget_category
    
    if category.approval_tier == 'A':
        return user.has_role('finance_manager')
    elif category.approval_tier == 'B':
        if budget_request.priority in ['high', 'urgent']:
            return user.is_staff  # Auto-approve path
        return user.has_role('department_manager')
    else:  # Tier C
        return user.has_role('senior_manager') or user.has_role('executive')
```

---

### 4. tier_management_dashboard (Phase 2)
**File:** `coda/finance/views/budget/views_tier_management.py`  
**URL:** `/finance/tier-management/{company_slug}/`  
**Permission:** Finance Manager only

**Features:**
- View all categories grouped by tier
- Toggle auto-approval per category
- Adjust variance thresholds
- Trigger tier reclassification
- View tier statistics

**Key Code:**
```python
@login_required
@user_passes_test(is_finance_manager)
def tier_management_dashboard(request, company_slug):
    """Finance Manager tier control interface"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Group categories by tier
    categories_by_tier = {
        'A': BudgetCategory.objects.filter(approval_tier='A'),
        'B': BudgetCategory.objects.filter(approval_tier='B'),
        'C': BudgetCategory.objects.filter(approval_tier='C'),
    }
    
    # Tier statistics
    tier_stats = {
        'tier_a_count': categories_by_tier['A'].count(),
        'tier_b_count': categories_by_tier['B'].count(),
        'tier_c_count': categories_by_tier['C'].count(),
        'auto_enabled_count': BudgetCategory.objects.filter(auto_approve_enabled=True).count(),
    }
    
    context = {
        'company': company,
        'categories_by_tier': categories_by_tier,
        'tier_stats': tier_stats,
    }
    
    return render(request, 'finance/budgets/tier_management_dashboard.html', context)
```

---

## 🔧 MANAGEMENT COMMANDS

### generate_budget_projections
**File:** `coda/finance/management/commands/generate_budget_projections.py`  
**Purpose:** Generate AI budget projections from transaction data

**Usage:**
```bash
# Generate 12-month projections and save
python manage.py generate_budget_projections --company coda --months 12 --save

# Generate but don't save (dry run)
python manage.py generate_budget_projections --company coda --months 12

# Use specific method
python manage.py generate_budget_projections --method historical_avg
```

**Algorithm:**
1. Get all transactions for company
2. Group by category
3. Calculate monthly average for each category
4. Apply 10% growth factor
5. Project forward N months
6. Save as BudgetEstimateProjection

**Output Example:**
```
Budget Projections for CODA (12 months):
===============================================
Category: Salaries and Wages
  Monthly Avg: $33,219
  Annual Total: $398,631
  Transactions: 94

Category: IT and Software
  Monthly Avg: $4,754
  Annual Total: $57,053
  Transactions: 16

Total Annual Projection: $766,387
```

---

### classify_budget_category_tiers
**File:** `coda/finance/management/commands/classify_budget_category_tiers.py`  
**Purpose:** Analyze $1.49M dataset and classify categories into tiers

**Usage:**
```bash
# Analyze and print recommendations
python manage.py classify_budget_category_tiers --analyze

# Analyze and save to database
python manage.py classify_budget_category_tiers --analyze --save

# Export to CSV
python manage.py classify_budget_category_tiers --export tiers.csv
```

**Classification Logic:**
1. Calculate transaction frequency (transactions/month)
2. Calculate amount variance (std dev / mean)
3. Calculate business criticality score
4. Classify:
   - **Tier A:** High frequency + Low variance + Essential = Auto-approve
   - **Tier B:** Medium frequency + Operational = Priority-based
   - **Tier C:** Low frequency or High variance = Assessment required

**Results (Oct 16, 2025):**
- Tier A: 1 category (Rent - 24 transactions, 0% variance)
- Tier B: 5 categories (Salaries, IT, Utilities, Travel, Office)
- Tier C: 19 categories (Strategic or dormant)

---

### analyze_transaction_data
**File:** `coda/finance/management/commands/analyze_transaction_data.py`  
**Purpose:** Generate spending analysis report

**Usage:**
```bash
python manage.py analyze_transaction_data
python manage.py analyze_transaction_data --category "IT and Software"
python manage.py analyze_transaction_data --export analysis.csv
```

**Output:**
- Category totals and percentages
- Department breakdown
- Top 10 transactions
- Monthly trends
- Categorization quality (97.1%)

---

## 🌐 URL PATTERNS

```python
# coda/finance/urls.py

urlpatterns = [
    # Main Dashboard
    path('budget-dashboard/<str:company_slug>/', 
         unified_budget_dashboard, 
         name='budget_dashboard'),
    
    # Approval Dashboard
    path('budget/<str:company_slug>/approvals/', 
         budget_approval_dashboard, 
         name='budget_approvals'),
    
    # Approval Actions
    path('budget/<str:company_slug>/approve/<int:request_id>/', 
         approve_budget_request, 
         name='approve_budget'),
    
    path('budget/<str:company_slug>/reject/<int:request_id>/', 
         reject_budget_request, 
         name='reject_budget'),
    
    # Tier Management (Phase 2)
    path('tier-management/<str:company_slug>/', 
         tier_management_dashboard, 
         name='tier_management'),
    
    path('tier/auto-approval-log/<str:company_slug>/', 
         auto_approval_log, 
         name='auto_approval_log'),
    
    # API Endpoints
    path('api/budget-categories/', 
         budget_categories_api, 
         name='api_budget_categories'),
    
    path('api/tier/toggle-auto-approval/<int:category_id>/', 
         toggle_auto_approval_api, 
         name='api_toggle_auto_approval'),
]
```

---

## 🔌 API ENDPOINTS

### GET /finance/api/budget-categories/
**View:** `coda/finance/views_api_cascading.py::budget_categories_api`  
**Purpose:** Return categories for AJAX dropdown

**Request:**
```
GET /finance/api/budget-categories/?department=coda
```

**Response:**
```json
{
  "categories": [
    {
      "id": 1,
      "name": "Salaries and Wages",
      "tier": "B",
      "auto_approve_enabled": false
    },
    {
      "id": 2,
      "name": "Rent",
      "tier": "A",
      "auto_approve_enabled": true
    }
  ]
}
```

---

### POST /finance/api/tier/toggle-auto-approval/{category_id}/
**View:** `coda/finance/views/budget/views_tier_management.py`  
**Purpose:** Toggle auto-approval for a category (Finance Manager only)

**Request:**
```json
POST /finance/api/tier/toggle-auto-approval/5/
{
  "enabled": true
}
```

**Response:**
```json
{
  "success": true,
  "category_id": 5,
  "auto_approve_enabled": true,
  "message": "Auto-approval enabled for Rent"
}
```

---

## 💼 SERVICES

### SmartApprovalService (Phase 2)
**File:** `coda/finance/services/smart_approval_service.py`

**Key Methods:**

```python
class SmartApprovalService:
    
    @staticmethod
    def should_auto_approve(budget_request):
        """
        Determine if request should be auto-approved
        
        Returns: (bool, str) - (should_approve, reason)
        """
        category = budget_request.budget_category
        amount = budget_request.amount
        
        # Only Tier A eligible for auto-approval
        if category.approval_tier != 'A':
            return False, f"Tier {category.approval_tier} requires manual approval"
        
        # Check if auto-approval enabled
        if not category.auto_approve_enabled:
            return False, "Auto-approval paused by Finance Manager"
        
        # Check variance
        if not category.should_auto_approve(amount):
            variance = abs(amount - category.typical_monthly_amount) / category.typical_monthly_amount * 100
            return False, f"Amount {variance:.1f}% above typical ${category.typical_monthly_amount}"
        
        return True, "Known recurring expense within normal range"
    
    @staticmethod
    def get_recommended_approver(budget_request):
        """
        Get recommended approver based on tier and priority
        
        Returns: str - Role name ('department_manager', 'finance_manager', etc.)
        """
        category = budget_request.budget_category
        priority = budget_request.priority
        
        if category.approval_tier == 'A':
            return 'finance_manager'  # Oversight
        elif category.approval_tier == 'B':
            if priority in ['high', 'urgent']:
                return 'auto_approve'
            elif priority == 'medium':
                return 'department_manager'
            else:
                return 'finance_manager'
        else:  # Tier C
            if priority in ['high', 'urgent']:
                return 'senior_manager'
            else:
                return 'executive'
```

---

## 🎨 TEMPLATES

### budget_approvals.html
**Location:** `coda/finance/templates/finance/budgets/budget_approvals.html`

**Key Components:**
1. **Statistics Bar:** Pending, approved, rejected counts
2. **Pending Requests Table:** All pending with action buttons
3. **Recent Activity:** Approved and rejected lists
4. **Theme Switcher:** Navy/Gold or Purple

**Approve Button:**
```html
<form method="post" action="{% url 'finance:approve_budget' company.slug request.id %}">
    {% csrf_token %}
    <button type="submit" class="btn btn-sm btn-success">
        <i class="fas fa-check"></i> Approve
    </button>
</form>
```

---

### tier_management_dashboard.html (Phase 2)
**Location:** `coda/finance/templates/finance/budgets/tier_management_dashboard.html`

**Key Features:**
- Category cards grouped by tier
- Toggle switches for auto-approval
- Variance threshold sliders
- Statistics dashboard
- Re-run analysis button

**Auto-Approval Toggle:**
```html
<input type="checkbox" 
       class="auto-approve-toggle" 
       data-category-id="{{ category.id }}"
       {% if category.auto_approve_enabled %}checked{% endif %}>
```

**JavaScript:**
```javascript
$('.auto-approve-toggle').on('change', function() {
    const categoryId = $(this).data('category-id');
    const enabled = $(this).is(':checked');
    
    $.ajax({
        url: `/finance/api/tier/toggle-auto-approval/${categoryId}/`,
        method: 'POST',
        data: { enabled: enabled },
        success: function(response) {
            showSuccessMessage(response.message);
        }
    });
});
```

---

## ⚙️ CONFIGURATION

### Settings
**File:** `coda/coda_project/coda_settings/heroku_settings.py`

```python
# Budget Configuration
BUDGET_AUTO_APPROVE_THRESHOLD = 1000  # Auto below this for Tier A
BUDGET_TIER_A_MAX = 5000              # Max for Tier A auto-approval
BUDGET_TIER_B_MAX = 10000             # Max for Tier B without exec
BUDGET_VARIANCE_THRESHOLD = 20        # Default variance % for anomaly
BUDGET_PATTERN_ANALYSIS_SCHEDULE = '0 2 * * *'  # Daily at 2 AM

# Email Settings
BUDGET_APPROVAL_EMAIL = 'finance@codanalytics.net'
BUDGET_NOTIFICATION_ENABLED = True
```

---

## 🐛 CRITICAL BUG FIXES

### Bug #1: Dashboard Aggregation (Oct 1, 2025) 🔴 CRITICAL

**Problem:** Budget totals inflated by 177x ($837K displayed as $148M)

**Root Cause:**
```python
# WRONG (before fix)
total = Sum('quantity') * Sum('unit_price')
# (2+3+4) * (100+200+150) = 9 * 450 = 4,050 ❌
# Multiplies sum of ALL quantities by sum of ALL prices
```

**Correct Fix:**
```python
# CORRECT (after fix)
total = Sum(F('unit_price') * F('quantity') * Coalesce(F('cases'), 1), 
            output_field=DecimalField())
# (2*100) + (3*200) + (4*150) = 200 + 600 + 600 = 1,400 ✅
# Multiplies EACH item's quantity by ITS price, then sums
```

**Files Changed:**
- `views_unified_budget.py` (line 164-174)

**Regression Test Added:**
- `tests/test_regressions.py::test_dashboard_aggregation_correct()`

**Status:** ✅ Fixed and deployed

---

### Bug #2: Approval Fields Missing (Oct 13, 2025) 🔴 CRITICAL

**Problem:** `AttributeError: 'BudgetRequest' object has no attribute 'approved_by'`

**Root Cause:** Template used fields that didn't exist in model

**Fix:** Added migration 0099 with approval fields:
- `approved_by`, `approved_at`
- `rejected_by`, `rejected_at`, `rejection_reason`
- `current_approver`, `approval_chain`

**Status:** ✅ Fixed with migration

---

## 🔐 SECURITY IMPLEMENTATION

### CSRF Protection
All POST forms include:
```html
{% csrf_token %}
```

### Permission Decorators
```python
from django.contrib.auth.decorators import login_required, user_passes_test

@login_required
@user_passes_test(is_finance_manager)
def tier_management_dashboard(request, company_slug):
    # Finance Manager only
```

### Data Access Control
```python
# Users only see their company's data
budget_requests = BudgetRequest.objects.filter(
    department__company=request.user.company
)
```

---

## 📊 CHANGE HISTORY

| Date | Change | File(s) | Developer | Ticket |
|------|--------|---------|-----------|--------|
| Oct 22, 2025 | Migrated to 7-doc structure | All budget docs | AI | #DOC-001 |
| Oct 16, 2025 | Phase 2 COMPLETE - Tier system deployed | Multiple | CM | #PHASE2 |
| Oct 16, 2025 | Added tier fields to BudgetCategory | models/budget.py | CM | #156 |
| Oct 16, 2025 | Created tier classification command | commands/ | CM | #157 |
| Oct 16, 2025 | Finance Manager tier control UI | views/, templates/ | CM | #158 |
| Oct 16, 2025 | SmartApprovalService integration | services/ | CM | #159 |
| Oct 13, 2025 | Added approval audit fields | models/budget.py | CM | #145 |
| Oct 2, 2025 | Fixed dashboard aggregation bug | views_unified_budget.py | CM | #123 |
| Oct 1, 2025 | Created BudgetRequest model | models/budget.py | CM | #100 |

---

## 📚 RELATED DOCUMENTATION

**See Also:**
- `01_ANALYSIS.md` - Problem statement and business case
- `02_REQUIREMENTS.md` - Functional requirements and acceptance criteria
- `03_ARCHITECTURE.md` - System design and data models
- `05_TESTING.md` - Test scenarios and validation
- `06_MAINTENANCE.md` - Known issues and troubleshooting
- `07_DEPLOYMENT.md` - Deployment procedures and configuration

---

**Document Owner:** Development Team  
**Last Major Update:** October 22, 2025  
**Next Review:** After Phase 3 implementation


