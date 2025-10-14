# Loan System - Implementation

## Data Model

### LoanProduct
**Location:** `coda/finance/models/loan.py`

```python
class LoanProduct(models.Model):
    name = models.CharField(max_length=100)
    product_type = models.CharField(choices=[('fixed', 'Fixed'), ('variable', 'Variable'), ('kcc', 'KCC')])
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    term_months = models.PositiveIntegerField()  # Fixed Oct 13 (was min_term/max_term)
    min_amount = models.DecimalField(max_digits=12, decimal_places=2)
    max_amount = models.DecimalField(max_digits=12, decimal_places=2)
    is_active = models.BooleanField(default=True)
```

**Note:** Schema was aligned with production on Oct 13 (single `term_months` instead of min/max)

### LoanApplication
```python
class LoanApplication(models.Model):
    applicant = models.ForeignKey(User)
    loan_product = models.ForeignKey(LoanProduct)
    requested_amount = models.DecimalField(...)
    purpose = models.TextField()
    status = models.CharField(choices=['pending', 'approved', 'rejected', 'disbursed'])
    application_date = models.DateTimeField(auto_now_add=True)
```

## Services

### LoanService
**Location:** `coda/finance/services/loan_service.py`

Copied from production on Oct 13 (was missing in dev branch).

**Key Methods:**
- `calculate_monthly_payment(amount, rate, term)` - Amortization
- `get_eligibility(user)` - Check if user qualifies
- `process_application(application)` - Handle approval workflow

### EligibilityService
**Location:** `coda/finance/services/eligibility_service.py`

Checks:
- Employment status
- Income vs requested amount (DTI ratio)
- Existing loan obligations
- Minimum requirements

## Views

### Loan Analytics Dashboard
**URL:** `/finance/loans/analytics/`
**View:** `views.py::loan_analytics`
**Template:** `finance/admin/loan_analytics.html`

Fixed Oct 13: Template path was wrong (`finance/loan_analytics.html` → `finance/admin/loan_analytics.html`)

## Admin Configuration

**Location:** `coda/finance/admin.py`

```python
class LoanProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'product_type', 'min_amount', 'max_amount', 
                    'interest_rate', 'term_months', 'is_active']  # Fixed Oct 13
```

---

**Last Updated:** October 13, 2025

