# 🔍 COMPLETE MODEL AUDIT - ALL 38 MODELS
## CODA Investing App - November 5, 2025

**Purpose:** Comprehensive analysis of ALL 38 models to identify duplicates, legacy code, and consolidation opportunities

---

## 📊 SUMMARY

### **Total Models: 38**

**Categories:**
- ✅ **CURRENT SYSTEM** (Keep): 16 models
- ❌ **LEGACY** (Delete): 8 models
- ⚠️ **EVALUATE** (Need Decision): 5 models
- 🔧 **UTILITY** (Keep but Review): 9 models

---

## ❌ LEGACY MODELS (DELETE THESE - 8 models)

### **Category: CharField for Numeric Values** (4 models)

#### **1. credit_spread** (Line 563-583)
```python
class credit_spread(models.Model):
    symbol = models.CharField(max_length=255, blank=True, null=True)
    price = models.CharField(max_length=255, blank=True, null=True)      # ❌ Should be Decimal!
    sell_strike = models.CharField(max_length=255, blank=True, null=True) # ❌ Should be Decimal!
    buy_strike = models.CharField(max_length=255, blank=True, null=True)  # ❌ Should be Decimal!
    premium = models.CharField(max_length=255, blank=True, null=True)     # ❌ Should be Decimal!
    width = models.CharField(max_length=255, blank=True, null=True)       # ❌ Should be Decimal!
```

**Problems:**
- ❌ All numeric fields are CharField
- ❌ Same data as OptionPlayRawData (current system)
- ❌ Superseded by OptionsPosition + SuggestedPosition

**Replacement:** `OptionPlayRawData` (has proper Decimal fields)

---

#### **2. OverBoughtSold** (Line 602-632)
```python
class OverBoughtSold(models.Model):
    symbol = models.CharField(max_length=255, blank=True, null=True)
    last = models.CharField(max_length=255, blank=True, null=True)  # ❌ Stock price as CharField!
    volume = models.CharField(max_length=255, blank=True, null=True)  # ❌ Volume as CharField!
    RSI = models.CharField(max_length=255, blank=True, null=True)  # ❌ RSI as CharField!
    EPS = models.CharField(max_length=255, blank=True, null=True)  # ❌ EPS as CharField!
    PE = models.CharField(max_length=255, blank=True, null=True)  # ❌ PE ratio as CharField!
```

**Problems:**
- ❌ Technical indicators stored as CharField
- ❌ No relationships to positions or accounts
- ❌ Not used in current workflow

**Replacement:** Integrate into `MarketData` model (Line 1358) which has proper structure

---

#### **3. Options_Returns** (Line 648-683)
```python
class Options_Returns(models.Model):
    symbol = models.CharField(max_length=255, blank=True, null=True)
    qty = models.CharField(max_length=255, blank=True, null=True)  # ❌ Quantity as CharField!
    strike_price = models.CharField(max_length=255, blank=True, null=True)  # ❌ Strike as CharField!
    cost = models.CharField(max_length=255, blank=True, null=True)  # ❌ Cost as CharField!
    LT_GL = models.CharField(max_length=255, blank=True, null=True)  # ❌ Gain/Loss as CharField!
    ST_GL = models.CharField(max_length=255, blank=True, null=True)  # ❌ Gain/Loss as CharField!
    proceeds = models.CharField(max_length=255, blank=True, null=True)  # ❌ Proceeds as CharField!
```

**Problems:**
- ❌ All financial data as CharField
- ❌ Duplicate functionality with OptionsPositionHistory

**Replacement:** `OptionsPositionHistory` (Line 3664) - has proper Decimal fields

---

#### **4. Cost_Basis** (Line 686-702)
```python
class Cost_Basis(models.Model):
    symbol = models.CharField(max_length=255, blank=True, null=True)
    qty = models.CharField(max_length=255, blank=True, null=True)  # ❌ Quantity as CharField!
    strike_price = models.CharField(max_length=255, blank=True, null=True)  # ❌ Strike as CharField!
    cost = models.CharField(max_length=255, blank=True, null=True)  # ❌ Cost as CharField!
```

