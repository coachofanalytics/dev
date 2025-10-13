# Documentation Structure - REFINED PROPOSAL
**Date:** October 13, 2025  
**Based on:** User feedback for simpler, maintainable structure

---

## 🎯 CORE PRINCIPLE

**4 Docs Per Feature. That's It.**

Every feature gets exactly 4 documents:
1. **Overview** (What & Why)
2. **Requirements** (What it should do)
3. **Implementation** (How it works)
4. **Testing** (How to verify)

**Any new requirement, change, or feature update goes into one of these 4 docs.**

---

## 📋 THE 4-DOC STANDARD

### **1. README.md** (Overview & Discovery)
**Purpose:** First stop for anyone learning about this feature  
**AKA:** Discovery doc, feature overview, "start here"

**Contents:**
```markdown
# [Feature Name] System

## What It Does
[2-3 paragraphs explaining the feature's purpose and value]

## Why It Exists
[Business context, problem it solves]

## Current Status
✅ Working: [list]
🔄 In Progress: [list]
⚠️ Known Issues: [list]
📋 Planned: [list]

## Quick Start
1. [How to use - 3-4 steps]
2. [Common use cases]

## Key Concepts
- **Concept 1:** Explanation
- **Concept 2:** Explanation

## Documentation
- [REQUIREMENTS.md](REQUIREMENTS.md) - What it should do
- [IMPLEMENTATION.md](IMPLEMENTATION.md) - How it works
- [TESTING.md](TESTING.md) - How to test

## Code Location
- Models: `path/to/models.py`
- Views: `path/to/views/`
- Services: `path/to/services/`

## History
- **Oct 2025:** Phase 1 complete
- **Sept 2025:** Initial development
```

**Update Frequency:** Monthly or after major changes

---

### **2. REQUIREMENTS.md** (What It Should Do)
**Purpose:** Single source of truth for ALL requirements - past, present, future  
**AKA:** Business requirements, functional spec

**Contents:**
```markdown
# [Feature Name] - Requirements

## Business Goals
[Why this feature exists from business perspective]

## User Stories
### As a [role], I want to [action] so that [benefit]
- Acceptance criteria
- Priority: High/Medium/Low

## Functional Requirements

### Phase 1 (Completed)
✅ REQ-001: [Requirement description]
  - Implemented: [Date]
  - Location: [Code reference]

✅ REQ-002: [Another requirement]
  - Implemented: [Date]
  - Location: [Code reference]

### Phase 2 (Current)
🔄 REQ-010: [Current requirement]
  - Status: In progress
  - Target: [Date]
  - Notes: [Implementation notes]

⚠️ REQ-011: [Blocked requirement]
  - Status: Blocked by [reason]
  - Dependency: [What's needed]

### Phase 3 (Planned)
📋 REQ-020: [Future requirement]
  - Priority: High
  - Effort: Medium
  - Dependencies: [List]

## Non-Functional Requirements
- Performance: [Response time targets]
- Security: [Access controls, data protection]
- Scalability: [Expected load]

## Business Rules
1. **Rule 1:** [Description]
   - Example: Budgets > $10K require approval
   - Rationale: Risk management

2. **Rule 2:** [Description]
   - Example: Staff can approve up to $5K
   - Rationale: Operational efficiency

## Data Requirements
- What data is needed
- Data quality standards
- Data retention policies

## Integration Requirements
- What other systems/features this depends on
- What other systems depend on this

## Constraints
- Technical limitations
- Business constraints
- Regulatory requirements

## Change History
| Date | Change | By | Reason |
|------|--------|-----|--------|
| Oct 2025 | Added tier-based approval | CM | Data analysis showed patterns |
| Sept 2025 | Initial requirements | CM | Project kickoff |
```

**Update Frequency:** Every time a requirement is added, changed, or completed

---

### **3. IMPLEMENTATION.md** (How It Works)
**Purpose:** Complete technical reference for developers  
**AKA:** Technical documentation, architecture doc

