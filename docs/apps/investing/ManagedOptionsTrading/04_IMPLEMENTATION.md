# CODA Trading Platform - Implementation Guide
**System:** Comprehensive Managed Options Trading + AI + Notifications  
**Last Updated:** November 8, 2025  
**Status:** ✅ **CORE COMPLETE** | 🚀 **PHASE 2 IN PROGRESS**

---

## 🎯 **CRITICAL: NO DUPLICATION STRATEGY**

**This document ensures:**
1. ✅ REUSE existing 33 models (don't create duplicates)
2. ✅ EXTEND existing 25 services (don't recreate)
3. ✅ ENHANCE existing 69 views (don't duplicate)
4. ✅ UPDATE existing templates (minimal new ones)
5. ✅ BUILD ON solid foundation (no rewrites)

---

## 📊 **COMPLETE CODE AUDIT (November 2025)**

### **✅ EXISTING MODELS - ALL IMPLEMENTED (33 Models)**

**DO NOT CREATE THESE - THEY EXIST!**

#### **Core Managed Trading Models** [IMPLEMENTED ✅]
| Model | Location | Fields | Status | Reuse Strategy |
|-------|----------|--------|--------|----------------|
| `ManagedTradingAccount` | models.py:1443 | 30+ fields, 5 fee tiers | ✅ Production | REUSE as-is |
| `OptionsPosition` | models.py:1738 | Greeks, P&L, status | ✅ Production | EXTEND for ML |
| `TradingRule` | models.py:1996 | Risk limits | ✅ Production | EXTEND for dynamic limits |
| `TradingActivity` | models.py:2056 | Audit trail | ✅ Production | REUSE as-is |
| `TradingSession` | models.py:2136 | Sessions | ✅ Production | REUSE as-is |
| `PositionBatch` | models.py:2729 | Batch approvals | ✅ Production | EXTEND for WhatsApp |
| `SuggestedPosition` | models.py:2962 | AI scores | ✅ UAT | EXTEND for ML predictions |
| `OptionsPositionHistory` | models.py:3500 | Historical data for ML | ✅ UAT | REUSE for training |
| `OptionPlayRawData` | models.py:3279 | CSV import | ✅ UAT | REUSE as-is |

#### **Investment & Risk Models** [IMPLEMENTED ✅]
| Model | Location | Purpose | Status |
|-------|----------|---------|--------|
| `Investor_Information` | models.py:41 | Investor management | ✅ Production |
| `Investment_rates` | models.py:296 | Investment tiers | ✅ Production |
| `InvestmentPerformance` | models.py:628 | Performance tracking | ✅ Production |
| `RiskAssessment` | models.py:880 | Risk scoring | ✅ Production |
| `RiskAlert` | models.py:974 | Alerts | ✅ Production |
| `ComplianceRecord` | models.py:1040 | Compliance | ✅ Production |
| `AuditTrail` | models.py:1121 | Audit history | ✅ Production |
| `InvestorRiskProfile` | models.py:2362 | Risk profiles | ✅ Production |

#### **Configuration & Application Models** [IMPLEMENTED ✅]
| Model | Location | Purpose | Status |
|-------|----------|---------|--------|
| `FeeTierConfiguration` | models.py:2233 | Fee config | ✅ Production |
| `ManagedTradingApplication` | models.py:2451 | Client applications | ✅ Production |
| `ManagedTradingContract` | models.py:2622 | Digital contracts | ✅ Production |
| `NotificationPreference` | models.py:1368 | Notification settings | ✅ Production |

#### **Analytics & Reporting Models** [IMPLEMENTED ✅]
| Model | Location | Purpose | Status |
|-------|----------|---------|--------|
| `InvestmentAnalytics` | models.py:1210 | Analytics | ✅ Production |
| `InvestmentReport` | models.py:702 | Reports | ✅ Production |
| `InvestmentMilestone` | models.py:752 | Milestones | ✅ Production |
| `MarketData` | models.py:1173 | Market data | ✅ Production |
| `InvestorCommunication` | models.py:1307 | Communications | ✅ Production |

#### **Legacy Models (Maintained)** [IMPLEMENTED ✅]
- `Ticker_Data`, `Daily_Trades`, `Returns_Balances`, `InvestmentsStrategy`, etc.

**Total: 33 Models - ALL EXIST - DON'T RECREATE! ✅**

---

### **✅ EXISTING SERVICES - ALL IMPLEMENTED (25 Services)**

**DO NOT RECREATE THESE - EXTEND THEM!**

#### **Core Trading Services** [IMPLEMENTED ✅]
| Service | File | Functions | Reuse Strategy |
|---------|------|-----------|----------------|
| `ManagedTradingService` | managed_trading_service.py | Account mgmt, positions, fees | EXTEND for broker API |
| `PositionScoringService` | position_scoring_service.py | 6-factor scoring | EXTEND with ML |
| `NotificationService` | notification_service.py | WhatsApp/Telegram | EXTEND for more channels |
| `RiskManagementService` | risk_management_service.py | Risk monitoring | EXTEND for dynamic limits |
| `PerformanceReportingService` | performance_reporting_service.py | Reports | EXTEND for analytics |

#### **AI & Automation Services** [IMPLEMENTED ✅]
| Service | File | Functions | Reuse Strategy |
|---------|------|-----------|----------------|
| `PositionFetcherService` | position_fetcher_service.py | Fetch positions | REUSE as-is |
| `PositionRankingService` | position_ranking_service.py | Ranking | EXTEND with ML |
| `AutoApprovalService` | auto_approval_service.py | Auto-approve | EXTEND criteria |
| `BatchApprovalService` | batch_approval_service.py | Batch management | REUSE as-is |
| `OptionPlayScraperService` | optionplay_scraper.py | Web scraping | REUSE as-is |

#### **Integration Services** [IMPLEMENTED ✅]
| Service | File | Functions | Reuse Strategy |
|---------|------|-----------|----------------|
| `OptionPlayIntegrationService` | optionplay_integration_service.py | API integration | REUSE as-is |
| `UnusualWhalesService` | unusual_whales_service.py | Whales data | REUSE as-is |
| `GoToMeetingService` | gotomeeting_service.py | Meeting integration | REUSE as-is |

#### **Analytics & Reporting Services** [IMPLEMENTED ✅]
| Service | File | Functions | Reuse Strategy |
|---------|------|-----------|----------------|
| `InvestmentAnalyticsService` | investment_analytics_service.py | Analytics | EXTEND for advanced charts |
| `InvestmentReportingService` | investment_reporting_service.py | Report generation | EXTEND for PDF/Excel |
| `TechnicalAnalysisService` | technical_analysis_service.py | Technical indicators | REUSE as-is |
| `OptionsMonitoringService` | options_monitoring_service.py | Monitoring | EXTEND with WebSocket |

#### **Utility Services** [IMPLEMENTED ✅]
| Service | File | Functions | Reuse Strategy |
|---------|------|-----------|----------------|
| `PositionHistoryCollector` | position_history_collector.py | Historical data | REUSE for ML training |
| `LeapsConverterService` | leaps_converter_service.py | LEAPS conversion | REUSE as-is |
| `SpreadBuilder` | spread_builder.py | Spread construction | REUSE as-is |
| `OptionPlayConverter` | optionplay_converter.py | Data conversion | REUSE as-is |
| `ApplicationApprovalService` | application_approval_service.py | Application workflow | REUSE as-is |
| `BaseService` | base_service.py | Base class | INHERIT from this |

**Total: 25 Services - ALL EXIST - EXTEND, DON'T DUPLICATE! ✅**

---

### **✅ EXISTING VIEWS - ALL IMPLEMENTED (69+ Views/Functions)**

**DO NOT RECREATE THESE - ENHANCE THEM!**

#### **Managed Trading Views** [IMPLEMENTED ✅]
| Module | File | Views | Reuse Strategy |
|--------|------|-------|----------------|
| Dashboard | dashboard.py | 1 view | ENHANCE with WebSocket |
| Accounts | accounts.py | 3 views | EXTEND for analytics |
| Positions | positions.py | 6 views | EXTEND with ML scores |
| Batches | batches.py | 6 views | REUSE as-is |
| AI Suggestions | position_suggestions.py | 8 views | ENHANCE display |
| CSV Upload | csv_upload.py | 15 views | WRAP in Celery |
| Monitoring | monitoring.py | 2 views | EXTEND with WebSocket |
| Onboarding | onboarding.py | 12 views | REUSE as-is |
| Sessions | sessions.py | 2 views | REUSE as-is |
| API Endpoints | api.py | 3 views | EXTEND for new features |
| Bulk Actions | api_bulk_actions.py | 1 view | REUSE as-is |
| Webhooks | webhooks.py | 3 views | EXTEND for Zapier |
| Multi-File Analyzer | multi_file_analyzer.py | 5 views | WRAP in Celery |
| Client Portal | client.py | 2 views | ENHANCE with real-time |

**Total: 69+ Views - ALL EXIST - ENHANCE, DON'T DUPLICATE! ✅**

---

## 🚀 **ENHANCEMENT IMPLEMENTATION STRATEGY**

### **CRITICAL PRINCIPLE: BUILD ON EXISTING, DON'T RECREATE**

Every enhancement follows this pattern:
1. ✅ **Audit** - What exists?
2. ✅ **Reuse** - Can we use as-is?
3. ✅ **Extend** - Add to existing code
4. ✅ **Minimal New** - Only create what's absolutely needed

---

### **Phase 1: Quick Wins** [PLANNED - 4 days]

#### **Enhancement 1.1: Dark Mode** (1 day)
**Status:** ✅ Implemented in code (Nov 7, 2025) — `investing/staff/suggested_positions.html`, `investing/css/dark-mode.css`

**Existing Code to Reuse:**
- ✅ All templates in `coda/investing/templates/`
- ✅ Base template structure
- ✅ CSS files in `coda/investing/static/`

**New Code Required:**
```
Files to CREATE:
- coda/investing/static/css/dark-mode.css (NEW - 200 lines)

Files to MODIFY:
- coda/investing/templates/investing/base_managed.html (ADD toggle button, theme script)
- NO backend changes needed
- NO models, views, or services
```

**Implementation:**
```css
/* coda/investing/static/css/dark-mode.css */
:root {
    --bg-color: #ffffff;
    --text-color: #333333;
    --card-bg: #f8f9fa;
}

[data-theme="dark"] {
    --bg-color: #1a1a1a;
    --text-color: #e0e0e0;
    --card-bg: #2d2d2d;
}

body {
    background-color: var(--bg-color);
    color: var(--text-color);
}
```

```javascript
// Add to base template
const toggleTheme = () => {
    const current = localStorage.getItem('theme') || 'light';
    const next = current === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
};
```

**Duplication Risk:** ✅ NONE (CSS only)

---

#### **Enhancement 1.2: Database Indexes** (1 day)
**Status:** ✅ Implemented (Nov 7, 2025) — migration `0016_add_phase1_indexes.py`

**Existing Code to Reuse:**
- ✅ All 33 models in `coda/investing/models.py`

**New Code Required:**
```
Files to MODIFY:
- coda/investing/models.py (ADD Meta.indexes to existing models)

Migration to CREATE:
- 0016_add_performance_indexes.py (NEW)
```

**Implementation:**
```python
# EXTEND existing OptionsPosition model (models.py:1738)
class OptionsPosition(TimeStampedModel):
    # ... existing 50+ fields ...
    
    class Meta:
        indexes = [
            models.Index(fields=['symbol', 'status']),  # For filtering
            models.Index(fields=['-ai_score']),  # For ranking
            models.Index(fields=['managed_account', 'opened_date']),  # For reports
            models.Index(fields=['expiration_date', 'status']),  # For monitoring
        ]

# EXTEND existing SuggestedPosition model (models.py:2962)
class SuggestedPosition(TimeStampedModel):
    # ... existing fields ...
    
    class Meta:
        indexes = [
            models.Index(fields=['-ai_score', 'rating']),  # For top positions
            models.Index(fields=['created_at', 'source']),  # For fetching
        ]
```

**Duplication Risk:** ✅ NONE (extending existing models)

---

#### **Enhancement 1.3: Portfolio Heat Map** (1 day)
**Status:** ✅ Implemented (Nov 7, 2025) — heatmap toggle + exposure summary integrated into `suggested_positions`

**Existing Code to Reuse:**
- ✅ `position_suggestions.py` query set for pending suggestions
- ✅ Staff suggestions template + Phase 10A Top 5 component

**New Code Required:**
```
Files to MODIFY:
- coda/investing/views/managed_trading/position_suggestions.py (heatmap aggregation + summary context)
- coda/investing/templates/investing/staff/suggested_positions.html (collapsible heatmap + UW detail drawer)
- coda/investing/templates/investing/staff/top_5_recommended_section.html (exposure snapshot banner)

Files to CREATE:
- NONE
```

**Implementation:**
```python
# position_suggestions.py (excerpt)
heatmap_symbols_qs = pending.values('symbol').annotate(
    total_capital=Sum('capital_required'),
    avg_ai_score=Avg('ai_score'),
    avg_probability=Avg('probability_of_profit'),
    position_count=Count('id'),
)

heatmap_symbols = [
    {
        'symbol': item['symbol'],
        'total_capital': float(item['total_capital'] or 0),
        'avg_ai_score': float(item['avg_ai_score'] or 0),
        'avg_probability': float(item['avg_probability'] or 0),
        'position_count': item['position_count'],
    }
    for item in heatmap_symbols_qs
]

heatmap_summary = {
    'total_capital': sum(item['total_capital'] for item in heatmap_symbols),
    'top_symbols': heatmap_symbols[:3],
    'top_strategies': heatmap_strategies[:2],
}
```

**Duplication Risk:** ✅ NONE (reuse existing data models + views)

---

#### **Enhancement 1.4: Zapier Webhooks** (1 day)
**Status:** ✅ Implemented (Nov 7, 2025) — reusing `webhooks.py` with bulk UW enrichment + Fetch button integration

**Existing Code to Reuse:**
- ✅ `webhooks.py` endpoints (WhatsApp)
- ✅ `PositionFetcherService` & `SuggestedPosition` model

**New Code Required:**
```
Files to MODIFY:
- coda/investing/services/unusual_whales_service.py (ADD bulk flow enrichment helper)
- coda/investing/views/managed_trading/position_suggestions.py (wire UW auto-check into fetch buttons)
- coda/investing/views/managed_trading/webhooks.py (refined payload + inbound token handling)
- coda/investing/templates/investing/staff/suggested_positions.html (Zapier + UW detail toggle)

Files to CREATE:
- NONE
```

**Implementation:**
```python
# unusual_whales_service.py (excerpt)
def apply_flow_to_suggestions(self, suggestions):
    symbols = list({s.symbol for s in suggestions if getattr(s, 'symbol', None)})
    flow_map = self.get_flow_summary_for_symbols(symbols, max_symbols=len(symbols))
    for suggestion in suggestions:
        flow_data = flow_map.get(suggestion.symbol)
        if not flow_data:
            continue
        ...  # adjust ai_score, rating, notes, api_response_data

# position_suggestions.fetch_positions_now
suggested = fetcher.fetch_high_probability_positions(filters)
if suggested and UnusualWhalesService().is_enabled():
    uw_summary = UnusualWhalesService().apply_flow_to_suggestions(suggested)
    messages.success(request, f"✅ Fetched {len(suggested)}..." +
                      f" • UW signals on {uw_summary['enriched']} symbol(s)")
```

**Duplication Risk:** ✅ NONE (extending existing services + views)

---

#### **Enhancement 1.5: Capital Allocation Engine & Scheduler** (2 days)
**Status:** 🚀 Planned — Phase 1 automation to guarantee $420/mo net income per $30K sleeve.

**Existing Code to Reuse:**
- ✅ `investing.tasks.daily_position_fetch_task`
- ✅ `PositionFetcherService`, `SuggestedPosition`, `NotificationService`

**New Code Required:**
```
Files to MODIFY:
- coda/investing/services/unusual_whales_service.py (reuse flow map for sizing)
- coda/investing/tasks.py (CALL new allocation service + staff notifications)

Files to CREATE:
- coda/investing/services/capital_allocation_service.py (NEW)
```

**Implementation Sketch:**
```python
# services/capital_allocation_service.py
class CapitalAllocationService(BaseInvestingService):
    TARGET_MONTHLY_INCOME = Decimal('420')
    TARGET_ACCOUNT_CAPITAL = Decimal('30000')
    MAX_POSITION_PCT = Decimal('0.10')

    def recommend_allocations(self, suggestions):
        """Return list of {suggestion, capital_required, expected_income}."""
        # Prioritise 🟢 timing, then 🟡
        scored = self._score_by_flow_and_ai(suggestions)
        return self._size_positions(scored)

# tasks.py
@shared_task
def managed_income_scheduler():
    suggestions = PositionFetcherService().fetch_high_probability_positions(filters)
    summary = CapitalAllocationService().recommend_allocations(suggestions)
    NotificationService().send_internal_allocation_digest(summary)
```

**Operational Notes:**
- Celery Beat entry `managed-income-scheduler` runs daily at 14:30 UTC (≈9:30 AM EST) via `coda/celeryapp.py`.
- Task short-circuits gracefully when no qualifying suggestions remain.

**Duplication Risk:** ✅ NONE (wrap existing fetch task, single allocation hub)

---

#### **Enhancement 1.6: UW Flow Caching & Reuse** (1 day)
**Status:** 🚀 Planned — shared cache prevents duplicate API calls across fetchers, Celery tasks, and ranking pipelines.

**Existing Code to Reuse:**
- ✅ `UnusualWhalesService`
- ✅ `django.core.cache`

**Implementation Sketch:**
```python
from django.core.cache import cache

class UnusualWhalesService:
    CACHE_TTL = 60 * 10  # 10 minutes

    def get_flow_summary_for_symbols(self, symbols, max_symbols=20):
        cache_key = f"uw-flow:{','.join(sorted(symbols))}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        results = self._fetch_flow(symbols, max_symbols)
        cache.set(cache_key, results, self.CACHE_TTL)
        return results
```

**Duplication Risk:** ✅ NONE (central cache used by fetch endpoints + Celery)

---

#### **Enhancement 2.1: Managed Income Dashboard (Client Read-Only)** (2 days)
**Status:** 🚀 Planned — expose performance outcomes while keeping CODA as executor.

**Existing Code to Reuse:**
- ✅ `investing/views/managed_trading/client_dashboard.py`
- ✅ `templates/investing/client/dashboard.html`
- ✅ `SuggestedPosition.api_response_data['unusual_whales']`

**Work Plan:**
- Add serializer helpers that transform UW metadata into client-safe sentiment badges (no trade directions).
- Extend dashboard context with `income_goal_progress`, `uw_alignment_summary`, `strategy_mix`.
- Render new dashboard cards + sparkline using existing `stats_card` partial to avoid duplication.
- Hook “Preview Trade” button to staff-only modal that reuses `pending_positions` partial and shows leg breakdown.

**Duplication Risk:** ✅ LOW (reuse shared partials + service layer for aggregation)

---

#### **Enhancement 2.2: Scenario Reports & Capital Upsell** (1.5 days)
**Status:** 🚀 Planned — automated WhatsApp + email digests to encourage higher funding.

**Existing Code to Reuse:**
- ✅ `NotificationService` (WhatsApp/Email drivers)
- ✅ `InvestmentReport` generation utilities
- ✅ `ManagedTradingAccount` fee configuration

**Work Plan:**
- Add `ScenarioProjectionService` that projects income at +$10K/+ $25K using CapitalAllocationService heuristics.
- Build templated message generator (Jinja/format strings) stored in `templates/notifications/managed_income/`.
- Expose staff UI toggle (`Send Scenario Digest`) on dashboard -> triggers Celery task to send via WhatsApp + email.
- Log outreach events in `CommunicationLog` model extension (audit + compliance).

**Duplication Risk:** ✅ NONE (extends existing notification pipelines)

---

#### **Enhancement 3.1: Premium Alert Tier Toggle** (1 day)
**Status:** 🚀 Planned — allow opt-in instructions while defaulting to managed summaries.

**Existing Code to Reuse:**
- ✅ `ManagedTradingAccount` settings fields
- ✅ `NotificationPreference` model
- ✅ `NotificationService`

**Work Plan:**
- Add boolean `allow_direct_instructions` to account settings with audit timestamp.
- Gate existing trade alert templates behind new permission check.
- Update staff workflows to require explicit confirmation before sending actionable entries/exits.
- Record each premium alert with metadata (position id, UW score, allocation size).

**Duplication Risk:** ✅ NONE (small extension of current preference logic)

**Phase 1 Summary:**
- Investment: 4 days
- New files: 1 CSS file, 1 migration
- Modified files: 4 existing files
- New models: 0
- New views: 0
- New services: 0
- Duplication risk: ✅ NONE

---

### **Phase 2: Performance** [IN PROGRESS - 9 days]

#### **Enhancement 2.0: Managed Risk Guardrails UI** (2 days) — ✅ **Completed Nov 8, 2025**

**Objective:** Surface account-specific risk limits to staff reviewers and allow superusers to adjust guardrails without leaving the suggestions dashboard.

**Existing Code Reused:**
- ✅ `ManagedTradingAccount`, `TradingRule`, `TradingActivity` (risk metadata + audit trail)
- ✅ `ManagedTradingService` (batch creation workflow)
- ✅ Staff suggestions template + preview payload helper
- ✅ `NotificationService` (existing digest sender)

**Implementation Details (Delivered):**
- Added risk summary + violation banners inside `Create Batch` modal (`investing/staff/suggested_positions.html`).
- Loaded account risk limits in `suggested_positions_list` view and exposed new `update_account_position_limit` view.
- Added superuser-only adjust-limit modal with audit logging via `TradingActivity`.
- Hardened digest recipient filtering (`NotificationService._get_staff_emails`) so only superusers and members of `MANAGED_INCOME_DIGEST_GROUP` receive allocation previews.
- Created placeholder `static/investing/css/dark-mode.css` inside app namespace to align WhiteNoise paths (prevents 404 triggered by modal theme toggle).
- Tests: `tests/apps/investing/01_unit/test_notification_service.py` (recipient filtering) and integration scaffolding (`tests/apps/investing/02_integration/test_account_limit_controls.py`, currently skipped until legacy migrations exist).

**Duplication Risk:** ✅ NONE (extends existing view/service; no new models).

---

#### **Enhancement 2.1: Redis Caching** (3 days)

**Existing Code to Reuse:**
- ✅ All 25 services
- ✅ All views

**New Code Required:**
```
Files to CREATE:
- coda/investing/services/caching_service.py (NEW - 300 lines)

Files to MODIFY:
- coda/investing/services/position_scoring_service.py (ADD caching)
- coda/investing/views/managed_trading/dashboard.py (USE cache)
- requirements.txt (ADD redis==5.0.1, django-redis==5.4.0)
```

**Implementation:**
```python
# CREATE new caching service
# coda/investing/services/caching_service.py (NEW)
from django.core.cache import cache
import json

class PositionCacheService:
    """Redis caching for position data"""
    
    def get_scored_positions(self, account_id):
        cache_key = f"positions:scored:{account_id}"
        cached = cache.get(cache_key)
        
        if cached:
            return json.loads(cached)
        
        # Call existing scoring service
        from .position_scoring_service import PositionScoringService
        scorer = PositionScoringService()
        positions = scorer.score_batch(account_id)
        
        # Cache for 1 hour
        cache.set(cache_key, json.dumps(positions), 3600)
        return positions
    
    def invalidate_position_cache(self, account_id):
        cache.delete(f"positions:scored:{account_id}")

# EXTEND existing position_scoring_service.py
class PositionScoringService:
    def score_position(self, position_data):
        # Check cache first
        cache_service = PositionCacheService()
        cached = cache_service.get_cached_score(position_data['id'])
        if cached:
            return cached
        
        # ... existing scoring logic ...
        score = self._calculate_score(position_data)
        
        # Cache result
        cache_service.cache_score(position_data['id'], score)
        return score
```

**Duplication Risk:** ✅ NONE (wrapping existing services)

---

#### **Enhancement 2.2: Celery Background Tasks** (4 days)

**Existing Code to Reuse:**
- ✅ All services (especially scoring, reporting, CSV processing)
- ✅ All views

**New Code Required:**
```
Files to CREATE:
- coda/investing/tasks.py (NEW - 500 lines)
- coda/celery.py (NEW - 50 lines)

Files to MODIFY:
- coda/investing/views/managed_trading/csv_upload.py (WRAP in tasks)
- coda/investing/views/managed_trading/dashboard.py (ASYNC report generation)
- requirements.txt (ADD celery==5.3.4, redis==5.0.1)
```

**Implementation:**
```python
# CREATE new tasks.py
# coda/investing/tasks.py (NEW)
from celery import shared_task

@shared_task
def score_positions_async(position_ids):
    """Score positions in background - REUSES existing service"""
    from .services.position_scoring_service import PositionScoringService
    scorer = PositionScoringService()
    
    for pid in position_ids:
        position = SuggestedPosition.objects.get(id=pid)
        score = scorer.score_position(position)  # REUSE existing
        position.ai_score = score
        position.save()

@shared_task
def generate_report_async(account_id):
    """Generate report in background - REUSES existing service"""
    from .services.performance_reporting_service import PerformanceReportingService
    service = PerformanceReportingService()
    report = service.generate_monthly_report(account_id)  # REUSE existing
    service.email_report(report)

# MODIFY existing csv_upload.py view
def upload_optionplay_csv(request):
    # ... existing validation ...
    
    # BEFORE: Synchronous (blocks for 10 seconds)
    # process_csv(file)
    
    # AFTER: Asynchronous (instant response)
    from .tasks import process_csv_async
    task = process_csv_async.delay(file.id)
    
    return JsonResponse({
        'status': 'processing',
        'task_id': task.id
    })
```

**Duplication Risk:** ✅ NONE (wrapping existing logic)

---

#### **Enhancement 2.3: Query Optimization** (2 days)

**Existing Code to Reuse:**
- ✅ All views
- ✅ All models

**New Code Required:**
```
Files to MODIFY:
- coda/investing/views/managed_trading/dashboard.py
- coda/investing/views/managed_trading/positions.py
- coda/investing/views/managed_trading/batches.py
- (10-15 views total)

Files to CREATE:
- NONE
```

**Implementation:**
```python
# BEFORE (N+1 query problem)
def managed_trading_dashboard(request):
    positions = OptionsPosition.objects.filter(status='open')
    for pos in positions:
        print(pos.managed_account.client_name)  # 100 queries!

# AFTER (Optimized - 1 query)
def managed_trading_dashboard(request):
    positions = OptionsPosition.objects.filter(
        status='open'
    ).select_related(  # JOIN managed_account
        'managed_account',
        'batch'
    ).prefetch_related(  # Prefetch related data
        'managed_account__user'
    )
    # Now only 1-2 queries total!
```

**Duplication Risk:** ✅ NONE (optimizing existing queries)

**Phase 2 Summary:**
- ✅ Delivered: Risk guardrail UI + superuser adjustments + digest recipient hardening (Nov 8, 2025)
- Investment: 9 days (2 used, 7 planned for caching/Celery/query optimization)
- New files to date: 3 (app-level dark mode CSS, notification unit tests, integration scaffolding)
- Upcoming new files: caching_service.py, tasks.py, celery.py
- Modified files (to date): `base_settings.py`, `notification_service.py`, `position_suggestions.py`, `staff/suggested_positions.html`, `urls_managed_trading.py`
- New models: 0
- New views: 0
- Duplication risk: ✅ NONE

---

### **Phase 3: Advanced Features** [PLANNED - 20 days]

#### **Enhancement 3.0: Managed Outcomes Dashboard (Client-Facing)** (5 days)

**Goal:** Deliver a read-only dashboard that keeps managed clients informed (income progress, UW timing history, scenario planning) without exposing execution instructions.

**Key Widgets**
- **Income Coverage Gauge:** Visual against $420/month target, with MTD/YTD payout history pulled from `PositionBatch` + `OptionsPosition` P&L.
- **UW Timing History:** Lightweight timeline table (symbol, flow score, sentiment, entry window) sourced from existing `api_response_data['unusual_whales']` payloads.
- **Scenario Explorer:** Allow clients to adjust sleeve size sliders (e.g., +$5K, +$10K) and show projected income using `CapitalAllocationService` rates.

**Reuse Strategy**
- ✅ Reuse `ManagedTradingAccount` metrics, `CapitalAllocationService`, and `TradingActivity` for historical events.
- ✅ Extend existing client portal view (`investing/views/managed_trading/client.py`) and template with new context blocks.
- ✅ Introduce helper in `investing/utils.py` to aggregate income statistics (avoids duplicating reporting logic).
- 🔁 Optional: expose JSON endpoint for scenario explorer so the dashboard can poll without regeneration.

**Work Plan**
1. **Service helper:** `ManagedTradingService.get_income_summary(account)` returning coverage %, expected monthly income, realized payouts.
2. **Client view update:** Add `income_summary`, `uw_history` (limited to last 10 positions), and `scenario_defaults`.
3. **Template:** Build responsive cards (income gauge, UW timeline, scenario slider). Ensure “managed role” copy explains CODA executes trades.
4. **Security:** Retain `login_required` + account ownership checks; no action buttons rendered.

**Duplication Risk:** ✅ NONE (extends existing client portal stack).

#### **Enhancement 3.1: WebSocket Real-Time Dashboard** (5 days)

**Existing Code to Reuse:**
- ✅ Dashboard view and template
- ✅ All models

**New Code Required:**
```
Files to CREATE:
- coda/investing/consumers.py (NEW - 200 lines)
- coda/investing/routing.py (NEW - 30 lines)

Files to MODIFY:
- coda/investing/templates/investing/managed/dashboard.html (ADD WebSocket JS)
- coda/asgi.py (ADD channels routing)
- requirements.txt (ADD channels==4.0.0, daphne==4.0.0)

NO new models, NO new views
```

**Implementation:**
```python
# CREATE new consumers.py
# coda/investing/consumers.py (NEW)
from channels.generic.websocket import AsyncWebsocketConsumer
import json

class DashboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.account_id = self.scope['url_route']['kwargs']['account_id']
        await self.channel_layer.group_add(
            f"dashboard_{self.account_id}",
            self.channel_name
        )
        await self.accept()
    
    async def position_update(self, event):
        # Send to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'position_update',
            'position': event['position']
        }))

# MODIFY existing dashboard template
# Add WebSocket connection
const ws = new WebSocket(`ws://${window.location.host}/ws/dashboard/${accountId}/`);
ws.onmessage = function(e) {
    const data = JSON.parse(e.data);
    if (data.type === 'position_update') {
        updatePositionCard(data.position);  // Update UI live
    }
};
```

**Duplication Risk:** ✅ NONE (adding real-time layer on top)

---

#### **Enhancement 3.2: Machine Learning Predictions** (7 days)

**Existing Code to Reuse:**
- ✅ `PositionScoringService` (existing)
- ✅ `OptionsPositionHistory` model (existing)
- ✅ `SuggestedPosition` model (existing)

**New Code Required:**
```
Files to CREATE:
- coda/investing/services/ml_prediction_service.py (NEW - 400 lines)

Files to MODIFY:
- coda/investing/models.py (ADD 1 field to SuggestedPosition: ml_win_probability)
- coda/investing/services/position_scoring_service.py (USE ML predictions)
- coda/investing/views/managed_trading/position_suggestions.py (DISPLAY ML score)
- requirements.txt (ADD xgboost==2.0.1, scikit-learn==1.3.2, pandas==2.1.3)

Migration to CREATE:
- 0017_add_ml_prediction_field.py
```

**Implementation:**
```python
# CREATE new ML service
# coda/investing/services/ml_prediction_service.py (NEW)
import xgboost as xgb
import pandas as pd
from .position_history_collector import PositionHistoryCollector  # REUSE existing

class MLPositionPredictor:
    """ML prediction using existing historical data"""
    
    def train_model(self):
        # REUSE existing OptionsPositionHistory model
        history = OptionsPositionHistory.objects.filter(
            status='closed'
        ).values('delta', 'theta', 'iv_rank', 'dte', 'won')
        
        df = pd.DataFrame(history)
        X = df.drop('won', axis=1)
        y = df['won']
        
        model = xgb.XGBClassifier(n_estimators=100)
        model.fit(X, y)
        return model
    
    def predict_win_probability(self, position_data):
        model = self.load_model()
        prob = model.predict_proba([position_data])[0][1]
        return prob * 100  # Return as percentage

# EXTEND existing position_scoring_service.py
class PositionScoringService:
    def score_position(self, position_data):
        # Existing rule-based score
        rule_score = self._calculate_rule_based_score(position_data)
        
        # ADD ML prediction
        ml_service = MLPositionPredictor()
        ml_probability = ml_service.predict_win_probability(position_data)
        
        # Combine: 70% rules, 30% ML
        final_score = (rule_score * 0.7) + (ml_probability * 0.3)
        return final_score

# ADD 1 field to existing model
class SuggestedPosition(TimeStampedModel):
    # ... existing 20+ fields ...
    ml_win_probability = models.DecimalField(  # NEW field
        max_digits=5, decimal_places=2,
        null=True, blank=True,
        help_text="ML-predicted win probability (0-100)"
    )
```

**Duplication Risk:** ✅ NONE (extending existing scoring)

---

#### **Enhancement 3.3: Interactive Position Builder** (4 days)

**Existing Code to Reuse:**
- ✅ Position creation form (existing)
- ✅ Position creation view (existing)

**New Code Required:**
```
Files to MODIFY:
- coda/investing/templates/investing/managed/position_create.html (ADD interactive UI)
- coda/investing/static/js/position-builder.js (NEW - 300 lines)

NO backend changes needed
```

**Duplication Risk:** ✅ NONE (enhancing existing form)

---

#### **Enhancement 3.4: Advanced Analytics Dashboard** (4 days)

**Existing Code to Reuse:**
- ✅ `InvestmentAnalyticsService` (existing)
- ✅ Dashboard view (existing)

**New Code Required:**
```
Files to CREATE:
- coda/investing/views/managed_trading/analytics.py (NEW - 200 lines)
- coda/investing/templates/investing/managed/analytics.html (NEW)

Files to MODIFY:
- coda/investing/services/investment_analytics_service.py (EXTEND with chart data)
- requirements.txt (ADD plotly==5.17.0)
```

**Implementation:**
```python
# CREATE new analytics view (REUSES existing service)
def advanced_analytics(request, account_id):
    # REUSE existing analytics service
    from ..services.investment_analytics_service import InvestmentAnalyticsService
    service = InvestmentAnalyticsService()
    
    # Get data from existing service
    analytics = service.get_account_analytics(account_id)
    
    # Format for charts
    chart_data = {
        'win_rate_by_strategy': analytics['strategy_performance'],
        'pnl_trend': analytics['monthly_pnl'],
        'greeks_heatmap': analytics['greeks_exposure'],
    }
    
    return render(request, 'investing/managed/analytics.html', {
        'charts': chart_data
    })
```

**Duplication Risk:** ✅ NONE (new view, reuses existing service)

**Phase 3 Summary:**
- Investment: 20 days
- New files: 6 (consumers.py, routing.py, ml_prediction_service.py, analytics.py, 2 templates)
- Modified files: 10 existing files
- New models: 0 (only 1 field added)
- New views: 1 (analytics)
- Duplication risk: ✅ NONE

---

### **Phase 4: Integration** [PLANNED - 18 days]

#### **Enhancement 4.1: Broker API Integration** (10 days)

**Existing Code to Reuse:**
- ✅ `OptionsPosition` model (existing)
- ✅ `ManagedTradingAccount` model (existing)
- ✅ Position management views (existing)

**New Code Required:**
```
Files to CREATE:
- coda/investing/services/broker_api_service.py (NEW - 600 lines)
- coda/investing/models.py (ADD 1 new model: BrokerConnection)

Files to MODIFY:
- coda/investing/views/managed_trading/positions.py (ADD auto-sync)
- coda/investing/admin.py (ADD BrokerConnection admin)

Migration to CREATE:
- 0018_add_broker_connection.py
```

**Implementation:**
```python
# ADD 1 new model for broker credentials
class BrokerConnection(TimeStampedModel):
    managed_account = models.OneToOneField(ManagedTradingAccount, on_delete=models.CASCADE)
    broker = models.CharField(max_length=20, choices=[
        ('td', 'TD Ameritrade'),
        ('ibkr', 'Interactive Brokers'),
        ('tasty', 'Tastytrade'),
        ('schwab', 'Schwab'),
    ])
    api_key = models.CharField(max_length=255, encrypted=True)
    api_secret = models.CharField(max_length=255, encrypted=True)
    last_sync = models.DateTimeField(null=True)

# CREATE new broker service (wraps existing position logic)
class BrokerAPIService:
    def sync_positions(self, account):
        # Fetch from broker API
        positions = self._fetch_from_broker(account.broker_connection)
        
        # REUSE existing OptionsPosition model
        for pos_data in positions:
            OptionsPosition.objects.update_or_create(
                managed_account=account,
                symbol=pos_data['symbol'],
                defaults={
                    'premium_collected': pos_data['premium'],
                    'opened_date': pos_data['opened_date'],
                    # ... etc
                }
            )
```

**Duplication Risk:** ✅ NONE (1 new model, extends existing)

---

#### **Enhancement 4.2: TradingView Integration** (2 days)

**Existing Code to Reuse:**
- ✅ Dashboard template
- ✅ Position detail template

**New Code Required:**
```
Files to MODIFY:
- coda/investing/templates/investing/managed/position_detail.html (EMBED TradingView)

NO backend changes needed
```

**Implementation:**
```html
<!-- EXTEND existing position_detail.html -->
<div id="tradingview-chart"></div>
<script src="https://s3.tradingview.com/tv.js"></script>
<script>
new TradingView.widget({
    "symbol": "{{ position.symbol }}",
    "interval": "D",
    "container_id": "tradingview-chart",
});
</script>
```

**Duplication Risk:** ✅ NONE (embedding external widget)

---

#### **Enhancement 4.3: Predictive Analytics** (6 days)

**Existing Code to Reuse:**
- ✅ `OptionsPositionHistory` (existing)
- ✅ `InvestmentAnalyticsService` (existing)

**New Code Required:**
```
Files to CREATE:
- coda/investing/services/predictive_analytics_service.py (NEW - 400 lines)

Files to MODIFY:
- coda/investing/views/managed_trading/analytics.py (ADD forecasts)
- requirements.txt (ADD prophet==1.1.5)
```

**Implementation:**
```python
# CREATE new predictive service (REUSES existing data)
from prophet import Prophet

class PredictiveAnalyticsService:
    def forecast_account_balance(self, account):
        # REUSE existing OptionsPositionHistory
        history = OptionsPositionHistory.objects.filter(
            managed_account=account
        ).values('closed_date', 'profit_loss')
        
        df = pd.DataFrame(history)
        df.columns = ['ds', 'y']  # Prophet format
        
        model = Prophet()
        model.fit(df)
        
        future = model.make_future_dataframe(periods=90)
        forecast = model.predict(future)
        return forecast
```

**Duplication Risk:** ✅ NONE (new service, reuses existing data)

**Phase 4 Summary:**
- Investment: 18 days
- New files: 3 (broker_api_service.py, predictive_analytics_service.py, 1 migration)
- Modified files: 5 existing files
- New models: 1 (BrokerConnection)
- New views: 0
- Duplication risk: ✅ NONE

---

## 📊 **COMPLETE ENHANCEMENT SUMMARY**

| Phase | Days | New Files | Modified Files | New Models | New Views | New Services | Duplication Risk |
|-------|------|-----------|----------------|------------|-----------|--------------|------------------|
| **Phase 1** | 4 | 2 | 4 | 0 | 0 | 0 | ✅ NONE |
| **Phase 2** | 9 | 3 | 20 | 0 | 0 | 1 | ✅ NONE |
| **Phase 3** | 20 | 6 | 10 | 0 | 1 | 2 | ✅ NONE |
| **Phase 4** | 18 | 3 | 5 | 1 | 0 | 2 | ✅ NONE |
| **TOTAL** | **51** | **14** | **39** | **1** | **1** | **5** | **✅ NONE** |

**Existing Code Reused:**
- ✅ 33 models (32 reused as-is, 1 new)
- ✅ 25 services (20 reused, 5 new)
- ✅ 69 views (68 reused, 1 new)
- ✅ 50+ templates (all reused, enhanced)

**Code Reuse Ratio: 95%+ ✅**

---

## ✅ **IMPLEMENTATION CHECKLIST**

Before implementing ANY enhancement:

- [ ] ✅ Read this section for that enhancement
- [ ] ✅ Confirm "Existing Code to Reuse" still exists
- [ ] ✅ Check "Duplication Risk" = NONE
- [ ] ✅ Follow "Implementation" code exactly
- [ ] ✅ Only create "New Code Required" files
- [ ] ✅ Test that existing functionality still works
- [ ] ✅ Update this document with actual implementation

---

**Document Status:** ✅ **CRITICAL SECTIONS COMPLETE**  
**Next:** Complete 02_REQUIREMENTS.md and README.md  
**Then:** Return to update 03, 05, 06, 07 per CURSOR_AI_GUIDE

---

## 🚀 Quick Start: Manual Implementation (Week 1)

### **You Can Start Managing the Client TODAY!**

Since 80% of the infrastructure exists, you can begin managing the client's $30,000 account immediately using existing models while building the full system.

#### **Step 1: Create Client Record (5 minutes)**

```python
# In Django shell or admin
from accounts.models import CustomerUser
from investing.models import Investor_Information

# Create or get client user
client = CustomerUser.objects.get(username='client_options_30k')

# Create investment record to track the $30K account
managed_investment = Investor_Information.objects.create(
    investor=client,
    amount_invested=Decimal('30000.00'),
    investment_type='options',
    investment_purpose='Managed Options Trading Account',
    expected_return_rate=Decimal('20.00'),  # Target 20% annual
    risk_tolerance='moderate',
    kyc_status='verified',
    status='active',
    model_type='Options',
    duration=12,  # 12 months initial
    notes='MANAGED ACCOUNT - Options Trading Strategy Mix'
)

print(f"✅ Created managed account tracking: {managed_investment.id}")
```

#### **Step 2: Execute First Position (15 minutes)**

```python
from investing.models import Portfolio

# Example: Cash-secured put on AAPL
position = Portfolio.objects.create(
    user=request.user,  # CODA trader, not client
    symbol='AAPL',
    strategy='short_put',
    short_strike=Decimal('170.00'),  # Strike price
    long_strike=Decimal('0.00'),  # N/A for short put
    amount=Decimal('300.00'),  # Premium collected
    number_of_contract=1,
    expiry='2025-11-22',  # 30 days out
    short_leg_delta=Decimal('0.30'),  # 30 delta
    short_leg_theta=Decimal('0.15'),  # Positive theta
    comment=f'Client: {client.username} | Capital: $17,000 | Max Loss: $16,700',
    is_active=True,
    is_featured=True
)

print(f"✅ Position created: AAPL $170 Put @ $3.00 premium")
```

#### **Step 3: Track in Spreadsheet (Parallel)**

Create Google Sheet with columns:
```
Date | Account | Symbol | Strategy | Strike | Contracts | Premium | Capital | Max Loss | Status | P&L | Notes
```

This allows you to:
- Track all positions across clients
- Calculate total P&L
- Monitor risk exposure
- Generate client reports

**You can now trade the client's account using existing infrastructure!**

---

## 🏗️ Full System Implementation

### **Phase 1: Database Models** (Week 1-2)

#### **File: `coda/investing/models/managed_trading.py`**

```python
"""
Managed Trading Models
New models for professional options account management
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import date
from main.models import TimeStampedModel

User = get_user_model()


class ManagedTradingAccount(TimeStampedModel):
    """Full model code from 03_ARCHITECTURE.md"""
    # ... (copy complete model from architecture doc)
    pass


class OptionsPosition(TimeStampedModel):
    """Full model code from 03_ARCHITECTURE.md"""
    # ... (copy complete model from architecture doc)
    pass


class TradingRule(TimeStampedModel):
    """Full model code from 03_ARCHITECTURE.md"""
    # ... (copy complete model from architecture doc)
    pass


class TradingActivity(TimeStampedModel):
    """Full model code from 03_ARCHITECTURE.md"""
    # ... (copy complete model from architecture doc)
    pass
```

#### **Update: `coda/investing/models/__init__.py`**

```python
# Add new imports
from .managed_trading import (
    ManagedTradingAccount,
    OptionsPosition,
    TradingRule,
    TradingActivity
)

__all__ = [
    # ... existing models
    'ManagedTradingAccount',
    'OptionsPosition',
    'TradingRule',
    'TradingActivity',
]
```

#### **Create Migration:**

```bash
cd coda
python manage.py makemigrations investing
python manage.py migrate
```

---

### **Phase 2: Services** (Week 2-3)

#### **File: `coda/investing/services/managed_trading_service.py`**

```python
"""
Managed Trading Service
Core business logic for managing client options accounts
"""

import logging
from decimal import Decimal
from datetime import date, timedelta
from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Dict, List, Tuple, Optional

from ..models import (
    ManagedTradingAccount,
    OptionsPosition,
    TradingRule,
    TradingActivity
)
from .base_service import BaseInvestingService

logger = logging.getLogger(__name__)


class ManagedTradingService(BaseInvestingService):
    """
    Service for managed options trading operations
    """
    
    def create_managed_account(
        self, 
        client_user, 
        account_data: Dict
    ) -> ManagedTradingAccount:
        """
        Create new managed trading account
        
        Args:
            client_user: User instance (client)
            account_data: Dict with account parameters
        
        Returns:
            ManagedTradingAccount instance
        """
        try:
            with transaction.atomic():
                # Generate account number
                account_number = self._generate_account_number()
                
                # Create account
                account = ManagedTradingAccount.objects.create(
                    client=client_user,
                    account_name=account_data.get('account_name'),
                    account_number=account_number,
                    initial_capital=Decimal(str(account_data['initial_capital'])),
                    current_balance=Decimal(str(account_data['initial_capital'])),
                    cash_available=Decimal(str(account_data['initial_capital'])),
                    cash_reserved=Decimal('0.00'),
                    high_water_mark=Decimal(str(account_data['initial_capital'])),
                    account_manager=account_data.get('account_manager'),
                    management_fee_percentage=account_data.get('management_fee', Decimal('1.50')),
                    performance_fee_percentage=account_data.get('performance_fee', Decimal('20.00')),
                    status='active',
                    activation_date=date.today()
                )
                
                # Create default trading rules
                self._create_default_trading_rules(account)
                
                # Log activity
                TradingActivity.objects.create(
                    managed_account=account,
                    activity_type='account_created',
                    description=f'Managed account created with ${account.initial_capital}',
                    performed_by=account_data.get('account_manager'),
                    data_snapshot={'initial_capital': str(account.initial_capital)}
                )
                
                logger.info(f"Created managed account {account.account_number} for {client_user.username}")
                
                return account
                
        except Exception as e:
            logger.error(f"Error creating managed account: {e}")
            raise ValidationError(f"Failed to create account: {str(e)}")
    
    def _generate_account_number(self) -> str:
        """Generate unique account number"""
        import random
        prefix = 'CODA-OPT'
        
        # Get count of existing accounts
        count = ManagedTradingAccount.objects.count() + 1
        
        # Format: CODA-OPT-001, CODA-OPT-002, etc.
        account_number = f"{prefix}-{count:03d}"
        
        # Ensure uniqueness
        while ManagedTradingAccount.objects.filter(account_number=account_number).exists():
            count += 1
            account_number = f"{prefix}-{count:03d}"
        
        return account_number
    
    def _create_default_trading_rules(self, account):
        """Create standard trading rules for account"""
        default_rules = [
            {
                'name': 'Max Position Size',
                'type': 'position_limit',
                'config': {'max_position_size': 7000, 'max_contracts': 3},
                'priority': 1
            },
            {
                'name': 'Profit Target',
                'type': 'profit_target',
                'config': {'target_percentage': 50, 'recommend_close': True},
                'priority': 2
            },
            {
                'name': 'Stop Loss',
                'type': 'stop_loss',
                'config': {'loss_percentage': 200, 'auto_close': False},
                'priority': 1
            },
            {
                'name': 'Daily Loss Limit',
                'type': 'risk_limit',
                'config': {'max_daily_loss': 2.0},
                'priority': 1
            },
        ]
        
        for rule_data in default_rules:
            TradingRule.objects.create(
                managed_account=account,
                rule_name=rule_data['name'],
                rule_type=rule_data['type'],
                rule_config=rule_data['config'],
                priority=rule_data['priority'],
                is_active=True
            )
```

**Continue in file with additional methods...**
- `create_position()`
- `close_position()`
- `calculate_fees()`
- `get_account_summary()`

---

### **Phase 3: Views** (Week 3-4)

#### **File: `coda/investing/views/managed_trading_views.py`**

```python
"""
Managed Trading Views
Views for managing client options accounts
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from decimal import Decimal

from ..models import ManagedTradingAccount, OptionsPosition
from ..services.managed_trading_service import ManagedTradingService
from ..forms import ManagedAccountForm, OptionsPositionForm


@staff_member_required
def managed_accounts_list(request):
    """
    List all managed trading accounts
    """
    accounts = ManagedTradingAccount.objects.filter(
        status__in=['active', 'paused']
    ).select_related('client', 'account_manager').order_by('-created_at')
    
    context = {
        'accounts': accounts,
        'title': 'Managed Trading Accounts'
    }
    
    return render(request, 'investing/managed/accounts_list.html', context)


@staff_member_required
def create_managed_account(request):
    """
    Create new managed trading account
    """
    if request.method == 'POST':
        form = ManagedAccountForm(request.POST)
        if form.is_valid():
            service = ManagedTradingService()
            try:
                account = service.create_managed_account(
                    client_user=form.cleaned_data['client'],
                    account_data=form.cleaned_data
                )
                messages.success(request, f'Account {account.account_number} created successfully')
                return redirect('investing:managed_account_detail', account_id=account.id)
            except Exception as e:
                messages.error(request, f'Error creating account: {str(e)}')
    else:
        form = ManagedAccountForm()
    
    return render(request, 'investing/managed/create_account.html', {'form': form})


@login_required
def managed_account_detail(request, account_id):
    """
    View managed account details
    Permissions: Admin, Account Manager, or Client (owner)
    """
    account = get_object_or_404(ManagedTradingAccount, id=account_id)
    
    # Permission check
    if not (request.user.is_staff or 
            account.account_manager == request.user or 
            account.client == request.user):
        messages.error(request, 'Access denied')
        return redirect('investing:home')
    
    # Get positions
    positions = account.positions.filter(
        status='open'
    ).order_by('expiration_date')
    
    # Get service
    service = ManagedTradingService()
    summary = service.get_account_summary(account)
    
    context = {
        'account': account,
        'positions': positions,
        'summary': summary,
        'is_manager': account.account_manager == request.user,
        'is_client': account.client == request.user,
    }
    
    return render(request, 'investing/managed/account_detail.html', context)
```

**Additional views to implement:**
- `create_position()`
- `close_position()`
- `position_list()`
- `account_performance()`
- `generate_report()`

---

### **Phase 4: Templates** (Week 4-5)

#### **File: `coda/investing/templates/investing/managed/accounts_list.html`**

```django
{% extends "main/base_templates/new_base.html" %}
{% load static %}

{% block content %}
<div class="container-fluid py-4">
    <div class="row mb-4">
        <div class="col">
            <h2><i class="fa fa-briefcase"></i> Managed Trading Accounts</h2>
        </div>
        <div class="col text-end">
            <a href="{% url 'investing:create_managed_account' %}" class="btn btn-primary">
                <i class="fa fa-plus"></i> New Account
            </a>
        </div>
    </div>
    
    <!-- Summary Cards -->
    <div class="row mb-4">
        <div class="col-md-3">
            <div class="card">
                <div class="card-body">
                    <h6 class="text-muted">Total Accounts</h6>
                    <h3>{{ accounts.count }}</h3>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card">
                <div class="card-body">
                    <h6 class="text-muted">Total AUM</h6>
                    <h3>${{ total_aum|floatformat:0 }}</h3>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card">
                <div class="card-body">
                    <h6 class="text-muted">Total P&L</h6>
                    <h3 class="{% if total_pnl > 0 %}text-success{% else %}text-danger{% endif %}">
                        ${{ total_pnl|floatformat:0 }}
                    </h3>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card">
                <div class="card-body">
                    <h6 class="text-muted">Open Positions</h6>
                    <h3>{{ total_positions }}</h3>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Accounts Table -->
    <div class="card">
        <div class="card-body">
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>Account #</th>
                        <th>Client</th>
                        <th>Balance</th>
                        <th>P&L</th>
                        <th>ROI %</th>
                        <th>Positions</th>
                        <th>Manager</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for account in accounts %}
                    <tr>
                        <td><strong>{{ account.account_number }}</strong></td>
                        <td>{{ account.client.get_full_name }}</td>
                        <td>${{ account.current_balance|floatformat:2 }}</td>
                        <td class="{% if account.total_profit_loss > 0 %}text-success{% else %}text-danger{% endif %}">
                            ${{ account.total_profit_loss|floatformat:2 }}
                        </td>
                        <td class="{% if account.return_on_investment > 0 %}text-success{% else %}text-danger{% endif %}">
                            {{ account.return_on_investment|floatformat:2 }}%
                        </td>
                        <td>{{ account.positions.filter(status='open').count }}</td>
                        <td>{{ account.account_manager.get_full_name }}</td>
                        <td>
                            <span class="badge bg-{% if account.status == 'active' %}success{% else %}warning{% endif %}">
                                {{ account.get_status_display }}
                            </span>
                        </td>
                        <td>
                            <a href="{% url 'investing:managed_account_detail' account.id %}" class="btn btn-sm btn-info">
                                <i class="fa fa-eye"></i> View
                            </a>
                        </td>
                    </tr>
                    {% empty %}
                    <tr>
                        <td colspan="9" class="text-center text-muted">
                            No managed accounts yet. Create one to get started.
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>
{% endblock %}
```

**Additional templates needed:**
- `account_detail.html`
- `create_account.html`
- `position_entry_form.html`
- `client_dashboard.html`
- `performance_report.html`

---

### **Phase 5: URLs** (Week 5)

#### **File: `coda/investing/urls_managed_trading.py`**

```python
"""
URLs for Managed Options Trading
"""

from django.urls import path
from .views import managed_trading_views

urlpatterns = [
    # Account Management
    path('managed/accounts/', 
         managed_trading_views.managed_accounts_list, 
         name='managed_accounts_list'),
    path('managed/accounts/create/', 
         managed_trading_views.create_managed_account, 
         name='create_managed_account'),
    path('managed/accounts/<int:account_id>/', 
         managed_trading_views.managed_account_detail, 
         name='managed_account_detail'),
    
    # Position Management
    path('managed/positions/create/', 
         managed_trading_views.create_position, 
         name='create_managed_position'),
    path('managed/positions/<int:position_id>/close/', 
         managed_trading_views.close_position, 
         name='close_managed_position'),
    path('managed/positions/<int:position_id>/', 
         managed_trading_views.position_detail, 
         name='managed_position_detail'),
    
    # Client Portal
    path('managed/portal/', 
         managed_trading_views.client_portal_dashboard, 
         name='client_portal'),
    
    # Reporting
    path('managed/accounts/<int:account_id>/report/', 
         managed_trading_views.generate_account_report, 
         name='generate_account_report'),
    
    # API
    path('managed/api/accounts/<int:account_id>/summary/', 
         managed_trading_views.account_summary_api, 
         name='account_summary_api'),
    path('managed/api/positions/monitor/', 
         managed_trading_views.monitor_positions_api, 
         name='monitor_positions_api'),
]
```

#### **Update: `coda/investing/urls.py`**

```python
# Add at the end
urlpatterns += [
    # Managed Options Trading
    path('managed/', include('investing.urls_managed_trading')),
]
```

---

### **Phase 6: Admin Interface** (Week 5)

#### **File: `coda/investing/admin.py` (add to existing)**

```python
from .models import (
    ManagedTradingAccount, 
    OptionsPosition, 
    TradingRule, 
    TradingActivity
)

@admin.register(ManagedTradingAccount)
class ManagedTradingAccountAdmin(admin.ModelAdmin):
    list_display = [
        'account_number',
        'client',
        'current_balance',
        'total_profit_loss',
        'win_rate',
        'status',
        'account_manager'
    ]
    list_filter = ['status', 'account_manager', 'trading_enabled']
    search_fields = ['account_number', 'client__username', 'client__email']
    readonly_fields = ['account_number', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Account Information', {
            'fields': ('account_number', 'client', 'account_name', 'account_manager')
        }),
        ('Financial Details', {
            'fields': (
                'initial_capital', 'current_balance', 
                'cash_available', 'cash_reserved', 'high_water_mark'
            )
        }),
        ('Fee Structure', {
            'fields': (
                'management_fee_percentage', 
                'performance_fee_percentage', 
                'performance_threshold'
            )
        }),
        ('Risk Parameters', {
            'fields': (
                'max_position_risk', 'max_total_risk', 
                'max_daily_loss', 'max_weekly_loss', 'max_monthly_loss',
                'max_positions'
            )
        }),
        ('Status & Permissions', {
            'fields': ('status', 'trading_enabled', 'auto_trading_enabled')
        }),
        ('Performance Tracking', {
            'fields': (
                'total_trades', 'winning_trades', 'losing_trades',
                'total_profit_loss', 'total_fees_paid'
            ),
            'classes': ('collapse',)
        }),
    )


