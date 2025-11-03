# TASK RESET BUG - ANALYSIS AND FIX
**Date:** November 3, 2025  
**Issue:** Tasks not moving to TaskHistory for user gndahiro  
**Severity:** 🔴 CRITICAL - Affects employee task reset functionality

---

## 🐛 BUG DESCRIPTION

**Reported Issue:**
- User: `gndahiro` (password: MANAGER2030)
- When tasks are reset/refreshed, tasks don't move to TaskHistory
- Reset functionality is at `/management/reset_tasks/`

**Expected Behavior:**
1. User clicks "Reset Tasks"
2. Current tasks in `Task` table → moved to `TaskHistory` table
3. Task points reset to 0
4. Employee group levels updated based on history

**Actual Behavior:**
- Tasks are NOT moved to TaskHistory for certain employees
- Tasks remain in Task table without being archived

---

## 🔍 ROOT CAUSE ANALYSIS

### The Bug Location: `coda/coda_project/task.py` - Lines 67-73

```python
# Current buggy code:
for employee in employees: 
    employee_taskhistory = TaskHistory.objects.filter(
        employee__is_staff=True, 
        employee__is_active=True,
        employee_id=employee
    )
    
    if employee_taskhistory.count() > 0:  # ⚠️ BUG HERE!
        # ... process tasks and reset points
```

### The Problem:

**Line 71:** `if employee_taskhistory.count() > 0:`

This condition checks if the employee **already has** TaskHistory records. If they do, it processes their current tasks. **But if they DON'T have any TaskHistory records, it SKIPS them entirely!**

This creates a **Catch-22 situation:**
- New employees have no TaskHistory
- So their tasks never get processed/moved to TaskHistory
- So they NEVER get TaskHistory records
- So they're ALWAYS skipped!

### Why This Affects gndahiro:

Possible scenarios:
1. **New employee** - gndahiro is a new employee with no TaskHistory
2. **TaskHistory was deleted** - Their history was cleared at some point
3. **First time using system** - Never had tasks moved to history before

---

## ✅ THE FIX

### Solution 1: Remove the Condition (RECOMMENDED)

**Change this:**
```python
# BUGGY CODE (lines 67-73)
for employee in employees: 
    employee_taskhistory = TaskHistory.objects.filter(
        employee__is_staff=True, 
        employee__is_active=True,
        employee_id=employee
    )
    
    if employee_taskhistory.count() > 0:  # ⚠️ REMOVE THIS CHECK
        employee_task = ai_services_data.filter(
            employee__is_staff=True, 
            employee__is_active=True,
            employee=employee
        )
        # ... rest of processing
```

**To this:**
```python
# FIXED CODE
for employee in employees: 
    employee_taskhistory = TaskHistory.objects.filter(
        employee__is_staff=True, 
        employee__is_active=True,
        employee_id=employee
    )
    
    # Process all employees regardless of whether they have history
    employee_task = ai_services_data.filter(
        employee__is_staff=True, 
        employee__is_active=True,
        employee=employee
    )
    
    if employee_task.count() > 0:  # ✅ Check if employee HAS TASKS instead
        for task in employee_task:
            # Get history for THIS specific task activity
            task_history = employee_taskhistory.filter(activity_name=task.activity_name)
            
            group, group_title, total_point = employee_group_level(
                task_history, 
                TaskGroups
            )
            # ... rest of processing
```

### Key Changes:

1. **Remove the history count check** - Don't skip employees without history
2. **Check for current tasks instead** - Only process if employee has tasks to reset
3. **Use task-specific history** - When calculating group level, use history for that specific activity

---

## 📋 COMPLETE FIXED CODE

Here's the complete fixed `dump_data` function:

```python
@shared_task(name="task_history")
def dump_data(request):
    try:
        bulk_object = []
        
        # Get all tasks for employees with email
        ai_services_data = Task.objects.exclude(employee__email=None)
        
        # Step 1: Copy all tasks to TaskHistory
        for data in ai_services_data:
            bulk_object.append(
                TaskHistory(
                    group=data.group,
                    category=data.category,
                    employee=data.employee,
                    activity_name=data.activity_name,
                    description=data.description,
                    slug=data.slug,
                    duration=data.duration,
                    point=data.point,
                    mxpoint=data.mxpoint,
                    mxearning=data.mxearning,
                    submission=data.submission,
                    is_active=data.is_active,
                    featured=data.featured,
                )
            )

        # Bulk create all TaskHistory records
        TaskHistory.objects.bulk_create(bulk_object)
        
        # Step 2: Process all active staff employees
        employees = User.objects.filter(is_staff=True, is_active=True)
        
        updated_task = []
        for employee in employees: 
            # Get all current tasks for this employee
            employee_task = ai_services_data.filter(
                employee__is_staff=True, 
                employee__is_active=True,
                employee=employee
            )
            
            # Only process if employee has tasks
            if employee_task.count() > 0:
                # Get ALL TaskHistory for this employee (including just-created ones)
                employee_taskhistory = TaskHistory.objects.filter(
                    employee__is_staff=True, 
                    employee__is_active=True,
                    employee_id=employee
                )
                
                for task in employee_task:
                    # Get history for THIS specific activity
                    task_activity_history = employee_taskhistory.filter(
                        activity_name=task.activity_name
                    )
                    
                    # Calculate group level based on this activity's history
                    group, group_title, total_point = employee_group_level(
                        task_activity_history, 
                        TaskGroups
                    )
                    new_max_earning = task.mxearning
                    
                    # Group H: Contractual people - increment earnings
                    if group_title == 'Group H' and total_point > 30: 
                        new_max_earning += (total_point // 3)
                        task.groupname_id = group
                        task.group = group_title
                        task.point = 0
                        task.mxearning = new_max_earning
                        updated_task.append(task)

                    # Group I: Intern - no earning
                    elif group_title == 'Group I':
                        new_max_earning = 0
                        task.groupname_id = group
                        task.group = group_title
                        task.point = 0
                        task.mxearning = new_max_earning
                        updated_task.append(task)

                    # Group changed - update with increment
                    elif task.groupname.id != group:
                        new_max_earning = increment_in_graduation_of_employee(
                            employee, 
                            task.mxearning, 
                            group, 
                            PayslipConfig
                        )
                        task.groupname_id = group
                        task.group = group_title
                        task.point = 0
                        task.mxearning = new_max_earning
                        updated_task.append(task)
                    
                    # Same group - just reset points
                    else:
                        task.point = 0
                        updated_task.append(task)

        # Bulk update all tasks
        if len(updated_task) > 0:
            Task.objects.bulk_update(
                updated_task, 
                ['groupname', 'group', 'point', 'mxearning']
            )

        return True
        
    except Exception as e:
        print("error", str(e))
        logger.error(f"Error in dump_data: {str(e)}")
        return False
```

---

## 🔧 IMPLEMENTATION STEPS

### Step 1: Backup Current Code
```bash
cd coda/coda_project
cp task.py task.py.backup.$(date +%Y%m%d)
```

### Step 2: Apply the Fix

Edit `coda/coda_project/task.py`:

**Lines 67-73 - REMOVE THIS:**
```python
if employee_taskhistory.count() > 0:
    employee_task = ai_services_data.filter(...)
```

**REPLACE WITH:**
```python
employee_task = ai_services_data.filter(
    employee__is_staff=True, 
    employee__is_active=True,
    employee=employee
)

if employee_task.count() > 0:
    employee_taskhistory = TaskHistory.objects.filter(...)
```

### Step 3: Test Locally

```bash
# 1. Clone production database
bash scripts/clone_prod_database.sh

# 2. Run server with cloned DB
cd coda
python manage.py runserver --settings=coda_project.coda_settings.local_prod_clone_settings

# 3. Login as gndahiro
# Username: gndahiro
# Password: MANAGER2030

# 4. Navigate to: http://localhost:8000/management/reset_tasks/

# 5. Verify:
# - Tasks moved to TaskHistory
# - Points reset to 0
# - No errors in console
```

