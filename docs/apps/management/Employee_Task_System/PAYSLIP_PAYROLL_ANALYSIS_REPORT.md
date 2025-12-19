# CODA Payslip & Payroll System - Comprehensive Analysis Report

**Date:** December 2025  
**Branch:** `25.12_CODA_DEV_CM`  
**Purpose:** Detailed, DRY-focused analysis of current payslip/payroll system to guide unified, AI-assisted salary engine design

---

## Executive Summary

This report maps the complete payslip and payroll computation system in the CODA monolith, focusing on:
- **How final payslip amounts are computed** (earnings + bonuses + deductions + taxes)
- **End-to-end flow** from Tasks → TaskHistory → Payslip
- **Duplication and risks** in pay calculation logic
- **Existing motivation levers** (bonuses, penalties, awards)
- **Extension points** for unified PayCalculationService

**Key Finding:** Payslip calculation is **highly fragmented** across multiple functions in `management/utils.py` and `management/views.py`. The final payslip amount is computed in the view layer (`payslip()` function) by calling multiple helper functions. There is **no unified service** for pay calculation, leading to duplication and inconsistency.

---

## 1. Payslip-Related Models

### 1.1 Core Payslip Configuration Model

#### PayslipConfig Model
**File:** `coda/finance/models/core.py` (lines 214-257)

| Field | Type | Purpose | Default | Notes |
|-------|------|---------|---------|-------|
| `user` | ForeignKey → CustomerUser | Employee this config belongs to | Nullable | One config per employee |
| `web_pay_hour` | DecimalField(10,2) | Base hourly rate | 0.00 | Used for web-related work |
| `web_delta` | DecimalField(10,2) | Increment percentage for group changes | 0.00 | Used in `increment_in_graduation_of_employee()` |
| `laptop_status` | BooleanField | Whether employee has laptop | True | Affects laptop bonus/savings |
| `loan_status` | BooleanField | Whether employee has active loan | True | Affects loan deductions |
| `loan_amount` | DecimalField(10,2) | Loan amount | 20000.00 | Used if no LoanApplication exists |
| `loan_repayment_percentage` | DecimalField(5,2) | % of pay deducted for loan | 0.20 (20%) | Applied to `total_pay` |
| `installment_amount` | DecimalField(10,2) | Fixed installment amount | 1000.00 | Alternative to percentage |
| `installment_date` | DateField | Next installment date | Nullable | For scheduled payments |
| `lb_amount` | DecimalField(10,2) | Laptop bonus amount | 1000.00 | Bonus if laptop_status=True |
| `ls_amount` | DecimalField(10,2) | Laptop savings amount | 1000.00 | Deduction if laptop_status=False |
| `ls_max_limit` | DecimalField(10,2) | Max laptop savings | 20000.00 | Cap on laptop savings |
| `rp_starting_period` | CharField(10) | Retirement package start period | - | Text field |
| `rp_starting_amount` | DecimalField(10,2) | Retirement package base amount | 10000.00 | Base retirement contribution |
| `rp_increment_percentage` | DecimalField(5,2) | Retirement increment % | 0.01 (1%) | Applied to `total_pay` |
| `rp_increment_max_percentage` | DecimalField(5,2) | Max retirement increment % | 0.05 (5%) | Used for "late night bonus" |
| `rp_increment_percentage_increment` | DecimalField(5,2) | Increment cycle amount | 0.01 (1%) | Increment per cycle |
| `rp_increment_percentage_increment_cycle` | IntegerField | Increment cycle (months) | 12 | How often to increment |
| `holiday_pay` | DecimalField(10,2) | Holiday bonus | 3000.00 | Paid in Dec/Jan |
| `night_bonus` | DecimalField(10,2) | Night shift bonus | 500.00 | **NOT USED** (see `rp_increment_max_percentage`) |
| `eom_bonus` | DecimalField(10,2) | Employee of the Month | 1000.00 | Awarded if point_percentage >= 75% |
| `eoq_bonus` | DecimalField(10,2) | Employee of the Quarter | 3000.00 | **NOT IMPLEMENTED** |
| `eoy_bonus` | DecimalField(10,2) | Employee of the Year | 10000.00 | **NOT IMPLEMENTED** |
| `computer_maintenance` | DecimalField(10,2) | Computer maintenance deduction | 500.00 | Only for FULL_TIME applicants |
| `food_accommodation` | DecimalField(10,2) | Food & accommodation deduction | 1000.00 | Only for FULL_TIME applicants |
| `health` | DecimalField(10,2) | Health deduction | 500.00 | Only for FULL_TIME applicants |

**Domain Concept:** Per-employee payslip configuration. Contains all bonus rates, deduction amounts, and loan settings. Falls back to latest config if employee doesn't have one.

**Relationships:**
- `user` → `CustomerUser` (one-to-one, nullable)
- Used by: `paymentconfigurations()`, `loan_computation()`, `deductions()`, `bonus()`

**Gaps:**
- ❌ No `tax_rate` field (hardcoded 5% in `deductions()`)
- ❌ No `nssf_rate` or `nhif_rate` fields (not implemented)
- ❌ `eoq_bonus` and `eoy_bonus` defined but never used
- ❌ `night_bonus` defined but not used (uses `rp_increment_max_percentage` instead)

---

### 1.2 Loan Models (Affect Deductions)

#### LoanApplication Model
**File:** `coda/finance/models/loan.py` (lines 121-299)

| Field | Type | Purpose | Notes |
|-------|------|---------|-------|
| `borrower` | ForeignKey → CustomerUser | Employee with loan | Related name: `loan_applications` |
| `status` | CharField(20) | Loan status | `active`, `approved`, `repaid`, etc. |
| `amount_requested` | DecimalField(10,2) | Original loan amount | Stored in USD |
| `total_payable` | DecimalField(10,2) | Total amount to repay | Principal + interest |
| `monthly_payment` | DecimalField(10,2) | Monthly payment amount | Calculated from loan product |
| `balance_amount` | Property | Remaining balance | `total_payable - total_paid` |
| `is_outstanding` | Property | Has outstanding balance | `status == 'active' AND balance_amount > 0` |

**Domain Concept:** Active loan applications that affect payroll deductions.