**Contents:**
```markdown
# [Feature Name] - Implementation

## Architecture Overview
[High-level diagram or description of how components interact]

## Data Model

### Models
**BudgetRequest** (`finance/models/budget.py`)
- Fields: [List key fields]
- Relationships: [Foreign keys, M2M]
- Methods: [Key methods]
- Signals: [Any signals]

**ApprovalPolicy** (`finance/models/budget.py`)
- Purpose: [Why this exists]
- Configuration: [How it's configured]

### Database Schema
```sql
-- Key tables and relationships
CREATE TABLE finance_budgetrequest (
  id, title, amount, status, ...
)
```

## Service Layer

### BudgetApprovalService
**Location:** `finance/services/budget/approval_service.py`

**Key Methods:**
- `approve_request(request_id, user)`: [What it does]
- `can_approve(user, request)`: [Permission logic]
- `get_approval_policy(request)`: [Policy lookup]

**Business Logic:**
- [Explain approval tiers]
- [Explain escalation rules]
- [Explain auto-approval conditions]

## Views & URLs

### Budget Approval View
**URL:** `/finance/budget/{company}/approvals/`  
**View:** `finance/views/budget/approvals.py`  
**Template:** `finance/budgets/budget_approvals.html`

**Flow:**
1. User requests page
2. View fetches pending requests
3. Checks user permissions
4. Renders with context

### API Endpoints
**POST** `/finance/api/budget/approve/`
- Request: `{"request_id": 123, "notes": "..."}`
- Response: `{"status": "approved", "approved_by": "..."}`
- Permissions: Staff only (Phase 1)

## Templates

### budget_approvals.html
**Purpose:** Display pending approval requests  
**Key Features:**
- Filter by status
- Approve/reject actions
- Approval history

**Dynamic Elements:**
- Theme switcher
- Real-time status updates (future)

## Frontend Logic

### JavaScript
**File:** Inline in template (future: separate file)

**Key Functions:**
- `approveRequest(id)`: AJAX call to approve
- `rejectRequest(id)`: AJAX call to reject
- `switchTheme(theme)`: Toggle theme

## Workflows

### Approval Workflow (Phase 1)
```
Budget Request Created
    ↓
Staff/Superuser Reviews
    ↓
  Approve ──→ Status: Approved
    or           ↓
  Reject ──→ Status: Rejected
```

### Approval Workflow (Phase 2 - Planned)
```
Budget Request Created
    ↓
Determine Tier (A/B/C)
    ↓
Tier A → Auto-approve
Tier B → Manager approval
Tier C → Director approval
    ↓
Approval/Rejection
```

## Algorithms & Logic

### Tier Classification (Phase 2)
```python
def classify_budget_tier(budget_request):
    """
    Classify budget into approval tier based on:
    - Amount
    - Category
    - Historical patterns
    - Risk factors
    """
    # Algorithm details
```

## Data Flow

### Budget Creation Flow
1. User fills form (`budget_create.html`)
2. POST to `create_budget_request` view
3. View validates data
4. Service creates BudgetRequest
5. Service determines approval policy
6. Email notification sent
7. Redirect to detail view

## Security & Permissions

### Permission Checks
- `@login_required`: All budget views
- `user.is_staff`: Approval actions (Phase 1)
- Future: Role-based (Tier A/B/C approvers)

### Data Access Control
- Users see only their company's budgets
- Filter: `.filter(company=request.user.company)`

## Performance Considerations

### Database Queries
- Use `select_related('user', 'company')`
- Use `prefetch_related('line_items')`
- Index on: `status`, `company_id`, `created_at`

### Caching
- Cache approval policies (1 hour)
- Cache category hierarchies (24 hours)

## External Dependencies

### Third-Party
- None currently
- Future: Email service (SendGrid/AWS SES)

### Internal
- Depends on: Transaction system (for data analysis)
- Used by: Dashboard (for stats)

## Configuration

### Settings
```python
# heroku_settings.py
BUDGET_AUTO_APPROVE_THRESHOLD = 1000  # Phase 2
BUDGET_TIER_A_MAX = 5000
BUDGET_TIER_B_MAX = 10000
```

### Environment Variables
- `BUDGET_APPROVAL_EMAIL`: Notification recipient
- `ENABLE_AUTO_APPROVAL`: Feature flag (Phase 2)

## Code Examples

### Creating a Budget Request
```python
from finance.services import BudgetService

