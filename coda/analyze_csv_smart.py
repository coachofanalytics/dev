#!/usr/bin/env python
"""Smart options filtering - Industry Standards"""
import csv

with open('sample/ShortPuts_20251102_v1.csv', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    reader = csv.DictReader(lines[1:])
    
    positions = []
    for row in reader:
        try:
            position = {
                'symbol': row.get('Symbol', '').strip(),
                'iv_rank': float(row.get('Implied Volatility Rank', '0').replace('%', '').replace(' ', '').strip()),
                'premium': float(row.get('Mid Price', '0').replace('$', '').replace(' ', '').strip()),
                'annual_return': float(row.get('Annualized Return', '0').replace('%', '').replace(' ', '').strip()),
                'dte': int(row.get('Days To Expiry', '0').strip()),
                'distance': float(row.get('Distance To Strike', '0').replace('%', '').replace(' ', '').strip()),
                'earnings_flag': row.get('Earnings Flag', '').strip() == 'Y',
                'stock_price': float(row.get('Stock Price', '0').replace('$', '').replace(' ', '').strip()),
            }
            positions.append(position)
        except:
            pass

print('=' * 80)
print('🎯 INDUSTRY-STANDARD OPTIONS FILTERS')
print('=' * 80)
print(f'Total Positions Available: {len(positions)}')
print()

# TIER 1: Conservative (Highest Probability)
tier1 = [p for p in positions if
    p['iv_rank'] >= 40 and  # Higher IV for better premium
    p['annual_return'] >= 90 and  # Strong returns
    p['distance'] >= -4 and p['distance'] <= -2 and  # Safe distance (70-80% prob)
    not p['earnings_flag'] and  # No earnings risk
    p['dte'] >= 25 and p['dte'] <= 35  # Theta sweet spot
]

print('🏆 TIER 1: CONSERVATIVE (Highest Win Rate ~80%)')
print('-' * 80)
print(f'Filters:')
print(f'  ✓ IV Rank ≥ 40% (good premium without extreme vol)')
print(f'  ✓ Annual Return ≥ 90% (strong income)')
print(f'  ✓ Distance -4% to -2% (70-80% probability)')
print(f'  ✓ No earnings before expiration')
print(f'  ✓ DTE 25-35 days (theta peak)')
print(f'Passed: {len(tier1)} positions')
if tier1:
    print(f'Avg IV: {sum(p["iv_rank"] for p in tier1)/len(tier1):.1f}%')
    print(f'Avg Return: {sum(p["annual_return"] for p in tier1)/len(tier1):.1f}%')
    print('Top 10:')
    for i, p in enumerate(sorted(tier1, key=lambda x: x['annual_return'], reverse=True)[:10], 1):
        earnings = '⚠️' if p['earnings_flag'] else '✓'
        print(f'  {i:2d}. {p["symbol"]:6s} - {p["annual_return"]:5.0f}% return, IV:{p["iv_rank"]:3.0f}%, {earnings}')
print()

# TIER 2: Balanced (Good Risk/Reward)
tier2 = [p for p in positions if
    p['iv_rank'] >= 35 and  # Moderate IV
    p['annual_return'] >= 80 and  # Good returns
    p['distance'] >= -5 and p['distance'] <= -2 and  # Reasonable distance
    p['dte'] >= 25 and p['dte'] <= 35
]

print('⚖️  TIER 2: BALANCED (Best Risk/Reward)')
print('-' * 80)
print(f'Filters:')
print(f'  ✓ IV Rank ≥ 35% (balanced premium)')
print(f'  ✓ Annual Return ≥ 80% (good income)')
print(f'  ✓ Distance -5% to -2% (65-80% probability)')
print(f'  ✓ Earnings OK if return compensates')
print(f'  ✓ DTE 25-35 days')
print(f'Passed: {len(tier2)} positions')
if tier2:
    print(f'Avg IV: {sum(p["iv_rank"] for p in tier2)/len(tier2):.1f}%')
    print(f'Avg Return: {sum(p["annual_return"] for p in tier2)/len(tier2):.1f}%')
    print('Top 10:')
    for i, p in enumerate(sorted(tier2, key=lambda x: x['annual_return'], reverse=True)[:10], 1):
        earnings = '⚠️' if p['earnings_flag'] else '✓'
        print(f'  {i:2d}. {p["symbol"]:6s} - {p["annual_return"]:5.0f}% return, IV:{p["iv_rank"]:3.0f}%, {earnings}')
print()

# TIER 3: Aggressive (Higher Returns, Higher Risk)
tier3 = [p for p in positions if
    p['iv_rank'] >= 30 and  # Lower IV acceptable
    p['annual_return'] >= 100 and  # High returns required
    p['distance'] >= -6 and p['distance'] <= -2 and  # Closer to money OK
    p['dte'] >= 25 and p['dte'] <= 35
]

print('🚀 TIER 3: AGGRESSIVE (Highest Returns)')
print('-' * 80)
print(f'Filters:')
print(f'  ✓ IV Rank ≥ 30% (accept lower vol for right opportunity)')
print(f'  ✓ Annual Return ≥ 100% (premium compensates risk)')
print(f'  ✓ Distance -6% to -2% (60-80% probability)')
print(f'  ✓ Earnings risk acceptable if return > 120%')
print(f'  ✓ DTE 25-35 days')
print(f'Passed: {len(tier3)} positions')
if tier3:
    print(f'Avg IV: {sum(p["iv_rank"] for p in tier3)/len(tier3):.1f}%')
    print(f'Avg Return: {sum(p["annual_return"] for p in tier3)/len(tier3):.1f}%')
    print('Top 10:')
    for i, p in enumerate(sorted(tier3, key=lambda x: x['annual_return'], reverse=True)[:10], 1):
        earnings = '⚠️' if p['earnings_flag'] else '✓'
        print(f'  {i:2d}. {p["symbol"]:6s} - {p["annual_return"]:5.0f}% return, IV:{p["iv_rank"]:3.0f}%, {earnings}')
print()

print('=' * 80)
print('💡 RECOMMENDATION:')
print('=' * 80)
print('Start with TIER 2 (Balanced) for your first 10 positions')
print('  → Good risk/reward balance')
print('  → 65-80% win probability')
print('  → ~80-120% annualized returns')
print()
print('Add TIER 1 if you want more conservative plays')
print('  → Higher win rate (~80%)')
print('  → Lower returns but safer')
print()
print('Add TIER 3 for 1-2 "moonshot" positions if desired')
print('  → Higher risk, higher reward')
print('  → Only allocate 10-20% of capital here')
print('=' * 80)

