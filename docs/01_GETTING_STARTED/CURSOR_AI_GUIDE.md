# CURSOR AI GUIDE FOR CODA DEVELOPMENT
**Purpose:** Complete guide for AI-assisted development on CODA  
**Last Updated:** December 2025 (Updated branch structure to 25.12_CODA_*, strict no-new-docs policy)

---

## ⚡ **QUICK REFERENCE: When to UPDATE vs CREATE**

| Situation | ❌ DON'T | ✅ DO |
|-----------|----------|-------|
| Bug fix during feature work | Create "BUG_FIX.md" | Update `04_IMPLEMENTATION.md` Change History |
| New requirement discovered | Create "UPDATE.md" | Add to `02_REQUIREMENTS.md` Phase X |
| Need to track session progress | Create "SESSION_SUMMARY.md" in root | Create in `docs/_temp_summaries/` (if absolutely needed) |
| Code changed | Create "CODE_CHANGES.md" | Update `04_IMPLEMENTATION.md` |
| Test added | Create "TEST_RESULTS.md" | Update `05_TESTING.md` |
| Deployment done | Create "DEPLOYMENT_LOG.md" | Update `07_DEPLOYMENT.md` |
| Working on existing feature | Create new .md files | Edit the 7 existing docs |

**Golden Rule:** If feature has 7 docs, NEVER create an 8th! Update the existing ones.

---

## 🚨 **CRITICAL: DO NOT CREATE NEW DOCUMENTS!** 🚨

### ❌ **NEVER CREATE NEW .MD FILES (STRICTEST RULE)**

**This is the #1 rule violation by AI assistants!**

**ONLY 3 legitimate cases for new .md files:**
1. ✅ New feature/app (needs 7 docs) - User initiates
2. ✅ Project-level doc (cross-cutting) - User explicitly requests  
3. ✅ Session summary - User explicitly requests + goes in `docs/05_DEPLOYMENT/[DATE]_SESSION.md`

**For ALL other changes: UPDATE existing docs!**

### ✅ **CORRECT Approach:**

1. **Working on EXISTING feature?** → **UPDATE** existing docs in `docs/apps/[Feature]/`
   - Don't create "SESSION_SUMMARY.md" ❌
   - Don't create "PROGRESS_UPDATE.md" ❌  
   - **DO:** Update `04_IMPLEMENTATION.md` Change History ✅

2. **Need to track progress?** → **UPDATE existing docs**
   - New requirement? → Edit `02_REQUIREMENTS.md`
   - New analysis? → Edit `01_ANALYSIS.md`
   - New architecture? → Edit `03_ARCHITECTURE.md`
   - Code changed? → Edit `04_IMPLEMENTATION.md` Change History
   - **NO temporary files or summaries**

3. **Back-and-forth is NORMAL!** → Don't create new docs each time
   - Requirements evolve during development
   - **Update existing docs AS IF you knew requirements from start**
   - Don't create "UPDATE_1.md", "UPDATE_2.md" ❌
   - **DO:** Edit the original `02_REQUIREMENTS.md` ✅

### 📋 **The 7-Doc Structure (MANDATORY):**

Every feature has **EXACTLY 7 documents** - no more, no less:
1. `01_ANALYSIS.md` - Why (business case)
2. `02_REQUIREMENTS.md` - What (requirements)
3. `03_ARCHITECTURE.md` - How (design)
4. `04_IMPLEMENTATION.md` - Built (code)
5. `05_TESTING.md` - Verified (tests)
6. `06_MAINTENANCE.md` - Issues/TODO
7. `07_DEPLOYMENT.md` - Deploy procedures

**When things change during development:**
- ✅ **Update the original doc** (e.g., add to `02_REQUIREMENTS.md`)
- ❌ **Don't create** "REQUIREMENTS_UPDATE.md"

### 🎯 **Document Update Rules:**

| What Changed | Update This Doc | Example |
|--------------|----------------|---------|
| New requirement discovered | `02_REQUIREMENTS.md` | Add to Phase X section |
| Code changed | `04_IMPLEMENTATION.md` | Add to Change History table |
| Bug fixed | `04_IMPLEMENTATION.md` + `05_TESTING.md` | Log fix + add regression test |
| New test | `05_TESTING.md` | Add to Test Scenarios |
| Issue found | `06_MAINTENANCE.md` | Add to Known Issues |
| Deploy procedure changed | `07_DEPLOYMENT.md` | Update procedure |

