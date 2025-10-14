# Production Deployment Strategy - Incremental Cherry-Pick Approach
**Created:** October 12, 2025  
**Branch Comparison:** `25.10_CODA_DEV_CM` → `production/main`

## Overview

**Current Status:**
- **Development Branch:** `25.10_CODA_DEV_CM` (182 commits ahead of production)
- **Staging Branch:** `25.10_CODA_STAGING_CM` (created today, pushed to GitHub)
- **UAT Environment:** codamakutano.herokuapp.com (v884, deployed Oct 7, 2025)
- **Production Environment:** codatrainingapp.herokuapp.com (v1726, deployed Oct 9, 2025)
- **Production Branch:** `production/main`

**Key Changes in Development:**
- 416 files changed in `coda/` directory
- 83,259 insertions, 14,792 deletions
- Major focus: Budget workflow, smart forms, approval system, unified dashboard

---

## Phase 1: Critical Budget Workflow Changes 🔴 HIGH PRIORITY

These changes are essential for the budget management system to function properly.

### Group 1A: Transaction Model Fixes (Foundation)
**Commits to cherry-pick (in order):**
```bash
# 1. Base model alignment
4f20ce4f - Fix Transaction model user field database mismatch
1314b2cc - COMPREHENSIVE DATABASE SCHEMA FIX: Align Transact
025-10-12T21:13:45.685891+00:00 app[web.1]: File "/app/.heroku/python/lib/python3.12/site-packages/django/core/handlers/exception.py", line 47, in inner

9ffec113 - FINAL FIX: Replace user field with sender/receiver in Transaction model
2361408e - ULTIMATE FIX: Correct receiver field type in Transaction model
82307842 - Fix select_related error: Remove receiver from select_related
5f37b10b - FIX THE REAL ISSUE: Use subcategory.id instead of subcategory object

# 2. Schema alignment
ec6c6bee - COMPREHENSIVE DATABASE SCHEMA ALIGNMENT: Fix Transaction model to match actual database
55c364e5 - FINAL SCHEMA FIX: Use CharField for all ID fields to match database
f6879cb5 - REMOVE NON-EXISTENT FIELDS: Remove processed_date and other missing fields
afd02d0a - CLEAN TRANSACTION MODEL: Remove all non-existent fields
f5557394 - FINAL SCHEMA ALIGNMENT: Remove created_at and updated_at fields

# 3. Apply migration
2dd46700 - MIGRATE TO PRODUCTION TRANSACTION MODEL: Proper ForeignKey relationships
```

**Deployment Steps:**
```bash
# Create production deployment branch
git checkout production/main
git pull production main
git checkout -b 25.10_CODA_PROD_TRANSACTION_FIX_CM

# Cherry-pick transaction model fixes
git cherry-pick 4f20ce4f 1314b2cc 9ffec113 2361408e 82307842 5f37b10b ec6c6bee 55c364e5 f6879cb5 afd02d0a f5557394 2dd46700

# Test locally
cd coda && python manage.py makemigrations
cd coda && python manage.py migrate --dry-run

# Deploy to production
git push production 25.10_CODA_PROD_TRANSACTION_FIX_CM:main

# Verify
heroku run "cd coda && python manage.py showmigrations finance" --app codatrainingapp
```

**Testing Checklist:**
- [ ] Transaction admin loads without errors
- [ ] Transaction list displays correctly
- [ ] Finance dashboard shows accurate data
- [ ] No database field errors in logs

---

### Group 1B: Forms and Admin Updates
**Commits to cherry-pick:**
```bash
94d936cf - FIX TRANSACTIONADMIN: Update all fields to match production model
ea02954c - FIX FORMS + DOCUMENT TESTING GAP: Update SmartTransactionForm for new model
```

**Deployment Steps:**
```bash
git checkout production/main
git checkout -b 25.10_CODA_PROD_FORMS_FIX_CM
git cherry-pick 94d936cf ea02954c

# Test locally
cd coda && python manage.py check
python test_budget_workflow.py

# Deploy
git push production 25.10_CODA_PROD_FORMS_FIX_CM:main
```

