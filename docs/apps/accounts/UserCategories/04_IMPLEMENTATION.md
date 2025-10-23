# User Categories - Implementation

**Feature:** Multi-Category User System  
**Status:** ✅ Production Ready  
**Last Updated:** October 22, 2025

---

## 📂 CODE LOCATIONS

### Models
**File:** `coda/accounts/models.py`
- `CustomerUser.category` - Primary category field
- `CustomerUser.sub_category` - Sub-category field

### Choices
**File:** `coda/accounts/choices.py`
- `UserCategory` - Category enum

### Utilities
**File:** `coda/accounts/user_utils.py`
- `get_user_employment_status()`
- `get_user_client_status()`
- `get_user_applicant_status()`
- `get_user_lifecycle_stage()`
- `validate_user_category_combination()`
- `get_redirect_url()` - Category-based routing

---

## 🔑 KEY FUNCTIONS

```python
def get_redirect_url(user):
    """Redirect based on category"""
    if user.is_staff:
        return '/dashboard/'
    elif user.category == 2:  # Client
        return '/client/dashboard/'
    elif user.category == 3:  # Applicant
        return '/applicant/portal/'
    elif user.category == 4:  # Investor
        return '/investing/portfolio/'
    else:
        return '/dashboard/'
```

---

**See:** 05_TESTING.md for category tests


