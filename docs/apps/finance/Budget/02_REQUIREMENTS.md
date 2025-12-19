# Budget System - Requirements

**Last Updated:** October 22, 2025  
**Status:** Phase 1 Complete ✅ | Phase 2 Complete ✅ | Phase 3 Planned 📋  
**Purpose:** Define what the budget system must do (functional & non-functional requirements)

---

## 🎯 Primary Objective

Create an **intelligent budget management system** that maximizes automation while maintaining financial controls, allowing staff to focus on strategic decisions rather than routine approvals.

### Success Criteria:
- ✅ 70-80% of routine budgets auto-approved (Tier A) - **Current: 40%**
- ✅ Strategic budgets routed intelligently based on criticality
- ✅ 5x faster processing for operational expenses
- ✅ Complete audit trail for all decisions
- ✅ Finance Manager maintains oversight and control

---

## 📋 PHASE 1: Basic Workflow (COMPLETED ✅)

**Status:** Deployed October 13, 2025  
**Goal:** Establish foundation for budget request and approval workflow

### REQ-001: Budget Request Creation
**Implemented:** October 1, 2025  
**Location:** `coda/finance/views/budget/editing.py`

**Requirements:**
- ✅ Users can create budget requests with:
  - Title, amount, purpose
  - Category and subcategory selection
  - Department assignment
  - Priority level (high/medium/low)
  - Attachment support
  
**Acceptance Criteria:**
- ✅ Form validates all required fields
- ✅ Categorization aids (dropdown, suggestions)
- ✅ Status defaults to "draft"
- ✅ Requester automatically recorded

---

### REQ-002: Approval Dashboard
**Implemented:** October 2, 2025  
**Location:** `coda/finance/views/budget/approvals.py`

**Requirements:**
- ✅ Staff can view and manage pending budget approvals:
  - List of pending requests
  - Filter by status, department, date
  - Approve/reject actions
  - Approval history
  - Statistics summary

**Acceptance Criteria:**
- ✅ Only authorized users can access
- ✅ Real-time status updates
- ✅ Responsive UI
- ✅ Theme switcher (Navy/Gold, Purple)

---

### REQ-003: Approve/Reject Actions
**Implemented:** October 13, 2025  
**Location:** `coda/finance/views/budget/approvals.py`

**Requirements:**
- ✅ Authorized users can approve or reject budget requests:
  - Single-click approve
  - Reject with reason
  - Optional notes for both actions
  - Audit trail captured

**Acceptance Criteria:**
- ✅ User, timestamp recorded
- ✅ Status updated immediately
- ✅ Email notifications sent
- ✅ Cannot approve own requests

---

### REQ-004: Audit Trail
**Implemented:** October 13, 2025  
**Location:** `coda/finance/models/budget.py` (Migration 0099)

**Requirements:**
- ✅ Complete tracking of approval actions:
  - `approved_by`, `approved_at`
  - `rejected_by`, `rejected_at`
  - `approval_chain` (for multi-step)
  - `current_approver`

**Acceptance Criteria:**
- ✅ All fields nullable (pending requests)
- ✅ Immutable after set
- ✅ Queryable for reports
- ✅ Displayed in UI

---

### REQ-005: Simple Permission Logic
**Implemented:** October 13, 2025  
**Location:** `coda/finance/views/budget/editing.py::_can_approve_request`

**Logic:**
```python
def _can_approve_request(user, budget_request):
    return user.is_staff or user.is_superuser
```

**Why Simple?** Phase 1 focuses on workflow foundation. Complex approval logic built in Phase 2 based on actual transaction data analysis.

**Acceptance Criteria:**
- ✅ Staff can approve any request
- ✅ Regular users cannot approve
- ✅ Clear messaging to users

---

## 📊 PHASE 2: Data-Driven Intelligence (COMPLETED ✅)

**Status:** Deployed October 16, 2025  
**Goal:** Analyze $1.49M transaction data to implement intelligent approval tiers

### REQ-010: Data-Driven Category Tier Assignment
**Implemented:** October 15, 2025  
**Analysis Tool:** `python manage.py analyze_transaction_data`

**Requirements:**
- ✅ Analyze production transaction data ($1.49M, 18+ months)
- ✅ Classify 25 budget categories into Tiers A/B/C based on:
  - Transaction frequency (recurring vs one-time)
  - Amount variance (predictable vs variable)
  - Business criticality
  - Spending patterns
