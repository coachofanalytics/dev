# User Categories - Architecture

**Feature:** Multi-Category User System  
**Status:** ✅ Implemented  
**Last Updated:** October 22, 2025

---

## 📊 DATA MODEL

### Category Choices

**File:** `coda/accounts/choices.py`

```python
class UserCategory(models.IntegerChoices):
    EMPLOYEE = 1, "Employee"
    CLIENT = 2, "Client"
    APPLICANT = 3, "Applicant"
    INVESTOR = 4, "Investor"
    UNKNOWN = 999, "Unknown"
```

### CustomerUser Category Fields

```python
class CustomerUser(AbstractUser):
    category = IntegerField(
        choices=CategoryChoices.choices,
        default=999
    )
    sub_category = IntegerField(blank=True, null=True)
```

### Computed Properties

```python
@property
def employment_status(self):
    """Get employment status from category"""
    return get_user_employment_status(self)

@property
def client_status(self):
    """Get client status from category"""
    return get_user_client_status(self)
```

---

**See:** 04_IMPLEMENTATION.md for utility functions