service = BudgetService()
request = service.create_request(
    user=request.user,
    title="Office Supplies",
    amount=500.00,
    category_id=5
)
```

### Checking Approval Permissions
```python
from finance.services import BudgetApprovalService

service = BudgetApprovalService()
can_approve = service.can_approve(user, budget_request)
```

## Migration History

### 0099_add_approval_fields_to_budget_request.py
**Date:** Oct 13, 2025  
**Purpose:** Add `approved_by`, `approved_at`, `rejected_by`, `rejected_at`  
**Impact:** Required for approval workflow Phase 1

## Known Technical Debt
- [ ] Approval logic currently in view - should move to service
- [ ] Template has inline JS - should extract
- [ ] Need to add approval notifications
- [ ] Policy lookup not cached

## Future Improvements
- [ ] Real-time approval updates (WebSockets)
- [ ] Mobile-optimized approval interface
- [ ] Batch approval actions
- [ ] Approval delegation

## Change History
| Date | Change | Developer | Reason |
|------|--------|-----------|--------|
| Oct 13, 2025 | Added approval fields | CM | Support Phase 1 workflow |
| Oct 2, 2025 | Created BudgetRequest model | CM | Separate from Budget |
```

**Update Frequency:** Every time you change code structure, add features, or fix bugs

---

### **4. TESTING.md** (How to Verify)
**Purpose:** Complete guide to testing this feature  
**AKA:** Test plan, QA guide, verification doc

**Contents:**
```markdown
# [Feature Name] - Testing Guide

## Test Environments

### Local Development
- URL: `http://localhost:8000`
- Database: SQLite/PostgreSQL
- User: Create via `python manage.py createsuperuser`

### UAT (Staging)
- URL: `https://codamakutano.herokuapp.com`
- Database: Heroku PostgreSQL
- Users: [List test accounts]

### Production
- URL: `https://codatrainingapp.herokuapp.com`
- Database: Heroku PostgreSQL
- Users: Real users only

## Test Data Setup

### Prerequisites
```bash
# Create test users
python manage.py shell
from accounts.models import CustomerUser
user = CustomerUser.objects.create_user(
    username='testmanager',
    email='test@coda.com',
    is_staff=True
)

# Create test company
from main.models import Company
company = Company.objects.create(name='Test CODA')

# Create test categories
from finance.models import BudgetCategory
cat = BudgetCategory.objects.create(name='Office Supplies')
```

### Sample Data
- Test budgets: [How to create]
- Test transactions: [How to import]
- Test approval policies: [How to configure]

## Functional Tests

### Test 1: Create Budget Request
**Objective:** Verify users can create budget requests

**Steps:**
1. Login as regular user
2. Navigate to `/finance/budget/{company}/create/`
3. Fill form:
   - Title: "Test Budget"
   - Amount: $500
   - Category: Office Supplies
4. Submit

**Expected Result:**
- ✅ Budget created successfully
- ✅ Status: Pending
- ✅ Redirected to detail page
- ✅ Approval required message shown

**Actual Result:** [Fill during testing]

---

### Test 2: Approve Budget Request (Staff)
**Objective:** Verify staff can approve budgets

**Steps:**
1. Login as staff user
2. Navigate to `/finance/budget/{company}/approvals/`
3. Find pending budget
4. Click "Approve" icon
5. Add optional notes
6. Confirm

**Expected Result:**
- ✅ Status changes to "Approved"
- ✅ `approved_by` set to current user
- ✅ `approved_at` timestamp recorded
- ✅ Success message shown

**Actual Result:** [Fill during testing]

---

### Test 3: Reject Budget Request
**Objective:** Verify staff can reject budgets

**Steps:**
1. Login as staff user
2. Navigate to approvals page
3. Click "Reject" icon
4. Add rejection reason
5. Confirm

**Expected Result:**
- ✅ Status changes to "Rejected"
- ✅ `rejected_by` set to current user
- ✅ `rejected_at` timestamp recorded
- ✅ Rejection reason saved

**Actual Result:** [Fill during testing]

---

