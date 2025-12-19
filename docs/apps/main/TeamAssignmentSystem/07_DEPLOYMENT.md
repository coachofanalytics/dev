# Team Assignment System - Deployment

**Feature:** Hybrid Team Assignment with Django Groups + TeamProfile  
**Date:** November 5, 2025  
**Status:** 🚀 Deployment Guide

---

## 🎯 Deployment Overview

### **Deployment Strategy**
1. Dev environment (local testing)
2. UAT environment (stakeholder testing)
3. Production environment (go live)

### **Timeline**
- Dev: Day 1-4 (development & testing)
- UAT: Day 5-6 (UAT deployment & testing)
- Production: Day 7 (production deployment)

---

## 📋 PRE-DEPLOYMENT CHECKLIST

### **Code Quality**
- [ ] All tests pass (50 tests)
- [ ] Code coverage ≥ 80%
- [ ] No linting errors
- [ ] Code reviewed
- [ ] Documentation complete

### **Database**
- [ ] Migration created
- [ ] Migration reviewed (sqlmigrate)
- [ ] Migration tested on dev database
- [ ] Backup plan documented

### **Team Data**
- [ ] All 14 required members verified
- [ ] All usernames confirmed correct
- [ ] Manual assignments defined
- [ ] Points calculation tested

### **Testing**
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual E2E testing complete
- [ ] Performance benchmarks met (<2s, <10 queries)

---

## 🚀 DEPLOYMENT TO DEV

### **Step 1: Verify Environment**

```bash
cd c:\Users\admin\Desktop\project\coda\stg\coda

# Check Python version
python --version  # Should be 3.8+

# Check Django version
python -c "import django; print(django.VERSION)"  # Should be 4.x

# Check database connection
python manage.py check
```

---

### **Step 2: Run Migration**

```bash
# Create migration
python manage.py makemigrations accounts --name create_team_profile

# Review migration SQL
python manage.py sqlmigrate accounts XXXX

# Check migration plan
python manage.py migrate --plan

# Run migration
python manage.py migrate

# Verify table created
python manage.py dbshell
# In psql:
\d accounts_teamprofile
\q
```

---

### **Step 3: Create Team Groups**

```bash
python manage.py create_team_groups
```

**Expected output:**
```
Creating team groups...
  ✅ Created: BOG/Leadership
  ✅ Created: Elite Team
  ✅ Created: Lead Team
  ✅ Created: Support Team
  ✅ Created: Senior Analysts
  ✅ Created: Junior Analysts
  ✅ Created: Senior Trainee
  ✅ Created: Junior Trainee
  ✅ Created: Elementary

✅ Created/verified 9 groups
```

---

### **Step 4: Verify Team Members**

```bash
# Check all required members exist
python manage.py verify_team_members

# If any missing
python manage.py verify_team_members --create-missing
```

---

### **Step 5: Assign Manual Categories**

```bash
# Dry run first
python manage.py assign_manual_team_members --dry-run

# Review output, then actually assign
python manage.py assign_manual_team_members
```

**Expected output:**
```
📂 BOG/LEADERSHIP:
  ✅ Amanda Towe        (amanda_towe)          → bog_leadership (priority: 100)
  ✅ Chris Maghas       (cmaghas)              → bog_leadership (priority: 90)
  ✅ Tirimba Obonyo     (tirimba_obonyo)       → bog_leadership (priority: 80)

📂 ELITE:
  ✅ Chris Maghas       (coda-info)            → elite (priority: 100)

... etc

📊 SUMMARY:
  ✅ Successfully assigned: 10
  ❌ Errors: 0
```

---

### **Step 6: Calculate Points**

```bash
python manage.py recalculate_team_points --verbose
```

**Expected output:**
```
  📊 Points  Bonie Luke                      5,200 pts (no change)      → senior_trainee
  📊 Points  Brenda Nasimiyu                 5,100 pts (no change)      → senior_trainee
  📊 Points  Angel                           4,600 pts (↑ +200)         → junior_trainee
  📊 Points  Eugene                          4,300 pts (no change)      → junior_trainee

📊 SUMMARY:
  ✅ Profiles updated: 4
  🌟 Senior Trainee (5,000-6,000): 2
  📚 Junior Trainee (4,000-5,000): 2
```

---

### **Step 7: Test Locally**

```bash
# Start server
python manage.py runserver

# Test URLs
# http://localhost:8000/about/
# http://localhost:8000/members/team_profiles
# http://localhost:8000/members/future_talents
# http://localhost:8000/members/board
```

