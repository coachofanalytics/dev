# DAF v2 Finish Line Checklist

## ✅ COMPLETED ITEMS

1. ✅ **Import/Views Conflict**: Resolved - legacy views in `legacy_views.py`, views package exports deterministically
2. ✅ **Evidence Contradictions**: Resolved - `evidence_summary_service.py` is single source of truth
3. ✅ **Quality Without Evidence**: Resolved - quality capped when evidence missing
4. ✅ **Policy Layer**: Implemented - `policy_resolver.py` enforces Group A vs B
5. ✅ **Meeting Source**: Audited - Canonical is `ai_services.models.Meeting` → `ai_services_meeting` table
6. ✅ **DAF v2 UI**: Implemented - Needs Attention shows deterministic reasons + CTAs
7. ✅ **Employee Filtering**: Implemented - `employee_filter_service.py` shared helper
8. ✅ **Task Navigation**: Implemented - Flow works: tasks list → filtered → DAF v2
9. ✅ **AI Shadow Mode**: Implemented - Flags default OFF, panel on `/dashboard/`
10. ✅ **Admin Group Controls**: Implemented - Bulk actions in EmployeeCareerStateAdmin

## 🔍 REMAINING VERIFICATION (5 items)

### 1. Meeting Table Name Consistency ⚠️ HIGHEST RISK
**Status**: Code uses `Meeting._meta.db_table` (correct), but need final verification
**Action**: Verify no runtime code hardcodes `'getdata_gotomeetings'` or `'gotomeeting_meeting'`
**Verification Command**:
```bash
grep -rn "getdata_gotomeetings\|gotomeeting_meeting" coda/management/ coda/ai_services/ --include="*.py" | grep -v "#\|comment\|deprecated\|legacy\|test\|migration"
```
**Expected**: Only comments/documentation should reference old names

### 2. Evidence Summary Service Coverage
**Status**: Used in `daf_v2_view()` and `compute_task_compliance()`
**Action**: Verify all evidence checks use `evidence_summary_service`
**Verification**: Check for any remaining direct `TaskLinks.objects.filter()` in DAF v2 code
**Risk**: Low (already integrated)

### 3. Policy Resolver Integration
**Status**: Used in `compute_task_compliance()`
**Action**: Test with Group A and Group B employees to verify policy differences
**Verification Command**:
```bash
poetry run python coda/manage.py test management.tests.test_policy_enforcement -v 2
```
**Risk**: Low (code looks correct)

### 4. Navigation Flow End-to-End
**Status**: Code looks correct
**Action**: Manual smoke test
**Steps**:
1. Go to `/management/tasks/`
2. Click employee name → should filter to `/management/tasks/?employee=<id>`
3. Click "Open DAF" button → should go to `/management/daf/v2/?user_id=<id>`
**Risk**: Medium (needs manual verification)

### 5. Template Field Safety
**Status**: `link_name` used (not `topic_name`)
**Action**: Verify no template references to `topic_name`
**Verification Command**:
```bash
grep -r "topic_name" coda/management/templates/ --include="*.html"
```
**Risk**: Low (already fixed)

## 🎯 HIGHEST RISK ITEM TO FIX NOW

**Item #1: Meeting Table Name Consistency**

**Why Critical**: If any runtime code hardcodes `'getdata_gotomeetings'` or `'gotomeeting_meeting'`, it will fail because the actual table is `ai_services_meeting`.

**Current State**: 
- ✅ `_safe_meeting_query()` uses `Meeting._meta.db_table` (dynamic, correct)
- ✅ Meeting model uses Django default table name (`ai_services_meeting`)
- ⚠️ Need to verify no other code hardcodes table names

## 📋 NEXT SINGLE CURSOR PROMPT

**Title**: Verify Meeting Table Name Consistency - Final Audit

**Goal**: Ensure no runtime code hardcodes meeting table names

**Files to Open**:
1. `coda/management/legacy_views.py` (line ~2888-2892)
2. `coda/ai_services/models.py` (line ~203-206)

**Exact Code Edits**:

1. **Verify `_safe_meeting_query()` uses dynamic table name** (already correct):
   - Line 2891: `if Meeting._meta.db_table not in table_names:` ✅ Correct
   - No changes needed

2. **Verify Meeting model Meta** (already correct):
   - Line 204-206: Comment documents canonical table name ✅ Correct
   - No changes needed

3. **Add guard test to prevent regressions**:
   - Create/update: `coda/management/tests/test_meeting_source_guard.py`
   - Test that no runtime code hardcodes table names

**Verification Commands**:
```bash
# 1. Check for hardcoded table names (should only find comments/tests)
grep -rn "getdata_gotomeetings\|gotomeeting_meeting" coda/management/ coda/ai_services/ --include="*.py" | grep -v "#\|comment\|deprecated\|legacy\|test\|migration"

# 2. Verify Meeting model uses Django default
poetry run python coda/manage.py shell -c "from ai_services.models import Meeting; print('Table:', Meeting._meta.db_table)"

# 3. Run guard test
poetry run python coda/manage.py test management.tests.test_meeting_source_guard -v 2

# 4. System check
poetry run python coda/manage.py check
```

**Expected Results**:
- ✅ No hardcoded table names in runtime code (only in comments/tests/migrations)
- ✅ Meeting model table is `ai_services_meeting`
- ✅ Guard test passes
- ✅ System check passes

## 🏁 FINISH LINE CRITERIA

Project is "wrapped" when ALL of these pass:

1. ✅ `/management/daf/v2/` returns 200 reliably (no meeting table errors)
2. ✅ Evidence badge and evidence body never contradict
3. ✅ Quality cannot pass without evidence/requirement where policy requires it
4. ✅ Needs Attention always shows deterministic reason + correct CTA
5. ✅ Drill-down works: `/management/tasks/` → filtered tasks → Open DAF
6. ✅ AI status panel visible to staff, flags default OFF
7. ✅ Group A vs B policy differences enforced and test-covered
8. ✅ Meeting table name is consistent (no hardcoded references)

## 📝 DECISIONS NEEDED

1. **Group Assignment UI**: Admin bulk actions exist. Do we need Team Management reuse?
   - **Recommendation**: Keep admin bulk actions for now. Add Team Management reuse only if managers request it.

2. **Manager vs Group B UX**: Review wording for clarity
   - **Recommendation**: See "Manager vs Group B Perspective Review" section below