**Problems:**
- ❌ All numeric fields as CharField
- ❌ Duplicate of Options_Returns
- ❌ Superseded by OptionsPosition.capital_required

**Replacement:** `OptionsPosition` already tracks capital requirements properly

---

### **Category: Already Deleted** (3 models - for reference)

#### **5. ShortPut** (Line 585-587) ✅ **ALREADY DELETED**
```python
# LEGACY MODEL DELETED: ShortPut (Nov 5, 2025)
# Data backed up to: legacy_shortput_backup_20251105_112852.csv
# Reason: Used CharField for numeric values, superseded by OptionsPosition
```

#### **6. covered_calls** (Line 590-592) ✅ **ALREADY DELETED**
```python
# LEGACY MODEL DELETED: covered_calls (Nov 5, 2025)
# Data backed up to: legacy_covered_calls_backup_20251105_112852.csv
# Reason: Used CharField for numeric values, superseded by OptionsPosition
```

#### **7. Portfolio** (Line 595-597) ✅ **ALREADY DELETED**
```python
# LEGACY MODEL DELETED: Portfolio (Nov 5, 2025)
# Table never existed in database (migration never ran)
# Reason: Conflicts with ManagedTradingAccount, superseded by OptionsPosition
```

---

### **Category: Old/Unused** (1 model)

#### **8. SavedResponses** (Line 635-645)
```python
class SavedResponses(models.Model):
    CONDITION_CHOICES = (
        ("80", "Overbought (RSI > 80)"),
        ("20", "Oversold (RSI < 20)"),
    )
    condition = models.CharField(max_length=10, choices=CONDITION_CHOICES, unique=True)
    standard_response = models.TextField(null=True)
```

**Problems:**
- ⚠️ Only 2 records max (overbought/oversold responses)
- ⚠️ Not used in current system
- ⚠️ Could be config/settings instead of model

**Decision:** DELETE or move to settings/config

---

## ⚠️ EVALUATE CAREFULLY (5 models)

### **1. Ticker_Data** (Line 532-560)
```python
class Ticker_Data(models.Model):
    symbol = models.CharField(max_length=255, blank=True, null=True)
    overallrisk = models.DecimalField(max_digits=17, decimal_places=3)  # ✅ Proper Decimal
    sharesshort = models.DecimalField(max_digits=17, decimal_places=3)  # ✅ Proper Decimal
    enterprisetoebitda = models.DecimalField(...)  # ✅ Proper Decimal
    ebitda = models.DecimalField(...)  # ✅ Proper Decimal
    quickratio = models.DecimalField(...)  # ✅ Proper Decimal
    currentratio = models.DecimalField(...)  # ✅ Proper Decimal
    revenuegrowth = models.DecimalField(...)  # ✅ Proper Decimal
    fetched_date = models.DateField(auto_now_add=True)
    industry = models.CharField(max_length=500)
```

**Status:** ✅ **KEEP** - Has proper Decimal fields
**Purpose:** Fundamental stock data (ratios, growth, risk metrics)
**Overlap:** Some overlap with `MarketData` (Line 1358)

**Recommendation:** **KEEP** but consider consolidating with MarketData
- Ticker_Data = Fundamental data (P/E, EPS, ratios)
- MarketData = Price data (OHLC, volume, technical indicators)

---

### **2. InvestmentsStrategy** (Line 705-730)
```python
class InvestmentsStrategy(models.Model):
    symbol = models.CharField(max_length=255)
    strike_price = models.DecimalField(max_digits=10, decimal_places=2)  # ✅ Proper Decimal
    mid_price = models.DecimalField(max_digits=10, decimal_places=2)  # ✅ Proper Decimal
    bid_price = models.DecimalField(max_digits=10, decimal_places=2)  # ✅ Proper Decimal
    ask_price = models.DecimalField(max_digits=10, decimal_places=2)  # ✅ Proper Decimal
    implied_volatility_rank = models.DecimalField(...)  # ✅ Proper Decimal
    raw_return = models.DecimalField(...)  # ✅ Proper Decimal
    annualized_return = models.DecimalField(...)  # ✅ Proper Decimal
    trade_type = models.CharField(max_length=255)
```

