"""
OptionPlay Outcome Service

Evaluates historical outcomes for SuggestedPosition ideas so that we can
produce data-backed win rates for Balanced/Elite plan messaging.
"""

import logging
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from typing import Dict, Iterable, Optional, Tuple

import yfinance as yf
from django.db import transaction
from django.utils import timezone

from ..models import SuggestedPosition, SuggestedPositionOutcome

logger = logging.getLogger(__name__)


@dataclass
class PriceSample:
    symbol: str
    price: Decimal
    pricing_date: timezone.datetime


class PriceProvider:
    """Simple interface so we can swap providers in tests."""

    def get_close_price(self, symbol: str, expiration_date) -> Optional[PriceSample]:
        raise NotImplementedError


class YFinancePriceProvider(PriceProvider):
    """Default implementation using yfinance daily close data."""

    def get_close_price(self, symbol: str, expiration_date) -> Optional[PriceSample]:
        try:
            # yfinance needs an end date that is AFTER the target date
            start_date = expiration_date
            end_date = expiration_date + timedelta(days=2)
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=start_date, end=end_date)
            if hist.empty:
                return None
            close_value = hist['Close'].iloc[-1]
            price = Decimal(str(round(close_value, 2)))
            # yfinance returns timezone-aware pandas timestamps; use the index
            pricing_timestamp = hist.index[-1].to_pydatetime()
            return PriceSample(symbol=symbol, price=price, pricing_date=pricing_timestamp)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("💾 yfinance lookup failed for %s (%s)", symbol, exc)
            return None


class OptionPlayOutcomeService:
    """
    Converts expired SuggestedPosition ideas into outcome records by evaluating
    the legs against the underlying close price.
    """

    SUPPORTED_LEG_TYPES = {'short_put', 'long_put', 'short_call', 'long_call'}

    def __init__(self, price_provider: Optional[PriceProvider] = None):
        self.price_provider = price_provider or YFinancePriceProvider()

    # ------------------------------------------------------------------ PUBLIC
    def evaluate_pending(self, as_of=None) -> Dict[str, int]:
        """
        Evaluate all expired suggestions without an outcome.

        Returns summary counts for reporting.
        """
        today = as_of or timezone.now().date()
        pending = SuggestedPosition.objects.filter(
            expiration_date__lt=today,
            outcome_record__isnull=True,
            source__in=['optionplay', 'unusual_whales']
        )

        summary = {
            'evaluated': 0,
            'created': 0,
            'errors': 0,
            'unsupported': 0,
        }

        for suggestion in pending.iterator():
            summary['evaluated'] += 1
            try:
                outcome = self.evaluate_suggestion(suggestion)
                if outcome is None:
                    summary['unsupported'] += 1
                else:
                    summary['created'] += 1
            except Exception as exc:  # pragma: no cover - defensive logging
                summary['errors'] += 1
                logger.exception("Outcome evaluation failed for suggestion %s: %s", suggestion.id, exc)

        return summary

    @transaction.atomic
    def evaluate_suggestion(self, suggestion: SuggestedPosition) -> Optional[SuggestedPositionOutcome]:
        """
        Evaluate a single suggestion. Returns the outcome instance or None if
        the strategy is unsupported.
        """
        if suggestion.outcome_record_id:
            return suggestion.outcome_record

        positions = suggestion.positions or []
        if not self._supports_positions(positions):
            logger.debug(
                "Skipping outcome for suggestion %s (%s) – unsupported leg types",
                suggestion.id, suggestion.strategy
            )
            return None

        price_sample = self.price_provider.get_close_price(suggestion.symbol, suggestion.expiration_date)
        if not price_sample:
            return self._create_outcome(
                suggestion=suggestion,
                status='error',
                notes='Unable to fetch underlying close price',
                data_snapshot={'positions': positions},
            )

        pnl = self._calculate_pnl(positions, price_sample.price)
        if pnl is None:
            return self._create_outcome(
                suggestion=suggestion,
                status='error',
                notes='Could not compute P&L for leg configuration',
                data_snapshot={
                    'positions': positions,
                    'close_price': str(price_sample.price),
                },
            )

        return_pct = None
        try:
            if suggestion.capital_required:
                return_pct = (pnl / suggestion.capital_required) * Decimal('100')
        except (InvalidOperation, ZeroDivisionError):
            return_pct = None

        status = self._determine_status(pnl)
        return self._create_outcome(
            suggestion=suggestion,
            status=status,
            pnl=pnl,
            return_pct=return_pct,
            price_sample=price_sample,
            data_snapshot={
                'positions': positions,
                'close_price': str(price_sample.price),
            }
        )

    # ----------------------------------------------------------------- HELPERS
    def _create_outcome(
        self,
        *,
        suggestion: SuggestedPosition,
        status: str,
        notes: str = '',
        pnl: Optional[Decimal] = None,
        return_pct: Optional[Decimal] = None,
        price_sample: Optional[PriceSample] = None,
        data_snapshot: Optional[Dict] = None,
    ) -> SuggestedPositionOutcome:
        outcome = SuggestedPositionOutcome.objects.create(
            suggestion=suggestion,
            source=suggestion.source,
            symbol=suggestion.symbol,
            strategy=suggestion.strategy,
            expiration_date=suggestion.expiration_date,
            premium_collected=suggestion.premium_collected,
            capital_required=suggestion.capital_required,
            probability_of_profit=suggestion.probability_of_profit,
            status=status,
            calculation_notes=notes,
            data_snapshot=data_snapshot or {},
        )

        if price_sample:
            outcome.underlying_close = price_sample.price
            outcome.evaluated_at = price_sample.pricing_date
        else:
            outcome.evaluated_at = timezone.now()

        if pnl is not None:
            outcome.realized_pnl = pnl.quantize(Decimal('0.01'))
        if return_pct is not None:
            outcome.return_pct = return_pct.quantize(Decimal('0.01'))

        outcome.save()
        return outcome

    def _supports_positions(self, positions: Iterable[Dict]) -> bool:
        if not positions:
            return False
        return all(leg.get('type') in self.SUPPORTED_LEG_TYPES for leg in positions)

    def _calculate_pnl(self, positions: Iterable[Dict], underlying_price: Decimal) -> Optional[Decimal]:
        total_pnl = Decimal('0')
        try:
            for leg in positions:
                total_pnl += self._leg_pnl(leg, underlying_price)
            return total_pnl
        except (InvalidOperation, KeyError, TypeError) as exc:
            logger.debug("P&L calculation error: %s", exc)
            return None

    def _leg_pnl(self, leg: Dict, underlying_price: Decimal) -> Decimal:
        leg_type = leg.get('type')
        strike = Decimal(str(leg.get('strike')))
        premium = Decimal(str(leg.get('premium', 0)))
        contracts = Decimal(str(leg.get('contracts', 1)))

        option_intrinsic = Decimal('0')
        if 'call' in leg_type:
            option_intrinsic = max(Decimal('0'), underlying_price - strike)
        elif 'put' in leg_type:
            option_intrinsic = max(Decimal('0'), strike - underlying_price)

        option_intrinsic *= Decimal('100') * contracts
        premium_value = premium * Decimal('100') * contracts

        if leg_type.startswith('short'):
            return premium_value - option_intrinsic
        else:
            return option_intrinsic - premium_value

    def _determine_status(self, pnl: Decimal) -> str:
        threshold = Decimal('0.50')  # $0.50 threshold to treat as breakeven
        if pnl >= threshold:
            return 'won'
        if pnl <= -threshold:
            return 'lost'
        return 'breakeven'





