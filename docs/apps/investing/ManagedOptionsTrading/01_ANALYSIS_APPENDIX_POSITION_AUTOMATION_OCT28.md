# Automated Position Sourcing - Codebase Analysis
**Date:** October 28, 2025  
**Goal:** Automate position fetching from OptionPlay/Thinkorswim to replace manual entry

---

## 🔍 **EXISTING INFRASTRUCTURE (What We Can Reuse)**

### ✅ **1. Position Management System - FULLY BUILT**

**Model:** `OptionsPosition` (`coda/investing/models.py`, lines 2029-2300)
- ✅ Complete position data structure (symbol, strategy, legs, Greeks, P&L)
- ✅ Multi-leg support via `positions` JSONField
- ✅ Batch linkage via `batch` ForeignKey
- ✅ Approval tracking (`requires_client_approval`, `approved_at`, `approval_method`)
- ✅ Status workflow: pending → open → closed

**Service:** `ManagedTradingService.create_position()` (`coda/investing/services/managed_trading_service.py`, line 205)
- ✅ Creates positions with validation
- ✅ Updates account balances (cash_reserved, cash_available)
- ✅ Logs trading activity
- ✅ Validates against trading rules

**Form:** `OptionsPositionForm` (`coda/investing/forms.py`, lines 331-368)
- ✅ Handles manual position entry
- ✅ JSONField widget for multi-leg positions

**REUSE:** ✅ All of this! Just need to populate position_data from API instead of form

---

### ✅ **2. Batch Approval System - FULLY BUILT**

**Model:** `PositionBatch` (`coda/investing/models.py`, lines 3014-3177)
- ✅ Weekly batch container for positions
- ✅ 24-hour approval deadline
- ✅ Status: pending → approved/rejected/expired
- ✅ Methods: `approve_all()`, `reject_all()`, `expire_batch()`

**Service:** `BatchApprovalService` (`coda/investing/services/batch_approval_service.py`)
- ✅ `create_weekly_batch()` - Groups pending positions into batch
- ✅ `get_batch_summary()` - Calculates totals, risk
- ✅ `approve_batch()`, `reject_batch()`, `process_timeouts()`

**Views:** `batches.py` (`coda/investing/views/managed_trading/batches.py`)
- ✅ Client approval interface
- ✅ Staff batch management
- ✅ Individual position review

**REUSE:** ✅ Perfect! Just need to create positions with `status='pending'` and `requires_client_approval=True`

---

### ✅ **3. OptionPlay Integration Service - 80% BUILT!**

**File:** `coda/investing/services/optionplay_integration_service.py`

**What Exists:**
- ✅ `OptionPlayIntegrationService` class
- ✅ `get_top_positions()` method (fetches top 5 recommendations)
- ✅ `_get_stock_data()` - Gets current stock price
- ✅ `_get_options_chain()` - Gets options chain
- ✅ `_generate_recommendations()` - AI-powered suggestions
- ✅ Strategy generators:
  - `_generate_income_strategies()` (puts, spreads)
  - `_generate_directional_strategies()` (covered calls)
  - `_generate_volatility_strategies()` (iron condor)
- ✅ `calculate_realistic_metrics()` - Greeks, capital, P&L
- ✅ Mock fallback data when API unavailable

**What's Missing:**
- ❌ Real OptionPlay API authentication (currently mock)
- ❌ Filtering by probability of profit (70%+)
- ❌ Filtering by premium ($100+)
- ❌ Filtering by DTE (30-60 days)
- ❌ Bull/Bear Call spreads (only has put spreads)

**REUSE:** ✅ 80% done! Just enhance filters and add real API calls

---

### ✅ **4. Celery Background Tasks - FULLY CONFIGURED**

**Config Files:**
- ✅ `coda/celeryapp.py` - Celery app configuration
- ✅ `coda/coda_project/celery.py` - Alternative config
- ✅ `Procfile` - Heroku worker & beat processes already defined

**Existing Tasks:** `coda/ai_services/tasks.py`
- ✅ `@shared_task` decorator pattern
- ✅ `fetch_meetings_task` - Example async task (30s operation)
- ✅ `daily_meeting_sync_task` - Example scheduled task (1 AM daily)
- ✅ Email notifications on completion
- ✅ Error handling with retries

