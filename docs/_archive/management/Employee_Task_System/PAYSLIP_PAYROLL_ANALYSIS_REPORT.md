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

*(truncated – see original report for full details)*





