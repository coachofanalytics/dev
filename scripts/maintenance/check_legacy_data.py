"""
Check if legacy models have any data
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda.settings')
django.setup()

from investing.models import ShortPut, covered_calls, Portfolio

print("=" * 80)
print("CHECKING LEGACY MODELS FOR DATA")
print("=" * 80)

shortput_count = ShortPut.objects.count()
coveredcalls_count = covered_calls.objects.count()
portfolio_count = Portfolio.objects.count()

print(f"ShortPut: {shortput_count} records")
print(f"covered_calls: {coveredcalls_count} records")
print(f"Portfolio: {portfolio_count} records")
print()
print("=" * 80)

if shortput_count + coveredcalls_count + portfolio_count == 0:
    print("✅ NO DATA FOUND - Safe to delete models!")
else:
    print("⚠️  DATA EXISTS - Need to migrate before deletion!")
    if shortput_count > 0:
        print(f"   - ShortPut: {shortput_count} records need migration")
    if coveredcalls_count > 0:
        print(f"   - covered_calls: {coveredcalls_count} records need migration")
    if portfolio_count > 0:
        print(f"   - Portfolio: {portfolio_count} records need migration")

print("=" * 80)

