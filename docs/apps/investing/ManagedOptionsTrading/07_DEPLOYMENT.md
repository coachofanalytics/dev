# Managed Options Trading - Deployment
**Feature:** CODA Managed Options Trading Service  
**Date:** October 22, 2025  
**Status:** 🚀 Deployment Guide

---

## 🚀 Deployment Checklist

### **Pre-Deployment**
- [ ] All tests passing (unit, integration, E2E)
- [ ] Code review completed
- [ ] Documentation complete
- [ ] Database migrations ready
- [ ] Environment variables configured
- [ ] Backup system tested
- [ ] Legal agreements signed
- [ ] Client onboarded and trained

### **Deployment Steps**

#### **1. Database Migration**
```bash
# UAT Environment
git push heroku-uat 25.10_CODA_UAT_CM:main
heroku run "cd coda && python manage.py migrate" --app codamakutano

# Verify migration
heroku run "cd coda && python manage.py showmigrations investing" --app codamakutano
```

#### **2. Verify Deployment**
```bash
# Check URLs
heroku run "cd coda && python manage.py show_urls | grep managed" --app codamakutano

# Test access
curl https://codamakutano.herokuapp.com/investing/managed/accounts/
```

#### **3. Configure Scheduled Jobs**
```bash
# Setup daily monitoring
heroku run "cd coda && python manage.py crontab add" --app codamakutano

# Verify cron jobs
heroku run "cd coda && python manage.py crontab show" --app codamakutano
```

### **Post-Deployment**
- [ ] Test all URLs in UAT
- [ ] Verify first client can access portal
- [ ] Execute test position
- [ ] Verify monitoring alerts
- [ ] Test report generation
- [ ] Monitor for 24 hours

---

## 🔄 Rollback Plan

If critical issues found:
```bash
# Rollback deployment
git reset --hard HEAD~1
git push heroku-uat 25.10_CODA_UAT_CM:main --force

# Revert migrations
heroku run "cd coda && python manage.py migrate investing XXXX" --app codamakutano
```

---

## 📊 Go-Live Plan

### **Week 1: UAT Testing**
- Deploy to UAT
- Internal testing
- Client UAT
- Fix any issues

### **Week 2: Production Launch**
- Deploy to production
- Execute first client trades
- Monitor closely
- 24/7 availability

---

**Previous Phase:** [06_MAINTENANCE.md](06_MAINTENANCE.md)  
**Return to:** [README.md](README.md)

