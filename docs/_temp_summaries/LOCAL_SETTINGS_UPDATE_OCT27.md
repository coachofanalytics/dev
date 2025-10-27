# Local Settings Updated for Cloned Database Support

**Date:** October 27, 2025  
**File Modified:** `coda/coda_project/coda_settings/local_settings.py`  
**Status:** ✅ Complete

---

## 🎯 What Was Changed

Updated `local_settings.py` to **default to using a cloned production database** instead of connecting directly to production.

---

## 📋 Changes Made

### 1. New Default: 'clone' Instead of 'prod'

**Before:**
```python
DB_TYPE = 'prod'  # Dangerous - connects to production!
```

**After:**
```python
DB_TYPE = os.environ.get('DB_TYPE', 'clone').lower()  # Default to 'clone' for safety
```

### 2. New Function: `get_clone_config()`

Added a dedicated configuration function for the cloned database:

```python
def get_clone_config():
    """
    Get configuration for local cloned production database
    This is the RECOMMENDED setup for local development
    """
    return {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'coda_prod_clone',
            'USER': 'postgres',
            'PASSWORD': '',
            'HOST': 'localhost',
            'PORT': '5432',
            'CONN_MAX_AGE': 600,
            'OPTIONS': {
                'connect_timeout': 10,
            }
        }
    }
```

### 3. Enhanced Documentation in Docstring

Added comprehensive usage guide at the top of the file:

```python
"""
DATABASE CONFIGURATION:
=======================

By default, this file uses a CLONED production database for safe local development.

USAGE OPTIONS:
--------------

1. **CLONED DATABASE (RECOMMENDED)** ⭐
   - Uses local PostgreSQL clone of production
   - Safe to test with real production data
   - Isolated from production (no risk!)
   
   Setup:
   # Run once to clone production database
   .\scripts\clone_prod_database.ps1
   
   # Then just run Django normally (default behavior)
   cd coda
   python manage.py runserver
   
   Environment variable: DB_TYPE='clone' (default)

2. **SQLITE DATABASE**
   Usage: $env:DB_TYPE = 'sqlite'

3. **UAT DATABASE** (NOT recommended)
   Usage: $env:DB_TYPE = 'uat'

4. **PRODUCTION DATABASE** ⚠️ NEVER USE FOR TESTING!
   Usage: $env:DB_TYPE = 'prod'
"""
```

### 4. Improved Database Detection Logic

**Before:**
```python
if DB_TYPE in ['uat', 'prod', 'postgres'] or USE_POSTGRESQL:
    # ...
```

**After:**
```python
# RECOMMENDED: Use cloned production database
if DB_TYPE == 'clone':
    print("   ✅ Using CLONED production database (safe for development)")
    return get_clone_config()

# Determine which database to use
if DB_TYPE in ['uat', 'prod', 'postgres'] or USE_POSTGRESQL:
    # ...
```

### 5. Enhanced Warning System

Added clear warnings when using production database:

```python
# Warn if using production database
db_name = DATABASES['default']['NAME']
if 'prod' in db_name.lower() or 'd5ts3j5r06arts' in db_name:
    print("   " + "="*50)
    print("   ⚠️  WARNING: Using PRODUCTION database!")
    print("   ⚠️  This is DANGEROUS - test changes will affect real users!")
    print("   ⚠️  RECOMMENDED: Use DB_TYPE='clone' instead")
    print("   " + "="*50)
elif db_name == 'coda_prod_clone':
    print("      ✅ SAFE: Using cloned database (isolated from production)")
```

### 6. Better Startup Logging

**New output when using clone:**
```
🗄️ Database Configuration:
   DB_TYPE: clone
   USE_POSTGRESQL: False
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

**Output when using production (WARNING):**
```
🗄️ Database Configuration:
   DB_TYPE: prod
==================================================
   ⚠️  WARNING: Using PRODUCTION database!
   ⚠️  This is DANGEROUS - test changes will affect real users!
   ⚠️  RECOMMENDED: Use DB_TYPE='clone' instead
