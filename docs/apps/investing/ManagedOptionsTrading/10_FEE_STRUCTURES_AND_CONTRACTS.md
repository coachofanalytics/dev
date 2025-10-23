# Managed Options Trading - Fee Structures & Contracts
**Purpose:** Define business models, compare to industry standards, automate contracts  
**Date:** October 22, 2025  
**Status:** 💰 Fee Structure Analysis & Contract Design

---

## 💰 Proposed Fee Structures Analysis

### **Your Proposals:**

#### **Model A: CODA Bears 100% Risk**
```
Structure:
- CODA takes 100% of risk
- Client gets 30% of profits
- CODA gets 70% of profits

Example ($30K account, $6K profit):
- Client receives: $6,000 × 30% = $1,800
- CODA receives: $6,000 × 70% = $4,200
```

#### **Model B: Client Bears 100% Risk**
```
Structure:
- Client takes 100% of risk
- Client gets 100% of profits
- CODA charges $50 per position setup fee

Example ($30K account, 20 positions/month):
- Client profit: $6,000
- CODA receives: 20 × $50 = $1,000/month = $12,000/year
- Client keeps: $6,000 - $1,000 = $5,000
```

---

## 📊 **Industry Standards Comparison**

### **Hedge Funds (Industry Standard)**

| Fee Type | Industry Standard | Description |
|----------|------------------|-------------|
| **Management Fee** | 1-2% annual AUM | Charged regardless of performance |
| **Performance Fee** | 15-25% of profits | Charged only on gains |
| **High-Water Mark** | Standard | Only charge performance fee on NEW highs |
| **Hurdle Rate** | 5-8% | Client gets first X% free, fees above that |

**Classic "2 and 20" Model:**
- 2% annual management fee
- 20% performance fee above hurdle rate

---

### **Robo-Advisors (Modern Alternative)**

| Provider | Management Fee | Performance Fee | Min Investment |
|----------|---------------|----------------|----------------|
| **Betterment** | 0.25% | 0% | $0 |
| **Wealthfront** | 0.25% | 0% | $500 |
| **M1 Finance** | 0% | 0% (subscription model) | $100 |

---

### **Active Trading Services**

| Provider | Fee Structure | Min Investment |
|----------|--------------|----------------|
| **Interactive Brokers** | $0.65/contract + $10/month | $0 |
| **Tastytrade** | $1/contract (capped $10/trade) | $0 |
| **Manual Advisors** | $50-200/trade + 1% AUM | $25,000+ |

---

## 🎯 **Analysis of Your Proposals**

### **Model A: CODA 100% Risk, 70/30 Split**

**Pros:**
- ✅ Very attractive to clients (no risk!)
- ✅ Aligned incentives (CODA profits when client profits)
- ✅ Can attract many clients quickly

**Cons:**
- ❌ **EXTREMELY RISKY for CODA!**
- ❌ If account loses money, CODA loses 100%
- ❌ Client has no skin in the game (moral hazard)
- ❌ One bad trade can wipe out CODA's capital
- ❌ Not scalable (CODA needs capital for each client)
- ❌ Violates fiduciary principles

**Industry Comparison:**
- ⚠️ **NOT STANDARD** - No legitimate hedge fund does this
- ⚠️ High-risk prop trading firms might, but with strict limits
- ⚠️ Could create regulatory issues (looks like gambling)

**Recommendation:** ❌ **DO NOT OFFER** - Too risky for CODA

**If You Must Offer It:**
```python
# Extreme risk controls needed:
- Start with max $5,000 CODA capital per client
- Stop trading if CODA down 10% on account
- Require client to share losses 50/50 after 15% drawdown
- Cap CODA's exposure at $50,000 total across all clients
- Insurance or reserve fund required
```

---

### **Model B: Client 100% Risk, $50 Per Position**

**Pros:**
- ✅ Zero risk to CODA (we just charge fees)
- ✅ Simple, transparent pricing
- ✅ Predictable revenue for CODA
- ✅ Client keeps all profits

**Cons:**
- ❌ **Too cheap for the value provided!**
- ❌ $50/position = only $1,000-$1,500/month revenue
- ❌ Doesn't align with client's success
- ❌ Similar to discount brokers (low margin business)
- ❌ Clients may question value if paying fees while losing

**Industry Comparison:**
- ✅ Similar to trading platforms ($0.65-$1/contract)
- ⚠️ But those are self-directed, not managed!
- ⚠️ Managed services typically 10-20x more expensive

**Recommendation:** ⚠️ **TOO CHEAP** - Consider hybrid approach

**If You Offer It:**
```python
# Recommended improvements:
- Charge $100-$150 per position (more realistic for managed service)
- Add minimum monthly fee ($500/month regardless of trades)
- OR combine with small performance fee (10% of profits)
```

---

## 💡 **Recommended Fee Structures (Industry-Aligned)**

### **Option 1: "Classic 1 and 20" (Recommended for Most Clients)**

```yaml
Structure:
  Management Fee: 1% annual (charged quarterly)
  Performance Fee: 20% of profits above 8% hurdle
  High-Water Mark: Yes
  Risk Bearer: Client (100%)

For $30K account with 20% annual return ($6,000 profit):
  Management Fee: $30,000 × 1% = $300/year ($75/quarter)
  Hurdle: $30,000 × 8% = $2,400 (client gets this free)
  Excess Profit: $6,000 - $2,400 = $3,600
  Performance Fee: $3,600 × 20% = $720
  
  Total Fees to CODA: $300 + $720 = $1,020/year
  Client Net Profit: $6,000 - $1,020 = $4,980 (16.6% net return)

Why This Works:
✅ Client keeps first 8% (beats market average)
✅ CODA only profits when client exceeds hurdle
✅ Aligned incentives
✅ Industry standard (familiar to sophisticated clients)
✅ Predictable revenue for CODA
✅ Fair to both parties

Monthly CODA Revenue (predictable):
  - Management: $25/month
  - Performance: Varies (avg $60-100/month)
  - Total: $85-125/month per client
```

---

### **Option 2: "Performance-First" (Aggressive Growth)**

```yaml
Structure:
  Management Fee: 0% (waived to attract clients)
  Performance Fee: 30% of ALL profits (no hurdle)
  High-Water Mark: Yes
  Risk Bearer: Client (100%)

For $30K account with 20% return ($6,000 profit):
  Management Fee: $0
  Performance Fee: $6,000 × 30% = $1,800
  
  Total Fees to CODA: $1,800/year
  Client Net Profit: $6,000 - $1,800 = $4,200 (14% net return)

Why This Works:
✅ Very attractive to clients (no fee if no profit!)
✅ Higher performance fee justified (no management fee)
✅ Simple, transparent
✅ Aligned incentives
✅ Good for marketing ("We only make money if you make money")

Monthly CODA Revenue (variable):
  - Performance only: Varies greatly
  - Good month: $300-500
  - Bad month: $0
```

---

### **Option 3: "Tiered Performance" (Sophisticated)**

```yaml
Structure:
  Management Fee: 1% annual
  Performance Fee: TIERED
    - 0-10% return: 0% fee (client keeps all)
    - 10-20% return: 15% fee
    - 20-30% return: 20% fee
    - 30%+ return: 25% fee
  Risk Bearer: Client (100%)

For $30K account with 25% return ($7,500 profit):
  Management Fee: $300/year
  
  Performance Fee Calculation:
  - First $3,000 (10%): $0 (client keeps all)
  - Next $3,000 (10-20%): $3,000 × 15% = $450
  - Last $1,500 (20-25%): $1,500 × 20% = $300
  - Total Performance Fee: $750
  
  Total Fees to CODA: $300 + $750 = $1,050
  Client Net Profit: $7,500 - $1,050 = $6,450 (21.5% net)

Why This Works:
✅ Client keeps ALL gains up to 10% (very fair)
✅ Incentivizes CODA to maximize returns
✅ Progressive fee structure
✅ Sophisticated clients appreciate complexity
```