@admin.register(OptionsPosition)
class OptionsPositionAdmin(admin.ModelAdmin):
    list_display = [
        'symbol',
        'strategy',
        'managed_account',
        'expiration_date',
        'days_to_expiration',
        'unrealized_pnl',
        'status'
    ]
    list_filter = ['strategy', 'status', 'managed_account']
    search_fields = ['symbol', 'managed_account__account_number']
    readonly_fields = ['entry_date', 'created_at', 'updated_at']
    
    def days_to_expiration(self, obj):
        return obj.days_to_expiration
    days_to_expiration.short_description = 'DTE'
```

---

### **Phase 7: Forms** (Week 5)

#### **File: `coda/investing/forms/managed_trading_forms.py`**

```python
from django import forms
from decimal import Decimal
from datetime import date, timedelta

from ..models import ManagedTradingAccount, OptionsPosition, TradingRule


class ManagedAccountForm(forms.ModelForm):
    """
    Form for creating/editing managed trading accounts
    """
    
    class Meta:
        model = ManagedTradingAccount
        fields = [
            'client',
            'account_name',
            'initial_capital',
            'account_manager',
            'management_fee_percentage',
            'performance_fee_percentage',
            'performance_threshold',
            'max_position_risk',
            'max_total_risk',
            'max_daily_loss',
            'max_weekly_loss',
            'max_monthly_loss',
            'max_positions'
        ]
        widgets = {
            'client': forms.Select(attrs={'class': 'form-control'}),
            'account_name': forms.TextInput(attrs={'class': 'form-control'}),
            'initial_capital': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'account_manager': forms.Select(attrs={'class': 'form-control'}),
            # ... other widgets
        }
    
    def clean_initial_capital(self):
        capital = self.cleaned_data.get('initial_capital')
        if capital < Decimal('5000.00'):
            raise forms.ValidationError('Minimum account size is $5,000')
        return capital


