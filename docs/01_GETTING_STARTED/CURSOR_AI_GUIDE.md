# CURSOR AI GUIDE FOR CODA DEVELOPMENT
**Purpose:** Complete guide for AI-assisted development on CODA  
**Last Updated:** October 16, 2025 (Added Production Deployment Lessons)

---

## 🎯 QUICK START FOR CURSOR AI

### When Starting ANY Task:

**ALWAYS Read These Files First:**
1. `docs/README.md` - Master documentation index
2. `docs/apps/finance/[Feature]/README.md` - Feature overview and status
3. `docs/PROJECT_HISTORY_TIMELINE.md` - Project history and decisions

**For Specific Tasks:**
- **Bug Fix:** Read `docs/05_DEPLOYMENT/KNOWN_ISSUES.md`
- **New Feature:** Read `docs/apps/finance/[Feature]/REQUIREMENTS.md`
- **Testing:** Read `docs/COMPREHENSIVE_TESTING_STRATEGY.md`
- **Deployment:** Read `docs/05_DEPLOYMENT/READY_TO_DEPLOY.md`

---

## 📚 ESSENTIAL DOCUMENTS TO ALWAYS CHECK

### 1. Feature Documentation (REQUIRED)
**Location:** `docs/apps/finance/[Feature]/`

Every feature has exactly 4 documents:
- **README.md** - What & Why (overview, status, history)
- **REQUIREMENTS.md** - What it should do (business requirements, all phases)
- **IMPLEMENTATION.md** - How it works (technical details, code locations)
- **TESTING.md** - How to verify (test scenarios, results)

**Always check these BEFORE making changes!**

### 2. Project History (CRITICAL)
**Location:** `docs/PROJECT_HISTORY_TIMELINE.md`

**Contains:**
- Complete project timeline (Sept 2024 - Oct 2025)
- All phases (Phase 1, 2, 3 completion status)
- Critical bugs fixed (7 major bugs documented)
- Lessons learned from each bug
- Key decisions and rationale

**Why Critical:** Prevents repeating mistakes, understand context

### 3. Known Issues (MUST READ BEFORE DEPLOYMENT)
**Location:** `docs/05_DEPLOYMENT/KNOWN_ISSUES.md`

**Contains:**
- Current blocking issues
- Workarounds in place
- Issues to watch for
- Recent fixes

**Always check before deploying!**

---

## 🛠️ DEVELOPMENT WORKFLOW

### Step 1: Understand the Request
```
User Request → Read Feature Docs → Check if Already Exists → Plan Approach
```

**Questions to Ask:**
1. Which feature does this affect? (Budget, Transaction, Loan, Payment)
2. Is this already in REQUIREMENTS.md? (might be planned in Phase X)
3. Does this relate to a known bug? (check KNOWN_ISSUES.md)
4. What phase are we in? (check PROJECT_HISTORY_TIMELINE.md)

### Step 2: Review Existing Code
```
Read IMPLEMENTATION.md → Locate files → Understand current implementation
```

