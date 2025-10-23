# AI-Powered Options Analyzer
**Feature:** Automated Options Analysis & Recommendation System  
**Data Source:** OptionPlay API + AI Analysis  
**Output:** Top 10 Recommended Positions  
**Date:** October 22, 2025  
**Status:** 🤖 AI Enhancement Design

---

## 🎯 Feature Overview

### **What It Does**
An **intelligent options scanner** that:
1. Fetches live options data from OptionPlay or similar APIs
2. Applies CODA's strict trading rules to filter candidates
3. Uses AI to analyze and score each opportunity
4. Ranks by expected return and risk profile
5. Recommends top 10 positions for each managed account
6. Provides detailed analysis for each recommendation

### **Business Value**
- ⚡ **Speed**: Analyze 1,000+ options in seconds vs hours manually
- 🎯 **Accuracy**: Consistent rule application, no human error
- 📈 **Performance**: Higher win rate through data-driven decisions
- 💰 **Scalability**: Can manage 50+ client accounts simultaneously
- 🤖 **24/7**: Continuous market scanning

---

## 🏗️ System Architecture

### **AI Analysis Pipeline**

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: DATA COLLECTION                                         │
│ ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│ │ OptionPlay   │  │  yfinance    │  │ Market Data  │          │
│ │     API      │  │     API      │  │   Provider   │          │
│ └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└────────┼──────────────────┼──────────────────┼──────────────────┘
         │                  │                  │
         └──────────────────┴──────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────────┐
│ STEP 2: DATA AGGREGATION & ENRICHMENT                           │
│ - Combine data from multiple sources                            │
│ - Calculate Greeks (Delta, Theta, Gamma, Vega)                  │
│ - Add technical indicators (RSI, IV Rank, etc.)                 │
│ - Fetch company fundamentals (earnings, P/E, etc.)              │
└───────────────────────────┬──────────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────────┐
│ STEP 3: RULE-BASED FILTERING                                    │
│ Apply CODA Trading Rules:                                        │
│ ✓ IV Rank > 30%                                                 │
│ ✓ Delta between 0.25-0.35                                       │
│ ✓ DTE between 30-45 days                                        │
│ ✓ Liquidity > 100 contracts/day                                 │
│ ✓ No earnings within expiration                                 │
│ ✓ Stock price > $50 (avoid penny stocks)                        │
│ ✓ Premium > $100 per contract                                   │
│ Result: 1000+ options → ~50-100 candidates                      │
└───────────────────────────┬──────────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────────┐
│ STEP 4: AI SCORING & RANKING                                    │
│ ┌────────────────────────────────────────────────────────────┐ │
│ │ AI Analysis Engine (GPT-4 or Custom ML Model)              │ │
│ │                                                             │ │
│ │ For each candidate, analyze:                               │ │
│ │ • Technical Setup (chart patterns, support/resistance)     │ │
│ │ • Fundamental Strength (company financials, sector)        │ │
│ │ • Market Sentiment (news, social media, insider trading)   │ │
│ │ • Historical Performance (past trades on same symbol)      │ │
│ │ • Risk/Reward Ratio (probability of profit vs max loss)    │ │
│ │                                                             │ │
│ │ Output: Score 0-100 for each position                      │ │
│ └────────────────────────────────────────────────────────────┘ │
└───────────────────────────┬──────────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────────┐
│ STEP 5: RANKING & OPTIMIZATION                                  │
│ - Sort by AI score (highest first)                              │
│ - Apply diversification (max 2 per sector)                      │
│ - Optimize capital allocation                                   │
│ - Check correlation between positions                           │
│ Result: Top 10 optimized recommendations                        │
└───────────────────────────┬──────────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────────┐
│ STEP 6: OUTPUT & PRESENTATION                                   │
│ ┌───────────────────┐  ┌──────────────────┐                    │
│ │ Trader Dashboard  │  │ Email Report     │                    │
│ │ Top 10 List       │  │ Top 10 with      │                    │
│ │ with Details      │  │ Analysis         │                    │
│ └───────────────────┘  └──────────────────┘                    │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🔌 Data Source Integration

### **Option 1: OptionPlay API** (Recommended)

#### **API Capabilities:**
- ✅ Real-time options chain data
- ✅ Greeks calculations (Delta, Theta, Gamma, Vega)
- ✅ Implied volatility data
- ✅ Volume and open interest
- ✅ Historical options data
- ✅ Earnings calendar

#### **Integration Code:**

