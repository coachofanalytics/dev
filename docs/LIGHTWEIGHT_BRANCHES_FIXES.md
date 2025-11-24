# 🔧 Lightweight Branches - Required Fixes

## Issues Found & Fixed

### Issue 1: Missing "My Account Services" Section in Production Dashboard ✅ FIXED

**Problem:** UAT has "My Account Services" section with buttons like "Edit Profile", "My DAF", etc., but PROD only shows "Available Dashboards".

**Solution:** Added "My Account Services" section to `coda/unified_dashboard/templates/unified_dashboard/dashboard.html` that renders `role_based_links` context variable.

**Status:** ✅ Fixed in UAT branch, needs to be merged to PROD.

---

### Issue 2: Template Tag Error in Lightweight Branches ⚠️ IN PROGRESS

**Error:**
```
InvalidTemplateLibrary: Invalid template library specified. 
ImportError raised when trying to load 'application.templatetags.customfilters': 
No module named 'application'
```

**Problem:** INVESTING branch has minimal INSTALLED_APPS but templates reference `application.templatetags.customfilters`.

**Solution Applied:**
1. ✅ Added `application.apps.ApplicationConfig` to INSTALLED_APPS
2. ✅ Added `unified_dashboard.apps.UnifiedDashboardConfig` to INSTALLED_APPS
3. ✅ Commented out context processors for removed apps (management, professional_services)

**Status:** ⚠️ Still testing - need to verify all required apps are included.

---

## Required Apps for Lightweight Branches

Each lightweight branch needs these **core apps** even if it's focused on one app:

### Minimum Required Apps:
1. `main.apps.MainConfig` - Core functionality
2. `accounts.apps.AccountsConfig` - User management
3. `application.apps.ApplicationConfig` - Template tags (customfilters)
4. `unified_dashboard.apps.UnifiedDashboardConfig` - Dashboard views
5. Your focused app (e.g., `investing.apps.InvestingConfig`)

### Apps That Can Be Removed:
- `finance.apps.FinanceConfig` (unless working on finance)
- `management.apps.ManagementConfig` (unless working on management)
- `ai_services.apps.AiServicesConfig` (unless working on AI services)
- `portfolio.apps.PortfolioConfig` (unless working on portfolio)
- `professional_services.apps.ProfessionalServicesConfig` (unless working on it)

---

## Testing Checklist

Before using a lightweight branch:

- [ ] ✅ Check that `runserver` starts without errors
- [ ] ✅ Verify templates load correctly
- [ ] ✅ Test that your focused app works
- [ ] ✅ Check that dashboard views work (if used)
- [ ] ⚠️ Verify no missing template tag errors

---

## Next Steps

1. **Complete INVESTING branch fix:**
   - Verify all required apps are in INSTALLED_APPS
   - Test that `python manage.py runserver` works
   - Test that templates load without errors

2. **Apply fixes to other lightweight branches:**
   - FINANCE branch
   - MANAGEMENT branch
   - AI_SERVICES branch

3. **Sync PROD with UAT:**
   - Merge UAT changes (My Account Services section) to PROD
   - Verify PROD dashboard matches UAT

---

**Created:** November 22, 2025  
**Status:** In Progress  
**Priority:** High


