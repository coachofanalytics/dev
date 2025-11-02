"""
OptionPlay Web Scraper Service

Scrapes high-probability options positions from OptionPlay.com using Playwright
Integrates with existing position automation system

Based on: Opions_play_automation repository
Enhanced for: SuggestedPosition model integration
"""

import logging
import os
from decimal import Decimal
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from django.conf import settings

# Optional imports (only needed when scraper is used)
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

logger = logging.getLogger(__name__)


class OptionPlayScraperService:
    """
    Scrapes options positions from OptionPlay.com
    
    Strategies supported:
    - Credit Spreads (Bull Put Spread, Bear Call Spread)
    - Short Puts (Cash-Secured)
    - Covered Calls
    """
    
    def __init__(self):
        """Initialize scraper with credentials from environment"""
        if not PANDAS_AVAILABLE:
            logger.warning("❌ pandas not installed - scraper unavailable")
            self.is_configured = False
            return
        
        self.username = os.environ.get('OPTIONPLAY_USERNAME')
        self.password = os.environ.get('OPTIONPLAY_PASSWORD')
        
        if not self.username or not self.password:
            logger.warning("OptionPlay credentials not found in environment variables")
            self.is_configured = False
        else:
            self.is_configured = True
            logger.info("✅ OptionPlay scraper configured")
    
    def fetch_all_positions(self, filters: Dict = None) -> List[Dict]:
        """
        Fetch all positions from OptionPlay (Credit Spreads, Short Puts, Covered Calls)
        
        Args:
            filters: Optional filters (min_probability, min_premium, dte_min, dte_max, etc.)
        
        Returns:
            List of position dictionaries ready for SuggestedPosition model
        """
        if not self.is_configured:
            logger.error("❌ OptionPlay not configured - missing credentials")
            return []
        
        all_positions = []
        
        try:
            # Fetch Credit Spreads
            logger.info("🔍 Fetching Credit Spreads from OptionPlay...")
            credit_spreads = self._fetch_credit_spreads()
            all_positions.extend(credit_spreads)
            logger.info(f"✅ Fetched {len(credit_spreads)} credit spreads")
        except Exception as e:
            logger.error(f"❌ Error fetching credit spreads: {e}")
        
        try:
            # Fetch Short Puts
            logger.info("🔍 Fetching Short Puts from OptionPlay...")
            short_puts = self._fetch_short_puts()
            all_positions.extend(short_puts)
            logger.info(f"✅ Fetched {len(short_puts)} short puts")
        except Exception as e:
            logger.error(f"❌ Error fetching short puts: {e}")
        
        try:
            # Fetch Covered Calls
            logger.info("🔍 Fetching Covered Calls from OptionPlay...")
            covered_calls = self._fetch_covered_calls()
            all_positions.extend(covered_calls)
            logger.info(f"✅ Fetched {len(covered_calls)} covered calls")
        except Exception as e:
            logger.error(f"❌ Error fetching covered calls: {e}")
        
        # Apply filters
        if filters:
            all_positions = self._apply_filters(all_positions, filters)
        
        logger.info(f"📊 Total positions fetched: {len(all_positions)}")
        return all_positions
    
    def _fetch_credit_spreads(self) -> List[Dict]:
        """
        Scrape credit spreads from OptionPlay
        
        Returns: List of normalized position dictionaries
        """
        try:
            from playwright.sync_api import sync_playwright
            from bs4 import BeautifulSoup
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, slow_mo=50)
                page = browser.new_page()
                
                # Login
                page.goto('https://www.optionsplay.com/hub/credit-spread-file')
                page.fill('input#Login', self.username)
                page.fill('input#Password', self.password)
                page.click("button[type=submit]")
                
                # Wait for data to load
                page.wait_for_timeout(30000)
                
                # Extract HTML
                html = page.inner_html('//*[@id="CreditSpreadFile_wrapper"]')
                browser.close()
            
            # Parse HTML to DataFrame
            soup = BeautifulSoup(html, 'html.parser')
            table = soup.select('table#CreditSpreadFile')[0]
            df = pd.read_html(str(table))[0]
            df = df.iloc[:-1, :]  # Remove last row (totals)
            
            # Save raw data for debugging
            df.to_csv('optionplay_credit_spreads.csv', index=False)
            
            # Normalize to our SuggestedPosition format
            positions = self._normalize_credit_spreads(df)
            return positions
            
        except ImportError:
            logger.error("❌ Playwright not installed. Run: pip install playwright && playwright install")
            return []
        except Exception as e:
            logger.error(f"❌ Error scraping credit spreads: {e}")
            return []
    
    def _fetch_short_puts(self) -> List[Dict]:
        """Scrape short puts from OptionPlay"""
        try:
            from playwright.sync_api import sync_playwright
            from bs4 import BeautifulSoup
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, slow_mo=50)
                page = browser.new_page()
                
                page.goto('https://www.optionsplay.com/hub/short-puts')
                page.fill('input#Login', self.username)
                page.fill('input#Password', self.password)
                page.click("button[type=submit]")
                page.wait_for_timeout(30000)
                
                html = page.inner_html('//*[@id="shortPuts_wrapper"]')
                browser.close()
            
            soup = BeautifulSoup(html, 'html.parser')
            table = soup.select('table#shortPuts')[0]
            df = pd.read_html(str(table))[0]
            df = df.iloc[:-1, :]
            
            df.to_csv('optionplay_short_puts.csv', index=False)
            
            positions = self._normalize_short_puts(df)
            return positions
            
        except Exception as e:
            logger.error(f"❌ Error scraping short puts: {e}")
            return []
    
    def _fetch_covered_calls(self) -> List[Dict]:
        """Scrape covered calls from OptionPlay"""
        try:
            from playwright.sync_api import sync_playwright
            from bs4 import BeautifulSoup
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, slow_mo=50)
                page = browser.new_page()
                
                page.goto('https://www.optionsplay.com/hub/covered-calls')
                page.fill('input#Login', self.username)
                page.fill('input#Password', self.password)
                page.click("button[type=submit]")
                page.wait_for_timeout(30000)
                
                html = page.inner_html('//*[@id="coveredCalls_wrapper"]')
                browser.close()
            
            soup = BeautifulSoup(html, 'html.parser')
            table = soup.select('table#coveredCalls')[0]
            df = pd.read_html(str(table))[0]
            df = df.iloc[:-1, :]
            
            df.to_csv('optionplay_covered_calls.csv', index=False)
            
            positions = self._normalize_covered_calls(df)
            return positions
            
        except Exception as e:
            logger.error(f"❌ Error scraping covered calls: {e}")
            return []
    
    def _normalize_credit_spreads(self, df) -> List[Dict]:
        """
        Convert OptionPlay credit spread DataFrame to our SuggestedPosition format
        
        OptionPlay columns (example):
        - Symbol, Price, Strike (Short), Strike (Long), Expiry, Premium, IV Rank, etc.
        """
        positions = []
        
        for idx, row in df.iterrows():
            try:
                # Determine if Bull Put or Bear Call based on strikes
                symbol = str(row.get('Symbol', '')).strip().upper()
                stock_price = float(str(row.get('Price', '0')).replace('$', '').replace(',', ''))
                
                # Extract strikes
                short_strike = float(str(row.get('Strike (Short)', '0')).replace('$', ''))
                long_strike = float(str(row.get('Strike (Long)', '0')).replace('$', ''))
                
                # Determine strategy type
                if short_strike < stock_price:  # Below current price = Bull Put Spread
                    strategy = 'bull_put_spread'
                    option_type = 'put'
                else:  # Above current price = Bear Call Spread
                    strategy = 'bear_call_spread'
                    option_type = 'call'
                
                # Extract other data
                expiry_str = str(row.get('Expiry', '')).strip()
                expiration_date = pd.to_datetime(expiry_str).date() if expiry_str else (datetime.now() + timedelta(days=45)).date()
                dte = (expiration_date - datetime.now().date()).days
                
                premium = float(str(row.get('Premium', '0')).replace('$', '').replace(',', ''))
                iv_rank = float(str(row.get('IV Rank', '0')).replace('%', ''))
                
                # Calculate position metrics
                spread_width = abs(short_strike - long_strike)
                capital_required = spread_width * 100  # 1 contract = 100 shares
                max_profit = premium * 100
                max_loss = capital_required - max_profit
                
                # Probability of profit (estimate from IV Rank)
                probability_of_profit = min(70 + (iv_rank / 10), 85)  # Higher IV = Higher PoP
                
                # Build position legs
                positions_data = [
                    {
                        'type': f'short_{option_type}',
                        'strike': short_strike,
                        'contracts': 1,
                        'premium': premium,
                        'delta': -0.30 if strategy == 'bull_put_spread' else 0.30,
                        'theta': 0.05
                    },
                    {
                        'type': f'long_{option_type}',
                        'strike': long_strike,
                        'contracts': 1,
                        'premium': 0,
                        'delta': -0.10 if strategy == 'bull_put_spread' else 0.10,
                        'theta': -0.02
                    }
                ]
                
                position = {
                    'symbol': symbol,
                    'strategy': strategy,
                    'positions': positions_data,
                    'expiration_date': expiration_date,
                    'dte': dte,
                    'premium_collected': Decimal(str(max_profit)),
                    'capital_required': Decimal(str(capital_required)),
                    'max_profit': Decimal(str(max_profit)),
                    'max_loss': Decimal(str(max_loss)),
                    'breakeven': Decimal(str(short_strike - (premium if strategy == 'bull_put_spread' else -premium))),
                    'probability_of_profit': Decimal(str(probability_of_profit)),
                    'position_delta': Decimal('-0.20') if strategy == 'bull_put_spread' else Decimal('0.20'),
                    'position_theta': Decimal('0.03'),
                    'position_gamma': Decimal('0.01'),
                    'position_vega': Decimal('-0.05'),
                    'ai_confidence': Decimal(str(min(75 + (iv_rank / 5), 90))),
                    'ai_reasoning': f"OptionPlay {strategy.replace('_', ' ').title()}. IV Rank: {iv_rank}%, PoP: {probability_of_profit:.1f}%"
                }
                
                positions.append(position)
                
            except Exception as e:
                logger.warning(f"⚠️ Error normalizing row {idx}: {e}")
                continue
        
        return positions
    
    def _normalize_short_puts(self, df) -> List[Dict]:
        """Convert OptionPlay short puts to our format"""
        positions = []
        
        for idx, row in df.iterrows():
            try:
                symbol = str(row.get('Symbol', '')).strip().upper()
                stock_price = float(str(row.get('Stock Price', '0')).replace('$', '').replace(',', ''))
                strike = float(str(row.get('Strike', '0')).replace('$', ''))
                premium = float(str(row.get('Premium', '0')).replace('$', '').replace(',', ''))
                
                expiry_str = str(row.get('Expiry', '')).strip()
                expiration_date = pd.to_datetime(expiry_str).date()
                dte = (expiration_date - datetime.now().date()).days
                
                capital_required = strike * 100
                max_profit = premium * 100
                max_loss = capital_required - max_profit
                
                position = {
                    'symbol': symbol,
                    'strategy': 'short_put',
                    'positions': [{
                        'type': 'short_put',
                        'strike': strike,
                        'contracts': 1,
                        'premium': premium,
                        'delta': -0.30,
                        'theta': 0.08
                    }],
                    'expiration_date': expiration_date,
                    'dte': dte,
                    'premium_collected': Decimal(str(max_profit)),
                    'capital_required': Decimal(str(capital_required)),
                    'max_profit': Decimal(str(max_profit)),
                    'max_loss': Decimal(str(max_loss)),
                    'breakeven': Decimal(str(strike - premium)),
                    'probability_of_profit': Decimal('72.0'),
                    'position_delta': Decimal('-0.30'),
                    'position_theta': Decimal('0.08'),
                    'position_gamma': Decimal('0.02'),
                    'position_vega': Decimal('-0.10'),
                    'ai_confidence': Decimal('80.0'),
                    'ai_reasoning': f"OptionPlay Cash-Secured Short Put. Strike: ${strike}, Premium: ${premium}"
                }
                
                positions.append(position)
                
            except Exception as e:
                logger.warning(f"⚠️ Error normalizing short put row {idx}: {e}")
                continue
        
        return positions
    
    def _normalize_covered_calls(self, df) -> List[Dict]:
        """Convert OptionPlay covered calls to our format"""
        positions = []
        
        for idx, row in df.iterrows():
            try:
                symbol = str(row.get('Symbol', '')).strip().upper()
                stock_price = float(str(row.get('Stock Price', '0')).replace('$', '').replace(',', ''))
                strike = float(str(row.get('Strike', '0')).replace('$', ''))
                premium = float(str(row.get('Premium', '0')).replace('$', '').replace(',', ''))
                
                expiry_str = str(row.get('Expiry', '')).strip()
                expiration_date = pd.to_datetime(expiry_str).date()
                dte = (expiration_date - datetime.now().date()).days
                
                # Covered call requires owning 100 shares
                capital_required = stock_price * 100
                max_profit = premium * 100 + ((strike - stock_price) * 100 if strike > stock_price else 0)
                max_loss = capital_required - (premium * 100)
                
                position = {
                    'symbol': symbol,
                    'strategy': 'covered_call',
                    'positions': [
                        {
                            'type': 'long_stock',
                            'strike': stock_price,
                            'contracts': 100,  # 100 shares
                            'premium': 0,
                            'delta': 1.00,
                            'theta': 0
                        },
                        {
                            'type': 'short_call',
                            'strike': strike,
                            'contracts': 1,
                            'premium': premium,
                            'delta': 0.30,
                            'theta': 0.08
                        }
                    ],
                    'expiration_date': expiration_date,
                    'dte': dte,
                    'premium_collected': Decimal(str(premium * 100)),
                    'capital_required': Decimal(str(capital_required)),
                    'max_profit': Decimal(str(max_profit)),
                    'max_loss': Decimal(str(max_loss)),
                    'breakeven': Decimal(str(stock_price - premium)),
                    'probability_of_profit': Decimal('70.0'),
                    'position_delta': Decimal('0.70'),  # Long stock - short call delta
                    'position_theta': Decimal('0.08'),
                    'position_gamma': Decimal('-0.02'),
                    'position_vega': Decimal('-0.10'),
                    'ai_confidence': Decimal('75.0'),
                    'ai_reasoning': f"OptionPlay Covered Call. Stock: ${stock_price}, Strike: ${strike}, Premium: ${premium}"
                }
                
                positions.append(position)
                
            except Exception as e:
                logger.warning(f"⚠️ Error normalizing covered call row {idx}: {e}")
                continue
        
        return positions
    
    def _apply_filters(self, positions: List[Dict], filters: Dict) -> List[Dict]:
        """Apply filters to positions"""
        filtered = positions
        
        # Min probability filter
        if 'min_probability' in filters:
            min_prob = filters['min_probability']
            filtered = [p for p in filtered if p['probability_of_profit'] >= min_prob]
        
        # Min premium filter
        if 'min_premium' in filters:
            min_prem = filters['min_premium']
            filtered = [p for p in filtered if p['premium_collected'] >= min_prem]
        
        # DTE range filter
        if 'dte_min' in filters and 'dte_max' in filters:
            dte_min, dte_max = filters['dte_min'], filters['dte_max']
            filtered = [p for p in filtered if dte_min <= p['dte'] <= dte_max]
        
        # Strategy filter
        if 'strategies' in filters:
            allowed_strategies = filters['strategies']
            filtered = [p for p in filtered if p['strategy'] in allowed_strategies]
        
        # Max positions limit
        if 'max_positions' in filters:
            filtered = filtered[:filters['max_positions']]
        
        logger.info(f"📊 After filters: {len(filtered)} positions (from {len(positions)})")
        return filtered

