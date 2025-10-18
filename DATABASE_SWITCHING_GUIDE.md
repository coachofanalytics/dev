# Database Switching Guide - Local Development

**Last Updated:** October 18, 2025  
**Feature:** Conditional database selection for local development

## 🎯 Overview

You can now run your local development server connected to **three different databases**:

1. **SQLite (Local)** - Default, no setup required
2. **UAT (Heroku Staging)** - Test with real UAT data
3. **Production (Heroku)** - ⚠️ Use with extreme caution!

## 🚀 Quick Start

### Option 1: Local SQLite (Recommended)

```bash
./runserver_local.sh
```

**Best for:**
- Regular development
- Testing new features
- Fast iteration
- No risk to UAT/production data

### Option 2: UAT Database

```bash
./runserver_uat.sh
```

**Best for:**
- Testing with real data
- Debugging UAT-specific issues
- Data analysis
- Testing migrations before production

### Option 3: Production Database

```bash
./runserver_prod.sh
```

**⚠️ Use with EXTREME CAUTION!**
- You're modifying LIVE data
- Affects REAL users
- Only for emergency debugging
- Always use read-only operations when possible

## 📋 Setup Requirements

### SQLite (No Setup)

✅ Works out of the box - no configuration needed!

### UAT Database

Set environment variables with UAT credentials:

```bash
export HEROKU_DEV_HOST='your-uat-host.amazonaws.com'
export HEROKU_DEV_NAME='your-uat-database-name'
export HEROKU_DEV_USER='your-uat-username'
export HEROKU_DEV_PASS='your-uat-password'
```

**Or create a `.env` file:**

```bash
# .env file
HEROKU_DEV_HOST=your-uat-host.amazonaws.com
HEROKU_DEV_NAME=d1234567890abc
HEROKU_DEV_USER=uabcdefghijklm
HEROKU_DEV_PASS=p1234567890abcdefghijklmnopqrstuvwxyz
```

Then load it:
```bash
source .env
./runserver_uat.sh
```

### Production Database

Set environment variables with production credentials:

```bash
export HEROKU_PROD_HOST='your-prod-host.amazonaws.com'
export HEROKU_PROD_NAME='your-prod-database-name'
export HEROKU_PROD_USER='your-prod-username'
export HEROKU_PROD_PASS='your-prod-password'
```

**Script will ask for confirmation before connecting!**

## 🔧 Advanced Usage

### Manual Database Selection

You can also set the `LOCAL_DB` environment variable manually:

```bash
# SQLite (default)
LOCAL_DB=sqlite ./runserver_local.sh

# UAT
LOCAL_DB=uat python manage.py shell

# Production (with confirmation)
LOCAL_DB=prod python manage.py dbshell
```

### Django Management Commands

Run management commands with specific database:

```bash
# Run migrations on UAT
LOCAL_DB=uat python manage.py migrate

# Create superuser on local SQLite
LOCAL_DB=sqlite python manage.py createsuperuser

# Open shell with production database (CAREFUL!)
LOCAL_DB=prod python manage.py shell
```

### Quick Database Check

```bash
# Check which database you're connected to
LOCAL_DB=uat python manage.py shell

# Then in shell:
>>> from django.db import connection
>>> connection.settings_dict
```

## ⚙️ How It Works

The `local_settings.py` file now checks the `LOCAL_DB` environment variable:

```python
LOCAL_DB = os.environ.get('LOCAL_DB', 'sqlite').lower()

if LOCAL_DB == 'sqlite':
    # Use SQLite database
elif LOCAL_DB == 'uat':
    # Connect to UAT Heroku PostgreSQL
elif LOCAL_DB == 'prod':
    # Connect to Production Heroku PostgreSQL (with warnings!)
```

## 📊 Database Comparison

| Feature | SQLite | UAT | Production |
|---------|--------|-----|------------|
| **Setup** | None required | Need credentials | Need credentials |
| **Speed** | Very fast | Network latency | Network latency |
| **Data** | Local test data | Real UAT data | LIVE production data |
| **Risk** | No risk | Low risk | ⚠️ HIGH RISK |
| **Use For** | Development | Testing, debugging | Emergency only |
| **Migrations** | Safe to test | Test before prod | Be very careful |

## ⚠️ Safety Guidelines

### When Using UAT Database

✅ **Safe Operations:**
- Reading data for analysis
- Testing queries
- Debugging issues
- Running reports
- Creating test users

⚠️ **Be Careful:**
- Creating/modifying data
- Running migrations
- Bulk operations
- Deleting records

