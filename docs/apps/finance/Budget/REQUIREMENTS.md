# Budget System - Requirements

**Last Updated:** October 13, 2025  
**Status:** Phase 1 Complete, Phase 2 Planned

---

## Business Goals

### Primary Objective
Create an intelligent budget management system that **maximizes automation while maintaining financial controls**, allowing staff to focus on strategic decisions rather than routine approvals.

### Success Criteria
- 70-80% of routine budgets auto-approved (Tier A)
- Strategic budgets routed intelligently based on criticality
- 5x faster processing for operational expenses
- Complete audit trail for all decisions
- Finance Manager maintains oversight and control

---

## Functional Requirements

### Phase 1 (Completed) ✅

#### REQ-001: Budget Request Creation
**Implemented:** October 1, 2025  
**Location:** `coda/finance/views/budget/editing.py`

Users can create budget requests with:
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

#### REQ-002: Approval Dashboard
**Implemented:** October 2, 2025  
**Location:** `coda/finance/views/budget/approvals.py`

Staff can view and manage pending budget approvals:
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

#### REQ-003: Approve/Reject Actions
**Implemented:** October 13, 2025  
**Location:** `coda/finance/views/budget/approvals.py`

Authorized users can approve or reject budget requests:
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

#### REQ-004: Audit Trail
**Implemented:** October 13, 2025  
**Location:** `coda/finance/models/budget.py` (Migration 0099)

Complete tracking of approval actions:
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

#### REQ-005: Simple Permission Logic (Temporary)
**Implemented:** October 13, 2025  
**Location:** `coda/finance/views/budget/editing.py::_can_approve_request`

**Logic:**
```python
def _can_approve_request(user, budget_request):
    return user.is_staff or user.is_superuser
```

**Why Simple?** Building Phase 2 based on actual transaction data analysis, not guesses!

**Acceptance Criteria:**
- ✅ Staff can approve any request
- ✅ Regular users cannot approve
- ✅ Clear messaging to users

---

### Phase 2 (Current - In Planning) 🔄

#### REQ-010: Data-Driven Category Tier Assignment
**Status:** Analysis phase  
**Target:** October 20, 2025  
**Priority:** High

**Description:**  
Analyze $1.49M in production transaction data to classify budget categories into three tiers:

**Acceptance Criteria:**
- [ ] Export production transaction data
- [ ] Run comprehensive spending pattern analysis
- [ ] Classify 25 categories into Tiers A/B/C based on:
  - Transaction frequency (recurring vs one-time)
  - Amount variance (predictable vs variable)
  - Business criticality
  - Vendor patterns
- [ ] Generate `category_spending_analysis.csv`
- [ ] Finance Manager validates tier assignments

**Deliverables:**
1. Analysis scripts (management commands)
2. Category tier assignments (data file)
3. Validation report

**See:** Phase 2 implementation plan below

---

#### REQ-011: Intelligent Approval Routing
**Status:** Planned (pending REQ-010)  
**Target:** October 27, 2025  
**Priority:** High  
**Dependency:** REQ-010 (tier classification)

**Description:**  
Implement smart approval routing based on category tier and business rules.

**Routing Logic:**

**Tier A (Known/Recurring):**
- Auto-approve if amount within normal variance
- Flag for review if amount unusual
- Daily digest to Finance Manager

**Tier B (Variable/Operational):**
- HIGH priority → Auto-approve
- MEDIUM priority → Department Manager
- LOW priority → Requires justification

**Tier C (Strategic):**
- Requires critical assessment
- Score-based routing
- Executive review for low scores

**Acceptance Criteria:**
- [ ] Add `approval_tier` field to `BudgetCategory` model
- [ ] Implement `IntelligentApprovalEngine` service
- [ ] Route requests automatically on submission
- [ ] Finance Manager can override routing
- [ ] Complete test coverage

---

#### REQ-012: Auto-Approval with Anomaly Detection
**Status:** Planned  
**Target:** October 27, 2025  
**Priority:** High  
**Dependency:** REQ-010, REQ-011

**Description:**  
Auto-approve Tier A (Known/Recurring) budgets with intelligent anomaly detection.

