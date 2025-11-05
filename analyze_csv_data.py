"""
Analyze all 6 CSV files to determine smart default filters

Purpose: Set filter defaults based on REAL data patterns to avoid:
- Too strict = 0 positions (filtering everything)
- Too loose = 100 positions (no filtering)

Goal: Catch top 70-80% quality positions, filter bottom 20-30%
"""

import csv
import statistics
from collections import defaultdict

def clean_value(val, is_percent=False, is_money=False):
    """Clean CSV values"""
    if not val:
        return 0
    val = str(val).replace('$', '').replace('%', '').replace(',', '').strip()
    try:
        num = float(val)
        if is_percent and num > 1:  # Already percentage
            return num
        return num
    except:
        return 0

def analyze_file(filepath, name):
    """Analyze a single CSV file"""
    print(f"\n{'='*80}")
    print(f"📊 {name}")
    print(f"{'='*80}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
        # Find header row (skip title rows)
        header_idx = 0
        for i, line in enumerate(lines[:10]):
            if 'Symbol' in line or 'symbol' in line or 'underlying_symbol' in line:
                header_idx = i
                break
        
        # Parse from header onwards
        reader = csv.DictReader(lines[header_idx:])
        rows = list(reader)
    
    if not rows:
        print("  ❌ No data")
        return
    
    print(f"Total Rows: {len(rows)}")
    
    # Collect data
    premiums = []
    iv_ranks = []
    dtes = []
    rocs = []
    symbols = set()
    
    for row in rows:
        # Premium (Mid Price or Premium column)
        prem = clean_value(row.get('Mid Price') or row.get('Premium', '0'), is_money=True)
        if prem > 0:
            premiums.append(prem)
        
        # IV Rank
        iv = clean_value(row.get('Implied Volatility Rank') or row.get('IV Rank', '0'))
        if iv > 0:
            iv_ranks.append(iv)
        
        # DTE
        dte = int(clean_value(row.get('Days To Expiry') or row.get('DTE', '0')))
        if dte > 0:
            dtes.append(dte)
        
        # ROC (Raw Return or calculate)
        roc = clean_value(row.get('Raw Return', '0'), is_percent=True)
        if roc > 0:
            rocs.append(roc)
        
        # Symbol
        sym = row.get('Symbol') or row.get('underlying_symbol', '')
        if sym:
            symbols.add(sym.strip().upper())
    
    # Calculate statistics
    if premiums:
        sorted_prem = sorted(premiums)
        print(f"\nPREMIUM:")
        print(f"  Min: ${min(premiums):.2f}")
        print(f"  Max: ${max(premiums):.2f}")
        print(f"  Avg: ${statistics.mean(premiums):.2f}")
        print(f"  Median: ${statistics.median(premiums):.2f}")
        print(f"  25th %ile: ${sorted_prem[len(sorted_prem)//4]:.2f} (bottom quarter)")
        print(f"  75th %ile: ${sorted_prem[3*len(sorted_prem)//4]:.2f} (top quarter)")
        print(f"  💡 Suggested filter: ${sorted_prem[len(sorted_prem)//4]:.2f} (catches top 75%)")
    
    if iv_ranks:
        sorted_iv = sorted(iv_ranks)
        print(f"\nIV RANK:")
        print(f"  Min: {min(iv_ranks):.0f}%")
        print(f"  Max: {max(iv_ranks):.0f}%")
        print(f"  Avg: {statistics.mean(iv_ranks):.0f}%")
        print(f"  Median: {statistics.median(iv_ranks):.0f}%")
        print(f"  25th %ile: {sorted_iv[len(sorted_iv)//4]:.0f}%")
        print(f"  75th %ile: {sorted_iv[3*len(sorted_iv)//4]:.0f}%")
        print(f"  💡 Suggested filter: {sorted_iv[len(sorted_iv)//4]:.0f}% (catches top 75%)")
    
    if dtes:
        sorted_dte = sorted(dtes)
        print(f"\nDTE:")
        print(f"  Min: {min(dtes)}")
        print(f"  Max: {max(dtes)}")
        print(f"  Avg: {statistics.mean(dtes):.0f}")
        print(f"  Median: {statistics.median(dtes):.0f}")
        print(f"  25th %ile: {sorted_dte[len(sorted_dte)//4]}")
        print(f"  75th %ile: {sorted_dte[3*len(sorted_dte)//4]}")
        print(f"  💡 Suggested max: {sorted_dte[3*len(sorted_dte)//4]} (catches top 75%)")
    
    if rocs:
        sorted_roc = sorted(rocs)
        print(f"\nROC (Raw Return):")
        print(f"  Min: {min(rocs):.1f}%")
        print(f"  Max: {max(rocs):.1f}%")
        print(f"  Avg: {statistics.mean(rocs):.1f}%")
        print(f"  Median: {statistics.median(rocs):.1f}%")
        print(f"  25th %ile: {sorted_roc[len(sorted_roc)//4]:.1f}%")
        print(f"  75th %ile: {sorted_roc[3*len(sorted_roc)//4]:.1f}%")
        print(f"  💡 Suggested filter: {sorted_roc[len(sorted_roc)//4]:.1f}% (catches top 75%)")
    
    print(f"\nSYMBOLS: {len(symbols)} unique symbols")
    
    return {
        'name': name,
        'total_rows': len(rows),
        'premium_25th': sorted_prem[len(sorted_prem)//4] if premiums else 0,
        'iv_25th': sorted_iv[len(sorted_iv)//4] if iv_ranks else 0,
        'dte_75th': sorted_dte[3*len(sorted_dte)//4] if dtes else 60,
        'roc_25th': sorted_roc[len(sorted_roc)//4] if rocs else 0,
        'unique_symbols': len(symbols)
    }

# Analyze all files
print("🔍 ANALYZING ALL CSV FILES FOR SMART DEFAULTS")
print("="*80)

results = []

# File 1: Short Puts
results.append(analyze_file('coda/sample/ShortPuts_20251102_v1.csv', 'SHORT PUTS (OptionsPlay)'))

# File 2: Covered Calls
results.append(analyze_file('coda/sample/CoveredCalls_20251103_v1.csv', 'COVERED CALLS (OptionsPlay)'))

# File 3: Credit Spreads
results.append(analyze_file('coda/sample/CreditSpread_20251103_v1.csv', 'CREDIT SPREADS (OptionsPlay)'))

# File 4: Unusual Whales - Options Flow
results.append(analyze_file('coda/sample/whales/OptionFlow_251103_v1.csv', 'OPTIONS FLOW (Unusual Whales)'))

# File 5: Dark Pool
results.append(analyze_file('coda/sample/whales/dark-pool_50_251103_v1.csv', 'DARK POOL (Unusual Whales)'))

# File 6: Lit Flow
results.append(analyze_file('coda/sample/whales/lit_flow_50.csv', 'LIT FLOW (Unusual Whales)'))

# Summary recommendations
print("\n" + "="*80)
print("🎯 SMART DEFAULT FILTER RECOMMENDATIONS")
print("="*80)

# Calculate weighted averages across all OptionPlay files (not Whales)
optionplay_results = [r for r in results if r and 'OptionsPlay' in r['name']]

if optionplay_results:
    avg_prem_25th = statistics.mean([r['premium_25th'] for r in optionplay_results if r['premium_25th'] > 0])
    avg_iv_25th = statistics.mean([r['iv_25th'] for r in optionplay_results if r['iv_25th'] > 0])
    avg_dte_75th = statistics.mean([r['dte_75th'] for r in optionplay_results if r['dte_75th'] > 0])
    avg_roc_25th = statistics.mean([r['roc_25th'] for r in optionplay_results if r['roc_25th'] > 0])
    
    print(f"\nBased on {sum(r['total_rows'] for r in optionplay_results)} OptionsPlay positions:")
    print(f"\n📌 TIER 1 DEFAULTS (Quality Filters):")
    print(f"  Min Premium: ${avg_prem_25th:.2f} (catches top 75% by quality)")
    print(f"  Min IV Rank: {avg_iv_25th:.0f}% (high volatility = better premiums)")
    print(f"  Max DTE: {avg_dte_75th:.0f} days (optimal theta decay window)")
    print(f"  Min ROC: {avg_roc_25th:.1f}% (capital efficiency threshold)")
    
    # Conservative vs Aggressive presets
    print(f"\n📊 FILTER PRESETS:")
    print(f"\n  AGGRESSIVE (Catch 90%):")
    print(f"    Min Premium: ${avg_prem_25th * 0.7:.2f}")
    print(f"    Min IV: {max(20, avg_iv_25th * 0.7):.0f}%")
    print(f"    Max DTE: {min(60, avg_dte_75th * 1.3):.0f}")
    print(f"    Min ROC: {avg_roc_25th * 0.6:.1f}%")
    
    print(f"\n  BALANCED (Catch 75%) ⭐ RECOMMENDED:")
    print(f"    Min Premium: ${avg_prem_25th:.2f}")
    print(f"    Min IV: {avg_iv_25th:.0f}%")
    print(f"    Max DTE: {avg_dte_75th:.0f}")
    print(f"    Min ROC: {avg_roc_25th:.1f}%")
    
    print(f"\n  CONSERVATIVE (Catch 50% - highest quality):")
    print(f"    Min Premium: ${avg_prem_25th * 1.5:.2f}")
    print(f"    Min IV: {min(50, avg_iv_25th * 1.2):.0f}%")
    print(f"    Max DTE: {max(30, avg_dte_75th * 0.8):.0f}")
    print(f"    Min ROC: {avg_roc_25th * 1.3:.1f}%")

print("\n" + "="*80)
print("✅ Analysis Complete!")
print("="*80)

