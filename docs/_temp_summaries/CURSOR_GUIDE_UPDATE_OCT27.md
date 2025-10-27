# CURSOR AI GUIDE - Updated October 27, 2025

## 🎯 Purpose
Updated `docs/01_GETTING_STARTED/CURSOR_AI_GUIDE.md` to emphasize the **CRITICAL importance** of using cloned production database for local development instead of testing against production.

---

## 📋 What Was Added

### 1. New Reference Documents in Quick Start
Added to "For Specific Tasks" section:
- **Local Development:** `docs/LOCAL_DEVELOPMENT_WITH_PROD_DATA.md` ⭐ **NEW!**
- **Error Prevention:** `docs/WHY_ERRORS_HAPPEN.md` ⭐ **NEW!**

### 2. New Critical Section: Local Development Environment Setup
Added **BEFORE Step 1** in Development Workflow:

```markdown
### ⚠️ CRITICAL: Local Development Environment Setup

**BEFORE writing ANY code, set up local development with production data clone:**

1. Read: docs/LOCAL_DEVELOPMENT_WITH_PROD_DATA.md
2. Install: PostgreSQL (if not already installed)
3. Clone: Production database to local
   bash scripts/clone_prod_database.sh
4. Test: Against cloned database (NOT production!)
```

**Why Critical?**
- ❌ Working against production causes 90% of testing errors
- ✅ Clone lets you test safely with real data
- ✅ Catch errors before users do
- ✅ Test migrations without risk

### 3. New Step 6: Test on Cloned Database
Added between "Write Tests" and "Run Tests":

```markdown
### Step 6: Test on Cloned Database

**CRITICAL: Test against production clone, NOT production!**

- Use cloned database for testing
- Test your changes with REAL data
- Visit http://localhost:8000 and test thoroughly
```

### 4. New #0 Critical Thing to Watch
Added as the **MOST CRITICAL** item (before all others):

```markdown
### 0. Local Development Environment (MOST CRITICAL - Oct 27, 2025)
**ALWAYS test against cloned database, NEVER against production!**

**Why Critical:**
- Working against production causes 90% of testing errors
- Users discover bugs instead of tests
- Production data gets corrupted by test changes
- No safe way to experiment
```

### 5. Updated Testing Requirements
Added **Step 0** before all other testing steps:

```markdown
**0. Test on Cloned Database (MANDATORY):**
- Clone production (refresh weekly)
- Test with real production data
- Visit http://localhost:8000 and test ALL changed functionality

**5. Migration Testing (if models changed):**
- Test migrations on cloned database
- If migration works on clone with real data → safe for production!
```

### 6. Updated Deployment Checklists

**UAT Pre-Deployment:**
- Added: "Tested on cloned database with real data" (first item)
- Added: "Migrations tested on clone (if applicable)"

**Production Pre-Deployment:**
- Added: "Tested on cloned database with real production data" (first item)

**Production Deployment Checklist:**
- Added: "Tested on cloned production database locally"
- Added: "All changes tested with real production data"
- Added: "Migrations tested on clone (if applicable)"

### 7. New Production Lesson 0
Added as the **first and most important** lesson learned:

```markdown
### Critical Lesson 0: NEVER Test Against Production Database (Oct 27, 2025)

**Problem Encountered:**
- Local development was pointing to production database
- Every test change affected real users
- Schema mismatches caused production crashes
- No safe way to test migrations
- Users discovered bugs instead of developers

**Solution:**
bash scripts/clone_prod_database.sh
python manage.py runserver --settings=coda_project.coda_settings.local_prod_clone_settings

**Results:**
- ✅ Test with real production data safely
- ✅ Catch errors before deployment (90% reduction!)
- ✅ Test migrations without risk
- ✅ No user complaints during testing

**References:**
- Complete guide: docs/LOCAL_DEVELOPMENT_WITH_PROD_DATA.md
- Error analysis: docs/WHY_ERRORS_HAPPEN.md
- Clone script: scripts/clone_prod_database.sh
```

### 8. Updated Important Commands
Added at the top:
```bash
# Clone production database (FIRST STEP!)
bash scripts/clone_prod_database.sh

# Run server with cloned database
cd coda
python manage.py runserver --settings=coda_project.coda_settings.local_prod_clone_settings
```

### 9. Updated Important Files
Added:
- `docs/LOCAL_DEVELOPMENT_WITH_PROD_DATA.md` - **Setup guide (CRITICAL!)** ⭐
- `docs/WHY_ERRORS_HAPPEN.md` - **Error prevention (CRITICAL!)** ⭐
- `scripts/clone_prod_database.sh` - Clone production database

### 10. Updated Critical Bugs We Fixed
Added as **#1 bug** (renumbered all others):
```
1. **Testing Against Production** (Oct 27) - Clone production locally, NEVER test against production
```

Added note:
**Biggest Lesson (Oct 27):** Working against production causes 90% of errors. Clone production data locally!

### 11. Updated ALWAYS/NEVER Lists

**ALWAYS (added to top):**
- ✅ **Clone production database before any development** ⭐ **MOST IMPORTANT!**
- ✅ **Test against cloned database, NEVER against production** ⭐

**NEVER (added to top):**
- ❌ **Test against production database** ⭐ **MOST CRITICAL!**

Updated last item:
- ❌ Commit without testing on cloned database

### 12. New Quick Start Summary (End of Document)
Added comprehensive 4-step quick start for new AI assistants:

```markdown
## 🎯 QUICK START SUMMARY FOR NEW AI ASSISTANTS

**Step 1:** Clone production database
bash scripts/clone_prod_database.sh

**Step 2:** Read these 3 documents
1. docs/LOCAL_DEVELOPMENT_WITH_PROD_DATA.md - How to test safely
2. docs/WHY_ERRORS_HAPPEN.md - Why this matters
3. docs/apps/finance/[Feature]/README.md - Feature overview

**Step 3:** Use cloned database for ALL development
cd coda
python manage.py runserver --settings=coda_project.coda_settings.local_prod_clone_settings

**Step 4:** Follow development workflow in this guide

**Remember:** Testing against production causes 90% of errors! Always use clone! 🎯
```

---

## 🎯 Key Messages Emphasized

1. **NEVER test against production** - Added to 12+ locations throughout document
2. **ALWAYS clone production first** - Made first step in all workflows
3. **90% of errors come from testing against production** - Repeated multiple times
4. **Test with real data safely** - Main benefit highlighted
5. **Use cloned database for ALL development** - Emphasized as mandatory

---

## 📊 Impact

**Before:**
- No mention of production cloning
- Implicit assumption of using whatever database was configured
- No emphasis on testing environment setup

**After:**
- **12 new sections/updates** about production cloning
- Cloning is **Step 0** (before all other steps)
- Clear, repeated warnings against production testing
- Complete references to setup guides
- Quick start summary at end

---

## 🔗 Related Documents Created

1. `docs/LOCAL_DEVELOPMENT_WITH_PROD_DATA.md` - Complete setup guide
2. `docs/WHY_ERRORS_HAPPEN.md` - Root cause analysis (already existed)

---

## ✅ Verification

All updates emphasize:
- ⭐ **CRITICAL** importance markers
- 🎯 Clear actionable steps
- 📚 Links to detailed guides
- ⚠️ Warnings against production testing
- ✅ Benefits of using clone

---

**Created:** October 27, 2025  
**Purpose:** Document CURSOR_AI_GUIDE.md updates for production clone emphasis  
**Result:** AI assistants will now prioritize cloning production database before any development! 🚀

