# Budget System - Deployment

**Last Updated:** October 22, 2025  
**Current Version:** Phase 2 Complete (v1746)  
**Purpose:** Deployment procedures, configuration, and post-deployment validation

---

## 🎯 DEPLOYMENT ENVIRONMENTS

| Environment | Branch | Heroku App | URL | Purpose |
|-------------|--------|------------|-----|---------|
| **Local Dev** | Any | N/A | localhost:8000 | Development & testing |
| **UAT** | `25_UAT_CM` | codamakutano | codamakutano.herokuapp.com | Staging & validation |
| **Production** | `25.10_CODA_PROD_v2_CM` | codatrainingapp | codatrainingapp.herokuapp.com | Live system |

---

## ✅ PRE-DEPLOYMENT CHECKLIST

### Code Readiness
- [ ] All regression tests passing (`./tests/run_tests.sh --regression`)
- [ ] Budget-specific tests passing (`python manage.py test finance.tests.test_budget`)
- [ ] No linter errors (`python manage.py check`)
- [ ] Code reviewed and approved
- [ ] Documentation updated (all 7 docs)
- [ ] Change history updated in 04_IMPLEMENTATION.md

### Database Readiness
- [ ] Migrations created (`makemigrations --dry-run` shows nothing)
- [ ] Migrations tested in local dev
- [ ] Migration 0099 (approval fields) confirmed in UAT
- [ ] No data loss expected (migrations are additive)
- [ ] Backup created (production only)

### Configuration Readiness
- [ ] Environment variables set (see below)
- [ ] Budget tier thresholds configured
- [ ] Email settings verified
- [ ] No hardcoded secrets in code
- [ ] Settings file correct for environment

### Integration Readiness
- [ ] Transaction data >95% categorized
- [ ] Budget categories exist and configured
- [ ] Tier classifications run and validated
- [ ] Finance Manager trained on tier controls
- [ ] User notifications configured

---

## 🔧 ENVIRONMENT VARIABLES

### Required for Budget System

**No additional environment variables required!**

Budget system uses standard Django settings and database configuration.

### Optional Configuration

```bash
# If enabling email notifications (future)
EMAIL_HOST='smtp.sendgrid.net'
EMAIL_PORT=587
EMAIL_HOST_USER='apikey'
EMAIL_HOST_PASSWORD='SG.xxxxx'
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL='noreply@codanalytics.net'

# If enabling budget alerts (future)
BUDGET_ALERT_EMAIL='finance@codanalytics.net'
```

---

## 🚀 DEPLOYMENT COMMANDS

### Deploy to UAT (Testing)

```bash
# 1. Ensure on correct branch
git status
# Should show current branch

# 2. Commit all changes
git add -A
git commit -m "Budget: [brief description of changes]"

# 3. Push to GitHub (backup)
git push uat [your-branch-name]

# 4. Deploy to Heroku UAT
git push heroku [your-branch-name]:main

# 5. Monitor deployment
heroku logs --tail --app codamakutano --num 50
# Watch for "Verifying deploy... done."

# 6. Run migrations (if any)
heroku run "cd coda && python manage.py migrate" --app codamakutano

# 7. Verify deployment
curl -I https://codamakutano.herokuapp.com/finance/budget-dashboard/coda/
# Should return: HTTP/1.1 200 OK
```

---

### Deploy to Production (REQUIRES USER PERMISSION! ⚠️)

**NEVER deploy to production without explicit user permission!**

```bash
# ⚠️ ASK USER FIRST: "Ready to deploy budget system to production?"

# If YES, proceed:

# 1. Ensure on production branch
git checkout 25.10_CODA_PROD_v2_CM

# 2. Merge changes (if coming from another branch)
git merge [your-branch-name]
# Resolve any conflicts

# 3. Test locally one more time
python manage.py runserver
# Navigate to budget URLs, test critical paths

# 4. Commit
git add -A
git commit -m "Budget: Production deployment - [description]"

# 5. Push to GitHub
git push production 25.10_CODA_PROD_v2_CM

# 6. Deploy to Heroku Production
git push production 25.10_CODA_PROD_v2_CM:main

# 7. Run migrations
heroku run "cd coda && python manage.py migrate" --app codatrainingapp

# 8. Monitor logs closely
heroku logs --tail --app codatrainingapp --num 100

# 9. Test immediately
curl -I https://codatrainingapp.herokuapp.com/finance/budget-dashboard/coda/

# 10. Monitor for 1 hour minimum
# Watch for errors, performance issues, user feedback
```

