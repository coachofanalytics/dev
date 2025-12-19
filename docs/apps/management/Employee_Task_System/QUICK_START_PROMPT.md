# Quick Start Prompt - CODA Pay System

> **⚠️ IMPORTANT:** This is a quick reference only.  
> **📖 For complete information, see the Master Document:**  
> **`docs/03_IMPLEMENTATION/COMPREHENSIVE_CONTEXT_PROMPT.md`**

**Copy this into a new chat to pick up where we left off.**

---

You are working on the CODA Django monolith, branch `25.12_CODA_DEV_CM`.

**🎯 Master Document:** `docs/03_IMPLEMENTATION/MASTER_CODA_TASK_PAY_CAREER_DAF_SYSTEM.md` - This is the single source of truth. 

## ✅ Completed Work

**All Phases Complete:**
- ✅ **Phase T2:** ActivityType System (49 tests passing)
- ✅ **Phase P1:** PayCalculationService (7 tests passing)
- ✅ **Phase P2:** Payslip View Refactoring (verified)
- ✅ **Phase P3:** Earned vs Released Separation (10 tests passing)

**See Master Document for complete details:** `COMPREHENSIVE_CONTEXT_PROMPT.md`

## 🎯 Current Status

**Phase P3 is COMPLETE.** All tests passing.

**Next:** Phase P4 (Quality Gates - Future)

Read the design document: `docs/03_IMPLEMENTATION/PAY_SYSTEM_PHASE_P3_33_RULE_BASE_STIPEND_DESIGN.md`

### Key Requirements:

1. **Extend PayCalculationService** to separate:
   - `earned_amount_n` = Month N earnings (from TaskHistory)
   - `released_amount_n` = Portion actually paid (controlled by 33% rule)
   - `locked_amount_n` = `earned_amount_n - released_amount_n`

2. **Add Base Stipend** calculation:
   - Only for tenured employees (12+ months)
   - Compliance-scaled: 0% at 33%, 50% at ~66.5%, 100% at 100%
   - Formula: `stipend = base_stipend * ((compliance_rate - 33) / 67)`
   - Treated as release-time component (not part of Month N earning)

3. **Integrate 33% Rule:**
   - Use `ComplianceCalculator` and `EmployeeComplianceService`
   - Rule active after 15th of Month N+1
   - Controls release timing, not whether earnings exist

4. **Configuration:**
   - Add to Django settings (NOT PayslipConfig yet):
     - `PAYROLL_BASE_STIPEND_AMOUNT = Decimal('2500.00')`
     - `PAYROLL_MIN_STIPEND_TENURE_MONTHS = 12`

### Constraints:

- ❌ **Do NOT** add fields to PayslipConfig yet
- ❌ **Do NOT** create MonthlyEarningsSnapshot model yet
- ✅ Maintain 100% backward compatibility
- ✅ All existing tests must still pass

## 📁 Key Files

- Service: `coda/management/services/pay_calculation_service.py`
- Compliance: `coda/management/services/compliance_calculator.py`
- Compliance Service: `coda/management/services/employee_compliance_service.py`
- View: `coda/management/views.py` (payslip function)
- Design: `docs/03_IMPLEMENTATION/PAY_SYSTEM_PHASE_P3_33_RULE_BASE_STIPEND_DESIGN.md`

## 🧪 Testing

- Run tests: `python manage.py test management.tests.test_pay_calculation_service_integration --keepdb`
- Verify backward compatibility with regression tests
- All 7 integration tests currently passing

## 📖 Full Context

**🎯 MASTER DOCUMENT:** `docs/03_IMPLEMENTATION/MASTER_CODA_TASK_PAY_CAREER_DAF_SYSTEM.md`

This is the **single source of truth** containing:
- Complete implementation details
- All test results
- File locations
- Technical patterns
- Business rules
- Next steps

**Always refer to the Master Document for complete information.**

---

**Status:** ✅ Phase P1, P2 & P3 Complete | 🎯 Ready for Phase P4

