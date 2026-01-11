# EVIDENCE / CHECKLIST / DAF INTEGRATION ANALYSIS

**Branch:** 25.12_CODA_DEV_CM  
**Date:** 2024-12-26  
**Focus:** Evidence + Checklist + DAF integration (excluding regional pay & future phases)

---

## Section 1 – Current Evidence Flow

### 1.1 Data Model

**Model:** `TaskLinks`  
**File:** `coda/management/models.py` (lines 861-915)  
**Key Fields:**
- `task`: ForeignKey → `Task` (CASCADE delete)
- `added_by`: ForeignKey → `User` (staff/admin/superuser only)
- `link_name`: CharField(255), default="General"
- `description`: TextField (optional)
- `link`: CharField(1000, blank=True, null=True) — URL to evidence (e.g., GoToMeeting recordings)
- `doc`: FileField, upload_to="evidence/docs/" — uploaded document
- `drive_link`: URLField(2000, blank=True, null=True) — Google Drive link for large files
- `linkpassword`: CharField(255), default="No Password Needed"
- `is_active`: BooleanField, default=True
- `is_featured`: BooleanField, default=False
- `created_at`: DateTimeField, auto_now_add=True
- `updated_at`: DateTimeField, auto_now=True

**Relationships:**
- TaskLinks links to `Task` (NOT `TaskHistory`)
- No explicit reverse relation name defined, but Django creates `tasklinks_set` on `Task`
- Used in code via: `task.tasklinks_set.filter(is_active=True)`

### 1.2 Evidence Upload Flow

**User clicks "Upload Evidence" on DAF template:**
- Template: `coda/management/templates/management/daf/usertasks/employeetasks.html` (line 356)
- Button link: `{{ task.task_url }}`
- `Task.task_url` property (`coda/management/models.py`, lines 690-702):
  - Returns URL via `reverse("management:new_evidence", args=[task.id])`
  - Special cases for "one on one sessions" and "job support" redirect to other URLs

**View:** `newevidence(request, taskid)`  
**File:** `coda/management/views.py` (lines 1762-1833)  
**URL Pattern:** `path('newevidence/<int:taskid>', views.newevidence, name='new_evidence')`

**Form:** `EvidenceForm`  
**File:** `coda/management/forms.py` (lines 196-241)  
**Model:** `TaskLinks`  
**Fields:** task, added_by, link_name, linkpassword, description, doc, link, is_active, is_featured, requirement

**Processing Flow:**
1. User submits `EvidenceForm` via POST
2. View validates form (ensures link OR file provided)
3. Validates link accessibility (HEAD request with timeout)
4. Checks for duplicate links (with exceptions for shared activities)
5. If file uploaded: saves to temp file
6. Spawns background thread: `process_evidence_submission()` (line 1820)
7. Background thread:
   - Uploads file to Google Drive (if applicable)
   - Creates `TaskLinks` record via `TaskLinks.objects.create()` (lines 1848-1858)
   - Updates task points (increments `task.point` if requirement linked or general increment logic)
8. Redirects to: `redirect("management:user_evidence", username=request.user.username)`

**Evidence Display View:** `userevidence(request, user=None, *args, **kwargs)`  
**File:** `coda/management/views.py` (lines 1880-1893)  
**Template:** `coda/management/templates/management/daf/userevidence.html`  
**Query:** Filters `TaskLinks` by `added_by__username` and `created_at__range=[two_months_ago, now]`

### 1.3 Evidence Storage & Access

**Storage:**
- Files: `MEDIA_ROOT/evidence/docs/` (via FileField upload_to)
- Google Drive: Large files stored via Drive API, `drive_link` saved in `TaskLinks.drive_link`
- URLs: External links (GoToMeeting, docs, etc.) stored in `TaskLinks.link`

**Access Pattern:**
- Employees view evidence via `/management/userevidence/?username=<username>`
- DAF template does NOT currently display evidence inline with tasks
- Evidence is accessed separately via "Upload Evidence" button → redirects to form → redirects to evidence list

**Current Gap:** No direct display of evidence status/links in the main DAF task table

---

## Section 2 – Current Checklist/Quality Integration

### 2.1 ChecklistEvaluationService Status

**File:** Does NOT exist in codebase  
**Expected Location:** `coda/management/services/checklist_evaluation_service.py`