**Verify:**
- [ ] BOG/Leadership: 3 members
- [ ] Elite Team: 1 member
- [ ] Lead Team: 3 members
- [ ] Support Team: 2 members
- [ ] Senior Analysts: 1 member
- [ ] Junior Analysts: 1 member
- [ ] Future talents auto-categorized
- [ ] Images load
- [ ] Page loads < 2 seconds

---

## 🌐 DEPLOYMENT TO UAT

### **Step 1: Backup UAT Database**

```bash
heroku pg:backups:capture --app codamakutano

# Verify backup
heroku pg:backups --app codamakutano
```

---

### **Step 2: Deploy Code**

```bash
# Commit changes
git add -A
git commit -m "Add hybrid team assignment system with Django Groups + TeamProfile"

# Push to UAT
git push uat 25.10_CODA_UAT_CM
```

---

### **Step 3: Run Migration on UAT**

```bash
# Run migration
heroku run "cd coda && python manage.py migrate" --app codamakutano

# Verify migration
heroku run "cd coda && python manage.py showmigrations accounts" --app codamakutano
```

---

### **Step 4: Setup Team Data on UAT**

```bash
# Create groups
heroku run "cd coda && python manage.py create_team_groups" --app codamakutano

# Verify members
heroku run "cd coda && python manage.py verify_team_members" --app codamakutano

# Assign manual categories
heroku run "cd coda && python manage.py assign_manual_team_members" --app codamakutano

# Calculate points
heroku run "cd coda && python manage.py recalculate_team_points" --app codamakutano

# Check promotion candidates
heroku run "cd coda && python manage.py show_promotion_candidates" --app codamakutano
```

---

### **Step 5: Test on UAT**

```bash
# Visit UAT
# https://codamakutano.herokuapp.com/members/team_profiles
```

**Complete UAT Testing Checklist:**
- [ ] All categories display
- [ ] Correct member counts
- [ ] Images load
- [ ] Descriptions show
- [ ] Read More/Less works
- [ ] Admin sees points
- [ ] Non-admin doesn't
- [ ] Page loads < 2 seconds
- [ ] No console errors (F12)

---

### **Step 6: Schedule Daily Job on UAT**

```bash
# Add Heroku Scheduler
heroku addons:create scheduler:standard --app codamakutano

# Configure scheduler
heroku addons:open scheduler --app codamakutano

# Add job:
# Command: cd coda && python manage.py recalculate_team_points
# Frequency: Daily at 02:00 UTC
```

---

## 🎉 DEPLOYMENT TO PRODUCTION

### **Prerequisites**
- [ ] UAT testing complete
- [ ] Stakeholder approval
- [ ] No critical bugs
- [ ] Performance acceptable
- [ ] Backup plan ready

---

### **Step 1: Backup Production Database**

```bash
heroku pg:backups:capture --app codatrainingapp

# Download backup locally (safety)
heroku pg:backups:download --app codatrainingapp
```

---

### **Step 2: Deploy Code**

```bash
# Push to production
git push production main

# Or deploy via Heroku
git push heroku main
```

---

### **Step 3: Run Migration**

```bash
# Run migration
heroku run "cd coda && python manage.py migrate" --app codatrainingapp

# Verify
heroku run "cd coda && python manage.py showmigrations accounts" --app codatrainingapp
```

---

### **Step 4: Setup Team Data**

```bash
# Create groups
heroku run "cd coda && python manage.py create_team_groups" --app codatrainingapp

# Verify members
heroku run "cd coda && python manage.py verify_team_members" --app codatrainingapp

# Assign manual categories
heroku run "cd coda && python manage.py assign_manual_team_members" --app codatrainingapp

# Calculate points
heroku run "cd coda && python manage.py recalculate_team_points" --app codatrainingapp
```

---

### **Step 5: Schedule Daily Job**

```bash
heroku addons:create scheduler:standard --app codatrainingapp
heroku addons:open scheduler --app codatrainingapp

# Add job:
# Command: cd coda && python manage.py recalculate_team_points
# Frequency: Daily at 02:00 UTC
```

---

### **Step 6: Verify Production**

```bash
# Test URLs
curl https://codatrainingapp.herokuapp.com/members/team_profiles

# Check logs
heroku logs --tail --app codatrainingapp

# Monitor performance
heroku logs --ps web --app codatrainingapp | grep "team_profiles"
```

---

