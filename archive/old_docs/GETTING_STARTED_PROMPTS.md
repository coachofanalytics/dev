# CURSOR AI - GETTING STARTED PROMPTS
**Quick Start Guide for New Chat Sessions**

---

## 🎯 **PURPOSE**

Use these prompts at the start of **every new Cursor chat** to give the AI full context instantly. This prevents repetition and gets you productive immediately.

---

## 📋 **STANDARD PROMPTS** (Copy & Paste)

### 1. **FULL CONTEXT PROMPT** (Use this for ANY task)

```
I'm working on the CODA Budget System (Django app). Please read these files for full context:

1. /Users/coda/PROJECTS/CODA/DEVELOPMENT/DEV/coda/docs/apps/finance/Budgeting/MASTER_REFERENCE.md
2. /Users/coda/PROJECTS/CODA/DEVELOPMENT/DEV/coda/docs/apps/finance/Budgeting/CURRENT_STATE_AND_ROADMAP.md

Key info:
- This is a data-driven budget system
- Transactions are the source of truth
- We just fixed a 177x dashboard inflation bug
- Currently in Phase 3: User drill-down views
- UAT environment: codamakutano.herokuapp.com
- Main files: finance/views_unified_budget.py, forms_improved.py

What I need help with: [YOUR TASK HERE]
```

### 2. **BUG FIX PROMPT**

```
I found a bug in the CODA Budget System. Context:

Read: /Users/coda/PROJECTS/CODA/DEVELOPMENT/DEV/coda/docs/apps/finance/Budgeting/MASTER_REFERENCE.md (Section: DEBUGGING GUIDE)

The issue:
- What's happening: [DESCRIBE BEHAVIOR]
- What should happen: [EXPECTED BEHAVIOR]
- Browser console logs: [PASTE LOGS]
- URL where it happens: [URL]

Recent fixes we've done:
- Dashboard aggregation (Sum bug)
- Admin 404 (model registration)
- Form fields (subcategory/type widgets)

Please help me debug and fix this.
```

### 3. **NEW FEATURE PROMPT**

```
I want to add a new feature to CODA Budget System.

Context files:
1. MASTER_REFERENCE.md - See "DEVELOPMENT WORKFLOW" section
2. CURRENT_STATE_AND_ROADMAP.md - See what's already done

Feature request: [DESCRIBE FEATURE]

System architecture:
- Transactions → AI Service → Budget → Dashboard
- We use: Django ORM, jQuery, AJAX APIs
- Current phase: Phase 3 (drill-down views)

Please:
1. Check if similar feature exists
2. Suggest implementation approach
3. Identify files to modify
4. Consider data model changes
```

### 4. **DEPLOYMENT PROMPT**

```
I need to deploy changes to UAT (codamakutano.herokuapp.com).

Read: MASTER_REFERENCE.md (Section: DEPLOYMENT)

Changes made:
- [LIST YOUR CHANGES]

Please:
1. Review changes for deployment readiness
2. Suggest commit message
3. Provide deployment command
4. List post-deployment tests
5. Generate test URLs for UAT verification
```

### 5. **DATA ANALYSIS PROMPT**

```
I need to analyze transaction/budget data in CODA system.

Context: Read MASTER_REFERENCE.md (Section: DATA ANALYSIS INSIGHTS)

Current data state:
- 366 transactions ($1.49M historical)
- 95.6% categorized
- 266 active budgets

What I need:
- [DESCRIBE ANALYSIS NEEDED]

Relevant commands:
- analyze_transaction_data
- generate_budget_projections
- categorize_transactions
```

---

## 🔧 **TASK-SPECIFIC PROMPTS**

### Smart Form Issues:

```
Smart transaction form issue. 

Read: MASTER_REFERENCE.md (Sections: "Smart Transaction Form" + "DEBUGGING GUIDE")

Current behavior: [DESCRIBE]
Console logs: [PASTE F12 CONSOLE OUTPUT]

Form URL: /finance/transaction/smart-entry/
APIs involved: /finance/api/predict-all/, /finance/api/subcategories/

Help me fix this.
```

