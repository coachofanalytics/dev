# COMPREHENSIVE TESTING GUIDE

**Feature:** Hybrid Team Assignment with Django Groups + TeamProfile  
**Date:** November 5, 2025  
**Status:** 🧪 Pre-Deployment Testing

---

## ⚠️ MIGRATION SITUATION

**Discovery:** The `accounts` app has no existing migrations (only `__init__.py`).

**This means:**
- All accounts tables were created manually or migrations were deleted
- Cannot use `python manage.py migrate` directly
- Need alternative approach

---

## ✅ RECOMMENDED TESTING APPROACH

### **Option 1: SQL Script (Safest - RECOMMENDED)** ⭐

Use the SQL script I created to add the TeamProfile table:

**File:** `scripts/database/create_team_profile_table.sql`

**Advantages:**
- ✅ Reviewable SQL
- ✅ Idempotent (can run multiple times)
- ✅ Doesn't touch existing tables
- ✅ Clear what it does

**Testing Steps:**
```bash
# 1. Review SQL script
cat scripts/database/create_team_profile_table.sql

# 2. Test on dev database
psql -h localhost -U postgres -d coda_prod_clone -f scripts/database/create_team_profile_table.sql

# 3. Verify table created
psql -h localhost -U postgres -d coda_prod_clone -c "\d accounts_teamprofile"

# 4. Verify indexes
psql -h localhost -U postgres -d coda_prod_clone -c "\d+ accounts_teamprofile"
```

---

### **Option 2: Django Shell (Interactive)**

Create the table via Django's schema editor:

```python
python manage.py shell

>>> from django.db import connection
>>> from accounts.models import TeamProfile
>>> 
>>> # Create table using Django's schema editor
>>> with connection.schema_editor() as schema_editor:
...     schema_editor.create_model(TeamProfile)
...
>>> # Verify
>>> from django.db import connection
>>> with connection.cursor() as cursor:
...     cursor.execute("SELECT COUNT(*) FROM accounts_teamprofile")
...     print(f"Table exists, row count: {cursor.fetchone()[0]}")
```

---

### **Option 3: Manual SQL (Quick Test)**

```sql
-- Connect to database
psql -h localhost -U postgres -d coda_prod_clone

-- Create table
CREATE TABLE accounts_teamprofile (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES auth_user(id) ON DELETE CASCADE,
    priority INTEGER DEFAULT 0,
    total_points INTEGER DEFAULT 0,
    is_manually_assigned BOOLEAN DEFAULT FALSE,
    last_promoted TIMESTAMP WITH TIME ZONE NULL,
    promotion_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_team_priority_points ON accounts_teamprofile(priority, total_points DESC);
CREATE INDEX idx_team_manual ON accounts_teamprofile(is_manually_assigned);
CREATE INDEX idx_team_points ON accounts_teamprofile(total_points);
```

---

## 🧪 COMPREHENSIVE TEST SUITE

### **TEST 1: Table Creation**

```bash
# Run SQL script
psql -h localhost -U postgres -d coda_prod_clone -f scripts/database/create_team_profile_table.sql
```

**Expected Output:**
```
CREATE TABLE
CREATE INDEX
CREATE INDEX
CREATE INDEX
COMMENT
COMMENT
COMMENT
 table_exists | index_count 
--------------+-------------
            1 |           3
```

**Verification:**
```sql
-- Check table exists
SELECT table_name FROM information_schema.tables 
WHERE table_name = 'accounts_teamprofile';

-- Check columns
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'accounts_teamprofile'
ORDER BY ordinal_position;

-- Check indexes
SELECT indexname FROM pg_indexes 
WHERE tablename = 'accounts_teamprofile';
```

✅ **Pass Criteria:**
- Table exists
- 9 columns (id, user_id, priority, total_points, is_manually_assigned, last_promoted, promotion_notes, created_at, updated_at)
- 3 indexes created
- Foreign key to auth_user

---

### **TEST 2: Django Model Recognition**