### Test 4: Permission Check - Non-Staff Cannot Approve
**Objective:** Verify regular users cannot approve budgets

**Steps:**
1. Login as non-staff user
2. Try to access `/finance/budget/{company}/approvals/`
3. Try direct POST to approval endpoint

**Expected Result:**
- ✅ Cannot access approvals page (403 or redirect)
- ✅ Cannot approve via API (403 error)
- ✅ Approve/reject buttons not visible

**Actual Result:** [Fill during testing]

---

## Integration Tests

### Test 5: Budget + Transaction Integration
**Objective:** Verify budget creation uses transaction data

**Steps:**
1. Ensure transactions exist for "Office Supplies"
2. Create budget for "Office Supplies"
3. Check if AI prediction suggests amount

**Expected Result:**
- ✅ Prediction based on historical spending
- ✅ Suggested amount shown in form

---

### Test 6: Budget + Dashboard Integration
**Objective:** Verify approved budgets appear in dashboard

**Steps:**
1. Approve a budget request
2. Navigate to `/dashboard/`
3. Check budget statistics

**Expected Result:**
- ✅ Approved budget count updated
- ✅ Total approved amount accurate
- ✅ Budget appears in recent activity

---

## Edge Cases & Error Handling

### Test 7: Approve Already Approved Budget
**Steps:**
1. Approve a budget
2. Try to approve it again

**Expected Result:**
- ✅ Error message or no-op
- ✅ Original approval data preserved

---

### Test 8: Large Budget Amount
**Steps:**
1. Create budget with amount = $1,000,000

**Expected Result:**
- ✅ Accepts large amounts
- ✅ Displays correctly (no overflow)

---

### Test 9: Missing Required Fields
**Steps:**
1. Submit budget form with missing title

**Expected Result:**
- ✅ Form validation error
- ✅ User-friendly error message
- ✅ Form data preserved

---

## Performance Tests

### Test 10: Approval Page Load Time
**Objective:** Verify page loads quickly with many budgets

**Steps:**
1. Create 100 budget requests
2. Navigate to approvals page
3. Measure load time

**Expected Result:**
- ✅ Page loads in < 2 seconds
- ✅ All budgets displayed
- ✅ Pagination working (if implemented)

---

## Security Tests

### Test 11: Cross-Company Access
**Objective:** Verify users cannot access other companies' budgets

**Steps:**
1. Login as Company A user
2. Try to access Company B budget URL

**Expected Result:**
- ✅ 404 or 403 error
- ✅ No data leaked

---

### Test 12: SQL Injection
**Steps:**
1. Enter `'; DROP TABLE finance_budgetrequest; --` in title field
2. Submit

**Expected Result:**
- ✅ Input escaped properly
- ✅ No database damage
- ✅ Budget created with literal string

---

## Regression Tests

### Test 13: Dashboard Aggregation (Critical!)
**Objective:** Verify dashboard doesn't have 177x inflation bug

**Steps:**
1. Create budget: $100
2. Approve it
3. Check dashboard total

**Expected Result:**
- ✅ Total shows $100, not $17,700
- ✅ Uses correct aggregation formula

**Reference:** Fixed Oct 2, 2025 (see MASTER_REFERENCE.md)

---

## Browser Compatibility

### Test 14: Theme Switcher
**Browsers:** Chrome, Firefox, Safari, Edge

**Steps:**
1. Load dashboard
2. Click "Navy & Gold" theme
3. Click "Purple" theme
4. Reload page

**Expected Result:**
- ✅ Theme switches correctly
- ✅ Preference saved in localStorage
- ✅ Persists after reload

---

## Automated Tests

### Unit Tests
**File:** `finance/tests/test_budget_approval.py`

```python
def test_can_approve_as_staff():
    """Test staff can approve budgets"""
    user = create_staff_user()
    request = create_budget_request()
    service = BudgetApprovalService()
    assert service.can_approve(user, request) == True

def test_cannot_approve_as_regular_user():
    """Test regular users cannot approve"""
    user = create_regular_user()
    request = create_budget_request()
    service = BudgetApprovalService()
    assert service.can_approve(user, request) == False
```