**Testing Checklist:**
- [ ] Transaction form loads correctly
- [ ] Form validation works
- [ ] Admin interface functional
- [ ] Smart form API responds

---

### Group 1C: Budget Display and Calculations
**Commits to cherry-pick:**
```bash
201adb3c - FIX BUDGET CALCULATIONS + ADD EDIT BUTTONS: Show correct amounts and enable editing
63ce028a - ADD BUDGET ITEMS TABLE: Show individual budget items with Edit buttons
ca48b410 - FIX TEMPLATE SYNTAX ERROR: Remove invalid 'mul' filter
7a3d249f - FIX BUDGET DETAIL PAGE: Correct URL name and budget assignment
ba686fbe - FIX CURRENCY DISPLAY AND EDIT URL: KES amounts and correct URL pattern
```

**Deployment Steps:**
```bash
git checkout production/main
git checkout -b 25.10_CODA_PROD_BUDGET_DISPLAY_CM
git cherry-pick 201adb3c 63ce028a ca48b410 7a3d249f ba686fbe

# Test locally - verify dashboard
curl http://localhost:8000/finance/budget-dashboard/coda/

# Deploy
git push production 25.10_CODA_PROD_BUDGET_DISPLAY_CM:main

# Verify production
curl https://codatrainingapp.herokuapp.com/finance/budget-dashboard/coda/
```

**Testing Checklist:**
- [ ] Budget dashboard displays correct amounts
- [ ] No 177x inflation issue
- [ ] Currency displays as KES
- [ ] Edit buttons functional
- [ ] Budget detail page loads

---

### Group 1D: Budget Editing Functionality
**Commits to cherry-pick:**
```bash
21a3dd02 - FIX BUDGET EDIT FIELD ERROR: Correct Transaction model field references
a09cd96d - CREATE BUDGET ITEM EDIT TEMPLATE: Complete budget edit functionality
d245f6ed - FIX BUDGET SAVE ERROR: Remove manual estimated_amount input
75fdf631 - FIX TIMEZONE WARNINGS: Proper datetime handling for budget dates
```

**Deployment Steps:**
```bash
git checkout production/main
git checkout -b 25.10_CODA_PROD_BUDGET_EDIT_CM
git cherry-pick 21a3dd02 a09cd96d d245f6ed 75fdf631

# Deploy
git push production 25.10_CODA_PROD_BUDGET_EDIT_CM:main
```

**Testing Checklist:**
- [ ] Budget edit page loads
- [ ] Can save budget changes
- [ ] No timezone warnings
- [ ] estimated_amount calculates correctly

---

## Phase 2: Budget Approval Workflow 🟡 MEDIUM PRIORITY

### Group 2A: Complete Approval System
**Commits to cherry-pick:**
```bash
ac55d8b5 - IMPLEMENT COMPLETE BUDGET REQUEST & APPROVAL WORKFLOW
d6861729 - FIX BUDGET REQUEST FORM & APPROVAL DASHBOARD ERRORS
b499dade - FIX: Correct template path for approval dashboard
```

**Files Affected:**
- `coda/finance/views/budget/approvals.py`
- `coda/finance/services/smart_approval_service.py`
- `coda/finance/views/api/smart_form_api.py`
- `coda/finance/templates/finance/budget_request_form.html`
- `coda/finance/templates/finance/budgets/budget_request_detail.html`
- `coda/finance/templates/finance/budgets/budget_requests_list.html`

**Deployment Steps:**
```bash
git checkout production/main
git checkout -b 25.10_CODA_PROD_APPROVAL_WORKFLOW_CM
git cherry-pick ac55d8b5 d6861729 b499dade

# Test approval workflow
cd coda && python manage.py test finance.tests.test_approval_workflow

# Deploy
git push production 25.10_CODA_PROD_APPROVAL_WORKFLOW_CM:main
```