==================================================
```

---

## 🎯 Supported Database Types

### 1. `clone` (Default - RECOMMENDED) ⭐

```powershell
# Uses default - no environment variable needed
cd coda
python manage.py runserver
```

**Configuration:**
- Database: `coda_prod_clone`
- Host: `localhost`
- Port: `5432`
- User: `postgres`

**Benefits:**
- ✅ Real production data
- ✅ Isolated from production
- ✅ Safe to test migrations
- ✅ Safe to experiment

### 2. `sqlite` (Lightweight)

```powershell
$env:DB_TYPE = 'sqlite'
cd coda
python manage.py runserver
```

**Configuration:**
- Database: `db.sqlite3`
- Engine: SQLite3

**Benefits:**
- ✅ No PostgreSQL required
- ✅ Quick setup
- ❌ Not production-like data

### 3. `uat` (Heroku UAT)

```powershell
$env:DB_TYPE = 'uat'
$env:UAT_DATABASE_URL = 'postgres://...'
cd coda
python manage.py runserver
```

**Configuration:**
- Database: Heroku UAT database
- Requires: `UAT_DATABASE_URL`

**Use case:**
- Testing against UAT environment
- NOT recommended for local development

### 4. `prod` (Heroku Production) ⚠️

```powershell
# DANGER: Only use if absolutely necessary!
$env:DB_TYPE = 'prod'
$env:PROD_DATABASE_URL = 'postgres://...'
cd coda
python manage.py runserver
```

**Configuration:**
- Database: Heroku Production database
- Requires: `PROD_DATABASE_URL`

**WARNING:**
- ❌ Changes affect real users
- ❌ No isolation
- ❌ Risky migrations
- ⚠️ **NEVER USE FOR TESTING**

---

## 📖 Additional Documentation Created

### 1. Quick Start Guide

Created: `docs/QUICK_START_LOCAL_DEVELOPMENT.md`

**Contents:**
- 3-step setup guide
- How to switch databases
- Troubleshooting
- Testing migrations
- Refreshing clone

### 2. Clone Script (Windows)

Created: `scripts/clone_prod_database.ps1`

**Features:**
- One-command database clone
- Automatic PostgreSQL detection
- Progress indicators
- Error handling

### 3. Comprehensive Guide

Already exists: `docs/LOCAL_DEVELOPMENT_WITH_PROD_DATA.md`

**Contents:**
- Complete setup guide
- Usage examples
- SQL queries
- Performance testing
- Best practices

---

## 🔄 Migration Path

### Old Workflow (Dangerous):

```powershell
# local_settings.py had: DB_TYPE = 'prod'
cd coda
python manage.py runserver
# ❌ Connected to PRODUCTION database
# ❌ Test changes affected real users
```

### New Workflow (Safe):

```powershell
# One-time: Clone production
.\scripts\clone_prod_database.ps1

# Then just run normally (uses clone by default)
cd coda
python manage.py runserver
# ✅ Connected to CLONED database
# ✅ Test changes isolated from production
```

---

## ✅ Verification

### Check Your Configuration

When you run `python manage.py runserver`, look for:

**✅ GOOD (Using Clone):**
```
DB_TYPE: clone
✅ Using CLONED production database (safe for development)
✅ SAFE: Using cloned database (isolated from production)
```

**⚠️ BAD (Using Production):**
```
DB_TYPE: prod
⚠️  WARNING: Using PRODUCTION database!
⚠️  This is DANGEROUS - test changes will affect real users!
```

### Force Check

```powershell
cd coda
python -c "from coda_project.coda_settings import local_settings"
# Read the output carefully
```

---

## 🎯 Impact

### Before This Change:

- ❌ `local_settings.py` defaulted to **production database**
- ❌ Every developer risked affecting production
- ❌ No clear warning system
- ❌ Testing was dangerous

### After This Change:

- ✅ `local_settings.py` defaults to **cloned database**
- ✅ Safe development by default
- ✅ Clear warnings if using production
- ✅ Easy to switch databases with environment variable

---

## 📊 Configuration Matrix

| DB_TYPE | Default? | Env Var Required? | Safe for Testing? | Use Case |
|---------|----------|-------------------|-------------------|----------|
| `clone` | ✅ Yes | ❌ No | ✅ Yes | **Local development** |
| `sqlite` | ❌ No | ✅ Yes | ✅ Yes | Quick testing |
| `uat` | ❌ No | ✅ Yes | ⚠️ Maybe | UAT testing |
| `prod` | ❌ No | ✅ Yes | ❌ NO | **Never for testing!** |

---

## 🚀 Next Steps for Developers

### First Time Setup:

1. **Clone production database:**
   ```powershell
   .\scripts\clone_prod_database.ps1
   ```

2. **Run Django (uses clone by default):**
   ```powershell
   cd coda
   python manage.py runserver
   ```

3. **Verify in logs:**
   - Look for: `DB_TYPE: clone`
   - Look for: `✅ SAFE: Using cloned database`

### Weekly Maintenance:

1. **Refresh clone (get latest production data):**
   ```powershell
   .\scripts\clone_prod_database.ps1
   ```

### Before Deploying:

1. **Test migrations on clone:**
   ```powershell
   cd coda
   python manage.py makemigrations
   python manage.py migrate
   # If it works on clone → safe for production!
   ```

---

## 🔗 Related Updates

1. **CURSOR_AI_GUIDE.md** - Updated with 12 sections emphasizing clone usage
2. **LOCAL_DEVELOPMENT_WITH_PROD_DATA.md** - Complete setup guide created
3. **QUICK_START_LOCAL_DEVELOPMENT.md** - Quick reference created
4. **clone_prod_database.ps1** - Windows PowerShell clone script created

---

## 💡 Key Takeaways

1. **Default is now safe** - `clone` is the default, not `prod`
2. **Clear warnings** - Production usage shows big red warnings
3. **Easy to switch** - Just set `$env:DB_TYPE`
4. **Well documented** - Multiple guides available
5. **Backward compatible** - Can still use other database types if needed

---

**Created:** October 27, 2025  
**Purpose:** Document local_settings.py changes for cloned database support  
**Result:** Safe-by-default local development! 🎯

