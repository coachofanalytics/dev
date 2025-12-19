# Employee Activity System (Management) – 01_ANALYSIS.md

## 1. Purpose (Why this system exists)

The Management app powers the **Employee Activity System (DAF)** – a data‑driven layer that:
- Correlates **tasks, meetings, and department activities**.
- Automates **evidence collection and validation**.
- Produces **reliable inputs for budgeting, salary compliance (33% rule), and performance management**.

The core vision is to move from ad‑hoc, manual tracking to a **standardized activity platform** that Finance and Management can trust for decisions.

---

## 2. Current System – What We Already Have (December 2025)

### 2.1 Core Models & Data
- **Task / TaskHistory**
  - Task: current month activities with points (`point`), max points (`mxpoint`), and earnings (`mxearning`).
  - TaskHistory: **monthly snapshot** (using `daf_date`) used for salary and budget calculations.
  - Both enforce `point ≤ mxpoint`, `mxpoint > 0`, `mxearning ≥ 0`.
- **TaskCategory / TaskGroups**
  - Categories for activity type (PBR, Data Analysis, Website Development, etc.).
  - Groups for employee leveling (Group A/H/I) that affect earnings (`mxearning`).
- **TaskLinks**
  - Evidence layer (docs, URLs, Drive links, meeting recordings) attached to Task.
- **Department / CustomerUser (Employee)**
  - Department lives in `accounts` (8 departments).
  - Employees are staff users with `department` set.

> **Key gap:** Tasks and TaskHistory **do not store department directly** – they infer it via employee, which complicates historical reporting and budget integration.

### 2.2 Services & Processes
- **TaskResetService**
  - Monthly reset on the 1st of the month (Celery `dump_data` task).
  - Creates TaskHistory records first, then resets Task points to 0, updates group/earnings.
- **TaskStandardizationService**
  - Standardizes activity names and consolidates categories into 8 core groups.
- **IntelligentAssignmentService**
  - AI‑based task assignment using TaskHistory patterns (performance, workload, skills).
- **ComplianceCalculator / EmployeeComplianceService**
  - Implements the **33% compliance rule** for salary inclusion.
- **Evidence services**
  - EvidenceValidationService and EvidenceReminderService for evidence coverage and reminders.
- **Finance integration**
  - Management exposes APIs for **activity totals, evidence validation, compliance and forecasting**.
  - Finance consumes these for budget estimation and validation.

### 2.3 Views / APIs / UI
- Classic Django views for **task CRUD, evidence submission, task reset**, and admin.
- API endpoints for:
  - Activity summary & analytics.
  - Intelligent assignment suggestions.
  - Budget activity totals & evidence validation.
  - Forecasting, trend analysis, compliance KPIs, anomaly detection.

> Today, most heavy users are **admins and finance/management staff**; there is no modern, dedicated **Task Management dashboard** for day‑to‑day operations.

---

## 3. Problems & Pain Points

### 3.1 Structural Gaps
- **No department field on Task / TaskHistory**
  - Department filtering is indirect and historical department changes are not captured.
- **No template model for standard activities**
  - Tasks are created one‑by‑one or via hard‑coded logic in admin (e.g., “6 default tasks” after training).
- **No subcategory / hierarchy**
  - 32% of tasks fall into “Other” category → weak analytics and poor classification.

### 3.2 Process & Logic Issues
- **Task reset automation**
  - Historically lacked robust transaction handling, validation, and admin alerting for failures.
- **Compliance rule inconsistency (33%)**
  - Two competing formulas appeared (task‑count vs point‑based) before centralizing on a calculator.
  - Edge cases (new staff, leave, zero tasks) need explicit policy.
- **Evidence integration**
  - Evidence not consistently required for salary inclusion.
  - Auto‑upload from meetings exists but is fragile and not fully enforced end‑to‑end.

### 3.3 UX / Operational Issues
- No **task management dashboard** (similar to `/team-management/`).
- No **bulk assignment** or bulk operations; most workflows are one‑by‑one.
- Limited **visibility** into upcoming compliance status and reset timing for employees.

---

## 4. Goals & Target Outcomes

### 4.1 System Goals
1. **Standardized activity platform**
   - Clear activity taxonomy (category + optional subcategory) with minimal “Other”.
   - Department stored explicitly on Task and TaskHistory.
2. **Reliable compliance and salary inputs**
   - Single source of truth for **33% rule**, evidence thresholds, and eligibility logic.
3. **Tight Finance integration**
   - Stable APIs for activity totals, evidence coverage, and compliance that Finance can rely on for:
   - Budget planning, salary decisions, and variance analysis.
4. **Operational efficiency**
   - Bulk assignment, rule‑based + AI assignment, management dashboards.
   - Automation of repetitive flows (reset, evidence reminders, forecasting).

### 4.2 Success Metrics
- **Activity / Data Quality**
  - < 10% of tasks in “Other” category (down from 32%).
  - ≥ 80% of tasks with valid evidence attached.
- **Compliance & Finance**
  - 33% compliance calculated from a **single, documented formula** everywhere.
  - ≥ 90% of employees above compliance threshold each month.
  - Material reduction in budget/salary variance driven by Management data.
- **Automation & UX**
  - Monthly reset success rate > 99.9% (with full audit trail).
  - Majority of task assignments via **dashboard + rule/AI path**, not manual picks.

---

## 5. Phases & High‑Level Roadmap

> These phases align with the detailed requirements, architecture, and implementation docs – this section describes the **business intent** at a high level.

### Phase 0 – Consolidation (Done)
- DRY foundation: shared utilities, base models/views, shared templates, consolidation command.
- Legacy code isolated under `deprecated/`.

### Phase 1 – Data Pipeline & Automation
- Turn existing Task / TaskHistory / TaskLinks / meeting data into a **coherent activity pipeline**.
- Auto‑link meetings to tasks; provide assignment suggestions; expose basic activity analytics.

### Phase 2 – Finance & Compliance Integration
- Harden **33% rule** and evidence requirements.
- Provide robust Management → Finance APIs for activity totals, evidence validation, and compliant employee lists.
- Ensure department‑aware reporting (including historical snapshots).

### Phase 3 – Advanced Analytics & Forecasting
- Forecast activity and budget needs for 3+ months out.
- Provide trend analysis, anomaly detection, and compliance KPIs for management dashboards.

---

## 6. Risks, Assumptions & Open Questions

### 6.1 Key Risks
- **Data quality** (historic gaps, inconsistent activity names, missing daf_date) can degrade analytics.
- **Schema alignment** between Management and Finance (especially department fields) is critical.
- Over‑reliance on AI without fast rule‑based paths can slow operations and obscure logic.

### 6.2 Assumptions
- All salary and budget decisions will eventually route through the standardized **ComplianceCalculator + Management APIs**.
- Department and evidence policies will be clarified and encoded as explicit rules (not scattered checks).

### 6.3 Open Questions (To Resolve with Stakeholders)
- Final policy for:
  - Compliance formula (confirmed: point‑based, but edge‑case rules still to be ratified).
  - Evidence requirements and minimum coverage for inclusion.
  - Handling department changes mid‑month and historical reporting.

---

## 7. Summary

The Employee Activity System already has **rich models, services, and early integrations** with Finance, but suffers from:
- Missing structural fields (department, subcategory, templates),
- Inconsistent or under‑specified compliance/evidence rules, and
- A lack of unified, user‑friendly management interfaces.

This analysis establishes the **business context, current reality, and target outcomes** that the remaining 6 documents (Requirements, Architecture, Implementation, Testing, Maintenance, Deployment) will refine into precise specifications and procedures.