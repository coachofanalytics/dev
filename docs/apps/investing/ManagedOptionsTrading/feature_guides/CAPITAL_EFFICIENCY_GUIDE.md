# Capital Efficiency: Return on Capital (ROC) Filter

## 🎯 The Big Idea

**Don't filter by capital size - filter by capital EFFICIENCY!**

A $700 position returning $4 (57% ROC) is **BETTER** than a $400 position returning $1.50 (38% ROC).

---

## 📊 What is Return on Capital (ROC)?

**Formula:**
```
ROC = (Premium Collected / Capital Required) × 100
```

**Example 1:**
- Premium: $4.00
- Capital (7-point spread): $700
- **ROC = ($4 / $700) × 100 = 57%** ✅

**Example 2:**
- Premium: $2.00
- Capital (6-point spread): $600
- **ROC = ($2 / $600) × 100 = 33%** ❌

**Which is better?** Example 1! Even though it requires more capital ($700 vs $600), you're getting better efficiency (57% vs 33%).

---

## 🤔 Why This Matters

### Old Way (Capital Limit Filter):
```
Filter: Max $600 per position

Position A: $700 capital, $4 premium → REJECTED ❌
Position B: $400 capital, $1.50 premium → ACCEPTED ❌

Result: You took the WORSE position!
```

### New Way (ROC Filter):
```
Filter: Min 40% ROC

Position A: $700 capital, $4 premium → 57% ROC → ACCEPTED ✅
Position B: $400 capital, $1.50 premium → 38% ROC → REJECTED ❌

Result: You took the BETTER position!
```

---

## 💡 Real-World Example

You have $10,000 to deploy across positions.

### Scenario A (Capital Limit $600):
- 10 positions × $600 = $6,000 deployed
- Average ROC: 35%
- **Monthly Return: $2,100 (35% of $6,000)**
- Leftover: $4,000 idle (missed opportunity!)

### Scenario B (ROC Filter 40%+):
- Position 1: $700 @ 50% ROC
- Position 2: $650 @ 48% ROC
- Position 3: $800 @ 55% ROC
- ...
- Total: $9,500 deployed (higher utilization!)
- Average ROC: 48%
- **Monthly Return: $4,560 (48% of $9,500)**

**Result: $2,460 more profit** (116% higher!) just by focusing on efficiency!

---

## 🎯 Filter Recommendations

### Conservative (50%+ ROC)
**Goal:** Highest quality, best efficiency  
**Example:** Only take positions returning 50%+ on capital  
**Typical:** 8-10 positions with excellent returns

### Balanced (40%+ ROC) ⭐ **RECOMMENDED**
**Goal:** Solid efficiency with good diversification  
**Example:** Accept any position with 40%+ ROC  
**Typical:** 12-15 positions with strong returns  
**Sweet Spot:** Best balance of quality and quantity

### Aggressive (35%+ ROC)
**Goal:** Maximum positions deployed  
**Example:** Accept positions with 35%+ ROC  
**Typical:** 15-20 positions, some with lower efficiency  
**Trade-off:** More diversification, slightly lower average ROC

---

## 🔧 How Auto-Suggest Spread Width Works

The system calculates optimal spread widths based on strike price:

| Strike Price | Suggested Width | Capital | Example Premium | Expected ROC |
|--------------|-----------------|---------|-----------------|--------------|
| $0-50 | 5 points | $500 | $2.00 | 40% |
| $50-100 | 5 points | $500 | $2.50 | 50% |
| $100-200 | 7 points | $700 | $3.50 | 50% |
| $200+ | 10 points | $1,000 | $5.00 | 50% |

**Why these widths?**
- Too narrow (3 points): Low capital BUT also low premium
- Too wide (15+ points): High premium BUT also high capital (lower ROC)
- **5-10 points:** Sweet spot for consistent 40-60% ROC

---

## 📈 Expected Results

### Using 40% Min ROC (Balanced):

**Portfolio: $10,000**

```
Position 1: SOUN  - $500 capital, $3.50 premium → 70% ROC ✅
Position 2: IONQ  - $700 capital, $4.00 premium → 57% ROC ✅
Position 3: PLTR  - $700 capital, $3.85 premium → 55% ROC ✅
Position 4: AMD   - $700 capital, $3.50 premium → 50% ROC ✅
...
Position 12: MU   - $600 capital, $2.75 premium → 46% ROC ✅

Total Capital: $9,200
Total Premium: $4,416
Average ROC: 48%
```