```python
import requests
from decimal import Decimal
from datetime import date, timedelta

class OptionPlayAPI:
    """
    Integration with OptionPlay API for options data
    """
    
    BASE_URL = "https://api.optionplay.com/v1"
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    def get_options_chain(self, symbol, expiration_min_days=30, expiration_max_days=45):
        """
        Fetch options chain for symbol within date range
        
        Args:
            symbol: Stock ticker (e.g., 'AAPL')
            expiration_min_days: Minimum days to expiration
            expiration_max_days: Maximum days to expiration
        
        Returns:
            List of option contracts with full data
        """
        url = f"{self.BASE_URL}/options/chain"
        
        min_date = date.today() + timedelta(days=expiration_min_days)
        max_date = date.today() + timedelta(days=expiration_max_days)
        
        params = {
            'symbol': symbol,
            'expirationDateMin': min_date.isoformat(),
            'expirationDateMax': max_date.isoformat(),
            'optionType': 'put',  # or 'call'
            'includeGreeks': True
        }
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        
        return response.json()['options']
    
    def get_iv_rank(self, symbol):
        """
        Get implied volatility rank for symbol
        
        Returns:
            Float between 0-100 (percentage)
        """
        url = f"{self.BASE_URL}/volatility/iv-rank"
        
        params = {'symbol': symbol}
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        
        return response.json()['iv_rank']
    
    def get_earnings_date(self, symbol):
        """
        Get next earnings date for symbol
        
        Returns:
            Date object or None
        """
        url = f"{self.BASE_URL}/fundamentals/earnings"
        
        params = {'symbol': symbol}
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        
        earnings_data = response.json()
        if earnings_data.get('next_earnings_date'):
            return date.fromisoformat(earnings_data['next_earnings_date'])
        
        return None
    
    def scan_market_for_opportunities(self, strategy='short_put', min_premium=100):
        """
        Scan entire market for options matching criteria
        
        Returns:
            List of options matching basic criteria
        """
        url = f"{self.BASE_URL}/screener/scan"
        
        params = {
            'optionType': 'put' if 'put' in strategy else 'call',
            'minPremium': min_premium,
            'minDaysToExpiry': 30,
            'maxDaysToExpiry': 45,
            'minIVRank': 30,
            'minVolume': 100
        }
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        
        return response.json()['results']
```

### **Option 2: Custom Data Aggregator**

If OptionPlay API isn't available, build custom aggregator:

```python
class CustomOptionsDataAggregator:
    """
    Aggregate options data from multiple free sources
    """
    
    def __init__(self):
        self.yfinance_available = True  # Already in codebase
    
    def get_options_data(self, symbol):
        """
        Aggregate options data from yfinance + other sources
        """
        import yfinance as yf
        
        # Get stock data
        ticker = yf.Ticker(symbol)
        
        # Get options expiration dates
        expirations = ticker.options
        
        # Filter for 30-45 day expirations
        target_expirations = self._filter_expirations(expirations, 30, 45)
        
        options_data = []
        for exp_date in target_expirations:
            # Get options chain
            opt_chain = ticker.option_chain(exp_date)
            
            # Process puts
            for _, row in opt_chain.puts.iterrows():
                options_data.append({
                    'symbol': symbol,
                    'type': 'put',
                    'strike': row['strike'],
                    'expiration': exp_date,
                    'bid': row['bid'],
                    'ask': row['ask'],
                    'last_price': row['lastPrice'],
                    'volume': row['volume'],
                    'open_interest': row['openInterest'],
                    'implied_volatility': row['impliedVolatility'],
                    'delta': self._estimate_delta(row, 'put'),
                    'theta': self._estimate_theta(row)
                })
        
        return options_data
    
    def _estimate_delta(self, option_row, option_type):
        """Estimate delta from Black-Scholes if not provided"""
        # Simplified estimation or use external library
        # For puts: delta is negative, typically -0.10 to -0.50
        return -0.30  # Placeholder
    
    def _estimate_theta(self, option_row):
        """Estimate theta (time decay)"""
        # Positive theta for sold options
        return 0.15  # Placeholder
```

---

## 🤖 AI Analysis Engine

### **Service: `ai_options_analyzer_service.py`**