**Key Sections to Check:**
- Data Model (what models are involved)
- Views & URLs (what views handle this)
- Services (what business logic exists)
- API Endpoints (what APIs are available)
- Change History (what's been done recently)

### Step 3: Implement Changes

**ALWAYS:**
- ✅ Follow existing patterns in the codebase
- ✅ Use service layer for business logic
- ✅ Add docstrings to functions/classes
- ✅ Use Django ORM efficiently (select_related, prefetch_related)
- ✅ Handle errors gracefully

**NEVER:**
- ❌ Create duplicate functionality
- ❌ Skip migrations for model changes
- ❌ Hardcode values (use settings)
- ❌ Ignore existing conventions
- ❌ Make breaking changes without discussion

### Step 4: Update Documentation

**Required Updates:**
1. **IMPLEMENTATION.md** - Add to Change History table
2. **README.md** - Update status if major feature
3. **TESTING.md** - Add test scenarios
4. **REQUIREMENTS.md** - Mark requirement as completed

### Step 5: Write Tests

**ALWAYS add tests for:**
- ✅ Bug fixes (regression test)
- ✅ New features (unit + integration tests)
- ✅ Model changes (model tests)
- ✅ API changes (API tests)

**Test Location:**
- Django tests: `coda/finance/tests/test_*.py`
- Integration tests: `tests/test_*.py`
- Regression tests: `coda/finance/tests/test_regressions.py`

### Step 6: Run Tests Before Committing

```bash
# ALWAYS run before committing
./tests/run_tests.sh --regression

# For Django tests
cd coda && python manage.py test finance

# Check for linter errors
cd coda && python manage.py check
```

---

## ⚠️ CRITICAL THINGS TO WATCH

### 1. Dashboard Aggregation (CRITICAL BUG - Fixed Oct 1)
**ALWAYS use this pattern for budget totals:**
```python
# CORRECT ✅
total = Sum(F('unit_price') * F('quantity') * Coalesce(F('cases'), 1), 
            output_field=DecimalField())

# WRONG ❌ (causes 177x inflation)
total = Sum('quantity') * Sum('unit_price')
```

**Why:** The wrong pattern multiplies sum of ALL quantities by sum of ALL prices

### 2. Model Schema Alignment (CRITICAL)
**ALWAYS verify dev schema matches production!**

**Example:** LoanProduct schema mismatch (Oct 13)
- Dev had: `min_term_months`, `max_term_months`
- Production had: `term_months`
- Result: Crashed in production

**Before changing models:**
1. Check production schema
2. Create migration
3. Test migration in UAT
4. Document in IMPLEMENTATION.md

### 3. Missing Model Fields (Common Error)
**ALWAYS verify template fields exist in model!**

**Example:** BudgetRequest missing `approved_by` fields (Oct 13)
- Template used: `request.approved_by.username`
- Model didn't have: `approved_by` field
- Result: AttributeError

**Before using fields in templates:**
1. Check model has the field
2. Check field is nullable if optional
3. Add null checks in template: `{% if request.approved_by %}`

### 4. Circular Imports (Watch For)
**Avoid:** Views → Services → Models → Views

**Solution:** Use service layer properly
- Models should NOT import views
- Services should NOT import views
- Views CAN import services and models
- Use lazy imports if needed: `from django.apps import apps`

### 5. Form Widget IDs (Required for JavaScript)
**ALWAYS add explicit widget IDs for JavaScript targeting:**

```python
# CORRECT ✅
class MyForm(forms.ModelForm):
    class Meta:
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control', 'id': 'id_category'}),
            'subcategory': forms.Select(attrs={'class': 'form-control', 'id': 'id_subcategory'}),
        }

# WRONG ❌ (JavaScript can't find fields)
# No widgets dict - Django auto-generates IDs inconsistently
```

---

## 🧪 TESTING REQUIREMENTS

### Before ANY Deployment:

**1. Run Regression Tests (MANDATORY):**
```bash
./tests/run_tests.sh --regression
```

**These MUST pass:**
- Budget approval fields exist
- Loan product schema correct
- Staff permission logic works
- Dashboard aggregation correct

**2. Check Django Tests:**
```bash
cd coda && python manage.py test finance
```

**3. Manual Checks:**
- [ ] No linter errors: `python manage.py check`
- [ ] Migrations created: `python manage.py makemigrations --dry-run`
- [ ] Local server runs: `python manage.py runserver`
- [ ] Test critical URLs manually

**4. Browser Testing:**
- [ ] Open browser console (F12)
- [ ] Check for JavaScript errors
- [ ] Test key user journeys
- [ ] Verify theme switcher works

---

## 🚀 DEPLOYMENT WORKFLOW

### Deploying to UAT (Allowed)

**Pre-Deployment Checklist:**
1. ✅ All regression tests pass
2. ✅ Documentation updated
3. ✅ Changes committed to git
4. ✅ Reviewed by user (if major change)

**Deployment Commands:**
```bash
# 1. Ensure on correct branch
git branch  # Should show 25.10_UAT_DEPLOYMENT_FIX_CM

# 2. Push to GitHub (backup)
git push uat 25.10_UAT_DEPLOYMENT_FIX_CM

# 3. Deploy to Heroku UAT
git push heroku 25.10_UAT_DEPLOYMENT_FIX_CM:main --force

# 4. Monitor deployment
heroku logs --tail --app codamakutano --num 50

# 5. Wait for build complete
# (Watch for "Verifying deploy... done.")

# 6. Run post-deployment tests
./tests/test_uat_urls.sh

# 7. Manual verification
# Visit: https://codamakutano.herokuapp.com
# Test: Login, dashboard, key features
```

**Post-Deployment:**
```bash
# Check for errors
heroku logs --app codamakutano --tail

# Verify URLs
curl https://codamakutano.herokuapp.com/dashboard/
curl https://codamakutano.herokuapp.com/finance/budget/coda/approvals/

# Check database migrations
heroku run "cd coda && python manage.py showmigrations finance" --app codamakutano
```

---

### Deploying to Production (REQUIRES PERMISSION)

⚠️ **NEVER deploy to production without explicit user permission!**

**Pre-Production Checklist:**
1. ✅ Thoroughly tested in UAT (minimum 24 hours)
2. ✅ User has approved deployment
3. ✅ No known critical bugs
4. ✅ Database backup created
5. ✅ Rollback plan prepared
6. ✅ Deployment time agreed (low-traffic window)

**Production Deployment (Only with Permission):**
```bash
# ASK USER FIRST: "Ready to deploy to production?"

# If YES:
git push production 25.10_UAT_DEPLOYMENT_FIX_CM:main --force

# Monitor closely
heroku logs --tail --app codatrainingapp --num 100

# Verify immediately
curl https://codatrainingapp.herokuapp.com/dashboard/

# Monitor for 1 hour post-deployment
# Be ready to rollback if issues
```

**Rollback (If Issues):**
```bash
# Revert to previous version
heroku releases --app codatrainingapp
heroku rollback v[PREVIOUS_VERSION] --app codatrainingapp
```

---

## 🎓 PRODUCTION DEPLOYMENT LESSONS LEARNED (October 2025)

### Critical Lesson 1: NEVER Commit Virtual Environments

**Problem Encountered:**
- `venv/` directory was tracked in git (597MB!)
- This bloated the repository and Heroku slug size to 600MB+
- Slow deployments, wasted storage, unnecessary files in production

**Solution:**
```bash
# Remove venv from git tracking
git rm -r --cached venv/

# Ensure venv/ is in .gitignore
echo "venv/" >> .gitignore
echo "env/" >> .gitignore
echo "ENV/" >> .gitignore
```

**Result:** Reduced Heroku slug from 600MB+ to 79.7MB (87% reduction!)

**Rule:** ✅ Virtual environments should ALWAYS be in `.gitignore`

---

### Critical Lesson 2: Understand .gitignore vs .slugignore

**Key Difference:**
- **`.gitignore`**: Controls what goes into git repository
- **`.slugignore`**: Controls what gets deployed to Heroku

**Best Practice:**
```bash
# .gitignore - Don't commit these
venv/
*.pyc
__pycache__/
.env
local_settings.py

# .slugignore - Don't deploy these (but keep in git)
docs/
tests/
scripts/
archive/
backups/
*.md
```

**Result:** Lean production deployment with full documentation in git

---

### Critical Lesson 3: Django Settings Import Paths Matter

**Problem Encountered:**
```
ModuleNotFoundError: No module named 'coda_project.heroku_settings'
```

**Root Cause:** 
`wsgi.py` was using wrong import path when settings were in a subdirectory:
```python
# WRONG ❌
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda_project.heroku_settings')

# CORRECT ✅
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda_project.coda_settings.heroku_settings')
```

**Fix Location:** `coda/coda_project/wsgi.py`

**Rule:** Always verify import paths match your actual directory structure!

---

### Critical Lesson 4: ENVIRONMENT Variable Must Match Settings Logic

**Problem Encountered:**
```
ModuleNotFoundError: No module named 'coda_project.coda_settings.local_settings'
```

**Root Cause:**
UAT had `ENVIRONMENT=testing` but `settings.py` didn't have a case for "testing", so it fell through to loading `local_settings.py` (which doesn't exist on Heroku).

