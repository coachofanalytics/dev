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
            
            # Mark raw data as processed
            raw_data.is_processed = True
            raw_data.processed_date = timezone.now()
            raw_data.created_suggestion = suggestion
            raw_data.save()
            
            logger.info(f"✅ Converted {raw_data.symbol} to SuggestedPosition #{suggestion.id}")
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
    
    def bulk_convert(self, queryset) -> List:
        """
        Convert multiple OptionPlayRawData to SuggestedPositions
        
        Args:
            queryset: QuerySet of OptionPlayRawData
        
        Returns:
            List of created SuggestedPosition instances
        """
        suggestions = []
        errors = []
        
        for raw_data in queryset:
            try:
                suggestion = self.convert_raw_to_suggestion(raw_data)
                suggestions.append(suggestion)
            except Exception as e:
                errors.append(f"{raw_data.symbol}: {str(e)}")
                logger.error(f"❌ Conversion failed for {raw_data.symbol}: {e}")
        
        logger.info(f"✅ Converted {len(suggestions)} positions, {len(errors)} errors")
        return suggestions, errors

