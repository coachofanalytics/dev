# Field Definitions Summary - Complete Reference

**Date:** December 28, 2024  
**Status:** ✅ All fields are already added - use this as reference for verification

**Note:** This document consolidates information from `FIELDS_TO_ADD.md` (manual addition guide) and provides a complete reference for all department field definitions.

---

## 📋 Complete Field Definitions

### 1. Task Model - Department Field

**Location:** `coda/management/models.py` (after `employee` field)

```python
department = models.ForeignKey(
    Department,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name="tasks",
    help_text=_("Department this task belongs to (snapshot)."),
)
```

---

### 2. TaskHistory Model - Department Field

**Location:** `coda/management/models.py` (after `employee` field)

```python
department = models.ForeignKey(
    Department,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name="task_histories",
    help_text=_("Department snapshot at the time this history was created."),
)
```

---

### 3. Required Import

**Location:** `coda/management/models.py` (top of file)

```python
from shared_core.users import CustomerUser, Department
```

---

### 4. TaskResetService - Copy Department

**Location:** `coda/management/services/task_reset_service.py` (line ~159)

```python
TaskHistory(
    group=task.group,
    category=task.category,
    employee=task.employee,
    department=task.department,  # Copy department snapshot
    activity_name=task.activity_name,
    # ... rest of fields ...
)
```

---

### 5. Indexes (Already Added)

**Task.Meta.indexes:**
- `models.Index(fields=['department'])`
- `models.Index(fields=['department', 'is_active'])`
- `models.Index(fields=['employee', 'department', 'is_active'])`

**TaskHistory.Meta.indexes:**
- `models.Index(fields=['department'])`
- `models.Index(fields=['employee', 'department'])`

---

## ✅ Verification Status

All fields are verified as present:
- ✅ `Task.department` - Line ~358
- ✅ `TaskHistory.department` - Line ~650
- ✅ `TaskResetService` copies department - Line ~159
- ✅ Indexes are in place
- ✅ Department import is present

---

## 📝 Quick Reference for Manual Addition

If you need to add these fields manually, here are the exact code blocks:

### Block 1: Task Department Field
```python
department = models.ForeignKey(
    Department,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name="tasks",
    help_text=_("Department this task belongs to (snapshot)."),
)
```

### Block 2: TaskHistory Department Field
```python
department = models.ForeignKey(
    Department,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name="task_histories",
    help_text=_("Department snapshot at the time this history was created."),
)
```

### Block 3: TaskResetService Department Copy
```python
department=task.department if task.department else None,
```

### Block 4: Required Import
```python
from shared_core.users import CustomerUser, Department
```

### Block 5: Task Model Indexes
```python
# In Task.Meta.indexes:
models.Index(fields=['department', 'is_active']),
models.Index(fields=['employee', 'department', 'is_active']),
```

### Block 6: TaskHistory Model Indexes
```python
# In TaskHistory.Meta.indexes:
models.Index(fields=['department']),
models.Index(fields=['employee', 'department']),
```

## 🎯 Key Points

1. **Both fields are nullable** (`null=True, blank=True`) - safe for existing data
2. **SET_NULL on delete** - preserves data if department is deleted
3. **Related names** - `tasks` (plural) and `task_histories` (plural)
4. **Snapshot concept** - TaskHistory stores department at creation time
5. **Indexes** - For query performance on common filters

## 🚀 Next Steps

Since fields are already added, proceed with incremental migrations:

1. **Delete existing migrations:**
   ```bash
   rm coda/management/migrations/0001_add_department_fields.py
   rm coda/management/migrations/0002_backfill_department_fields.py
   ```

2. **Create fresh migrations incrementally:**
   - Step 1: Task only
   - Step 2: TaskHistory only  
   - Step 3: Indexes

---

**Ready to proceed with migrations!**




