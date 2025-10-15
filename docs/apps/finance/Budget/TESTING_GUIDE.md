# Testing Guide

## Manual Testing Checklist

### 1. Login Flow ✅
- [ ] Go to `/accounts/login/`
- [ ] Login: `budget_manager` / `test123`
- [ ] Should redirect to `/dashboard/` (unified dashboard)
- [ ] Should see navigation menu

### 2. Budget Dashboard ✅
- [ ] Navigate to `/finance/budget-dashboard/coda/`
- [ ] Should see budget categories with counts and totals
- [ ] Should see 👁️ "View Details" and ✏️ "Edit" buttons

### 3. View Details Button ✅
- [ ] Click 👁️ "View Details" on any category
- [ ] Should open `/finance/budget/coda/category/X/`
- [ ] Should see: Category stats, subcategories, recent transactions
- [ ] Should have "Back to Dashboard" button

### 4. Edit Button ⏳
- [ ] Click ✏️ "Edit" button
- [ ] Should open `/finance/budget/coda/category/X/edit/`
- [ ] Should see edit form
- [ ] Should be able to save changes

### 5. Calculations Verification 🧮
- [ ] Check if budget totals match sum of items
- [ ] Verify category summaries are correct
- [ ] Compare with raw transaction data
- [ ] Report any miscalculations

### 6. Complete Workflows ⏳
- [ ] Create new budget request
- [ ] Submit for approval
- [ ] Approve/reject request
- [ ] Enter new transaction
- [ ] Verify it appears in reports

## Automated Testing

### URL Testing
```bash
# Test all critical URLs
curl -s -o /dev/null -w "Login: %{http_code}\n" http://127.0.0.1:8000/accounts/login/
curl -s -o /dev/null -w "Dashboard: %{http_code}\n" http://127.0.0.1:8000/dashboard/
curl -s -o /dev/null -w "Budget: %{http_code}\n" http://127.0.0.1:8000/finance/budget-dashboard/coda/
```

### Model Testing
```python
# Test in Django shell
python manage.py shell
from finance.models import Transaction, Budget, BudgetCategory
print(f"Transactions: {Transaction.objects.count()}")
print(f"Budgets: {Budget.objects.count()}")
print(f"Categories: {BudgetCategory.objects.count()}")
```

## Error Monitoring

### Common Errors to Watch
1. **Template Errors:** Missing templates
2. **Field Errors:** Non-existent model fields
3. **Relationship Errors:** Wrong related_name
4. **Permission Errors:** Access denied
5. **Calculation Errors:** Wrong math/formulas

### Log Locations
- **Django Logs:** Console output
- **Error Logs:** `/tmp/django_*.log`
- **Heroku Logs:** `heroku logs --tail`

## Performance Testing

### Load Testing
- Test with multiple users
- Check response times
- Monitor database queries
- Verify memory usage

### Data Volume Testing
- Test with large datasets
- Check pagination
- Verify filtering performance
- Test search functionality

## Browser Testing

### Cross-Browser
- Chrome (primary)
- Firefox
- Safari
- Edge

### Mobile Testing
- Responsive design
- Touch interactions
- Mobile navigation

## Regression Testing

### After Each Fix
1. Test the specific fix
2. Test related functionality
3. Run full test suite
4. Deploy to UAT
5. User acceptance testing

## Bug Reporting

### When Reporting Issues
1. **Steps to reproduce**
2. **Expected behavior**
3. **Actual behavior**
4. **Browser/OS info**
5. **Console errors**
6. **Screenshots if applicable**

### Priority Levels
- **P1:** Critical - System down
- **P2:** High - Major feature broken
- **P3:** Medium - Minor issue
- **P4:** Low - Enhancement

## Test Data

### Sample Users
- `budget_manager` / `test123` - Budget operations
- `finance_officer` / `test123` - Finance operations  
- `it_manager` / `test123` - IT operations
- `investor_user` / `test123` - Investor view

### Sample Data
- **366 transactions** ($1.49M total)
- **14 budget categories**
- **Multiple departments**
- **Various transaction types**