**NEVER create:** SESSION_LOG.md, PROGRESS.md, UPDATE.md, SUMMARY.md ❌

---

## 🔄 **UNDERSTANDING THE DEVELOPMENT PROCESS**

### **Development is Iterative - This is NORMAL:**

```
User: "Add feature X"
AI: Creates initial implementation
User: "Actually, also need Y"
AI: ❌ WRONG: Creates "FEATURE_X_UPDATE.md"
AI: ✅ RIGHT: Updates 02_REQUIREMENTS.md and 04_IMPLEMENTATION.md
```

**Key Insight:** Requirements evolve during development. This is expected!

### **How to Handle Changes:**

#### **Scenario 1: New Requirement Discovered**
```
User: "Oh, also need to filter by Z"
```
❌ **DON'T:** Create "ADDITIONAL_REQUIREMENTS.md"  
✅ **DO:** Add to existing `02_REQUIREMENTS.md`:
```markdown
### Phase X Requirements (Updated Nov 5)
- Original: Filter by X, Y
- Added: Filter by Z (discovered during development)
```

#### **Scenario 2: Bug Found During Testing**
```
User: "The filter isn't working correctly"
```
❌ **DON'T:** Create "BUG_FIX_SUMMARY.md"  
✅ **DO:** Update `04_IMPLEMENTATION.md` Change History:
```markdown
| Date | Change | Reason | Files |
|------|--------|--------|-------|
| Nov 5 | Fixed IV filter format bug | Compared 0.26 to 16 instead of 0.16 | csv_upload.py |
```

#### **Scenario 3: Implementation Details Changed**
```
User: "Let's use approach B instead of A"
```
❌ **DON'T:** Create "IMPLEMENTATION_CHANGE.md"  
✅ **DO:** Update `04_IMPLEMENTATION.md`:
- Remove approach A details
- Add approach B details
- Note change in Change History

### **The Goal: Docs Should Read Like You Knew Everything Upfront**

Someone reading `02_REQUIREMENTS.md` should see a clean list of requirements, **not** a chronological log of how requirements evolved.

**Bad (Chronological):**
```markdown
## Requirements
- Filter by IV (Sept 20)
- UPDATE: Also filter by ROC (Oct 15)
- UPDATE 2: Fix IV format bug (Nov 5)
```

**Good (Clean Final State):**
```markdown
## Requirements
- Filter by IV rank (decimal format: 0.16 = 16%)
- Filter by ROC (return on capital)

Note: IV format bug fixed Nov 5 (see Change History)
```

---

## 🔑 CRITICAL REFERENCE - READ FIRST

### Production Branch & Environments

| Environment | Branch | Heroku App | Remote | Status |
|-------------|--------|------------|--------|--------|
| **Production** | `25.12_CODA_PROD_CM` | codatrainingapp.herokuapp.com | `production` | ✅ Active (Dec 2025) |
| **UAT/Staging** | `25.12_CODA_UAT_CM` | codamakutano.herokuapp.com | `heroku` | ✅ Testing |
| **Development** | `25.12_CODA_DEV_CM` | Local only | N/A | ✅ Local with all docs |

**⚠️ ALWAYS use `25.12_CODA_PROD_CM` branch for production deployments!**

**Quick Deploy Commands:**
```bash
# Production (REQUIRES USER PERMISSION!)
git push production 25.12_CODA_PROD_CM:main --force

# UAT (Allowed for testing)
git push heroku 25.12_CODA_UAT_CM:main --force

# Development (Local only - do NOT deploy)
# Work on: 25.12_CODA_DEV_CM
```

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
- **Local Development:** Read `docs/LOCAL_DEVELOPMENT_WITH_PROD_DATA.md` ⭐ **NEW!**
- **Error Prevention:** Read `docs/WHY_ERRORS_HAPPEN.md` ⭐ **NEW!**

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

### ⚠️ CRITICAL: Local Development Environment Setup

**BEFORE writing ANY code, set up local development with production data clone:**