### When Using Production Database

❌ **Avoid if possible!**

✅ **Only use for:**
- Emergency debugging
- Read-only data analysis
- Investigating critical bugs
- Quick data fixes (with approval)

❌ **NEVER:**
- Run untested migrations
- Delete data without backups
- Test new features
- Bulk updates without review
- Make changes without approval

## 🛡️ Best Practices

### 1. Always Start with SQLite

```bash
# Default - use for regular development
./runserver_local.sh
```

### 2. Test on UAT Before Production

```bash
# Test your changes on UAT first
LOCAL_DB=uat python manage.py migrate
# If successful, then deploy to production via Heroku
```

### 3. Use Read-Only Queries When Possible

```python
# In Django shell or views
from django.db import connection
connection.ensure_connection()
connection.connection.set_session(readonly=True)
```

### 4. Backup Before Risky Operations

```bash
# On UAT, create a backup first
heroku pg:backups:capture --app codamakutano

# Then proceed with your operation
LOCAL_DB=uat python manage.py migrate
```

### 5. Log Production Database Access

Always document when you connect to production:
- What you're doing
- Why it's necessary
- What queries you ran
- Any changes made

## 🔍 Troubleshooting

### "Database credentials not found"

**Solution:** Set the required environment variables:

```bash
# For UAT
export HEROKU_DEV_HOST='...'
export HEROKU_DEV_NAME='...'
export HEROKU_DEV_USER='...'
export HEROKU_DEV_PASS='...'
```

### "Can't connect to database"

**Check:**
1. Credentials are correct
2. Database host is accessible
3. Firewall allows connection
4. SSL mode is enabled (PostgreSQL on Heroku requires SSL)

**Test connection:**
```bash
psql "postgres://$HEROKU_DEV_USER:$HEROKU_DEV_PASS@$HEROKU_DEV_HOST/$HEROKU_DEV_NAME?sslmode=require"
```

### "Falling back to SQLite"

This happens when credentials are missing or invalid. Check your environment variables.

## 📝 Examples

### Example 1: Analyze UAT Data

```bash
# Connect to UAT
LOCAL_DB=uat python manage.py shell

# In shell
>>> from finance.models import Transaction
>>> Transaction.objects.count()
15234
>>> Transaction.objects.filter(category__isnull=True).count()
42
```

### Example 2: Test Migration on UAT

```bash
# Dry-run first
LOCAL_DB=uat python manage.py migrate --plan

# If looks good, apply
LOCAL_DB=uat python manage.py migrate
```

### Example 3: Create Test User on Local

```bash
# Use SQLite (safe)
LOCAL_DB=sqlite python manage.py createsuperuser
```

### Example 4: Export Data from UAT

```bash
LOCAL_DB=uat python manage.py dumpdata finance.Transaction --indent 2 > uat_transactions.json
```

## 🎓 Environment Variable Reference

### SQLite (No vars needed)

Just run: `./runserver_local.sh`

### UAT Database

```bash
HEROKU_DEV_HOST=your-host.amazonaws.com    # Heroku PostgreSQL host
HEROKU_DEV_NAME=d1234567890abc            # Database name
HEROKU_DEV_USER=uabcdefghijklm            # Database user
HEROKU_DEV_PASS=p1234567890...            # Database password
```

### Production Database

```bash
HEROKU_PROD_HOST=your-prod-host.amazonaws.com
HEROKU_PROD_NAME=d9876543210xyz
HEROKU_PROD_USER=uproduser12345
HEROKU_PROD_PASS=pprod1234567890...
```

## 📞 Getting Credentials

### From Heroku Dashboard

1. Go to your Heroku app
2. Resources tab → Heroku Postgres
3. Settings → View Credentials
4. Copy: Host, Database, User, Password

### From Heroku CLI

```bash
# UAT credentials
heroku config:get DATABASE_URL --app codamakutano

# Production credentials
heroku config:get DATABASE_URL --app codatrainingapp
```

Then parse the URL:
```
postgres://USER:PASSWORD@HOST:5432/DATABASE
```

## ✅ Summary

**Three Scripts, Three Databases:**

1. `./runserver_local.sh` → SQLite (default, safe)
2. `./runserver_uat.sh` → UAT database (for testing)
3. `./runserver_prod.sh` → Production (emergency only!)

**Choose the right tool for the job:**
- Development → SQLite
- Testing/Debugging → UAT
- Emergency only → Production

---

**Last Updated:** October 18, 2025  
**Feature Status:** ✅ Production Ready  
**Safety Level:** Multiple safeguards in place

