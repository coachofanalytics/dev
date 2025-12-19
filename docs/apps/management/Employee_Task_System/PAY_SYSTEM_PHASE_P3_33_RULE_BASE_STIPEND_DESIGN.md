# CODA Pay System - Complete Documentation

**Date:** December 2024 - December 2025  
**Branch:** `25.12_CODA_DEV_CM`  
**Status:** Phase P1 ✅ Complete | Phase P2 ✅ Complete | Phase P3 🟡 Design

**Note:** This document consolidates information from:
- `PAY_CALCULATION_SERVICE_P1.md` (Phase P1 - Service Creation)
- `PAY_SYSTEM_PHASE_P2_PAYSLIP_VIEW_REFACTOR.md` (Phase P2 - View Refactoring)
- `QUICK_START_PROMPT.md` (Quick reference for Phase P3)
- `COMPREHENSIVE_CONTEXT_PROMPT.md` (Full context for pay system)
- Pay System Phase P3 (33% Rule, Base Stipend Design - current)

---

## Phase P1: PayCalculationService Creation ✅

**Date:** December 2024  
**Status:** ✅ Service Created

### Goal
Introduce a unified `PayCalculationService` as the single source of truth for payslip computation, while keeping **all current numeric behavior identical** and **without changing any database models**.

### What Was Implemented

#### 1. PayCalculationService Created

**File:** `coda/management/services/pay_calculation_service.py`

A comprehensive service class that encapsulates all payslip calculation logic:

- **Base Pay Calculation**: From Tasks/TaskHistory using existing `get_tasks()` and `calculate_total_pay()`
- **Bonuses**: EOM, holiday, late-night, login bonus, laptop bonus
- **Deductions**: Tax (KRA), loan, laptop savings, food, maintenance, health
- **Structured Output**: Currency-aware API that returns organized payslip data

#### 2. Service Structure

```python
class PayCalculationService:
    BASE_CURRENCY = "KES"
    
    def calculate_payslip(
        self,
        employee,
        target_month: int,
        target_year: int,
        pay_type: str = "task_payslip",
        enforce_evidence: bool = False,  # Placeholder for future
        display_currency: str = None,    # Placeholder for future
    ) -> Dict[str, Any]:
        # Returns structured payslip data
```

#### 3. Return Structure

The service returns a structured dictionary with:
- `currency`: Base currency (KES)
- `base_pay`: Total, num_tasks, points, max_points, point_percentage, goal_amount, pay_balance, points_balance
- `bonuses`: login_bonus, login_hours, points_bonus, late_night_bonus, holiday_pay, eom_bonus, eoq_bonus, eoy_bonus, laptop_bonus, total
- `deductions`: tax_kra, food_accommodation, computer_maintenance, health, laptop_saving, total_laptop_savings, loan_payment, loan_amount, loan_balance, total
- `summary`: gross_pay, total_deductions, net_pay, base_pay, total_bonuses
- `metadata`: employee_id, employee_username, period_month, period_year, pay_type, currency, display_currency, message

### Key Features

- ✅ **Encapsulation**: All payslip calculation logic centralized in one service
- ✅ **Currency-Aware API**: Structure includes `currency` and `display_currency` fields (ready for future conversion)
- ✅ **Backward Compatibility**: No model changes, uses existing models as-is
- ✅ **Structured Output**: Clear separation between base_pay, bonuses, deductions, summary

### Helper Methods

1. **`_get_user_data()`**: Retrieves user profile, loan data, and payslip config
2. **`_calculate_base_pay()`**: Calculates base pay from tasks using existing `payinitial()` function
3. **`_calculate_bonuses()`**: Calculates all bonuses via existing functions
4. **`_calculate_deductions()`**: Calculates all deductions via existing functions
5. **`_empty_payslip()`**: Returns empty payslip structure when employee is None

### Usage Example