---

### **Option 4: "Hybrid Subscription Plus Performance"**

```yaml
Structure:
  Monthly Subscription: $200/month ($2,400/year)
  Performance Fee: 15% of profits (no hurdle)
  Risk Bearer: Client (100%)
  Minimum Commitment: 6 months

For $30K account with 20% return ($6,000 profit):
  Subscription: $2,400/year
  Performance Fee: $6,000 × 15% = $900
  
  Total Fees to CODA: $3,300/year
  Client Net Profit: $6,000 - $3,300 = $2,700 (9% net)

Why This Works:
✅ Predictable revenue for CODA ($200/month guaranteed)
✅ Client committed (subscription = serious intent)
✅ Lower performance fee (already paying subscription)
✅ Good for CODA's cash flow planning

Monthly CODA Revenue:
  - Guaranteed: $200/month minimum
  - Performance: Variable (avg $75/month)
  - Total: $275/month per client
```

---

### **Option 5: "Shared Risk, Shared Reward" (Modified Model A)**

```yaml
Structure:
  CODA Risk: 30% of losses
  Client Risk: 70% of losses
  Profit Split: 50/50
  Management Fee: 0%

For $30K account with $6,000 profit:
  Client gets: $3,000
  CODA gets: $3,000

For $30K account with $3,000 loss:
  Client loses: $3,000 × 70% = $2,100
  CODA loses: $3,000 × 30% = $900

Why This Could Work:
✅ CODA has skin in the game (builds trust)
✅ But risk is limited (30% not 100%)
✅ Client shares risk (moral hazard reduced)
✅ Fair profit split

Risk Control for CODA:
- Require $10,000 reserve fund (covers 30% of losses)
- Max 10 clients at a time
- Stop trading if CODA reserve depleted
- Very conservative strategies only
```

---

## 🎯 **CODA's Recommended Fee Structures (Final)**

### **Recommendation #1: "Standard Professional" (Start Here)**

```yaml
Fee Structure: "1.5 and 20 with 8% Hurdle"
Management Fee: 1.5% annual ($450/year for $30K)
Performance Fee: 20% of profits above 8% hurdle
High-Water Mark: Yes
Risk: Client bears 100%
Minimum Account: $25,000
Minimum Commitment: 6 months

Projected CODA Revenue (per $30K client):
  Conservative (10% return): $300 mgmt + $120 perf = $420/year
  Target (20% return): $300 mgmt + $720 perf = $1,020/year
  Optimistic (30% return): $300 mgmt + $1,320 perf = $1,620/year

Client Net Return:
  Conservative: 10% - 1.4% = 8.6% net
  Target: 20% - 3.4% = 16.6% net
  Optimistic: 30% - 5.4% = 24.6% net

Why Recommended:
✅ Industry standard (clients understand it)
✅ Fair to both parties
✅ Predictable revenue
✅ Zero risk to CODA
✅ Scales easily
```

---

### **Recommendation #2: "Growth Tier" (For Smaller Accounts)**

```yaml
Fee Structure: "Performance-Only 25%"
Management Fee: 0% (waived)
Performance Fee: 25% of ALL profits (no hurdle)
High-Water Mark: Yes
Risk: Client bears 100%
Minimum Account: $10,000
Minimum Commitment: 3 months

For $10K account with 20% return ($2,000 profit):
  Performance Fee: $2,000 × 25% = $500
  Client Net: $2,000 - $500 = $1,500 (15% net)

Why Offer This:
✅ Attracts smaller accounts ($10-25K)
✅ No upfront fees (client-friendly)
✅ Simple, transparent
✅ Only make money if client makes money
✅ Good for marketing
```

---

### **Recommendation #3: "Premium Tier" (For Larger Accounts)**

```yaml
Fee Structure: "1 and 15 with Monthly Minimum"
Management Fee: 1% annual
Performance Fee: 15% of profits (no hurdle)
Monthly Minimum: $500/month
Risk: Client bears 100%
Minimum Account: $100,000+
Includes: Priority support, custom strategies, weekly calls

For $100K account with 20% return ($20,000 profit):
  Management Fee: $1,000/year
  Performance Fee: $20,000 × 15% = $3,000
  Monthly Minimum: $500 × 12 = $6,000
  
  Total Fees: MAX($1,000 + $3,000, $6,000) = $6,000
  Client Net: $20,000 - $6,000 = $14,000 (14% net)

Why Offer This:
✅ Higher revenue per client
✅ Attracts serious, high-net-worth clients
✅ Guaranteed minimum revenue
✅ Premium service justifies premium fees
```

---

### **Recommendation #4: "Profit Share Light" (Modified Model A)**

```yaml
Fee Structure: "CODA Co-Invests 20%, Shares 50/50"
CODA Investment: 20% of account ($6K for $30K account)
Client Investment: 80% of account ($24K for $30K account)
Profit Split: 50/50
Loss Split: 50/50
Management Fee: 0%

For combined $30K account ($24K client + $6K CODA) with 20% profit ($6,000):
  Client gets: $6,000 × 50% = $3,000 (12.5% return on their $24K)
  CODA gets: $6,000 × 50% = $3,000 (50% return on their $6K!)

For $3,000 loss:
  Client loses: $1,500 (6.25% of their $24K)
  CODA loses: $1,500 (25% of their $6K)

Why This Could Work:
✅ CODA has skin in the game (builds massive trust!)
✅ But risk is limited (only $6K at risk)
✅ High return on CODA's capital (50% annual potential!)
✅ Client loves shared risk model

Risk for CODA:
⚠️ Need $60K capital for 10 clients
⚠️ Could lose $60K if all fail
⚠️ Capital intensive model

Recommendation:
✅ Offer to 2-3 VIP clients only
✅ Require CODA reserve fund
✅ Use most conservative strategies
```

---

## 💡 **Additional Attractive Proposals**

### **Option 5: "Consultative Session Model" (Your Existing Offering)** ⭐ HYBRID

```yaml
Structure:
  Session Fee: $50 per session
  Session Frequency: 2 sessions per week (8 sessions/month)
  Monthly Platform Fee: $20/month
  Performance Fee: 0% (optional: can add 10% for alignment)
  Risk: Client 100%
  
Monthly Revenue Calculation:
  Session Fees: 8 sessions × $50 = $400/month
  Platform Fee: $20/month
  Total Monthly: $420/month
  Total Annual: $5,040/year per client

For $30K account with 20% return ($6,000 profit):
  CODA Fees: $5,040/year (from sessions + platform)
  Client Profit: $6,000
  Client Net: $6,000 - $5,040 = $960 (3.2% net after fees)
  
  BUT client also gets:
  ✅ 8 expert sessions/month (direct access to you!)
  ✅ Education and learning
  ✅ Hands-on involvement
  ✅ Understanding strategies

Value Proposition:
  This is EDUCATION + MANAGED SERVICE hybrid
  Client pays for your time/expertise (sessions)
  Plus small platform fee
  Client keeps all profits (incentivized to learn)

Why This Works:
✅ Predictable revenue for CODA ($420/month guaranteed)
✅ Client feels in control (they're involved via sessions)
✅ Educational component (teaches client to fish)
✅ Not pure performance-based (you get paid for time)
✅ Can scale if you record sessions (group coaching)
✅ Builds strong client relationships

Revenue at Scale:
  1 client: $420/month = $5,040/year
  5 clients: $2,100/month = $25,200/year
  10 clients: $4,200/month = $50,400/year
  
Time Investment:
  Per client: 8 hours/month (2 sessions × 30 min × 8)
  5 clients: 40 hours/month
  10 clients: 80 hours/month (2 hours/day)
```

**Recommended Enhancement:**
```yaml
Add Optional Performance Bonus:
  Base: $50/session + $20/month = $420/month
  PLUS: 10% of profits as success bonus
  
For $30K with $6K profit:
  Session fees: $5,040/year
  Performance bonus: $600/year
  Total CODA: $5,640/year
  Client net: $5,400 (18% net)
  
Why Add This:
✅ Aligns incentives (you want them to profit)
✅ Bonus for excellent performance
✅ Still primarily time-based (predictable)
✅ Extra upside for CODA
```

