# 🔍 Heroku UAT vs Local Comparison

## Current Heroku UAT Deployment
- **Commit:** `f23127ccd` (v1073)
- **Deployed:** 2025/11/18 18:38:30
- **Branch:** `heroku/main` (Heroku git remote)

## Findings

### Dashboard Template Analysis

**Heroku UAT deployed template** (`heroku/main:coda/unified_dashboard/templates/unified_dashboard/dashboard.html`):
- ❌ **DOES NOT** have "My Account Services" section
- ✅ Has "Available Dashboards" section
- ✅ Has "Dashboard Sections" section
- ✅ `role_based_links` is passed in context from `views.py` but NOT rendered in template

**Local UAT branch** (`25.11_CODA_UAT_CM`):
- ❌ Also does NOT have "My Account Services" section (same as Heroku)
- Same template structure as Heroku

**User Observation:**
- User sees "My Account Services" section with buttons like "Edit Profile", "My DAF" on codamakutano.herokuapp.com
- This suggests either:
  1. A different template/view is being used
  2. Template was manually modified on Heroku (unlikely, as it's read-only)
  3. A different route/URL is being accessed
  4. Browser cache showing old version

## Next Steps

1. **Check what template is actually being served:**
   ```bash
   # Check Heroku logs to see which template is rendered
   heroku logs -a codamakutano --tail 100 | grep -i dashboard
   ```

2. **Compare department_dashboards.html:**
   - This template DOES have "My Account Services" section
   - Check if users are accessing `/dashboard/department/` instead of `/dashboard/`

3. **Verify the actual deployed files match git:**
   ```bash
   heroku run -a codamakutano "ls -la coda/unified_dashboard/templates/unified_dashboard/"
   ```

4. **Check URL routing:**
   - Verify which view handles `/dashboard/` route
   - Check if there's a redirect or different view being used

---

**Created:** November 22, 2025  
**Status:** Investigation in progress