**How It Affects Payslip:**
- If `is_outstanding == True`, loan payment deducted from `total_pay`
- Payment = `total_pay × loan_repayment_percentage` (from PayslipConfig)
- Or: `loan.calculate_monthly_deduction(total_pay, 10.0)` if no config

---

### 1.3 Payment Models (Not Directly Used in Payslip)

#### Payment_History Model
**File:** `coda/finance/models/core.py` (lines 135-171)

**Note:** This model tracks **client payments** (for services), NOT employee salary payments. It's not directly used in payslip calculation but may be referenced for eligibility checks.

---

## 2. Payslip Calculation Functions

### 2.1 Core Pay Calculation Functions

#### calculate_total_pay()
**File:** `coda/management/utils.py` (lines 743-763)

**What It Does:**
- Sums `task.get_pay` for all tasks in a queryset
- Handles invalid pay values gracefully
- Returns `Decimal(0)` if no tasks

**Formula:**
```python
total_pay = sum(task.get_pay for task in tasks)
```

**Where `task.get_pay` is:**
- **If ActivityType exists:** `(points_earned / points_for_full_target) × max_earning_per_month × late_penalty`
- **If no ActivityType:** `(point / mxpoint) × mxearning × late_penalty`

**Used By:**
- `payslip()` view (line 1044)
- `get_tasks()` (line 172)
- `IntegratedBudgetService._get_compliant_employee_salaries()` (line 179)

**Gaps:**
- ❌ No evidence validation
- ❌ No billable activity checks
- ❌ Uses legacy formula if no ActivityType

---

#### get_tasks()
**File:** `coda/management/utils.py` (lines 49-173)

**What It Does:**
- Retrieves Task or TaskHistory records based on `pay_type`
- Calculates `total_pay` using `calculate_total_pay()`
- Handles month/year filtering with complex date logic

**Pay Types:**
- `'payslip'`, `'usertasks'`, `'tasks'` → Returns `Task` objects (current month)
- `'task_payslip'`, `'usertaskhistory'`, `'taskhistory'` → Returns `TaskHistory` objects (last month)

**Complex Date Logic:**
- For `usertaskhistory`: Includes tasks with `daf_date` matching selected month/year
- Also includes tasks created this month when viewing last month (catches late submissions)
- Handles NULL `daf_date` cases

**Returns:**
- `(tasks, total_pay, message)` tuple

**Used By:**
- `payslip()` view (line 1044)

---

### 2.2 Bonus Calculation Functions

#### bonus()
**File:** `coda/management/utils.py` (lines 702-740)

**What It Does:**
- Calculates all bonus components for an employee
- Uses `PayslipConfig` for bonus rates
- Returns tuple of bonus amounts

**Bonus Components:**

1. **Points Bonus (`bonus_points_ammount`):**
   - **Formula:** `Sum(task.point)` (total points earned)
   - **Source:** `payinitial(tasks)` function
   - **Note:** This is just the raw points, not a monetary bonus

2. **Late Night Bonus (`latenight_Bonus`):**
   - **Formula:** `total_pay × payslip_config.rp_increment_max_percentage`
   - **Default:** `total_pay × 0.05` (5% of total pay)
   - **Note:** Uses retirement package max percentage, not `night_bonus` field

3. **Yearly Bonus (`yearly`):**
   - **Formula:** `rp_starting_amount + (total_pay × rp_increment_percentage)`
   - **Default:** `10000 + (total_pay × 0.01)` (base + 1% of pay)
   - **Note:** Retirement package contribution

4. **Holiday Pay (`offpay`):**
   - **Formula:** `payslip_config.holiday_pay` if month in (12, 1) and day in (24, 25, 26, 31, 1, 2)
   - **Default:** 3000.00 (only in December/January)

5. **Employee of the Month (`EOM`):**
   - **Formula:** `payslip_config.eom_bonus` if `point_percentage >= 75`
   - **Default:** 1000.00
   - **Calculation:** `point_percentage = (total_points / total_max_points) × 100`

6. **Employee of the Quarter (`EOQ`):**
   - **Always:** `Decimal(0.00)` (not implemented)

7. **Employee of the Year (`EOY`):**
   - **Always:** `Decimal(0.00)` (not implemented)

**Returns:**
```python
(bonus_points_ammount, latenight_Bonus, yearly, offpay, EOM, EOQ, EOY, sub_bonus)
```

**Where `sub_bonus` = sum of all bonuses except `yearly`**

**Used By:**
- `get_bonus_and_summary()` (line 781)
- `payslip()` view (via `get_bonus_and_summary()`)

**Gaps:**
- ❌ `bonus_points_ammount` is just points, not a monetary bonus
- ❌ `EOQ` and `EOY` never implemented
- ❌ `night_bonus` field in PayslipConfig not used

---

#### calculate_login_bonus()
**File:** `coda/accounts/utils.py` (lines 345-415)

**What It Does:**
- Calculates bonus based on valid login hours
- Validates hours (must be between 1 and 12 hours per day)
- Applies threshold and hourly rate

**Formula:**
```python
# Sum valid login hours (1-12 hours per day)
total_login_hours = sum(valid_login_hours)

# Calculate bonus if threshold met
if total_login_hours >= threshold:  # Default: 20 hours
    login_bonus = total_login_hours × hourly_rate  # Default: $5/hour
else:
    login_bonus = 0
```

**Parameters:**
- `threshold`: Default 20 hours (minimum to qualify)
- `hourly_rate`: Default $5/hour

**Returns:**
- `(total_login_hours, login_bonus, invalid_entries)`

**Used By:**
- `payslip()` view (line 1037)

**Gaps:**
- ❌ Hardcoded threshold and rate (should be in PayslipConfig)
- ❌ No validation of login patterns (could be gamed)

---

#### lap_save_bonus()
**File:** `coda/management/utils.py` (lines 630-645)

**What It Does:**
- Calculates laptop bonus and savings based on `laptop_status`

**Logic:**
```python
if payslip_config.laptop_status == True:
    # Employee has laptop → gets bonus, no savings deduction
    laptop_bonus = payslip_config.lb_amount if employee is FULL_TIME else 0
    laptop_saving = 0
    total_laptop_savings = 0
else:
    # Employee doesn't have laptop → savings deduction, no bonus
    laptop_bonus = 0
    laptop_saving = 1000.00
    total_laptop_savings = min(payslip_config.ls_amount, 20000.00)
```

