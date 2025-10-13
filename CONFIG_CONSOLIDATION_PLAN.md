# Configuration Files Consolidation Plan
**Date:** October 13, 2025  
**Purpose:** Consolidate duplicate config files into single location

---

## 🎯 PROBLEM

We have duplicate configuration files:

```
/Procfile                  ← ACTIVE (Heroku uses this)
/requirements.txt          ← ACTIVE
/runtime.txt               ← ACTIVE

/coda/Procfile             ← OLD (not used)
/coda/requirements.txt     ← DUPLICATE (same content)
/coda/runtime.txt          ← DUPLICATE (same content)
```

**Issue:** Confusing, risk of updating wrong file

---

## 📊 ANALYSIS

### Heroku Deployment Structure

**How Heroku Works:**
1. Heroku looks for `Procfile`, `requirements.txt`, `runtime.txt` in **repository root**
2. Our Django project is in `/coda/` subdirectory
3. Root `Procfile` tells Heroku: `cd coda && run gunicorn`

**Current (Working) Setup:**
```
/Procfile              → "cd coda && gunicorn ..."
/requirements.txt      → Python dependencies
/runtime.txt           → Python version
```

### Why We Have Duplicates

**History:**
- Initially tried to move everything to `/coda/`
- Heroku couldn't find config files
- Created root-level files as workaround
- Never cleaned up `/coda/` files

---

## ✅ DECISION: KEEP ROOT LEVEL

**Rationale:**
1. **Heroku Standard:** Config files in root is Heroku convention
2. **Currently Working:** Root files are what's deployed
3. **Less Complexity:** No need for custom buildpack config

**Structure:**
```
/                          ← Heroku deployment root
├── Procfile              ← Heroku process definition
├── requirements.txt      ← Python dependencies
├── runtime.txt           ← Python version
├── README.md             ← Project README
├── tests/                ← Test scripts
├── scripts/              ← Helper scripts
│
└── coda/                 ← Django project
    ├── coda_project/     ← Django settings
    ├── finance/          ← Apps
    ├── manage.py
    └── docs/             ← Documentation
```

---

## 🗑️ FILES TO REMOVE

### From `/coda/`:
- ❌ `Procfile` (not used, confusing)
- ❌ `requirements.txt` (duplicate)
- ❌ `runtime.txt` (duplicate)

### Keep in Root:
- ✅ `Procfile` (Heroku uses this)
- ✅ `requirements.txt` (Heroku uses this)
- ✅ `runtime.txt` (Heroku uses this)

---

## 📝 IMPLEMENTATION

### Step 1: Verify Root Files Are Correct

**Check Procfile:**
```bash
cat Procfile
# Should be: web: cd coda && gunicorn coda_project.wsgi:application ...
```

**Check requirements.txt:**
```bash
# Should have all dependencies
grep Django requirements.txt
```

**Check runtime.txt:**
```bash
cat runtime.txt
# Should be: python-3.12.6 (or current version)
```

### Step 2: Remove Duplicate Files from /coda/

```bash
cd /Users/coda/PROJECTS/CODA/DEVELOPMENT/DEV/coda

# Remove duplicates
rm Procfile
rm requirements.txt
rm runtime.txt
```

### Step 3: Document in README

Update root README to clarify:
```markdown
## Configuration Files

**Heroku Deployment Files (Root Level):**
- `Procfile` - Heroku process definition
- `requirements.txt` - Python dependencies
- `runtime.txt` - Python version

These files MUST stay in the root directory for Heroku deployment.
```

### Step 4: Add .gitignore Entry (Optional)

Prevent future duplicates:
```bash
# Add to .gitignore
echo "coda/Procfile" >> .gitignore
echo "coda/requirements.txt" >> .gitignore
echo "coda/runtime.txt" >> .gitignore
```

---

## ⚠️ IMPORTANT NOTES

### DO NOT Move Root Files to /coda/

**Why?**
- Heroku looks for config files in repository root
- Moving them would require custom buildpack configuration
- Current setup is standard and working

### When Updating Dependencies

**Always update ROOT level files:**
```bash
# CORRECT
pip install new-package
pip freeze > requirements.txt  # Root level

# WRONG
pip freeze > coda/requirements.txt  # Don't do this!
```

### Heroku Deployment Flow

```
1. Heroku receives push
2. Looks for Procfile in ROOT
3. Reads requirements.txt from ROOT
4. Installs dependencies
5. Runs command from Procfile: "cd coda && gunicorn ..."
6. Django app runs from /coda/ directory
```

---

## 🔍 VERIFICATION

After cleanup, verify:

```bash
# 1. Check root has config files
ls -la | grep -E "(Procfile|requirements|runtime)"

# 2. Check coda/ doesn't have duplicates
ls -la coda/ | grep -E "(Procfile|requirements|runtime)"
# Should return nothing

# 3. Test deployment
git add -A
git commit -m "Remove duplicate config files from coda/"
git push heroku 25.10_UAT_DEPLOYMENT_FIX_CM:main

# 4. Verify deployment works
heroku logs --tail --app codamakutano
```

---

## 📊 BEFORE vs AFTER

### Before (Confusing):
```
/Procfile                  ← Which one is used?
/requirements.txt          ← Which one is used?
/runtime.txt               ← Which one is used?
/coda/Procfile             ← Which one is used?
/coda/requirements.txt     ← Which one is used?
/coda/runtime.txt          ← Which one is used?
```

### After (Clear):
```
/Procfile                  ← Heroku uses this ✅
/requirements.txt          ← Heroku uses this ✅
/runtime.txt               ← Heroku uses this ✅
/coda/                     ← Django project (no config files)
```

---

## 🎯 BENEFITS

1. **No Confusion:** One set of config files
2. **Standard Practice:** Follows Heroku conventions
3. **Less Maintenance:** Update one file, not two
4. **Clear Ownership:** Root = deployment, coda/ = Django code

---

## 📋 CHECKLIST

- [ ] Verify root Procfile is correct
- [ ] Verify root requirements.txt is complete
- [ ] Verify root runtime.txt is correct
- [ ] Remove coda/Procfile
- [ ] Remove coda/requirements.txt
- [ ] Remove coda/runtime.txt
- [ ] Update README with clarification
- [ ] Commit changes
- [ ] Test deployment
- [ ] Verify app still works

---

**Ready to execute?** This is a safe cleanup with no functional changes.

