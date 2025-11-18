from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from typing import List, Dict, Any, Iterable

from django.db.models import QuerySet

from .position_ranking_service import PositionRankingService

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PortfolioPresetConfig:
    code: str
    name: str
    target_tier: str
    description: str
    max_positions: int
    capital_cap: Decimal
    min_probability: Decimal
    min_score: Decimal
    dte_range: tuple[int, int]
    strategy_whitelist: tuple[str, ...]
    required_signal_tiers: tuple[str, ...]


class PortfolioPresetBuilder:
    """
    Groups ranked suggestions into ready-to-run sleeves for each plan tier.
    """

    PRESETS: tuple[PortfolioPresetConfig, ...] = (
        PortfolioPresetConfig(
            code="core_income",
            name="Core Income Sleeve",
            target_tier="consultative",
            description="High-probability income spreads for premium managed accounts.",
            max_positions=5,
            capital_cap=Decimal("75000"),  # Updated to match Consultative capital req
            min_probability=Decimal("70"),
            min_score=Decimal("85"),
            dte_range=(28, 55),
            strategy_whitelist=("bull_put_spread", "short_put", "covered_call"),
            required_signal_tiers=("strong", "apex"),
        ),
        PortfolioPresetConfig(
            code="balanced_engine",
            name="Balanced Automation Sleeve",
            target_tier="balanced",
            description="Diverse mix of income + momentum with capped exposure.",
            max_positions=4,
            capital_cap=Decimal("45000"),
            min_probability=Decimal("70"),
            min_score=Decimal("82"),
            dte_range=(28, 60),
            strategy_whitelist=("bull_put_spread", "bear_call_spread", "short_put"),
            required_signal_tiers=("strong", "apex"),
        ),
        PortfolioPresetConfig(
            code="apex_aggressive",
            name="Apex Momentum Sleeve",
            target_tier="elite",
            description="Tactical trades with highest AI score for Elite automation tier.",
            max_positions=5,
            capital_cap=Decimal("50000"),  # Updated to match Elite capital req
            min_probability=Decimal("65"),
            min_score=Decimal("85"),
            dte_range=(21, 50),
            strategy_whitelist=("bull_put_spread", "bear_call_spread", "iron_condor", "strangle"),
            required_signal_tiers=("apex", "strong"),
        ),
    )

    def __init__(self):
        self.ranker = PositionRankingService()

    def build_presets(
        self,
        pending_suggestions: QuerySet | Iterable,
        *,
        pre_ranked: List[Dict[str, Any]] | None = None,
    ) -> List[Dict[str, Any]]:
        ranked = pre_ranked or self.ranker.rank_positions(pending_suggestions)
        presets = []
        for config in self.PRESETS:
            portfolio = self._select_for_preset(ranked, config)
            presets.append(portfolio)
        return presets

    def _select_for_preset(
        self,
        ranked_positions: List[Dict[str, Any]],
        config: PortfolioPresetConfig,
    ) -> Dict[str, Any]:
        selected = []
        capital = Decimal("0")
        coverage = defaultdict(int)
        symbol_counts = defaultdict(int)  # Track symbol occurrences for diversification

        for item in ranked_positions:
            suggestion = item["position"]

            if len(selected) >= config.max_positions:
                break

            if suggestion.signal_tier not in config.required_signal_tiers:
                continue

            if suggestion.strategy not in config.strategy_whitelist:
                continue

            prob = suggestion.probability_of_profit or Decimal("0")
            if prob < config.min_probability:
                continue

            if item["total_score"] < config.min_score:
                continue

            dte = suggestion.dte or 0
            if not (config.dte_range[0] <= dte <= config.dte_range[1]):
                continue

            capital_required = suggestion.capital_required or Decimal("0")
            if capital + capital_required > config.capital_cap:
                continue

            # Symbol diversification: Limit to 1 occurrence per symbol (max 2 for larger presets)
            max_symbol_count = 1 if config.max_positions <= 3 else 2
            if symbol_counts[suggestion.symbol] >= max_symbol_count:
                continue

            selected.append({
                "suggestion": suggestion,
                "score": item["total_score"],
                "rank": item["rank"],
                "capital": capital_required,
                "premium": suggestion.premium_collected or Decimal("0"),
            })
            capital += capital_required
            coverage[suggestion.strategy] += 1
            symbol_counts[suggestion.symbol] += 1

        total_premium = sum(pos["premium"] for pos in selected)
        avg_dte = (
            sum((pos["suggestion"].dte or 0) for pos in selected) / len(selected)
            if selected else 0
        )

        slots_remaining = max(0, config.max_positions - len(selected))

        return {
            "config": config,
            "positions": selected,
            "total_capital": capital,
            "total_premium": total_premium,
            "avg_dte": avg_dte,
            "coverage": dict(coverage),
            "is_complete": len(selected) == config.max_positions,
            "slots_remaining": slots_remaining,
        }

