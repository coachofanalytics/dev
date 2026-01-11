# DAF v2 Final Checklist - "Are We Done?"

## ✅ COMPLETED

1. **Import/Views Conflict**: ✅ RESOLVED
   - Legacy views in `legacy_views.py`
   - Views package exports deterministically
   - URL imports stable

2. **Evidence Contradictions**: ✅ RESOLVED
   - `evidence_summary_service.py` is single source of truth
   - Template uses `task.compliance_chips.evidence.status` consistently
   - No more "Evidence ✅" with "No evidence" mismatch

3. **Quality Without Evidence**: ✅ RESOLVED
   - Quality capped when evidence/requirement missing
   - Cannot show "Quality Pass" without evidence

4. **Policy Layer**: ✅ IMPLEMENTED
   - `policy_resolver.py` enforces Group A vs B differences
   - Deterministic reason codes implemented
   - Policy-driven compliance checks

5. **Meeting Source Consistency**: ✅ AUDITED
   - Canonical: `ai_services.models.Meeting` → `ai_services_meeting` table
   - `_safe_meeting_query()` uses `Meeting._meta.db_table` (dynamic)
   - No hardcoded table names in runtime code

6. **DAF v2 UI Actionability**: ✅ IMPLEMENTED
   - Needs Attention shows deterministic reason + CTA
   - Evidence progress shows "Partial (1/2)" format
   - Staff audit details available

7. **Employee Filtering**: ✅ IMPLEMENTED
   - `employee_filter_service.py` shared helper
   - Consistent active-only filtering

8. **Task Navigation**: ✅ IMPLEMENTED
   - Flow: `/tasks/` → filtered → "Open DAF" → DAF v2
   - `employee_identity_service.py` handles ID mapping

9. **AI Shadow Mode**: ✅ IMPLEMENTED
   - Flags default OFF
   - Status panel on `/dashboard/` (staff only)
   - Never crashes

10. **Admin Group Controls**: ✅ IMPLEMENTED
    - Bulk actions in EmployeeCareerStateAdmin

## 🔍 REMAINING ITEMS (Short Checklist)

### HIGH PRIORITY

1. **Verify Meeting Table Name in `_safe_meeting_query()`**
   - **Status**: Code uses `Meeting._meta.db_table` (correct)
   - **Risk**: Low (already fixed)
   - **Action**: Verify no hardcoded `'getdata_gotomeetings'` or `'gotomeeting_meeting'` strings remain
   - **Verification**: `grep -r "getdata_gotomeetings\|gotomeeting_meeting" coda/management/`

2. **Verify Evidence Summary Service Integration**
   - **Status**: Used in `daf_v2_view()` and `compute_task_compliance()`
   - **Risk**: Low (already integrated)
   - **Action**: Confirm all evidence checks use `evidence_summary_service`
   - **Verification**: Check for any remaining `TaskLinks.objects.filter()` in DAF v2 code

3. **Verify Policy Resolver Integration**
   - **Status**: Used in `compute_task_compliance()`
   - **Risk**: Low (already integrated)
   - **Action**: Confirm policy-driven checks work for Group A vs B
   - **Verification**: Test with Group A and Group B employees

### MEDIUM PRIORITY

4. **Template Field Safety**
   - **Status**: `link_name` used (not `topic_name`)
   - **Risk**: Low (already fixed)
   - **Action**: Verify no template references to `topic_name`
   - **Verification**: `grep -r "topic_name" coda/management/templates/`

5. **Navigation Flow End-to-End Test**
   - **Status**: Code looks correct
   - **Risk**: Medium (needs manual verification)
   - **Action**: Test full flow: tasks list → filtered → DAF v2
   - **Verification**: Manual smoke test

### LOW PRIORITY

6. **AI Status Panel Visibility**
   - **Status**: Implemented in unified_dashboard
   - **Risk**: Low
   - **Action**: Verify panel shows for staff users
   - **Verification**: Manual test on `/dashboard/`

7. **Group Assignment UI Decision**
   - **Status**: Admin bulk actions exist
   - **Risk**: Low (nice-to-have)
   - **Action**: Decide if Team Management reuse is needed
   - **Verification**: Product decision

## 🎯 HIGHEST RISK ITEM

**Item**: Verify Meeting Table Name Consistency

**Why**: If any code still hardcodes `'getdata_gotomeetings'` or `'gotomeeting_meeting'`, it will fail when the actual table is `ai_services_meeting`.

**Current State**: `_safe_meeting_query()` uses `Meeting._meta.db_table` (correct), but we need to verify no other code hardcodes table names.

## 📋 NEXT SINGLE PROMPT

**Goal**: Verify and fix any remaining hardcoded meeting table references

**Files to Check**:
- `coda/management/legacy_views.py` - `_safe_meeting_query()` function
- `coda/ai_services/models.py` - Meeting model Meta.db_table
- Any other files that query Meeting model

**Verification Command**:
```bash
grep -rn "getdata_gotomeetings\|gotomeeting_meeting" coda/management/ coda/ai_services/ --include="*.py" | grep -v "#\|comment\|deprecated\|legacy"
```

**Expected Result**: Only comments/documentation should reference old table names. All runtime code should use `Meeting._meta.db_table` or `Meeting.objects`.

