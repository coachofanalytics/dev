# Budget System

## Overview
Complete budget management system for CODA including budget request creation, approval workflows, tracking, and reporting. The system supports tiered approval logic designed to maximize automation while maintaining financial controls.

**Key Features:**
- Budget request submission with category classification
- Three-tier approval system (Known/Variable/Strategic)
- Approval dashboard with filtering and actions
- Audit trail for all approvals/rejections
- Theme-customizable dashboard
- Email notifications

## Current Status

### ✅ Phase 1 Complete (October 13, 2025)
- Budget request creation
- Approval dashboard (`/finance/budget/{company}/approvals/`)
- Approve/reject functionality
- Simple permission logic: **Staff can approve**
- Audit trail (approved_by, approved_at, rejected_by, rejected_at)
- Email notifications
- Theme switcher (Navy/Gold, Purple)

### ✅ Phase 2 Complete (October 16, 2025) 🎉
- **Data-driven tier classification** - Analyzed $1.49M transaction dataset ✅
- **Intelligent approval routing** - Tier-based (A/B/C) ✅
- **Auto-approval system** - Tier A categories with variance checking ✅
- **Finance Manager control dashboard** - Full tier management UI ✅
- **Tier classification results:**
  - Tier A: 1 category (Rent - $2,000/mo)
  - Tier B: 5 categories (Salaries, IT, Utilities, Travel, Office)
  - Tier C: 19 categories (Strategic + dormant)
- **Access:** `/finance/tier-management/coda/` (Finance Manager only)

### ⚠️ Known Issues
- None currently blocking (as of Oct 13, 2025)

### 📋 Planned (Phase 3+)
- Mobile-optimized approval interface
- Real-time approval updates (WebSockets)
- Batch approval actions
- Approval delegation
- Budget vs actuals tracking

## Quick Start

### ⚡ 5-Minute Setup (For Developers):

**Step 1: Categorize Transactions** (2 min)
```bash
cd coda
python manage.py categorize_transactions --company coda
```
Expected: 97% of transactions categorized

**Step 2: Generate Projections** (2 min)
```bash
python manage.py generate_budget_projections --company coda --save
```
Expected: 15 budget projections created

**Step 3: Auto-Sync Budgets** (1 min)
```bash
python manage.py sync_budgets --company coda --min-transactions 10
```
Expected: 4 active budgets created

**Step 4: View Dashboard**
Navigate to: `/finance/budget-dashboard/coda/`

---

### For Budget Requesters:
1. Login to system
2. Navigate to `/finance/budget/request/new/`
3. Fill out budget request form:
   - Title, amount, category
   - Purpose/justification
   - Priority (high/medium/low)
4. Submit for approval
5. Track status on dashboard

### For Approvers (Staff):
1. Navigate to `/finance/budget/{company}/approvals/`
2. Review pending requests
3. Click approve ✅ or reject ❌ icon
4. Add optional notes
5. Confirm action

---

## 👥 User Roles & Permissions

### Budget Viewer
- View dashboard
- View reports
- View transactions

### Budget Creator
- All Viewer permissions
- Create budget requests
- Submit for approval
- Clone templates

### Department Head
- All Creator permissions
- Approve department budgets (< $10K)
- View department variance reports

### Finance Manager
- All Department Head permissions
- Approve all budgets
- Generate projections
- Run auto-sync
- Configure templates
- Manage approval policies
- **Access tier management:** `/finance/tier-management/coda/`

### System Admin
- All permissions
- Configure system settings
- Manage users
- Run management commands
- Database migrations

---

## 🔧 Common Management Commands

```bash
# Categorize transactions
python manage.py categorize_transactions --company coda

# Generate projections
python manage.py generate_budget_projections --company coda --save

# Auto-sync budgets
python manage.py sync_budgets --company coda

# Analyze transactions
python manage.py analyze_transaction_data

# Setup templates
python manage.py setup_budget_templates

# View URLs
python manage.py show_urls | grep budget
```

## Documentation

- **[README.md](README.md)** - This file - overview and navigation
- **[REQUIREMENTS.md](REQUIREMENTS.md)** - Business requirements and approval tiers
- **[IMPLEMENTATION.md](IMPLEMENTATION.md)** - Technical details and architecture
- **[TESTING.md](TESTING.md)** - Test scenarios and validation guide

## Key Code Locations