**Monthly Return:** ~$4,400 (48% of capital)  
**Annual Return:** ~57% (assuming 70% win rate)

---

## 🎓 Understanding the Math

### Question: "Shouldn't I just pick the HIGHEST ROC positions?"

**Answer:** Not necessarily! Here's why:

**High ROC positions (70%+):**
- Usually smaller capital ($300-500)
- Often lower-priced stocks (more risk)
- Premium might be small ($2-3)

**Moderate ROC positions (40-50%):**
- Larger capital ($600-800)
- Quality underlying stocks
- Good absolute premium ($3-5)

**Best Strategy:** Mix of both!
- 60% in moderate ROC (40-50%) with quality stocks
- 40% in high ROC (60%+) for extra returns

---

## ❌ Common Mistakes

### 1. Chasing Capital Size
```
❌ "I want all positions under $500"
Result: Miss great 60% ROC opportunities on $700 positions
```

**Fix:** Set ROC minimum (40%+), let capital vary

### 2. Ignoring ROC
```
❌ "This $400 position is safe"
But: $400 capital with $1 premium = 25% ROC (poor!)
```

**Fix:** Always check ROC before entering

### 3. Too Aggressive ROC Filter
```
❌ "Only take 70%+ ROC positions"
Result: Only 3-4 positions available (no diversification!)
```

**Fix:** Use 40-50% ROC for balanced portfolio

---

## 🔍 How to Read the Logs

```
✅ Imported:
  1. SOUN: Premium=$3.50, ROC=70%, 5pt spread
     Capital: $500
     Suggested: Sell $17/Buy $12

Interpretation:
- 5-point spread (width) = $500 capital
- $3.50 premium / $500 capital = 70% ROC ✅
- When entering: Sell $17 put, Buy $12 put
```

```
❌ Rejected:
  3. XYZ: Premium=$2, ROC=33%, 6pt spread
     Reason: ROC 33% < 40% minimum

Interpretation:
- 6-point spread = $600 capital
- $2 premium / $600 capital = 33% ROC ❌
- Too inefficient - better opportunities exist
```

---

## 💰 Calculating Your Own ROC

**Step 1:** Determine spread width
- Look at strike price
- Use 5-10 points based on system suggestion

**Step 2:** Calculate capital
```
Capital = Spread Width × 100

Example: 7-point spread = $700 capital
```

**Step 3:** Get premium from CSV
```
Premium = Mid Price from OptionPlay
```

**Step 4:** Calculate ROC
```
ROC = (Premium / Capital) × 100

Example: $4 / $700 × 100 = 57%
```

**Step 5:** Compare to your minimum
```
Is 57% ≥ 40% minimum? YES ✅ → Enter position
Is 33% ≥ 40% minimum? NO ❌ → Skip
```

---

## 🎯 Decision Tree

```
New Position Opportunity
    │
    ├─> Calculate spread width (based on strike)
    │
    ├─> Calculate capital (width × 100)
    │
    ├─> Get premium from CSV
    │
    ├─> Calculate ROC (premium / capital × 100)
    │
    ├─> Is ROC ≥ 40%?
        │
        ├─> YES ✅ → Enter position
        │
        └─> NO ❌ → Look for better opportunity
```

---

## 🚀 Next Steps

1. **Upload your CSV** with Balanced preset (40% ROC minimum)
2. **Review results** - See which positions pass ROC filter
3. **Check suggested spread widths** - System auto-calculates
4. **Enter positions manually** as credit spreads:
   - Sell strike: From CSV
   - Buy strike: Sell strike - Width
5. **Monitor ROC** - Track actual vs expected returns

---

## 📚 Key Takeaways

1. **ROC > Capital Size** - Efficiency matters more than absolute dollars
2. **40% ROC is solid** - Industry-standard minimum for income trading
3. **Auto spread widths** - System suggests 5-10 points based on strike
4. **Don't fear larger capital** - $700 @ 60% ROC beats $400 @ 30% ROC
5. **Diversify** - Mix of high ROC (70%+) and moderate ROC (40-50%)

---

**Remember:** The goal isn't to deploy the LEAST capital. The goal is to deploy capital where it generates the BEST returns!

---

*Last Updated: November 3, 2025*  
*Part of CODA Options Management System*

