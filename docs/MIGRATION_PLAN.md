# 📋 App Migration Plan - shared_core

**Date:** November 23, 2025  
**Branch:** `25.12_CODA_DEV_CM`

---

## 🎯 Process for Each App (One by One)

### Steps:
1. ✅ **Migrate imports** - Update `main.*`/`accounts.*` → `shared_core.*`
2. ✅ **Test it works** - Run system check, verify functionality
3. ✅ **Create DEV branch** - Example: `25.12_FINANCE_DEV`
4. ✅ **Make small change** - Add test comment on DEV branch
5. ✅ **Merge back** - Verify no merge conflicts
6. ✅ **Proceed to next app** - Repeat for remaining apps

---

## 📊 Apps to Migrate

### ✅ 1. Investing (COMPLETE)
- **Status:** ✅ Done
- **Files migrated:** 7 files
- **Test:** ✅ Passed
- **Merge test:** ✅ Passed (no conflicts)

### ⏳ 2. Finance (IN PROGRESS)
- **Status:** Starting
- **Files to migrate:** 39 files
- **Common imports:**
  - `CustomerUser`, `Department` → `shared_core.users`
  - `Company` → `shared_core.models`
  - `path_values`, `countdown_in_month`, `dates_functionality` → `shared_core.utils`
  - `FoodFilter` → `shared_core.filters`
  - `FilteredListViewMixin` → `shared_core.mixins`

### 📋 3. Management (PENDING)
- **Status:** Not started
- **Files:** TBD

### 📋 4. AI Services (PENDING)
- **Status:** Not started
- **Files:** TBD

### 📋 5. Marketing (PENDING)
- **Status:** Not started
- **Files:** TBD

---

## 🔄 Migration Status Tracker

| App | Files | Status | Test | DEV Branch | Merge Test |
|-----|-------|--------|------|------------|------------|
| Investing | 7 | ✅ Complete | ✅ Passed | ✅ Created | ✅ Passed |
| Finance | 39 | ⏳ In Progress | ⏳ Pending | ⏳ Pending | ⏳ Pending |
| Management | ? | 📋 Pending | ⏳ Pending | ⏳ Pending | ⏳ Pending |
| AI Services | ? | 📋 Pending | ⏳ Pending | ⏳ Pending | ⏳ Pending |
| Marketing | ? | 📋 Pending | ⏳ Pending | ⏳ Pending | ⏳ Pending |

---

## ✅ shared_core Updates Made

### Models (`shared_core.models`)
- ✅ TimeStampedModel
- ✅ ContractBase
- ✅ DocumentMixin
- ✅ StatusMixin
- ✅ UserReferenceMixin
- ✅ **Company** (added for Finance)

### Users (`shared_core.users`)
- ✅ CustomerUser
- ✅ **Department** (added for Finance)
- ✅ UserCategory

### Utils (`shared_core.utils`)
- ✅ path_values
- ✅ dates_functionality
- ✅ generate_chatbot_response
- ✅ today_date
- ✅ date_converter
- ✅ **countdown_in_month** (added for Finance)

### Filters (`shared_core.filters`)
- ✅ ReturnsFilter
- ✅ CredentialFilter
- ✅ **FoodFilter** (added for Finance)

### Mixins (`shared_core.mixins`)
- ✅ FilteredListViewMixin

---

**Status:** ⏳ Finance migration in progress