### Budget Dashboard Issues:

```
Budget dashboard showing incorrect data.

Read: MASTER_REFERENCE.md (Section: "CRITICAL FIXES IMPLEMENTED")

Issue: [DESCRIBE]
Dashboard URL: /finance/budget-dashboard/coda/

Note: We recently fixed the 177x inflation bug (Sum aggregation). 
Check if this is related or a new issue.
```

### Category/Model Issues:

```
Issue with categories/database models.

Read: MASTER_REFERENCE.md (Section: "DATABASE SCHEMA")

Problem: [DESCRIBE]

Models involved: [Transaction / Budget / BudgetCategory / BudgetSubCategory]

Do I need a migration? Data migration? Model change?
```

---

## 💡 **ADVANCED PROMPTS**

### Architecture Review:

```
I want to understand/review the CODA Budget System architecture.

Please read and summarize:
1. MASTER_REFERENCE.md (Section: SYSTEM ARCHITECTURE)
2. Current file structure in coda/finance/

Focus on: [SPECIFIC AREA]

Questions:
- [YOUR QUESTIONS]
```

### Performance Optimization:

```
Dashboard/form is slow. Need performance optimization.

Context: MASTER_REFERENCE.md (Section: SYSTEM ARCHITECTURE)

Slow operation: [DESCRIBE WHAT'S SLOW]
Load time: [SECONDS]
URL: [URL]

Current optimizations:
- Select_related for foreign keys
- Caching in AIPredictionCache
- Shared static files (budget-common.css/js)

What else can we do?
```

### Code Review:

```
Please review my changes before deployment.

Files changed:
- [LIST FILES]

Changes summary:
- [DESCRIBE CHANGES]

Check against: MASTER_REFERENCE.md (Section: DEVELOPMENT WORKFLOW)

Verify:
1. Follows existing patterns
2. No breaking changes
3. Backward compatible
4. Properly tested
```

---

## 🎓 **EXPLANATION PROMPTS**

### "Explain How This Works":

```
Explain how [FEATURE] works in CODA Budget System.

Reference: MASTER_REFERENCE.md

Feature: [Auto-categorization / Smart Form / Dashboard / Budget Projections]

Please explain:
1. Data flow
2. Key files involved
3. How to test it
4. Common issues
```

### "Teach Me the Codebase":

```
I'm new to CODA Budget System. Teach me the codebase.

Start with: MASTER_REFERENCE.md (Section: QUICK CONTEXT)

Teach me:
1. Overall architecture (10,000 ft view)
2. Key models and relationships
3. Important views and URLs
4. Recent changes and why
5. Current priorities (Phase 3)

Then quiz me to check understanding.
```

---

## 🚨 **EMERGENCY PROMPTS**

### Production Down:

```
URGENT: Production issue in budget system.

Error: [ERROR MESSAGE]
URL: [URL]
Impact: [WHO'S AFFECTED]

Recent deployments: [CHECK GIT LOG]

Read: MASTER_REFERENCE.md (Section: DEBUGGING GUIDE)

Need immediate:
1. Root cause analysis
2. Quick fix or rollback plan
3. Verification steps
```

### Data Issue:

```
URGENT: Data integrity issue.

Problem: [DESCRIBE DATA PROBLEM]
Affected records: [HOW MANY]
Discovered: [WHEN/HOW]

Context: MASTER_REFERENCE.md (Section: DATA ANALYSIS INSIGHTS)

Need:
1. Assess impact
2. Data recovery plan
3. Prevention measures
4. Migration script if needed
```

---

## 📝 **DOCUMENTATION PROMPTS**

### Update Docs:

```
I made changes that need documentation updates.

Changes:
- [LIST CHANGES]

Please update:
1. MASTER_REFERENCE.md (if technical change)
2. CURRENT_STATE_AND_ROADMAP.md (if feature complete)

Maintain existing format and style.
```

### Create User Guide:

```
Create user-facing documentation for [FEATURE].

Technical reference: MASTER_REFERENCE.md

Create guide for:
- Non-technical users
- Step-by-step instructions
- Screenshots placeholders
- Common questions

Audience: [Finance team / Managers / Data entry staff]
```

