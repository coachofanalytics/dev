# Production Budget System - Quick Start Guide

**Environment:** Production Database (codatrainingapp)  
**Date:** October 20, 2025  
**Status:** Ready to Begin

---

## 🚀 Step 1: Run Discovery (Start Here!)

```bash
cd /Users/coda/PROJECTS/CODA/DEVELOPMENT/DEV
./run_production_discovery.sh
```

This will tell you:
- ✅ What data already exists in production
- ✅ What's missing
- ✅ Where to start based on your current state

**Expected Output:**
```
=== PRODUCTION DATABASE STATE ===
Companies: X
Departments: X
Budget Items: X
Categories: X
Transactions: X
...
=== RECOMMENDATIONS ===
🎯 START: Phase X - ...
```

---

## 📋 Phases Overview (Based on Discovery Results)

### **Scenario A: Fresh Start (No Categories)**
```
Phase 1 → Phase 3 → Phase 4 → Phase 5
(Create   (Manual   (Approval  (Monitor
 Setup)    Budget)   Workflow)  & Track)
```

**Timeline:** 4-6 weeks  
**Approach:** Manual budget creation, then track actual vs budget

---

### **Scenario B: Have Transaction Data**
```
Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5
(Create   (Analyze  (AI-Gen    (Approval  (Monitor
 Setup)    Data)     Budget)    Workflow)  & Track)
```

**Timeline:** 6-8 weeks  
**Approach:** Data-driven budget creation using AI projections

---

### **Scenario C: Have Existing Budgets**
```
Phase 4 → Phase 5 → Phase 6
(Approval  (Monitor   (Optimize
 Workflow)  & Track)   & Improve)
```

**Timeline:** 2-4 weeks  
**Approach:** Enhance existing budget system

---

## 🎯 Phase 1: Foundation Setup

### IF Discovery shows: "Categories: 0"

**Action: Create Budget Categories**

```bash
# Method 1: Use management command (if it exists)
heroku run "cd coda && python manage.py setup_budget_categories" --app codatrainingapp

# Method 2: Load from fixture
heroku run "cd coda && python manage.py loaddata budget_categories" --app codatrainingapp

# Method 3: Create via Django shell (manual)
heroku run "cd coda && python manage.py shell" --app codatrainingapp
```

**Categories to Create (14 standard):**
1. Salaries and Wages
2. Utilities
3. IT & Software
4. Office Supplies
5. Travel
6. Training and Development
7. Rent
8. Maintenance and Repairs
9. Insurance
10. Taxes
11. Marketing & Communications
12. Professional Services
13. Program Costs
14. Miscellaneous

**Time:** 1-2 hours  
**Deliverable:** Categories and subcategories loaded

---

## 💰 Phase 2: Transaction Data Analysis

### IF Discovery shows: "Transactions: 100+"

**Action: Analyze Historical Spending**

```bash
# Full analysis
heroku run "cd coda && python manage.py analyze_transaction_data" --app codatrainingapp

# This will show:
# - Total transaction volume and value
# - Spending by category
# - Spending by department
# - Top vendors
# - Monthly trends
# - Data quality metrics
```

**Time:** 30 minutes  
**Deliverable:** Transaction analysis report

**Then: Auto-Categorize**

```bash
# Dry run first (see what would be categorized)
heroku run "cd coda && python manage.py categorize_transactions --dry-run" --app codatrainingapp

# Apply categorization
heroku run "cd coda && python manage.py categorize_transactions --auto-assign" --app codatrainingapp
```

**Target:** 95%+ categorization rate  
**Time:** 15 minutes  
**Deliverable:** Clean, categorized transaction data

---

## 📊 Phase 3: Budget Creation

### Option A: AI-Generated Budget (If you have 6+ months of transaction data)

```bash
# Generate budget projections from transaction data
heroku run "cd coda && python manage.py generate_budget_projections --months 12 --save" --app codatrainingapp
```

**This will:**
- Analyze spending patterns by category
- Calculate monthly averages
- Account for seasonality
- Generate budget recommendations

**Time:** 30 minutes  
**Deliverable:** Draft FY 2025 budget based on historical data

### Option B: Manual Budget Creation

**Via Web Interface:**
1. Go to: https://codatrainingapp.herokuapp.com/finance/budget-dashboard/coda/
2. Click "Create Budget Item"
3. Fill in:
   - Department
   - Category
   - Item name
   - Quantity
   - Unit price
   - Date range

**Time:** 2-4 hours (depending on detail level)  
**Deliverable:** Manual FY 2025 budget

---

## ✅ Phase 4: Approval Workflow

### Configure Approval Tiers

**Based on your transaction analysis, set thresholds:**

```python
# Example tiers (adjust based on your data)
Tier 1: $0 - $1,000      → Auto-approve (or Department Head)
Tier 2: $1,001 - $5,000  → Department Head
Tier 3: $5,001 - $20,000 → Department + Finance Manager
Tier 4: $20,000+         → Department + Finance + CEO
```

**Setup:**
```bash
heroku run "cd coda && python manage.py shell" --app codatrainingapp
# Then create ApprovalPolicy objects
```

**Time:** 1-2 hours  
**Deliverable:** Approval policies configured

---

## 📈 Phase 5: Monitoring & Tracking

### Enable Real-Time Budget Monitoring

**Access Dashboard:**
https://codatrainingapp.herokuapp.com/finance/budget-dashboard/coda/

**What You'll See:**
- Budget vs Actual by Category
- Spending trends
- Variance alerts
- Drill-down views
- Forecasts

**Setup Alerts:**
- Email notifications for overbudget categories
- Weekly summary reports
- Monthly executive dashboard

