# OptionPlay Data Structure Analysis - Nov 2, 2025

## 📊 CSV Files Analysis

### 1. **Credit Spreads** (`credit_spread.csv`)

**Columns**:
```
Symbol, Strategy, Type, Price, Sell Strike, Buy Strike, Expiry, Premium, 
Width, Prem/Width, IV Rank, Earnings Date
```

**Example Row**:
```
DIS, Bearish, Call, $101.50, $102.00, $107.00, 08/02/2024, $2.30, $5.00, 45.9%, 14%, 08/07/2024 (48) AM
```

**Strategy Logic**:
- **Bearish + Call** = Bear Call Spread (sell call, buy higher call)
- **Bullish + Put** = Bull Put Spread (sell put, buy lower put)

**Key Fields**:
- `Sell Strike`: Short leg strike
- `Buy Strike`: Long leg strike
- `Width`: Spread width ($5.00 = $5 * 100 = $500 capital required)
- `Premium`: Premium collected per contract
- `IV Rank`: Implied Volatility Rank (higher = better for selling premium)

---

### 2. **Short Puts** (`shortput.csv`)

**Columns**:
```
Symbol, Action, Expiry, Days To Expiry, Strike Price, Mid Price, Bid Price, 
Ask Price, Implied Volatility Rank, Earnings Date, Earnings Flag, Stock Price, 
Raw Return, Annualized Return, Distance To Strike
```

**Example Row**:
```
TIL, Sell to Open, 07/19/2024, 30, $7.50, $6.75, $6.50, $7.00, 14%, 08/14/2024, N, $9.86, 68.46%, 861.63%, -23.94%
```

**Key Fields**:
- `Strike Price`: Where you sell the put
- `Mid Price`: Premium collected (midpoint of bid/ask)
- `Stock Price`: Current stock price
- `Distance To Strike`: How far OTM (negative = below current price = safer)
- `Raw Return`: Return on capital if kept until expiration
- `Annualized Return`: Yearly equivalent return

---

### 3. **Covered Calls** (`covered_calls.csv`)

**Expected Similar Structure** (need to verify):
```
Symbol, Action, Expiry, Days To Expiry, Strike Price, Premium, Stock Price, ...
```

**Strategy**:
- Buy 100 shares of stock
- Sell 1 call contract against it
- Collect premium while owning stock

---

## 🎯 Mapping to Our `SuggestedPosition` Model

### Current Model Fields:
```python
symbol, strategy, positions (JSONField), expiration_date, dte, 
premium_collected, capital_required, max_profit, max_loss, breakeven,
probability_of_profit, position_delta, position_theta, position_gamma, position_vega,
ai_confidence, ai_reasoning, api_response_data
```

### Mapping from CSV:

| CSV Field | Our Model Field | Transformation |
|-----------|----------------|----------------|
| **Symbol** | `symbol` | Direct |
| **Strategy** (Bearish/Bullish) + **Type** (Call/Put) | `strategy` | "Bearish Call" → `bear_call_spread` |
| **Sell Strike**, **Buy Strike** | `positions` JSONField | `[{type: 'short_call', strike: X}, {type: 'long_call', strike: Y}]` |
| **Expiry** | `expiration_date` | Parse date |
| **Days To Expiry** | `dte` | Direct |
| **Premium** | `premium_collected` | `Premium * 100` (per contract) |
| **Width** | `capital_required` | `Width * 100` |
| **Premium** | `max_profit` | Same as `premium_collected` |
| **Width - Premium** | `max_loss` | `capital_required - max_profit` |
| **Sell Strike - Premium** (put) or **Sell Strike + Premium** (call) | `breakeven` | Calculate |
| **IV Rank** | `ai_confidence` | Higher IV = higher confidence |
| N/A (need to calculate) | `probability_of_profit` | Estimate from delta/IV |

---

## 🗄️ New Table Design: `OptionPlayRawData`

Since Playwright scraping has challenges on Heroku, we'll create a **manual upload table**:

### Model: `OptionPlayRawData`

