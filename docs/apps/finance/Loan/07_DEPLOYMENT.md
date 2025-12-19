# Loan System - Deployment

**Last Updated:** October 22, 2025

---

## ✅ PRE-DEPLOYMENT CHECKLIST

### Code Readiness
- [ ] All tests passing
- [ ] Schema alignment verified (term_months not min/max)
- [ ] Eligibility service tested
- [ ] No template errors

---

## 🚀 DEPLOYMENT COMMANDS

### Deploy to UAT
```bash
git push heroku [branch]:main
heroku run "cd coda && python manage.py migrate" --app codamakutano
```

### Deploy to Production (REQUIRES PERMISSION)
```bash
# ASK USER FIRST!
git checkout 25.10_CODA_PROD_v2_CM
git push production 25.10_CODA_PROD_v2_CM:main
heroku run "cd coda && python manage.py migrate" --app codatrainingapp
```

---

## ✅ POST-DEPLOYMENT VERIFICATION

```bash
# Test loan product list
curl -I https://codamakutano.herokuapp.com/finance/loans/products/

# Test loan application form
curl -I https://codamakutano.herokuapp.com/finance/loans/apply/

# Verify schema
heroku run "cd coda && python manage.py shell" --app codamakutano
# >>> from finance.models import LoanProduct
# >>> LoanProduct._meta.get_field('term_months')
# Should exist (not min_term_months)
```

---

## ⚙️ CONFIGURATION

### Environment Variables
**No additional environment variables required.**

---

## 🚨 CRITICAL: Schema Alignment

**Always verify:**
- Production schema: `term_months`
- Dev schema: `term_months`
- Template references: `loan.term_months`

**Never use:** `min_term_months`, `max_term_months` (doesn't exist in production)

---

## 📊 DEPLOYMENT HISTORY

| Date | Version | Changes | Status |
|------|---------|---------|--------|
| Nov 2025 | - | Loan Product Type Fixes - Removed invalid 'external' type, fixed kcc/staff type references | ✅ Success |
| Oct 13, 2025 | v904 | Schema fix (term_months alignment) | ✅ Success |
| Sept 2025 | v880 | KCC integration | ✅ Success |
| Aug 2025 | v860 | Initial loan system | ✅ Success |

---

## Loan Product Type Fixes (November 2025)

### Problem
- External loan applicants unable to access loan products
- Invalid product type references causing filtering issues
- Product type assignments incorrect

### Changes Made

**File:** `coda/finance/views.py`

**Changes:**
- **Line 237-246**: Removed `"external"` from external user product filter (not a valid model choice)
- **Line 574**: Changed `"kcc_member"` → `"kcc_premium"` (correct product type)
- **Line 579**: Changed `"staff_only"` → `["staff_emergency", "staff_development"]` (correct product types)
- **Line 584-591**: Removed `"external"` from validation check, added all valid external product types
- **Line 605, 612**: Changed `"kcc_member"` → `"kcc_premium"` for KCC product selection
- **Line 616-621**: Changed `"staff_only"` → `"staff_emergency"` with fallback to `"staff_development"`
- **Line 625-630**: Removed `"external"` from default product selection, added all valid external types

**Summary:**
- Removed all references to invalid `"external"` product type
- Fixed product type references to match actual model choices:
  - `kcc_member` → `kcc_premium`
  - `staff_only` → `staff_emergency` / `staff_development`
- Updated filters to use only valid product types from model

### Database Changes Required

**Note:** Database changes should be run AFTER code deployment.

The following script needs to be run on both UAT and Production databases:
- `update_prod_loan_products.py` - Updates product types based on product names

**Product Type Mappings:**
- KCC products → `kcc_premium`
- Staff Emergency → `staff_emergency`
- Staff Development → `staff_development`
- Education → `education`
- Business Startup → `business_startup`
- Medical Emergency → `medical_emergency`
- Vehicle Purchase → `vehicle_purchase`
- Debt Consolidation → `debt_consolidation`
- Wedding & Events → `wedding_events`
- Home Improvement → `home_improvement`
- Others → `general`

### Testing Checklist

**Before Deployment:**
- [ ] Code changes reviewed
- [ ] No syntax errors
- [ ] All references to invalid product types removed

**After Code Deployment:**
- [ ] Verify external users can see loan products
- [ ] Verify staff users see only staff products
- [ ] Verify KCC members see only KCC products
- [ ] Test loan application flow for each user type

**After Database Update:**
- [ ] Verify product types are correctly assigned
- [ ] Verify product filtering works correctly
- [ ] Test with external users to confirm access

### Deployment Steps

**1. Deploy Code Changes:**
```bash
# Commit changes
git add coda/finance/views.py
git commit -m "Fix loan product type filters - remove invalid 'external' type, fix kcc/staff type references"

# Deploy to UAT first, then Production
```

**2. Update Database (After Code Deployment):**
```bash
# UAT Database
cd /Users/coda/PROJECTS/CODA/DEVELOPMENT/DEV/coda
python3 manage.py shell < ../update_prod_loan_products.py

# Production Database (after UAT verification)
# Ensure connected to Production
python3 manage.py shell < ../update_prod_loan_products.py
```

### Impact
- **External Users**: Will now be able to see and apply for appropriate loan products
- **Staff Users**: Will see only staff-specific products (emergency/development)
- **KCC Members**: Will see only KCC premium products
- **Product Types**: All products will have correct type assignments

### Rollback Plan
If issues occur:
1. **Code Rollback:** Revert `coda/finance/views.py` to previous version
2. **Database Rollback:** Product types can be manually reverted in Django admin or restore from backup

---

**See:** 06_MAINTENANCE.md for known issues


