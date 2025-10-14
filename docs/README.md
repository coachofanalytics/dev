# CODA Project - Documentation Index

**Last Updated:** October 13, 2025  
**Structure:** Feature-based, 4 docs per feature

---

## 🎯 START HERE

### For New Developers:
1. ⭐ **READ:** [01_GETTING_STARTED/CURSOR_AI_GUIDE.md](01_GETTING_STARTED/CURSOR_AI_GUIDE.md)
2. **Understand:** [02_ARCHITECTURE/](02_ARCHITECTURE/) - System overview
3. **Review:** [03_PROJECT_MANAGEMENT/PROJECT_HISTORY_TIMELINE.md](03_PROJECT_MANAGEMENT/PROJECT_HISTORY_TIMELINE.md)
4. **Then:** Pick your app/feature below

### For Cursor AI (Every Session):
1. ⭐ **ALWAYS READ:** [01_GETTING_STARTED/CURSOR_AI_GUIDE.md](01_GETTING_STARTED/CURSOR_AI_GUIDE.md)
2. **Then Read:** Feature-specific docs in [apps/finance/](#finance-app)
3. **Follow:** Development workflow in the guide
4. **Remember:** Never deploy to production without user permission!

### For Feature Work:
1. Pick your app: [Finance](#finance-app) | Investing | Management
2. Pick your feature within that app
3. Read feature README → IMPLEMENTATION → TESTING

### For Deployment:
1. ⚠️ **Check:** [05_DEPLOYMENT/KNOWN_ISSUES.md](05_DEPLOYMENT/KNOWN_ISSUES.md)
2. **Follow:** [05_DEPLOYMENT/README.md](05_DEPLOYMENT/README.md)
3. **Remember:** Production requires user permission!

---

## 📁 DOCUMENTATION STRUCTURE

```
docs/
├── README.md                       ⭐ You are here
│
├── 01_GETTING_STARTED/            🚀 Start here
│   ├── CURSOR_AI_GUIDE.md         ⭐ AI development guide
│   ├── WORKING_WITH_AI.md
│   └── setup_development_environment.py
│
├── 02_ARCHITECTURE/               🏗️ System architecture
│   ├── README.md
│   └── TECHNICAL_DOCS.md
│
├── 03_PROJECT_MANAGEMENT/         📊 History & roadmap
│   ├── README.md
│   └── PROJECT_HISTORY_TIMELINE.md
│
├── 04_TESTING/                    🧪 Testing strategy
│   ├── README.md
│   └── COMPREHENSIVE_TESTING_STRATEGY.md
│
├── 05_DEPLOYMENT/                 🚀 Deployment
│   ├── README.md
│   ├── KNOWN_ISSUES.md           ⚠️ Read before deploying
│   └── Session summaries
│
├── 06_INTEGRATION/                🔌 External integrations
│
├── 07_MAINTENANCE/                🔧 Operations
│   ├── README.md
│   └── SHARING_FINANCE_APP.md
│
├── apps/                          📱 App-specific docs
│   └── finance/                   ⭐ Finance App (Complete)
│       ├── README.md               Master index for finance
│       ├── Budget/                 💰 4 docs
│       │   ├── README.md
│       │   ├── REQUIREMENTS.md
│       │   ├── IMPLEMENTATION.md
│       │   └── TESTING.md
│       ├── Transaction/            📊 4 docs
│       ├── Loan/                   🏦 4 docs
│       ├── Payment/                💳 4 docs
│       └── Shared/                 🔧 Cross-feature
│
└── 05_DEPLOYMENT/                  🚀 Deployment logs
    ├── LATEST.md                   Most recent session
    ├── 2025_OCT_13.md              This session
    ├── KNOWN_ISSUES.md             Project-wide issues
    └── archive/                    Old session logs
```

---

## 💰 FINANCE APP

**Location:** [`coda/docs/apps/finance/`](coda/docs/apps/finance/)

### Master Index
- **[Finance README](coda/docs/apps/finance/README.md)** - Start here for finance app overview

### Features (4 docs each):

#### Budget System
**Status:** Phase 1 Complete, Phase 2 In Progress  
**Docs:**
- [README](coda/docs/apps/finance/Budget/README.md) - Overview & status
- [REQUIREMENTS](coda/docs/apps/finance/Budget/REQUIREMENTS.md) - Business requirements & tiers
- [IMPLEMENTATION](coda/docs/apps/finance/Budget/IMPLEMENTATION.md) - Technical details
- [TESTING](coda/docs/apps/finance/Budget/TESTING.md) - Test guide

**Quick Summary:** Budget request creation, three-tier approval system (Known/Variable/Strategic), approval dashboard.

---

#### Transaction System
**Status:** Working (95.6% data quality)  
**Docs:**
- [README](coda/docs/apps/finance/Transaction/README.md)
- [REQUIREMENTS](coda/docs/apps/finance/Transaction/REQUIREMENTS.md)
- [IMPLEMENTATION](coda/docs/apps/finance/Transaction/IMPLEMENTATION.md)
- [TESTING](coda/docs/apps/finance/Transaction/TESTING.md)

**Quick Summary:** Smart transaction entry with AI predictions, auto-categorization, $1.49M dataset.

---

#### Loan System
**Status:** Working  
**Docs:**
- [README](coda/docs/apps/finance/Loan/README.md)
- [REQUIREMENTS](coda/docs/apps/finance/Loan/REQUIREMENTS.md)
- [IMPLEMENTATION](coda/docs/apps/finance/Loan/IMPLEMENTATION.md)
- [TESTING](coda/docs/apps/finance/Loan/TESTING.md)

**Quick Summary:** Loan products, applications, eligibility checking, KCC integration.

---

#### Payment System
**Status:** ⚠️ Temporarily Disabled  
**Docs:**
- [README](coda/docs/apps/finance/Payment/README.md)
- [REQUIREMENTS](coda/docs/apps/finance/Payment/REQUIREMENTS.md)
- [IMPLEMENTATION](coda/docs/apps/finance/Payment/IMPLEMENTATION.md)
- [TESTING](coda/docs/apps/finance/Payment/TESTING.md)

**Quick Summary:** M-Pesa, Stripe, Bank Transfer (currently disabled - missing `_deprecated` module).

---

#### Shared Documentation
**Docs:**
- [Shared README](coda/docs/apps/finance/Shared/README.md)
- [Theme Switcher](coda/docs/apps/finance/Shared/THEME_SWITCHER.md) - Dashboard themes

**Quick Summary:** Cross-feature functionality (themes, APIs, common analysis frameworks).

---

## 🚀 DEPLOYMENT DOCUMENTATION

**Location:** [`coda/docs/05_DEPLOYMENT/`](coda/docs/05_DEPLOYMENT/)

### Session Summaries
- **[October 13, 2025](coda/docs/05_DEPLOYMENT/2025_OCT_13.md)** - Latest session (approval workflow fixes, schema alignment, doc reorganization)
- **[Known Issues](coda/docs/05_DEPLOYMENT/KNOWN_ISSUES.md)** - Project-wide tracking

### Deployment Commands
```bash
# Deploy to UAT
git push heroku 25.10_UAT_DEPLOYMENT_FIX_CM:main --force

# Check logs
heroku logs --tail --app codamakutano

# Run migrations
heroku run "cd coda && python manage.py migrate" --app codamakutano
```

---

## 📋 DOCUMENTATION STANDARDS

### The 4-Doc Standard

Every feature has exactly 4 docs:

1. **README.md** - What & Why
   - Overview, current status, quick start
   - Update: After major changes

2. **REQUIREMENTS.md** - What It Should Do
   - Business requirements (Phase 1, 2, 3...)
   - Update: When requirements change

3. **IMPLEMENTATION.md** - How It Works
   - Technical details, code locations, architecture
   - Update: Every code change

4. **TESTING.md** - How to Verify
   - Test scenarios, validation, results log
   - Update: Every new test or test run

### Naming Conventions
- ✅ Standard docs: **ALL_CAPS.md** (README, REQUIREMENTS, etc.)
- ✅ Feature names: **PascalCase** (Budget/, Loan/, Transaction/)
- ❌ Don't create: Date-based docs (OCT13_*.md) - update existing instead

### When NOT to Create New Docs
- ❌ Bug fixes → Add to TESTING (regression test)
- ❌ Feature planning → Add to REQUIREMENTS (Phase X)
- ❌ Code changes → Update IMPLEMENTATION
- ❌ Deployment notes → Goes in `/docs/05_DEPLOYMENT/`

---

## 🔍 FINDING INFORMATION

### "Where is the budget approval logic?"
→ [Budget/IMPLEMENTATION.md](coda/docs/apps/finance/Budget/IMPLEMENTATION.md)

### "What are the business requirements for loans?"
→ [Loan/REQUIREMENTS.md](coda/docs/apps/finance/Loan/REQUIREMENTS.md)

### "How do I test transactions?"
→ [Transaction/TESTING.md](coda/docs/apps/finance/Transaction/TESTING.md)

### "What's the current status of payments?"
→ [Payment/README.md](coda/docs/apps/finance/Payment/README.md)

### "What broke in deployment?"
→ [05_DEPLOYMENT/KNOWN_ISSUES.md](coda/docs/05_DEPLOYMENT/KNOWN_ISSUES.md)

### "How does the theme switcher work?"
→ [Shared/THEME_SWITCHER.md](coda/docs/apps/finance/Shared/THEME_SWITCHER.md)

---

## 📊 METRICS

### Before Reorganization (Oct 13):
- 30-50+ scattered docs
- No clear structure
- Lots of duplication
- Hard to maintain

### After Reorganization (Oct 13):
- **19 core docs** (Finance: 4 features × 4 docs + 3 shared)
- Clear, predictable structure
- Zero duplication
- Easy to maintain

**Reduction:** ~60% fewer docs, 100% better clarity! 🎯

---

## 🗺️ ROADMAP

### Immediate (This Week):
- ✅ Finance app documentation restructured
- 🔄 Test all finance features in UAT
- 📋 Deploy Phase 2 budget approval system

### Next (This Month):
- Reorganize other app docs (Marketing, Management)
- Create master API documentation
- Consolidate deployment guides

### Future:
- Interactive documentation site
- Auto-generated API docs
- Video walkthroughs

---

## 🤝 CONTRIBUTING

### Adding Documentation for New Feature:

1. **Create feature directory:**
   ```bash
   mkdir -p coda/docs/apps/[app_name]/[FeatureName]/
   ```

2. **Create 4 standard docs:**
   - Copy templates from `DOCUMENTATION_STRUCTURE_REFINED.md`
   - Fill in: README, REQUIREMENTS, IMPLEMENTATION, TESTING

3. **Update parent README:**
   - Add link to your feature in app README
   - Add summary

4. **Update this index:**
   - Add entry under appropriate app section

### Updating Existing Documentation:

- **New requirement?** → Update REQUIREMENTS.md (add to Phase X)
- **Code change?** → Update IMPLEMENTATION.md
- **Bug fix?** → Add regression test to TESTING.md
- **Status change?** → Update README.md

**Don't create new docs - update existing ones!**

---

## 📞 GETTING HELP

### Documentation Issues:
- File in repo as issue
- Tag with `documentation` label
- Suggest fix if you have one

### Technical Questions:
- Check feature IMPLEMENTATION docs first
- Check MASTER_REFERENCE (being phased out)
- Ask in team channel

---

## 📚 LEGACY DOCUMENTATION

### Being Phased Out:
- `MASTER_REFERENCE.md` - Consolidated into feature docs
- Various `_PLAN.md`, `_ANALYSIS.md` files - Merged into REQUIREMENTS/IMPLEMENTATION
- Date-based session docs - Archived in 05_DEPLOYMENT/archive/

### Archive Location:
- `coda/docs/apps/finance/_archive/pre_restructure_oct13/`

**Don't use legacy docs - they're outdated!**

---

## ✨ WHAT'S NEW

### October 13, 2025:
- 🎯 **Complete finance documentation restructure**
  - Budget, Transaction, Loan, Payment features
  - 4-doc standard implemented
  - Shared documentation created

- 🐛 **Bug fixes documented:**
  - Budget approval workflow (missing fields)
  - Loan schema alignment (term_months)
  - Payment system disabled gracefully

- 🎨 **New features:**
  - Theme switcher documented
  - Approval workflow business analysis

---

**Maintained by:** Cursor AI Assistant  
**Restructured:** October 13, 2025  
**Next Review:** After Phase 2 budget implementation

---

## 🎯 QUICK LINKS

- [Finance App Docs](coda/docs/apps/finance/)
- [Budget System](coda/docs/apps/finance/Budget/)
- [Deployment Logs](coda/docs/05_DEPLOYMENT/)
- [Known Issues](coda/docs/05_DEPLOYMENT/KNOWN_ISSUES.md)
- [This Session Summary](coda/docs/05_DEPLOYMENT/2025_OCT_13.md)

**Happy Documenting! 📖**