```python
from management.services.pay_calculation_service import PayCalculationService

service = PayCalculationService()

payslip_data = service.calculate_payslip(
    employee=user,
    target_month=11,
    target_year=2024,
    pay_type="task_payslip"
)

# Access structured data
gross_pay = payslip_data['summary']['gross_pay']
net_pay = payslip_data['summary']['net_pay']
eom_bonus = payslip_data['bonuses']['eom_bonus']
tax_deduction = payslip_data['deductions']['tax_kra']
```

---

## Phase P2: Payslip View Refactoring ✅

**Date:** December 2025  
**Status:** ✅ Complete

### Overview
Phase P2 refactored the `payslip()` view in `coda/management/views.py` to use `PayCalculationService` as the single source of truth for all payslip calculations. The view is now a **thin controller** that delegates all calculation logic to the service.

### Implementation Details

**File:** `coda/management/views.py`  
**Function:** `payslip()` (around line 1012)

**Before (Phase P1):**
- View directly called utility functions:
  - `get_tasks()`
  - `calculate_total_pay()`
  - `bonus()`
  - `deductions()`
  - `loan_computation()`
  - `calculate_login_bonus()`
- Manual accumulation of bonuses/deductions
- Ad-hoc logic constructing context variables

**After (Phase P2):**
- View instantiates `PayCalculationService`
- Calls `service.calculate_payslip(...)`
- Maps service output to existing template context
- **No longer calls** legacy utility functions directly

### Code Structure

```python
def payslip(request, *args, **kwargs):
    # ... parameter resolution ...
    
    # Use PayCalculationService as single source of truth
    service = PayCalculationService()
    payslip_data = service.calculate_payslip(
        employee=employee,
        target_month=selected_month,
        target_year=selected_year,
        pay_type=pay_type,
        enforce_evidence=False,
    )
    
    # Extract data from service response
    tasks = payslip_data.get('tasks')
    base_pay = payslip_data.get('base_pay', {})
    bonuses = payslip_data.get('bonuses', {})
    deductions = payslip_data.get('deductions', {})
    summary = payslip_data.get('summary', {})
    
    # Map to existing template context (backward compatibility)
    context = {
        'base_pay': base_pay.get('total', Decimal('0')),
        'gross_pay': summary.get('gross_pay', Decimal('0')),
        # ... all existing template variables ...
    }
    
    return render(request, template, context)
```

### Template Compatibility

The refactoring maintains **100% backward compatibility** with existing templates:
- All existing context keys are preserved
- Template variable names unchanged
- Numeric values identical to previous implementation
- No template changes required

### Context Mapping

The view maps service output to legacy template variables:
- `base_pay.total` → `total_pay` (Base pay amount)
- `summary.gross_pay` → `total_value` (Gross pay)
- `summary.net_pay` → `net` (Net pay after deductions)
- `bonuses.eom_bonus` → `EOM` (End of month bonus)
- `bonuses.login_bonus` → `Logged_In_Bonus` (Login bonus)
- `deductions.loan_payment` → `loan` (Loan payment)
- `base_pay.point_percentage` → `point_percentage` (Point percentage)

(Full mapping in `payslip()` function around line 1064-1111)

### Backward Compatibility

**Numeric Behavior:**
- ✅ All numeric calculations remain **identical** to previous implementation
- ✅ Base pay, gross pay, net pay match exactly
- ✅ Individual bonuses and deductions match exactly
- ✅ Verified by integration tests (7 scenarios, all passing)

**Legacy Helpers:**
- ✅ Legacy helper functions in `coda/management/utils.py` are **still present**
- ✅ Not removed (may be used elsewhere)
- ✅ `payslip()` view no longer calls them directly
- ✅ `PayCalculationService` uses them internally (delegation pattern)

**Template Compatibility:**
- ✅ All existing templates work without modification
- ✅ No breaking changes to template context
- ✅ Full backward compatibility maintained

### Testing

**Integration Tests:**
- **File:** `coda/management/tests/test_pay_calculation_service_integration.py`
- **Test Scenarios:** 7 scenarios covering full-time employees, contractors, EOM thresholds, no tasks, detailed breakdowns
- **Test Results:** ✅ All 7 tests passing, numeric equality verified (to 2 decimal places)