```python
"""
AI-Powered Options Analysis Service

Uses OpenAI GPT-4 or custom ML model to analyze options opportunities
and recommend top positions based on CODA's trading rules
"""

import json
import openai
from typing import List, Dict
from decimal import Decimal
from datetime import date

from django.conf import settings
from ..models import ManagedTradingAccount, OptionsPosition


class AIOptionsAnalyzerService:
    """
    AI-powered options analysis and recommendation engine
    """
    
    def __init__(self, managed_account: ManagedTradingAccount):
        self.account = managed_account
        self.api_key = settings.OPENAI_API_KEY
        openai.api_key = self.api_key
        
        # Trading rules for this account
        self.trading_rules = self._load_trading_rules()
    
    def analyze_and_recommend(self, strategy='short_put', max_recommendations=10):
        """
        Main method: Fetch data, analyze with AI, return top recommendations
        
        Returns:
            List of top 10 recommended positions with analysis
        """
        # Step 1: Fetch options data
        print("📡 Fetching options data from OptionPlay...")
        options_data = self._fetch_options_data(strategy)
        print(f"   Found {len(options_data)} options in market")
        
        # Step 2: Apply rule-based filtering
        print("📋 Applying CODA trading rules...")
        filtered_options = self._apply_trading_rules(options_data)
        print(f"   {len(filtered_options)} options passed rules")
        
        # Step 3: AI analysis and scoring
        print("🤖 AI analyzing opportunities...")
        scored_options = self._ai_analysis(filtered_options)
        print(f"   Scored {len(scored_options)} opportunities")
        
        # Step 4: Rank and optimize
        print("🎯 Ranking and optimizing...")
        top_recommendations = self._rank_and_optimize(scored_options, max_recommendations)
        
        # Step 5: Generate detailed analysis
        print("📊 Generating detailed analysis...")
        recommendations = self._generate_recommendations(top_recommendations)
        
        print(f"✅ Complete! {len(recommendations)} recommendations ready")
        
        return recommendations
    
    def _fetch_options_data(self, strategy):
        """
        Fetch options data from API
        """
        # Define watchlist (S&P 500 top stocks)
        watchlist = self._get_watchlist()
        
        options_data = []
        api = OptionPlayAPI(settings.OPTIONPLAY_API_KEY)
        
        for symbol in watchlist:
            try:
                # Get options chain
                chain = api.get_options_chain(symbol)
                
                # Get IV Rank
                iv_rank = api.get_iv_rank(symbol)
                
                # Get earnings date
                earnings_date = api.get_earnings_date(symbol)
                
                # Process each option
                for option in chain:
                    option['symbol'] = symbol
                    option['iv_rank'] = iv_rank
                    option['earnings_date'] = earnings_date
                    options_data.append(option)
                    
            except Exception as e:
                print(f"   ⚠️ Error fetching {symbol}: {e}")
                continue
        
        return options_data
    
    def _apply_trading_rules(self, options_data):
        """
        Apply CODA's strict trading rules to filter options
        """
        filtered = []
        
        for option in options_data:
            # Rule 1: IV Rank > 30% (need volatility for good premium)
            if option.get('iv_rank', 0) < 30:
                continue
            
            # Rule 2: Delta between 0.25-0.35 (optimal probability)
            delta = abs(option.get('delta', 0))
            if delta < 0.25 or delta > 0.35:
                continue
            
            # Rule 3: DTE between 30-45 days (optimal time decay)
            dte = option.get('days_to_expiry', 0)
            if dte < 30 or dte > 45:
                continue
            
            # Rule 4: Premium > $100 (worth the capital)
            premium = option.get('bid', 0) * 100  # Premium per contract
            if premium < 100:
                continue
            
            # Rule 5: Volume > 100 (liquidity requirement)
            if option.get('volume', 0) < 100:
                continue
            
            # Rule 6: Open Interest > 50 (liquidity)
            if option.get('open_interest', 0) < 50:
                continue
            
            # Rule 7: Stock price > $50 (avoid penny stocks)
            if option.get('stock_price', 0) < 50:
                continue
            
            # Rule 8: No earnings within expiration period
            earnings_date = option.get('earnings_date')
            expiration = option.get('expiration_date')
            if earnings_date and expiration:
                if earnings_date < expiration:
                    continue
            
            # Rule 9: Capital required <= account max position size
            capital_required = option['strike'] * 100  # For cash-secured put
            if capital_required > self.account.max_position_risk * float(self.account.current_balance) / 100:
                continue
            
            # Passed all rules!
            filtered.append(option)
        
        return filtered
    
    def _ai_analysis(self, options_list):
        """
        Use AI to analyze and score each option
        """
        scored_options = []
        
        # Process in batches to optimize API calls
        batch_size = 10
        for i in range(0, len(options_list), batch_size):
            batch = options_list[i:i+batch_size]
            
            # Prepare data for AI
            analysis_prompt = self._create_analysis_prompt(batch)
            
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": analysis_prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for consistent analysis
                max_tokens=2000
            )
            
            # Parse AI response
            ai_analysis = json.loads(response.choices[0].message.content)
            
            # Merge AI scores with option data
            for option, analysis in zip(batch, ai_analysis['options']):
                option['ai_score'] = analysis['score']
                option['ai_reasoning'] = analysis['reasoning']
                option['risk_level'] = analysis['risk_level']
                option['confidence'] = analysis['confidence']
                scored_options.append(option)
        
        return scored_options
    
    def _create_analysis_prompt(self, options_batch):
        """
        Create prompt for AI analysis
        """
        options_summary = []
        for opt in options_batch:
            options_summary.append({
                'symbol': opt['symbol'],
                'strike': opt['strike'],
                'expiration': str(opt['expiration_date']),
                'premium': opt['bid'] * 100,
                'delta': opt['delta'],
                'iv_rank': opt['iv_rank'],
                'stock_price': opt['stock_price'],
                'volume': opt['volume']
            })
        
        prompt = f"""
Analyze these {len(options_batch)} options trading opportunities for a cash-secured put strategy.
Account: ${self.account.current_balance:,.0f}
Risk Tolerance: Moderate
Target: Monthly income generation with capital preservation

Options Data:
{json.dumps(options_summary, indent=2)}

For each option, provide:
1. Score (0-100): Overall attractiveness of the trade
2. Risk Level (low/medium/high): Based on all factors
3. Confidence (0-100): How confident are you in this trade
4. Reasoning: 2-3 sentence analysis covering:
   - Technical setup
   - Risk/reward profile
   - Why this is a good/bad opportunity

Return JSON format:
{{
    "options": [
        {{
            "symbol": "AAPL",
            "score": 85,
            "risk_level": "low",
            "confidence": 90,
            "reasoning": "Strong technical support at $165. IV Rank of 45 provides good premium. Apple's fundamentals are solid with upcoming product launches. Excellent risk/reward ratio."
        }}
    ]
}}

Prioritize:
- Low risk positions (strong companies, good technical support)
- High probability of profit (delta 0.25-0.35)
- Good premium relative to risk
- Diversification across sectors
"""
        return prompt
    
    def _get_system_prompt(self):
        """
        System prompt for AI analysis
        """
        return """
You are an expert options trader with 20+ years of experience.
You specialize in conservative income-generating strategies with high win rates.
You prioritize capital preservation while generating consistent returns.

Your analysis should consider:
1. Technical Analysis: Chart patterns, support/resistance, trends
2. Fundamental Analysis: Company strength, sector health, financials
3. Market Sentiment: News, market conditions, volatility
4. Risk/Reward: Probability of profit vs maximum loss
5. Liquidity: Ability to enter and exit positions easily

Be conservative and realistic. Only recommend high-quality setups.
"""
    
    def _rank_and_optimize(self, scored_options, max_recommendations):
        """
        Rank options and optimize for diversification
        """
        # Sort by AI score (highest first)
        sorted_options = sorted(scored_options, key=lambda x: x['ai_score'], reverse=True)
        
        # Apply diversification
        recommendations = []
        sectors_used = {}
        
        for option in sorted_options:
            # Get sector for this symbol
            sector = self._get_sector(option['symbol'])
            
            # Check sector diversification (max 2 per sector)
            if sectors_used.get(sector, 0) >= 2:
                continue
            
            # Check we're not duplicating symbols
            if option['symbol'] in [r['symbol'] for r in recommendations]:
                continue
            
            # Add to recommendations
            recommendations.append(option)
            sectors_used[sector] = sectors_used.get(sector, 0) + 1
            
            # Stop when we have enough
            if len(recommendations) >= max_recommendations:
                break
        
        return recommendations
    
    def _generate_recommendations(self, top_options):
        """
        Generate detailed recommendations with all analysis
        """
        recommendations = []
        
        for i, option in enumerate(top_options, 1):
            rec = {
                'rank': i,
                'symbol': option['symbol'],
                'strategy': 'Cash-Secured Put',
                'strike': option['strike'],
                'expiration': option['expiration_date'],
                'days_to_expiry': option['days_to_expiry'],
                'premium': option['bid'] * 100,
                'capital_required': option['strike'] * 100,
                'max_profit': option['bid'] * 100,
                'max_loss': (option['strike'] * 100) - (option['bid'] * 100),
                'delta': option['delta'],
                'theta': option['theta'],
                'iv_rank': option['iv_rank'],
                'stock_price': option['stock_price'],
                'distance_to_strike': ((option['stock_price'] - option['strike']) / option['stock_price']) * 100,
                
                # AI Analysis
                'ai_score': option['ai_score'],
                'risk_level': option['risk_level'],
                'confidence': option['confidence'],
                'analysis': option['ai_reasoning'],
                
                # Calculated Metrics
                'expected_return': (option['bid'] * 100 / (option['strike'] * 100)) * 100,
                'probability_of_profit': self._estimate_pop(option['delta']),
                'risk_reward_ratio': (option['bid'] * 100) / ((option['strike'] * 100) - (option['bid'] * 100)),
                
                # Account Fit
                'fits_account': self._check_account_fit(option)
            }
            
            recommendations.append(rec)
        
        return recommendations
    
    def _estimate_pop(self, delta):
        """
        Estimate probability of profit from delta
        For short puts, PoP ≈ 100 - abs(delta * 100)
        """
        return round(100 - abs(delta * 100), 1)
    
    def _check_account_fit(self, option):
        """
        Check if position fits account parameters
        """
        capital_required = option['strike'] * 100
        available_power = self.account.available_buying_power
        
        return capital_required <= available_power
    
    def _get_watchlist(self):
        """
        Get watchlist of quality stocks to scan
        """
        # S&P 500 top 50 stocks by market cap
        return [
            # Technology
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA',
            # Finance
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C',
            # Healthcare
            'JNJ', 'UNH', 'PFE', 'ABBV', 'TMO', 'LLY',
            # Consumer
            'WMT', 'HD', 'PG', 'KO', 'PEP', 'COST', 'NKE',
            # Industrial
            'BA', 'CAT', 'UPS', 'GE', 'MMM',
            # Energy
            'XOM', 'CVX', 'COP',
            # Communications
            'DIS', 'NFLX', 'CMCSA',
            # Utilities
            'NEE', 'DUK'
        ]
    
    def _get_sector(self, symbol):
        """
        Get sector for symbol
        """
        sector_map = {
            # Technology
            'AAPL': 'Technology', 'MSFT': 'Technology', 'GOOGL': 'Technology',
            'AMZN': 'Technology', 'NVDA': 'Technology', 'META': 'Technology',
            'TSLA': 'Technology', 'NFLX': 'Technology',
            
            # Finance
            'JPM': 'Finance', 'BAC': 'Finance', 'WFC': 'Finance',
            'GS': 'Finance', 'MS': 'Finance', 'C': 'Finance',
            
            # Healthcare
            'JNJ': 'Healthcare', 'UNH': 'Healthcare', 'PFE': 'Healthcare',
            'ABBV': 'Healthcare', 'TMO': 'Healthcare', 'LLY': 'Healthcare',
            
            # Consumer
            'WMT': 'Consumer', 'HD': 'Consumer', 'PG': 'Consumer',
            'KO': 'Consumer', 'PEP': 'Consumer', 'COST': 'Consumer',
            'NKE': 'Consumer', 'DIS': 'Consumer',
            
            # Industrial
            'BA': 'Industrial', 'CAT': 'Industrial', 'UPS': 'Industrial',
            'GE': 'Industrial', 'MMM': 'Industrial',
            
            # Energy
            'XOM': 'Energy', 'CVX': 'Energy', 'COP': 'Energy',
            
            # Communications
            'CMCSA': 'Communications',
            
            # Utilities
            'NEE': 'Utilities', 'DUK': 'Utilities'
        }
        
        return sector_map.get(symbol, 'Other')
    
    def _load_trading_rules(self):
        """
        Load trading rules for the account
        """
        rules = {}
        
        for rule in self.account.trading_rules.filter(is_active=True):
            rules[rule.rule_type] = rule.rule_config
        
        # Add default rules if not configured
        if 'position_limit' not in rules:
            rules['position_limit'] = {
                'max_position_size': 7000,
                'max_contracts': 3
            }
        
        if 'greek_limit' not in rules:
            rules['greek_limit'] = {
                'min_delta': 0.25,
                'max_delta': 0.35,
                'min_theta': 0.10
            }
        
        return rules
```

