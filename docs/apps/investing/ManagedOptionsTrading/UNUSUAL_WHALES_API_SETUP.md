# Unusual Whales API Setup Guide

**Date:** November 2025  
**Purpose:** Get your Unusual Whales API key and integrate with CODA

---

## STEP 1: Get Your API Key

### For Professional Plan ($54/month):

1. **Log into Unusual Whales:**
   - Go to https://unusualwhales.com/
   - Click your profile (top right)

2. **Navigate to API Settings:**
   - Click "Settings" or "Account"
   - Look for "API Access" or "Developer Settings"
   - Click "Generate API Key"

3. **Copy Your API Key:**
   - Format: `uw_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   - **IMPORTANT:** Save this securely - you can't see it again!

4. **Note Your Plan Limits:**
   - Professional Plan includes API access
   - Rate limits: Check your dashboard (usually 100 requests/minute)
   - Data included: Real-time flow, dark pool, historical

---

## STEP 2: Add API Key to CODA

### Option A: Environment Variable (RECOMMENDED for Production)

**On Heroku:**
```bash
heroku config:set UNUSUAL_WHALES_API_KEY="uw_your_key_here" --app codamakutano
```

**Verify:**
```bash
heroku config:get UNUSUAL_WHALES_API_KEY --app codamakutano
```

### Option B: Local Development

**In your `.env` file:**
```
UNUSUAL_WHALES_API_KEY=uw_your_key_here
UNUSUAL_WHALES_ENABLED=True
```

---

## STEP 3: Test API Connection

**Run this command:**
```bash
cd coda
python manage.py test_unusual_whales_api
```

**Expected output:**
```
✅ API Key valid
✅ Connection successful
✅ Rate limit: 100/minute
✅ Plan: Professional
✅ Data access: Real-time flow, Dark pool, Historical
```

---

## STEP 4: How It Works in CODA

### Automatic Integration:

1. **Upload OptionPlay CSVs** (as usual)
2. **CODA filters to 12 positions** (as usual)
3. **NEW: Unusual Whales checks each symbol:**
   - Is there unusual call/put volume today?
   - Any dark pool buying/selling?
   - What's the flow sentiment (bullish/bearish)?
4. **Positions get "Flow Score"** (0-100)
5. **You see timing indicator:**
   - 🟢 **GREEN (80-100):** Heavy buying flow - ENTER NOW!
   - 🟡 **YELLOW (50-79):** Normal flow - OK to enter
   - 🔴 **RED (0-49):** Heavy selling flow - WAIT or SKIP!

---

## WHAT DATA CODA FETCHES FROM UNUSUAL WHALES

### For Each Symbol in Your Filtered Positions:

1. **Today's Unusual Options Activity:**
   - Large call volume (bullish signal)
   - Large put volume (bearish signal)
   - Unusual volume vs open interest

2. **Dark Pool Activity:**
   - Large block trades (>100k shares)
   - Institutional buying/selling
   - Price level of dark pool activity

3. **Flow Sentiment:**
   - Net premium spent on calls vs puts
   - Aggressive vs passive orders
   - Overall bullish/bearish score

4. **Recent History (7 days):**
   - Pattern detection (accumulation/distribution)
   - Trend of institutional activity

---

## EXAMPLE: How You'll Use It

### Scenario: AAPL $170 Short Put

**OptionPlay suggests:**
- Symbol: AAPL
- Strike: $170
- Premium: $3.50
- DTE: 28 days
- IV Rank: 45%

**CODA AI scores:** 75/100 (Good)

**Unusual Whales checks:**
- 🟢 **Unusual call buying detected** (+15 pts)
- 🟢 **Dark pool buying at $175** (+10 pts)
- 🟢 **Bullish flow sentiment: 70%** (+10 pts)
- **Flow Score: 95/100** (EXCELLENT!)

**Final Total Score:** 75 + 35 = **110/100** ⭐ **ENTER IMMEDIATELY!**

---

### Scenario: TSLA $250 Short Put

**OptionPlay suggests:**
- Symbol: TSLA
- Strike: $250
- Premium: $5.00
- DTE: 28 days
- IV Rank: 55%

**CODA AI scores:** 68/100 (Above Average)

**Unusual Whales checks:**
- 🔴 **Unusual put buying detected** (-20 pts)
- 🔴 **Dark pool selling at $260** (-15 pts)
- 🔴 **Bearish flow sentiment: 80%** (-15 pts)
- **Flow Score: 18/100** (DANGER!)

**Final Total Score:** 68 - 50 = **18/100** ⚠️ **SKIP THIS POSITION!**

---

## MONITORING ACTIVE POSITIONS

### Real-Time Alerts:

Once positions are entered, CODA monitors them via Unusual Whales:

**Example: You have AAPL $170 short put (entered 1 week ago)**

**Unusual Whales detects:**
- 🚨 Large dark pool selling at $172 (2 points above entry)
- 🚨 Institutional put buying spike
- 🚨 Bearish flow sentiment: 85%

**CODA sends WhatsApp alert:**
```
⚠️ ALERT: AAPL Flow Reversal Detected!

Position: AAPL $170 Short Put (Entered 7 days ago)
Current P&L: +$150 (43% profit)

Unusual Whales Detected:
🔴 Dark pool selling at $172
🔴 Institutional put buying spike
🔴 Bearish sentiment: 85%

RECOMMENDATION: Close early, take profit
Risk of assignment increased significantly

Reply YES to close position
Reply NO to hold (risky!)
```

---

## COST BREAKDOWN

### With Unusual Whales Integration:

**Monthly:**
- OptionPlay: $42/month ($500/year)
- Unusual Whales Professional: $54/month ($648/year with discount)
- **Total:** $96/month ($1,148/year)

**Value for $30k Capital:**
- Cost: 3.8% of capital
- Benefit: Avoid 2-3 bad trades/year = $500-1,000 saved
- ROI: 43-87% on subscription costs

**Time Saved:**
- No manual flow checking
- Automatic monitoring of active positions
- Real-time alerts for exits

---

## TROUBLESHOOTING

### "API Key Invalid" Error:
- Check you copied the entire key (starts with `uw_`)
- Verify in Unusual Whales dashboard (Settings > API)
- Regenerate key if needed

### "Rate Limit Exceeded" Error:
- Professional plan: 100 requests/minute
- CODA uses: ~1 request per symbol (12 requests/upload)
- You're fine unless uploading >100 symbols at once

### "No Data Available" Error:
- Some symbols may not have unusual activity today
- CODA will skip flow scoring and use AI score only
- Not an error - just means normal flow

---

## NEXT STEPS

1. ✅ Get your API key from Unusual Whales
2. ✅ Add to Heroku: `heroku config:set UNUSUAL_WHALES_API_KEY="your_key"`
3. ✅ Upload OptionPlay CSVs (as usual)
4. ✅ CODA auto-fetches flow data
5. ✅ See flow scores + timing indicators
6. ✅ Enter positions with confidence!

---

**Questions?** Check the API status dashboard: https://unusualwhales.com/api-status

