# Managed Options Trading - Testing
**Feature:** CODA Managed Options Trading Service  
**Date:** November 8, 2025  
**Status:** 🧪 Testing Plan (Phase 2 coverage in progress)

---

## 🎯 Testing Strategy

### **Testing Pyramid**

```
             /\
            /  \
           / E2E\ ──────► 10% - End-to-End Tests
          /──────\
         /        \
        /Integration\ ───► 30% - Integration Tests
       /────────────\
      /              \
     /   Unit Tests   \ ─► 60% - Unit Tests
    /──────────────────\
```

**Target Coverage:** 80%+

---

## 🧪 Unit Tests

### **Phase 1 & 2 Coverage**
- ✅ `tests/apps/investing/01_unit/test_unusual_whales_service.py`
  - Verifies flow score math, caching wrapper, and put-score inversion (cache hits tracked).
- ✅ `tests/apps/investing/01_unit/test_capital_allocation_service.py`
  - Ensures position sizing caps at 10% of sleeve, enforces $420 target, considers debit spread fallback.
- ✅ `tests/apps/investing/01_unit/test_notification_service.py`
  - Confirms allocation digest recipients are limited to superusers + configured group, and emails skip when recipient list is empty.
- ✅ `tests/apps/investing/01_unit/test_services.py`
  - Validates `ManagedTradingService.get_income_summary()` coverage %, target gaps, and Unusual Whales timeline metadata powering the Phase 3 dashboard.
- ✅ `tests/apps/investing/01_unit/test_services.py::BrokerAPIServiceTests`
  - Ensures broker credentials encrypt correctly and broker sync upserts positions as expected.
- ✅ `tests/apps/investing/01_unit/test_services.py::PredictiveAnalyticsServiceTests`
  - Exercises fallback forecasting and minimum-history guard for predictive analytics.
- 🚀 `tests/apps/investing/01_unit/test_notification_templates.py`
  - Guards WhatsApp/email scenario digests for placeholder variables.

### **Test File: `tests/test_managed_trading_models.py`**

```python
from django.test import TestCase
from decimal import Decimal
from datetime import date, timedelta

from investing.models import ManagedTradingAccount, OptionsPosition
from accounts.models import CustomerUser


class ManagedTradingAccountTestCase(TestCase):
    def setUp(self):
        self.client_user = CustomerUser.objects.create_user(
            username='test_client',
            email='client@test.com',
            password='test123'
        )
        
        self.account = ManagedTradingAccount.objects.create(
            client=self.client_user,
            account_name='Test Account',
            account_number='CODA-OPT-TEST-001',
            initial_capital=Decimal('30000.00'),
            current_balance=Decimal('30000.00'),
            cash_available=Decimal('30000.00'),
            cash_reserved=Decimal('0.00')
        )
    
    def test_win_rate_calculation(self):
        """Test win rate property calculation"""
        self.account.total_trades = 10
        self.account.winning_trades = 7
        self.account.save()
        
        self.assertEqual(self.account.win_rate, 70.0)
    
    def test_roi_calculation(self):
        """Test ROI property calculation"""
        self.account.total_profit_loss = Decimal('1500.00')
        self.account.save()
        
        self.assertEqual(self.account.return_on_investment, 5.0)
    
    def test_available_buying_power(self):
        """Test available buying power calculation"""
        self.account.cash_available = Decimal('30000.00')
        self.account.cash_reserved = Decimal('17000.00')
        self.account.save()
        
        self.assertEqual(self.account.available_buying_power, Decimal('13000.00'))


class OptionsPositionTestCase(TestCase):
    # Test position creation, P&L calculations, etc.
    pass
```

---

## 🔄 Integration Tests

### **Phase 1 & 2 Addendum: Managed Income Automation**
- ✅ `tests/apps/investing/02_integration/test_phase1_features.py`
  - Extends coverage for UW enrichment + heatmap context.
- 🚀 `tests/apps/investing/02_integration/test_capital_allocation.py`
  - Verifies `CapitalAllocationService` sizing logic meets $420/mo target.
  - Mocks `UnusualWhalesService` to confirm cache hit path is used (no duplicate API calls).
- 🚧 `tests/apps/investing/03_system/test_managed_income_scheduler.py`
  - Currently skipped (`TODO-managed-income`) until legacy account/investing migrations are generated.
  - Once migrations land, execute to cover Celery beat path (fetch → allocate → digest notification).
