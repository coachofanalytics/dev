"""
Ledger Valuation Service - Converts internal units to USD values.

Migrated to investing app - models imported from shareholders app.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict
import logging

# Models imported from original shareholders app (preserves DB ownership)
from investing.models import Deal, ValuationRate

logger = logging.getLogger(__name__)

DEFAULT_VALUATION_RATES = {
    'IN_KIND': {'rate_per_unit': Decimal('1.00'), 'unit_label': 'USD'},
    'TIME': {'rate_per_unit': Decimal('50.00'), 'unit_label': 'hr'},
    'WORK': {'rate_per_unit': Decimal('25.00'), 'unit_label': 'pts'},
}


class LedgerValuationService:
    """Service for calculating USD values from internal units."""
    
    def __init__(self, deal: Deal):
        self.deal = deal
        self._rates_cache = {}
        self._load_rates()
    
    def _load_rates(self):
        rates = ValuationRate.objects.filter(deal=self.deal, is_active=True)
        for rate in rates:
            self._rates_cache[rate.tier] = rate
    
    def get_rate(self, tier: str) -> Dict:
        if tier == 'CASH':
            return {'rate_per_unit': Decimal('1.00'), 'unit_label': 'USD', 'source': 'fixed'}
        if tier in self._rates_cache:
            rate = self._rates_cache[tier]
            return {'rate_per_unit': rate.rate_per_unit, 'unit_label': rate.unit_label, 'source': 'custom'}
        if tier in DEFAULT_VALUATION_RATES:
            return {**DEFAULT_VALUATION_RATES[tier], 'source': 'default'}
        return {'rate_per_unit': Decimal('1.00'), 'unit_label': 'units', 'source': 'fallback'}
    
    def calculate_value_usd(self, tier: str, internal_units: Decimal) -> Decimal:
        rate_info = self.get_rate(tier)
        value = internal_units * rate_info['rate_per_unit']
        return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def get_all_rates(self) -> Dict[str, Dict]:
        return {tier: self.get_rate(tier) for tier in ['CASH', 'IN_KIND', 'TIME', 'WORK']}