---

### **Option 6: "Setup Fee Plus Performance"**

```yaml
One-Time Setup Fee: $2,500 (covers analysis, account setup, strategy design)
Ongoing Management: 0%
Performance Fee: 20% of profits
Minimum Account: $25,000
Minimum Commitment: 12 months

For $30K account:
  Year 1: $2,500 (setup) + $1,200 (perf on $6K profit) = $3,700
  Year 2+: $0 (mgmt) + $1,200 (perf) = $1,200/year

Why Attractive:
✅ High upfront revenue ($2,500)
✅ Covers CODA's time investment
✅ No ongoing fees if account loses money
✅ Client sees value in setup work
✅ Performance fee reasonable (20%)
```

---

### **Option 6: "Success Fee Only"**

```yaml
Management Fee: 0%
Performance Fee: 30% of profits IF account beats S&P 500
Otherwise: 15% of profits
High-Water Mark: Yes
Risk: Client 100%

For $30K with 20% return (S&P did 12%):
  Beat benchmark by 8%
  Performance Fee: $6,000 × 30% = $1,800
  Client Net: $4,200 (14% net, still beats S&P!)

For $30K with 15% return (S&P did 18%):
  Didn't beat benchmark
  Performance Fee: $4,500 × 15% = $675
  Client Net: $3,825 (12.75% net)

Why Attractive:
✅ Incentivizes outperformance
✅ Fair if we don't beat market
✅ Client-friendly
✅ Differentiated from robo-advisors
```

---

## 📊 **Comprehensive Fee Structure Comparison**

| Model | Mgmt Fee | Perf Fee | Hurdle | Min Acct | CODA Risk | Client Risk | CODA Revenue ($30K, 20% return) | Client Net Return |
|-------|----------|----------|--------|----------|-----------|-------------|--------------------------------|-------------------|
| **Model A (Your Proposal)** | 0% | 70% of profit | None | $30K | 100%! | 0% | $4,200 | 6% (very low!) |
| **Model B (Your Proposal)** | 0% | $50/position | N/A | Any | 0% | 100% | $1,000 | 16.7% (good!) |
| **Consultative (Your Model)** ⭐ | $50/session | 0% | N/A | $10K | 0% | 100% | $5,040 | 3.2% ✅ BUT gets coaching! |
| **Consultative Enhanced** ⭐ | $50/session | 10% bonus | None | $10K | 0% | 100% | $5,640 | 10.7% ✅ Better! |
| **Industry Standard (2/20)** | 2% | 20% | None | $100K | 0% | 100% | $1,800 | 14% |
| **Recommended #1 (1.5/20)** | 1.5% | 20% | 8% | $25K | 0% | 100% | $1,170 | 16.1% ✅ Best! |
| **Recommended #2 (0/25)** | 0% | 25% | None | $10K | 0% | 100% | $1,500 | 15% ✅ Good! |
| **Recommended #3 (Premium)** | 1% | 15% | Min $500/mo | $100K | 0% | 100% | $6,000 | 14% ✅ Great! |
| **Recommended #4 (Co-Invest)** | 0% | 50/50 split | None | $24K client | 50% | 50% | $3,000 | 12.5% ⚠️ Risky! |

---

## 🎯 **CODA's Complete Fee Menu (4 Tiers + Consultative)**

### **TIER 0: "Consultative Coaching" (Your Existing Model)** ⭐ UNIQUE

```yaml
Structure: SESSION-BASED (Time + Platform Fee)
  Session Fee: $50 per session
  Frequency: 2 sessions/week (8 sessions/month)
  Platform Fee: $20/month
  Performance Bonus: 10% of profits (recommended addition)
  Minimum: $10,000
  Commitment: Month-to-month

Revenue Breakdown (per client):
  Sessions: 8 × $50 = $400/month = $4,800/year
  Platform: $20/month = $240/year
  Base Total: $5,040/year GUARANTEED
  
  Performance Bonus (if $6K profit):
    $6,000 × 10% = $600/year
  
  Total CODA Revenue: $5,640/year
  Client Net (after $5,640 fees): $360 (1.2% net)
  
  BUT Client Gets:
  ✅ 8 personal sessions/month with expert
  ✅ Hands-on education
  ✅ Strategy discussions
  ✅ Learn to trade themselves
  ✅ Ongoing mentorship

Perfect for:
  ✅ Clients who want to LEARN options trading
  ✅ Hands-on, involved investors
  ✅ Those who value education over pure returns
  ✅ Building long-term trading skills

CODA Benefits:
  ✅ HIGHEST revenue per client ($5,040+/year)
  ✅ Guaranteed income (not performance-based)
  ✅ Strong client relationships
  ✅ Can scale via group sessions (1-on-many)
  ✅ Builds community of educated traders

Scalability:
  Individual sessions: Max 5-10 clients (time-intensive)
  Group sessions: Can handle 20-50 clients
    - $50/person × 10 people = $500/session
    - 2 group sessions/week = $4,000/month!
    - Plus $20 × 10 = $200 platform fees
    - Total: $4,200/month = $50,400/year!

Client Appeal:
  "Learn professional options trading with expert guidance
   for just $420/month. Keep 90% of your profits!"
```

---

### **Tier 1: "Starter" (For $10K-$25K Accounts)**
```yaml
Structure: PERFORMANCE-ONLY
  Management Fee: 0%
  Performance Fee: 25% of all profits
  Minimum: $10,000
  Commitment: 3 months

For $30K with 20% return ($6K profit):
  CODA Revenue: $1,500/year
  Client Net: $4,500 (15% net)

Perfect for: First-time clients, smaller accounts
Client Appeal: No fee if no profit!
```

---

### **Tier 2: "Professional" (For $25K-$100K Accounts)** ⭐ MAIN OFFERING
```yaml
Structure: INDUSTRY STANDARD
  Management Fee: 1.5% annual
  Performance Fee: 20% of profits above 8% hurdle
  High-Water Mark: Yes
  Minimum: $25,000
  Commitment: 6 months

For $30K with 20% return ($6K profit):
  Management: $450/year
  Hurdle: $2,400 (client gets free)
  Performance: ($6K - $2.4K) × 20% = $720
  CODA Revenue: $1,170/year
  Client Net: $4,830 (16.1% net)

Perfect for: Serious investors, passive management
Client Appeal: Only pay performance fee if beating 8%
```

---

### **Tier 3: "Premium" (For $100K+ Accounts)**
```yaml
Structure: PREMIUM SERVICE
  Management Fee: 1% annual
  Performance Fee: 15% of profits
  Monthly Minimum: $500/month
  Minimum: $100,000
  Commitment: 12 months
  Includes: Weekly calls, custom strategies, priority

For $100K with 20% return ($20K profit):
  CODA Revenue: $6,000-$10,000/year
  Client Net: $14,000 (14% net)

Perfect for: High-net-worth, hands-off clients
Client Appeal: Premium service, dedicated attention
```

---

### **Tier 4: "Co-Investment" (Limited Offering)**
```yaml
Structure: SHARED RISK/REWARD
  CODA Invests: 20% of account
  Profit Split: 50/50
  Loss Split: 50/50
  Management Fee: 0%
  Minimum: $24,000 client contribution
  Commitment: 12 months
  Availability: 2-3 VIP clients only

For $30K total ($24K client + $6K CODA):
  With 20% return ($6K profit):
    CODA Gets: $3,000 (50% return on $6K invested!)
    Client Gets: $3,000 (12.5% return on $24K)

Perfect for: VIP clients, builds extreme trust
CODA Risk: Limited ($6K per client, max $60K total)
```

---

## 🤝 **Contract System Design**

### **Leveraging Existing Contract Infrastructure**