1. **Read:** `docs/LOCAL_DEVELOPMENT_WITH_PROD_DATA.md`
2. **Install:** PostgreSQL (if not already installed)
3. **Clone:** Production database to local
   ```bash
   bash scripts/clone_prod_database.sh
   ```
4. **Test:** Against cloned database (NOT production!)
   ```bash
   cd coda
   python manage.py runserver --settings=coda_project.coda_settings.local_prod_clone_settings
   ```

**Why Critical?**
- ❌ **Working against production causes 90% of testing errors** (see `WHY_ERRORS_HAPPEN.md`)
- ✅ Clone lets you test safely with real data
- ✅ Catch errors before users do
- ✅ Test migrations without risk

---

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

### Step 6: Test on Cloned Database

**CRITICAL: Test against production clone, NOT production!**

```bash
# Use cloned database for testing
cd coda
python manage.py shell --settings=coda_project.coda_settings.local_prod_clone_settings

# Test your changes with REAL data
python manage.py runserver --settings=coda_project.coda_settings.local_prod_clone_settings

# Visit http://localhost:8000 and test thoroughly
```

### Step 7: Run Tests Before Committing

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

### 0. Local Development Environment (MOST CRITICAL - Oct 27, 2025)
**ALWAYS test against cloned database, NEVER against production!**

```bash
# CORRECT ✅ - Clone production first
bash scripts/clone_prod_database.sh
python manage.py runserver --settings=coda_project.coda_settings.local_prod_clone_settings

# WRONG ❌ - Testing against production
python manage.py runserver  # Uses local_settings.py pointing to PRODUCTION DB
```

**Why Critical:**
- Working against production causes **90% of testing errors**
- Users discover bugs instead of tests
- Production data gets corrupted by test changes
- No safe way to experiment

**Read:** `docs/LOCAL_DEVELOPMENT_WITH_PROD_DATA.md` for complete setup guide

**Read:** `docs/WHY_ERRORS_HAPPEN.md` for root cause analysis

---

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

**0. Test on Cloned Database (MANDATORY):**
```bash
# Clone production (refresh weekly)
bash scripts/clone_prod_database.sh

# Test with real production data
cd coda
python manage.py runserver --settings=coda_project.coda_settings.local_prod_clone_settings

# Visit http://localhost:8000 and test ALL changed functionality
```

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
- [ ] Local server runs with cloned DB
- [ ] Test critical URLs manually with REAL data

**4. Browser Testing:**
- [ ] Open browser console (F12)
- [ ] Check for JavaScript errors
- [ ] Test key user journeys
- [ ] Verify theme switcher works

**5. Migration Testing (if models changed):**
```bash
# Test migrations on cloned database
python manage.py migrate --settings=coda_project.coda_settings.local_prod_clone_settings

# If migration works on clone with real data → safe for production!
```

---

## 🚀 DEPLOYMENT WORKFLOW

### Branch Strategy (IMPORTANT!)

**Current Production Branch:** `25.12_CODA_PROD_CM` (December 2025)

**Branch Structure:**
- **Production Branch**: `25.12_CODA_PROD_CM`
  - Deployed to: `codatrainingapp.herokuapp.com` (Production)
  - Remote: `production`
  - Status: Active production deployment
  
- **UAT Branch**: `25.12_CODA_UAT_CM`
  - Deployed to: `codamakutano.herokuapp.com` (UAT/Staging)
  - Remote: `heroku`
  - Status: Testing environment

- **Development Branch**: `25.12_CODA_DEV_CM`
  - Local development only (NOT deployed to Heroku)
  - Contains all documentation
  - Work here, then merge to UAT for testing

**Deployment Commands by Environment:**
```bash
# Deploy to UAT (codamakutano.herokuapp.com)
git push heroku 25.12_CODA_UAT_CM:main --force

# Deploy to Production (codatrainingapp.herokuapp.com)
git push production 25.12_CODA_PROD_CM:main --force
```

**Important Notes:**
- ✅ Always deploy `25.12_CODA_PROD_CM` branch to production
- ✅ Development happens on `25.12_CODA_DEV_CM` (local only)
- ✅ Test on `25.12_CODA_UAT_CM` before merging to production
- ⚠️ Never deploy untested code directly to production

