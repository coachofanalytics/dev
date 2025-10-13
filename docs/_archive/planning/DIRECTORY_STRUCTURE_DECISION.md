# Directory Structure Decision: tests/, scripts/, docs/
**Date:** October 13, 2025  
**Question:** Should these be in root or in coda/?

---

## 🎯 CURRENT SITUATION

You moved:
- `tests/` → `coda/tests/`
- `scripts/` → `coda/scripts/`
- `docs/` → `coda/docs/` (or `coda/udocs/`?)

---

## 📊 ANALYSIS

### Option A: Root Level (Original Plan)
```
/
├── tests/              ← Project-wide test scripts
├── scripts/            ← Helper scripts
├── docs/               ← Project documentation
├── coda/               ← Django project
│   ├── finance/tests/  ← Django unit tests
│   └── manage.py
└── venv/
```

**Pros:**
- ✅ Separation of concerns (project vs Django app)
- ✅ Easy to run tests from root: `./tests/run_tests.sh`
- ✅ Documentation covers whole project, not just Django
- ✅ Scripts can work on any part of project

**Cons:**
- ❌ More directories at root level
- ❌ Need to reference `coda/` in paths

---

### Option B: Inside coda/ (Current)
```
/
├── Procfile
├── requirements.txt
├── coda/
│   ├── tests/          ← Test scripts
│   ├── scripts/        ← Helper scripts
│   ├── docs/           ← Documentation
│   ├── finance/tests/  ← Django unit tests
│   └── manage.py
└── venv/
```

**Pros:**
- ✅ Everything Django-related in one place
- ✅ Cleaner root directory
- ✅ Easier to understand "this is the Django project"

**Cons:**
- ❌ Confusing: `coda/tests/` vs `coda/finance/tests/`
- ❌ Scripts need to navigate up/down directories
- ❌ Documentation path longer

---

## 🎯 RECOMMENDATION: **ROOT LEVEL** (Option A)

### Why Root Level is Better:

#### 1. **Clear Separation of Purpose**
- **Root `tests/`** = Project-wide integration/E2E tests
- **`coda/finance/tests/`** = Django unit tests for finance app
- **Root `scripts/`** = Deployment, database, project-wide helpers
- **Root `docs/`** = Project documentation (covers all aspects)

#### 2. **Easier to Use**
```bash
# Root level (easy)
./tests/run_tests.sh
./scripts/deploy_to_uat.sh
cat docs/README.md

# Inside coda/ (awkward)
cd coda && ./tests/run_tests.sh
cd coda && ./scripts/deploy_to_uat.sh
cat coda/docs/README.md
```

#### 3. **Industry Standard**
Most Django projects with subdirectory structure use:
```
/
├── tests/          ← Project tests
├── docs/           ← Project docs
├── myproject/      ← Django code
└── requirements.txt
```

#### 4. **Logical Hierarchy**
```
PROJECT (root)
├── Documentation (docs/)
├── Testing (tests/)
├── Utilities (scripts/)
└── Application Code (coda/)
```

---

## 📁 RECOMMENDED STRUCTURE

```
/Users/coda/PROJECTS/CODA/DEVELOPMENT/DEV/
│
├── Procfile                    ← Heroku config
├── requirements.txt            ← Python deps
├── runtime.txt                 ← Python version
├── README.md                   ← Project README
│
├── docs/                       ← PROJECT DOCUMENTATION
│   ├── README.md               (Master index)
│   ├── apps/finance/           (Finance docs)
│   ├── 01_GETTING_STARTED/
│   ├── 05_DEPLOYMENT/
│   └── COMPREHENSIVE_TESTING_STRATEGY.md
│
├── tests/                      ← PROJECT-WIDE TESTS
│   ├── README.md
│   ├── run_tests.sh            (Main test runner)
│   ├── test_budget_workflow.py (Integration tests)
│   ├── test_payment_control.py
│   └── test_uat_urls.sh        (E2E URL tests)
│
├── scripts/                    ← HELPER SCRIPTS
│   ├── README.md
│   ├── create_budget_item_library.sql
│   ├── deploy_to_uat.sh        (Future)
│   └── backup_database.sh      (Future)
│
├── coda/                       ← DJANGO PROJECT
│   ├── manage.py
│   ├── coda_project/           (Settings, wsgi)
│   ├── finance/
│   │   ├── models.py
│   │   ├── views.py
│   │   └── tests/              ← Django unit tests (finance app)
│   │       ├── test_models.py
│   │       ├── test_views.py
│   │       └── test_regressions.py
│   ├── accounts/
│   │   └── tests/              ← Django unit tests (accounts app)
│   └── ...
│
├── venv/                       ← Virtual environment
│
└── archive/                    ← Old files
```

---

## 🔄 MIGRATION PLAN

### Move Everything Back to Root:

```bash
cd /Users/coda/PROJECTS/CODA/DEVELOPMENT/DEV

# Move docs
mv coda/docs docs/
# OR if you have coda/udocs:
mv coda/udocs docs/

# Move tests
mv coda/tests tests/

# Move scripts
mv coda/scripts scripts/

# Verify
ls -la | grep -E "(docs|tests|scripts)"
```

### Update Paths in Scripts:

**tests/run_tests.sh:**
```bash
# OLD (if inside coda/)
cd "$(dirname "$0")"  # Already in coda/
python manage.py test

# NEW (root level)
cd "$(dirname "$0")/../coda"  # Go to coda from tests/
python manage.py test
```

---

## 🎯 DECISION MATRIX

| Aspect | Root Level | Inside coda/ | Winner |
|--------|-----------|--------------|--------|
| **Ease of Use** | `./tests/run.sh` | `cd coda && ./tests/run.sh` | ✅ Root |
| **Clarity** | Clear separation | Confusing with app tests | ✅ Root |
| **Industry Standard** | Common pattern | Less common | ✅ Root |
| **Heroku Deploy** | No impact | No impact | 🟰 Tie |
| **Root Clutter** | More dirs | Fewer dirs | ✅ coda/ |
| **Logical Grouping** | Project-level | App-level | ✅ Root |

**Score: Root Level wins 5-1**

---

## ⚠️ SPECIAL CASE: Django Unit Tests

**These MUST stay inside Django apps:**
```
coda/finance/tests/         ← Django discovers these
coda/accounts/tests/        ← Django discovers these
```

**Why?**
- Django's test discovery looks inside apps
- `python manage.py test finance` finds `finance/tests/`
- This is Django convention

---

## 🎯 FINAL RECOMMENDATION

### Move to Root:
- ✅ `docs/` → Root (project documentation)
- ✅ `tests/` → Root (integration/E2E tests)
- ✅ `scripts/` → Root (project utilities)

### Keep in coda/:
- ✅ `coda/finance/tests/` (Django unit tests)
- ✅ `coda/accounts/tests/` (Django unit tests)
- ✅ All Django app code

---

## 📝 IMPLEMENTATION

```bash
# Execute this to move everything back:
cd /Users/coda/PROJECTS/CODA/DEVELOPMENT/DEV

# Check what's in coda/
ls -la coda/ | grep -E "(docs|tests|scripts)"

# Move to root
mv coda/docs docs/ 2>/dev/null || mv coda/udocs docs/
mv coda/tests tests/
mv coda/scripts scripts/

# Update test runner paths
# (I'll do this after you confirm)

# Commit
git add -A
git commit -m "refactor: Move docs, tests, scripts to root level for clarity"
```

---

**What do you want to do?**

1. ✅ **Move back to root** (recommended)
2. ❌ **Keep in coda/** (current)
3. 🤔 **Discuss more**

Let me know and I'll execute the move!