**Settings.py Logic:**
```python
if ENVIRONMENT == 'local':
    from .coda_settings.local_settings import *
elif ENVIRONMENT == 'staging':
    from .coda_settings.heroku_settings import *
elif ENVIRONMENT == 'production':
    from .coda_settings.prod_settings import *
else:
    # Falls through to local_settings ❌
    from .coda_settings.local_settings import *
```

**Solution:**
```bash
# UAT
heroku config:set ENVIRONMENT=staging --app codamakutano

# Production
heroku config:set ENVIRONMENT=production --app codatrainingapp
```

**Rule:** ✅ ENVIRONMENT variable must match a case in settings.py!

---

### Critical Lesson 5: ALLOWED_HOSTS Must Include Heroku App URLs

**Problem Encountered:**
```
Invalid HTTP_HOST header: 'codatrainingapp.herokuapp.com'. 
You may need to add 'codatrainingapp.herokuapp.com' to ALLOWED_HOSTS.
```

**Root Cause:**
Production settings didn't include the Heroku app URL in ALLOWED_HOSTS.

**Solution:**
```python
# prod_settings.py
ALLOWED_HOSTS = [
    'www.codanalytics.net',
    'codanalytics.net',
    'codatrainingapp.herokuapp.com',  # ← Must add this!
    'localhost',
    '127.0.0.1',
]

# heroku_settings.py  
ALLOWED_HOSTS = [
    'codamakutano.herokuapp.com',  # ← Must add this!
    'www.codanalytics.net',
    'codanalytics.net',
    'localhost',
    '127.0.0.1',
]
```