class OptionsPositionForm(forms.ModelForm):
    """
    Form for creating options positions
    """
    
    class Meta:
        model = OptionsPosition
        fields = [
            'managed_account',
            'symbol',
            'strategy',
            'positions',  # JSONField - need custom widget
            'capital_required',
            'premium_collected',
            'max_profit',
            'max_loss',
            'expiration_date',
            'notes'
        ]
    
    def clean(self):
        cleaned_data = super().clean()
        account = cleaned_data.get('managed_account')
        capital = cleaned_data.get('capital_required')
        
        if account and capital:
            if capital > account.available_buying_power:
                raise forms.ValidationError(
                    f'Insufficient buying power. Available: ${account.available_buying_power}'
                )
        
        return cleaned_data
```

---

## 📊 Database Migrations

### **Create Migrations**

```bash
# In coda directory
python manage.py makemigrations investing --name managed_trading_models

# Review migration file
python manage.py sqlmigrate investing XXXX

# Apply migration
python manage.py migrate investing

# Verify
python manage.py check
```

### **Sample Migration Output**

```python
# Generated migration file
operations = [
    migrations.CreateModel(
        name='ManagedTradingAccount',
        fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True)),
            ('client', models.ForeignKey(...)),
            # ... all fields
        ],
        options={
            'verbose_name': 'Managed Trading Account',
            'ordering': ['-created_at'],
            'indexes': [...]
        },
    ),
    # ... other models
]
```

---

## 🧪 Implementation Checklist

### **Week 1: Database Foundation**
- [ ] Create `models/managed_trading.py`
- [ ] Define `ManagedTradingAccount` model
- [ ] Define `OptionsPosition` model
- [ ] Define `TradingRule` model
- [ ] Define `TradingActivity` model
- [ ] Create migration
- [ ] Apply migration
- [ ] Verify in database
- [ ] Register in admin
- [ ] Test CRUD operations in admin

### **Week 2: Services**
- [ ] Create `services/managed_trading_service.py`
- [ ] Implement `create_managed_account()`
- [ ] Implement `create_position()`
- [ ] Implement `close_position()`
- [ ] Implement `calculate_fees()`
- [ ] Implement `get_account_summary()`
- [ ] Create unit tests for service methods
- [ ] Test with sample data

### **Week 3-4: Views & Forms**
- [ ] Create `views/managed_trading_views.py`
- [ ] Create `forms/managed_trading_forms.py`
- [ ] Implement account list view
- [ ] Implement account detail view
- [ ] Implement create account view
- [ ] Implement position entry view
- [ ] Implement position close view
- [ ] Test all views

### **Week 5: Templates**
- [ ] Create `templates/investing/managed/` directory
- [ ] Create `accounts_list.html`
- [ ] Create `account_detail.html`
- [ ] Create `create_account.html`
- [ ] Create `position_entry_form.html`
- [ ] Create `client_dashboard.html`
- [ ] Test responsive design

### **Week 6: Risk & Monitoring**
- [ ] Implement position monitoring service
- [ ] Create alert generation logic
- [ ] Setup scheduled tasks (cron/celery)
- [ ] Test alert system
- [ ] Verify stop loss triggers

### **Week 7: Reporting**
- [ ] Implement daily summary email
- [ ] Implement weekly report
- [ ] Implement monthly statement
- [ ] Create PDF templates
- [ ] Test email delivery

### **Week 8: Testing & Launch**
- [ ] Full end-to-end testing
- [ ] Client UAT
- [ ] Performance testing
- [ ] Security audit
- [ ] Documentation review
- [ ] Go live!

---

## 🔧 Code Snippets & Examples

### **Example: Creating First Position**

```python
# In Django view or management command
from investing.services.managed_trading_service import ManagedTradingService
from investing.models import ManagedTradingAccount
from decimal import Decimal