## 🚨 ROLLBACK PROCEDURES

### **If Critical Issues Occur**

#### **Option 1: Code Rollback**

```bash
# Revert last commit
git revert HEAD

# Push revert
git push uat 25.10_CODA_UAT_CM

# Or rollback Heroku release
heroku rollback --app codamakutano
```

---

#### **Option 2: Database Rollback**

```bash
# Restore from backup
heroku pg:backups:restore BACKUP_ID --app codamakutano --confirm codamakutano

# Verify data
heroku run "cd coda && python manage.py shell" --app codamakutano
```

---

#### **Option 3: Partial Rollback (Disable Feature)**

```python
# In views.py - revert team() view to old logic
# Keep migration (no harm)
# Remove new code, redeploy
```

---

## ✅ POST-DEPLOYMENT CHECKLIST

### **Immediate (Within 1 hour)**
- [ ] All URLs accessible
- [ ] No 500 errors
- [ ] Team categories display
- [ ] Images load
- [ ] No console errors

### **Within 24 Hours**
- [ ] Point calculation runs successfully
- [ ] Performance acceptable
- [ ] No user complaints
- [ ] Monitoring shows green

### **Within 1 Week**
- [ ] Review promotion candidates
- [ ] Check for any issues
- [ ] Gather user feedback
- [ ] Plan enhancements

---

## 📊 Deployment Metrics

### **Success Criteria**

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Uptime | 100% | No downtime during deployment |
| Error Rate | 0% | No 500 errors |
| Page Load | < 2s | Chrome DevTools |
| Query Count | < 10 | Django Debug Toolbar |
| Team Display | 100% | All 14 members show correctly |
| User Satisfaction | High | Stakeholder feedback |

---

## 🎉 GO-LIVE ANNOUNCEMENT

### **Email Template**

```
Subject: New Team Assignment System Live!

Team,

We've deployed the new Team Assignment System with the following improvements:

✅ Accurate team structure (BOG/Leadership, Elite, Lead, Support, Analysts)
✅ Faster page loads (95% query reduction)
✅ Clear progression path for trainees
✅ Automated daily point calculations

Changes:
- /members/team_profiles now shows accurate team hierarchy
- /members/future_talents shows trainees by performance
- Team structure reflects current organization

Questions? See docs/apps/main/TeamAssignmentSystem/

Thanks,
Development Team
```

---

## 📝 Deployment History

### **Template**

```markdown
# Deployment History

## YYYY-MM-DD - UAT Deployment
- **Version:** v1.0
- **Environment:** UAT (codamakutano)
- **Migration:** 0XXX_create_team_profile
- **Status:** ✅ Success
- **Issues:** None
- **Notes:** All tests passed, stakeholder approved

## YYYY-MM-DD - Production Deployment
- **Version:** v1.0
- **Environment:** Production (codatrainingapp)
- **Migration:** 0XXX_create_team_profile
- **Status:** ✅ Success
- **Issues:** None
- **Notes:** Deployed successfully, monitoring shows green
```

---

## 🔧 Environment Configuration

### **Environment Variables**

```bash
# No new environment variables needed!
# Uses existing Django Groups infrastructure
```

---

### **Heroku Configuration**

```bash
# Scheduler addon (if not already installed)
heroku addons:create scheduler:standard --app codamakutano

# Redis (optional, for caching)
heroku addons:create heroku-redis:mini --app codamakutano
```

---

## ✅ DEPLOYMENT COMPLETE

After successful deployment:

1. ✅ Update CURRENT_STATE_AND_ROADMAP.md
2. ✅ Update this deployment log
3. ✅ Notify stakeholders
4. ✅ Monitor for 24-48 hours
5. ✅ Celebrate! 🎉

---

**End of 7-Document Implementation Guide**

**All documents:**
- [README.md](README.md) - Overview
- [01_ANALYSIS.md](01_ANALYSIS.md) - Business case & defects
- [02_REQUIREMENTS.md](02_REQUIREMENTS.md) - Requirements
- [03_ARCHITECTURE.md](03_ARCHITECTURE.md) - System design
- [04_IMPLEMENTATION.md](04_IMPLEMENTATION.md) - Implementation steps
- [05_TESTING.md](05_TESTING.md) - Testing strategy
- [06_MAINTENANCE.md](06_MAINTENANCE.md) - Maintenance guide
- [07_DEPLOYMENT.md](07_DEPLOYMENT.md) - Deployment guide

**Ready to implement!** 🚀