---

### Deploying to UAT (Allowed)

**Pre-Deployment Checklist:**
1. ✅ Tested on cloned database with real data
2. ✅ All regression tests pass
3. ✅ Migrations tested on clone (if applicable)
4. ✅ Documentation updated
5. ✅ Changes committed to git
6. ✅ Reviewed by user (if major change)

**Deployment Commands:**
```bash
# 1. Ensure on correct branch
git branch  # Should be: 25.12_CODA_UAT_CM

# 2. Push to GitHub (backup)
git push origin 25.12_CODA_UAT_CM

# 3. Deploy to Heroku UAT
git push heroku 25.12_CODA_UAT_CM:main --force

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
1. ✅ Tested on cloned database with real production data
2. ✅ Thoroughly tested in UAT (minimum 24 hours)
3. ✅ User has approved deployment
4. ✅ No known critical bugs
5. ✅ Database backup created
6. ✅ Rollback plan prepared
7. ✅ Deployment time agreed (low-traffic window)

**Production Deployment (Only with Permission):**
```bash
# ASK USER FIRST: "Ready to deploy to production?"

# If YES:
# ALWAYS use the production branch: 25.12_CODA_PROD_CM
git checkout 25.12_CODA_PROD_CM
git push production 25.12_CODA_PROD_CM:main --force

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

### Critical Lesson 0: NEVER Test Against Production Database (Oct 27, 2025)

**Problem Encountered:**
- Local development was pointing to production database
- Every test change affected real users
- Schema mismatches caused production crashes
- No safe way to test migrations
- Users discovered bugs instead of developers

**Root Cause:**
```python
# local_settings.py was pointing to PRODUCTION
DATABASES = {
    'default': {
        'HOST': 'ccqnant9i80rgh.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com',  # PROD!
    }
}
```

**Solution:**
```bash
# Clone production database locally
bash scripts/clone_prod_database.sh

# Use cloned database for all development
python manage.py runserver --settings=coda_project.coda_settings.local_prod_clone_settings
```

**Results:**
- ✅ Test with real production data safely
- ✅ Catch errors before deployment (90% reduction!)
- ✅ Test migrations without risk
- ✅ No user complaints during testing

**Rule:** ✅ **ALWAYS clone production data locally, NEVER test against production!**

**References:**
- Complete guide: `docs/LOCAL_DEVELOPMENT_WITH_PROD_DATA.md`
- Error analysis: `docs/WHY_ERRORS_HAPPEN.md`
- Clone script: `scripts/clone_prod_database.sh`

---

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

### Production Deployment Checklist (Updated Oct 27, 2025)

**Before Deploying:**
- [ ] ✅ Tested on cloned production database locally
- [ ] ✅ All changes tested with real production data
- [ ] ✅ Migrations tested on clone (if applicable)
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

### The 7-Doc Standard (Implemented October 22, 2025)

**Every feature has EXACTLY 7 documents:**

```
Feature/
├── 01_ANALYSIS.md       ← Why (problem, goals, metrics, ROI)
├── 02_REQUIREMENTS.md   ← What (functional requirements, phases)
├── 03_ARCHITECTURE.md   ← How to design (system design, data models)
├── 04_IMPLEMENTATION.md ← How it's built (code locations, functions)
├── 05_TESTING.md        ← How to verify (test scenarios, results)
├── 06_MAINTENANCE.md    ← How to maintain (issues, TODO, troubleshooting)
└── 07_DEPLOYMENT.md     ← How to deploy (procedures, configuration)
```

**Examples:**
- Budget: `docs/apps/finance/Budget/01-07`
- Transaction: `docs/apps/finance/Transaction/01-07`
- Loan: `docs/apps/finance/Loan/01-07`
- Payment: `docs/apps/finance/Payment/01-07`
- GoToMeeting: `docs/apps/ai_services/GoToMeeting/01-07`

---

### When to Update Which Doc:

**Problem Definition or ROI Change?**
→ `01_ANALYSIS.md` (problem statement, business goals, metrics)

**New Requirement?**
→ `02_REQUIREMENTS.md` (add to Phase X section)

**Architecture/Design Change?**
→ `03_ARCHITECTURE.md` (system design, data models)

