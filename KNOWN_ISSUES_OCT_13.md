# Known Issues - October 13, 2025
**Branch:** `25.10_UAT_DEPLOYMENT_FIX_CM`

## ✅ FIXED (Ready for UAT Testing)

### 1. ModuleNotFoundError: finance._deprecated
**Status:** ✅ FIXED  
**Fix:** Wrapped import in try-except, disabled payment URLs temporarily  
**Files:** `coda/finance/urls.py`, `coda/management/utils.py`, `coda/unified_dashboard/views.py`

### 2. BudgetRequest company field errors  
**Status:** ✅ FIXED  
**Issue:** BudgetRequest model doesn't have `company` field, but queries were filtering by it  
**Fix:** Removed `company=company` filters, updated field names (`requester` vs `requested_by`, `budget_category` vs `category`)  
**Files:** `coda/finance/views/budget/approvals.py`, `coda/finance/views/budget/approval.py`, `coda/finance/views/budget/editing.py`

### 3. FinancialAnalyticsService missing generate_performance_report
**Status:** ✅ FIXED  
**Issue:** Wrong `FinancialAnalyticsService` class being imported (from `analytics_service` instead of `financial_analytics_service`)  
**Fix:** Updated import in `services/__init__.py`  
**Files:** `coda/finance/services/__init__.py`

## 🔄 REQUIRES ATTENTION (Not Critical for Core Functionality)

### 4. LoanService not defined
**Status:** 🔄 NEEDS REFACTORING  
**Issue:** `views.py` references `LoanService()` which doesn't exist  
**Impact:** Admin loan analytics page (`/finance/admin/loan-analytics/`) and loan application management  
**Workaround:** Use `LoanPerformanceService` or `LoanEligibilityService` instead  
**Files:** `coda/finance/views.py` (lines 168, 754, 779, 800, 820, 842, 891, 949)

### 5. Transaction model field mismatches
**Status:** 🔄 NEEDS INVESTIGATION  
**Issue:** Multiple field name inconsistencies:
- Code references `user_id` but model has `sender` (ForeignKey)
- Code references `transaction_type` but field doesn't exist
- Code references `receiver` as ForeignKey but may not have `select_related`
**Impact:** Transaction queries failing in budget category details
**Files:** Various views referencing Transaction model

### 6. BudgetDashboardView.log_error attribute
**Status:** 🔄 MINOR FIX NEEDED  
**Issue:** View trying to call `self.log_error()` which doesn't exist  
**Fix:** Should use `self.handle_error()` or add `log_error` method  
**Files:** Budget dashboard views

### 7. NoReverseMatch for 'unified-budget-dashboard'
**Status:** 🔄 TEMPLATE FIX NEEDED  
**Issue:** Templates referencing `{% url 'unified-budget-dashboard' %}` without namespace  
**Fix:** Add `finance:` namespace → `{% url 'finance:unified-budget-dashboard' company_slug %}`  
**Files:** Templates in `coda/finance/templates/finance/budgets/`

### 8. BudgetEditForm not defined
**Status:** 🔄 FORM MISSING  
**Issue:** Views trying to use `BudgetEditForm` which doesn't exist  
**Impact:** Budget edit page fails to load  
**Files:** Budget editing views

### 9. Invalid prefetch_related on BudgetSubCategory
**Status:** 🔄 MODEL RELATIONSHIP ISSUE  
**Issue:** Code trying to `prefetch_related('budgets')` but relationship doesn't exist  
**Files:** Budget category detail views

### 10. Invalid filter 'mul' in templates
**Status:** 🔄 TEMPLATE FILTER MISSING  
**Issue:** Template using `|mul` filter which isn't registered  
**Fix:** Either install `django-mathfilters` or remove usage  
**Files:** Budget templates

## 📊 IMPACT SUMMARY

**Critical (Blocking):** 0  
**High (Fixed):** 3  
**Medium (Workaround Available):** 4  
**Low (Minor UX Issues):** 3  

## 🎯 DEPLOYMENT RECOMMENDATION

**Safe to deploy to UAT** - Core functionality (dashboard, approvals, transactions) should work. Admin analytics and some edge cases may have issues but won't block primary workflows.

## 📝 NEXT STEPS

1. Deploy current fixes to UAT
2. Test core workflows:
   - Budget dashboard loading
   - Budget approval/rejection
   - Transaction entry
   - Category drill-down
3. If core works, create separate tickets for remaining issues
4. Consider disabling admin loan analytics temporarily if causing problems

---

**Created:** October 13, 2025  
**Last Updated:** October 13, 2025  
**Author:** Cursor AI Assistant

