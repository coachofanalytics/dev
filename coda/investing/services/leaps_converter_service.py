"""
LEAPS Converter Service - Long-Dated Options to Bull Call Spreads

Converts LEAPS (Long-term Equity AnticiPation Securities) with 60-365 DTE
to Bull Call Spreads when strong institutional signals are present.

Why Convert LEAPS to Spreads:
  - Reduces capital requirement by 60-70%
  - Limits downside risk (capped at debit paid)
  - Still captures most upside (up to short strike)
  - Makes LEAPS positions more accessible

Conversion Criteria:
  - DTE: 60-365 days (long-dated options)
  - Whales Signal: ≥ +30 (strong bullish institutional flow)
  - IV Rank: >30% (high implied volatility)
  - Premium: >$100k in flow (significant institutional interest)

Strategy:
  - BUY ATM/ITM call (from Unusual Whales data)
  - SELL 10-15% OTM call (calculate optimal strike)
  - Net Debit = Reduced capital requirement
  - Max Profit = (Spread Width × 100) - Net Debit
  - Max Loss = Net Debit (capped risk)

Example:
  Before: BUY NBIS $115 Call @ $46.00 = $4,600 capital
  After:  BUY NBIS $115 Call @ $46.00
          SELL NBIS $130 Call @ $30.00
          Net Debit: $1,600 (65% capital reduction!)

Created: November 5, 2025
Phase: 10B - LEAPS Conversion
"""

import logging
from decimal import Decimal
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple
import math

logger = logging.getLogger(__name__)