**Returns:**
- `(laptop_bonus, laptop_saving, total_laptop_savings)`

**Used By:**
- `deductions()` (line 679)
- `payslip()` view (line 1059)

**Gaps:**
- ❌ Hardcoded `1000.00` for `laptop_saving` (should use `ls_amount`)
- ❌ Only FULL_TIME applicants get laptop bonus (hardcoded check)

---

### 2.3 Deduction Calculation Functions

#### deductions()
**File:** `coda/management/utils.py` (lines 649-700)

**What It Does:**
- Calculates all deduction components for an employee
- Applies deductions only to FULL_TIME applicants
- Returns tuple of deduction amounts

**Deduction Components:**

1. **Food & Accommodation (`food_accommodation`):**
   - **Formula:** `payslip_config.food_accommodation` if FULL_TIME
   - **Default:** 1000.00
   - **Otherwise:** 0.00

2. **Computer Maintenance (`computer_maintenance`):**
   - **Formula:** `payslip_config.computer_maintenance` if FULL_TIME
   - **Default:** 500.00
   - **Otherwise:** 0.00

3. **Health (`health`):**
   - **Formula:** `payslip_config.health` if FULL_TIME
   - **Default:** 500.00
   - **Otherwise:** 0.00

4. **KRA Tax (`kra`):**
   - **Formula:** `total_pay × 0.05` (hardcoded 5%)
   - **Note:** No configurable tax rate in PayslipConfig

5. **Laptop Savings (`lap_saving`):**
   - **Formula:** From `lap_save_bonus()` (1000.00 if no laptop)
   - **Note:** Only deducted if `laptop_status == False`

6. **Loan Payment (`loan_payment`):**
   - **Formula:** From `loan_computation()` (see below)
   - **Note:** Only if employee has active loan

**Total Deductions:**
```python
total_deductions = (
    food_accommodation +
    computer_maintenance +
    health +
    kra +
    laptop_saving +
    loan_payment
)
```

**Returns:**
```python
(food_accommodation, computer_maintenance, health, kra, 
 laptop_saving, total_laptop_savings, loan_payment, total_deductions)
```

**Used By:**
- `get_bonus_and_summary()` (line 784)
- `payslip()` view (line 1057)

**Gaps:**
- ❌ KRA tax hardcoded at 5% (should be in PayslipConfig)
- ❌ No NSSF or NHIF deductions (Kenyan payroll requirements)
- ❌ Deductions only apply to FULL_TIME applicants (hardcoded)

---

#### loan_computation()
**File:** `coda/management/utils.py` (lines 520-577)

**What It Does:**
- Calculates loan amount, loan payment, and balance for an employee
- Uses `LoanApplication` if exists, otherwise falls back to `PayslipConfig`

**Logic:**
```python
if employee has active LoanApplication:
    loan_amount = active_loan.balance_amount  # Remaining balance
    loan_payment = total_pay × payslip_config.loan_repayment_percentage
    # Ensure payment doesn't exceed balance
    if loan_amount < loan_payment:
        loan_payment = loan_amount
    balance_amount = loan_amount - loan_payment
    # Record payment to loan
    active_loan.make_payment(loan_payment)
else:
    # Use PayslipConfig defaults
    loan_amount = payslip_config.loan_amount
    loan_payment = total_pay × payslip_config.loan_repayment_percentage
    balance_amount = loan_amount - loan_payment
```

**Returns:**
- `(loan_amount, loan_payment, balance_amount)`

**Used By:**
- `deductions()` (line 671)
- `payslip()` view (line 1056)
- `updateloantable()`, `addloantable()`

**Gaps:**
- ❌ Falls back to PayslipConfig if no loan (should be 0 if no loan)
- ❌ Default 20% deduction if no config (hardcoded)

---

### 2.4 Helper Functions

#### get_bonus_and_summary()
**File:** `coda/management/utils.py` (lines 779-786)

**What It Does:**
- Wrapper function that calls `bonus()` and `deductions()`
- Combines results into single return value

**Returns:**
```python
(bonus_points_ammount, latenight_Bonus, yearly, offpay, EOM, EOQ, EOY, 
 sub_bonus, total_deduction, total_bonus)
```

**Used By:**
- `payslip()` view (line 1062)

---

#### payinitial()
**File:** `coda/management/utils.py` (lines 373-413)

**What It Does:**
- Calculates points, max points, pay, and goal amount from tasks
- Used for bonus calculations

**Returns:**
```python
(num_tasks, points, mxpoints, pay, GoalAmount, pointsbalance, point_percentage)
```

**Where:**
- `points` = `Sum(task.point)`
- `mxpoints` = `Sum(task.mxpoint)`
- `pay` = `Sum(task.mxearning)` (NOT actual pay, just max earning)
- `GoalAmount` = `Sum(task.mxearning)` (same as pay)
- `point_percentage` = `(points / mxpoints) × 100`

**Used By:**
- `bonus()` (line 707)
- `employee_reward()` (line 723)

**Gaps:**
- ❌ `pay` and `GoalAmount` are the same (both `Sum(mxearning)`)
- ❌ Doesn't use `task.get_pay` (uses `mxearning` instead)

---

#### employee_reward()
**File:** `coda/management/utils.py` (lines 253-271)

**What It Does:**
- Calculates point percentage for EOM bonus eligibility

**Formula:**
```python
point_percentage = (total_points / total_max_points) × 100
```

**Returns:**
- `point_percentage` (0-100)

**Used By:**
- `bonus()` (line 723) - for EOM eligibility

---

## 3. How Final Payslip Amount Is Computed Today

### 3.1 Step-by-Step Calculation Flow

**Location:** `coda/management/views.py` (lines 1011-1142)

**Step 1: Get Employee Data**
```python
userprofile, user_data, payslip_config = get_user_data(employee)
# user_data = LoanApplication queryset
# payslip_config = PayslipConfig instance (or default)
```

**Step 2: Calculate Login Bonus**
```python
total_login_hours, login_bonus, invalid_entries = calculate_login_bonus(
    user=employee,
    selected_month=selected_month,
    selected_year=selected_year
)
# login_bonus = total_login_hours × $5/hour (if >= 20 hours)
```