**References Found:**
- `coda/management/services/daf_summary_service.py` (lines 629-642): Has a placeholder `calculate_quality_score()` function that:
  - Attempts to import `ChecklistEvaluationService` (fails silently)
  - Falls back to simple heuristic: `0.5 if has_evidence else 0.2`
- Master Doc (Section 2.2.5, P4): Describes `ChecklistEvaluationService` as "Design stage; implementation is Phase P4"
- Master Doc (Section 1913-1960): States "Phase P4: ChecklistEvaluationService & Real Quality Metrics (Complete)" but the service file is missing

**Status:** ⚠️ **Partially implemented / Missing file** — Referenced but not found in codebase

### 2.2 ACTIVITY_CHECKLIST_CONFIG Status

**Expected Location:** `coda/config/activity_checklists.py`  
**Status:** ❌ **File does not exist**

**Master Doc Reference:** Section 2.2.5 describes structure:
```python
ACTIVITY_CHECKLIST_CONFIG = {
    "BI_SESSION": {
        "impact": "high",
        "required_evidence": ["attendance", "recording_or_notes", "summary"],
        "promotion_weight": 3.0,
    },
    ...
}
```

### 2.3 ActivityDefinition Model (Checklist Storage)

**Model:** `ActivityDefinition`  
**File:** `coda/management/models.py` (lines 422-498)  
**Relationship:** OneToOneField → `ActivityType` (via `activity_type` FK)

**Key Fields for Checklists:**
- `quality_criteria`: JSONField, stores `{'checklist': [...]}`
- `evidence_requirements`: JSONField, stores list of required evidence types
- `ai_context`: TextField, stores activity description

**Checklist Structure in Catalog:**
- `coda/config/activity_catalog.py`: Some activities have `"checklist"` field in spec
- Example: `PRODUCT_BACKLOG_REFINEMENT`, `CLIENT_TRAINING_SESSION`, `INTERNAL_TRAINING_SESSION`, `SELF_TRAINING_SESSION`
- Checklist format: `[{"code": "REQ_CLARIFICATION", "label": "...", "requires_evidence": True}, ...]`

**Sync Command:** `sync_activity_types.py` (lines 215-256):
- Creates/updates `ActivityDefinition` records
- Stores checklist in `quality_criteria['checklist']`
- Stores description in `ai_context`

**Current Usage:**
- Checklist data is stored in `ActivityDefinition.quality_criteria['checklist']`
- Checklist is displayed in DAF template (`employeetasks.html`, lines 322-331) for tasks with `activity_checklist`
- BUT: No evaluation logic exists to check if checklist items are actually completed

### 2.4 How Evidence is Currently Read

**In DAFSummaryService (`daf_summary_service.py`, lines 651-662):**
```python
has_evidence = hasattr(task, 'tasklinks') and task.tasklinks.exists()
```

**Problem:** This checks if ANY `TaskLinks` exist, but doesn't:
- Check if evidence matches required items from checklist
- Validate evidence completeness
- Score quality based on evidence coverage

**In Views (`views.py`, payslip view, lines 1268-1293):**
- Accesses `ActivityDefinition` via `task.activity_type.ai_definition`
- Extracts checklist from `quality_criteria['checklist']`
- Adds `activity_checklist` to template context
- BUT: No quality scoring or evidence validation

**In AnomalyDetectionService (`anomaly_detection_service.py`, lines 365-399):**
- Queries `TaskLinks` for evidence coverage statistics
- Computes `evidence_coverage` percentage
- BUT: Doesn't use checklist or ActivityDefinition requirements

### 2.5 Quality Score Consumption

**Where Quality Scores Are Expected:**
1. **DAFSummaryService** (`daf_summary_service.py`, line 649): Calls `calculate_quality_score(task, activity_def)` but falls back to simple heuristic
2. **PerformanceMetricsService**: Should consume `checklist_quality_score` per Master Doc, but current implementation unclear
3. **DAF Activities List**: `activities_data` dict includes `quality_score` field (line 699), but value is from fallback heuristic
4. **Stipend Caps**: Master Doc mentions quality caps stipend (Section 2.6.1), but not implemented
5. **Career Progression**: Master Doc mentions quality gates for promotions, but current implementation unclear

**Current Reality:**
- Quality scores are **computed via simple heuristic** (0.5 if evidence exists, 0.2 otherwise)
- No checklist-based evaluation
- No evidence requirement matching
- No per-checklist-item completion tracking

