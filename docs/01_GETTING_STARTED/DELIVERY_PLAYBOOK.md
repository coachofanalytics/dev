# CODA AI Delivery Playbook (Module-Agnostic, Hardened for Integrations & Data Hygiene)
**Purpose:** A reusable, repeatable delivery system for implementing any CODA feature/module with ChatGPT + Cursor/CASA while minimizing prompt volume, preventing regressions, and preserving documentation hygiene.  
**Compatible With:** `cursor_ai_guide.md` (this playbook is the delivery workflow; the guide is the guardrails).  
**Version:** 1.1 (Jan 2026) — updated with integration hardening patterns (canonicalization, cleanup, reconciliation, verification loops).

---

## 0) How This Playbook Works With `cursor_ai_guide.md`

### A) Separation of Concerns
- **`cursor_ai_guide.md` = Guardrails**
  - No-new-docs policy, branch discipline, clone DB discipline, deployment discipline, doc structure rules.
- **This Playbook = Delivery Workflow**
  - How to move from requirement → plan → implement → verify → deploy in a consistent pattern.

### B) The Lanes (Generalized)
Most tasks fall into 1–3 lanes, plus one always-on lane:
1. **Core Feature Lane:** models, services, views, templates, UX, business rules.
2. **Third-Party Lane:** OAuth, APIs, sync/ingestion, provider quirks, normalization, cleanup.
3. **AI Lane:** inference/matching/scoring, caching, determinism, auditability, fallbacks.
4. **Platform Integrity Lane (always):** migrations, tests, performance, logging, docs, release readiness.

---

## 1) Non-Negotiables (Inherited From `cursor_ai_guide.md`)
Always enforce these on every session:
- **No-new-docs by default.** Update existing docs only (unless an explicitly allowed case applies).
- **Never test against production DB.** Use clone DB for verification and realistic data.
- **UAT first; production only with explicit permission.**
- **Single Source of Truth (SSOT) for business calculations/state.** Avoid “parallel logic” across templates/views/services.

---

## 2) Standard Delivery Phases (0–5)
Every module follows the same phases. This is the primary mechanism for reducing prompt volume.

### Phase 0 — Intake & Definition of Done (DoD)
**Minimum inputs required:**
- Objective and acceptance criteria (observable outputs)
- Scope boundaries (explicitly out-of-scope)
- Known failure modes (if bug)
- Environment constraints (branch, DB mode, services)

**Deliverables:**
- A DoD checklist
- Explicit unknowns (what must be validated)

**Stop condition:** No code changes until DoD is explicit.

---

### Phase 1 — Inventory & SSOT Map
**Goal:** Prevent drift by identifying where truth lives.
**Deliverables:**
- SSOT for calculations (service layer preferred)
- SSOT for policy (config/policies)
- SSOT for state (task “done”, evidence, gates, meeting completion, etc.)
- Dependency chain (what must exist before downstream features work)

**Stop condition:** If SSOT is unclear, do not implement.

---

### Phase 2 — Plan, Risks, and Verification Protocol
**Deliverables:**
- File-level change plan
- Top 3 risks and mitigations
- Test plan (unit + integration + manual)
- Verification protocol (DB queries/counters + command outputs)
- Rollback plan (especially for migrations and data cleanup)

**Stop condition:** No implementation until verification protocol exists.

---

### Phase 3 — Implement in Small, Verifiable Slices
**Rule:** Each slice must be testable and revertible.
Typical slice order:
1. Service/utility logic (SSOT)
2. Data guardrails (prevent bad state)
3. Backfill/cleanup path (if historical contamination exists)
4. View/template wiring
5. Diagnostics (logs, counters, skip reasons)
6. Tests (new + regression)

---

### Phase 4 — Integration Hardening Loop (Normalize → Guard → Cleanup → Verify)
This phase is mandatory whenever provider data can be malformed or incomplete.

**Pattern:**
1. **Normalize (Pure Function)**
   - Create/extend a normalizer that canonicalizes provider inputs to a single valid format.
   - Normalizer must be deterministic, test-driven, and safe on garbage input.