```python
python manage.py shell

>>> from accounts.models import TeamProfile
>>> print(TeamProfile._meta.db_table)
# Should print: accounts_teamprofile

>>> # Check fields
>>> for field in TeamProfile._meta.fields:
...     print(f"{field.name}: {field.get_internal_type()}")

# Expected:
# id: AutoField
# user: OneToOneField
# priority: IntegerField
# total_points: IntegerField
# is_manually_assigned: BooleanField
# last_promoted: DateTimeField
# promotion_notes: TextField
# created_at: DateTimeField
# updated_at: DateTimeField

>>> # Test creating a record
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> test_user = User.objects.first()
>>> team_profile = TeamProfile.objects.create(user=test_user, priority=100)
>>> print(f"Created: {team_profile}")
>>> team_profile.delete()  # Clean up
```

✅ **Pass Criteria:**
- Model imports successfully
- All fields recognized
- Can create/read/update/delete records

---

### **TEST 3: Create Team Groups**

```bash
python manage.py create_team_groups
```

**Expected Output:**
```
🏗️ Creating Team Groups
======================================================================
  ✅ Created: BOG/Leadership
  ✅ Created: Elite Team
  ✅ Created: Lead Team
  ✅ Created: Support Team
  ✅ Created: Senior Analysts
  ✅ Created: Junior Analysts
  ✅ Created: Senior Trainee
  ✅ Created: Junior Trainee
  ✅ Created: Elementary

======================================================================
📊 SUMMARY:
  ✅ Created: 9
  ⏭️  Already existed: 0
  📂 Total groups: 9
```

**Verification:**
```python
>>> from django.contrib.auth.models import Group
>>> groups = Group.objects.filter(name__in=[
...     'BOG/Leadership', 'Elite Team', 'Lead Team'
... ])
>>> print(f"Groups created: {groups.count()}")  # Should be 3
```

✅ **Pass Criteria:**
- 9 groups created
- No errors
- Groups queryable

---

### **TEST 4: Verify Team Members**

```bash
python manage.py verify_team_members
```

**Expected:** Shows which of the 14 required members exist

**Example Output:**
```
🔍 Verifying Team Members
======================================================================

📂 BOG/LEADERSHIP:
  ✅ Amanda Towe        (amanda_towe)        - ✅ Active | ⚠️ No TeamProfile
  ❌ Chris Maghas       (cmaghas)            - USER NOT FOUND
  ❌ Tirimba Obonyo     (tirimba_obonyo)     - USER NOT FOUND
...

📊 SUMMARY:
  Total Required: 14
  ✅ Found with Profile: X
  ⚠️  User exists, no profile: Y
  ❌ Missing Users: Z
```

**Action:** If users are missing, note them for creation

✅ **Pass Criteria:**
- Command runs without errors
- Shows accurate status for each member
- Identifies missing users

---

### **TEST 5: TeamService - Point Calculation**

```python
python manage.py shell

>>> from main.services.team_service import TeamService
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> 
>>> # Test with a real user
>>> user = User.objects.filter(is_active=True, category=2).first()
>>> if user:
...     points = TeamService.calculate_total_points(user)
...     print(f"User: {user.username}")
...     print(f"Total Points: {points}")
...     
...     # Test point breakdown
...     edu_pts = TeamService._calculate_education_points(user)
...     task_pts = TeamService._calculate_task_points(user)
...     req_pts = TeamService._calculate_requirement_points(user)
...     train_pts = TeamService._calculate_training_points(user)
...     assess_pts = TeamService._calculate_assessment_points(user)
...     
...     print(f"Education: {edu_pts}")
...     print(f"Tasks: {task_pts}")
...     print(f"Requirements: {req_pts}")
...     print(f"Training: {train_pts}")
...     print(f"Assessment: {assess_pts}")
...     print(f"Total: {edu_pts + task_pts + req_pts + train_pts + assess_pts}")
...     assert points == (edu_pts + task_pts + req_pts + train_pts + assess_pts)
...     print("✅ Point calculation correct!")
```

✅ **Pass Criteria:**
- No errors during calculation
- Points sum correctly
- All 5 sources calculate

---

### **TEST 6: TeamService - Assignment**