**Business Rules:**
1. Calculate typical monthly amount per category (from transaction data)
2. Set variance threshold (default: 20%)
3. If request within threshold → Auto-approve
4. If request exceeds threshold → Flag for Finance Manager review
5. Daily digest of all auto-approvals

**Acceptance Criteria:**
- [ ] `typical_monthly_amount` calculated per category
- [ ] `variance_threshold` configurable per category
- [ ] `auto_approve_enabled` flag (Finance Manager control)
- [ ] Anomaly detection logic tested
- [ ] Notification system for digest

---

#### REQ-013: Finance Manager Control Dashboard
**Status:** Planned  
**Target:** November 3, 2025  
**Priority:** Medium  
**Dependency:** REQ-011, REQ-012

**Description:**  
Dashboard for Finance Manager to:
- Enable/disable auto-approval per category
- Set variance thresholds
- Review daily auto-approvals
- Investigate flagged anomalies
- View spending trends

**Acceptance Criteria:**
- [ ] Toggle auto-approval per category
- [ ] Adjust thresholds (per category)
- [ ] View auto-approval log (today, this week, this month)
- [ ] Bulk review flagged items
- [ ] Export reports (CSV/PDF)

---

#### REQ-014: Strategic Budget Assessment Form
**Status:** Planned  
**Target:** November 10, 2025  
**Priority:** Low  
**Dependency:** REQ-011

**Description:**  
For Tier C (Strategic) budgets, require critical assessment questions to determine routing priority.

**Assessment Questions:**
1. Strategic alignment? (0-20 points)
2. ROI/benefit expected? (0-25 points)
3. Time sensitivity? (0-15 points)
4. Risk if denied? (0-20 points)
5. Alternatives considered? (0-10 points)
6. Long-term impact? (0-10 points)

**Scoring & Routing:**
- **80-100 points:** Fast-track to Senior Manager
- **50-79 points:** Standard approval chain
- **<50 points:** Executive review required

**Acceptance Criteria:**
- [ ] Assessment form integrated into budget request flow
- [ ] Auto-scoring system
- [ ] Score-based routing logic
- [ ] Assessment visible to approvers

---

### Phase 3 (Planned) 📋

#### REQ-020: Budget vs Actuals Tracking
**Priority:** Medium  
**Effort:** High

Track actual spending against approved budgets:
- Real-time comparison dashboard
- Alerts when approaching budget limits
- Automatic budget utilization reports
- Forecasting based on spending trends

---

#### REQ-021: Mobile-Optimized Approval Interface
**Priority:** Low  
**Effort:** Medium

Allow approvals from mobile devices:
- Responsive design
- Quick approve/reject actions
- Push notifications
- Offline support

---

#### REQ-022: Batch Approval Actions
**Priority:** Low  
**Effort:** Low

Allow approvers to:
- Select multiple pending requests
- Bulk approve/reject
- Apply same notes to batch

---

#### REQ-023: Approval Delegation
**Priority:** Low  
**Effort:** Medium

Allow approvers to:
- Delegate approval authority temporarily
- Set date range for delegation
- View delegation history

---

## Business Rules

### BR-001: Approval Tier Classification

**TIER A: Known/Recurring (Auto-Approve)**

**Categories (9 total):**
- Utilities (electricity, water, gas)
- Rent
- Insurance
- Security
- Salaries and Wages
- Sales Commissions
- IT and Software (subscriptions, licenses)
- Taxes
- Compliance and Regulatory

**Rationale:**
- Budgeted, recurring expenses
- Predictable amounts
- Business cannot operate without them
- Already committed/contracted
- Low risk of fraud or waste

**Rule:** Auto-approve if:
- Amount within ±20% of typical monthly spend
- Finance Manager has not paused auto-approval
- Category `auto_approve_enabled = TRUE`

**Exception:** Flag for manual review if:
- Amount >20% above typical
- New vendor
- Unusual timing (e.g., duplicate in same month)

---

**TIER B: Variable/Operational (Priority-Based)**

**Categories (9 total):**
- Office Supplies
- Inventory and Supplies
- Facilities and Equipment (maintenance/small purchases)
- Maintenance and Repairs
- Training and Development
- Travel and Entertainment
- Professional Services (consultants, legal, accounting)
- Customer Service
- Logistics and Shipping