---

## ✅ POST-DEPLOYMENT VERIFICATION

### Automated Checks

```bash
# 1. Test critical budget URLs
curl -I https://codamakutano.herokuapp.com/finance/budget-dashboard/coda/
# Expected: HTTP/1.1 200 OK

curl -I https://codamakutano.herokuapp.com/finance/budget/coda/approvals/
# Expected: HTTP/1.1 200 OK (with authentication)

# 2. Check migrations applied
heroku run "cd coda && python manage.py showmigrations finance" --app codamakutano
# Look for [X] on 0099_add_approval_fields

# 3. Verify database integrity
heroku run "cd coda && python manage.py shell" --app codamakutano
# >>> from finance.models import BudgetRequest
# >>> BudgetRequest.objects.first().approved_by
# Should work without AttributeError

# 4. Check for errors in logs
heroku logs --app codamakutano --tail | grep -i "error\|fail\|exception"
# Should be minimal or zero errors

# 5. Verify data quality
heroku run "cd coda && python manage.py analyze_transaction_data" --app codamakutano
# Expected: 97%+ categorization rate
```

---

### Manual Verification

**For UAT:**
1. [ ] Login to https://codamakutano.herokuapp.com
2. [ ] Navigate to `/finance/budget-dashboard/coda/`
3. [ ] Verify dashboard loads (<2 seconds)
4. [ ] Check Overview tab shows real transaction data
5. [ ] Navigate to `/finance/budget/coda/approvals/`
6. [ ] Verify approval dashboard loads
7. [ ] Create test budget request
8. [ ] Approve test request (as staff user)
9. [ ] Verify approval recorded (approved_by, approved_at set)
10. [ ] Check theme switcher works (Navy/Gold ↔ Purple)
11. [ ] Test on mobile device (responsive design)
12. [ ] Check for JavaScript errors (F12 → Console)

**For Production:**
- Same checklist as UAT
- Extra caution: Real users, real data
- Test with real user accounts
- Verify existing data not affected

---

## 🔄 ROLLBACK PROCEDURE

### If Deployment Fails

```bash
# 1. Check recent releases
heroku releases --app codamakutano

# Output example:
# v905  Deploy abc123  yourname@email.com  2025/10/13 15:32:00 +0000
# v904  Deploy def456  yourname@email.com  2025/10/13 14:15:00 +0000

# 2. Rollback to previous working version
heroku rollback v904 --app codamakutano

# 3. Verify rollback successful
curl -I https://codamakutano.herokuapp.com/finance/budget-dashboard/coda/
# Should return 200 OK

# 4. Check logs
heroku logs --app codamakutano --tail
# Verify no errors

# 5. Test critical paths
# Login, navigate to budget pages, verify working
```

---

### If Database Migration Fails

```bash
# 1. Check migration status
heroku run "cd coda && python manage.py showmigrations finance" --app codamakutano

# 2. If partially applied, check which step failed
heroku logs --app codamakutano --tail | grep migration

# 3. Options:
#    a) Fix migration locally, redeploy
#    b) Fake migration if safe: 
#       heroku run "cd coda && python manage.py migrate finance 0099 --fake" --app codamakutano
#    c) Rollback app (migrations auto-rollback with code)

# 4. Worst case: Restore from backup (production only)
# Contact Heroku support for database restore
```

---

## ⚙️ CONFIGURATION BY ENVIRONMENT

### Local Development

**Settings File:** `coda/coda_project/coda_settings/local_settings.py`

```python
DEBUG = True

# Database: SQLite or local PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Budget Configuration
BUDGET_AUTO_APPROVE_THRESHOLD = 1000
BUDGET_TIER_A_MAX = 5000
BUDGET_TIER_B_MAX = 10000
BUDGET_VARIANCE_THRESHOLD = 20  # Default variance %

# Email: Console backend (prints to console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

**Environment Variable:**
```bash
set ENVIRONMENT=local  # Windows
export ENVIRONMENT=local  # Mac/Linux
```

---

### UAT (Staging)

**Settings File:** `coda/coda_project/coda_settings/heroku_settings.py`

```python
DEBUG = False
ALLOWED_HOSTS = [
    'codamakutano.herokuapp.com',
    'www.codanalytics.net',
    'localhost',
]

