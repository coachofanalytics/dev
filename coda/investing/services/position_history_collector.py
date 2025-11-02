"""
Position History Collector Service
Automatically tracks closed positions for ML training

Purpose:
- Auto-populate OptionsPositionHistory when positions close
- Capture entry/exit conditions
- Generate AI post-analysis
- Build ML training dataset

Usage:
    # Called automatically via signal when position closes
    from investing.services.position_history_collector import PositionHistoryCollector
    
    collector = PositionHistoryCollector()
    history = collector.collect_from_position(position)

Architecture:
- Reuses InvestmentAnalytics pattern (proven)
- Integrates with existing AI services
- Signal-based automation (no manual calls needed)

Author: CODA Development Team
Created: November 2, 2025
Part of: AI Position Scoring System (Week 1)
"""

from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
import logging

logger = logging.getLogger(__name__)


class PositionHistoryCollector:
    """
    Collects historical data from closed positions
    
    Workflow:
    1. Position closes (status='closed')
    2. Signal triggers collector
    3. Calculate outcome metrics
    4. Capture entry conditions
    5. Generate AI analysis
    6. Save to OptionsPositionHistory
    
    ML Features Captured:
    - Symbol win rate
    - Strategy effectiveness
    - IV rank patterns
    - Market conditions
    - Earnings correlation
    """
    
    def collect_from_position(self, position):
        """
        Create OptionsPositionHistory record from closed position
        
        Args:
            position: OptionsPosition instance (must be closed)
            
        Returns:
            OptionsPositionHistory instance
            
        Raises:
            ValueError: If position not closed
        """
        from investing.models import OptionsPositionHistory
        
        if position.status != 'closed':
            raise ValueError(f"Position {position.id} is not closed (status={position.status})")
        
        # Check if history already exists (avoid duplicates)
        if hasattr(position, 'outcome_history'):
            logger.warning(f"Position {position.id} already has outcome history - skipping")
            return position.outcome_history
        
        logger.info(f"📊 Collecting history for position {position.id} ({position.symbol})")
        
        # Calculate outcome metrics
        outcome_metrics = self._calculate_outcome_metrics(position)
        
        # Capture entry conditions (for ML)
        entry_conditions = self._get_entry_conditions(position)
        
        # Determine exit reason
        exit_reason = self._determine_exit_reason(position)
        
        # Generate AI analysis (if available)
        ai_analysis = self._generate_ai_analysis(position, outcome_metrics)
        
        # Create history record
        with transaction.atomic():
            history = OptionsPositionHistory.objects.create(
                position=position,
                
                # Outcome
                was_profitable=outcome_metrics['was_profitable'],
                actual_return_amount=outcome_metrics['return_amount'],
                actual_return_percentage=outcome_metrics['return_percentage'],
                annualized_return=outcome_metrics['annualized_return'],
                days_held=outcome_metrics['days_held'],
                
                # Exit
                exit_reason=exit_reason,
                exit_notes=outcome_metrics.get('exit_notes', ''),
                exit_stock_price=outcome_metrics.get('exit_stock_price'),
                max_profit_captured=outcome_metrics.get('max_profit_captured'),
                
                # Entry conditions (ML features)
                entry_iv_rank=entry_conditions.get('iv_rank'),
                entry_market_trend=entry_conditions.get('market_trend'),
                entry_vix=entry_conditions.get('vix'),
                entry_stock_price=entry_conditions.get('stock_price'),
                days_to_earnings=entry_conditions.get('days_to_earnings'),
                
                # AI
                ai_post_analysis=ai_analysis,
                ai_confidence_at_entry=entry_conditions.get('ai_confidence'),
            )
        
        logger.info(f"✅ Created history for {position.symbol}: "
                   f"{'WIN' if history.was_profitable else 'LOSS'} "
                   f"({history.actual_return_percentage}% ROI)")
        
        return history
    
    def _calculate_outcome_metrics(self, position):
        """Calculate return metrics"""
        # P&L
        realized_pnl = position.realized_pnl or Decimal('0')
        capital_required = position.capital_required or Decimal('1')  # Avoid division by zero
        
        # ROI
        return_percentage = (realized_pnl / capital_required) * Decimal('100')
        
        # Days held
        if position.exit_date and position.entry_date:
            days_held = (position.exit_date - position.entry_date).days
        else:
            days_held = 1  # Default to avoid division by zero
        
        # Annualized return
        if days_held > 0:
            annualized_return = (return_percentage * Decimal('365')) / Decimal(str(days_held))
        else:
            annualized_return = return_percentage
        
        # Max profit captured (for credit spreads)
        max_profit_captured = None
        if position.premium_collected and position.premium_collected > 0:
            # For credit strategies: max profit = premium collected
            # % captured = (premium - exit cost) / premium
            exit_premium = position.exit_premium or Decimal('0')
            profit_captured = ((position.premium_collected - exit_premium) / position.premium_collected) * Decimal('100')
            max_profit_captured = min(profit_captured, Decimal('100'))  # Cap at 100%
        
        return {
            'was_profitable': realized_pnl > 0,
            'return_amount': realized_pnl,
            'return_percentage': return_percentage,
            'annualized_return': annualized_return,
            'days_held': days_held,
            'exit_stock_price': None,  # TODO: Fetch from price API
            'max_profit_captured': max_profit_captured,
            'exit_notes': position.notes or ''
        }
    
    def _get_entry_conditions(self, position):
        """
        Capture market conditions at entry time
        
        ML Features:
        - IV rank (volatility level)
        - Market trend (bullish/bearish)
        - VIX level (market fear gauge)
        - Stock price
        - Days to earnings
        """
        conditions = {}
        
        # IV Rank (if available from position or batch)
        if hasattr(position, 'iv_rank') and position.iv_rank:
            conditions['iv_rank'] = position.iv_rank
        elif hasattr(position, 'batch') and position.batch and hasattr(position.batch, 'avg_iv_rank'):
            conditions['iv_rank'] = position.batch.avg_iv_rank
        
        # Market trend (simple heuristic for now - TODO: integrate market data API)
        conditions['market_trend'] = self._estimate_market_trend(position)
        
        # VIX (TODO: fetch from market data API)
        conditions['vix'] = None
        
        # Stock price at entry
        conditions['stock_price'] = None  # TODO: fetch from price history
        
        # Days to earnings (TODO: integrate earnings calendar)
        conditions['days_to_earnings'] = None
        
        # AI confidence (if position was scored)
        if hasattr(position, 'ai_score') and position.ai_score:
            conditions['ai_confidence'] = position.ai_score
        
        return conditions
    
    def _estimate_market_trend(self, position):
        """
        Estimate market trend based on position type
        
        Heuristic (until we integrate market data API):
        - Bull Put Spread → bullish
        - Bear Call Spread → bearish
        - Iron Condor → neutral
        """
        strategy = position.strategy.lower() if position.strategy else ''
        
        if 'bull' in strategy or 'short put' in strategy:
            return 'bullish'
        elif 'bear' in strategy or 'short call' in strategy:
            return 'bearish'
        elif 'iron condor' in strategy or 'strangle' in strategy:
            return 'neutral'
        else:
            return 'neutral'
    
    def _determine_exit_reason(self, position):
        """Determine why position was closed"""
        # Check if hit profit target (closed early with good profit)
        if position.realized_pnl and position.realized_pnl > 0:
            if position.exit_date and position.expiration_date:
                days_before_expiry = (position.expiration_date - position.exit_date).days
                if days_before_expiry > 5:  # Closed >5 days before expiration
                    return 'profit_target'
        
        # Check if hit stop loss
        if position.realized_pnl and position.realized_pnl < 0:
            return 'stop_loss'
        
        # Check if held to expiration
        if position.exit_date and position.expiration_date:
            if (position.expiration_date - position.exit_date).days <= 1:
                return 'expiration'
        
        # Default
        return 'early_close'
    
    def _generate_ai_analysis(self, position, outcome_metrics):
        """
        Generate AI post-analysis of trade outcome
        
        Analysis includes:
        - Why position won/lost
        - Key factors that contributed
        - Lessons learned
        - Pattern recognition
        
        TODO: Integrate with RealAIService for GPT-4 analysis
        """
        was_profitable = outcome_metrics['was_profitable']
        roi = outcome_metrics['return_percentage']
        days_held = outcome_metrics['days_held']
        
        # Simple template for now (TODO: replace with GPT-4)
        if was_profitable:
            if roi > 30:
                analysis = (f"🎯 EXCELLENT TRADE: {roi:.1f}% return in {days_held} days. "
                          f"Position closed profitably, likely due to favorable market movement "
                          f"and high IV rank. Strategy ({position.strategy}) was well-suited for conditions.")
            elif roi > 15:
                analysis = (f"✅ GOOD TRADE: {roi:.1f}% return. "
                          f"Position performed as expected. {position.strategy} strategy effective.")
            else:
                analysis = (f"✓ PROFITABLE: {roi:.1f}% return. "
                          f"Small profit captured. May have closed early or held through challenges.")
        else:
            analysis = (f"❌ LOSS: {roi:.1f}% return. "
                      f"Position closed at loss. Likely due to adverse market movement, "
                      f"low IV, or poor timing. Review entry conditions for this symbol.")
        
        # Add strategy-specific notes
        if 'spread' in position.strategy.lower():
            analysis += f" Credit spread collected ${position.premium_collected or 0:.2f} premium."
        
        return analysis
    
    def bulk_collect(self, positions_queryset):
        """
        Bulk collect history for multiple positions
        
        Args:
            positions_queryset: QuerySet of closed OptionsPosition instances
            
        Returns:
            dict: {'created': count, 'skipped': count, 'errors': count}
        """
        from investing.models import OptionsPosition
        
        results = {'created': 0, 'skipped': 0, 'errors': 0}
        
        # Filter to only closed positions without history
        closed_positions = positions_queryset.filter(
            status='closed'
        ).exclude(
            outcome_history__isnull=False
        )
        
        logger.info(f"📊 Bulk collecting history for {closed_positions.count()} positions")
        
        for position in closed_positions:
            try:
                self.collect_from_position(position)
                results['created'] += 1
            except Exception as e:
                logger.error(f"Error collecting history for position {position.id}: {e}")
                results['errors'] += 1
        
        logger.info(f"✅ Bulk collection complete: {results}")
        return results
    
    def get_symbol_win_rate(self, symbol):
        """
        Calculate historical win rate for a symbol
        
        Args:
            symbol: Stock ticker (e.g., 'AAPL')
            
        Returns:
            dict: {
                'win_rate': Decimal,  # 0-100%
                'total_trades': int,
                'wins': int,
                'losses': int,
                'avg_return': Decimal
            }
        """
        from investing.models import OptionsPositionHistory
        from django.db.models import Avg, Count
        
        histories = OptionsPositionHistory.objects.filter(
            position__symbol=symbol
        )
        
        total = histories.count()
        if total == 0:
            return {
                'win_rate': Decimal('0'),
                'total_trades': 0,
                'wins': 0,
                'losses': 0,
                'avg_return': Decimal('0')
            }
        
        wins = histories.filter(was_profitable=True).count()
        losses = total - wins
        win_rate = (Decimal(str(wins)) / Decimal(str(total))) * Decimal('100')
        
        avg_return = histories.aggregate(
            avg=Avg('actual_return_percentage')
        )['avg'] or Decimal('0')
        
        return {
            'win_rate': win_rate,
            'total_trades': total,
            'wins': wins,
            'losses': losses,
            'avg_return': Decimal(str(avg_return))
        }
    
    def get_strategy_win_rate(self, strategy):
        """Calculate historical win rate for a strategy"""
        from investing.models import OptionsPositionHistory
        from django.db.models import Avg
        
        histories = OptionsPositionHistory.objects.filter(
            position__strategy__icontains=strategy
        )
        
        total = histories.count()
        if total == 0:
            return {'win_rate': Decimal('0'), 'total_trades': 0}
        
        wins = histories.filter(was_profitable=True).count()
        win_rate = (Decimal(str(wins)) / Decimal(str(total))) * Decimal('100')
        
        return {
            'win_rate': win_rate,
            'total_trades': total,
            'wins': wins
        }