**Celery Beat Schedule:**
```python
app.conf.beat_schedule = {
    'daily-meeting-sync': {
        'task': 'ai_services.tasks.daily_meeting_sync_task',
        'schedule': crontab(hour=1, minute=0),  # 1 AM daily
    },
}
```

**REUSE:** ✅ Perfect pattern! Just create `fetch_positions_task` using same structure

---

### ✅ **5. API Authentication Pattern - ESTABLISHED**

**File:** `coda/ai_services/views.py` (lines 223-355)

**Pattern:**
1. ✅ Store API keys in settings: `settings.OPTIONPLAY_API_KEY`
2. ✅ OAuth flow: `get_authorization_url()` → `exchange_code_for_tokens()`
3. ✅ Token refresh: `refresh_access_token()`
4. ✅ Header pattern:
   ```python
   headers = {
       'Authorization': f'Bearer {access_token}',
       'Content-Type': 'application/json'
   }
   ```
5. ✅ Timeout handling: `timeout=10`
6. ✅ Error handling: `try/except` with fallback

**REUSE:** ✅ Same pattern for OptionPlay/Thinkorswim authentication

---

### ✅ **6. Admin Interface Patterns - ESTABLISHED**

**File:** `coda/investing/admin.py`

**Existing Admin Classes:**
- ✅ `ManagedTradingAccountAdmin` (lines 36-120)
- ✅ `OptionsPositionAdmin` (lines 122-200)
- ✅ `PositionBatchAdmin` (lines 521-578)

**Features:**
- ✅ `list_display` with custom methods
- ✅ `list_filter` for quick filtering
- ✅ `search_fields` for searching
- ✅ `readonly_fields` for calculated fields
- ✅ Custom actions (e.g., "Approve selected")

**REUSE:** ✅ Create `SuggestedPositionAdmin` following same pattern

---

## 📦 **DEPENDENCIES (What's Already Installed)**

### ✅ **HTTP/API Libraries:**
- ✅ `requests==2.31.0` - HTTP requests (sync)
- ✅ `httpx==0.26.0` - Modern HTTP client (async)
- ✅ `aiohttp==3.10.5` - Async HTTP

### ✅ **Task Queue:**
- ✅ `celery==5.5.1` - Background tasks
- ✅ `django-celery-beat==2.4.0` - Scheduled tasks
- ✅ `redis==4.3.1` - Task broker

### ✅ **Data Processing:**
- ✅ `python-dateutil==2.9.0` - Date parsing
- ✅ `pytz==2025.2` - Timezone support

### ❌ **NOT Installed (May Need):**
- ❌ `tda-api` - Official TD Ameritrade Python client
- ❌ `pandas` - Data analysis (commented out as "heavy")
- ❌ `numpy` - Numerical computing (commented out as "heavy")

**DECISION:** Use `requests` (already installed) for both APIs, avoid pandas/numpy for now

---

## 🔧 **WHAT WE NEED TO BUILD**

### 🆕 **1. SuggestedPosition Model** (NEW)

**Purpose:** Store auto-fetched positions pending staff review

**Location:** `coda/investing/models.py` (add after `PositionBatch`)

**Fields:**
- `source` - 'optionplay' or 'thinkorswim'
- `symbol`, `strategy`, `leg1_*`, `leg2_*` - Position details
- `expiration_date`, `premium_collected` - Financial details
- `probability_of_profit` - % chance of profit (70%+)
- `max_profit`, `max_loss`, `breakeven` - Risk metrics
- `dte` - Days to expiration (30-60)
- `review_status` - pending/approved/rejected/modified
- `reviewed_by`, `reviewed_at`, `staff_notes` - Review tracking
- `created_position` - Link to OptionsPosition if approved

**Why NOT just use OptionsPosition?**
- Separation of concerns: suggested vs. actual positions
- Staff can reject suggestions without affecting position history
- Allows bulk editing before batch creation

---

### 🆕 **2. Enhanced PositionFetcherService** (ENHANCE EXISTING)

**File:** `coda/investing/services/optionplay_integration_service.py` (RENAME & ENHANCE)

**Current Status:** 80% done (mock data only)