# Get account
account = ManagedTradingAccount.objects.get(account_number='CODA-OPT-001')

# Create service
service = ManagedTradingService()

# Position data
position_data = {
    'symbol': 'AAPL',
    'strategy': 'short_put',
    'positions': [
        {
            'type': 'short_put',
            'strike': 170.00,
            'contracts': 1,
            'premium': 300.00,
            'delta': -0.30,
            'theta': 0.15
        }
    ],
    'capital_required': Decimal('17000.00'),
    'premium_collected': Decimal('300.00'),
    'max_profit': Decimal('300.00'),
    'max_loss': Decimal('16700.00'),
    'position_delta': Decimal('-0.30'),
    'position_theta': Decimal('0.15'),
    'expiration_date': date(2025, 11, 22),
    'notes': 'Cash-secured put on AAPL, IV Rank: 45'
}

# Create position
position = service.create_position(account, position_data)

print(f"✅ Position created: {position}")
print(f"Account buying power: ${account.available_buying_power}")
```

---

### **Example: Monitoring Positions**

```python
from investing.services.options_monitoring_service import OptionsMonitoringService

service = OptionsMonitoringService()

# Monitor all active accounts
active_accounts = ManagedTradingAccount.objects.filter(status='active')

for account in active_accounts:
    alerts = service.monitor_account(account)
    
    if alerts:
        for alert in alerts:
            print(f"🚨 Alert: {alert['message']}")
            
            # If critical, take action
            if alert['severity'] == 'critical':
                service.handle_critical_alert(account, alert)
