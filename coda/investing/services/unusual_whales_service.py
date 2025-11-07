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
from django.core.cache import cache
from django.utils import timezone
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
        self.cache_enabled = getattr(settings, 'UW_CACHE_ENABLED', True)
        self.cache_ttl = int(getattr(settings, 'UW_CACHE_TTL_SECONDS', 600) or 600)
        self.last_fetch_stats = None
    
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
            self.last_fetch_stats = {
                'requested': len(symbols or []),
                'cache_hits': 0,
                'api_calls': 0,
                'ttl': self.cache_ttl,
            }
            return {}

        symbols = symbols or []

        unique_symbols = []
        seen = set()
        for symbol in symbols:
            if not symbol:
                continue
            normalized = symbol.upper().strip()
            if normalized in seen:
                continue
            seen.add(normalized)
            unique_symbols.append(normalized)

        symbols_to_consider = unique_symbols[:max_symbols]
        results = {}
        cache_hits = 0
        api_calls = 0
        missing_symbols = []

        for symbol in symbols_to_consider:
            cached = self._get_cached_flow(symbol)
            if cached:
                cache_hits += 1
                results[symbol] = {**cached, 'cache_source': 'cache'}
            else:
                missing_symbols.append(symbol)

        if missing_symbols:
            logger.info(
                "📊 Fetching Unusual Whales flow data for %s symbols (cache hits: %s)...",
                len(missing_symbols),
                cache_hits,
            )

        for symbol in missing_symbols:
            try:
                unusual = self.get_unusual_activity(symbol)
                api_calls += 1
                if unusual:
                    self._set_cached_flow(symbol, unusual)
                    results[symbol] = {**unusual, 'cache_source': 'live'}
                    logger.debug(
                        "  ✅ %s: Flow score %s/100 (%s)",
                        symbol,
                        f"{unusual['flow_score']:.0f}",
                        unusual['sentiment'],
                    )
                else:
                    logger.debug(f"  ⚠️  {symbol}: No unusual activity")
            except Exception as e:
                logger.warning(f"  ❌ {symbol}: Error - {str(e)}")
                continue

        logger.info(
            "✅ Flow data ready for %s/%s symbols (cache hits=%s, api_calls=%s)",
            len(results),
            len(symbols_to_consider),
            cache_hits,
            api_calls,
        )

        self.last_fetch_stats = {
            'requested': len(symbols_to_consider),
            'cache_hits': cache_hits,
            'api_calls': api_calls,
            'ttl': self.cache_ttl,
        }

        return results
    
    def apply_flow_to_suggestions(self, suggestions):
        """Apply Unusual Whales data to a list of SuggestedPosition objects."""
        from .position_scoring_service import PositionScoringService

        if not self.enabled or not suggestions:
            return {'enriched': 0, 'symbols_requested': len(suggestions) if suggestions else 0}

        symbols = list({s.symbol for s in suggestions if getattr(s, 'symbol', None)})
        if not symbols:
            return {'enriched': 0, 'symbols_requested': 0}

        flow_map = self.get_flow_summary_for_symbols(symbols, max_symbols=len(symbols))
        if not flow_map:
            return {'enriched': 0, 'symbols_requested': len(symbols)}

        scorer = PositionScoringService()
        enriched = 0

        for suggestion in suggestions:
            flow_data = flow_map.get(str(suggestion.symbol).upper())
            if not flow_data:
                continue

            metadata = suggestion.api_response_data or {}
            whales_meta = metadata.get('unusual_whales', {})
            base_score = whales_meta.get('base_ai_score', float(suggestion.ai_score or 0))

            flow_score = flow_data['flow_score']
            if flow_score >= 75:
                timing = '🟢 ENTER NOW (Heavy buying flow detected!)'
                entry_window = 'Next 1-2 sessions (re-check flow within 24h)'
                ai_boost = 20
            elif flow_score >= 50:
                timing = '🟡 OK TO ENTER (Normal flow)'
                entry_window = 'Within the next 2-4 sessions (stale after ~48h)'
                ai_boost = 10
            else:
                timing = '🔴 WAIT/SKIP (Heavy selling flow detected!)'
                entry_window = 'Hold off until new bullish flow appears'
                ai_boost = -20

            adjusted_score = max(0, min(100, base_score + ai_boost))
            suggestion.ai_score = Decimal(str(adjusted_score))
            suggestion.ai_rating = scorer._get_rating(float(suggestion.ai_score))

            whales_meta.update({
                'symbol': suggestion.symbol,
                'flow_score': float(flow_data.get('flow_score', 0)),
                'sentiment': flow_data.get('sentiment'),
                'sentiment_score': float(flow_data.get('sentiment_score', 0)),
                'unusual_calls': flow_data.get('unusual_calls'),
                'unusual_puts': flow_data.get('unusual_puts'),
                'premium_spent': flow_data.get('premium_spent'),
                'volume_oi_ratio': flow_data.get('volume_oi_ratio'),
                'timing_signal': timing,
                'entry_window': entry_window,
                'base_ai_score': base_score,
                'last_updated': timezone.now().isoformat(),
            })

            metadata['unusual_whales'] = whales_meta
            suggestion.api_response_data = metadata
            suggestion.notes = self._inject_flow_notes(suggestion.notes, whales_meta)
            suggestion.save()
            enriched += 1

        return {
            'enriched': enriched,
            'symbols_requested': len(symbols),
            'flow_map': flow_map,
        }

    def _inject_flow_notes(self, existing_notes, whales_meta):
        note_header = '💎 Unusual Whales Flow:'
        base_notes = (existing_notes or '').split(note_header)[0].rstrip()

        entry_window = whales_meta.get('entry_window')
        timing_text = whales_meta.get('timing_signal', 'N/A')
        if entry_window:
            timing_text = f"{timing_text} — Window: {entry_window}"

        flow_lines = [
            note_header,
            f"  • Flow Score: {whales_meta.get('flow_score', 0):.0f}/100",
            f"  • Sentiment: {str(whales_meta.get('sentiment', '')).upper()} ({whales_meta.get('sentiment_score', 0):.0f}%)",
            f"  • Unusual Calls: {whales_meta.get('unusual_calls', 0)}",
            f"  • Unusual Puts: {whales_meta.get('unusual_puts', 0)}",
            f"  • Net Premium: ${whales_meta.get('premium_spent', 0):,.0f}",
            f"  • Timing: {timing_text}",
        ]

        combined = base_notes
        if combined:
            combined += '\n\n'
        combined += '\n'.join(flow_lines)
        return combined

    def _cache_key(self, symbol: str) -> str:
        return f"uw:flow:{symbol.upper()}"

    def _get_cached_flow(self, symbol: str):
        if not self.cache_enabled:
            return None
        return cache.get(self._cache_key(symbol))

    def _set_cached_flow(self, symbol: str, data: dict) -> None:
        if not self.cache_enabled:
            return
        try:
            cache.set(self._cache_key(symbol), data, self.cache_ttl)
        except Exception as exc:
            logger.debug("UW cache set failed for %s: %s", symbol, exc)