**Enhancements Needed:**
```python
class PositionFetcherService:
    """
    Unified service for fetching positions from multiple sources
    """
    
    def fetch_high_probability_positions(self, filters):
        """
        PRIMARY METHOD: Fetch from OptionPlay, fallback to Thinkorswim
        
        Args:
            filters = {
                'probability_min': 70,  # 70%+ chance of profit
                'premium_min': 100,  # $100+ premium
                'dte_min': 30,  # 30-60 days to expiration
                'dte_max': 60,
                'strategies': ['bull_put_spread', 'bear_call_spread', 'bull_call_spread', 'bear_put_spread'],
                'max_positions': 5
            }
        
        Returns:
            List of SuggestedPosition instances
        """
        try:
            # Try OptionPlay first
            positions = self._fetch_from_optionplay(filters)
            if len(positions) >= 5:
                return positions[:5]
        except Exception as e:
            logger.warning(f"OptionPlay fetch failed: {e}, trying Thinkorswim...")
        
        # Fallback to Thinkorswim
        try:
            positions = self._fetch_from_thinkorswim(filters)
            return positions[:5]
        except Exception as e:
            logger.error(f"Both APIs failed: {e}")
            return []
    
    def _fetch_from_optionplay(self, filters):
        """OptionPlay API integration (PRIMARY)"""
        # TODO: Implement real API call
        pass
    
    def _fetch_from_thinkorswim(self, filters):
        """TD Ameritrade API integration (FALLBACK)"""
        # TODO: Implement real API call
        pass
    
    def _apply_filters(self, positions, filters):
        """
        Filter positions by:
        - Probability of profit >= 70%
        - Premium >= $100
        - DTE between 30-60 days
        - Specific strategies only
        """
        filtered = []
        for pos in positions:
            if (
                pos['probability_of_profit'] >= filters['probability_min'] and
                pos['premium_collected'] >= filters['premium_min'] and
                filters['dte_min'] <= pos['dte'] <= filters['dte_max'] and
                pos['strategy'] in filters['strategies']
            ):
                filtered.append(pos)
        return filtered
```

---

### 🆕 **3. Staff Review Interface** (NEW)

**Views:** `coda/investing/views/managed_trading/position_suggestions.py` (NEW FILE)

**Methods:**
- `suggested_positions_list()` - View all pending suggestions
- `fetch_positions_now()` - Manual "Fetch Now" button
- `review_position()` - Edit/approve/reject individual position
- `create_batch_from_suggestions()` - Convert 5 approved suggestions → PositionBatch

**Template:** `coda/investing/templates/investing/staff/suggested_positions.html` (NEW)
- Table of suggested positions
- "Fetch Now" button
- Edit/Approve/Reject buttons per row
- "Create Batch from Selected" button

---

### 🆕 **4. Celery Scheduled Task** (NEW)

**File:** `coda/investing/tasks.py` (NEW)

```python
@shared_task
def daily_position_fetch_task():
    """
    Scheduled task: Fetch high-probability positions daily at 9 AM EST
    """
    fetcher = PositionFetcherService()
    filters = {
        'probability_min': 70,
        'premium_min': 100,
        'dte_min': 30,
        'dte_max': 60,
        'strategies': ['bull_put_spread', 'bear_call_spread', 'bull_call_spread', 'bear_put_spread'],
        'max_positions': 5
    }
    
    positions = fetcher.fetch_high_probability_positions(filters)
    
    # Save to SuggestedPosition model
    for pos_data in positions:
        SuggestedPosition.objects.create(**pos_data)
    
    # Notify staff
    send_mail(
        subject=f"Daily Position Fetch: {len(positions)} new suggestions",
        message=f"Review at: https://codatrainingapp.herokuapp.com/investing/managed/staff/suggestions/",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.STAFF_EMAIL],
    )
```

**Celery Beat Schedule:**
```python
app.conf.beat_schedule = {
    'daily-position-fetch': {
        'task': 'investing.tasks.daily_position_fetch_task',
        'schedule': crontab(hour=14, minute=0),  # 9 AM EST = 14:00 UTC
    },
}
```

---

## 🔑 **API CREDENTIALS NEEDED**

### **1. OptionPlay API**
**Add to settings:**
```python
# In heroku_settings.py or local_settings.py
OPTIONPLAY_API_KEY = os.environ.get('OPTIONPLAY_API_KEY', '')
OPTIONPLAY_API_URL = "https://api.optionplay.com/v1"
```

