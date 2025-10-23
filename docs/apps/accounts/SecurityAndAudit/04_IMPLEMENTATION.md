# Security & Audit - Implementation

**Feature:** Security Monitoring  
**Last Updated:** October 22, 2025

---

## 📂 CODE LOCATIONS

### Models
**File:** `coda/accounts/models.py`
- `LoginHistory` (lines 440-456)

### Views
**File:** `coda/accounts/views.py`
- `user_login_history()` - View login history

---

## 🔑 LOGGING

```python
# Login event logged in login_view()
LoginHistory.objects.create(
    user=user,
    ip_address=request.META.get('REMOTE_ADDR'),
    user_agent=request.META.get('HTTP_USER_AGENT'),
    success=True
)
```

---

**See:** 05_TESTING.md