# Database: Heroku PostgreSQL (auto-configured)
# Uses DATABASE_URL from Heroku

# Budget Configuration (same as local)
BUDGET_AUTO_APPROVE_THRESHOLD = 1000
BUDGET_TIER_A_MAX = 5000
BUDGET_TIER_B_MAX = 10000
BUDGET_VARIANCE_THRESHOLD = 20

# Email: SendGrid or console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # For now
```

**Heroku Config:**
```bash
heroku config:set ENVIRONMENT=staging --app codamakutano
heroku config:set DEBUG=False --app codamakutano
```

---

### Production

**Settings File:** `coda/coda_project/coda_settings/prod_settings.py`

```python
DEBUG = False
ALLOWED_HOSTS = [
    'codatrainingapp.herokuapp.com',
    'www.codanalytics.net',
    'codanalytics.net',
]

# Budget Configuration (same as UAT)
BUDGET_AUTO_APPROVE_THRESHOLD = 1000
BUDGET_TIER_A_MAX = 5000
BUDGET_TIER_B_MAX = 10000
BUDGET_VARIANCE_THRESHOLD = 20

# Email: SendGrid (production)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.sendgrid.net'
# Other email settings from environment variables
```

**Heroku Config:**
```bash
heroku config:set ENVIRONMENT=production --app codatrainingapp
heroku config:set DEBUG=False --app codatrainingapp
```

---

## 📊 MONITORING POST-DEPLOYMENT

### First Hour (Critical Window)

```bash
# Monitor logs continuously
heroku logs --tail --app codamakutano

# Watch for:
# - Any ERROR or EXCEPTION messages
# - 500/404 status codes
# - Database query errors
# - Template rendering issues
```

**Key Metrics:**
- Error rate (target: <1%)
- Response time (target: <2s)
- Database connection count
- Memory usage

---

### First 24 Hours

**Monitor:**
- [ ] User feedback (any complaints?)
- [ ] Error logs (any new errors?)
- [ ] Performance metrics (slow queries?)
- [ ] Data integrity (approvals working correctly?)
- [ ] Email delivery (if enabled)

**Test Critical Paths:**
- [ ] Budget dashboard loads
- [ ] Approval dashboard loads
- [ ] Can create budget request
- [ ] Can approve budget request
- [ ] Data displays correctly

---

### First Week

**Track:**
- Usage patterns (how many approvals?)
- User adoption (who's using it?)
- Feature usage (which tabs most used?)
- Performance trends
- Bug reports

**Gather Feedback:**
- Survey approvers (satisfaction?)
- Survey requesters (easy to use?)
- Finance Manager (automation working?)
- IT team (any issues?)

---

## 🔄 DEPLOYMENT HISTORY

| Date | Version | Environment | Changes | Status | Notes |
|------|---------|-------------|---------|--------|-------|
| Oct 22, 2025 | v1750 | UAT | 7-doc migration | 🔄 Pending | Documentation restructure |
| Oct 16, 2025 | v1746 | Production | Phase 2 complete | ✅ Success | Tier system deployed |
| Oct 16, 2025 | v1745 | UAT | Tier management UI | ✅ Success | Finance Manager dashboard |
| Oct 15, 2025 | v1742 | UAT | Tier classification | ✅ Success | Added tier fields |
| Oct 13, 2025 | v904 | UAT | Approval fields added | ✅ Success | Migration 0099 |
| Oct 2, 2025 | v895 | UAT | Dashboard aggregation fix | ✅ Success | Fixed 177x inflation bug |
| Oct 1, 2025 | v890 | UAT | Initial budget system | ✅ Success | Phase 1 launch |

---

## 📋 DEPLOYMENT PROCEDURES

### Standard UAT Deployment

```bash
# === STEP 1: PRE-DEPLOYMENT ===
# Run tests locally
cd coda
python manage.py test finance.tests.test_budget
./tests/run_tests.sh --regression

# Check for pending migrations
python manage.py makemigrations --dry-run
# Should output: "No changes detected"

