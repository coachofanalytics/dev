import logging
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from django.contrib.postgres.aggregates import ArrayAgg
from django.core.exceptions import FieldDoesNotExist
from django.db.models import Avg, Count, F, Max, Q
from django.utils import timezone

from ..models import SuggestedPosition, SuggestedPositionOutcome

logger = logging.getLogger(__name__)


STRATEGY_BUCKET_MAP = {
    'bull_put_spread': 'credit_spreads',
    'bear_call_spread': 'credit_spreads',
    'iron_condor': 'credit_spreads',
    'short_put': 'credit_spreads',
    'short_call': 'credit_spreads',
    'covered_call': 'covered_calls',
    'covered_call_earnings': 'covered_calls',
    'bull_call_spread': 'leaps',
    'long_call': 'leaps',
    'long_put': 'leaps',
}


@dataclass
class OverlapSummary:
    optionplay_total: int
    whales_total: int
    overlap_count: int
    overlap_ratio: Decimal
    primary_symbols: List[Tuple[str, int]]


@dataclass
class RotationSnapshot:
    mix: Dict[str, int]
    mix_ratio: Dict[str, Decimal]
    top_symbols: List[Tuple[str, int]]
    suggested_target_variance: Dict[str, Decimal]


@dataclass
class OutcomeSnapshot:
    total: int
    win_rate: Optional[Decimal]
    loss_rate: Optional[Decimal]
    breakeven_rate: Optional[Decimal]
    by_bucket: Dict[str, Dict[str, Optional[Decimal]]]


@dataclass
class StreakSnapshot:
    repeating_symbols: List[Tuple[str, int]]
    average_streak: Optional[Decimal]
    max_streak: int


