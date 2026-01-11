# AI DELIVERY GUIDE — UNIVERSAL (Legacy Cursor Guide, De-CODA’d and De-Cursor’d)
**Purpose:** A complete, project-agnostic guide for AI-assisted software delivery (works with ChatGPT, Claude, Gemini, Copilot, Cursor, CASA, internal agents, etc.).  
**Last Updated:** January 2026  
**Core Principle:** Deliver correct, verifiable outcomes with minimal risk and minimal process overhead.

---

## 1) Quick Reference: When to UPDATE vs CREATE (Documentation)

| Situation | Don’t | Do |
|---|---|---|
| Bug fix during feature work | Create new ad-hoc docs (“BUG_FIX.md”) | Update existing implementation + testing documentation |
| New requirement discovered mid-stream | Create “UPDATE.md” or “NEW_REQ.md” | Update the primary requirements/spec doc as the new source of truth |
| Need to track progress | Create session notes in the repo root | Add a short entry to the designated changelog/runbook (if the project has one) |
| Code changed | Create “CODE_CHANGES.md” | Update the existing change history or implementation doc |
| Test added/results captured | Create “TEST_RESULTS.md” | Update the testing doc or test plan (or record in CI output) |
| Deployment / release executed | Create “DEPLOYMENT_LOG.md” | Update the release runbook / deployment doc |
| Working on an existing feature | Create new docs every iteration | Edit the existing feature docs |

**Golden Rule:** If the project already has a documentation structure, **do not invent a second one**.

---

## 2) Critical Rule: Avoid Documentation Sprawl

### 2.1 Default: **Never create new docs**
Most AI assistants over-produce documentation. This creates:
- conflicting “truth”
- outdated files
- review fatigue
- slower onboarding

### 2.2 Only create a new doc in these cases
1. **New product area / new module** (project owner explicitly initiates)  
2. **Project-level standard** (cross-cutting; explicitly requested)  
3. **Session report** (explicitly requested; stored in the project’s established location)

If none of the above are true: **UPDATE existing docs**.

---

## 3) The “7-Doc Standard” (Optional but Recommended)

If the project already uses another structure, follow it.  
If the project has no structure, this standard is a proven default:

1. `01_ANALYSIS.md` — Why (problem, goals, success metrics)
2. `02_REQUIREMENTS.md` — What (functional + non-functional requirements)
3. `03_ARCHITECTURE.md` — How (design, data flow, integration points)
4. `04_IMPLEMENTATION.md` — Built (key code locations + change history)
5. `05_TESTING.md` — Verified (test plan + results)
6. `06_MAINTENANCE.md` — Issues/TODO (known issues, operational notes)
7. `07_DEPLOYMENT.md` — Release (deploy steps, configuration, rollback)

**Rule:** If a feature uses a structured doc set, **do not add an 8th doc** unless explicitly requested.

---

## 4) Iterative Development Is Normal — Don’t Record Chaos in Requirements

Requirements evolve. That is expected.