class LEAPSConverterService:
    """
    Convert long-dated options (LEAPS) to Bull Call Spreads
    for capital efficiency and risk management
    """
    
    # DTE thresholds
    MIN_DTE = 60      # Below this = normal short-term options
    MAX_DTE = 365     # Above this = too long-term
    
    # Conversion requirements
    MIN_WHALES_SIGNAL = 30   # Require strong bullish signal
    MIN_IV_RANK = 30         # High volatility preferred
    MIN_FLOW_PREMIUM = 100000  # $100k+ flow = institutional
    
    # Spread configuration
    OTM_PERCENTAGE_DEFAULT = 0.12  # 12% above buy strike for sell strike
    OTM_PERCENTAGE_MIN = 0.10      # 10% minimum
    OTM_PERCENTAGE_MAX = 0.20      # 20% maximum
    
    # Premium estimation (if no API available)
    PREMIUM_DECAY_FACTOR = 0.65    # Short call ~65% of long call premium
    
    def __init__(self):
        """Initialize LEAPS converter service"""
        self.logger = logger
    
    def should_convert(self, option_data: Dict) -> Tuple[bool, str]:
        """
        Determine if LEAPS should be converted to Bull Call Spread
        
        Args:
            option_data: Dict with keys:
                - dte: Days to expiration
                - whales_signal: Bullish signal strength (-50 to +50)
                - iv_rank: Implied volatility rank (0-100)
                - flow_premium: Total premium in flow ($)
                - option_type: 'call' or 'put'
                
        Returns:
            (bool, str) - (should_convert, reason)
        """
        dte = option_data.get('dte', 0)
        whales_signal = option_data.get('whales_signal', 0)
        iv_rank = option_data.get('iv_rank', 0)
        flow_premium = option_data.get('flow_premium', 0)
        option_type = option_data.get('option_type', 'call').lower()
        
        # Must be a call option (not put)
        if option_type != 'call':
            return False, "Only CALL options converted to Bull Call Spreads"
        
        # Check DTE range
        if dte < self.MIN_DTE:
            return False, f"DTE {dte} < {self.MIN_DTE} (not a LEAP)"
        
        if dte > self.MAX_DTE:
            return False, f"DTE {dte} > {self.MAX_DTE} (too long-term)"
        
        # Check Whales signal strength
        if whales_signal < self.MIN_WHALES_SIGNAL:
            return False, f"Whales signal {whales_signal} < {self.MIN_WHALES_SIGNAL} (not strong enough)"
        
        # Check IV rank
        if iv_rank < self.MIN_IV_RANK:
            return False, f"IV Rank {iv_rank}% < {self.MIN_IV_RANK}% (volatility too low)"
        
        # Check flow premium (institutional interest)
        if flow_premium < self.MIN_FLOW_PREMIUM:
            return False, f"Flow premium ${flow_premium:,.0f} < ${self.MIN_FLOW_PREMIUM:,.0f} (insufficient institutional interest)"
        
        # All criteria met!
        reason = (
            f"✅ LEAPS conversion approved: "
            f"DTE={dte}, Whales={whales_signal}, IV={iv_rank}%, "
            f"Flow=${flow_premium:,.0f}"
        )
        
        self.logger.info(f"  {reason}")
        return True, reason
    
    def convert_to_bull_call_spread(
        self, 
        long_call_data: Dict,
        short_strike_override: Optional[Decimal] = None,
        short_premium_override: Optional[Decimal] = None
    ) -> Dict:
        """
        Convert long LEAPS call to Bull Call Spread
        
        Args:
            long_call_data: Dict with:
                - symbol: Stock symbol
                - strike: Long call strike price
                - premium: Long call premium (per share)
                - dte: Days to expiration
                - stock_price: Current stock price
                - iv: Implied volatility (decimal, e.g., 0.45 = 45%)
                - contracts: Number of contracts (default 1)
            short_strike_override: Optional manual short strike
            short_premium_override: Optional manual short premium
            
        Returns:
            Dict with Bull Call Spread position data:
                - strategy: 'bull_call_spread'
                - symbol: str
                - expiration_date: date
                - dte: int
                - positions: List[Dict] (2 legs)
                - capital_required: Decimal (net debit)
                - max_profit: Decimal
                - max_loss: Decimal
                - breakeven: Decimal
                - capital_reduction_pct: Decimal
                - original_capital: Decimal
        """
        symbol = long_call_data['symbol']
        buy_strike = Decimal(str(long_call_data['strike']))
        buy_premium = Decimal(str(long_call_data['premium']))
        dte = long_call_data['dte']
        stock_price = Decimal(str(long_call_data.get('stock_price', buy_strike)))
        iv = Decimal(str(long_call_data.get('iv', 0.40)))
        contracts = int(long_call_data.get('contracts', 1))
        
        self.logger.info(f"📊 Converting LEAPS: {symbol} ${buy_strike} Call ({dte} DTE)")
        self.logger.info(f"  Long premium: ${buy_premium}/share = ${buy_premium * 100}/contract")
        
        # Calculate short strike
        if short_strike_override:
            sell_strike = Decimal(str(short_strike_override))
            self.logger.info(f"  Using override short strike: ${sell_strike}")
        else:
            sell_strike = self.calculate_short_strike(buy_strike, stock_price)
            self.logger.info(f"  Calculated short strike: ${sell_strike} ({self._calculate_otm_pct(stock_price, sell_strike):.1f}% OTM)")
        
        # Estimate short premium
        if short_premium_override:
            sell_premium = Decimal(str(short_premium_override))
            self.logger.info(f"  Using override short premium: ${sell_premium}/share")
        else:
            sell_premium = self.estimate_short_premium(
                long_strike=buy_strike,
                long_premium=buy_premium,
                short_strike=sell_strike,
                stock_price=stock_price,
                dte=dte,
                iv=iv
            )
            self.logger.info(f"  Estimated short premium: ${sell_premium}/share")
        
        # Calculate spread metrics
        spread_width = sell_strike - buy_strike
        net_debit_per_contract = (buy_premium - sell_premium) * 100  # Per contract
        capital_required = net_debit_per_contract * contracts
        
        max_profit_per_contract = (spread_width * 100) - net_debit_per_contract
        max_profit = max_profit_per_contract * contracts
        
        max_loss = capital_required  # Can only lose the debit paid
        
        breakeven = buy_strike + (net_debit_per_contract / 100)
        
        # Calculate capital reduction
        original_capital = buy_premium * 100 * contracts
        capital_reduction = original_capital - capital_required
        capital_reduction_pct = (capital_reduction / original_capital) * 100 if original_capital > 0 else 0
        
        self.logger.info(f"  Spread width: ${spread_width}")
        self.logger.info(f"  Net debit: ${net_debit_per_contract}/contract × {contracts} = ${capital_required}")
        self.logger.info(f"  Capital reduction: ${capital_reduction} ({capital_reduction_pct:.1f}%)")
        self.logger.info(f"  Max profit: ${max_profit} | Max loss: ${max_loss}")
        self.logger.info(f"  Breakeven: ${breakeven}")
        
        # Build position legs
        positions = [
            {
                'type': 'long_call',
                'strike': float(buy_strike),
                'contracts': contracts,
                'premium': float(buy_premium),  # Per share
                'delta': 0.60,  # ATM call delta
                'theta': -0.08,
                'gamma': 0.03,
                'vega': 0.15
            },
            {
                'type': 'short_call',
                'strike': float(sell_strike),
                'contracts': contracts,
                'premium': float(sell_premium),  # Per share
                'delta': -0.35,  # OTM call delta
                'theta': 0.05,
                'gamma': -0.02,
                'vega': -0.10
            }
        ]
        
        # Calculate net Greeks
        net_delta = 0.60 - 0.35  # ~0.25 per contract
        net_theta = -0.08 + 0.05  # ~-0.03 (still time decay)
        net_gamma = 0.03 - 0.02
        net_vega = 0.15 - 0.10
        
        # Get expiration date
        expiration_date = long_call_data.get('expiration_date')
        if not expiration_date and dte:
            expiration_date = date.today() + timedelta(days=dte)
        
        spread_data = {
            'strategy': 'bull_call_spread',
            'symbol': symbol,
            'expiration_date': expiration_date,
            'dte': dte,
            'positions': positions,
            
            # Financial metrics
            'capital_required': float(capital_required),
            'premium_collected': 0,  # Debit spread (we pay, not collect)
            'max_profit': float(max_profit),
            'max_loss': float(max_loss),
            'breakeven': float(breakeven),
            
            # Greeks
            'position_delta': net_delta * contracts,
            'position_theta': net_theta * contracts,
            'position_gamma': net_gamma * contracts,
            'position_vega': net_vega * contracts,
            
            # Capital efficiency
            'original_capital': float(original_capital),
            'capital_reduction': float(capital_reduction),
            'capital_reduction_pct': float(capital_reduction_pct),
            
            # Metadata
            'conversion_source': 'LEAPS_CONVERTER',
            'conversion_reason': 'Converted from long call to reduce capital requirement',
            'spread_width': float(spread_width)
        }
        
        self.logger.info(f"✅ LEAPS conversion complete: {symbol} ${buy_strike}/${sell_strike} Bull Call Spread")
        
        return spread_data
    
    def calculate_short_strike(
        self, 
        long_strike: Decimal, 
        stock_price: Decimal,
        otm_percentage: Optional[Decimal] = None
    ) -> Decimal:
        """
        Calculate optimal short call strike for Bull Call Spread
        
        Strategy: Sell call 10-15% above current stock price
        
        Args:
            long_strike: Buy strike price
            stock_price: Current stock price
            otm_percentage: Optional custom OTM % (default 12%)
            
        Returns:
            Decimal - Short call strike price (rounded to nearest $5)
        """
        if not otm_percentage:
            otm_percentage = Decimal(str(self.OTM_PERCENTAGE_DEFAULT))
        
        # Calculate target strike (12% above stock price)
        target_strike = stock_price * (1 + otm_percentage)
        
        # Ensure short strike is above long strike
        if target_strike <= long_strike:
            target_strike = long_strike * Decimal('1.10')  # At least 10% above
        
        # Round to nearest $5 for liquid strikes
        rounded_strike = self._round_to_nearest(target_strike, 5)
        
        # Ensure minimum spread width ($5)
        if rounded_strike - long_strike < 5:
            rounded_strike = long_strike + 5
        
        return rounded_strike
    
    def estimate_short_premium(
        self,
        long_strike: Decimal,
        long_premium: Decimal,
        short_strike: Decimal,
        stock_price: Decimal,
        dte: int,
        iv: Decimal
    ) -> Decimal:
        """
        Estimate short call premium using decay factor
        
        Since we don't have real-time options pricing API, we estimate based on:
        1. Long call premium (known from Whales data)
        2. Moneyness ratio (how far OTM short call is)
        3. Decay factor (~65% for typical OTM call)
        
        Better solution: Integrate with options pricing API
        
        Args:
            long_strike: Buy strike
            long_premium: Buy premium (per share)
            short_strike: Sell strike
            stock_price: Current stock price
            dte: Days to expiration
            iv: Implied volatility (decimal)
            
        Returns:
            Decimal - Estimated short premium (per share)
        """
        # Calculate moneyness for both strikes
        long_moneyness = float((stock_price - long_strike) / stock_price)
        short_moneyness = float((stock_price - short_strike) / stock_price)
        
        # Short call is further OTM, worth less
        # Rough estimate: Premium decays exponentially with moneyness
        
        if short_moneyness >= 0:
            # Short strike is ITM/ATM - shouldn't happen for OTM spread
            # Use conservative estimate
            short_premium = long_premium * Decimal('0.80')
        else:
            # Short strike is OTM (negative moneyness)
            # Further OTM = lower premium
            # Rule of thumb: ~65% of long premium for 12% OTM
            decay_factor = Decimal(str(self.PREMIUM_DECAY_FACTOR))
            
            # Adjust for extra distance
            otm_distance = abs(short_moneyness)
            if otm_distance > 0.15:  # Very far OTM
                decay_factor *= Decimal('0.85')
            elif otm_distance > 0.10:  # Moderately OTM
                decay_factor *= Decimal('0.90')
            
            short_premium = long_premium * decay_factor
        
        # Ensure short premium is less than long premium
        short_premium = min(short_premium, long_premium * Decimal('0.90'))
        
        # Round to nearest $0.05
        short_premium = self._round_to_nearest(short_premium, Decimal('0.05'))
        
        self.logger.debug(f"  Premium estimation: Long ${long_premium} → Short ${short_premium}")
        
        return short_premium
    
    def _calculate_otm_pct(self, stock_price: Decimal, strike: Decimal) -> Decimal:
        """Calculate how far OTM a strike is (percentage)"""
        if stock_price <= 0:
            return Decimal('0')
        return ((strike - stock_price) / stock_price) * 100
    
    def _round_to_nearest(self, value: Decimal, increment: Decimal or int) -> Decimal:
        """
        Round value to nearest increment
        
        Examples:
            _round_to_nearest(127.34, 5) → 125
            _round_to_nearest(127.34, 0.05) → 127.35
        """
        increment = Decimal(str(increment))
        return (value / increment).quantize(Decimal('1.')) * increment
    
    def convert_unusual_whales_leaps(
        self,
        whales_data: Dict,
        auto_convert: bool = True
    ) -> Optional[Dict]:
        """
        Convert Unusual Whales LEAPS call to Bull Call Spread
        
        Args:
            whales_data: Unusual Whales flow data dict with:
                - symbol: str
                - strike: Decimal
                - option_type: 'call' or 'put'
                - premium: Decimal (per share)
                - expiry: date
                - dte: int
                - underlying_price: Decimal (stock price)
                - implied_volatility: Decimal
                - size: int (contracts in flow)
                - premium_total: Decimal (total $ in flow)
                - bearish_or_bullish: 'bullish' or 'bearish'
            auto_convert: If False, only check criteria (don't convert)
            
        Returns:
            Dict with Bull Call Spread data, or None if shouldn't convert
        """
        symbol = whales_data.get('symbol', 'UNKNOWN')
        
        # Parse Whales signal
        direction = whales_data.get('bearish_or_bullish', '').lower()
        if direction == 'bullish':
            whales_signal = 50  # Strong bullish
        elif direction == 'bearish':
            whales_signal = -50  # Bearish (don't convert)
        else:
            whales_signal = 0  # Neutral
        
        # Build option data for criteria check
        option_data = {
            'dte': whales_data.get('dte', 0),
            'whales_signal': whales_signal,
            'iv_rank': float(whales_data.get('implied_volatility', 0)) * 100,  # Convert 0.45 → 45%
            'flow_premium': float(whales_data.get('premium_total', 0)),
            'option_type': whales_data.get('option_type', 'call').lower()
        }
        
        # Check if should convert
        should_convert, reason = self.should_convert(option_data)
        
        if not should_convert:
            self.logger.info(f"❌ {symbol}: Not converting - {reason}")
            return None
        
        if not auto_convert:
            # Just checking criteria, not actually converting
            self.logger.info(f"✅ {symbol}: Eligible for conversion - {reason}")
            return {'eligible': True, 'reason': reason}
        
        # Build long call data for conversion
        long_call_data = {
            'symbol': symbol,
            'strike': whales_data['strike'],
            'premium': whales_data['premium'],  # Per share
            'dte': whales_data['dte'],
            'stock_price': whales_data.get('underlying_price', whales_data['strike']),
            'iv': whales_data.get('implied_volatility', 0.40),
            'contracts': 1,  # Default to 1 contract
            'expiration_date': whales_data.get('expiry')
        }
        
        # Convert to Bull Call Spread
        spread_data = self.convert_to_bull_call_spread(long_call_data)
        
        # Add Whales metadata
        spread_data['whales_flow_data'] = {
            'direction': direction,
            'signal_strength': whales_signal,
            'flow_premium': whales_data.get('premium_total', 0),
            'size': whales_data.get('size', 0),
            'tags': whales_data.get('tags', ''),
            'sector': whales_data.get('sector', 'Unknown')
        }
        
        return spread_data
    
    def batch_convert_leaps(
        self,
        unusual_whales_positions: List[Dict]
    ) -> Dict:
        """
        Batch convert multiple LEAPS from Unusual Whales flow data
        
        Args:
            unusual_whales_positions: List of Whales flow data dicts
            
        Returns:
            {
                'converted': List[Dict],  # Successfully converted spreads
                'rejected': List[Dict],   # Not eligible for conversion
                'total_capital_before': Decimal,
                'total_capital_after': Decimal,
                'total_savings': Decimal,
                'savings_pct': Decimal
            }
        """
        converted = []
        rejected = []
        total_capital_before = Decimal('0')
        total_capital_after = Decimal('0')
        
        self.logger.info(f"🔄 Batch converting {len(unusual_whales_positions)} LEAPS positions...")
        
        for whales_data in unusual_whales_positions:
            try:
                result = self.convert_unusual_whales_leaps(whales_data, auto_convert=True)
                
                if result:
                    converted.append(result)
                    total_capital_before += Decimal(str(result['original_capital']))
                    total_capital_after += Decimal(str(result['capital_required']))
                else:
                    rejected.append({
                        'symbol': whales_data.get('symbol'),
                        'strike': whales_data.get('strike'),
                        'dte': whales_data.get('dte'),
                        'reason': 'Did not meet conversion criteria'
                    })
            
            except Exception as e:
                symbol = whales_data.get('symbol', 'UNKNOWN')
                self.logger.error(f"❌ Error converting {symbol}: {e}")
                rejected.append({
                    'symbol': symbol,
                    'strike': whales_data.get('strike'),
                    'dte': whales_data.get('dte'),
                    'reason': f"Conversion error: {str(e)}"
                })
        
        total_savings = total_capital_before - total_capital_after
        savings_pct = (total_savings / total_capital_before * 100) if total_capital_before > 0 else Decimal('0')
        
        self.logger.info(f"✅ Batch conversion complete:")
        self.logger.info(f"  Converted: {len(converted)} positions")
        self.logger.info(f"  Rejected: {len(rejected)} positions")
        self.logger.info(f"  Capital savings: ${total_savings:,.2f} ({savings_pct:.1f}%)")
        
        return {
            'converted': converted,
            'rejected': rejected,
            'summary': {
                'total_positions': len(unusual_whales_positions),
                'converted_count': len(converted),
                'rejected_count': len(rejected),
                'conversion_rate': len(converted) / len(unusual_whales_positions) * 100 if unusual_whales_positions else 0,
                'total_capital_before': float(total_capital_before),
                'total_capital_after': float(total_capital_after),
                'total_savings': float(total_savings),
                'savings_pct': float(savings_pct)
            }
        }
    
    def generate_conversion_summary(self, batch_result: Dict) -> str:
        """
        Generate human-readable summary of batch conversion
        
        Args:
            batch_result: Output from batch_convert_leaps()
            
        Returns:
            str - Multi-line summary
        """
        summary = batch_result['summary']
        converted = batch_result['converted']
        
        lines = []
        lines.append("=" * 70)
        lines.append("LEAPS CONVERSION SUMMARY")
        lines.append("=" * 70)
        lines.append(f"Total Positions Analyzed: {summary['total_positions']}")
        lines.append(f"✅ Converted to Spreads: {summary['converted_count']}")
        lines.append(f"❌ Rejected (criteria not met): {summary['rejected_count']}")
        lines.append(f"Conversion Rate: {summary['conversion_rate']:.1f}%")
        lines.append("")
        
        lines.append("CAPITAL EFFICIENCY:")
        lines.append(f"  Before: ${summary['total_capital_before']:,.2f} (buying calls outright)")
        lines.append(f"  After:  ${summary['total_capital_after']:,.2f} (using spreads)")
        lines.append(f"  Savings: ${summary['total_savings']:,.2f} ({summary['savings_pct']:.1f}% reduction!)")
        lines.append("")
        
        if converted:
            lines.append("CONVERTED POSITIONS:")
            for spread in converted:
                lines.append(f"  ✅ {spread['symbol']} ${spread['positions'][0]['strike']}/${spread['positions'][1]['strike']} Bull Call Spread")
                lines.append(f"     Capital: ${spread['original_capital']:,.0f} → ${spread['capital_required']:,.0f} ({spread['capital_reduction_pct']:.0f}% savings)")
        
        lines.append("=" * 70)
        
        return "\n".join(lines)

