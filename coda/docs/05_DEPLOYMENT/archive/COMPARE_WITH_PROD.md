# Comparison: Our Fixes vs Production Branch
**Date:** October 13, 2025  
**Production Branch:** `uat/25.10_CODA_PROD_MINIMAL_CM`  
**Our Branch:** `25.10_UAT_DEPLOYMENT_FIX_CM`

## 🔍 FILES TO COMPARE

### 1. **BudgetRequest Model Queries**
**Our Fixes:** Removed `company=company` filters from BudgetRequest queries

**Files We Modified:**
- `coda/finance/views/budget/approval.py`
- `coda/finance/views/budget/approvals.py`  
- `coda/finance/views/budget/editing.py`

**Action:** Check if production has these same filters or if they handle it differently

### 2. **Service Layer Imports**
**Our Fixes:** 
- Changed `FinancialAnalyticsService` import from `analytics_service` to `financial_analytics_service`
- Added `LoanService` import

**Files We Modified:**
- `coda/finance/services/__init__.py`
- `coda/finance/views.py`

**Action:** Compare service imports and organization with production

### 3. **Template Paths**
**Our Fixes:**
- Changed `finance/loan_analytics.html` → `finance/admin/loan_analytics.html`

**Files We Modified:**
- `coda/finance/views.py` (loan_analytics function)

**Action:** Verify template paths match production structure

### 4. **Payment URLs**
**Our Fixes:**
- Wrapped `payment_views` import in try-except
- Commented out payment URLs temporarily

**Files We Modified:**
- `coda/finance/urls.py`
- `coda/management/utils.py`
- `coda/unified_dashboard/views.py`

**Action:** Check if production has `_deprecated` module and payment URLs working

---

## 📋 SYSTEMATIC COMPARISON CHECKLIST

### Step 1: Check BudgetRequest Model
```bash
# Compare model definition
git show uat/25.10_CODA_PROD_MINIMAL_CM:finance/models.py | grep -A 30 "class BudgetRequest"
```

### Step 2: Check Budget View Patterns
```bash
# See how production handles BudgetRequest filtering
git show uat/25.10_CODA_PROD_MINIMAL_CM:finance/views/budget/approval.py | grep -A 5 "BudgetRequest.objects.filter"
```

### Step 3: Check Service Organization
```bash
# Compare services/__init__.py
git diff HEAD uat/25.10_CODA_PROD_MINIMAL_CM -- finance/services/__init__.py
```

### Step 4: Check Template Structure
```bash
# List all loan/budget templates in production
git ls-tree -r --name-only uat/25.10_CODA_PROD_MINIMAL_CM | grep "finance/templates.*\(loan\|budget\).*\.html$"
```

### Step 5: Check Payment Views
```bash
# See if _deprecated exists in production
git ls-tree -r --name-only uat/25.10_CODA_PROD_MINIMAL_CM | grep "_deprecated"
```

---

## 🎯 PRIORITY CHECKS

### HIGH PRIORITY (Do These First):

1. **BudgetRequest Queries**
   - Does production filter by `company`?
   - If yes, does production's BudgetRequest model have a `company` field?
   - If no, how does production handle company-specific filtering?

2. **Service Imports**
   - Which FinancialAnalyticsService does production use?
   - Does production have both `analytics_service.py` and `financial_analytics_service.py`?
   - How is LoanService imported and used?

3. **URL Patterns**
   - Does production have payment URLs active?
   - Does `_deprecated.legacy_views` exist in production?

### MEDIUM PRIORITY:

4. **Template Paths**
   - Verify all template references point to correct locations
   - Check for any missing templates we need to restore

5. **Model Field Names**
   - Transaction model: `user_id` vs `sender`, `transaction_type` existence
   - BudgetRequest model: field name consistency

### LOW PRIORITY:

6. **Form Classes**
   - BudgetEditForm existence
   - Other missing forms

7. **Template Filters**
   - `|mul` filter availability
   - Django-mathfilters installation

---

## 🚀 EXECUTION PLAN

1. **Run Comparison Commands** (see checklist above)
2. **Document Differences** in this file
3. **Restore Missing Components** from production where our fixes are incomplete
4. **Test Locally** after each restoration
5. **Deploy to UAT** once all local tests pass
6. **User Testing** on UAT
7. **Document Final State** before production deployment

---

## 📝 FINDINGS (To Be Filled In)

### Finding 1: BudgetRequest Model
- [ ] Checked production model definition
- [ ] Finding:
- [ ] Action needed:

### Finding 2: Service Imports
- [ ] Checked production services/__init__.py
- [ ] Finding:
- [ ] Action needed:

### Finding 3: Payment URLs
- [ ] Checked for _deprecated module
- [ ] Finding:
- [ ] Action needed:

### Finding 4: Template Structure
- [ ] Listed production templates
- [ ] Finding:
- [ ] Action needed:

---

**Status:** Ready to execute comparison  
**Next Step:** Run comparison commands and document findings