**Run:** `python manage.py test finance.tests.test_budget_approval`

### Integration Tests
**File:** `finance/tests/test_budget_workflow.py`

```python
def test_full_approval_workflow():
    """Test complete budget approval flow"""
    # Create request
    # Approve request
    # Verify status
    # Verify dashboard updated
```

**Run:** `python manage.py test finance.tests.test_budget_workflow`

---

## Test Results Log

### Test Run: Oct 13, 2025 (UAT v904)
| Test # | Name | Status | Notes |
|--------|------|--------|-------|
| 1 | Create Budget | ✅ Pass | - |
| 2 | Approve Budget | ✅ Pass | - |
| 3 | Reject Budget | ✅ Pass | - |
| 4 | Permission Check | ✅ Pass | - |
| 13 | Dashboard Aggregation | ✅ Pass | No inflation bug |

**Overall:** 4/4 tests passed  
**Tester:** CM  
**Environment:** UAT  
**Version:** v904

---

### Test Run: Oct 2, 2025 (UAT v895)
| Test # | Name | Status | Notes |
|--------|------|--------|-------|
| 1 | Create Budget | ✅ Pass | - |
| 2 | Approve Budget | ❌ Fail | `approved_by` field missing |

**Overall:** 1/2 tests passed  
**Tester:** CM  
**Environment:** UAT  
**Version:** v895  
**Action:** Added missing fields, created migration 0099

---

## Known Issues
- [ ] No email notifications yet (planned Phase 2)
- [ ] Cannot bulk approve (planned Phase 3)
- [ ] Mobile UI needs polish

## Test Checklist (Before Deployment)

### Pre-Deployment
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] No linter errors
- [ ] Migrations run successfully
- [ ] Test data created

### UAT Testing
- [ ] Create budget request
- [ ] Approve budget request
- [ ] Reject budget request
- [ ] Check permissions
- [ ] Verify dashboard updates
- [ ] Test theme switcher
- [ ] Check all URLs work

### Production Deployment
- [ ] UAT tests all pass
- [ ] Migrations reviewed
- [ ] Backup database
- [ ] Deploy
- [ ] Run smoke tests
- [ ] Monitor logs for 1 hour

---

## Troubleshooting

### Issue: Cannot approve budget
**Check:**
- Is user staff? (`user.is_staff`)
- Does budget exist?
- Is budget already approved?
- Check browser console for JS errors

### Issue: 500 error on approval page
**Check:**
- Heroku logs: `heroku logs --tail --app codamakutano`
- Missing fields on BudgetRequest model?
- Database migration needed?

### Issue: Theme not saving
**Check:**
- Browser localStorage enabled?
- JavaScript errors in console?
- Correct theme attribute set?

---

## Change History
| Date | Change | By | Reason |
|------|--------|-----|--------|
| Oct 13, 2025 | Added Phase 1 tests | CM | Initial approval workflow |
| Oct 2, 2025 | Created test plan | CM | Project setup |
```

**Update Frequency:** Every time you add a feature (add test case), find a bug (add regression test), or complete a test run (log results)

---

## 📁 COMPLETE STRUCTURE

```
coda/docs/apps/finance/
│
├── Budget/
│   ├── README.md              (What & Why - 200 lines)
│   ├── REQUIREMENTS.md        (What it should do - 300 lines)
│   ├── IMPLEMENTATION.md      (How it works - 400 lines)
│   └── TESTING.md             (How to verify - 300 lines)
│
├── Loan/
│   ├── README.md
│   ├── REQUIREMENTS.md
│   ├── IMPLEMENTATION.md
│   └── TESTING.md
│
├── Payment/
│   ├── README.md
│   ├── REQUIREMENTS.md
│   ├── IMPLEMENTATION.md
│   └── TESTING.md
│
├── Transaction/
│   ├── README.md
│   ├── REQUIREMENTS.md
│   ├── IMPLEMENTATION.md
│   └── TESTING.md
│
└── Shared/
    ├── README.md              (Cross-feature documentation)
    ├── THEME_SWITCHER.md      (Can be in IMPLEMENTATION.md of relevant feature)
    └── API_REFERENCE.md       (All finance APIs)