```python
# Existing: coda/management/models.py
class BaseContract(models.Model):
    """
    EXISTING contract model - REUSE THIS!
    """
    CONTRACT_TYPES = [
        ('Student', 'Student Contract'),
        ('JobSupport', 'Job Support Contract'),
        ('Loan', 'Loan Contract'),
        ('Investment', 'Investment Contract'),  # ← USE THIS!
        ('General', 'General Contract'),
    ]
    
    contract_type = models.CharField(max_length=20, choices=CONTRACT_TYPES)
    client = models.ForeignKey(User, ...)
    contract_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, default='Pending')
    terms_and_conditions = models.TextField(blank=True)
    additional_info = models.JSONField(default=dict, blank=True)
    related_object_id = models.PositiveIntegerField(...)
    related_content_type = models.ForeignKey(ContentType, ...)
```

### **Extension: ManagedTradingContract**

```python
# File: coda/investing/models/managed_trading.py

class ManagedTradingContract(models.Model):
    """
    Specific contract for managed trading agreements
    Links to BaseContract via related_object
    """
    
    # Link to base contract
    base_contract = models.OneToOneField(
        'management.BaseContract',
        on_delete=models.CASCADE,
        related_name='managed_trading_contract'
    )
    
    # Link to managed account
    managed_account = models.OneToOneField(
        ManagedTradingAccount,
        on_delete=models.CASCADE,
        related_name='contract'
    )
    
    # Fee Structure (selected tier)
    fee_tier = models.CharField(
        max_length=20,
        choices=[
            ('starter', 'Starter (0% mgmt, 25% perf)'),
            ('professional', 'Professional (1.5% mgmt, 20% perf + hurdle)'),
            ('premium', 'Premium (1% mgmt, 15% perf, min $500/mo)'),
            ('custom', 'Custom Fee Structure')
        ],
        default='professional'
    )
    
    # Detailed Fee Terms (stored even if using tier)
    management_fee_annual = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Annual management fee percentage"
    )
    performance_fee_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Performance fee percentage"
    )
    performance_hurdle_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Minimum return before performance fees apply"
    )
    has_high_water_mark = models.BooleanField(
        default=True,
        help_text="Only charge performance fee on new account highs"
    )
    
    # Risk Allocation
    coda_risk_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Percentage of losses CODA bears"
    )
    client_risk_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('100.00'),
        help_text="Percentage of losses client bears"
    )
    
    # Terms
    minimum_commitment_months = models.IntegerField(
        default=6,
        help_text="Minimum months client must keep account active"
    )
    early_termination_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Fee if client terminates early"
    )
    
    # Trading Parameters (from contract)
    allowed_strategies = models.JSONField(
        default=list,
        help_text="List of approved strategies for this client"
    )
    # Example: ['short_put', 'covered_call', 'credit_spread']
    
    max_position_size_override = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Client-specific position size limit"
    )
    
    # Contract Acceptance
    client_signature = models.TextField(
        blank=True,
        null=True,
        help_text="Digital signature or acceptance token"
    )
    client_ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address when contract accepted"
    )
    contract_signed_date = models.DateTimeField(
        null=True,
        blank=True
    )
    contract_pdf = models.FileField(
        upload_to='contracts/managed_trading/',
        null=True,
        blank=True,
        help_text="Generated PDF contract"
    )
    
    class Meta:
        verbose_name = "Managed Trading Contract"
        verbose_name_plural = "Managed Trading Contracts"
    
    def __str__(self):
        return f"Contract for {self.managed_account.account_number}"
```

---

## 📄 **Contract Template Design**

### **Template: `managed_trading_contract.html`**