**Status:** ⚠️ **EVALUATE**
**Purpose:** Similar to SuggestedPosition but older
**Overlap:** Significant overlap with `SuggestedPosition` (Line 3139)

**Recommendation:** 
- **If actively used** → Migrate data to SuggestedPosition
- **If not used** → DELETE

**Check Usage:**
```bash
# Check if referenced in views/services
grep -r "InvestmentsStrategy" coda/investing/ --include="*.py"
```

---

### **3. Returns_Balances** (Line 733-751)
```python
class Returns_Balances(TimeStampedModel):
    opening = models.DecimalField(max_digits=10, decimal_places=2)  # ✅ Proper Decimal
    closing = models.DecimalField(max_digits=10, decimal_places=2)  # ✅ Proper Decimal
    closing_date = models.DateField()
    
    @property
    def balances(self):
        return round(Decimal(self.closing - self.opening), 2)
```

**Status:** ✅ **KEEP**
**Purpose:** Track daily/monthly account balances
**Overlap:** Some overlap with `ManagedTradingAccount.cash_available`

**Recommendation:** **KEEP** - useful for historical balance tracking

---

### **4. Daily_Trades** (Line 754-811)
```python
class Daily_Trades(TimeStampedModel):
    symbol = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # ✅ Proper Decimal
    strike_price = models.DecimalField(max_digits=10, decimal_places=2)  # ✅ Proper Decimal
    credit = models.DecimalField(max_digits=10, decimal_places=2)  # ✅ Proper Decimal
    debit = models.DecimalField(max_digits=10, decimal_places=2)  # ✅ Proper Decimal
    qty = models.IntegerField()
    transaction = models.CharField(max_length=255)
```

**Status:** ⚠️ **EVALUATE**
**Purpose:** Daily trade log/journal
**Overlap:** Significant overlap with `TradingActivity` (Line 2233)

**Recommendation:**
- **If actively used** → Keep for historical data
- **If not used** → Migrate to TradingActivity
- **TradingActivity is more robust** (has foreign keys, better structure)

---

### **5. Investment_rates** (Line 381-488)
```python
class Investment_rates(models.Model):
    # Large model with many fields
    # Purpose: Unknown from this snippet
```

**Status:** ⚠️ **NEEDS REVIEW**
**Purpose:** Need to read full model to understand

---

## ✅ CURRENT SYSTEM (KEEP - 16 models)

### **Core Trading Models** (6 models) ⭐

#### **1. ManagedTradingAccount** (Line 1628)
```python
class ManagedTradingAccount(TimeStampedModel):
    """
    Core account model for managed options trading
    - Tracks balance, positions, P&L
    - Links to client user
    - Links to account manager
    """
```
**Status:** ✅ **EXCELLENT** - Keep

---

#### **2. OptionsPosition** (Line 1919)
```python
class OptionsPosition(TimeStampedModel):
    """
    Active options positions
    - Proper Decimal fields
    - JSONField for multi-leg strategies
    - Greeks tracking
    - P&L tracking
    - Status workflow
    """
```
**Status:** ✅ **EXCELLENT** - Keep

---

#### **3. SuggestedPosition** (Line 3139)
```python
class SuggestedPosition(TimeStampedModel):
    """
    Auto-fetched positions pending staff review
    - AI scoring integration
    - Whales integration
    - Approval workflow
    """
```
**Status:** ✅ **EXCELLENT** - Keep

---

#### **4. OptionPlayRawData** (Line 3449)
```python
class OptionPlayRawData(TimeStampedModel):
    """
    Raw CSV import data
    - Fallback when scraper fails
    - Proper Decimal fields
    - Converts to SuggestedPosition
    """
```
**Status:** ✅ **EXCELLENT** - Keep

---

#### **5. PositionBatch** (Line 2906)
```python
class PositionBatch(TimeStampedModel):
    """
    Batch approval system
    - Groups positions for client approval
    - WhatsApp notifications
    """
```
**Status:** ✅ **EXCELLENT** - Keep

---

#### **6. OptionsPositionHistory** (Line 3664)
```python
class OptionsPositionHistory(TimeStampedModel):
    """
    Closed positions for ML training
    - Tracks win/loss
    - Feeds AI scoring algorithm
    """
```
**Status:** ✅ **EXCELLENT** - Keep