**Rule:** ✅ Always add your Heroku app URL to ALLOWED_HOSTS!

---

### Critical Lesson 6: Production Deployment Verification Process

**Step-by-Step Debugging:**

1. **Deploy and check slug size:**
   ```bash
   git push heroku branch:main --force
   # Watch for: "Compressing... Done: XX.XM"
   # Should be <100M for lean deployment
   ```

2. **Test URL immediately:**
   ```bash
   curl -I https://yourapp.herokuapp.com/
   # Should return: HTTP/1.1 200 OK
   # If 503: App crashed - check logs immediately
   ```

3. **Check logs for errors:**
   ```bash
   heroku logs --app yourapp --num 100 | grep -i "error\|crash\|fail"
   ```

4. **Common errors to look for:**
   - `ModuleNotFoundError` → Import path wrong
   - `Invalid HTTP_HOST` → Add to ALLOWED_HOSTS
   - `Worker failed to boot` → Check settings loading
   - `TemplateDoesNotExist` → Template path issue

5. **Test critical URLs:**
   ```bash
   curl -I https://yourapp.herokuapp.com/
   curl -I https://yourapp.herokuapp.com/finance/budget-dashboard/coda/
   curl -I https://yourapp.herokuapp.com/accounts/login/
   ```

**Rule:** ✅ Never assume deployment worked - always verify!

---

### Critical Lesson 7: Settings Files May Be in .gitignore

**Problem Encountered:**
```bash
git add coda/coda_project/coda_settings/prod_settings.py
# The following paths are ignored by one of your .gitignore files
```

**Root Cause:**
Settings directory was in `.gitignore` to protect sensitive data.

**Solution:**
```bash
# Force add specific settings file
git add -f coda/coda_project/coda_settings/prod_settings.py

# OR: Create template files that aren't ignored
# Then load secrets from environment variables
```

**Best Practice:**
- Keep sensitive settings in environment variables
- Commit template settings files
- Load secrets with `os.environ.get()`

**Rule:** ✅ Use environment variables for secrets, not hardcoded values!

---

### Production Deployment Checklist (Updated)

**Before Deploying:**
- [ ] ✅ venv/ NOT in git (check: `git ls-files | grep venv`)
- [ ] ✅ .slugignore exists and excludes docs/, tests/, scripts/
- [ ] ✅ ENVIRONMENT variable set correctly on Heroku
- [ ] ✅ ALLOWED_HOSTS includes Heroku app URL
- [ ] ✅ wsgi.py uses correct settings import path
- [ ] ✅ Settings conditional logic covers all ENVIRONMENT values
- [ ] ✅ All sensitive data in environment variables

**After Deploying:**
- [ ] ✅ Check slug size (should be <100M)
- [ ] ✅ Test home page (curl -I)
- [ ] ✅ Check logs for errors
- [ ] ✅ Test critical URLs
- [ ] ✅ Monitor for 5-10 minutes
- [ ] ✅ Verify no ALLOWED_HOSTS errors

---

### Deployment Metrics to Track

**Good Deployment:**
- Slug size: <100M (lean)
- Build time: <3 minutes
- No errors in logs
- All URLs return 200 OK
- Memory usage: <50% of dyno limit

**Problem Indicators:**
- Slug size: >200M (bloated - check for venv/)
- Build time: >5 minutes (too slow)
- 503 errors (app crashed - check logs)
- ALLOWED_HOSTS errors (config issue)
- High memory usage: >80% (optimization needed)

---

## 🐛 DEBUGGING WORKFLOW

### When User Reports a Bug:

**Step 1: Gather Information**
Ask for:
- [ ] URL where error occurs
- [ ] Browser console logs (F12 → Console tab)
- [ ] Expected vs actual behavior
- [ ] Steps to reproduce
- [ ] Recent changes that might be related

**Step 2: Check Known Issues**
```bash
# Read this file
cat docs/05_DEPLOYMENT/KNOWN_ISSUES.md

# Check if this bug is already documented
# Check if there's a workaround
```

**Step 3: Check Recent Fixes**
```bash
# Read change history
cat docs/apps/finance/[Feature]/IMPLEMENTATION.md | grep "Change History"

# Check for similar bugs in timeline
cat docs/PROJECT_HISTORY_TIMELINE.md | grep -i "[keyword]"
```

