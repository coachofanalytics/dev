"""
Currency Conversion Utility

Handles conversion between different currencies using exchange rate APIs
and provides standardized USD conversion for budget estimates.
"""

import requests
import json
from decimal import Decimal, ROUND_HALF_UP
from django.core.cache import cache
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class CurrencyConverter:
    """
    Currency converter using exchange rate APIs
    """
    
    def __init__(self):
        self.base_currency = 'USD'
        self.cache_timeout = 3600  # 1 hour cache
        self.api_key = getattr(settings, 'EXCHANGE_RATE_API_KEY', None)
        self.fallback_rates = {
            'KES': 0.0067,  # 1 KES = 0.0067 USD (approximate)
            'EUR': 1.08,    # 1 EUR = 1.08 USD (approximate)
            'GBP': 1.27,    # 1 GBP = 1.27 USD (approximate)
            'USD': 1.0,     # Base currency
        }
    
    def get_exchange_rate(self, from_currency: str, to_currency: str = 'USD') -> Decimal:
        """
        Get exchange rate from cache or API
        
        Args:
            from_currency: Source currency code
            to_currency: Target currency code (default: USD)
            
        Returns:
            Exchange rate as Decimal
        """
        if from_currency == to_currency:
            return Decimal('1.0')
        
        cache_key = f'exchange_rate_{from_currency}_{to_currency}'
        cached_rate = cache.get(cache_key)
        
        if cached_rate:
            return Decimal(str(cached_rate))
        
        # Try to get from API
        rate = self._fetch_from_api(from_currency, to_currency)
        
        if rate is None:
            # Fallback to hardcoded rates
            rate = self._get_fallback_rate(from_currency, to_currency)
            logger.warning(f"Using fallback exchange rate for {from_currency} to {to_currency}: {rate}")
        
        # Cache the rate
        cache.set(cache_key, float(rate), self.cache_timeout)
        return rate
    
    def _fetch_from_api(self, from_currency: str, to_currency: str) -> Decimal:
        """
        Fetch exchange rate from external API
        """
        try:
            # Try multiple APIs for reliability
            rate = self._fetch_from_exchangerate_api(from_currency, to_currency)
            if rate is not None:
                return rate
            
            rate = self._fetch_from_fixer_api(from_currency, to_currency)
            if rate is not None:
                return rate
                
        except Exception as e:
            logger.error(f"Error fetching exchange rate from API: {e}")
        
        return None
    
    def _fetch_from_exchangerate_api(self, from_currency: str, to_currency: str) -> Decimal:
        """
        Fetch from exchangerate-api.com (free tier)
        """
        try:
            url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            rate = data['rates'].get(to_currency)
            
            if rate:
                return Decimal(str(rate)).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
                
        except Exception as e:
            logger.error(f"Error with exchangerate-api: {e}")
        
        return None
    
    def _fetch_from_fixer_api(self, from_currency: str, to_currency: str) -> Decimal:
        """
        Fetch from fixer.io (requires API key)
        """
        if not self.api_key:
            return None
            
        try:
            url = f"http://data.fixer.io/api/latest"
            params = {
                'access_key': self.api_key,
                'base': from_currency,
                'symbols': to_currency
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get('success'):
                rate = data['rates'].get(to_currency)
                if rate:
                    return Decimal(str(rate)).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
                    
        except Exception as e:
            logger.error(f"Error with fixer.io: {e}")
        
        return None
    
    def _get_fallback_rate(self, from_currency: str, to_currency: str) -> Decimal:
        """
        Get fallback exchange rate
        """
        if to_currency == 'USD':
            return Decimal(str(self.fallback_rates.get(from_currency, 1.0)))
        elif from_currency == 'USD':
            # Reverse calculation
            usd_rate = Decimal(str(self.fallback_rates.get(to_currency, 1.0)))
            return Decimal('1.0') / usd_rate
        else:
            # Convert through USD
            to_usd = self._get_fallback_rate(from_currency, 'USD')
            from_usd = self._get_fallback_rate('USD', to_currency)
            return to_usd * from_usd
    
    def convert_to_usd(self, amount: Decimal, from_currency: str) -> Decimal:
        """
        Convert amount to USD
        
        Args:
            amount: Amount to convert
            from_currency: Source currency code
            
        Returns:
            Amount in USD
        """
        if from_currency == 'USD':
            return amount
        
        rate = self.get_exchange_rate(from_currency, 'USD')
        usd_amount = amount * rate
        
        # Round to 2 decimal places for currency
        return usd_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def convert_from_usd(self, usd_amount: Decimal, to_currency: str) -> Decimal:
        """
        Convert amount from USD to target currency
        
        Args:
            usd_amount: Amount in USD
            to_currency: Target currency code
            
        Returns:
            Amount in target currency
        """
        if to_currency == 'USD':
            return usd_amount
        
        rate = self.get_exchange_rate('USD', to_currency)
        converted_amount = usd_amount * rate
        
        # Round to 2 decimal places for currency
        return converted_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def get_currency_symbol(self, currency_code: str) -> str:
        """
        Get currency symbol for display
        
        Args:
            currency_code: Currency code
            
        Returns:
            Currency symbol
        """
        symbols = {
            'USD': '$',
            'KES': 'KSh',
            'EUR': '€',
            'GBP': '£',
        }
        return symbols.get(currency_code, currency_code)


# Global instance
currency_converter = CurrencyConverter()