```django
{% extends "main/base_templates/email_base.html" %}
{% load static %}

{% block content %}
<div class="container-fluid" style="max-width: 800px; margin: 0 auto;">
    
    <!-- Header -->
    <div class="text-center mb-4">
        <img src="{% static 'images/coda_logo.png' %}" alt="CODA Logo" style="height: 60px;">
        <h2 class="mt-3">MANAGED OPTIONS TRADING AGREEMENT</h2>
        <p class="text-muted">Account Number: {{ contract.managed_account.account_number }}</p>
    </div>
    
    <hr>
    
    <!-- Parties -->
    <div class="mb-4">
        <h4>PARTIES TO THIS AGREEMENT</h4>
        <p><strong>SERVICE PROVIDER:</strong><br>
        CODA-CROWN DATA ANALYSIS AND CONSULTANCY LLC<br>
        Registration Number: [XXX]<br>
        Address: [Address]</p>
        
        <p><strong>CLIENT:</strong><br>
        {{ contract.managed_account.client.get_full_name }}<br>
        Email: {{ contract.managed_account.client.email }}<br>
        Account Number: {{ contract.managed_account.account_number }}</p>
        
        <p><strong>EFFECTIVE DATE:</strong> {{ contract.base_contract.contract_date|date:"F d, Y" }}</p>
    </div>
    
    <hr>
    
    <!-- Account Details -->
    <div class="mb-4">
        <h4>ACCOUNT DETAILS</h4>
        <table class="table table-bordered">
            <tr>
                <td><strong>Initial Capital:</strong></td>
                <td>${{ contract.managed_account.initial_capital|floatformat:2 }}</td>
            </tr>
            <tr>
                <td><strong>Fee Tier:</strong></td>
                <td>{{ contract.get_fee_tier_display }}</td>
            </tr>
            <tr>
                <td><strong>Minimum Commitment:</strong></td>
                <td>{{ contract.minimum_commitment_months }} months</td>
            </tr>
        </table>
    </div>
    
    <!-- Fee Structure -->
    <div class="mb-4">
        <h4>FEE STRUCTURE</h4>
        <table class="table table-bordered">
            <tr>
                <td><strong>Management Fee:</strong></td>
                <td>{{ contract.management_fee_annual }}% annual (charged quarterly)</td>
            </tr>
            <tr>
                <td><strong>Performance Fee:</strong></td>
                <td>{{ contract.performance_fee_rate }}% of profits
                    {% if contract.performance_hurdle_rate > 0 %}
                    above {{ contract.performance_hurdle_rate }}% hurdle rate
                    {% endif %}
                </td>
            </tr>
            <tr>
                <td><strong>High-Water Mark:</strong></td>
                <td>{{ contract.has_high_water_mark|yesno:"Yes,No" }}</td>
            </tr>
        </table>
        
        <div class="alert alert-info">
            <strong>Example Fee Calculation (20% annual return = ${{ example_profit|floatformat:0 }} profit):</strong><br>
            Management Fee: ${{ example_mgmt_fee|floatformat:2 }}<br>
            Performance Fee: ${{ example_perf_fee|floatformat:2 }}<br>
            <strong>Total Fees: ${{ example_total_fees|floatformat:2 }}</strong><br>
            Your Net Profit: ${{ example_net_profit|floatformat:2 }} ({{ example_net_return|floatformat:1 }}% net return)
        </div>
    </div>
    
    <!-- Risk Allocation -->
    <div class="mb-4">
        <h4>RISK ALLOCATION</h4>
        <table class="table table-bordered">
            <tr>
                <td><strong>Trading Losses Borne by Client:</strong></td>
                <td>{{ contract.client_risk_percentage }}%</td>
            </tr>
            <tr>
                <td><strong>Trading Losses Borne by CODA:</strong></td>
                <td>{{ contract.coda_risk_percentage }}%</td>
            </tr>
        </table>
        
        {% if contract.coda_risk_percentage > 0 %}
        <div class="alert alert-warning">
            <strong>Shared Risk Model:</strong> CODA will co-invest and share {{ contract.coda_risk_percentage }}% of any trading losses. This demonstrates our confidence in the trading strategy.
        </div>
        {% endif %}
    </div>
    
    <!-- Trading Strategy -->
    <div class="mb-4">
        <h4>APPROVED TRADING STRATEGIES</h4>
        <ul>
            {% for strategy in contract.allowed_strategies %}
            <li>{{ strategy|title }}</li>
            {% endfor %}
        </ul>
        
        <table class="table table-bordered">
            <tr>
                <td><strong>Maximum Position Size:</strong></td>
                <td>${{ contract.managed_account.max_position_risk|floatformat:0 }}</td>
            </tr>
            <tr>
                <td><strong>Maximum Daily Loss:</strong></td>
                <td>{{ contract.managed_account.max_daily_loss }}% of account</td>
            </tr>
            <tr>
                <td><strong>Maximum Monthly Loss:</strong></td>
                <td>{{ contract.managed_account.max_monthly_loss }}% of account</td>
            </tr>
        </table>
    </div>
    
    <!-- Terms & Conditions -->
    <div class="mb-4">
        <h4>TERMS AND CONDITIONS</h4>
        
        <ol>
            <li><strong>Services Provided:</strong> CODA will provide discretionary options trading services for the Client's account, using approved strategies outlined in this agreement.</li>
            
            <li><strong>Discretionary Authority:</strong> Client grants CODA full discretionary authority to make trading decisions without prior approval for each trade.</li>
            
            <li><strong>Fee Payment:</strong> 
                <ul>
                    <li>Management fees charged quarterly in advance</li>
                    <li>Performance fees calculated and charged monthly</li>
                    <li>Fees automatically deducted from account balance</li>
                </ul>
            </li>
            
            <li><strong>Reporting:</strong>
                <ul>
                    <li>Daily: Email summary of positions and P&L</li>
                    <li>Weekly: Performance report</li>
                    <li>Monthly: Comprehensive statement with fee breakdown</li>
                    <li>Real-time: Access to client portal 24/7</li>
                </ul>
            </li>
            
            <li><strong>Risk Controls:</strong> CODA will adhere to the risk parameters outlined in this agreement. If daily or monthly loss limits are hit, trading will be paused pending client consultation.</li>
            
            <li><strong>Performance Expectations:</strong> While CODA targets {{ contract.managed_account.expected_return_rate }}% annual returns, past performance does not guarantee future results. Client acknowledges that losses are possible.</li>
            
            <li><strong>Termination:</strong>
                <ul>
                    <li>Client may terminate with 30 days written notice</li>
                    <li>Early termination before {{ contract.minimum_commitment_months }} months incurs ${{ contract.early_termination_fee|floatformat:0 }} fee</li>
                    <li>CODA may terminate with 30 days notice</li>
                    <li>Upon termination, all open positions will be closed within 5 business days</li>
                </ul>
            </li>
            
            <li><strong>Liability:</strong> CODA's liability is limited to management fees paid in the last 12 months. CODA is not liable for market losses or force majeure events.</li>
            
            <li><strong>Confidentiality:</strong> Both parties agree to keep all trading strategies, account details, and proprietary information confidential.</li>
            
            <li><strong>Governing Law:</strong> This agreement is governed by the laws of [State/Country].</li>
        </ol>
    </div>
    
    <!-- Risk Disclosures -->
    <div class="mb-4 p-3" style="background-color: #fff3cd; border: 2px solid #ffc107;">
        <h5 class="text-danger">⚠️ RISK DISCLOSURES</h5>
        <ul>
            <li><strong>Trading Risk:</strong> Options trading involves substantial risk of loss. You may lose some or all of your invested capital.</li>
            <li><strong>No Guarantee:</strong> There is no guarantee of profit. Past performance does not predict future results.</li>
            <li><strong>Market Risk:</strong> Market conditions can change rapidly, affecting position values.</li>
            <li><strong>Assignment Risk:</strong> Short options may be assigned early, requiring capital deployment.</li>
            <li><strong>Fees Impact:</strong> Fees will reduce your overall returns.</li>
        </ul>
        
        <p><strong>By signing this agreement, you acknowledge that you understand these risks and accept them.</strong></p>
    </div>
    
    <!-- Signature Section -->
    <div class="mb-4">
        <h4>ACCEPTANCE</h4>
        
        <form method="POST" action="{% url 'investing:accept_managed_trading_contract' contract.id %}" id="contract-form">
            {% csrf_token %}
            
            <div class="form-check mb-3">
                <input class="form-check-input" type="checkbox" id="understand-risks" required>
                <label class="form-check-label" for="understand-risks">
                    I have read and understand the Risk Disclosures above
                </label>
            </div>
            
            <div class="form-check mb-3">
                <input class="form-check-input" type="checkbox" id="agree-terms" required>
                <label class="form-check-label" for="agree-terms">
                    I agree to all Terms and Conditions outlined in this agreement
                </label>
            </div>
            
            <div class="form-check mb-3">
                <input class="form-check-input" type="checkbox" id="grant-authority" required>
                <label class="form-check-label" for="grant-authority">
                    I grant CODA discretionary trading authority over my account
                </label>
            </div>
            
            <div class="mb-3">
                <label for="client-signature" class="form-label">Digital Signature (Type your full name):</label>
                <input type="text" class="form-control" id="client-signature" name="signature" required 
                       placeholder="{{ contract.managed_account.client.get_full_name }}">
            </div>
            
            <div class="mb-3">
                <label class="form-label">Date:</label>
                <input type="text" class="form-control" value="{% now 'F d, Y' %}" readonly>
            </div>
            
            <div class="text-center">
                <button type="submit" class="btn btn-success btn-lg">
                    <i class="fa fa-check"></i> Accept Agreement & Activate Account
                </button>
            </div>
        </form>
    </div>
    
    <!-- Footer -->
    <div class="text-center text-muted mt-5">
        <small>
            This is a legally binding agreement. Please review carefully before accepting.<br>
            For questions, contact your account manager: {{ contract.managed_account.account_manager.get_full_name }}<br>
            Email: {{ contract.managed_account.account_manager.email }}
        </small>
    </div>
    
</div>

<script>
document.getElementById('contract-form').addEventListener('submit', function(e) {
    const signature = document.getElementById('client-signature').value;
    const clientName = '{{ contract.managed_account.client.get_full_name }}';
    
    if (signature.toLowerCase() !== clientName.toLowerCase()) {
        e.preventDefault();
        alert('Signature must match your full name: ' + clientName);
        return false;
    }
    
    if (!confirm('By clicking OK, you are legally accepting this Managed Trading Agreement. Continue?')) {
        e.preventDefault();
        return false;
    }
});
</script>
{% endblock %}
```

---

## 🤖 **Contract Automation Workflow**

### **Complete Automated Flow:**

```
Step 1: Client Expresses Interest
    ↓
Step 2: Admin Creates Managed Account (Pending)
    ↓
Step 3: System Auto-Generates Contract
    │
    ├─> Creates BaseContract record
    ├─> Creates ManagedTradingContract record
    ├─> Generates PDF from template
    ├─> Sends email to client with contract link
    └─> Status: 'pending_signature'
    ↓
Step 4: Client Reviews Contract Online
    │
    ├─> Views contract at /investing/managed/contract/<id>/
    ├─> Reads all terms
    ├─> Understands risks
    └─> Can download PDF
    ↓
Step 5: Client Signs Digitally
    │
    ├─> Checks all agreement boxes
    ├─> Types full name as signature
    ├─> Clicks "Accept Agreement"
    └─> System records:
        - Signature
        - IP address
        - Timestamp
        - Generates signed PDF
    ↓
Step 6: Account Activation
    │
    ├─> ManagedTradingAccount.status = 'active'
    ├─> ManagedTradingContract.status = 'active'
    ├─> Email confirmation to client
    ├─> Email notification to account manager
    └─> Trading can begin!
    ↓
Step 7: Ongoing Compliance
    │
    ├─> Annual contract review
    ├─> Re-sign if terms change
    └─> Archived when account closes
```

---

## 💻 **Technical Implementation**

### **Service: `contract_service.py`**

