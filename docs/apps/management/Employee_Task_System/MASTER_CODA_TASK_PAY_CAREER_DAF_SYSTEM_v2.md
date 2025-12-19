# CODA – Task, Pay, Career & DAF System  

**Master Architecture & Implementation Document – Dec 2025**  

**Branch:** `25.12_CODA_DEV_CM`  

> **🎯 SINGLE SOURCE OF TRUTH** – This document is the complete reference for CODA's Task, Pay, Career, DAF, and Regional Pay systems.  
> **Use this document to start a new chat session and pick up where we left off.**  
>  
> Business rules from **Think-Ahead Rounds 1–4** are treated as **ground truth** in this document.

---

## 📋 Table of Contents

1. [High-Level Goals](#0-high-level-goals)  
2. [Domain Overview & Current State (Dec 2025)](#1-domain-overview--current-state-dec-2025)  
3. [Target Architecture](#2-target-architecture)  
   - [Pay Philosophy & Safety Nets (Rounds 1 & 4)](#21-pay-philosophy--safety-nets-rounds-1--4)  
   - [Service Layers](#22-service-layers)  
   - [Group B Career Ladder (B1–B18)](#23-group-b-career-ladder-b1-b18)  
   - [Group A Ladder (A1–A5, Design Sketch)](#24-group-a-ladder-a1-a5-design-sketch)  
   - [Group C Structure (C1–C3 Badges)](#25-group-c-structure-c1-c3-badges)  
   - [Stipend & Safety Net – Group B](#26-stipend--safety-net--group-b)  
   - [Loyalty Fund & Vesting](#27-loyalty-fund--vesting)  
   - [Regional PayPolicy & Currencies](#28-regional-paypolicy--currencies)  
   - [DAF UX Expectations (Rounds 2 & 3)](#29-daf-ux-expectations-rounds-2--3)  
4. [Policy Knobs & Default Values (from Rounds 1–4)](#3-policy-knobs--default-values-from-rounds-1-4)  
5. [Implementation Status](#4-implementation-status)  
6. [Key Files and Locations](#5-key-files-and-locations)  
7. [Technical Patterns and Constraints](#6-technical-patterns-and-constraints)  
8. [Test Results and Status](#7-test-results-and-status)  
9. [Next Steps & Roadmap](#8-next-steps--roadmap)  
10. [Implementation Roadmap & Open Questions](#9-implementation-roadmap--open-questions)  
11. [Glossary](#10-glossary)  
12. [Quick Reference](#11-quick-reference)  
13. [AI Assist Layer for Task, Pay & DAF (Domain-Specific)](#13-ai-assist-layer-for-task-pay--daf-domain-specific)  
14. [Document Maintenance](#14-document-maintenance)  

---

## 0. High-Level Goals

CODA has struggled for 10+ years with:

- **Fairness in pay vs performance** – Hard to align pay with actual work *quality*.  
- **People gaming the system** – Working late in the cycle to meet thresholds.  
- **Harsh-feeling delays and gates** – 45+ day delay, 33% rule feels punitive.  
- **Extremely pay-sensitive Group B staff** – Small changes have big impact.

We are now designing a **long-term**, **AI-assisted**, **self-regulating** system that:

1. Keeps **Task & ActivityType** as the source of truth for work done.  
2. Separates **what is earned** from **what is released** (cash paid).  
3. Provides **deep career ladders**, especially for Group B (3k → 30k).  
4. Uses the **DAF UI as the behaviour engine** (clear progress toward next raise).  
5. Avoids salary cuts; instead uses **promotion freezes, stipend adjustments, and visibility**.  
6. Stays **backward-compatible**, minimizing migrations and breaking changes.  
7. Scales across **regions and currencies** with a canonical KES ladder and per-country `PayPolicy`.  
8. Aligns with the **emotional rules** from Think-Ahead Rounds 1–4:
   - Group B: stability, small but real steps, “never zero if they showed up”.  
   - Group A: higher risk/reward via retainer + variable pay.  
   - Group C: training pipeline into A or B.  
   - Quality: clean, evidence-backed work > raw speed.  

---

## 1. Domain Overview & Current State (Dec 2025)

### 1.1 Employee Groups

We conceptually divide CODA employees into three groups:

- **Group A – Grads / Skilled / Remote**
  - Degree or higher, can be remote, multiple gigs.
  - Upper pay cap ≈ 100k KES for top performers, with exceptional cases above that by explicit agreement.
  - Strong emphasis on evidence & quality, often billable.
  - Pay model: **retainer + variable** (see [2.4](#24-group-a-ladder-a1-a5-design-sketch)).

- **Group B – Core Staff (onsite, HS or below)**
  - Onsite, often >40, CODA is main income.
  - Cost-centre & internal work (cleaning, ops, internal processes).
  - Start ≈ 3k KES, target cap ≈ 30k KES (B1–B18 ladder).
  - Highly pay-sensitive; +1k steps are big motivators.
  - Limited English; DAF labels are English but behaviour explained with Swahili helper text.

- **Group C – High school trainees**
  - In school, CODA sponsors upkeep & education.
  - Mostly no formal salary; receives allowances and education support.
  - Treated as **C1–C3 badges** that indicate progression and potential to move into Group B or A.

These groups exist as **business logic** and should be represented in code via a `group` field in a career/employee state model (e.g. `EmployeeCareerState`).

---

### 1.2 Core Models (Existing)

**Task system**

- `Task`  
  - Represents a *current-month* activity for a user.  
  - Linked to an `ActivityType` (new system) or legacy task type.  
  - Has points, completion status, and `TaskLinks` for evidence.

- `TaskHistory`  
  - Monthly snapshot of tasks (by employee, for month N).  
  - Used as the basis for salary calculation for that month.  
  - Finance dashboards aggregate from `TaskHistory`.

- `ActivityType`  
  - Canonical activity definitions:
    - `unit_rate` (KES per unit)
    - `monthly_target_units`
    - `points_per_unit`
    - `is_billable`
  - Used by `Task.get_pay()` to compute pay based on ActivityType logic.
  - Provides structure for target-setting and quality tracking.

- `TaskLinks`  
  - Evidence: documents, forms, drive links, meeting recordings.  
  - Connects tasks to external evidence sources.

**Evidence & meetings**

- `GotoMeetings`  
  - Stores GoToMeeting data (meeting IDs, date, attendees).

- `MeetingLinkingService`  
  - Multi-strategy matcher that links meetings to tasks:
    - Uses date, attendees, titles, and confidence scoring.  
  - Planned to **replace** legacy `auto_uplaod_evidence` Celery job.

**Pay & compliance**

- `Task.get_pay`  
  - Now prefers **ActivityType-based** logic:
    - `unit_rate * monthly_target_units`, adjusted proportionally by points, plus late penalties.
  - Falls back to legacy formula:
    - `(points / mxpoint) * mxearning * late_penalty`.

- `PayCalculationService`  
  - Centralizes payslip logic for a month:
    - Base pay from tasks / TaskHistory.
    - Bonuses: EOM, holiday, late-night, login, laptop, etc.
    - Deductions: tax, food, maintenance, health, laptop savings, loans.
  - Returns a structured, currency-aware breakdown for payslip rendering.
  - Phase P3 extends it with **earned vs released** separation and stipend logic.

- `PayslipConfig`  
  - Per-employee knobs controlling:
    - Loan %
    - Holiday pay
    - EOM bonus rules
    - Other bonus/deduction parameters.

- **Compliance rule ("33% rule")**  
  - Implemented via:
    - `ComplianceCalculator`
    - `EmployeeComplianceService`
    - `RealtimeComplianceService`
  - Rule:
    - Employees must reach **33% completion of current tasks by the 15th of the new month** for last month's pay to be **released**.
    - In the target system it becomes a **release gate**, not an "earnings eraser" (earnings are recorded but may remain locked).

**Finance integration**

- Finance uses:
  - `TaskHistory`
  - `calculate_total_pay` (legacy) or `PayCalculationService` (new)
- For:
  - Salary dashboards
  - Budgeting and forecasting.

---

## 2. Target Architecture

We are moving toward a **service-oriented internal architecture** with clear responsibility boundaries.  
`PayCalculationService` is the orchestrator that calls specialized engines, all constrained by **business truths from Rounds 1–4**.

### 2.1 Pay Philosophy & Safety Nets (Rounds 1 & 4)

**Group B – Core Staff**

- **Raises per year:** Target **2–3 raises/year** in normal circumstances.  
- **Step size:** Mostly **1k KES** increments, occasionally 2k at key milestones.  
- **Month-to-month variation:**
  - Base ladder pay **should not go down** except in extreme, HR-driven cases or role changes.
  - Variability should come from:
    - Release fraction (how much of earned is released now),
    - Stipend,
    - Bonuses.
  - Soft rule: Total monthly cash generally should **not drop more than ~20–25%** from the recent 3-month average, unless attendance is very low.
- **Safety net:**
  - They **only get 0** if they **never showed up at all** in that month.
  - If they attend at least **≈10 days** and their total (release + stipend) is below **≈1,500 KES**, a **safety net top-up** brings them up to the minimum (details in [2.6](#26-stipend--safety-net--group-b)).
- **Progression timing:**
  - 3k → 10k: ~18–24 months typical, 12–18 best-case.
  - 10k → 20k: +24–36 months.
  - 20k → 30k: +36–48 months.
  - So **3k → 30k** ≈ **6–8 years typical**, and **3–4 years** is the fastest allowed for true superstars.
- **Tough months:**
  - Preference: **promotion freezes + reduced stipend + tighter release** rather than salary cuts.
  - Sharp drops like 20k → 10k should only happen as part of **formal HR processes**, not automatic maths.

**Group A – Grads / Skilled / Remote**

- **Pay model:** **Retainer + variable**:
  - Retainer is more stable (reviewed every 6–12 months).
  - Variable swings with billable work, client feedback, and quality.
- **Swings allowed:**
  - Total pay can drop significantly (e.g. 50k → 30k) if billable work collapses, provided:
    - The retainer portion is stable (e.g. 30–35k),
    - The drop is clearly associated with fewer billable hours/work.
- **Safety net:**
  - No global “never zero” rule.
  - Any guarantee is via **per-role or per-person retainer** configured in `PayslipConfig`, not a system-wide safety net.

**Group C – Students**

- Treated primarily as a **pipeline**; CODA optimizes for:
  - Training, character, discipline.
  - Identifying who should join **Group B or A** later.
- Structure: **C1–C3 badges** (not a pay ladder).
  - C3 comes with a **guaranteed fast-track** into B1–B2 or A1.

**Soft vs sharp system**

- CODA prefers to avoid a system that is “mathematically perfect but emotionally brutal.”  
- We **err slightly on the “soft but clear” side**, especially for Group B:
  - Protect from big downward shocks.
  - Accept a bit of gaming/softness in exchange for retention and trust.

These principles constrain:

- Ladder design in [2.3](#23-group-b-career-ladder-b1-b18), [2.4](#24-group-a-ladder-a1-a5-design-sketch), [2.5](#25-group-c-structure-c1-c3-badges).  
- Release & stipend logic in [2.2.2](#222-releaseengine) and [2.6](#26-stipend--safety-net--group-b).  
- Loyalty Fund design in [2.7](#27-loyalty-fund--vesting).  
- Regional pay design in [2.8](#28-regional-paypolicy--currencies).  

---

### 2.2 Service Layers

The target architecture uses a **service-oriented design**. `PayCalculationService` orchestrates the following engines:

- `EarningsEngine` – “How much did month N objectively earn?”  
- `PerformanceMetricsService` – “What was compliance, quality, attendance?”  
- `CareerLevelService` – “Where is this person on the ladder? Ready to move?”  
- `ReleaseEngine` – “Given compliance & policy, how much do we release now vs lock?”  
- `LoyaltyFundService` – “What is allocated to long-term savings?”  
- `PayPolicy` layer – “Given country, what are the local equivalents of our KES ladders & safety nets?”  
- `ChecklistEvaluationService` – “What is the quality & evidence score for tasks?”  

#### 2.2.1 EarningsEngine

Wraps the existing pay logic based on tasks and ActivityTypes.

**Responsibilities:**

- Read `TaskHistory` for month N.  
- Apply `Task.get_pay()` and ActivityType formulas.  
- Apply bonuses (EOM, holiday, etc.) and deductions.  
- Produce a structured breakdown:

```python
class EarningsEngine:
    def calculate_earned(self, employee, month) -> dict:
        return {
            "base_task_pay": ...,
            "bonuses": {...},
            "deductions": {...},
            "earned_amount": ...,   # after bonuses & deductions
            "currency": "KES",
        }
Current Implementation:

Logic currently lives inside PayCalculationService._calculate_base_pay(), _calculate_bonuses(), _calculate_deductions().

Future: Extract into dedicated EarningsEngine for clearer separation.

Earnings are always in canonical KES, but PayPolicy will handle local currency equivalents (see 2.8
).

2.2.2 ReleaseEngine

Decides how much of earned_amount_N to release based on compliance, quality, tenure, and policy.

Responsibilities:

Check compliance for month N+1 (33% rule).

Consult PerformanceMetricsService:

Current month compliance & quality,

Earned-month attendance.

Check career state (Group, level, tenure).

Calculate:

Base release vs locked portion (33% gate).

Stipend release (Group B, tenured, compliance + quality-scaled).

Safety net top-up (Group B, attendance-based minimum).

Produce release decision with explanations for DAF UI.

Interface:

class ReleaseEngine:
    def compute_release(
        self,
        employee,
        month_earned,
        month_now,
        earned: dict,
        metrics_now: dict,
        metrics_earned_month: dict,
        career_state: CareerState,
        pay_policy: PayPolicy,
    ) -> dict:
        return {
            "earned_amount": ...,
            "released_now": ...,         # base release from earned if compliant
            "locked_remaining": ...,     # earned - cumulative released
            "stipend_release": ...,      # compliance & quality-scaled (Group B, tenured)
            "safety_net_topup": ...,     # minimum pay top-up (Group B, attendance-based)
            "explanations": [...],       # DAF/HR messages
            "compliance": {...},
            "quality_gates": {...},      # structure for future abuse guardrails
        }


Group-specific behaviour:

Group B:

Release factor driven primarily by compliance & attendance.

Quality influences stipend and promotions first; tightens release only in chronic abuse cases.

Safety net ensures non-zero pay when they genuinely show up.

Group A:

For certain billable tasks, strong rule: “No evidence → no billable credit” (see 2.2.5
).

Release is more tightly tied to evidence & billable metrics, less to safety nets.

Abuse guardrail hook (future):

If avg_quality and evidence_coverage are consistently low over several months while compliance is high, ReleaseEngine can:

Reduce released_now fraction (even above 33% compliance), and/or

Reduce or nullify stipend.

This is Phase P4+ and should be implemented cautiously with clear DAF messaging.

Current Implementation:

Implemented inside PayCalculationService._calculate_release_breakdown() (Phase P3).

Future: Extract into dedicated ReleaseEngine.

2.2.3 CareerLevelService (Future)

Manages career progression for all groups, with a focus on Group B’s B1–B18 ladder.

Responsibilities:

Track CareerState:

group (A/B/C), current_level_code, date_at_level, is_tenured, loyalty_fund_balance.

Consume PerformanceMetricsService window metrics:

avg_compliance, avg_quality, avg_attendance (last 3+ months).

Evaluate promotion readiness based on ladder config:

GROUP_B_LADDER, GROUP_A_LADDER, and C-badges.

Provide progress to next level (0–1) for DAF, plus blocker reasons (“quality too low”, “attendance low”, etc.).

Group B Ladder behaviour (Round 1 constraints):

Hard-coded min months per level + “max promotions per year” = encodes:

3k→30k ~6–8 years typical, 3–4 years fastest allowed.

No demotions from current level; we use promotion freezes instead.

Quality is a hard gate for high levels – you can’t climb into B16–B18 with poor checklists.

Interface (example):

class CareerLevelService:
    def get_state(self, employee) -> CareerState: ...
    
    def get_progress_to_next_level(self, employee, month_now) -> dict:
        return {
            "current_level": "B4",
            "next_level": "B5",
            "progress": 0.65,  # 65%
            "blockers": [
                {"code": "QUALITY_LOW", "message": "Checklist quality 52% < 60% target"},
            ],
        }
    
    def evaluate_promotion(self, employee, month_now) -> PromotionDecision: ...


Status: Not yet implemented (Phase P5).

2.2.4 PerformanceMetricsService (Future)

Aggregates performance metrics for use by ReleaseEngine and CareerLevelService.

Responsibilities:

Monthly metrics per employee:

compliance (from ComplianceCalculator),

checklist_quality_score (from ChecklistEvaluationService),

attendance_days (from attendance system / Task presence),

total_points, total_max_points.

Rolling window metrics (e.g. last 3 months) for promotion decisions.

Interface:

class PerformanceMetricsService:
    def get_month_metrics(self, employee, month) -> dict:
        return {
            "compliance": ...,
            "checklist_quality_score": ...,
            "attendance_days": ...,
            "total_points": ...,
            "total_max_points": ...,
        }
    
    def get_window_metrics(self, employee, months_back=3) -> dict:
        return {
            "avg_compliance": ...,
            "avg_quality": ...,
            "avg_attendance": ...,
        }


Round 2 integration:

Must honor impact tiers and evidence rules from Round 2:

High-impact activities (BI sessions, QA, mentoring, key process owners) have stronger weight on avg_quality.

Missing evidence caps quality contribution for high-impact tasks.

Metrics must distinguish high-impact quality (for promotions) vs overall quality (for stipend caps).

Status: Not yet implemented (Phase P4+).

2.2.5 ChecklistEvaluationService (Future)

Evaluates task-level quality from checklists & evidence.

Responsibilities:

Use Task, ActivityType, and TaskLinks to:

Determine which checklists and evidence are required (via config).

Score each task (0–1 or 0–100%) for quality.

Provide per-activity-type metrics and an aggregated checklist_quality_score per month.

Config: ACTIVITY_CHECKLIST_CONFIG
Location: coda/config/activity_checklists.py (planned)

Example structure:

ACTIVITY_CHECKLIST_CONFIG = {
    "BI_SESSION": {
        "impact": "high",
        "required_evidence": ["attendance", "recording_or_notes", "summary"],
        "promotion_weight": 3.0,  # strong weight for promotions
    },
    "CLEANING_ROUND": {
        "impact": "medium",
        "required_evidence": ["checklist", "periodic_photos", "periodic_supervisor_check"],
        "promotion_weight": 1.5,
    },
    "MICRO_TASK": {
        "impact": "low",
        "required_evidence": [],
        "promotion_weight": 0.5,
    },
}


Round 2 behaviour:

BI Session (high-impact, “properly done” definition):

Minimum evidence:

Attendance recorded (or manually confirmed).

Recording or shared notes/doc.

Short written summary (3–5 bullets).

No or partial evidence:

Task may still contribute to points/compliance,

But quality score is capped (e.g. 30–40%), and promotion weight drops.

Cleaning Round (medium-impact):

Checklist completion (floor, surfaces, trash, bathrooms, etc.).

Periodic before/after photos (not necessarily every day; N per week per area).

Periodic supervisor confirmation / spot-check score.

Evidence rule for high-impact tasks:

“High-impact activities must ALWAYS have evidence, or they can’t be counted as full quality.”

Tolerance curve:

Rollout months 1–2: mostly warnings and training prompts.

After that:

Stage 1: missing evidence → lower task quality, slows promotion, caps stipend (e.g. max 50%).

Stage 2: chronic issues (3+ months) → can block promotions, zero stipend, and “no billable credit” for Group A billable tasks.

Stage 3: triggers HR escalation.
Output examples:

task_quality = {
    task_id: {
        "quality_score": 0.78,
        "impact": "high",
        "missing_evidence": ["summary"],
    },
    ...
}

monthly_quality = {
    "overall_quality": 0.62,
    "high_impact_quality": 0.55,
    "medium_impact_quality": 0.70,
    "evidence_coverage": 0.80,
}


Status: Design stage; implementation is Phase P4.

2.2.6 LoyaltyFundService (Future)

Manages long-term loyalty/retirement accumulation, with vesting rules from Round 4.

Responsibilities:

Compute small percentage (1–3%) of released_now as loyalty fund allocation.

Track per-employee balance and transactions.

Compute vested portion based on tenure & vesting schedule.

Surface visible balance vs vested balance for DAF and HR.

Vesting schedule (Round 4):

< 2 years at CODA → 0% vested.

2–3 years → 25% vested.

3–4 years → 50% vested.

4–5 years → 75% vested.

≥ 5 years → 100% vested.

Example interface:

class LoyaltyFundService:
    def allocate(self, employee, released_now: Decimal) -> AllocationResult: ...
    
    def get_balances(self, employee) -> dict:
        return {
            "total_balance": ...,
            "vested_balance": ...,
            "unvested_balance": ...,
            "vesting_schedule": [...],
        }


Status: Not yet implemented (Phase P7).

2.2.7 PayCalculationService (Orchestrator)

Thin orchestrator that coordinates all engines.

Current Implementation (Phase P1/P2/P3):

Encapsulates earnings calculation and release logic.

Returns structured payslip data.

Already separates earned vs released and calculates stipend.

Target Implementation (Future):

class PayCalculationService:
    def calculate_payslip(self, employee, month_to_pay, month_now=None, display_currency=None):
        earned = EarningsEngine().calculate_earned(employee, month_to_pay)
        
        metrics_now = PerformanceMetricsService().get_month_metrics(employee, month_now)
        metrics_earned = PerformanceMetricsService().get_month_metrics(employee, month_to_pay)
        window_metrics = PerformanceMetricsService().get_window_metrics(employee, months_back=3)
        
        career_state = CareerLevelService().get_state(employee)
        pay_policy = PayPolicyRegistry().for_employee(employee)
        
        release = ReleaseEngine().compute_release(
            employee,
            month_to_pay,
            month_now,
            earned,
            metrics_now,
            metrics_earned,
            career_state,
            pay_policy,
        )
        
        loyalty = LoyaltyFundService().allocate(employee, release["released_now"])
        progress = CareerLevelService().get_progress_to_next_level(employee, month_now)
        
        return {
            "employee_id": employee.id,
            "month_earned": month_to_pay,
            "earnings": earned,
            "release": release,
            "career": {
                "group": career_state.group,
                "level": career_state.current_level_code,
                "next_level": progress["next_level"],
                "progress_to_next": progress["progress"],
                "blockers": progress["blockers"],
                "loyalty_fund_balance": loyalty.balance_after,
            },
            "display_currency": display_currency or pay_policy.local_currency,
        }


Status:

Phase P1/P2/P3 done, using an integrated version of these behaviours.

Future: factor out EarningsEngine, ReleaseEngine, PerformanceMetricsService, CareerLevelService, LoyaltyFundService, PayPolicy.

2.3 Group B Career Ladder (B1-B18)

Group B is CORE_STAFF with a long-term ladder 3k → 30k in small steps.
This ladder must respect Round 1 timelines (approx 6–8 years typical from 3k to 30k).

Ladder Structure:

B1–B10: Foundation / Process Operators (3k → 15k KES).

B11–B15: Senior Operators (17k → 25k KES).

B16–B18: Core Anchors (27k → 30k KES).

Config Structure (Python dict):

Location: coda/config/career_levels.py

GROUP_B_LADDER = [
    # --- Foundation / Process Operators ---
    {"code": "B1",  "title": "Foundation Operator I",   "base_pay": 3000,
     "min_months": 1, "min_compliance": 0.33, "min_quality": 0.40, "min_attendance_days": 12},
    {"code": "B2",  "title": "Foundation Operator II",  "base_pay": 4000,
     "min_months": 2, "min_compliance": 0.40, "min_quality": 0.45, "min_attendance_days": 14},
    {"code": "B3",  "title": "Foundation Operator III", "base_pay": 5000,
     "min_months": 2, "min_compliance": 0.45, "min_quality": 0.50, "min_attendance_days": 16},
    {"code": "B4",  "title": "Process Operator I",      "base_pay": 6000,
     "min_months": 3, "min_compliance": 0.50, "min_quality": 0.55, "min_attendance_days": 18},
    {"code": "B5",  "title": "Process Operator II",     "base_pay": 7000,
     "min_months": 3, "min_compliance": 0.55, "min_quality": 0.60, "min_attendance_days": 18},
    {"code": "B6",  "title": "Process Operator III",    "base_pay": 8000,
     "min_months": 3, "min_compliance": 0.60, "min_quality": 0.60, "min_attendance_days": 18},
    {"code": "B7",  "title": "Advanced Operator I",     "base_pay": 9000,
     "min_months": 4, "min_compliance": 0.65, "min_quality": 0.65, "min_attendance_days": 18},
    {"code": "B8",  "title": "Advanced Operator II",    "base_pay": 10000,
     "min_months": 4, "min_compliance": 0.70, "min_quality": 0.70, "min_attendance_days": 20},
    {"code": "B9",  "title": "Advanced Operator III",   "base_pay": 12000,
     "min_months": 4, "min_compliance": 0.70, "min_quality": 0.70, "min_attendance_days": 20},
    {"code": "B10", "title": "Lead Operator",           "base_pay": 15000,
     "min_months": 5, "min_compliance": 0.75, "min_quality": 0.75, "min_attendance_days": 20},
    
    # --- Senior Operators ---
    {"code": "B11", "title": "Senior Operator I",       "base_pay": 17000,
     "min_months": 6, "min_compliance": 0.78, "min_quality": 0.78, "min_attendance_days": 20},
    {"code": "B12", "title": "Senior Operator II",      "base_pay": 19000,
     "min_months": 6, "min_compliance": 0.80, "min_quality": 0.80, "min_attendance_days": 20},
    {"code": "B13", "title": "Senior Operator III",     "base_pay": 21000,
     "min_months": 6, "min_compliance": 0.82, "min_quality": 0.82, "min_attendance_days": 20},
    {"code": "B14", "title": "Senior Operator IV",      "base_pay": 23000,
     "min_months": 6, "min_compliance": 0.85, "min_quality": 0.85, "min_attendance_days": 20},
    {"code": "B15", "title": "Senior Operator V",       "base_pay": 25000,
     "min_months": 6, "min_compliance": 0.87, "min_quality": 0.87, "min_attendance_days": 20},
    
    # --- Core Anchors ---
    {"code": "B16", "title": "Core Anchor I",           "base_pay": 27000,
     "min_months": 9, "min_compliance": 0.88, "min_quality": 0.88, "min_attendance_days": 20,
     "extra_requirements": ["mentoring_junior", "qa_tasks"]},
    {"code": "B17", "title": "Core Anchor II",          "base_pay": 29000,
     "min_months": 9, "min_compliance": 0.90, "min_quality": 0.90, "min_attendance_days": 20,
     "extra_requirements": ["mentoring_junior", "qa_tasks"]},
    {"code": "B18", "title": "Core Anchor III",         "base_pay": 30000,
     "min_months": 12, "min_compliance": 0.92, "min_quality": 0.92, "min_attendance_days": 20,
     "extra_requirements": ["mentoring_junior", "qa_tasks", "reliability_flag"]},
]


Promotion Logic Summary:

if (months_at_level >= next.min_months
    and avg_compliance >= next.min_compliance
    and avg_quality >= next.min_quality
    and avg_attendance >= next.min_attendance_days
    and extra_requirements_satisfied
    and promotions_this_year < GROUP_B_MAX_PROMOTIONS_PER_YEAR):
    decision = READY
else:
    decision = NOT_YET or FROZEN


Progress to Next Level (0–1 scale for DAF):

progress = min(
    avg_compliance / next.min_compliance,
    avg_quality / next.min_quality,
    months_at_level / next.min_months,
    avg_attendance / next.min_attendance_days,
)
progress = max(0.0, min(1.0, progress))


No demotions: current_level_code only increases.

Poor performance → promotion freezes, stipend & bonuses adjust, release may tighten in abuse scenarios.

2.4 Group A Ladder (A1–A5, Design Sketch)

Group A is smaller, with fewer levels and bigger jumps, strongly tied to billable work and quality.

Design ladder (KES-equivalent baseline):

Location: coda/config/career_levels.py

GROUP_A_LADDER = [
    {"code": "A1", "title": "Associate",             "base_pay": 40000,
     "min_months": 6, "min_billable_ratio": 0.40, "min_quality": 0.75},
    {"code": "A2", "title": "Specialist / Analyst",  "base_pay": 55000,
     "min_months": 9, "min_billable_ratio": 0.50, "min_quality": 0.78},
    {"code": "A3", "title": "Senior Specialist / Lead", "base_pay": 70000,
     "min_months": 12, "min_billable_ratio": 0.60, "min_quality": 0.82},
    {"code": "A4", "title": "Principal / Manager",   "base_pay": 85000,
     "min_months": 18, "min_billable_ratio": 0.65, "min_quality": 0.85,
     "extra_requirements": ["team_lead", "client_ownership"]},
    {"code": "A5", "title": "Partner / Anchor",      "base_pay": 100000,
     "min_months": 24, "min_billable_ratio": 0.70, "min_quality": 0.90,
     "extra_requirements": ["portfolio_ownership", "strategic_role"]},
]


Key principles:

Typical upper cap: ≈100k KES/month; rare exceptions allowed by explicit management decision.

High-impact criteria:

Billable hours / revenue (ActivityTypes with is_billable=True).

Client satisfaction and rework rates.

Evidence coverage (docs, code, recordings – mandatory for billing).

Evidence rule for billable tasks:

For certain billable ActivityTypes: “No evidence → no billable credit.”

2.5 Group C Structure (C1–C3 Badges)

Group C = students/trainees. They are not on a salary ladder; they have badges indicating progression.

Location: coda/config/career_levels.py

GROUP_C_BADGES = [
    {"code": "C1", "title": "New Trainee"},
    {"code": "C2", "title": "Reliable Trainee"},
    {"code": "C3", "title": "Top Trainee / Candidate"},
]


Behaviour:

C1 → Learning basics and discipline.

C2 → Consistent attendance and basic task competence.

C3 → Reliable, good quality; triggers guaranteed fast-track into:

B1–B2 (if practical/ops track), or

A1 (if academic/analytical track and they later get a degree).

Group C mostly ties into DAF as:

Training checklists,

Behaviour scores,

Simple progress bar C1→C3.

2.6 Stipend & Safety Net – Group B
2.6.1 Stipend (Tenured, Group B Only)

Business Rules (Round 1 & 2):

Applies only to: group == "B" and is_tenured == True (e.g. ≥12 months at CODA).

Stipend is not salary; it is a release-time safety top-up based on current month’s compliance & quality.

Not part of earned_amount_N – it is added when ReleaseEngine decides the payout for N.

Base design:

def calculate_stipend(employee, metrics_now, career_state, pay_policy):
    if not (career_state.group == "B" and career_state.is_tenured):
        return 0
    
    base_stipend = pay_policy.local_stipend_base  # e.g. 2500 KES equivalent
    
    c = metrics_now["compliance"]         # 0–1 or 0–100 scaled
    q = metrics_now["checklist_quality_score"]
    
    # Compliance factor – aligned to 33% and ~66.5% thresholds
    if c < 0.33:
        factor = 0.0
    elif c < 0.665:
        factor = 0.5   # 50% stipend
    else:
        factor = 1.0   # 100% stipend
    
    # Quality cap – Round 2 rule
    if q < 0.5:
        factor = min(factor, 0.5)  # low quality → stipend capped at 50%
    
    return int(base_stipend * factor)


Status:

Phase P3 implements a simpler compliance-only version in PayCalculationService._calculate_stipend().

Quality caps (Round 2) will be wired in during Phase P4 when ChecklistEvaluationService delivers real checklist_quality_score.

2.6.2 Safety Net (“Never Zero if They Showed Up”)

Principle (Round 1):

Group B only gets 0 pay if they never showed up in that month.

Rule (tunable knobs):

Let:

MIN_ATTENDANCE_FOR_SAFETY_NET ≈ 10 days.

SAFETY_NET_MIN_PAY ≈ 1500–2000 KES (in KES equivalent, then localized via PayPolicy).

Design:

def calculate_safety_net(employee, earned_month, release, metrics_earned_month, pay_policy):
    min_attendance = pay_policy.local_safety_net_min_attendance  # default 10
    min_pay = pay_policy.local_safety_net_min_pay                # default 1500 KES eq
    
    if metrics_earned_month["attendance_days"] < min_attendance:
        return 0
    
    total_current = release["released_now"] + release["stipend_release"]
    if total_current >= min_pay:
        return 0
    
    return min_pay - total_current

2.7 Loyalty Fund & Vesting

Concept:

Each month, 1–3% of released_now is allocated into a Loyalty Fund account per employee.

Visible on DAF as “Loyalty Fund” with future availability date and vesting status.

Rate logic (example for Group B):

def get_loyalty_rate(group, level_code) -> float:
    if group == "B":
        if level_code in ["B1", "B2", "B3", "B4", "B5"]:
            return 0.01  # 1%
        elif level_code in ["B6", "B7", "B8", "B9", "B10", "B11", "B12"]:
            return 0.02  # 2%
        else:  # B13-B18
            return 0.03  # 3%
    # Group A, C can be defined separately
    return 0.0


Vesting (Round 4):

Vesting schedule config, e.g. in coda/config/loyalty_fund.py:

LOYALTY_VESTING_SCHEDULE = [
    {"min_years": 0, "max_years": 2, "vested_fraction": 0.0},
    {"min_years": 2, "max_years": 3, "vested_fraction": 0.25},
    {"min_years": 3, "max_years": 4, "vested_fraction": 0.50},
    {"min_years": 4, "max_years": 5, "vested_fraction": 0.75},
    {"min_years": 5, "max_years": None, "vested_fraction": 1.00},
]


DAF messaging should highlight:

Total balance vs vested balance.

Approximate date when balance becomes fully accessible.

2.8 Regional PayPolicy & Currencies

CODA wants to scale beyond Kenya while keeping KES as the canonical anchor.

Principles (Round 4):

Define ladders (B1–B18, A1–A5, C-badges) in KES as the canonical pay bands.

Pay staff in their local currency by default.

Internally, store both:

base_amount_local, base_currency, and

kes_equivalent for cross-country comparison and budgeting.

Avoid month-to-month FX salary whiplash:

FX rate updates are periodic (e.g. 6–12 months) or when movement exceeds a band (e.g. ±10%).

Finance can use live FX for reporting; employees experience stable local currency pay.

PayPolicy design:

Location: coda/config/pay_policy.py

@dataclass
class PayPolicy:
    country_code: str              # "KE", "UG", "US", ...
    local_currency: str            # "KES", "UGX", "USD", ...
    kes_to_local_rate: Decimal     # snapshot rate for ladder mapping
    ladder_multiplier: Decimal     # adjustment vs KES baseline if needed
    local_safety_net_min_pay: Decimal
    local_safety_net_min_attendance: int
    local_stipend_base: Decimal
    group_a_typical_max_local: Decimal

class PayPolicyRegistry:
    def for_employee(self, employee) -> PayPolicy:
        # Look up by employee.country / office
        ...


Example: for Uganda, we might say:

Local currency: UGX.

Ladder multiplier tuned to local salary norms.

Stipend base = KES 2500 equivalent in UGX.

Safety net min pay tuned to UGX reality.

2.9 DAF UX Expectations (Rounds 2 & 3)

The DAF (Daily Activity Form) is the behaviour engine, not just a report.

2.9.1 Layout Overview (Group B focus)

Order of importance on the main DAF screen:

Career level & next raise

“What to focus on this month”

This month’s compliance (current progress)

Quality / checklist status

Earned vs released vs locked

Today’s tasks / details

2.9.2 Career & Pay Summary (Hero Card)

Example:

[Jane Doe] – CORE_STAFF – B4 (Process Operator I)
Base pay: 6,000 KES
Next level: B5 – 7,000 KES
Loyalty fund: 4,200 KES (available from Jun 2028)

Progress to next raise
[██████████████--------] 65%
"Estimated 2–3 months at your current pace."

✅ At level B4 for 3 months (needs ≥3).
✅ Average compliance (last 3 months): 57% (needs ≥55%).
⚠️ Checklist quality (last 3 months): 52% (needs ≥60%).
✅ Attendance: 19 days/month (needs ≥18).


Data from CareerLevelService + PerformanceMetricsService + LoyaltyFundService.

2.9.3 Earned vs Released vs Locked (Money Card)

Example:

"Last month's money (Earned in Nov, paid in Dec)"

Item                    Amount (KES)
Earned from tasks       22,300
Released this month     18,000
Still locked            4,300
Stipend (Dec)           1,500
Safety net top-up       0
─────────────────────────────────
Total pay this month    19,500


Messaging rules (Round 3):

High transparency: show earned, released, locked, stipend, safety net.

Explain why money is locked or stipend reduced, in simple language.

Always pair “locked” with “how to unlock”:

“You have 4,300 KES locked from November. Reach 33% completion this month to unlock more.”

2.9.4 Activity List + Quality & Promotion Impact

Table:

Activity        Points      Evidence    Quality    Promotion impact
BI Session      40 / 60     ✔           78%        ⭐ High
Cleaning Round  26 / 40     !           45%        ◔ Medium
Training Task   10 / 20     ✖           20%        ✖ Low


Clicking an activity opens:

Checklist items & status.

Evidence links (recordings, photos, docs).

Coach-like hint:

“To get full credit for BI Sessions and help your next raise, always add a short summary.”

2.9.5 Language & Tone (Round 3)

Language:

UI labels in English, with Swahili helper text for Group B.

Important messages show both:

“Your quality score is 45%. Target is 60%. Complete all checklist items to improve.”
“Maelezo: Ubora wako ulikuwa 45%. Tunahitaji angalau 60%. Tafadhali kamilisha vitu vyote kwenye checklist.”

Tone:

Primarily coach, with manager clarity, not robotic.

Example:

“You’re 65% of the way to B5 (7,000 KES). Keep your compliance above 55% and improve your quality to 60%+ to move faster.”

Avoid shaming (“you did a bad job”); avoid vagueness (“stipend changed”).

2.9.6 Notifications & Nudges

Types:

Compliance nudges: “You are at 24% completion. You need 9% more by the 15th to unlock last month’s pay.”

Evidence nudges: “2 activities are missing evidence. Add photos/summary to improve your quality score.”

Promotion nudges: “You’re 80% ready for B5 (7,000 KES). Keep quality above 60% this month.”

Positive reinforcement: “Great work! Your quality improved from 48% to 62% this month.”

Frequency:

Group B:

Weekly summary (e.g. Friday), plus extra nudges around 10th–15th and when something is seriously off.

Group A:

Weekly summary, plus nudges when billable work or evidence is low.

General rule: Notify only when there is something actionable and time to fix it.

2.9.7 Appeals & Monthly Audit

DAF should expose a simple path:

“Think this is wrong? Talk to your supervisor or HR.”

Optionally a short feedback form.

Monthly breakdown for employees:

“You were paid 19,500 KES because:

18,000 KES from last month’s work (80% of earnings released),

1,500 KES stipend (60% of max stipend),

0 KES safety net (already above minimum),

4,300 KES remains locked; reach 33% this month to unlock more.”

Managers get a slightly more detailed version (with compliance %, attendance, quality, etc.).

3. Policy Knobs & Default Values (from Rounds 1–4)

These are configuration knobs, not hard-coded laws.
They should live in config modules (or settings), be easy to tweak, and be visible to leadership.

3.1 Group B Progression

GROUP_B_MAX_PROMOTIONS_PER_YEAR = 3

Target timelines (inform ladder config and promotion gating):

B_TARGET_3K_TO_10K_MONTHS = (18, 24)

B_TARGET_10K_TO_20K_MONTHS = (24, 36)

B_TARGET_20K_TO_30K_MONTHS = (36, 48)

Fastest allowed path:

B_FASTEST_3K_TO_30K_YEARS = 3–4

3.2 Safety Net (Group B)

MIN_ATTENDANCE_FOR_SAFETY_NET = 10 days (per earned month).

SAFETY_NET_MIN_PAY_KES = 1500 (canonical; PayPolicy converts to local).

3.3 Stipend (Group B, Tenured)

PAYROLL_BASE_STIPEND_AMOUNT_KES = 2500 (canonical).

PAYROLL_MIN_STIPEND_TENURE_MONTHS = 12.

Compliance thresholds:

<33% → 0% stipend.

33–66.5% → 50% stipend.

≥66.5% → 100% stipend.

Quality cap (Phase P4):

If quality < 0.5, stipend_factor <= 0.5.

3.4 Group A (Grads / Skilled / Remote)

GROUP_A_TYPICAL_MAX_KES = 100000 (typical upper band; exceptions allowed).

Retainer review period:

GROUP_A_RETAINER_REVIEW_MIN_MONTHS = 6

GROUP_A_RETAINER_REVIEW_MAX_MONTHS = 12

3.5 Group C (Students)

GROUP_C_STRUCTURE = ["C1", "C2", "C3"].

C3_FAST_TRACK_DESTINATIONS = ["B1", "B2", "A1"] (depending on path).

3.6 Loyalty Fund

Rate by level (example – see 2.7
):

LOYALTY_RATE_B1_B5 = 0.01

LOYALTY_RATE_B6_B12 = 0.02

LOYALTY_RATE_B13_B18 = 0.03

Vesting:

<2 years → 0%

2–3 years → 25%

3–4 years → 50%

4–5 years → 75%

≥5 years → 100%

3.7 Region / PayPolicy

Canonical currency:

BASE_CANONICAL_CURRENCY = "KES".

PayPolicy defaults per country:

local_currency (e.g. "KES", "UGX").

kes_to_local_rate (FX snapshot).

ladder_multiplier vs KES baseline.

local_safety_net_min_pay, local_safety_net_min_attendance.

local_stipend_base.

group_a_typical_max_local.

3.8 DAF UX / Notifications

DAF_NOTIF_WEEKLY_SUMMARY_DAY = "Friday".

DAF_NOTIF_EXTRA_NUDGE_DAYS = [10, 12, 14, 15] (around 33% gate).

DAF_NOTIF_MAX_PER_WEEK = 3 (to avoid spam).

4. Implementation Status

### 4.1 Implementation Flow Summary

**Phase T2: ActivityType System**  

├── ✅ Models: `TaskSubcategory`, `ActivityType`  

├── ✅ Seeding: 15 canonical `ActivityType` rows  

├── ✅ Service: `ActivityTypeApplicationService`  

├── ✅ Integration: `Task.get_pay()` uses `ActivityType` when present  

└── ✅ Tests: 49 tests passing

**Phase P1: PayCalculationService**  

├── ✅ Service: `PayCalculationService` created  

├── ✅ Encapsulates: base pay, bonuses, deductions  

├── ✅ Backward compatible: reuses existing utilities  

└── ✅ Tests: 7 integration tests passing

**Phase P2: Payslip View Refactoring**  

├── ✅ View: `payslip()` uses `PayCalculationService`  

├── ✅ Thin controller pattern

├── ✅ Template compatibility maintained

└── ✅ Tests: covered by P1 integration tests  

**Phase P3: Earned vs Released Separation**  

├── ✅ Extended: `PayCalculationService` with `earned` / `released` / `locked`  

├── ✅ Integrated: `ComplianceCalculator` for 33% rule  

├── ✅ Feature: base stipend calculation (+ Django settings config)  

├── ✅ Quality gates stub structure added  

└── ✅ Tests: 10 dedicated tests passing  

**Phase P4: ChecklistEvaluationService & Real Quality Metrics**  

├── ✅ Config: `ACTIVITY_CHECKLIST_CONFIG` in `coda/config/activity_checklists.py`  

│   ├── `ChecklistItemConfig` dataclass (`code`, `label`, `weight`)  

│   ├── `ActivityChecklistConfig` dataclass (`activity_slug`, `items`, `promotion_weight`)  

│   └── Registry entries for: BI Session, Cleaning Round, Training Session, Data Analysis, Default  

├── ✅ Service: `ChecklistEvaluationService`  

│   ├── `get_task_quality_score()` – per-task scoring from evidence  

│   ├── `get_month_quality_score()` – weighted monthly average (by `mxpoint`)  

│   ├── `_find_related_task()` – match `TaskHistory` → `Task` for evidence  

│   ├── `_check_evidence_items()` – inspect `TaskLinks` for required evidence  

│   └── `_calculate_score_from_evidence()` – compute score from weights  

├── ✅ Integration: `PerformanceMetricsService` updated  

│   ├── Real `quality` values (no longer stubbed)  

│   ├── `get_month_metrics()` returns real quality scores  

│   └── `get_window_metrics()` uses real quality averages  

├── ✅ Shadow mode: quality used for **career metrics**, not pay yet  

└── ✅ Tests:  

    ├── `test_checklist_evaluation_service_p4.py` – 9 tests  

    └── Updated `test_performance_metrics_service_p5.py` – 11 tests total passing  

**Phase P5 Part 3: PromotionExecutionService**  

├── ✅ Service: `PromotionExecutionService` in `coda/management/services/promotion_execution_service.py`  

│   ├── `shadow_mode=True` by default (recommendations only)  

│   ├── Execution mode updates `EmployeeCareerState` when criteria met  

│   ├── Uses `CareerLevelService.get_progress_to_next_level()`  

│   ├── Uses `CareerLevelService.evaluate_promotion()`  

│   ├── Uses `PerformanceMetricsService` (compliance, quality, attendance)  

│   ├── `evaluate_employee_for_period()` – builds full recommendation payload  

│   ├── `execute_promotion_if_applicable()` – applies promotion when ready & not in shadow mode  

│   ├── `batch_evaluate_employees()` – multi-employee evaluation  

│   └── `batch_execute_promotions()` – multi-employee execution  

├── ✅ Integration:  

│   ├── Reuses existing `CareerLevelService` (no duplication)  

│   ├── Reuses `EmployeeCareerState` model (no new models)  

│   └── Reuses `GROUP_B_LADDER` config from `coda/config/career_levels.py`  

└── ✅ Tests: `test_promotion_execution_service_p5.py` – 12 tests  

    ├── Shadow vs execution mode  

    ├── With/without tasks  

    ├── Ready vs not-ready scenarios  

    ├── Batch ops  

    └── Edge cases (already at top level, etc.)  

**Phase P6: EarningsEngine & ReleaseEngine Extraction**  

├── ✅ Service: `EarningsEngine` in `coda/management/services/earnings_engine.py`  

│   ├── Pure calculation engine (stateless, no Django ORM)  

│   ├── Operates on plain dicts/DTOs  

│   ├── `calculate()` – base pay, bonuses, deductions, summary  

│   ├── `_calculate_base_pay()` – base pay details  

│   ├── `_structure_bonuses()` – bonus structuring  

│   ├── `_structure_deductions()` – deduction structuring  

│   └── `_calculate_summary()` – gross, net, totals  

├── ✅ Service: `ReleaseEngine` in `coda/management/services/release_engine.py`  

│   ├── Extracted release logic from `PayCalculationService`  

│   ├── `compute_release()` – release decision with compliance/quality gates  

│   ├── `_calculate_stipend()` – Group B, tenured, compliance & quality-scaled  

│   ├── `_calculate_safety_net()` – Group B, attendance-based minimum  

│   └── `_build_explanations()` – DAF UI messages  

├── ✅ Integration: `PayCalculationService` refactored  

│   ├── Uses `EarningsEngine` for pure calculations  

│   ├── Uses `ReleaseEngine` for release decisions  

│   ├── `_prepare_base_pay_input()` – converts Django models → plain dicts  

│   ├── `_prepare_bonus_inputs()` – converts Django models → plain dicts  

│   └── `_prepare_deduction_inputs()` – converts Django models → plain dicts  

├── ✅ Backward compatible: Public API unchanged, internal refactoring only  

└── ✅ Tests: `test_earnings_engine_p6.py` – comprehensive pure calculation tests  

**Phase P7: LoyaltyFundService**  

├── ✅ Config: `LOYALTY_VESTING_SCHEDULE` in `coda/config/loyalty_fund.py`  

│   ├── Vesting schedule: 0-2 years (0%), 2-3 years (25%), 3-4 years (50%), 4-5 years (75%), 5+ years (100%)  

│   ├── `get_loyalty_rate()` – 1-3% based on group/level  

│   ├── `get_vested_fraction()` – vesting fraction by tenure  

│   ├── `calculate_vested_balance()` – total, vested, unvested breakdown  

│   └── `get_estimated_vesting_date()` – years to full vesting  

├── ✅ Service: `LoyaltyFundService` in `coda/management/services/loyalty_fund_service.py`  

│   ├── `allocate()` – monthly allocation from released pay (1-3%)  

│   ├── `get_balances()` – total, vested, unvested balances  

│   ├── `_calculate_years_at_coda()` – tenure calculation  

│   └── Integrates with `EmployeeCareerState.loyalty_fund_balance`  

├── ✅ Integration:  

│   ├── Uses `EmployeeCareerState` model for balance tracking  

│   ├── Uses `get_loyalty_rate()` from config  

│   └── Uses vesting schedule from config  

├── ✅ Shadow mode: Allocations calculated, may not affect actual pay yet  

└── ✅ Tests: `test_loyalty_fund_service_p7.py` – allocation, vesting, balance tests  

**Phase P8: DAF Summary API & UI**  

├── ✅ Service: `DAFSummaryService` in `coda/management/services/daf_summary_service.py`  

│   ├── Aggregates data from existing services (PayCalculationService, CareerLevelService, etc.)  

│   ├── `get_summary()` – comprehensive DAF summary payload  

│   ├── `_get_career_data()` – career state, progress, loyalty fund  

│   ├── `_get_money_data()` – earned/released/locked, stipend, safety net  

│   ├── `_get_metrics_data()` – current month + window metrics  

│   ├── `_get_activities_data()` – task list with quality scores and promotion impact  

│   └── `_get_focus_data()` – recommendations and Swahili helper text  

├── ✅ API Endpoint: `/api/daf/summary` in `coda/management/views/api_views.py`  

│   ├── `daf_summary_api()` – GET endpoint with month and employee_id params  

│   ├── Permissions: users can view own data, staff can view others  

│   └── Returns JSON with employee, career, money, metrics, activities, focus  

├── ✅ Integration:  

│   ├── Uses `PayCalculationService` for money data  

│   ├── Uses `CareerLevelService` for career progress  

│   ├── Uses `PerformanceMetricsService` for metrics  

│   ├── Uses `ChecklistEvaluationService` for quality scores  

│   └── Uses `LoyaltyFundService` for loyalty fund balances  

├── ✅ Shadow mode: API available, UI components optional for this phase  

└── ✅ Tests:  

    ├── `test_daf_summary_service_p8.py` – service structure and data aggregation tests  

    └── `test_daf_summary_api_p8.py` – API endpoint, permissions, and response structure tests  

**Phase P9: Regional PayPolicy (Shadow Mode)**  

├── ✅ Config: `PayPolicy` dataclass and `PayPolicyRegistry` in `coda/config/pay_policy.py`  

│   ├── `PayPolicy` – country-specific pay configuration  

│   │   ├── `country_code`, `local_currency`, `kes_to_local_rate`, `ladder_multiplier`  

│   │   ├── `local_safety_net_min_pay`, `local_safety_net_min_attendance`  

│   │   ├── `local_stipend_base`, `group_a_typical_max_local`  

│   │   ├── `convert_kes_to_local()` – KES → local currency conversion  

│   │   └── `convert_local_to_kes()` – local currency → KES conversion  

│   ├── `PayPolicyRegistry` – registry for country policies  

│   │   ├── `for_country()` – lookup by country code (defaults to KES)  

│   │   ├── `for_employee()` – lookup by employee.country field  

│   │   ├── `register()` – register custom policies  

│   │   └── Default policies: KE (KES, 1:1), UG (UGX, 1:35)  

│   └── `get_policy_registry()` – singleton registry instance  

├── ✅ Integration: `PayCalculationService` (shadow mode)  

│   ├── Gets `PayPolicy` for employee via `PayPolicyRegistry`  

│   ├── Adds `pay_policy` metadata to response  

│   ├── Adds `local_currency_equivalents` for display (KES amounts converted)  

│   └── **No changes to actual calculations** – all remain in KES (shadow mode)  

├── ✅ Integration: `DAFSummaryService` (shadow mode)  

│   ├── Gets `PayPolicy` for employee  

│   ├── Adds local currency equivalents to money data  

│   └── Adds pay policy metadata for UI display  

├── ✅ Backward compatibility:  

│   ├── If no PayPolicy found, defaults to KES (1:1 rate)  

│   ├── If employee has no country, defaults to KES  

│   ├── All existing calculations unchanged (still in KES)  

│   └── PayPolicy info is additive only (doesn't break existing behavior)  

└── ✅ Tests: `test_pay_policy_p9.py` – policy creation, conversion, registry lookup, integration tests  

**Future Phases (Design Complete, Not Implemented Yet)**  

- Phase P10+ – Additional features as needed  

---

### 4.2 Current Status

| Phase | Status       | Tests                | Notes                                                  |

|------:|--------------|----------------------|--------------------------------------------------------|

| T2    | ✅ Complete  | 49 passing           | ActivityType system                                    |

| P1    | ✅ Complete  | 7 passing            | `PayCalculationService` core                          |

| P2    | ✅ Complete  | Covered in P1        | `payslip()` view uses service                         |

| P3    | ✅ Complete  | 10 passing           | Earned/released separation + stipend                  |

| P4    | ✅ Complete  | 9 + 11 passing       | Real quality via `ChecklistEvaluationService`         |

| P5.3  | ✅ Complete  | 12 passing           | `PromotionExecutionService` (shadow + execution)      |

| P6    | ✅ Complete  | Tests passing        | `EarningsEngine` & `ReleaseEngine` extracted          |

| P7    | ✅ Complete  | Tests passing        | `LoyaltyFundService` (allocation + vesting)          |

| P8    | ⏳ Planned   | –                    | DAF UX/API                                            |

| P9    | ⏳ Planned   | –                    | Regional `PayPolicy` rollout                          |
4.3 What Has Been Completed
Phase T2: ActivityType System (Complete)

Models Added:

TaskSubcategory model in coda/management/models.py

ActivityType model with fields:

name, slug, description

department (FK to Department)

category (FK to TaskCategory)

subcategory (FK to TaskSubcategory)

unit_type (session, hour, meeting, work_block, item, approved_video, candidate_cycle, month, requirement, other)

unit_rate, monthly_target_units, points_per_unit

is_billable, is_active

Task model extended with:

activity_type (FK to ActivityType, nullable)

is_client_project (Boolean)

Seeding:

Management command: python manage.py seed_activity_types

Seeds 15 canonical ActivityTypes idempotently

Location: coda/management/management/commands/seed_activity_types.py

Services:

ActivityTypeApplicationService in coda/management/services/activity_type_service.py

apply_to_task() – applies ActivityType defaults to Task

find_activity_type_by_name() – finds by name, legacy mapping, or slug

Integration:

Task.get_pay prefers ActivityType-based calculation when available, falls back to legacy

Admin flows updated (TrainingAdmin, TaskAdmin, create_task helper)

All backward compatible

Tests:

49 tests passing for ActivityType model, seeding, service, and admin integration

Test files:

coda/management/tests/test_activity_type_model.py

coda/management/tests/test_activity_type_seeding.py

coda/management/tests/test_activity_type_service.py

coda/management/tests/test_admin_activity_type_integration.py

Phase P1: PayCalculationService (Complete)

Service Created:

File: coda/management/services/pay_calculation_service.py

Class: PayCalculationService

BASE_CURRENCY = "KES"

Main method:
calculate_payslip(employee, target_month, target_year, pay_type, enforce_evidence=False, display_currency=None, include_release_breakdown=False)

Service Structure:

Encapsulates all payslip calculation logic:

Base pay from Tasks/TaskHistory

Bonuses (EOM, holiday, late-night, login bonus, laptop bonus)

Deductions (tax, loan, laptop savings, food, maintenance, health)

Returns structured dictionary with:

base_pay – tasks queryset and total

bonuses – detailed bonus breakdown

deductions – detailed deduction breakdown

summary – gross_pay, net_pay, total_bonus, total_deductions

metadata – employee info, period, currency

tasks – queryset for template rendering

Helper Methods:

_get_user_data() – gets user profile, loan data, payslip config

_calculate_base_pay() – uses payinitial() utility

_calculate_bonuses() – uses bonus() and calculate_login_bonus()

_calculate_deductions() – uses deductions() and loan_computation()

_empty_payslip() – returns empty structure

Backward Compatibility:

Delegates to existing utility functions in management/utils.py

No model changes

No numeric behavior changes

All calculations remain identical

Phase P2: Payslip View Refactoring (Complete)

View Refactored:

File: coda/management/views.py

Function: payslip() (around line 1012)

Now a thin controller:

Resolves request parameters (employee, selected_month, selected_year, pay_type)

Instantiates PayCalculationService

Calls service.calculate_payslip(...)

Maps service output to template context

No longer calls calculate_total_pay, bonus, deductions, loan_computation, lap_save_bonus, get_bonus_and_summary, calculate_login_bonus directly

Legacy Helper for Testing:

File: coda/management/tests/helpers/legacy_payslip_calculator.py

Function: calculate_legacy_payslip()

Reproduces OLD payslip calculation for regression testing

Integration Tests:

File: coda/management/tests/test_pay_calculation_service_integration.py

7 comprehensive test scenarios:

Full-time employee with loan, laptop, high performance

Contractor, low performance, no loan

Below and above EOM threshold (75%)

No tasks scenario

Detailed bonus/deduction breakdowns

All tests assert numeric equality (to 2 decimals) between legacy and new service

Status: ✅ All 7 tests passing

Test Results:

python manage.py test management.tests.test_pay_calculation_service_integration --keepdb → ✅ PASS

All existing management tests still passing

python manage.py check → ✅ 0 issues

Phase P3: Earned vs Released Separation (Complete)

Service Extended:

File: coda/management/services/pay_calculation_service.py

Added include_release_breakdown parameter to calculate_payslip()

New methods:

_calculate_release_breakdown() – Calculates earned/released/locked amounts

_get_check_month_year() – Determines Month N+1 for compliance checking

_calculate_stipend() – Calculates base stipend with compliance scaling

Earned vs Released Logic:

earned_amount_n = Net pay from Month N work (TaskHistory snapshot)

released_amount_n = Portion of Month N earnings actually paid out

locked_amount_n = earned_amount_n - released_amount_n

Earnings are never deleted – just locked until compliance met

33% Rule Integration:

Uses ComplianceCalculator to check Month N+1 compliance

Rule active after 15th of current month (is_rule_active())

If compliant: Release Month N earnings + stipend

If not compliant: Locked until compliance met

Base Stipend:

Safety net for tenured employees (configurable, default: 2,500 KES)

Only for employees with tenure ≥ PAYROLL_MIN_STIPEND_TENURE_MONTHS (default: 12 months)

Compliance-scaled formula:

At 33% compliance → stipend factor = 0

At ~66.5% compliance → stipend factor ≈ 0.5

At 100% compliance → stipend factor = 1

Formula: stipend = base_stipend_amount * ((compliance_rate - 33) / (100 - 33))

Treated as release-time component, not part of Month N earning

Configuration:

Added to coda/coda_project/coda_settings/base_settings.py:

PAYROLL_BASE_STIPEND_AMOUNT (default: 2500.00 KES)

PAYROLL_MIN_STIPEND_TENURE_MONTHS (default: 12 months)

Service-level config (NOT in PayslipConfig yet)

Tests:

File: coda/management/tests/test_pay_calculation_service_p3.py

10 comprehensive test scenarios (all passing):

test_earned_amount_equals_net_pay – Verifies earned = net pay

test_compliant_employee_releases_full_amount – Compliant employees release earnings

test_non_compliant_employee_locks_amount – Non-compliant employees lock earnings

test_stipend_calculation_tenured_employee – Stipend calculation for tenured

test_stipend_zero_for_new_employee – New employees get no stipend

test_stipend_zero_below_33_percent – No stipend below 33%

test_stipend_full_at_100_percent_compliance – Full stipend at 100%

test_compliance_data_structure – Compliance data structure validation

test_quality_gates_structure – Quality gates (stub for Phase P4)

test_backward_compatibility_without_release_breakdown – Backward compatibility

Status: ✅ All 10 tests passing

Test Command: python manage.py test management.tests.test_pay_calculation_service_p3 --keepdb

Backward Compatibility:

include_release_breakdown=False by default (Phase P1/P2 behavior preserved)

All existing numeric calculations remain identical

Payslip view continues to work as before

No model changes (service-level only)

#### Phase P4: ChecklistEvaluationService & Real Quality Metrics (Complete)

**New Files:**

- `coda/config/activity_checklists.py`  

  - `ChecklistItemConfig` dataclass (`code`, `label`, `weight`)  

  - `ActivityChecklistConfig` dataclass (`activity_slug`, `items`, `promotion_weight`)  

  - `ACTIVITY_CHECKLIST_CONFIG` registry with entries such as:  

    - `BI Session` (high promotion weight)  

    - `Cleaning Round` (medium)  

    - `Training Session` (medium)  

    - `Data Analysis` (high)  

    - `Default` (low)  

  - Helper functions: `get_checklist_config()`, `get_promotion_weight()`  

- `coda/management/services/checklist_evaluation_service.py`  

  - `ChecklistEvaluationService` with:  

    - `get_task_quality_score(task_history)` – per-task quality using evidence  

    - `get_month_quality_score(employee, year, month)` – weighted monthly score  

    - `_find_related_task()` – match `TaskHistory` → `Task` for evidence lookup  

    - `_check_evidence_items()` – check `TaskLinks` for evidence items  

    - `_calculate_score_from_evidence()` – compute final score from weights  

**Integration:**

- `PerformanceMetricsService` updated to use real quality:

  - `get_month_metrics()` returns real `quality` from `ChecklistEvaluationService`.  

  - `get_window_metrics()` aggregates real monthly quality scores.  

- Existing docstrings updated to reflect that Phase P4 is fully wired (no more stubbed quality).  

- Quality remains in **shadow mode** for pay – used for career progression and analytics first.

**Tests:**

- `coda/management/tests/test_checklist_evaluation_service_p4.py`  

  - 9 tests covering:

    - Config matching  

    - Per-task scoring with/without evidence  

    - Monthly aggregation (weighted by `mxpoint`)  

    - Evidence checking logic  

    - Score calculation from evidence  

- `coda/management/tests/test_performance_metrics_service_p5.py`  

  - Updated expectations to use real quality  

  - All 11 `PerformanceMetricsService` tests passing  

---

#### Phase P5 Part 3: PromotionExecutionService (Complete)

**New File:**

- `coda/management/services/promotion_execution_service.py`  

**Core Methods:**

- `evaluate_employee_for_period(employee, start_date, end_date, months_back=...) -> dict`  

  - Uses:

    - `CareerLevelService.get_progress_to_next_level()` for detailed progress.  

    - `CareerLevelService.evaluate_promotion()` for simple readiness evaluation.  

    - `PerformanceMetricsService` (real compliance, quality, attendance).  

  - Returns a **structured dict** including:

    - `current_state` (career state)  

    - `promotion_evaluation`  

    - `progress_data`  

    - `recommendation`:

      - `ready_for_promotion: bool`  

      - `recommended_level: str|None`  

      - `reason: str`  

      - `blockers: List[str]`  

    - `evaluation_period` (start/end, months_back)  

    - `metrics_summary` (avg compliance/quality/attendance).  

- `execute_promotion_if_applicable(employee, recommendation) -> dict`  

  - Honours `shadow_mode`:

    - If `True`: returns a non-executed result with the recommendation.  

    - If `False` and ready: updates `EmployeeCareerState.current_level_code` + `date_at_level`.  

  - Returns:

    - `executed`, `shadow_mode`  

    - `previous_level`, `new_level`  

    - `promotion_date`  

    - `message`  

    - `recommendation` (the full dict).  

- `batch_evaluate_employees(employees=None, ...) -> List[dict]`  

- `batch_execute_promotions(employees=None, ...) -> List[dict]`  

**Integration:**

- Reuses:

  - `CareerLevelService` for ladder logic (no duplication).  

  - `PerformanceMetricsService` for performance inputs.  

  - `EmployeeCareerState` as the source of truth for levels.  

  - `GROUP_B_LADDER` config from `coda/config/career_levels.py`.  

- **Shadow mode by default**:

  - No automatic promotions unless explicitly enabled.  

**Tests:**

- `coda/management/tests/test_promotion_execution_service_p5.py` (12 tests)  

  - Shadow mode (default and explicit)  

  - Evaluation with and without tasks  

  - Execution:

    - Shadow mode → no changes  

    - Not ready → no changes  

    - Ready → level change applied  

  - Batch evaluation & execution  

  - Recommendation structure validation  

  - Edge cases (e.g. already at ladder top)  

All tests related to **P4 + P5 Part 3** are **passing**.

---

#### Phase P6: EarningsEngine & ReleaseEngine Extraction (Complete)

**New Files:**

- `coda/management/services/earnings_engine.py`  

  - `EarningsEngine` class – pure calculation engine (stateless, no Django ORM)  

  - `calculate()` – main entry point, takes plain dict inputs  

  - `_calculate_base_pay()` – base pay details (total, points, goal_amount, balances)  

  - `_structure_bonuses()` – structures bonus inputs (login, EOM, holiday, etc.)  

  - `_structure_deductions()` – structures deduction inputs (tax, loan, food, etc.)  

  - `_calculate_summary()` – gross pay, net pay, totals  

  - Operates on plain dicts/DTOs (no Django models)  

- `coda/management/services/release_engine.py`  

  - `ReleaseEngine` class – release decision logic  

  - `compute_release()` – main entry point, returns release decision  

  - `_calculate_stipend()` – Group B, tenured, compliance & quality-scaled stipend  

  - `_calculate_safety_net()` – Group B, attendance-based minimum pay top-up  

  - `_build_explanations()` – human-readable messages for DAF UI  

  - `_get_check_month_year()` – calculates Month N+1 for compliance check  

**Integration:**

- `PayCalculationService` refactored to use engines:

  - `_prepare_base_pay_input()` – converts Django models/querysets → plain dicts for `EarningsEngine`  

  - `_prepare_bonus_inputs()` – converts Django models → plain dicts for `EarningsEngine`  

  - `_prepare_deduction_inputs()` – converts Django models → plain dicts for `EarningsEngine`  

  - `calculate_payslip()` now orchestrates: `EarningsEngine.calculate()` → `ReleaseEngine.compute_release()`  

- **Backward compatible**: Public API unchanged, all existing callers work without modification  

- Internal refactoring only – no breaking changes

**Tests:**

- `coda/management/tests/test_earnings_engine_p6.py`  

  - Tests for pure calculation logic (no Django ORM)  

  - Base pay, bonuses, deductions, summary calculations  

  - Edge cases (empty inputs, negative values, etc.)  

  - All tests passing

---

#### Phase P7: LoyaltyFundService (Complete)

**New Files:**

- `coda/config/loyalty_fund.py`  

  - `LOYALTY_VESTING_SCHEDULE` – vesting schedule configuration  

  - `get_loyalty_rate(group, level_code)` – returns 1-3% allocation rate based on group/level  

  - `get_vested_fraction(years_at_coda)` – returns vesting fraction (0.0 to 1.0)  

  - `calculate_vested_balance(total_balance, years_at_coda)` – returns (vested, unvested) tuple  

  - `get_estimated_vesting_date(years_at_coda)` – returns years to full vesting  

- `coda/management/services/loyalty_fund_service.py`  

  - `LoyaltyFundService` class  

  - `allocate(employee, released_now)` – allocates 1-3% of released pay to loyalty fund  

  - `get_balances(employee)` – returns total, vested, unvested balances  

  - `_calculate_years_at_coda(employee)` – calculates tenure from `date_joined`  

**Integration:**

- Uses `EmployeeCareerState.loyalty_fund_balance` for balance tracking  

- Integrates with `get_loyalty_rate()` from config  

- Uses vesting schedule from config  

- **Shadow mode**: Allocations calculated, may not affect actual pay yet (can be wired into `PayCalculationService` later)

**Tests:**

- `coda/management/tests/test_loyalty_fund_service_p7.py`  

  - Allocation tests (rate calculation, balance updates)  

  - Vesting tests (0-2 years, 2-3 years, 3-4 years, 4-5 years, 5+ years)  

  - Balance tracking tests (total, vested, unvested)  

  - Edge cases (new employees, no date_joined, etc.)  

  - All tests passing

---

5. Key Files and Locations
Core Services

coda/management/services/pay_calculation_service.py – Main payslip calculation service (P1/P2/P3)

coda/management/services/activity_type_service.py – ActivityType application logic (T2)

coda/management/services/compliance_calculator.py – 33% rule compliance calculation

coda/management/services/employee_compliance_service.py – Compliance service wrapper

coda/management/services/checklist_evaluation_service.py – Checklist & quality scoring (P4)

coda/management/services/performance_metrics_service.py – Aggregated metrics (P4+)

coda/management/services/career_level_service.py – Career ladder & promotions (P5)

coda/management/services/promotion_execution_service.py – Promotion evaluation & execution (P5 Part 3)

coda/management/services/earnings_engine.py – Pure earnings calculation engine (P6)

coda/management/services/release_engine.py – Release decision logic (P6)

coda/management/services/loyalty_fund_service.py – Loyalty fund allocation & vesting (P7)

Models

coda/management/models.py – Contains Task, TaskHistory, ActivityType, TaskSubcategory, EmployeeCareerState

coda/finance/models/core.py – Contains PayslipConfig

coda/shared_core/users.py – Contains Department, CustomerUser

Views

coda/management/views.py – Contains refactored payslip() view (around line 1012)

Utilities

coda/management/utils.py – Contains legacy calculation functions:

get_tasks(), calculate_total_pay(), payinitial()

bonus(), deductions(), loan_computation()

lap_save_bonus(), get_bonus_and_summary()

coda/accounts/utils.py – Contains calculate_login_bonus()

Tests

coda/management/tests/test_pay_calculation_service_integration.py – Phase P1/P2 regression tests (7 tests, all passing)

coda/management/tests/test_pay_calculation_service_p3.py – Phase P3 earned/released tests (10 tests, all passing)

coda/management/tests/helpers/legacy_payslip_calculator.py – Legacy calculator helper for regression testing

coda/management/tests/test_activity_type_*.py – ActivityType tests (4 files, 49 tests, all passing)

Configuration

coda/coda_project/coda_settings/base_settings.py – Contains stipend configuration:

PAYROLL_BASE_STIPEND_AMOUNT,

PAYROLL_MIN_STIPEND_TENURE_MONTHS.

(Planned config modules)

coda/config/career_levels.py – GROUP_B_LADDER, GROUP_A_LADDER, GROUP_C_BADGES

coda/config/activity_checklists.py – ACTIVITY_CHECKLIST_CONFIG

coda/config/pay_policy.py – PayPolicy definitions per country

coda/config/loyalty_fund.py – LOYALTY_VESTING_SCHEDULE, rates

6. Technical Patterns and Constraints
Import Patterns

Departments: from shared_core.users import Department

UserProfile: from accounts.models import UserProfile

PayslipConfig: from finance.models import PayslipConfig

Finance services: Use get_finance_task_service() helper from management.services.finance_service_helper

Currency

Base canonical currency: KES.

All amounts use Decimal for precision.

Current implementation is effectively KES-only, but structure is currency-aware for future multi-currency using PayPolicy.

Test Patterns

Use Django’s TestCase, not pytest.

Use get_or_create for TaskCategory to prevent duplicates.

Use --keepdb flag for faster test runs.

Compare legacy vs new calculations to 2 decimal places.

Calculation Formulas

Legacy Task Pay:

task_pay = (point / mxpoint) * mxearning * late_penalty


ActivityType Task Pay (when activity_type set):

expected_points_for_full_target = monthly_target_units * points_per_unit
max_earning_for_type = unit_rate * monthly_target_units
pay = max_earning_for_type * (task.point / expected_points_for_full_target) * late_penalty
(capped at max_earning_for_type)


Gross Pay:

gross_pay = total_pay + total_bonus + login_bonus


Net Pay:

net_pay = gross_pay - total_deductions


Stipend Formula (Phase P3):

effective_rate = clamp(compliance_rate, 33, 100)
factor = (effective_rate - 33) / (100 - 33)
stipend = base_stipend_amount * factor

Compliance Calculation

Source: ComplianceCalculator in management/services/compliance_calculator.py

Formula: completion_rate = (total_points / total_max_points) * 100

Compliant if: completion_rate >= 33

Rule active: After 15th of current month (is_rule_active())

7. Test Results and Status
Phase P1/P2 Integration Tests

File: test_pay_calculation_service_integration.py

Tests: 7 scenarios

Status: ✅ All passing

Purpose: Verify backward compatibility (numeric equality with legacy calculations)

Phase P3 Earned/Released Tests

File: test_pay_calculation_service_p3.py

Tests: 10 scenarios

Status: ✅ All passing

Purpose: Verify earned/released separation, compliance integration, stipend calculation

ActivityType Tests

Files: test_activity_type_*.py (4 files)

Tests: 49 scenarios

Status: ✅ All passing

Purpose: Verify ActivityType system integration

Test Execution
# Run all Phase P3 tests
python manage.py test management.tests.test_pay_calculation_service_p3 --keepdb

# Run all Phase P1/P2 integration tests
python manage.py test management.tests.test_pay_calculation_service_integration --keepdb

# Run all ActivityType tests
python manage.py test management.tests.test_activity_type_* --keepdb

# Run all management tests
python manage.py test management --keepdb

8. Next Steps & Roadmap
Phase P4: Quality Gates & Evidence Enforcement (Future)

Goal: Evidence enforcement and quality tracking.

Enhancements:

ChecklistEvaluationService:

Evaluate task quality based on evidence & checklists.

Implement ACTIVITY_CHECKLIST_CONFIG with impact tiers (high/medium/low).

Evidence rules for BI Sessions, Cleaning Rounds, training, mentoring, etc.

PerformanceMetricsService:

Aggregate compliance, quality, attendance into monthly and rolling metrics.

Provide checklist_quality_score for:

Stipend caps (max 50% when quality <50%).

Promotion gates (CareerLevelService).

Quality Gates Integration (Round 2):

Quality mainly impacts promotions and stipend.

Release factor (33% rule) remains primarily driven by compliance & attendance for Group B, with only abuse guardrail hooks for chronic low quality.

Evidence Enforcement (Group A):

For selected billable ActivityTypes: “no evidence → no billable credit.”

Soft rollout with warnings → penalties → strict enforcement.

Phase P5: CareerLevelService & Group B Ladder (Future)

Goal: Career progression system, especially for Group B (B1–B18).

Enhancements:

Group B Ladder Configuration:

Implement GROUP_B_LADDER in coda/config/career_levels.py.

EmployeeCareerState Model:

Fields: user, group, current_level_code, date_at_level, loyalty_fund_balance, is_tenured, promotions_this_year.

CareerLevelService:

get_state(), evaluate_promotion(), get_progress_to_next_level().

Enforce Round 1 progression timing (3k→30k ~6–8 years typical; not 18–24 months).

DAF Integration:

Show progress bar, blockers, and estimated time to next raise.

Phase P6: Service Extraction & Refactoring (Future)

Goal: Extract engines from PayCalculationService for clearer separation.

Enhancements:

EarningsEngine:

Extract _calculate_base_pay(), _calculate_bonuses(), _calculate_deductions().

ReleaseEngine:

Extract _calculate_release_breakdown() into dedicated service.

Add safety net top-up logic (Group B).

Integrate richer quality gates and abuse guardrails.

PerformanceMetricsService:

Implement as described in 2.2.4
.

PayCalculationService Refactor:

Make it call: EarningsEngine, PerformanceMetricsService, CareerLevelService, ReleaseEngine, LoyaltyFundService, PayPolicy.

Preserve existing external API for callers.

Phase P7: LoyaltyFundService (Future)

Goal: Long-term loyalty/retirement accumulation.

Enhancements:

LoyaltyFundService:

Compute 1–3% of released amounts per month.

Track balances and apply vesting schedule from Round 4.

DAF Display:

Show current total vs vested amount and estimated vesting date.

Phase P8: DAF UI Implementation (Future)

Goal: Full DAF UX with career progression visualization.

Enhancements:

API Endpoint:

/api/daf/summary?month=YYYY-MM&employee_id=...

Returns: career summary, progress, earned/released/locked, activity list, quality, focus recommendations.

Front-end Components:

Progress bar for next level.

Career & pay summary card.

Earned vs released vs locked card.

Activity list with quality & promotion impact.

“What to focus on this month” hints.

Localizable strings (English + Swahili).

Phase P9: Regional PayPolicy Rollout (Future)

Goal: Multi-country readiness.

Enhancements:

PayPolicyRegistry Implementation:

Kenya baseline policy (KES 1:1).

Example Uganda policy (UGX, multiplier, local safety net values).

Shadow Mode:

Run PayPolicy logic in parallel to current system, compare outputs.

Validate fairness and stability before switching contracts in new countries.

9. Implementation Roadmap & Open Questions
9.1 Foundation Services (Phase P4–P7)

Suggested sequence of technical tasks:

Create Config Modules:

coda/config/career_levels.py – Add GROUP_B_LADDER, GROUP_A_LADDER, GROUP_C_BADGES.

coda/config/activity_checklists.py – Add ACTIVITY_CHECKLIST_CONFIG.

coda/config/pay_policy.py – Add default PayPolicy for Kenya and placeholder for others.

coda/config/loyalty_fund.py – Add LOYALTY_VESTING_SCHEDULE.

Implement EarningsEngine.

Implement ChecklistEvaluationService.

Implement PerformanceMetricsService.

Introduce EmployeeCareerState Model.

Implement CareerLevelService.

Implement LoyaltyFundService.

Implement ReleaseEngine.

Refactor PayCalculationService into thin orchestrator.

9.2 Rollout Plan

Phase 0 – Shadow Mode (Internal Only):

Implement services without changing actual payouts.

Log new vs old pay calculations.

Validate fairness and behaviour over several months.

Phase 1 – DAF UX (Read-Only New Logic):

For Group B: show “Career & Progress” panel and “Earned vs Released vs Locked” card using new logic.

Finance & actual payout still uses old calculate_total_pay.

Phase 2 – Switch Payout Logic for Group B:

Finance starts using new PayCalculationService orchestrator for Group B.

Keep old totals visible in internal dashboards for cross-checking.

Phase 3 – Extend to Group A & C:

Enable Group A ladder and Group C badges.

Apply stricter evidence rules for Group A billable tasks.

Phase 4 – Regional Rollout:

Use PayPolicy to onboard new countries with local currencies and safety nets.

9.3 Open Questions / Policy Knobs

These are business decisions, not coding:

Exact Ladder Values:

Are B1–B18 pay levels and min months final, or do they need tuning after pilots?

Tenure Definition for is_tenured:

Exactly how many months at CODA, or reaching which level?

Compliance and Quality Thresholds:

Are the proposed thresholds realistic vs current performance?

Should we tune them so a "good, not superstar" advances every 6–9 months?

Quality Impact:

At which point does low quality:

Only slow promotion?

Also cut stipend?

Or block release (beyond 33% rule) in abuse cases?

Safety Net Minimum Values (per country):

Exact SAFETY_NET_MIN_PAY and MIN_ATTENDANCE_FOR_SAFETY_NET in each PayPolicy.

Loyalty Fund Payout Rules:

Do we allow partial payouts before exit (e.g. after 5+ years while still employed)?

Do we allow employees to "leave the fund invested"?

Group A & C Ladders:

How aggressive to be with Group A bonuses and penalties?

Which combination of grades & behaviours triggers Group C → Group B vs Group C → Group A?

Regional PayPolicy:

Exact multipliers and local caps for first 1–2 new countries.

How we communicate FX adjustments to staff when we update PayPolicy.

DAF UX Detail Level:

How much formula detail to surface to Group B vs managers?

Where to draw the line between transparency vs overwhelm.

10. Glossary

DAF – CODA’s main employee dashboard (Day Activity Form / Daily Activity Form).

Task – An atomic piece of work for the current month.

TaskHistory – Monthly snapshot of tasks; used for payroll and finance.

ActivityType – Canonical classification of activities with rates and targets.

Earned amount – Objective value of work done in month N (from tasks & rules).

Released amount – Cash actually paid out so far for month N.

Locked amount – Earned but unreleased money (due to gates).

Stipend – Tenured Group B top-up based on current compliance & quality.

Safety net – Attendance-based minimum cash to avoid zero pay when they did show up.

Career level – Code like B4, A2, etc., representing salary band and expectations.

Loyalty fund – Long-term savings/retirement balance funded by small % of releases.

33% Rule – Employees must reach 33% completion of current tasks by 15th of new month for last month's pay to be released.

Promotion freeze – When performance drops, promotions are frozen but base pay remains (alternative to salary cuts).

Group A/B/C – Employee segments: grads/skilled/remote (A), core onsite staff (B), students/trainees (C).

PayPolicy – Per-country configuration defining local currency, KES-to-local mapping, local safety net and stipend baselines, local caps.

Group C badges – C1–C3 levels for students/trainees indicating readiness for Group B/A transitions.

11. Quick Reference
Commands
# Run all management tests
python manage.py test management --keepdb

# Run integration tests only
python manage.py test management.tests.test_pay_calculation_service_integration --keepdb

# Run Phase P3 tests
python manage.py test management.tests.test_pay_calculation_service_p3 --keepdb

# Run ActivityType tests
python manage.py test management.tests.test_activity_type_* --keepdb

# Django system check
python manage.py check

# Seed ActivityTypes
python manage.py seed_activity_types

# Create migrations (if needed)
python manage.py makemigrations

# Run migrations
python manage.py migrate

Important Constraints

No Model Changes in Phase P3:

Do not add fields to PayslipConfig.

Do not create MonthlyEarningsSnapshot model.

Focus on service-level logic only.

Backward Compatibility:

All existing numeric calculations must remain identical.

Payslip view must continue to work as before.

Finance integration unchanged for now.

Configuration:

Stipend parameters in Django settings (NOT PayslipConfig yet).

Pattern: PAYROLL_BASE_STIPEND_AMOUNT = Decimal('2500.00').

---

## 13. AI Assist Layer for Task, Pay & DAF (Domain-Specific)

**Scope:** This section defines how AI is allowed to interact with the Task / Pay / DAF system.

**Rule:** AI may explain and coach, but never calculate or decide pay, compliance, or promotions.

This AI layer sits on top of the deterministic phases (T2, P1–P9, P6, P7, P8) and does not change any existing numeric outputs. It is purely an assist / explanation / coaching layer.

### 13.1 Hard Boundaries for AI in this Domain

**AI is ALLOWED to:**

- Generate natural-language explanations of:
  - Earned vs released vs locked amounts.
  - Stipend and safety net behavior.
- Generate DAF focus & coaching messages:
  - "What to focus on this month."
  - Simple Swahili helper lines for Group B.
- Generate career coaching messages:
  - What is blocking the next level.
  - What to improve to move faster.
- Generate quality & evidence feedback:
  - What evidence is missing.
  - How to improve checklist coverage.

**AI is NOT ALLOWED to:**

- **Calculate:**
  - Task pay, bonuses, deductions, net pay, stipend, safety net.
  - Compliance percentages or thresholds.
  - Career levels, promotion decisions, loyalty fund amounts.
- **Modify:**
  - Task, TaskHistory, EmployeeCareerState, payslips, loyalty balances.
  - Any numeric values produced by deterministic services.
- **Override business rules:**
  - 33% rule (ComplianceCalculator).
  - Group B ladder rules (CareerLevelService).
  - Stipend & safety net rules (ReleaseEngine).

**Source of truth remains:**

- **Pay math:** EarningsEngine, ReleaseEngine, PayCalculationService.
- **Compliance:** ComplianceCalculator (+ related services).
- **Career ladder:** CareerLevelService, PromotionExecutionService, GROUP_B_LADDER, GROUP_A_LADDER.
- **Quality:** ChecklistEvaluationService (checklists), PerformanceMetricsService.

AI can describe these outputs; it can never change them.

### 13.2 AIInsightService (Task/Pay/DAF)

All AI assistance for this domain must go through a single service:

`ai_services.services.ai_insight_service.AIInsightService` (planned name).

**Responsibilities (for this domain):**

```python
class AIInsightService:

    def generate_pay_explanation(
        self,
        employee,
        pay_breakdown: dict,      # from PayCalculationService + ReleaseEngine
        compliance_data: dict,    # from ComplianceCalculator / EmployeeComplianceService
        career_state: dict,       # from CareerLevelService.get_state()
    ) -> dict:
        """
        Returns:
        {
            "text_en": "...",     # main explanation in English
            "text_sw": "...",     # helper explanation in simple Swahili (for Group B)
            "highlights": [...],  # key bullet points
        }
        """
    

    def generate_daf_focus(
        self,
        employee,
        career_data: dict,        # group, level, progress, blockers
        money_data: dict,         # earned/released/locked, stipend, safety net
        metrics_data: dict,       # compliance, quality, attendance (current + window)
        activities_data: list,    # per-activity quality & impact (from DAFSummaryService)
    ) -> dict:
        """
        Returns:
        {
            "focus_areas": [...],        # main topics e.g. "Improve BI Session preparation"
            "recommendations": [...],    # plain-English tips
            "swahili_helpers": [...],    # simple Swahili lines for Group B
            "action_items": [            # optional structured actions
                {"title": "...", "deadline_hint": "..."},
            ],
        }
        """
    

    def generate_career_coaching(
        self,
        employee,
        career_state: dict,       # current_level, group, tenure flags
        progress_data: dict,      # progress_to_next_level + blockers
    ) -> dict:
        """
        Returns:
        {
            "summary": "...",           # where you are on the ladder
            "blockers_explained": "...",
            "next_steps": [...],        # practical next steps
        }
        """
    

    def generate_quality_feedback(
        self,
        employee,
        task_or_activity: dict,   # from ChecklistEvaluationService per-task
        quality_score: float,
        missing_items: list,
    ) -> dict:
        """
        Returns:
        {
            "message": "...",           # short feedback
            "missing_items_explained": [...],
        }
        """
    

    def generate_compliance_coaching(
        self,
        employee,
        compliance_data: dict,    # completion rate, threshold, days to 15th, etc.
        target_month: int,
        target_year: int,
    ) -> dict:
        """
        Returns:
        {
            "summary": "...",           # e.g. "You are at 24% completion"
            "what_to_do": "...",        # what to do before the 15th
        }
        """
```

**Key rule:**

AIInsightService only reads deterministic results and writes text. It never changes numbers.

### 13.3 Data Contracts / Schemas (Task/DAF AI Outputs)

For this domain we standardize the shapes that AI must return. These sit conceptually in an OutputSchemaRegistry (even if implemented as simple dataclasses or Pydantic models later).

#### 13.3.1 PayExplanationOutput

Used by payslip view / DAF money card.

```python
PayExplanationOutput = {
    "text_en": str,          # main explanation
    "text_sw": str,          # simple Swahili helper
    "highlights": [str],     # bullet points, 2–5 items max
}
```

**Examples of content:**

- "You earned 22,300 KES in November and unlocked 18,000 KES this month."
- "You received 1,500 KES stipend because your compliance is 62% and you are tenured."
- "You still have 4,300 KES locked. Reach 33% completion this month to unlock more."

#### 13.3.2 DAFFocusOutput

Used by DAFSummaryService for the focus section.

```python
DAFFocusOutput = {
    "focus_areas": [str],       # 1–3 main focus topics
    "recommendations": [str],   # simple sentences
    "swahili_helpers": [str],   # Swahili lines parallel to the main advice
    "action_items": [           # optional structured actions
        {
            "title": str,
            "description": str,
            "priority": int,    # 1 = highest
        }
    ],
}
```

#### 13.3.3 CareerCoachingOutput

Used by career/progression UI and nudges.

```python
CareerCoachingOutput = {
    "summary": str,              # where you are now (level, group)
    "blockers_explained": str,   # plain-language description of blockers
    "next_steps": [str],         # concrete actions for the next 1–3 months
}
```

#### 13.3.4 QualityFeedbackOutput

Used when showing quality per activity / task.

```python
QualityFeedbackOutput = {
    "message": str,              # overall quality feedback
    "missing_items_explained": [str],  # checklist/evidence gaps
}
```

#### 13.3.5 ComplianceCoachingOutput

Used for compliance nudges, especially around the 15th.

```python
ComplianceCoachingOutput = {
    "summary": str,          # e.g. "You are at 24% completion for December."
    "what_to_do": str,       # e.g. "Complete 2 more BI Sessions and 3 Cleaning Rounds before the 15th."
}
```

All AI outputs must be validated against these shapes before being shown. If validation fails, we fall back to deterministic/template text.

### 13.4 Activity-Level AI Context & ActivityDefinition Registry

For AI to coach properly, it needs structured activity definitions that match CODA's reality and our canonical activity list (the 30+ activities derived from TaskHistory and aligned with ActivityType):

- Daily Update Session
- Client Training Preparation Session
- Self-Training Session
- Internal Training Session
- Simulation Training Session
- Client Job Support
- Internal Technical Support
- Developer Project Work (Internal / Client Project)
- Employee DAF Review
- Client Assignment Review
- Strategic Foresight Workshop
- Annual Department Report Preparation
- Research & Development / Innovation Work
- Team-Building / General Assembly Event
- Developer Recruitment
- General Staff Recruitment
- Employee Development Meeting
- Facilities & Office Maintenance Round
- Cashflow Update & Reconciliation
- Budgeting & Forecasting Session
- Video Editing
- Marketing Content Creation
- Social Media Content Publishing
- Social Media Monitoring & Engagement
- …(rest of canonical list as in Activity Catalog).

We will maintain these definitions in an ActivityDefinition registry, for example `coda/config/activity_definitions.py`. Each entry will extend the canonical catalog (`activity_catalog.py`) with:

- `checklist`: list of required/expected steps,
- `good_examples` / `bad_examples`: short scenario examples,
- `ai_context`: short description used in prompts,
- (optional) `quality_thresholds`, `evidence_requirements`.

**Example (aligned with new naming):**

```python
ACTIVITY_DEFINITIONS = {
    "client_training_preparation": {
        "name": "Client Training Preparation Session",
        "checklist": [
            "Open CODA attendance / session page",
            "Prepare training slide deck or walkthrough material",
            "Open required tools (e.g. Tableau, Alteryx, Django app) with the correct project",
            "Load CODA-defined sample data or requirements",
            "Confirm access to GitHub/Heroku if deployment is part of the training",
        ],
        "good_examples": [
            "Prepared Tableau dashboard with CODA sample data and rehearsed full walkthrough.",
        ],
        "bad_examples": [
            "Only watched random YouTube video; no CODA-specific dataset or requirement prepared.",
        ],
        "ai_context": "This session is internal preparation before training a client. The trainer must be ready with tools, data, and materials.",
    },
    "self_training_session": {
        "name": "Self-Training Session",
        "checklist": [
            "Pick a CODA-relevant topic (e.g. SQL joins, Django forms, Tableau filters)",
            "Follow a structured tutorial or course segment",
            "Practice on a small exercise or sample project",
            "Write 3–5 bullet points summarizing what you learned",
        ],
        "ai_context": "Self-training is an individual learning session. The goal is to build skills that can later be applied to real CODA projects.",
    },
}
```

AIInsightService can then:

- Use checklist, good_examples, bad_examples, ai_context to:
  - Explain each activity to employees.
  - Check whether a TaskHistory description "looks like" a valid BI Session or not.
  - Generate specific coaching ("next time, prepare X and Y before the session").

### 13.5 Integration Points (Where AI Hooks into Existing Services)

For this domain, AI will be wired into specific points only:

#### ReleaseEngine → Pay Explanation

After `ReleaseEngine.compute_release(...)` produces:

- `earned_amount`, `released_now`, `locked_remaining`,
- `stipend_release`, `safety_net_topup`,
- `compliance` & `quality_gates`.

We call `AIInsightService.generate_pay_explanation(...)` and attach the result to the payslip/DAF context (e.g. `money["explanation"]`).

**Controlled via setting:**

```python
PAYROLL_AI_EXPLANATIONS_ENABLED = False  # default shadow mode
```

#### DAFSummaryService → Focus & Coaching

After deterministic aggregation in `DAFSummaryService.get_summary(...)`:

- `career`, `money`, `metrics`, `activities`, `meta`.

We call `AIInsightService.generate_daf_focus(...)` and put the output under `summary["focus"]`.

**Controlled via setting:**

```python
DAF_AI_FOCUS_ENABLED = False  # default shadow mode
```

#### CareerLevelService / PromotionExecutionService → Career Coaching

After computing progress to next level:

- `get_progress_to_next_level()` and `evaluate_promotion()`.

We call `AIInsightService.generate_career_coaching(...)` to produce human-readable narrative for DAF or manager dashboards.

**No effect on promotion decisions themselves.**

#### ChecklistEvaluationService / Evidence Services → Quality Feedback

After computing per-task quality scores and missing items.

We call `AIInsightService.generate_quality_feedback(...)` to produce messages employees can see when they click a task in DAF.

#### ComplianceCalculator Wrapper → Compliance Coaching

After `ComplianceCalculator` computes status for the 33% rule.

We call `AIInsightService.generate_compliance_coaching(...)` to generate nudges before the 15th.

### 13.6 Feature Flags, Shadow Mode & Rollout for Task/DAF AI

To protect the existing P1–P9 system, all AI features for this domain must be:

- Behind explicit feature flags in settings.
- Safe to disable without breaking any view or API.
- Tested against deterministic outputs.

**Proposed flags:**

```python
PAYROLL_AI_EXPLANATIONS_ENABLED = False  # ReleaseEngine → pay explanations
DAF_AI_FOCUS_ENABLED = False             # DAFSummaryService → DAF focus/coaching
CAREER_AI_COACHING_ENABLED = False       # CareerLevelService integration
QUALITY_AI_FEEDBACK_ENABLED = False      # Quality feedback integration
COMPLIANCE_AI_COACHING_ENABLED = False   # Compliance nudges
```

**Rollout steps (for this domain):**

#### A1 – Pay Explanations (Shadow Mode)

- Implement `AIInsightService.generate_pay_explanation`.
- Wire into `ReleaseEngine.compute_release()` behind `PAYROLL_AI_EXPLANATIONS_ENABLED`.
- Keep existing hard-coded explanations as fallback.

**Tests:**

- Pay numbers unchanged.
- When AI off or fails, old explanations still served.

#### A2 – DAF Focus & Coaching

- Implement `AIInsightService.generate_daf_focus`.
- Wire into `DAFSummaryService` behind `DAF_AI_FOCUS_ENABLED`.
- Fallback to existing template focus messages.

#### A3 – Career & Quality Coaching

- Implement `generate_career_coaching`, `generate_quality_feedback`, `generate_compliance_coaching`.
- Wire into CareerLevelService / quality flows, with flags.
- Ensure no impact on promotion or compliance decisions.

Only after A1–A3 are stable and observed in shadow mode should we consider:

- RAG retrieval for policy/training snippets.
- MCP tools for structured access to pay, compliance, and career data.

### 13.7 Risks & Safeguards (Task/DAF Domain)

**Main risks:**

- AI text contradicts deterministic numbers (pay, compliance, promotion).
- Confusing or harsh messaging for Group B staff.
- Hallucinated policy rules ("you lost your stipend because X" when not true).

**Safeguards:**

- AI outputs never used to calculate anything; they only explain.
- Explanations must always be passed real numbers from:
  - PayCalculationService, ReleaseEngine, ComplianceCalculator, CareerLevelService.
- Optionally:
  - Validate AI text against deterministic values (e.g. if AI mentions 20,000 KES but actual is 19,500, discard and fall back).
- All critical AI features can be turned off via settings flags.
- For Group B:
  - Tone requirements enforced in prompt templates: coach first, clear but non-shaming, English + simple Swahili.

**Status (AI Layer – Task/DAF):**

- **Design:** This section defines the architecture and boundaries for AI in Task/Pay/DAF.
- **Implementation:** First target is A1 – Pay Explanations in shadow mode, followed by A2 – DAF Focus and A3 – Career/Quality coaching, all behind feature flags and with full backward compatibility.

---

## 14. Document Maintenance

This is THE master document. When making changes:

Update this document first – Adjust sections under:

Target Architecture

Implementation Status

Test Results & Status

Next Steps & Roadmap

Policy Knobs

Update test results – Add to “Test Results and Status” section.

Update file locations – Add to “Key Files and Locations” section.

Update roadmap – Add to “Next Steps & Roadmap” and “Implementation Roadmap & Open Questions”.

Do NOT create new architecture docs – Update this one instead.

**Status:**  

- ✅ Phase T2, P1, P2, P3 **Complete**  

- ✅ Phase P4 **Complete** – evidence-based quality & real metrics  

- ✅ Phase P5 Part 3 **Complete** – PromotionExecutionService (shadow + execution)  

- ✅ Phase P6 **Complete** – EarningsEngine & ReleaseEngine extraction  

- ✅ Phase P7 **Complete** – LoyaltyFundService (allocation + vesting)  

- 🎯 **Next technical focus:** Phase P8 (DAF UI implementation) or Phase P9 (Regional PayPolicy rollout)  



**Last Session:**  

- Updated Master Document to reflect P6 and P7 completion.  

- Phase P6: Extracted `EarningsEngine` (pure calculation) and `ReleaseEngine` (release decisions) from `PayCalculationService`.  

- Phase P7: Implemented `LoyaltyFundService` with allocation rates (1-3%), vesting schedule, and balance tracking.  

- All services integrated and backward compatible.  

- All tests passing for P6 and P7.



**Next Step (for future sessions):**  

- **Phase P8 – DAF UI Implementation**: Build API endpoints and front-end components for career progression visualization, earned/released/locked display, and "what to focus on" recommendations.  

- **Phase P9 – Regional PayPolicy Rollout**: Design and implement multi-region pay policy system with local currencies and region-specific safety nets.



**Master Document:**  

This file is the **single source of truth** for the CODA Task, Pay, Career, DAF & Regional Pay System.  

Always update this document first when architecture or behaviour changes.