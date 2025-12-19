# CODA – Task, Pay, Career & DAF System  

**Master Architecture & Implementation Document – Dec 2025**  

**Branch:** `25.12_CODA_DEV_CM`  

> **🎯 SINGLE SOURCE OF TRUTH** - This document is the complete reference for CODA's Task, Pay, Career, and DAF systems.  
> **Use this document to start a new chat session and pick up where we left off.**

---

## 📋 Table of Contents

1. [High-Level Goals](#0-high-level-goals)
2. [Domain Overview & Current State](#1-domain-overview--current-state-dec-2025)
3. [Target Architecture](#2-target-architecture)
   - [Service Layers](#22-service-layers)
   - [Group B Career Ladder](#23-group-b-career-ladder-b1-b18)
   - [Stipend & Safety Net](#24-stipend--safety-net--group-b)
   - [Loyalty Fund](#25-loyalty-fund)
   - [DAF UX Expectations](#26-daf-ux-expectations)
4. [Implementation Status](#3-implementation-status)
5. [Key Files and Locations](#4-key-files-and-locations)
6. [Technical Patterns and Constraints](#5-technical-patterns-and-constraints)
7. [Test Results and Status](#6-test-results-and-status)
8. [Next Steps & Roadmap](#7-next-steps--roadmap)
9. [Implementation Roadmap & Open Questions](#8-implementation-roadmap--open-questions)
10. [Glossary](#9-glossary)
11. [Quick Reference](#10-quick-reference)

---

## 0. High-Level Goals

CODA has struggled for 10+ years with:

- **Fairness in pay vs performance** - Hard to align pay with actual work quality
- **People gaming the system** - Working late in the cycle to meet thresholds
- **Harsh-feeling delays and gates** - 45+ day delay, 33% rule feels punitive
- **Extremely pay-sensitive Group B staff** - Small changes have big impact

We are now designing a **long-term**, **AI-assisted**, **self-regulating** system that:

1. Keeps **Task & ActivityType** as the source of truth for work done.
2. Separates **what is earned** from **what is released** (cash paid).
3. Provides a **deep career ladder**, especially for Group B (3k → 30k).
4. Uses the **DAF UI as the behaviour engine** (clear progress toward next raise).
5. Avoids salary cuts; instead uses **promotion freezes, stipend adjustments, and visibility**.
6. Stays **backward-compatible**, minimizing migrations and breaking changes.

---

## 1. Domain Overview & Current State (Dec 2025)

### 1.1 Employee Groups

We conceptually divide CODA employees into three groups:

- **Group A – Grads / Skilled / Remote**
  - Degree or higher, can be remote, multiple gigs.
  - Upper pay cap ≈ 100k KES for top performers.
  - Strong emphasis on evidence & quality, often billable.

- **Group B – Core Staff (onsite, HS or below)**
  - Onsite, often >40, CODA is main income.
  - Cost-centre & internal work (cleaning, ops, internal processes).
  - Start ≈ 3k KES, target cap ≈ 30k KES.
  - Highly pay-sensitive; +1k steps are big motivators.
  - Limited English; DAF labels are English but behaviour may be explained in Swahili.

- **Group C – High school trainees**
  - In school, CODA sponsors upkeep & education.
  - Mostly unpaid salary, but supported via other mechanisms.
  - Future path into Group B or A.

These groups **exist as business logic** and will be represented in code via a `group` field in an employee/career state model.

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
    - Today it acts more like a hard gate on pay; in the target system it becomes a **release gate**, not an "earnings eraser".

**Finance integration**

- Finance uses:
  - `TaskHistory`
  - `calculate_total_pay` (legacy) or `PayCalculationService` (new)
- For:
  - Salary dashboards
  - Budgeting and forecasting.

---

## 2. Target Architecture

We are moving toward a **service-oriented internal architecture** with clear responsibility boundaries. The key concept: **PayCalculationService is the orchestrator** that calls specialized engines.

### 2.1 Key Concepts Per Month (N)

For each employee and month **N**:

- `earned_amount_N`
  - Objective value of the work done in month N.
  - Comes from Tasks/TaskHistory + ActivityType + bonuses/deductions (EarningsEngine).

- `released_amount_N`
  - Cash actually paid out so far for month N (could be at N+1, N+2…).

- `locked_amount_N`
  - `earned_amount_N - total_released_for_month_N`.
  - Employee's money that is not yet released (gated by compliance/quality rules).

Additional pay elements (decided at *release* time):

- `stipend_release` (Group B, tenured only)
- `safety_net_topup` (Group B, attendance-based minimum)

These are separate from `earned_amount_N` and only decided when we release pay.

---

### 2.2 Service Layers

The target architecture uses a **service-oriented design** with clear responsibility boundaries. `PayCalculationService` acts as the orchestrator that coordinates specialized engines.

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
```

**Current Implementation:**
- This logic currently lives in `PayCalculationService._calculate_base_pay()`, `_calculate_bonuses()`, and `_calculate_deductions()`.
- Future: Extract into dedicated `EarningsEngine` class for clearer separation.

#### 2.2.2 ReleaseEngine

Decides how much of `earned_amount_N` to release based on compliance, quality gates, and policy.

**Responsibilities:**

- Check compliance for month N+1 (33% rule).
- Check quality gates (evidence coverage, checklist completion).
- Calculate stipend (if eligible - Group B, tenured only).
- Calculate safety net topup (Group B only - minimum pay if attended enough days).
- Produce release decision with explanations for DAF UI.

**Interface:**

```python
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
    ) -> dict:
        return {
            "earned_amount": ...,        # from EarningsEngine
            "released_now": ...,         # base release from earned if compliant
            "locked_remaining": ...,      # earned - released_now
            "stipend_release": ...,       # compliance-scaled stipend (Group B, tenured)
            "safety_net_topup": ...,     # minimum pay topup (Group B, attendance-based)
            "explanations": [...],        # human-readable messages for DAF/HR dashboards
            "compliance": {...},
            "quality_gates": {...},
        }
```

**Helper Methods:**
- `calculate_release_factor_from_compliance()` - 33% rule & beyond
- `calculate_stipend()` - Group B, tenured, compliance-scaled
- `calculate_safety_net()` - minimum pay if attended enough days (Group B)

**Current Implementation:**
- This logic currently lives in `PayCalculationService._calculate_release_breakdown()`.
- Phase P3 implements the core release logic with compliance and stipend.
- Future: Extract into dedicated `ReleaseEngine` class for clearer separation.

#### 2.2.3 CareerLevelService (Future)

Manages career progression, especially for Group B (B1-B18 ladder).

**Responsibilities:**

- Track career level progression (current_level_code, date_at_level).
- Calculate promotion eligibility based on:
  - Months at current level
  - Average compliance (last 3 months)
  - Average quality score (last 3 months)
  - Average attendance days
  - Extra requirements (mentoring, QA tasks for B16-B18)
- Calculate progress to next level (0-1 scale for DAF visualization).
- Manage promotion freezes (alternative to salary cuts).
- Provide DAF UI data for progress visualization.

**Group B Ladder (B1-B18):**
- **B1-B10:** Foundation / Process Operators (3k → 15k KES)
- **B11-B15:** Senior Operators (17k → 25k KES)
- **B16-B18:** Core Anchors (27k → 30k KES)

**Promotion Logic:**
- Requires meeting next level's thresholds:
  - `months_at_level >= next.min_months`
  - `avg_compliance >= next.min_compliance`
  - `avg_quality >= next.min_quality`
  - `avg_attendance >= next.min_attendance_days`
  - Extra requirements satisfied (for B16-B18)
- **No demotions:** Never lower current_level_code
- **Promotion freezes:** When performance drops, promotions freeze but base pay remains

**Status:** Not yet implemented (future phase - Phase P5).

#### 2.2.4 PerformanceMetricsService (Future)

Aggregates performance metrics for promotion and release decisions.

**Responsibilities:**

- Integrate ComplianceCalculator for monthly compliance.
- Track attendance stats (from existing attendance system / Task presence).
- Integrate ChecklistEvaluationService for quality scores.
- Provide window metrics (last 3 months averages).

**Interface:**

```python
class PerformanceMetricsService:
    def get_month_metrics(self, employee, month) -> dict:
        return {
            "compliance": ...,           # from ComplianceCalculator
            "checklist_quality_score": ...,  # from ChecklistEvaluationService
            "attendance_days": ...,      # from attendance tracking
            "total_points": ...,
            "total_max_points": ...,
        }
    
    def get_window_metrics(self, employee, months_back=3) -> dict:
        return {
            "avg_compliance": ...,
            "avg_quality": ...,
            "avg_attendance": ...,
        }
```

**Status:** Not yet implemented (future phase).

#### 2.2.5 ChecklistEvaluationService (Future)

Evaluates task quality based on evidence and checklist completion.

**Responsibilities:**

- Use TaskLinks & ActivityType to determine required evidence.
- Score tasks based on checklist completion.
- Provide per-task and per-month quality scores.
- Integrate with ReleaseEngine for quality gates.

**Status:** Not yet implemented (future phase).

#### 2.2.6 LoyaltyFundService (Future)

Manages long-term loyalty/retirement accumulation.

**Responsibilities:**

- Compute small percentage (1-3%) of released amounts as loyalty fund.
- Track per-employee balance and transactions.
- Handle payout conditions (5-year horizon, completed cycles, exit policy).

**Interface:**

```python
class LoyaltyFundService:
    def allocate(self, employee, released_now: Decimal) -> AllocationResult:
        # Returns updated balance, allocated amount this month, etc.
        rate = get_loyalty_rate(employee.group, employee.level_code)
        # Example: 1% at B1-B5, 2% at B6-B12, 3% at B13-B18
        allocation = released_now * rate
        # Store transaction, update balance
        return AllocationResult(...)
```

**Status:** Not yet implemented (future phase).

#### 2.2.7 PayCalculationService (Orchestrator)

Reframed as a thin orchestrator that coordinates all engines.

**Current Implementation (Phase P1/P2/P3):**
- Encapsulates earnings calculation (will become EarningsEngine).
- Encapsulates release calculation (will become ReleaseEngine).
- Returns structured payslip data.

**Target Implementation (Future):**

```python
class PayCalculationService:
    def calculate_payslip(self, employee, month_to_pay, month_now=None):
        # month_to_pay: the earned month (N)
        # month_now: the current month (N+1 etc) – defaults to "now"
        
        earned = EarningsEngine().calculate_earned(employee, month_to_pay)
        metrics_now = PerformanceMetricsService().get_month_metrics(employee, month_now)
        metrics_earned = PerformanceMetricsService().get_month_metrics(employee, month_to_pay)
        career_state = CareerLevelService().get_state(employee)
        
        release = ReleaseEngine().compute_release(
            employee,
            month_to_pay,
            month_now,
            earned,
            metrics_now,
            metrics_earned,
            career_state,
        )
        
        loyalty = LoyaltyFundService().allocate(employee, release["released_now"])
        
        return {
            "employee_id": employee.id,
            "month_earned": month_to_pay,
            "earnings": earned,
            "release": release,
            "career": {
                "group": career_state.group,
                "level": career_state.current_level_code,
                "next_level": career_state.next_level_code,
                "progress_to_next": CareerLevelService().get_progress_to_next_level(employee, month_now),
                "loyalty_fund_balance": loyalty.balance_after,
            },
        }
```

**Status:** Phase P1/P2/P3 complete. Future: Refactor to use extracted engines.

---

### 2.3 Group B Career Ladder (B1-B18)

Group B is CORE_STAFF with a long-term ladder 3k → 30k in small steps.

**Ladder Structure:**

- **B1-B10:** Foundation / Process Operators (3k → 15k KES)
- **B11-B15:** Senior Operators (17k → 25k KES)
- **B16-B18:** Core Anchors (27k → 30k KES)

**Config Structure (Python dict):**

Location: `coda/config/career_levels.py`

```python
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
```

**Note:** These numbers are tunable knobs, not final gospel.

**Promotion Logic:**

Promotion requires meeting the next level's thresholds:

```python
if (months_at_level >= next.min_months
    and avg_compliance >= next.min_compliance
    and avg_quality >= next.min_quality
    and avg_attendance >= next.min_attendance_days
    and extra_requirements_satisfied):
    PromotionDecision = READY
else:
    PromotionDecision = NOT_YET or FROZEN
```

**Progress to Next Level (0-1 scale for DAF):**

```python
progress = min(
    avg_compliance / next.min_compliance,
    avg_quality / next.min_quality,
    months_at_level / next.min_months,
    avg_attendance / next.min_attendance_days,
)
progress = max(0.0, min(1.0, progress))
```

This gives a natural "bottleneck" – the weakest dimension limits progress.

**No Demotions:**
- We never lower `current_level_code`
- When performance drops: Promotions freeze, but base pay of current level remains
- Stipend, bonuses, and release factor may be reduced instead

---

### 2.4 Stipend & Safety Net – Group B

#### 2.4.1 Stipend (Tenured, Group B Only)

**Business Rules:**

- Applies only to: `group == "B"` AND `is_tenured == True` (e.g., ≥12 months at CODA)
- Stipend is **not salary** - it is a release-time safety top-up based on current month's compliance & quality
- **Not part of earned_amount_N** - calculated at release time

**Formula:**

```python
def calculate_stipend(employee, metrics_now, career_state):
    if not (career_state.group == "B" and career_state.is_tenured):
        return 0
    
    base_stipend = 2500  # KES
    c = metrics_now["compliance"]
    q = metrics_now["checklist_quality_score"]
    
    # Compliance-based factor
    if c < 0.33:
        factor = 0.0  # 0% stipend
    elif c < 0.665:
        factor = 0.5  # 50% stipend
    else:
        factor = 1.0  # 100% stipend
    
    # Quality cap
    if q < 0.5:
        factor = min(factor, 0.5)
    
    return int(base_stipend * factor)
```

**Current Implementation (Phase P3):**
- Basic stipend calculation implemented in `PayCalculationService._calculate_stipend()`
- Uses compliance scaling: `stipend = base_stipend * ((compliance_rate - 33) / 67)`
- Quality cap not yet implemented (Phase P4)

#### 2.4.2 Safety Net (Never Zero if They Showed Up)

**Principle:**
- Group B should only get 0 pay if they never showed up at all in the earned month
- Safety net ensures a minimum cash if they attended enough days

**Parameters (tunable):**
- `MIN_ATTENDANCE_FOR_SAFETY_NET` (e.g., 10-12 days in earned month)
- `SAFETY_NET_MIN_PAY` (e.g., 1,500-2,000 KES)

**Formula:**

```python
def calculate_safety_net(employee, earned_month, release, metrics_earned_month):
    min_attendance = 10  # days
    min_pay = 1500  # KES
    
    if metrics_earned_month["attendance_days"] < min_attendance:
        return 0
    
    total_current = release["released_now"] + release["stipend_release"]
    if total_current >= min_pay:
        return 0
    
    return min_pay - total_current
```

**Status:** Not yet implemented (future phase).

---

### 2.5 Loyalty Fund

**Concept:**
- Every month, a small % of `released_now` is allocated to a Loyalty Fund
- Visible on DAF as "Loyalty/Retirement Fund"
- Payout after certain conditions (e.g., 5 years at CODA and completion of certain career cycles)

**Example Logic:**

```python
def get_loyalty_rate(group, level_code) -> float:
    # Example: 1% at B1-B5, 2% at B6-B12, 3% at B13-B18
    if group == "B":
        if level_code in ["B1", "B2", "B3", "B4", "B5"]:
            return 0.01  # 1%
        elif level_code in ["B6", "B7", "B8", "B9", "B10", "B11", "B12"]:
            return 0.02  # 2%
        else:  # B13-B18
            return 0.03  # 3%
    return 0.0

def allocate(employee, released_now):
    rate = get_loyalty_rate(employee.group, employee.level_code)
    allocation = int(released_now * rate)
    # Store transaction, update balance
```

**Status:** Not yet implemented (future phase - Phase P7).

---

### 2.6 DAF UX Expectations

The DAF (Daily Activity Form) UI is the **behavior engine** - it drives employee behavior by making progress visible and motivating.

#### 2.3.1 Layout Overview

1. **Month selector** - View different months (earned vs release timing)
2. **Career & pay summary card** - Current level, next level, progress bar
3. **Earned vs released vs locked card** - Money breakdown with explanations
4. **Activity list** - Tasks with quality scores and promotion impact
5. **"What to focus on" hints** - Actionable recommendations

#### 2.3.2 Career & Pay Summary (Hero Card)

**Example Display:**
```
[Jane Doe] – CORE_STAFF – B4 (Process Operator I)
Base pay: 6,000 KES
Next level: B5 – 7,000 KES
Loyalty fund: 4,200 KES (available from 2027)

Progress to next raise
[██████████████--------] 65%
"Estimated 2–3 months at your current pace."

✅ At level B4 for 3 months (needs ≥3).
✅ Average compliance (last 3 months): 57% (needs ≥55%).
⚠️ Checklist quality (last 3 months): 52% (needs ≥60%).
✅ Attendance: 19 days/month (needs ≥18).
```

**Data Source:** `CareerLevelService.get_progress_to_next_level()`

#### 2.3.3 Earned vs Released vs Locked (Money Card)

**Example Table:**
```
"Last month's money (Earned in Nov, paid in Dec)"

Item                    Amount (KES)
Earned from tasks       22,300
Released this month     18,000
Still locked            4,300
Stipend (Dec)           1,500
Safety net top-up       0
─────────────────────────────────
Total pay this month    19,500
```

**Human Explanation:**
- "Your current month compliance is 68%, so you unlocked 80% of last month's earnings and got 60% of your maximum stipend."
- If below threshold: "You are at 21% completion. You need at least 33% to unlock the rest of your November money."

**Data Source:** `PayCalculationService.calculate_payslip() → release + earnings`

#### 2.3.4 Activity List with Quality & Promotion Impact

**Table Format:**
```
Activity        Points      Evidence    Quality    Promotion impact
BI Session      40 / 60     ✔           78%        ⭐ High
Cleaning Round  26 / 40     !           45%        ◔ Medium
Training Task   10 / 20     ✖           20%        ✖ Low
```

- **Points:** Current vs target for the month
- **Evidence:** ✔ complete, ! partial, ✖ missing
- **Quality:** 0-100% from ChecklistEvaluationService
- **Promotion impact:** Based on promotion_weight from checklist config

**Clicking a row opens side panel:**
- Checklist items (with ticks)
- Evidence links (documents, recordings)
- Plain-language hint: "To get full points from BI Sessions and help your next raise, always finish the summary."

#### 2.3.5 "What to Focus on This Month"

**Short, friendly text (Swahili-localized for Group B):**

```
To move from B4 (6,000 KES) to B5 (7,000 KES), try:

• Keep your compliance above 55%.
• Improve your checklist score to 60%+ (finish summaries & upload photos).
• Attend at least 18 days each month.
```

**Data Source:** `PromotionDecision + ladder config`

This drives behavior by making progress visible and motivating.

---

## 3. Implementation Status

### 3.1 Implementation Flow Summary

```
Phase T2: ActivityType System
├── ✅ Models: TaskSubcategory, ActivityType
├── ✅ Seeding: 15 canonical ActivityTypes
├── ✅ Service: ActivityTypeApplicationService
├── ✅ Integration: Task.get_pay uses ActivityType
└── ✅ Tests: 49 tests passing

Phase P1: PayCalculationService
├── ✅ Service: PayCalculationService created
├── ✅ Encapsulates: Base pay, bonuses, deductions
├── ✅ Backward compatible: Uses existing utilities
└── ✅ Tests: 7 integration tests passing

Phase P2: Payslip View Refactoring
├── ✅ View: payslip() uses PayCalculationService
├── ✅ Thin controller pattern
├── ✅ Template compatibility maintained
└── ✅ Tests: Verified in integration tests

Phase P3: Earned vs Released Separation
├── ✅ Extended: PayCalculationService with release breakdown
├── ✅ Integration: ComplianceCalculator for 33% rule
├── ✅ Feature: Base stipend calculation
├── ✅ Configuration: Django settings for stipend
└── ✅ Tests: 10 tests passing

Phase P4: Quality Gates (Future)
└── ⏳ Not yet implemented

Phase P5: CareerEngine (Future)
└── ⏳ Not yet implemented
```

### 3.2 Current Status

| Phase | Status | Tests | Notes |
|-------|--------|-------|-------|
| T2 | ✅ Complete | 49 passing | ActivityType system |
| P1 | ✅ Complete | 7 passing | PayCalculationService |
| P2 | ✅ Complete | Included in P1 tests | View refactoring |
| P3 | ✅ Complete | 10 passing | Earned/released, stipend |
| P4 | ⏳ Future | - | Quality gates |
| P5 | ⏳ Future | - | CareerEngine |

---

### 3.3 What Has Been Completed

#### Phase T2: ActivityType System (Complete)

1. **Models Added:**
   - `TaskSubcategory` model in `coda/management/models.py`
   - `ActivityType` model with fields:
     - `name`, `slug`, `description`
     - `department` (FK to Department)
     - `category` (FK to TaskCategory)
     - `subcategory` (FK to TaskSubcategory)
     - `unit_type` (session, hour, meeting, work_block, item, approved_video, candidate_cycle, month, requirement, other)
     - `unit_rate`, `monthly_target_units`, `points_per_unit`
     - `is_billable`, `is_active`
   - `Task` model extended with:
     - `activity_type` (FK to ActivityType, nullable)
     - `is_client_project` (Boolean)

2. **Seeding:**
   - Management command: `python manage.py seed_activity_types`
   - Seeds 15 canonical ActivityTypes idempotently
   - Location: `coda/management/management/commands/seed_activity_types.py`

3. **Services:**
   - `ActivityTypeApplicationService` in `coda/management/services/activity_type_service.py`
     - `apply_to_task()` - applies ActivityType defaults to Task
     - `find_activity_type_by_name()` - finds by name, legacy mapping, or slug

4. **Integration:**
   - `Task.get_pay` prefers ActivityType-based calculation when available, falls back to legacy
   - Admin flows updated (`TrainingAdmin`, `TaskAdmin`, `create_task` helper)
   - All backward compatible

5. **Tests:**
   - 49 tests passing for ActivityType model, seeding, service, and admin integration
   - Test files:
     - `coda/management/tests/test_activity_type_model.py`
     - `coda/management/tests/test_activity_type_seeding.py`
     - `coda/management/tests/test_activity_type_service.py`
     - `coda/management/tests/test_admin_activity_type_integration.py`

#### Phase P1: PayCalculationService (Complete)

1. **Service Created:**
   - File: `coda/management/services/pay_calculation_service.py`
   - Class: `PayCalculationService`
   - `BASE_CURRENCY = "KES"`
   - Main method: `calculate_payslip(employee, target_month, target_year, pay_type, enforce_evidence=False, display_currency=None, include_release_breakdown=False)`

2. **Service Structure:**
   - Encapsulates all payslip calculation logic:
     - Base pay from Tasks/TaskHistory
     - Bonuses (EOM, holiday, late-night, login bonus, laptop bonus)
     - Deductions (tax, loan, laptop savings, food, maintenance, health)
   - Returns structured dictionary with:
     - `base_pay` - tasks queryset and total
     - `bonuses` - detailed bonus breakdown
     - `deductions` - detailed deduction breakdown
     - `summary` - gross_pay, net_pay, total_bonus, total_deductions
     - `metadata` - employee info, period, currency
     - `tasks` - queryset for template rendering

3. **Helper Methods:**
   - `_get_user_data()` - gets user profile, loan data, payslip config
   - `_calculate_base_pay()` - uses `payinitial()` utility
   - `_calculate_bonuses()` - uses `bonus()` and `calculate_login_bonus()`
   - `_calculate_deductions()` - uses `deductions()` and `loan_computation()`
   - `_empty_payslip()` - returns empty structure

4. **Backward Compatibility:**
   - Delegates to existing utility functions in `management/utils.py`
   - No model changes
   - No numeric behavior changes
   - All calculations remain identical

#### Phase P2: Payslip View Refactoring (Complete)

1. **View Refactored:**
   - File: `coda/management/views.py`
   - Function: `payslip()` (around line 1012)
   - Now a **thin controller**:
     - Resolves request parameters (employee, selected_month, selected_year, pay_type)
     - Instantiates `PayCalculationService`
     - Calls `service.calculate_payslip(...)`
     - Maps service output to template context
   - **No longer calls** `calculate_total_pay`, `bonus`, `deductions`, `loan_computation`, `lap_save_bonus`, `get_bonus_and_summary`, `calculate_login_bonus` directly

2. **Legacy Helper for Testing:**
   - File: `coda/management/tests/helpers/legacy_payslip_calculator.py`
   - Function: `calculate_legacy_payslip()`
   - Reproduces OLD payslip calculation for regression testing

3. **Integration Tests:**
   - File: `coda/management/tests/test_pay_calculation_service_integration.py`
   - 7 comprehensive test scenarios:
     - Full-time employee with loan, laptop, high performance
     - Contractor, low performance, no loan
     - Below and above EOM threshold (75%)
     - No tasks scenario
     - Detailed bonus/deduction breakdowns
   - All tests assert numeric equality (to 2 decimals) between legacy and new service
   - **Status:** ✅ All 7 tests passing

4. **Test Results:**
   - `python manage.py test management.tests.test_pay_calculation_service_integration --keepdb` → ✅ PASS
   - All existing management tests still passing
   - `python manage.py check` → ✅ 0 issues

#### Phase P3: Earned vs Released Separation (Complete)

1. **Service Extended:**
   - File: `coda/management/services/pay_calculation_service.py`
   - Added `include_release_breakdown` parameter to `calculate_payslip()`
   - New methods:
     - `_calculate_release_breakdown()` - Calculates earned/released/locked amounts
     - `_get_check_month_year()` - Determines Month N+1 for compliance checking
     - `_calculate_stipend()` - Calculates base stipend with compliance scaling

2. **Earned vs Released Logic:**
   - `earned_amount_n` = Net pay from Month N work (TaskHistory snapshot)
   - `released_amount_n` = Portion of Month N earnings actually paid out
   - `locked_amount_n` = `earned_amount_n - released_amount_n`
   - Earnings are **never deleted** - just locked until compliance met

3. **33% Rule Integration:**
   - Uses `ComplianceCalculator` to check Month N+1 compliance
   - Rule active after 15th of current month (`is_rule_active()`)
   - If compliant: Release Month N earnings + stipend
   - If not compliant: Locked until compliance met

4. **Base Stipend:**
   - Safety net for tenured employees (configurable, default: 2,500 KES)
   - Only for employees with tenure >= `PAYROLL_MIN_STIPEND_TENURE_MONTHS` (default: 12 months)
   - Compliance-scaled formula:
     - At 33% compliance → stipend factor = 0
     - At ~66.5% compliance → stipend factor ≈ 0.5
     - At 100% compliance → stipend factor = 1
   - Formula: `stipend = base_stipend_amount * ((compliance_rate - 33) / (100 - 33))`
   - Treated as **release-time component**, not part of Month N earning

5. **Configuration:**
   - Added to `coda/coda_project/coda_settings/base_settings.py`:
     - `PAYROLL_BASE_STIPEND_AMOUNT` (default: 2500.00 KES)
     - `PAYROLL_MIN_STIPEND_TENURE_MONTHS` (default: 12 months)
   - Service-level config (NOT in PayslipConfig yet)

6. **Tests:**
   - File: `coda/management/tests/test_pay_calculation_service_p3.py`
   - 10 comprehensive test scenarios (all passing):
     1. `test_earned_amount_equals_net_pay` - Verifies earned = net pay
     2. `test_compliant_employee_releases_full_amount` - Compliant employees release earnings
     3. `test_non_compliant_employee_locks_amount` - Non-compliant employees lock earnings
     4. `test_stipend_calculation_tenured_employee` - Stipend calculation for tenured
     5. `test_stipend_zero_for_new_employee` - New employees get no stipend
     6. `test_stipend_zero_below_33_percent` - No stipend below 33%
     7. `test_stipend_full_at_100_percent_compliance` - Full stipend at 100%
     8. `test_compliance_data_structure` - Compliance data structure validation
     9. `test_quality_gates_structure` - Quality gates (stub for Phase P4)
     10. `test_backward_compatibility_without_release_breakdown` - Backward compatibility
   - **Status:** ✅ All 10 tests passing
   - **Test Command:** `python manage.py test management.tests.test_pay_calculation_service_p3 --keepdb`

7. **Backward Compatibility:**
   - `include_release_breakdown=False` by default (Phase P1/P2 behavior preserved)
   - All existing numeric calculations remain identical
   - Payslip view continues to work as before
   - No model changes (service-level only)

---

## 4. Key Files and Locations

### Core Services
- `coda/management/services/pay_calculation_service.py` - Main payslip calculation service (P1/P2/P3)
- `coda/management/services/activity_type_service.py` - ActivityType application logic (T2)
- `coda/management/services/compliance_calculator.py` - 33% rule compliance calculation
- `coda/management/services/employee_compliance_service.py` - Compliance service wrapper

### Models
- `coda/management/models.py` - Contains Task, TaskHistory, ActivityType, TaskSubcategory
- `coda/finance/models/core.py` - Contains PayslipConfig
- `coda/shared_core/users.py` - Contains Department, CustomerUser

### Views
- `coda/management/views.py` - Contains refactored `payslip()` view (around line 1012)

### Utilities
- `coda/management/utils.py` - Contains legacy calculation functions:
  - `get_tasks()`, `calculate_total_pay()`, `payinitial()`
  - `bonus()`, `deductions()`, `loan_computation()`
  - `lap_save_bonus()`, `get_bonus_and_summary()`
- `coda/accounts/utils.py` - Contains `calculate_login_bonus()`

### Tests
- `coda/management/tests/test_pay_calculation_service_integration.py` - Phase P1/P2 regression tests (7 tests, all passing)
- `coda/management/tests/test_pay_calculation_service_p3.py` - Phase P3 earned/released tests (10 tests, all passing)
- `coda/management/tests/helpers/legacy_payslip_calculator.py` - Legacy calculator helper for regression testing
- `coda/management/tests/test_activity_type_*.py` - ActivityType tests (4 files, 49 tests, all passing)

### Configuration
- `coda/coda_project/coda_settings/base_settings.py` - Contains stipend configuration (PAYROLL_BASE_STIPEND_AMOUNT, PAYROLL_MIN_STIPEND_TENURE_MONTHS)

---

## 5. Technical Patterns and Constraints

### Import Patterns

- Departments: `from shared_core.users import Department`
- UserProfile: `from accounts.models import UserProfile`
- PayslipConfig: `from finance.models import PayslipConfig`
- Finance services: Use `get_finance_task_service()` helper from `management.services.finance_service_helper`

### Currency

- Base currency: KES (Kenyan Shillings)
- All amounts use `Decimal` for precision
- Currency-aware API structure, but currently KES-only

### Test Patterns

- Use Django's `TestCase`, not pytest
- Use `get_or_create` for TaskCategory to prevent duplicates
- Use `--keepdb` flag for faster test runs
- Compare legacy vs. new calculations to 2 decimal places

### Calculation Formulas

**Legacy Task Pay:**
```
task_pay = (point / mxpoint) * mxearning * late_penalty
```

**ActivityType Task Pay (when activity_type set):**
```
expected_points_for_full_target = monthly_target_units * points_per_unit
max_earning_for_type = unit_rate * monthly_target_units
pay = max_earning_for_type * (task.point / expected_points_for_full_target) * late_penalty
(capped at max_earning_for_type)
```

**Gross Pay:**
```
gross_pay = total_pay + total_bonus + login_bonus
```

**Net Pay:**
```
net_pay = gross_pay - total_deductions
```

**Stipend Formula (Phase P3):**
```
effective_rate = clamp(compliance_rate, 33, 100)
factor = (effective_rate - 33) / (100 - 33)
stipend = base_stipend_amount * factor
```

### Compliance Calculation

- Source: `ComplianceCalculator` in `management/services/compliance_calculator.py`
- Formula: `completion_rate = (total_points / total_max_points) * 100`
- Compliant if: `completion_rate >= 33`
- Rule active: After 15th of current month (`is_rule_active()`)

---

## 6. Test Results and Status

### Phase P1/P2 Integration Tests
- **File:** `test_pay_calculation_service_integration.py`
- **Tests:** 7 scenarios
- **Status:** ✅ All passing
- **Purpose:** Verify backward compatibility (numeric equality with legacy calculations)

### Phase P3 Earned/Released Tests
- **File:** `test_pay_calculation_service_p3.py`
- **Tests:** 10 scenarios
- **Status:** ✅ All passing
- **Purpose:** Verify earned/released separation, compliance integration, stipend calculation

### ActivityType Tests
- **Files:** `test_activity_type_*.py` (4 files)
- **Tests:** 49 scenarios
- **Status:** ✅ All passing
- **Purpose:** Verify ActivityType system integration

### Test Execution
```bash
# Run all Phase P3 tests
python manage.py test management.tests.test_pay_calculation_service_p3 --keepdb

# Run all Phase P1/P2 integration tests
python manage.py test management.tests.test_pay_calculation_service_integration --keepdb

# Run all ActivityType tests
python manage.py test management.tests.test_activity_type_* --keepdb

# Run all management tests
python manage.py test management --keepdb
```

---

## 7. Next Steps & Roadmap

### Phase P4: Quality Gates & Evidence Enforcement (Future)

**Goal:** Evidence enforcement and quality tracking

**Enhancements:**
1. **ChecklistEvaluationService:**
   - Evaluate task quality based on evidence
   - Score tasks based on checklist completion
   - Provide per-task and per-month quality scores

2. **Quality Gates:**
   - Evidence coverage tracking
   - Checklist completion scoring
   - Integration with release logic (affect stipend factor)

3. **Evidence Enforcement:**
   - Require evidence for task completion
   - Link meetings to tasks automatically (MeetingLinkingService)
   - Track evidence quality scores

### Phase P5: CareerLevelService & Group B Ladder (Future)

**Goal:** Career progression system, especially for Group B (B1-B18 ladder)

**Enhancements:**
1. **Group B Ladder Configuration:**
   - B1-B10: Foundation / Process Operators (3k → 15k KES)
   - B11-B15: Senior Operators (17k → 25k KES)
   - B16-B18: Core Anchors (27k → 30k KES)
   - Config file: `coda/config/career_levels.py` with `GROUP_B_LADDER`

2. **EmployeeCareerState Model:**
   - Track: `user`, `group`, `current_level_code`, `date_at_level`, `loyalty_fund_balance`, `is_tenured`
   - Management command to seed current levels from existing salary data

3. **CareerLevelService:**
   - `get_state(employee)` - Get current career state
   - `evaluate_promotion(employee, month)` - Check promotion eligibility
   - `get_progress_to_next_level(employee, month)` - Calculate 0-1 progress for DAF

4. **Promotion Logic:**
   - Requires: months_at_level, avg_compliance, avg_quality, avg_attendance, extra_requirements
   - **No demotions:** Never lower current_level_code
   - **Promotion freezes:** When performance drops, freeze promotions but keep base pay

5. **DAF UX Integration:**
   - Show progress toward next raise (progress bar)
   - Visualize career ladder position
   - Display compliance and quality status
   - "What to focus on" recommendations

### Phase P6: Service Extraction & Refactoring (Future)

**Goal:** Extract engines from PayCalculationService for clearer separation

**Enhancements:**
1. **EarningsEngine:**
   - Extract `_calculate_base_pay()`, `_calculate_bonuses()`, `_calculate_deductions()`
   - File: `coda/management/services/earnings_engine.py`
   - Clean interface: `calculate_earned(employee, month)`

2. **ReleaseEngine:**
   - Extract `_calculate_release_breakdown()` into dedicated service
   - File: `coda/management/services/release_engine.py`
   - Add safety net topup logic (Group B)
   - Integrate quality gates
   - Add explanation messages for DAF

3. **PerformanceMetricsService:**
   - File: `coda/management/services/performance_metrics_service.py`
   - Integrate ComplianceCalculator, ChecklistEvaluationService, attendance tracking
   - Provide `get_month_metrics()` and `get_window_metrics()`

4. **PayCalculationService Refactor:**
   - Become thin orchestrator
   - Call: EarningsEngine, PerformanceMetricsService, CareerLevelService, ReleaseEngine, LoyaltyFundService
   - Preserve existing API for backward compatibility

### Phase P7: LoyaltyFundService (Future)

**Goal:** Long-term loyalty/retirement accumulation

**Enhancements:**
1. **LoyaltyFundService:**
   - File: `coda/management/services/loyalty_fund_service.py`
   - Compute 1-3% of released amounts (rate based on group/level)
   - Track per-employee balance and transactions
   - Model: `LoyaltyFundTransaction` (optional)

2. **Payout Rules:**
   - After 5 years at CODA
   - After completing certain career cycles
   - Exit policy (partial vs full loss on early exit)

### Phase P8: DAF UI Implementation (Future)

**Goal:** Full DAF UX with career progression visualization

**Enhancements:**
1. **API Endpoint:**
   - `/api/daf/summary?month=YYYY-MM&employee_id=...`
   - Returns: Career summary, progress, earned/released/locked, activity list, focus recommendations

2. **Front-end Components:**
   - Progress bar for next level
   - Career & pay summary card
   - Earned vs released vs locked card
   - Activity list with quality & promotion impact
   - "What to focus on" hints
   - Localizable strings (English + Swahili)

---

## 8. Implementation Roadmap & Open Questions

### 8.1 Foundation Services (Phase P4-P7)

**Suggested sequence of technical tasks:**

1. **Create Config Module:**
   - `coda/config/career_levels.py` - Add `GROUP_B_LADDER`
   - `coda/config/activity_checklists.py` - Add `ACTIVITY_CHECKLIST_CONFIG`

2. **Implement EarningsEngine:**
   - Location: `coda/management/services/earnings_engine.py`
   - Wrap existing logic from `PayCalculationService` / `Task.get_pay`
   - Provide `calculate_earned(employee, month)`

3. **Implement ChecklistEvaluationService:**
   - Location: `coda/management/services/checklist_evaluation_service.py`
   - Use TaskLinks & ActivityType names and `ACTIVITY_CHECKLIST_CONFIG`
   - Provide per-task & per-month quality scores

4. **Implement PerformanceMetricsService:**
   - Location: `coda/management/services/performance_metrics_service.py`
   - Integrate: ComplianceCalculator, ChecklistEvaluationService, attendance tracking
   - Provide: `get_month_metrics()`, `get_window_metrics()`

5. **Introduce EmployeeCareerState Model:**
   - New model: `coda/management/models/employee_career_state.py`
   - Fields: `user`, `group`, `current_level_code`, `date_at_level`, `loyalty_fund_balance`, `is_tenured`
   - Management command: Seed `current_level_code` based on current salary & business rules

6. **Implement CareerLevelService:**
   - Location: `coda/management/services/career_level_service.py`
   - Methods: `get_state()`, `evaluate_promotion()`, `get_progress_to_next_level()`

7. **Implement LoyaltyFundService:**
   - Location: `coda/management/services/loyalty_fund_service.py`
   - Possibly new model: `LoyaltyFundTransaction`

8. **Implement ReleaseEngine:**
   - Location: `coda/management/services/release_engine.py`
   - Encapsulate: 33% rule, stipend logic, safety net logic, locked vs released tracking

9. **Refactor PayCalculationService:**
   - Make it call: EarningsEngine, PerformanceMetricsService, CareerLevelService, ReleaseEngine, LoyaltyFundService
   - Preserve existing API for callers

### 8.2 Rollout Plan

**Phase 0 – Shadow Mode (Internal Only):**
- Implement all services without changing actual payouts
- Log new vs old pay calculations for several months
- Validate fairness and behavior

**Phase 1 – DAF UX (Read-Only New Logic):**
- For Group B users: Show "Career & Progress" panel
- Show "Earned vs Released vs Locked" card using new logic
- Finance & actual payout still uses old `calculate_total_pay`
- HR can validate fairness

**Phase 2 – Switch Payout Logic for Group B:**
- Finance starts using `PayCalculationService` (new orchestrator) for Group B
- Keep old totals visible in internal dashboards for cross-checking

**Phase 3 – Extend to Group A & C:**
- Define `GROUP_A_LADDER` and `GROUP_C_LADDER`
- Group A: Fewer levels, bigger jumps, aggressive bonuses, strict evidence gates
- Group C: Training levels, mainly non-cash support, path to A/B

### 8.3 Open Questions / Policy Knobs

These are **business decisions**, not coding:

1. **Exact Ladder Values:**
   - Are B1-B18 pay levels final?
   - Do we need more granular levels or fewer?

2. **Tenure Definition for `is_tenured`:**
   - X months at CODA?
   - Or reaching a certain level (e.g., B4/B5)?

3. **Compliance and Quality Thresholds:**
   - Are the proposed thresholds realistic vs current performance?
   - Should we tune them so a "good, not superstar" advances every 6-9 months?

4. **Quality Impact:**
   - At which point does low quality:
     - Only slow promotion?
     - Also cut stipend?
     - Or block release (beyond 33% rule)?

5. **Safety Net Minimum Values:**
   - Exact `SAFETY_NET_MIN_PAY` (1.5k? 2k?)
   - Exact `MIN_ATTENDANCE_FOR_SAFETY_NET` (10? 12?)

6. **Loyalty Fund Payout Rules:**
   - After 5 years?
   - After completing certain levels?
   - What happens on early exit (partial vs full loss)?

7. **Group A & C Ladders:**
   - Group A: How aggressive to be with bonuses / penalties?
   - Group C: When to transition them into proper ladders?

---

## 9. Glossary

**DAF** – CODA's main employee dashboard (Day Activity Form / Daily Activity Form).

**Task** – An atomic piece of work for the current month.

**TaskHistory** – Monthly snapshot of tasks; used for payroll and finance.

**ActivityType** – Canonical classification of activities with rates and targets.

**Earned amount** – Objective value of work done in month N (from tasks & rules).

**Released amount** – Cash actually paid out so far for month N.

**Locked amount** – Earned but unreleased money (due to gates).

**Stipend** – Tenured Group B top-up based on current compliance & quality.

**Safety net** – Attendance-based minimum cash to avoid zero pay when they did show up.

**Career level** – Code like B4, A2, etc., representing salary band and expectations.

**Loyalty fund** – Long-term savings/retirement balance funded by small % of releases.

**33% Rule** – Employees must reach 33% completion of current tasks by 15th of new month for last month's pay to be released.

**Promotion freeze** – When performance drops, promotions are frozen but base pay remains (alternative to salary cuts).

---

## 10. Quick Reference

### Commands

```bash
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
```

### Important Constraints

1. **No Model Changes in Phase P3:**
   - Do not add fields to PayslipConfig
   - Do not create MonthlyEarningsSnapshot model
   - Focus on service-level logic only

2. **Backward Compatibility:**
   - All existing numeric calculations must remain identical
   - Payslip view must continue to work as before
   - Finance integration unchanged for now

3. **Configuration:**
   - Stipend parameters in Django settings (NOT PayslipConfig yet)
   - Pattern: `PAYROLL_BASE_STIPEND_AMOUNT = Decimal('2500.00')`

---

## 📝 Document Maintenance

**This is THE master document.** When making changes:

1. **Update this document first** - Add to "Implementation Status" section
2. **Update test results** - Add to "Test Results and Status" section
3. **Update file locations** - Add to "Key Files and Locations" section
4. **Update roadmap** - Add to "Next Steps & Roadmap" section

**Do NOT create new documents** - Update this one instead.

---

## 🔗 Related Documentation (Reference Only)

> **Note:** This master document is the single source of truth. Other documents are for reference only.

- **Phase P3 Design:** `docs/03_IMPLEMENTATION/PAY_SYSTEM_PHASE_P3_33_RULE_BASE_STIPEND_DESIGN.md` - Detailed design specifications
- **Task System Analysis:** `docs/TASK_SYSTEM_ANALYSIS_REPORT.md` - Overall task system analysis
- **Payslip Analysis:** `docs/PAYSLIP_PAYROLL_ANALYSIS_REPORT.md` - Payslip system analysis
- **ActivityType T2:** `docs/03_IMPLEMENTATION/TASK_SYSTEM_PHASE_T2_STEP_1.3_COMPLETE.md` - ActivityType system completion

---

**Status:** ✅ Phase T2, P1, P2 & P3 Complete | 🎯 Ready for Phase P4  
**Last Session:** Phase P3 implementation complete - earned/released separation, stipend calculation, compliance integration  
**Next Step:** Phase P4 - Quality gates and evidence enforcement (future enhancement)  
**Master Document:** This file is the single source of truth for CODA Task, Pay, Career & DAF System