---

## Section 3 – Gap Analysis vs Master Doc

### 3.1 Target Design (From Master Doc)

**From Section 2.2.5 (ChecklistEvaluationService):**
- Evaluate task-level quality from checklists & evidence
- Use `Task`, `ActivityType`, and `TaskLinks`
- Determine which checklists and evidence are required (via config)
- Score each task (0–1 or 0–100%) for quality
- Provide per-activity-type metrics and aggregated `checklist_quality_score` per month

**From Section 2.6.1 (Stipend Caps):**
- Quality cap: if `q < 0.5`, stipend factor is `min(factor, 0.5)` (max 50% stipend)
- Status: "Quality caps (Round 2) will be wired in during Phase P4 when ChecklistEvaluationService delivers real checklist_quality_score"

**From Section 2.9.2 (DAF UX):**
- Activity list should show:
  - Quality & Promotion Impact
  - Evidence status (✔/✖/!)
  - Quality icon or percentage
  - "What is missing" hints per checklist

**From Section 2.2.5 (Evidence Rules for High-Impact Tasks):**
- BI Session (high-impact): Minimum evidence = attendance, recording_or_notes, summary
- No or partial evidence → quality score capped (e.g., 30–40%)
- Missing evidence → lower task quality, slows promotion, caps stipend

### 3.2 Current Reality vs Target

#### ✅ Already Implemented & Aligned

1. **TaskLinks Model**: ✅ Exists with all required fields (link, doc, drive_link, description)
2. **Evidence Upload UI**: ✅ Form, view, and template exist and work
3. **ActivityDefinition Model**: ✅ Exists with `quality_criteria`, `evidence_requirements`, `ai_context`
4. **Checklist Storage**: ✅ Checklists stored in `ActivityDefinition.quality_criteria['checklist']`
5. **Checklist Display**: ✅ DAF template shows checklist (collapsible) for tasks with `activity_checklist`
6. **DAFSummaryService Structure**: ✅ Has `activities_data` with `quality_score` field
7. **Sync Command**: ✅ `sync_activity_types.py` populates `ActivityDefinition` from catalog

#### ⚠️ Partially Implemented (Needs Wiring)

1. **ChecklistEvaluationService**: ⚠️ Referenced but file missing — needs to be created
   - Expected location: `coda/management/services/checklist_evaluation_service.py`
   - Expected interface: `get_task_quality_score(task)`, `get_month_quality_score(employee, month)`

2. **ACTIVITY_CHECKLIST_CONFIG**: ⚠️ File missing — needs to be created
   - Expected location: `coda/config/activity_checklists.py`
   - Should define impact tiers, required_evidence, promotion_weight per activity slug

3. **Evidence → Checklist Mapping**: ⚠️ No logic to check if uploaded evidence matches checklist items
   - Current: Only checks `task.tasklinks.exists()` (any evidence = true)
   - Needed: Match evidence types (link, doc, drive_link) to `evidence_requirements` from ActivityDefinition

4. **Quality Score Computation**: ⚠️ Fallback heuristic only
   - Current: `0.5 if has_evidence else 0.2`
   - Needed: Score based on checklist completion + evidence requirements

5. **DAF UI Quality Indicators**: ⚠️ Structure exists but values are placeholders
   - Current: `quality_score` field in activities_data, but value is heuristic
   - Needed: Real quality scores, evidence status icons (✔/✖/!), missing items list

6. **PerformanceMetricsService Integration**: ⚠️ Structure exists but quality source unclear
   - Master Doc says it should use real quality from ChecklistEvaluationService
   - Current implementation not verified

#### ❌ Missing (Design Exists, No Implementation Yet)

1. **Evidence Requirement Matching**: ❌ No code to check if `TaskLinks.link`, `TaskLinks.doc`, `TaskLinks.drive_link` match `ActivityDefinition.evidence_requirements`
2. **Checklist Item Completion Tracking**: ❌ No logic to mark checklist items as complete/incomplete based on evidence
3. **Quality Score → Stipend Caps**: ❌ Quality caps for stipend not implemented (Master Doc Section 2.6.1)
4. **Quality Score → Promotion Gates**: ❌ Quality gates for promotions mentioned but not verified in CareerLevelService
5. **Missing Items Feedback**: ❌ No "what's missing" logic to show employees which checklist items or evidence types are missing
6. **Evidence Type Classification**: ❌ No logic to classify `TaskLinks` entries as "recording", "notes", "summary", "photos", etc.
7. **High-Impact Task Evidence Rules**: ❌ No special handling for high-impact activities (BI Session, QA, mentoring) with stricter evidence requirements