### Bad (chronological clutter)
```md
## Requirements
- Feature A (Sept 20)
- UPDATE: Add Feature B (Oct 15)
- UPDATE 2: Fix bug (Nov 5)

Good (clean final state + change history elsewhere)
## Requirements
- Feature A
- Feature B

Note: Delivery changes are tracked in Change History.


Rule: Requirements docs should read like the final contract, not the conversation transcript.   

## 5) Universal Delivery Workflow (Any Stack)

### Step 1 — Understand the Request
**Output:** Definition of Done (DoD) + constraints.

- What should happen?
- What should not happen?
- What is measurable success?
- What is explicitly out of scope?

---

### Step 2 — Locate the System of Truth
**Output:** A short “truth map.”

- Where is the canonical data?
- Where is the canonical business logic?
- Where do downstream views/metrics read from?

---

### Step 3 — Implement the Minimum Viable Change
**Output:** A small, testable slice.

- Follow existing patterns
- Avoid parallel implementations
- Avoid “cleanup refactors” unless required to ship

---

### Step 4 — Verification (Mandatory)
**Output:** Evidence that the system works.

- Tests (unit/integration)
- Data checks (queries / counts / sample records)
- User flow checks (UI/API path)

---

### Step 5 — Document Updates (Minimal + Accurate)
**Output:** Updated existing docs (not new docs).

- Change history updated
- Testing notes updated
- Known issues updated (if applicable)
- Deployment/runbook updated (if applicable)

---

## 6) Engineering Rules That Prevent 80% of Production Incidents

### 6.1 Never overwrite good data with bad data
If an upstream provider returns inconsistent values:

- Normalize inputs
- Validate “canonical format”
- Only persist when valid
- Preserve existing canonical values if new values are inferior

---

### 6.2 Threshold gating must be explicit
If a feature has “Approved/Complete” status:

- Require `completed >= required`
- Display progress `X/N`
- Never use “truthy” shortcuts like “has any record”

---

### 6.3 Reconciliation must be idempotent
If the system needs derived links or joins:

- Reconciliation should be safely re-runnable
- It must log `created/updated/skipped`
- It must explain “no match” reasons

---

### 6.4 Normalize identifiers across boundaries
When matching keys across systems:

- Normalize type (string/int), casing, whitespace
- Define fallback rules (and log when fallback used)
- Add safety checks when filters drop to zero unexpectedly

---

## 7) Testing Standards (Project-Agnostic)

### When tests are required
Add/adjust tests for:

- Bug fixes (regression tests)
- New features (happy path + failure path)
- Normalization/guardrail logic
- Reconciliation / matching logic
- Any approval/threshold rule changes

---

### Minimum acceptable test set
- Unit tests for pure logic/normalizers
- Integration tests for persistence and side-effects
- One end-to-end/manual path validation for the primary user journey

---

## 8) Environment & Deployment Rules (Project-Agnostic)

### 8.1 Always know what environment you are touching
Before running commands:

- Confirm environment: local / dev / staging / prod
- Confirm credentials & configuration
- Confirm DB target (especially if using production-like clones)

---

### 8.2 Production actions require explicit permission (recommended)
For high-risk environments:

- Require explicit approval before production deploys or data migrations
- Define rollback plan before executing

---

### 8.3 Verify deployments immediately
Do not trust “deploy succeeded” messages. Verify:

- Health endpoint / homepage
- Critical user routes
- Logs for crash loops
- Migrations state (if applicable)

---

## 9) Debugging Workflow (Universal)

### Step 1 — Gather Facts
- Reproduction steps
- Expected vs actual
- Stack trace/logs
- Screenshots (if UI)
- Recent changes

---

### Step 2 — Determine the Failure Class
- Configuration/env
- Schema mismatch
- Missing field / contract drift
- Logic/threshold bug
- Integration payload change
- Permissions/auth
- Caching/staleness

---

### Step 3 — Patch + Regression Test + Verify
A bug is not “fixed” until:

- A regression test exists (where feasible)
- Verification steps confirm resolution

---

## 10) “AI Prompt Contract” (Use This With Any AI)

### When starting any task, provide

#### Context Block (copy/paste template)
```text
Task:
Objective:
Definition of Done (measurable):
Constraints (no refactor / backward compatible / no new docs / etc.):
Scope (in/out):
System of Truth (if known):
Relevant modules/files (if known):
Current behavior:
Desired behavior:
Verification required (tests + data checks + user flow):
Risk tolerance (low/medium/high):

## Output Format Required From the AI

1. **Plan (file-by-file)**
   - Files to touch (or “no code change” if not needed)
   - For each file: what change and why (one paragraph max)

2. **Implementation notes (minimal changes)**
   - What the smallest viable change is
   - What existing patterns/conventions will be followed
   - What will *not* be changed (explicit non-goals)

3. **Verification steps (exact commands/checks)**
   - Unit tests to run (exact commands)
   - Integration checks (exact commands)
   - Data verification (queries/counts/samples)
   - Manual user journey checks (UI/API path)

4. **Risks + rollback**
   - Risk assessment (low/medium/high) with rationale
   - Failure modes to watch for
   - Rollback plan (how to revert code/data/config)

---

## 11) Success Criteria (Universal)

### Good AI assistance
- Reads relevant existing docs/code first
- Follows established patterns
- Makes minimal, targeted changes
- Adds tests and verification
- Updates existing docs (no doc sprawl)
- Avoids risky operations without explicit approval
- Provides clear, reproducible verification steps

### Bad AI assistance
- Invents a new architecture unnecessarily
- Creates many new docs by default
- Skips verification
- Overwrites good data with bad data
- Deploys or migrates without explicit permission (in high-risk contexts)
- Cannot explain how to validate the outcome

---

## 12) Change Log (Optional)

Maintain a small table if the project uses changelogs.

| Date | Change | Reason |
|---|---|---|
| Jan 2026 | Universalized guide (tool-agnostic) | Apply across any AI + any project |
