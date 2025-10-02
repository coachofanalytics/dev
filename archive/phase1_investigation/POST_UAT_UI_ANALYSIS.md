# Post-UAT UI Analysis - Budget Dashboard
**Date:** October 1, 2025  
**URL:** https://codamakutano.herokuapp.com/finance/unified-budget/coda/  
**Analysis Type:** First UI Review & Data Quality Assessment

---

## 📊 What We See on the UI

### 1. Dashboard Overview Metrics
- **Total Budgets:** 156
- **Active Budgets:** 151
- **Total Amount:** $143,586,025.96
- **Categories:** 14

#### ✅ Positive Observations:
- Clean, organized layout
- Key metrics prominently displayed
- Tab navigation (Overview, Estimation, Planning, Approvals, Analytics) is intuitive

#### 🤔 Questions/Concerns:
1. **Missing Budgets:** 156 total vs 151 active = **5 inactive budgets**
   - What's the status of these 5 budgets? (Pending, Rejected, Archived?)
   - Should there be a metric showing inactive/pending budgets?

2. **Large Total Amount:** $143.5M seems high
   - Is this cumulative across multiple years?
   - What's the time period for these budgets?
   - Should we add date range filters at the top?

---

### 2. Budget by Category Table

#### Data Distribution Analysis:
| Category | Count | Amount | % of Total |
|----------|-------|--------|------------|
| Operational Expenses | 70 | $239,364.00 | 0.17% |
| Salaries and Wages | 33 | $310,416.00 | 0.22% |
| Utilities | 24 | $105,197.96 | 0.07% |
| Travel and Entertainment | 6 | $38,805.00 | 0.03% |
| Maintenance and Repairs | 3 | $7,324.00 | <0.01% |
| Professional Services | 3 | $11,880.00 | <0.01% |
| Rent | 3 | $6,050.00 | <0.01% |
| Miscellaneous Expenses | 2 | $8,150.00 | <0.01% |
| Others (7 categories) | 7 | $29,320.00 | 0.02% |
| **TOTAL SHOWN** | **151** | **$756,506.96** | **0.53%** |

#### 🚨 CRITICAL DATA ISSUE DISCOVERED:

**The numbers don't add up!**
- Sum of category amounts: **$756,506.96**
- Dashboard total amount: **$143,586,025.96**
- **Missing amount: $142,829,519.00 (99.47%)**

### 3. Urgent Questions to Resolve:

#### A. Data Integrity Issues
1. **Where is the missing $142.8M?**
   - Are there budgets not showing in the category breakdown?
   - Are there hidden/archived budgets included in the total?
   - Database query issue in the aggregation?

2. **Category Counts:**
   - Category table shows 151 budgets (matches Active Budgets)
   - But the total amount doesn't match
   - Possible query filtering mismatch?

3. **Date Ranges:**
   - No visible date filters on the dashboard
   - Are we showing all-time budgets or current year?
   - Should we filter by fiscal year?

#### B. User Experience Issues
1. **No Time Context:**
   - Missing date range selector
   - No indication of fiscal year or period
   - Users can't filter by date

2. **No Department Filter:**
   - Header shows "All Departments" dropdown
   - But no way to see department-level breakdowns in the overview
   - Department filter should affect all metrics

3. **Limited Sorting/Filtering:**
   - Category table appears static
   - No sort by amount or count
   - No search functionality visible

4. **Status Visibility:**
   - Recent Budgets shows only "active" status
   - Where are pending, rejected, or draft budgets?
   - Need status legend/filter

---

## 🔍 Recommended Investigations

### High Priority (Investigate Immediately)
1. **Query the Database:**
   ```sql
   -- Total budgets and amounts by status
   SELECT status, COUNT(*), SUM(amount) 
   FROM finance_budget 
   GROUP BY status;
   
   -- Category breakdown with all budgets
   SELECT category_id, category__name, COUNT(*), SUM(amount)
   FROM finance_budget
   GROUP BY category_id, category__name;
   
   -- Check for NULL categories
   SELECT COUNT(*) FROM finance_budget WHERE category_id IS NULL;
   ```

2. **Review View Logic:**
   - Check `views_unified_budget.py` - unified_budget_dashboard function
   - Verify aggregation queries for:
     - Total amount calculation
     - Category breakdown query
     - Any filtering differences

3. **Check for Multiple Budget Models:**
   - Are we querying both `Budget` and `CodaBudget` models?
   - Is the consolidation working correctly?
   - Any duplicates?