---

## 📊 AI Analysis Prompt Engineering

### **Advanced Analysis Prompt**

```python
def _create_advanced_analysis_prompt(self, options_batch):
    """
    Enhanced prompt with market context
    """
    # Get current market conditions
    market_context = self._get_market_context()
    
    prompt = f"""
MARKET CONTEXT:
- S&P 500: {market_context['sp500_trend']}
- VIX: {market_context['vix_level']}
- Overall Market Sentiment: {market_context['sentiment']}
- Economic Indicators: {market_context['economic_summary']}

ACCOUNT PARAMETERS:
- Account Size: ${self.account.current_balance:,.0f}
- Available Capital: ${self.account.available_buying_power:,.0f}
- Risk Tolerance: Moderate
- Strategy Focus: Income generation with capital preservation
- Current Positions: {self.account.positions.filter(status='open').count()}
- Current Total Risk: {self._calculate_current_risk():.1f}%

TRADING RULES (STRICT - MUST FOLLOW):
1. IV Rank: Must be > 30% (higher = better premium)
2. Delta Range: 0.25-0.35 (70-75% probability of profit)
3. Days to Expiry: 30-45 days (optimal theta decay)
4. Premium: Minimum $100 per contract
5. Liquidity: Volume >100, Open Interest >50
6. Stock Quality: Price >$50, avoid penny stocks
7. Earnings: No earnings within expiration period
8. Capital: Max $7,000 per position

OPTIONS TO ANALYZE:
{self._format_options_for_ai(options_batch)}

FOR EACH OPTION, PROVIDE:

1. **SCORE (0-100)**:
   - 90-100: Exceptional opportunity (rare)
   - 80-89: Excellent setup
   - 70-79: Good opportunity
   - 60-69: Acceptable
   - 0-59: Avoid

2. **RISK LEVEL**:
   - Low: Strong company, good support, favorable conditions
   - Medium: Decent setup but some concerns
   - High: Risky, only if comfortable with assignment

3. **CONFIDENCE (0-100)**:
   - How certain are you this trade will be profitable?

4. **DETAILED ANALYSIS** (3-5 sentences):
   - Technical: Chart pattern, support/resistance
   - Fundamental: Company strength, sector outlook
   - Market: Current conditions, sentiment
   - Risk/Reward: Probability vs potential loss
   - Recommendation: Why trade or avoid

5. **KEY FACTORS** (Bullet points):
   - Positive factors supporting the trade
   - Negative factors/concerns
   - Critical levels to watch

RETURN STRUCTURED JSON:
{{
    "market_assessment": "Brief overall market view",
    "options": [
        {{
            "symbol": "AAPL",
            "score": 85,
            "risk_level": "low",
            "confidence": 90,
            "analysis": "Detailed analysis here...",
            "key_factors": {{
                "positive": ["Factor 1", "Factor 2"],
                "negative": ["Concern 1"],
                "watch_levels": ["Support at $170", "Resistance at $185"]
            }},
            "trade_recommendation": "STRONG BUY"
        }}
    ]
}}

IMPORTANT:
- Be conservative - prioritize capital preservation
- Only recommend high-quality setups
- Consider all risk factors
- Provide actionable insights
- Score honestly (not everything is 90+)
"""
    return prompt
```