```python
class ManagedTradingContractService:
    """
    Automated contract generation and management
    """
    
    def generate_contract(self, managed_account, fee_tier='professional'):
        """
        Auto-generate contract for new managed account
        """
        from management.models import BaseContract
        from django.contrib.contenttypes.models import ContentType
        
        # Create base contract
        base_contract = BaseContract.objects.create(
            contract_type='Investment',
            client=managed_account.client,
            status='Pending',
            terms_and_conditions=self._get_standard_terms(),
            additional_info={
                'account_number': managed_account.account_number,
                'fee_tier': fee_tier
            }
        )
        
        # Get fee structure for tier
        fee_config = self._get_fee_config(fee_tier)
        
        # Create managed trading contract
        contract = ManagedTradingContract.objects.create(
            base_contract=base_contract,
            managed_account=managed_account,
            fee_tier=fee_tier,
            management_fee_annual=fee_config['management_fee'],
            performance_fee_rate=fee_config['performance_fee'],
            performance_hurdle_rate=fee_config.get('hurdle_rate', Decimal('0')),
            has_high_water_mark=fee_config.get('high_water_mark', True),
            client_risk_percentage=fee_config['client_risk'],
            coda_risk_percentage=fee_config['coda_risk'],
            minimum_commitment_months=fee_config['min_months'],
            allowed_strategies=fee_config['allowed_strategies']
        )
        
        # Generate PDF
        pdf_path = self._generate_contract_pdf(contract)
        contract.contract_pdf = pdf_path
        contract.save()
        
        # Send to client
        self._send_contract_email(contract)
        
        return contract
    
    def _get_fee_config(self, fee_tier):
        """
        Get fee configuration for tier
        """
        FEE_TIERS = {
            'starter': {
                'management_fee': Decimal('0.00'),
                'performance_fee': Decimal('25.00'),
                'hurdle_rate': Decimal('0.00'),
                'high_water_mark': True,
                'client_risk': Decimal('100.00'),
                'coda_risk': Decimal('0.00'),
                'min_months': 3,
                'allowed_strategies': ['short_put', 'covered_call']
            },
            'professional': {
                'management_fee': Decimal('1.50'),
                'performance_fee': Decimal('20.00'),
                'hurdle_rate': Decimal('8.00'),
                'high_water_mark': True,
                'client_risk': Decimal('100.00'),
                'coda_risk': Decimal('0.00'),
                'min_months': 6,
                'allowed_strategies': ['short_put', 'covered_call', 'credit_spread']
            },
            'premium': {
                'management_fee': Decimal('1.00'),
                'performance_fee': Decimal('15.00'),
                'hurdle_rate': Decimal('0.00'),
                'high_water_mark': True,
                'client_risk': Decimal('100.00'),
                'coda_risk': Decimal('0.00'),
                'min_months': 12,
                'allowed_strategies': ['short_put', 'covered_call', 'credit_spread', 'iron_condor'],
                'monthly_minimum': Decimal('500.00')
            },
            'co_invest': {
                'management_fee': Decimal('0.00'),
                'performance_fee': Decimal('50.00'),  # 50/50 split
                'hurdle_rate': Decimal('0.00'),
                'high_water_mark': True,
                'client_risk': Decimal('50.00'),  # Shared risk!
                'coda_risk': Decimal('50.00'),  # CODA shares losses
                'min_months': 12,
                'allowed_strategies': ['short_put', 'covered_call']  # Conservative only
            }
        }
        
        return FEE_TIERS.get(fee_tier, FEE_TIERS['professional'])
    
    def process_contract_acceptance(self, contract, signature, ip_address):
        """
        Process client's contract acceptance
        """
        from django.utils import timezone
        
        # Validate signature
        expected_name = contract.managed_account.client.get_full_name()
        if signature.lower().strip() != expected_name.lower().strip():
            raise ValidationError("Signature must match your full name")
        
        # Record acceptance
        contract.client_signature = signature
        contract.client_ip_address = ip_address
        contract.contract_signed_date = timezone.now()
        contract.base_contract.status = 'Active'
        contract.base_contract.save()
        contract.save()
        
        # Activate account
        contract.managed_account.status = 'active'
        contract.managed_account.activation_date = date.today()
        contract.managed_account.save()
        
        # Send confirmations
        self._send_acceptance_confirmation(contract)
        self._notify_account_manager(contract)
        
        # Create activity log
        TradingActivity.objects.create(
            managed_account=contract.managed_account,
            activity_type='account_created',
            description='Contract signed and account activated',
            performed_by=contract.managed_account.client,
            data_snapshot={
                'contract_id': contract.id,
                'signature': signature,
                'signed_at': contract.contract_signed_date.isoformat()
            }
        )
        
        return contract
```

---

## 📊 **Fee Structure in Requirements**

### **Update to 02_REQUIREMENTS.md:**

```markdown
### **BR-005: Multiple Fee Structure Support**
**Priority:** 🔴 Critical

**Requirements:**
- [ ] Support multiple fee tiers (Starter, Professional, Premium)
- [ ] Allow custom fee structures for VIP clients
- [ ] Automated fee calculation based on tier
- [ ] High-water mark enforcement
- [ ] Hurdle rate support
- [ ] Shared risk models (optional)

**Fee Tiers to Support:**

1. **Starter Tier:**
   - Management: 0%
   - Performance: 25% (no hurdle)
   - Min Account: $10,000
   - Min Commitment: 3 months

2. **Professional Tier:** (Recommended Default)
   - Management: 1.5% annual
   - Performance: 20% above 8% hurdle
   - Min Account: $25,000
   - Min Commitment: 6 months

3. **Premium Tier:**
   - Management: 1% annual
   - Performance: 15% (no hurdle)
   - Monthly Minimum: $500
   - Min Account: $100,000
   - Min Commitment: 12 months

4. **Co-Investment Tier:** (Limited Offering)
   - CODA invests 20% of account
   - Profit split: 50/50
   - Loss split: 50/50
   - Management: 0%
```

---

## ✅ **Updated System Architecture**

### **With Contract System:**

```
Client Onboarding Flow:

1. Admin Creates Account (status='pending_contract')
2. System Auto-Generates Contract
    ↓
3. BaseContract created (management app)
4. ManagedTradingContract created (investing app)
5. PDF generated
6. Email sent to client
    ↓
7. Client Reviews & Signs Online
8. Digital signature recorded
9. IP + timestamp logged
   ↓
10. Account Status → 'active'
11. Trading can begin!
```

---

## 🎉 **Recommendations Summary**

### **1. Fee Structure Recommendations:**

**❌ Reject Model A (CODA 100% Risk):**
- Too risky for CODA
- Not industry standard
- Could create regulatory issues
- Not scalable

**⚠️ Modify Model B (Client Risk, $50/position):**
- Increase to $100-150/position OR
- Add small performance fee (10%)
- Consider monthly minimum

**✅ Adopt Industry Standards:**
- **Primary:** 1.5% mgmt + 20% perf with 8% hurdle
- **Alternative:** 0% mgmt + 25% perf (no hurdle)
- **Premium:** 1% mgmt + 15% perf + $500/mo min

---

### **2. Contract System:**

✅ **Reuse existing `BaseContract` model** from management app  
✅ **Create `ManagedTradingContract`** extension  
✅ **Auto-generate contracts** when account created  
✅ **Digital signature** capture  
✅ **PDF generation** for records  
✅ **Email delivery** automated  

---

### **3. Implementation Priority:**

**Week 1:**
- Define final fee tiers
- Create `ManagedTradingContract` model
- Link to existing `BaseContract`

**Week 2:**
- Create contract template
- Implement PDF generation
- Test email delivery

**Week 3:**
- Build digital signature flow
- Test end-to-end
- Client UAT

---

**All requirements captured! Contract system designed! Ready for detailed implementation!** 🚀

---

## 🎯 **Complete Product Menu for Clients**

### **Client Decision Matrix: "Which Option is Right for Me?"**