**Step 3: Get Tasks and Calculate Base Pay**
```python
tasks, total_pay, message = get_tasks(employee, selected_month, selected_year, pay_type)
# total_pay = sum(task.get_pay for task in tasks)
# Uses TaskHistory if pay_type in ['task_payslip', 'usertaskhistory']
# Uses Task if pay_type in ['payslip', 'usertasks']
```

**Step 4: Calculate Loan Deduction**
```python
loan_amount, loan_payment, balance_amount = loan_computation(
    total_pay, user_data, payslip_config
)
# loan_payment = total_pay × loan_repayment_percentage (default 20%)
```

**Step 5: Calculate All Deductions**
```python
food_accomodation, computer_maintenance, health, kra, lap_saving, 
total_laptop_savings, loan_payment, total_deductions = deductions(
    employee, user_data, payslip_config, total_pay
)
# total_deductions = food + maintenance + health + kra + laptop_saving + loan_payment
```

**Step 6: Calculate Laptop Bonus/Savings**
```python
laptop_bonus, laptop_saving, total_laptop_savings = lap_save_bonus(payslip_config)
# laptop_bonus = 1000 if has laptop AND is FULL_TIME
# laptop_saving = 1000 if no laptop (deduction)
```

**Step 7: Calculate All Bonuses**
```python
bonus_points_ammount, latenight_Bonus, yearly, offpay, EOM, EOQ, EOY, 
sub_bonus, total_deduction, total_bonus = get_bonus_and_summary(
    employee, tasks, total_pay, user_data, payslip_config
)
# total_bonus = points + late_night + EOM + EOQ + EOY + holiday_pay
# Note: yearly is NOT included in total_bonus (it's separate)
```

**Step 8: Calculate Gross Pay**
```python
Logged_In_Bonus = bonus_points_ammount + login_bonus
Gross_pay = total_pay + total_bonus + login_bonus
# Note: bonus_points_ammount is just points, not monetary
# So: Gross_pay = total_pay + (late_night + EOM + holiday_pay) + login_bonus
```

**Step 9: Calculate Net Pay**
```python
net_pay = Gross_pay - total_deduction
# net_pay = (total_pay + bonuses + login_bonus) - (deductions)
```

---

### 3.2 Complete Formula Summary

**Final Payslip Amount = Net Pay**

```
Net Pay = Gross Pay - Total Deductions

Where:

Gross Pay = Base Pay + Bonuses + Login Bonus

Base Pay = Sum(task.get_pay for task in tasks)
  - If ActivityType: (points_earned / points_for_full_target) × max_earning × late_penalty
  - If no ActivityType: (point / mxpoint) × mxearning × late_penalty

Bonuses = Late Night Bonus + EOM Bonus + Holiday Pay
  - Late Night Bonus = total_pay × 0.05 (5% of base pay)
  - EOM Bonus = 1000.00 if point_percentage >= 75%
  - Holiday Pay = 3000.00 if month in (12, 1) and day in (24, 25, 26, 31, 1, 2)
  - Laptop Bonus = 1000.00 if has laptop AND is FULL_TIME

Login Bonus = total_login_hours × $5/hour (if >= 20 hours)

Total Deductions = Food + Maintenance + Health + KRA Tax + Laptop Savings + Loan Payment
  - Food & Accommodation = 1000.00 (if FULL_TIME)
  - Computer Maintenance = 500.00 (if FULL_TIME)
  - Health = 500.00 (if FULL_TIME)
  - KRA Tax = total_pay × 0.05 (5% hardcoded)
  - Laptop Savings = 1000.00 (if no laptop)
  - Loan Payment = total_pay × loan_repayment_percentage (default 20%)
```

---

### 3.3 Where Performance Pay from TaskHistory Comes In

**Location:** `coda/management/views.py` (line 1044)

**Flow:**
1. `get_tasks()` retrieves `TaskHistory` records for selected month/year
2. Filters by `daf_date__month` and `daf_date__year`
3. Calls `calculate_total_pay(tasks)` which sums `task.get_pay` for each TaskHistory
4. `TaskHistory.get_pay` uses legacy formula: `(point / mxpoint) × mxearning × late_penalty`

**Note:** TaskHistory doesn't support ActivityType, so always uses legacy formula.

---

### 3.4 Where Bonuses Are Added

**Location:** `coda/management/views.py` (lines 1062-1065, 1073)

**Bonus Sources:**

1. **From `get_bonus_and_summary()`:**
   - Late Night Bonus (5% of total_pay)
   - EOM Bonus (1000 if point_percentage >= 75%)
   - Holiday Pay (3000 in Dec/Jan)
   - **Note:** `yearly` (retirement package) is calculated but NOT added to `total_bonus`

2. **From `calculate_login_bonus()`:**
   - Login Bonus (hours × $5/hour if >= 20 hours)

3. **From `lap_save_bonus()`:**
   - Laptop Bonus (1000 if has laptop AND is FULL_TIME)
   - **Note:** This is added separately in context, not in `total_bonus`

**Final Gross Pay Calculation:**
```python
Gross_pay = total_pay + total_bonus + Decimal(login_bonus)
# total_bonus = late_night + EOM + holiday_pay (from get_bonus_and_summary)
# login_bonus = from calculate_login_bonus()
# laptop_bonus = added separately in template context
```

**Gap:** `laptop_bonus` and `yearly` are calculated but not included in `total_bonus` or `Gross_pay`.

---

### 3.5 Where Deductions Are Applied

**Location:** `coda/management/views.py` (lines 1056-1058, 1076)

**Deduction Sources:**

1. **From `deductions()`:**
   - Food & Accommodation (1000 if FULL_TIME)
   - Computer Maintenance (500 if FULL_TIME)
   - Health (500 if FULL_TIME)
   - KRA Tax (5% of total_pay, hardcoded)
   - Laptop Savings (1000 if no laptop)
   - Loan Payment (20% of total_pay, or from loan balance)

2. **Total Deductions:**
   ```python
   total_deduction = sum of all deductions above
   ```

3. **Net Pay:**
   ```python
   net_pay = Gross_pay - total_deduction
   ```