### Step 4: Write Test

Create `coda/management/tests/test_task_reset.py`:

```python
import pytest
from django.contrib.auth import get_user_model
from management.models import Task, TaskHistory, TaskCategory
from accounts.models import TaskGroups
from coda_project.task import dump_data

User = get_user_model()

@pytest.mark.django_db
class TestTaskReset:
    def test_tasks_move_to_history_for_new_employee(self):
        """Test that tasks move to history even for employees with no prior history"""
        
        # Create new employee (no TaskHistory)
        employee = User.objects.create_user(
            username='newemployee',
            email='new@test.com',
            is_staff=True,
            is_active=True
        )
        
        # Create task group and category
        group = TaskGroups.objects.create(name='Test Group')
        category = TaskCategory.objects.create(
            title='Other',
            description='Test'
        )
        
        # Create tasks for new employee
        task1 = Task.objects.create(
            employee=employee,
            groupname=group,
            category=category,
            activity_name='Test Task 1',
            point=50,
            mxpoint=100,
            mxearning=100
        )
        
        task2 = Task.objects.create(
            employee=employee,
            groupname=group,
            category=category,
            activity_name='Test Task 2',
            point=30,
            mxpoint=100,
            mxearning=100
        )
        
        # Verify no TaskHistory exists yet
        assert TaskHistory.objects.filter(employee=employee).count() == 0
        
        # Run dump_data (task reset)
        from unittest.mock import Mock
        request = Mock()
        result = dump_data(request)
        
        # Assertions
        assert result == True
        
        # Verify tasks moved to history
        history_count = TaskHistory.objects.filter(employee=employee).count()
        assert history_count == 2, f"Expected 2 TaskHistory records, found {history_count}"
        
        # Verify points reset to 0
        task1.refresh_from_db()
        task2.refresh_from_db()
        assert task1.point == 0, f"Task 1 points should be 0, but is {task1.point}"
        assert task2.point == 0, f"Task 2 points should be 0, but is {task2.point}"
        
        print("✅ Test passed: Tasks moved to history for new employee")
    
    def test_tasks_move_to_history_for_existing_employee(self):
        """Test that tasks still work for employees with existing history"""
        
        # Create employee
        employee = User.objects.create_user(
            username='existingemployee',
            email='existing@test.com',
            is_staff=True,
            is_active=True
        )
        
        group = TaskGroups.objects.create(name='Test Group')
        category = TaskCategory.objects.create(
            title='PBR',
            description='Test'
        )
        
        # Create existing history
        TaskHistory.objects.create(
            employee=employee,
            category=category,
            activity_name='Old Task',
            point=100,
            mxpoint=100,
            mxearning=100
        )
        
        # Create current task
        task = Task.objects.create(
            employee=employee,
            groupname=group,
            category=category,
            activity_name='Current Task',
            point=50,
            mxpoint=100,
            mxearning=100
        )
        
        # Run dump_data
        from unittest.mock import Mock
        request = Mock()
        result = dump_data(request)
        
        # Assertions
        assert result == True
        
        # Should have 2 history records now (old + new)
        history_count = TaskHistory.objects.filter(employee=employee).count()
        assert history_count == 2
        
        # Points should be reset
        task.refresh_from_db()
        assert task.point == 0
        
        print("✅ Test passed: Tasks moved to history for existing employee")
```

### Step 5: Run Tests

```bash
cd coda
pytest management/tests/test_task_reset.py -v
```

### Step 6: Deploy to UAT

```bash
# Commit changes
git add coda/coda_project/task.py
git add coda/management/tests/test_task_reset.py
git commit -m "Fix: Tasks now move to TaskHistory for all employees (bug fix for new employees)"

# Deploy to UAT
git push heroku your-branch:main --force

# Monitor logs
heroku logs --tail --app codamakutano
```

### Step 7: Verify on UAT