# === STEP 2: COMMIT & PUSH ===
git add -A
git commit -m "Budget: [clear description]"
git push uat [branch-name]

# === STEP 3: DEPLOY TO HEROKU ===
git push heroku [branch-name]:main

# === STEP 4: POST-DEPLOYMENT ===
# Monitor logs
heroku logs --tail --app codamakutano

# Run migrations (if any)
heroku run "cd coda && python manage.py migrate" --app codamakutano

# Collect static files (if changed CSS/JS)
heroku run "cd coda && python manage.py collectstatic --noinput" --app codamakutano

# === STEP 5: VERIFICATION ===
# Test critical URLs
curl -I https://codamakutano.herokuapp.com/finance/budget-dashboard/coda/
curl -I https://codamakutano.herokuapp.com/finance/budget/coda/approvals/

# Check database state
heroku run "cd coda && python manage.py analyze_transaction_data" --app codamakutano

# === STEP 6: MANUAL TESTING ===
# Run Test 1-6 from 05_TESTING.md
# Verify:
# - Dashboard loads
# - Approvals work
# - Theme switcher works
# - No JavaScript errors

# === STEP 7: NOTIFY ===
# If major change, notify users via email/Slack
```

---

### Production Deployment (CRITICAL - REQUIRES PERMISSION!)

**⚠️ NEVER deploy to production without explicit user permission!**

```bash
# === PREREQUISITES ===
# 1. Thoroughly tested in UAT (minimum 24 hours)
# 2. User has approved deployment
# 3. No known critical bugs
# 4. Database backup created
# 5. Rollback plan prepared
# 6. Deployment time agreed (low-traffic window)

# === ASK USER ===
# "The budget system has been tested in UAT for 24+ hours.
#  All tests passing. Ready to deploy to production?"

# === IF YES, PROCEED ===

# STEP 1: Checkout production branch
git checkout 25.10_CODA_PROD_v2_CM

# STEP 2: Merge changes (if needed)
git merge [your-feature-branch]
# Resolve any conflicts carefully

# STEP 3: Final local test
python manage.py runserver
# Test budget URLs one more time

# STEP 4: Commit
git add -A
git commit -m "Budget: Production deployment - [description]"

# STEP 5: Push to GitHub
git push production 25.10_CODA_PROD_v2_CM

# STEP 6: Deploy to Heroku Production
git push production 25.10_CODA_PROD_v2_CM:main

# STEP 7: Run migrations (if any)
heroku run "cd coda && python manage.py migrate" --app codatrainingapp

# STEP 8: Monitor logs CLOSELY
heroku logs --tail --app codatrainingapp --num 100
# Watch for any errors

# STEP 9: Verify immediately
curl -I https://codatrainingapp.herokuapp.com/finance/budget-dashboard/coda/
# Must return: HTTP/1.1 200 OK

# STEP 10: Test critical paths
# Login to production
# Test budget creation
# Test approval workflow
# Verify data integrity

# STEP 11: Monitor for 1 hour
# Stay available to rollback if needed
# Watch logs, error rates, user feedback

# STEP 12: All-clear notification
# If no issues after 1 hour, notify team: "Deployment successful"
```

---

## 🗂️ MIGRATION PROCEDURES

### Migration 0099: Add Approval Fields

**File:** `coda/finance/migrations/0099_add_approval_fields_to_budget_request.py`  
**Created:** October 13, 2025  
**Purpose:** Add approval audit trail fields to BudgetRequest model

**Fields Added:**
- `approved_by` (ForeignKey to User)
- `approved_at` (DateTimeField)
- `rejected_by` (ForeignKey to User)
- `rejected_at` (DateTimeField)
- `current_approver` (ForeignKey to User)
- `approval_chain` (JSONField)

**Risks:** None (all fields nullable, backward compatible)

**Rollback:** Not needed (additive change only)

**Applied:**
- ✅ UAT: October 13, 2025 (v904)
- ✅ Production: October 16, 2025 (v1746)

---

### Migration 0002: Budget Category Tier Fields (Phase 2)

**File:** `coda/finance/migrations/0002_budgetcategory_tier_fields.py`  
**Created:** October 15, 2025  
**Purpose:** Add tier classification fields for data-driven approval

**Fields Added:**
- `approval_tier` (CharField: A/B/C)
- `auto_approve_enabled` (BooleanField)
- `typical_monthly_amount` (DecimalField)
- `variance_threshold` (DecimalField)
- `is_recurring` (BooleanField)
- `last_pattern_analysis` (DateTimeField)

**Risks:** None (all fields nullable/have defaults)

**Post-Migration:** Run `classify_budget_category_tiers --analyze --save`

**Applied:**
- ✅ UAT: October 15, 2025
- ✅ Production: October 16, 2025

---

## 🎯 ENVIRONMENT-SPECIFIC CONFIGURATION

### Local Development Setup

```bash
# 1. Clone repository
git clone https://github.com/yourusername/coda.git
cd coda/stg/coda

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# 3. Install dependencies
pip install -r ../requirements.txt

