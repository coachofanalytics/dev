# Known Issues - Finance App
**Last Updated:** October 13, 2025  
**Branch:** `25.10_UAT_DEPLOYMENT_FIX_CM`  
**UAT Version:** v903

---

## ✅ RESOLVED (October 13-17, 2025)

1. **ModuleNotFoundError: finance._deprecated** - Graceful import handling ✅
2. **BudgetRequest.company field errors** - Removed invalid filters ✅
3. **FinancialAnalyticsService import** - Fixed path ✅
4. **LoanService missing** - Restored from production ✅
5. **LoanProduct schema mismatch** - Aligned with database ✅
6. **BudgetRequest approval fields** - Added approved_by, etc. ✅
7. **ApprovalPolicy.approvers error** - Simplified logic ✅
8. **Payment_History 'description' field error** - Changed to 'notes' field (Oct 17) ✅

---

## 🔄 KNOWN (Non-Critical)

### Low Impact:
1. **Transaction Model Fields**
   - Some code references `user_id` (should be `sender`)
   - Some code references `transaction_type` (field doesn't exist)
   - **Impact:** Minor query issues in edge cases
   - **Workaround:** Use correct field names
   - **Fix:** Update queries when encountered

2. **Template Namespaces**
   - Some templates missing `finance:` namespace in URLs
   - **Impact:** Occasional NoReverseMatch errors
   - **Workaround:** Add namespace when needed
   - **Fix:** Systematic template audit

3. **Payment URLs Disabled**
   - Temporarily disabled due to missing `_deprecated` module
   - **Impact:** Payment features not accessible
   - **Workaround:** Use legacy payment views
   - **Fix:** Deploy `_deprecated` module or refactor payment views

---

## 🎯 PLANNED IMPROVEMENTS

### Phase 2: Intelligent Approval System
- **What:** Data-driven tier-based approvals
- **When:** This week (after transaction analysis)
- **Why:** Maximum automation based on actual CODA spending patterns
- **See:** `/coda/docs/apps/finance/planning/PHASE2_DATA_DRIVEN_APPROVAL_PLAN.md`

---

## 📝 REPORTING NEW ISSUES

**When you find a bug:**

1. **Check if it blocks core workflow**
   - If YES → Report immediately
   - If NO → Add to this doc under "Known"

2. **Include:**
   - URL where error occurs
   - Error message (from browser console or Django logs)
   - Expected vs actual behavior
   - Steps to reproduce

3. **Update this doc** with:
   - Brief description
   - Impact level
   - Workaround if known
   - Planned fix approach

---

## 🔧 CURRENT WORKAROUNDS

### For Development:
- Use `http://127.0.0.1:8000` not `https://` (Django dev server is HTTP only)
- Restart server after service layer changes
- Run migrations after model changes

### For UAT:
- Login required for all finance pages (expected)
- Use staff account to test approvals

---

**Status:** Core functionality working ✅  
**Next Review:** After Phase 2 implementation
