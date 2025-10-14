# Working with Cursor AI on CODA Project
**Purpose:** Quick start guide for productive AI-assisted development  
**Source:** GETTING_STARTED_PROMPTS.md

---

## 🎯 QUICK CONTEXT

### Project Overview:
- **CODA Budget System** - Django-based data-driven budget management
- **Core Philosophy:** "Transactions are the source of truth"
- **Current Phase:** Phase 3 (User Experience)
- **Data:** $1.49M in transactions, 95.6% categorized

### Key Principles:
1. **Data quality first** - Clean data enables accurate predictions
2. **Incremental improvement** - Phase-by-phase enhancement
3. **User experience matters** - Smart forms prevent bad data at entry

---

## 📋 STANDARD PROMPTS (Copy & Paste)

### 1. FULL CONTEXT PROMPT (Use for ANY task)

```
I'm working on the CODA Budget System (Django app). Please read these files for full context:

1. docs/README.md (Master documentation index)
2. docs/apps/finance/[Feature]/README.md (specific feature)
3. docs/PROJECT_HISTORY_TIMELINE.md (project history)

Key info:
- Data-driven budget system (transactions are source of truth)
- Current status: Phase 3 (User Experience)
- UAT: codamakutano.herokuapp.com
- Production: codatrainingapp.herokuapp.com
- $1.49M in transaction data, 95.6% categorized

What I need help with: [YOUR TASK HERE]
```

### 2. BUG FIX PROMPT

```
I found a bug in CODA. Context:

Read: docs/05_DEPLOYMENT/KNOWN_ISSUES.md

The issue:
- What's happening: [DESCRIBE BEHAVIOR]
- What should happen: [EXPECTED BEHAVIOR]
- Browser console logs: [PASTE LOGS]
- URL where it happens: [URL]

Recent fixes (check for similar patterns):
- Dashboard aggregation (Sum bug - Oct 1)
- Approval fields missing (Oct 13)
- Loan schema mismatch (Oct 13)

Please help debug and fix.
```

### 3. NEW FEATURE PROMPT

```
I want to add a new feature to CODA.

Context:
1. Read: docs/apps/finance/[Feature]/REQUIREMENTS.md
2. Check: Is this already planned in Phase X?
3. Review: docs/COMPREHENSIVE_TESTING_STRATEGY.md

Feature request:
- What: [FEATURE DESCRIPTION]
- Why: [BUSINESS VALUE]
- Where: [WHICH FEATURE/APP]

Please:
1. Check if it exists
2. Suggest implementation approach
3. Identify dependencies
4. Propose testing strategy
```

### 4. DEPLOYMENT PROMPT

```
Ready to deploy to UAT.

Pre-deployment checklist:
1. Read: docs/05_DEPLOYMENT/DEPLOYMENT_READY_SUMMARY.md
2. Run: ./tests/run_tests.sh --regression
3. Check: All tests pass?

Deploy command:
git push heroku 25.10_UAT_DEPLOYMENT_FIX_CM:main --force

Post-deployment:
1. Run: ./tests/test_uat_urls.sh
2. Check: heroku logs --tail --app codamakutano
3. Verify: Critical URLs work

Please guide me through deployment.
```

### 5. TESTING PROMPT

```
Need to test [FEATURE].

Read: docs/apps/finance/[Feature]/TESTING.md

Test scenarios needed:
- Functional tests
- Edge cases
- Integration tests
- Regression tests (if fixing bug)

Please create comprehensive test cases.
```

---

## 🔧 ESSENTIAL FILES TO REFERENCE

### Always Check First:
1. **`docs/README.md`** - Master index, navigation
2. **`docs/PROJECT_HISTORY_TIMELINE.md`** - What's been done
3. **`docs/COMPREHENSIVE_TESTING_STRATEGY.md`** - Testing approach

### For Feature Work:
4. **`docs/apps/finance/[Feature]/README.md`** - Current status
5. **`docs/apps/finance/[Feature]/REQUIREMENTS.md`** - Business rules
6. **`docs/apps/finance/[Feature]/IMPLEMENTATION.md`** - Code details

### For Deployment:
7. **`docs/05_DEPLOYMENT/KNOWN_ISSUES.md`** - Current issues
8. **`docs/05_DEPLOYMENT/DEPLOYMENT_READY_SUMMARY.md`** - Deploy checklist

