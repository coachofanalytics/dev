"""
KILLER SYSTEM: Multi-Strategy Cross-Validation Analysis
Analyze 3 OptionPlay files to find highest-probability positions
"""

import csv
from collections import defaultdict
from decimal import Decimal

def clean_value(val):
    """Clean string values (remove $, %, spaces)"""
    if not val:
        return None
    return val.strip().replace('$', '').replace('%', '').replace(',', '')

def read_csv_file(filepath, skiprows=1):
    """Read CSV and return list of dicts"""
    with open(filepath, 'r') as f:
        lines = f.readlines()[skiprows:]  # Skip title rows
        reader = csv.DictReader(lines)
        return list(reader)

# Read all 3 files
print("="  * 80)
print("🎯 KILLER SYSTEM: MULTI-STRATEGY ANALYSIS")
print("=" * 80)
print()

short_puts = read_csv_file('sample/ShortPuts_20251102_v1.csv')
covered_calls = read_csv_file('sample/CoveredCalls_20251103_v1.csv')
credit_spreads = read_csv_file('sample/CreditSpread_20251103_v1.csv')

print(f"✅ Loaded {len(short_puts)} Short Puts")
print(f"✅ Loaded {len(covered_calls)} Covered Calls")
print(f"✅ Loaded {len(credit_spreads)} Credit Spreads")
print()

# Extract symbols
sp_symbols = {row['Symbol'].strip().upper() for row in short_puts if row.get('Symbol')}
cc_symbols = {row['Symbol'].strip().upper() for row in covered_calls if row.get('Symbol')}
cs_symbols = {row['Symbol'].strip().upper() for row in credit_spreads if row.get('Symbol')}

# Find overlaps
sp_cc_overlap = sp_symbols.intersection(cc_symbols)
sp_cs_overlap = sp_symbols.intersection(cs_symbols)
all_three_overlap = sp_symbols.intersection(cc_symbols, cs_symbols)

print("=" * 80)
print("🔍 CROSS-VALIDATION RESULTS:")
print("=" * 80)
print(f"📌 Short Puts ONLY: {len(sp_symbols - cc_symbols - cs_symbols)} symbols")
print(f"📌 Covered Calls ONLY: {len(cc_symbols - sp_symbols - cs_symbols)} symbols")
print(f"📌 Credit Spreads ONLY: {len(cs_symbols - sp_symbols - cc_symbols)} symbols")
print()
print(f"💎 SHORT PUTS + COVERED CALLS: {len(sp_cc_overlap)} symbols (HIGH CONVICTION!)")
print(f"💎 SHORT PUTS + CREDIT SPREADS: {len(sp_cs_overlap)} symbols")
print(f"🏆 ALL THREE STRATEGIES: {len(all_three_overlap)} symbols (HIGHEST CONVICTION!)")
print()

# Analyze high-conviction symbols (in multiple lists)
print("=" * 80)
print("💎 TOP HIGH-CONVICTION SYMBOLS (In Both Short Puts + Covered Calls):")
print("=" * 80)
print(f"{'Symbol':<10} {'SP IV':<10} {'CC IV':<10} {'SP Return':<12} {'CC Return':<12} {'Earnings':<10}")
print("-" * 80)

# Create lookup dicts
sp_dict = {row['Symbol'].strip().upper(): row for row in short_puts if row.get('Symbol')}
cc_dict = {row['Symbol'].strip().upper(): row for row in covered_calls if row.get('Symbol')}

for symbol in sorted(list(sp_cc_overlap))[:20]:
    sp_data = sp_dict.get(symbol, {})
    cc_data = cc_dict.get(symbol, {})
    
    sp_iv = clean_value(sp_data.get('Implied Volatility Rank', 'N/A'))
    cc_iv = clean_value(cc_data.get('Implied Volatility Rank', 'N/A'))
    sp_return = clean_value(sp_data.get('Raw Return', 'N/A'))
    cc_return = clean_value(cc_data.get('Raw Return', 'N/A'))
    earnings = sp_data.get('Earnings Flag', 'N/A')
    
    print(f"{symbol:<10} {sp_iv or 'N/A':<10} {cc_iv or 'N/A':<10} {sp_return or 'N/A':<12} {cc_return or 'N/A':<12} {earnings:<10}")

print()
print("=" * 80)
print("🎯 KILLER SYSTEM INSIGHTS:")
print("=" * 80)
print("""
1. 💎 HIGH-CONVICTION SYMBOLS (In Both SP + CC):
   - OptionPlay suggests BOTH bullish (short put) AND income (covered call)
   - Means: Strong stock, good volatility, multiple profit paths
   - Strategy: Convert short puts to CREDIT SPREADS for lower risk
   
2. 🏆 ULTRA-HIGH-CONVICTION (In All 3 Lists):
   - Appears in Short Puts + Covered Calls + Credit Spreads
   - Means: OptionPlay has VERY high confidence
   - Strategy: Use credit spreads from list #3, validate with SP/CC data

3. ⚠️ SINGLE-LIST SYMBOLS:
   - Only in one strategy = lower conviction
   - May still be good, but less validated
   
4. 🎲 EARNINGS RISK:
   - Symbols with earnings in window = higher risk/reward
   - High-conviction + no earnings = safest bets
   
RECOMMENDED FILTER CRITERIA:
✅ Must appear in at least 2 strategies (cross-validation)
✅ IV Rank >30% (good premium)
✅ No earnings in next 7 days (reduce risk)
✅ Convert to credit spreads (cap max loss)
""")

print()
print("=" * 80)
print("🚀 NEXT-LEVEL DATA SOURCES (Game Changers):")
print("=" * 80)
print("""
1. 📈 MARKET SENTIMENT DATA:
   - Reddit WallStreetBets mentions
   - Twitter/X trending tickers
   - StockTwits sentiment scores
   - Why: Catch momentum before it explodes

2. 📰 NEWS & CATALYSTS:
   - FDA approvals (biotech)
   - Earnings surprises
   - Analyst upgrades/downgrades
   - Product launches
   - Why: Trade the news, not after

3. 🏛️ INSTITUTIONAL FLOW:
   - Dark pool activity
   - Unusual options activity (sweeps)
   - 13F filings (institutional holdings)
   - Why: Follow smart money

4. 📊 TECHNICAL INDICATORS:
   - Support/resistance levels
   - RSI (overbought/oversold)
   - Moving average crossovers
   - Volume spikes
   - Why: Better entry/exit timing

5. 🏦 FUNDAMENTAL SCREENING:
   - Market cap >$1B (liquidity)
   - Positive earnings (profitability)
   - Low debt-to-equity (financial health)
   - Analyst consensus (1-2 rating)
   - Why: Trade quality companies

6. 🔥 VOLATILITY EVENTS:
   - Upcoming earnings calendar
   - Fed announcements
   - Sector rotation signals
   - Economic data releases
   - Why: Avoid unexpected volatility

IMPLEMENTATION PRIORITY:
1. ✅ Multi-strategy cross-validation (YOU HAVE THIS!)
2. 🔥 Unusual options activity (easy API: unusualwhales.com)
3. 📈 Social sentiment (free: Reddit/Twitter APIs)
4. 📊 Technical indicators (free: yfinance library)
5. 🏛️ Institutional data (free: finviz.com scraping)
""")

