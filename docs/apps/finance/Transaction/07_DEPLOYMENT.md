# Transaction System - Deployment

**Last Updated:** October 22, 2025  
**Current Version:** Phase 2 Complete (Smart Forms)

---

## ✅ PRE-DEPLOYMENT CHECKLIST

### Code Readiness
- [ ] All tests passing
- [ ] AI prediction service tested
- [ ] Cascading dropdowns working
- [ ] No console errors

### Data Readiness
- [ ] Categories configured (25 categories)
- [ ] Historical transactions imported
- [ ] AI cache populated
- [ ] Data quality >95%

---

## 🚀 DEPLOYMENT COMMANDS

### Deploy to UAT
```bash
git push heroku [branch]:main
heroku run "cd coda && python manage.py migrate" --app codamakutano
heroku run "cd coda && python manage.py categorize_transactions" --app codamakutano
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
# Test smart entry form
curl -I https://codamakutano.herokuapp.com/finance/transaction/smart-entry/

# Test AI prediction API
curl "https://codamakutano.herokuapp.com/finance/api/predict-all/?receiver=KPLC"

# Run data quality check
heroku run "cd coda && python manage.py analyze_transaction_data" --app codamakutano
```

---

## ⚙️ CONFIGURATION

### Environment Variables
**No additional environment variables required.**

Uses standard Django configuration.

---

## 🔄 MAINTENANCE COMMANDS

```bash
# Run auto-categorization (weekly)
heroku run "cd coda && python manage.py categorize_transactions" --app codamakutano

# Check data quality (daily)
heroku run "cd coda && python manage.py analyze_transaction_data" --app codamakutano
```

---

## 📊 DEPLOYMENT HISTORY

| Date | Version | Environment | Changes | Status |
|------|---------|-------------|---------|--------|
| Oct 2, 2025 | v895 | UAT | Smart forms deployed | ✅ Success |
| Oct 1, 2025 | v890 | UAT | Auto-categorization | ✅ Success |
| Sept 30, 2025 | v885 | UAT | Data cleanup | ✅ Success |

---

**See:** 06_MAINTENANCE.md for known issues, 05_TESTING.md for validation


