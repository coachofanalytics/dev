"""
Predictive analytics utilities for managed options accounts.

Phase 4 enhancement: provide short-term balance forecasts using Prophet when
available, with a deterministic fallback when the dependency is absent.
"""

from __future__ import annotations

import logging
from datetime import timedelta
from decimal import Decimal, DecimalException
from typing import Dict, Iterable, List

from django.utils import timezone

from .base_service import BaseInvestingService
from ..models import ManagedTradingAccount, OptionsPositionHistory

logger = logging.getLogger(__name__)


class PredictiveAnalyticsService(BaseInvestingService):
    """
    Generates account-level forecasts from historical position outcomes.

    The service attempts to use Facebook/Meta Prophet if installed. When the
    dependency is unavailable (local dev, CI), it automatically falls back to a
    lightweight rolling-average projection so that analytics pages still render.
    """

    def __init__(self):
        super().__init__()
        self._prophet_cls = None
        self._pd = None
        try:
            from prophet import Prophet
            import pandas as pd
        except ImportError:  # pragma: no cover - dependency optional
            logger.debug("Prophet not available; falling back to simple forecast.")
        else:
            self._prophet_cls = Prophet
            self._pd = pd

    @property
    def supports_prophet(self) -> bool:
        return self._prophet_cls is not None and self._pd is not None

    def forecast_account_balance(
        self,
        account: ManagedTradingAccount,
        periods: int = 30,
    ) -> Dict[str, Iterable[Dict[str, object]]]:
        """
        Generate a balance projection for the specified managed account.

        Returns a dictionary containing historic series and forecast series.
        """
        history_qs = OptionsPositionHistory.objects.filter(
            position__managed_account=account,
            position__exit_date__isnull=False,
        ).select_related('position').order_by('position__exit_date')

        if history_qs.count() < 3:
            raise ValueError("Not enough closed positions to generate a forecast.")

        history_data = [
            {
                'ds': row.position.exit_date,
                'y': float(row.actual_return_amount),
            }
            for row in history_qs
        ]

        if self.supports_prophet:
            try:
                return self._build_prophet_forecast(history_data, periods)
            except Exception as exc:  # pragma: no cover - Prophet edge case
                logger.warning("Prophet forecast failed, falling back. %s", exc)

        return self._build_fallback_forecast(history_data, account, periods)

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _build_prophet_forecast(
        self,
        history_data: List[Dict[str, object]],
        periods: int,
    ) -> Dict[str, Iterable[Dict[str, object]]]:
        pd = self._pd  # type: ignore[assignment]
        df = pd.DataFrame(history_data)
        df['ds'] = pd.to_datetime(df['ds'])

        model = self._prophet_cls()
        model.fit(df)

        future = model.make_future_dataframe(periods=periods)
        forecast = model.predict(future)

        latest_history = df[['ds', 'y']].to_dict('records')
        forecast_records = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(periods).to_dict('records')

        return {
            'history': latest_history,
            'forecast': forecast_records,
            'uses_prophet': True,
        }

    def _build_fallback_forecast(
        self,
        history_data: List[Dict[str, object]],
        account: ManagedTradingAccount,
        periods: int,
    ) -> Dict[str, Iterable[Dict[str, object]]]:
        """
        Simple deterministic fallback based on average per-position return.
        """
        total_return = sum(self._to_decimal(item['y']) for item in history_data)
        avg_per_trade = total_return / Decimal(len(history_data))
        last_date = history_data[-1]['ds']
        if not isinstance(last_date, timezone.datetime) and hasattr(last_date, 'toordinal'):
            last_date = timezone.datetime.combine(last_date, timezone.datetime.min.time())

        history_records = history_data
        forecast_records: List[Dict[str, object]] = []
        running_balance = Decimal(account.current_balance or 0)

        for day in range(1, periods + 1):
            running_balance += avg_per_trade / Decimal(30)  # approximate daily drift
            forecast_date = last_date + timedelta(days=day)
            forecast_records.append({
                'ds': forecast_date.date(),
                'yhat': float(running_balance),
                'yhat_lower': float(running_balance * Decimal('0.97')),
                'yhat_upper': float(running_balance * Decimal('1.03')),
            })

        return {
            'history': history_records,
            'forecast': forecast_records,
            'uses_prophet': False,
        }

    def _to_decimal(self, value) -> Decimal:
        try:
            return Decimal(str(value))
        except (DecimalException, TypeError, ValueError):
            return Decimal('0')

