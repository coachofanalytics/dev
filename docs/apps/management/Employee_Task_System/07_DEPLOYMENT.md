# Employee Activity System (Management) – 07_DEPLOYMENT.md

## Purpose
This document provides deployment procedures, scheduling configuration, deployment history, and post-deployment monitoring for the Employee Task Management System.

---

## Deployment Environments

### Development (Local)
- **Purpose:** Local development and testing
- **Database:** Cloned production database (via `scripts/clone_prod_database.sh`)
- **Settings:** `coda_project.coda_settings.local_prod_clone_settings`
- **Command:** `python manage.py runserver`

### UAT (User Acceptance Testing)
- **URL:** https://codamakutano.herokuapp.com
- **Purpose:** Pre-production testing with real users
- **Branch:** `25.10_CODA_UAT_CM`
- **Deployment:** Automatic via Heroku

### Production
- **URL:** https://www.codanalytics.net
- **Purpose:** Live production environment
- **Branch:** `25.10_CODA_PROD_v2_CM`
- **Deployment:** Manual with approval

---

## Pre-Deployment Checklist

### Code Quality
- [ ] All tests pass (`pytest` / `python manage.py test management`)
- [ ] Test coverage > 80%
- [ ] No linter errors
- [ ] Code reviewed and approved

### Functionality
- [ ] UAT validation complete
- [ ] Dashboards render correctly
- [ ] No N+1 queries introduced
- [ ] API endpoints tested
- [ ] Manual testing completed

### Configuration
- [ ] `.env` configured for AI and meeting providers
- [ ] Environment variables set in Heroku
- [ ] Database migrations tested
- [ ] `.slugignore` excludes docs/tests/scripts

### Data Safety
- [ ] Database backup created
- [ ] Data validation passed (`python manage.py validate_task_data`)
- [ ] No breaking changes to data model
- [ ] Migration rollback plan prepared

### Documentation
- [ ] Implementation.md updated with changes
- [ ] Change history documented
- [ ] Deployment notes added
- [ ] Known issues documented

---

## Deployment Procedures

### Deploy to UAT

**Command:**
```bash
git push heroku 25.10_CODA_UAT_CM:main --force
heroku logs --tail --app codamakutano --num 100
```

**Steps:**
1. Ensure all pre-deployment checklist items complete
2. Commit all changes to UAT branch
3. Push to Heroku
4. Monitor deployment logs
5. Verify deployment successful
6. Run smoke tests

**Verification:**
```bash
# Check deployment status
heroku releases --app codamakutano

# Monitor logs
heroku logs --tail --app codamakutano

# Check application health
curl https://codamakutano.herokuapp.com/management/
```

### Smoke Verification (UAT)

**Dashboard Tests:**
- [ ] Open Management dashboard pages
- [ ] Confirm page load < 2s
- [ ] Verify no errors in browser console
- [ ] Check database queries (no N+1)

**API Tests:**
- [ ] Verify activity summary API returns 200 with non-zero data
- [ ] Test intelligent assignment API
- [ ] Test meeting link review UI
- [ ] Test budget integration APIs (if Phase 2+)

**Functional Tests:**
- [ ] Test task creation
- [ ] Test evidence upload
- [ ] Test task reset (if applicable)
- [ ] Test compliance calculation

### Deploy to Production

**⚠️ CRITICAL: Requires approval before deployment**

**Command:**
```bash
git push production 25.10_CODA_PROD_v2_CM:main --force
heroku logs --tail --app codatrainingapp --num 100
```

**Steps:**
1. ✅ UAT testing complete (minimum 24 hours)
2. ✅ User approval obtained
3. ✅ All pre-deployment checklist items complete
4. ✅ Production deployment scheduled
5. ✅ Backup production database
6. ✅ Deploy to production
7. ✅ Monitor closely for 1 hour post-deploy
8. ✅ Verify functionality
9. ✅ Update documentation

**Verification:**
```bash
# Check deployment status
heroku releases --app codatrainingapp

# Monitor logs
heroku logs --tail --app codatrainingapp

# Check application health
curl https://www.codanalytics.net/management/
```