- ✅ Generate category tier assignments
- ✅ Finance Manager validates classifications

**Results:**
- ✅ **Tier A (Auto-approve):** 1 category - Rent only ($2,000/mo exactly)
- ✅ **Tier B (Standard review):** 5 categories - Salaries, IT, Utilities, Travel, Office
- ✅ **Tier C (Strategic):** 19 categories - Everything else

**Acceptance Criteria:**
- ✅ Export production transaction data
- ✅ Run comprehensive spending pattern analysis
- ✅ Classify all active categories into tiers
- ✅ Generate analysis reports
- ✅ Finance Manager approves tier assignments

---

### REQ-011: Intelligent Approval Routing
**Implemented:** October 16, 2025  
**Location:** `coda/finance/services/budget/approval_engine.py`

**Requirements:**
- ✅ Implement smart approval routing based on category tier
- ✅ Different workflows for different tiers

**Routing Logic:**

**Tier A (Known/Recurring):**
- ✅ Auto-approve if amount within normal variance
- ✅ Flag for review if amount unusual
- ✅ Daily digest to Finance Manager

**Tier B (Variable/Operational):**
- ✅ HIGH priority → Auto-approve
- ✅ MEDIUM priority → Department Manager
- ✅ LOW priority → Requires justification

**Tier C (Strategic):**
- ✅ Requires critical assessment
- ✅ Score-based routing
- ✅ Executive review for high-value items

**Acceptance Criteria:**
- ✅ `approval_tier` field added to `BudgetCategory` model
- ✅ Intelligent routing engine implemented
- ✅ Requests routed automatically on submission
- ✅ Finance Manager can override routing
- ✅ Complete test coverage

---

### REQ-012: Auto-Approval with Anomaly Detection
**Implemented:** October 16, 2025  
**Location:** `coda/finance/services/budget/anomaly_detector.py`

**Requirements:**
- ✅ Auto-approve Tier A budgets with intelligent anomaly detection

**Business Rules:**
1. ✅ Calculate typical monthly amount per category (from transaction data)
2. ✅ Set variance threshold (default: 20%)
3. ✅ If request within threshold → Auto-approve
4. ✅ If request exceeds threshold → Flag for Finance Manager review
5. ✅ Daily digest of all auto-approvals

**Acceptance Criteria:**
- ✅ `typical_monthly_amount` calculated per category
- ✅ `variance_threshold` configurable per category
- ✅ `auto_approve_enabled` flag (Finance Manager control)
- ✅ Anomaly detection logic tested
- ✅ Notification system for digest

---

### REQ-013: Finance Manager Control Dashboard
**Implemented:** October 16, 2025  
**Location:** `/finance/tier-management/coda/`  
**Access:** Finance Manager only

**Requirements:**
- ✅ Dashboard for Finance Manager to:
  - Enable/disable auto-approval per category
  - Set variance thresholds
  - Review daily auto-approvals
  - Investigate flagged anomalies
  - View spending trends
  - Manage tier classifications

**Acceptance Criteria:**
- ✅ Toggle auto-approval per category
- ✅ Adjust thresholds (per category)
- ✅ View auto-approval log (today, this week, this month)
- ✅ Bulk review flagged items
- ✅ Export reports (CSV/PDF)
- ✅ Tier A: 1 category, Tier B: 5 categories, Tier C: 19 categories

---

## 🚀 PHASE 3: Advanced Features (PLANNED 📋)

**Status:** Planned for Q1 2026  
**Goal:** Advanced automation, mobile experience, and analytics

### REQ-020: Budget vs Actuals Tracking
**Priority:** HIGH  
**Effort:** 3 weeks  
**Dependencies:** Transaction system integration

**Requirements:**
- [ ] Real-time comparison of budgeted vs actual spending
- [ ] Visual dashboard showing variance
- [ ] Alerts when approaching budget limits (80%, 90%, 100%)
- [ ] Automatic budget utilization reports
- [ ] Forecasting based on spending trends

**Acceptance Criteria:**
- [ ] Dashboard shows budget vs actual by category
- [ ] Real-time updates (< 1 hour lag)
- [ ] Alert system configured
- [ ] Weekly/monthly reports generated
- [ ] Forecast accuracy >85%

---

