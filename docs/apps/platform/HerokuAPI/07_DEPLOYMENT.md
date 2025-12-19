# Heroku Platform API Integration - Deployment Guide
**Feature:** Platform-Wide Heroku Automation  
**Date:** October 28, 2025  
**Status:** 🚀 Deployment Guide

---

## 🎯 DEPLOYMENT OVERVIEW

### **Environments:**
1. **Local Development** - Your laptop (uses SQLite or local Postgres)
2. **UAT (Staging)** - `codamakutano.herokuapp.com` (test before production)
3. **Production** - `codatrainingapp.herokuapp.com` (live system)

### **Deployment Strategy:**
```
Local → UAT → Production
  ↓      ↓         ↓
Tests  Tests   Monitored Rollout
```

---

## ⚙️ PREREQUISITES

### **1. Install Heroku CLI**
```bash
# Windows (PowerShell as Admin)
$env:HEROKU_BIN_PATH="C:\Program Files\Heroku\bin"
$env:PATH="$env:HEROKU_BIN_PATH;$env:PATH"
irm https://cli-assets.heroku.com/install.ps1 | iex

# Verify installation
heroku --version
```

### **2. Authenticate with Heroku**
```bash
# Login
heroku login

# Get API key
heroku auth:token

# Save API key (add to environment variables)
# Windows: Environment Variables → New
# Name: HEROKU_API_KEY
# Value: <your-api-key>
```

### **3. Install Python Dependencies**
```bash
cd coda
pip install heroku3
pip install celery[redis]  # For async tasks
```

### **4. Verify Heroku Access**
```bash
# List your apps
heroku apps

# Should see:
# - codamakutano (UAT)
# - codatrainingapp (Production)
```

---

## 🚀 PHASE 1: LOCAL SETUP

### **Step 1: Create Platform Services Directory**
```bash
cd coda
mkdir platform_services
cd platform_services

# Create __init__.py
echo "from .heroku_service import HerokuService" > __init__.py
```

### **Step 2: Configure Settings**

**File: `coda/coda_project/settings/heroku_settings.py`**

```python
# Heroku API Configuration
HEROKU_API_KEY = os.getenv('HEROKU_API_KEY')

# Heroku Apps
HEROKU_APPS = {
    'local': None,  # Local development
    'uat': 'codamakutano',
    'production': 'codatrainingapp',
}

# Get current environment
CURRENT_ENVIRONMENT = os.getenv('ENVIRONMENT', 'local')
CURRENT_HEROKU_APP = HEROKU_APPS.get(CURRENT_ENVIRONMENT)

# Celery Configuration for Heroku Tasks
CELERY_BEAT_SCHEDULE.update({
    'daily-heroku-backup': {
        'task': 'platform_services.daily_backup',
        'schedule': crontab(hour=2, minute=0),
        'args': (HEROKU_APPS['production'],)
    },
    'heroku-health-check': {
        'task': 'platform_services.health_check',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
        'args': (HEROKU_APPS['production'],)
    },
    'heroku-auto-scale': {
        'task': 'platform_services.auto_scale',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
        'args': (HEROKU_APPS['production'],)
    },
    'heroku-security-audit': {
        'task': 'platform_services.security_audit',
        'schedule': crontab(minute=0),  # Every hour
        'args': (HEROKU_APPS['production'],)
    },
})
```

### **Step 3: Test Locally**
```bash
# Test basic functionality
python manage.py shell

>>> from platform_services.heroku_service import HerokuService
>>> service = HerokuService()
>>> apps = service.list_apps()
>>> print([app.name for app in apps['data']])
['codamakutano', 'codatrainingapp']

# Success! ✅
```

### **Step 4: Run Tests**
```bash
# Run unit tests
cd coda
pytest platform_services/tests/ -v

# All tests should pass ✅
```

---

## 🧪 PHASE 2: DEPLOY TO UAT

### **Step 1: Commit Code**
```bash
cd C:\Users\admin\Desktop\project\coda\stg

# Check status
git status

# Add platform services
git add coda/platform_services/
git add coda/coda_project/settings/heroku_settings.py

# Commit
git commit -m "feat: Add Heroku Platform API integration (Phase 1)"
```

### **Step 2: Configure UAT Environment**
```bash
# Set environment variables in UAT
heroku config:set ENVIRONMENT=uat --app codamakutano
heroku config:set HEROKU_API_KEY=<your-api-key> --app codamakutano

# Verify
heroku config --app codamakutano | grep HEROKU
```

### **Step 3: Deploy to UAT**
```bash
# Push to UAT
git push uat 25.10_CODA_UAT_CM

# Or if you have heroku remote configured:
git push heroku main

# Watch deployment
heroku logs --tail --app codamakutano
```

### **Step 4: Run Migrations (if any)**
```bash
# Check for new migrations
heroku run "cd coda && python manage.py showmigrations platform_services" --app codamakutano

# Run migrations
heroku run "cd coda && python manage.py migrate platform_services" --app codamakutano
```

