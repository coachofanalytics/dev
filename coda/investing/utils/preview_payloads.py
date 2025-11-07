"""Utility helpers for building preview payloads without hitting the database."""

from typing import Iterable, Any, Dict


def _safe_number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return value


def _normalize_legs(legs_payload):
    if not legs_payload:
        return []
    normalized = []
    for leg in legs_payload:
        normalized.append({
            'type': leg.get('type') or leg.get('leg_type'),
            'direction': leg.get('direction'),
            'contracts': leg.get('contracts'),
            'strike': _safe_number(leg.get('strike')),
            'expiration': leg.get('expiration') or leg.get('expiry'),
            'premium': _safe_number(leg.get('premium')),
            'delta': _safe_number(leg.get('delta')),
            'theta': _safe_number(leg.get('theta')),
        })
    return normalized


def build_preview_payloads(pending_queryset: Iterable[Any], approved_queryset: Iterable[Any]) -> Dict[int, Dict[str, Any]]:
    preview_payloads = {}
    for position in list(pending_queryset) + list(approved_queryset):
        metadata = getattr(position, 'api_response_data', {}) or {}
        whales_meta = metadata.get('unusual_whales') or {}
        preview_payloads[position.id] = {
            'id': position.id,
            'symbol': position.symbol,
            'strategy': position.get_strategy_display() if hasattr(position, 'get_strategy_display') else getattr(position, 'strategy', ''),
            'raw_strategy': getattr(position, 'strategy', None),
            'probability': float(getattr(position, 'probability_of_profit', 0) or 0),
            'ai_score': float(getattr(position, 'ai_score', 0) or 0),
            'premium_collected': float(getattr(position, 'premium_collected', 0) or 0),
            'capital_required': float(getattr(position, 'capital_required', 0) or 0),
            'max_profit': float(getattr(position, 'max_profit', 0) or 0),
            'max_loss': float(getattr(position, 'max_loss', 0) or 0),
            'dte': getattr(position, 'dte', None),
            'timing_signal': whales_meta.get('timing_signal'),
            'flow_score': whales_meta.get('flow_score'),
            'sentiment': whales_meta.get('sentiment'),
            'notes': getattr(position, 'notes', '') or '',
            'legs': _normalize_legs(getattr(position, 'positions', [])),
        }
    return preview_payloads


__all__ = ['build_preview_payloads']

