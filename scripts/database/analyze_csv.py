#!/usr/bin/env python
"""Quick CSV analysis script"""
import csv

with open('sample/ShortPuts_20251102_v1.csv', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    # Skip title row, use second row as header
    reader = csv.DictReader(lines[1:])
    
    iv_ranks = []
    premiums = []
    dtes = []
    
    for row in reader:
        try:
            # Get IV Rank and strip % and spaces
            iv_str = row.get('Implied Volatility Rank', '').replace('%', '').replace(' ', '').strip()
            if iv_str:
                iv_ranks.append(float(iv_str))
            
            # Get Mid Price
            premium_str = row.get('Mid Price', '').replace('$', '').replace(' ', '').strip()
            if premium_str:
                premiums.append(float(premium_str))
                
            # Get DTE
            dte_str = row.get('Days To Expiry', '').strip()
            if dte_str:
                dtes.append(int(dte_str))
        except Exception as e:
            pass
    
    print('📊 YOUR NEW CSV DATA:')
    print('=' * 60)
    if iv_ranks:
        avg_iv = sum(iv_ranks)/len(iv_ranks)
        print(f'✅ IV Rank: {avg_iv:.1f}% avg')
        print(f'   Range: {min(iv_ranks):.0f}% to {max(iv_ranks):.0f}%')
        below_40 = len([x for x in iv_ranks if x < 40])
        below_30 = len([x for x in iv_ranks if x < 30])
        print(f'   Below 40% filter: {below_40}/{len(iv_ranks)} would be rejected')
        print(f'   Below 30% filter: {below_30}/{len(iv_ranks)} would be rejected')
    if premiums:
        avg_prem = sum(premiums)/len(premiums)
        print(f'✅ Premium: ${avg_prem:.2f} avg')
        print(f'   Range: ${min(premiums):.2f} to ${max(premiums):.2f}')
    if dtes:
        avg_dte = sum(dtes)//len(dtes)
        print(f'✅ DTE: {avg_dte} days avg')
        print(f'   Range: {min(dtes)} to {max(dtes)} days')
    print('=' * 60)
    print(f'Total positions: {len(iv_ranks)}')
    print('')
    print('💡 RECOMMENDATION:')
    if iv_ranks:
        if avg_iv >= 40:
            print(f'   Your avg IV is {avg_iv:.1f}% - a 40% filter is OK ✅')
        elif avg_iv >= 30:
            print(f'   Your avg IV is {avg_iv:.1f}% - lower filter to 30% ⚠️')
        else:
            print(f'   Your avg IV is {avg_iv:.1f}% - lower filter to 20% or 0% ⚠️')