### Medium Priority
4. **Date Filtering:**
   - Add current fiscal year filter by default
   - Show date range selector
   - Display what period is being shown

5. **Status Breakdown:**
   - Add status filter (Active, Pending, Approved, Rejected, Draft)
   - Show counts for each status
   - Highlight pending approvals

6. **Department Breakdown:**
   - When "All Departments" is selected, show department breakdown
   - Add drill-down capability
   - Link to department-specific views

### Low Priority
7. **UI Enhancements:**
   - Add sorting to category table
   - Add export to Excel/CSV
   - Add print-friendly view
   - Visual charts (pie chart for categories, trend lines)

---

## 📋 Data Quality Checks Needed

### 1. Budget Records Audit
- [ ] Count total budgets in database vs. UI
- [ ] Verify sum of all budget amounts
- [ ] Check for orphaned budgets (no category)
- [ ] Check for duplicate budgets
- [ ] Verify status distribution

### 2. Category Assignment
- [ ] Ensure all budgets have a category
- [ ] Check for miscategorized budgets
- [ ] Verify category totals match detail records

### 3. Date Ranges
- [ ] Identify oldest and newest budget
- [ ] Check if multi-year budgets are included
- [ ] Verify fiscal year boundaries

### 4. Department Assignment
- [ ] Check if all budgets have departments
- [ ] Verify department totals
- [ ] Check for orphaned department records

---

## 🎯 Next Steps - Post Analysis Phase

### Immediate Actions (Today)
1. ✅ Run database queries to identify the $142.8M discrepancy
2. ✅ Review the view logic for aggregation issues
3. ✅ Check for model consolidation issues (Budget vs CodaBudget)
4. ✅ Document findings

### Short-term (This Week)
5. 📋 Add date range filters to dashboard
6. 📋 Add status breakdown metrics
7. 📋 Fix any data aggregation bugs discovered
8. 📋 Add department-level breakdown view
9. 📋 Implement sorting/filtering on tables

### Medium-term (Next Sprint)
10. 📋 Add data visualization (charts/graphs)
11. 📋 Implement export functionality
12. 📋 Add drill-down capabilities
13. 📋 Performance optimization for large datasets
14. 📋 Add caching for expensive queries

---

## 💬 Questions for Stakeholders

1. **What time period should the dashboard show by default?**
   - Current fiscal year only?
   - Last 12 months?
   - All time?

2. **What's the expected total budget amount?**
   - Is $143M realistic for your organization?
   - Should this be annual or multi-year?

3. **Budget Status Workflow:**
   - What are all possible budget statuses?
   - What's the approval workflow?
   - Who needs to see what statuses?

4. **Department-Level Access:**
   - Should department heads see only their department?
   - Should finance see all departments?
   - What's the permission model?

5. **Reporting Requirements:**
   - What reports do you need from this data?
   - Monthly/Quarterly/Annual views?
   - Comparison to previous periods?

---

## 🎨 UI Improvements Suggested

### Quick Wins
- Add "Last Updated" timestamp
- Add "as of [date]" to metrics
- Add help text/tooltips
- Add breadcrumb navigation
- Improve mobile responsiveness

### Enhanced Features
- Add dashboard customization (widgets)
- Add saved filters/views
- Add email alerts for budget approvals
- Add budget vs. actual comparison
- Add forecasting/projections view

---

**Analysis Status:** 🟡 In Progress  
**Data Quality Status:** 🔴 Critical Issue Found  
**Next Action:** Database Investigation Required

---

## 🎯 ROOT CAUSE IDENTIFIED!

### Critical Bug in Budget Aggregation Logic

**Location:** `coda/finance/views_unified_budget.py`, lines 164-166

**Problem Code:**
```python
total_amount = Budget.objects.filter(budget_filter).aggregate(
    total=Sum('quantity') * Sum('unit_price')  # ❌ WRONG!
)
```

**Why It's Wrong:**
This calculates:
1. Sum of ALL quantities across ALL budgets
2. Sum of ALL unit_prices across ALL budgets  
3. Multiplies these two huge numbers together

**Example:**
- Budget 1: quantity=10, unit_price=$1,000
- Budget 2: quantity=5, unit_price=$2,000
- Budget 3: quantity=20, unit_price=$500

Wrong calculation:
- Sum(quantities) = 10 + 5 + 20 = 35
- Sum(unit_prices) = 1,000 + 2,000 + 500 = 3,500
- Total = 35 × 3,500 = **$122,500** ❌