```

---

### **Example: Generating Report**

```python
from investing.services.managed_trading_reporting_service import ManagedTradingReportingService

service = ManagedTradingReportingService()

# Generate monthly statement
account = ManagedTradingAccount.objects.get(account_number='CODA-OPT-001')
statement = service.generate_monthly_statement(account)

# Send to client
service.send_monthly_statement(account, statement)

print(f"✅ Monthly statement sent to {account.client.email}")
```

---

## 🎯 Best Practices

### **Code Organization**
```
coda/investing/
├── models/
│   ├── __init__.py
│   ├── core.py (existing)
│   └── managed_trading.py (NEW)
├── services/
│   ├── managed_trading_service.py (NEW)
│   ├── options_monitoring_service.py (NEW)
│   └── managed_trading_reporting_service.py (NEW)
├── views/
│   └── managed_trading_views.py (NEW)
├── forms/
│   └── managed_trading_forms.py (NEW)
├── templates/investing/managed/ (NEW)
└── urls_managed_trading.py (NEW)
```

### **Naming Conventions**
- **Models**: PascalCase (e.g., `ManagedTradingAccount`)
- **Services**: PascalCase with "Service" suffix
- **Views**: snake_case with descriptive names
- **URLs**: Kebab-case in URL patterns
- **Templates**: snake_case.html

### **Error Handling**

```python
try:
    position = service.create_position(account, position_data)
    messages.success(request, 'Position created successfully')
    return redirect('investing:managed_account_detail', account.id)
