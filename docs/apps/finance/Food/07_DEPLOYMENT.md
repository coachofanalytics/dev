# Food Supply Management - Deployment

**Feature:** Food & Inventory Tracking  
**Status:** 🚧 Not Ready - Pending Phase 1-3 Implementation  
**Last Updated:** October 22, 2025

---

## 📋 PRE-DEPLOYMENT CHECKLIST

### Phase 1: Foundation (Before Deployment)
- [ ] FoodInventory model created and migrated
- [ ] FoodConsumption model created and migrated
- [ ] Existing Food data migrated to FoodInventory
- [ ] food.html template updated
- [ ] FoodFilter fixed to match model fields
- [ ] Unit tests pass (>80% coverage)
- [ ] Manual testing complete

### Phase 2: Integration (Before Deployment)
- [ ] FoodPurchaseRequest model implemented
- [ ] Approval workflow integrated
- [ ] Budget integration service tested
- [ ] Email notifications configured
- [ ] Integration tests pass
- [ ] UAT approval received

### Phase 3: Analytics (Before Deployment)
- [ ] Analytics dashboard functional
- [ ] Charts rendering correctly
- [ ] Reports accurate
- [ ] Mobile-responsive verified
- [ ] Performance acceptable (<2sec page load)

---

## 🚀 DEPLOYMENT PROCEDURE

### Step 1: Database Migrations

**UAT:**
```bash
# Push code to UAT
git push heroku feature/food-inventory:main --app codamakutano

# Run migrations
heroku run "cd coda && python manage.py migrate" --app codamakutano

# Verify migrations
heroku run "cd coda && python manage.py showmigrations finance" --app codamakutano
```

**Production:**
```bash
# Push to production
git push heroku feature/food-inventory:main --app codatrainingapp

# Run migrations
heroku run "cd coda && python manage.py migrate" --app codatrainingapp
```

---

### Step 2: Data Migration

**Migrate existing Food records to FoodInventory:**
```bash
# Run custom management command
heroku run "cd coda && python manage.py migrate_food_to_inventory" --app codamakutano

# Verify migration
heroku run "cd coda && python manage.py shell" --app codamakutano
>>> from finance.models import FoodInventory
>>> FoodInventory.objects.count()
```

---

### Step 3: Configure Cron Jobs

**Heroku Scheduler (Add-on required):**
```bash
# Add scheduler if not exists
heroku addons:create scheduler:standard --app codamakutano

# Configure jobs
heroku addons:open scheduler --app codamakutano
```

**Add these jobs:**
1. **Calculate Consumption Rates** (Daily at 11:59 PM)
   ```
   python coda/manage.py calculate_food_consumption_rates
   ```

2. **Send Low Stock Alerts** (Daily at 8:00 AM)
   ```
   python coda/manage.py send_food_alerts
   ```

---

### Step 4: Environment Variables

**Email Configuration (if not already set):**
```bash
heroku config:set EMAIL_HOST_USER="noreply@codanalytics.net" --app codamakutano
heroku config:set EMAIL_HOST_PASSWORD="your_password" --app codamakutano
```

**Food-Specific Settings:**
```bash
# Default reorder threshold days
heroku config:set FOOD_REORDER_ALERT_DAYS=7 --app codamakutano

# Auto-approval threshold
heroku config:set FOOD_AUTO_APPROVE_THRESHOLD=50 --app codamakutano
```

---

## ✅ POST-DEPLOYMENT VERIFICATION

### Test in UAT:
```bash
# 1. Access food inventory
curl -I https://codamakutano.herokuapp.com/finance/food/inventory/

# 2. Check database records
heroku run "cd coda && python manage.py shell" --app codamakutano
>>> from finance.models import FoodInventory, FoodConsumption
>>> FoodInventory.objects.count()
>>> FoodConsumption.objects.count()

# 3. Verify cron jobs registered
heroku run "cd coda && python manage.py crontab show" --app codamakutano
```

### Manual Testing Checklist:
- [ ] View food inventory list
- [ ] Log consumption
- [ ] Create purchase request
- [ ] Approve purchase (auto and manual)
- [ ] Verify budget entry created
- [ ] Check email notifications received
- [ ] View analytics dashboard
- [ ] Test on mobile device

---

## 🔄 ROLLBACK PROCEDURE

If critical issues found post-deployment:

```bash
# Rollback to previous version
heroku releases --app codamakutano
heroku rollback v<previous_version> --app codamakutano

# If database changes, rollback migration
heroku run "cd coda && python manage.py migrate finance <previous_migration>" --app codamakutano
```

---

## 📊 DEPLOYMENT TIMELINE

### Phase 1 Deployment:
- **Duration:** 2 weeks development + 1 week UAT
- **Go-Live:** TBD (after development complete)
- **Rollout:** All offices simultaneously

### Phase 2 Deployment:
- **Duration:** 3 weeks development + 1 week UAT
- **Go-Live:** 4 weeks after Phase 1
- **Rollout:** Gradual (pilot in 1 office, then expand)

### Phase 3 Deployment:
- **Duration:** 2 weeks development + 1 week UAT
- **Go-Live:** 8 weeks after Phase 1
- **Rollout:** All offices simultaneously

---

## 👥 USER TRAINING

### Training Sessions Required:
1. **Office Managers** (1 hour) - Inventory management, consumption logging
2. **Procurement** (1 hour) - Purchase requests, approval workflow
3. **Finance Team** (1 hour) - Budget integration, reports, analytics

### Training Materials:
- [ ] User guide (PDF)
- [ ] Video tutorials (5-10 min each)
- [ ] Quick reference cards
- [ ] FAQ document

---

## 📞 POST-DEPLOYMENT SUPPORT

### Week 1 After Launch:
- Daily check-ins with office managers
- Monitor error logs closely
- Quick response to issues (<2 hours)

### Week 2-4:
- Bi-weekly check-ins
- Gather feedback for improvements
- Monitor adoption metrics

### Ongoing:
- Monthly review of analytics
- Quarterly feature enhancements
- Annual ROI assessment

---

## 🎯 SUCCESS CRITERIA

### Phase 1 Success:
- ✅ All offices logging consumption daily
- ✅ Low stock alerts triggering correctly
- ✅ No critical bugs
- ✅ User satisfaction > 80%

### Phase 2 Success:
- ✅ 100% food purchases in budget system
- ✅ Approval turnaround < 24 hours
- ✅ Auto-approval working correctly

### Phase 3 Success:
- ✅ Analytics used weekly by management
- ✅ Cost savings >15% achieved
- ✅ Mobile adoption >50%

---

**DEPLOYMENT BLOCKED BY:** Phase 1-3 implementation  
**READY TO DEPLOY:** No  
**NEXT STEP:** Complete development


