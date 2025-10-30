# Heroku Platform API Integration - Maintenance Guide
**Feature:** Platform-Wide Heroku Automation  
**Date:** October 28, 2025  
**Status:** 🔧 Operations Guide

---

## 📅 AUTOMATED OPERATIONS

### **Daily Operations (Fully Automated)**

#### **2:00 AM - Database Backup**
```python
# Celery task: platform_services.daily_backup
# Runs automatically via Celery Beat

# What it does:
- Creates PostgreSQL backup
- Verifies backup integrity
- Downloads to local/Google Drive (optional)
- Cleans up backups older than 30 days
- Sends alert if backup fails

# Monitor:
heroku logs --app codatrainingapp --source worker -t

# Manual trigger if needed:
python manage.py heroku_backup --app codatrainingapp
```

#### **Every 5 Minutes - Health Check**
```python
# Celery task: platform_services.health_check

# Checks:
- Response times (p50, p95, p99)
- Error rates
- Memory usage
- Database connections
- Dyno status

# Alerts if:
- Response time p95 > 2000ms
- Error rate > 5%
- Memory usage > 85%
- Any dyno down

# View health status:
python manage.py heroku_health_check --app codatrainingapp
```

#### **Every 30 Minutes - Auto-Scaling**
```python
# Celery task: platform_services.auto_scale

# Scales based on:
- Time of day
- Day of month (month-end rush)
- Trading hours (for ManagedOptionsTrading)
- Performance metrics

# Example scaling:
Night (12 AM - 6 AM): web=1, worker=1
Business (8 AM - 6 PM): web=2, worker=2
Month-end (days 28-31): web=3, worker=2

# View current scaling:
heroku ps --app codatrainingapp
```

#### **Every Hour - Security Audit**
```python
# Celery task: platform_services.security_audit

# Checks:
- SSL/TLS enforcement
- Secret key age (rotate if >90 days)
- OAuth token security
- Database encryption
- Unauthorized config changes

# Auto-remediates:
- Reverts unauthorized config changes
- Rotates expired secrets (with testing)
- Enables SSL if disabled

# View security score:
python manage.py heroku_security_audit --app codatrainingapp
```

---

## 📆 WEEKLY OPERATIONS

### **Monday 3:00 AM - Backup Cleanup**
```bash
# Celery task: platform_services.cleanup_old_backups

# Deletes backups older than 30 days
# Keeps:
- Last 7 daily backups
- Last 4 weekly backups
- Monthly backups (indefinitely)

# Manual cleanup:
python manage.py heroku_cleanup_backups --app codatrainingapp --days 30
```

### **Wednesday 2:00 AM - Performance Analysis**
```bash
# Analyze performance trends
python manage.py heroku_performance_report --app codatrainingapp --period 7d

# Generates report:
- Slow endpoints (p95 > 1000ms)
- N+1 query detection
- Missing database indexes
- Cache hit rates
- Recommendations

# Review report and implement optimizations
```

### **Friday - Cost Optimization Review**
```bash
# Review Heroku costs
python manage.py heroku_cost_report --app codatrainingapp --month current

# Shows:
- Dyno costs (web, worker, breakdown)
- Database costs
- Add-on costs
- Estimated monthly total
- Optimization recommendations

# Example output:
# Current Month Cost: $156.00
# Web Dynos: $50 (2x Hobby @ $25/each)
# Worker Dynos: $25 (1x Hobby @ $25)
# Database: $50 (Standard-0)
# Add-ons: $31 (Papertrail, Redis, etc.)
#
# Recommendations:
# - Scale down web dynos at night (save ~$15/month)
# - Consider switching to Standard-2 DB with auto-scaling (more cost-effective)
```

---

## 📆 MONTHLY OPERATIONS

