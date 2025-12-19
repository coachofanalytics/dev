# CODA Development Project

**Status:** Active Development  
**Last Updated:** December 2025

## 📚 Documentation

**Complete documentation is available in:** [`docs/`](docs/)

### Quick Links:
- **[Getting Started Guide](docs/01_GETTING_STARTED/CURSOR_AI_GUIDE.md)** - AI development guidelines and workflow
- **[Architecture](docs/02_ARCHITECTURE/)** - System architecture and design patterns
- **[Project Management](docs/03_IMPLEMENTATION/)** - Branch management, workflows, migrations
- **[Testing](docs/04_TESTING/)** - Testing strategies and results
- **[Deployment](docs/05_DEPLOYMENT/)** - Deployment guides and procedures
- **[Integration](docs/06_INTEGRATION/)** - Integration patterns and external services
- **[Maintenance](docs/07_MAINTENANCE/)** - Operational procedures and maintenance guides

### Application Documentation:
- **[Finance App](docs/apps/finance/)** - Budget, Transaction, Loan, Payment systems
- **[Accounts App](docs/apps/accounts/)** - Authentication, Registration, Permissions
- **[Investing App](docs/apps/investing/)** - Managed Options Trading, AI Position Scoring
- **[Management App](docs/apps/management/)** - Employee Task System
- **[AI Services](docs/apps/ai_services/)** - GoToMeeting integration

## 🎯 Current Status

### ✅ Documentation Structure (Dec 2025)
- **7-Doc Framework:** All app features follow standardized 7-doc structure
- **Organization:** Complete reorganization into feature-based documentation
- **Branch Management:** Lightweight branches and focused development workflows established

### ✅ Completed Features
- **Finance System:** Budget, Transaction, Loan, Payment systems operational
- **Investing System:** Managed Options Trading, AI Position Scoring deployed
- **Management System:** Employee Task System with analytics and forecasting
- **Accounts System:** Complete authentication, permissions, and user management

### 🔄 Active Development
- Feature enhancements across all apps
- Code quality improvements and refactoring
- Performance optimization

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

All application features follow a **7-doc standard**:
1. **01_ANALYSIS.md** - Problem statement, goals, ROI
2. **02_REQUIREMENTS.md** - Functional and non-functional requirements
3. **03_ARCHITECTURE.md** - System design and architecture
4. **04_IMPLEMENTATION.md** - Code locations and implementation details
5. **05_TESTING.md** - Test strategy and scenarios
6. **06_MAINTENANCE.md** - Known issues, fixes, operational procedures
7. **07_DEPLOYMENT.md** - Deployment procedures and history
8. **README.md** - Quick overview and navigation

See [`docs/01_GETTING_STARTED/CURSOR_AI_GUIDE.md`](docs/01_GETTING_STARTED/CURSOR_AI_GUIDE.md) for complete development guidelines.

## 📞 Support
For detailed information, see the [comprehensive documentation](docs/) or check deployment logs in [`docs/05_DEPLOYMENT/`](docs/05_DEPLOYMENT/).
