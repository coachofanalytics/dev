# Finance App Documentation
**Last Updated:** October 13, 2025  
**App Location:** `coda/finance/`

---

## 📚 DOCUMENTATION INDEX

### 🚀 **START HERE:**
1. **[BUDGET_APPROVAL_SYSTEM.md](BUDGET_APPROVAL_SYSTEM.md)** ⭐
   - Complete reference for budget approval workflow
   - Current status, business requirements, technical implementation
   - Testing guide, known issues, next steps
   - **Read this first for approval system questions!**

### 📋 **PLANNING (Future Implementation):**
Located in: `planning/`

2. **[PHASE2_DATA_DRIVEN_APPROVAL_PLAN.md](planning/PHASE2_DATA_DRIVEN_APPROVAL_PLAN.md)**
   - 7-day plan to implement intelligent approval routing
   - Based on production transaction data analysis
   - Includes database export, analysis, and implementation steps

3. **[APPROVAL_WORKFLOW_BUSINESS_ANALYSIS.md](planning/APPROVAL_WORKFLOW_BUSINESS_ANALYSIS.md)**
   - Business decision framework
   - Different approval approaches compared
   - Helps choose right solution for business needs

4. **[BUDGET_CATEGORY_CLASSIFICATION.md](planning/BUDGET_CATEGORY_CLASSIFICATION.md)**
   - All 25 budget categories classified into 3 tiers
   - Tier A: Auto-approve (9 categories)
   - Tier B: Priority-based (9 categories)
   - Tier C: Strategic assessment (7 categories)

5. **[CODA_APPROVAL_BUSINESS_REQUIREMENTS.md](planning/CODA_APPROVAL_BUSINESS_REQUIREMENTS.md)**
   - Detailed business requirements captured from user
   - Automation principles
   - Finance Manager controls spec

### ✨ **FEATURES:**
Located in: `features/`

6. **[THEME_SWITCHER.md](features/THEME_SWITCHER.md)**
   - Dashboard theme switcher feature
   - Navy & Gold vs Purple themes
   - How to use, how it works, how to customize

### 📊 **EXISTING DOCS:**
7. **[BUDGET_WORKFLOW_IMPLEMENTATION_COMPLETE.md](BUDGET_WORKFLOW_IMPLEMENTATION_COMPLETE.md)**
   - Original budget workflow implementation
   - Phase 1 & 2 completion notes

8. **[TRANSACTION_MODEL_MIGRATION_PLAN.md](TRANSACTION_MODEL_MIGRATION_PLAN.md)**
   - Transaction model evolution plan
   - Field changes and migration strategy

9. **[TESTING_GUIDE.md](TESTING_GUIDE.md)**
   - Finance app testing scenarios
   - Test data setup

---

## 🗂️ DIRECTORY STRUCTURE

```
coda/docs/apps/finance/
├── README.md                              ← You are here
├── BUDGET_APPROVAL_SYSTEM.md             ⭐ Main reference
├── BUDGET_WORKFLOW_IMPLEMENTATION_COMPLETE.md
├── TRANSACTION_MODEL_MIGRATION_PLAN.md
├── TESTING_GUIDE.md
│
├── planning/                              📋 Future implementation
│   ├── PHASE2_DATA_DRIVEN_APPROVAL_PLAN.md
│   ├── APPROVAL_WORKFLOW_BUSINESS_ANALYSIS.md
│   ├── BUDGET_CATEGORY_CLASSIFICATION.md
│   └── CODA_APPROVAL_BUSINESS_REQUIREMENTS.md
│
├── features/                              ✨ Feature documentation
│   └── THEME_SWITCHER.md
│
├── Budgeting/                            📊 Budget subsystem
│   └── README.md
│
├── Loan System/                          💰 Loan subsystem
│
└── Payment System/                       💳 Payment subsystem
```

---

## 🎯 DOCUMENTATION STANDARDS

### When to Update:
- **Bug Fix:** Update `BUDGET_APPROVAL_SYSTEM.md` → Known Issues section
- **Feature Add:** Create doc in `features/`, reference in main README
- **Planning:** Add to `planning/` directory
- **Deployment:** Update `/coda/docs/05_DEPLOYMENT/`

### What NOT to Do:
- ❌ Create random .md files in project root
- ❌ Duplicate information across files
- ❌ Create session-specific docs (use archive instead)

### One Document Per:
- **System/Feature** (Budget Approval, Theme Switcher)
- **Major Plan** (Phase 2 Implementation)
- **Deployment Session** (One summary per deployment)

---

## 🔍 QUICK NAVIGATION

**Need to...**

**Understand approval system?**  
→ Read: `BUDGET_APPROVAL_SYSTEM.md`

**Plan Phase 2 implementation?**  
→ Read: `planning/PHASE2_DATA_DRIVEN_APPROVAL_PLAN.md`

**Know current issues?**  
→ Read: `/coda/docs/05_DEPLOYMENT/KNOWN_ISSUES.md`

**Learn about theme switcher?**  
→ Read: `features/THEME_SWITCHER.md`

**See what got deployed?**  
→ Read: `/coda/docs/05_DEPLOYMENT/OCT13_SESSION_SUMMARY.md`

**Understand business requirements?**  
→ Read: `planning/CODA_APPROVAL_BUSINESS_REQUIREMENTS.md`

---

## 📊 FINANCE APP OVERVIEW

### Main Features:
1. **Budget Management**
   - Unified dashboard
   - Category drill-down
   - Request/approval workflow (NEW)
   - Projections & analytics

2. **Transaction Management**
   - Smart entry with AI predictions
   - Cascading dropdowns
   - Categorization
   - Historical analysis

3. **Loan System**
   - Loan applications
   - Eligibility checking
   - Approval workflow
   - Analytics

4. **Payment System**
   - Multiple payment methods
   - Payment tracking
   - (Currently disabled - missing _deprecated module)

### Current Focus:
**Budget Approval Automation** - Moving from manual to intelligent automated approvals

---

## 🎯 MAINTENANCE

### Regular Updates Needed:
- **BUDGET_APPROVAL_SYSTEM.md** - After any approval logic changes
- **KNOWN_ISSUES.md** - As bugs are fixed/discovered
- **Deployment summaries** - After each deployment
- **This README** - When structure changes

### Monthly Review:
- Consolidate session notes
- Archive outdated docs
- Update status in main docs
- Check links still valid

---

## 💡 PHILOSOPHY

**One Source of Truth Per Topic**
- Don't scatter information
- Consolidate, don't duplicate
- Make docs easy to find and update
- Quality over quantity

**Living Documentation**
- Update as you go
- Keep current
- Archive old versions
- Link related docs

---

**Questions?** Start with `BUDGET_APPROVAL_SYSTEM.md` - it has everything! 📖