---

### **Supporting Models** (10 models)

7. **TradingRule** (Line 2173) - Position size limits, risk rules ✅
8. **TradingActivity** (Line 2233) - Activity log ✅
9. **TradingSession** (Line 2313) - Trading sessions ✅
10. **FeeTierConfiguration** (Line 21, 2410) - Fee structure ✅ (Duplicate - consolidate)
11. **InvestorRiskProfile** (Line 2539) - Risk assessment ✅
12. **ManagedTradingApplication** (Line 2628) - Application workflow ✅
13. **ManagedTradingContract** (Line 2799) - Contracts ✅
14. **RiskAssessment** (Line 1065) - Risk analysis ✅
15. **RiskAlert** (Line 1159) - Risk alerts ✅
16. **ComplianceRecord** (Line 1225) - Compliance tracking ✅

---

## 🔧 UTILITY MODELS (KEEP - 9 models)

These are general-purpose models used across the system:

1. **MarketData** (Line 1358) - OHLC price data ✅
2. **InvestmentAnalytics** (Line 1395) - Analytics ✅
3. **InvestorCommunication** (Line 1492) - Communications ✅
4. **NotificationPreference** (Line 1553) - Notification settings ✅
5. **AuditTrail** (Line 1306) - Audit log ✅
6. **InvestmentPerformance** (Line 813) - Performance metrics ✅
7. **InvestmentReport** (Line 887) - Reports ✅
8. **InvestmentMilestone** (Line 937) - Milestones ✅
9. **InvestmentUpgradeOffer** (Line 986) - Upgrade offers ✅

---

## 📊 MODEL DUPLICATION ANALYSIS

### **Issue 1: FeeTierConfiguration (DUPLICATE)**
```python
# Line 21
class FeeTierConfiguration(TimeStampedModel):
    # ... fee config ...

# Line 2410
class FeeTierConfiguration(TimeStampedModel):  # ❌ DUPLICATE!
    # ... fee config ...
```

**Problem:** Same model defined twice!
**Solution:** Keep Line 2410 (newer), delete Line 21

---

### **Issue 2: Options Data Overlap**

**Legacy Models (DELETE):**
- `credit_spread` → Use `OptionPlayRawData`
- `Options_Returns` → Use `OptionsPositionHistory`
- `Cost_Basis` → Use `OptionsPosition.capital_required`

**Current Models (KEEP):**
- `OptionsPosition` - Active positions
- `SuggestedPosition` - Pending positions
- `OptionPlayRawData` - CSV import
- `OptionsPositionHistory` - Closed positions

---

### **Issue 3: Trade Tracking Overlap**

**Legacy Models:**
- `Daily_Trades` - Daily trade journal (Line 754)

**Current Models:**
- `TradingActivity` - Activity log with foreign keys (Line 2233)

**Recommendation:** 
- Keep both if Daily_Trades has historical data
- Future trades → use TradingActivity only

---

### **Issue 4: Market Data Overlap**

**Models:**
- `Ticker_Data` - Fundamental data (P/E, EPS, ratios) ✅ KEEP
- `OverBoughtSold` - Technical indicators (RSI, etc.) ❌ DELETE
- `MarketData` - Price data (OHLC, volume) ✅ KEEP

**Recommendation:**
- DELETE `OverBoughtSold` (CharField for numbers)
- Integrate RSI/technical indicators into `MarketData`

---

## 🎯 ACTION PLAN

### **Phase 1: Delete Legacy Models** (2 hours)

**Models to Delete:**
1. ❌ `credit_spread` (Line 563-583)
2. ❌ `OverBoughtSold` (Line 602-632)
3. ❌ `Options_Returns` (Line 648-683)
4. ❌ `Cost_Basis` (Line 686-702)
5. ❌ `SavedResponses` (Line 635-645) - or move to settings
6. ❌ `FeeTierConfiguration` (Line 21) - duplicate

**Already Deleted:**
- ✅ `ShortPut`
- ✅ `covered_calls`
- ✅ `Portfolio`

