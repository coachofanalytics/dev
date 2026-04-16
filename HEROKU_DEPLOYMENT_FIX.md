# Heroku Deployment Fix Guide

## Issue Summary
**Error:** Deployment failed due to invalid `chromedriver-py` version  
**App:** codadev (coachofanalytics@gmail.com)  
**Branch:** 26.02_DC48K_UAT_NF  
**Stack:** Heroku-24  
**Buildpack:** heroku/python  

---

## ✅ Fixes Applied

### 1. Fixed chromedriver-py Version
**Problem:** Version `141.0.7390.30b0` doesn't exist in PyPI  
**Solution:** Updated to valid version `141.0.7390.54`

**File:** `requirements.txt` (line 20)
```diff
- chromedriver-py==141.0.7390.30b0
+ chromedriver-py==141.0.7390.54
```

### 2. Created .python-version File
**Problem:** No Python version specified, causing warnings  
**Solution:** Created `.python-version` file with `3.11`

**File:** `.python-version` (NEW)
```
3.11
```

---

## 📋 Pre-Deployment Checklist

Before deploying, verify these files exist and are correct:

- [x] `requirements.txt` - Updated with valid chromedriver-py version
- [x] `.python-version` - Created with Python 3.11
- [x] `Procfile` - Already exists with correct configuration
- [x] `.gitignore` - Does NOT ignore `.python-version`
- [x] `runtime.txt` - Not needed (using `.python-version` instead)

---

## 🚀 Deployment Steps

### Step 1: Commit the Fixes
```bash
cd c:\Users\Fadhiri\Desktop\Work\DC48K\Training\Updatedbranch\dev

# Add the changed files
git add requirements.txt
git add .python-version

# Commit with descriptive message
git commit -m "Fix Heroku deployment: update chromedriver-py version and add .python-version"
```

### Step 2: Push to Heroku
```bash
# Make sure you're on the correct branch
git branch
# Should show: * 26.02_DC48K_UAT_NF

# Push to Heroku
git push heroku 26.02_DC48K_UAT_NF:main
```

**OR** if your Heroku remote is named differently:
```bash
# Check your remotes
git remote -v

# Push to the correct remote (replace 'codadev' if different)
git push codadev 26.02_DC48K_UAT_NF:main
```

### Step 3: Monitor the Build
Watch the build output to ensure:
- ✅ Python 3.11 is installed
- ✅ All dependencies install successfully
- ✅ No errors in the build log
- ✅ Build completes with "Build succeeded"

### Step 4: Run Migrations
```bash
# Heroku will run this automatically via Procfile release command
# But you can run manually if needed:
heroku run python manage.py migrate --app codadev
```

### Step 5: Create Superuser (if needed)
```bash
heroku run python manage.py createsuperuser --app codadev
```

### Step 6: Verify Deployment
```bash
# Open the app
heroku open --app codadev

# Check logs
heroku logs --tail --app codadev
```

---

## 🔍 Troubleshooting

### If Build Still Fails

#### Issue: chromedriver-py version not found
**Solution:** Check available versions and update:
```bash
# Visit: https://pypi.org/project/chromedriver-py/#history
# Or run:
pip index versions chromedriver-py
```

#### Issue: Other dependency conflicts
**Solution:** 
1. Check the error log for the problematic package
2. Update the version in requirements.txt
3. Test locally first: `pip install -r requirements.txt`
4. Commit and push again

#### Issue: Python version mismatch
**Solution:** Update `.python-version` file:
```
# For Python 3.10
3.10

# For Python 3.11 (current)
3.11

# For Python 3.12
3.12
```

### If App Crashes After Deployment

#### Check logs:
```bash
heroku logs --tail --app codadev
```

#### Common issues:

**1. Database not configured**
```bash
# Add PostgreSQL addon
heroku addons:create heroku-postgresql:mini --app codadev
```

**2. Environment variables missing**
```bash
# Set required env vars
heroku config:set SECRET_KEY='your-secret-key' --app codadev
heroku config:set DEBUG=False --app codadev
heroku config:set ENVIRONMENT=production --app codadev

# Set database URL (usually automatic with Heroku Postgres)
# DATABASE_URL will be set automatically
```