---

## Section 4 – Proposed Integration Strategy (No Code Yet)

### 4.1 Reuse Existing Components

**✅ We will reuse:**
1. **TaskLinks Model** — No changes needed to model structure
2. **Evidence Upload UI** — Keep `newevidence()` view and `EvidenceForm` as-is
3. **ActivityDefinition Model** — Use existing `quality_criteria['checklist']` and `evidence_requirements` fields
4. **DAFSummaryService** — Extend existing `_get_activities_data()` method to call real quality evaluation
5. **DAF Templates** — Extend existing template to show quality indicators and missing items

**❌ We will NOT:**
- Create new evidence tables
- Duplicate evidence forms
- Create parallel UI flows

### 4.2 Integration Points

#### Point 1: Create ChecklistEvaluationService

**File:** `coda/management/services/checklist_evaluation_service.py` (NEW)

**Interface:**
```python
class ChecklistEvaluationService:
    def get_task_quality_score(self, task: Task) -> dict:
        """
        Returns:
        {
            "quality_score": 0.78,  # 0.0 to 1.0
            "missing_evidence": ["summary"],
            "missing_checklist_items": ["COMMIT_PUSH"],
            "evidence_coverage": 0.67,  # fraction of required evidence present
            "checklist_completion": 0.83,  # fraction of checklist items complete
        }
        """
    
    def get_month_quality_score(self, employee, year, month) -> dict:
        """
        Aggregated monthly quality score (weighted by activity impact).
        """
```

**How it finds evidence:**
- Query: `TaskLinks.objects.filter(task=task, is_active=True)`
- Map evidence types: Check `TaskLinks.link`, `TaskLinks.doc`, `TaskLinks.drive_link` against `ActivityDefinition.evidence_requirements`
- Match checklist items: Compare evidence against checklist item `requires_evidence` flags

**How it uses ACTIVITY_CHECKLIST_CONFIG:**
- If config exists: Use it as primary source for impact tiers and required_evidence
- Fallback: Use `ActivityDefinition.evidence_requirements` from database
- Merge: Combine config and ActivityDefinition data for scoring

#### Point 2: Create ACTIVITY_CHECKLIST_CONFIG

**File:** `coda/config/activity_checklists.py` (NEW)

**Structure:**
```python
ACTIVITY_CHECKLIST_CONFIG = {
    "BI_SESSION": {
        "impact": "high",
        "required_evidence": ["attendance", "recording_or_notes", "summary"],
        "promotion_weight": 3.0,
    },
    "CLIENT_TRAINING_SESSION": {
        "impact": "high",
        "required_evidence": ["recording_or_notes", "summary", "demo_screenshots"],
        "promotion_weight": 2.5,
    },
    ...
}
```

**Integration:** ChecklistEvaluationService will use this config, with fallback to ActivityDefinition

#### Point 3: Trigger Evaluation Points

**Option A: On Evidence Upload (Immediate)**
- Hook: `process_evidence_submission()` in `views.py` (line 1836)
- After `TaskLinks.objects.create()`, call: `ChecklistEvaluationService().get_task_quality_score(task)`
- Store quality_score (if we add a field) OR just compute on-demand

**Option B: When DAF is Loaded (On-Demand)**
- Hook: `DAFSummaryService._get_activities_data()` (line 542)
- Current: Calls placeholder `calculate_quality_score()` (line 649)
- Change: Replace with real `ChecklistEvaluationService().get_task_quality_score(task)`

**Option C: Daily Background Job**
- Run `ChecklistEvaluationService` for all active tasks
- Cache quality scores (if we add a field to Task/TaskHistory)

**Recommendation:** **Option B (On-Demand)** for initial implementation:
- No model changes needed (compute on-demand)
- No risk of blocking evidence upload flow
- Can cache later if performance becomes an issue

#### Point 4: Extend DAFSummaryService

**File:** `coda/management/services/daf_summary_service.py`

**Change Location:** `_get_activities_data()` method (lines 542-717)