- ✅ `tests/apps/investing/02_integration/test_staff_dashboard_preview.py`
  - Confirms strategy legs render in modal and "Preview Trade" button appears only for staff.
- 🚀 `tests/apps/investing/02_integration/test_client_dashboard_income.py`
  - Validates client sees income vs $420 target but no execution instructions.
- 🧪 `tests/apps/investing/02_integration/test_auto_ranking.py` *(planned)*
  - Will exercise `PositionRankingService.auto_approve_top_positions`, ensure system flags and notifications fire.
- 🚧 `tests/apps/investing/02_integration/test_account_limit_controls.py`
  - New scaffolding for risk guardrail UI; currently skipped with `@skipIf` until legacy migrations are restored.
- ✅ `tests/apps/investing/02_integration/test_views.py::ManagedAccountPhase3ViewTest`
  - Exercises Phase 3 dashboard copy, scenario slider JSON defaults, and verifies the page remains read-only for managed clients.
- ✅ `tests/apps/investing/02_integration/test_views.py::BrokerSyncViewTest`
  - Verifies staff-only broker sync endpoint wiring and permission guard.
- ✅ `tests/apps/investing/02_integration/test_views.py::AccountAnalyticsViewTest`
  - Confirms predictive analytics page renders for staff accounts with sufficient history.
- 🚀 `tests/apps/investing/02_integration/test_client_managed_dashboard.py`
  - Legacy scaffold kept for future E2E flow; high-level assertions now live in `test_views.py`.

### **Test File: `tests/test_managed_trading_service.py`**

```python
from django.test import TestCase
from investing.services.managed_trading_service import ManagedTradingService


class ManagedTradingServiceTestCase(TestCase):
    def test_create_account_workflow(self):
        """Test complete account creation workflow"""
        service = ManagedTradingService()
        
        account_data = {
            'account_name': 'Test Client Account',
            'initial_capital': '30000.00',
            'management_fee': '1.50',
            'performance_fee': '20.00'
        }
        
        account = service.create_managed_account(self.client_user, account_data)
        
        # Verify account created
        self.assertIsNotNone(account.id)
        self.assertEqual(account.current_balance, Decimal('30000.00'))
        
        # Verify trading rules created
        self.assertTrue(account.trading_rules.exists())
    
    def test_position_entry_and_close(self):
        """Test complete position lifecycle"""
        # Create position
        # Monitor position
        # Close position
        # Verify P&L updated
        pass
```

---

## 🌐 End-to-End Tests

### **Environment & Tooling Notes (Updated)**
- Set `TEST_MODE=True` in `.env` (switches to SQLite, avoids Postgres `CREATEDB` requirement).
- Export `UW_API_MOCK_FIXTURE=tests/fixtures/uw_sample.json` to reuse canned responses and prevent live API calls.
- Use `pytest -k managed_options --ds=coda_project.settings` for focused runs; Django test runner also supported.
- Always run `python manage.py collectstatic --noinput` on UAT before selenium tests to ensure latest assets.

### **Test Scenarios**

#### **E2E Test 1: Complete Account Setup**
```
1. Admin logs in
2. Creates new managed account for client
3. Sets risk parameters
4. Activates account
5. Verifies account appears in list
6. Client logs in and sees dashboard
```

#### **E2E Test 2: Complete Position Lifecycle**
```
1. Trader identifies opportunity
2. Enters position via form
3. System validates against rules
4. Position created successfully
5. System monitors position
6. Profit target reached
7. Alert generated
8. Trader closes position
9. P&L updated
10. Client notified
```

#### **E2E Test 4: CSV Upload with UW Auto-Enrichment**
```
1. Staff uploads CSV with 5 symbols (TEST_MODE mocks UW response)
2. System converts rows to SuggestedPosition records
3. UW cache hit ensures only one API call per symbol
4. Flow scores and timing signals appear in dashboard (🟢/🟡/🔴)
5. "Preview Trade" modal displays leg breakdown
6. Staff approves top 5
```

#### **E2E Test 5: Managed Income Scenario Digest**
```
1. Staff opens managed account dashboard
2. Clicks "Send Scenario Digest"
3. ScenarioProjectionService computes base/+10K/+25K cases
4. WhatsApp + email messages queued via NotificationService
5. CommunicationLog records outreach with timestamp and staff id
6. Client dashboard shows updated income vs target the next day
```