**Code Change?**
→ `04_IMPLEMENTATION.md` (Change History table, code locations)

**Bug Fix?**
→ `04_IMPLEMENTATION.md` (Change History) + `05_TESTING.md` (regression test) + `06_MAINTENANCE.md` (resolved issues)

**New Test?**
→ `05_TESTING.md` (test scenarios + results log)

**Issue Discovered?**
→ `06_MAINTENANCE.md` (Known Issues section)

**TODO Added?**
→ `06_MAINTENANCE.md` (TODO List section)

**Deployment Procedure Change?**
→ `07_DEPLOYMENT.md` (update procedures)

**Status Change?**
→ Feature `README.md` (not in 7 docs - app-level overview only)

**Historical Context?**
→ `01_ANALYSIS.md` (Lessons Learned) or `04_IMPLEMENTATION.md` (Change History)

**Business Rule Change?**
→ `02_REQUIREMENTS.md` (Business Rules section)

---

## 📚 THE 7-DOC STANDARD FOR FEATURE DOCUMENTATION

**Implemented:** October 22, 2025  
**Status:** ✅ Active standard for all features

### Structure Overview

Every feature (Budget, Transaction, Loan, etc.) has EXACTLY 7 documents:

| Doc | Name | Purpose | When to Update |
|-----|------|---------|----------------|
| **01** | ANALYSIS.md | Why we built it (problem, goals, ROI) | When business case changes |
| **02** | REQUIREMENTS.md | What it must do (functional requirements) | When requirements change |
| **03** | ARCHITECTURE.md | How it's designed (system design, models) | When architecture changes |
| **04** | IMPLEMENTATION.md | How it's built (code locations, functions) | **Every code change** |
| **05** | TESTING.md | How to verify (test scenarios) | When tests added/run |
| **06** | MAINTENANCE.md | How to maintain (issues, TODO) | When issues found/resolved |
| **07** | DEPLOYMENT.md | How to deploy (procedures, config) | When deployment changes |

### Benefits:
- ✅ **Easy Navigation:** Always know where to find information
- ✅ **No Duplication:** Each topic has exactly one home
- ✅ **Prevents Sprawl:** Clear rules prevent doc proliferation
- ✅ **Consistent:** Same structure across all features

### Results (October 2025):
- **Before:** 41 files (Budget: 13, Payment: 15, scattered)
- **After:** 35 organized files (7 per feature)
- **Improvement:** 53% fewer files, 100% better organization

---

### Quick Navigation Examples:

**"Where do I find the Budget approval code?"**
→ `docs/apps/finance/Budget/04_IMPLEMENTATION.md`

**"What are the loan requirements?"**
→ `docs/apps/finance/Loan/02_REQUIREMENTS.md`

**"How do I deploy transactions?"**
→ `docs/apps/finance/Transaction/07_DEPLOYMENT.md`

**"What issues exist with payments?"**
→ `docs/apps/finance/Payment/06_MAINTENANCE.md`

---

## 🚨 CRITICAL RULE: WHEN ARE NEW .MD FILES LEGITIMATE?

### ✅ **ONLY 3 Legitimate Cases for New .md Files:**

#### **Case 1: New Feature/App (User-Initiated)**
Creating a **completely new feature** that doesn't exist in the system.

**Example:**
```bash
User: "Build a new Payroll management feature"

You create:
docs/apps/finance/Payroll/
├── 01_ANALYSIS.md
├── 02_REQUIREMENTS.md
├── 03_ARCHITECTURE.md
├── 04_IMPLEMENTATION.md
├── 05_TESTING.md
├── 06_MAINTENANCE.md
└── 07_DEPLOYMENT.md
```

**Criteria:**
- ✅ User explicitly requests a NEW feature
- ✅ Feature doesn't exist in `docs/apps/`
- ✅ Create ALL 7 docs at once (not one at a time)
- ❌ NOT for enhancements to existing features

---

#### **Case 2: Project-Level Documentation (User-Requested)**
Documentation that applies to **entire project**, not one specific feature.