---

## 💡 TIPS FOR EFFECTIVE AI COLLABORATION

### DO:
- ✅ Reference specific files/sections
- ✅ Provide browser console logs for errors
- ✅ Mention recent related fixes
- ✅ Ask for testing strategy
- ✅ Request documentation updates

### DON'T:
- ❌ Ask vague questions ("fix the budget system")
- ❌ Skip context files
- ❌ Forget to mention the phase we're in
- ❌ Deploy without testing
- ❌ Create new docs without checking existing

---

## 🎯 COMMON TASKS

### Task: Fix a Template Error
```
Template error in [file].html at line [X].

Error: [PASTE ERROR]

Context:
- Recent template fixes: approval fields, loan analytics path
- Check: docs/apps/finance/[Feature]/IMPLEMENTATION.md for correct paths

Please fix and add regression test.
```

### Task: Add a New Model Field
```
Need to add field [field_name] to [Model].

Context:
- Read: docs/apps/finance/[Feature]/IMPLEMENTATION.md (Data Model section)
- Check: Will this break existing code?
- Consider: Migration strategy

Please:
1. Add field to model
2. Create migration
3. Update admin
4. Update forms/views
5. Add to IMPLEMENTATION.md
```

### Task: Improve Performance
```
[Page/Feature] is slow.

Context:
- Read: docs/COMPREHENSIVE_TESTING_STRATEGY.md (Performance Tests)
- Check: Database queries (N+1 problem?)
- Review: Aggregation formulas (use F() expressions!)

Please analyze and optimize.
```

---

## 📊 PROJECT STRUCTURE QUICK REFERENCE

```
/
├── docs/               Documentation
├── tests/              Integration/E2E tests
├── scripts/            Helper scripts
└── coda/               Django project
    ├── finance/        Finance app
    │   └── tests/      Django unit tests
    └── manage.py
```

---

## 🚀 WORKFLOW EXAMPLES

### Example 1: Fixing Budget Approval Bug
```
1. User reports: "Approve button doesn't work"
2. AI reads: docs/apps/finance/Budget/IMPLEMENTATION.md
3. AI checks: Recent fixes (approval fields Oct 13)
4. AI debugs: Browser console, view logic
5. AI fixes: Update view + template
6. AI creates: Regression test
7. AI updates: IMPLEMENTATION.md change history
8. Deploy: Run tests → Deploy → Verify
```

### Example 2: Adding New Feature
```
1. Request: "Add budget vs actuals tracking"
2. AI reads: docs/apps/finance/Budget/REQUIREMENTS.md
3. AI checks: Is this in Phase 3 roadmap? (Yes!)
4. AI plans: Data model, views, templates
5. AI implements: Step by step
6. AI tests: Unit + integration tests
7. AI documents: Update all 4 feature docs
8. Deploy: UAT → Test → Production
```

---

## ⚠️ CRITICAL REMINDERS

### Before Every Deployment:
1. **Run regression tests:** `./tests/run_tests.sh --regression`
2. **Check known issues:** `docs/05_DEPLOYMENT/KNOWN_ISSUES.md`
3. **Review recent fixes:** Might affect your changes

### After Every Bug Fix:
1. **Add regression test** to prevent recurrence
2. **Update IMPLEMENTATION.md** (Change History)
3. **Update TESTING.md** (add test case)
4. **Check for similar bugs** elsewhere

### When Adding Features:
1. **Check REQUIREMENTS.md** - might already be planned
2. **Follow 4-doc standard** - update all 4 docs
3. **Add tests** - unit + integration
4. **Consider Phase** - does it fit current phase?

---

## 📞 GETTING HELP

### If AI Seems Confused:
- Provide more context files
- Reference specific sections
- Mention recent related work
- Share browser console logs

### If Stuck on a Bug:
- Check `docs/05_DEPLOYMENT/KNOWN_ISSUES.md`
- Review similar fixes in IMPLEMENTATION.md
- Look at regression tests for patterns
- Check Heroku logs

### If Unsure About Structure:
- Check `docs/README.md` for navigation
- Review feature README for current status
- See REQUIREMENTS.md for planned features

---

**This guide helps you work efficiently with AI on CODA!**  
**Source:** GETTING_STARTED_PROMPTS.md (archived)  
**Last Updated:** October 13, 2025