```
Client Question 1: "How involved do I want to be?"

├─> "I want to LEARN and be hands-on"
│   └─> ✅ CONSULTATIVE COACHING
│       • $420/month ($50/session × 8 + $20 platform)
│       • 2 expert sessions per week
│       • Learn professional trading
│       • Keep 90% of profits
│       • Best for: Education-focused investors
│
├─> "I want passive management, minimal involvement"
│   │
│   └─> Question 2: "What's my account size?"
│       │
│       ├─> "$10K-$25K"
│       │   └─> ✅ STARTER TIER
│       │       • 0% management, 25% performance
│       │       • Only pay if you profit
│       │       • Best for: First-time clients
│       │
│       ├─> "$25K-$100K"
│       │   └─> ✅ PROFESSIONAL TIER (Most Popular)
│       │       • 1.5% mgmt + 20% perf (above 8% hurdle)
│       │       • Industry standard
│       │       • Best for: Serious investors
│       │
│       └─> "$100K+"
│           └─> ✅ PREMIUM TIER
│               • 1% mgmt + 15% perf + $500/mo min
│               • Weekly calls, VIP service
│               • Best for: High-net-worth
│
└─> "I want CODA to have skin in the game"
    └─> ✅ CO-INVESTMENT TIER (Limited to 3 clients)
        • CODA invests 20%, you invest 80%
        • 50/50 profit and loss split
        • Shared risk builds trust
        • Best for: VIP clients seeking partnership
```

---

## 📊 **Quick Comparison Table (All Options)**

| Tier | Monthly Cost | Annual Revenue (CODA) | Client Net Return ($30K, 20% return) | Involvement | Best For |
|------|--------------|----------------------|--------------------------------------|-------------|----------|
| **Consultative** ⭐ | $420 guaranteed | $5,040-$5,640 | 1-11% | ⬆️ High | Want to learn |
| **Starter** | $0 (only if profit) | $1,500 | 15% | ⬇️ Low | Small accounts |
| **Professional** | $37.50 avg | $1,170 | 16.1% | ⬇️ Low | Mainstream |
| **Premium** | $500 minimum | $6,000+ | 14% | ⬇️ Low | Wealthy |
| **Co-Invest** | $0 | $3,000 | 12.5% | ⬇️ Low | VIPs only |

---

## 🎨 **Client Onboarding Flow (All Tiers)**

### **Universal Flow:**

```
Step 1: Client Inquiry
    │
    ├─> "Tell us about your goals and account size"
    │
Step 2: CODA Recommends Tier
    │
    ├─> Small account + wants to learn → Consultative
    ├─> Medium account + passive → Professional
    ├─> Large account + premium service → Premium
    └─> VIP + wants partnership → Co-Investment
    │
Step 3: Client Selects Tier
    │
    └─> System creates account with selected fee structure
    │
Step 4: Auto-Generate Contract
    │
    ├─> Contract customized for selected tier
    ├─> Fee structure clearly outlined
    ├─> Email sent to client
    │
Step 5: Client Signs Digitally
    │
    └─> Account activated automatically
    │
Step 6: Trading Begins!
    │
    ├─> Consultative: First session scheduled
    ├─> Others: Positions executed based on AI recommendations
```

---

## 💻 **Technical Implementation: Fee Tier Selection**

### **Database Schema Update:**

```python
class ManagedTradingAccount(TimeStampedModel):
    # ... existing fields ...
    
    # ADD: Fee tier selection
    fee_tier = models.CharField(
        max_length=20,
        choices=[
            ('consultative', 'Consultative Coaching - $420/month + 10% bonus'),
            ('starter', 'Starter - 0% mgmt + 25% performance'),
            ('professional', 'Professional - 1.5% mgmt + 20% perf'),
            ('premium', 'Premium - 1% mgmt + 15% perf + $500/mo min'),
            ('co_invest', 'Co-Investment - 50/50 split'),
            ('custom', 'Custom Fee Structure')
        ],
        default='professional'
    )
    
    # For Consultative tier
    session_fee = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal('50.00'),
        help_text="Fee per coaching session"
    )
    sessions_per_month = models.IntegerField(
        default=8,
        help_text="Number of sessions per month"
    )
    monthly_platform_fee = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal('20.00'),
        help_text="Monthly platform/software fee"
    )
    
    # Session tracking
    sessions_completed_this_month = models.IntegerField(default=0)
    total_sessions_completed = models.IntegerField(default=0)
    next_session_date = models.DateTimeField(null=True, blank=True)
```

---

### **Fee Calculation Service:**

```python
class FeeCalculationService:
    """
    Calculate fees based on account tier
    """
    
    def calculate_monthly_fees(self, account, month_profit):
        """
        Calculate all fees for the month
        """
        if account.fee_tier == 'consultative':
            return self._calculate_consultative_fees(account, month_profit)
        elif account.fee_tier == 'starter':
            return self._calculate_starter_fees(account, month_profit)
        elif account.fee_tier == 'professional':
            return self._calculate_professional_fees(account, month_profit)
        # ... other tiers
    
    def _calculate_consultative_fees(self, account, month_profit):
        """
        Consultative tier: Session fees + platform + optional performance
        """
        # Session fees
        sessions_fee = account.sessions_completed_this_month * account.session_fee
        
        # Platform fee
        platform_fee = account.monthly_platform_fee
        
        # Optional performance bonus (10% of profit)
        performance_bonus = month_profit * Decimal('0.10') if month_profit > 0 else Decimal('0.00')
        
        return {
            'session_fees': sessions_fee,
            'platform_fee': platform_fee,
            'performance_bonus': performance_bonus,
            'total': sessions_fee + platform_fee + performance_bonus,
            'breakdown': f"{account.sessions_completed_this_month} sessions @ ${account.session_fee} + ${platform_fee} platform + ${performance_bonus} performance bonus"
        }
    
    def _calculate_professional_fees(self, account, month_profit):
        """
        Professional tier: 1.5% annual mgmt + 20% perf above 8% hurdle
        """
        # Monthly management fee
        annual_mgmt = account.current_balance * (account.management_fee_percentage / 100)
        monthly_mgmt = annual_mgmt / 12
        
        # Performance fee (only if above high-water mark and hurdle)
        perf_fee = Decimal('0.00')
        if account.current_balance > account.high_water_mark:
            profit_above_hwm = account.current_balance - account.high_water_mark
            hurdle_amount = account.high_water_mark * Decimal('0.08')  # 8% hurdle
            
            if profit_above_hwm > hurdle_amount:
                excess_profit = profit_above_hwm - hurdle_amount
                perf_fee = excess_profit * (account.performance_fee_percentage / 100)
        
        return {
            'management_fee': monthly_mgmt,
            'performance_fee': perf_fee,
            'total': monthly_mgmt + perf_fee,
            'breakdown': f"${monthly_mgmt} mgmt + ${perf_fee} performance"
        }
```

---

## 📋 **Session Tracking System (for Consultative Tier)**

### **Model: Session Record**

```python
class TradingSession(TimeStampedModel):
    """
    Track coaching/review sessions with clients
    For Consultative tier accounts
    """
    
    managed_account = models.ForeignKey(
        ManagedTradingAccount,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    
    session_date = models.DateTimeField()
    session_duration_minutes = models.IntegerField(default=30)
    session_type = models.CharField(
        max_length=20,
        choices=[
            ('position_review', 'Position Review'),
            ('strategy_planning', 'Strategy Planning'),
            ('performance_review', 'Performance Review'),
            ('education', 'Education/Training'),
            ('risk_review', 'Risk Management Review')
        ]
    )
    
    # Session content
    topics_discussed = models.TextField()
    positions_reviewed = models.ManyToManyField(
        'Portfolio',
        blank=True,
        related_name='review_sessions'
    )
    action_items = models.JSONField(default=list)
    # Example: [
    #   "Close AAPL position at 50% profit",
    #   "Consider MSFT short put for next week"
    # ]
    
    # Session notes
    session_notes = models.TextField(blank=True)
    client_feedback = models.TextField(blank=True)
    
    # Billing
    fee_charged = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal('50.00')
    )
    is_billed = models.BooleanField(default=False)
    billing_date = models.DateField(null=True, blank=True)
    
    # Recording (optional)
    recording_url = models.URLField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Trading Session"
        verbose_name_plural = "Trading Sessions"
        ordering = ['-session_date']
    
    def __str__(self):
        return f"{self.managed_account.account_number} - {self.session_date.strftime('%Y-%m-%d')}"
```