### REQ-021: Mobile-Optimized Approval Interface
**Priority:** MEDIUM  
**Effort:** 2 weeks  
**Dependencies:** None

**Requirements:**
- [ ] Responsive design for mobile devices
- [ ] Quick approve/reject actions (swipe gestures)
- [ ] Push notifications for new requests
- [ ] Offline support (queue actions)
- [ ] Touch-optimized UI

**Acceptance Criteria:**
- [ ] Works on iOS and Android
- [ ] < 3 seconds to approve on mobile
- [ ] Push notifications delivered
- [ ] Offline mode functional
- [ ] User satisfaction >80%

---

### REQ-022: Batch Approval Actions
**Priority:** MEDIUM  
**Effort:** 1 week  
**Dependencies:** REQ-002 (Approval Dashboard)

**Requirements:**
- [ ] Select multiple pending requests (checkboxes)
- [ ] Bulk approve selected requests
- [ ] Bulk reject with single reason
- [ ] Apply same notes to batch
- [ ] Confirm before batch action

**Acceptance Criteria:**
- [ ] Can select 2-50 requests at once
- [ ] Batch approval < 5 seconds
- [ ] Each request gets individual audit entry
- [ ] Confirmation dialog shown
- [ ] Rollback capability if error

---

### REQ-023: Approval Delegation
**Priority:** LOW  
**Effort:** 2 weeks  
**Dependencies:** REQ-002 (Approval Dashboard)

**Requirements:**
- [ ] Approvers can delegate authority temporarily
- [ ] Set date range for delegation (start/end)
- [ ] Specify delegate (another user)
- [ ] View delegation history
- [ ] Automatic expiration of delegation

**Acceptance Criteria:**
- [ ] Delegation form with date picker
- [ ] Delegate receives notification
- [ ] Delegation auto-expires
- [ ] Audit trail captures delegation
- [ ] Can revoke delegation early

---

### REQ-024: AI-Powered Budget Suggestions
**Priority:** LOW  
**Effort:** 4 weeks  
**Dependencies:** Phase 2 data analysis

**Requirements:**
- [ ] AI predicts budget needs based on historical patterns
- [ ] Suggests optimal timing for requests
- [ ] Flags unusual requests automatically
- [ ] Learns from approval patterns
- [ ] Improves tier classifications over time

**Acceptance Criteria:**
- [ ] Prediction accuracy >75%
- [ ] Suggestions appear in request form
- [ ] ML model updates monthly
- [ ] Finance Manager can override AI
- [ ] Explanation for each suggestion

---

### REQ-025: Multi-Year Budget Planning
**Priority:** LOW  
**Effort:** 3 weeks  
**Dependencies:** REQ-020 (Budget vs Actuals)

**Requirements:**
- [ ] Annual budget setting (fiscal year)
- [ ] Quarterly budget reviews
- [ ] Multi-year projections (3-5 years)
- [ ] Trend analysis and forecasting
- [ ] Budget carryover rules

**Acceptance Criteria:**
- [ ] Set annual budget per category
- [ ] Quarterly review dashboard
- [ ] 3-year projection charts
- [ ] Carry forward unused budget
- [ ] Finance Manager approval required

---

## 📜 BUSINESS RULES

### BR-001: Approval Tier Classification

**TIER A: Known/Recurring (Auto-Approve)**

**Current Categories (1 total):**
- Rent

**Characteristics:**
- ✅ Extremely predictable amounts
- ✅ Monthly recurring expenses
- ✅ Business cannot operate without them
- ✅ Already committed/contracted
- ✅ Low risk of fraud or waste

**Auto-Approval Rule:**
- Amount within ±20% of typical monthly spend
- Finance Manager has not paused auto-approval
- Category `auto_approve_enabled = TRUE`

**Exception Handling:**
- Amount >20% above typical → Flag for manual review
- New vendor → Require approval
- Unusual timing → Alert Finance Manager

---

**TIER B: Variable/Operational (Priority-Based)**

**Current Categories (5 total):**
- Salaries and Wages
- IT and Software
- Utilities
- Travel and Entertainment
- Office Supplies

**Characteristics:**
- ✅ Variable but operational needs
- ✅ Amounts fluctuate based on business activity
- ✅ Some urgency considerations
- ✅ Medium risk

**Priority Rules:**
- **HIGH/URGENT:** Auto-approve (emergency repairs, urgent travel)
- **MEDIUM:** Department Manager approval
- **LOW:** Requires justification + approval policy