**3. Static files not collected**
```bash
heroku run python manage.py collectstatic --noinput --app codadev
```

---

## 📝 Current Procfile Configuration

```procfile
release: python manage.py migrate
web: gunicorn coda_project.wsgi
worker: celery -A coda_project worker --loglevel=info
beat: celery -A coda_project beat --loglevel=info
```

**Note:** This configuration includes Celery workers. If you don't need them on Heroku:
```procfile
release: python manage.py migrate
web: gunicorn coda_project.wsgi
```

---

## 🗄️ Database Configuration

Your `settings.py` already has Heroku database configuration via `dj_database_url`. It will automatically use the `DATABASE_URL` environment variable that Heroku Postgres provides.

**Current setup:**
- Development: SQLite3 (db.sqlite3)
- Production: PostgreSQL (via DATABASE_URL)

---

## 🔐 Required Environment Variables

Make sure these are set on Heroku:

```bash
# Django
heroku config:set SECRET_KEY='your-secret-key-here' --app codadev
heroku config:set DEBUG=False --app codadev
heroku config:set ENVIRONMENT=production --app codadev

# Cloudinary (from your .env file)
heroku config:set CLOUDINARY_CLOUD_NAME=dgi8cg82n --app codadev
heroku config:set CLOUDINARY_API_KEY=239986871426312 --app codadev
heroku config:set CLOUDINARY_API_SECRET=ERuhqJSbGlVZrPJNjGe830BOAqo --app codadev

# Groq API (from your .env file)
heroku config:set GROQ_API_KEY=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 --app codadev

# Email (Mailtrap for testing)
heroku config:set MAILTRAP_USER=65cbef48e3431c --app codadev
heroku config:set MAILTRAP_PASS=acc08784ceac8f --app codadev

# Allowed Hosts
heroku config:set ALLOWED_HOSTS=codadev.herokuapp.com,www.codanalytics.net,codanalytics.net --app codadev
```

---

## 🧪 Testing Locally Before Deployment

```bash
# 1. Activate virtual environment
cd c:\Users\Fadhiri\Desktop\Work\DC48K\Training\Updatedbranch\dev
venv\Scripts\activate

# 2. Install updated dependencies
pip install -r requirements.txt

# 3. Run migrations
python manage.py migrate

# 4. Test the app locally
python manage.py runserver

# 5. Visit http://127.0.0.1:8000 and test critical features
```

---

## 📊 Deployment Checklist

- [ ] Committed all changes to Git
- [ ] Pushed to Heroku (`git push heroku 26.02_DC48K_UAT_NF:main`)
- [ ] Build succeeded (check Heroku dashboard)
- [ ] Migrations ran successfully
- [ ] Environment variables are set
- [ ] App opens without errors
- [ ] Login works
- [ ] Database is connected
- [ ] Static files load correctly
- [ ] No errors in logs (`heroku logs --tail`)

---

## 🎯 Quick Deploy Commands

```bash
# All-in-one deployment
cd c:\Users\Fadhiri\Desktop\Work\DC48K\Training\Updatedbranch\dev
git add requirements.txt .python-version
git commit -m "Fix Heroku deployment issues"
git push heroku 26.02_DC48K_UAT_NF:main

# Monitor deployment
heroku logs --tail --app codadev
```

---

## 📞 Support

If you encounter issues:
1. Check build logs: `heroku logs --num 1500 --app codadev`
2. Check app status: `heroku ps --app codadev`
3. Restart app: `heroku restart --app codadev`
4. Run Django checks: `heroku run python manage.py check --app codadev`

---

## ✅ What Was Fixed

1. ✅ **chromedriver-py version** - Changed from non-existent `141.0.7390.30b0` to valid `141.0.7390.54`
2. ✅ **Python version specification** - Created `.python-version` file with `3.11`
3. ✅ **Removed deployment warnings** - App now explicitly specifies Python version

**Next Step:** Commit and push to Heroku!

---

*Generated: April 16, 2026*  
*App: codadev*  
*Branch: 26.02_DC48K_UAT_NF*