### **Step 5: Verify UAT Deployment**
```bash
# Test Heroku service
heroku run "cd coda && python manage.py shell" --app codamakutano

# In shell:
from platform_services.heroku_service import HerokuService
service = HerokuService()
result = service.list_apps()
print(result)
# Should see your apps! ✅

exit()

# Test management command
heroku run "cd coda && python manage.py heroku_health_check --app codamakutano" --app codamakutano
```

---

## 🎯 PHASE 3: DEPLOY TO PRODUCTION

### **Pre-Deployment Checklist:**
- [ ] All UAT tests passed
- [ ] No critical issues in UAT logs
- [ ] Backup created in Production
- [ ] Team notified of deployment
- [ ] Rollback plan ready

### **Step 1: Create Production Backup**
```bash
# CRITICAL: Always backup before deploying!
heroku run "cd coda && python manage.py heroku_backup --app codatrainingapp" --app codatrainingapp

# Verify backup created
heroku run "cd coda && python manage.py heroku_list_backups --app codatrainingapp" --app codatrainingapp
```

### **Step 2: Configure Production Environment**
```bash
# Set environment variables (only once)
heroku config:set ENVIRONMENT=production --app codatrainingapp
heroku config:set HEROKU_API_KEY=<your-api-key> --app codatrainingapp

# Verify
heroku config --app codatrainingapp | grep ENVIRONMENT
```

### **Step 3: Deploy to Production**
```bash
# Double-check you're deploying to production!
git remote -v

# Push to production
git push production main

# Or:
git push heroku main  # If heroku remote is production

# Watch deployment
heroku logs --tail --app codatrainingapp
```

### **Step 4: Run Migrations**
```bash
# Run migrations
heroku run "cd coda && python manage.py migrate" --app codatrainingapp

# Verify
heroku run "cd coda && python manage.py showmigrations" --app codatrainingapp
```

### **Step 5: Enable Celery Workers**
```bash
# Check current Procfile
heroku ps --app codatrainingapp

# Scale up Celery worker and beat
heroku ps:scale worker=1 beat=1 --app codatrainingapp

# Verify running
heroku ps --app codatrainingapp

# Should see:
# web.1: up
# worker.1: up
# beat.1: up
```

### **Step 6: Add Redis (for Celery)**
```bash
# Check if Redis already exists
heroku addons --app codatrainingapp

# If not, add Redis
heroku addons:create heroku-redis:hobby-dev --app codatrainingapp

# Verify
heroku addons:info heroku-redis --app codatrainingapp
```

### **Step 7: Verify Production Deployment**
```bash
# 1. Check app health
heroku run "cd coda && python manage.py heroku_health_check --app codatrainingapp" --app codatrainingapp

# 2. Test Heroku API integration
heroku run "cd coda && python manage.py shell" --app codatrainingapp

# In shell:
from platform_services.heroku_service import HerokuService
service = HerokuService()
apps = service.list_apps()
print(f"✅ Found {len(apps['data'])} apps")
exit()

# 3. Check Celery tasks running
heroku logs --source worker --tail --app codatrainingapp
# Should see scheduled tasks executing ✅

# 4. Verify backup task
heroku run "cd coda && python manage.py heroku_list_backups --app codatrainingapp" --app codatrainingapp
```

---

## 🚨 ROLLBACK PROCEDURES

### **Scenario 1: Code Bug Detected**
```bash
# 1. Identify previous version
heroku releases --app codatrainingapp -n 10

# Example output:
# v147  Deploy 1234abcd  admin@coda.com  2025/10/28 10:30 (current)
# v146  Deploy 5678efgh  admin@coda.com  2025/10/27 15:20
# v145  Deploy 9012ijkl  admin@coda.com  2025/10/26 12:10

# 2. Rollback to previous version
heroku rollback v146 --app codatrainingapp

# 3. Verify rollback
heroku releases --app codatrainingapp -n 3
# v148  Rollback to v146  admin@coda.com  2025/10/28 10:35 (current)

# 4. Check app health
python manage.py heroku_health_check --app codatrainingapp
```

### **Scenario 2: Database Migration Failed**
```bash
# 1. Identify backup before migration
heroku run "cd coda && python manage.py heroku_list_backups --app codatrainingapp" --app codatrainingapp

# 2. Restore from backup
heroku run "cd coda && python manage.py heroku_restore --app codatrainingapp --backup backup-id" --app codatrainingapp

# 3. Rollback code
heroku rollback v146 --app codatrainingapp

# 4. Verify restoration
# Check database integrity
# Test critical operations
```

### **Scenario 3: Performance Degradation**
```bash
# Quick fix: Scale up resources temporarily
heroku ps:scale web=3 worker=2 --app codatrainingapp

# Check performance
python manage.py heroku_metrics --app codatrainingapp --metric router.latency.p95

# If still slow, investigate or rollback
heroku rollback --app codatrainingapp
```