class StrategyInsightsService:
    """
    Generates aggregated insights that feed Phase 3 (strategy overlap discovery)
    and Phase 4 (portfolio presentation) without duplicating existing dashboards.
    """

    DEFAULT_ROTATION_TARGETS = {
        'credit_spreads': Decimal('0.60'),
        'covered_calls': Decimal('0.30'),
        'leaps': Decimal('0.10'),
    }

    def __init__(self, lookback_days: int = 7, as_of=None):
        self.as_of = as_of or timezone.now()
        self.window_start = self.as_of - timedelta(days=lookback_days)
        self.lookback_days = lookback_days

    # ------------------------------------------------------------------ HELPERS
    def _base_suggestions(self):
        return SuggestedPosition.objects.filter(
            fetched_at__gte=self.window_start
        )

    def _active_suggestions(self):
        return self._base_suggestions().filter(
            review_status__in=['pending', 'approved', 'modified']
        )

    def _bucket_for_position(self, suggestion: SuggestedPosition) -> str:
        strategy_key = (suggestion.strategy or '').lower()
        bucket = STRATEGY_BUCKET_MAP.get(strategy_key, 'other')
        if bucket == 'leaps' and suggestion.dte and suggestion.dte < 60:
            # Long-dated criteria not met; treat as credit spread substitute
            return 'credit_spreads'

        if bucket == 'other' and suggestion.dte and suggestion.dte >= 60:
            return 'leaps'

        return bucket

    # --------------------------------------------------------------- OVERLAP
    def calculate_overlap(self) -> OverlapSummary:
        qs = self._base_suggestions()
        optionplay_total = qs.filter(source='optionplay').count()
        whales_total = qs.filter(source='unusual_whales').count()

        combo_rows = qs.values('symbol', 'strategy', 'expiration_date').annotate(
            sources=ArrayAgg('source', distinct=True),
            latest_fetched=Max('fetched_at'),
        )

        overlap_count = 0
        symbol_counter = Counter()
        for row in combo_rows:
            source_set = set(row['sources'] or [])
            if {'optionplay', 'unusual_whales'}.issubset(source_set):
                overlap_count += 1
                symbol_counter[row['symbol']] += 1

        overlap_ratio = Decimal('0')
        denominator = max(optionplay_total, 1)
        if overlap_count:
            overlap_ratio = (Decimal(overlap_count) / Decimal(denominator)).quantize(Decimal('0.01'))

        top_symbols = symbol_counter.most_common(10)

        return OverlapSummary(
            optionplay_total=optionplay_total,
            whales_total=whales_total,
            overlap_count=overlap_count,
            overlap_ratio=overlap_ratio,
            primary_symbols=top_symbols,
        )

    # --------------------------------------------------------------- ROTATION
    def build_rotation_snapshot(self) -> RotationSnapshot:
        qs = self._active_suggestions().filter(ai_rating__in=['EXCELLENT', 'GOOD'])
        bucket_counts = Counter()
        symbol_frequency = Counter()

        for suggestion in qs.iterator():
            bucket = self._bucket_for_position(suggestion)
            bucket_counts[bucket] += 1
            symbol_frequency[suggestion.symbol] += 1

        total = sum(bucket_counts.values()) or 1
        mix_ratio = {
            bucket: (Decimal(count) / Decimal(total)).quantize(Decimal('0.01'))
            for bucket, count in bucket_counts.items()
        }

        variance = {}
        for bucket, target_ratio in self.DEFAULT_ROTATION_TARGETS.items():
            actual_ratio = mix_ratio.get(bucket, Decimal('0'))
            variance[bucket] = (actual_ratio - target_ratio).quantize(Decimal('0.01'))

        return RotationSnapshot(
            mix=dict(bucket_counts),
            mix_ratio=mix_ratio,
            top_symbols=symbol_frequency.most_common(10),
            suggested_target_variance=variance,
        )

    # --------------------------------------------------------------- OUTCOMES
    def build_outcome_snapshot(self) -> OutcomeSnapshot:
        qs = SuggestedPositionOutcome.objects.filter(
            evaluated_at__gte=self.window_start
        )
        total = qs.count()
        if not total:
            return OutcomeSnapshot(total=0, win_rate=None, loss_rate=None, breakeven_rate=None, by_bucket={})

        status_counts = qs.values('status').annotate(count=Count('id'))
        status_lookup = {row['status']: row['count'] for row in status_counts}

        win_rate = self._calculate_ratio(status_lookup.get('won', 0), total)
        loss_rate = self._calculate_ratio(status_lookup.get('lost', 0), total)
        breakeven_rate = self._calculate_ratio(status_lookup.get('breakeven', 0), total)

        bucket_breakdown: Dict[str, Dict[str, Optional[Decimal]]] = defaultdict(dict)

        for bucket, strategies in self._bucket_strategies().items():
            bucket_qs = qs.filter(strategy__in=strategies)
            bucket_count = bucket_qs.count()
            if not bucket_count:
                continue
            bucket_status_counts = bucket_qs.values('status').annotate(count=Count('id'))
            bucket_lookup = {row['status']: row['count'] for row in bucket_status_counts}
            bucket_breakdown[bucket] = {
                'count': bucket_count,
                'win_rate': self._calculate_ratio(bucket_lookup.get('won', 0), bucket_count),
                'loss_rate': self._calculate_ratio(bucket_lookup.get('lost', 0), bucket_count),
                'breakeven_rate': self._calculate_ratio(bucket_lookup.get('breakeven', 0), bucket_count),
            }

        return OutcomeSnapshot(
            total=total,
            win_rate=win_rate,
            loss_rate=loss_rate,
            breakeven_rate=breakeven_rate,
            by_bucket=dict(bucket_breakdown),
        )

    def _bucket_strategies(self) -> Dict[str, List[str]]:
        buckets = defaultdict(list)
        for strategy, bucket in STRATEGY_BUCKET_MAP.items():
            buckets[bucket].append(strategy)
        return buckets

    # --------------------------------------------------------------- STREAKS
    def build_streak_snapshot(self) -> StreakSnapshot:
        if not self._has_field('consistency_streak'):
            logger.warning("consistency_streak field missing; returning empty streak snapshot")
            return StreakSnapshot(repeating_symbols=[], average_streak=None, max_streak=0)

        qs = self._base_suggestions().filter(consistency_streak__gt=1)
        if not qs.exists():
            return StreakSnapshot(repeating_symbols=[], average_streak=None, max_streak=0)

        streak_values = qs.values_list('consistency_streak', flat=True)
        total_streaks = sum(streak_values)
        count = len(streak_values)
        average_streak = (Decimal(total_streaks) / Decimal(count)).quantize(Decimal('0.01')) if count else None
        max_streak = max(streak_values) if streak_values else 0

        symbol_counts = Counter()
        for suggestion in qs.iterator():
            symbol_counts[suggestion.symbol] += 1

        return StreakSnapshot(
            repeating_symbols=symbol_counts.most_common(10),
            average_streak=average_streak,
            max_streak=max_streak,
        )

    # --------------------------------------------------------------- REPORT
    def build_report(self) -> Dict:
        overlap = self.calculate_overlap()
        rotation = self.build_rotation_snapshot()
        outcomes = self.build_outcome_snapshot()
        streaks = self.build_streak_snapshot()

        logger.info("Strategy insights generated for lookback=%s days", self.lookback_days)

        return {
            'generated_at': self.as_of,
            'window_start': self.window_start,
            'lookback_days': self.lookback_days,
            'overlap': overlap,
            'rotation': rotation,
            'outcomes': outcomes,
            'streaks': streaks,
        }

    # --------------------------------------------------------------- UTILITIES
    @staticmethod
    def _calculate_ratio(numerator: int, denominator: int) -> Optional[Decimal]:
        if not denominator:
            return None
        return (Decimal(numerator) / Decimal(denominator)).quantize(Decimal('0.01'))

    @staticmethod
    def _has_field(field_name: str) -> bool:
        try:
            SuggestedPosition._meta.get_field(field_name)
            return True
        except FieldDoesNotExist:
            return False

