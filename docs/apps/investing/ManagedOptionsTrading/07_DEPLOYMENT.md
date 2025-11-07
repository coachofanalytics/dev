# Managed Options Trading - Deployment
**Feature:** CODA Managed Options Trading Service  
**Date:** October 22, 2025  
**Status:** 🚀 Deployment Guide

---

## 🚀 Deployment Checklist

### **Pre-Deployment**
- [ ] All tests passing (unit, integration, E2E)
- [ ] Code review completed
- [ ] Documentation complete
- [ ] Database migrations ready
- [ ] Environment variables configured
- [ ] `UNUSUAL_WHALES_API_KEY`, `UNUSUAL_WHALES_ENABLED` set (UAT + Prod)
- [ ] `UW_CACHE_TTL_SECONDS` configured (default 600)
- [ ] `TEST_MODE=True` for pre-deploy test run (switches to SQLite)
- [ ] Backup system tested
- [ ] Legal agreements signed
- [ ] Client onboarded and trained

### **Deployment Steps**

#### **1. Database Migration**
```bash
# UAT Environment
git push heroku-uat 25.10_CODA_UAT_CM:main
heroku run "cd coda && python manage.py migrate" --app codamakutano

# Verify migration
heroku run "cd coda && python manage.py showmigrations investing" --app codamakutano
```

#### **2. Verify Deployment**
```bash
# Check URLs
heroku run "cd coda && python manage.py show_urls | grep managed" --app codamakutano

# Test access
curl https://codamakutano.herokuapp.com/investing/managed/accounts/
```

#### **3. Configure Scheduled Jobs**
```bash
# Setup daily monitoring
heroku run "cd coda && python manage.py crontab add" --app codamakutano

# Verify cron jobs
heroku run "cd coda && python manage.py crontab show" --app codamakutano
```

#### **4. UW + Managed Income Release Verification (Phase 1)**
```bash
# Warm UW cache (avoid multiple API hits)
heroku run "cd coda && python manage.py cache_whales_flow --symbols AAPL,MSFT,SPY" --app codamakutano-uat

# Trigger allocation scheduler (dry-run)
heroku run "cd coda && python manage.py run_managed_income --dry-run" --app codamakutano-uat

# Collect static to ensure heatmap assets
heroku run "cd coda && python manage.py collectstatic --noinput" --app codamakutano-uat
```

**Manual QA Checklist:**
- [ ] Staff dashboard shows heatmap toggle + working "Preview Trade" modal.
- [ ] UW drawer toggle (`ℹ️`) expands with flow score/sentiment in UAT.
- [ ] Client dashboard displays income vs $420 target without trade instructions.
- [ ] WhatsApp/email scenario digest sends to test number/email.
- [ ] Celery logs indicate single UW API hit per symbol (check `uw_cache` log entries).

#### **5. Promote to Production (after UAT sign-off)**
```bash
# Tag release
git tag v1003-uw-phase1
git push origin v1003-uw-phase1

# Deploy
git push heroku 25.11_CODA_DEV_CM:main

# Post-deploy checks (prod app)
heroku run "cd coda && python manage.py migrate" --app codamakutano
heroku run "cd coda && python manage.py collectstatic --noinput" --app codamakutano
```

### **Post-Deployment**
- [ ] Test all URLs in UAT
- [ ] Verify first client can access portal
- [ ] Execute test position
- [ ] Verify monitoring alerts
- [ ] Test report generation
- [ ] Monitor for 24 hours

---

## 🔄 Rollback Plan

If critical issues found:
```bash
# Rollback deployment
git reset --hard HEAD~1
git push heroku-uat 25.10_CODA_UAT_CM:main --force

# Revert migrations
heroku run "cd coda && python manage.py migrate investing XXXX" --app codamakutano
```

---

## 📊 DEPLOYMENT HISTORY

### **🚀 Phase 1-5 Deployment** - October 27, 2025
**Release:** v946  
**Status:** ✅ Successfully Deployed to UAT

**What Was Deployed:**
- ✅ Database Models: `ManagedTradingAccount`, `OptionsPosition`, `TradingRule`, `TradingActivity`, `TradingSession`
- ✅ Service Layer: `ManagedTradingService`, `OptionsMonitoringService`, `OptionPlayIntegrationService`
- ✅ Views & Forms: 6 staff view files, multi-leg options forms
- ✅ Templates: 14 HTML templates (12 staff + 2 client)
- ✅ URLs: 30+ URL patterns configured
- ✅ Dashboard Integration: 8 quick-access buttons

**Deployment Steps:**
1. Documentation consolidation (17 files → 7-doc structure)
2. Pre-deployment verification (all tests passed)
3. Git push to UAT (commit e0de6fff1)
4. Database migrations applied
5. Static files collected
6. URL verification completed
7. Manual testing passed

**Results:**
- ✅ All tables created successfully
- ✅ All URLs accessible
- ✅ Staff dashboard operational
- ✅ Client portal accessible
- ✅ No critical errors

---

### **🚀 Phase 6 Deployment** - October 27, 2025 (Later)
**Release:** v949  
**Status:** ✅ Successfully Deployed to UAT

**What Was Deployed:**
- ✅ New Models: `InvestorRiskProfile`, `ManagedTradingApplication`, `ManagedTradingContract`
- ✅ Forms: Risk assessment, application, contract signing forms
- ✅ Service: `ApplicationReviewService` with auto-approval logic
- ✅ Views: 7 onboarding views (risk, apply, contracts, signatures)
- ✅ URLs: 10 new onboarding patterns