**Rationale:**
- Variable but operational needs
- Amounts fluctuate based on business activity
- Some urgency considerations
- Medium risk

**Priority Rules:**
- **HIGH/URGENT:** Auto-approve (emergency repairs, urgent travel)
- **MEDIUM:** Department Manager approval
- **LOW:** Requires justification + approval policy

---

**TIER C: Strategic/Discretionary (Smart Assessment)**

**Categories (7 total):**
- Research and Development (R&D)
- Marketing and Advertising
- Human Resources (new hires, restructuring)
- Depreciation and Amortization (capital assets)
- Operational Expenses (new programs)
- Miscellaneous Expenses
- Other

**Rationale:**
- Non-routine, strategic impact
- Requires thoughtful evaluation
- Higher risk if wrong decision
- Long-term implications

**Rule:** Require critical assessment → score → route based on score

---

### BR-002: Permission Matrix

**Current (Phase 1):**
| Role | Can Create | Can Approve | Can Reject | Can Override |
|------|-----------|-------------|-----------|--------------|
| Regular User | ✅ Yes | ❌ No | ❌ No | ❌ No |
| Staff | ✅ Yes | ✅ Yes | ✅ Yes | ❌ No |
| Superuser | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |

**Future (Phase 2):**
| Role | Tier A | Tier B | Tier C | Override |
|------|--------|--------|--------|----------|
| Regular User | ❌ | ❌ | ❌ | ❌ |
| Department Manager | 👁️ View | ✅ Approve (Medium) | ❌ | ❌ |
| Finance Manager | ✅ Enable/Disable | ✅ Approve | ✅ Review | ✅ Override |
| Senior Manager | 👁️ View | ✅ Approve | ✅ Approve (High Score) | ❌ |
| Executive | 👁️ View | ✅ Approve | ✅ Approve (All) | ✅ Override |

---

### BR-003: Auto-Approval Safety Rules

1. **Finance Manager can pause auto-approval** for any category at any time
2. **Daily digest** sent to Finance Manager with all auto-approvals
3. **Anomaly detection** flags unusual patterns for review:
   - Amount spikes (>threshold)
   - New vendors
   - Duplicate requests in same period
   - Timing anomalies
4. **Audit trail** captures all auto-approvals for compliance
5. **Monthly re-analysis** of spending patterns to adjust thresholds

---

### BR-004: Conflict of Interest

1. Users cannot approve their own budget requests
2. Department Managers cannot approve requests from their own department (future)
3. Family members cannot approve each other's requests (future - requires relationship data)

---

## Budget Categories & Structure

### Active Categories (25 Total)

**Top 5 Categories by Spending:**
1. **Salaries and Wages** - $939K (64.4% of spending)
   - Regular employee salaries
   - Overtime pay
   - Bonuses
   - Employee benefits
   - Contractor payments

2. **Operational Expenses** - $183K (12.6%)
   - Office utilities
   - Communication services
   - Equipment rentals
   - Food and groceries (most active)

3. **IT and Software** - $116K (7.9%)
   - Website maintenance
   - Hosting fees
   - Communication tools
   - Software licenses
   - Cloud services
   - IT support

4. **Human Resources** - $88K (6.0%)
   - Recruitment costs
   - Employee relations
   - Payroll services
   - Cleaning services

5. **Utilities** - $52K (3.6%)
   - Electricity (KPLC)
   - Water
   - Gas
   - Internet and phone

**Other Active Categories:**
- Travel and Entertainment ($22K)
- Facilities and Equipment ($29K)
- Maintenance and Repairs ($4K)
- Professional Services ($7K)

**Dormant Categories (0 transactions):**
- Marketing and Advertising
- Sales Commissions
- Insurance
- Training and Development
- R&D
- Inventory and Supplies
- Logistics and Shipping
- Customer Service
- Security
- Compliance and Regulatory
- Taxes
- Depreciation and Amortization

**Source:** BUDGET_TAXONOMY_ANALYSIS.md

### Budget Reality Check

**Historical Analysis (27 months, July 2022 - Oct 2024):**
- **Total Spending:** $1,458,482
- **Monthly Average:** $54,682
- **Annual Projection:** $722K (with 10% growth)
- **Current Budget:** $65K
- **Gap:** 1,007% increase needed!