### Models
- **Primary:** `coda/finance/models/budget.py`
  - `BudgetRequest` - Budget request model with approval tracking
  - `ApprovalPolicy` - Approval rules and routing logic
  - `BudgetCategory` - Category classification (future: tier assignments)

### Views
- **Approvals:** `coda/finance/views/budget/approvals.py`
  - `budget_approval_dashboard` - Main approval interface
  - `approve_budget_request` - Approve action
  - `reject_budget_request` - Reject action
- **Editing:** `coda/finance/views/budget/editing.py`
  - `budget_request_detail` - Detail view
  - `create_budget_request` - Request creation

### Templates
- **Dashboard:** `coda/finance/templates/finance/budgets/budget_approvals.html`
- **Detail:** `coda/finance/templates/finance/budgets/budget_request_detail.html`
- **Forms:** `coda/finance/templates/finance/budgets/budget_request_form.html`

### Services (Planned)
- **Approval Engine:** `coda/finance/services/budget/approval_engine.py` (Phase 2)
- **Budget Service:** `coda/finance/services/budget/budget_service.py`

## URLs

### User-Facing
- Approval Dashboard: `/finance/budget/{company}/approvals/`
- Request List: `/finance/budget-requests/`
- Create Request: `/finance/budget/request/new/`
- Request Detail: `/finance/budget/request/{id}/`

### API Endpoints (Future)
- Approve: `POST /finance/api/budget/approve/`
- Reject: `POST /finance/api/budget/reject/`
- Stats: `GET /finance/api/budget/stats/`

## Approval Tiers (Planned - Phase 2)

### Tier A: Known/Recurring (Auto-Approve)
- Utilities, Salaries, Rent, Insurance, IT Subscriptions
- Auto-approve if within normal variance
- Finance Manager daily digest

### Tier B: Variable/Operational (Priority-Based)
- Supplies, Travel, Maintenance, Training
- HIGH priority → Auto-approve
- MEDIUM → Manager approval
- LOW → Requires justification

### Tier C: Strategic (Smart Assessment)
- R&D, Marketing, New Projects
- Critical assessment questions
- Scoring-based routing

**See:** [REQUIREMENTS.md](REQUIREMENTS.md) for complete tier details

## History

### October 2025 - Phase 1 Complete
- **Oct 13:** Fixed approval workflow bugs, added audit fields
- **Oct 2:** Dashboard bug fix (177x inflation → accurate aggregation)
- **Oct 1:** Initial budget request model created

### September 2025 - Foundation
- **Sept 30:** Project planning, tier system design
- Transaction analysis framework established ($1.49M dataset)

## Budget Categories

**25 Total Categories, 77 Subcategories**

**Top 5 Active Categories:**
1. Salaries and Wages (181 transactions, $939K)
2. Operational Expenses (67 transactions, $183K)
3. Human Resources (25 transactions, $88K)
4. IT and Software (21 transactions, $116K)
5. Utilities (16 transactions, $52K)

**Dormant Categories (0 transactions):**
- Marketing, Sales Commissions, Insurance, Training, R&D, Inventory, Logistics, Customer Service, Security, Compliance, Taxes (12 total)

**See:** [REQUIREMENTS.md](REQUIREMENTS.md) for complete category breakdown

---

## Key URLs

### User-Facing:
- **Main Dashboard:** `/finance/budget-dashboard/{company}/`
- **Approval Dashboard:** `/finance/budget/{company}/approvals/`
- **Request List:** `/finance/budget-requests/`
- **Create Request:** `/finance/budget/request/new/`
- **Request Detail:** `/finance/budget/request/{id}/`
- **Category Detail:** `/finance/budget/{company}/category/{id}/`

### API Endpoints:
- **Budget by Category:** `GET /finance/api/budget-category/{id}/`
- **Budget Projections:** `GET /finance/api/budget-projections/`
- **Generate Projection:** `POST /finance/api/generate-projection/`
- **Approve Request:** `POST /finance/api/budget/approve/`
- **Reject Request:** `POST /finance/api/budget/reject/`

---

## Next Steps

1. **Export production transaction data** (for tier classification)
2. **Run spending pattern analysis** (identify recurring vs strategic)
3. **Classify categories** into Tiers A/B/C
4. **Implement intelligent approval engine**
5. **Build Finance Manager control dashboard**

**See:** [REQUIREMENTS.md](REQUIREMENTS.md) Phase 2 plan for details

---

**Maintained by:** Cursor AI Assistant  
**Last Updated:** October 13, 2025  
**Questions?** Check other docs in this directory or deployment logs