**Step 4: Review Regression Tests**
```bash
# Check if we have a test for this
cat coda/finance/tests/test_regressions.py

# If bug is related to a previous fix, regression test might have clues
```

**Step 5: Debug**
```bash
# Check Heroku logs (if UAT/Production)
heroku logs --tail --app codamakutano

# Run locally to reproduce
cd coda && python manage.py runserver
# Test at http://localhost:8000

# Check browser console
# F12 → Console tab → Look for errors
```

**Step 6: Fix & Document**
1. Fix the bug
2. **Add regression test** to `test_regressions.py`
3. Update `IMPLEMENTATION.md` (Change History)
4. Update `TESTING.md` (add test case)
5. Update `KNOWN_ISSUES.md` (if it was listed)

---

## 💡 COMMON PATTERNS & SOLUTIONS

### Pattern 1: Template Error - Field Missing
**Error:** `AttributeError: 'Model' object has no attribute 'field_name'`

**Solution:**
1. Check model has the field
2. Check migration was run
3. Add null check in template: `{% if object.field_name %}`
4. **Create regression test!**

### Pattern 2: API 404 Error
**Error:** API endpoint returns 404

**Check:**
1. URL pattern in `finance/urls.py`
2. View function exists
3. URL name matches reverse lookup
4. Test URL: `curl http://localhost:8000/finance/api/endpoint/`

### Pattern 3: JavaScript Not Working
**Error:** Cascading dropdowns, auto-fill not working

**Check:**
1. jQuery loaded: Check base template
2. Field IDs correct: `id_category`, `id_subcategory`
3. Browser console for errors (F12)
4. API endpoint works: Test in browser
5. Event binding: `$('#id_category').on('change')`

### Pattern 4: Aggregation Wrong
**Error:** Dashboard totals incorrect

**Check:**
1. Using F() expressions: `Sum(F('a') * F('b'))`
2. NOT using: `Sum('a') * Sum('b')`
3. Test with small dataset first
4. **Add regression test!**

---

## 📋 CODE REVIEW CHECKLIST

### Before Committing:

**Code Quality:**
- [ ] Follows existing patterns in codebase
- [ ] Has docstrings on functions/classes
- [ ] No hardcoded values (use settings)
- [ ] Error handling in place
- [ ] Uses Django ORM efficiently

**Testing:**
- [ ] Regression test added (if bug fix)
- [ ] Unit test added (if new feature)
- [ ] Tests pass: `./tests/run_tests.sh`
- [ ] Manual testing done

**Documentation:**
- [ ] IMPLEMENTATION.md updated (Change History)
- [ ] TESTING.md updated (test scenarios)
- [ ] README.md updated (if status changed)
- [ ] REQUIREMENTS.md updated (if completed)

**Database:**
- [ ] Migration created (if model changed)
- [ ] Migration tested locally
- [ ] Migration reversible
- [ ] No data loss

---

## 🎯 FEATURE-SPECIFIC GUIDANCE

### Budget System

**Key Files:**
- Models: `coda/finance/models/budget.py`
- Views: `coda/finance/views/budget/`
- Templates: `coda/finance/templates/finance/budgets/`

**Critical Pattern:**
```python
# Dashboard aggregation (MUST use this pattern)
total = Sum(F('unit_price') * F('quantity') * Coalesce(F('cases'), 1))
```

**Common Tasks:**
- Approval workflow changes → Update `views/budget/approvals.py`
- Dashboard changes → Update `views_unified_budget.py`
- New budget fields → Update model, create migration, update forms

**Watch Out For:**
- Dashboard aggregation bug (use F() expressions!)
- Approval permission logic (currently: is_staff)
- Missing approval fields (approved_by, approved_at, etc.)

---

### Transaction System

**Key Files:**
- Models: `coda/finance/models/core.py`
- Views: `coda/finance/views_smart_transaction.py`
- Services: `coda/finance/services/ai_prediction_service.py`
- Commands: `coda/finance/management/commands/categorize_transactions.py`

**Critical Patterns:**
- AI predictions use `AIPredictionCache` for performance
- Categorization rules in `categorize_transactions.py`
- Cascading dropdowns via AJAX APIs

**Common Tasks:**
- Add categorization rule → Update `CATEGORIZATION_RULES` dict
- Improve AI → Update `ai_prediction_service.py`
- Add API endpoint → Update `views_api_*.py`