---

## 🎯 Trading Rules Engine

### **Service: `trading_rules_engine.py`**

```python
class TradingRulesEngine:
    """
    Validates positions against trading rules
    """
    
    def __init__(self, managed_account):
        self.account = managed_account
        self.rules = managed_account.trading_rules.filter(is_active=True)
    
    def validate_position(self, position_data):
        """
        Validate position against all active rules
        
        Returns:
            (is_valid, violations)
        """
        violations = []
        
        for rule in self.rules:
            violation = self._check_rule(position_data, rule)
            if violation:
                violations.append(violation)
        
        return len(violations) == 0, violations
    
    def _check_rule(self, position_data, rule):
        """
        Check individual rule
        """
        rule_type = rule.rule_type
        config = rule.rule_config
        
        if rule_type == 'position_limit':
            return self._check_position_limit(position_data, config)
        elif rule_type == 'greek_limit':
            return self._check_greek_limit(position_data, config)
        elif rule_type == 'risk_limit':
            return self._check_risk_limit(position_data, config)
        # ... other rule types
        
        return None
    
    def _check_position_limit(self, position_data, config):
        """
        Check position size limits
        """
        capital = position_data['capital_required']
        max_size = config.get('max_position_size', 7000)
        
        if capital > max_size:
            return {
                'rule': 'Position Size Limit',
                'message': f'Position requires ${capital}, max allowed ${max_size}',
                'severity': 'high'
            }
        
        return None
    
    def _check_greek_limit(self, position_data, config):
        """
        Check Greeks limits
        """
        delta = abs(position_data.get('delta', 0))
        min_delta = config.get('min_delta', 0.25)
        max_delta = config.get('max_delta', 0.35)
        
        if delta < min_delta or delta > max_delta:
            return {
                'rule': 'Delta Limit',
                'message': f'Delta {delta:.2f} outside range {min_delta}-{max_delta}',
                'severity': 'medium'
            }
        
        return None
```

