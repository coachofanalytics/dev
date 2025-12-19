# Employee Activity System (Management) – 06_MAINTENANCE.md

## Purpose
This document provides operational procedures, troubleshooting guides, known issues, and maintenance runbooks for the Employee Task Management System.

---

## Operations & Monitoring

### Background Jobs Monitoring

**Celery Tasks:**
- **Monthly Task Reset:** Runs on 1st of each month at midnight (00:00)
  - Task: `task_history` (dump_data function)
  - Monitor via: Celery logs, admin notifications
  - Check: TaskHistory records created, points reset correctly

- **Weekly Evidence Reminders:** Runs every Friday at 5 PM (17:00)
  - Task: `management.tasks.send_weekly_evidence_reminders`
  - Monitor via: Email logs, reminder history
  - Check: Reminders sent, employees notified

**Monitoring Commands:**
```bash
# Check Celery task status
celery -A coda_project inspect active

# Check scheduled tasks
celery -A coda_project inspect scheduled

# View Celery logs
heroku logs --tail --app codamakutano | grep celery
```

### AI Health Monitoring

**Service:** `AIHealthChecker`

**Monitor:**
- AI service health checks
- API response times
- Error rates
- Service availability

**Commands:**
```bash
# Check AI service health
python manage.py shell -c "from ai_services.services import AIHealthChecker; checker = AIHealthChecker(); print(checker.check_health())"
```

### Activity Linking Accuracy

**Review Frequency:** Weekly

**What to Monitor:**
- Auto-link rate (target: ≥80%)
- Manual review queue size
- Confidence score distribution
- False positive/negative rates

**Tuning:**
- Adjust keyword matching rules
- Update `MeetingActivityMapping` patterns
- Refine confidence thresholds
- Review historical pattern weights

**Commands:**
```bash
# Get linking statistics
python manage.py shell -c "from management.services.meeting_linking_service import MeetingLinkingService; service = MeetingLinkingService(); stats = service.get_linking_statistics(); print(stats)"
```

### Database Health

**Monitor:**
- Query performance
- Index usage
- Table sizes
- Connection pool

**Commands:**
```bash
# Check slow queries
python manage.py shell -c "from django.db import connection; print(connection.queries)"

# Check table sizes
python manage.py shell -c "from django.db import connection; cursor = connection.cursor(); cursor.execute(\"SELECT pg_size_pretty(pg_total_relation_size('management_taskhistory'))\"); print(cursor.fetchone())"
```

---

## Runbooks

### Re-index TaskHistory

**Purpose:** Rebuild database indexes for performance

**Command:**
```bash
python manage.py shell -c "from management.services import maintenance; maintenance.rebuild_indexes()"
```

**When to Run:**
- After bulk data imports
- If query performance degrades
- After schema changes

### Reprocess Meeting Links for Date Range

**Purpose:** Re-run meeting-to-task linking for specific date range

**Command:**
```bash
python manage.py reprocess_links --from 2025-10-01 --to 2025-10-31
```

**When to Run:**
- After updating linking rules
- To fix incorrect links
- After data corrections

### Fix NULL daf_date Records

**Purpose:** Fix TaskHistory records with NULL daf_date

**Command:**
```bash
python manage.py shell -c "from management.views import bulk_update_daf_date; bulk_update_daf_date()"
```

**When to Run:**
- After discovering NULL daf_date records
- After manual task resets
- To fix historical data

### Validate Task Data

**Purpose:** Run data validation checks

**Command:**
```bash
python manage.py validate_task_data

# For specific employee
python manage.py validate_task_data --employee username

# For specific month/year
python manage.py validate_task_data --month 10 --year 2025

# Attempt to fix errors (future feature)
python manage.py validate_task_data --fix
```

**When to Run:**
- Weekly data quality checks
- Before major deployments
- After data migrations

### Manual Task Reset

**Purpose:** Manually trigger task reset (for edge cases)