**Legacy Helper:**
- **File:** `coda/management/tests/helpers/legacy_payslip_calculator.py`
- Function: `calculate_legacy_payslip()` - Reproduces OLD payslip calculation for regression testing

### Benefits

1. **Single Source of Truth:** All payslip logic centralized in `PayCalculationService`
2. **Separation of Concerns:** View handles request/response, service handles business logic
3. **Testability:** Service can be tested independently
4. **Backward Compatibility:** No breaking changes, templates unchanged, numeric behavior identical

---

## Phase P3: 33% Rule, Base Stipend, and PayslipConfig Evolution 🟡

**Date:** December 2025  
**Branch:** `25.12_CODA_DEV_CM`  
**Scope:** Design-level changes only (no model edits yet)

---

## 1. Analysis of the Current 33% Rule

### 1.1 How Compliance Is Calculated Today

- **Single source of truth:** `ComplianceCalculator`  
  - **File:** `coda/management/services/compliance_calculator.py`  
  - **Core formula:**  
    \[
    \text{completion\_rate} = \frac{\text{total\_points}}{\text{total\_max\_points}} \times 100
    \]
    and employee is compliant if:
    \[
    \text{completion\_rate} \ge 33
    \]
  - **Data source:** `TaskHistory` records for the **target month**:
    - Filter: `TaskHistory.objects.filter(employee=employee, daf_date__month=target_month, daf_date__year=target_year)`
    - Aggregates:
      - `total_points = Sum('point')`
      - `total_max_points = Sum('mxpoint')`
      - `total_earnings = Sum(F('point') / F('mxpoint') * F('mxearning'))`
  - **Target period:** previous month, resolved by `get_current_target_period()`:
    - If today is e.g. **Feb 2025**, target is **Jan 2025**.
  - **Active rule window:** `is_rule_active()` returns `True` when `current_date.day > 15`.

- **Service wrapper:** `EmployeeComplianceService`  
  - **File:** `coda/management/services/employee_compliance_service.py`  
  - Wraps `ComplianceCalculator` and exposes:
    - `check_33_percent_compliance(employee, target_month, target_year)`
    - `get_company_compliance_report(target_month, target_year)`
    - `get_compliant_employees(...)` and `get_non_compliant_employees(...)`
  - Adds derived values:
    - `required_tasks ≈ task_count × 0.33`
    - `missing_tasks = max(0, required_tasks - completed_tasks)`
  - Business rule embedded in docstring:
    - “For a new month, an employee must meet 33% of their activities by 15th of the month for the pay for last month to be approved.”

- **Real-time monitoring:** `RealtimeComplianceService`  
  - **File:** `coda/finance/services/realtime_compliance_service.py`  
  - Uses `EmployeeComplianceService` and direct `TaskHistory` queries to:
    - Check individual thresholds (`check_employee_compliance_threshold`)
    - Send notifications on **newly compliant** or **newly non-compliant** transitions
    - Feed real-time dashboards and reminders

**Key point:** The 33% rule is purely **point-based** and is evaluated over **TaskHistory for last month**, but the **“active rule” window** (after the 15th) is based on **current date in the new month**.

---

### 1.2 Interaction with Payslip Calculation and Payout Timing

**Earnings (Month N):**

- **Where earnings are computed:**
  - Management-side payslip view:
    - **File:** `coda/management/views.py`, `payslip()` function
    - Core steps:
      - `get_tasks(employee, selected_month, selected_year, pay_type)` returns a queryset of `Task` or `TaskHistory`.
      - `calculate_total_pay(tasks)` sums `task.get_pay` for each record.
        - For `TaskHistory`, `get_pay` uses legacy formula:  
          \[
          \text{task\_pay} = \frac{\text{point}}{\text{mxpoint}} \times \text{mxearning} \times \text{late\_penalty}
          \]
      - Bonuses and deductions are then applied on top of `total_pay`.
  - Finance-side salary integration:
    - **File:** `coda/finance/services/integrated_budget_service.py`
    - Function: `_get_compliant_employee_salaries(target_month, target_year, department=None)`
      - Queries `TaskHistory` for the **target month/year**.
      - For each staff employee:
        - Calculates compliance rate (points/mxpoints).
        - Calculates `employee_salary = calculate_total_pay(employee_tasks)`.

