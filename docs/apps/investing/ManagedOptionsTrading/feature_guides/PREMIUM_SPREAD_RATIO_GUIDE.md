# Premium-to-Spread Ratio: The 1/3 Rule

## 🎯 The Industry Standard

**Tastytrade's 1/3 Rule:**  
Collect **at least 1/3 of the spread width** as premium

---

## 📊 Why 1/3?

This ratio ensures you're getting paid enough relative to the risk you're taking:

- **Spread Width = Maximum Risk**
- **Premium = Maximum Reward**
- **1/3 ratio = Minimum 33% ROC before commissions**

---

## 💰 Calculation Examples

### Example 1: 5-Point Spread
```
Spread Width: $5.00 ($500 capital)
Minimum Premium: $5.00 ÷ 3 = $1.67
ROC: $1.67 / $500 = 33%
```

✅ **Accept:** Premium of $2.00 or higher  
❌ **Reject:** Premium of $1.50 (too low)

---

### Example 2: 7-Point Spread
```
Spread Width: $7.00 ($700 capital)
Minimum Premium: $7.00 ÷ 3 = $2.33
ROC: $2.33 / $700 = 33%
```

✅ **Accept:** Premium of $3.00 or higher  
❌ **Reject:** Premium of $2.00 (too low)

---

### Example 3: 10-Point Spread
```
Spread Width: $10.00 ($1,000 capital)
Minimum Premium: $10.00 ÷ 3 = $3.33
ROC: $3.33 / $1,000 = 33%
```

✅ **Accept:** Premium of $4.00 or higher  
❌ **Reject:** Premium of $3.00 (too low)

---

## 🎓 Why This Works

### Risk/Reward Math:
- **Max Loss:** Spread Width - Premium Collected
- **Max Profit:** Premium Collected
- **1/3 Rule:** Ensures manageable risk/reward

**Example:**
```
5-point spread, $2 premium collected (40% ROC)

Max Loss: $500 - $200 = $300
Max Profit: $200
Risk/Reward: $300 risk / $200 reward = 1.5:1 ratio

To breakeven: Need 60% win rate
(0.60 × $200) - (0.40 × $300) = $120 - $120 = $0

With 70% win rate (typical):
(0.70 × $200) - (0.30 × $300) = $140 - $90 = +$50 profit
```

---

## 📈 ROC vs 1/3 Rule

| Spread Width | 1/3 Premium | Min ROC | Balanced Premium | Good ROC |
|--------------|-------------|---------|------------------|----------|
| 3 points ($300) | $1.00 | 33% | $1.20 | 40% |
| 5 points ($500) | $1.67 | 33% | $2.00 | 40% |
| 7 points ($700) | $2.33 | 33% | $2.80 | 40% |
| 10 points ($1000) | $3.33 | 33% | $4.00 | 40% |

**Our System:**
- **Minimum ROC: 40%** (better than 1/3 rule's 33%)
- **This automatically enforces the 1/3 rule + 7% cushion**
- Result: Higher quality trades!

---

## ✅ How CODA Implements This

### Automatic Enforcement:
1. **Spread Width Auto-Calculated** based on strike price
2. **ROC Filter** ensures >= 40% (exceeds 1/3 rule)
3. **Result:** Only accept trades meeting industry standards

### Example from Your CSV:
```
Position: PLTR
Strike: $195
Spread Width: 7 points ($700 capital)
Premium: $4.00

1/3 Rule Check:
$7.00 ÷ 3 = $2.33 minimum
$4.00 > $2.33 ✅ PASSES

ROC Check:
$4.00 / $700 = 57%
57% > 40% minimum ✅ PASSES

Result: Excellent trade!
```

---

## 🚫 Common Mistakes

### Mistake 1: Ignoring the Ratio
```
❌ Bad: 10-point spread, $2 premium
   1/3 rule: Need $3.33, got $2.00
   ROC: 20% (too low!)
   
✅ Good: 10-point spread, $4 premium
   1/3 rule: Need $3.33, got $4.00
   ROC: 40% (solid!)
```

### Mistake 2: Too Tight Spreads
```
❌ Bad: 3-point spread on $200 stock
   Capital: $300
   Premium: ~$0.80 (27% ROC)
   Below 1/3 rule!
   
✅ Good: 5-point spread on $200 stock
   Capital: $500
   Premium: ~$2.00 (40% ROC)
   Meets standards!
```

### Mistake 3: Too Wide Spreads
```
❌ Bad: 20-point spread, $5 premium
   Capital: $2,000
   Premium: $5 (only 25% ROC!)
   Below 1/3 rule!
   
✅ Good: 10-point spread, $4 premium
   Capital: $1,000
   Premium: $4 (40% ROC)
   Better efficiency!
```

---

## 🎯 Decision Tree

```
New Spread Trade Opportunity
    │
    ├─> Calculate spread width (5-10 points typical)
    │
    ├─> Check premium offered
    │
    ├─> Calculate: Premium / (Width × 100)
    │
    ├─> Is ROC ≥ 40%? (Exceeds 1/3 rule)
        │
        ├─> YES ✅ → Enter trade
        │
        └─> NO ❌ → Reject
            │
            ├─> Premium too low?
            │   └─> Ask for better fill
            │
            ├─> Spread too wide?
            │   └─> Try narrower spread (5-7 points)
            │
            └─> Volatility too low?
                └─> Wait for IV expansion
```

---

## 📚 Tastytrade Research

**Why 1/3 is the minimum:**

1. **Win Rate Math:**
   - With 33% ROC, need 60% win rate to breakeven
   - Typical win rates: 65-75% for credit spreads
   - 5-15% edge over breakeven = profitable long-term

2. **Commission Impact:**
   - $1 round-trip commission on 5-point spread
   - $1.67 premium - $1 commission = $0.67 net
   - Still 13% ROC after commissions

3. **Slippage Buffer:**
   - Market moves between quote and fill
   - 1/3 rule provides cushion
   - Ensures profitability even with slight slippage

---

## 💡 Key Takeaways

1. **1/3 Rule = 33% minimum ROC** before commissions
2. **CODA uses 40% ROC minimum** (exceeds industry standard)
3. **Spread width matters** - optimal is 5-10 points
4. **Premium must scale with risk** - don't accept low premiums on wide spreads
5. **ROC filter automatically enforces this** - no manual checking needed!

---

## 🔢 Quick Reference Table

**"Should I take this trade?"**

| Spread Width | Minimum Premium (1/3) | CODA Minimum (40%) | Great Premium (50%+) |
|--------------|----------------------|-------------------|---------------------|
| 3 points | $1.00 | $1.20 | $1.50+ |
| 5 points | $1.67 | $2.00 | $2.50+ |
| 7 points | $2.33 | $2.80 | $3.50+ |
| 10 points | $3.33 | $4.00 | $5.00+ |

**If premium offered is:**
- ✅ **≥ CODA Minimum (40% ROC)** → Excellent trade
- ⚠️ **Between 1/3 and 40%** → Acceptable but not ideal
- ❌ **< 1/3 rule** → Reject (too risky)

---

**Remember:** The 1/3 rule is the MINIMUM. CODA's 40% ROC filter ensures you're getting trades that exceed this standard!

---

*Last Updated: November 3, 2025*  
*Part of CODA Options Management System*  
*Source: Tastytrade Research*