```

**Total:** 4 features × 4 docs = **16 core docs** (+ 3 shared = 19 total)

Down from 30-50+ scattered docs! 🎯

---

## 🎯 MAPPING YOUR PROPOSAL TO STANDARD NAMES

| Your Idea | Standard Name | Purpose |
|-----------|--------------|---------|
| Comprehensive Analysis / Discovery | **README.md** | What & Why (overview) |
| Requirements (historical + current) | **REQUIREMENTS.md** | What it should do (all phases) |
| Implementation | **IMPLEMENTATION.md** | How it works (technical) |
| Test Doc | **TESTING.md** | How to verify |

---

## 📊 WHERE DOES EVERYTHING GO?

### New Feature Request?
→ **REQUIREMENTS.md** (add to Phase X section)

### Feature Implementation Details?
→ **IMPLEMENTATION.md** (update workflows, add code examples)

### Bug Fix?
→ **IMPLEMENTATION.md** (update Change History)  
→ **TESTING.md** (add regression test)

### Architecture Change?
→ **README.md** (update overview if major)  
→ **IMPLEMENTATION.md** (update architecture section)

### Historical Context?
→ **README.md** (History section)  
→ **REQUIREMENTS.md** (Phase 1 completed requirements)

### Business Rule Change?
→ **REQUIREMENTS.md** (update Business Rules section)

### Code Example?
→ **IMPLEMENTATION.md** (Code Examples section)

### Test Results?
→ **TESTING.md** (Test Results Log section)

---

## ✅ BENEFITS OF THIS STRUCTURE

### For Development:
- ✅ **Always know where to look** (4 places, clear purposes)
- ✅ **No duplication** (each doc has distinct role)
- ✅ **Easy to maintain** (update existing, don't create new)
- ✅ **Scales well** (structure works for simple or complex features)

### For Planning:
- ✅ **See all requirements in one place** (historical + current + future)
- ✅ **Track progress** (move requirements between phases)
- ✅ **Understand dependencies** (REQUIREMENTS.md integration section)

### For Testing:
- ✅ **Complete test guide** (all scenarios documented)
- ✅ **Test results tracked** (know what's been verified)
- ✅ **Regression prevention** (known bugs have tests)

### For Onboarding:
- ✅ **Start with README** (understand feature in 10 minutes)
- ✅ **Deep dive as needed** (REQUIREMENTS → IMPLEMENTATION → TESTING)
- ✅ **Self-service** (docs answer most questions)

---

## 🚀 IMPLEMENTATION PLAN

### Step 1: Create Structure (5 min)
```bash
cd coda/docs/apps/finance
mkdir -p {Budget,Loan,Payment,Transaction,Shared}
```

### Step 2: Create Template Files (10 min)
For each feature:
- Copy template for README.md
- Copy template for REQUIREMENTS.md
- Copy template for IMPLEMENTATION.md
- Copy template for TESTING.md

### Step 3: Consolidate Existing Docs (30 min)

**Budget Feature:**
```
Source                                          → Destination
--------------------------------------------------------------------
BUDGET_APPROVAL_SYSTEM.md                       → Budget/IMPLEMENTATION.md (main content)
CODA_APPROVAL_BUSINESS_REQUIREMENTS.md          → Budget/REQUIREMENTS.md (business rules)
APPROVAL_WORKFLOW_BUSINESS_ANALYSIS.md          → Budget/REQUIREMENTS.md (analysis section)
BUDGET_CATEGORY_CLASSIFICATION.md               → Budget/REQUIREMENTS.md (categorization)
PHASE2_DATA_DRIVEN_APPROVAL_PLAN.md             → Budget/REQUIREMENTS.md (Phase 2 section)
BUDGET_WORKFLOW_IMPLEMENTATION_COMPLETE.md      → Budget/README.md (history + overview)
```

**Transaction Feature:**
```
TRANSACTION_MODEL_MIGRATION_PLAN.md             → Transaction/IMPLEMENTATION.md
[Smart entry docs]                              → Transaction/IMPLEMENTATION.md
```

### Step 4: Create READMEs (15 min)
- Write Budget/README.md (from scratch using template)
- Write Loan/README.md
- Write Payment/README.md
- Write Transaction/README.md

### Step 5: Archive Old Docs (5 min)
```bash
mkdir -p coda/docs/apps/finance/_archive/pre_restructure_oct13
mv [old docs] _archive/pre_restructure_oct13/
```

### Step 6: Update Indexes (5 min)
- Update `/DOCUMENTATION_INDEX.md`
- Update `coda/docs/apps/finance/README.md` (master index)

**Total Time:** ~70 minutes

---

## 📝 DOCUMENT TEMPLATES

### README.md Template (Compact)
```markdown
# [Feature] System