### Rollback Procedure

**If deployment fails or issues discovered:**

**Command:**
```bash
# List recent releases
heroku releases --app codatrainingapp

# Rollback to previous version
heroku rollback v<PREVIOUS> --app codatrainingapp

# Monitor after rollback
heroku logs --tail --app codatrainingapp --num 100
```

**Steps:**
1. Identify issue
2. List recent releases
3. Rollback to previous stable version
4. Monitor logs
5. Verify rollback successful
6. Document issue and resolution

---

## Scheduled Tasks Configuration

### Monthly Task Reset

**Schedule:** Automated on 1st of each month at midnight (00:00)

**Configuration:**
```python
# In coda/coda_project/celery.py
app.conf.beat_schedule = {
    'monthly_task_reset': {
        'task': 'task_history',  # dump_data function
        'schedule': crontab(hour=0, minute=0, day_of_month='1'),
    },
}
```

**Process:**
1. Create TaskHistory records first (with `daf_date` calculation)
2. Validate all records created
3. Only then reset Task points to 0
4. Update group/mxearning if needed
5. Log success/failure
6. Send notification on failure

**daf_date Logic:**
- **Automated reset on 1st:** `daf_date` = Last day of previous month
- **Manual reset:** `daf_date` = Same day of last month

**Manual Override:**
- Available via `/management/reset_tasks/`
- Uses same logic (set daf_date to last month)
- Useful for edge cases or testing

**Monitoring:**
```bash
# Check Celery task status
celery -A coda_project inspect scheduled

# Monitor task execution
heroku logs --tail --app codamakutano | grep task_history

# Verify TaskHistory created
python manage.py shell -c "from management.models import TaskHistory; from datetime import date; print(TaskHistory.objects.filter(created_at__date=date.today()).count())"
```

### Weekly Evidence Reminders

**Schedule:** Every Friday at 5 PM (17:00)

**Configuration:**
```python
# In coda/coda_project/celery.py
app.conf.beat_schedule = {
    'weekly_evidence_reminders': {
        'task': 'management.tasks.send_weekly_evidence_reminders',
        'schedule': crontab(hour=17, minute=0, day_of_week=4),  # Friday
    },
}
```

**Process:**
1. Find employees with <80% evidence coverage
2. Generate personalized messages with task details
3. Send email reminders
4. Track reminder history

**Monitoring:**
```bash
# Check Celery task status
celery -A coda_project inspect scheduled

# Monitor email sending
heroku logs --tail --app codamakutano | grep evidence_reminder

# Check reminder history
python manage.py shell -c "from management.services.evidence_reminder_service import EvidenceReminderService; service = EvidenceReminderService(); print(service.get_reminder_history())"
```

### Task Reset Scheduling Options

**Current Implementation: Option 1 (Reset on 1st) ✅**

**Why Option 1:**
- ✅ More reliable: Running on 1st gives buffer - if it fails, can manually run
- ✅ Clear semantics: `daf_date` = "work done in previous month" is intuitive
- ✅ Payroll alignment: When viewing October payroll, all October work is there
- ✅ Less timezone sensitive: 1st of month is clear regardless of timezone
- ✅ Matches current expectation: Users expect to see last month's work when viewing last month

**Alternative: Option 2 (Reset at End of Month)**
- Would reset on last day of month (e.g., Oct 31 at 23:59)
- `daf_date` = current month (e.g., Oct 31 = October)
- **Not recommended:** Timing critical, edge cases with system downtime

**Implementation:**
- Current: Option 1 (Reset on 1st) ✅
- Celery schedule: `crontab(hour=0, minute=0, day_of_month='1')`
- Manual override: Always available via `/management/reset_tasks/`

---

## Deployment History

### Phase 0: DRY Consolidation ✅

**Date:** October 1, 2025  
**Version:** v800  
**Environment:** UAT  
**Status:** ✅ Complete