---

## 📋 POST-DEPLOYMENT CHECKLIST

### **Immediate (Within 10 minutes):**
- [ ] No errors in logs (`heroku logs --tail --app codatrainingapp`)
- [ ] App responding (`curl https://codatrainingapp.herokuapp.com`)
- [ ] Health check passed
- [ ] Celery tasks running
- [ ] No user complaints

### **Within 1 Hour:**
- [ ] Monitor error rates
- [ ] Check response times
- [ ] Verify scheduled tasks executed
- [ ] Review backup creation
- [ ] Update team on deployment status

### **Within 24 Hours:**
- [ ] Review full day's metrics
- [ ] Check for slow endpoints
- [ ] Verify all automated tasks
- [ ] Document any issues
- [ ] Update runbook if needed

---

## 🔧 TROUBLESHOOTING DEPLOYMENT ISSUES

### **Issue: Deployment Fails**
```bash
# Check build logs
heroku logs --app codatrainingapp --source app --tail

# Common causes:
# - Missing dependencies: Update requirements.txt
# - Python version mismatch: Check runtime.txt
# - Collectstatic error: Set DISABLE_COLLECTSTATIC=1

# Fix and redeploy
git add .
git commit -m "fix: deployment issue"
git push production main
```

### **Issue: Celery Workers Not Starting**
```bash
# Check Procfile
cat Procfile

# Should have:
# worker: cd coda && celery -A coda.celeryapp worker -l info
# beat: cd coda && celery -A coda.celeryapp beat -l info

# Scale up if needed
heroku ps:scale worker=1 beat=1 --app codatrainingapp

# Check worker logs
heroku logs --source worker --tail --app codatrainingapp
```

### **Issue: "Heroku API Key Invalid"**
```bash
# Regenerate API key
heroku auth:token

# Update config
heroku config:set HEROKU_API_KEY=new_key --app codatrainingapp

# Restart app
heroku ps:restart --app codatrainingapp
```

---

## 📊 MONITORING POST-DEPLOYMENT

### **Heroku Metrics:**
```bash
# View app metrics
heroku labs:enable log-runtime-metrics --app codatrainingapp

# Monitor response times
heroku logs --tail --app codatrainingapp | grep "ms"

# Monitor errors
heroku logs --tail --app codatrainingapp | grep "error"
```

### **Custom Monitoring:**
```bash
# Health check
python manage.py heroku_health_check --app codatrainingapp

# Performance metrics
python manage.py heroku_metrics --app codatrainingapp --period 1h

# Cost estimate
python manage.py heroku_cost_report --app codatrainingapp
```

---

## ✅ DEPLOYMENT SUCCESS CRITERIA

### **Deployment is Successful When:**
- ✅ App is accessible (https://codatrainingapp.herokuapp.com)
- ✅ No errors in logs for 1 hour
- ✅ Response time p95 < 1500ms
- ✅ Error rate < 1%
- ✅ Celery tasks executing
- ✅ Backups being created
- ✅ Health check score > 80
- ✅ All core features working
- ✅ No user complaints

---

## 🎓 DEPLOYMENT BEST PRACTICES

### **Always:**
- ✅ Deploy during low-traffic hours (2-4 AM)
- ✅ Create backup before deployment
- ✅ Test in UAT first
- ✅ Have rollback plan ready
- ✅ Monitor for 24 hours post-deployment
- ✅ Document changes
- ✅ Notify team

### **Never:**
- ❌ Deploy during business hours (without approval)
- ❌ Deploy during month-end (budget rush)
- ❌ Deploy during trading hours (for ManagedOptionsTrading)
- ❌ Deploy without testing
- ❌ Deploy without backup
- ❌ Deploy and go offline

---

## 📞 SUPPORT CONTACTS

### **Heroku Issues:**
- Heroku Status: https://status.heroku.com
- Heroku Support: https://help.heroku.com

### **CODA Team:**
- Deployment Questions: [Team Channel]
- Emergency Contact: [On-Call Engineer]

---

**Deployment Guide Complete**  
**Status:** ✅ **READY FOR DEPLOYMENT**  
**All 7 Documents Complete!** 🎉

---

## 🎊 CONGRATULATIONS!

You now have **complete documentation** for Heroku Platform API integration!

**What You Have:**
- ✅ Strategic analysis (ROI $319K/year)
- ✅ Detailed requirements (6 services)
- ✅ Complete architecture (service-based, event-driven)
- ✅ Step-by-step implementation guide
- ✅ Comprehensive testing strategy (90%+ coverage)
- ✅ Operations and maintenance procedures
- ✅ Deployment and rollback procedures

**Next Steps:**
1. Review documentation with team
2. Get management approval
3. Start with Phase 1 implementation (2 weeks)
4. Deploy to UAT and test
5. Deploy to Production
6. Monitor and optimize

**This will transform CODA into an outstanding, enterprise-grade platform!** 🚀