---

**TIER C: Strategic/Discretionary (Assessment Required)**

**Current Categories (19 total):**
- All remaining categories including:
  - Research and Development (R&D)
  - Marketing and Advertising
  - Human Resources (restructuring)
  - Capital Expenditures
  - Miscellaneous Expenses
  - Other

**Characteristics:**
- ⚠️ Non-routine, strategic impact
- ⚠️ Requires thoughtful evaluation
- ⚠️ Higher risk if wrong decision
- ⚠️ Long-term implications

**Assessment Rule:**
- Require critical assessment form
- Score-based routing (0-100 points)
- Route based on score:
  - **80-100:** Fast-track to Senior Manager
  - **50-79:** Standard approval chain
  - **<50:** Executive review required

---

### BR-002: Permission Matrix

**Current Implementation (Phase 1 & 2):**

| Role | Can Create | Tier A | Tier B | Tier C | Override |
|------|-----------|--------|--------|--------|----------|
| Regular User | ✅ Yes | 👁️ View | ❌ No | ❌ No | ❌ No |
| Staff | ✅ Yes | ✅ Approve | ✅ Approve (Med) | ❌ No | ❌ No |
| Department Manager | ✅ Yes | 👁️ View | ✅ Approve | ❌ No | ❌ No |
| Finance Manager | ✅ Yes | ✅ Configure | ✅ Approve | ✅ Review | ✅ Override |
| Senior Manager | ✅ Yes | 👁️ View | ✅ Approve | ✅ Approve (High) | ❌ No |
| Executive | ✅ Yes | 👁️ View | ✅ Approve | ✅ Approve (All) | ✅ Override |

---

### BR-003: Auto-Approval Safety Rules

1. **Finance Manager Control:** Can pause auto-approval for any category at any time
2. **Daily Digest:** Sent to Finance Manager with all auto-approvals
3. **Anomaly Detection:** Flags unusual patterns for review:
   - Amount spikes (>threshold)
   - New vendors
   - Duplicate requests in same period
   - Timing anomalies
4. **Audit Trail:** Captures all auto-approvals for compliance
5. **Monthly Re-Analysis:** Spending patterns analyzed to adjust thresholds

---

### BR-004: Conflict of Interest

1. ✅ Users cannot approve their own budget requests
2. 📋 Department Managers cannot approve requests from their own department (Phase 3)
3. 📋 Family members cannot approve each other's requests (Phase 3 - requires relationship data)

---

## 📊 DATA REQUIREMENTS

### Required Fields (BudgetRequest Model)

**Core Fields:**
- `requester` (User FK) - Who created the request
- `amount` (Decimal) - Budget amount requested
- `purpose` (Text) - Justification
- `department` (Department FK) - Which department
- `budget_category` (BudgetCategory FK) - Classification
- `priority` (CharField) - High/Medium/Low/Urgent
- `status` (CharField) - Draft/Submitted/Approved/Rejected

**Audit Fields (Phase 1):**
- `approved_by` (User FK, nullable) - Who approved
- `approved_at` (DateTime, nullable) - When approved
- `rejected_by` (User FK, nullable) - Who rejected
- `rejected_at` (DateTime, nullable) - When rejected
- `approval_chain` (JSONField) - Multi-step approval history
- `current_approver` (User FK, nullable) - Current approver

**Intelligence Fields (Phase 2):**
- `approval_tier` (CharField) - A/B/C (on Category model)
- `auto_approve_enabled` (Boolean) - Auto-approval active?
- `typical_monthly_amount` (Decimal) - From transaction analysis
- `variance_threshold` (Decimal) - Acceptable variance %
- `is_recurring` (Boolean) - Detected recurring pattern
- `last_pattern_analysis` (DateTime) - Last analysis run

---

## 🔗 INTEGRATION REQUIREMENTS

### Dependencies (Existing Systems):
- ✅ **Transaction System:** For spending pattern analysis (Phase 2)
- ✅ **User/Accounts System:** For permissions and roles
- ✅ **Department System:** For departmental routing
- ✅ **Email System:** For notifications

### Integrates With (Future):
- 📋 **Payment System:** Link approved budgets to payments (Phase 3)
- 📋 **Accounting System:** Export for financial reporting (Phase 3)
- 📋 **Analytics System:** Spending trends and forecasting (Phase 3)