except ValidationError as e:
    messages.error(request, f'Validation error: {str(e)}')
    return redirect('investing:create_managed_position')
except Exception as e:
    logger.error(f'Unexpected error creating position: {e}')
    messages.error(request, 'An error occurred. Please try again.')
    return redirect('investing:managed_accounts_list')
```

---

## 📚 Development Workflow

### **Step-by-Step Development Process**

1. **Start with Models** (Week 1)
   - Define models in `models/managed_trading.py`
   - Create and run migrations
   - Test in Django admin

2. **Build Services** (Week 2)
   - Implement core business logic
   - Create unit tests
   - Test with sample data

3. **Create Views** (Week 3)
   - Implement view functions
   - Handle permissions
   - Add error handling

4. **Design Templates** (Week 4)
   - Create HTML templates
   - Add JavaScript for interactivity
   - Ensure responsive design

5. **Connect URLs** (Week 5)
   - Map URLs to views
   - Test all endpoints
   - Verify permissions

6. **Add Monitoring** (Week 6)
   - Implement scheduled tasks
   - Create alert system
   - Test notifications

7. **Build Reporting** (Week 7)
   - Create report generators
   - Test PDF generation
   - Verify email delivery

8. **Final Testing** (Week 8)
   - End-to-end testing
   - Load testing
   - Security testing
   - Client UAT

---

## 🎉 Implementation Summary

**Total Implementation Time:** 8 weeks  
**Files to Create:** ~15 new files  
**Lines of Code:** ~3,000 lines (estimated)  
**Leverages Existing Code:** 80%  
**Development Effort:** Medium

**Immediate Option:** Can start managing client account TODAY using existing `Portfolio` models while building full system in parallel.

---

## 🆕 PHASE 9 COMPLETE: Automation & Spread Builder (Nov 3, 2025)

### **Status:** ✅ Fully Implemented - Ready for Testing

### **New Features Added:**

#### 1. **Automatic Spread Builder** ✅
- **File:** `coda/investing/services/spread_builder.py`
- **Purpose:** Auto-converts single-leg positions to multi-leg spreads
- **Conversions:**
  - Short Puts → Bull Put Spreads (90% capital reduction)
  - Covered Calls → Bear Call Spreads (if no stock owned)
  - Credit Spreads → Import as-is
- **Algorithms:** AI-optimized spread width based on IV, DTE, price
- **Result:** $180k capital → $5-10k (97% savings!)

#### 2. **Auto-Approval Pipeline** ✅
- **File:** `coda/investing/services/auto_approval_service.py`
- **Features:**
  - Auto-approves positions with AI score ≥60
  - Smart distribution to accounts with <2 positions
  - Automatic batch creation
  - WhatsApp notifications
- **Time Savings:** 45 minutes → 0 minutes per upload

#### 3. **Manual Unusual Whales Integration** ✅
- **Updated:** `coda/investing/views/managed_trading/csv_upload.py`
- **Features:**
  - Process manually uploaded Whales CSVs (Options Flow, Dark Pool, Lit Flow)
  - Cross-reference symbols for timing signals
  - Score boosts: +10 to +50 points
  - 🟢🟡🔴 Entry signals
- **Value:** Know WHEN to enter (not just WHAT)

#### 4. **Smart Duplicate Ranking** ✅
- **Updated:** `coda/investing/views/managed_trading/csv_upload.py`
- **Features:**
  - Detects duplicate symbols in current upload + database
  - Ranks by AI score (40%), R:R ratio (30%), DTE (20%), Premium (10%)
  - Marks best as 🏆 RECOMMENDED
  - Marks alternatives with ⚠️ ALTERNATIVE warnings
  - Clear action recommendations in position notes
- **Value:** Know which position to approve when same symbol appears multiple times

#### 5. **One-Click Bulk Approval** ✅
- **Files:** `api_bulk_actions.py`, `suggested_positions.html`, `urls_managed_trading.py`
- **Features:**
  - Purple button on Pending Review page
  - Auto-approves all EXCELLENT positions (score ≥95)
  - Distributes top 3-6 to client accounts
  - Creates batches and sends notifications
  - Updates page automatically
- **Time Savings:** 5 minutes → 2 seconds per batch!

#### 6. **Bug Fixes Applied:**
- ✅ Fixed all OptionPlayRawData field name mismatches
- ✅ Updated strategy_type choices to include spreads
- ✅ Fixed approval button (@staff_member_required)
- ✅ Fixed spread converter recognition (Bear Call vs Bull Put)
- ✅ Fixed list modification during iteration
- ✅ Fixed IV Rank percentage display (3200% → 32%)
- ✅ Fixed import error (PositionScoringService)
- ✅ Fixed rating recalculation after score boosts
- ✅ Fixed premium calculation for spreads
- ✅ Added database migrations (0013, 0014)

### **Database Changes:**
- Migration 0013: Added `notes` field to SuggestedPosition
- Migration 0014: Updated `strategy_type` choices and max_length=30

### **Files Modified:**
1. `coda/investing/models.py` - Updated OptionPlayRawData strategy choices
2. `coda/investing/views/managed_trading/csv_upload.py` - Added spread builder + Whales integration
3. `coda/investing/services/optionplay_converter.py` - Handle all spread types
4. `coda/investing/views/managed_trading/position_suggestions.py` - Fixed approval endpoint
5. `coda/investing/templates/investing/managed/csv_upload_step3.html` - Added automation checkboxes

### **New Files Created:**
1. `coda/investing/services/spread_builder.py` (450 lines)
2. `coda/investing/services/auto_approval_service.py` (500 lines)

### **Testing Required:**
- [x] Restart Django server
- [x] Upload Short Puts CSV
- [x] Verify spread conversion: 12/12 ✅
- [x] Verify SuggestedPosition shows "Bull Put Spread" ✅
- [x] Verify SuggestedPosition shows "Bear Call Spread" for Covered Calls ✅
- [ ] Verify auto-approval for scores ≥95 (EXCELLENT only)
- [ ] Verify distribution to accounts with <2 positions
- [ ] Test one-click bulk approval button
- [ ] Upload with Whales CSVs and verify scoring boosts

### **Known Issues (All Fixed):**
1. ✅ AttributeError 'strike' → Fixed to 'sell_strike'
2. ✅ AttributeError 'premium_total' → Fixed to 'premium'
3. ✅ list.remove() error → Fixed with delayed ID updates
4. ✅ PositionBatch field mismatches → Fixed to use correct model fields
5. ✅ Missing strategy_type choices → Added migration

### **Next Steps:**
1. User tests upload with new code
2. Verify all features working
3. Deploy to Heroku UAT
4. Client acceptance testing

---

## 🎯 PHASE 10: PORTFOLIO INTELLIGENCE & OPTIMIZATION
**Status:** 📋 Approved - Ready to Implement (Nov 5, 2025)  
**Timeline:** 4-5 weeks (Phased: 10A → 10B → 10C → 10D)

### **Phase 10A: Smart Position Ranking** (CURRENT - Week 1-2)
**Priority:** 🔴 CRITICAL | **Status:** ⏳ Starting Implementation

#### **New Service:** `PositionRankingService`
**File:** `coda/investing/services/position_ranking_service.py` (NEW - 400 lines est.)

**Purpose:** Multi-factor ranking algorithm to select top 5 positions from 20+ approved positions.

**Core Methods:**
```python
class PositionRankingService:
    """Intelligent position ranking using multi-factor analysis"""
    
    # Ranking weights (configurable)
    WHALES_WEIGHT = Decimal('0.35')  # 35%
    EARNINGS_WEIGHT = Decimal('0.25')  # 25%
    PROFIT_WEIGHT = Decimal('0.20')   # 20%
    DTE_WEIGHT = Decimal('0.20')      # 20%
    
    def rank_positions(self, positions: List[SuggestedPosition]) -> List[Dict]:
        """
        Rank positions using weighted multi-factor algorithm
        
        Returns:
            [{
                'position': SuggestedPosition,
                'total_score': Decimal,
                'breakdown': {
                    'whales_score': Decimal,
                    'earnings_score': Decimal,
                    'profit_score': Decimal,
                    'dte_score': Decimal
                },
                'rank': int,  # 1-N
                'recommendation': str  # "STRONG BUY", "BUY", etc.
            }]
        """
        
    def _score_whales_signal(self, position) -> Decimal:
        """Score: 0-100 based on Unusual Whales alignment"""
        
    def _score_earnings_safety(self, position) -> Decimal:
        """Score: 100 if safe, 0 if earnings before expiry"""
        
    def _score_profit_potential(self, position) -> Decimal:
        """Score: 0-100 based on ROC%"""
        
    def _score_dte_diversity(self, position, all_positions) -> Decimal:
        """Penalize clustering in same expiry week"""
        
    def get_top_n(self, ranked_positions, n=5) -> List[Dict]:
        """Select top N positions with diversity checks"""
