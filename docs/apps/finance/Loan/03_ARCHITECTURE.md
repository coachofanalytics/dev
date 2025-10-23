# Loan System - Architecture

**Last Updated:** October 22, 2025

---

## 🏗️ SYSTEM ARCHITECTURE

```
┌───────────┐      ┌──────────────┐      ┌─────────────┐
│  User/UI  │─────▶│    Views     │─────▶│   Models    │
│ (Template)│◀─────│              │◀─────│ (Database)  │
└───────────┘      └──────────────┘      └─────────────┘
                          │
                          ▼
                   ┌──────────────┐
                   │ LoanService  │
                   │ (Eligibility)│
                   └──────────────┘
```

---

## 📊 DATA MODEL

### LoanProduct
```python
class LoanProduct(models.Model):
    name = CharField(max_length=200)
    interest_rate = DecimalField(max_digits=5, decimal_places=2)
    term_months = IntegerField()  # Fixed schema alignment issue
    min_amount = DecimalField(max_digits=12, decimal_places=2)
    max_amount = DecimalField(max_digits=12, decimal_places=2)
    is_kcc_product = BooleanField(default=False)
```

**Critical:** Schema uses `term_months` not `min_term_months`/`max_term_months`

---

### LoanApplication
```python
class LoanApplication(models.Model):
    applicant = ForeignKey(User)
    loan_product = ForeignKey(LoanProduct)
    amount_requested = DecimalField(max_digits=12, decimal_places=2)
    status = CharField(max_length=20)  # pending/approved/rejected
    application_date = DateTimeField(auto_now_add=True)
    approved_by = ForeignKey(User, null=True)
    approved_at = DateTimeField(null=True)
```

---

## 🔧 TECHNOLOGY STACK

- Django 4.x
- PostgreSQL
- jQuery for forms
- No external loan APIs (internal system)

---

**See:** 04_IMPLEMENTATION.md for code details


