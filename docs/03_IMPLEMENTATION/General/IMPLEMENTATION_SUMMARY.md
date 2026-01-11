# DAF v2 Activity Scrutiny + Evidence/Quality Consistency + Task Navigation Fix

## What Changed

### 1. Activity Policy Registry ✅

**File**: `coda/config/activity_definitions.py`

- Added `ActivityPolicy` dataclass with fields:
  - `slug`, `label`, `description_manager`, `description_employee`
  - `requirement_required`, `meeting_required`
  - `evidence_requirements`, `checklist_items`, `gaming_risk`, `notes`
- Created `ACTIVITY_POLICIES` registry with 15+ activity definitions
- Helper functions: `get_activity_policy()`, `get_activity_policy_for_employee()`

**Activities Defined**:
- Internal Training Session, Self Training Session, Client Training Session
- Product Backlog Refinement (PBR)
- Identification Documentation, Stocks & Options Session
- General Project Work (Group A/B differentiation)
- Employee DAF Review, Makutano Supervision
- Budgeting & Forecasting Session, R&D/Innovation Work
- Cashflow Auditing, General Staff Recruitment
- App/Data Entry & Testing Support, Farming Coordination
- Daily Update Session (VERY HIGH gaming risk)

### 2. Evidence/Quality Consistency ✅

**New File**: `coda/management/services/task_quality_gate_service.py`

- `TaskQualityGateService` provides unified gate status
- `get_task_gate_status()` ensures:
  - Evidence Pass and Quality Pass use same queryset
  - Quality cannot be "Pass" without evidence
  - Respects user filtering (non-staff see only their evidence)
- `get_next_steps()` provides actionable hints

**Updated**: `coda/management/legacy_views.py` (daf_v2_view)

- Replaced ad-hoc evidence/quality calculation with gate service
- All evidence/quality checks now use `gate_status` (single source of truth)
- Updated `compliance_chips` to use gate_status values

**Key Fix**: Previously quality could show "Pass" when evidence panel showed "No evidence" because they used different querysets. Now both use the same filtered queryset.

### 3. Task Navigation Fix ✅

**File**: `coda/management/templates/management/daf/tasklist.html`

- Already correctly implemented:
  - Step 1: `/management/tasks/` → Click employee name → `/management/tasks/?employee=<id>`
  - Step 2: Filtered view → Click "Open DAF" button → `/management/daf/v2/?user_id=<id>`
- No direct jump from unfiltered list to DAF v2

### 4. UX Improvements ✅

**File**: `coda/management/templates/management/daf/usertasks/employeetasks_v2.html`

- Added "What this activity means" expandable section (uses activity_policy)
- Added "Next Steps" alert with actionable hints
- Updated evidence display to show count when evidence exists
- Quality status only shown if evidence exists (prevents "Quality ✅" with "No evidence")

### 5. Meeting Model Audit ✅

**New File**: `MEETING_MODEL_REFERENCES.md`

**Findings**:
- **Canonical Model**: `ai_services.models.Meeting`
- **Canonical Table**: `getdata_gotomeetings` (verified in DB)
- **Legacy Model**: `GotoMeetings` (deprecated, kept for migration)
- **Unused**: `gotomeeting_meeting` table (commented out, never used)

**Code Comments Added**:
- `_safe_meeting_query()` documents canonical model/table
- `Meeting` model documents active table name

## Evidence/Quality Logic Explanation

The `TaskQualityGateService` ensures logical consistency:

1. **Single Queryset**: Evidence panel and quality check use the same filtered TaskLinks queryset
2. **Quality Pass Rule**: `quality_score >= 0.8 AND has_evidence` - quality cannot pass without evidence
3. **User Privacy**: Non-staff users see only their own evidence in both panel and quality check
4. **Meeting Requirements**: Checks activity policy for meeting requirement, validates meeting evidence exists
5. **Overall Ready**: All gates must pass (requirement, evidence, meeting, duration, quality)

**Before**: Evidence panel used filtered queryset, quality check used all evidence → mismatch
**After**: Both use same filtered queryset → consistent

## Files Changed (Exact List)

1. `coda/config/activity_definitions.py` - Added ActivityPolicy registry (400+ lines)
2. `coda/management/services/task_quality_gate_service.py` - NEW (250 lines)
3. `coda/management/legacy_views.py` - Updated daf_v2_view (lines ~1722, ~1761-2040)
4. `coda/management/templates/management/daf/usertasks/employeetasks_v2.html` - UX improvements (lines ~415-510)
5. `MEETING_MODEL_REFERENCES.md` - NEW (audit documentation)
6. `DAF_V2_IMPROVEMENTS_SUMMARY.md` - NEW (detailed summary)

## Verification Commands

```bash
# System check
poetry run python coda/manage.py check
# ✅ System check identified no issues (0 silenced).

# Linter check
# ✅ No linter errors found
```

## Manual Verification

### URLs Tested

1. **Task Navigation**:
   - `/management/tasks/` → Click employee → `/management/tasks/?employee=<id>` → Click "Open DAF" → `/management/daf/v2/?user_id=<id>`
   - ✅ Flow works correctly

2. **DAF v2 Evidence/Quality**:
   - `/management/daf/v2/`
   - ✅ Evidence count matches panel
   - ✅ Quality only shows "Pass" when evidence exists
   - ✅ No mismatches

3. **Activity Policy UX**:
   - `/management/daf/v2/` → Expand "What this activity means"
   - ✅ Shows appropriate description
   - ✅ "Next Steps" shows actionable hints

## Expected Behavior

- **Evidence Panel**: Shows user's evidence count (or "No evidence")
- **Quality Status**: Only shows "Pass" if evidence exists AND quality >= 0.8
- **Consistency**: Evidence panel and quality status always match
- **Navigation**: Tasks list → Filtered tasks → DAF v2 (no direct jump)
- **UX**: Activity definitions and next steps help employees understand requirements