- **Important:** The **amount earned in Month N** is entirely determined by:
  - TaskHistory snapshot for Month N (`daf_date` in Month N).
  - Per-task pay via `get_pay`.
  - Bonuses/deductions defined in `management.utils`/`PayslipConfig`.
  - **Compliance is not currently used to change the numeric amount earned for Month N**, only whether it is **approved/included** in salary/budget flows.

**Release / payout timing (Month N+1):**

- **Business rule in code comments:**
  - EmployeeComplianceService docstring explicitly encodes:
    - “For a new month, an employee must meet 33% of their activities by 15th of the month for the pay for last month to be approved.”
- **Operational behavior today (intended):**
  - **Month N:** Employee works, accumulating Task points and earnings.
  - **Month N+1 up to 15th:**
    - Employee must reach **33% completion** on the **current month’s tasks**.
    - Compliance is checked via `ComplianceCalculator` and `EmployeeComplianceService`.
    - If compliant by 15th:
      - Month N earnings are **approved** and included in:
        - Salary dashboard (`IntegratedBudgetService.get_salary_dashboard_data`).
        - Budget approvals and salary exports.
    - If not compliant by 15th:
      - Month N earnings remain **unapproved / not released**.
      - Real-time service can send reminders and highlight non-compliance.
- **Effect:** Month N pay is effectively **locked** until the employee hits 33% by 15th of Month N+1 (or later), even though the **earnings themselves are already determinable** from Month N TaskHistory.

**Conclusion:**  
Today’s implementation conflates:
- **“Earned”** = what Month N work produced, and  
- **“Released/paid”** = whether Month N earnings are approved for payout in Month N+1+,

by using the 33% rule as a **gate on inclusion in payroll/budget**, without a clear, explicit separation in data structures or services.

---

### 1.3 Where the 33% Rule Is Used

- **ComplianceCalculator**
  - Computes `completion_rate` and `is_compliant` using TaskHistory.
  - Exposes `is_rule_active()` (after 15th of current month).
- **EmployeeComplianceService**
  - Higher-level methods for:
    - Company-wide and department-level reports.
    - Lists of compliant and non-compliant employees.
  - Intended as the **integration point for payroll/budget inclusion**.
- **RealtimeComplianceService (Finance)**
  - Interprets compliance rate for:
    - Notifications when employees **cross** the 33% threshold.
    - Reminders to employees below threshold.
    - Real-time dashboard indicators of who is currently compliant.
- **IntegratedBudgetService**
  - Uses `TaskHistory` and `calculate_total_pay()` to compute salaries for compliant employees.
  - Currently does not explicitly store or expose “locked vs released” amounts—it simply includes or excludes employees from the salary totals.

---

### 1.4 Separating “Earned in Month N” vs “Released in Month N+1”

**Earned in Month N (Earnings):**

- **Definition (business):**
  - The amount that an employee’s tasks for Month N justify, based on:
    - TaskHistory snapshot (`daf_date` in Month N).
    - Pay formulas (`ActivityType` or legacy mxearning-based).
    - Per-task penalties (late submission) and adjustments.
  - **Independent of** what happens in Month N+1.

- **Implementation surface today:**
  - `calculate_total_pay(TaskHistory for Month N)`  
  - Plus Month N bonuses/deductions (if we view Month N in isolation).

**Released in Month N+1 (Payout timing):**

- **Definition (business):**
  - The portion of Month N earnings that is actually **paid out** in Month N+1’s payroll run.
  - Controlled by:
    - 33% rule evaluated on **Month N+1’s tasks**.
    - Potentially other constraints (budget caps, administrative decisions).