# 4. Set environment variable
export ENVIRONMENT=local

# 5. Run migrations
python manage.py migrate

# 6. Create superuser
python manage.py createsuperuser

# 7. Setup budget categories
python manage.py setup_budget_categories

# 8. Load sample data (optional)
python manage.py loaddata budget_sample_data.json

# 9. Run server
python manage.py runserver

# 10. Access budget system
# Navigate to: http://localhost:8000/finance/budget-dashboard/coda/
```

---

### UAT Configuration

**Required Heroku Config Vars:**
```bash
heroku config:set ENVIRONMENT=staging --app codamakutano
heroku config:set DEBUG=False --app codamakutano
heroku config:set ALLOWED_HOSTS=codamakutano.herokuapp.com,www.codanalytics.net --app codamakutano
```

**Database:**
- Heroku PostgreSQL (auto-configured via DATABASE_URL)
- Current plan: Hobby Dev (10K rows free)
- Can upgrade if needed

**Addons:**
```bash
heroku addons --app codamakutano
# Expected: heroku-postgresql:hobby-dev
```

---

### Production Configuration

**Required Heroku Config Vars:**
```bash
heroku config:set ENVIRONMENT=production --app codatrainingapp
heroku config:set DEBUG=False --app codatrainingapp
heroku config:set ALLOWED_HOSTS=codatrainingapp.herokuapp.com,www.codanalytics.net,codanalytics.net --app codatrainingapp
```

**Database Backup:**
```bash
# Create backup before major deployment
heroku pg:backups:capture --app codatrainingapp

# List backups
heroku pg:backups --app codatrainingapp

# Restore if needed
heroku pg:backups:restore [backup-id] --app codatrainingapp
```

---

## 🛡️ DEPLOYMENT SAFETY MEASURES

### Before Production Deployment

1. **UAT Testing Period:** Minimum 24 hours
2. **User Acceptance:** Finance Manager approval required
3. **Backup Created:** Database backup verified
4. **Rollback Plan:** Documented and tested
5. **Low-Traffic Window:** Deploy during off-peak hours
6. **Team Availability:** On-call engineer available for 1 hour post-deployment

### During Production Deployment

1. **Monitor Actively:** Watch logs in real-time
2. **Test Immediately:** Verify critical paths within 5 minutes
3. **User Communication:** Notify users of deployment
4. **Quick Rollback:** Ready to rollback within 2 minutes if issues
5. **Incident Response:** PagerDuty alert configured

### After Production Deployment

1. **1 Hour Monitoring:** Active log monitoring
2. **Smoke Testing:** Test all critical workflows
3. **Error Analysis:** Check for any new errors
4. **Performance Check:** Verify response times acceptable
5. **User Feedback:** Gather initial reactions
6. **All-Clear:** Notify team after monitoring period

---

## 📊 DEPLOYMENT SUCCESS CRITERIA

### UAT Deployment Success:
- ✅ Slug size <100M (lean deployment)
- ✅ Build time <3 minutes
- ✅ No errors in logs
- ✅ All URLs return 200 OK
- ✅ Migrations applied successfully
- ✅ Test suite passes
- ✅ Manual testing complete

### Production Deployment Success:
- ✅ All UAT criteria met
- ✅ No user complaints within 1 hour
- ✅ Error rate <0.5%
- ✅ Response time <2s (p95)
- ✅ Data integrity verified
- ✅ Rollback not needed
- ✅ Finance Manager approves

---

## 🚨 EMERGENCY PROCEDURES

### If Production is Down

```bash
# 1. Immediate rollback
heroku rollback v[PREVIOUS_VERSION] --app codatrainingapp