**Current Code (lines 629-642):**
```python
def calculate_quality_score(task, activity_def):
    try:
        from management.services.checklist_evaluation_service import ChecklistEvaluationService
        eval_service = ChecklistEvaluationService()
        quality_result = eval_service.get_task_quality_score(task)
        return quality_result.get('quality_score', 0.0)
    except (ImportError, AttributeError, Exception):
        # Fallback heuristic
        return 0.5 if has_evidence else 0.2
```

**Change to:**
- Import and use real `ChecklistEvaluationService`
- Extract `missing_evidence` and `missing_checklist_items` from result
- Pass to `activities_data` dict (already has fields for these)

**Add to activities_data (lines 691-709):**
- `quality_score`: Real score from ChecklistEvaluationService
- `missing_evidence`: List of missing evidence types
- `missing_checklist_items`: List of incomplete checklist item codes
- `evidence_status`: Simple string ("complete", "partial", "missing")

#### Point 5: Extend DAF Templates

**File:** `coda/management/templates/management/daf/usertasks/employeetasks.html`

**Current:** Shows checklist (lines 322-331) but no quality indicators

**Add:**
1. **Quality Icon/Badge** next to activity name:
   - ✔ if `quality_score >= 0.8`
   - ! if `0.5 <= quality_score < 0.8`
   - ✖ if `quality_score < 0.5`
   - Or show percentage: `{{ task.quality_score|floatformat:0 }}%`

2. **Evidence Status** indicator:
   - Show "Evidence: Complete / Partial / Missing"
   - Color-coded badge

3. **"What's Missing" Hint**:
   - If `missing_evidence` or `missing_checklist_items` exists, show tooltip or expandable section
   - Format: "Missing: recording, summary" or "Incomplete: COMMIT_PUSH, EVIDENCE"

**Minimal Changes:**
- Add quality icon/percentage to task row (same row as activity name)
- Add "Missing items" expandable section below checklist (only if missing items exist)
- Use existing template structure, no new forms or modals

#### Point 6: Optional Model Field Addition

**Decision Point:** Should we add `quality_score` field to `Task` or `TaskHistory`?

**Recommendation:** **NO** — Compute on-demand initially
- Keeps model unchanged
- Always uses latest evidence data
- Can add caching field later if needed for performance

**If we need caching later:**
- Add `quality_score`: DecimalField to `Task` model
- Update via signal or background job when evidence changes
- Use cached value in DAFSummaryService, but allow recomputation

### 4.3 Minimal Changes Summary

**New Files:**
1. `coda/config/activity_checklists.py` — ACTIVITY_CHECKLIST_CONFIG registry
2. `coda/management/services/checklist_evaluation_service.py` — Quality evaluation logic

**Modified Files:**
1. `coda/management/services/daf_summary_service.py` — Replace heuristic with real evaluation
2. `coda/management/templates/management/daf/usertasks/employeetasks.html` — Add quality indicators

**No Changes Needed:**
- TaskLinks model
- Evidence upload views/forms
- ActivityDefinition model (structure already supports checklists)
- Task/TaskHistory models (compute on-demand)

---

## Section 5 – Implementation Roadmap (Evidence Only)

### Step 1: Create ACTIVITY_CHECKLIST_CONFIG Registry

**File:** `coda/config/activity_checklists.py` (NEW)

**Tasks:**
1. Create file with dataclass structures:
   - `ChecklistItemConfig` (code, label, weight)
   - `ActivityChecklistConfig` (activity_slug, impact, required_evidence, promotion_weight)
2. Populate `ACTIVITY_CHECKLIST_CONFIG` dict for key activities:
   - BI Session (high impact)
   - Client Training Session (high impact)
   - Internal Training Session (medium impact)
   - Self-Training Session (medium impact)
   - Product Backlog Refinement (medium impact)
   - Cleaning Round (medium impact)
   - Default fallback (low impact)
3. Add helper functions: `get_checklist_config(activity_slug)`, `get_promotion_weight(activity_slug)`

**Validation:**
- Config matches activity slugs from `activity_catalog.py`
- Required_evidence lists align with evidence types we can detect (link, doc, drive_link, description)

### Step 2: Implement ChecklistEvaluationService

**File:** `coda/management/services/checklist_evaluation_service.py` (NEW)