**Watch Out For:**
- Data quality (aim for 99%+ categorized)
- Case sensitivity in categorization rules
- API response format (must be valid JSON)

---

### Loan System

**Key Files:**
- Models: `coda/finance/models/loan.py`
- Services: `coda/finance/services/loan_service.py`
- Views: `coda/finance/views.py` (loan views)

**Critical Patterns:**
- Eligibility based on user type (Staff/KCC/External)
- Guarantor requirements (3+ months for staff)
- Schema aligned with production (`term_months` not min/max)

**Common Tasks:**
- Eligibility changes → Update `services/loan_service.py`
- New loan product → Add via admin, update REQUIREMENTS.md
- Guarantor logic → Update `utils.py` guarantor functions

**Watch Out For:**
- Schema alignment (dev must match production)
- Template path: `finance/admin/loan_analytics.html` (not `finance/loan_analytics.html`)
- EligibilityService vs LoanEligibilityService (naming consistency)

---

### Payment System

**Key Files:**
- Models: `coda/finance/models/payment.py`
- Views: `coda/finance/_deprecated/legacy_views/payment_views.py` (currently disabled)

**Current Status:**
- ⚠️ DISABLED (missing `_deprecated` module)
- URLs commented out in `finance/urls.py`

**To Re-Enable:**
1. Deploy `_deprecated` module OR
2. Refactor views to new structure
3. Uncomment URLs in `finance/urls.py`
4. Test thoroughly in UAT

**Watch Out For:**
- Payment system is disabled - don't try to use it
- M-Pesa/Stripe need credentials configured
- Recommended architecture in IMPLEMENTATION.md is future state

---

## 🧪 TESTING STRATEGY

### Test Pyramid:
- **80%** Unit Tests (models, services, utilities)
- **15%** Integration Tests (views, APIs, workflows)
- **5%** E2E Tests (critical user journeys)

### Regression Tests (CRITICAL)

**Location:** `coda/finance/tests/test_regressions.py`

**Current Tests:**
1. Budget approval fields exist
2. Loan product has `term_months` field
3. Staff can approve budgets
4. Dashboard aggregation correct

**ALWAYS add regression test when fixing a bug!**

### Running Tests:
```bash
# All regression tests (before deployment)
./tests/run_tests.sh --regression

# Specific test
cd coda && python manage.py test finance.tests.test_regressions.RegressionTests.test_budget_request_has_approval_fields

# With coverage
cd coda && coverage run manage.py test finance
cd coda && coverage report
```

---

## 📝 DOCUMENTATION UPDATE PROTOCOL

### When to Update Which Doc:

**New Requirement?**
→ `REQUIREMENTS.md` (add to Phase X section)

**Code Change?**
→ `IMPLEMENTATION.md` (Change History table)

**Bug Fix?**
→ `IMPLEMENTATION.md` (Change History) + `TESTING.md` (regression test)

**Status Change?**
→ `README.md` (Current Status section)

**Historical Context?**
→ `README.md` (History section)

**Business Rule Change?**
→ `REQUIREMENTS.md` (Business Rules section)

**New Test?**
→ `TESTING.md` (test scenarios + results log)

---

## 🚨 CRITICAL RULE: NO .MD FILES IN PROJECT ROOT OR DOCS ROOT

### ❌ NEVER Create Files In:
- `/` (project root) - Only `README.md` allowed
- `/docs/` (docs root) - Only `README.md` allowed

### ✅ ALWAYS Create Progress/Summary Files In:
**`docs/_temp_summaries/`** - Temporary working folder

**Why?**
- Keeps root clean
- User can review summaries
- Then move information to appropriate feature docs
- Delete temp files after integration

### Examples:

**DON'T:** ❌
```bash
# Creating files in wrong locations
/INTEGRATION_PROGRESS.md          # ROOT - Wrong!
/docs/SESSION_SUMMARY.md           # DOCS ROOT - Wrong!
/DEPLOYMENT_STRATEGY.md            # ROOT - Wrong!
```

**DO:** ✅
```bash
# Create in temp folder
/docs/_temp_summaries/INTEGRATION_PROGRESS.md          # Correct!
/docs/_temp_summaries/SESSION_SUMMARY.md               # Correct!
/docs/_temp_summaries/DEPLOYMENT_STRATEGY.md           # Correct!

# Then user reviews and you move info to:
docs/apps/finance/Budget/IMPLEMENTATION.md             # Permanent
docs/apps/finance/Budget/REQUIREMENTS.md               # Permanent
docs/05_DEPLOYMENT/OCT13_SESSION.md                    # Permanent
```

