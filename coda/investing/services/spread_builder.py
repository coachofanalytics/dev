"""
Automatic Spread Builder Service

Converts single-leg positions to multi-leg credit spreads for better risk management:
- Short Put → Bull Put Spread (vertical credit spread)
- Covered Call → Bear Call Spread (if no stock) OR keeps as Covered Call
- Credit Spreads from CSV → Import as-is

Strategy:
1. Detect single-leg vs multi-leg from CSV
2. For single-leg: Calculate optimal protective leg
3. Create spread with ideal width based on IV, Greeks, liquidity
4. Reduce capital requirements while maintaining profit potential
"""

import logging
from decimal import Decimal
from datetime import date, timedelta
from typing import Dict, List, Tuple, Optional
from django.db.models import Q

logger = logging.getLogger(__name__)


class SpreadBuilderService:
    """
    Automatically converts single-leg positions to spreads
    """
    
    # Spread width strategies
    SPREAD_WIDTH_STRATEGIES = {
        'tight': {
            'width_multiplier': 1.0,  # 1x strike width
            'description': 'Tight spread (higher win rate, lower profit)',
        },
        'balanced': {
            'width_multiplier': 2.0,  # 2x strike width
            'description': 'Balanced risk/reward',
        },
        'wide': {
            'width_multiplier': 3.0,  # 3x strike width
            'description': 'Wide spread (lower win rate, higher profit)',
        },
        'auto': {
            'width_multiplier': None,  # Calculate based on IV/Greeks
            'description': 'AI-optimized width based on IV rank and liquidity',
        }
    }
    
    def __init__(self):
        self.logger = logger
    
    def should_convert_to_spread(self, raw_position: Dict, strategy_type: str, account_info: Optional[Dict] = None) -> bool:
        """
        Determine if a single-leg position should be converted to a spread
        
        Args:
            raw_position: Position data from CSV
            strategy_type: 'short_put', 'covered_call', 'credit_spread', etc.
            account_info: Optional account info (to check if stock is owned for covered calls)
        
        Returns:
            True if should convert to spread, False otherwise
        """
        # Already a spread - don't convert
        if strategy_type in ['bull_put_spread', 'bear_call_spread', 'iron_condor']:
            self.logger.info(f"   ℹ️  {raw_position.get('symbol')}: Already a spread - no conversion needed")
            return False
        
        # Short puts - always convert to bull put spread (unless user overrides)
        if strategy_type == 'short_put':
            self.logger.info(f"   💡 {raw_position.get('symbol')}: Short Put → Will convert to Bull Put Spread")
            return True
        
        # Covered calls - convert to bear call spread if no stock owned
        if strategy_type == 'covered_call':
            symbol = raw_position.get('symbol')
            
            # Check if account owns stock (if account_info provided)
            if account_info and 'stock_positions' in account_info:
                owns_stock = symbol in account_info['stock_positions']
                if owns_stock:
                    self.logger.info(f"   ✅ {symbol}: Owns stock - Keep as Covered Call")
                    return False
                else:
                    self.logger.info(f"   💡 {symbol}: No stock owned → Convert to Bear Call Spread")
                    return True
            else:
                # No account info - assume no stock, convert to spread
                self.logger.info(f"   💡 {symbol}: Account info not available → Convert to Bear Call Spread (safer)")
                return True
        
        # Other strategies - don't convert
        return False
    
    def calculate_optimal_spread_width(
        self, 
        sell_strike: Decimal, 
        iv_rank: Optional[Decimal], 
        dte: int,
        underlying_price: Optional[Decimal],
        width_strategy: str = 'auto'
    ) -> Decimal:
        """
        Calculate optimal spread width based on market conditions
        
        Args:
            sell_strike: Strike price of the short leg
            iv_rank: Implied volatility rank (0-1)
            dte: Days to expiration
            underlying_price: Current price of underlying
            width_strategy: 'tight', 'balanced', 'wide', or 'auto'
        
        Returns:
            Optimal spread width (distance between strikes)
        """
        # Default width: 5 points for equities, scaled for index options
        if underlying_price and underlying_price > 500:
            # High-priced stocks (like SPX, TSLA) - wider strikes
            base_width = Decimal('10')
        elif underlying_price and underlying_price < 50:
            # Low-priced stocks - tighter strikes
            base_width = Decimal('2.5')
        else:
            # Most stocks
            base_width = Decimal('5')
        
        # Apply strategy multiplier
        if width_strategy in ['tight', 'balanced', 'wide']:
            multiplier = Decimal(str(self.SPREAD_WIDTH_STRATEGIES[width_strategy]['width_multiplier']))
            width = base_width * multiplier
        elif width_strategy == 'auto':
            # AI-optimized width based on IV rank and DTE
            multiplier = Decimal('1.5')  # Start with balanced
            
            # High IV → wider spread (capture more premium)
            if iv_rank and iv_rank > Decimal('0.7'):
                multiplier += Decimal('0.5')
                self.logger.debug(f"      High IV ({iv_rank*100:.0f}%) → +0.5x width")
            
            # Low IV → tighter spread (higher win rate)
            elif iv_rank and iv_rank < Decimal('0.3'):
                multiplier -= Decimal('0.3')
                self.logger.debug(f"      Low IV ({iv_rank*100:.0f}%) → -0.3x width")
            
            # Short DTE (<21 days) → tighter spread
            if dte < 21:
                multiplier -= Decimal('0.2')
                self.logger.debug(f"      Short DTE ({dte}d) → -0.2x width")
            
            # Long DTE (>45 days) → wider spread
            elif dte > 45:
                multiplier += Decimal('0.2')
                self.logger.debug(f"      Long DTE ({dte}d) → +0.2x width")
            
            width = base_width * multiplier
        else:
            width = base_width
        
        # Round to nearest standard strike width ($2.50 or $5)
        if width < Decimal('5'):
            width = Decimal('2.5')
        elif width < Decimal('10'):
            width = Decimal('5')
        else:
            width = (width / Decimal('5')).quantize(Decimal('1')) * Decimal('5')
        
        self.logger.info(f"   📏 Spread width: ${width} (strategy: {width_strategy})")
        return width
    
    def build_bull_put_spread(
        self,
        short_put_data: Dict,
        spread_width: Decimal,
        protective_leg_premium: Optional[Decimal] = None
    ) -> Dict:
        """
        Convert Short Put → Bull Put Spread (vertical credit spread)
        
        Structure:
        - SELL Put at higher strike (same as original short put)
        - BUY Put at lower strike (protective leg)
        
        Args:
            short_put_data: Original short put data
            spread_width: Distance between strikes
            protective_leg_premium: Premium paid for long put (estimated if not provided)
        
        Returns:
            Spread position data
        """
        symbol = short_put_data.get('symbol')
        sell_strike = Decimal(str(short_put_data.get('strike', 0)))
        sell_premium = Decimal(str(short_put_data.get('premium', 0)))
        expiration = short_put_data.get('expiry')
        quantity = int(short_put_data.get('quantity', 1))
        
        # Calculate protective leg strike
        buy_strike = sell_strike - spread_width
        
        # Estimate protective leg premium if not provided
        # Rule of thumb: Long leg costs ~30-40% of short leg premium for typical width
        if protective_leg_premium is None:
            protective_leg_premium = sell_premium * Decimal('0.35')
        
        # Net credit = Premium received - Premium paid
        net_credit = (sell_premium - protective_leg_premium) * Decimal(str(quantity)) * Decimal('100')
        
        # Max loss = Spread width - Net credit
        max_loss = (spread_width * Decimal(str(quantity)) * Decimal('100')) - net_credit
        
        # Capital required = Max loss (for spread)
        capital_required = max_loss
        
        self.logger.info(f"   📊 {symbol} Bull Put Spread:")
        self.logger.info(f"      SELL {quantity} Put @ ${sell_strike} for ${sell_premium}")
        self.logger.info(f"      BUY  {quantity} Put @ ${buy_strike} for ${protective_leg_premium}")
        self.logger.info(f"      Net Credit: ${net_credit:.2f}")
        self.logger.info(f"      Max Loss: ${max_loss:.2f}")
        self.logger.info(f"      Capital: ${capital_required:.2f} (vs ${sell_strike * Decimal(str(quantity)) * Decimal('100'):.2f} for naked put)")
        
        spread_data = {
            'symbol': symbol,
            'strategy': 'bull_put_spread',
            'positions': [
                {
                    'leg_type': 'short',
                    'option_type': 'put',
                    'strike': float(sell_strike),
                    'premium': float(sell_premium),
                    'quantity': quantity,
                },
                {
                    'leg_type': 'long',
                    'option_type': 'put',
                    'strike': float(buy_strike),
                    'premium': float(protective_leg_premium),
                    'quantity': quantity,
                }
            ],
            'expiration_date': expiration,
            'premium_collected': float(net_credit),
            'max_profit': float(net_credit),
            'max_loss': float(max_loss),
            'capital_required': float(capital_required),
            'width': float(spread_width),
            'conversion_note': f'Auto-converted from Short Put to Bull Put Spread (${spread_width} width)',
        }
        
        return spread_data
    
    def build_bear_call_spread(
        self,
        short_call_data: Dict,
        spread_width: Decimal,
        protective_leg_premium: Optional[Decimal] = None
    ) -> Dict:
        """
        Convert Short Call → Bear Call Spread (vertical credit spread)
        
        Structure:
        - SELL Call at lower strike (same as original short call)
        - BUY Call at higher strike (protective leg)
        
        Args:
            short_call_data: Original short call/covered call data
            spread_width: Distance between strikes
            protective_leg_premium: Premium paid for long call (estimated if not provided)
        
        Returns:
            Spread position data
        """
        symbol = short_call_data.get('symbol')
        sell_strike = Decimal(str(short_call_data.get('strike', 0)))
        sell_premium = Decimal(str(short_call_data.get('premium', 0)))
        expiration = short_call_data.get('expiry')
        quantity = int(short_call_data.get('quantity', 1))
        
        # Calculate protective leg strike
        buy_strike = sell_strike + spread_width
        
        # Estimate protective leg premium if not provided
        if protective_leg_premium is None:
            protective_leg_premium = sell_premium * Decimal('0.35')
        
        # Net credit = Premium received - Premium paid
        net_credit = (sell_premium - protective_leg_premium) * Decimal(str(quantity)) * Decimal('100')
        
        # Max loss = Spread width - Net credit
        max_loss = (spread_width * Decimal(str(quantity)) * Decimal('100')) - net_credit
        
        # Capital required = Max loss
        capital_required = max_loss
        
        self.logger.info(f"   📊 {symbol} Bear Call Spread:")
        self.logger.info(f"      SELL {quantity} Call @ ${sell_strike} for ${sell_premium}")
        self.logger.info(f"      BUY  {quantity} Call @ ${buy_strike} for ${protective_leg_premium}")
        self.logger.info(f"      Net Credit: ${net_credit:.2f}")
        self.logger.info(f"      Max Loss: ${max_loss:.2f}")
        self.logger.info(f"      Capital: ${capital_required:.2f}")
        
        spread_data = {
            'symbol': symbol,
            'strategy': 'bear_call_spread',
            'positions': [
                {
                    'leg_type': 'short',
                    'option_type': 'call',
                    'strike': float(sell_strike),
                    'premium': float(sell_premium),
                    'quantity': quantity,
                },
                {
                    'leg_type': 'long',
                    'option_type': 'call',
                    'strike': float(buy_strike),
                    'premium': float(protective_leg_premium),
                    'quantity': quantity,
                }
            ],
            'expiration_date': expiration,
            'premium_collected': float(net_credit),
            'max_profit': float(net_credit),
            'max_loss': float(max_loss),
            'capital_required': float(capital_required),
            'width': float(spread_width),
            'conversion_note': f'Auto-converted from Short Call to Bear Call Spread (${spread_width} width)',
        }
        
        return spread_data
    
    def convert_position_to_spread(
        self,
        raw_position: Dict,
        strategy_type: str,
        spread_width_strategy: str = 'auto',
        account_info: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Main entry point: Convert single-leg position to spread
        
        Args:
            raw_position: CSV row data
            strategy_type: Position strategy type
            spread_width_strategy: 'tight', 'balanced', 'wide', or 'auto'
            account_info: Optional account data for covered call decisions
        
        Returns:
            Spread position data or None if no conversion needed
        """
        symbol = raw_position.get('symbol')
        self.logger.info(f"🔄 Analyzing {symbol} ({strategy_type})...")
        
        # Check if conversion needed
        if not self.should_convert_to_spread(raw_position, strategy_type, account_info):
            return None
        
        # Calculate optimal spread width
        sell_strike = Decimal(str(raw_position.get('strike', 0)))
        iv_rank = Decimal(str(raw_position.get('iv_rank', 0.5))) if raw_position.get('iv_rank') else None
        dte = int(raw_position.get('dte', 30))
        underlying_price = Decimal(str(raw_position.get('underlying_price', 0))) if raw_position.get('underlying_price') else None
        
        spread_width = self.calculate_optimal_spread_width(
            sell_strike=sell_strike,
            iv_rank=iv_rank,
            dte=dte,
            underlying_price=underlying_price,
            width_strategy=spread_width_strategy
        )
        
        # Build appropriate spread
        if strategy_type == 'short_put':
            return self.build_bull_put_spread(raw_position, spread_width)
        
        elif strategy_type in ['short_call', 'covered_call']:
            return self.build_bear_call_spread(raw_position, spread_width)
        
        else:
            self.logger.warning(f"   ⚠️  Unknown strategy type: {strategy_type}")
            return None
    
    def batch_convert_positions(
        self,
        positions: List[Dict],
        strategy_type: str,
        spread_width_strategy: str = 'auto',
        account_info: Optional[Dict] = None
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Convert multiple positions to spreads in batch
        
        Args:
            positions: List of position data dicts
            strategy_type: Strategy type for all positions
            spread_width_strategy: Width strategy to use
            account_info: Optional account info
        
        Returns:
            Tuple of (converted_spreads, unchanged_positions)
        """
        converted = []
        unchanged = []
        
        self.logger.info("=" * 80)
        self.logger.info("🔄 SPREAD BUILDER: Converting single-leg positions to spreads")
        self.logger.info("=" * 80)
        self.logger.info(f"📊 Total positions: {len(positions)}")
        self.logger.info(f"📈 Strategy type: {strategy_type}")
        self.logger.info(f"📏 Spread width strategy: {spread_width_strategy}")
        self.logger.info("")
        
        for idx, position in enumerate(positions, 1):
            symbol = position.get('symbol', f'Position {idx}')
            
            try:
                spread_data = self.convert_position_to_spread(
                    position,
                    strategy_type,
                    spread_width_strategy,
                    account_info
                )
                
                if spread_data:
                    converted.append(spread_data)
                    self.logger.info(f"   ✅ Converted to {spread_data['strategy']}")
                else:
                    unchanged.append(position)
                    self.logger.info(f"   ➡️  Keeping as {strategy_type}")
                
                self.logger.info("")  # Blank line between positions
                
            except Exception as e:
                self.logger.error(f"   ❌ Error converting {symbol}: {e}")
                unchanged.append(position)  # Keep original if conversion fails
        
        self.logger.info("=" * 80)
        self.logger.info(f"✅ Conversion complete:")
        self.logger.info(f"   Converted to spreads: {len(converted)}")
        self.logger.info(f"   Unchanged: {len(unchanged)}")
        
        capital_saved = sum(
            float(pos.get('capital_required', 0)) 
            for pos in unchanged
        ) - sum(
            float(spread.get('capital_required', 0)) 
            for spread in converted
        )
        
        if capital_saved > 0:
            self.logger.info(f"   💰 Capital saved: ${capital_saved:,.2f}")
        
        self.logger.info("=" * 80)
        
        return converted, unchanged

