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

### ✅ Working (Phase 1 Complete)
- Budget request creation
- Approval dashboard (`/finance/budget/{company}/approvals/`)
- Approve/reject functionality
- Simple permission logic: **Staff can approve**
- Audit trail (approved_by, approved_at, rejected_by, rejected_at)
- Email notifications
- Theme switcher (Navy/Gold, Purple)

### 🔄 In Progress (Phase 2)
- Data-driven tier classification (analyzing $1.49M in transaction data)
- Intelligent approval routing
- Auto-approval for known recurring expenses
- Finance Manager control dashboard

### ⚠️ Known Issues
- None currently blocking (as of Oct 13, 2025)

### 📋 Planned (Phase 3+)
- Mobile-optimized approval interface
- Real-time approval updates (WebSockets)
- Batch approval actions
- Approval delegation
- Budget vs actuals tracking

## Quick Start

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

