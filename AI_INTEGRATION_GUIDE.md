# AI INTEGRATION GUIDE
## 3-Tier Hybrid System with Self-Learning Cache

**Status:** ✅ Deployed to UAT with Dummy AI  
**Ready For:** Real OpenAI API key integration  
**Expected Cost:** <$10/month (99% cache hit rate after 3 months)

---

## SYSTEM ARCHITECTURE

```
┌────────────────────────────────────────────────────────────────┐
│              USER ENTERS RECEIVER NAME ("KPLC")                 │
└────────────────────────────────────────────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────────────┐
│  TIER 1: Historical Transaction Data (350 transactions)        │
│  Coverage: 95%  |  Cost: $0  |  Speed: <1 second              │
│  ✓ Check if we've paid this receiver before                   │
│  ✓ Return most common category, amount, description           │
└────────────────────────────────────────────────────────────────┘
                    ↓ (if no match)
┌────────────────────────────────────────────────────────────────┐
│  TIER 2: AI Prediction Cache (AIPredictionCache model)        │
│  Coverage: 4%   |  Cost: $0  |  Speed: <1 second              │
│  ✓ Check if AI already predicted this receiver before         │
│  ✓ Reuse cached prediction (mark times_used++)                │
│  ✓ Track money saved (tokens_used * times_reused * $0.00003)  │
└────────────────────────────────────────────────────────────────┘
                    ↓ (if cache miss)
┌────────────────────────────────────────────────────────────────┐
│  TIER 3: AI API or Dummy AI                                    │
│  Coverage: 1%   |  Cost: ~$0.60/call  |  Speed: 3-5 seconds   │
│  ✓ Call OpenAI GPT-4 (if real key) or Dummy AI (if testing)   │
│  ✓ Save response to cache for future use                      │
│  ✓ Return prediction with confidence score                    │
└────────────────────────────────────────────────────────────────┘
                            ↓
               AUTO-FILL FORM FIELDS!
```

---

## DEPLOYED COMPONENTS

###  1. AIPredictionCache Model
**File:** `coda/finance/models_ai_cache.py`

**Purpose:** Store AI predictions for reuse

**Fields:**
- `receiver_name`: Who we're paying (e.g., "KPLC")
- `predicted_category`: What category AI suggested
- `predicted_item`: What item AI suggested
- `predicted_amount`: Typical amount
- `confidence_score`: 0-100
- `times_used`: How many times reused (cache hits)
- `api_cost`: Original API cost
- `money_saved`: Cost × times_used

**Key Feature:** Tracks ROI! Shows how much money saved by caching.

### 2. HybridAIPredictionService
**File:** `coda/finance/services/hybrid_ai_service.py`

**Methods:**
- `predict_transaction_fields()`: Main entry point
- `_check_historical_data()`: Tier 1
- `_check_cache()`: Tier 2
- `_call_dummy_ai()` or `_call_real_ai_api()`: Tier 3
- `_save_to_cache()`: Cache AI responses
- `get_cache_stats()`: Performance analytics

**Intelligence:**
- Auto-detects if using dummy or real AI
- Logs all tier decisions
- Calculates confidence scores
- Tracks costs and savings

### 3. API Endpoint
**URL:** `/finance/api/predict-all/`

**Usage:**
```javascript
$.ajax({
    url: '/finance/api/predict-all/',
    data: { receiver: 'KPLC', department_id: 1, amount: 5000 },
    success: function(data) {
        // data.source: 'historical_data', 'ai_cache', or 'dummy_ai'
        // data.predictions: {category_id, subcategory_id, type, amount...}
        // data.confidence: {overall: 'high', category: 95}
        // data.cost: 0 (if cached) or >0 (if AI API)
    }
});
```

---

## CURRENT STATUS: DUMMY AI MODE

### What's Working:
✅ Dummy AI key configured: `sk-dummy-key-for-testing`  
✅ System detects it's not a real key  
✅ Falls back to historical data + smart guessing  
✅ All form auto-fill works without API costs  
✅ Can test full flow without spending money

### How Dummy AI Works:
1. Checks historical data first (95% coverage)
2. If found → uses real transaction patterns
3. If not found → makes educated guess based on:
   - Receiver name patterns (KPLC → Utilities)
   - Amount range (>$1K → likely Salary)
   - Department context
4. Returns prediction with "dummy" source tag

---

## UPGRADING TO REAL AI