## Overview
[What it does - 2 paragraphs]

## Status
✅ Working | 🔄 In Progress | ⚠️ Issues | 📋 Planned

## Quick Start
1-2-3 steps

## Documentation
- [REQUIREMENTS.md] - What it should do
- [IMPLEMENTATION.md] - How it works
- [TESTING.md] - How to test

## Code Location
Links to key files

## History
Timeline of major changes
```

### REQUIREMENTS.md Template (Compact)
```markdown
# [Feature] - Requirements

## Business Goals
Why this exists

## Functional Requirements

### Phase 1 (Completed) ✅
REQ-001: [Description]

### Phase 2 (Current) 🔄
REQ-010: [Description]

### Phase 3 (Planned) 📋
REQ-020: [Description]

## Business Rules
1. Rule
2. Rule

## Change History
Table of changes
```

### IMPLEMENTATION.md Template (Compact)
```markdown
# [Feature] - Implementation

## Architecture
Overview diagram/description

## Data Model
Models, fields, relationships

## Service Layer
Key services and methods

## Views & URLs
Routes and view logic

## Workflows
Step-by-step flows

## Code Examples
Common usage patterns

## Change History
Table of changes
```

### TESTING.md Template (Compact)
```markdown
# [Feature] - Testing

## Test Setup
Prerequisites and test data

## Functional Tests
Test 1: [Scenario]
- Steps
- Expected result

## Integration Tests
How it works with other features

## Edge Cases
Unusual scenarios

## Test Results Log
Date | Tests | Pass/Fail | Notes

## Known Issues
Current bugs/limitations
```

---

## 🎯 DECISION NEEDED

### Option A: Implement Immediately ✅ (Recommended)
- I create structure now
- Consolidate docs in ~70 minutes
- You review and approve
- Deploy clean structure

### Option B: Pilot with One Feature
- I do Budget feature only
- You review
- If good, do rest

### Option C: Modify This Proposal
- You suggest changes
- I refine
- Then implement

**Which option do you prefer?**

---

## 📊 COMPARISON

### Before (Current):
```
coda/docs/apps/finance/
├── BUDGET_APPROVAL_SYSTEM.md
├── CODA_APPROVAL_BUSINESS_REQUIREMENTS.md
├── APPROVAL_WORKFLOW_BUSINESS_ANALYSIS.md
├── BUDGET_CATEGORY_CLASSIFICATION.md
├── PHASE2_DATA_DRIVEN_APPROVAL_PLAN.md
├── BUDGET_WORKFLOW_IMPLEMENTATION_COMPLETE.md
├── TRANSACTION_MODEL_MIGRATION_PLAN.md
├── THEME_SWITCHER.md
└── planning/
    ├── (4 more docs)
```
**Issues:**
- 😵 Don't know where to look for specific info
- 😵 Overlap and duplication
- 😵 No clear update pattern
- 😵 Mix of planning, implementation, requirements

### After (Proposed):
```
coda/docs/apps/finance/
├── Budget/
│   ├── README.md           ← Start here
│   ├── REQUIREMENTS.md     ← What it should do
│   ├── IMPLEMENTATION.md   ← How it works
│   └── TESTING.md          ← How to verify
├── Loan/
│   └── (same 4 docs)
├── Payment/
│   └── (same 4 docs)
└── Transaction/
    └── (same 4 docs)
```
**Benefits:**
- ✅ Always know where to look
- ✅ No duplication
- ✅ Clear update pattern
- ✅ Logical grouping

---

**Ready to implement? Give me the green light! 🚀**