**Command:**
```bash
# Via Django shell
python manage.py shell -c "from management.services.task_reset_service import TaskResetService; service = TaskResetService(); result = service.manual_reset(dry_run=False); print(result)"

# Via web interface
# Navigate to: /management/reset_tasks/
```

**When to Run:**
- If automated reset fails
- For testing purposes
- For specific date ranges

### Profile Task Data

**Purpose:** Analyze real task data for design decisions

**Commands:**
```bash
# Basic profiling
python manage.py profile_task_data

# Focus on activity names
python manage.py profile_task_data --activity-names

# Focus on department patterns
python manage.py profile_task_data --department-patterns

# Export to JSON
python manage.py profile_task_data --export-json task_profiling_results.json
```

**When to Run:**
- Before making schema changes
- To understand data patterns
- For design validation

### Analyze Task History

**Purpose:** Comprehensive TaskHistory analysis

**Command:**
```bash
python manage.py analyze_task_history
```

**When to Run:**
- For analytics insights
- To identify patterns
- For reporting

---

## Known Issues & Troubleshooting

### Critical Issues 🔴

#### 1. Monolithic Files (Code Organization)

**Issue:** Large files make maintenance difficult
- `views.py`: 2,596+ lines (should be split into modules)
- `models.py`: 1,046 lines (should be split into models/ directory)
- `urls.py`: 173+ URL patterns (hard to navigate)

**Impact:**
- Difficult to navigate and maintain
- Hard to make safe changes
- Slower development

**Workaround:**
- Use IDE search to find specific views/models
- Reference documentation for structure

**Planned Fix:**
- Split views.py into 8+ modules (Week 5-6 of action plan)
- Split models.py into 6+ modules (Week 6 of action plan)
- Organize URLs into sub-includes

**Status:** 📅 Planned (Phase 4 prep)

#### 2. Test Coverage Gap

**Issue:** Minimal test coverage (currently improving)

**Impact:**
- Cannot verify changes work correctly
- No regression protection
- Hard to refactor safely

**Workaround:**
- Manual testing before deployment
- Code reviews

**Planned Fix:**
- Comprehensive test suite (Weeks 1-4 of action plan)
- Target: 80%+ coverage

**Status:** 🔄 In Progress

### Moderate Issues 🟡

#### 3. Meeting Vendor Rate Limits

**Issue:** Meeting vendor rate limits can delay evidence ingestion

**Symptoms:**
- Slow evidence ingestion
- API errors
- Missing meeting links

**Solution:**
- Implement batch processing
- Add exponential backoff retry logic
- Cache responses when possible

**Workaround:**
- Process in smaller batches
- Increase retry delays
- Monitor rate limit headers

**Status:** ✅ Partially addressed (retry logic implemented)

#### 4. Historical Data Gaps

**Issue:** Historical gaps from manual entries

**Symptoms:**
- Missing TaskHistory records
- Incomplete analytics
- Budget calculation issues

**Solution:**
- Run backfill job before analytics
- Validate data completeness
- Use data validation service

**Command:**
```bash
python manage.py validate_task_data
```

**Status:** ✅ Addressed (validation service created)

#### 5. Hardcoded Default FK Values

**Issue:** Models use hardcoded default IDs (default=1, default=999)

**Risk:** Will break if those records don't exist

**Examples:**
- `Task` model: `default=999` for employee
- Some models: `default=1` for category

**Solution:**
- Replace with proper defaults or nullable fields
- Use `TaskCategory.get_default_pk()` pattern
- Make fields nullable if appropriate

**Status:** 📅 Planned (technical debt cleanup)

#### 6. Auto-Now Fields Issue

**Issue:** `TaskHistory.submission` uses `auto_now=True` which updates on every save

**Impact:**
- Submission date changes on every update
- Not ideal for historical records

**Solution:**
- Change to `auto_now_add=True` (only set on creation)
- Or use `default=timezone.now` with manual setting

**Status:** 📅 Planned (technical debt cleanup)

### Minor Issues 🟢

#### 7. Commented Code Blocks