**Examples of legitimate project-level docs:**
- `docs/PROJECT_HISTORY_TIMELINE.md` (timeline across all features)
- `docs/TESTING_STANDARDS_AND_STRUCTURE.md` (testing strategy)
- `docs/LOCAL_DEVELOPMENT_WITH_PROD_DATA.md` (setup guide)
- `docs/COMPREHENSIVE_TESTING_STRATEGY.md` (testing approach)

**Criteria:**
- ✅ User explicitly requests new project-level documentation
- ✅ Affects multiple features/apps (cross-cutting concern)
- ✅ Cannot fit in any existing feature's 7 docs
- ✅ No existing project-level doc covers this topic
- ❌ NOT for feature-specific information

---

#### **Case 3: Session Documentation (User-Requested, Date-Stamped)**
Historical record of a **major development session** affecting multiple features.

**Example:**
```bash
User: "Create a summary of today's major refactoring session"

You create:
docs/05_DEPLOYMENT/NOV06_SESSION.md
```

**Criteria:**
- ✅ User explicitly requests session summary
- ✅ Major work affecting multiple features
- ✅ Goes in `docs/05_DEPLOYMENT/[DATE]_SESSION.md`
- ✅ Date format: `NOV06_SESSION.md`, `OCT13_SESSION.md`
- ❌ NOT created automatically after each prompt
- ❌ NOT for routine development work

**Existing examples:**
- `docs/05_DEPLOYMENT/OCT13_SESSION.md`

---

### ❌ **NEVER Create These (Common Violations):**

| ❌ Don't Create | ✅ Instead Update | Reason |
|----------------|-------------------|---------|
| `PROGRESS_UPDATE.md` | `04_IMPLEMENTATION.md` (Change History) | Routine changes |
| `SESSION_SUMMARY.md` | Existing feature docs | Routine work |
| `REQUIREMENTS_UPDATE.md` | `02_REQUIREMENTS.md` (just edit) | Requirement evolution |
| `BUG_FIX_LOG.md` | `04_IMPLEMENTATION.md` + `06_MAINTENANCE.md` | Bug fixes |
| `NEW_ARCHITECTURE.md` | `03_ARCHITECTURE.md` (edit existing) | Architecture changes |
| `CODE_CHANGES.md` | `04_IMPLEMENTATION.md` (Change History) | Code changes |
| `TEST_RESULTS.md` | `05_TESTING.md` (Test Results section) | Test outcomes |
| `INTEGRATION_SUMMARY.md` | Relevant feature docs | Integration work |
| `DEPLOYMENT_LOG.md` | `07_DEPLOYMENT.md` | Deployment changes |

---

### 🎯 **Decision Tree: "Should I Create a New .md File?"**

```
┌─────────────────────────────────────┐
│ Do I need to document something?   │
└───────────────┬─────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│ Is this a NEW feature?              │◄── User explicitly requested new feature
│ (Not enhancement to existing)       │
└───────┬─────────────────────────────┘
        │ YES → Create 7 docs for feature ✅
        │
        ▼ NO
┌─────────────────────────────────────┐
│ Is this project-level documentation?│◄── Affects ALL features (cross-cutting)
│ (Affects multiple features)         │    AND user explicitly requested
└───────┬─────────────────────────────┘
        │ YES → Create project doc ✅
        │       (get user approval first)
        │
        ▼ NO
┌─────────────────────────────────────┐
│ Did user request session summary?   │◄── User explicitly asked for summary
│ (Historical record of major work)   │    AND major multi-feature work
└───────┬─────────────────────────────┘
        │ YES → Create in docs/05_DEPLOYMENT/ ✅
        │       with date: [DATE]_SESSION.md
        │
        ▼ NO
┌─────────────────────────────────────┐
│ UPDATE EXISTING DOCUMENTATION       │◄── 99% of cases fall here!
│                                     │
│ • New requirement? → 02_REQUIREMENTS.md
│ • Code change? → 04_IMPLEMENTATION.md
│ • Bug fix? → 04_IMPLEMENTATION.md + 06_MAINTENANCE.md
│ • New test? → 05_TESTING.md
│ • Architecture change? → 03_ARCHITECTURE.md
│                                     │
│ DO NOT CREATE NEW FILE ❌           │
└─────────────────────────────────────┘
```

---

### 📝 **Examples of Correct Behavior:**

