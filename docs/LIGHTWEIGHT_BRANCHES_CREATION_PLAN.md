# 🪶 Lightweight Branches - Recreation Plan

## Strategy

Each lightweight branch will:
1. ✅ Start from synced Heroku UAT code (commit f23127ccd)
2. ✅ Keep ALL apps in INSTALLED_APPS (required for dependencies)
3. ✅ Remove only non-relevant app documentation
4. ✅ Add BRANCH_FOCUS.md to guide developers
5. ✅ Test that `runserver` works before proceeding

## Branch Configuration

### INVESTING Branch
- **Keep Apps:** All apps (main, accounts, application, unified_dashboard, investing, etc.)
- **Remove Docs:** finance, management, ai_services, portfolio app docs
- **Keep Docs:** investing app docs, core docs (01-07)

### FINANCE Branch  
- **Keep Apps:** All apps (required for cross-app dependencies)
- **Remove Docs:** investing, management, ai_services, portfolio app docs
- **Keep Docs:** finance app docs, core docs (01-07)

### MANAGEMENT Branch
- **Keep Apps:** All apps (required for cross-app dependencies)
- **Remove Docs:** investing, finance, ai_services, portfolio app docs
- **Keep Docs:** management app docs, core docs (01-07)

### AI_SERVICES Branch
- **Keep Apps:** All apps (required for cross-app dependencies)
- **Remove Docs:** investing, finance, management, portfolio app docs
- **Keep Docs:** ai_services app docs, core docs (01-07)

## Testing Checklist

For each branch:
- [ ] `python manage.py check` - No errors
- [ ] `python manage.py runserver` - Starts successfully
- [ ] No missing module errors
- [ ] No template tag errors
- [ ] Focus app works correctly

---

**Created:** November 22, 2025  
**Based on:** Heroku UAT deployment (commit f23127ccd)


