# Quick Start: Local Development with Cloned Database

**Date:** October 27, 2025  
**Status:** Complete Setup Guide  
**Time to Setup:** 10 minutes

---

## 🎯 What This Does

Sets up your local development environment to use a **cloned copy** of the production database, so you can:
- ✅ Test with **real production data** safely
- ✅ Test migrations before deploying
- ✅ Catch errors before users do
- ✅ Experiment without risk

---

## ⚡ Quick Setup (3 Steps)

### Step 1: Clone Production Database (One-time, ~5 minutes)

```powershell
# In project root
.\scripts\clone_prod_database.ps1
```

Choose **Option 1** when prompted.

**What it does:**
- Downloads production database backup from Heroku
- Creates local PostgreSQL database: `coda_prod_clone`
- Restores all tables and data

**Time:** 5-10 minutes (depending on database size)

---

### Step 2: Run Django (Default uses clone!)

```powershell
cd coda
python manage.py runserver
```

**That's it!** By default, `local_settings.py` now uses the cloned database.

You'll see:
```
🗄️ Database Configuration:
   DB_TYPE: clone
   ✅ Using CLONED production database (safe for development)
   🎯 Using cloned production database
   📍 Database: coda_prod_clone
   📍 Host: localhost (PostgreSQL)
   ✅ Safe to test - isolated from production!
==================================================
   🗄️  Database Details:
      Engine: django.db.backends.postgresql
      Name: coda_prod_clone
      Host: localhost
      Port: 5432
      User: postgres
      ✅ SAFE: Using cloned database (isolated from production)
==================================================
```

---

### Step 3: Test Your Changes

Visit http://localhost:8000 and test with **real production data**!

All changes only affect your local clone - **production is safe**.

---

## 🔄 Switching Databases

### Use SQLite Instead (Quick Testing)

```powershell
$env:DB_TYPE = 'sqlite'
cd coda
python manage.py runserver
```

### Use UAT Database (Testing Against UAT)

```powershell
$env:DB_TYPE = 'uat'
$env:UAT_DATABASE_URL = 'postgres://...'
cd coda
python manage.py runserver
```

### Use Production Database ⚠️ (NOT RECOMMENDED!)

```powershell
# DANGER: Only use if you absolutely must!
$env:DB_TYPE = 'prod'
$env:PROD_DATABASE_URL = 'postgres://...'
cd coda
python manage.py runserver
```

### Back to Clone (Default)

```powershell
Remove-Item Env:\DB_TYPE  # Removes environment variable
cd coda
python manage.py runserver  # Uses default 'clone'
```

---

## 📊 Verifying Your Setup

### Check What Database You're Using

Look for this in the startup logs:

**✅ GOOD (Cloned Database):**
```
   DB_TYPE: clone
   ✅ Using CLONED production database (safe for development)
   🎯 Using cloned production database
   ✅ SAFE: Using cloned database (isolated from production)
```

**⚠️ DANGER (Production Database):**
```
   DB_TYPE: prod
   ⚠️  WARNING: Using PRODUCTION database!
   ⚠️  This is DANGEROUS - test changes will affect real users!
   ⚠️  RECOMMENDED: Use DB_TYPE='clone' instead
```

If you see the WARNING, **STOP IMMEDIATELY** and switch to clone:
```powershell
Remove-Item Env:\DB_TYPE
# Restart Django
```

---

## 🔄 Refreshing the Clone (Weekly)

Production data changes daily. Refresh your clone weekly or before major changes:

```powershell
# Just re-run the clone script
.\scripts\clone_prod_database.ps1
```

Choose **Option 1** again. It will drop the old clone and create a fresh one.

---

## 🧪 Testing Migrations

**ALWAYS test migrations on clone before deploying:**

```powershell
cd coda

# Test migration on cloned database
python manage.py makemigrations
python manage.py migrate

# If it works on clone with real data → safe for production!
```

---

## 📚 Exploring the Data

### Django Shell

```powershell
cd coda
python manage.py shell
```

```python
from finance.models import Transaction, BudgetCategory, BudgetRequest
from accounts.models import CustomerUser

# Explore real production data!
Transaction.objects.count()  # See actual transaction count
BudgetCategory.objects.filter(approval_tier='A')  # Real tier data
CustomerUser.objects.all()[:5]  # Real users (passwords hashed)
```

### SQL Queries

```powershell
# Connect to cloned database
psql -U postgres -d coda_prod_clone
```

```sql
-- See all tables
\dt

-- Query real data
SELECT COUNT(*) FROM finance_transaction;
SELECT name, approval_tier FROM finance_budgetcategory;
```

---

## 🐛 Troubleshooting

### Error: "relation does not exist"

The clone database might be empty or incomplete. Re-run the clone script:

```powershell
.\scripts\clone_prod_database.ps1
```

### Error: "FATAL: password authentication failed"

PostgreSQL requires a password. Update `local_settings.py`:

```python
def get_clone_config():
    return {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'coda_prod_clone',
            'USER': 'postgres',
            'PASSWORD': 'your_password_here',  # ← Add your password
            'HOST': 'localhost',
            'PORT': '5432',
        }
    }
```

### Error: "database 'coda_prod_clone' does not exist"

You haven't run the clone script yet:

```powershell
.\scripts\clone_prod_database.ps1
```

### Want to Use SQLite Instead?

```powershell
$env:DB_TYPE = 'sqlite'
cd coda
python manage.py runserver
```

---

## 📖 Complete Documentation

For detailed information:

- **Complete Guide:** `docs/LOCAL_DEVELOPMENT_WITH_PROD_DATA.md`
- **Why This Matters:** `docs/WHY_ERRORS_HAPPEN.md`
- **Cursor AI Guide:** `docs/01_GETTING_STARTED/CURSOR_AI_GUIDE.md`
- **Clone Script Details:** `scripts/README_CLONE_DATABASE.md`

---

## ✅ Checklist

**Initial Setup:**
- [ ] Ran `.\scripts\clone_prod_database.ps1`
- [ ] Database `coda_prod_clone` created successfully
- [ ] `python manage.py runserver` shows "Using CLONED production database"
- [ ] Visited http://localhost:8000 and saw real data

**Before Every Development Session:**
- [ ] Verify startup logs show: `DB_TYPE: clone`
- [ ] Verify startup logs show: `✅ SAFE: Using cloned database`
- [ ] No production database warnings

**Weekly Maintenance:**
- [ ] Refresh clone: `.\scripts\clone_prod_database.ps1`

---

## 🎯 Key Benefits

| Before (Production DB) | After (Cloned DB) |
|------------------------|-------------------|
| ❌ Testing affects users | ✅ Testing is isolated |
| ❌ Can't experiment | ✅ Experiment freely |
| ❌ Risky migrations | ✅ Safe migration testing |
| ❌ Users find bugs | ✅ You find bugs first |
| ❌ Stressful development | ✅ Confident development |

---

## 💡 Remember

1. **Default is 'clone'** - Safest option, automatically used
2. **Weekly refresh** - Keep clone data current
3. **Test migrations on clone** - Before deploying to production
4. **Check startup logs** - Verify you're using clone
5. **Never test against production** - Use clone instead!

---

**Created:** October 27, 2025  
**Purpose:** Quick reference for local development with cloned database  
**Result:** Safe, confident development with real production data! 🚀