### **1st of Month - Disaster Recovery Test**
```bash
# CRITICAL: Test disaster recovery monthly

# 1. Create test backup
python manage.py heroku_backup --app codatrainingapp

# 2. Run DR simulation
python manage.py heroku_dr_test --app codatrainingapp

# What it does:
- Creates temporary test app
- Restores latest backup to test app
- Runs data integrity checks
- Tests critical operations
- Measures recovery time
- Deletes test app
- Generates report

# Expected Result:
# ✅ Recovery Time: < 5 minutes
# ✅ Data Integrity: 100%
# ✅ Operations Functional: All passed

# Alert if:
- Recovery time > 5 minutes
- Data integrity < 100%
- Any critical operation fails

# Document results
```

### **15th of Month - Secret Rotation**
```bash
# Rotate secrets (90-day policy)

# Automatic rotation (if enabled):
python manage.py heroku_rotate_secrets --app codatrainingapp --auto

# Manual rotation (safer for critical secrets):
python manage.py heroku_rotate_secrets --app codatrainingapp --manual

# Secrets rotated:
- SECRET_KEY (Django)
- GOOGLE_CLIENT_SECRET
- STRIPE_SECRET_KEY
- API keys (GoToMeeting, OptionPlay, etc.)

# Process:
1. Generate new secret
2. Update in UAT
3. Test UAT thoroughly
4. Update in Production
5. Restart dynos
6. Verify functionality
7. Document rotation
```

### **Last Day of Month - Compliance Report**
```bash
# Generate compliance report (SOC 2, financial regulations)

python manage.py heroku_compliance_report --app codatrainingapp --month $(date +%Y-%m)

# Report includes:
- Security audit summary
- Backup verification (100%?)
- DR test results
- Secret rotation log
- Access audit trail
- Incident log
- Uptime statistics (target: 99.99%)

# Export for auditors
python manage.py heroku_compliance_report --export --format pdf
```

---

## 🚨 INCIDENT RESPONSE

### **Alert: High Error Rate**
```bash
# 1. Check error dashboard
heroku logs --app codatrainingapp --tail

# 2. Identify error type
python manage.py heroku_analyze_errors --last 1h

# 3. Common fixes:
# - Memory leak: Restart dynos
heroku ps:restart --app codatrainingapp

# - Database connections: Scale dynos down then up
heroku ps:scale web=1 --app codatrainingapp
heroku ps:scale web=2 --app codatrainingapp

# - Code bug: Rollback deployment
python manage.py heroku_rollback --app codatrainingapp --version previous

# 4. Verify resolution
python manage.py heroku_health_check --app codatrainingapp
```

### **Alert: Slow Response Times**
```bash
# 1. Check current performance
python manage.py heroku_metrics --app codatrainingapp --metric router.latency.p95

# 2. Identify bottleneck
python manage.py heroku_performance_analysis --app codatrainingapp

# 3. Quick fixes:
# - Scale up dynos temporarily
heroku ps:scale web=+2 --app codatrainingapp

# - Upgrade database temporarily
python manage.py heroku_upgrade_database --app codatrainingapp --plan standard-2

# 4. Long-term fixes:
# - Optimize slow queries
# - Add database indexes
# - Implement caching
# - Code optimization
```

### **Alert: Database Connection Limit**
```bash
# 1. Check current connections
heroku pg:info --app codatrainingapp

# 2. Kill idle connections
heroku pg:killall --app codatrainingapp

# 3. Add connection pooling (PgBouncer)
heroku addons:create heroku-postgres:pgbouncer --app codatrainingapp

# 4. Optimize code to use fewer connections
# - Use connection pooling in Django
# - Close connections explicitly
# - Use select_related/prefetch_related
```

### **Alert: Backup Failed**
```bash
# 1. Check error
python manage.py heroku_list_backups --app codatrainingapp

# 2. Retry manually
python manage.py heroku_backup --app codatrainingapp

# 3. If still fails:
# - Check database health
heroku pg:info --app codatrainingapp

# - Check Heroku status
# Visit: https://status.heroku.com

# 4. Alternative: Clone database
python manage.py heroku_clone_database --from codatrainingapp --to backup-$(date +%Y%m%d)
```

