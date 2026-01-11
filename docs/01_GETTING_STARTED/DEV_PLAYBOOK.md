# Universal AI Delivery Playbook (Project-Agnostic)
**Purpose:** A reusable, repeatable system for delivering software changes with AI assistance (ChatGPT/Cursor/Copilot/CASA) across any project—without refactoring-by-default, without documentation sprawl, and with strong verification discipline.  
**Scope:** Features, bugs, integrations, data pipelines, and AI/ML augmentations.  
**Outputs:** Predictable delivery phases, checklists, and copy/paste session templates.

---

## 1) Core Principle
**Every delivery is a chain:** requirement → design → implementation → verification → release.  
Most failures happen when teams skip chain links (especially verification and data integrity).

---

## 2) The Four Lanes Model (Use on Any Task)
Nearly every project task touches one or more lanes:

1. **Core Feature Lane**
   - Business rules, UX/UI, endpoints, persistence, core services.

2. **External Dependency Lane**
   - Third-party APIs, OAuth, SDKs, webhooks, file formats, upstream data quirks.

3. **AI/Automation Lane**
   - Scoring, inference, matching, NLP, recommendation, classification, LLM features.

4. **Platform Integrity Lane (Always On)**
   - Tests, migrations, performance, logging, security, deploy strategy, documentation hygiene.

**Rule:** Declare which lanes are involved before coding.

---

## 3) Standard Delivery Phases (0–6)
Use these phases to reduce prompt volume and prevent thrash. One phase per session or per “chunk” of work.

### Phase 0 — Intake & Definition of Done (DoD)
**Goal:** Make “done” observable.
- Objective (1–2 sentences)
- Acceptance criteria (measurable; what users see; what DB/API returns)
- Scope boundaries (explicit out-of-scope)
- Constraints (environment, deadlines, compatibility requirements)

**Deliverable:** DoD checklist.

**Stop condition:** No code until DoD is explicit.

---

### Phase 1 — Inventory & System Truth Map
**Goal:** Avoid logic duplication and drift.
- Identify the **single source of truth** for:
  - calculations
  - policies/configuration
  - state transitions (e.g., “complete”, “approved”, “eligible”)
- Identify upstream/downstream dependencies:
  - what data must exist for the feature to work

**Deliverable:** “Truth map” + dependency chain.

---

### Phase 2 — Plan + Risk + Verification Protocol
**Goal:** Know what to change and how to prove it worked.
- File-level plan (what gets edited)
- Risks (top 3) + mitigations
- Verification protocol:
  - which tests to run
  - which logs/counters to check
  - which DB queries or API responses to confirm
  - which UI flows to manually validate
- Rollback plan (especially for data changes)

**Deliverable:** Execution plan + verification checklist.

---

### Phase 3 — Implement in Verifiable Slices
**Goal:** Each slice is testable and reversible.
Recommended slice order:
1. Core logic/services (truth layer)
2. Data guardrails (prevent bad states)
3. Wiring (controllers/views/handlers)
4. UI integration (if applicable)
5. Diagnostics (logs, counters, error categories)
6. Tests (new + regression)

**Rule:** Each slice must have a verification step.

---

### Phase 4 — Data Integrity & Integration Hardening (If External/Data-Heavy)
Use this phase whenever you ingest or depend on messy upstream data.

**Pattern: Normalize → Guard → Cleanup → Verify**
1. **Normalize**
   - Convert many input formats into one canonical internal format.
2. **Guard**
   - Enforce canonical format at write boundaries.
   - Never overwrite good data with worse data.
3. **Cleanup**
   - Provide an idempotent backfill/cleanup path for historical contamination.
4. **Verify**
   - DB/API metrics: bad-state count = 0 (or bounded), canonical count increases as expected.

---

### Phase 5 — Release Readiness
**Goal:** Ensure safe deployment.
- All checks/tests passing
- Manual verification completed
- Documentation updated
- Migration/backfill strategy validated (if applicable)
- Monitoring/alerts considered (at least minimal)

---