**Issue:** Large blocks of commented code in admin.py, urls.py

**Impact:**
- Code clutter
- Confusion about what's active

**Solution:**
- Remove commented code
- Move to archive if needed
- Use version control for history

**Status:** 📅 Planned (technical debt cleanup)

#### 8. Missing Docstrings

**Issue:** Most views lack docstrings

**Impact:**
- Reduced code clarity
- Harder to understand purpose

**Solution:**
- Add docstrings to all views
- Document parameters and return values
- Use consistent format

**Status:** 📅 Planned (documentation improvement)

#### 9. Inconsistent Naming

**Issue:** Some views use function-based, others class-based; URL names not always consistent

**Impact:**
- Harder to find specific views
- Inconsistent patterns

**Solution:**
- Standardize view patterns (prefer CBV where appropriate)
- Consistent URL naming (snake_case)
- Extract choices to choices.py

**Status:** 📅 Planned (code consistency)

---

## Recent Fixes

### ✅ Task Reset Bug (Fixed Nov 3, 2025)

**Problem:** Tasks not moving to TaskHistory for employees with no prior history

**Root Cause:** Logic error in `dump_data()` - checked if employee had TaskHistory before processing

**Fix Applied:**
- Removed history count check
- Changed logic to check for current tasks first
- Process all employees with current tasks

**Files Changed:**
- `coda/coda_project/task.py` - Fixed `dump_data()` function
- `coda/management/tests/test_task_reset_fix.py` - Added tests

**Impact:** ✅ All employees (including new) can now reset tasks correctly

### ✅ NULL daf_date Fix (Fixed Nov 4, 2025)

**Problem:** Tasks moved to TaskHistory had `daf_date` set to NULL, not appearing in payroll

**Root Cause:** `dump_data()` function was not setting `daf_date` when creating TaskHistory records

**Fix Applied:**
- Updated `dump_data()` to set `daf_date` when creating TaskHistory
- Enhanced `bulk_update_daf_date()` to fix existing NULL records
- Updated filter logic to handle NULL `daf_date`

**Files Changed:**
- `coda/coda_project/task.py` - Fixed `dump_data()` to set `daf_date`
- `coda/management/views.py` - Enhanced `bulk_update_daf_date()`
- `coda/management/utils.py` - Updated filter to handle NULL `daf_date`

**Impact:** ✅ Tasks now have correct `daf_date` for monthly filtering

### ✅ Task List Pagination (Fixed Nov 4, 2025)

**Problem:** Users could only see 4 employees in task list, despite 16 employees having 375 total tasks

**Root Cause:**
- View (`TaskListView`) paginated to 20 tasks per page
- Template (`tasklist.html`) had NO pagination controls
- Result: Only first 20 tasks visible

**Fix Applied:**
- Added Bootstrap pagination controls to template
- Shows: Previous/Next, page numbers, First/Last buttons
- Displays: "Page X of Y (Showing start-end of total tasks)"

**Files Changed:**
- `coda/management/templates/management/daf/tasklist.html` (lines 117-178)

**Deployment:**
- UAT: commit 57e3bb758
- Production: v1776 (www.codanalytics.net)

**Impact:** ✅ All employees with tasks now visible and accessible

---

## Code Quality Issues

### Technical Debt

**High Priority:**
1. **Split Large Files** 🔴
   - Break views.py into modules (dashboard, task, requirement, etc.)
   - Split models.py into models/ directory
   - Organize URLs into sub-includes

2. **Add Tests** 🔴
   - Create comprehensive test suite
   - Unit tests for models, services
   - Integration tests for views
   - API contract tests for Finance integration

3. **Remove Technical Debt** 🔴
   - Delete commented code blocks
   - Remove or refactor legacy patterns
   - Update hardcoded default FK values

**Medium Priority:**
4. **Improve Documentation** 🟡
   - Add inline docstrings to views
   - Add code examples to Implementation.md
   - Log test results in Testing.md