---

## 🔍 **RESEARCH PROMPTS**

### Find Similar Code:

```
Find existing code that does [FUNCTIONALITY].

Search in:
- coda/finance/
- Look for similar patterns

I want to: [DESCRIBE WHAT YOU NEED]

Don't reinvent the wheel - show me what exists that I can reuse or extend.
```

### Best Practice Check:

```
Is this the right approach for [TASK]?

My plan: [DESCRIBE APPROACH]

Check against:
- MASTER_REFERENCE.md (DEVELOPMENT WORKFLOW)
- Existing patterns in codebase
- Django best practices

Suggest alternatives if there's a better way.
```

---

## 💬 **COMMUNICATION PROMPTS**

### Generate Commit Message:

```
Generate git commit message for these changes:

Files changed: [LIST]
What changed: [SUMMARY]
Why: [REASON]
Impact: [WHAT IT FIXES/ADDS]

Follow format:
[CATEGORY]: Brief description

DETAILS:
- Change 1
- Change 2

IMPACT:
- What users will see

TESTING:
- How to verify
```

### Create Deployment Summary:

```
Create deployment summary for stakeholders.

Changes deployed:
- [LIST CHANGES]

Environment: UAT / Production
Date: [DATE]
Version: [GIT COMMIT/HEROKU VERSION]

Format for:
- Non-technical audience
- Highlight business impact
- Include test results
- Note any required actions
```

---

## 🎯 **QUICK TIPS**

### Always Include:
1. ✅ Path to MASTER_REFERENCE.md
2. ✅ What you're trying to do
3. ✅ What you've tried
4. ✅ Error messages (if any)
5. ✅ Console logs (for UI issues)

### Never Assume:
- ❌ AI remembers previous chats
- ❌ AI knows recent changes
- ❌ AI has current file versions

### Do Provide:
- ✅ File paths
- ✅ URLs where issues occur
- ✅ Console/server logs
- ✅ Expected vs actual behavior

---

## 📚 **REFERENCE FILES**

Always available for context:

1. **MASTER_REFERENCE.md** - Complete technical documentation
2. **CURRENT_STATE_AND_ROADMAP.md** - What's done, what's next
3. **DEPLOYMENT_GUIDE.md** - How to deploy safely
4. **.cursorrules** - AI behavior rules

Location: `/Users/coda/PROJECTS/CODA/DEVELOPMENT/DEV/coda/docs/apps/finance/Budgeting/`

---

## 🎬 **EXAMPLE SESSION**

**Good Start:**
```
Working on CODA Budget System. Read MASTER_REFERENCE.md for context.

Task: Fix subcategory dropdown not populating when category changes.

What I see:
- Category dropdown works
- Category change doesn't trigger subcategory load
- Console shows "CATEGORY CHANGE EVENT TRIGGERED" but no API call
- URL: /finance/transaction/smart-entry/

Already checked:
- API endpoint works: /finance/api/subcategories/?category_id=1 returns data
- jQuery is loaded (version 3.6.0)
- Field IDs are correct (#id_category, #id_subcategory)

Browser console logs: [PASTE LOGS]

Help me debug the JavaScript event handler.
```

**Bad Start:**
```
The dropdown doesn't work. Fix it.
```

**Why Bad?**
- No context about which dropdown
- No file/URL reference
- No error messages
- No indication of what was tried
- AI has to ask 10 questions before helping

---

## ✅ **CHECKLIST: Starting New Chat**

Before asking for help:

- [ ] Started chat with context prompt (copy from above)
- [ ] Referenced MASTER_REFERENCE.md
- [ ] Described what I'm trying to do
- [ ] Included relevant error messages
- [ ] Pasted console logs (for UI issues)
- [ ] Listed what I've already tried
- [ ] Specified files/URLs involved

**With this checklist, AI can help you 10x faster!**

---

**Save this file. Reference it every time you start a new Cursor chat.**  
**It will save you hours of repeated explanations.**

*Last Updated: October 2, 2025*  
*Part of CODA Budget System Documentation*