---

## 📊 Output: Top 10 Recommendations

### **Sample Output JSON**

```json
{
    "generated_at": "2025-10-22T14:30:00Z",
    "account": "CODA-OPT-001",
    "account_balance": "30000.00",
    "available_capital": "13000.00",
    "market_conditions": {
        "sp500_trend": "Bullish",
        "vix": 18,
        "sentiment": "Positive"
    },
    "recommendations": [
        {
            "rank": 1,
            "symbol": "AAPL",
            "strategy": "Cash-Secured Put",
            "strike": 170.00,
            "expiration": "2025-11-22",
            "days_to_expiry": 30,
            "premium": 310.00,
            "capital_required": 17000.00,
            "max_profit": 310.00,
            "max_loss": 16690.00,
            "delta": -0.30,
            "theta": 0.16,
            "iv_rank": 45,
            "stock_price": 180.50,
            "distance_to_strike": "5.8% below",
            "expected_return": "1.82%",
            "annualized_return": "21.9%",
            "probability_of_profit": "70%",
            
            "ai_analysis": {
                "score": 88,
                "risk_level": "low",
                "confidence": 92,
                "reasoning": "Apple shows strong technical support at $170 level. IV Rank of 45 provides excellent premium collection opportunity. Company fundamentals remain solid with upcoming iPhone launch. The 5.8% downside cushion provides good safety margin. Probability of profit is high at 70%.",
                "key_factors": {
                    "positive": [
                        "Strong support level at $170",
                        "IV Rank elevated (45) - good premium",
                        "Apple fundamentals solid",
                        "No earnings until after expiration",
                        "High liquidity (>10,000 daily volume)"
                    ],
                    "negative": [
                        "Tech sector slightly overbought",
                        "Market cap very large (less upside potential)"
                    ],
                    "watch_levels": [
                        "Support: $170 (strike)",
                        "Next support: $165",
                        "Resistance: $185",
                        "50-day MA: $172"
                    ]
                },
                "recommendation": "STRONG BUY - Excellent risk/reward setup"
            },
            
            "fits_account": true,
            "sectors": "Technology",
            "earnings_date": null,
            "next_steps": "Execute 1 contract. Monitor daily. Close at 50% profit or if stock breaks $165 support."
        },
        {
            "rank": 2,
            "symbol": "MSFT",
            "strategy": "Cash-Secured Put",
            "strike": 360.00,
            "ai_analysis": {
                "score": 85,
                "reasoning": "Microsoft showing consolidation pattern with support at $360. Cloud business strong. IV Rank 48 provides good premium. Excellent probability setup."
            }
            // ... full details
        }
        // ... positions 3-10
    ],
    "portfolio_analysis": {
        "total_capital_needed": 45000.00,
        "capital_available": 30000.00,
        "recommended_to_execute": 3,
        "sector_diversification": {
            "Technology": 2,
            "Finance": 1,
            "Healthcare": 1,
            "Consumer": 1
        },
        "total_expected_monthly_return": "1.95%",
        "average_ai_score": 83,
        "average_confidence": 88
    },
    "execution_plan": "Execute top 3 positions (#1, #2, #3) for total capital of $29,500. Reserve $500 cash buffer."
}
```