**Critical Fix:**
- Fixed Heroku settings to use `heroku_settings.py` instead of `local_settings.py`
- Resolved DATABASE_URL connection issue

**Results:**
- ✅ 3 new tables created
- ✅ Complete onboarding workflow operational
- ✅ Digital contract signing working
- ✅ Auto-approval logic functional

---

### **🔧 P&L Editing Feature** - October 2025
**Migration:** `0007_add_pnl_adjustment_activity.py`  
**Status:** ✅ Successfully Deployed

**What Was Implemented:**
- ✅ Added 'pnl_adjusted' activity type to `TradingActivity`
- ✅ New view: `adjust_position_pnl()` (staff-only, POST)
- ✅ URL pattern: `/managed/positions/<id>/adjust-pnl/`
- ✅ Enhanced position detail template with edit modal
- ✅ Full audit trail logging (old/new values, reasons)

**Features:**
- Manual P&L adjustment for entry premium or exit premium
- Required reason field for all adjustments
- Activity log highlights (yellow background for adjustments)
- Staff-only permission control

**Results:**
- ✅ Staff can correct data entry errors
- ✅ Full audit trail maintained
- ✅ No data integrity issues

---

### **🤖 AI Position Scoring** - November 2, 2025
**Release:** v976  
**Status:** ✅ Successfully Deployed to UAT

**What Was Deployed:**
- ✅ New Model: `OptionsPositionHistory` (ML training dataset)
- ✅ AI Fields on `SuggestedPosition`: `ai_score`, `ai_rating`, `ai_breakdown`, `ai_recommendation`
- ✅ Services: `PositionScoringService`, `PositionHistoryCollector`
- ✅ Signal-based automation for history collection and scoring
- ✅ Staff UI enhancements: star ratings, color-coding, 6-factor breakdown

**Migration:** `0009_add_position_history_model.py`, `0010_add_ai_scoring_fields.py`

**Test Results:**
- ✅ 499 real positions scored successfully
- ✅ Score distribution: 0 excellent, 0 good, 1 average, 150 below-avg, 348 poor
- ✅ Algorithm correctly identified poor positions (bond ETFs, low premiums)

**Results:**
- ✅ AI scoring operational
- ✅ Staff can sort by AI score
- ✅ 6-factor breakdown visible
- ✅ Auto-scoring via signals working

---

### **📱 WhatsApp/Telegram Notifications** - November 2, 2025
**Release:** v982  
**Status:** ✅ 95% Deployed (credentials needed)

**What Was Deployed:**
- ✅ Added fields to `ManagedTradingAccount`: `whatsapp_enabled`, `whatsapp_phone`, `telegram_enabled`, `telegram_chat_id`
- ✅ Extended `NotificationService` with WhatsApp and Telegram methods
- ✅ Created 6 message templates for position events
- ✅ Signal-based triggers for position open/close and batch approvals
- ✅ Admin configuration for notification preferences

**Migration:** `0011_add_whatsapp_telegram_notifications.py`

**Dependencies Added:**
- ✅ `twilio==8.10.0` for WhatsApp integration

**Remaining:**
- ⏳ User needs to configure Twilio credentials (3 minutes)

**Results:**
- ✅ Code deployed and tested locally
- ✅ Ready for production use once credentials configured

---

### **🐋 UW Managed Income Enhancements** - November 7, 2025
**Release:** v1003 *(planned)*  
**Status:** 🚧 In UAT validation

**Scope:**
- Staff CSV uploads auto-enrich with UW flow + timing signals.
- Heatmap toggle + "Preview Trade" modal with strategy legs.
- CapitalAllocationService + scheduler groundwork (dry-run mode).
- UW caching layer to prevent duplicate calls.
- Scenario digest templates (WhatsApp/email) for capital upsell.

**UAT Actions:**
- Heatmap + UW drawer verified (Bootstrap 4 attributes corrected).
- Managed income target card visible on client dashboard.
- Allocation dry-run produced 5 recommendations ≥ $420 target combined.
- WhatsApp digest delivered to test number with three scenarios.

**Next Steps Before Prod:**
- Finalize Celery schedule in `heroku addons:create scheduler` (15 min).
- Monitor cache hit logs for 48 hours.
- Obtain sign-off from managed options lead.
- ✅ Sandbox testing successful

---

## 📈 DEPLOYMENT STATISTICS

| Metric | Count |
|--------|-------|
| **Total Deployments** | 5 major releases |
| **Heroku Releases** | v946, v949, v976, v982 |
| **Migrations Applied** | 11 migrations |
| **New Tables Created** | 12 tables |
| **URL Patterns Added** | 40+ patterns |
| **Templates Created** | 20+ templates |
| **Success Rate** | 100% (no rollbacks needed) |

---

## 📋 DETAILED DEPLOYMENT DOCS

For detailed deployment information, see:
- **[deployment_history/DEPLOYMENT_SUCCESS_OCT27.md](deployment_history/DEPLOYMENT_SUCCESS_OCT27.md)** - Phase 1-5 deployment
- **[deployment_history/PHASE6_DEPLOYMENT_SUCCESS.md](deployment_history/PHASE6_DEPLOYMENT_SUCCESS.md)** - Phase 6 onboarding
- **[deployment_history/PNL_EDITING_FEATURE.md](deployment_history/PNL_EDITING_FEATURE.md)** - P&L editing implementation
- **[deployment_history/COMPLETE_SYSTEM_DEPLOYED.md](deployment_history/COMPLETE_SYSTEM_DEPLOYED.md)** - Complete system status

---

**Previous Phase:** [06_MAINTENANCE.md](06_MAINTENANCE.md)  
**Return to:** [README.md](README.md)