2. **Guard (Write Path Protection)**
   - Callers must persist only canonical values.
   - Never overwrite good canonical values with poor provider values.
   - Return `None` rather than writing non-actionable placeholders.
3. **Cleanup (Historical Data Remediation)**
   - Add idempotent cleanup command (supports dry-run and filters).
   - Ensure cleanup is safe, bounded, and reversible where possible.
4. **Verify (Counts + Samples)**
   - Verify via DB counts and sample rows:
     - “Bad format count = 0”
     - “Non-canonical count = 0”
     - “Canonical count matches expectations”
   - Prefer DB verification over repeated API calls.

---

### Phase 5 — Release Readiness
Required gates:
- Django check passes
- Tests pass (targeted + regressions)
- Manual verification completed on clone DB
- Documentation updated (existing docs only)
- Deploy checklist ready (if deploying)

---

## 3) Data Dependency Chain (Critical for DAF, Evidence, Meetings, and Beyond)
Many CODA modules are “chains.” Failures upstream cause downstream “it doesn’t work” symptoms.

### Example Chain (Meetings → DAF/Tasks)
**Provider Sync** → **Meeting records** → **Attendees persisted** → **Attribution** → **TaskLinks created** → **DAF counters** → **Gate/Approval logic** → **UI state**

**Rule:** Always debug and verify in this order. Do not “fix UI” when the chain is broken upstream.

---

## 4) Integration Hardening Playbook (General Form)
Use this whenever provider data is messy, inconsistent, or partially missing.

### 4.1 Canonicalization Standard
- Define exactly one persisted format for each provider-derived field (URL, token, ids).
- Normalizer must:
  - Handle fragments, query strings, missing keys, and edge cases
  - Return canonical format or `None`
  - Never return non-actionable placeholders (e.g., a bare host)

### 4.2 Persistence Rules
- Persist only canonical output.
- Preserve canonical data if new provider payload is not canonical.
- Log skip reasons and counters:
  - `missing_token`
  - `invalid_format`
  - `not_canonical`
  - `preserved_existing_canonical`

### 4.3 Cleanup Command Rules
- Must be idempotent.
- Must support `--dry-run`.
- Must support scoped filtering (service name, date range).
- Must print:
  - `found`
  - `updated`
  - `skipped`
  - `examples` (bounded sample)

### 4.4 Verification Protocol (DB-First)
Always verify with DB metrics:
- counts by category (canonical vs non-canonical vs missing)
- sample outputs (bounded)
- timestamp sanity (max updated_at)
- “bad state = 0” invariant checks

---

## 5) Reconciliation Playbook (Linking Data Across Systems)
Use this pattern any time the UI/metrics depend on derived relationships (e.g., TaskLinks, allocations, matching).

### 5.1 Reconciliation Must Be Idempotent
- Re-running reconciliation should not create duplicates.
- Use stable keys for dedupe (task_id + meeting_id + requirement code, etc.)
- Output:
  - processed meetings
  - eligible tasks
  - created links
  - updated links
  - tasks affected
  - reasons for no-match

### 5.2 Diagnostics Are First-Class
For every “no link created,” log the reason category:
- no employee attribution
- no matching task window
- requirement mismatch
- meeting room mismatch
- evidence already present / duplicate
- missing required fields

### 5.3 Verification of Reconciliation Effect
Verify the chain outcome:
- TaskLinks count increases as expected
- DAF counters move (X/N)
- Gate logic matches threshold rules
- UI reflects the computed state

---

## 6) Gate & Threshold Playbook (Prevent False Approval)
Whenever there is an “Approved/Complete” state:
- approval requires **meeting_completed >= required_meetings** (or equivalent threshold)
- UI must display **X/N** progress
- do not infer completion from “any meeting exists”
- derive counts from the SSOT (typically links/relationships, not raw meetings)

---

