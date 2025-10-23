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
| Oct 13, 2025 | v904 | Schema fix | ✅ Success |
| Sept 2025 | v880 | KCC integration | ✅ Success |
| Aug 2025 | v860 | Initial loan system | ✅ Success |

---

**See:** 06_MAINTENANCE.md for known issues