---

## ⚡ NON-FUNCTIONAL REQUIREMENTS

### Performance
- ✅ Approval dashboard loads in <2 seconds (100 requests) - **Current: 1.2s**
- ✅ Auto-approval processing <500ms per request - **Current: 120ms**
- ✅ Pattern analysis runs overnight (batch job)

### Security
- ✅ Role-based access control (RBAC)
- ✅ Audit trail immutable
- ✅ SSL/TLS for all transactions
- ✅ Data encrypted at rest (Heroku PostgreSQL)
- ✅ CSRF protection on all forms

### Scalability
- ✅ Support 1000+ budget requests/month - **Current: ~50/month**
- ✅ Handle 50+ categories - **Current: 25 categories**
- ✅ Multi-company support (already implemented)

### Usability
- ✅ Intuitive approval interface
- ✅ Mobile-responsive design
- ✅ Theme customization (Navy/Gold, Purple)
- 📋 Inline help and tooltips (Phase 3)

### Reliability
- ✅ 99.9% uptime target - **Current: 100% (no downtime)**
- ✅ Automated backups (daily)
- ✅ Rollback capability
- ✅ Error logging and monitoring

---

## 🚫 CONSTRAINTS

### Technical Constraints
- ✅ Django 4.x framework (current)
- ✅ PostgreSQL database (Heroku)
- ✅ Heroku deployment platform
- ✅ No third-party approval tools (build in-house)
- ⚠️ No React/Vue (keep frontend simple - jQuery)

### Business Constraints
- ✅ Must maintain complete audit trail (compliance)
- ✅ Finance Manager must have override control
- ⚠️ Cannot auto-approve above $10,000 (business policy)
- ⚠️ All strategic budgets require human approval

### Regulatory Constraints
- 📋 SOX compliance (if applicable)
- ✅ Audit requirements (complete trail maintained)
- ✅ Data retention policies (7 years)

---

## 📈 ACCEPTANCE CRITERIA SUMMARY

### Phase 1 (COMPLETE ✅)
- ✅ Budget request creation functional
- ✅ Approval dashboard accessible by staff
- ✅ Approve/reject actions work correctly
- ✅ Audit trail captures all actions
- ✅ Email notifications sent
- ✅ Theme switcher functional
- ✅ All tests passing

### Phase 2 (COMPLETE ✅)
- ✅ Transaction data analyzed ($1.49M dataset)
- ✅ Categories classified into tiers (A/B/C)
- ✅ Intelligent routing implemented
- ✅ Auto-approval with anomaly detection
- ✅ Finance Manager control dashboard
- ✅ Tier A: 1 category, Tier B: 5, Tier C: 19
- ✅ 40% automation rate achieved

### Phase 3 (PLANNED 📋)
- [ ] Budget vs actuals tracking operational
- [ ] Mobile interface responsive and functional
- [ ] Batch approval actions working
- [ ] Approval delegation implemented
- [ ] AI suggestions achieving >75% accuracy
- [ ] Multi-year planning functional

---

## 📝 CHANGE HISTORY

| Date | Change | By | Reason |
|------|--------|-----|--------|
| Oct 22, 2025 | Consolidated into 7-doc structure | AI | Documentation reorganization |
| Oct 16, 2025 | Phase 2 COMPLETE - All tier management deployed | CM | Phase 2 finished |
| Oct 15, 2025 | Added Phase 2 results (tier classifications) | CM | After data analysis complete |
| Oct 13, 2025 | Added Phase 2 requirements (data-driven tiers) | CM | After Phase 1 complete |
| Oct 13, 2025 | Added audit fields requirements | CM | Support Phase 1 workflow |
| Oct 2, 2025 | Initial requirements doc created | CM | Project kickoff |

---

**Next Steps:**
- Review Phase 3 priorities with stakeholders
- Validate Phase 2 automation rates (target: 70-80%)
- Plan Phase 3 implementation timeline
- Gather user feedback on Phase 2 features

**See Also:**
- `01_ANALYSIS.md` - Problem statement and ROI analysis
- `03_ARCHITECTURE.md` - System design and data models
- `04_IMPLEMENTATION.md` - Technical implementation details

---

**Document Owner:** Finance Manager  
**Last Review:** October 22, 2025  
**Next Review:** After Phase 3 planning