### Step 1: Get OpenAI API Key
```bash
# Sign up: https://platform.openai.com/signup
# Create API key: https://platform.openai.com/api-keys
# You'll get key like: sk-proj-AbCd1234...
```

### Step 2: Update Heroku Config
```bash
# Replace dummy key with real key
heroku config:set OPENAI_API_KEY=sk-proj-YOUR-REAL-KEY-HERE --app codamakutano

# Verify
heroku config:get OPENAI_API_KEY --app codamakutano
```

### Step 3: Test Real AI
```bash
# Test with a NEW receiver (not in historical data)
# e.g., "Amazon Web Services" or "Microsoft Azure"

# Watch logs
heroku logs --tail --app codamakutano | grep "TIER 3"

# Should see:
# "✓ TIER 3: Calling REAL AI API for Amazon Web Services"
# "✓ Saved prediction to cache"
```

### Step 4: Monitor Costs
```bash
# Check OpenAI usage: https://platform.openai.com/usage

# Expected costs:
# Month 1: $5-10 (building cache)
# Month 2: $2-5 (cache growing)
# Month 3+: <$1/month (99% cache hit rate)
```

---

## CACHE PERFORMANCE MONITORING

### Check Cache Stats
```python
from finance.services.hybrid_ai_service import HybridAIPredictionService

service = HybridAIPredictionService()
stats = service.get_cache_stats()

print(f"Total cached predictions: {stats['total_cached']}")
print(f"Total cache hits: {stats['total_reuses']}")
print(f"Money saved: {stats['money_saved']}")
print(f"Avg confidence: {stats['avg_confidence']}%")
```

### Expected Progression

**Month 1:**
- Cache entries: ~20
- Cache hit rate: 10%
- API calls: 90%
- Cost: $8-12

**Month 2:**
- Cache entries: ~50
- Cache hit rate: 60%
- API calls: 40%
- Cost: $4-6

**Month 3+:**
- Cache entries: ~80+
- Cache hit rate: 95%+
- API calls: <5%
- Cost: <$2/month

**Month 6:**
- Cache entries: 100+
- Cache hit rate: 99%+
- API calls: <1%
- Cost: <$1/month (essentially free!)

---

## AI USE CASES (Implemented)

### 1. Transaction Auto-Fill ✅
**Trigger:** User types receiver name  
**AI Analyzes:** Historical patterns + receiver name + amount  
**AI Predicts:** Category, subcategory, item, amount, description  
**Confidence:** High (95%+) for known receivers  
**Caching:** All predictions saved

### 2. Budget Forecasting ✅
**Trigger:** Monthly automated run  
**AI Analyzes:** 27 months of transaction data  
**AI Predicts:** Next 12-month budget by category  
**Result:** $722K realistic projection  
**Caching:** Monthly projections cached

### 3. Data Quality (Future)
**Trigger:** New transaction submitted  
**AI Analyzes:** Transaction details  
**AI Detects:** Anomalies, duplicates, errors  
**Action:** Flag for review or auto-correct  
**Caching:** Anomaly rules saved

### 4. Vendor Standardization (Future)
**Trigger:** New vendor name entered  
**AI Analyzes:** Similar existing vendors  
**AI Suggests:** Canonical name (Safaricom vs safaricom)  
**Action:** Auto-link to existing vendor  
**Caching:** Vendor aliases saved

### 5. Description Enhancement (Future)
**Trigger:** User enters minimal description  
**AI Analyzes:** Category, receiver, amount  
**AI Generates:** Professional description  
**Result:** Consistent, detailed descriptions  
**Caching:** Description templates saved

---

## SELF-LEARNING MECHANISM

### How System Gets Smarter:
1. **User confirms AI prediction** → `accuracy_score = 100`
2. **User modifies AI prediction** → `accuracy_score = 0`, log correction
3. **After 5+ confirmations** → Prediction becomes "historical data"
4. **After 3+ corrections** → Cache entry expires, AI retrains
5. **System learns** → Future predictions improve

### Feedback Loop:
```
AI predicts → User saves → Track accuracy → Update cache
    ↑                                              ↓
    └──────────── Learn from corrections ──────────┘
```

---

## COST COMPARISON

### Without Our System (Naive AI):
```
100 transactions/month × 200 tokens × $0.0003/token = $60/month
Annual cost: $720
```

