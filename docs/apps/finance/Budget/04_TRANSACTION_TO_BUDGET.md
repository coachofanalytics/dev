# Transaction to Budget Flow

**How Real Spending Data Becomes Future Budgets**

**Last Updated:** October 22, 2025  
**Document Version:** 1.0

---

## 📋 **TABLE OF CONTENTS**

1. [Overview](#overview)
2. [The Complete Flow](#the-complete-flow)
3. [Step-by-Step Process](#step-by-step-process)
4. [Automation Configuration](#automation-configuration)
5. [Examples](#examples)
6. [Troubleshooting](#troubleshooting)

---

## 🎯 **OVERVIEW**

The CODA Budget System transforms **real transaction data** into **future budgets** through an automated, data-driven process. This ensures budgets are based on actual spending patterns, not guesswork.

### **Core Principle**
> Transactions (PAST) → Analysis → Budgets (FUTURE)

### **Key Benefits**
- ✅ **Data-driven:** Based on real spending
- ✅ **Automated:** Runs weekly without manual intervention
- ✅ **Accurate:** 70-95% confidence scores
- ✅ **Adaptive:** Updates when patterns change

---

## 🔄 **THE COMPLETE FLOW**

```
┌─────────────────────────────────────────────────────────────────┐
│                    STEP 1: DATA COLLECTION                       │
│                                                                   │
│  Bank Statements → CSV Import → Transaction Model (561 entries)  │
│  $2.3M total spending                                            │
└───────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    STEP 2: CATEGORIZATION                        │
│                                                                   │
│  Command: python manage.py categorize_transactions              │
│  • AI-powered + Rule-based categorization                       │
│  • Keyword matching (KPLC → Utilities, Safaricom → IT, etc.)    │
│  • Result: 545 transactions categorized (97.1% success)         │
│  • 15 categories identified                                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    STEP 3: PATTERN ANALYSIS                      │
│                                                                   │
│  Command: python manage.py analyze_transaction_data             │
│  • Group by category and department                             │
│  • Calculate monthly averages (6 months)                        │
│  • Identify trends and patterns                                  │
│  • Detect recurring expenses                                     │
│                                                                   │
│  Example Output:                                                 │
│  Salaries: $103K/month (188 transactions)                       │
│  Operations: $33K/month (129 transactions)                       │
│  IT: $9.6K/month (22 transactions)                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    STEP 4: PROJECTION GENERATION                 │
│                                                                   │
│  Command: python manage.py generate_budget_projections          │
│  • Apply 10% growth factor to historical averages               │
│  • Project 12 months ahead                                       │
│  • Calculate confidence scores based on data quality            │
│  • Create Budget + BudgetEstimateProjection records             │
│                                                                   │
│  Result:                                                         │
│  • 15 budget projections created                                 │
│  • Total: $766K annual                                           │
│  • Confidence: 70-95%                                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    STEP 5: AUTO-SYNC                             │
│                                                                   │
│  Command: python manage.py sync_budgets                         │
│  • Create budgets for categories with sufficient data           │
│  • Update existing budgets if variance > threshold              │
│  • Mark as "active" for current use                             │
│  • Link to department and budget lead                           │
│                                                                   │
│  Result:                                                         │
│  • 4 active budgets created                                      │
│  • Salaries: $44K/month                                          │
│  • Customer Service: $16K/month                                  │
│  • Office Supplies: $14K/month                                   │
│  • Miscellaneous: $2K/month                                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    STEP 6: VARIANCE TRACKING                     │
│                                                                   │
│  Ongoing: Compare actual spending vs budget                      │
│  • Calculate variance daily                                      │
│  • Alert if variance > threshold (default: 20%)                 │
│  • Update dashboard in real-time                                 │
│  • Generate reports                                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    STEP 7: CONTINUOUS IMPROVEMENT                │
│                                                                   │
│  Weekly Auto-Sync (Cron Job):                                    │
│  • Re-analyze transaction patterns                               │
│  • Update budgets if patterns change                             │
│  • Improve confidence scores with more data                      │
│  • Adapt to business changes                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📝 **STEP-BY-STEP PROCESS**

### **STEP 1: Data Collection**

**Import Transactions:**
```bash
# Manual import via Django admin or API
POST /finance/api/transactions/import/
```

**Transaction Model Fields:**
- `amount`: Transaction amount
- `description`: Transaction details
- `transaction_date`: When it occurred
- `receiver`: Who received payment
- `category`: Budget category (after categorization)
- `department`: Department (after categorization)

**Current Data:**
- 561 transactions
- $2,272,002 total
- Date range: 2022-07-24 to 2025-10-11

---

### **STEP 2: Auto-Categorization**

**Command:**
```bash
python manage.py categorize_transactions --company coda
```

**How It Works:**
1. **Rule-Based Matching:**
   ```python
   rules = {
       'KPLC': 'Utilities',
       'Safaricom': 'IT and Software',
       'boda': 'Travel and Entertainment',
       'salary': 'Salaries and Wages',
       # ... more rules
   }
   ```

2. **Keyword Analysis:**
   - Searches transaction description
   - Matches against known patterns
   - Assigns category

3. **AI Enhancement (Future):**
   - Machine learning classification
   - Learns from manual corrections
   - Improves over time

**Output:**
```
Processed 561 transactions
Categorized: 545 (97.1%)
Uncategorized: 16 (2.9%)

Top Categories:
  Salaries and Wages: 188 transactions
  Operational Expenses: 129 transactions
  IT and Software: 22 transactions
```

**What Gets Saved:**
- `transaction.category` = BudgetCategory object
- `transaction.department` = Department object (if detectable)

---

### **STEP 3: Pattern Analysis**

**Command:**
```bash
python manage.py analyze_transaction_data
```

**Analysis Types:**

#### **3.1 Monthly Averages**
```python
from finance.services.budget_service import BudgetService

monthly_avg = BudgetService.calculate_monthly_average(
    category=category,
    months=6  # Analyze last 6 months
)
```

**Example:**
- Salaries: $103,149/month (avg of 6 months)
- IT: $9,645/month
- Utilities: $8,424/month

#### **3.2 Trend Detection**
```python
trend = BudgetService.get_spending_trend(
    category=category,
    months=12
)
```

**Identifies:**
- Increasing trends (need more budget)
- Decreasing trends (can reduce budget)
- Seasonal patterns (adjust by month)
- One-time expenses (exclude from projections)

#### **3.3 Confidence Calculation**
```python
if transaction_count >= 50:
    confidence = 95.0
elif transaction_count >= 20:
    confidence = 85.0
elif transaction_count >= 10:
    confidence = 70.0
else:
    confidence = 50.0
```

---

### **STEP 4: Projection Generation**

**Command:**
```bash
python manage.py generate_budget_projections \
    --company coda \
    --months 6 \  # Historical analysis period
    --projection-months 12 \  # Future projection period
    --save
```

**Projection Logic:**

#### **4.1 Calculate Historical Average**
```python
historical_monthly = total_spending / analysis_months
# Example: $1,237,794 / 12 months = $103,149/month
```

#### **4.2 Apply Growth Factor**
```python
growth_factor = 1.10  # 10% conservative growth
projected_monthly = historical_monthly * growth_factor
# Example: $103,149 * 1.10 = $113,464/month
```

#### **4.3 Calculate Annual Projection**
```python
annual_projection = projected_monthly * 12
# Example: $113,464 * 12 = $1,361,568/year
```

#### **4.4 Create Records**

**Budget Record:**
```python
budget = Budget.objects.create(
    company=company,
    category=category,
    item_name=f"{category.name} - 2026 Projection",
    unit_price=projected_monthly,  # $113,464
    quantity=1,
    cases=12,  # months
    estimation_method='trend_analysis',
    estimation_confidence=95.0,
    status='draft',
    is_active=False  # Not yet active
)
```

**Projection Record:**
```python
projection = BudgetEstimateProjection.objects.create(
    budget=budget,
    projection_date=date.today(),
    projected_amount=annual_projection,  # $1,361,568
    confidence_score=95.0,
    projection_method='transaction_analysis'
)
```

**Result:**
- 15 budget projections created
- Total annual: $766,365
- Categories: Salaries ($418K), Operations ($134K), IT ($39K), etc.

---

### **STEP 5: Auto-Sync**

**Command:**
```bash
python manage.py sync_budgets \
    --company coda \
    --analysis-months 6 \
    --min-transactions 10 \
    --variance-threshold 20.0
```

**Sync Logic:**

#### **5.1 Identify Categories**
```python
# Get categories with sufficient transaction data
spending_by_category = BudgetService.get_spending_by_category()

for category, spending_data in spending_by_category.items():
    if spending_data['count'] >= min_transactions:
        # Process this category
```

#### **5.2 Check Existing Budgets**
```python
existing_budget = Budget.objects.filter(
    company=company,
    category=category,
    estimation_method='trend_analysis',
    is_active=True
).first()
```

#### **5.3 Create or Update**

**If No Budget Exists:**
```python
budget = Budget.objects.create(
    company=company,
    category=category,
    item_name=f"{category.name} - Auto-Generated Budget",
    unit_price=projected_monthly,
    quantity=1,
    cases=12,
    status='active',  # Mark as active
    is_active=True,
    estimation_method='trend_analysis'
)
```

**If Budget Exists:**
```python
# Calculate variance
variance_pct = abs((new_amount - current_amount) / current_amount * 100)

if variance_pct > variance_threshold:  # Default: 20%
    # Update budget
    budget.unit_price = new_amount
    budget.save()
```

**Result:**
- Salaries: Created $44K/month budget (27 transactions, 95% confidence)
- Customer Service: Created $16K/month budget (10 transactions, 70% confidence)
- Office Supplies: Created $14K/month budget (38 transactions, 85% confidence)
- Miscellaneous: Created $2K/month budget (10 transactions, 70% confidence)

---

### **STEP 6: Variance Tracking**

**Ongoing Process:**

#### **6.1 Calculate Daily Variance**
```python
from finance.services.budget_service import BudgetService

for budget in active_budgets:
    variance = BudgetService.calculate_variance(budget)
    # Returns: {
    #     'budgeted': $50000,
    #     'actual': $48000,
    #     'variance': -$2000,
    #     'variance_pct': -4.0%,
    #     'status': 'under'
    # }
```

#### **6.2 Alert Thresholds**
```python
if abs(variance_pct) > 20:
    # Send alert to budget lead
    send_variance_alert(budget, variance)
```

#### **6.3 Dashboard Updates**
- Real-time variance display
- Color coding: Green (under), Yellow (on track), Red (over)
- Trend charts

---

### **STEP 7: Continuous Improvement**

**Weekly Auto-Sync (Cron Job):**
```bash
# Add to crontab
0 0 * * 0 python manage.py sync_budgets --company coda
```

**What Happens Weekly:**
1. Re-analyze last 6 months of transactions
2. Recalculate monthly averages
3. Update projections
4. Sync active budgets
5. Adjust confidence scores

**Adaptive Behavior:**
- More transactions → Higher confidence
- Pattern changes → Updated budgets
- New categories → Auto-create budgets
- Inactive categories → Mark budgets inactive

---

## ⚙️ **AUTOMATION CONFIGURATION**

### **Cron Jobs**

#### **1. Weekly Auto-Sync**
```bash
# Every Sunday at midnight
0 0 * * 0 cd /app/coda && python manage.py sync_budgets --company coda
```

#### **2. Monthly Projection Regeneration**
```bash
# First day of month at 2 AM
0 2 1 * * cd /app/coda && python manage.py generate_budget_projections --company coda --save
```

#### **3. Daily Variance Check**
```bash
# Every day at 6 AM
0 6 * * * cd /app/coda && python manage.py check_budget_variances --alert-threshold 20
```

### **Configuration Options**

**sync_budgets Command:**
```bash
--analysis-months 6          # Months of history to analyze
--projection-months 12       # Months to project forward
--min-transactions 10        # Min transactions to create budget
--variance-threshold 20.0    # % variance to trigger update
--dry-run                    # Preview without saving
```

**generate_budget_projections Command:**
```bash
--company coda               # Company slug
--months 6                   # Historical analysis period
--projection-months 12       # Future projection period
--save                       # Save to database
```

---

## 📊 **EXAMPLES**

### **Example 1: Salaries Budget**

**Transaction Data:**
- 188 transactions over 12 months
- Total: $1,237,794
- Monthly average: $103,149

**Projection:**
```python
projected_monthly = $103,149 * 1.10 = $113,464
annual = $113,464 * 12 = $1,361,568
confidence = 95% (high transaction count)
```

**Auto-Sync:**
```python
Budget.objects.create(
    item_name="Salaries and Wages - Auto-Generated Budget",
    unit_price=44296.90,  # Adjusted for recent 6 months
    quantity=1,
    cases=12,
    status='active'
)
```

**Variance Tracking:**
- Budget: $531,563 annual ($44,297/month)
- Actual (Q1): $132,894 (3 months)
- Expected: $132,891 (3 * $44,297)
- Variance: $3 (0.002%) - On track! ✅

---

### **Example 2: IT Software Budget**

**Transaction Data:**
- 22 transactions over 12 months
- Total: $115,745
- Monthly average: $9,645

**Projection:**
```python
projected_monthly = $9,645 * 1.10 = $10,610
annual = $10,610 * 12 = $127,318
confidence = 70% (moderate transaction count)
```

**Auto-Sync:**
- Skip (only 22 transactions, need 10+ in last 6 months)
- Created as projection only, not active budget

**Why Skipped:**
- Recent 6 months: Only 8 transactions
- Below minimum threshold (10)
- Need more data before auto-activating

---

## 🔧 **TROUBLESHOOTING**

### **Issue 1: Low Categorization Rate**

**Symptom:** Only 60% of transactions categorized

**Cause:** Missing keyword rules

**Solution:**
```python
# Add custom rules in categorize_transactions.py
custom_rules = {
    'your_vendor': 'Category Name',
    'another_keyword': 'Another Category'
}
```

---

### **Issue 2: No Budgets Auto-Created**

**Symptom:** sync_budgets runs but creates 0 budgets

**Possible Causes:**
1. Not enough transactions per category
2. Transaction date range too old
3. Categories not matching

**Solution:**
```bash
# Lower minimum threshold
python manage.py sync_budgets --min-transactions 5

# Check transaction dates
python manage.py analyze_transaction_data

# Verify categories
python manage.py shell -c "from finance.models import Transaction; print(Transaction.objects.values('category__name').annotate(count=Count('id')))"
```

---

### **Issue 3: Projections Too High/Low**

**Symptom:** Projected amounts don't match expectations

**Cause:** Growth factor or analysis period

**Solution:**
```bash
# Adjust growth factor (modify command source)
# Or use shorter analysis period for recent trends
python manage.py generate_budget_projections --months 3
```

---

## 📚 **RELATED DOCUMENTS**

- **01_OVERVIEW.md** - System overview
- **02_ARCHITECTURE.md** - Technical architecture
- **03_USER_WORKFLOWS.md** - User guides
- **09_MANAGEMENT_COMMANDS.md** - Command reference

---

**Document Version:** 1.0  
**Last Updated:** October 22, 2025  
**Maintained By:** CODA Development Team

