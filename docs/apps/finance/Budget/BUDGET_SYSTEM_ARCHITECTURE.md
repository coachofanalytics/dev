# CODA BUDGET SYSTEM ARCHITECTURE

**Date:** October 22, 2025  
**System:** Data-Driven Budget Management Platform  
**Status:** Production (Phase 3 - User Drill-Down)

---

## 📋 **TABLE OF CONTENTS**

1. [Overview](#overview)
2. [Sample Data Location](#sample-data-location)
3. [System Architecture](#system-architecture)
4. [Data Models](#data-models)
5. [Data Flow](#data-flow)
6. [Views & Templates](#views--templates)
7. [Management Commands](#management-commands)
8. [Critical Issues & Improvements](#critical-issues--improvements)
9. [Recommendations](#recommendations)

---

## 🎯 **OVERVIEW**

The CODA Budget System is a **data-driven** budget management platform that uses **real transaction data** to inform budget decisions. The core principle is: **Transactions are the source of truth**.

### **Key Stats**
- **545 transactions** (97.1% categorized)
- **$2.3M total spending** analyzed
- **15 budget categories** derived from real spending patterns
- **8 departments** with spending tracked
- **10% growth factor** applied for projections

---

## 📍 **SAMPLE DATA LOCATION**

### **Q: Where is the sample data?**

**A: Sample data exists in TWO places:**

#### 1. **Database (Production PostgreSQL)**
```
Location: finance_budget table
Total Entries: 9 sample budget items
Created: October 21-22, 2025
```

**Sample Budget Entries:**
| ID | Item Name | Amount | Category | Created |
|----|-----------|--------|----------|---------|
| 984 | Utilities | $800 | Human Resources | 2025-10-22 |
| 983 | Marketing Campaign | $2,000 | Facilities | 2025-10-22 |
| 982 | IT Equipment | $1,500 | Depreciation | 2025-10-22 |
| 981 | Employee Salaries | $5,000 | Compliance | 2025-10-22 |
| 980 | Marketing | $2,000 | Compliance | 2025-10-21 |
| 979 | Office Supplies | $500 | Compliance | 2025-10-21 |
| 978 | Software Licenses | $1,000 | Compliance | 2025-10-21 |
| 977 | Internet | $200 | Compliance | 2025-10-21 |
| 976 | Office Rent | $5,000 | Compliance | 2025-10-21 |

**Created Via:**
- Django shell commands (manual creation during testing)
- NOT from fixtures or JSON files
- Stored in `finance_budget` table with `company_id=1` (CODA)

#### 2. **Real Transaction Data (PRIMARY SOURCE)**
```
Location: finance_transaction table
Total Entries: 561 transactions
Categorized: 545 (97.1%)
Date Range: 2022-07-24 to 2025-10-11
```

**Top Spending Categories (Real Data):**
1. **Salaries & Wages**: $1,237,794 (188 transactions)
2. **Operational Expenses**: $397,547 (129 transactions)
3. **IT & Software**: $115,745 (22 transactions)
4. **Utilities**: $101,086 (35 transactions)
5. **Human Resources**: $96,425 (29 transactions)

### **Important Note:**
**The dashboard now uses REAL transaction data**, not the sample budget entries. The 9 sample budget items were created for testing but are NOT used in the dashboard calculations.

---

## 🏗️ **SYSTEM ARCHITECTURE**

### **Architecture Layers**

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INTERFACE LAYER                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Dashboard   │  │  Budget      │  │  Transaction │      │
│  │  (Overview)  │  │  Projections │  │  Entry Form  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                      VIEW LAYER                              │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │ unified_budget   │  │ api_cascading    │                │
│  │ _dashboard       │  │ (AJAX endpoints) │                │
│  └──────────────────┘  └──────────────────┘                │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                   SERVICE LAYER (MISSING!)                   │
│  ❌ No service layer - Logic is in views                    │
│  ❌ No EstimationService (referenced but doesn't exist)     │
│  ❌ No ConsolidationService (referenced but doesn't exist)  │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                      MODEL LAYER                             │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │Transaction │  │   Budget   │  │  Budget    │           │
│  │            │  │            │  │  Category  │           │
│  └────────────┘  └────────────┘  └────────────┘           │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                   MANAGEMENT COMMANDS                        │
│  ┌──────────────────────────────────────────────────┐      │
│  │ • categorize_transactions (AI-powered)           │      │
│  │ • generate_budget_projections (data-driven)      │      │
│  │ • analyze_transaction_data (insights)            │      │
│  └──────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                    DATA LAYER                                │
│  ┌──────────────────────────────────────────────────┐      │
│  │ PostgreSQL (Heroku RDS)                          │      │
│  │ • finance_transaction (561 rows, $2.3M)          │      │
│  │ • finance_budget (9 sample rows)                 │      │
│  │ • finance_budgetcategory (25 categories)         │      │
│  └──────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 **DATA MODELS**

### **Core Models (12 Total)**

#### 1. **Transaction** (Core - Real Data Source)
```python
# Location: finance/models/core.py
# Purpose: Actual spending data (source of truth)
# Key Fields:
- amount: Decimal (transaction amount)
- description: Text (transaction details)
- transaction_date: DateTime
- category: FK to BudgetCategory
- department: FK to Department
- receiver: Char (who received payment)
```

#### 2. **Budget** (Primary Budget Model)
```python
# Location: finance/models/budget.py (lines 230-468)
# Purpose: Budget line items (can be auto-generated from transactions)
# Key Fields:
- company: FK to Company
- department: FK to Department
- budget_lead: FK to User
- category: FK to BudgetCategory
- subcategory: FK to BudgetSubCategory
- item_name: CharField
- quantity: Decimal
- unit_price: Decimal
- cases: Integer
- status: CharField (draft, active, approved, etc.)
- estimation_method: CharField (manual, average_3_months, etc.)
- total_amount: Property (calculated)
```

#### 3. **BudgetCategory** (Classification)
```python
# Location: finance/models/budget.py (lines 34-138)
# Purpose: Budget category with intelligent approval tiers
# Key Fields:
- name: CharField
- approval_tier: CharField (A=Auto, B=Priority, C=Assessment)
- auto_approve_enabled: Boolean
- typical_monthly_amount: Decimal (from transaction analysis)
- variance_threshold: Decimal (% variance allowed)
- is_recurring: Boolean (detected from data)
```

#### 4. **BudgetSubCategory** (Sub-Classification)
```python
# Location: finance/models/budget.py (lines 140-152)
# Purpose: Subcategory for granular classification
# Key Fields:
- category: FK to BudgetCategory
- name: CharField
```

#### 5. **BudgetItemLibrary** (Item Master List)
```python
# Location: finance/models/budget.py (lines 155-228)
# Purpose: Master library of budget items with typical amounts
# Key Fields:
- category: FK to BudgetCategory
- subcategory: FK to BudgetSubCategory
- item_name: CharField
- typical_amount: Decimal (learned from history)
- usage_count: Integer (for sorting popular items)
```

#### 6. **BudgetEstimateProjection** (Forecasting)
```python
# Location: finance/models/budget.py (lines 498-515)
# Purpose: Future budget projections
# Key Fields:
- budget: FK to Budget
- projection_date: DateField
- projected_amount: Decimal
- confidence_score: Decimal
- projection_method: CharField
```

#### 7. **BudgetRequest** (Approval Workflow)
```python
# Location: finance/models/budget.py (lines 540-717)
# Purpose: Budget request submission and approval
# Key Fields:
- requester: FK to User
- amount: Decimal
- department: FK to Department
- budget_category: FK to BudgetCategory
- status: CharField (draft, submitted, approved, etc.)
- approval_policy: FK to ApprovalPolicy
- current_approver: FK to User
- approval_chain: JSONField
```

#### 8. **ApprovalPolicy** (Automation Rules)
```python
# Location: finance/models/budget.py (lines 719-841)
# Purpose: Configurable approval policies
# Key Fields:
- name: CharField
- min_amount/max_amount: Decimal (amount thresholds)
- approver_roles: JSONField
- approval_chain: JSONField
- auto_approve: Boolean
- applicable_departments: M2M
- applicable_categories: M2M
```

#### 9. **DisbursementRequest** (Payment Processing)
```python
# Location: finance/models/budget.py (lines 843-957)
# Purpose: Disbursement of approved budgets
# Key Fields:
- budget_request: FK to BudgetRequest
- requested_amount: Decimal
- disbursement_method: CharField
- status: CharField
- transaction_reference: CharField
```

#### 10-12. **Supporting Models**
- **BudgetEstimationTemplate**: Templates for estimation methods
- **MultiYearBudgetPlan**: Multi-year planning
- **AutomationAuditLog**: Audit trail for all actions

---

## 🔄 **DATA FLOW**

### **1. Transaction → Budget Flow (Data-Driven)**

```
Real Transaction Data (561 entries)
           ↓
[categorize_transactions command]
  • AI-powered categorization
  • 97.1% success rate
           ↓
Categorized Transactions (545 entries)
           ↓
[analyze_transaction_data command]
  • Calculate spending patterns
  • Identify top categories
  • Calculate monthly averages
           ↓
Transaction Analysis Report
           ↓
[generate_budget_projections command]
  • Group by category/department
  • Calculate historical averages
  • Apply 10% growth factor
  • Generate 12-month projections
           ↓
Budget Projections ($766K annual)
           ↓
[Dashboard View]
  • Display real spending data
  • Show category breakdowns
  • Monthly averages
  • Department analysis
```

### **2. User Budget Request Flow (Manual)**

```
User Fills Form
           ↓
[Smart Form with AI Predictions]
  • Cascading dropdowns
  • AI suggests category
  • Pre-fill typical amounts
           ↓
Budget Request Created
           ↓
[Approval Policy Engine]
  • Match to policy
  • Determine approval chain
  • Check auto-approval rules
           ↓
Approval Workflow
  • Route to approvers
  • Track status
  • Send notifications
           ↓
Approved Budget
           ↓
[Disbursement Request]
  • Create disbursement
  • Process payment
  • Update actual spending
```

---

## 🖥️ **VIEWS & TEMPLATES**

### **Key Views**

#### 1. **unified_budget_dashboard**
```python
# File: finance/views/budget/views_unified_budget.py
# Purpose: Main dashboard showing budget overview
# Data Source: NOW USES REAL TRANSACTION DATA (fixed Oct 22)
# Key Functions:
  - _get_overview_tab_data(): Real transaction stats
  - _get_estimation_tab_data(): Budget estimates
  - _get_approval_tab_data(): Approval requests
```

#### 2. **generate_budget_projections_api**
```python
# File: finance/views/api/api_cascading.py
# Purpose: API endpoint to trigger budget generation
# Key Features:
  - Calls generate_budget_projections command
  - Returns detailed breakdown by category
  - Shows total annual, monthly average
```

#### 3. **projections_list**
```python
# File: finance/views/budget/views_projections.py
# Purpose: List saved budget projections
# Issue: select_related fields were wrong (FIXED)
```

### **Key Templates**

```
finance/templates/finance/budgets/
  ├── unified_dashboard.html (main dashboard)
  ├── tabs/
  │   ├── overview_tab.html (real transaction data display)
  │   ├── estimation_tab.html
  │   ├── approval_tab.html
  │   └── analysis_tab.html
  ├── budget_projection.html (projection view)
  └── projections_list.html (list view)
```

---

## ⚙️ **MANAGEMENT COMMANDS**

### **1. categorize_transactions**
```bash
python manage.py categorize_transactions --company coda
```
**Purpose:** AI-powered transaction categorization  
**Result:** 97.1% categorization success (545/561)  
**Uses:** Intelligent rules + keyword matching

### **2. generate_budget_projections**
```bash
python manage.py generate_budget_projections --company coda --projection-months 12 --save
```
**Purpose:** Generate data-driven budget projections  
**Result:** $766K annual projection across 15 categories  
**Method:** Historical analysis + 10% growth factor

### **3. analyze_transaction_data**
```bash
python manage.py analyze_transaction_data
```
**Purpose:** Generate spending analysis report  
**Output:** Category totals, department breakdown, trends

---

## 🚨 **CRITICAL ISSUES & IMPROVEMENTS**

### **❌ CRITICAL ISSUES**

#### 1. **Missing Service Layer**
**Problem:**
```python
# Code references services that don't exist:
from finance.services.estimation_service import EstimationService  # ❌ File doesn't exist
from finance.services.consolidation_service import ConsolidationService  # ❌ File doesn't exist
```

**Impact:**
- Business logic is scattered in views
- Hard to test
- Code duplication
- Violates separation of concerns

**Fix Priority:** HIGH

#### 2. **Sample Data vs Real Data Confusion**
**Problem:**
- 9 sample budget entries in database (created manually)
- Dashboard was showing Budget model data (sample)
- Should be showing Transaction model data (real)

**Status:** FIXED (Oct 22, 2025)
- Dashboard now uses real transaction data
- Sample budget entries exist but not used

**Fix Priority:** DONE ✅

#### 3. **Projection Saving Fails**
**Problem:**
```
Error saving projections: Cannot resolve keyword 'company' into field.
Choices are: budget, budget_id, confidence_score, created_at, id, notes...
```

**Root Cause:**
- `BudgetEstimateProjection` has FK to `Budget`, not direct to `Company`
- Command tries to save with `company=` parameter
- Should use `budget__company=`

**Fix Priority:** HIGH

#### 4. **No Transaction → Budget Automation**
**Problem:**
- Transactions and Budgets are separate
- No automatic budget creation from transaction data
- Manual process to create budgets

**Impact:**
- Data-driven approach not fully automated
- Budgets can become stale
- Requires manual intervention

**Fix Priority:** MEDIUM

### **⚠️ ARCHITECTURAL ISSUES**

#### 1. **Tight Coupling**
- Views directly query models
- No abstraction layer
- Hard to change data sources

#### 2. **Inconsistent Data Flow**
- Sometimes uses Budget model
- Sometimes uses Transaction model
- Not clear which is source of truth

#### 3. **Missing Caching**
- Dashboard queries run every page load
- Expensive aggregations
- No caching layer

#### 4. **No Data Validation Layer**
- Budget amounts not validated against transactions
- No variance alerts
- No anomaly detection

---

## 💡 **RECOMMENDATIONS**

### **IMMEDIATE (Do This Week)**

#### 1. **Create Service Layer**
```python
# Create: finance/services/budget_service.py
class BudgetService:
    @staticmethod
    def get_real_spending_data(company, department=None):
        """Get spending data from transactions"""
        pass
    
    @staticmethod
    def generate_projections(company, months=12):
        """Generate budget projections from real data"""
        pass
    
    @staticmethod
    def calculate_variance(budget, actual_spending):
        """Calculate budget vs actual variance"""
        pass
```

**Benefits:**
- Centralized business logic
- Testable
- Reusable
- Maintainable

#### 2. **Fix Projection Saving**
```python
# In generate_budget_projections.py
# Change from:
BudgetEstimateProjection.objects.create(
    company=company,  # ❌ Wrong
    projected_amount=amount
)

# To:
budget = Budget.objects.get_or_create(
    company=company,
    category=category,
    defaults={...}
)[0]

BudgetEstimateProjection.objects.create(
    budget=budget,  # ✅ Correct
    projected_amount=amount
)
```

#### 3. **Delete Sample Data**
```bash
# Remove sample budget entries
python manage.py shell -c "
from finance.models import Budget
Budget.objects.filter(
    id__in=[976, 977, 978, 979, 980, 981, 982, 983, 984]
).delete()
"
```

**Reason:** Not used, causes confusion

### **SHORT-TERM (This Month)**

#### 4. **Implement Automated Budget Sync**
```python
# Create: finance/management/commands/sync_budgets_from_transactions.py
# Purpose: Auto-create/update budgets based on transaction patterns
# Frequency: Daily cron job
# Logic:
  1. Analyze last 30 days of transactions
  2. Compare to existing budgets
  3. Create missing budgets
  4. Update typical amounts
  5. Flag variances > threshold
```

#### 5. **Add Caching Layer**
```python
from django.core.cache import cache

def get_dashboard_data(company):
    cache_key = f'dashboard_data_{company.slug}'
    data = cache.get(cache_key)
    
    if not data:
        data = calculate_dashboard_data(company)
        cache.set(cache_key, data, 3600)  # 1 hour
    
    return data
```

#### 6. **Implement Variance Alerts**
```python
# Create: finance/services/alert_service.py
# Purpose: Alert when spending deviates from budget
# Logic:
  - Check actual spending vs budget daily
  - If variance > threshold, create alert
  - Notify budget lead
  - Show on dashboard
```

### **LONG-TERM (Next Quarter)**

#### 7. **ML-Powered Predictions**
```python
# Use scikit-learn or Prophet for:
  - Seasonal trend detection
  - Anomaly detection
  - Better forecasting
  - Auto-adjust budgets
```

#### 8. **API Layer for External Systems**
```python
# REST API for:
  - Budget data export
  - Transaction import
  - Integration with accounting systems
  - Mobile app support
```

#### 9. **Real-Time Dashboard**
```javascript
// WebSocket updates for:
  - Live transaction feed
  - Real-time budget updates
  - Approval notifications
  - Alert system
```

---

## 📈 **ARCHITECTURE QUALITY SCORE**

| Component | Score | Notes |
|-----------|-------|-------|
| **Models** | 8/10 | Well-designed, comprehensive |
| **Views** | 5/10 | Too much logic, no service layer |
| **Templates** | 7/10 | Good structure, needs optimization |
| **Data Flow** | 6/10 | Works but inconsistent |
| **Testing** | 3/10 | Minimal testing coverage |
| **Documentation** | 7/10 | Good docs, needs API specs |
| **Performance** | 5/10 | No caching, slow queries |
| **Security** | 7/10 | Good permissions, needs audit |

**Overall: 6/10** - Functional but needs refactoring

---

## ✅ **DOES THE ARCHITECTURE MAKE SENSE?**

### **✅ STRENGTHS**

1. **Data-Driven Approach**: Using real transactions is excellent
2. **Comprehensive Models**: Well-designed budget models
3. **Intelligent Categorization**: AI-powered is smart
4. **Approval Workflow**: Good automation framework
5. **Management Commands**: Powerful data processing tools

### **❌ WEAKNESSES**

1. **No Service Layer**: Business logic in views
2. **Inconsistent Data Source**: Budget vs Transaction confusion
3. **Manual Sync Required**: No auto-sync between transactions and budgets
4. **Performance Issues**: No caching
5. **Testing Gaps**: Minimal test coverage

### **VERDICT**

**The core concept is EXCELLENT** (data-driven budgeting), but **implementation needs refactoring** (service layer, caching, automation).

**Recommended Path:**
1. Create service layer (1 week)
2. Fix projection saving (1 day)
3. Delete sample data (1 hour)
4. Implement auto-sync (1 week)
5. Add caching (3 days)
6. Write tests (1 week)

**Total Effort:** 3-4 weeks to production-ready architecture

---

**END OF ARCHITECTURE DOCUMENT**

*Last Updated: October 22, 2025*  
*Author: CODA Development Team*