---

## 📊 MONITORING DASHBOARDS

### **Primary Dashboard**
**URL:** `/admin/platform/heroku-dashboard/`

**Widgets:**
- App health score (0-100)
- Response times (p50, p95, p99)
- Error rate (last hour)
- Current dyno count
- Database connections
- Memory usage
- Recent deployments
- Recent backups
- Security score
- Cost (current month)

### **Metrics Dashboard**
**URL:** `/admin/platform/heroku-metrics/`

**Charts:**
- Response time trends (24h, 7d, 30d)
- Error rate trends
- Dyno scaling history
- Database performance
- Cost trends

### **Heroku CLI Monitoring**
```bash
# Real-time logs
heroku logs --tail --app codatrainingapp

# Dyno metrics
heroku ps --app codatrainingapp

# Database metrics
heroku pg:info --app codatrainingapp

# Cost estimate
heroku labs:enable runtime-dyno-metadata --app codatrainingapp
```

---

## 🔍 TROUBLESHOOTING GUIDE

### **Issue: API Key Invalid**
**Symptoms:** All Heroku API calls fail with "Unauthorized"

**Fix:**
```bash
# 1. Generate new API key
heroku auth:token

# 2. Update environment variable
heroku config:set HEROKU_API_KEY=new_key --app codatrainingapp

# 3. Restart dynos
heroku ps:restart --app codatrainingapp
```

### **Issue: Backup Verification Fails**
**Symptoms:** Backup created but verification fails

**Diagnosis:**
```bash
# Check backup status
python manage.py heroku_list_backups --app codatrainingapp

# Try manual restoration to test app
python manage.py heroku_restore --app coda-test --backup latest
```

**Fix:**
- If corrupted: Create new backup
- If restoration fails: Check database compatibility
- If data missing: Investigate recent migrations

### **Issue: Auto-Scaling Not Working**
**Symptoms:** Dynos not scaling based on schedule

**Diagnosis:**
```bash
# Check Celery Beat is running
heroku ps --app codatrainingapp | grep beat

# Check recent scaling tasks
heroku logs --app codatrainingapp --source worker --grep "auto_scale"
```

**Fix:**
```bash
# Restart Celery Beat
heroku ps:restart beat.1 --app codatrainingapp

# Manually trigger scaling
python manage.py heroku_scale --app codatrainingapp --auto
```

---

## 📚 DOCUMENTATION MAINTENANCE

### **Update Documentation When:**
- New Heroku service added
- Scaling rules changed
- Alert thresholds changed
- Backup schedule changed
- New environment added

### **Files to Update:**
- `03_ARCHITECTURE.md` - Architecture changes
- `04_IMPLEMENTATION.md` - New services
- `05_TESTING.md` - New tests
- `06_MAINTENANCE.md` (this file) - Operations changes
- `07_DEPLOYMENT.md` - Deployment procedures

---

## ✅ MONTHLY MAINTENANCE CHECKLIST

### **Operations Health:**
- [ ] All daily backups successful (30/30 days)
- [ ] DR test passed (< 5 min recovery)
- [ ] Secrets rotated (90-day policy)
- [ ] Security audits clean (no critical issues)
- [ ] Uptime >99.9%
- [ ] Average response time p95 < 1000ms

### **Cost Optimization:**
- [ ] Review cost report
- [ ] Implement optimization recommendations
- [ ] Remove unused add-ons
- [ ] Optimize dyno scaling rules

### **Documentation:**
- [ ] Update runbooks if procedures changed
- [ ] Document incidents and resolutions
- [ ] Update architecture docs if changed
- [ ] Compliance report generated

### **Team Training:**
- [ ] Review incident responses
- [ ] Update team on new features
- [ ] Conduct DR drill with team
- [ ] Update on-call procedures

---

**Maintenance Guide Complete**  
**Status:** ✅ **READY FOR OPERATIONS**  
**Next:** Deployment procedures (07_DEPLOYMENT.md)

