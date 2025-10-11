# Management App - Troubleshooting & Maintenance Guide

## Executive Summary

This document provides comprehensive troubleshooting guidance, maintenance procedures, and operational best practices for the Management App. It covers common issues, their solutions, and preventive measures.

---

## Table of Contents

1. [Common Issues and Solutions](#common-issues-and-solutions)
2. [Data Quality Issues](#data-quality-issues)
3. [AI Service Issues](#ai-service-issues)
4. [Performance Issues](#performance-issues)
5. [Deployment Issues](#deployment-issues)
6. [Monitoring and Alerts](#monitoring-and-alerts)
7. [Maintenance Procedures](#maintenance-procedures)
8. [Emergency Procedures](#emergency-procedures)

---

## Common Issues and Solutions

### Issue: Tasks Not Displaying

**Symptoms:**
- Employee logs in but sees no tasks
- Task list appears empty

**Possible Causes:**
1. Tasks are not assigned to the logged-in user
2. Tasks are filtered by status (e.g., showing only completed tasks)
3. Tasks are marked as inactive
4. Database query error

**Solutions:**

```python
# Check if tasks exist for user
from management.models import Task
from accounts.models import CustomUser

user = CustomUser.objects.get(username='<username>')
tasks = Task.objects.filter(employee=user, is_active=True)
print(f"Active tasks for {user.username}: {tasks.count()}")

# Check task status distribution
from django.db.models import Count
Task.objects.filter(employee=user).values('is_active').annotate(count=Count('id'))
```

**Prevention:**
- Always verify task assignment during creation
- Use filters carefully in UI
- Implement task assignment validation

---

### Issue: Payslip Not Generating

**Symptoms:**
- Payslip page loads but shows no data
- Error message when accessing payslip
- Calculations appear incorrect

**Possible Causes:**
1. No TaskHistory data for selected month
2. NULL `daf_date` values in TaskHistory
3. Division by zero in calculations
4. Missing employee salary data

**Solutions:**

```bash
# Check TaskHistory data
python coda/manage.py shell
>>> from management.models import TaskHistory
>>> from accounts.models import CustomUser
>>> user = CustomUser.objects.get(username='<username>')
>>> history = TaskHistory.objects.filter(
...     history_user_assigned=user,
...     daf_date__year=2024,
...     daf_date__month=3
... )
>>> print(f"Records found: {history.count()}")

# Fix NULL dates
python coda/manage.py fix_taskhistory_dates

# Validate data
python coda/manage.py validate_data_quality
```

**Prevention:**
- Run monthly data validation
- Ensure monthly reset process completes successfully
- Monitor TaskHistory table size and integrity

---

### Issue: AI Predictions Failing

**Symptoms:**
- Prediction commands fail with errors
- Predictions return None or empty results
- Low confidence scores

**Possible Causes:**
1. Insufficient historical data
2. NULL values in training data
3. Missing ML library dependencies
4. Data format issues (Decimal vs Float)

**Solutions:**

```bash
# Check data availability
python coda/manage.py shell
>>> from management.models import TaskHistory
>>> total_records = TaskHistory.objects.count()
>>> recent_records = TaskHistory.objects.filter(
...     daf_date__gte='2024-01-01'
... ).count()
>>> print(f"Total: {total_records}, Recent: {recent_records}")
>>> # Need minimum 30 days of data

# Test predictions with debug output
python coda/manage.py test_ai_predictions

# Check ML dependencies
pip list | grep -E "(numpy|scikit-learn|joblib|scipy)"

# Reinstall if missing
pip install numpy scikit-learn joblib scipy
```

**Prevention:**
- Maintain at least 90 days of historical data
- Run data validation before AI operations
- Monitor prediction confidence scores
- Implement fallback strategies

---

### Issue: Intelligent Assignment Not Working

**Symptoms:**
- Tasks assigned randomly or to wrong employees
- Assignment algorithm fails
- Unbalanced workload distribution

**Possible Causes:**
1. No historical performance data
2. Incorrect employee category mapping
3. Workload calculation errors
4. Missing employee capacity settings

**Solutions:**

```bash
# Test assignment service
python coda/manage.py test_intelligent_assignment

# Check employee workload
python coda/manage.py shell
>>> from management.models import Task
>>> from accounts.models import CustomUser
>>> from django.db.models import Count, Sum
>>> 
>>> employees = CustomUser.objects.annotate(
...     task_count=Count('assigned_user'),
...     total_points=Sum('assigned_user__point')
... )
>>> for emp in employees:
...     print(f"{emp.username}: {emp.task_count} tasks, {emp.total_points} points")

# Verify employee categories
>>> employees = CustomUser.objects.values('category').annotate(count=Count('id'))
>>> for cat in employees:
...     print(f"Category {cat['category']}: {cat['count']} employees")
```

**Prevention:**
- Regularly update employee capacity settings
- Monitor workload distribution
- Review assignment algorithm performance monthly
- Keep historical performance data clean

---

## Data Quality Issues

### NULL Date Values

**Problem:** TaskHistory records with NULL `daf_date` cause analysis failures

**Detection:**
```bash
python coda/manage.py shell
>>> from management.models import TaskHistory
>>> null_count = TaskHistory.objects.filter(daf_date__isnull=True).count()
>>> print(f"NULL daf_date count: {null_count}")
```

**Fix:**
```bash
python coda/manage.py fix_taskhistory_dates
```

**Prevention:**
- Ensure monthly reset process sets `daf_date`
- Add database constraint for non-NULL `daf_date` (future)
- Monitor NULL count weekly

---

### Division by Zero Errors

**Problem:** Calculations fail when `maxpoints` is zero

**Detection:**
```python
from management.models import Task, TaskHistory

# Check for zero maxpoints
zero_max_tasks = Task.objects.filter(mxpoint=0).count()
zero_max_history = TaskHistory.objects.filter(maxpoints=0).count()
print(f"Tasks: {zero_max_tasks}, History: {zero_max_history}")
```

**Fix in Code:**
```python
# Always use safe division
if maxpoints > 0:
    completion_rate = (points / maxpoints) * 100
else:
    completion_rate = 0
    
# Or use default
completion_rate = (points / maxpoints * 100) if maxpoints else 0
```

**Prevention:**
- Add validation on task creation (maxpoints > 0)
- Implement database constraint
- Review all calculation methods for safe division

---

### Data Validation Process

**Run Comprehensive Validation:**
```bash
python coda/manage.py validate_data_quality
```

**Expected Output:**
```
=== Data Quality Validation Report ===

TaskHistory Validation:
✅ NULL dates: 0
✅ Zero maxpoints: 0
✅ Negative points: 0
✅ Total records: 1,234
Status: PASS

Active Tasks Validation:
✅ Missing evidence: 12 (acceptable)
✅ Unassigned tasks: 0
✅ Inactive tasks: 45
Status: PASS

Employee Data Validation:
✅ No salary: 0
✅ No category: 0
✅ Inactive with tasks: 0
Status: PASS

Overall Status: PASS
```

**Schedule Regular Validation:**
```bash
# Add to cron (daily at 2 AM)
0 2 * * * cd /path/to/project && python coda/manage.py validate_data_quality >> /path/to/logs/validation.log 2>&1
```

---

## AI Service Issues

### RealAIService Connection Errors

**Problem:** AI service calls fail or timeout

**Detection:**
```bash
# Check Heroku logs
heroku logs --tail --app codamakutano | grep "RealAIService"

# Test AI service directly
python coda/manage.py shell
>>> from ai_services.ai_integration_service import RealAIService
>>> service = RealAIService()
>>> result = service.generate_text("Test prompt")
>>> print(result)
```

**Solutions:**

1. **API Key Issues:**
```bash
# Verify API keys are set
heroku config --app codamakutano | grep API_KEY

# Set if missing
heroku config:set OPENAI_API_KEY=your_key --app codamakutano
```

2. **Rate Limiting:**
```python
# Implement exponential backoff
import time

def call_ai_service_with_retry(prompt, max_retries=3):
    for i in range(max_retries):
        try:
            return ai_service.generate_text(prompt)
        except RateLimitError:
            wait_time = 2 ** i  # Exponential backoff
            time.sleep(wait_time)
    return None
```

3. **Fallback Strategy:**
```python
# Use statistical fallback if AI fails
try:
    prediction = ai_service.predict(data)
except Exception as e:
    print(f"AI service failed: {e}, using statistical fallback")
    prediction = statistical_fallback(data)
```

---

### Model Training Failures

**Problem:** ML models fail to train or produce poor predictions

**Detection:**
```bash
# Check training data availability
python coda/manage.py shell
>>> from management.services.simple_ai_service import SimpleAIService
>>> service = SimpleAIService()
>>> # Check if enough data
>>> from management.models import TaskHistory
>>> recent_data = TaskHistory.objects.filter(daf_date__gte='2024-01-01')
>>> print(f"Training samples: {recent_data.count()}")
>>> # Need minimum 50-100 samples
```

**Solutions:**

1. **Insufficient Data:**
```python
# Add check before training
MIN_TRAINING_SAMPLES = 50

if training_data.count() < MIN_TRAINING_SAMPLES:
    return {
        'status': 'insufficient_data',
        'message': f'Need at least {MIN_TRAINING_SAMPLES} samples',
        'fallback': statistical_prediction(data)
    }
```

2. **Data Type Issues (Decimal vs Float):**
```python
# Convert Decimal to float for sklearn
import numpy as np

X = np.array([[float(r.points), float(r.maxpoints)] for r in training_data])
y = np.array([float(r.earning) for r in training_data])
```

3. **Feature Scaling:**
```python
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
model.fit(X_scaled, y)
```

---

## Performance Issues

### Slow Database Queries

**Problem:** Pages load slowly or timeout

**Detection:**
```bash
# Enable Django debug toolbar (development only)
pip install django-debug-toolbar

# Check slow queries in Heroku
heroku pg:outliers --app codamakutano

# Use Django's query logging
python coda/manage.py shell
>>> from django.db import connection
>>> from django.db import reset_queries
>>> reset_queries()
>>> # Run your query
>>> print(len(connection.queries))
>>> for q in connection.queries:
...     print(q['time'], q['sql'][:100])
```

**Solutions:**

1. **Add Database Indexes:**
```python
# In models.py
class TaskHistory(models.Model):
    daf_date = models.DateField(db_index=True)  # Add index
    history_user_assigned = models.ForeignKey(..., db_index=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['daf_date', 'history_user_assigned']),
        ]
```

2. **Optimize Queries:**
```python
# Bad: N+1 queries
tasks = Task.objects.all()
for task in tasks:
    print(task.employee.username)  # Extra query each time

# Good: Select related
tasks = Task.objects.select_related('employee', 'category').all()
for task in tasks:
    print(task.employee.username)  # No extra queries
```

3. **Use Aggregation:**
```python
# Bad: Python loops
total = sum([task.point for task in Task.objects.all()])

# Good: Database aggregation
from django.db.models import Sum
total = Task.objects.aggregate(Sum('point'))['point__sum'] or 0
```

4. **Implement Caching:**
```python
from django.core.cache import cache

def get_employee_performance(employee_id):
    cache_key = f'performance_{employee_id}'
    performance = cache.get(cache_key)
    
    if not performance:
        performance = calculate_performance(employee_id)
        cache.set(cache_key, performance, 300)  # 5 minutes
    
    return performance
```

---

### High Memory Usage

**Problem:** Application crashes or restarts due to memory limits

**Detection:**
```bash
# Monitor Heroku metrics
heroku logs --tail --app codamakutano | grep "Memory"

# Check dyno size
heroku ps --app codamakutano
```

**Solutions:**

1. **Query Optimization:**
```python
# Bad: Loads all objects into memory
all_history = list(TaskHistory.objects.all())

# Good: Use iterator for large datasets
for record in TaskHistory.objects.iterator(chunk_size=100):
    process_record(record)
```

2. **Batch Processing:**
```python
# Process in batches
from django.core.paginator import Paginator

queryset = TaskHistory.objects.all()
paginator = Paginator(queryset, 100)

for page_num in paginator.page_range:
    page = paginator.page(page_num)
    for record in page.object_list:
        process_record(record)
```

3. **Upgrade Dyno:**
```bash
# Temporarily upgrade for heavy operations
heroku ps:scale web=1:standard-2x --app codamakutano
```

---

## Deployment Issues

### Heroku Build Failures

**Problem:** Deployment fails during build phase

**Detection:**
```bash
git push heroku 25.10_CODA_DEV_CM:main
# Watch build output for errors
```

**Common Causes and Solutions:**

1. **Missing Dependencies:**
```bash
# Ensure requirements.txt is up to date
pip freeze > coda/requirements.txt

# Commit and redeploy
git add coda/requirements.txt
git commit -m "Update dependencies"
git push heroku 25.10_CODA_DEV_CM:main
```

2. **Python Version Mismatch:**
```bash
# Check runtime.txt
cat coda/runtime.txt
# Should contain: python-3.9.16 (or your version)

# Update if needed
echo "python-3.9.16" > coda/runtime.txt
```

3. **Procfile Issues:**
```bash
# Ensure Procfile is correct
cat coda/Procfile
# Should contain:
# web: gunicorn coda_project.wsgi --log-file -
```

---

### Database Migration Issues

**Problem:** Migrations fail on Heroku

**Detection:**
```bash
heroku run python coda/manage.py showmigrations --app codamakutano
# Look for [ ] (not applied) migrations
```

**Solutions:**

```bash
# Apply migrations
heroku run python coda/manage.py migrate --app codamakutano

# If migration conflicts:
heroku run python coda/manage.py migrate --fake <app_name> <migration_name> --app codamakutano

# If all else fails, reset migrations (DANGEROUS - production)
# Only do this in UAT/development
heroku run python coda/manage.py migrate --fake-initial --app codamakutano
```

---

### Environment Variable Issues

**Problem:** Application can't access configuration

**Detection:**
```bash
# Check environment variables
heroku config --app codamakutano

# Check in Python
heroku run python coda/manage.py shell --app codamakutano
>>> import os
>>> print(os.environ.get('SECRET_KEY'))
```

**Solutions:**

```bash
# Set missing variables
heroku config:set SECRET_KEY=your_secret_key --app codamakutano
heroku config:set DEBUG=False --app codamakutano
heroku config:set OPENAI_API_KEY=your_key --app codamakutano

# Remove incorrect variables
heroku config:unset WRONG_VAR --app codamakutano
```

---

## Monitoring and Alerts

### Heroku Logging

**Setup Comprehensive Logging:**

```python
# In settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'management': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
```

**Monitor Logs:**
```bash
# Real-time logs
heroku logs --tail --app codamakutano

# Filter logs
heroku logs --tail --app codamakutano | grep ERROR
heroku logs --tail --app codamakutano | grep "management"

# Historical logs
heroku logs --num 500 --app codamakutano
```

---

### Performance Monitoring

**Setup Monitoring:**

```bash
# Add New Relic (free tier available)
heroku addons:create newrelic:wayne --app codamakutano

# Or use Scout APM
heroku addons:create scout:chair --app codamakutano
```

**Key Metrics to Monitor:**
- Response time (target: < 500ms)
- Error rate (target: < 1%)
- Memory usage (target: < 80%)
- Database query time (target: < 100ms)
- AI service response time (target: < 2s)

---

### Alerting

**Setup Email Alerts:**

```python
# In settings.py
ADMINS = [('Admin Name', 'admin@example.com')]
SERVER_EMAIL = 'server@codamakutano.com'

# Django will email admins on 500 errors
```

**Custom Alerts:**

```python
# In management/services/data_validation_service.py
def validate_and_alert(self):
    report = self.generate_validation_report()
    
    if report['status'] == 'FAIL':
        send_mail(
            subject='Data Quality Alert',
            message=f'Validation failed: {report}',
            from_email='alerts@codamakutano.com',
            recipient_list=['admin@example.com'],
        )
```

---

## Maintenance Procedures

### Daily Maintenance

```bash
# Check application health
heroku ps --app codamakutano

# Review logs for errors
heroku logs --tail --app codamakutano | grep ERROR | tail -50

# Monitor dyno metrics
heroku ps:autoscale:status --app codamakutano
```

---

### Weekly Maintenance

```bash
# Run data validation
heroku run python coda/manage.py validate_data_quality --app codamakutano

# Check database size
heroku pg:info --app codamakutano

# Review slow queries
heroku pg:outliers --app codamakutano

# Check for unused indexes
heroku pg:unused-indexes --app codamakutano
```

---

### Monthly Maintenance

```bash
# Backup database
heroku pg:backups:capture --app codamakutano

# Download backup for local storage
heroku pg:backups:download --app codamakutano

# Run comprehensive tests
heroku run python coda/manage.py test_phase2_comprehensive --app codamakutano

# Review and retrain AI models
heroku run python coda/manage.py retrain_ai_models --app codamakutano

# Analyze performance trends
python coda/manage.py analyze_task_history --start_date YYYY-MM-01 --end_date YYYY-MM-DD

# Clean up old data (if applicable)
heroku run python coda/manage.py cleanup_old_data --days 365 --app codamakutano
```

---

### Quarterly Maintenance

- Review and optimize database indexes
- Analyze performance metrics and trends
- Update dependencies and security patches
- Conduct security audit
- Review and update documentation
- Plan capacity upgrades if needed

---

## Emergency Procedures

### Application Down

**Immediate Actions:**
```bash
# Check Heroku status
heroku status

# Check application logs
heroku logs --tail --app codamakutano | tail -100

# Restart dynos
heroku restart --app codamakutano

# Check dyno status
heroku ps --app codamakutano
```

**If Still Down:**
```bash
# Scale up dynos
heroku ps:scale web=2 --app codamakutano

# Rollback to previous version
heroku rollback --app codamakutano
```

---

### Data Corruption

**Immediate Actions:**
```bash
# Stop accepting new data
heroku maintenance:on --app codamakutano

# Capture current state
heroku pg:backups:capture --app codamakutano

# Assess damage
heroku run python coda/manage.py validate_data_quality --app codamakutano
```

**Recovery:**
```bash
# If recent corruption, restore from backup
heroku pg:backups:restore <backup_id> --app codamakutano

# If data can be fixed, run fix scripts
heroku run python coda/manage.py fix_taskhistory_dates --app codamakutano

# Re-enable application
heroku maintenance:off --app codamakutano
```

---

### Security Breach

**Immediate Actions:**
1. **Isolate:** Take application offline
2. **Assess:** Review logs for unauthorized access
3. **Rotate:** Change all API keys and secrets
4. **Restore:** Deploy from known-good backup
5. **Monitor:** Watch for further suspicious activity

```bash
# Take offline
heroku maintenance:on --app codamakutano

# Rotate secrets
heroku config:set SECRET_KEY=new_secret_key --app codamakutano
heroku config:set OPENAI_API_KEY=new_key --app codamakutano

# Review access logs
heroku logs --num 5000 --app codamakutano | grep "POST\|DELETE\|PUT"

# Restore from backup if needed
heroku pg:backups:restore <backup_id> --app codamakutano

# Bring back online
heroku maintenance:off --app codamakutano
```

---

## Best Practices

### Code Quality
- Write comprehensive tests for all new features
- Use type hints in Python code
- Follow PEP 8 style guidelines
- Document complex logic with comments
- Review code before deployment

### Database Management
- Run migrations in off-peak hours
- Always backup before major changes
- Monitor database size and performance
- Clean up old data regularly
- Use indexes strategically

### Deployment
- Test thoroughly in local environment
- Deploy to UAT before production
- Run smoke tests after deployment
- Monitor logs immediately after deployment
- Have rollback plan ready

### Security
- Keep dependencies updated
- Rotate API keys regularly
- Use environment variables for secrets
- Implement rate limiting
- Monitor for suspicious activity

---

## Support Contacts

### Technical Support
- **Heroku Support:** https://help.heroku.com/
- **Django Documentation:** https://docs.djangoproject.com/
- **Internal Team:** [Contact information]

### Emergency Contacts
- **System Administrator:** [Contact]
- **Database Administrator:** [Contact]
- **Development Lead:** [Contact]

---

## References

- **System Overview:** `01_SYSTEM_OVERVIEW_AND_ARCHITECTURE.md`
- **Implementation Guide:** `02_IMPLEMENTATION_AND_DEPLOYMENT.md`
- **Data Analysis Guide:** `03_DATA_ANALYSIS_AND_AI_FEATURES.md`
- **UI Testing Guide:** `04_UI_TESTING_GUIDE.md`
- **Heroku Documentation:** https://devcenter.heroku.com/
- **Django Troubleshooting:** https://docs.djangoproject.com/en/stable/howto/error-reporting/