5. **Performance Optimization** 🟡
   - Review query optimization (select_related, prefetch_related)
   - Add missing indexes
   - Implement caching where appropriate

6. **Consistency** 🟡
   - Standardize view patterns (FBV vs CBV)
   - Consistent URL naming
   - Extract choices to choices.py

**Low Priority:**
7. **Polish** 🟢
   - Organize imports consistently
   - Add type hints to service methods
   - Improve error messages
   - Better logging

---

## Improvement Opportunities

### Phase 4 Enhancements (Planned)

**Task System Enhancements:**
- Add `department` field to Task and TaskHistory models
- Enhance `TaskStandardizationService` with department classification
- Create Task management dashboard (similar to team-management)
- Enhance auto-assignment with rule-based fast path
- Add ActivityType model for template-based task creation (optional)

**Benefits:**
- Better task organization
- Improved assignment accuracy
- Reduced manual work
- Better analytics

### Code Organization Improvements

**Refactoring Plan:**
- Week 5: Split views.py into 8 modules
- Week 6: Split models.py into 6 modules
- Week 7+: Continue with other improvements

**Benefits:**
- Easier maintenance
- Faster development
- Better code organization
- Improved testability

### Testing Improvements

**Test Coverage Goals:**
- Current: Improving (targeting 80%+)
- Add performance tests
- Add security tests
- Add load tests

**Benefits:**
- Regression protection
- Safer refactoring
- Better code quality
- Faster debugging

---

## Backups & Data Safety

### Database Backups

**Production:**
- Automated daily backups via Heroku
- Manual backups before major changes
- Test restore procedures quarterly

**Local Development:**
- Use cloned production database (never production directly)
- Command: `bash scripts/clone_prod_database.sh`
- Settings: `coda_project.coda_settings.local_prod_clone_settings`

**Critical Rule:**
- **NEVER run experiments on production DB**
- Always use cloned DB per CURSOR_AI_GUIDE.md

### Data Validation

**Before Major Changes:**
- Run data validation: `python manage.py validate_task_data`
- Check for orphaned records
- Verify data integrity
- Backup database

**After Data Migrations:**
- Verify all data migrated correctly
- Check for data loss
- Validate relationships
- Test queries

### Environment Variables

**Critical Variables:**
- AI service API keys
- Database credentials
- Email service credentials
- External API keys

**Safety:**
- Never commit to repository
- Store in environment variables
- Verify present in UAT/Prod before enabling jobs
- Rotate keys regularly

---

## Upgrade Notes

### AI Provider Updates

**Procedure:**
1. Validate through `AIConfigurationService` staging keys first
2. Test in UAT environment
3. Monitor for errors
4. Deploy to production

**Commands:**
```bash
# Test AI configuration
python manage.py shell -c "from ai_services.services import AIConfigurationService; service = AIConfigurationService(); print(service.get_config())"
```

### Django Version Updates

**Procedure:**
1. Test in local environment first
2. Run full test suite
3. Check for deprecation warnings
4. Update dependencies
5. Test in UAT
6. Deploy to production

### Database Migrations

**Procedure:**
1. Backup database
2. Test migration on cloned DB
3. Run migration in UAT
4. Verify data integrity
5. Deploy to production