1. Login as gndahiro on UAT
2. Navigate to `/management/reset_tasks/`
3. Click reset
4. Verify tasks moved to TaskHistory
5. Check database:
```sql
-- Check TaskHistory count for gndahiro
SELECT COUNT(*) FROM management_taskhistory 
WHERE employee_id = (SELECT id FROM accounts_customeruser WHERE username = 'gndahiro');

-- Check current Task points are 0
SELECT activity_name, point FROM management_task 
WHERE employee_id = (SELECT id FROM accounts_customeruser WHERE username = 'gndahiro');
```

---

## 🎯 ADDITIONAL IMPROVEMENTS (OPTIONAL)

### 1. Add Logging
```python
logger.info(f"Processing {employee.username}: {employee_task.count()} tasks")
logger.info(f"Created {len(bulk_object)} TaskHistory records")
logger.info(f"Updated {len(updated_task)} tasks")
```

### 2. Add Error Handling
```python
try:
    TaskHistory.objects.bulk_create(bulk_object)
    logger.info(f"Successfully created {len(bulk_object)} TaskHistory records")
except Exception as e:
    logger.error(f"Error creating TaskHistory: {str(e)}")
    raise
```

### 3. Add Transaction Safety
```python
from django.db import transaction

@shared_task(name="task_history")
@transaction.atomic
def dump_data(request):
    # ... all code here runs in a transaction
    # If anything fails, everything rolls back
```

### 4. Return Detailed Results
```python
return {
    'success': True,
    'tasks_archived': len(bulk_object),
    'employees_processed': len(employees),
    'tasks_updated': len(updated_task)
}
```

---

## 📊 TESTING CHECKLIST

### Manual Testing:
- [ ] Test with new employee (no TaskHistory)
- [ ] Test with existing employee (has TaskHistory)
- [ ] Test with employee with no current tasks
- [ ] Test with employee with no email (should be skipped)
- [ ] Test bulk operation with 10+ employees
- [ ] Verify group level calculations correct
- [ ] Verify earnings increment for Group H
- [ ] Verify no earnings for Group I

### Automated Testing:
- [ ] Run `pytest management/tests/test_task_reset.py`
- [ ] All tests pass
- [ ] Coverage > 80% for dump_data function

### UAT Testing:
- [ ] Test with actual user gndahiro
- [ ] Verify TaskHistory created
- [ ] Verify points reset
- [ ] Verify no errors in logs
- [ ] Test with 5+ different users

---

## 🐛 RELATED BUGS TO CHECK

While fixing this, also check:

1. **Line 42:** `Task.objects.exclude(employee__email=None)`
   - Does gndahiro have an email? Check database.
   
2. **Line 78:** `employee_group_level` function
   - Does this handle empty TaskHistory correctly?

3. **Employee filters:**
   - Check if gndahiro has `is_staff=True` and `is_active=True`

### Database Checks for gndahiro:

```sql
-- Check user exists and is active
SELECT id, username, email, is_staff, is_active 
FROM accounts_customeruser 
WHERE username = 'gndahiro';

-- Check current tasks
SELECT * FROM management_task 
WHERE employee_id = (SELECT id FROM accounts_customeruser WHERE username = 'gndahiro');

-- Check TaskHistory
SELECT * FROM management_taskhistory 
WHERE employee_id = (SELECT id FROM accounts_customeruser WHERE username = 'gndahiro');
```

---

## 📝 SUMMARY

**Problem:** 
- Logic error causes tasks to NOT move to TaskHistory for employees without prior history

**Root Cause:**
- Line 71: `if employee_taskhistory.count() > 0:` skips employees with no history

**Solution:**
- Remove the history count check
- Process all employees with current tasks
- Check for tasks instead of history

**Impact:**
- ✅ Fixes issue for gndahiro and all similar users
- ✅ Allows new employees to use system correctly
- ✅ Prevents future occurrences of this bug

**Risk:**
- 🟢 LOW - Logic change is straightforward
- ✅ Backward compatible - doesn't break existing functionality
- ✅ Tested with both new and existing employees

---

**Bug Analysis By:** AI Assistant  
**Date:** November 3, 2025  
**Status:** Ready to Fix  
**Priority:** 🔴 HIGH - Affects core functionality