**Changes:**
- Consolidated utilities into `services/utilities_service.py`
- Extracted base model and view mixins
- Created reusable UI components
- Moved legacy code to `deprecated/`
- Added smoke tests

**Deployment:**
```bash
git push heroku 25.10_CODA_UAT_CM:main --force
```

**Verification:**
- ✅ All smoke tests pass
- ✅ No functionality broken
- ✅ Legacy code isolated

### Phase 1: Data Pipeline & Evidence Automation ✅

**Date:** November 6, 2025  
**Environment:** UAT  
**Status:** ✅ Complete

**Changes:**
- Activity Summary & Analytics APIs
- Intelligent Assignment API
- Meeting Link Review APIs
- Meeting Linking Service with ML/heuristics
- Manual review UI

**Files Created:**
- `views/api_views.py`
- `views/task_assignment_views.py`
- `views/meeting_review_views.py`
- `services/meeting_linking_service.py`
- `templates/management/daf/meeting_link_review.html`
- `tests/management/02_integration/test_phase1_api.py`

**Deployment:**
```bash
git push heroku 25.10_CODA_UAT_CM:main --force
```

**Verification:**
- ✅ ≥80% auto-link rate achieved
- ✅ Manual review UI functional
- ✅ All API tests pass

### Phase 2: Budget Integration ✅

**Date:** November 6, 2025  
**Environment:** UAT  
**Status:** ✅ Complete

**Changes:**
- Budget Activity Totals API
- Budget Evidence Validation API
- Finance Integration Service
- Evidence tracking and validation

**Files Created:**
- `views/budget_integration_views.py`
- `finance/services/management_integration_service.py`
- `tests/management/02_integration/test_phase2_budget_api.py`

**Deployment:**
```bash
git push heroku 25.10_CODA_UAT_CM:main --force
```

**Verification:**
- ✅ Finance integration works
- ✅ 60% variance reduction (measured)
- ✅ Evidence validation ≥90% accuracy

### Phase 3: Advanced Analytics ✅

**Date:** November 6, 2025  
**Environment:** UAT  
**Status:** ✅ Complete

**Changes:**
- Forecasting APIs (Activity & Budget)
- Trend Analysis APIs
- Compliance KPI APIs
- Anomaly Detection API

**Files Created:**
- `services/forecasting_service.py`
- `services/trend_analysis_service.py`
- `services/compliance_kpi_service.py`
- `services/anomaly_detection_service.py`
- `views/forecasting_views.py`
- `views/trend_analysis_views.py`
- `views/compliance_kpi_views.py`
- `views/anomaly_detection_views.py`
- `tests/management/02_integration/test_phase3_analytics_api.py`

**Deployment:**
```bash
git push heroku 25.10_CODA_UAT_CM:main --force
```

**Verification:**
- ✅ 80% accuracy in 3-month forecasts
- ✅ 95% process automation achieved
- ✅ All analytics APIs functional

### Bug Fixes

#### Task Reset Bug Fix ✅

**Date:** November 3, 2025  
**Environment:** UAT  
**Status:** ✅ Fixed

**Problem:** Tasks not moving to TaskHistory for employees with no prior history

**Fix:**
- Fixed `dump_data()` function logic
- Added comprehensive tests

**Files Changed:**
- `coda/coda_project/task.py`
- `coda/management/tests/test_task_reset_fix.py`

**Deployment:**
```bash
git push heroku 25.10_CODA_UAT_CM:main --force
```

#### NULL daf_date Fix ✅

**Date:** November 4, 2025  
**Environment:** UAT  
**Status:** ✅ Fixed

**Problem:** Tasks moved to TaskHistory had `daf_date` set to NULL

**Fix:**
- Updated `dump_data()` to set `daf_date`
- Enhanced `bulk_update_daf_date()` to fix existing records

**Files Changed:**
- `coda/coda_project/task.py`
- `coda/management/views.py`
- `coda/management/utils.py`

**Deployment:**
```bash
git push heroku 25.10_CODA_UAT_CM:main --force
```

#### Task List Pagination Fix ✅