```python
class OptionPlayRawData(TimeStampedModel):
    """
    Raw data uploaded from OptionPlay CSV exports
    Serves as fallback when web scraper fails
    
    Workflow:
    1. Staff downloads CSV from OptionPlay manually
    2. Uploads via Django admin
    3. System converts to SuggestedPosition format
    4. Regular approval workflow continues
    """
    
    # Source tracking
    STRATEGY_TYPE_CHOICES = [
        ('credit_spread', 'Credit Spread'),
        ('short_put', 'Short Put'),
        ('covered_call', 'Covered Call'),
    ]
    strategy_type = models.CharField(max_length=20, choices=STRATEGY_TYPE_CHOICES)
    
    # Data fields (flexible to accommodate all 3 CSV types)
    symbol = models.CharField(max_length=10)
    
    # Credit Spread specific
    spread_strategy = models.CharField(max_length=20, blank=True, null=True)  # Bearish/Bullish
    option_type = models.CharField(max_length=10, blank=True, null=True)  # Call/Put
    stock_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    sell_strike = models.DecimalField(max_digits=10, decimal_places=2)
    buy_strike = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    # Common fields
    expiry = models.DateField()
    days_to_expiry = models.IntegerField()
    premium = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Optional metrics
    iv_rank = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    width = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    prem_width_ratio = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    raw_return = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    annualized_return = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    distance_to_strike = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    earnings_date = models.CharField(max_length=50, blank=True)
    earnings_flag = models.CharField(max_length=5, blank=True)
    
    # Upload tracking
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    upload_date = models.DateTimeField(auto_now_add=True)
    is_processed = models.BooleanField(default=False)
    processed_date = models.DateTimeField(null=True, blank=True)
    created_suggestion = models.ForeignKey('SuggestedPosition', null=True, blank=True, on_delete=models.SET_NULL)
    
    class Meta:
        verbose_name = "OptionPlay Raw Data"
        verbose_name_plural = "OptionPlay Raw Data"
        ordering = ['-upload_date', 'symbol']
        indexes = [
            models.Index(fields=['strategy_type', 'is_processed']),
            models.Index(fields=['symbol', 'expiry']),
        ]
```

---

## 💡 Proposed Solution: 3-Tier Fallback System

### Current (2-tier):
```
1. OptionPlay API (if configured)
2. Playwright Scraper (if credentials set)
3. Mock Data (fallback)
```

### Proposed (4-tier):
```
1. OptionPlay API (if configured)
2. Playwright Scraper (if credentials set)
3. Database Table (OptionPlayRawData - manually uploaded CSVs)
4. Mock Data (last resort)
```

---

## 🔧 Implementation Plan

### Step 1: Create `OptionPlayRawData` Model
- Add model to `coda/investing/models.py`
- Support all 3 CSV formats (credit spreads, short puts, covered calls)

### Step 2: Create CSV Import View
- Admin action: "Import OptionPlay CSV"
- Upload CSV file
- Parse and save to `OptionPlayRawData` table
- Validate data before saving

### Step 3: Create Conversion Service
- `OptionPlayRawDataService.convert_to_suggestions()`
- Reads unprocessed rows from `OptionPlayRawData`
- Converts to `SuggestedPosition` format
- Marks rows as processed

### Step 4: Update Fallback Logic
```python
def fetch_high_probability_positions(self, filters):
    # Try API
    if api_configured:
        try: return fetch_from_api()
        except: pass
    
    # Try Scraper
    if scraper_configured:
        try: return fetch_from_scraper()
        except: pass
    
    # Try Database (NEW!)
    try:
        return fetch_from_database()  # Convert OptionPlayRawData to SuggestedPosition
    except: pass
    
    # Last resort: Mock
    return get_mock_positions()
```

### Step 5: Admin Interface
- List view showing uploaded data
- Filter by strategy type, processed status
- Bulk actions: "Convert to Suggestions", "Delete"
- CSV upload button

---

## 📋 Benefits of This Approach

1. **Reliability**: ✅ Staff can manually upload when automation fails
2. **Real Data**: ✅ Uses actual OptionPlay CSV exports (not mock)
3. **No Playwright Issues**: ✅ Bypasses browser automation on Heroku
4. **Audit Trail**: ✅ Tracks who uploaded, when, and what was processed
5. **Flexibility**: ✅ Can mix automated + manual uploads
6. **Testing**: ✅ Easy to test with historical data

---

## 🎯 Next Steps

1. Create `OptionPlayRawData` model
2. Add CSV import management command
3. Create admin interface for uploads
4. Update `PositionFetcherService` with database fallback
5. Test with real CSV files from your repo

---

**Should I proceed with implementing this solution?**

This gives you the best of both worlds:
- ✅ Automated scraping when it works
- ✅ Manual CSV upload when it doesn't
- ✅ Real OptionPlay data (not mock)
- ✅ No dependency on Playwright working on Heroku

