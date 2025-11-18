from __future__ import annotations

import logging
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Dict, Any, List

from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class SignalValidationService:
    """
    Lightweight validation/sanitization for fetched suggestion payloads.

    Ensures the core metrics we rely on (probability, DTE, capital, greeks)
    are present, properly typed, and within reasonable bounds before the
    records ever touch the database.
    """

    REQUIRED_FIELDS = [
        "symbol",
        "strategy",
        "positions",
        "expiration_date",
        "dte",
        "premium_collected",
        "capital_required",
        "max_profit",
        "max_loss",
        "probability_of_profit",
    ]

    DECIMAL_FIELDS = [
        "premium_collected",
        "capital_required",
        "max_profit",
        "max_loss",
        "breakeven",
        "probability_of_profit",
        "position_delta",
        "position_theta",
        "position_gamma",
        "position_vega",
        "ai_confidence",
    ]

    def clean_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate mandatory attributes and coerce all numeric values to Decimal.
        Raises ValidationError when a violation is detected.
        """
        missing = [field for field in self.REQUIRED_FIELDS if field not in payload]
        if missing:
            raise ValidationError(f"Missing required fields: {', '.join(missing)}")

        cleaned = payload.copy()
        cleaned["symbol"] = str(cleaned["symbol"]).upper().strip()
        cleaned["strategy"] = str(cleaned["strategy"]).lower().strip()

        positions = cleaned.get("positions") or []
        if not isinstance(positions, list) or not positions:
            raise ValidationError("positions must be a non-empty list")
        cleaned["positions"] = positions

        cleaned["expiration_date"] = self._coerce_date(cleaned["expiration_date"])

        dte = int(cleaned["dte"])
        if dte <= 0 or dte > 120:
            raise ValidationError(f"DTE out of bounds: {dte}")
        cleaned["dte"] = dte

        for field in self.DECIMAL_FIELDS:
            if field not in cleaned or cleaned[field] in (None, ""):
                continue
            cleaned[field] = self._coerce_decimal(field, cleaned[field])

        prob = cleaned["probability_of_profit"]
        if prob < Decimal("0") or prob > Decimal("100"):
            raise ValidationError(f"Probability of profit out of bounds: {prob}")

        premium = cleaned["premium_collected"]
        capital = cleaned["capital_required"]
        max_profit = cleaned["max_profit"]
        max_loss = cleaned["max_loss"]

        for name, value in [
            ("premium_collected", premium),
            ("capital_required", capital),
            ("max_profit", max_profit),
        ]:
            if value < Decimal("0"):
                raise ValidationError(f"{name} cannot be negative")

        if max_loss >= Decimal("0"):
            # We typically store losses as positive numbers (absolute exposure)
            pass
        else:
            cleaned["max_loss"] = abs(max_loss)

        return cleaned

    def _coerce_date(self, value: Any) -> date:
        if isinstance(value, date):
            return value
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, str):
            value = value.strip()
            for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    continue
        raise ValidationError(f"Invalid expiration_date: {value!r}")

    def _coerce_decimal(self, field: str, value: Any) -> Decimal:
        try:
            return Decimal(str(value))
        except (InvalidOperation, TypeError):
            raise ValidationError(f"Invalid decimal for {field}: {value!r}")




