# 🎯 INVESTING Branch - Focus Guide

## This Branch: `25.11_INVESTING_DEV`

**FOCUS ON:** `coda/investing/` app

## 📁 Work Here
- `coda/investing/models.py` - Trading accounts, positions, signals
- `coda/investing/views/managed_trading/` - Staff and client views
- `coda/investing/services/` - Ranking, fetching, analytics services
- `coda/investing/templates/investing/` - Dashboard templates

## 📚 Documentation
- `docs/apps/investing/` - Investing-specific documentation only
- `docs/01_GETTING_STARTED/` - Core setup guides
- `docs/02_ARCHITECTURE/` - System architecture
- `docs/03_PROJECT_MANAGEMENT/` - Project workflows
- `docs/04_TESTING/` - Testing strategies
- `docs/05_DEPLOYMENT/` - Deployment guides
- `docs/06_INTEGRATION/` - Integration patterns
- `docs/07_MAINTENANCE/` - Maintenance procedures

## ⚙️ INSTALLED_APPS
**All apps are installed** - required for cross-app dependencies:
- ✅ All apps present (main, accounts, investing, finance, management, etc.)
- ✅ This ensures imports and dependencies work correctly
- ✅ Only documentation is removed for performance

## 🚫 Ignore These (Other Branches)
- `coda/finance/` → Use `25.11_FINANCE_DEV` for finance work
- `coda/management/` → Use `25.11_MANAGEMENT_DEV` for management work
- `coda/ai_services/` → Use `25.11_AI_SERVICES_DEV` for AI services work

## 💡 Quick Start
1. Read `docs/01_GETTING_STARTED/CURSOR_AI_GUIDE.md`
2. Review `docs/apps/investing/` for investing docs
3. Start coding in `coda/investing/`!
4. Test: `python coda/manage.py runserver`

## 🧪 Testing
```bash
cd /Users/coda/PROJECTS/CODA/DEVELOPMENT/DEV
source venv/bin/activate
python coda/manage.py check
python coda/manage.py runserver
```

---
**Created:** November 22, 2025  
**Based on:** Heroku UAT (commit f23127ccd)  
**Status:** ✅ Ready for development