- **Implementation surface today:**
  - 33% rule is checked via `ComplianceCalculator` + `EmployeeComplianceService`.
  - Inclusion/exclusion in salary dashboard / budget approvals stands in as “released vs not released”, but there is **no explicit tracking** of:
    - `earned_amount_n`
    - `released_amount_n`
    - `locked_amount_n`

**Design requirement:** We need to formalize this separation:
- Earnings should always exist as **deterministic amounts** per month.
- The 33% rule (and later quality checks) should only affect **when and how much of those earnings are released**, not whether they exist.

---

## 2. Design: Earned vs Released Money

### 2.1 Conceptual Model

For each **employee** and each **earning month N**, we want to track:

- **`earned_amount_n`**  
  - Total amount generated by Month N work (TaskHistory + PayCalculationService).
  - Includes any Month-N-specific bonuses/deductions that are part of “earning the money” (e.g., late penalties, in-month performance bonuses).

- **`released_amount_n`**  
  - Portion of `earned_amount_n` that has actually been paid out in subsequent months (N+1, N+2, …).
  - Controlled by:
    - 33% compliance rule for Month N+1 (and possibly subsequent months if delayed).
    - Future quality gates (evidence, checklist, QA).

- **`locked_amount_n`**  
  - The difference:
    \[
    \text{locked\_amount\_n} = \text{earned\_amount\_n} - \text{released\_amount\_n}
    \]
  - Represents earnings that exist but are not yet released.
  - Can be released later when conditions (33%, quality, etc.) are satisfied.

**In words:**  
“Month N earnings are calculated once and fixed. The 33% rule (and later quality rules) decide **when** and **how much** of that fixed amount becomes available as cash in a given payroll run.”

---

### 2.2 Where This Logic Should Live

We have two natural options:

- **Option A: Extend `PayCalculationService` (preferred)**  
  - Treat earned vs released as part of the **payroll calculation summary**.
  - PayCalculationService becomes the single orchestrator for:
    - Reading TaskHistory and computing earnings.
    - Querying compliance status for current month.
    - Deciding how much of past months’ earnings are released.
  - Output structure (conceptual):

  ```python
  {
      "employee": employee,
      "target_month": N,
      "target_year": Y,
      "earned_amount": Decimal,   # earned_amount_n
      "released_amount": Decimal, # released_amount_n for this run
      "locked_amount": Decimal,   # locked_amount_n
      "compliance": {
          "check_month": N_plus_1,
          "check_year": Y_plus_1,
          "completion_rate": float,
          "is_compliant": bool,
          "threshold": 33.0,
          "rule_active": bool,  # after 15th
      },
      "quality_gates": {
          "evidence_coverage": float,
          "checklist_score": float,
          "passed": bool,
      },
      "calculation_metadata": {...}
  }
  ```

- **Option B: New `MonthlyEarningsSnapshot` model**
  - A small, persistent model that summarizes monthly earnings and release state per employee.
  - Candidate fields (design-only, not implementing yet):

  ```text
  MonthlyEarningsSnapshot
  - employee (FK → CustomerUser)
  - earning_month (int)    # 1–12
  - earning_year (int)
  - earned_amount (Decimal)
  - released_amount (Decimal)
  - locked_amount (Decimal)
  - last_release_run_at (DateTime)
  - last_release_reason (CharField)  # '33_percent_met', 'manual_override', etc.
  - metadata (JSONField)  # optional – details from PayCalculationService
  - is_final (bool)       # once true, no further changes (e.g., after full payout)
  ```

**Recommended hybrid:**  
- **Core logic** (how to compute amounts) lives in `PayCalculationService`.
- **Persistence of summary** lives in **Optional** `MonthlyEarningsSnapshot`, created/updated by the service.
  - This keeps models small and focused while giving Finance and Management a stable view of “what is earned vs released”.

---

### 2.3 Flow: Earning vs Release with 33% Rule

For a given employee and Month N:

1. **End of Month N (or at reset):**  
   - `TaskResetService` creates `TaskHistory` snapshots for Month N.
   - `PayCalculationService` can be run in **“earnings-only mode”** for Month N:
     - Reads Month N TaskHistory.
     - Computes `earned_amount_n` (base pay + Month-N bonuses − Month-N deductions).
     - Stores result in `MonthlyEarningsSnapshot` (or returns via API).

2. **Month N+1, before 15th:**  
   - 33% rule may or may not be considered “active” yet:
     - `ComplianceCalculator.is_rule_active()` is false before or on the 15th.
   - Business option:
     - Either **allow early release** if 33% is already met.
     - Or **always wait until 15th** before any release evaluation.

3. **Month N+1, on/after 15th:**  
   - `ComplianceCalculator` evaluates Month N+1 TaskHistory up to current date.
   - If `completion_rate >= 33`:
     - **Release Month N earnings** (subject to any quality gates).
     - `released_amount_n` increases by some amount (could be the full `locked_amount_n` or a portion).
   - If `completion_rate < 33`:
     - `locked_amount_n` remains unchanged.
     - Real-time services send reminders.

4. **Subsequent months (N+2, N+3, …):**  
   - If employee only reaches 33% later, `PayCalculationService` can:
     - Re-run for Month N+2, check compliance, and release previously locked `locked_amount_n`.

**Key change vs today:**  
- Earnings for Month N are **never deleted or “not earned”**—they are just **locked** until compliance/quality conditions are met.

---

## 3. Base Stipend Concept (Design-Only)

### 3.1 Business Goals for Base Stipend

- Avoid “dry months” for long-term employees:
  - Introduce a small **base stipend** (e.g. 2,500 KES) as a safety net.
  - Protects against total zero payout when compliance is slightly missed.
- Preserve motivational effect of 33% rule:
  - Employees should still feel **strong pressure** to start early in the month.
  - Base stipend should not reward non-participation or very low effort.
- Make stipend performance-sensitive:
  - **0%** of base stipend at exactly **33%** compliance.
  - About **50%** of base stipend at **≈ 66.5%** compliance.
  - **100%** of base stipend at **100%** compliance.
- Only available to **tenured employees**:
  - Must have at least **X months** at CODA (e.g. 6 or 12 months) to qualify.

---

### 3.2 Tenure Requirement

**Inputs:**
- Employee tenure is already tracked via `CustomerUser.tenure` (months since joining).

**Design rule:**

- Define a **configurable threshold** `MIN_STIPEND_TENURE_MONTHS` (e.g. 12 months).
- Only employees with `tenure >= MIN_STIPEND_TENURE_MONTHS` are eligible for stipend calculations.
- For ineligible employees:
  - `stipend_amount_n = 0` regardless of compliance.

**Where this logic should live:**
- Inside `PayCalculationService` when it computes **release** for Month N:
  - Reads tenure from the user object.
  - “Opt-in” to stipend calculation only if tenure threshold is met.

---

### 3.3 Compliance-Scaled Stipend Formula

We want a **monotonic** scaling of stipend between 33% and 100% compliance:

- At **33%** compliance → stipend factor = 0
- At **≈66.5%** compliance → stipend factor ≈ 0.5
- At **100%** compliance → stipend factor = 1

We can define:

```text
effective_rate = clamp(compliance_rate, 33, 100)
factor = (effective_rate - 33) / (100 - 33)
stipend = base_stipend_amount * factor
```

Where:

- `compliance_rate` is the Month N+1 (or current month) completion rate from `ComplianceCalculator`.
- `clamp(x, 33, 100)` ensures we treat anything below 33 as 33 and anything above 100 as 100, preventing negative factors or >100% stipend.
- `base_stipend_amount` is a **policy parameter** (e.g. 2,500 KES), not hardcoded into models.

**Behavior:**

- If `compliance_rate < 33`:
  - `effective_rate = 33`
  - `factor = (33 - 33) / 67 = 0`
  - `stipend = 0` (no stipend at all)
- If `compliance_rate = 66.5`:
  - `effective_rate = 66.5`
  - `factor = (66.5 - 33) / 67 ≈ 0.5`
  - `stipend ≈ 0.5 × base_stipend_amount`
