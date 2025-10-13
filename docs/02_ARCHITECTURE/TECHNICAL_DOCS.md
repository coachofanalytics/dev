# Technical Documentation

## Architecture

### Models
- **Transaction:** Core spending data (366 records)
- **Budget:** Budget planning and tracking
- **BudgetCategory/BudgetSubCategory:** Classification system
- **BudgetRequest:** Approval workflow

### Views Organization
```
finance/views/
├── budget/
│   ├── dashboard.py (unified_budget_dashboard)
│   ├── drilldown.py (budget_category_detail)
│   ├── editing.py (budget_category_edit)
│   └── approvals.py (approval workflow)
├── core/ (finance dashboard)
├── loan/ (KCC loan system)
└── transaction/ (smart entry)
```

### Key URLs
```python
# Budget System
path('budget-dashboard/<str:company_slug>/', unified_budget_dashboard, name='unified-budget-dashboard')
path('budget/<str:company_slug>/category/<int:category_id>/', budget_category_detail, name='budget-category-detail')
path('budget/<str:company_slug>/category/<int:category_id>/edit/', budget_category_edit, name='budget-category-edit')

# Authentication
path('accounts/', include('allauth.urls'))
LOGIN_REDIRECT_URL = "dashboard:unified_dashboard"
```

## Database Schema

### Critical Relationships
```python
# Budget Model
Budget.subcategory → BudgetSubCategory (related_name='sub_category_type')
BudgetSubCategory.category → BudgetCategory (related_name='subcategories')

# Transaction Model  
Transaction.subcategory → BudgetSubCategory (not 'budget_subcategory')
Transaction.category → BudgetCategory
```

### Field Mappings
```python
# Transaction Fields (Actual)
'amount', 'category', 'subcategory', 'vendor', 'transaction_date', 
'transaction_type', 'status', 'currency', 'description', 'notes'

# Budget Fields (Actual)
'company', 'department', 'category', 'subcategory', 'item_name',
'estimated_amount', 'actual_spent', 'budget_lead', 'start_date', 'end_date'
```

## Recent Fixes

### Model Relationship Fix
```python
# BEFORE (BROKEN):
subcategories = BudgetSubCategory.objects.prefetch_related('budgets')  # ❌

# AFTER (FIXED):
subcategories = BudgetSubCategory.objects.prefetch_related('sub_category_type')  # ✅
```

### Transaction Filter Fix
```python
# BEFORE (BROKEN):
transaction_filter = {'budget_subcategory': subcategory}  # ❌

# AFTER (FIXED):  
transaction_filter = {'subcategory': subcategory}  # ✅
```

## Error Patterns

### Common Issues
1. **Field Mismatches:** Admin configs referencing non-existent fields
2. **Relationship Errors:** Wrong related_name in prefetch_related
3. **Template Missing:** Views trying to render non-existent templates
4. **Import Errors:** Circular imports or missing module imports

### Debugging Steps
1. Check Django logs for specific errors
2. Verify model fields with `python manage.py shell`
3. Test URLs with `curl` to see HTTP codes
4. Check template existence in filesystem

## Performance Notes
- Use `select_related` for foreign keys
- Use `prefetch_related` for many-to-many/reverse FK
- Avoid N+1 queries in list views
- Cache expensive calculations

## Security
- All views use `@login_required_finance` or `@login_required`
- Company isolation with `@company_required`
- User permissions checked in views
- CSRF protection enabled