**Time:** 1 hour setup  
**Deliverable:** Monitoring dashboard active

---

## 🎯 Recommended Starting Sequence

### **Day 1: Discovery**
1. ✅ Run `./run_production_discovery.sh`
2. ✅ Review output
3. ✅ Determine starting phase
4. ✅ Document current state

### **Week 1: Foundation**
- [ ] Create/verify categories (Phase 1.1)
- [ ] Verify departments (Phase 1.2)
- [ ] Set fiscal year (Phase 1.3)

### **Week 2: Data (If applicable)**
- [ ] Analyze transactions (Phase 2.1)
- [ ] Categorize transactions (Phase 2.2)
- [ ] Clean vendor data (Phase 2.3)

### **Week 3-4: Budget Creation**
- [ ] Generate AI projections OR create manually (Phase 3)
- [ ] Review and adjust budget
- [ ] Get executive approval

### **Week 5: Approvals**
- [ ] Configure approval policies (Phase 4.1)
- [ ] Test approval workflow (Phase 4.2)
- [ ] Train users

### **Week 6+: Live Operation**
- [ ] Enable monitoring (Phase 5)
- [ ] Track budget vs actual
- [ ] Generate reports
- [ ] Optimize and improve

---

## 📝 Decision Tree

```
START
  │
  ├─ Run Discovery Script
  │
  ├─ Do categories exist?
  │  ├─ NO → Create categories (Phase 1.1)
  │  └─ YES → Continue
  │
  ├─ Do transactions exist? (100+)
  │  ├─ YES → Analyze data (Phase 2)
  │  │        └─ Generate AI budget (Phase 3.1)
  │  └─ NO  → Create manual budget (Phase 3.2)
  │
  ├─ Does budget exist?
  │  ├─ YES → Configure approvals (Phase 4)
  │  └─ NO  → See above
  │
  └─ Enable monitoring (Phase 5)
```

---

## 🛠️ Management Commands Cheat Sheet

```bash
# Discovery & Analysis
heroku run "cd coda && python manage.py analyze_transaction_data" --app codatrainingapp
heroku run "cd coda && python manage.py verify_data_quality" --app codatrainingapp

# Data Cleanup
heroku run "cd coda && python manage.py categorize_transactions --auto-assign" --app codatrainingapp

# Budget Generation
heroku run "cd coda && python manage.py generate_budget_projections --months 12 --save" --app codatrainingapp

# Category Setup
heroku run "cd coda && python manage.py setup_budget_categories" --app codatrainingapp

# Database Inspection
heroku run "cd coda && python manage.py dbshell" --app codatrainingapp
```

---

## 📊 Expected Outcomes by Phase

### After Phase 1:
- ✅ 14 budget categories created
- ✅ 50+ subcategories created
- ✅ Departments configured
- ✅ Fiscal periods defined

### After Phase 2 (if applicable):
- ✅ 95%+ transactions categorized
- ✅ Spending patterns analyzed
- ✅ Vendor list cleaned
- ✅ Historical baseline established

### After Phase 3:
- ✅ FY 2025 budget created
- ✅ Budget approved by leadership
- ✅ Budget allocated by department/category
- ✅ Dashboard showing budget data

### After Phase 4:
- ✅ Approval workflow active
- ✅ Budget requests flowing
- ✅ Email notifications working
- ✅ Audit trail functional

### After Phase 5:
- ✅ Real-time monitoring live
- ✅ Budget vs actual tracking
- ✅ Variance alerts active
- ✅ Reports being generated

---

## 🚨 Common Issues & Solutions

### Issue: "Table doesn't exist"
**Solution:** Run migrations
```bash
heroku run "cd coda && python manage.py migrate finance" --app codatrainingapp
```

### Issue: "No categories found"
**Solution:** Load categories
```bash
heroku run "cd coda && python manage.py setup_budget_categories" --app codatrainingapp
```

### Issue: "Permission denied"
**Solution:** Check user has finance access
```bash
# In Django shell
user.groups.add(Group.objects.get(name='Finance'))
```

### Issue: "Budget dashboard empty"
**Solution:** Create budget items or check filters

---

## 📞 Support Resources

**Documentation:**
- Full Roadmap: `PRODUCTION_BUDGET_IMPLEMENTATION_ROADMAP.md`
- Technical Docs: `docs/apps/finance/Budget/IMPLEMENTATION.md`
- Testing Guide: `docs/apps/finance/Budget/TESTING.md`

**Management Commands:**
- Location: `coda/finance/management/commands/`
- Available commands listed in roadmap

**URLs:**
- Dashboard: `/finance/budget-dashboard/coda/`
- Analytics: `/finance/analytics/`
- Requests: `/finance/budget-requests/coda/`

---

## ✅ Checklist Before Starting

- [ ] Production database backup created
- [ ] Heroku CLI authenticated (`heroku auth:whoami`)
- [ ] Discovery script ran successfully
- [ ] Current state documented
- [ ] Starting phase identified
- [ ] Stakeholders notified
- [ ] Rollback plan ready

---

## 🎯 TODAY'S ACTION ITEMS

1. **Run Discovery** (5 min)
   ```bash
   ./run_production_discovery.sh
   ```

2. **Review Output** (10 min)
   - Note what exists
   - Identify gaps
   - Determine starting phase

3. **Share Results** (5 min)
   - Copy output to chat
   - We'll create specific action plan

4. **Execute Phase 1.1** (If needed)
   - Create categories
   - Set up reference data

---

**Ready to begin?** Run the discovery script and share the results! 🎯

