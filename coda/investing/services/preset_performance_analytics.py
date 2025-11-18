"""
Preset Performance Analytics Service

Tracks performance of portfolio presets (Core Income, Balanced, Apex sleeves)
by linking SuggestedPosition → OptionsPosition → Outcomes.

Phase 4: Analytics & Feedback Loop
"""

import logging
from collections import defaultdict
from decimal import Decimal
from typing import Dict, List, Optional, Any
from datetime import date, timedelta

from django.db.models import (
    Count, Sum, Avg, Q, F, When, Case, Value, IntegerField, DecimalField
)
from django.utils import timezone

from ..models import (
    SuggestedPosition,
    OptionsPosition,
    OptionsPositionHistory,
)
from .portfolio_preset_service import PortfolioPresetBuilder

logger = logging.getLogger(__name__)


class PresetPerformanceAnalytics:
    """
    Analytics for portfolio preset performance.
    
    Tracks:
    - Preset-level win rates
    - Average returns per preset
    - Capital efficiency
    - Position count by preset
    """
    
    def __init__(self):
        self.preset_builder = PortfolioPresetBuilder()
    
    def get_preset_performance(
        self,
        days_back: int = 90,
        preset_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get performance metrics for portfolio presets.
        
        Args:
            days_back: How many days to look back
            preset_code: Optional filter to specific preset
            
        Returns:
            Dict with preset-level metrics
        """
        cutoff_date = timezone.now() - timedelta(days=days_back)
        
        # Get all positions that came from suggestions
        positions_qs = OptionsPosition.objects.filter(
            source_suggestion__isnull=False,
            entry_date__gte=cutoff_date.date(),
        ).select_related('source_suggestion', 'outcome_history')
        
        if preset_code:
            # Map preset_code to signal tier and score requirements
            preset_config = self._get_preset_config(preset_code)
            if preset_config:
                positions_qs = positions_qs.filter(
                    source_suggestion__signal_tier__in=preset_config.required_signal_tiers,
                    source_suggestion__ai_score__gte=preset_config.min_score,
                )
        
        # Group by preset (determine preset from suggestion metadata)
        preset_metrics = {}
        
        for position in positions_qs:
            suggestion = position.source_suggestion
            preset_name = self._determine_preset_from_suggestion(suggestion)
            
            if preset_name not in preset_metrics:
                preset_metrics[preset_name] = {
                    'preset_name': preset_name,
                    'total_positions': 0,
                    'closed_positions': 0,
                    'winning_positions': 0,
                    'losing_positions': 0,
                    'total_premium_collected': Decimal('0'),
                    'total_realized_pnl': Decimal('0'),
                    'total_capital_required': Decimal('0'),
                    'positions': [],
                }
            
            metrics = preset_metrics[preset_name]
            metrics['total_positions'] += 1
            metrics['total_premium_collected'] += position.premium_collected or Decimal('0')
            metrics['total_capital_required'] += position.capital_required or Decimal('0')
            
            if position.status == 'closed' and hasattr(position, 'outcome_history'):
                metrics['closed_positions'] += 1
                history = position.outcome_history
                
                if history.was_profitable:
                    metrics['winning_positions'] += 1
                else:
                    metrics['losing_positions'] += 1
                
                metrics['total_realized_pnl'] += history.actual_return_amount or Decimal('0')
                metrics['positions'].append({
                    'symbol': position.symbol,
                    'strategy': position.strategy,
                    'pnl': float(history.actual_return_amount or 0),
                    'roi': float(history.actual_return_percentage or 0),
                    'closed_at': position.exit_date,
                })
        
        # Calculate derived metrics
        for preset_name, metrics in preset_metrics.items():
            if metrics['closed_positions'] > 0:
                metrics['win_rate'] = (
                    metrics['winning_positions'] / metrics['closed_positions']
                ) * 100
                metrics['avg_pnl'] = (
                    metrics['total_realized_pnl'] / metrics['closed_positions']
                )
                metrics['avg_roi'] = (
                    sum(p['roi'] for p in metrics['positions']) / metrics['closed_positions']
                )
            else:
                metrics['win_rate'] = None
                metrics['avg_pnl'] = None
                metrics['avg_roi'] = None
            
            if metrics['total_capital_required'] > 0:
                metrics['capital_efficiency'] = (
                    metrics['total_realized_pnl'] / metrics['total_capital_required']
                ) * 100
            else:
                metrics['capital_efficiency'] = None
        
        return {
            'cutoff_date': cutoff_date.date(),
            'days_back': days_back,
            'presets': list(preset_metrics.values()),
        }
    
    def _determine_preset_from_suggestion(self, suggestion: SuggestedPosition) -> str:
        """
        Determine which preset a suggestion would belong to based on its metadata.
        
        Logic:
        - Apex tier + score >= 92 → Apex Aggressive
        - Strong tier + score >= 85 → Balanced
        - Others → Core Income
        """
        if suggestion.signal_tier == 'apex' and (
            suggestion.ai_score and suggestion.ai_score >= 92
        ):
            return 'Apex Aggressive'
        elif suggestion.signal_tier in ('apex', 'strong') and (
            suggestion.ai_score and suggestion.ai_score >= 85
        ):
            return 'Balanced Engine'
        else:
            return 'Core Income'
    
    def _get_preset_config(self, preset_code: str):
        """Get preset config by code."""
        for config in self.preset_builder.PRESETS:
            if config.code == preset_code:
                return config
        return None


class SignalTierAnalytics:
    """
    Analytics for signal tier performance (Apex, Strong, Watchlist).
    
    Tracks:
    - Win rate by tier
    - Average returns by tier
    - Conversion rate (suggestion → position)
    """
    
    def get_tier_performance(
        self,
        days_back: int = 90,
        tier: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get performance metrics by signal tier.
        
        Args:
            days_back: How many days to look back
            tier: Optional filter to specific tier ('apex', 'strong', 'watchlist')
            
        Returns:
            Dict with tier-level metrics
        """
        cutoff_date = timezone.now() - timedelta(days=days_back)
        
        # Suggestions
        suggestions_qs = SuggestedPosition.objects.filter(
            created_at__gte=cutoff_date,
            signal_tier__isnull=False,
        )
        
        if tier:
            suggestions_qs = suggestions_qs.filter(signal_tier=tier)
        
        # Positions created from suggestions
        positions_qs = OptionsPosition.objects.filter(
            source_suggestion__isnull=False,
            source_suggestion__signal_tier__isnull=False,
            entry_date__gte=cutoff_date.date(),
        ).select_related('source_suggestion', 'outcome_history')
        
        if tier:
            positions_qs = positions_qs.filter(source_suggestion__signal_tier=tier)
        
        tier_metrics = defaultdict(lambda: {
            'tier': None,
            'total_suggestions': 0,
            'converted_to_position': 0,
            'closed_positions': 0,
            'winning_positions': 0,
            'losing_positions': 0,
            'total_realized_pnl': Decimal('0'),
            'positions': [],
        })
        
        # Count suggestions by tier
        for suggestion in suggestions_qs:
            tier_name = suggestion.signal_tier or 'unknown'
            tier_metrics[tier_name]['tier'] = tier_name
            tier_metrics[tier_name]['total_suggestions'] += 1
        
        # Aggregate position outcomes
        for position in positions_qs:
            suggestion = position.source_suggestion
            tier_name = suggestion.signal_tier or 'unknown'
            
            tier_metrics[tier_name]['converted_to_position'] += 1
            
            if position.status == 'closed' and hasattr(position, 'outcome_history'):
                tier_metrics[tier_name]['closed_positions'] += 1
                history = position.outcome_history
                
                if history.was_profitable:
                    tier_metrics[tier_name]['winning_positions'] += 1
                else:
                    tier_metrics[tier_name]['losing_positions'] += 1
                
                tier_metrics[tier_name]['total_realized_pnl'] += (
                    history.actual_return_amount or Decimal('0')
                )
                tier_metrics[tier_name]['positions'].append({
                    'symbol': position.symbol,
                    'pnl': float(history.actual_return_amount or 0),
                    'roi': float(history.actual_return_percentage or 0),
                })
        
        # Calculate derived metrics
        result = []
        for tier_name, metrics in tier_metrics.items():
            metrics['conversion_rate'] = None
            if metrics['total_suggestions'] > 0:
                metrics['conversion_rate'] = (
                    metrics['converted_to_position'] / metrics['total_suggestions']
                ) * 100
            
            metrics['win_rate'] = None
            metrics['avg_pnl'] = None
            if metrics['closed_positions'] > 0:
                metrics['win_rate'] = (
                    metrics['winning_positions'] / metrics['closed_positions']
                ) * 100
                metrics['avg_pnl'] = (
                    metrics['total_realized_pnl'] / metrics['closed_positions']
                )
            
            result.append(metrics)
        
        return {
            'cutoff_date': cutoff_date.date(),
            'days_back': days_back,
            'tiers': result,
        }