## 7) Attendee/Identity Matching Playbook (Avoid Silent Drop to Zero)
Identity mapping issues cause “everything is zero” downstream.

### 7.1 Key Normalization Rules
- Normalize types and formatting consistently (string/int, whitespace, casing).
- When filtering by instance keys:
  - use safe fallback keys in a controlled order (documented)
  - log mismatch counts and samples

### 7.2 Safety Guards
- If filtering removes 100% of attendees:
  - treat as a warning-level incident
  - emit reason summary
  - do not proceed to downstream steps that require attendees (unless reconciliation supports fallback attribution)

### 7.3 Verification
- Verify attendees persisted:
  - total attendees created/updated
  - sample attendee names
  - mismatch warnings drop meaningfully

---

## 8) Prompt-Volume Reduction System (Operational Discipline)

### 8.1 One Prompt Per Phase
Do not mix “planning” and “implementation” and “verification” in one loop.  
Pick the phase and finish it.

### 8.2 DB-First Verification (Stop Repeated API Calls)
Provider calls are expensive and noisy.
- Sync once
- Verify using DB counts and timestamps
- Only re-sync after a specific hypothesis is formed

### 8.3 Minimal Repro for UI Bugs
When UI is unstable:
- strip to minimal HTML + minimal JS
- remove hover transforms/tooltips/modals first
- confirm stability
- reintroduce UX enhancements only after stable baseline

---

## 9) Documentation Protocol (No Sprawl)
To comply with `cursor_ai_guide.md`:

### 9.1 Where Changes Must Be Recorded
- `02_REQUIREMENTS.md`: final-state requirements
- `04_IMPLEMENTATION.md`: change history + SSOT decisions + file pointers
- `05_TESTING.md`: test cases + manual verification steps + DB verification queries
- `06_MAINTENANCE.md`: known issues + mitigations + operational caveats (e.g., “some meetings may lack tokens”)
- `07_DEPLOYMENT.md`: commands/runbooks that must be executed in UAT/Prod (e.g., cleanup commands, reconcile commands)

### 9.2 Verification Notes Policy
- Prefer embedding verification steps into `05_TESTING.md` and `07_DEPLOYMENT.md`.
- Only create a standalone verification doc if user explicitly requests and it is project-level.

---

## 10) Universal Definition of Done (DoD)
A task is “done” only if all are true:
- Acceptance criteria met on clone DB
- Tests pass (targeted + relevant regressions)
- DB verification invariants satisfied (e.g., “bad format = 0”)
- Downstream chain verified (if applicable)
- Docs updated in-place (no sprawl)
- Deploy readiness confirmed (if deploying)

---

## 11) Session Templates (Copy/Paste)

### 11.1 Implementation Session Template
- Objective:
- Acceptance Criteria (observable):
- Scope In / Out:
- Constraints (branch/env/db/services):
- Lanes involved (Core / Third-Party / AI / Platform Integrity):
- SSOT targets:
- Dependency chain (upstream → downstream):
- Verification protocol (DB counts, commands, expected outputs):
- Tests to run:
- Manual checks:

### 11.2 Integration Hardening Template (Normalize → Guard → Cleanup → Verify)
- Canonical format definition:
- Normalizer cases to support:
- Persistence rule (when to write, when to preserve):
- Cleanup command design (dry-run, filters, output counters):
- Verification queries (counts + samples):
- Failure-mode table:

### 11.3 Reconciliation Template
- Link target (what relationship must exist):
- Idempotency key:
- Matching signals (time window, room, attendee, requirement codes):
- Diagnostics categories:
- Verification (TaskLinks count, UI counters, gate status):

---

## 12) Operating Ethos (For Any AI Assistant)
- Prefer deterministic > AI; prefer SSOT services > template logic.
- Protect production: clone DB, UAT first, permission for production.
- Normalize and guard provider data; remediate historical contamination with idempotent cleanup.
- Treat reconciliation as a first-class system (idempotent + diagnosable).
- Validate the full dependency chain, not just the UI symptom.

---
**End of Playbook**
