# Database Cursor Error Fix
**Error:** `InvalidCursorName: cursor "_django_curs_15300_sync_4" does not exist`  
**Location:** `/finance/food/record-purchase/`  
**Date:** October 28, 2025  
**Status:** 🔍 INVESTIGATING

---

## 🚨 THE ERROR

```
InvalidCursorName at /finance/food/record-purchase/
cursor "_django_curs_15300_sync_4" does not exist

Request Method: GET
Request URL: http://127.0.0.1:8080/finance/food/record-purchase/
Django Version: 3.2.6
Exception Location: django\db\models\sql\compiler.py, line 1178, in execute_sql
```

---

## 🔍 ROOT CAUSE ANALYSIS

### **What This Error Means:**
PostgreSQL cursor errors typically occur when:
1. **Database connection was closed** while a query was still active
2. **Transaction rolled back** but query tried to continue
3. **Connection pool issue** (stale connection)
4. **Long-running query** that exceeded timeout
5. **Concurrent access** to same cursor

### **Common Causes:**
- Database connection timeout
- Stale database connection in pool
- PostgreSQL server restart/disconnect
- `select_for_update()` with closed transaction
- Database connection settings issue

---

## ✅ SOLUTIONS (Try in Order)

### **Solution 1: Restart Local Server (EASIEST)**
```bash
# Stop server (Ctrl+C)
# Restart
python manage.py runserver 8080
```

**Why:** Clears stale database connections

---

### **Solution 2: Close All Database Connections**
```bash
cd coda
python manage.py shell -c "from django.db import connection; connection.close(); print('✅ Connections closed')"
```

Then restart server.

---

### **Solution 3: Check Database Connection Settings**

**File:** `coda/coda_project/coda_settings/local_settings.py`

**Look for:**
```python
DATABASES = {
    'default': {
        # ... 
        'CONN_MAX_AGE': 600,  # Should not be too high
        'OPTIONS': {
            # PostgreSQL specific options
        }
    }
}
```

**Recommended:**
```python
'CONN_MAX_AGE': 0,  # Close connections immediately (for dev)
# OR
'CONN_MAX_AGE': 60,  # Max 60 seconds
```

---

### **Solution 4: Check for Unclosed Cursors in View**

**File:** `coda/finance/views_food.py` (line 210)

The `record_food_purchase` view uses:
```python
form = FoodPurchaseForm(request.POST)
```

**Check if form queries:**
```python
class FoodPurchaseForm:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Are there any raw SQL queries here?
        # Are there any select_for_update() calls?
```

**Most Likely Cause:** The form's `__init__` is querying `Food.objects.filter()` or similar, and the cursor is being closed before the template renders.

---

## 🔧 IMMEDIATE FIX (Try This First)

### **Quick Fix: Restart Server**
```bash
# Press Ctrl+C to stop server
# Then restart:
cd coda
python manage.py runserver 8080
```

**Then refresh the page:** http://127.0.0.1:8080/finance/food/record-purchase/

**Expected:** Should load without error

---

## 📋 IF ERROR PERSISTS

### **Check 1: Database Connection**
```bash
cd coda
python manage.py shell -c "from django.db import connection; connection.ensure_connection(); print('✅ DB connected')"
```

### **Check 2: Form Querysets**
The error might be in `FoodPurchaseForm.__init__()` - check if it's doing:
```python
self.fields['food_item'].queryset = Food.objects.all()  # Might be causing cursor issue
```

**Fix:** Use `iterator()` or ensure queryset is evaluated before rendering:
```python
self.fields['food_item'].queryset = Food.objects.all().select_related('...')
```

---

## 💡 PREVENTIVE MEASURES

### **1. Use Connection Pooling Properly**
```python
# In settings
DATABASES = {
    'default': {
        'CONN_MAX_AGE': 60,  # Reuse connections for 60 sec
        'ATOMIC_REQUESTS': True,  # Wrap views in transactions
    }
}
```

### **2. Close Connections in Management Commands**
```python
from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    def handle(self, *args, **options):
        try:
            # ... your code ...
        finally:
            connection.close()  # Always close
```

### **3. Use select_related/prefetch_related**
```python
# In forms __init__
self.fields['food_item'].queryset = Food.objects.select_related(
    'category', 'subcategory'
).filter(is_active=True)
```

---

## 🎯 RECOMMENDED ACTION

**IMMEDIATE:** Restart local server (Solution 1)

**IF PERSISTS:** Check `local_settings.py` for `CONN_MAX_AGE` setting

**IF STILL PERSISTS:** Check `FoodPurchaseForm.__init__()` for cursor-holding queries

---

**Note:** This is a **local development issue**, not related to our GoToMeeting deployment to production.

---

**Error Analyzed:** October 28, 2025  
**Severity:** MEDIUM (affects local dev, not production)  
**Quick Fix:** Restart server  
**Root Cause:** Stale PostgreSQL cursor/connection