---

## 📅 **Session Management UI**

### **For Consultative Tier Clients:**

```html
<!-- Client Dashboard Addition for Consultative Tier -->

{% if account.fee_tier == 'consultative' %}
<div class="card mb-4">
    <div class="card-header bg-info text-white">
        <h5><i class="fa fa-calendar"></i> Your Sessions This Month</h5>
    </div>
    <div class="card-body">
        <!-- Sessions Stats -->
        <div class="row mb-3">
            <div class="col-md-4">
                <div class="text-center">
                    <h3>{{ account.sessions_completed_this_month }}</h3>
                    <small class="text-muted">Sessions This Month</small>
                </div>
            </div>
            <div class="col-md-4">
                <div class="text-center">
                    <h3>{{ sessions_remaining }}</h3>
                    <small class="text-muted">Remaining (of 8)</small>
                </div>
            </div>
            <div class="col-md-4">
                <div class="text-center">
                    <h3>${{ session_fees_this_month }}</h3>
                    <small class="text-muted">Session Fees</small>
                </div>
            </div>
        </div>
        
        <!-- Next Session -->
        {% if account.next_session_date %}
        <div class="alert alert-info">
            <strong>Next Session:</strong> 
            {{ account.next_session_date|date:"l, F d, Y at g:i A" }}
            <a href="{% url 'investing:join_session' account.id %}" class="btn btn-sm btn-primary float-end">
                <i class="fa fa-video"></i> Join Session
            </a>
        </div>
        {% else %}
        <div class="alert alert-warning">
            No session scheduled. 
            <a href="{% url 'investing:schedule_session' account.id %}" class="btn btn-sm btn-success">
                <i class="fa fa-calendar-plus"></i> Schedule Next Session
            </a>
        </div>
        {% endif %}
        
        <!-- Past Sessions -->
        <h6 class="mt-4">Recent Sessions:</h6>
        <table class="table table-sm">
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Type</th>
                    <th>Topics</th>
                    <th>Fee</th>
                    <th>Recording</th>
                </tr>
            </thead>
            <tbody>
                {% for session in recent_sessions %}
                <tr>
                    <td>{{ session.session_date|date:"M d, Y" }}</td>
                    <td>{{ session.get_session_type_display }}</td>
                    <td>{{ session.topics_discussed|truncatewords:10 }}</td>
                    <td>${{ session.fee_charged }}</td>
                    <td>
                        {% if session.recording_url %}
                        <a href="{{ session.recording_url }}" target="_blank">
                            <i class="fa fa-play-circle"></i> Watch
                        </a>
                        {% else %}
                        -
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endif %}
```

---

## 💰 **Revenue Comparison: All Tiers at Scale**

### **CODA Revenue Projections:**

| Tier | Fee Structure | Revenue per Client | 5 Clients | 10 Clients | 25 Clients |
|------|---------------|-------------------|-----------|------------|------------|
| **Consultative** | Session + Platform | $5,040+/year | $25,200 | $50,400 | $126,000 |
| **Starter** | 25% performance | $1,500/year | $7,500 | $15,000 | $37,500 |
| **Professional** | 1.5/20 + hurdle | $1,170/year | $5,850 | $11,700 | $29,250 |
| **Premium** | 1/15 + $500 min | $6,000/year | $30,000 | $60,000 | $150,000 |

**Mixed Portfolio Example (Realistic):**
```
2 Consultative clients:    $10,080/year
3 Professional clients:    $3,510/year
1 Starter client:          $1,500/year
1 Premium client:          $6,000/year
────────────────────────────────────
Total (7 clients):         $21,090/year

With manageable time investment:
- Consultative: 2 clients × 8 hours/month = 16 hours/month
- Others: 5 clients × 2 hours/month = 10 hours/month
- Total: 26 hours/month = ~6.5 hours/week
```

---

## 🎯 **Final Recommendations Summary**

### **Product Menu to Offer:**

✅ **Tier 0: Consultative Coaching** - YOUR EXISTING MODEL
- $50/session (2/week) + $20/month + 10% performance bonus
- **Perfect for:** Education-focused clients
- **CODA Revenue:** $5,040+/year (HIGHEST per client!)
- **Time:** High (8 hours/month per client)
- **Max Clients:** 5-10 individual, or 20-50 group

✅ **Tier 1: Starter** - Entry Level
- 0% mgmt + 25% performance
- **Perfect for:** Smaller accounts, first-timers
- **CODA Revenue:** $1,500/year
- **Time:** Low (automated)
- **Max Clients:** Unlimited

✅ **Tier 2: Professional** - Main Offering
- 1.5% mgmt + 20% perf (8% hurdle)
- **Perfect for:** Mainstream clients
- **CODA Revenue:** $1,170/year
- **Time:** Low (automated)
- **Max Clients:** Unlimited

✅ **Tier 3: Premium** - High-End
- 1% mgmt + 15% perf + $500/mo min
- **Perfect for:** $100K+ accounts
- **CODA Revenue:** $6,000+/year
- **Time:** Medium (weekly calls)
- **Max Clients:** 10-20

⚠️ **Tier 4: Co-Investment** - Special
- 50/50 profit/loss split, CODA invests 20%
- **Perfect for:** VIP partnership
- **CODA Revenue:** $3,000/year
- **Risk:** CODA capital at risk
- **Max Clients:** 2-3 only

---

## ✅ **System Integration**

### **Contract Template Supports All Tiers:**

```django
<!-- Contract automatically adjusts based on fee_tier -->

{% if contract.managed_account.fee_tier == 'consultative' %}
    <h4>CONSULTATIVE COACHING FEE STRUCTURE</h4>
    <table class="table">
        <tr>
            <td>Session Fee:</td>
            <td>${{ contract.managed_account.session_fee }} per session</td>
        </tr>
        <tr>
            <td>Sessions Per Month:</td>
            <td>{{ contract.managed_account.sessions_per_month }} sessions</td>
        </tr>
        <tr>
            <td>Monthly Platform Fee:</td>
            <td>${{ contract.managed_account.monthly_platform_fee }}</td>
        </tr>
        <tr>
            <td>Performance Bonus:</td>
            <td>10% of monthly profits</td>
        </tr>
        <tr class="table-info">
            <td><strong>Total Monthly Base:</strong></td>
            <td><strong>${{ monthly_base_fee }}</strong> (sessions + platform)</td>
        </tr>
    </table>
    
{% elif contract.managed_account.fee_tier == 'professional' %}
    <!-- Professional tier fee structure -->
    
{% elif contract.managed_account.fee_tier == 'premium' %}
    <!-- Premium tier fee structure -->
    
{% endif %}
```

---

## 🎉 **Summary**

### **Your Consultative Model:**
✅ **Integrated** into complete fee menu  
✅ **Positioned** as Tier 0 (entry point for education-focused)  
✅ **Enhanced** with 10% performance bonus recommendation  
✅ **Scaled** with group session option  
✅ **Automated** via TradingSession model  
✅ **Contracted** via same automated system  

### **Complete Offering:**
- **5 tiers** to choose from (Consultative + 4 standard tiers)
- **All automated** via same system
- **Client chooses** what fits their needs
- **Mix and match** - some consultative, some passive
- **Scalable** - from 1 to 50+ clients

### **Revenue Potential:**
- **Conservative** (5 consultative + 5 professional): $30,000/year
- **Target** (10 mixed clients): $40,000-$50,000/year
- **Aggressive** (25 mixed clients): $100,000+/year

**Your session model is now fully integrated into the system!** 🎉

---

**Return to:** [README.md](README.md)