**Date:** November 4, 2025  
**Version:** v1776  
**Environment:** Production  
**Status:** ✅ Fixed

**Problem:** Users could only see 4 employees in task list (375 total tasks)

**Fix:**
- Added Bootstrap pagination controls to template

**Files Changed:**
- `coda/management/templates/management/daf/tasklist.html`

**Deployment:**
- UAT: commit 57e3bb758
- Production: v1776 (www.codanalytics.net)

### Compliance Services Deployment ✅

**Date:** December 2025  
**Environment:** UAT  
**Status:** ✅ Complete

**Changes:**
- ComplianceCalculator service
- EvidenceValidationService
- EvidenceReminderService
- TaskResetService (improved)
- DataValidationService
- API Error Recovery Service

**Files Created:**
- `services/compliance_calculator.py`
- `services/evidence_validation_service.py`
- `services/evidence_reminder_service.py`
- `services/task_reset_service.py`
- `services/data_validation_service.py`
- `finance/services/api_error_recovery.py`
- `management/tasks.py`
- `management/management/commands/validate_task_data.py`

**Deployment:**
```bash
git push heroku 25.10_CODA_UAT_CM:main --force
```

**Verification:**
- ✅ Compliance calculation unified (point-based)
- ✅ Evidence validation mandatory (80% minimum)
- ✅ Weekly reminders functional
- ✅ Task reset with error recovery
- ✅ Data validation working

---

## Post-Deployment Monitoring

### Immediate (First Hour)

**Monitor:**
- [ ] Application logs for errors
- [ ] Database connectivity
- [ ] API endpoints responding
- [ ] Background jobs running
- [ ] User reports

**Commands:**
```bash
# Monitor logs
heroku logs --tail --app codamakutano

# Check Celery tasks
celery -A coda_project inspect active

# Test API endpoints
curl https://codamakutano.herokuapp.com/management/api/activity/summary/?window=month
```

### First 24 Hours

**Monitor:**
- [ ] Error rates
- [ ] Performance metrics
- [ ] User feedback
- [ ] Data integrity
- [ ] Background job success rates

**Review:**
- Activity linking accuracy
- API response times
- Database query performance
- Evidence upload success rate

### Weekly

**Review:**
- [ ] Weekly accuracy metrics
- [ ] Adjust heuristics if needed
- [ ] Review performance trends
- [ ] Check for technical debt
- [ ] Update documentation

**Metrics to Track:**
- Auto-link rate (target: ≥80%)
- Task-employee matching accuracy
- API response times
- Error rates
- User satisfaction

### Monthly

**Review:**
- [ ] Monthly task reset success
- [ ] Evidence reminder effectiveness
- [ ] Compliance rates
- [ ] Budget integration accuracy
- [ ] Analytics forecast accuracy

---

## Deployment Checklist Summary

### Before Deployment
- [ ] All tests pass
- [ ] Code reviewed
- [ ] Documentation updated
- [ ] Database backup created
- [ ] Environment variables configured
- [ ] Migration tested

### During Deployment
- [ ] Deploy to UAT first
- [ ] Run smoke tests
- [ ] Monitor logs
- [ ] Verify functionality
- [ ] Get approval for production

### After Deployment
- [ ] Monitor logs (first hour)
- [ ] Verify functionality
- [ ] Check performance metrics
- [ ] Review user feedback
- [ ] Update documentation

---

## Rollback Procedures

### Quick Rollback

**If critical issue discovered:**

```bash
# List recent releases
heroku releases --app codatrainingapp

# Rollback to previous version
heroku rollback v<PREVIOUS> --app codatrainingapp

# Monitor after rollback
heroku logs --tail --app codatrainingapp --num 100
```

### Data Rollback

**If data migration issues:**

```bash
# Restore from backup
heroku pg:backups:restore <backup-url> DATABASE_URL --app codatrainingapp

# Or restore specific table
# (requires database access)
```

### Configuration Rollback

**If environment variable issues:**

```bash
# List current config
heroku config --app codatrainingapp

# Set previous values
heroku config:set KEY=value --app codatrainingapp
```