**Heroku Config:**
```bash
heroku config:set OPTIONPLAY_API_KEY="your_api_key_here" --app codatrainingapp
```

### **2. TD Ameritrade API (Fallback)**
**Add to settings:**
```python
TD_AMERITRADE_CLIENT_ID = os.environ.get('TD_AMERITRADE_CLIENT_ID', '')
TD_AMERITRADE_REDIRECT_URI = "https://codatrainingapp.herokuapp.com/investing/api/td-callback/"
TD_AMERITRADE_ACCESS_TOKEN = os.environ.get('TD_AMERITRADE_ACCESS_TOKEN', '')
```

**Heroku Config:**
```bash
heroku config:set TD_AMERITRADE_CLIENT_ID="your_client_id@AMER.OAUTHAP" --app codatrainingapp
heroku config:set TD_AMERITRADE_ACCESS_TOKEN="your_access_token" --app codatrainingapp
```

---

## 📊 **SYSTEM ARCHITECTURE**

### **Current Workflow (Manual):**
```
Staff Member
    ↓
Clicks "+ Add Position" button
    ↓
Fills out form manually (symbol, strikes, premium, etc.)
    ↓
Position created with status='pending'
    ↓
Staff creates PositionBatch
    ↓
Client approves/rejects batch
```

**Time:** ~5-10 minutes per position × 5 positions = **25-50 minutes**

---

### **NEW Workflow (Automated):**
```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: FETCH POSITIONS (Automated Daily at 9 AM EST)      │
├─────────────────────────────────────────────────────────────┤
│ Celery Beat triggers: daily_position_fetch_task()          │
│     ↓                                                        │
│ PositionFetcherService.fetch_high_probability_positions()  │
│     ↓                                                        │
│ Try OptionPlay API first:                                   │
│   - GET /v1/strategies?probability_min=70&premium_min=100   │
│   - Filter by DTE 30-60 days                                │
│   - Filter by strategies (bull/bear spreads)                │
│     ↓                                                        │
│ If OptionPlay fails → Fallback to Thinkorswim:             │
│   - GET /v1/marketdata/chains?symbol=SPY                   │
│   - Calculate probability for each spread                   │
│   - Filter by criteria                                       │
│     ↓                                                        │
│ Save top 5 positions to SuggestedPosition model             │
│ Status: review_status='pending'                             │
│     ↓                                                        │
│ Send email to staff: "5 new positions need review"          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ STEP 2: STAFF REVIEW & EDIT (Manual, but Fast)             │
├─────────────────────────────────────────────────────────────┤
│ Staff opens: /investing/managed/staff/suggestions/          │
│     ↓                                                        │
│ Sees table of 5 suggested positions:                        │
│   Symbol | Strategy | Probability | Premium | DTE | Actions │
│   AAPL   | Bull Put | 75%         | $120    | 45  | [Edit]  │
│   TSLA   | Bear Call| 72%         | $180    | 52  | [Edit]  │
│   ...                                                        │
│     ↓                                                        │
│ Staff can:                                                   │
│   ✏️ Edit strikes, contracts (opens edit modal)            │
│   ✅ Approve as-is (mark review_status='approved')          │
│   ❌ Reject (mark review_status='rejected')                 │
│     ↓                                                        │
│ Staff selects 5 approved positions                          │
│ Clicks "Create Batch from Selected"                         │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ STEP 3: BATCH CREATION (Automated)                         │
├─────────────────────────────────────────────────────────────┤
│ System converts SuggestedPosition → OptionsPosition         │
│     ↓                                                        │
│ Creates PositionBatch with 5 positions                      │
│ Status: 'pending' (waiting for client approval)             │
│ Approval deadline: Now + 24 hours                           │
│     ↓                                                        │
│ Sends email/notification to client                          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ STEP 4: CLIENT APPROVAL (Existing System)                  │
├─────────────────────────────────────────────────────────────┤
│ Client opens: /investing/managed/portal/approvals/batch/1/ │
│     ↓                                                        │
│ Reviews 5 positions                                          │
│ Approves entire batch with signature                        │
│     ↓                                                        │
│ Positions execute automatically                             │
└─────────────────────────────────────────────────────────────┘
```