### Phase 6 — Post-Release Validation (Optional but Recommended)
**Goal:** Ensure production reality matches expectations.
- Validate key metrics and logs
- Confirm no error spikes
- Confirm user journey success
- Prepare rollback plan activation criteria

---

## 4) Universal Patterns (Reusable Across Projects)

### 4.1 “Single Source of Truth” Pattern
**Problem:** Two places compute the same thing differently.  
**Fix:** Centralize computation in one module/service and have UI/API consume it.

**Verification:** same inputs → same outputs across pages/endpoints.

---

### 4.2 “Threshold & Approval” Pattern (Prevent False Positives)
Any “approved/complete” state must:
- require explicit thresholds
- report progress (X/N)
- avoid “truthy” shortcuts (“any exists = complete”)

**Verification:** partial completion never yields “approved.”

---

### 4.3 “Reconciliation” Pattern (Linking Entities)
Whenever a UI/metric depends on derived links:
- reconciliation must be **idempotent** (no duplicates on rerun)
- must emit **diagnostic reasons** for non-matches
- must be verifiable with counts and samples

**Verification:** rerun produces zero unintended churn.

---

### 4.4 “Identity Mapping” Pattern
Whenever you map “people/things” across systems:
- normalize keys consistently
- include fallback rules carefully (ordered, bounded)
- add safety checks when filters drop everything

**Verification:** no “silent zeroing,” mismatch counts decrease.

---

### 4.5 “UI Stabilization” Pattern
When UI is unstable (flicker, layout thrash, modal chaos):
- revert to a minimal stable implementation
- remove hover transforms/tooltips first
- reintroduce enhancements only after baseline stability

**Verification:** baseline behavior is stable across browsers and data sizes.

---

## 5) Verification Discipline (Non-Negotiable)
### 5.1 Three-Layer Verification
1. **Automated tests** (unit/integration)
2. **Data verification** (queries, counters, samples)
3. **User-flow validation** (manual UI/API flow)

### 5.2 “DB/API First” for Expensive Integrations
Avoid repeated external calls.
- sync once
- verify from internal system state (timestamps, counts)
- only resync after forming a specific hypothesis

---

## 6) Documentation Hygiene (Project-Agnostic)
You can adapt to any doc structure, but keep these rules:

- **Prefer updating existing docs** over creating new ones.
- Documentation must reflect the *final state*, not a messy chronological history.
- Every change should update at least one of:
  - requirements/spec (what)
  - implementation notes (how)
  - testing/verification notes (proof)
  - operational runbook (deploy/backfill/cleanup)

---

## 7) Universal Definition of Done (DoD)
A change is “done” only if:
- acceptance criteria are met
- automated tests pass
- verification protocol results match expected outputs
- data integrity invariants hold (no new bad states)
- documentation updated appropriately
- rollout/rollback approach is clear (if release involved)

---

## 8) Copy/Paste Session Templates

### 8.1 New Session Kickoff Template
- Objective:
- Acceptance Criteria:
- Scope In:
- Scope Out:
- Constraints (env/version/compat):
- Lanes involved (Core / External / AI / Platform):
- Single Source of Truth (what module owns truth):
- Dependency Chain (upstream → downstream):
- Verification Protocol:
  - tests:
  - data checks:
  - manual flow:

---

### 8.2 Integration Hardening Template (Normalize → Guard → Cleanup → Verify)
- Canonical format definition:
- Input formats to support:
- Normalization rules:
- Guard rules (when to write/preserve):
- Cleanup/backfill approach:
- Verification queries/counters:
- Failure modes + handling:

---

### 8.3 Reconciliation Template
- Entities to link:
- Idempotency key:
- Matching signals (ranked):
- Diagnostics categories for no-match:
- Verification plan (counts, samples, UI impact):

---

## 9) Operating Ethos for AI-Assisted Delivery
- Clarify “done” before coding.
- Centralize truth; avoid duplicating logic.
- Make changes in small slices with verification per slice.
- Treat integration data as hostile: normalize, guard, cleanup, verify.
- Make reconciliation idempotent and diagnosable.
- Prefer evidence-based verification over repeated external calls.
- Keep documentation lean, current, and non-duplicative.

---
**End of Playbook**