- If `compliance_rate = 100`:
  - `effective_rate = 100`
  - `factor = (100 - 33) / 67 = 1`
  - `stipend = base_stipend_amount`

**Interpretation:**

- The stipend acts as a **smooth bonus** inside the “33%+” region:
  - Below 33%: **no stipend**, all Month N earnings are locked.
  - Between 33% and 100%: the stipend ramps up linearly.
  - At 100%: employee receives the full base stipend.

---

### 3.4 Stipend Position in Earned vs Released Model

We have two options for where the stipend sits:

1. **Part of Earned Amount (Month N):**
   - Treat stipend as part of Month N earnings:
     - Pros:
       - Simple: `earned_amount_n` includes stipend.
     - Cons:
       - Stipend depends on **future compliance** (Month N+1), not purely on Month N.
       - Makes Month N earnings depend on Month N+1 behavior → confusing.

2. **Part of Released Amount (Month N+1):** **(Recommended)**
   - Treat stipend as a **release-time adjustment**:
     - `stipend_amount_n` is computed when we release Month N earnings, based on Month N+1 compliance.
     - Conceptually:

     ```text
     released_amount_n = base_release_n + stipend_amount_n
     locked_amount_n   = earned_amount_n - base_release_n
     ```

     - Pros:
       - Keeps `earned_amount_n` purely about Month N work.
       - Keeps stipend firmly in the “release control” space (like 33% rule).
       - Easier to explain to employees: “Your stipend depends on how you start the new month.”

**Recommendation:**  
- Treat **base stipend** as a **release-time component**, not part of Month N earning calculation.
- Implementation-wise:
  - `PayCalculationService` for Month N+1:
    - Computes:
      - `compliance_rate` for Month N+1.
      - `stipend_factor` via formula above.
      - `stipend_amount_n = base_stipend_amount * factor` (if tenure requirement met).
    - Adds `stipend_amount_n` into the **released** side of Month N summary.

---

### 3.5 Avoiding Immediate PayslipConfig Bloat

Owner is concerned about `PayslipConfig` already being heavy. For Phase P3, we can **design the stipend and 33%-rule evolution without adding fields yet**:

**Do NOT add these fields yet (conceptual only):**

- `base_stipend_amount`
- `min_stipend_tenure_months`
- `stipend_compliance_min` (33)
- `stipend_compliance_max` (100)

**Instead, for Phase P3:**

- Treat these as **service-level configuration parameters**, e.g. in:
  - Django settings: `PAYROLL_BASE_STIPEND_AMOUNT`, `PAYROLL_MIN_STIPEND_TENURE_MONTHS`, etc.
  - Or a small, generic config table (if one already exists).
- Keep `PayslipConfig` unchanged until:
  - We have validated the stipend behavior in sandbox.
  - We have a clear pattern for **group-level** and **region-aware** configuration.

**Future evolution plan (not for P3):**

- Once the pattern is validated:
  - Add stipend-related fields to a **lighter, dedicated config model** that `PayslipConfig` can reference (e.g. `PayPolicy` or `LevelPolicy`), instead of expanding `PayslipConfig` itself.

---

## 4. Preparing for Future Extensions

### 4.1 Level/Group-Based Perks (Unit Rate Multipliers, Stipend Ranges)

We already have:

- `TaskGroups` model (e.g. Group H, Group I, etc.).
- Group logic that affects `mxearning` and earning behavior.

**Design idea:**

- Introduce a **logical “PayPolicy” layer** (conceptual, not implemented now) that can be fetched by `PayCalculationService` based on:
  - Employee group (TaskGroups).
  - Employee level (if/when added).
  - Region/currency (future).
- This policy could define:
  - `unit_rate_multiplier` per group.
  - `stipend_min` / `stipend_max` per group/level.
  - Overrides for 33% threshold (e.g. higher for senior roles).

For Phase P3:

- **Do not** model PayPolicy yet.
- Ensure `PayCalculationService` interface is designed so it can **later look up** a “policy object” without changing its external API.