**Testing Checklist:**
- [ ] Budget request form loads
- [ ] Can submit budget request
- [ ] Approval dashboard shows pending requests
- [ ] Can approve/reject requests
- [ ] Email notifications sent
- [ ] Status updates correctly

---

## Phase 3: Enhanced Features 🟢 LOW PRIORITY

### Group 3A: Email Templates
**New Files:**
- `coda/templates/emails/approval_required.html`
- `coda/templates/emails/approval_decision.html`
- `coda/templates/emails/budget_request_submitted.html`
- `coda/templates/emails/disbursement_completed.html`
- `coda/templates/emails/disbursement_failed.html`
- `coda/templates/emails/escalation_notification.html`
- `coda/templates/emails/otp_verification.html`
- `coda/templates/emails/base_email.html`

**Deployment:** Cherry-pick commits that add these templates (bundle with approval workflow)

### Group 3B: Unified Dashboard Enhancements
**Files:**
- `coda/unified_dashboard/views.py` (264 changes)
- `coda/unified_dashboard/templates/` (multiple new files)

**Deployment:** Test thoroughly in UAT before production

### Group 3C: Documentation Updates
**Note:** Already organized in staging branch `25.10_CODA_STAGING_CM`
- Deployment documentation moved to `coda/docs/05_DEPLOYMENT/`
- Testing guides consolidated
- Can be deployed anytime (low risk)

---

## Recommended Deployment Sequence

### Week 1: Foundation (Critical)
**Day 1-2:** Group 1A - Transaction Model Fixes
**Day 3:** Group 1B - Forms and Admin Updates  
**Day 4:** Group 1C - Budget Display and Calculations  
**Day 5:** Group 1D - Budget Editing Functionality

### Week 2: Core Features
**Day 1-3:** Group 2A - Complete Approval System
**Day 4-5:** Testing and bug fixes

### Week 3: Enhancements
**Day 1-2:** Email templates and notifications
**Day 3-5:** Unified dashboard enhancements

---

## Cherry-Pick Command Reference

### Basic Cherry-Pick
```bash
git cherry-pick <commit-hash>
```

### Cherry-Pick Multiple Commits
```bash
git cherry-pick <commit1> <commit2> <commit3>
```

### Cherry-Pick Range
```bash
git cherry-pick <start-commit>..<end-commit>
```

### Handle Conflicts
```bash
# If conflict occurs
git status
# Edit conflicting files
git add <resolved-files>
git cherry-pick --continue

# Or abort
git cherry-pick --abort
```

### Skip a Commit
```bash
git cherry-pick --skip
```

---

## Testing Strategy

### Before Each Deployment:
1. **Local Testing**
   ```bash
   cd coda
   python manage.py check
   python manage.py test finance
   python test_budget_workflow.py
   ```

2. **Database Migration Check**
   ```bash
   cd coda
   python manage.py makemigrations --dry-run
   python manage.py migrate --dry-run
   ```

3. **Linter Check**
   ```bash
   flake8 coda/finance/ --exclude=migrations
   ```

### After Each Deployment:
1. **Verify URLs**
   ```bash
   heroku run "cd coda && python manage.py show_urls | grep finance" --app codatrainingapp
   ```

2. **Check Logs**
   ```bash
   heroku logs --tail --app codatrainingapp
   ```

3. **Test Critical Paths**
   - Login → Dashboard → Budget List → Budget Detail
   - Create Transaction → View Transaction
   - Submit Budget Request → View Approval Dashboard

4. **Database Check**
   ```bash
   heroku run "cd coda && python manage.py dbshell --command='SELECT COUNT(*) FROM finance_transaction;'" --app codatrainingapp
   ```

---

## Rollback Plan

### If Deployment Fails:
```bash
# Check current release
heroku releases --app codatrainingapp

# Rollback to previous version
heroku rollback v1726 --app codatrainingapp

# Or rollback one version
heroku rollback --app codatrainingapp
```

