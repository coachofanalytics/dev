"""
Unusual Whales API Service

Fetches real-time options flow, dark pool data, and unusual activity
to TIME position entries based on institutional flow.

Use Case:
- Heavy buying flow detected → GREEN LIGHT to enter
- Heavy selling flow detected → RED LIGHT to skip/exit
"""

import logging
import requests
from django.conf import settings
from datetime import datetime, timedelta
from decimal import Decimal

logger = logging.getLogger(__name__)


class UnusualWhalesService:
    """
    Service for interacting with Unusual Whales API
    
    Features:
    - Real-time options flow data
    - Dark pool activity detection
    - Unusual volume alerts
    - Flow sentiment scoring
    """
    
    def __init__(self):
        self.api_key = getattr(settings, 'UNUSUAL_WHALES_API_KEY', None)
        self.enabled = getattr(settings, 'UNUSUAL_WHALES_ENABLED', False) and self.api_key
        # Unusual Whales API base (v1)
        # All endpoint paths below include the /api prefix explicitly
        self.base_url = 'https://api.unusualwhales.com'
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Accept': 'application/json'
        }
    
    def is_enabled(self):
        """Check if Unusual Whales is enabled and configured"""
        return self.enabled
    
    def test_connection(self):
        """
        Test API connection and return account info
        
        Returns:
            dict: {
                'valid': bool,
                'plan': str,
                'rate_limit': int,
                'error': str (if any)
            }
        """
        if not self.api_key:
            return {'valid': False, 'error': 'No API key configured'}
        
        try:
            # Test with a simple stock flow alert query (AAPL)
            # This validates the API key and permissions
            response = requests.get(
                f'{self.base_url}/api/stock/AAPL/flow-alerts',
                headers=self.headers,
                params={'limit': 1},
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    'valid': True,
                    'plan': 'API key valid',
                    'rate_limit': 'Check headers for X-RateLimit-Remaining',
                    'error': None
                }
            elif response.status_code == 401:
                return {
                    'valid': False,
                    'error': 'Invalid API key or expired'
                }
            elif response.status_code == 403:
                return {
                    'valid': False,
                    'error': 'API key valid but insufficient permissions for this endpoint'
                }
            else:
                return {
                    'valid': False,
                    'error': f'API returned {response.status_code}: {response.text[:200]}'
                }
        
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }
    
    def get_unusual_activity(self, symbol):
        """
        Get unusual options activity for a symbol
        
        Args:
            symbol (str): Stock ticker (e.g., 'AAPL')
        
        Returns:
            dict: {
                'symbol': str,
                'unusual_calls': int,  # Number of unusual call contracts
                'unusual_puts': int,   # Number of unusual put contracts
                'sentiment': str,      # 'bullish', 'bearish', 'neutral'
                'sentiment_score': float,  # 0-100 (higher = more bullish)
                'premium_spent': float,    # Net premium spent on calls vs puts
                'flow_score': float,   # 0-100 (timing indicator)
                'timestamp': datetime
            }
        """
        if not self.enabled:
            logger.warning("Unusual Whales not enabled - skipping")
            return None
        
        try:
            # Fetch unusual activity (latest flow alerts)
            response = requests.get(
                f'{self.base_url}/api/stock/{symbol}/flow-alerts',
                headers=self.headers,
                params={'limit': 100},  # Latest alerts
                timeout=10
            )
            
            if response.status_code != 200:
                logger.warning(f"Failed to fetch unusual activity for {symbol}: {response.status_code}")
                return None
            
            payload = response.json()
            # API wraps payload in "data"
            data_list = payload.get('data', []) if isinstance(payload, dict) else []
            if not data_list:
                return None
            # Take most recent alert
            data = data_list[0]
            
            # Calculate sentiment and flow score
            total_premium = float(data.get('total_premium', 0) or 0)
            if data.get('type') == 'call':
                calls_premium = total_premium
                puts_premium = 0.0
            elif data.get('type') == 'put':
                calls_premium = 0.0
                puts_premium = total_premium
            else:
                calls_premium = total_premium
                puts_premium = 0.0
            total_premium = calls_premium + puts_premium
            
            if total_premium > 0:
                sentiment_score = (calls_premium / total_premium) * 100
            else:
                sentiment_score = 50  # Neutral
            
            # Determine sentiment
            if sentiment_score >= 65:
                sentiment = 'bullish'
            elif sentiment_score <= 35:
                sentiment = 'bearish'
            else:
                sentiment = 'neutral'
            
            # Calculate flow score (0-100)
            # High score = good timing to enter
            flow_score = self._calculate_flow_score(data, sentiment_score)
            
            return {
                'symbol': symbol,
                'unusual_calls': data.get('volume', 0) if data.get('type') == 'call' else 0,
                'unusual_puts': data.get('volume', 0) if data.get('type') == 'put' else 0,
                'sentiment': sentiment,
                'sentiment_score': round(sentiment_score, 1),
                'premium_spent': calls_premium - puts_premium,  # Net bullish premium
                'flow_score': round(flow_score, 1),
                'timestamp': datetime.fromisoformat(
                    data.get('created_at', datetime.utcnow().isoformat()).replace('Z', '+00:00')
                )
            }
        
        except Exception as e:
            logger.error(f"Error fetching unusual activity for {symbol}: {str(e)}")
            return None
    
    def get_dark_pool_activity(self, symbol):
        """
        Get dark pool activity for a symbol
        
        Args:
            symbol (str): Stock ticker
        
        Returns:
            dict: {
                'symbol': str,
                'dark_pool_volume': int,    # Shares traded in dark pools today
                'dark_pool_price': float,   # Average dark pool price
                'net_flow': str,            # 'buying', 'selling', 'neutral'
                'large_blocks': int,        # Number of block trades (>100k shares)
                'timestamp': datetime
            }
        """
        if not self.enabled:
            return None
        
        try:
            response = requests.get(
                f'{self.base_url}/api/darkpool/{symbol}',
                headers=self.headers,
                params={'limit': 100},
                timeout=10
            )
            
            if response.status_code != 200:
                return None
            
            payload = response.json()
            data_list = payload.get('data', []) if isinstance(payload, dict) else []
            if not data_list:
                return None
            data = data_list[0]
            
            return {
                'symbol': symbol,
                'dark_pool_volume': data.get('shares', 0),
                'dark_pool_price': data.get('price', 0),
                'net_flow': data.get('net_flow', 'neutral'),
                'large_blocks': data.get('block_trades', 0),
                'timestamp': datetime.fromisoformat(
                    data.get('executed_at', datetime.utcnow().isoformat()).replace('Z', '+00:00')
                )
            }
        
        except Exception as e:
            logger.error(f"Error fetching dark pool for {symbol}: {str(e)}")
            return None
    
    def _calculate_flow_score(self, flow_data, sentiment_score):
        """
        Calculate flow score (0-100) for timing indicator
        
        Higher score = better timing to enter
        Lower score = wait or skip
        
        Factors:
        - Unusual volume (higher = better)
        - Sentiment strength (extreme bullish/bearish = better)
        - Premium size (larger = more conviction)
        - Consistency (multiple large trades = better)
        """
        score = 50  # Start neutral
        
        # Factor 1: Premium size (conviction)
        premium = float(flow_data.get('total_premium', 0) or 0)
        if premium >= 5_000_000:  # >$5M
            score += 15
        elif premium >= 2_000_000:
            score += 12
        elif premium >= 1_000_000:
            score += 8
        elif premium >= 500_000:
            score += 5
        
        # Factor 2: Volume vs OI ratio
        try:
            ratio = float(flow_data.get('volume_oi_ratio', 0) or 0)
        except (TypeError, ValueError):
            ratio = 0.0
        if ratio >= 0.5:
            score += 15
        elif ratio >= 0.25:
            score += 10
        elif ratio >= 0.1:
            score += 5
        
        # Factor 3: Trade characteristics
        volume = flow_data.get('volume', 0) or 0
        if volume >= 500:
            score += 10
        elif volume >= 200:
            score += 6
        elif volume >= 100:
            score += 3
        
        trade_count = flow_data.get('trade_count', 0) or 0
        if trade_count >= 10:
            score += 6
        elif trade_count >= 5:
            score += 3
        
        if flow_data.get('has_sweep'):
            score += 10
        if flow_data.get('has_floor'):
            score += 8
        if flow_data.get('has_multileg'):
            score += 4
        if flow_data.get('all_opening_trades'):
            score += 5
        
        # Factor 4: Sentiment strength
        if sentiment_score >= 75 or sentiment_score <= 25:
            score += 10
        elif sentiment_score >= 65 or sentiment_score <= 35:
            score += 5
        
        # For bearish flow (puts), invert score to reflect caution
        if flow_data.get('type') == 'put':
            score = 100 - score
        
        # Cap at 0-100
        return max(0, min(100, score))
    
    def get_flow_summary_for_symbols(self, symbols, max_symbols=20):
        """
        Get flow summary for multiple symbols
        
        Args:
            symbols (list): List of stock tickers
            max_symbols (int): Max symbols to fetch (rate limit protection)
        
        Returns:
            dict: {
                'AAPL': {flow_data},
                'TSLA': {flow_data},
                ...
            }
        """
        if not self.enabled:
            logger.info("Unusual Whales disabled - skipping flow data")
            return {}
        
        results = {}
        
        # Limit to max_symbols to avoid rate limits
        symbols_to_fetch = symbols[:max_symbols]
        
        logger.info(f"📊 Fetching Unusual Whales flow data for {len(symbols_to_fetch)} symbols...")
        
        for symbol in symbols_to_fetch:
            try:
                # Get unusual activity
                unusual = self.get_unusual_activity(symbol)
                
                # Get dark pool (optional - may hit rate limits)
                # dark_pool = self.get_dark_pool_activity(symbol)
                
                if unusual:
                    results[symbol] = unusual
                    logger.debug(f"  ✅ {symbol}: Flow score {unusual['flow_score']:.0f}/100 ({unusual['sentiment']})")
                else:
                    logger.debug(f"  ⚠️  {symbol}: No unusual activity")
            
            except Exception as e:
                logger.warning(f"  ❌ {symbol}: Error - {str(e)}")
                continue
        
        logger.info(f"✅ Fetched flow data for {len(results)}/{len(symbols_to_fetch)} symbols")
        
        return results
    
    def add_flow_signals_to_position(self, position):
        """
        Add Unusual Whales flow signals to a SuggestedPosition
        
        Modifies position object to include:
        - flow_score (0-100)
        - flow_sentiment ('bullish', 'bearish', 'neutral')
        - flow_timing_indicator ('🟢 ENTER', '🟡 WAIT', '🔴 SKIP')
        - Updated ai_score (boosted by flow)
        
        Args:
            position: SuggestedPosition object
        
        Returns:
            bool: True if flow data added, False if not available
        """
        if not self.enabled:
            return False
        
        try:
            # Get flow data
            flow_data = self.get_unusual_activity(position.symbol)
            
            if not flow_data:
                return False
            
            # Add flow score to position notes
            flow_notes = f"\n\n💎 Unusual Whales Flow:\n"
            flow_notes += f"  • Flow Score: {flow_data['flow_score']:.0f}/100\n"
            flow_notes += f"  • Sentiment: {flow_data['sentiment'].upper()} ({flow_data['sentiment_score']:.0f}%)\n"
            flow_notes += f"  • Unusual Calls: {flow_data['unusual_calls']}\n"
            flow_notes += f"  • Unusual Puts: {flow_data['unusual_puts']}\n"
            flow_notes += f"  • Net Premium: ${flow_data['premium_spent']:,.0f}\n"
            
            # Determine timing indicator
            flow_score = flow_data['flow_score']
            if flow_score >= 75:
                timing = '🟢 ENTER NOW (Heavy buying flow)'
                ai_boost = 20
            elif flow_score >= 50:
                timing = '🟡 OK TO ENTER (Normal flow)'
                ai_boost = 10
            else:
                timing = '🔴 WAIT/SKIP (Heavy selling flow)'
                ai_boost = -20
            
            flow_notes += f"  • Timing: {timing}\n"
            
            # Append to existing notes
            if position.notes:
                position.notes += flow_notes
            else:
                position.notes = flow_notes
            
            # Boost AI score based on flow
            if position.ai_score:
                position.ai_score += ai_boost
            else:
                position.ai_score = 50 + ai_boost
            
            position.save()
            
            logger.info(f"✅ {position.symbol}: Flow score {flow_score:.0f}, AI boost {ai_boost:+d}")
            
            return True
        
        except Exception as e:
            logger.error(f"Error adding flow signals to {position.symbol}: {str(e)}")
            return False

