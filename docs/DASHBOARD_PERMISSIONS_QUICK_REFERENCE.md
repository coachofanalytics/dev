# Dashboard Permissions Quick Reference

**For Developers:** Quick guide to applying permissions to dashboards

---

## Import Statement

```python
try:
    from core.permissions import require_employee, require_finance_staff, require_admin, require_manager, require_investor
except ImportError:
    from accounts.permissions import require_employee, require_finance_staff, require_admin, require_manager, require_investor
```

---

## Permission Decorators

| Decorator | Who Can Access | Use For |
|-----------|---------------|---------|
| `@require_employee` | Staff or Applicant category | Task dashboards, Analytics (personal) |
| `@require_manager` | Staff, Superuser, or Department heads | Compliance, Anomaly Detection, Team analytics |
| `@require_finance_staff` | Staff or Finance department | Budget, Salary, Loan, Payment dashboards |
| `@require_admin` | Staff or Superuser | Admin controls, System configuration |
| `@require_investor` | Investor category | Investment dashboards, Client portal |
| `@require_staff` | Staff only | Staff-only dashboards |

---

## Quick Examples

### Employee Dashboard
```python
from accounts.permissions import require_employee

@require_employee
def task_dashboard(request):
    # Only employees can access
    return render(request, 'task_dashboard.html')
```

### Finance Dashboard
```python
from accounts.permissions import require_finance_staff

@require_finance_staff
def budget_dashboard(request, company_slug):
    # Only finance staff can access
    return render(request, 'budget_dashboard.html')
```

### Manager Dashboard
```python
from accounts.permissions import require_manager

@require_manager
def compliance_dashboard(request):
    # Only managers can access
    return render(request, 'compliance_dashboard.html')
```

### Admin Dashboard
```python
from accounts.permissions import require_admin

@require_admin
def admin_controls_dashboard(request):
    # Only admins can access
    return render(request, 'admin_controls.html')
```

---

## Finance Dashboard Checklist

Apply `@require_finance_staff` to:
- [ ] `unified_budget_dashboard` in `finance/views/budget/dashboard.py`
- [ ] `finance_dashboard` in `finance/views/core/views_finance_dashboard.py`
- [ ] `salary_dashboard` in `finance/views/budget/views_salary_dashboard.py`
- [ ] `loan_budget_dashboard` in `finance/views/loan/budget_integration.py`
- [ ] `realtime_compliance_dashboard` in `finance/views/realtime_compliance.py`
- [ ] `budget_approval_dashboard` in `finance/views/budget/approvals.py`
- [ ] `tier_management_dashboard` in `finance/views/budget/views_tier_management.py`
- [ ] `enhanced_legacy_dashboard` in `finance/views/legacy/views_legacy_dashboard.py`

Apply `@require_admin` to:
- [ ] `admin_controls_dashboard` in `finance/views/admin_controls.py`
- [ ] `automation_dashboard` in `finance/views/automation.py`

---

## Investing Dashboard Checklist

Apply `@require_staff` to:
- [ ] `staff_dashboard` in `investing/views/managed_trading/dashboard.py`
- [ ] `monitor_dashboard` in `investing/views/managed_trading/monitoring.py`
- [ ] `preset_analytics_dashboard` in `investing/views/managed_trading/preset_analytics.py`

Apply `@require_investor` to:
- [ ] `client_portal` in `investing/views/managed_trading/client.py`
- [ ] Investment dashboard views

---

## Testing

After applying permissions, test:
1. ✅ Authenticated user can access allowed dashboards
2. ✅ Unauthorized user gets redirected with error message
3. ✅ Error message is user-friendly
4. ✅ Navigation only shows accessible dashboards

---

**Last Updated:** November 6, 2025

