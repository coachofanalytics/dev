"""Capital Allocation Service

Automates managed options sizing to achieve monthly income targets while
leveraging Unusual Whales timing signals and existing AI scores.
"""

from __future__ import annotations

import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, List, Dict, Any

from django.utils import timezone

from .base_service import BaseInvestingService
from .unusual_whales_service import UnusualWhalesService


logger = logging.getLogger(__name__)


class CapitalAllocationService(BaseInvestingService):
    """Recommend position sizes to meet managed income targets."""

    TARGET_ACCOUNT_CAPITAL = Decimal('30000')
    TARGET_MONTHLY_INCOME = Decimal('420')
    MAX_POSITION_PCT = Decimal('0.10')  # 10% per sleeve
    MIN_PROBABILITY = Decimal('65')
    MIN_FLOW_SCORE = Decimal('45')
    CREDIT_STRATEGIES = {
        'short_put',
        'covered_call',
        'bull_put_spread',
        'bear_call_spread',
        'iron_condor',
    }
    DEBIT_STRATEGIES = {
        'bull_call_spread',
        'bear_put_spread',
        'long_call',
        'long_put',
    }

    def __init__(self):
        super().__init__()
        self.whales_service = UnusualWhalesService()

    def recommend_allocations(
        self,
        suggestions: Iterable[Any],
        *,
        account_capital: Decimal | None = None,
        income_target: Decimal | None = None,
    ) -> Dict[str, Any]:
        """Return allocation plan for provided suggestions."""

        account_capital = Decimal(account_capital or self.TARGET_ACCOUNT_CAPITAL)
        income_target = Decimal(income_target or self.TARGET_MONTHLY_INCOME)

        suggestion_list = [s for s in suggestions if getattr(s, 'capital_required', None)]
        if not suggestion_list:
            return {
                'generated_at': timezone.now().isoformat(),
                'account_capital': account_capital,
                'income_target': income_target,
                'allocations': [],
                'totals': {
                    'capital': Decimal('0'),
                    'expected_income': Decimal('0'),
                    'positions': 0,
                },
                'meets_target': False,
                'notes': ['No suggestions available for allocation.'],
            }

        # Ensure flow data is available (uses internal caching to avoid duplicate hits)
        self._ensure_whales_metadata(suggestion_list)

        candidates = [
            self._build_candidate(suggestion, account_capital)
            for suggestion in suggestion_list
        ]

        # Sort: prefer UW 🟢, then AI score, then ROC
        candidates.sort(
            key=lambda item: (
                item['timing_rank'],
                item['scores']['ai'],
                item['scores']['roc'],
            ),
            reverse=True,
        )

        allocations: List[Dict[str, Any]] = []
        capital_remaining = account_capital
        per_position_cap = (account_capital * self.MAX_POSITION_PCT).quantize(Decimal('0.01'))
        expected_income_total = Decimal('0')

        used_symbols = set()

        for candidate in candidates:
            if candidate['symbol'] in used_symbols:
                continue

            required_capital = candidate['capital_required']
            if required_capital <= 0:
                continue

            if candidate['scores']['probability'] < self.MIN_PROBABILITY:
                continue

            if candidate['scores']['flow'] < self.MIN_FLOW_SCORE:
                continue

            if capital_remaining <= Decimal('0.00'):
                break

            allocation_cap = min(required_capital, per_position_cap, capital_remaining)
            scaling_factor = self._calculate_scaling_factor(required_capital, allocation_cap)
            if scaling_factor <= 0:
                continue
            if scaling_factor < Decimal('0.10'):
                # Skip extremely small fragments; better to find alternative idea
                continue

            expected_income = (candidate['expected_income'] * scaling_factor).quantize(Decimal('0.01'), ROUND_HALF_UP)
            if expected_income <= 0:
                # Allow debit strategies as diversification but with lower weight
                if candidate['is_debit']:
                    expected_income = (candidate['max_profit'] * Decimal('0.40') * scaling_factor).quantize(Decimal('0.01'), ROUND_HALF_UP)
                else:
                    continue

            capital_used = Decimal(allocation_cap).quantize(Decimal('0.01'), ROUND_HALF_UP)

            allocation = {
                'symbol': candidate['symbol'],
                'strategy': candidate['strategy'],
                'timing_signal': candidate['timing_signal'],
                'ai_score': candidate['scores']['ai'],
                'probability_of_profit': candidate['scores']['probability'],
                'flow_score': candidate['scores']['flow'],
                'capital_used': capital_used,
                'expected_income': expected_income,
                'scaling_factor': scaling_factor,
                'is_debit': candidate['is_debit'],
                'notes': candidate['notes'],
                'suggestion_id': candidate['suggestion_id'],
            }

            allocations.append(allocation)
            used_symbols.add(candidate['symbol'])
            capital_remaining = (capital_remaining - capital_used).quantize(Decimal('0.01'), ROUND_HALF_UP)
            expected_income_total += expected_income

            if expected_income_total >= income_target:
                break

        meets_target = expected_income_total >= income_target
        coverage_pct = (expected_income_total / income_target * 100).quantize(Decimal('0.01')) if income_target else Decimal('0')

        notes = []
        if not allocations:
            notes.append("No allocations met probability/flow thresholds.")
        elif not meets_target:
            notes.append("Income target not met — consider adding capital or approving more 🟢 flow positions.")

        return {
            'generated_at': timezone.now().isoformat(),
            'account_capital': account_capital,
            'income_target': income_target,
            'allocations': allocations,
            'totals': {
                'capital': sum(a['capital_used'] for a in allocations) if allocations else Decimal('0'),
                'expected_income': expected_income_total,
                'positions': len(allocations),
                'coverage_pct': coverage_pct,
            },
            'meets_target': meets_target,
            'notes': notes,
            'cache_stats': getattr(self.whales_service, 'last_fetch_stats', None),
        }

    def _ensure_whales_metadata(self, suggestions: List[Any]) -> None:
        symbols_missing = [
            s.symbol
            for s in suggestions
            if not ((s.api_response_data or {}).get('unusual_whales'))
        ]

        if not symbols_missing:
            return

        if not self.whales_service.is_enabled():
            logger.info("UW disabled; skipping flow enrichment for allocation plan")
            return

        unique_symbols = list(dict.fromkeys(symbols_missing))
        flow_map = self.whales_service.get_flow_summary_for_symbols(unique_symbols, max_symbols=len(unique_symbols))

        for suggestion in suggestions:
            flow_data = flow_map.get(str(suggestion.symbol).upper())
            if not flow_data:
                continue
            metadata = suggestion.api_response_data or {}
            metadata['unusual_whales'] = flow_data
            suggestion.api_response_data = metadata

    def _build_candidate(self, suggestion: Any, account_capital: Decimal) -> Dict[str, Any]:
        metadata = suggestion.api_response_data or {}
        whales_meta = metadata.get('unusual_whales', {})

        ai_score = Decimal(str(suggestion.ai_score or 50))
        probability = Decimal(str(suggestion.probability_of_profit or 0))
        flow_score = Decimal(str(whales_meta.get('flow_score') or 0))
        timing_signal = whales_meta.get('timing_signal') or self._derive_timing(flow_score)

        capital_required = Decimal(str(suggestion.capital_required or 0))
        premium_collected = Decimal(str(suggestion.premium_collected or 0))
        max_profit = Decimal(str(suggestion.max_profit or 0))

        roc = self._calculate_roc(max_profit, capital_required)

        expected_income = self._estimate_income(suggestion.strategy, premium_collected, max_profit)

        notes = []
        if premium_collected <= 0 and suggestion.strategy in self.CREDIT_STRATEGIES:
            notes.append('Premium missing — verify CSV values.')
        if suggestion.strategy in self.DEBIT_STRATEGIES and premium_collected > 0:
            notes.append('Check: debit strategy reported positive premium (expected debit).')

        timing_rank = 1 if '🟢' in timing_signal else 0
        if '🔴' in timing_signal:
            timing_rank = -1

        return {
            'suggestion_id': suggestion.id,
            'symbol': suggestion.symbol,
            'strategy': suggestion.get_strategy_display() if hasattr(suggestion, 'get_strategy_display') else suggestion.strategy,
            'capital_required': capital_required,
            'expected_income': expected_income,
            'max_profit': max_profit,
            'timing_signal': timing_signal,
            'timing_rank': timing_rank,
            'is_debit': suggestion.strategy in self.DEBIT_STRATEGIES,
            'scores': {
                'ai': ai_score,
                'probability': probability,
                'flow': flow_score,
                'roc': roc,
            },
            'notes': notes,
        }

    @staticmethod
    def _calculate_scaling_factor(required: Decimal, allowed: Decimal) -> Decimal:
        if required <= 0:
            return Decimal('0')
        factor = (allowed / required).quantize(Decimal('0.01'), ROUND_HALF_UP)
        return min(Decimal('1.00'), max(Decimal('0.00'), factor))

    @staticmethod
    def _calculate_roc(max_profit: Decimal, capital_required: Decimal) -> Decimal:
        if not capital_required or capital_required <= 0:
            return Decimal('0')
        return (max_profit / capital_required * 100).quantize(Decimal('0.01'), ROUND_HALF_UP)

    def _estimate_income(self, strategy: str, premium_collected: Decimal, max_profit: Decimal) -> Decimal:
        if strategy in self.CREDIT_STRATEGIES:
            return premium_collected
        if strategy in self.DEBIT_STRATEGIES:
            # Debit spreads: income realized if profit target hit — use 60% of max profit
            return max_profit * Decimal('0.60')
        # Default fallback: treat premium as income if positive
        return premium_collected if premium_collected > 0 else max_profit * Decimal('0.40')

    @staticmethod
    def _derive_timing(flow_score: Decimal) -> str:
        try:
            flow_value = Decimal(flow_score)
        except Exception:
            flow_value = Decimal('0')

        if flow_value >= 75:
            return '🟢 ENTER NOW (Flow-derived)'
        if flow_value >= 50:
            return '🟡 OK TO ENTER (Flow-derived)'
        return '🔴 WAIT/SKIP (Flow-derived)'


