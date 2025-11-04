"""
Technical Analysis Service using yfinance
Provides RSI, Moving Averages, Volume analysis for position validation
"""

import logging
from decimal import Decimal

logger = logging.getLogger(__name__)


def _calculate_rsi(prices, period=14):
    """Calculate RSI (Relative Strength Index)"""
    if len(prices) < period + 1:
        return None
    
    # Calculate price changes
    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    
    # Separate gains and losses
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]
    
    # Calculate average gains and losses
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    if avg_loss == 0:
        return 100
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return round(rsi, 2)


def get_technical_indicators(symbol):
    """
    Fetch technical indicators for a symbol using yfinance
    
    Returns dict with:
    - current_price: Current stock price
    - rsi: RSI (14-day)
    - rsi_signal: 'oversold', 'neutral', 'overbought'
    - ma_50: 50-day moving average
    - price_vs_ma: 'above' or 'below'
    - volume_ratio: Current volume vs 30-day average
    - technical_score: 0-30 points
    - signals: List of technical signals
    """
    try:
        # Lazy import (so it doesn't break if yfinance not installed)
        import yfinance as yf
        
        # Fetch stock data
        ticker = yf.Ticker(symbol)
        
        # Get 3 months of history for calculations
        hist = ticker.history(period='3mo')
        
        if hist.empty or len(hist) < 50:
            logger.warning(f"⚠️  {symbol}: Insufficient data for technical analysis")
            return None
        
        # Current price
        current_price = float(hist['Close'].iloc[-1])
        
        # Calculate RSI
        prices = hist['Close'].tolist()
        rsi = _calculate_rsi(prices, period=14)
        
        # RSI signal
        if rsi and rsi < 30:
            rsi_signal = 'oversold'  # Bullish!
        elif rsi and rsi > 70:
            rsi_signal = 'overbought'  # Bearish
        else:
            rsi_signal = 'neutral'
        
        # 50-day moving average
        ma_50 = float(hist['Close'].rolling(window=50).mean().iloc[-1])
        price_vs_ma = 'above' if current_price > ma_50 else 'below'
        
        # Volume analysis
        avg_volume = float(hist['Volume'].rolling(window=30).mean().iloc[-1])
        current_volume = float(hist['Volume'].iloc[-1])
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        
        # Calculate technical score (0-30 points)
        tech_score = 0
        signals = []
        
        # RSI scoring
        if rsi < 35:  # Oversold = good for short puts!
            tech_score += 15
            signals.append(f'RSI {rsi:.1f} (Oversold - Bullish!)')
        elif rsi < 50:  # Neutral-bullish
            tech_score += 10
            signals.append(f'RSI {rsi:.1f} (Neutral)')
        elif rsi < 70:  # Neutral-bearish
            tech_score += 5
            signals.append(f'RSI {rsi:.1f} (Elevated)')
        else:  # Overbought = risky!
            tech_score += 0
            signals.append(f'RSI {rsi:.1f} (Overbought - WAIT!)')
        
        # Moving average scoring
        if price_vs_ma == 'above':
            tech_score += 10
            signals.append(f'Above 50-day MA (Uptrend)')
        else:
            tech_score += 0
            signals.append(f'Below 50-day MA (Downtrend)')
        
        # Volume scoring
        if volume_ratio > 1.5:
            tech_score += 5
            signals.append(f'Volume {volume_ratio:.1f}x avg (High interest!)')
        elif volume_ratio > 0.8:
            tech_score += 3
            signals.append(f'Volume normal')
        else:
            tech_score += 0
            signals.append(f'Volume {volume_ratio:.1f}x avg (Low interest)')
        
        return {
            'current_price': round(current_price, 2),
            'rsi': rsi,
            'rsi_signal': rsi_signal,
            'ma_50': round(ma_50, 2),
            'price_vs_ma': price_vs_ma,
            'volume_ratio': round(volume_ratio, 2),
            'technical_score': tech_score,
            'signals': signals,
            'available': True
        }
        
    except ImportError:
        logger.warning("⚠️  yfinance not installed - skipping technical analysis")
        return None
    except Exception as e:
        logger.warning(f"⚠️  {symbol}: Error fetching technical data - {str(e)}")
        return None


def add_technical_analysis_to_scored_symbols(scored_symbols, max_symbols=50):
    """
    Add technical analysis to top scored symbols
    
    Args:
        scored_symbols: List of scored symbol dicts
        max_symbols: Only analyze top N (API rate limits)
    
    Returns:
        scored_symbols with technical_data added
    """
    logger.info(f"📊 Fetching technical indicators for top {max_symbols} symbols...")
    
    analyzed_count = 0
    for i, item in enumerate(scored_symbols[:max_symbols]):
        symbol = item['symbol']
        
        # Fetch technical data
        tech_data = get_technical_indicators(symbol)
        
        if tech_data:
            # Add technical score to total score
            item['technical_score'] = tech_data['technical_score']
            item['score'] += tech_data['technical_score']  # Boost total score!
            item['technical_data'] = tech_data
            item['breakdown']['technical'] = f"+{tech_data['technical_score']} ({', '.join(tech_data['signals'])})"
            
            analyzed_count += 1
            logger.debug(f"  ✅ {symbol}: RSI {tech_data['rsi']:.1f}, Score +{tech_data['technical_score']}")
        else:
            item['technical_data'] = None
            item['breakdown']['technical'] = 'N/A (No data)'
        
        # Progress
        if (i + 1) % 10 == 0:
            logger.info(f"  📊 Progress: {i + 1}/{max_symbols} analyzed")
    
    logger.info(f"✅ Technical analysis complete: {analyzed_count}/{max_symbols} symbols")
    
    # Re-sort by updated scores
    scored_symbols.sort(key=lambda x: x['score'], reverse=True)
    
    return scored_symbols