Correct calculation:
- Budget 1: 10 × $1,000 = $10,000
- Budget 2: 5 × $2,000 = $10,000
- Budget 3: 20 × $500 = $10,000
- Total = $10,000 + $10,000 + $10,000 = **$30,000** ✅

**Actual Data (from investigation):**
- Database shows: $17,946,788.96 (correct calculation)
- UI shows: $143,586,025.96 (incorrect aggregation)
- **Error magnitude: 8x larger than actual!**

### Correct Implementation

**Option 1: Python Calculation (Current Working)**
```python
total_amount = sum(
    (b.unit_price or 0) * (b.quantity or 0) * (b.cases or 1)
    for b in Budget.objects.filter(budget_filter)
)
```

**Option 2: Database Annotation (More Efficient)**
```python
from django.db.models import F, DecimalField, Sum
from django.db.models.functions import Coalesce

total_amount = Budget.objects.filter(budget_filter).annotate(
    item_total=Coalesce(F('unit_price'), 0) * 
                Coalesce(F('quantity'), 0) * 
                Coalesce(F('cases'), 1,
    output_field=DecimalField()
).aggregate(
    total=Sum('item_total')
)['total'] or Decimal('0.00')
```

**Option 3: Use Calculated Field (Best Long-term)**
Add a database field `total_amount` that's auto-calculated:
```python
class Budget(models.Model):
    # ... existing fields ...
    total_amount = models.GeneratedField(
        expression=F('unit_price') * F('quantity') * F('cases'),
        output_field=DecimalField(max_digits=15, decimal_places=2),
        db_persist=True
    )
```

---

## 📊 Data Investigation Results

### Budget Model (New - 266 records)
- `estimated_amount` field: **$0.00** (not populated)
- Calculated `total_amount` property: **$16,808,574.98**
- Status breakdown:
  - Active: 233 budgets
  - Draft: 33 budgets
- **Issue**: 23 budgets have NULL categories

### CodaBudget Model (Legacy - 259 records)
- Calculated `amount` property: **$1,138,213.98**
- Top categories:
  1. Salaries and Wages: $314,402.00
  2. Other: $307,236.00
  3. Operational Expenses: $300,799.00
  4. Utilities: $117,647.98

### Combined Totals (Correct Calculation)
- **Budget + CodaBudget: $17,946,788.96**
- **UI shows: $143,586,025.96**
- **Discrepancy: $125,639,237.00 (8x error!)**

---

## 🔧 Required Fixes

### Priority 1: Critical Bugs
1. **Fix aggregation logic in `views_unified_budget.py`**
   - Current: `Sum('quantity') * Sum('unit_price')` ❌
   - Fix: Use annotated field or Python calculation ✅
   - Impact: Corrects $143M down to $17M

2. **Check other views for same bug**
   - `budget_consolidation_service.py` - ✅ Correct (uses Python calc)
   - `views_finance_dashboard.py` line 122 - ⚠️ Check this!
   - Any other aggregation queries

### Priority 2: Data Quality
3. **Fix NULL categories** (23 Budget records)
   - Assign proper categories
   - Add validation to prevent NULL in future

4. **Populate `estimated_amount` field**
   - Currently $0.00 for all 266 Budget records
   - Should match calculated `total_amount`
   - Add migration to populate from unit_price × quantity × cases

### Priority 3: User Experience
5. **Add date range filters**
   - Default to current fiscal year
   - Allow users to select custom ranges
   - Show "as of [date]" on metrics

6. **Add status breakdown metrics**
   - Show counts for each status (Draft, Active, Approved, etc.)
   - Highlight pending approvals

7. **Improve category table**
   - Add sorting functionality
   - Add search/filter
   - Make it interactive (click to drill down)

---

## 🎯 Next Immediate Actions

1. **✅ URGENT: Fix the aggregation bug**
   - Update `views_unified_budget.py`
   - Test with real data
   - Verify numbers match database

2. **Test all other aggregation queries**
   - Search codebase for similar patterns
   - Fix any other instances

3. **Deploy hotfix to UAT**
   - Test thoroughly
   - Verify UI now shows ~$18M instead of $143M

4. **Stakeholder Communication**
   - Inform about the bug
   - Explain the fix
   - Set expectations for correct numbers

---

**Analysis Complete:** October 1, 2025  
**Status:** 🔴 Critical Bug Identified - Requires Immediate Fix
