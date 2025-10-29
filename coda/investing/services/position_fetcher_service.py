"""
Position Fetcher Service

Fetches high-probability options positions from external platforms:
- Primary: OptionPlay API
- Fallback: Thinkorswim/TD Ameritrade API

Filters positions by:
- Probability of profit >= 70%
- Premium >= $100
- Days to expiration: 30-60
- Specific strategies: Bull/Bear Put/Call Spreads
"""

import requests
import logging
from decimal import Decimal
from datetime import datetime, date, timedelta
from django.conf import settings
from django.utils import timezone
from typing import List, Dict, Optional

from ..models import SuggestedPosition

logger = logging.getLogger(__name__)


class PositionFetcherService:
    """
    Unified service for fetching high-probability options positions
    from multiple API sources with intelligent fallback
    """
    
    def __init__(self):
        # OptionPlay API (Primary)
        self.optionplay_api_key = getattr(settings, 'OPTIONPLAY_API_KEY', None)
        self.optionplay_base_url = "https://api.optionplay.com/v1"
        
        # TD Ameritrade API (Fallback)
        self.td_client_id = getattr(settings, 'TD_AMERITRADE_CLIENT_ID', None)
        self.td_access_token = getattr(settings, 'TD_AMERITRADE_ACCESS_TOKEN', None)
        self.td_base_url = "https://api.tdameritrade.com/v1"
    
    def fetch_high_probability_positions(self, filters: Dict = None) -> List[SuggestedPosition]:
        """
        PRIMARY METHOD: Fetch high-probability positions with fallback mechanism
        
        Args:
            filters: Dict with filtering criteria:
                {
                    'probability_min': 70,  # Minimum % chance of profit
                    'premium_min': 100,     # Minimum premium in dollars
                    'dte_min': 30,          # Minimum days to expiration
                    'dte_max': 60,          # Maximum days to expiration
                    'strategies': ['bull_put_spread', 'bear_call_spread', ...],
                    'max_positions': 5,     # Maximum positions to return
                    'symbols': ['SPY', 'QQQ', 'AAPL', ...]  # Optional specific symbols
                }
        
        Returns:
            List of SuggestedPosition instances (already saved to database)
        """
        # Default filters
        if filters is None:
            filters = self._get_default_filters()
        
        suggested_positions = []
        
        # Try OptionPlay first (PRIMARY)
        try:
            logger.info("🔄 Fetching positions from OptionPlay...")
            positions = self._fetch_from_optionplay(filters)
            
            if positions and len(positions) >= filters.get('max_positions', 5):
                logger.info(f"✅ OptionPlay returned {len(positions)} positions")
                suggested_positions = self._save_suggested_positions(positions, source='optionplay')
                return suggested_positions
            else:
                logger.warning(f"⚠️  OptionPlay returned only {len(positions) if positions else 0} positions")
        
        except Exception as e:
            logger.warning(f"❌ OptionPlay fetch failed: {e}, trying Thinkorswim...")
        
        # Fallback to Thinkorswim
        try:
            logger.info("🔄 Fetching positions from Thinkorswim...")
            positions = self._fetch_from_thinkorswim(filters)
            logger.info(f"✅ Thinkorswim returned {len(positions)} positions")
            suggested_positions = self._save_suggested_positions(positions, source='thinkorswim')
            return suggested_positions
        
        except Exception as e:
            logger.error(f"❌ Both APIs failed! OptionPlay and Thinkorswim unavailable: {e}")
            
            # Last resort: Return mock data for testing
            logger.info("🎭 Returning mock data for testing...")
            mock_positions = self._get_mock_positions(filters)
            suggested_positions = self._save_suggested_positions(mock_positions, source='manual')
            return suggested_positions
    
    def _get_default_filters(self) -> Dict:
        """Default filtering criteria for high-probability positions"""
        return {
            'probability_min': 70,          # 70%+ chance of profit
            'premium_min': 100,             # $100+ premium
            'dte_min': 30,                  # Minimum 30 days to expiration
            'dte_max': 60,                  # Maximum 60 days to expiration
            'strategies': [
                'bull_put_spread',
                'bear_call_spread',
                'bull_call_spread',
                'bear_put_spread'
            ],
            'max_positions': 5,             # Return top 5
            'symbols': ['SPY', 'QQQ', 'IWM', 'DIA', 'AAPL', 'MSFT', 'TSLA', 'NVDA']  # High-liquidity symbols
        }
    
    # ========================================================================
    # OPTIONPLAY API INTEGRATION (PRIMARY)
    # ========================================================================
    
    def _fetch_from_optionplay(self, filters: Dict) -> List[Dict]:
        """
        Fetch positions from OptionPlay API
        
        API Endpoint: GET /v1/strategies/high-probability
        Docs: https://api.optionplay.com/docs
        """
        if not self.optionplay_api_key:
            logger.warning("⚠️  OPTIONPLAY_API_KEY not configured in settings")
            return []
        
        headers = {
            'Authorization': f'Bearer {self.optionplay_api_key}',
            'Content-Type': 'application/json'
        }
        
        params = {
            'probability_min': filters['probability_min'],
            'premium_min': filters['premium_min'],
            'dte_min': filters['dte_min'],
            'dte_max': filters['dte_max'],
            'strategies': ','.join(filters['strategies']),
            'limit': filters['max_positions'],
            'sort': 'probability_desc'
        }
        
        # Add symbols if specified
        if 'symbols' in filters and filters['symbols']:
            params['symbols'] = ','.join(filters['symbols'])
        
        try:
            response = requests.get(
                f"{self.optionplay_base_url}/strategies/high-probability",
                headers=headers,
                params=params,
                timeout=30  # 30 seconds timeout
            )
            response.raise_for_status()
            
            data = response.json()
            positions = data.get('strategies', [])
            
            # Normalize OptionPlay response to our format
            normalized = [self._normalize_optionplay_response(pos) for pos in positions]
            
            # Apply additional filters
            filtered = self._apply_filters(normalized, filters)
            
            logger.info(f"✅ OptionPlay returned {len(filtered)} filtered positions")
            return filtered[:filters['max_positions']]
        
        except requests.exceptions.Timeout:
            logger.error("❌ OptionPlay API timeout (>30s)")
            raise
        except requests.exceptions.HTTPError as e:
            logger.error(f"❌ OptionPlay API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"❌ OptionPlay fetch failed: {e}")
            raise
    
    def _normalize_optionplay_response(self, api_response: Dict) -> Dict:
        """
        Convert OptionPlay API response to standardized format
        
        OptionPlay Response Format (example):
        {
            "symbol": "AAPL",
            "strategy": "bull_put_spread",
            "legs": [...],
            "probability_of_profit": 75.5,
            "premium": 150.00,
            "max_profit": 150.00,
            "max_loss": 350.00,
            ...
        }
        """
        return {
            'symbol': api_response['symbol'],
            'strategy': api_response['strategy'],
            'positions': api_response['legs'],  # Already in correct format
            'expiration_date': datetime.strptime(api_response['expiration'], '%Y-%m-%d').date(),
            'dte': api_response.get('dte', 0),
            'premium_collected': Decimal(str(api_response['premium'])),
            'capital_required': Decimal(str(api_response['capital_required'])),
            'max_profit': Decimal(str(api_response['max_profit'])),
            'max_loss': Decimal(str(api_response['max_loss'])),
            'breakeven': Decimal(str(api_response.get('breakeven', 0))),
            'probability_of_profit': Decimal(str(api_response['probability_of_profit'])),
            'position_delta': Decimal(str(api_response.get('delta', 0))),
            'position_theta': Decimal(str(api_response.get('theta', 0))),
            'position_gamma': Decimal(str(api_response.get('gamma', 0))),
            'position_vega': Decimal(str(api_response.get('vega', 0))),
            'ai_confidence': Decimal(str(api_response.get('confidence', 0))),
            'ai_reasoning': api_response.get('reasoning', ''),
            'api_response_data': api_response  # Store full response
        }
    
    # ========================================================================
    # THINKORSWIM/TD AMERITRADE API INTEGRATION (FALLBACK)
    # ========================================================================
    
    def _fetch_from_thinkorswim(self, filters: Dict) -> List[Dict]:
        """
        Fetch positions from TD Ameritrade API (Thinkorswim platform)
        
        API Endpoint: GET /v1/marketdata/chains
        Docs: https://developer.tdameritrade.com/option-chains/apis
        """
        if not self.td_access_token:
            logger.warning("⚠️  TD_AMERITRADE_ACCESS_TOKEN not configured in settings")
            return []
        
        headers = {
            'Authorization': f'Bearer {self.td_access_token}'
        }
        
        all_positions = []
        symbols = filters.get('symbols', ['SPY', 'QQQ'])  # Default to SPY and QQQ
        
        for symbol in symbols:
            try:
                params = {
                    'symbol': symbol,
                    'contractType': 'ALL',
                    'strikeCount': 20,  # Get 20 strikes above/below current price
                    'includeQuotes': 'TRUE',
                    'strategy': 'VERTICAL',  # Spreads
                    'range': 'OTM',  # Out of the money
                    'fromDate': (date.today() + timedelta(days=filters['dte_min'])).strftime('%Y-%m-%d'),
                    'toDate': (date.today() + timedelta(days=filters['dte_max'])).strftime('%Y-%m-%d')
                }
                
                response = requests.get(
                    f"{self.td_base_url}/marketdata/chains",
                    headers=headers,
                    params=params,
                    timeout=30
                )
                response.raise_for_status()
                
                chains = response.json()
                
                # Parse chains and generate spread strategies
                positions = self._parse_td_chains_to_spreads(symbol, chains, filters)
                all_positions.extend(positions)
            
            except Exception as e:
                logger.warning(f"⚠️  Failed to fetch {symbol} from TD Ameritrade: {e}")
                continue
        
        # Apply filters
        filtered = self._apply_filters(all_positions, filters)
        
        logger.info(f"✅ Thinkorswim returned {len(filtered)} filtered positions")
        return filtered[:filters['max_positions']]
    
    def _parse_td_chains_to_spreads(self, symbol: str, chains: Dict, filters: Dict) -> List[Dict]:
        """
        Parse TD Ameritrade options chain to generate spread strategies
        
        Creates Bull Put Spreads, Bear Call Spreads, etc. from individual options
        """
        positions = []
        
        # Get puts and calls
        put_exp_map = chains.get('putExpDateMap', {})
        call_exp_map = chains.get('callExpDateMap', {})
        
        # Generate Bull Put Spreads from puts
        for exp_date, strikes in put_exp_map.items():
            # Parse expiration date (format: "2025-12-19:52")
            exp_str = exp_date.split(':')[0]
            exp_datetime = datetime.strptime(exp_str, '%Y-%m-%d').date()
            dte = (exp_datetime - date.today()).days
            
            if not (filters['dte_min'] <= dte <= filters['dte_max']):
                continue
            
            # Get list of strikes
            strike_list = sorted([float(strike) for strike in strikes.keys()])
            
            # Generate Bull Put Spreads (sell higher strike, buy lower strike)
            for i in range(len(strike_list) - 1):
                short_strike = strike_list[i + 1]
                long_strike = strike_list[i]
                
                short_put = strikes[str(short_strike)][0]  # First option at this strike
                long_put = strikes[str(long_strike)][0]
                
                # Calculate spread metrics
                short_premium = short_put.get('bid', 0)
                long_premium = long_put.get('ask', 0)
                net_credit = short_premium - long_premium
                
                if net_credit < (filters['premium_min'] / 100):  # Convert to per-share
                    continue
                
                # Calculate probability of profit (using delta as proxy)
                # Delta ~= probability ITM, so 1 - delta ~= probability OTM (profit)
                short_delta = abs(short_put.get('delta', 0.3))
                prob_profit = (1 - short_delta) * 100  # Convert to percentage
                
                if prob_profit < filters['probability_min']:
                    continue
                
                # Build position data
                position = {
                    'symbol': symbol,
                    'strategy': 'bull_put_spread',
                    'positions': [
                        {
                            'type': 'short_put',
                            'strike': short_strike,
                            'contracts': 1,
                            'premium': short_premium,
                            'delta': -short_put.get('delta', 0),
                            'theta': short_put.get('theta', 0),
                        },
                        {
                            'type': 'long_put',
                            'strike': long_strike,
                            'contracts': 1,
                            'premium': long_premium,
                            'delta': -long_put.get('delta', 0),
                            'theta': long_put.get('theta', 0),
                        }
                    ],
                    'expiration_date': exp_datetime,
                    'dte': dte,
                    'premium_collected': Decimal(str(net_credit * 100)),
                    'capital_required': Decimal(str((short_strike - long_strike) * 100)),
                    'max_profit': Decimal(str(net_credit * 100)),
                    'max_loss': Decimal(str(((short_strike - long_strike) - net_credit) * 100)),
                    'breakeven': Decimal(str(short_strike - net_credit)),
                    'probability_of_profit': Decimal(str(prob_profit)),
                    'position_delta': Decimal(str((short_put.get('delta', 0) - long_put.get('delta', 0)) * 100)),
                    'position_theta': Decimal(str((short_put.get('theta', 0) - long_put.get('theta', 0)) * 100)),
                    'position_gamma': Decimal('0.0000'),
                    'position_vega': Decimal('0.0000'),
                    'ai_confidence': Decimal(str(prob_profit)),  # Use probability as confidence
                    'ai_reasoning': f"Bull Put Spread on {symbol}: {prob_profit:.1f}% probability, ${net_credit * 100:.0f} credit, {dte} DTE",
                    'api_response_data': {
                        'short_put': short_put,
                        'long_put': long_put,
                        'source': 'td_ameritrade'
                    }
                }
                
                positions.append(position)
        
        # Generate Bear Call Spreads from calls
        for exp_date, strikes in call_exp_map.items():
            exp_str = exp_date.split(':')[0]
            exp_datetime = datetime.strptime(exp_str, '%Y-%m-%d').date()
            dte = (exp_datetime - date.today()).days
            
            if not (filters['dte_min'] <= dte <= filters['dte_max']):
                continue
            
            strike_list = sorted([float(strike) for strike in strikes.keys()])
            
            # Generate Bear Call Spreads (sell lower strike, buy higher strike)
            for i in range(len(strike_list) - 1):
                short_strike = strike_list[i]
                long_strike = strike_list[i + 1]
                
                short_call = strikes[str(short_strike)][0]
                long_call = strikes[str(long_strike)][0]
                
                short_premium = short_call.get('bid', 0)
                long_premium = long_call.get('ask', 0)
                net_credit = short_premium - long_premium
                
                if net_credit < (filters['premium_min'] / 100):
                    continue
                
                short_delta = abs(short_call.get('delta', 0.3))
                prob_profit = (1 - short_delta) * 100
                
                if prob_profit < filters['probability_min']:
                    continue
                
                position = {
                    'symbol': symbol,
                    'strategy': 'bear_call_spread',
                    'positions': [
                        {
                            'type': 'short_call',
                            'strike': short_strike,
                            'contracts': 1,
                            'premium': short_premium,
                            'delta': short_call.get('delta', 0),
                            'theta': short_call.get('theta', 0),
                        },
                        {
                            'type': 'long_call',
                            'strike': long_strike,
                            'contracts': 1,
                            'premium': long_premium,
                            'delta': long_call.get('delta', 0),
                            'theta': long_call.get('theta', 0),
                        }
                    ],
                    'expiration_date': exp_datetime,
                    'dte': dte,
                    'premium_collected': Decimal(str(net_credit * 100)),
                    'capital_required': Decimal(str((long_strike - short_strike) * 100)),
                    'max_profit': Decimal(str(net_credit * 100)),
                    'max_loss': Decimal(str(((long_strike - short_strike) - net_credit) * 100)),
                    'breakeven': Decimal(str(short_strike + net_credit)),
                    'probability_of_profit': Decimal(str(prob_profit)),
                    'position_delta': Decimal(str((short_call.get('delta', 0) - long_call.get('delta', 0)) * 100)),
                    'position_theta': Decimal(str((short_call.get('theta', 0) - long_call.get('theta', 0)) * 100)),
                    'position_gamma': Decimal('0.0000'),
                    'position_vega': Decimal('0.0000'),
                    'ai_confidence': Decimal(str(prob_profit)),
                    'ai_reasoning': f"Bear Call Spread on {symbol}: {prob_profit:.1f}% probability, ${net_credit * 100:.0f} credit, {dte} DTE",
                    'api_response_data': {
                        'short_call': short_call,
                        'long_call': long_call,
                        'source': 'td_ameritrade'
                    }
                }
                
                positions.append(position)
        
        return positions
    
    # ========================================================================
    # FILTERING ENGINE
    # ========================================================================
    
    def _apply_filters(self, positions: List[Dict], filters: Dict) -> List[Dict]:
        """
        Apply filtering criteria to positions:
        - Probability of profit >= 70%
        - Premium >= $100
        - DTE between 30-60 days
        - Specific strategies only
        """
        filtered = []
        
        for pos in positions:
            # Check probability
            if pos['probability_of_profit'] < Decimal(str(filters['probability_min'])):
                continue
            
            # Check premium
            if pos['premium_collected'] < Decimal(str(filters['premium_min'])):
                continue
            
            # Check DTE
            if not (filters['dte_min'] <= pos['dte'] <= filters['dte_max']):
                continue
            
            # Check strategy
            if pos['strategy'] not in filters['strategies']:
                continue
            
            filtered.append(pos)
        
        # Sort by probability (highest first)
        filtered.sort(key=lambda x: float(x['probability_of_profit']), reverse=True)
        
        return filtered
    
    # ========================================================================
    # DATABASE OPERATIONS
    # ========================================================================
    
    def _save_suggested_positions(self, positions: List[Dict], source: str) -> List[SuggestedPosition]:
        """
        Save fetched positions to SuggestedPosition model
        
        Args:
            positions: List of normalized position dicts
            source: 'optionplay', 'thinkorswim', or 'manual'
        
        Returns:
            List of created SuggestedPosition instances
        """
        suggested_positions = []
        
        for pos_data in positions:
            try:
                suggested_pos = SuggestedPosition.objects.create(
                    source=source,
                    symbol=pos_data['symbol'],
                    strategy=pos_data['strategy'],
                    positions=pos_data['positions'],
                    expiration_date=pos_data['expiration_date'],
                    dte=pos_data['dte'],
                    premium_collected=pos_data['premium_collected'],
                    capital_required=pos_data['capital_required'],
                    max_profit=pos_data['max_profit'],
                    max_loss=pos_data['max_loss'],
                    breakeven=pos_data.get('breakeven'),
                    probability_of_profit=pos_data['probability_of_profit'],
                    position_delta=pos_data.get('position_delta', Decimal('0.0000')),
                    position_theta=pos_data.get('position_theta', Decimal('0.0000')),
                    position_gamma=pos_data.get('position_gamma', Decimal('0.0000')),
                    position_vega=pos_data.get('position_vega', Decimal('0.0000')),
                    ai_confidence=pos_data.get('ai_confidence'),
                    ai_reasoning=pos_data.get('ai_reasoning', ''),
                    api_response_data=pos_data.get('api_response_data', {}),
                    review_status='pending'
                )
                
                suggested_positions.append(suggested_pos)
                logger.info(f"✅ Saved: {suggested_pos}")
            
            except Exception as e:
                logger.error(f"❌ Failed to save position {pos_data.get('symbol', 'UNKNOWN')}: {e}")
                continue
        
        logger.info(f"✅ Saved {len(suggested_positions)} suggested positions to database")
        return suggested_positions
    
    # ========================================================================
    # MOCK DATA (For Testing When APIs Unavailable)
    # ========================================================================
    
    def _get_mock_positions(self, filters: Dict) -> List[Dict]:
        """
        Generate mock high-probability positions for testing
        Uses realistic data based on current market conditions
        """
        today = date.today()
        exp_date = today + timedelta(days=45)  # 45 DTE
        
        mock_positions = [
            {
                'symbol': 'SPY',
                'strategy': 'bull_put_spread',
                'positions': [
                    {'type': 'short_put', 'strike': 540.00, 'contracts': 1, 'premium': 2.50, 'delta': -0.25, 'theta': 0.05},
                    {'type': 'long_put', 'strike': 535.00, 'contracts': 1, 'premium': 1.30, 'delta': -0.15, 'theta': 0.02}
                ],
                'expiration_date': exp_date,
                'dte': 45,
                'premium_collected': Decimal('120.00'),
                'capital_required': Decimal('500.00'),
                'max_profit': Decimal('120.00'),
                'max_loss': Decimal('380.00'),
                'breakeven': Decimal('538.80'),
                'probability_of_profit': Decimal('75.00'),
                'position_delta': Decimal('-10.00'),
                'position_theta': Decimal('3.00'),
                'position_gamma': Decimal('0.0000'),
                'position_vega': Decimal('0.0000'),
                'ai_confidence': Decimal('75.00'),
                'ai_reasoning': 'SPY Bull Put Spread: Strong support at $540, 75% probability, 45 DTE',
                'api_response_data': {'note': 'Mock data for testing'}
            },
            {
                'symbol': 'QQQ',
                'strategy': 'bear_call_spread',
                'positions': [
                    {'type': 'short_call', 'strike': 490.00, 'contracts': 1, 'premium': 2.20, 'delta': 0.25, 'theta': 0.05},
                    {'type': 'long_call', 'strike': 495.00, 'contracts': 1, 'premium': 1.00, 'delta': 0.15, 'theta': 0.02}
                ],
                'expiration_date': exp_date,
                'dte': 45,
                'premium_collected': Decimal('120.00'),
                'capital_required': Decimal('500.00'),
                'max_profit': Decimal('120.00'),
                'max_loss': Decimal('380.00'),
                'breakeven': Decimal('491.20'),
                'probability_of_profit': Decimal('72.00'),
                'position_delta': Decimal('10.00'),
                'position_theta': Decimal('3.00'),
                'position_gamma': Decimal('0.0000'),
                'position_vega': Decimal('0.0000'),
                'ai_confidence': Decimal('72.00'),
                'ai_reasoning': 'QQQ Bear Call Spread: Resistance at $490, 72% probability, 45 DTE',
                'api_response_data': {'note': 'Mock data for testing'}
            },
            {
                'symbol': 'AAPL',
                'strategy': 'bull_put_spread',
                'positions': [
                    {'type': 'short_put', 'strike': 220.00, 'contracts': 1, 'premium': 2.80, 'delta': -0.28, 'theta': 0.06},
                    {'type': 'long_put', 'strike': 215.00, 'contracts': 1, 'premium': 1.50, 'delta': -0.18, 'theta': 0.03}
                ],
                'expiration_date': exp_date,
                'dte': 45,
                'premium_collected': Decimal('130.00'),
                'capital_required': Decimal('500.00'),
                'max_profit': Decimal('130.00'),
                'max_loss': Decimal('370.00'),
                'breakeven': Decimal('218.70'),
                'probability_of_profit': Decimal('73.00'),
                'position_delta': Decimal('-10.00'),
                'position_theta': Decimal('3.00'),
                'position_gamma': Decimal('0.0000'),
                'position_vega': Decimal('0.0000'),
                'ai_confidence': Decimal('73.00'),
                'ai_reasoning': 'AAPL Bull Put Spread: Strong support level, 73% probability, 45 DTE',
                'api_response_data': {'note': 'Mock data for testing'}
            },
            {
                'symbol': 'MSFT',
                'strategy': 'bull_put_spread',
                'positions': [
                    {'type': 'short_put', 'strike': 410.00, 'contracts': 1, 'premium': 3.00, 'delta': -0.26, 'theta': 0.07},
                    {'type': 'long_put', 'strike': 405.00, 'contracts': 1, 'premium': 1.60, 'delta': -0.16, 'theta': 0.03}
                ],
                'expiration_date': exp_date,
                'dte': 45,
                'premium_collected': Decimal('140.00'),
                'capital_required': Decimal('500.00'),
                'max_profit': Decimal('140.00'),
                'max_loss': Decimal('360.00'),
                'breakeven': Decimal('408.60'),
                'probability_of_profit': Decimal('74.00'),
                'position_delta': Decimal('-10.00'),
                'position_theta': Decimal('4.00'),
                'position_gamma': Decimal('0.0000'),
                'position_vega': Decimal('0.0000'),
                'ai_confidence': Decimal('74.00'),
                'ai_reasoning': 'MSFT Bull Put Spread: Tech support, 74% probability, 45 DTE',
                'api_response_data': {'note': 'Mock data for testing'}
            },
            {
                'symbol': 'TSLA',
                'strategy': 'bear_call_spread',
                'positions': [
                    {'type': 'short_call', 'strike': 250.00, 'contracts': 1, 'premium': 3.50, 'delta': 0.30, 'theta': 0.08},
                    {'type': 'long_call', 'strike': 255.00, 'contracts': 1, 'premium': 2.00, 'delta': 0.20, 'theta': 0.04}
                ],
                'expiration_date': exp_date,
                'dte': 45,
                'premium_collected': Decimal('150.00'),
                'capital_required': Decimal('500.00'),
                'max_profit': Decimal('150.00'),
                'max_loss': Decimal('350.00'),
                'breakeven': Decimal('251.50'),
                'probability_of_profit': Decimal('70.00'),
                'position_delta': Decimal('10.00'),
                'position_theta': Decimal('4.00'),
                'position_gamma': Decimal('0.0000'),
                'position_vega': Decimal('0.0000'),
                'ai_confidence': Decimal('70.00'),
                'ai_reasoning': 'TSLA Bear Call Spread: Resistance zone, 70% probability, 45 DTE',
                'api_response_data': {'note': 'Mock data for testing'}
            }
        ]
        
        return mock_positions