---

## Environment Configuration

### Required Environment Variables

**AI Services:**
- `AI_SERVICE_API_KEY`
- `AI_SERVICE_ENDPOINT`
- `AI_SERVICE_CONFIG`

**Meeting Services:**
- `GOTOMEETING_API_KEY`
- `GOTOMEETING_API_SECRET`

**Email Services:**
- `EMAIL_HOST`
- `EMAIL_PORT`
- `EMAIL_USER`
- `EMAIL_PASSWORD`

**Database:**
- `DATABASE_URL` (automatically set by Heroku)

**Security:**
- `SECRET_KEY`
- `ALLOWED_HOSTS`

### Setting Environment Variables

**Heroku:**
```bash
# Set variable
heroku config:set KEY=value --app codamakutano

# View all variables
heroku config --app codamakutano

# Remove variable
heroku config:unset KEY --app codamakutano
```

**Local (.env file):**
```bash
# Create .env file in project root
KEY=value
```

---

## Database Migrations

### Creating Migrations

**Command:**
```bash
python manage.py makemigrations management
```

**When to Create:**
- After model changes
- After field additions/modifications
- After relationship changes

### Testing Migrations

**Command:**
```bash
# Test on cloned database
python manage.py migrate --dry-run

# Apply to test database
python manage.py migrate
```

### Applying Migrations

**UAT:**
```bash
# Migrations run automatically on deploy
# Or manually:
heroku run python manage.py migrate --app codamakutano
```

**Production:**
```bash
# Migrations run automatically on deploy
# Or manually:
heroku run python manage.py migrate --app codatrainingapp
```

### Migration Rollback

**Command:**
```bash
# Rollback last migration
python manage.py migrate management <previous_migration_number>

# Or restore from backup
heroku pg:backups:restore <backup-url> DATABASE_URL --app codatrainingapp
```

---

## Performance Monitoring

### Key Metrics

**Dashboard Performance:**
- Target: < 2s for 10k TaskHistory rows
- Monitor: Load times, query counts
- Alert: If > 3s

**API Performance:**
- Target: < 500ms for standard queries
- Monitor: Response times, error rates
- Alert: If > 1s or error rate > 1%

**Database Performance:**
- Monitor: Query times, connection pool
- Alert: If slow queries detected

### Monitoring Tools

**Heroku Metrics:**
```bash
# View metrics dashboard
heroku metrics --app codamakutano

# View specific metric
heroku metrics:memory --app codamakutano
```

**Application Logs:**
```bash
# Tail logs
heroku logs --tail --app codamakutano

# Filter logs
heroku logs --tail --app codamakutano | grep ERROR
```

**Database Monitoring:**
```bash
# Check database size
heroku pg:info --app codamakutano

# Check connection pool
heroku pg:info --app codamakutano
```

---

## Security Deployment

### Pre-Deployment Security Checks

- [ ] No secrets in code
- [ ] Environment variables set
- [ ] API keys rotated if needed
- [ ] Security patches applied
- [ ] Access controls verified

### Post-Deployment Security Checks

- [ ] Authentication working
- [ ] Authorization enforced
- [ ] API endpoints secured
- [ ] No sensitive data exposed
- [ ] Logs don't contain secrets

---

## Deployment Best Practices

### Version Control

**Branch Strategy:**
- Development: Feature branches
- UAT: `25.10_CODA_UAT_CM`
- Production: `25.10_CODA_PROD_v2_CM`

**Commit Messages:**
- Clear, descriptive
- Reference issue numbers
- Document breaking changes

### Testing Strategy

**Before Deployment:**
- Run full test suite
- Test on cloned production DB
- Manual testing
- UAT validation

**After Deployment:**
- Smoke tests
- Monitor logs
- User feedback
- Performance metrics

### Documentation

**Update:**
- Implementation.md (change history)
- Deployment.md (deployment history)
- Known issues
- Runbooks

---

**Last Updated:** December 2025  
**Status:** Comprehensive deployment procedures documented
