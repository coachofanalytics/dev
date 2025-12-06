# Deployment Process for CODADEV (Heroku)

## 📋 Overview
This document outlines the step-by-step process for deploying code to the **codadev** Heroku application. This is a collaborative app, so all team members should follow these guidelines to ensure smooth deployments.

---

## 🎯 Prerequisites

Before deploying, ensure you have:

1. **Heroku CLI installed** - [Download here](https://devcenter.heroku.com/articles/heroku-cli)
2. **Git configured** with your credentials
3. **Access to the codadev Heroku app** (contact admin if needed)
4. **Heroku remote configured** in your local repository

### Check Heroku CLI Installation
```bash
heroku --version
```

### Login to Heroku
```bash
heroku login
```

---

## 🔧 Initial Setup (One-time)

### 1. Add Heroku Remote
If you haven't added the Heroku remote yet:

```bash
heroku git:remote -a codadev
```

### 2. Verify Remote Configuration
```bash
git remote -v
```

You should see:
```
heroku  https://git.heroku.com/codadev.git (fetch)
heroku  https://git.heroku.com/codadev.git (push)
origin  https://github.com/coachofanalytics/dev.git (fetch)
origin  https://github.com/coachofanalytics/dev.git (push)
```

---

## 🚀 Deployment Process

### Step 1: Prepare Your Branch

1. **Ensure your code is committed**
   ```bash
   git status
   git add .
   git commit -m "Your descriptive commit message"
   ```

2. **Push to GitHub (optional but recommended)**
   ```bash
   git push origin <your-branch-name>
   ```

### Step 2: Deploy to Heroku

**Current deployment branch**: `25.10_DC48_UAT_ND`

#### Option A: Deploy Current Branch (Standard)
```bash
git push heroku 25.10_DC48_UAT_ND:main
```

#### Option B: Force Deploy (if rejected)
⚠️ **Use with caution** - This overwrites the remote branch
```bash
git push heroku 25.10_DC48_UAT_ND:main --force
```

#### Option C: Deploy Different Branch
Replace `<your-branch>` with your branch name:
```bash
git push heroku <your-branch>:main
```

### Step 3: Run Database Migrations

**CRITICAL**: After every deployment that includes model changes, run migrations:

```bash
heroku run python manage.py migrate -a codadev
```

### Step 4: Collect Static Files (if needed)

If static files aren't automatically collected:
```bash
heroku run python manage.py collectstatic --noinput -a codadev
```

### Step 5: Restart the Application

```bash
heroku restart -a codadev
```

---

## 🔍 Verification & Monitoring

### Check Deployment Status
```bash
heroku releases -a codadev --num 5
```

### View Application Logs
```bash
# View recent logs
heroku logs -a codadev --num 100

# Tail logs in real-time
heroku logs -a codadev --tail
```

### Check Running Dynos
```bash
heroku ps -a codadev
```

### Open the Application
```bash
heroku open -a codadev
```

Or visit: **https://codadev.herokuapp.com/**

---

## ⚠️ Common Issues & Solutions

### Issue 1: `NotADirectoryError` for `static`
**Cause**: `static` exists as a file instead of a directory

**Solution**:
```bash
# Delete the file
rm static

# Create directory
mkdir static

# Add .gitkeep to track empty directory
echo "# This ensures static directory is tracked" > static/.gitkeep

# Commit and redeploy
git add static/.gitkeep
git commit -m "Fix: Convert static to directory"
git push heroku <your-branch>:main --force
```

### Issue 2: `relation "table_name" does not exist`
**Cause**: Database migrations not applied

**Solution**:
```bash
heroku run python manage.py migrate -a codadev
```

### Issue 3: Push Rejected (non-fast-forward)
**Cause**: Remote branch has commits you don't have locally

**Solution**:
```bash
# Option 1: Fetch and merge
git fetch heroku
git merge heroku/main

# Option 2: Force push (use with caution)
git push heroku <your-branch>:main --force
```

### Issue 4: Static Files Not Loading
**Cause**: Static files not collected or WhiteNoise misconfigured

**Solution**:
```bash
# Collect static files
heroku run python manage.py collectstatic --noinput -a codadev

# Check settings.py has:
# STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'
# MIDDLEWARE includes 'whitenoise.middleware.WhiteNoiseMiddleware'
```

---

## 📊 Deployment Checklist

Before deploying, ensure:

- [ ] All code changes are committed
- [ ] Tests pass locally (if applicable)
- [ ] Database migrations are created (`python manage.py makemigrations`)
- [ ] `.python-version` file exists with `3.11`
- [ ] `static/` is a directory (not a file)
- [ ] Environment variables are set on Heroku (if new ones added)
- [ ] `requirements.txt` is up to date

After deploying:

- [ ] Migrations run successfully
- [ ] Application starts without errors
- [ ] Static files load correctly
- [ ] Core functionality tested on production
- [ ] Logs checked for errors

---

## 🔐 Environment Variables

### View Current Config
```bash
heroku config -a codadev
```

### Set New Variable
```bash
heroku config:set VARIABLE_NAME=value -a codadev
```

### Unset Variable
```bash
heroku config:unset VARIABLE_NAME -a codadev
```

---

## 🗄️ Database Management

### Access Database Console
```bash
heroku pg:psql -a codadev
```

### Create Database Backup
```bash
heroku pg:backups:capture -a codadev
```

### Download Latest Backup
```bash
heroku pg:backups:download -a codadev
```

### View Database Info
```bash
heroku pg:info -a codadev
```

---

## 👥 Team Collaboration Guidelines

### 1. Communication
- **Announce deployments** in team chat before deploying
- **Document changes** in commit messages
- **Report issues** immediately if deployment fails

### 2. Branch Strategy
- **Main deployment branch**: `25.10_DC48_UAT_ND`
- Create feature branches from main branch
- Test locally before deploying
- Coordinate with team for major changes

### 3. Deployment Schedule
- **Avoid deploying during peak hours** (if possible)
- **Coordinate with team** for database migrations
- **Have rollback plan** for major changes

### 4. Rollback Procedure
If a deployment causes issues:

```bash
# View recent releases
heroku releases -a codadev

# Rollback to previous version
heroku rollback -a codadev

# Or rollback to specific version
heroku rollback v1083 -a codadev
```

---

## 📞 Support & Resources

### Heroku Resources
- **Dashboard**: https://dashboard.heroku.com/apps/codadev
- **Documentation**: https://devcenter.heroku.com/
- **Status**: https://status.heroku.com/

### Team Contacts
- **DevOps Lead**: [Add contact]
- **Tech Lead**: [Add contact]
- **Emergency Contact**: [Add contact]

---

## 📝 Deployment Log Template

Keep a log of deployments for team reference:

```
Date: YYYY-MM-DD HH:MM
Deployed By: [Your Name]
Branch: [Branch Name]
Release Version: [e.g., v1084]
Changes:
- [Change 1]
- [Change 2]
Migrations: [Yes/No]
Issues: [Any issues encountered]
Status: [Success/Failed/Rolled Back]
```

---

## 🔄 Quick Reference Commands

```bash
# Deploy
git push heroku 25.10_DC48_UAT_ND:main

# Migrate
heroku run python manage.py migrate -a codadev

# Restart
heroku restart -a codadev

# Logs
heroku logs -a codadev --tail

# Status
heroku ps -a codadev

# Open app
heroku open -a codadev

# Rollback
heroku rollback -a codadev
```

---

**Last Updated**: 2025-12-06  
**Document Version**: 1.0  
**Maintained By**: Development Team