### Workflow:

**Step 1: Create Summary (During Work)**
```bash
# You're working on budget feature
# Create progress summary
→ docs/_temp_summaries/BUDGET_WORK_PROGRESS.md
```

**Step 2: User Reviews**
```
User reads your summary in _temp_summaries/
User says: "Good, integrate this into Budget/IMPLEMENTATION.md"
```

**Step 3: Integrate & Delete**
```bash
# You extract key info and add to:
→ docs/apps/finance/Budget/IMPLEMENTATION.md (Change History)
→ docs/apps/finance/Budget/REQUIREMENTS.md (if new requirement)

# Then delete temp file
rm docs/_temp_summaries/BUDGET_WORK_PROGRESS.md
```

### File Naming in _temp_summaries/:
```
✅ BUDGET_WORK_PROGRESS.md        (feature-specific)
✅ SESSION_OCT13_SUMMARY.md        (session summary)
✅ INTEGRATION_STATUS.md           (progress update)
✅ DEPLOYMENT_PLAN.md              (planning)
```

**All temp files get reviewed and integrated, then deleted!**

---

## 🚀 DEPLOYMENT CHECKLIST

### Pre-Deployment (MANDATORY):
- [ ] All regression tests pass
- [ ] Documentation updated (all 4 feature docs if applicable)
- [ ] No linter errors
- [ ] Migrations created and tested
- [ ] Change committed to git
- [ ] User aware of deployment (if major change)

### UAT Deployment (Allowed):
```bash
# Push to GitHub first (backup)
git push uat 25.10_UAT_DEPLOYMENT_FIX_CM

# Deploy to Heroku UAT
git push heroku 25.10_UAT_DEPLOYMENT_FIX_CM:main --force

# Monitor logs
heroku logs --tail --app codamakutano

# Verify URLs
./tests/test_uat_urls.sh
```

### Production Deployment (REQUIRES USER PERMISSION):
⚠️ **ASK USER FIRST: "Ready to deploy to production?"**

**NEVER deploy to production without explicit permission!**

If approved:
```bash
# Deploy
git push production 25.10_UAT_DEPLOYMENT_FIX_CM:main --force

# Monitor closely
heroku logs --tail --app codatrainingapp

# Be ready to rollback if issues
```

---

## 📊 MONITORING & MAINTENANCE

### Daily Checks:
```bash
# Data quality
cd coda && python manage.py analyze_transaction_data

# Check for uncategorized
cd coda && python manage.py analyze_uncategorized
```

### Weekly Checks:
```bash
# Budget projections
cd coda && python manage.py generate_budget_projections --save

# Verify dashboard accuracy
cd coda && python manage.py verify_dashboard_fix
```

### After Deployment:
```bash
# Monitor logs for 1 hour
heroku logs --tail --app codamakutano

# Check error rates
heroku logs --app codamakutano | grep ERROR

# Verify critical paths
curl https://codamakutano.herokuapp.com/dashboard/
curl https://codamakutano.herokuapp.com/finance/budget/coda/approvals/
```

---

## 🆘 WHEN THINGS GO WRONG

### Deployment Failed:

**Check:**
1. Heroku logs: `heroku logs --tail --app codamakutano --num 100`
2. Look for error in logs (usually at the end)
3. Common errors:
   - `ModuleNotFoundError` → Import issue
   - `ProgrammingError` → Database schema mismatch
   - `AttributeError` → Missing model field
   - `TemplateDoesNotExist` → Wrong template path

**Fix:**
1. Fix the error locally
2. Test locally: `python manage.py runserver`
3. Commit fix
4. Redeploy

### UAT is Down:

**Check:**
```bash
# Get detailed logs
heroku logs --tail --app codamakutano --num 200 > uat_error.log

# Check dyno status
heroku ps --app codamakutano

# Restart if needed
heroku restart --app codamakutano
```

### Database Issues:

**Check:**
```bash
# Show migrations
heroku run "cd coda && python manage.py showmigrations" --app codamakutano

# Run pending migrations
heroku run "cd coda && python manage.py migrate" --app codamakutano

# Check database connection
heroku pg:info --app codamakutano
```

---

## 💡 TIPS FOR EFFECTIVE AI ASSISTANCE

### Provide Context:
```
I need help with [TASK].

Context:
- Feature: Budget System
- Files involved: views/budget/approvals.py
- Error: [PASTE ERROR MESSAGE]
- Browser console: [PASTE CONSOLE LOG]
- What I tried: [WHAT YOU TRIED]

Please help debug and fix.
```