```python
>>> from django.contrib.auth.models import Group
>>> from accounts.models import TeamProfile
>>> 
>>> # Create test user
>>> test_user = User.objects.create_user(
...     username='test_lead',
...     email='test@example.com',
...     first_name='Test',
...     last_name='Lead'
... )
>>> 
>>> # Test assignment
>>> TeamService.assign_to_category(
...     test_user,
...     'Lead Team',
...     priority=100,
...     is_manual=True
... )
>>> 
>>> # Verify
>>> assert test_user.groups.filter(name='Lead Team').exists()
>>> assert test_user.team_profile.is_manually_assigned == True
>>> assert test_user.team_profile.priority == 100
>>> print("✅ Assignment works!")
>>> 
>>> # Clean up
>>> test_user.delete()
```

✅ **Pass Criteria:**
- User assigned to group
- TeamProfile created
- Fields set correctly

---

### **TEST 7: Manual Assignment Command**

```bash
# Test with existing users only
python manage.py assign_manual_team_members --dry-run
```

**Expected:** Shows what would be assigned

**Then:**
```bash
# Actually assign (only if users exist)
python manage.py assign_manual_team_members
```

**Verification:**
```python
>>> from django.contrib.auth.models import Group
>>> bog = Group.objects.get(name='BOG/Leadership')
>>> print(f"BOG members: {bog.user_set.count()}")
>>> for user in bog.user_set.all():
...     print(f"  • {user.get_full_name()} ({user.username})")
```

✅ **Pass Criteria:**
- Command completes without errors
- Users assigned to correct groups
- TeamProfile records created

---

### **TEST 8: Point Calculation Command**

```bash
python manage.py recalculate_team_points --verbose --dry-run
```

**Expected:** Shows point calculations for non-manual members

**Then:**
```bash
python manage.py recalculate_team_points
```

**Verification:**
```python
>>> from accounts.models import TeamProfile
>>> profiles = TeamProfile.objects.filter(is_manually_assigned=False)
>>> for tp in profiles:
...     print(f"{tp.user.username}: {tp.total_points} points")
```

✅ **Pass Criteria:**
- Points calculated correctly
- Saved to database
- No errors

---

### **TEST 9: Promotion Candidates**

```bash
python manage.py show_promotion_candidates --detailed
```

**Expected:** Shows members with 6,000+ points (if any)

✅ **Pass Criteria:**
- Command runs
- Shows correct candidates
- Point breakdown displayed

---

### **TEST 10: Query Performance**

```python
>>> from django.db import connection, reset_queries
>>> from django.conf import settings
>>> 
>>> # Enable query logging
>>> settings.DEBUG = True
>>> 
>>> # Test query
>>> reset_queries()
>>> members = User.objects.filter(
...     groups__name='Lead Team',
...     is_active=True
... ).select_related('profile', 'team_profile')
>>> member_list = list(members)
>>> 
>>> print(f"Query count: {len(connection.queries)}")
>>> print("Queries:")
>>> for q in connection.queries:
...     print(f"  {q['sql'][:100]}...")
```

✅ **Pass Criteria:**
- Query count < 5 for single category
- Uses select_related properly
- No N+1 queries

---

## 📊 TEST RESULTS (To Be Updated)

| Test | Status | Notes |
|------|--------|-------|
| Table Creation | ⏳ Pending | SQL script created |
| Model Recognition | ⏳ Pending | Awaiting table |
| Create Groups | ⏳ Pending | Awaiting table |
| Verify Members | ⏳ Pending | Command ready |
| Assign Manual | ⏳ Pending | Command ready |
| Calculate Points | ⏳ Pending | Command ready |
| Promotion Candidates | ⏳ Pending | Command ready |
| Query Performance | ⏳ Pending | Test script ready |

---

## 🚨 BLOCKING ISSUES

### **Issue 1: No Accounts Migrations**
**Status:** Identified  
**Impact:** Cannot use `python manage.py migrate`  
**Solution:** Use SQL script to create table  
**Risk:** Low - SQL is reviewable and safe

---

## 📝 RECOMMENDATION

**Proceed with SQL-first approach:**

1. ✅ Review SQL script (`scripts/database/create_team_profile_table.sql`)
2. ✅ Run SQL to create table
3. ✅ Test Django model recognition
4. ✅ Test all management commands
5. ✅ Test service layer
6. ✅ Update this report with results

**This is safe because:**
- SQL script is idempotent (IF NOT EXISTS)
- Only creates TeamProfile table
- Doesn't modify existing tables
- Can be rolled back easily

---

**Ready to proceed with SQL approach?**