```

**Integration Points:**
- **View:** `coda/investing/views/managed_trading/position_suggestions.py`
  - Add "🏆 Top 5 Recommended" section at top
  - Show ranking breakdown table
  - Add "Accept Top 5" button
  
- **Template:** `coda/investing/templates/investing/staff/suggested_positions.html`
  - Display ranked list with scores
  - Color-code by recommendation (green=strong, yellow=moderate)
  - Show why each position ranked high

**Database Changes:**
- No new models needed (uses existing `SuggestedPosition`)
- Add `ranking_score` and `ranking_breakdown` JSON fields (optional, for caching)

---

### **Phase 10B: LEAPS Conversion** (Week 2-3)
**Priority:** 🟡 HIGH | **Status:** 📋 Planned

#### **New Service:** `LEAPSConverterService`
**File:** `coda/investing/services/leaps_converter_service.py` (NEW - 350 lines est.)

**Purpose:** Convert long-dated options (60-365 DTE) to Bull Call Spreads when Whales signal is strong.

**Core Methods:**
```python
class LEAPSConverterService:
    """Convert LEAPS to Bull Call Spreads for capital efficiency"""
    
    MIN_DTE = 60
    MAX_DTE = 365
    MIN_WHALES_SIGNAL = 30  # Require strong bullish signal
    
    def should_convert(self, option_data: Dict) -> bool:
        """Determine if LEAPS should be converted to spread"""
        
    def convert_to_bull_call_spread(self, long_call: Dict) -> Dict:
        """
        Convert long call to Bull Call Spread
        
        Strategy:
        - BUY ATM call (from Whales data)
        - SELL 10-15% OTM call (estimate premium)
        - Net debit = capital required
        
        Returns position data for Bull Call Spread
        """
        
    def calculate_short_strike(self, long_strike, stock_price) -> Decimal:
        """Calculate optimal short call strike (12% OTM)"""
        
    def estimate_short_premium(self, strike, dte, iv) -> Decimal:
        """Estimate premium using Black-Scholes (fallback if no API)"""
```

**Integration:**
- **File:** `coda/investing/views/managed_trading/csv_upload.py`
  - Modify `_parse_unusual_whales_flow()` to detect LEAPS
  - Call `LEAPSConverterService` for DTE > 60
  - Show conversion summary ("15 LEAPS converted to spreads")

**Example Output:**
```
LEAPS Conversion Summary:
✅ Converted: 15 positions
   - NBIS $115 Call (319 DTE) → $115/$130 Bull Call Spread
   - META $650 Call (227 DTE) → $650/$700 Bull Call Spread
   ...
💰 Capital Savings: $42,500 (67% reduction)
```

---

### **Phase 10C: Portfolio Optimizer** (Week 3-4)
**Priority:** 🔴 CRITICAL | **Status:** 📋 Planned

#### **New Models:** `Portfolio` and `PortfolioPosition`

**File:** `coda/investing/models.py` (Add to existing)

```python
class Portfolio(TimeStampedModel):
    """Generated portfolio of 3-5 positions"""
    
    # Identification
    name = models.CharField(max_length=100)  # "Aggressive Growth"
    strategy_type = models.CharField(
        max_length=20,
        choices=[
            ('aggressive', 'Aggressive Growth'),
            ('balanced', 'Balanced Income'),
            ('conservative', 'Conservative Safety')
        ]
    )
    description = models.TextField()
    
    # Metrics
    total_capital = models.DecimalField(max_digits=12, decimal_places=2)
    expected_roc = models.DecimalField(max_digits=6, decimal_places=2)
    avg_pop = models.DecimalField(max_digits=5, decimal_places=2)
    max_profit = models.DecimalField(max_digits=12, decimal_places=2)
    max_loss = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Diversity
    sector_diversity_score = models.IntegerField()  # 0-100
    dte_range = models.JSONField()  # {'min': 28, 'max': 48}
    earnings_conflicts = models.IntegerField(default=0)
    
    # Whales
    whales_alignment_score = models.IntegerField()  # 0-100
    
    # AI Scoring
    ai_score = models.IntegerField()  # 0-100 (overall portfolio score)
    ai_recommendation_rank = models.IntegerField()  # 1, 2, or 3
    is_recommended = models.BooleanField(default=False)  # Winner
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('generated', 'Generated'),
            ('selected', 'Selected by Staff'),
            ('submitted', 'Submitted to Clients'),
            ('rejected', 'Rejected')
        ],
        default='generated'
    )

class PortfolioPosition(TimeStampedModel):
    """Link between Portfolio and SuggestedPosition"""
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='positions')
    suggested_position = models.ForeignKey(SuggestedPosition, on_delete=models.CASCADE)
    allocation_pct = models.DecimalField(max_digits=5, decimal_places=2)  # % of portfolio
    selection_reason = models.TextField()  # Why this position was included