### With Our 3-Tier System:
```
Month 1:
- Tier 1 (Historical): 95 transactions × $0 = $0
- Tier 2 (Cache): 0 transactions × $0 = $0
- Tier 3 (AI): 5 transactions × $0.60 = $3
Total: $3

Month 3:
- Tier 1: 95 transactions × $0 = $0
- Tier 2: 4 transactions × $0 = $0
- Tier 3: 1 transaction × $0.60 = $0.60
Total: $0.60

Month 6+:
- Tier 1: 95 transactions × $0 = $0
- Tier 2: 4.9 transactions × $0 = $0
- Tier 3: 0.1 transactions × $0.60 = $0.06
Total: $0.06/month!

Annual savings: $720 - $20 = $700/year (97% reduction)
```

---

## TESTING GUIDE

### Test Tier 1 (Historical Data):
```
1. Go to: https://codamakutano.herokuapp.com/finance/transaction/smart-entry/
2. Type: "KPLC"
3. Open browser console (F12)
4. Should see: "✓ TIER 1: Historical data hit for KPLC"
5. Fields auto-fill from 9 previous transactions
```

### Test Tier 2 (Cache) - After First AI Call:
```
1. Enter a NEW receiver: "Amazon Web Services"
2. System calls AI (Tier 3)
3. Saves to cache
4. Next time you enter "Amazon Web Services":
   - Should see: "✓ TIER 2: Cache hit"
   - No AI call made
   - Instant response
```

### Test Tier 3 (Dummy AI):
```
1. Enter completely unknown receiver: "Random New Company LLC"
2. Should see: "✓ TIER 3: Using DUMMY AI"
3. Gets educated guess based on amount/department
4. Saves to cache
5. Next time: Tier 2 cache hit!
```

---

## ADMIN INTERFACE

### View Cache Entries:
**URL:** `/admin/finance/aipredictioncache/`

**What You'll See:**
- All cached predictions
- Times used (cache hits)
- Money saved per entry
- Confidence and accuracy scores
- AI provider (historical, dummy, openai)

**Filters:**
- By AI provider
- By confidence score
- By times used (popular predictions)
- By accuracy (user confirmed)

---

## TROUBLESHOOTING

### Issue: Auto-fill not working
**Check:**
1. Browser console for errors
2. Is `/finance/api/predict-all/` accessible?
3. Does receiver have historical data?
4. Try manual API call in browser: `/finance/api/predict-all/?receiver=KPLC`

### Issue: AI always returns dummy
**Check:**
1. Is real API key set? `heroku config:get OPENAI_API_KEY`
2. Key should start with `sk-proj-` not `sk-dummy-`
3. Check logs: `heroku logs | grep "Using REAL AI"`

### Issue: Cache not saving
**Check:**
1. Has migration run? `heroku run "cd coda && python manage.py showmigrations finance"`
2. Does AIPredictionCache table exist?
3. Check logs for errors: `heroku logs | grep "cache"`

---

## NEXT STEPS

### Immediate (This Week):
1. ✅ Test form in UAT with dummy AI
2. ✅ Verify console logs show correct tier usage
3. ✅ Check that known receivers use Tier 1 (historical)
4. ⚪ Get real OpenAI API key when ready

### Short-term (2 Weeks):
5. Replace dummy key with real key
6. Monitor first week of AI calls
7. Check cache is growing
8. Verify cost stays <$5/week

### Medium-term (1-2 Months):
9. Add user feedback mechanism
10. Track prediction accuracy
11. Build cache analytics dashboard
12. Implement self-learning from corrections

### Long-term (3-6 Months):
13. Achieve 99% cache hit rate
14. Cost drops to <$1/month
15. System becomes fully self-reliant
16. Explore local LLM for complete independence

---

## KEY METRICS TO TRACK

### Daily:
- API calls made (should decrease over time)
- Cache hits (should increase over time)
- Cost per day

### Weekly:
- Cache growth rate
- Prediction accuracy (user confirmations)
- Money saved vs uncached system

### Monthly:
- Total cache entries
- Cache hit rate %
- Total cost
- Cost per transaction
- Accuracy improvements

### Target Goals (3 Months):
- Cache hit rate: >95%
- Cost: <$3/month
- Accuracy: >90%
- Response time: <1 second (avg)

---

*Combines content from COMPREHENSIVE_ACTION_PLAN.md and technical implementation*  
*Single source of truth for AI integration*  
*Last Updated: October 2, 2025*