---

## 🖥️ User Interface

### **Trader Dashboard: Top 10 Recommendations View**

```html
<!-- Template: recommendations_dashboard.html -->

<div class="container-fluid">
    <h2><i class="fa fa-robot"></i> AI Options Recommendations</h2>
    
    <!-- Generate Button -->
    <div class="mb-4">
        <button id="generate-recommendations" class="btn btn-primary btn-lg">
            <i class="fa fa-magic"></i> Generate Top 10 Recommendations
        </button>
        <span id="loading" style="display:none;">
            <i class="fa fa-spinner fa-spin"></i> Analyzing market...
        </span>
    </div>
    
    <!-- Recommendations Table -->
    <div id="recommendations-container">
        <table class="table table-hover">
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Symbol</th>
                    <th>Strike</th>
                    <th>Expiry</th>
                    <th>Premium</th>
                    <th>AI Score</th>
                    <th>Risk</th>
                    <th>Confidence</th>
                    <th>Expected Return</th>
                    <th>PoP</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody id="recommendations-tbody">
                <!-- Populated via AJAX -->
            </tbody>
        </table>
    </div>
    
    <!-- Detailed Analysis Modal -->
    <div class="modal" id="analysisModal">
        <!-- Shows full AI analysis for selected position -->
    </div>
</div>

<script>
$('#generate-recommendations').click(function() {
    $('#loading').show();
    
    $.ajax({
        url: '/investing/managed/api/generate-recommendations/',
        method: 'POST',
        headers: {
            'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val()
        },
        data: JSON.stringify({
            account_id: {{ account.id }},
            strategy: 'short_put',
            max_results: 10
        }),
        contentType: 'application/json',
        success: function(data) {
            displayRecommendations(data.recommendations);
            $('#loading').hide();
        },
        error: function(xhr) {
            alert('Error generating recommendations: ' + xhr.responseJSON.error);
            $('#loading').hide();
        }
    });
});

function displayRecommendations(recommendations) {
    let html = '';
    
    recommendations.forEach(function(rec) {
        let scoreClass = rec.ai_analysis.score >= 80 ? 'success' : 
                        rec.ai_analysis.score >= 70 ? 'warning' : 'secondary';
        
        html += `
            <tr>
                <td><strong>#${rec.rank}</strong></td>
                <td><strong>${rec.symbol}</strong></td>
                <td>$${rec.strike.toFixed(2)}</td>
                <td>${rec.expiration} (${rec.days_to_expiry}d)</td>
                <td class="text-success">$${rec.premium.toFixed(0)}</td>
                <td><span class="badge bg-${scoreClass}">${rec.ai_analysis.score}</span></td>
                <td><span class="badge bg-${rec.ai_analysis.risk_level === 'low' ? 'success' : 'warning'}">
                    ${rec.ai_analysis.risk_level}
                </span></td>
                <td>${rec.ai_analysis.confidence}%</td>
                <td class="text-success">${rec.expected_return.toFixed(2)}%</td>
                <td>${rec.probability_of_profit}%</td>
                <td>
                    <button class="btn btn-sm btn-info" onclick="showAnalysis(${rec.rank})">
                        <i class="fa fa-chart-line"></i> Analysis
                    </button>
                    <button class="btn btn-sm btn-success" onclick="executePosition(${rec.rank})">
                        <i class="fa fa-check"></i> Execute
                    </button>
                </td>
            </tr>
        `;
    });
    
    $('#recommendations-tbody').html(html);
}
</script>
```

---

## 🔄 Workflow Integration

### **Daily Workflow with AI**