**Core Methods:**
1. `get_task_quality_score(task: Task) -> dict`:
   - Get `ActivityDefinition` for `task.activity_type`
   - Extract checklist from `quality_criteria['checklist']`
   - Extract `evidence_requirements` from `ActivityDefinition.evidence_requirements`
   - Query `TaskLinks.objects.filter(task=task, is_active=True)`
   - Match evidence to requirements (link → "recording_or_notes", doc → "summary", etc.)
   - Check checklist items (if `requires_evidence=True`, verify evidence exists)
   - Calculate scores: evidence_coverage, checklist_completion, overall quality_score
   - Return dict with scores and missing items

2. `get_month_quality_score(employee, year, month) -> dict`:
   - Query `TaskHistory` for employee/month
   - For each TaskHistory, find corresponding Task (match by activity_name + employee)
   - Call `get_task_quality_score()` for each task
   - Weight scores by activity impact (from ACTIVITY_CHECKLIST_CONFIG)
   - Aggregate into monthly score

**Helper Methods:**
- `_find_related_task(task_history: TaskHistory) -> Task | None`: Match TaskHistory → Task
- `_check_evidence_items(task: Task, required_evidence: list) -> dict`: Check which evidence types are present
- `_calculate_score_from_evidence(evidence_items: dict, required_evidence: list) -> float`: Compute evidence coverage score
- `_calculate_checklist_completion(checklist: list, evidence_items: dict) -> float`: Compute checklist completion score

**Tests:**
- `coda/management/tests/test_checklist_evaluation_service.py` (NEW)
- Test per-task scoring with/without evidence
- Test evidence type matching
- Test checklist item completion
- Test monthly aggregation
- Test fallback when ActivityDefinition missing

### Step 3: Wire ChecklistEvaluationService into DAFSummaryService

**File:** `coda/management/services/daf_summary_service.py`

**Change:** `_get_activities_data()` method, `calculate_quality_score()` function (lines 629-642)

**Before:**
```python
def calculate_quality_score(task, activity_def):
    try:
        from management.services.checklist_evaluation_service import ChecklistEvaluationService
        eval_service = ChecklistEvaluationService()
        quality_result = eval_service.get_task_quality_score(task)
        return quality_result.get('quality_score', 0.0) if quality_result else 0.0
    except (ImportError, AttributeError, Exception):
        # Fallback heuristic
        has_evidence = hasattr(task, 'tasklinks') and task.tasklinks.exists()
        return 0.5 if has_evidence else 0.2
```

**After:**
- Remove try/except fallback (or make it less aggressive)
- Use real `ChecklistEvaluationService.get_task_quality_score(task)`
- Extract `missing_evidence` and `missing_checklist_items` from result
- Update `activities_data` dict to include these fields (lines 691-709)

**Update activities_data structure:**
```python
activity_data = {
    ...
    'quality_score': quality_result['quality_score'],  # Real score
    'has_evidence': quality_result.get('evidence_coverage', 0) > 0,
    'missing_evidence': quality_result.get('missing_evidence', []),
    'missing_checklist_items': quality_result.get('missing_checklist_items', []),
    'evidence_status': 'complete' if quality_result['evidence_coverage'] >= 1.0 else 'partial' if quality_result['evidence_coverage'] > 0 else 'missing',
    ...
}
```

**Tests:**
- Update `test_daf_summary_service.py` to verify quality scores are real (not 0.5/0.2)
- Verify missing_evidence and missing_checklist_items are populated

### Step 4: Extend DAF Templates to Show Quality & Evidence Status

**File:** `coda/management/templates/management/daf/usertasks/employeetasks.html`

**Location:** Task table row (around lines 310-368)

**Add Quality Indicator:**
- Next to activity name (line 317): Add badge/icon showing quality_score
- Format: `{% if task.quality_score >= 0.8 %}✔{% elif task.quality_score >= 0.5 %}!{% else %}✖{% endif %} {{ task.quality_score|floatformat:0 }}%`
- Or simpler: Show percentage only

**Add Evidence Status:**
- Add column or inline indicator showing evidence status
- Format: `Evidence: {{ task.evidence_status|title }}` with color coding

**Add "What's Missing" Section:**
- Below checklist (after line 331), add expandable section:
```django
{% if task.missing_evidence or task.missing_checklist_items %}
  <div class="mt-1 small text-warning">
    <strong>Missing:</strong>
    {% if task.missing_evidence %}
      Evidence: {{ task.missing_evidence|join:", " }}
    {% endif %}
    {% if task.missing_checklist_items %}
      Checklist items: {{ task.missing_checklist_items|join:", " }}
    {% endif %}
  </div>
{% endif %}
```

