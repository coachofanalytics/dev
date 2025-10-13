# CODA Development Project

**Status:** Active Development  
**Last Updated:** October 13, 2025

## 📚 Documentation

**Complete documentation is available in:** [`coda/docs/`](coda/docs/)

### Quick Links:
- **[Master Documentation Index](coda/docs/README.md)** - Start here
- **[Finance App](coda/docs/apps/finance/)** - Budget, Transaction, Loan, Payment systems
- **[Deployment Guide](coda/docs/05_DEPLOYMENT/)** - Deployment instructions and logs
- **[Getting Started](coda/docs/01_GETTING_STARTED/)** - Setup guide

## 🎯 Current Status

### ✅ COMPLETED (Oct 2025)
- **Phase 1:** Data cleanup (95.6% categorized, $1.49M dataset)
- **Phase 2:** Smart forms with AI predictions, cascading dropdowns
- **Budget System:** Phase 1 approval workflow complete
- **Documentation:** Restructured into feature-based organization (4 docs per feature)
- **Critical Fixes:** Dashboard aggregation, schema alignment, approval workflow

### 🔄 IN PROGRESS
- **Budget System Phase 2:** Data-driven tier-based approval system
- **Transaction Analytics:** Enhanced reporting and insights
- **Code Quality:** Continued refactoring and optimization

## ⚙️ Configuration Files

**Heroku Deployment Files (Root Level):**
- `Procfile` - Heroku process definition (tells Heroku to run from `/coda/`)
- `requirements.txt` - Python dependencies
- `runtime.txt` - Python version

⚠️ **These files MUST stay in the root directory for Heroku deployment.**

## 🚀 Quick Start

### Local Development
```bash
cd /Users/coda/PROJECTS/CODA/DEVELOPMENT/DEV
source venv/bin/activate
cd coda
python manage.py runserver 0.0.0.0:8000
```

### Run Tests
```bash
# Run all tests
./tests/run_tests.sh

# Run regression tests only (before deployment)
./tests/run_tests.sh --regression
```

See [`tests/README.md`](tests/README.md) for complete testing guide.

### Test Users
- **budget_manager** / test123 (Budget Dashboard)
- **finance_officer** / test123 (Finance Operations)
- **it_manager** / test123 (IT Systems)

### Key URLs
- **Login:** http://127.0.0.1:8000/accounts/login/
- **Unified Dashboard:** http://127.0.0.1:8000/dashboard/
- **Budget Dashboard:** http://127.0.0.1:8000/finance/budget-dashboard/coda/

## 🔧 Recent Fixes

### View Details Button (FIXED)
- **Issue:** Buttons clicked but nothing happened
- **Root Cause:** Invalid model relationships + missing template
- **Fix:** Corrected prefetch_related, created template
- **Status:** ✅ Working

### Login Redirect (FIXED)
- **Issue:** Login went to home page instead of dashboard
- **Root Cause:** Missing @login_required decorator
- **Fix:** Added decorator to unified_dashboard view
- **Status:** ✅ Working

## 📊 System Health
- **Server:** Running stable
- **Database:** 366 transactions, $1.49M total
- **Errors:** All critical errors resolved
- **Performance:** Good

## 🎯 Next Steps
1. Test all buttons in templates
2. Verify budget calculations
3. Test complete workflows
4. Deploy to UAT

## 📖 Project Structure

```
CODA/
├── coda/                   # Django project
│   ├── docs/              # All documentation
│   ├── finance/           # Finance app
│   ├── accounts/          # User management
│   └── ...
│
├── tests/                 # All test scripts
│   ├── run_tests.sh      # Main test runner
│   └── README.md         # Testing guide
│
├── scripts/               # Helper scripts
│   └── README.md         # Scripts guide
│
└── venv/                  # Virtual environment
```

### Documentation Structure

All documentation follows a **4-doc standard per feature**:
1. **README.md** - Overview and current status
2. **REQUIREMENTS.md** - Business requirements (historical + current + future)
3. **IMPLEMENTATION.md** - Technical details and code locations
4. **TESTING.md** - Test scenarios and validation

See [`coda/docs/README.md`](coda/docs/README.md) for complete navigation guide.

## 📞 Support
For detailed information, see the [comprehensive documentation](coda/docs/) or check deployment logs in [`coda/docs/05_DEPLOYMENT/`](coda/docs/05_DEPLOYMENT/).