**Scenario 1: Bug fix during feature work**
```
User: "The budget filter isn't working"
You: Fix bug
     Update: 04_IMPLEMENTATION.md (Change History)
     Update: 05_TESTING.md (add regression test)
     Update: 06_MAINTENANCE.md (mark issue resolved)
❌ DON'T: Create "BUG_FIX_NOV06.md"
```

**Scenario 2: New requirement discovered**
```
User: "Oh, also need to filter by date range"
You: Update: 02_REQUIREMENTS.md (add to Phase X)
     Update: 04_IMPLEMENTATION.md (implement + Change History)
     Update: 05_TESTING.md (add tests)
❌ DON'T: Create "NEW_REQUIREMENT.md"
```

**Scenario 3: Architecture changes**
```
User: "Let's use Redis for caching instead of database"
You: Update: 03_ARCHITECTURE.md (update caching section)
     Update: 04_IMPLEMENTATION.md (implement + Change History)
     Update: 07_DEPLOYMENT.md (Redis setup instructions)
❌ DON'T: Create "ARCHITECTURE_UPDATE.md"
```

**Scenario 4: Completely new feature (LEGITIMATE)**
```
User: "Build a new Payroll management system"
You: ✅ Create: docs/apps/finance/Payroll/ (all 7 docs)
     This is a NEW feature, not enhancement
```

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
git push uat [your-branch]

# Deploy to Heroku UAT
git push heroku [your-branch]:main --force

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
# ALWAYS use the production branch
git checkout 25.12_CODA_PROD_CM

# Deploy
git push production 25.12_CODA_PROD_CM:main --force

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

### Production Branch & Environments:
- **Production Branch:** `25.12_CODA_PROD_CM` ⚠️ (ALWAYS use this for production!)
- **UAT Branch:** `25.12_CODA_UAT_CM` (matches heroku UAT)
- **Development Branch:** `25.12_CODA_DEV_CM` (local only, all docs)
- **Production URL:** https://codatrainingapp.herokuapp.com
- **UAT URL:** https://codamakutano.herokuapp.com

### Important URLs:
- **UAT:** https://codamakutano.herokuapp.com
- **Production:** https://codatrainingapp.herokuapp.com
- **Budget Dashboard:** `/finance/budget-dashboard/coda/`
- **Approvals:** `/finance/budget/coda/approvals/`
- **Smart Entry:** `/finance/transaction/smart-entry/`

### Important Commands:
```bash
# Clone production database (FIRST STEP!)
bash scripts/clone_prod_database.sh

# Run server with cloned database
cd coda
python manage.py runserver --settings=coda_project.coda_settings.local_prod_clone_settings

# Run tests
./tests/run_tests.sh --regression

# Deploy to UAT (Testing)
git push heroku [your-branch]:main --force

# Deploy to Production (REQUIRES PERMISSION!)
git push production 25.12_CODA_PROD_CM:main --force

# Check logs (UAT)
heroku logs --tail --app codamakutano

# Check logs (Production)
heroku logs --tail --app codatrainingapp

# Run migration (UAT)
heroku run "cd coda && python manage.py migrate" --app codamakutano

# Run migration (Production)
heroku run "cd coda && python manage.py migrate" --app codatrainingapp
```

### Important Files:
- `docs/README.md` - Start here
- `docs/LOCAL_DEVELOPMENT_WITH_PROD_DATA.md` - **Setup guide (CRITICAL!)** ⭐
- `docs/WHY_ERRORS_HAPPEN.md` - **Error prevention (CRITICAL!)** ⭐
- `docs/PROJECT_HISTORY_TIMELINE.md` - Complete history
- `docs/apps/finance/[Feature]/` - Feature docs (7 docs per feature)
- `tests/run_tests.sh` - Test runner
- `coda/finance/tests/test_regressions.py` - Regression tests
- `scripts/clone_prod_database.sh` - Clone production database

---

## 🎓 LEARNING FROM HISTORY

### Critical Bugs We Fixed:
1. **Testing Against Production** (Oct 27) - Clone production locally, NEVER test against production
2. **Dashboard Aggregation** (Oct 1) - Use F() expressions
3. **Approval Fields Missing** (Oct 13) - Schema must match templates
4. **Loan Schema Mismatch** (Oct 13) - Dev must match production
5. **Circular Imports** (Oct 11) - Use service layer
6. **Form Widget IDs** (Oct 2) - Explicit IDs for JavaScript
7. **Data Quality** (Sept 30) - Clean data enables features

