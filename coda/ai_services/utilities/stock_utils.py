"""
Stock Utilities

Handles all stock-related operations including:
- Stock data processing
- Crypto data handling
- Stock value calculations
- Market data analysis

This utility encapsulates stock-related functionality previously scattered across ai_services/utils.py
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
from django.utils import timezone

logger = logging.getLogger(__name__)


class StockUtils:
    """
    Utility class for stock-related operations.
    
    Provides methods for stock data processing and analysis.
    """
    
    def __init__(self):
        self.logger = logger
    
    def stock_data(
        self, 
        symbol: str, 
        action: str, 
        qty: float, 
        unit_price: float, 
        total_price: float, 
        date: str
    ) -> Dict[str, Any]:
        """
        Process stock data.
        
        Args:
            symbol: Stock symbol
            action: Buy/Sell action
            qty: Quantity
            unit_price: Unit price
            total_price: Total price
            date: Transaction date
            
        Returns:
            Dict with processed stock data
        """
        try:
            # Validate inputs
            if not symbol:
                return {
                    'success': False,
                    'error': 'Stock symbol is required'
                }
            
            if action not in ['buy', 'sell']:
                return {
                    'success': False,
                    'error': 'Action must be either "buy" or "sell"'
                }
            
            if qty <= 0:
                return {
                    'success': False,
                    'error': 'Quantity must be greater than 0'
                }
            
            if unit_price <= 0:
                return {
                    'success': False,
                    'error': 'Unit price must be greater than 0'
                }
            
            # Calculate values
            calculated_total = qty * unit_price
            difference = total_price - calculated_total
            
            # Process date
            processed_date = None
            if date:
                try:
                    processed_date = datetime.strptime(date, '%Y-%m-%d')
                except ValueError:
                    try:
                        processed_date = datetime.strptime(date, '%m/%d/%Y')
                    except ValueError:
                        processed_date = timezone.now()
            
            return {
                'success': True,
                'symbol': symbol.upper(),
                'action': action.lower(),
                'quantity': qty,
                'unit_price': unit_price,
                'total_price': total_price,
                'calculated_total': calculated_total,
                'difference': difference,
                'is_accurate': abs(difference) < 0.01,
                'date': processed_date or timezone.now(),
                'timestamp': timezone.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error processing stock data: {e}")
            return {
                'success': False,
                'error': str(e),
                'symbol': symbol,
                'action': action
            }
    
    def crypto_data(
        self, 
        symbol: str, 
        action: str, 
        unit_price: float, 
        total_price: float, 
        date: str
    ) -> Dict[str, Any]:
        """
        Process cryptocurrency data.
        
        Args:
            symbol: Crypto symbol
            action: Buy/Sell action
            unit_price: Unit price
            total_price: Total price
            date: Transaction date
            
        Returns:
            Dict with processed crypto data
        """
        try:
            # Validate inputs
            if not symbol:
                return {
                    'success': False,
                    'error': 'Crypto symbol is required'
                }
            
            if action not in ['buy', 'sell']:
                return {
                    'success': False,
                    'error': 'Action must be either "buy" or "sell"'
                }
            
            if unit_price <= 0:
                return {
                    'success': False,
                    'error': 'Unit price must be greater than 0'
                }
            
            # Calculate values
            calculated_total = unit_price  # Assuming quantity is 1 for crypto
            difference = total_price - calculated_total
            
            # Process date
            processed_date = None
            if date:
                try:
                    processed_date = datetime.strptime(date, '%Y-%m-%d')
                except ValueError:
                    try:
                        processed_date = datetime.strptime(date, '%m/%d/%Y')
                    except ValueError:
                        processed_date = timezone.now()
            
            return {
                'success': True,
                'symbol': symbol.upper(),
                'action': action.lower(),
                'unit_price': unit_price,
                'total_price': total_price,
                'calculated_total': calculated_total,
                'difference': difference,
                'is_accurate': abs(difference) < 0.01,
                'date': processed_date or timezone.now(),
                'timestamp': timezone.now(),
                'asset_type': 'cryptocurrency'
            }
            
        except Exception as e:
            self.logger.error(f"Error processing crypto data: {e}")
            return {
                'success': False,
                'error': str(e),
                'symbol': symbol,
                'action': action
            }
    
    def calculate_portfolio_value(self, holdings: list) -> Dict[str, Any]:
        """
        Calculate total portfolio value from holdings.
        
        Args:
            holdings: List of holding dictionaries
            
        Returns:
            Dict with portfolio calculations
        """
        try:
            if not holdings:
                return {
                    'success': True,
                    'total_value': 0,
                    'total_cost': 0,
                    'total_gain_loss': 0,
                    'gain_loss_percentage': 0,
                    'holdings_count': 0
                }
            
            total_value = 0
            total_cost = 0
            
            for holding in holdings:
                if isinstance(holding, dict):
                    quantity = float(holding.get('quantity', 0))
                    current_price = float(holding.get('current_price', 0))
                    cost_price = float(holding.get('cost_price', 0))
                    
                    total_value += quantity * current_price
                    total_cost += quantity * cost_price
            
            total_gain_loss = total_value - total_cost
            gain_loss_percentage = (total_gain_loss / total_cost * 100) if total_cost > 0 else 0
            
            return {
                'success': True,
                'total_value': total_value,
                'total_cost': total_cost,
                'total_gain_loss': total_gain_loss,
                'gain_loss_percentage': gain_loss_percentage,
                'holdings_count': len(holdings),
                'timestamp': timezone.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating portfolio value: {e}")
            return {
                'success': False,
                'error': str(e),
                'holdings': holdings
            }
    
    def get_market_summary(self) -> Dict[str, Any]:
        """
        Get market summary information.
        
        Returns:
            Dict with market summary data
        """
        try:
            # Placeholder for actual market data retrieval
            return {
                'success': True,
                'market_status': 'open',
                'total_stocks': 0,
                'gainers': 0,
                'losers': 0,
                'unchanged': 0,
                'market_cap': 0,
                'volume': 0,
                'timestamp': timezone.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting market summary: {e}")
            return {
                'success': False,
                'error': str(e)
            }