---

### **Phase 2: Evaluate Usage** (1 hour)

**Check if these are still used:**
```bash
# Check InvestmentsStrategy usage
grep -r "InvestmentsStrategy" coda/investing/ --include="*.py"

# Check Daily_Trades usage
grep -r "Daily_Trades" coda/investing/ --include="*.py"

# Check Investment_rates usage
grep -r "Investment_rates" coda/investing/ --include="*.py"
```

**Decision Matrix:**
- **If used in active views/services** → Keep for now, plan migration
- **If only in admin.py** → Delete (just admin interface)
- **If not referenced** → Safe to delete

---

### **Phase 3: Data Migration** (2-4 hours, if needed)

**If models have data:**
1. Export data to CSV backup
2. Create migration script to move to current models
3. Verify data integrity
4. Delete old models

**Migration Mapping:**
- `credit_spread` → `OptionPlayRawData`
- `Options_Returns` → `OptionsPositionHistory`
- `OverBoughtSold` technical indicators → `MarketData`
- `InvestmentsStrategy` → `SuggestedPosition`

---

### **Phase 4: Consolidate Constants** (30 minutes)

Already planned in `CLEANUP_HANDOFF_FOR_NEW_CHAT.md`

---

### **Phase 5: Tests** (4-6 hours)

Already planned in `CLEANUP_HANDOFF_FOR_NEW_CHAT.md`

---

## 📋 DATA CHECK SCRIPT

```python
# File: check_all_legacy_models.py
"""
Check ALL legacy models for data before deletion
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda.settings')
django.setup()

from investing.models import (
    credit_spread,
    OverBoughtSold,
    Options_Returns,
    Cost_Basis,
    SavedResponses,
    InvestmentsStrategy,
    Daily_Trades,
    Investment_rates,
    Ticker_Data,
    Returns_Balances
)

print("=" * 80)
print("LEGACY MODEL DATA CHECK")
print("=" * 80)

# Models to DELETE
print("\n🔥 MODELS TO DELETE (CharField for numbers):")
print(f"  credit_spread: {credit_spread.objects.count()} records")
print(f"  OverBoughtSold: {OverBoughtSold.objects.count()} records")
print(f"  Options_Returns: {Options_Returns.objects.count()} records")
print(f"  Cost_Basis: {Cost_Basis.objects.count()} records")
print(f"  SavedResponses: {SavedResponses.objects.count()} records")

# Models to EVALUATE
print("\n⚠️  MODELS TO EVALUATE (Check if still used):")
print(f"  InvestmentsStrategy: {InvestmentsStrategy.objects.count()} records")
print(f"  Daily_Trades: {Daily_Trades.objects.count()} records")
print(f"  Investment_rates: {Investment_rates.objects.count()} records")

# Models to KEEP (for reference)
print("\n✅ MODELS TO KEEP (for reference):")
print(f"  Ticker_Data: {Ticker_Data.objects.count()} records")
print(f"  Returns_Balances: {Returns_Balances.objects.count()} records")

print("\n" + "=" * 80)
```

---

## 🎉 FINAL MODEL COUNT

### **BEFORE Cleanup: 38 models**
### **AFTER Cleanup: 29 models** (-9 models, -24%)

**Breakdown:**
- ✅ **Keep (Current System):** 16 models
- ✅ **Keep (Utility):** 9 models
- ✅ **Keep (Evaluate first):** 4 models (InvestmentsStrategy, Daily_Trades, Investment_rates, Returns_Balances)
- ❌ **Delete:** 9 models (credit_spread, OverBoughtSold, Options_Returns, Cost_Basis, SavedResponses, ShortPut, covered_calls, Portfolio, FeeTierConfiguration duplicate)

---

## 🚀 NEXT STEPS

1. ✅ Run data check script
2. ✅ Export data from models with records
3. ✅ Delete legacy models from models.py
4. ✅ Create deprecation migration
5. ✅ Create constants.py
6. ✅ Update models to use constants
7. ✅ Write tests
8. ✅ Deploy

**Total Time:** 8-12 hours (including data migration if needed)

---

**Ready to proceed with comprehensive cleanup!** 🎯