**Time:** Fetch (automated) + Staff review (5 min) = **~5 minutes total**  
**Improvement:** 80-90% time reduction! 🎉

---

## 📁 **FILES TO CREATE/MODIFY**

### **CREATE (New Files):**

1. `coda/investing/tasks.py`
   - Celery tasks for position fetching
   - Daily scheduled fetch at 9 AM EST
   - Email notifications

2. `coda/investing/views/managed_trading/position_suggestions.py`
   - Staff review interface
   - Fetch now button
   - Edit/approve/reject actions

3. `coda/investing/templates/investing/staff/suggested_positions.html`
   - Table of fetched positions
   - Edit/approve UI
   - Batch creation button

4. `coda/investing/templates/investing/staff/position_suggestion_modal.html`
   - Modal for editing suggested positions
   - AJAX save

5. `coda/investing/management/commands/fetch_positions.py`
   - Manual command: `python manage.py fetch_positions`
   - For testing and manual triggers

### **MODIFY (Enhance Existing):**

1. `coda/investing/models.py`
   - Add `SuggestedPosition` model (after line 3177)

2. `coda/investing/services/optionplay_integration_service.py`
   - Rename to `position_fetcher_service.py`
   - Add real OptionPlay API calls
   - Add Thinkorswim fallback
   - Add filters (probability, premium, DTE)

3. `coda/investing/admin.py`
   - Register `SuggestedPositionAdmin`

4. `coda/investing/urls_managed_trading.py`
   - Add URLs for staff suggestion views

5. `coda/celeryapp.py`
   - Add daily position fetch to beat_schedule

6. `coda/investing/services/__init__.py`
   - Export `PositionFetcherService`

7. `coda/coda_project/coda_settings/base_settings.py`
   - Add `OPTIONPLAY_API_KEY`, `TD_AMERITRADE_*` settings

---

## 🎯 **IMPLEMENTATION STRATEGY**

### **Phase 1: Database & Models** (Day 1)
1. ✅ Create `SuggestedPosition` model
2. ✅ Create migration
3. ✅ Register in admin
4. ✅ Test CRUD operations

### **Phase 2: OptionPlay Integration** (Day 2)
1. ✅ Enhance `OptionPlayIntegrationService`
2. ✅ Add real API authentication
3. ✅ Implement filters (70%+ prob, $100+ premium, 30-60 DTE)
4. ✅ Add Bull/Bear Call/Put spreads
5. ✅ Test with mock data

### **Phase 3: Thinkorswim Fallback** (Day 3)
1. ✅ Add TD Ameritrade API integration
2. ✅ Implement OAuth flow
3. ✅ Parse options chains
4. ✅ Calculate probability metrics
5. ✅ Test fallback mechanism

### **Phase 4: Staff Review Interface** (Day 4)
1. ✅ Create views for suggestion list
2. ✅ Create edit/approve/reject views
3. ✅ Create templates
4. ✅ Add "Fetch Now" button
5. ✅ Test UI/UX

### **Phase 5: Batch Connection** (Day 5)
1. ✅ Convert SuggestedPosition → OptionsPosition
2. ✅ Create PositionBatch from approved suggestions
3. ✅ Test integration with existing batch approval
4. ✅ End-to-end workflow test

### **Phase 6: Automation** (Day 6)
1. ✅ Create Celery task for daily fetch
2. ✅ Add to Celery Beat schedule (9 AM EST)
3. ✅ Add email notifications
4. ✅ Test scheduled execution

### **Phase 7: Deployment** (Day 7)
1. ✅ Set API keys on Heroku
2. ✅ Deploy code
3. ✅ Run migrations
4. ✅ Start Celery worker & beat
5. ✅ UAT testing

---

## 🎓 **KEY INSIGHTS FROM CODEBASE**

### **1. Multi-Leg Position Structure (Already Perfect!)**
```python
# OptionsPosition.positions field is JSONB:
positions = [
    {
        'type': 'short_put',
        'strike': 240.00,
        'contracts': 1,
        'premium': 2.50,
        'delta': -0.30,
        'theta': 0.05
    },
    {
        'type': 'long_put',
        'strike': 230.00,
        'contracts': 1,
        'premium': 1.00,
        'delta': -0.15,
        'theta': 0.02
    }
]
```
**REUSE:** ✅ Same structure for SuggestedPosition!