### Emergency Hotfix:
```bash
# Create hotfix branch from production
git checkout production/main
git checkout -b hotfix/critical-fix

# Make fix, commit, deploy
git push production hotfix/critical-fix:main
```

---

## Branch Management

### Current Branches:
- `25.10_CODA_DEV_CM` - Active development (182 commits ahead)
- `25.10_CODA_STAGING_CM` - Staged for deployment (pushed to GitHub)
- `production/main` - Current production baseline
- `master` - Legacy (not used)

### Naming Convention for Production Deployment:
```
25.10_CODA_PROD_<FEATURE>_CM
```

Examples:
- `25.10_CODA_PROD_TRANSACTION_FIX_CM`
- `25.10_CODA_PROD_BUDGET_DISPLAY_CM`
- `25.10_CODA_PROD_APPROVAL_WORKFLOW_CM`

### Keep Staging Updated:
```bash
# After each production deployment
git checkout 25.10_CODA_STAGING_CM
git merge production/main
git push uat 25.10_CODA_STAGING_CM
```

---

## Communication and Documentation

### Before Each Deployment:
- [ ] Review commit changes
- [ ] Check MASTER_REFERENCE.md for related documentation
- [ ] Update CURRENT_STATE_AND_ROADMAP.md
- [ ] Notify users of maintenance window (if needed)

### After Each Deployment:
- [ ] Update version in deployment log
- [ ] Document any issues encountered
- [ ] Update CURRENT_STATE_AND_ROADMAP.md with new status
- [ ] Notify users of new features

---

## Monitoring Post-Deployment

### Key Metrics to Watch:
1. **Error Rate:** Check Heroku logs for 500 errors
2. **Response Time:** Monitor dashboard load times
3. **Database Performance:** Check query times
4. **User Activity:** Monitor login/transaction creation rates

### Heroku Monitoring Commands:
```bash
# Check app status
heroku ps --app codatrainingapp

# Monitor logs
heroku logs --tail --source app --app codatrainingapp

# Check dyno metrics
heroku metrics --app codatrainingapp

# Database size
heroku pg:info --app codatrainingapp
```

---

## Risk Assessment

### High Risk (Test Thoroughly):
- ⚠️ Transaction model changes (affects all finance data)
- ⚠️ Budget calculations (impacts financial reporting)
- ⚠️ Database migrations (cannot be easily rolled back)

### Medium Risk (Test in UAT First):
- ⚠️ Approval workflow (new functionality)
- ⚠️ Form changes (user interaction)
- ⚠️ Template updates (UI changes)

### Low Risk (Can Deploy Quickly):
- ✅ Documentation updates
- ✅ Email templates (only used when triggered)
- ✅ CSS/styling changes
- ✅ Static file updates

---

## Success Criteria

### Phase 1 Success:
- [ ] No 500 errors in production logs
- [ ] Budget dashboard shows correct amounts
- [ ] Transaction admin functional
- [ ] All database queries execute successfully
- [ ] Users can view and edit budgets

### Phase 2 Success:
- [ ] Budget requests can be submitted
- [ ] Approval dashboard loads
- [ ] Approvers can approve/reject
- [ ] Email notifications sent
- [ ] Workflow status updates correctly

### Phase 3 Success:
- [ ] Enhanced dashboard features working
- [ ] All email templates render correctly
- [ ] Documentation accessible
- [ ] System performance maintained

---

## Contact and Escalation

**If Issues Arise:**
1. Check Heroku logs immediately
2. Review error in LOCAL_TESTING_GUIDE.md debugging section
3. Check MASTER_REFERENCE.md troubleshooting
4. Rollback if critical
5. Document issue for future reference

**Deployment Lead:** Coach of Analytics (coachofanalytics@gmail.com)

---

*Last Updated: October 12, 2025*  
*Version: 1.0*  
*Status: Ready for Implementation*