### Reference Specific Docs:
```
Read: docs/apps/finance/Budget/IMPLEMENTATION.md (Section: Approval Workflow)

Then help me: [TASK]
```

### Mention Recent Related Work:
```
We recently fixed:
- Dashboard aggregation bug (Oct 1)
- Approval fields missing (Oct 13)

This might be related because: [REASON]
```

---

## 🎯 DECISION FRAMEWORK

### When Uncertain, Ask:

**Before Adding a Feature:**
- Is this in REQUIREMENTS.md already? (Phase X)
- Does this fit current phase?
- Is there existing code that does similar?

**Before Changing Database:**
- Is migration reversible?
- Will this break existing data?
- Does dev schema match production?

**Before Deploying:**
- Have all tests passed?
- Is documentation updated?
- Is user aware (if major change)?

**Before Deleting Code:**
- Is this code still used?
- Are there any references?
- Is there a test covering this?

---

## 📞 GETTING HELP

### Check These First:
1. `docs/apps/finance/[Feature]/IMPLEMENTATION.md` - Technical details
2. `docs/PROJECT_HISTORY_TIMELINE.md` - Similar issues in past
3. `docs/05_DEPLOYMENT/KNOWN_ISSUES.md` - Current issues
4. `docs/COMPREHENSIVE_TESTING_STRATEGY.md` - Testing approach

### Still Stuck?
- Search archived docs index: `docs/ARCHIVED_DOCS_INDEX.md`
- Check Heroku logs: `heroku logs --tail --app codamakutano`
- Review recent commits: `git log --oneline -20`

---

## ⚡ QUICK REFERENCE

### Important URLs:
- **UAT:** https://codamakutano.herokuapp.com
- **Production:** https://codatrainingapp.herokuapp.com
- **Budget Dashboard:** `/finance/budget-dashboard/coda/`
- **Approvals:** `/finance/budget/coda/approvals/`
- **Smart Entry:** `/finance/transaction/smart-entry/`

### Important Commands:
```bash
# Run tests
./tests/run_tests.sh --regression

# Deploy UAT
git push heroku 25.10_UAT_DEPLOYMENT_FIX_CM:main --force

# Check logs
heroku logs --tail --app codamakutano

# Run migration
heroku run "cd coda && python manage.py migrate" --app codamakutano
```

### Important Files:
- `docs/README.md` - Start here
- `docs/PROJECT_HISTORY_TIMELINE.md` - Complete history
- `docs/apps/finance/[Feature]/` - Feature docs (4 each)
- `tests/run_tests.sh` - Test runner
- `coda/finance/tests/test_regressions.py` - Regression tests

---

## 🎓 LEARNING FROM HISTORY

### Critical Bugs We Fixed:
1. **Dashboard Aggregation** (Oct 1) - Use F() expressions
2. **Approval Fields Missing** (Oct 13) - Schema must match templates
3. **Loan Schema Mismatch** (Oct 13) - Dev must match production
4. **Circular Imports** (Oct 11) - Use service layer
5. **Form Widget IDs** (Oct 2) - Explicit IDs for JavaScript
6. **Data Quality** (Sept 30) - Clean data enables features

**Lesson:** Every bug taught us something - check timeline before making similar changes!

---

## ✅ SUCCESS CRITERIA

**Good AI Assistance:**
- ✅ Reads relevant docs first
- ✅ Follows existing patterns
- ✅ Adds tests for changes
- ✅ Updates documentation
- ✅ Considers impact on other features
- ✅ Asks for permission (production deployments)

**Bad AI Assistance:**
- ❌ Makes changes without reading docs
- ❌ Ignores existing patterns
- ❌ Skips tests
- ❌ Doesn't update documentation
- ❌ Deploys without testing
- ❌ Deploys to production without permission

---

## 🎯 FINAL REMINDERS

### ALWAYS:
- ✅ Read feature docs before making changes
- ✅ Run regression tests before deploying
- ✅ Update documentation with every change
- ✅ Add regression test for every bug fix
- ✅ Test in UAT before production
- ✅ **Ask for permission before production deployment**

### NEVER:
- ❌ Deploy to production without user permission
- ❌ Skip regression tests
- ❌ Ignore existing documentation
- ❌ Make breaking changes without discussion
- ❌ Delete code without checking references
- ❌ Commit without testing

---

**This guide ensures consistent, high-quality development!**  
**Follow it for every task, every deployment, every change.**

**Last Updated:** October 13, 2025  
**Maintained by:** CODA Development Team