### **2. Batch Approval Already Handles Pending Positions**
```python
# In BatchApprovalService.create_weekly_batch():
pending_positions = OptionsPosition.objects.filter(
    status='pending',
    batch__isnull=True,
    requires_client_approval=True
)
```
**INSIGHT:** Just create OptionsPosition with `status='pending'` and they automatically get batched!

### **3. Celery Pattern is Established**
```python
# Pattern from ai_services/tasks.py:
@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def fetch_meetings_task(self, start_date, end_date, user_id):
    try:
        # Do work
        result = some_long_running_task()
        
        # Email user when done
        send_mail(...)
        
        return result
    except Exception as exc:
        self.retry(exc=exc)
```
**REUSE:** ✅ Same pattern for `fetch_positions_task`!

---

## ⚠️ **POTENTIAL CHALLENGES**

### **1. API Rate Limits**
**OptionPlay:** Likely 100-1000 requests/hour  
**Thinkorswim:** 120 requests/minute

**Solution:**
- Cache fetched positions for 1 hour
- Batch API calls (fetch all symbols at once)
- Use fallback if rate limited

### **2. API Data Format Differences**
**OptionPlay:** Returns pre-calculated probability  
**Thinkorswim:** Need to calculate probability ourselves

**Solution:**
- Standardize data format in `_normalize_position_data()`
- Both APIs return same structure to SuggestedPosition

### **3. Celery on Heroku**
**Status:** Already configured in Procfile!
```
worker: cd coda && celery -A coda.celeryapp worker -l info --concurrency=2
beat: cd coda && celery -A coda.celeryapp beat -l info
```

**Needs:**
- Heroku Redis addon (already using `REDIS_URL`)
- Scale worker dyno: `heroku ps:scale worker=1 beat=1`

---

## ✅ **REQUIREMENTS UPDATE**

### **ALREADY IN requirements.txt:**
- ✅ `requests==2.31.0` - HTTP client
- ✅ `celery==5.5.1` - Task queue
- ✅ `redis==4.3.1` - Task broker
- ✅ `python-dateutil==2.9.0` - Date parsing

### **NO NEW PACKAGES NEEDED!**

---

## 🎯 **SUMMARY: What to Build**

| Component | Status | Effort | Priority |
|-----------|--------|--------|----------|
| `SuggestedPosition` model | 🆕 NEW | 2 hours | HIGH |
| `PositionFetcherService` (OptionPlay) | 🔄 80% done | 4 hours | HIGH |
| Thinkorswim fallback | 🆕 NEW | 6 hours | MEDIUM |
| Staff review interface | 🆕 NEW | 6 hours | HIGH |
| Batch creation from suggestions | 🆕 NEW | 2 hours | HIGH |
| Celery daily task | 🆕 NEW | 2 hours | MEDIUM |
| Management command | 🆕 NEW | 1 hour | LOW |

**Total Effort:** ~23 hours (~3 days)

---

## 🚀 **RECOMMENDED APPROACH**

### **MVP (Day 1-2): Manual Fetch + Staff Review**
1. Create `SuggestedPosition` model
2. Enhance `OptionPlayIntegrationService` with filters
3. Create staff review interface
4. Add "Fetch Now" button
5. Connect to batch system

**Result:** Staff can fetch positions on-demand and review before sending to clients

### **Full System (Day 3-4): Automation**
1. Add Thinkorswim fallback
2. Create Celery scheduled task
3. Set up daily 9 AM fetch
4. Add email notifications

**Result:** Fully automated position sourcing with staff oversight

---

## 💡 **NEXT STEP**

**Start with:** SuggestedPosition model creation

**Confirm these decisions:**
1. ✅ Use existing `OptionsPosition` structure for suggested positions? (Yes - proven design)
2. ✅ OptionPlay primary, Thinkorswim fallback? (Yes - as specified)
3. ✅ Filters: 70%+ prob, $100+ premium, 30-60 DTE? (Yes - as specified)
4. ✅ Strategies: Bull/Bear Put/Call spreads? (Yes - as specified)
5. ✅ Daily auto-fetch at 9 AM EST? (Yes - as specified)
6. ✅ Staff can edit everything? (Yes - as specified)

**Ready to proceed?** Let me know and I'll start building! 🚀