**Key Findings:**
- Current budget is **11x too low**
- Salaries dominate (64.4% of spending)
- IT costs were invisible ($57K/year, $0 budgeted)
- Operations severely underfunded (14% of actual costs)

**Source:** BUDGET_PROJECTION_ANALYSIS.md

---

## Data Requirements

### Required Fields (BudgetRequest Model)
- `requester` (User FK) - Who created the request
- `amount` (Decimal) - Budget amount requested
- `purpose` (Text) - Justification
- `department` (Department FK) - Which department
- `budget_category` (BudgetCategory FK) - Classification
- `priority` (CharField) - High/Medium/Low/Urgent
- `status` (CharField) - Draft/Submitted/Approved/Rejected
- `approved_by` (User FK, nullable) - Who approved
- `approved_at` (DateTime, nullable) - When approved
- `rejected_by` (User FK, nullable) - Who rejected
- `rejected_at` (DateTime, nullable) - When rejected

### Category Classification Fields (Phase 2)
- `approval_tier` (CharField) - A/B/C
- `auto_approve_enabled` (Boolean) - Auto-approval active?
- `typical_monthly_amount` (Decimal, nullable) - From analysis
- `variance_threshold` (Decimal) - Acceptable variance %
- `is_recurring` (Boolean) - Detected recurring pattern
- `last_pattern_analysis` (DateTime) - Last analysis run

---

## Integration Requirements

### Depends On:
- **Transaction System:** For spending pattern analysis (Phase 2)
- **User/Accounts System:** For permissions and roles
- **Department System:** For departmental routing
- **Email System:** For notifications

### Used By:
- **Dashboard:** Budget statistics and recent activity
- **Reporting:** Budget vs actuals (Phase 3)
- **Analytics:** Spending trends

---

## Non-Functional Requirements

### Performance
- Approval dashboard loads in <2 seconds (100 requests)
- Auto-approval processing <500ms per request
- Pattern analysis runs overnight (batch job)

### Security
- Role-based access control (RBAC)
- Audit trail immutable
- SSL/TLS for all transactions
- Data encrypted at rest (Heroku PostgreSQL)

### Scalability
- Support 1000+ budget requests/month
- Handle 50+ categories
- Multi-company support (already implemented)

### Usability
- Intuitive approval interface
- Mobile-responsive design
- Theme customization (already implemented)
- Inline help and tooltips

---

## Constraints

### Technical
- Django 4.x framework
- PostgreSQL database
- Heroku deployment
- No third-party approval tools (build in-house)

### Business
- Must maintain complete audit trail (compliance)
- Finance Manager must have override control
- Cannot auto-approve above certain thresholds (TBD based on data)

### Regulatory
- SOX compliance (if applicable)
- Audit requirements
- Data retention policies

---

## Change History

| Date | Change | By | Reason |
|------|--------|-----|--------|
| Oct 13, 2025 | Added Phase 2 requirements (data-driven tiers) | CM | After data analysis framework established |
| Oct 13, 2025 | Added audit fields (approved_by, rejected_by, etc.) | CM | Support Phase 1 workflow |
| Oct 2, 2025 | Initial requirements doc created | CM | Project kickoff |

---

## Phase 2 Implementation Plan (Summary)

### 7-Day Timeline:

**Day 1-2: Data Export & Analysis**
- Export production transactions ($1.49M dataset)
- Analyze spending patterns by category
- Identify recurring vs strategic expenses
- Generate tier recommendations

**Day 3-4: Category Classification**
- Classify 25 categories into Tiers A/B/C
- Set variance thresholds
- Define anomaly detection rules
- Finance Manager validates

**Day 5-6: Implementation**
- Add tier fields to BudgetCategory model
- Build IntelligentApprovalEngine service
- Implement auto-approval logic
- Create Finance Manager control dashboard

**Day 7: Testing & Deployment**
- Validate with historical data
- UAT testing
- Production deployment
- Monitor and iterate

**See:** Phase 2 detailed plan in planning directory (PHASE2_DATA_DRIVEN_APPROVAL_PLAN.md)

---

**Maintained by:** Cursor AI Assistant  
**Next Review:** After Phase 2 implementation  
**Questions?** Check IMPLEMENTATION.md for technical details