**Commands:**
```bash
# Create migration
python manage.py makemigrations management

# Test migration
python manage.py migrate --dry-run

# Apply migration
python manage.py migrate
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
- Action: Review indexes, optimize queries

### Performance Optimization

**Query Optimization:**
- Use `select_related()` for ForeignKey
- Use `prefetch_related()` for ManyToMany
- Add indexes on frequently queried fields
- Avoid N+1 queries

**Caching:**
- API response caching (1 hour default)
- Cache frequently accessed data
- Invalidate cache on updates

**Bulk Operations:**
- Use `bulk_create()` for TaskHistory
- Use `bulk_update()` for Task resets
- Batch process large datasets

---

## Security Maintenance

### Access Control

**Monitor:**
- User permissions
- Role assignments
- Department access
- API authentication

**Review:**
- Quarterly access review
- Remove inactive users
- Update permissions as needed

### API Security

**Monitor:**
- API authentication
- Rate limiting (if implemented)
- Error messages (don't leak sensitive info)
- CORS configuration

**Review:**
- API keys rotation
- Authentication tokens
- Security patches

### Data Protection

**Monitor:**
- PII access logs
- Data export activities
- Unusual access patterns

**Review:**
- Quarterly security audit
- Data retention policies
- Compliance requirements

---

## Maintenance Schedule

### Daily
- [ ] Monitor background jobs
- [ ] Check error logs
- [ ] Review critical alerts

### Weekly
- [ ] Review activity linking accuracy
- [ ] Check test coverage
- [ ] Review performance metrics
- [ ] Update documentation

### Monthly
- [ ] Run data validation
- [ ] Review security logs
- [ ] Check for technical debt
- [ ] Plan improvements

### Quarterly
- [ ] Security audit
- [ ] Performance review
- [ ] Code quality assessment
- [ ] Dependency updates

---

## Troubleshooting Guide

### Task Reset Fails

**Symptoms:**
- No TaskHistory created
- Points not reset
- Error in logs

**Diagnosis:**
```bash
# Check Celery logs
heroku logs --tail --app codamakutano | grep task_history

# Check database
python manage.py shell -c "from management.models import TaskHistory; print(TaskHistory.objects.filter(created_at__date=date.today()).count())"
```

**Solutions:**
- Check transaction errors
- Verify database connectivity
- Check for data validation errors
- Use manual reset if needed

### Evidence Not Linking

**Symptoms:**
- Meetings not auto-linked to tasks
- Low auto-link rate

**Diagnosis:**
```bash
# Check linking statistics
python manage.py shell -c "from management.services.meeting_linking_service import MeetingLinkingService; service = MeetingLinkingService(); stats = service.get_linking_statistics(); print(stats)"
```

**Solutions:**
- Review meeting metadata
- Check keyword matching rules
- Update MeetingActivityMapping
- Adjust confidence thresholds

### API Errors

**Symptoms:**
- API returns errors
- Finance integration fails

**Diagnosis:**
```bash
# Check API logs
heroku logs --tail --app codamakutano | grep api

# Test API endpoint
curl -H "Authorization: Bearer <token>" "http://localhost:8000/management/api/activity/summary/?window=month"
```

**Solutions:**
- Check authentication
- Verify data exists
- Check error messages
- Review API documentation

### Performance Issues

**Symptoms:**
- Slow dashboard loads
- Timeout errors
- High database load

**Diagnosis:**
```bash
# Check slow queries
python manage.py shell -c "from django.db import connection; print([q for q in connection.queries if float(q['time']) > 0.1])"

# Check database indexes
python manage.py shell -c "from django.db import connection; cursor = connection.cursor(); cursor.execute(\"SELECT indexname FROM pg_indexes WHERE tablename = 'management_taskhistory'\"); print(cursor.fetchall())"
```

**Solutions:**
- Add missing indexes
- Optimize queries
- Implement caching
- Review N+1 queries

---

## Legacy Code Management

### Deprecated Directory

**Location:** `coda/management/deprecated/`

**Purpose:** Isolated legacy code from main codebase

**Maintenance:**
- Keep clean - remove once safely unused
- Document what's deprecated and why
- Set removal date
- Verify no dependencies before removal

**Review:**
- Quarterly review of deprecated code
- Remove if unused for 6+ months
- Update documentation

---

## Support & Escalation

### Support Channels

**Development Issues:**
- Check logs first
- Review this documentation
- Check known issues
- Review code comments

**Production Issues:**
- Check Heroku logs
- Review error tracking
- Check database health
- Review monitoring dashboards

**Escalation:**
- Critical issues: Immediate attention
- High priority: Within 24 hours
- Medium priority: Within 1 week
- Low priority: Next sprint

---

**Last Updated:** December 2025  
**Status:** Comprehensive maintenance procedures documented