---

### 3.6 Caps, Floors, and Minimum Salary Rules

**Current Implementation:**

1. **No Minimum Salary:**
   - Employees can have `net_pay = 0` or negative (if deductions exceed earnings)

2. **Loan Payment Cap:**
   - Loan payment cannot exceed loan balance (line 539 in `loan_computation()`)

3. **Laptop Savings Cap:**
   - Laptop savings capped at 20000.00 (line 643 in `lap_save_bonus()`)

4. **No Maximum Salary Cap:**
   - No limit on total earnings

5. **Late Penalty:**
   - Applied per-task: `late_penalty = 0.98` if submitted after deadline, else `1.0`

**Gaps:**
- ❌ No minimum wage enforcement
- ❌ No maximum salary cap
- ❌ No negative pay protection (could result in negative net_pay)

---

## 4. End-to-End Flow: Tasks → TaskHistory → Payslip

### 4.1 Monthly Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ MONTH 1: Active Tasks                                          │
│                                                                 │
│ Task.objects.filter(employee=user, is_active=True)             │
│ - Points accumulate during month                                │
│ - Evidence uploaded via TaskLinks                              │
│ - Pay calculated via Task.get_pay (ActivityType or legacy)      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ MONTH 1 END: Task Reset (1st of Month 2)                       │
│                                                                 │
│ TaskResetService.reset_tasks()                                 │
│ 1. Create TaskHistory records (snapshot of Task state)        │
│    - Copy: point, mxpoint, mxearning, activity_name, etc.     │
│    - Set: daf_date = last day of Month 1                       │
│ 2. Reset Task.point = 0                                         │
│ 3. Update Task.group, Task.mxearning (if group changed)       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ MONTH 2: Payslip Calculation (for Month 1)                    │
│                                                                 │
│ payslip() view called with pay_type='task_payslip'             │
│ 1. get_tasks() retrieves TaskHistory for Month 1               │
│    - Filter: daf_date__month=Month1, daf_date__year=Year        │
│ 2. calculate_total_pay() sums TaskHistory.get_pay               │
│    - Formula: (point/mxpoint) × mxearning × late_penalty       │
│ 3. Calculate bonuses (late night, EOM, holiday, login)         │
│ 4. Calculate deductions (food, maintenance, health, tax, loan)  │
│ 5. Net Pay = (Base Pay + Bonuses) - Deductions                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ MONTH 2: Finance Integration                                   │
│                                                                 │
│ IntegratedBudgetService.get_salary_dashboard_data()            │
│ 1. Get TaskHistory for Month 1 (last month)                    │
│ 2. Calculate compliance: (total_points / total_max_points)    │
│ 3. Filter: Only compliant employees (>= 33%)                    │
│ 4. Sum salaries for compliant employees                        │
│ 5. Include in budget approval workflow                          │
└─────────────────────────────────────────────────────────────────┘
```

---

### 4.2 Detailed Flow by Component

#### Component 1: Management App (Task Tracking)

**Location:** `coda/management/`

**Flow:**
1. **Task Creation:** Admin creates `Task` objects with `mxpoint`, `mxearning`
2. **Point Accumulation:** Employees complete work, `Task.point` increments
3. **Evidence Upload:** Employees upload evidence via `TaskLinks`
4. **Monthly Reset:** `TaskResetService` creates `TaskHistory` snapshots
5. **Payslip View:** `payslip()` view calculates pay from `TaskHistory`

**Key Functions:**
- `Task.get_pay` - Calculates pay per task
- `TaskResetService.reset_tasks()` - Monthly reset
- `get_tasks()` - Retrieves tasks for payslip
- `calculate_total_pay()` - Sums task pay
- `bonus()`, `deductions()`, `loan_computation()` - Pay components

---

#### Component 2: Finance App (Salary Dashboard)

**Location:** `coda/finance/`

**Flow:**
1. **Salary Dashboard:** `salary_dashboard()` view
2. **IntegratedBudgetService:** Queries `TaskHistory` for last month
3. **Compliance Check:** Uses `ComplianceCalculator` (33% rule)
4. **Salary Calculation:** Uses `calculate_total_pay()` from management
5. **Budget Integration:** Includes compliant salaries in budget totals

**Key Functions:**
- `IntegratedBudgetService.get_salary_dashboard_data()` - Salary totals
- `IntegratedBudgetService._get_compliant_employee_salaries()` - Filter by compliance
- `EmployeeComplianceService.check_33_percent_compliance()` - Compliance check

**Integration Point:**
- Finance calls `calculate_total_pay()` from `management.utils` (direct import)
- Finance queries `TaskHistory` directly (no service layer)

---

### 4.3 Data Flow: TaskHistory → Payslip

**Step-by-Step:**

1. **TaskHistory Records Created:**
   - Source: `TaskResetService.reset_tasks()` (monthly reset)
   - Contains: `point`, `mxpoint`, `mxearning`, `daf_date`, `employee`, `activity_name`

2. **Payslip View Retrieves TaskHistory:**
   - Function: `get_tasks(employee, month, year, 'task_payslip')`
   - Query: `TaskHistory.objects.filter(daf_date__month=month, daf_date__year=year, employee=employee)`

3. **Base Pay Calculated:**
   - Function: `calculate_total_pay(tasks)`
   - Formula: `sum(task.get_pay for task in tasks)`
   - Where `task.get_pay` = `(point / mxpoint) × mxearning × late_penalty`

4. **Bonuses Added:**
   - Function: `get_bonus_and_summary()`
   - Components: Late night (5%), EOM (1000 if >= 75%), Holiday (3000 in Dec/Jan)
   - Plus: Login bonus (hours × $5)

5. **Deductions Applied:**
   - Function: `deductions()`
   - Components: Food (1000), Maintenance (500), Health (500), Tax (5%), Laptop (1000), Loan (20%)

6. **Net Pay Calculated:**
   - Formula: `(Base Pay + Bonuses) - Deductions`

---

## 5. Duplication and Risk Analysis

### 5.1 Pay Calculation Duplication

**Location 1: `calculate_total_pay()` in `management/utils.py`**
- **What:** Sums `task.get_pay` for tasks
- **Used By:** `payslip()` view, `get_tasks()`, `IntegratedBudgetService`

**Location 2: `Task.get_pay` property**
- **What:** Calculates pay per task (ActivityType or legacy)
- **Used By:** `calculate_total_pay()`

**Location 3: `TaskHistory.get_pay` property**
- **What:** Calculates pay per TaskHistory (legacy only)
- **Used By:** `calculate_total_pay()` when processing TaskHistory

**Location 4: `IntegratedBudgetService._get_compliant_employee_salaries()`**
- **What:** Directly calls `calculate_total_pay()` and also calculates compliance
- **Used By:** Finance salary dashboard

**Duplication Issues:**
- ❌ Same calculation logic in multiple places
- ❌ TaskHistory always uses legacy (no ActivityType support)
- ❌ Finance directly imports from `management.utils` (tight coupling)

---

### 5.2 Hard-Coded Logic in Views

**Location:** `coda/management/views.py` (lines 1011-1142)

**Hard-Coded Values:**

1. **KRA Tax Rate:**
   ```python
   kra_percentage = Decimal('0.05')  # Line 657 in utils.py
   kra = round(Decimal(total_pay) * kra_percentage, 2)
   ```
   - **Issue:** Should be in PayslipConfig

2. **Login Bonus Threshold/Rate:**
   ```python
   threshold=Decimal(20.00)  # Default in calculate_login_bonus()
   hourly_rate=Decimal(5)     # Default in calculate_login_bonus()
   ```
   - **Issue:** Should be in PayslipConfig

3. **EOM Eligibility Threshold:**
   ```python
   EOM = payslip_config.eom_bonus if point_percentage>=75 else Decimal(0.00)
   ```
   - **Issue:** Hardcoded 75% threshold

4. **FULL_TIME Applicant Check:**
   ```python
   if employee.category == CategoryChoices.APPLICANT and employee.sub_category == ApplicantSubCategoryChoices.FULL_TIME:
   ```
   - **Issue:** Hardcoded category/subcategory check

5. **Holiday Pay Dates:**
   ```python
   offpay = payslip_config.holiday_pay if month in (12, 1) and day in (24, 25, 26, 31, 1, 2) else Decimal(0.00)
   ```
   - **Issue:** Hardcoded month/day logic

---

### 5.3 Manual Override Fields

**Current Override Mechanisms:**

1. **PayslipConfig Fields:**
   - All bonus/deduction amounts can be overridden per employee
   - `loan_repayment_percentage` can be adjusted
   - `rp_starting_amount` can be manually set

2. **No Explicit Override Field:**
   - ❌ No `additional_adjustment` field in PayslipConfig
   - ❌ No `manual_override_amount` field
   - ❌ No `override_reason` field

**How Overrides Are Done Today:**
- Admin manually edits `PayslipConfig` fields
- Admin manually adjusts `Task.point` or `Task.mxearning`
- No audit trail for overrides

**Gaps:**
- ❌ No override tracking
- ❌ No override approval workflow
- ❌ No override reason/justification

---

### 5.4 Risk Areas

**1. Negative Net Pay:**
- **Risk:** If deductions exceed earnings, `net_pay` can be negative
- **Location:** `payslip()` view (line 1076)
- **Current:** No protection

**2. Loan Payment Exceeds Balance:**
- **Mitigation:** Checked in `loan_computation()` (line 539)
- **Status:** ✅ Protected

**3. Division by Zero:**
- **Risk:** `point / mxpoint` if `mxpoint = 0`
- **Location:** `Task.get_pay`, `TaskHistory.get_pay`
- **Current:** Handled with try/except, returns 0

**4. Inconsistent Pay Calculations:**
- **Risk:** Task uses ActivityType, TaskHistory uses legacy
- **Location:** `Task.get_pay` vs `TaskHistory.get_pay`
- **Current:** ⚠️ Inconsistency exists

**5. Evidence Not Enforced:**
- **Risk:** Tasks without evidence still included in pay
- **Location:** `calculate_total_pay()` doesn't check evidence
- **Current:** ❌ No enforcement

---

## 6. Existing Motivation Levers

### 6.1 Employee of the Month (EOM)

**Implementation:**
- **Location:** `coda/management/utils.py` (line 724)
- **Formula:** `payslip_config.eom_bonus if point_percentage >= 75 else 0`
- **Amount:** 1000.00 (default)
- **Eligibility:** `point_percentage = (total_points / total_max_points) × 100 >= 75%`

**Status:** ✅ Implemented and active

**Gaps:**
- ❌ Hardcoded 75% threshold (should be configurable)
- ❌ No tracking of who won EOM
- ❌ No quarterly/yearly awards (EOQ/EOY defined but not used)

---

### 6.2 Late Penalty

**Implementation:**
- **Location:** `coda/management/models.py` (lines 604-608, 1027-1031)
- **Formula:** `0.98 if submitted > deadline else 1.0`
- **Applied To:** Each task's `get_pay` calculation
- **Effect:** 2% reduction in pay for late tasks

**Status:** ✅ Implemented and active

**Gaps:**
- ❌ Hardcoded 0.98 penalty (should be configurable)
- ❌ No graduated penalty (same penalty regardless of how late)

---

### 6.3 On-Time Completion Bonuses

**Current Implementation:**
- **None:** No explicit on-time completion bonus
- **Implicit:** Avoiding late penalty (0.98) is the "bonus"

**Potential:**
- Could add bonus for 100% completion before deadline
- Could add bonus for early completion

---

### 6.4 Group-Based Bonuses

**Implementation:**
- **Location:** `coda/management/utils.py` (lines 372-395)
- **Function:** `increment_in_graduation_of_employee()`
- **Logic:**
  - **Group H:** Increments `mxearning` after 30 hours: `mxearning += (total_point // 3)`
  - **Group I:** No earning (`mxearning = 0`)
  - **Other Groups:** Increments `mxearning` when group changes via `web_delta` percentage

**Status:** ✅ Implemented in task reset logic

**Gaps:**
- ❌ Group-based bonuses affect `mxearning` (future pay), not current pay
- ❌ No direct group-based bonus in payslip calculation

---

### 6.5 KPI/Score Fields Used for Awards

**Current KPIs:**

1. **Point Percentage:**
   - **Calculation:** `(total_points / total_max_points) × 100`
   - **Used For:** EOM eligibility (>= 75%)
   - **Location:** `employee_reward()` function

2. **Total Points:**
   - **Calculation:** `Sum(task.point)`
   - **Used For:** Display only (shown as `bonus_points_ammount` but not monetary)

3. **Completion Rate:**
   - **Calculation:** Same as point percentage
   - **Used For:** Compliance checking (33% threshold)

**Gaps:**
- ❌ No other KPIs used for bonuses
- ❌ No performance score aggregation
- ❌ No department-level bonuses

---

### 6.6 Other Motivation Levers

**1. Login Bonus:**
- **Amount:** `total_login_hours × $5/hour` (if >= 20 hours)
- **Purpose:** Reward consistent attendance
- **Status:** ✅ Active

**2. Holiday Pay:**
- **Amount:** 3000.00
- **When:** December 24-26, 31, January 1-2
- **Status:** ✅ Active

**3. Late Night Bonus:**
- **Amount:** `total_pay × 5%`
- **Purpose:** Reward working late (retirement package increment)
- **Status:** ✅ Active (but uses `rp_increment_max_percentage`, not `night_bonus`)

**4. Laptop Bonus:**
- **Amount:** 1000.00
- **When:** Employee has laptop AND is FULL_TIME
- **Status:** ✅ Active

---

## 7. Unified PayCalculationService Design

### 7.1 Where It Should Sit

**Recommended Location:** `coda/management/services/pay_calculation_service.py`

**Rationale:**
- Management app owns Task/TaskHistory models
- Pay calculation is primarily based on tasks
- Finance app should consume via service, not direct model access

---

### 7.2 Service Interface Design

**Proposed Structure:**

```python
class PayCalculationService:
    """
    Unified service for calculating employee payslip amounts.
    
    Single source of truth for:
    - Base pay calculation (TaskHistory → earnings)
    - Bonus calculation (EOM, login, holiday, etc.)
    - Deduction calculation (tax, loan, laptop, etc.)
    - Net pay calculation
    """
    
    def calculate_payslip(
        self,
        employee: User,
        target_month: int,
        target_year: int,
        include_bonuses: bool = True,
        include_deductions: bool = True,
        enforce_evidence: bool = False
    ) -> Dict[str, Any]:
        """
        Calculate complete payslip for an employee.
        
        Returns:
            {
                'base_pay': Decimal,
                'bonuses': {
                    'late_night': Decimal,
                    'eom': Decimal,
                    'holiday': Decimal,
                    'login': Decimal,
                    'laptop': Decimal,
                    'total': Decimal
                },
                'deductions': {
                    'food_accommodation': Decimal,
                    'computer_maintenance': Decimal,
                    'health': Decimal,
                    'kra_tax': Decimal,
                    'laptop_savings': Decimal,
                    'loan_payment': Decimal,
                    'total': Decimal
                },
                'gross_pay': Decimal,
                'net_pay': Decimal,
                'compliance_rate': float,
                'is_compliant': bool,
                'evidence_coverage': float,
                'tasks': [...],  # TaskHistory records used
                'calculation_details': {...}
            }
        """
```

---

### 7.3 How Finance Should Call It

**Current (WRONG):**
```python
# Finance directly imports from management
from management.utils import calculate_total_pay
from management.models import TaskHistory

# Direct query
tasks = TaskHistory.objects.filter(...)
total_pay = calculate_total_pay(tasks)
```

**Proposed (CORRECT):**
```python
# Finance uses service interface
from management.services.pay_calculation_service import PayCalculationService

pay_service = PayCalculationService()
payslip_data = pay_service.calculate_payslip(
    employee=employee,
    target_month=target_month,
    target_year=target_year,
    enforce_evidence=True  # Finance can enforce evidence
)

total_pay = payslip_data['net_pay']  # Or gross_pay, depending on need
```

---

### 7.4 Input Sources

**Service Should Receive:**

1. **TaskHistory Records:**
   - Source: `TaskHistory.objects.filter(daf_date__month=month, daf_date__year=year, employee=employee)`
   - Service should query internally, not receive as parameter

2. **PayslipConfig:**
   - Source: `PayslipConfig.objects.get(user=employee)` or default
   - Service should resolve internally

3. **LoanApplication:**
   - Source: `LoanApplication.objects.filter(borrower=employee, status='active')`
   - Service should query internally

4. **LoginHistory:**
   - Source: `LoginHistory.objects.filter(user=employee, login_time__month=month)`
   - Service should query internally

**Service Should NOT Receive:**
- ❌ Pre-calculated `total_pay` (should calculate internally)
- ❌ Pre-filtered tasks (should query internally)
- ❌ PayslipConfig instance (should resolve internally)

---

### 7.5 Integration Points

**1. Management Payslip View:**
```python
# Current
def payslip(request):
    tasks, total_pay, message = get_tasks(...)
    # ... manual calculation ...
    net_pay = Gross_pay - total_deduction

# Proposed
def payslip(request):
    pay_service = PayCalculationService()
    payslip_data = pay_service.calculate_payslip(employee, month, year)
    context = {'payslip_data': payslip_data}
    return render(request, 'payslip.html', context)
```

**2. Finance Salary Dashboard:**
```python
# Current
def _get_compliant_employee_salaries(...):
    tasks = TaskHistory.objects.filter(...)
    employee_salary = calculate_total_pay(tasks)  # Direct import

# Proposed
def _get_compliant_employee_salaries(...):
    pay_service = PayCalculationService()
    for employee in employees:
        payslip_data = pay_service.calculate_payslip(employee, month, year)
        if payslip_data['is_compliant']:
            employee_salary = payslip_data['net_pay']
```

**3. Compliance Calculator:**
```python
# Current
def calculate_compliance(...):
    tasks = TaskHistory.objects.filter(...)
    total_earnings = Sum(F('point') / F('mxpoint') * F('mxearning'))

# Proposed
def calculate_compliance(...):
    pay_service = PayCalculationService()
    payslip_data = pay_service.calculate_payslip(employee, month, year)
    return {
        'is_compliant': payslip_data['is_compliant'],
        'completion_rate': payslip_data['compliance_rate'],
        'total_earnings': payslip_data['base_pay']
    }
```

---

### 7.6 Extension Points for AI

**1. AI-Suggested Bonuses:**
- **Hook:** `PayCalculationService._calculate_ai_bonuses()`
- **Input:** TaskHistory patterns, performance metrics
- **Output:** Suggested bonus amounts with confidence scores

**2. Anomaly Detection:**
- **Hook:** `PayCalculationService._detect_anomalies()`
- **Input:** Payslip data, historical patterns
- **Output:** Risk scores, fraud flags

**3. Evidence Validation:**
- **Hook:** `PayCalculationService._validate_evidence()`
- **Input:** Tasks, TaskLinks
- **Output:** Evidence coverage, missing evidence flags

**4. Performance-Based Adjustments:**
- **Hook:** `PayCalculationService._apply_performance_adjustments()`
- **Input:** KPI scores, historical performance
- **Output:** Performance multipliers, adjustments

---

## 8. Summary: Reusable vs Replace

### 8.1 Reusable Building Blocks

**✅ Keep As-Is or Lightly Refactor:**

1. **PayslipConfig Model**
   - ✅ Solid configuration structure
   - **Action:** Add missing fields (tax_rate, login_bonus_threshold, eom_threshold)

2. **LoanApplication Model**
   - ✅ Clean loan tracking
   - **Action:** Keep, integrate into PayCalculationService

3. **LoginHistory Integration**
   - ✅ `calculate_login_bonus()` function works
   - **Action:** Move to PayCalculationService, make configurable

4. **ComplianceCalculator**
   - ✅ Single source of truth for 33% rule
   - **Action:** Keep, integrate into PayCalculationService

---

### 8.2 Things We Should Wrap, Not Bypass

**✅ Extend Existing Functions:**

1. **`calculate_total_pay()` Function**
   - ✅ Core logic is correct
   - **Action:** Move to PayCalculationService, add evidence validation

2. **`bonus()` Function**
   - ✅ Bonus calculation logic is correct
   - **Action:** Move to PayCalculationService, make thresholds configurable

3. **`deductions()` Function**
   - ✅ Deduction logic is correct
   - **Action:** Move to PayCalculationService, add tax rate configuration

---

### 8.3 Things That Should Be Deprecated or Replaced

**❌ Replace:**

1. **Payslip Calculation in View Layer**
   - **Location:** `coda/management/views.py` (lines 1011-1142)
   - **Issue:** Business logic in view, not reusable
   - **Action:** Move to PayCalculationService

2. **Direct Finance Imports from Management Utils**
   - **Location:** `coda/finance/services/integrated_budget_service.py` (line 27)
   - **Issue:** Tight coupling, direct import
   - **Action:** Use PayCalculationService interface

3. **Hard-Coded Values**
   - **Locations:** Multiple (tax rate, login bonus threshold, EOM threshold)
   - **Issue:** Not configurable
   - **Action:** Move to PayslipConfig or settings

4. **Duplicate Pay Calculations**
   - **Locations:** `calculate_total_pay()`, `Task.get_pay`, `TaskHistory.get_pay`, `IntegratedBudgetService`
   - **Issue:** Inconsistent formulas
   - **Action:** Unify in PayCalculationService

---

### 8.4 Extension Points for AI

**🎯 Best Spots to Plug AI:**

1. **Bonus Optimization**
   - **Service:** PayCalculationService
   - **Method:** `_calculate_ai_bonuses()`
   - **Hook:** After base pay calculated, before final bonuses
   - **Purpose:** Suggest optimal bonus amounts based on performance patterns

2. **Anomaly Detection**
   - **Service:** PayCalculationService
   - **Method:** `_detect_payroll_anomalies()`
   - **Hook:** After payslip calculated
   - **Purpose:** Flag suspicious patterns (high pay, no evidence, etc.)

3. **Evidence Validation**
   - **Service:** PayCalculationService
   - **Method:** `_validate_evidence_requirements()`
   - **Hook:** Before base pay calculated
   - **Purpose:** Enforce evidence requirements for billable activities

4. **Performance Prediction**
   - **Service:** PayCalculationService
   - **Method:** `_predict_future_earnings()`
   - **Hook:** After historical analysis
   - **Purpose:** Forecast next month's earnings based on patterns

---

## 9. Critical Gaps and Recommendations

### 9.1 Critical Gaps

1. **No Unified Pay Calculation Service**
   - **Impact:** Duplication, inconsistency, hard to test
   - **Recommendation:** Create `PayCalculationService` as single source of truth

2. **Evidence Not Enforced for Salary**
   - **Impact:** Billable activities can have pay without evidence
   - **Recommendation:** Add evidence validation to pay calculation

3. **Hard-Coded Tax/Deduction Rates**
   - **Impact:** Not configurable, hard to update
   - **Recommendation:** Move to PayslipConfig or settings

4. **TaskHistory Doesn't Support ActivityType**
   - **Impact:** Inconsistent pay calculations (Task vs TaskHistory)
   - **Recommendation:** Add `activity_type` FK to TaskHistory, migrate data

5. **No Negative Pay Protection**
   - **Impact:** Employees could have negative net pay
   - **Recommendation:** Add minimum wage or negative pay protection

6. **EOQ/EOY Bonuses Not Implemented**
   - **Impact:** Defined in PayslipConfig but never used
   - **Recommendation:** Implement or remove from model

---

### 9.2 Recommended Next Steps

**Phase 1: Create PayCalculationService**
1. Create `coda/management/services/pay_calculation_service.py`
2. Move `calculate_total_pay()`, `bonus()`, `deductions()` logic into service
3. Add evidence validation integration
4. Add ActivityType support

**Phase 2: Refactor Views**
1. Update `payslip()` view to use PayCalculationService
2. Remove business logic from view layer
3. Update Finance views to use service

**Phase 3: Configuration**
1. Add missing fields to PayslipConfig (tax_rate, thresholds)
2. Remove hard-coded values
3. Add override tracking fields

**Phase 4: AI Integration**
1. Add AI hooks to PayCalculationService
2. Implement anomaly detection
3. Add performance-based adjustments

---

**Report Generated:** December 2025  
**Branch:** `25.12_CODA_DEV_CM`  
**Status:** Ready for unified PayCalculationService design