```

#### **New Service:** `PortfolioOptimizerService`
**File:** `coda/investing/services/portfolio_optimizer_service.py` (NEW - 600 lines est.)

**Core Methods:**
```python
class PortfolioOptimizerService:
    """Generate and compare 3 optimized portfolios"""
    
    def generate_portfolios(self, approved_positions, account_balance):
        """
        Create 3 distinct portfolios from approved positions
        
        Returns:
            {
                'aggressive': Portfolio,
                'balanced': Portfolio,
                'conservative': Portfolio,
                'comparison': ComparisonTable,
                'recommended': Portfolio  # Highest score
            }
        """
        
    def _build_aggressive_portfolio(self, positions, balance):
        """High ROC, Whales-driven, concentrated"""
        
    def _build_balanced_portfolio(self, positions, balance):
        """Diversified sectors, mixed DTE, moderate risk"""
        
    def _build_conservative_portfolio(self, positions, balance):
        """High PoP, max diversification, safety first"""
        
    def _score_portfolio(self, portfolio):
        """
        Score portfolio on 5 dimensions
        
        Returns:
            {
                'total': Decimal (0-100),
                'breakdown': {
                    'expected_return': Decimal,
                    'sharpe_ratio': Decimal,
                    'diversification': Decimal,
                    'whales_alignment': Decimal,
                    'capital_efficiency': Decimal
                }
            }
        """
```

**New Views:**
- **File:** `coda/investing/views/managed_trading/portfolio_optimizer.py` (NEW)
  - `portfolio_generator_view()` - Generate 3 portfolios
  - `portfolio_comparison_view()` - Side-by-side comparison
  - `portfolio_select_view()` - Submit selected portfolio

**New Templates:**
- `portfolio_generator.html` - Generate portfolios UI
- `portfolio_comparison.html` - 3-column comparison table
- `portfolio_detail.html` - Single portfolio breakdown

**New URLs:**
```python
# urls_managed_trading.py
path('portfolio/generate/', views.portfolio_generator_view, name='portfolio_generate'),
path('portfolio/compare/<int:batch_id>/', views.portfolio_comparison_view, name='portfolio_compare'),
path('portfolio/select/<int:portfolio_id>/', views.portfolio_select_view, name='portfolio_select'),
```

---

### **Phase 10D: Portfolio Hedging** (Week 4-5)
**Priority:** 🟡 MEDIUM | **Status:** 📋 Planned

#### **New Model:** `PortfolioHedge`

```python
class PortfolioHedge(TimeStampedModel):
    """Insurance positions for portfolio protection"""
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='hedges')
    
    # Hedge Details
    hedge_type = models.CharField(
        max_length=30,
        choices=[
            ('spy_put_spread', 'SPY Put Spread (Market)'),
            ('vix_call', 'VIX Call (Volatility)'),
            ('qqq_put_spread', 'QQQ Put Spread (Tech Sector)'),
            ('iwm_put_spread', 'IWM Put Spread (Small Cap)')
        ]
    )
    symbol = models.CharField(max_length=10)  # SPY, VIX, QQQ
    
    # Cost/Benefit
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    cost_pct = models.DecimalField(max_digits=5, decimal_places=2)  # % of portfolio
    max_protection = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Position Legs
    positions = models.JSONField()  # Hedge leg details
    
    # Analysis
    scenario_analysis = models.JSONField()  # Market down 5%, 10%, 20%
    recommended = models.BooleanField(default=False)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('recommended', 'Recommended'),
            ('accepted', 'Accepted'),
            ('rejected', 'Rejected'),
            ('executed', 'Executed')
        ],
        default='recommended'
    )
```

#### **New Service:** `PortfolioHedgingService`
**File:** `coda/investing/services/portfolio_hedging_service.py` (NEW - 450 lines est.)

**Core Methods:**
```python
class PortfolioHedgingService:
    """Calculate and recommend portfolio insurance"""
    
    INSURANCE_BUDGET_MIN = Decimal('0.05')  # 5%
    INSURANCE_BUDGET_MAX = Decimal('0.10')  # 10%
    
    def analyze_portfolio_risk(self, portfolio):
        """Analyze exposure and recommend hedges"""
        
    def recommend_hedges(self, portfolio):
        """
        Returns list of recommended hedges
        
        [{
            'type': 'spy_put_spread',
            'cost': Decimal,
            'protection': Decimal,
            'reason': str,
            'required': bool
        }]
        """
        
    def calculate_spy_put_spread(self, portfolio_value):
        """SPY put spread for market crash protection"""
        
    def calculate_vix_call(self, portfolio_value, current_vix):
        """VIX call for volatility spike"""
        
    def calculate_sector_hedge(self, portfolio, sector):
        """Sector-specific put spread (QQQ, IWM, etc.)"""
        
    def simulate_scenarios(self, portfolio, hedges):
        """
        Simulate market scenarios
        
        Returns:
            {
                'market_down_5pct': {'unhedged': Decimal, 'hedged': Decimal},
                'market_down_10pct': {...},
                'vix_spike_to_60': {...}
            }
        """
```

**New View:**
- **File:** `coda/investing/views/managed_trading/portfolio_hedging.py` (NEW)
  - `portfolio_hedge_view()` - Show hedge recommendations
  - `portfolio_add_hedge_view()` - Add hedge to portfolio

**New Template:**
- `portfolio_hedging.html` - Insurance dashboard

---

## 📊 PHASE 10 IMPLEMENTATION SUMMARY

### **Files to Create (8 New Files):**
1. `coda/investing/services/position_ranking_service.py` (~400 lines)
2. `coda/investing/services/leaps_converter_service.py` (~350 lines)
3. `coda/investing/services/portfolio_optimizer_service.py` (~600 lines)
4. `coda/investing/services/portfolio_hedging_service.py` (~450 lines)
5. `coda/investing/views/managed_trading/portfolio_optimizer.py` (~300 lines)
6. `coda/investing/views/managed_trading/portfolio_hedging.py` (~200 lines)
7. `coda/investing/templates/investing/managed/portfolio_comparison.html` (~250 lines)
8. `coda/investing/templates/investing/managed/portfolio_hedging.html` (~200 lines)

**Total New Code:** ~2,750 lines

### **Files to Modify:**
1. `coda/investing/models.py` - Add Portfolio, PortfolioPosition, PortfolioHedge models
2. `coda/investing/admin.py` - Register new models
3. `coda/investing/views/managed_trading/position_suggestions.py` - Add ranking
4. `coda/investing/views/managed_trading/csv_upload.py` - Add LEAPS detection
5. `coda/investing/templates/investing/staff/suggested_positions.html` - Show rankings
6. `coda/investing/urls_managed_trading.py` - Add 5 new URLs

### **Migrations Needed:**
- **0015_add_portfolio_models.py** - Portfolio, PortfolioPosition, PortfolioHedge

### **Testing Requirements:**
See [05_TESTING.md](05_TESTING.md) for Phase 10 test plans.

### **Deployment Plan:**
See [07_DEPLOYMENT.md](07_DEPLOYMENT.md) for Phase 10 deployment strategy.

---

## 📝 **CHANGE HISTORY**

| Date | Change | Reason | Files Modified | Status |
|------|--------|--------|----------------|--------|
| Nov 8, 2025 | **Phase 4 Broker Sync & Analytics Foundation** - Added `BrokerConnection`, broker sync endpoints, predictive analytics service + TradingView embed | Kick off integration phase with secure credential storage, staff-triggered sync, and forecasting preview | `models.py`, `services/broker_api_service.py`, `services/predictive_analytics_service.py`, `views/managed_trading/accounts.py`, `views/managed_trading/positions.py`, `views/managed_trading/analytics.py`, `templates/investing/managed/account_detail.html`, `templates/investing/managed/position_detail.html`, `templates/investing/managed/account_analytics.html`, `urls_managed_trading.py`, `admin.py`, `requirements.txt`, `tests/investing/01_unit/test_services.py`, `tests/investing/02_integration/test_views.py`, `migrations/0017_add_broker_connection.py` | ✅ Complete |
| Nov 8, 2025 | **Phase 3 Dashboard Polish** - Responsive client portal, scenario deltas, UW timeline copy | Improve managed client insights without exposing execution actions | `views/managed_trading/client.py`, `templates/investing/managed/client_account_detail.html`, `services/managed_trading_service.py`, `tests/investing/01_unit/test_services.py`, `tests/investing/02_integration/test_views.py` | ✅ Complete |
| Nov 5, 2025 | **Legacy Model Cleanup** - Removed 9 models (ShortPut, covered_calls, Portfolio, credit_spread, OverBoughtSold, Options_Returns, Cost_Basis, SavedResponses, FeeTierConfiguration duplicate) | Models used CharField for numeric values, superseded by OptionsPosition system | `models.py`, `admin.py`, `forms.py`, `views_legacy.py` | ✅ Complete |
| Nov 5, 2025 | **Created constants.py** - Centralized STRATEGY_CHOICES (19 strategies), SOURCE_CHOICES, STATUS_CHOICES | Single source of truth for constants across models | `investing/constants.py` (new file) | ✅ Complete |
| Nov 5, 2025 | **Bug Fix: IV Rank Filter** - Fixed format mismatch (compared 0.26 to 16 instead of 0.16) | All positions incorrectly filtered, 0 results | `views/managed_trading/csv_upload.py` line 421 | ✅ Fixed |
| Nov 5, 2025 | **Bug Fix: ROC Filter** - Fixed format mismatch (compared 0.015 to 1.5 instead of 0.015) | All positions incorrectly filtered by ROC | `views/managed_trading/csv_upload.py` line 424 | ✅ Fixed |
| Nov 5, 2025 | **Bug Fix: LEAPS KeyError** - Initialized `total_savings` and `savings_pct` in dictionary | KeyError crash during CSV import | `views/managed_trading/csv_upload.py` lines 900-901 | ✅ Fixed |
| Nov 5, 2025 | **Bug Fix: Approval Timeout** - Added 30s timeout to bulk approval fetch() | Browser hung indefinitely waiting for server | `templates/investing/staff/suggested_positions.html` lines 560-610 | ✅ Fixed |
| Nov 5, 2025 | **Bug Fix: Telegram Timeout** - Added 10s timeout to Telegram API | API calls could hang indefinitely | `services/notification_service.py` line 339 | ✅ Fixed |
| Nov 5, 2025 | **Data Migration** - Backed up legacy data (35 records) to CSV before deletion | Preserve historical data | Created `backup_legacy_positions.py` management command | ✅ Complete |
| Nov 5, 2025 | **Database Migration** - Created migration to drop legacy tables (investing_shortput, investing_covered_calls) | Clean up database | `migrations/0015_remove_legacy_models.py` | ⏸️ Pending |

### **Bug Details:**

**IV/ROC Filter Bug (Critical):**
- **Problem:** Form sends percentages as integers (16 for 16%), but code compared directly to CSV decimals (0.26 for 26%)
- **Impact:** `if 0.26 < 16` was always TRUE → everything filtered
- **Fix:** Divide form values by 100: `min_iv / 100`, `min_roc / 100`
- **Result:** Filters now work correctly

**Timeout Bugs:**
- **Problem:** JavaScript fetch() and API calls had no timeout → infinite hangs
- **Impact:** Approval button could hang forever
- **Fix:** Added 30s timeout to frontend, 10s to backend API calls
- **Result:** Graceful timeout with user feedback

---

**Next Phase:** [05_TESTING.md](05_TESTING.md)  
**Previous Phase:** [03_ARCHITECTURE.md](03_ARCHITECTURE.md)  
**Return to:** [README.md](README.md)

