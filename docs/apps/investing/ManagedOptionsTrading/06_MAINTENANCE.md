# Managed Options Trading - Maintenance
**Feature:** CODA Managed Options Trading Service  
**Date:** November 10, 2025  
**Status:** 🔧 Maintenance Guide

---

## 🔧 Daily Maintenance Tasks

### **Morning Routine (Before Market Open)**
```bash
# Check system health
python manage.py check

# Verify scheduled jobs ran
python manage.py show_cron_jobs

# Check for overnight alerts
python manage.py check_risk_alerts

# Review expiring positions
python manage.py check_expiring_positions --days 5
```

### **End of Day Routine**
```bash
# Update all position values
python manage.py update_positions_value

# Generate daily summaries
python manage.py send_daily_summaries

# Check risk limits
python manage.py check_daily_risk_limits

# Backup database
python manage.py backup_database
```

---

## 📊 Weekly Maintenance

### **Monday: Week Start**
- Review last week's performance
- Plan week's trading strategy
- Check for compliance issues
- Review open positions

### **Wednesday: Mid-Week Check**
- Review position performance
- Adjust positions if needed
- Check for alerts
- Update client communications

### **Friday: Week End**
- Calculate weekly P&L
- Generate weekly reports
- Send client updates
- Plan next week

---

## 🗓️ Monthly Maintenance

### **Month-End Tasks**
```bash
# Generate monthly statements
python manage.py generate_monthly_statements

# Calculate fees
python manage.py calculate_monthly_fees

# Update high-water marks
python manage.py update_high_water_marks

# Risk assessment review
python manage.py run_risk_assessments

# Database optimization
python manage.py optimize_database

# Refresh UW cache baselines (prevent stale data)
python manage.py cache_whales_flow --symbols SPY,QQQ,IWM --refresh

# Dry-run capital allocation to validate $420 target
python manage.py run_managed_income --dry-run
```

---

## 🐋 UW Data & Allocation Maintenance (NEW)

- Review `uw_cache` metrics in logs daily; investigate if hit rate <70%.
- Ensure `UnusualWhalesService` cache TTL matches environment variable (`UW_CACHE_TTL_SECONDS`).
- Verify capital allocation recommendations stay within 10% per position; adjust configuration if market volatility changes.
- Capture sample of WhatsApp/email scenario digests weekly to confirm templates remain accurate.
- Log any manual overrides of UW timing so the allocation heuristics can be tuned.
- Run cross-app duplication audit (`python manage.py audit_shared_templates`) monthly; refactor shared partials into `shared/templates/` when flagged.

---

## 📞 Communications Maintenance (Nov 2025 Update)

- Confirm `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER`, and `TWILIO_WHATSAPP_FROM` are present in Heroku config after every credential rotation.
- Keep `TRADER_ALERT_PHONES` list current (desk handset numbers in E.164 format).
- After each deployment touching notifications, run the smoke test in `docs/operations/runbooks/twilio_alert_testing.md` (both SMS and WhatsApp).
- Monitor Twilio delivery logs weekly for failures or opt-out warnings; address issues immediately with the trading desk.
- Archive sample alerts monthly for compliance (store SIDs + timestamp in communication log).

---

## 🐛 Troubleshooting Guide

### **Issue 1: Position Not Updating**
**Symptom:** Position P&L not updating  
**Cause:** Market data API failure  
**Solution:**
```bash
# Check API status
python manage.py check_market_data_api

# Force update from backup source
python manage.py update_positions_value --force --backup-source
```

### **Issue 2: Alert Not Generated**
**Symptom:** Missing risk alert  
**Cause:** Monitoring job not running  
**Solution:**
```bash
# Check cron jobs
python manage.py crontab show

# Manually trigger monitoring
python manage.py monitor_positions --force
```

### **Issue 3: Report Generation Failed**
**Symptom:** Client didn't receive monthly statement  
**Cause:** Email sending failure  
**Solution:**
```bash
# Check email settings
python manage.py check_email_config

# Regenerate and resend
python manage.py generate_monthly_statement --account CODA-OPT-001 --send
```

---

## 📋 Monitoring Checklist

### **System Health Monitoring**
- [ ] Database connection stable
- [ ] Market data API responding
- [ ] Email service working
- [ ] Scheduled jobs running
- [ ] No error logs accumulating
- [ ] Disk space sufficient
- [ ] Memory usage normal

### **Business Metrics Monitoring**
- [ ] All accounts within risk limits
- [ ] No positions past expiration
- [ ] Win rate trending positively
- [ ] Clients receiving reports
- [ ] Fees calculating correctly

---

**Next Phase:** [07_DEPLOYMENT.md](07_DEPLOYMENT.md)  
**Previous Phase:** [05_TESTING.md](05_TESTING.md)  
**Return to:** [README.md](README.md)

