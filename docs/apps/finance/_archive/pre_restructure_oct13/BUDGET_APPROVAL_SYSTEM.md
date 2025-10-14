# Budget Approval System - Complete Documentation
**Last Updated:** October 13, 2025  
**Status:** Phase 1 Complete, Phase 2 Planned  
**Location:** `/finance/budget/approvals/`

---

## 📋 TABLE OF CONTENTS

1. [Current Status](#current-status)
2. [Business Requirements](#business-requirements)
3. [Technical Implementation](#technical-implementation)
4. [Phase 2 Plan](#phase-2-data-driven-system)
5. [Testing Guide](#testing)
6. [Known Issues](#known-issues)

---

## 🎯 CURRENT STATUS (Phase 1)

### What Works NOW:
- ✅ Budget request creation
- ✅ Approval dashboard (`/finance/budget/{company}/approvals/`)
- ✅ Approve/reject buttons functional
- ✅ Simple permission logic: **Staff can approve**
- ✅ Audit trail (approved_by, approved_at, rejected_by, rejected_at)
- ✅ Email notifications

### Temporary Logic:
```python
def can_approve(user, budget_request):
    return user.is_staff or user.is_superuser
```

**Why Simple?** Because we're building Phase 2 based on actual transaction data analysis, not guesses!

---

## 💼 BUSINESS REQUIREMENTS

### Three-Tier Approval System (Target State):

#### **TIER A: Known/Recurring** (Auto-Approve)
- **Categories:** Utilities, Salaries, Rent, Insurance, Taxes, IT Subscriptions
- **Logic:** Auto-approve if within normal variance
- **Oversight:** Finance Manager daily digest
- **Business Value:** Speed, efficiency, no bottlenecks

#### **TIER B: Variable/Operational** (Priority-Based)
- **Categories:** Supplies, Travel, Maintenance, Training
- **Logic:**
  - HIGH priority → Auto-approve
  - MEDIUM priority → Department Manager approval
  - LOW priority → Requires justification
- **Business Value:** Handles urgency while maintaining control

#### **TIER C: Strategic** (Smart Assessment)
- **Categories:** R&D, Marketing, New Projects
- **Logic:** Critical assessment questions → Scoring → Route to appropriate level
- **Business Value:** Data-driven strategic decisions

### Category Classification:
See `BUDGET_CATEGORY_CLASSIFICATION.md` for complete breakdown of all 25 categories

---

## 🔧 TECHNICAL IMPLEMENTATION

### Models

#### BudgetRequest
```python
class BudgetRequest(TimeStampedModel, StatusMixin):
    requester = ForeignKey(User)
    amount = DecimalField()
    purpose = TextField()
    department = ForeignKey(Department)
    budget_category = ForeignKey(BudgetCategory)
    priority = CharField(choices=['low', 'medium', 'high', 'urgent'])
    status = CharField(choices=['draft', 'submitted', 'approved', 'rejected'...])
    
    # Approval tracking (added Oct 13)
    approved_by = ForeignKey(User, null=True)
    approved_at = DateTimeField(null=True)
    rejected_by = ForeignKey(User, null=True)
    rejected_at = DateTimeField(null=True)
    current_approver = ForeignKey(User, null=True)
    approval_chain = JSONField(default=list)
```

#### ApprovalPolicy
```python
class ApprovalPolicy(TimeStampedModel):
    name = CharField()
    min_amount = DecimalField()
    max_amount = DecimalField(null=True)
    approver_roles = JSONField()  # List of role names
    approval_chain = JSONField()  # Sequential chain config
    auto_approve = BooleanField()
    applicable_departments = ManyToManyField(Department)
    applicable_categories = ManyToManyField(BudgetCategory)
```

### Views

#### Approval Dashboard
**URL:** `/finance/budget/{company_slug}/approvals/`  
**View:** `coda/finance/views/budget/approvals.py::budget_approval_dashboard`

**Features:**
- Lists pending requests
- Shows recent approvals/rejections
- Approval statistics
- Filter by status, department

#### Approve/Reject Actions
**URLs:**
- POST `/finance/budget/{company_slug}/approve/{request_id}/`
- POST `/finance/budget/{company_slug}/reject/{request_id}/`

**Views:**
- `approve_budget_request` - Sets approved_by, approved_at
- `reject_budget_request` - Sets rejected_by, rejected_at, rejection_reason

### Current Permission Logic
```python
# Temporary (Phase 1)
def _can_approve_budget(user, budget_request):
    return user.is_staff or user.is_superuser

# Future (Phase 2 - after data analysis)
def _can_approve_budget(user, budget_request):
    category = budget_request.budget_category
    
    if category.approval_tier == 'A' and category.auto_approve_enabled:
        return 'AUTO_APPROVE'
    elif category.approval_tier == 'B':
        return check_priority_based_approval(user, budget_request)
    elif category.approval_tier == 'C':
        return check_assessment_score(user, budget_request)
```

---

## 🚀 PHASE 2: DATA-DRIVEN SYSTEM

### Overview
Build intelligent approval routing based on analysis of $1.49M in production transaction data

### 7-Day Implementation Plan:

**Day 1-2:** Data Extraction & Analysis
- Export production transactions
- Analyze spending patterns
- Identify recurring vs strategic expenses

**Day 3-4:** Category Classification
- Classify 25 categories into Tiers A/B/C
- Set variance thresholds
- Define anomaly detection rules

**Day 5-6:** Implementation
- Add tier fields to BudgetCategory model
- Build IntelligentApprovalEngine service
- Create Finance Manager control dashboard

**Day 7:** Testing & Deployment
- Validate with historical data
- UAT testing
- Production deployment

### Key Outputs:
1. `category_spending_analysis.csv` - Data-backed tier assignments
2. `IntelligentApprovalEngine` service - Smart routing logic
3. Finance Manager dashboard - Override controls
4. Assessment form - For Tier C strategic requests

**See:** `PHASE2_DATA_DRIVEN_APPROVAL_PLAN.md` (in docs/planning/)

---

## 🧪 TESTING

### Test Scenarios (Phase 1):

**Scenario 1: Submit Budget Request**
1. Login as regular user
2. Visit `/finance/budget/coda/request/new/`
3. Fill form, submit
4. Verify status = 'submitted'

**Scenario 2: Approve Request**
1. Login as staff user
2. Visit `/finance/budget/coda/approvals/`
3. Click approve on pending request
4. Verify:
   - Status changes to 'approved'
   - approved_by = current user
   - approved_at = timestamp

**Scenario 3: Reject Request**
1. Login as staff user
2. Click reject, enter reason
3. Verify:
   - Status = 'rejected'
   - rejected_by = current user
   - rejection_reason saved

---

## ⚠️ KNOWN ISSUES

### Resolved (Oct 13):
- ✅ BudgetRequest.company field errors
- ✅ ApprovalPolicy.approvers attribute error
- ✅ LoanService import errors
- ✅ Schema mismatches

### Remaining (Low Priority):
- Transaction model field name inconsistencies
- Some template namespace issues
- BudgetEditForm missing

**See:** `KNOWN_ISSUES.md` (in docs/deployment/)

---

## 📚 RELATED DOCUMENTATION

**In this directory:**
- `BUDGET_APPROVAL_SYSTEM.md` (this file) - Complete reference
- `BUDGET_WORKFLOW_IMPLEMENTATION_COMPLETE.md` - Initial implementation
- `TRANSACTION_MODEL_MIGRATION_PLAN.md` - Data model evolution

**In docs/planning:**
- `PHASE2_DATA_DRIVEN_APPROVAL_PLAN.md` - Future implementation
- `APPROVAL_WORKFLOW_BUSINESS_ANALYSIS.md` - Business decision framework
- `BUDGET_CATEGORY_CLASSIFICATION.md` - Category tier assignments

**In docs/deployment:**
- `OCT13_DEPLOYMENT_SUMMARY.md` - Session summary
- `KNOWN_ISSUES.md` - Current issues tracker

**In docs/features:**
- `THEME_SWITCHER.md` - Dashboard theme feature

---

## 🔄 UPDATE PROTOCOL

**When making changes to approval system:**

1. **Update this document** - Technical changes section
2. **Update KNOWN_ISSUES.md** - If fixing bugs
3. **Update deployment docs** - If deploying changes
4. **DON'T create new docs** - Consolidate into existing

**One source of truth!**

---

## 🎯 QUICK REFERENCE

### URLs:
- Approval Dashboard: `/finance/budget/{company}/approvals/`
- Request List: `/finance/budget-requests/`
- Create Request: `/finance/budget/request/new/`

### Key Files:
- Models: `coda/finance/models/budget.py` (BudgetRequest, ApprovalPolicy)
- Views: `coda/finance/views/budget/approvals.py`
- Templates: `coda/finance/templates/finance/budgets/approval_dashboard.html`
- Services: `coda/finance/services/automation_service.py` (future)

### Permissions:
- **Current:** is_staff or is_superuser
- **Future:** Tier-based + role-based

---

**Maintained by:** Cursor AI Assistant  
**Next Review:** After Phase 2 implementation  
**Questions?** Check docs/planning/ for detailed plans