# 2. Verify service restored
curl -I https://codatrainingapp.herokuapp.com/

# 3. Investigate root cause
heroku logs --app codatrainingapp --num 500 > incident.log

# 4. Fix locally
# Debug, fix, test thoroughly

# 5. Redeploy when ready
# Follow standard production deployment procedure
```

### If Data Corruption Detected

```bash
# 1. Stop all writes (maintenance mode)
# 2. Assess damage
heroku run "cd coda && python manage.py shell" --app codatrainingapp

# 3. Restore from backup
heroku pg:backups:restore [backup-id] --app codatrainingapp

# 4. Replay transactions if needed
# 5. Verify data integrity
# 6. Resume normal operations
```

---

## 📝 POST-DEPLOYMENT CHECKLIST

### Immediately After Deployment
- [ ] Verify homepage loads
- [ ] Test budget dashboard URL
- [ ] Test approval dashboard URL
- [ ] Check for 500 errors in logs
- [ ] Verify database migrations applied
- [ ] Test one approval action
- [ ] Check theme switcher

### Within 1 Hour
- [ ] Monitor error rate
- [ ] Check response times
- [ ] Test all tabs (Overview, Approvals, etc.)
- [ ] Verify data accuracy (spot check)
- [ ] Check memory/CPU usage
- [ ] Test mobile view

### Within 24 Hours
- [ ] Gather user feedback
- [ ] Review full error logs
- [ ] Performance analysis
- [ ] Data integrity audit
- [ ] Document any issues
- [ ] Update MAINTENANCE.md if needed

### Within 1 Week
- [ ] User satisfaction survey
- [ ] Performance trends analysis
- [ ] Plan any fixes needed
- [ ] Update deployment history (this doc)
- [ ] Team retrospective

---

## 🎓 DEPLOYMENT LESSONS LEARNED

### Lesson 1: Test Migrations Thoroughly
- Migration 0099 initially missed in schema sync
- Caused production AttributeError
- **Fix:** Always run `showmigrations` before and after deployment
- **Prevention:** Add to deployment checklist

### Lesson 2: Dashboard Aggregation Pattern
- Wrong aggregation formula caused 177x inflation
- **Fix:** Always use `F()` expressions: `Sum(F('qty') * F('price'))`
- **Prevention:** Documented in CURSOR_AI_GUIDE, added regression test

### Lesson 3: Environment Variable Awareness
- ENVIRONMENT variable must match settings.py logic
- UAT had 'testing' but settings.py expected 'staging'
- **Fix:** Set `ENVIRONMENT=staging` for UAT
- **Prevention:** Document in deployment guide

### Lesson 4: ALLOWED_HOSTS Critical
- Production blocked access due to missing Heroku URL
- **Fix:** Add 'codatrainingapp.herokuapp.com' to ALLOWED_HOSTS
- **Prevention:** Validate ALLOWED_HOSTS during deployment

### Lesson 5: User Permission for Production
- Never deploy to production without asking user
- Even small changes can have big impact
- **Rule:** Always get explicit permission

---

## 🔗 RELATED DOCUMENTATION

**See Also:**
- `01_ANALYSIS.md` - Why we built this system
- `02_REQUIREMENTS.md` - What it should do
- `03_ARCHITECTURE.md` - How it's designed
- `04_IMPLEMENTATION.md` - Code details
- `05_TESTING.md` - Test procedures
- `06_MAINTENANCE.md` - Known issues and troubleshooting

**External:**
- `docs/01_GETTING_STARTED/CURSOR_AI_GUIDE.md` - AI development guide
- `docs/05_DEPLOYMENT/KNOWN_ISSUES.md` - Project-wide issues
- `docs/03_PROJECT_MANAGEMENT/PROJECT_HISTORY_TIMELINE.md` - Project history

---

**Document Owner:** DevOps Team + Development Team  
**Last Deployment:** October 16, 2025 (Phase 2 Complete)  
**Next Planned Deployment:** Phase 3 (Q1 2026)  
**Update This Doc:** After every production deployment


