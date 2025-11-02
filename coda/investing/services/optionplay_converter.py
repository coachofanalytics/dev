"""
OptionPlay Raw Data Converter Service

Converts manually uploaded OptionPlay CSV data to SuggestedPosition format
Handles 3 CSV types: Credit Spreads, Short Puts, Covered Calls
"""

import logging
from decimal import Decimal
from datetime import datetime, timedelta
from typing import List, Dict
from django.utils import timezone

logger = logging.getLogger(__name__)


class OptionPlayConverterService:
    """
    Converts OptionPlayRawData to SuggestedPosition format
    
    Handles all 3 strategy types:
    - Credit Spreads (Bull Put, Bear Call)
    - Short Puts (Cash-Secured)
    - Covered Calls
    """
    
    def convert_raw_to_suggestion(self, raw_data):
        """
        Convert single OptionPlayRawData to SuggestedPosition
        
        Args:
            raw_data: OptionPlayRawData instance
        
        Returns:
            SuggestedPosition instance
        """
        from ..models import SuggestedPosition
        
        try:
            if raw_data.strategy_type == 'credit_spread':
                suggestion_data = self._convert_credit_spread(raw_data)
            elif raw_data.strategy_type == 'short_put':
                suggestion_data = self._convert_short_put(raw_data)
            elif raw_data.strategy_type == 'covered_call':
                suggestion_data = self._convert_covered_call(raw_data)
            else:
                raise ValueError(f"Unknown strategy type: {raw_data.strategy_type}")
            
            # Create SuggestedPosition
            suggestion = SuggestedPosition.objects.create(
                source='manual',  # From manual CSV upload
                **suggestion_data
            )
            
            # AI Scoring (NEW)
            self._score_position(suggestion, raw_data)
            
            # Mark raw data as processed
            raw_data.is_processed = True
            raw_data.processed_date = timezone.now()
            raw_data.created_suggestion = suggestion
            raw_data.save()
            
            logger.info(f"✅ Converted {raw_data.symbol} to SuggestedPosition #{suggestion.id} (AI Score: {suggestion.ai_score})")
            return suggestion
            
        except Exception as e:
            logger.error(f"❌ Error converting {raw_data.symbol}: {e}")
            raw_data.processing_error = str(e)
            raw_data.save()
            raise
    
    def _convert_credit_spread(self, raw_data) -> Dict:
        """
        Convert credit spread to SuggestedPosition format
        
        CSV: Symbol, Strategy, Type, Price, Sell Strike, Buy Strike, Expiry, Premium, Width, IV Rank
        Example: DIS, Bearish, Call, $101.50, $102.00, $107.00, 08/02/2024, $2.30, $5.00, 14%
        """
        # Determine strategy code
        if raw_data.spread_strategy == 'Bearish' and raw_data.option_type == 'Call':
            strategy = 'bear_call_spread'
            option_type_code = 'call'
        elif raw_data.spread_strategy == 'Bullish' and raw_data.option_type == 'Put':
            strategy = 'bull_put_spread'
            option_type_code = 'put'
        else:
            # Default fallback
            strategy = 'bull_put_spread'
            option_type_code = 'put'
        
        # Build position legs
        positions_data = [
            {
                'type': f'short_{option_type_code}',
                'strike': float(raw_data.sell_strike),
                'contracts': 1,
                'premium': float(raw_data.premium),
                'delta': -0.30 if strategy == 'bull_put_spread' else 0.30,
                'theta': 0.05
            },
            {
                'type': f'long_{option_type_code}',
                'strike': float(raw_data.buy_strike),
                'contracts': 1,
                'premium': 0,
                'delta': -0.10 if strategy == 'bull_put_spread' else 0.10,
                'theta': -0.02
            }
        ]
        
        # Calculate metrics
        width = raw_data.width or (abs(raw_data.sell_strike - raw_data.buy_strike))
        capital_required = width * 100  # Per contract
        premium_collected = raw_data.premium * 100
        max_profit = premium_collected
        max_loss = capital_required - max_profit
        
        # Calculate breakeven
        if strategy == 'bull_put_spread':
            breakeven = raw_data.sell_strike - raw_data.premium
        else:  # bear_call_spread
            breakeven = raw_data.sell_strike + raw_data.premium
        
        # Estimate probability of profit from IV Rank and distance
        iv_rank_value = float(raw_data.iv_rank or 50)
        prob_of_profit = min(70 + (iv_rank_value / 5), 85)  # 70-85% range
        
        return {
            'symbol': raw_data.symbol,
            'strategy': strategy,
            'positions': positions_data,
            'expiration_date': raw_data.expiry,
            'dte': raw_data.calculated_dte,
            'premium_collected': Decimal(str(premium_collected)),
            'capital_required': Decimal(str(capital_required)),
            'max_profit': Decimal(str(max_profit)),
            'max_loss': Decimal(str(max_loss)),
            'breakeven': Decimal(str(breakeven)),
            'probability_of_profit': Decimal(str(prob_of_profit)),
            'position_delta': Decimal('-0.20') if strategy == 'bull_put_spread' else Decimal('0.20'),
            'position_theta': Decimal('0.03'),
            'position_gamma': Decimal('0.01'),
            'position_vega': Decimal('-0.05'),
            'ai_confidence': Decimal(str(min(75 + (iv_rank_value / 5), 90))),
            'ai_reasoning': f"OptionPlay {strategy.replace('_', ' ').title()}. IV Rank: {iv_rank_value}%, Width: ${width}"
        }
    
    def _convert_short_put(self, raw_data) -> Dict:
        """
        Convert short put to SuggestedPosition format
        
        CSV: Symbol, Action, Expiry, Days To Expiry, Strike Price, Mid Price, Stock Price, 
             Raw Return, Annualized Return, Distance To Strike, IV Rank
        """
        strike = raw_data.sell_strike
        premium = raw_data.premium
        stock_price = raw_data.stock_price or strike  # Fallback if missing
        
        # Build position leg
        positions_data = [{
            'type': 'short_put',
            'strike': float(strike),
            'contracts': 1,
            'premium': float(premium),
            'delta': -0.30,
            'theta': 0.08
        }]
        
        # Calculate metrics
        capital_required = strike * 100  # Cash-secured
        premium_collected = premium * 100
        max_profit = premium_collected
        max_loss = capital_required - max_profit
        breakeven = strike - premium
        
        # Probability from distance to strike
        distance = raw_data.distance_to_strike or Decimal('0')
        # More negative distance = further OTM = higher probability
        prob_of_profit = min(70 + abs(float(distance)) / 2, 85)
        
        return {
            'symbol': raw_data.symbol,
            'strategy': 'short_put',
            'positions': positions_data,
            'expiration_date': raw_data.expiry,
            'dte': raw_data.calculated_dte,
            'premium_collected': Decimal(str(premium_collected)),
            'capital_required': Decimal(str(capital_required)),
            'max_profit': Decimal(str(max_profit)),
            'max_loss': Decimal(str(max_loss)),
            'breakeven': Decimal(str(breakeven)),
            'probability_of_profit': Decimal(str(prob_of_profit)),
            'position_delta': Decimal('-0.30'),
            'position_theta': Decimal('0.08'),
            'position_gamma': Decimal('0.02'),
            'position_vega': Decimal('-0.10'),
            'ai_confidence': Decimal(str(min(75 + float(raw_data.annualized_return or 0) / 10, 90))),
            'ai_reasoning': f"OptionPlay Short Put. Strike: ${strike}, Premium: ${premium}, Return: {raw_data.raw_return}%"
        }
    
    def _convert_covered_call(self, raw_data) -> Dict:
        """
        Convert covered call to SuggestedPosition format
        
        CSV: Similar to short puts but for calls on owned stock
        """
        strike = raw_data.sell_strike
        premium = raw_data.premium
        stock_price = raw_data.stock_price or strike
        
        # Build position legs
        positions_data = [
            {
                'type': 'long_stock',
                'strike': float(stock_price),
                'contracts': 100,  # 100 shares
                'premium': 0,
                'delta': 1.00,
                'theta': 0
            },
            {
                'type': 'short_call',
                'strike': float(strike),
                'contracts': 1,
                'premium': float(premium),
                'delta': 0.30,
                'theta': 0.08
            }
        ]
        
        # Calculate metrics
        capital_required = stock_price * 100  # Buy 100 shares
        premium_collected = premium * 100
        max_profit = premium_collected + ((strike - stock_price) * 100 if strike > stock_price else 0)
        max_loss = capital_required - premium_collected
        breakeven = stock_price - premium
        
        return {
            'symbol': raw_data.symbol,
            'strategy': 'covered_call',
            'positions': positions_data,
            'expiration_date': raw_data.expiry,
            'dte': raw_data.calculated_dte,
            'premium_collected': Decimal(str(premium_collected)),
            'capital_required': Decimal(str(capital_required)),
            'max_profit': Decimal(str(max_profit)),
            'max_loss': Decimal(str(max_loss)),
            'breakeven': Decimal(str(breakeven)),
            'probability_of_profit': Decimal('70.0'),
            'position_delta': Decimal('0.70'),
            'position_theta': Decimal('0.08'),
            'position_gamma': Decimal('-0.02'),
            'position_vega': Decimal('-0.10'),
            'ai_confidence': Decimal('75.0'),
            'ai_reasoning': f"OptionPlay Covered Call. Stock: ${stock_price}, Strike: ${strike}, Premium: ${premium}"
        }
    
    def bulk_convert(self, queryset, filters: Dict = None) -> List:
        """
        Convert multiple OptionPlayRawData to SuggestedPositions
        
        Args:
            queryset: QuerySet of OptionPlayRawData
            filters: Optional filters to apply BEFORE conversion:
                {
                    'min_premium': 100,  # Minimum $100 premium
                    'min_iv_rank': 20,   # Minimum 20% IV rank
                    'dte_min': 30,       # Minimum 30 DTE
                    'dte_max': 60,       # Maximum 60 DTE
                    'max_positions': 10, # Limit conversions
                    'symbols': ['AAPL', 'MSFT', ...]  # Specific symbols only
                }
        
        Returns:
            List of created SuggestedPosition instances
        """
        suggestions = []
        errors = []
        skipped = []
        
        # Apply filters BEFORE conversion
        if filters:
            queryset = self._apply_filters_to_raw_data(queryset, filters)
        
        for raw_data in queryset:
            try:
                # Additional validation before conversion
                if not self._should_convert(raw_data, filters):
                    skipped.append(f"{raw_data.symbol}: Filtered out")
                    continue
                
                suggestion = self.convert_raw_to_suggestion(raw_data)
                suggestions.append(suggestion)
                
            except Exception as e:
                errors.append(f"{raw_data.symbol}: {str(e)}")
                logger.error(f"❌ Conversion failed for {raw_data.symbol}: {e}")
        
        logger.info(f"✅ Converted {len(suggestions)} positions, {len(errors)} errors, {len(skipped)} filtered out")
        return suggestions, errors
    
    def _apply_filters_to_raw_data(self, queryset, filters: Dict):
        """Apply filters to raw data queryset before conversion"""
        filtered = queryset
        
        # Filter by premium
        if 'min_premium' in filters:
            min_prem = Decimal(str(filters['min_premium']))
            filtered = filtered.filter(premium__gte=min_prem)
        
        # Filter by IV rank
        if 'min_iv_rank' in filters:
            min_iv = Decimal(str(filters['min_iv_rank']))
            filtered = filtered.filter(iv_rank__gte=min_iv)
        
        # Filter by symbols (whitelist)
        if 'symbols' in filters and filters['symbols']:
            filtered = filtered.filter(symbol__in=filters['symbols'])
        
        # Limit number
        if 'max_positions' in filters:
            filtered = filtered[:filters['max_positions']]
        
        return filtered
    
    def _should_convert(self, raw_data, filters: Dict = None) -> bool:
        """
        Validate if raw data should be converted
        
        Checks:
        - Not expired
        - DTE in range
        - Meets quality thresholds
        """
        # Check expiration
        if raw_data.is_expired:
            return False
        
        # Check DTE range
        if filters:
            dte = raw_data.calculated_dte
            dte_min = filters.get('dte_min', 0)
            dte_max = filters.get('dte_max', 999)
            
            if not (dte_min <= dte <= dte_max):
                return False
        
        # Quality checks
        # Avoid extremely low premiums (< $0.50)
        if raw_data.premium < Decimal('0.50'):
            return False
        
        # Avoid penny stocks for spreads (stock price < $10)
        if raw_data.stock_price and raw_data.stock_price < Decimal('10.00'):
            if raw_data.strategy_type in ['credit_spread', 'covered_call']:
                return False
        
        return True
    
    def _score_position(self, suggestion, raw_data=None):
        """
        Score SuggestedPosition using AI Position Scoring Service
        
        Args:
            suggestion: SuggestedPosition instance
            raw_data: Optional OptionPlayRawData for additional context
        """
        from investing.services.position_scoring_service import PositionScoringService
        
        try:
            scorer = PositionScoringService()
            
            # Build position data dict for scoring
            position_data = {
                'symbol': suggestion.symbol,
                'strategy': suggestion.get_strategy_display(),  # Human-readable
                'premium': suggestion.premium_collected or Decimal('0'),
                'max_loss': suggestion.max_loss or Decimal('1'),
                'dte': suggestion.dte,
                'iv_rank': raw_data.iv_rank if raw_data else None,
                'days_to_earnings': None,  # TODO: integrate earnings calendar
                'volume': None,  # TODO: integrate market data API
                'open_interest': None,
            }
            
            # Get AI score
            score_result = scorer.score_position(position_data)
            
            # Update suggestion with AI scoring
            suggestion.ai_score = score_result['score']
            suggestion.ai_rating = score_result['rating']
            # Convert Decimal to float for JSON serialization
            suggestion.ai_breakdown = {k: float(v) for k, v in score_result['breakdown'].items()}
            suggestion.ai_recommendation = score_result['recommendation']
            suggestion.ai_confidence_level = score_result['confidence']
            suggestion.save()
            
            logger.info(f"  🤖 AI Scored: {score_result['score']}/100 ({score_result['rating']})")
            
        except Exception as e:
            logger.error(f"  ❌ AI Scoring failed for {suggestion.symbol}: {e}")
            # Don't fail the entire conversion if scoring fails
            pass

