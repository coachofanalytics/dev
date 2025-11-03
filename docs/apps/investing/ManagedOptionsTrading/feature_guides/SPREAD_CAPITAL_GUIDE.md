# Spread Trading with $600 Capital Limit

## Capital Efficiency Strategy

### Problem
**Cash-Secured Put** requires: `Strike × 100`  
Example: $150 strike = **$15,000 capital** 😱

### Solution
Use **Credit Spreads** or **Debit Spreads** instead:

---

## Credit Spread (Bull Put Spread)

**Capital Required:** `(Sell Strike - Buy Strike) × 100`

### Example: PLTR Short Put → Credit Spread

**Original (from CSV):**
- Sell $195 put
- Premium: $11.77  
- **Capital: $19,500** ❌ Too much!

**Convert to Credit Spread:**
- Sell $195 put / Buy $189 put (6-point wide)
- Premium collected: ~$3.50 (estimated)
- **Capital: $600** ✅ Perfect!
- Return: $350 / $600 = **58% if spreads expires worthless**

---

## Industry-Standard Spread Widths

### For $600 Max Capital:

| Stock Price | Spread Width | Capital | Example Premium |
|-------------|--------------|---------|-----------------|
| $50-$100 | 5-10 points | $500-$1,000 | $1.50-$3.00 |
| $100-$200 | 5-10 points | $500-$1,000 | $2.00-$4.00 |
| $200-$300 | 5-10 points | $500-$1,000 | $2.50-$5.00 |

**Rule of Thumb:** Keep width at **5-10 points** for most stocks

---

## Converting CSV Short Puts to Spreads

### Step 1: Import CSV with Filters
```
Minimum Premium: $2.00
Minimum IV Rank: 35%
Maximum Capital: $600  ← This filters positions
Maximum DTE: 35 days
```

### Step 2: System Auto-Calculates
For each position, calculate:
```
Capital (Short Put) = Strike × 100
```

If `Capital > $600`: **Filter out** or **suggest spread width**

### Step 3: Manual Conversion
Take the filtered short puts and create spreads:
- **Sell strike:** From CSV
- **Buy strike:** Sell strike - Width (usually 5-10 points)
- **Width:** Calculate to keep capital ≤ $600

---

## Spread Width Selection Guide

### Conservative (Wider Spreads)
- **Width:** 10 points
- **Capital:** $1,000
- **Premium:** Higher (~$4-6)
- **Win Rate:** ~75-80%

### Balanced (Medium Spreads) ⭐ RECOMMENDED
- **Width:** 5-7 points
- **Capital:** $500-700
- **Premium:** Moderate (~$2-4)
- **Win Rate:** ~70-75%

### Aggressive (Tighter Spreads)
- **Width:** 3-5 points
- **Capital:** $300-500
- **Premium:** Lower (~$1-2.50)
- **Win Rate:** ~65-70%

---

## Capital Deployment Example

**Your Setup: $7,200 Portfolio**

### Balanced Preset (12 positions × $600):
```
Position 1: SOUN  - $600 capital, $3.50 premium (58% return)
Position 2: IONQ  - $600 capital, $4.00 premium (67% return)
...
Position 12: WDC  - $600 capital, $2.50 premium (42% return)

Total Capital: $7,200
Total Premium: ~$36-48 (if all spreads)
Monthly Return: 4-6%
Annual Return: 50-70% (if 70% win rate)
```

---

## Risk Management

### Per Position:
- **Max Loss:** Width × 100 - Premium
- Example: $600 capital, $3 premium collected
  - Max Loss: $600 - $300 = $300
  - Risk/Reward: $300 risk / $300 reward = **1:1 ratio**

### Portfolio:
- **12 positions** = diversification
- **70% win rate** = 8 winners, 4 losers expected
- **Net P&L:** (8 × $300) - (4 × $300) = **+$1,200** on $7,200 capital
- **Return:** 16.7% per cycle (4 weeks)

---

## Implementation in CODA

### Current System:
1. ✅ Import OptionPlay CSV (short puts)
2. ✅ Filter by IV Rank, DTE, Premium
3. ⚠️ **NEW:** Filter by capital requirement
4. ⚠️ **FUTURE:** Auto-suggest spread widths

### Suggested Workflow:
1. Upload CSV with "Balanced" preset
2. System filters to positions with strikes that allow $600 spreads
3. Review filtered positions (12 selected)
4. Manually enter as credit spreads in system
5. Set width to keep capital ≤ $600

---

## Tastytrade Methodology

### Spread Trading Rules:
1. **Width:** Keep consistent (5-10 points for most stocks)
2. **Premium:** Collect 1/3 of width as minimum
   - 5-point spread: Collect $1.67+ (33%)
   - 10-point spread: Collect $3.33+ (33%)
3. **Management:** Close at 50% max profit
4. **Loss Management:** Don't let losers exceed 2× max profit

### Expected Outcomes:
- **Win Rate:** 65-75%
- **Profit Factor:** 1.5-2.0 (winners 1.5-2x bigger than losers)
- **Annual Return:** 30-60% (highly achievable)

---

## Why $600 Max?

### Small Account Benefits:
- **Diversification:** 12 positions on $7,200 capital
- **Risk Management:** Only 8.3% of capital per position
- **Flexibility:** Can add positions or adjust easily
- **Psychology:** Small losses easier to handle

### Capital Scaling:
- $7,200 account → 12 positions × $600
- $15,000 account → 12 positions × $1,250 (or 25 × $600)
- $30,000 account → 12 positions × $2,500 (or 50 × $600)

**Keep position size consistent, add MORE positions as capital grows**

---

## Next Steps

### For Your $7,200 Portfolio:

1. **Upload CSV** with Balanced preset (done!)
2. **Filter selects** ~12 positions
3. **Convert to spreads:**
   - For each position, calculate width needed
   - Enter as "Bull Put Spread" in system
   - Set strikes to keep capital ≤ $600
4. **Monitor & Adjust**:
   - Close winners at 50% profit
   - Roll or close losers at 21 DTE
   - Replace with new positions weekly

---

## Further Reading

- Tastytrade: "Spread Width Selection"
- Option Alpha: "Capital Efficiency for Small Accounts"
- CBOE: "Managing Spread Risk"

---

*Last Updated: November 3, 2025*  
*Part of CODA Options Management System*

