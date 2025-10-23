# Security & Audit - Architecture

**Feature:** Security Monitoring & Audit Logging  
**Last Updated:** October 22, 2025

---

## 📊 CURRENT MODEL

### LoginHistory
```python
class LoginHistory(models.Model):
    user = ForeignKey(CustomerUser, on_delete=models.CASCADE)
    login_time = DateTimeField(auto_now_add=True)
    logout_time = DateTimeField(null=True, blank=True)
    ip_address = GenericIPAddressField(null=True)
    user_agent = TextField(null=True)
    success = BooleanField(default=True)
    failure_reason = CharField(max_length=255, null=True)
```

---

## 📊 PHASE 2 MODELS (Planned)

### AuditLog
```python
class AuditLog(models.Model):
    user = ForeignKey(CustomerUser, on_delete=models.SET_NULL, null=True)
    action = CharField(max_length=50)  # create, update, delete, view
    model_name = CharField(max_length=100)
    object_id = IntegerField()
    changes = JSONField()  # Before/after values
    ip_address = GenericIPAddressField()
    timestamp = DateTimeField(auto_now_add=True)
```

### SecurityAlert
```python
class SecurityAlert(models.Model):
    user = ForeignKey(CustomerUser, on_delete=models.CASCADE)
    alert_type = CharField(max_length=50)  # impossible_travel, unusual_time
    risk_score = IntegerField()  # 0-100
    details = JSONField()
    resolved = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)
```

---

**See:** 04_IMPLEMENTATION.md