---

### 4.2 Region-Aware Pay (USD vs KES, Local Purchasing Power)

Future requirement:

- Employees in different regions may:
  - Be paid in different currencies.
  - Have different base stipend amounts.
  - Have different unit rates.

Design implications for Phase P3:

- Ensure new design is:
  - **Currency-agnostic** at the conceptual level.
  - Uses `Decimal` amounts consistently and supports currency metadata.
- For now:
  - Treat `base_stipend_amount` as being in **employee’s primary pay currency**.
  - Defer currency conversion and region policies to a future `PayPolicy` / FX layer.

---

### 4.3 Evidence + Checklist-Based Quality Gating

Owner’s concern:

- Employees might “rush to 33%” with low-quality work just to unlock money and stipend.

Design hooks:

- Add a **quality gate** concept into the Earned vs Released model:

```text
quality_passed_n = (evidence_coverage_n >= MIN_EVIDENCE_COVERAGE) 
                   AND (checklist_score_n >= MIN_CHECKLIST_SCORE)
```

- `PayCalculationService` should be able to:
  - Inspect TaskHistory + TaskLinks + QA/checklist data.
  - Compute quality metrics:
    - `evidence_coverage_n` (e.g. % of tasks with at least one evidence item).
    - `checklist_score_n` (from existing or future QA forms).
  - Only allow full release of `earned_amount_n` + stipend if:
    - **Both** `is_compliant` (33% rule) **and** `quality_passed_n` are true.
  - Possibly:
    - Release a **reduced percentage** of `locked_amount_n` if compliance is hit but quality gates partially fail.

For Phase P3:

- Keep these as clearly named keys in the **design of the PayCalculationService summary**, even if we only partially implement them:

```python
{
    "quality_gates": {
        "evidence_coverage": float,  # 0–100
        "checklist_score": float,    # 0–100 or 0–1
        "passed": bool,
    }
}
```

---

## 5. Summary and Next Steps

### 5.1 Summary of Design Decisions

- **33% rule** remains the primary **behavioral lever**, but we:
  - Treat it as a **release control**, not an “earn or don’t earn” switch.
  - Use `ComplianceCalculator` + `EmployeeComplianceService` as the authority.
- We explicitly model:
  - `earned_amount_n` = what Month N work produced.
  - `released_amount_n` = what has been paid out so far.
  - `locked_amount_n` = earnings waiting on compliance/quality.
- We introduce a **base stipend** concept:
  - Only for staff with sufficient tenure.
  - Scaled linearly between 33% and 100% compliance:
    - 0 at 33%, 50% at ~66.5%, 100% at 100%.
  - Treated as a **release-time component**, not part of Month N earning.
- We avoid immediate `PayslipConfig` bloat by:
  - Keeping stipend parameters in service-level config for Phase P3.
  - Planning a future, lighter `PayPolicy`-style model for group/region rules.

---

### 5.2 Proposed Implementation Steps (Later Phases)

**Phase P3 (Design + Service API):**

- Implement `PayCalculationService` with:
  - Earned vs released split.
  - Integration with `ComplianceCalculator` and `EmployeeComplianceService`.
  - Stipend calculation using the proposed formula and tenure check (config-driven).
  - Return a structured summary suitable for:
    - Management payslip view.
    - Finance salary dashboards.

**Phase P4 (Persistence & Policies):**

- Introduce optional `MonthlyEarningsSnapshot` model to persist earned vs released per month.
- Begin introducing a `PayPolicy` abstraction for:
  - Group-based multipliers.
  - Region-aware stipend and rates.

**Phase P5 (Quality Gates & Region Support):**

- Integrate evidence and checklists as quality gates.
- Add region/currency-aware calculations.
- Refine stipend and release logic to incorporate these quality/region rules.

This document deliberately keeps model changes out of scope for P3 and focuses on a **clean conceptual separation** (earned vs released) and a **well-behaved stipend formula** that preserves the motivational effect of the 33% rule while reducing the risk of completely dry months for long-term employees.