**Lesson:** Every bug taught us something - check timeline before making similar changes!

**Biggest Lesson (Oct 27):** Working against production causes 90% of errors. Clone production data locally!

---

## ✅ SUCCESS CRITERIA

**Good AI Assistance:**
- ✅ Reads relevant docs first
- ✅ Follows existing patterns
- ✅ Adds tests for changes
- ✅ **Updates EXISTING documentation** (not creates new)
- ✅ Considers impact on other features
- ✅ Asks for permission (production deployments)
- ✅ **Respects 7-doc structure** (never creates extra docs)

**Bad AI Assistance:**
- ❌ Makes changes without reading docs
- ❌ Ignores existing patterns
- ❌ Skips tests
- ❌ **Creates new .md files after every prompt** ⚠️ **#1 VIOLATION**
- ❌ **Creates SESSION_SUMMARY.md, PROGRESS.md, etc. in root** ⚠️
- ❌ Deploys without testing
- ❌ Deploys to production without permission

---

## 🎯 FINAL REMINDERS

### ALWAYS:
- ✅ **Clone production database before any development** ⭐ **MOST IMPORTANT!**
- ✅ **Test against cloned database, NEVER against production** ⭐
- ✅ **UPDATE existing docs, NEVER create new .md files in root** 🚨 **CRITICAL!**
- ✅ Read feature docs before making changes
- ✅ Run regression tests before deploying
- ✅ Update documentation with every change (edit existing files!)
- ✅ Add regression test for every bug fix
- ✅ Test in UAT before production
- ✅ **Ask for permission before production deployment**
- ✅ **Respect the 7-doc structure** (no extra docs per feature)

### NEVER:
- ❌ **Test against production database** ⭐ **MOST CRITICAL!**
- ❌ **Create .md files in project root** 🚨 **#1 AI VIOLATION!**
- ❌ **Create SESSION_SUMMARY.md, PROGRESS.md, UPDATE.md** 🚨
- ❌ **Create new docs after every prompt** 🚨
- ❌ Deploy to production without user permission
- ❌ Skip regression tests
- ❌ Ignore existing documentation
- ❌ Make breaking changes without discussion
- ❌ Delete code without checking references
- ❌ Commit without testing on cloned database

---

**This guide ensures consistent, high-quality development!**  
**Follow it for every task, every deployment, every change.**

**Last Updated:** December 2025 (Updated branch structure to 25.12_CODA_*, strict no-new-docs policy)  
**Maintained by:** CODA Development Team

---

## 📋 **CHANGE LOG**

| Date | Change | Reason |
|------|--------|--------|
| Dec 2025 | Updated branch structure to 25.12_CODA_* | New month, new branches |
| Nov 6, 2025 | Removed docs/_temp_summaries/ workflow | Stricter policy: update existing docs only |
| Nov 6, 2025 | Added decision tree for new .md files | Clarify 3 legitimate cases |
| Oct 27, 2025 | Added LOCAL_DEVELOPMENT_WITH_PROD_DATA.md | Critical: never test against production |
| Oct 22, 2025 | Implemented 7-doc standard | Prevent documentation sprawl |
| Oct 13, 2025 | Added Known Issues section | Track deployment issues |

---

## 🎯 QUICK START SUMMARY FOR NEW AI ASSISTANTS

**Step 1:** Clone production database
```bash
bash scripts/clone_prod_database.sh
```

**Step 2:** Read these 3 documents
1. `docs/LOCAL_DEVELOPMENT_WITH_PROD_DATA.md` - How to test safely
2. `docs/WHY_ERRORS_HAPPEN.md` - Why this matters
3. `docs/apps/finance/[Feature]/README.md` - Feature overview

**Step 3:** Use cloned database for ALL development
```bash
cd coda
python manage.py runserver --settings=coda_project.coda_settings.local_prod_clone_settings
```

**Step 4:** Follow development workflow in this guide

**Remember:** Testing against production causes 90% of errors! Always use clone! 🎯

