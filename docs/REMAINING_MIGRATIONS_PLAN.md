# 🔍 Remaining Migrations Plan

## Executive Summary

After completing migrations for all 8 major Django apps, we found **5 remaining files** that need migration to `shared_core`. These are infrastructure/utility files rather than full apps.

---

## 📋 Files Requiring Migration

### 1. **coda/api/viewsets.py**
**Imports to migrate:**
- `Department` from `accounts.models` → `shared_core.users`

**Imports to keep as-is (app-specific):**
- `UserService` from `accounts.services`
- `CoreService` from `main.services`

**Impact:** Low - API infrastructure file

---

### 2. **coda/api/serializers.py**
**Imports to migrate:**
- `Department` from `accounts.models` → `shared_core.users`

**Impact:** Low - API infrastructure file

---

### 3. **coda/core/permissions.py**
**Status:** ✅ **No migration needed**
- Only contains a comment referencing `accounts.decorators`
- No actual imports to migrate

---

### 4. **coda/coda_project/task.py**
**Imports to migrate:**
- `CustomerUser` from `accounts.models` → `shared_core.users`

**Imports to keep as-is (app-specific):**
- `TaskGroups` from `accounts.models`
- `download_image` from `main.utils`

**Impact:** Low - Celery task file

---

### 5. **coda/signals/registry.py**
**Imports to migrate:**
- `CustomerUser` from `accounts.models` → `shared_core.users`
- `UserCategory` from `accounts.choices` → `shared_core.users`

**Imports to keep as-is (app-specific):**
- `UserGroups`, `LoginHistory` from `accounts.models`
- `send_email_to_applicant` from `accounts.utils`

**Impact:** Low - Signal registry infrastructure

---

### 6. **coda/tests/**
**Status:** ✅ **No migration needed**
- Test files checked - no imports from `accounts` or `main` requiring migration

---

## 🎯 Migration Strategy Options

### Option 1: Batch Migration on Main Branch (RECOMMENDED)
**Pros:**
- Faster execution
- Fewer merge steps
- All infrastructure files tested together
- Suitable since these are utility files, not full apps

**Cons:**
- Less granular tracking of changes
- All changes in one commit

**Implementation:**
1. Create branch: `25.11_INFRASTRUCTURE_DEV_CM`
2. Migrate all 5 files
3. Test with Django check
4. Merge to `25.12_CODA_DEV_CM`

---

### Option 2: Category-Based Branches
**Pros:**
- More organized
- Better separation of concerns
- Easier to track changes by category

**Cons:**
- More merge steps
- More commits
- May be overkill for infrastructure files

**Implementation:**
1. Create branch: `25.11_API_DEV_CM`
   - Migrate `api/viewsets.py`, `api/serializers.py`
   - Test and merge
2. Create branch: `25.11_INFRASTRUCTURE_DEV_CM`
   - Migrate `signals/registry.py`, `coda_project/task.py`
   - Test and merge

---

## ✅ Recommendation

**Option 1 (Batch Migration)** is recommended because:
1. These are infrastructure/utility files, not full apps
2. They don't need separate testing workflows
3. Faster to complete and verify
4. Consistent with the goal of completing all migrations

---

## 📊 Migration Checklist

Once strategy is approved:
- [ ] Migrate `api/viewsets.py` - Department import
- [ ] Migrate `api/serializers.py` - Department import
- [ ] Migrate `coda_project/task.py` - CustomerUser import
- [ ] Migrate `signals/registry.py` - CustomerUser, UserCategory imports
- [ ] Run Django check to verify no errors
- [ ] Test API endpoints if possible
- [ ] Create branch and commit changes
- [ ] Merge to main DEV branch
- [ ] Final verification scan

---

## 🎉 Completion Status

**Completed Apps:** 8/8
- ✅ Investing
- ✅ Finance
- ✅ Management
- ✅ AI Services
- ✅ Marketing
- ✅ Application
- ✅ Professional Services
- ✅ Unified Dashboard

**Remaining Files:** 5/5 (infrastructure files)

**Total Progress:** ~95% complete (all major apps done, only infrastructure files remaining)