```
06:00 AM - Pre-Market Analysis
    │
    ├─> AI generates recommendations for each account
    ├─> Email sent to trader with top 10 for each account
    └─> Dashboard updated with recommendations

09:30 AM - Market Open
    │
    ├─> Trader reviews AI recommendations
    ├─> Selects top 2-3 to execute
    ├─> One-click execution from dashboard
    └─> Positions created automatically

Throughout Day - Monitoring
    │
    ├─> AI monitors all open positions
    ├─> Generates alerts if exit criteria met
    └─> Sends notifications

04:00 PM - Market Close
    │
    ├─> AI generates end-of-day analysis
    ├─> Updates position values
    ├─> Sends daily summary
    └─> Prepares tomorrow's recommendations
```

---

## 📋 Implementation Checklist

### **Phase 1: Data Integration (Week 1)**
- [ ] Research OptionPlay API documentation
- [ ] Setup API credentials
- [ ] Create `OptionPlayAPI` wrapper class
- [ ] Test data fetching for 10 symbols
- [ ] Implement fallback to yfinance if API fails
- [ ] Create data caching layer (15-min cache)

### **Phase 2: AI Analysis Engine (Week 2)**
- [ ] Create `AIOptionsAnalyzerService` class
- [ ] Design AI prompts for analysis
- [ ] Implement OpenAI GPT-4 integration
- [ ] Test AI analysis with sample data
- [ ] Implement batch processing for efficiency
- [ ] Add error handling and retries

### **Phase 3: Rules Engine (Week 3)**
- [ ] Create `TradingRulesEngine` class
- [ ] Implement rule validation methods
- [ ] Create configurable rules system
- [ ] Test rule enforcement
- [ ] Add rule violation logging

### **Phase 4: Ranking & Optimization (Week 3)**
- [ ] Implement scoring algorithm
- [ ] Create diversification logic
- [ ] Implement capital optimization
- [ ] Test with various account sizes
- [ ] Verify top 10 selection quality

### **Phase 5: UI Implementation (Week 4)**
- [ ] Create recommendations dashboard
- [ ] Implement AJAX recommendation generation
- [ ] Create detailed analysis modal
- [ ] Add one-click execution
- [ ] Test user experience

### **Phase 6: Automation (Week 5)**
- [ ] Create scheduled task (daily 6 AM)
- [ ] Implement email delivery
- [ ] Create PDF report generation
- [ ] Setup monitoring alerts
- [ ] Test end-to-end automation

---

## 💰 Cost Analysis

### **API Costs (Estimated)**

| Service | Cost | Usage | Monthly Cost |
|---------|------|-------|--------------|
| **OptionPlay API** | $50-$200/month | 1000 requests/day | $150/month |
| **OpenAI GPT-4** | $0.03/1K tokens | ~500K tokens/month | $15/month |
| **Market Data** | Free (yfinance) | Backup data | $0 |
| **TOTAL** | | | **~$165/month** |

**ROI:** With just 1 client ($1,650/year revenue), API costs are covered 10x

---

## 🎯 Success Metrics

### **AI Analysis Quality**
- **Accuracy**: AI-recommended trades should have >75% win rate
- **Consistency**: Scores should correlate with actual performance
- **Speed**: Generate top 10 in <30 seconds
- **Reliability**: 99%+ uptime for API calls

### **Business Impact**
- **Time Savings**: 2 hours/day → 10 minutes/day (90% reduction)
- **Better Decisions**: Data-driven vs gut feeling
- **Scalability**: Can handle 50+ accounts simultaneously
- **Win Rate**: Target 80%+ (vs 70% manual)

---

## 🚀 Quick Start Guide

### **Day 1: Setup APIs**
```bash
# Install required libraries
pip install openai requests

# Set environment variables
export OPTIONPLAY_API_KEY="your_key_here"
export OPENAI_API_KEY="your_key_here"
```

### **Day 2: Test Analysis**
```python
# Django shell test
from investing.services.ai_options_analyzer_service import AIOptionsAnalyzerService
from investing.models import ManagedTradingAccount

account = ManagedTradingAccount.objects.get(account_number='CODA-OPT-001')
analyzer = AIOptionsAnalyzerService(account)

# Generate recommendations
recommendations = analyzer.analyze_and_recommend(strategy='short_put', max_recommendations=10)

# Display
for rec in recommendations:
    print(f"#{rec['rank']}: {rec['symbol']} - Score: {rec['ai_score']}")
    print(f"   {rec['analysis']}")
```

---

## ✅ Next Steps

1. **Research OptionPlay API** - Get API documentation and pricing
2. **Setup OpenAI Account** - Get GPT-4 API access
3. **Build POC** - Test with 5 symbols, verify AI quality
4. **Iterate on Prompts** - Optimize AI prompt for best results
5. **Full Implementation** - Follow 5-week plan above
6. **Go Live** - Start using for first client

---

**Feature Status:** 🤖 **READY FOR DEVELOPMENT**  
**Expected Impact:** 🚀 **TRANSFORMATIONAL** (10x efficiency improvement)  
**Investment Required:** ~$165/month (API costs)  
**ROI:** Covered by 1 client, enables scaling to 50+ clients

---

**Return to:** [README.md](README.md)

