# Permissions & Roles - Implementation

**Feature:** Role-Based Access Control  
**Status:** Implemented  
**Last Updated:** October 22, 2025

---

## 📂 CODE LOCATIONS

### Models
**File:** `coda/accounts/models.py`
- `Department` (lines 457-520)
- `UserGroups` (lines 28-35)
- `Team_Members` (lines 796-826)

### Decorators
**File:** `coda/accounts/decorators.py`
- `@staff_required`
- `@admin_required`

### Mixins
**File:** `coda/accounts/mixins.py`
- `StaffRequiredMixin`
- `DepartmentAccessMixin`

---

## 🔑 KEY FUNCTIONS

```python
# Permission check
if user.is_staff:
    # Allow staff access
    
if user.is_admin:
    # Allow admin access
```

---

**See:** 05_TESTING.md