#### **E2E Test 3: Risk Alert Workflow**
```
1. Position loses money
2. Stop loss threshold hit
3. Critical alert generated
4. Email sent to trader
5. Trader reviews position
6. Position closed
7. Loss recorded
8. Account updated
```

#### **E2E Test 6: Auto-Approval & Batch Timeout Flow**
```
1. Ensure at least 5 pending SuggestedPosition records exist (use CSV upload or fetch command)
2. Run `python manage.py auto_approve_top_positions --count=2`
3. Verify two top-ranked suggestions move to `approved` with `auto_approved_by_system=True`
4. Trigger `python manage.py process_batch_approvals` with a batch older than 3 hours
5. Confirm batch status becomes `auto_approved` and client dashboard loads the "Awaiting Trader Execution" card
6. Check staff email inbox for the auto-approval summaries (suggestions + batch)
7. Open `/investing/managed/portal/` as client and ensure CTA is disabled until trader confirms
```

---

## ✅ Test Cases

### **Critical Test Cases (Must Pass)**

#### **TC-001: Account Creation**
- **Given:** Valid client and account data
- **When:** Admin creates managed account
- **Then:** Account created with correct balance, rules generated, activity logged

#### **TC-002: Position Entry Validation**
- **Given:** Position data that exceeds buying power
- **When:** Trader attempts to create position
- **Then:** Validation error, position not created

#### **TC-003: Stop Loss Trigger**
- **Given:** Position with unrealized loss = 200% of premium
- **When:** Monitoring service runs
- **Then:** Critical alert generated, trader notified

#### **TC-004: Profit Target**
- **Given:** Position with profit = 50% of max
- **When:** Monitoring service runs
- **Then:** Alert generated recommending close

#### **TC-005: Fee Calculation**
- **Given:** Account with profit above threshold
- **When:** Monthly fee calculation runs
- **Then:** Correct management and performance fees calculated

#### **TC-006: Auto-Approve Top Suggestions**
- **Given:** 4+ pending `SuggestedPosition` records with ranking metadata
- **When:** `auto_approve_top_positions` management command runs (count=2)
- **Then:** Two suggestions move to `approved` with `auto_approved_by_system=True`, remaining suggestions stay pending, notification email sent to staff

---

## 📊 Performance Tests

### **Load Test Scenarios**

#### **Test 1: 50 Accounts, 250 Positions**
```python
# Measure:
- Dashboard load time
- Position monitoring time
- Report generation time
- Database query performance

# Acceptance:
- Dashboard: <3 seconds
- Monitoring: <30 seconds
- Reports: <10 seconds each
```

#### **Test 2: Real-time Updates**
```python
# Simulate:
- 50 concurrent users
- Accessing dashboards simultaneously
- Position updates every 15 seconds

# Acceptance:
- No timeouts
- All data accurate
- Response time <2 seconds
```

---

## 🐛 Bug Tracking Template

```markdown
### Bug #XXX
**Severity:** [Critical/High/Medium/Low]
**Component:** [Account/Position/Risk/Reporting]
**Environment:** [Local/UAT/Production]

**Description:**
[Clear description of the bug]

**Steps to Reproduce:**
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Expected Result:**
[What should happen]

**Actual Result:**
[What actually happened]

**Error Message:**
```
[Paste any error messages]
```

**Screenshots:**
[Attach if available]

**Additional Context:**
- Browser: [Chrome/Firefox/Safari]
- User Role: [Admin/Manager/Client]
- Account: [CODA-OPT-XXX]
```

---

## ✅ Testing Checklist

### **Pre-Deployment Testing**
- [ ] All unit tests passing (60+ tests)
- [ ] All integration tests passing (20+ tests)
- [ ] End-to-end workflows tested
- [ ] Performance tests passed
- [ ] Security audit completed
- [ ] Code coverage >80%
- [ ] No critical or high bugs
- [ ] All documentation updated
- [ ] Client UAT completed
- [ ] Regulatory compliance verified

---

**Next Phase:** [06_MAINTENANCE.md](06_MAINTENANCE.md)  
**Previous Phase:** [04_IMPLEMENTATION.md](04_IMPLEMENTATION.md)  
**Return to:** [README.md](README.md)