**Tests:**
- Manual browser test: Load DAF for user with tasks
- Verify quality indicators show correct values
- Verify missing items display when evidence incomplete

### Step 5: Add Tests for Full Path

**New Test File:** `coda/management/tests/test_evidence_quality_integration.py` (NEW)

**Test Scenarios:**
1. **Task → Evidence → Checklist → Quality → DAF UI:**
   - Create Task with ActivityType that has checklist
   - Create TaskLinks with partial evidence (e.g., link but no doc)
   - Call ChecklistEvaluationService.get_task_quality_score()
   - Verify quality_score < 1.0
   - Verify missing_evidence list contains missing types
   - Call DAFSummaryService.get_summary()
   - Verify activities_data includes correct quality_score and missing_evidence

2. **Complete Evidence → Full Quality Score:**
   - Create Task with all required evidence types
   - Verify quality_score >= 0.8

3. **No Evidence → Low Quality Score:**
   - Create Task with no TaskLinks
   - Verify quality_score <= 0.3

4. **High-Impact Activity with Missing Evidence → Capped Score:**
   - Create BI Session task with missing "summary" evidence
   - Verify quality_score is capped appropriately

5. **Checklist Items with requires_evidence=True:**
   - Create Task with checklist item requiring evidence
   - Upload evidence matching that item
   - Verify checklist_completion increases

**Integration Tests:**
- Test full flow: Upload evidence → Quality score updates → DAF shows correct indicators
- Test multiple tasks with varying evidence completeness
- Test monthly aggregation across multiple tasks

### Step 6: Optional Enhancement — Trigger Evaluation on Evidence Upload

**File:** `coda/management/views.py`

**Change:** `process_evidence_submission()` function (line 1836)

**Add after TaskLinks creation (line 1858):**
```python
# Optional: Trigger quality evaluation (can be async/background)
try:
    from management.services.checklist_evaluation_service import ChecklistEvaluationService
    eval_service = ChecklistEvaluationService()
    quality_result = eval_service.get_task_quality_score(task)
    # Log or store quality_result if needed (currently just compute on-demand)
except Exception as e:
    logger.warning(f"Quality evaluation failed for task {task.id}: {e}")
```

**Note:** This step is optional — quality can be computed on-demand when DAF loads. This hook is useful for:
- Pre-computing quality scores (if we add caching field)
- Triggering notifications if quality is low
- Logging quality metrics for analytics

### Step 7: Update Documentation & Master Doc

**Update Master Doc Section 2.2.5:**
- Mark ChecklistEvaluationService as "Implemented" (once Step 2 complete)
- Update status from "Design stage" to "Complete"

**Update Master Doc Section P4:**
- Confirm ChecklistEvaluationService file location and interface
- Update test results

---

## Summary of Safe Integration Points

### Files to Create (2)
1. `coda/config/activity_checklists.py` — Config registry
2. `coda/management/services/checklist_evaluation_service.py` — Evaluation service

### Files to Modify (2)
1. `coda/management/services/daf_summary_service.py` — Wire real evaluation
2. `coda/management/templates/management/daf/usertasks/employeetasks.html` — Add UI indicators

### Files to Reuse (No Changes)
1. `coda/management/models.py` — TaskLinks, ActivityDefinition (structure already supports)
2. `coda/management/views.py` — Evidence upload flow (no changes needed)
3. `coda/management/forms.py` — EvidenceForm (no changes needed)
4. `coda/config/activity_catalog.py` — Checklist data source (already populated)

### Model Changes Required
**NONE** — All evaluation is computed on-demand. Optional: Add `quality_score` caching field to `Task` later if performance requires it.

---

## Key Decisions Made

1. **On-Demand Computation**: Quality scores computed when DAF loads, not stored in database (initially)
2. **Reuse TaskLinks**: No new evidence tables; use existing `TaskLinks` model
3. **Reuse ActivityDefinition**: Use existing `quality_criteria['checklist']` and `evidence_requirements` fields
4. **Config + DB Hybrid**: ACTIVITY_CHECKLIST_CONFIG provides defaults; ActivityDefinition provides per-activity overrides
5. **Minimal UI Changes**: Add quality indicators to existing DAF template, no new forms or modals
6. **Backward Compatible**: All changes are additive; existing evidence upload flow unchanged

---

**End of Analysis Document**

