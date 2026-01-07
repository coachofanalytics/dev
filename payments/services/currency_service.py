import requests
from decimal import Decimal
from django.core.cache import cache
from django.conf import settings
from typing import Dict, Optional


class CurrencyConversionService:
    """Service for handling currency conversions between USD and KES"""
    
    # Free exchange rate API (no API key required for basic usage)
    EXCHANGE_RATE_API = "https://api.exchangerate-api.com/v4/latest/{base_currency}"
    
    # Alternative: use settings for API configuration
    CACHE_KEY_PREFIX = "exchange_rate"
    CACHE_TIMEOUT = 3600  # Cache rates for 1 hour
    
    @classmethod
    def get_exchange_rate(cls, from_currency: str, to_currency: str) -> Optional[Decimal]:
        """
        Get current exchange rate between two currencies
        
        Args:
            from_currency: Source currency code (USD or KES)
            to_currency: Target currency code (USD or KES)
            
        Returns:
            Decimal: Exchange rate or None if error
        """
        # Check cache first
        cache_key = f"{cls.CACHE_KEY_PREFIX}_{from_currency}_{to_currency}"
        cached_rate = cache.get(cache_key)
        
        if cached_rate:
            return Decimal(str(cached_rate))
        
        try:
            # Fetch from API
            url = cls.EXCHANGE_RATE_API.format(base_currency=from_currency)
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            rates = data.get('rates', {})
            
            if to_currency in rates:
                rate = Decimal(str(rates[to_currency]))
                
                # Cache the rate
                cache.set(cache_key, float(rate), cls.CACHE_TIMEOUT)
                
                return rate
            
        except Exception as e:
            print(f"Error fetching exchange rate: {e}")
            # Fallback to approximate rate if API fails
            return cls.get_fallback_rate(from_currency, to_currency)
        
        return None
    
    @classmethod
    def get_fallback_rate(cls, from_currency: str, to_currency: str) -> Decimal:
        """
        Get fallback exchange rate if API fails
        Using approximate rates as of 2025
        """
        fallback_rates = {
            ('USD', 'KES'): Decimal('150.00'),  # 1 USD = ~150 KES
            ('KES', 'USD'): Decimal('0.0067'),  # 1 KES = ~0.0067 USD
            ('USD', 'USD'): Decimal('1.00'),
            ('KES', 'KES'): Decimal('1.00'),
        }
        
        return fallback_rates.get((from_currency, to_currency), Decimal('1.00'))
    
    @classmethod
    def convert_amount(cls, amount: Decimal, from_currency: str, to_currency: str) -> Dict:
        """
        Convert amount from one currency to another
        
        Args:
            amount: Amount to convert
            from_currency: Source currency
            to_currency: Target currency
            
        Returns:
            Dict with converted_amount, rate, from_currency, to_currency
        """
        if from_currency == to_currency:
            return {
                'success': True,
                'converted_amount': amount,
                'rate': Decimal('1.00'),
                'from_currency': from_currency,
                'to_currency': to_currency,
                'original_amount': amount,
            }
        
        rate = cls.get_exchange_rate(from_currency, to_currency)
        
        if rate:
            converted_amount = amount * rate
            # Round to 2 decimal places
            converted_amount = converted_amount.quantize(Decimal('0.01'))
            
            return {
                'success': True,
                'converted_amount': converted_amount,
                'rate': rate,
                'from_currency': from_currency,
                'to_currency': to_currency,
                'original_amount': amount,
            }
        
        return {
            'success': False,
            'error': 'Failed to fetch exchange rate',
        }
    
    @classmethod
    def get_supported_currencies(cls) -> list:
        """Get list of supported currencies"""
        return ['USD', 'KES']
    
    @classmethod
    def get_all_rates(cls) -> Dict:
        """Get all current exchange rates"""
        return {
            'USD_to_KES': cls.get_exchange_rate('USD', 'KES'),
            'KES_to_USD': cls.get_exchange_rate('KES', 'USD'),
        }
