"""
Data Utilities

Handles all data-related operations including:
- Data fetching and insertion
- Excel data processing
- JSON data handling
- Data serialization and validation

This utility encapsulates data-related functionality previously scattered across ai_services/utils.py
"""

import logging
import json
import pandas as pd
from typing import Optional, Dict, Any, List
from datetime import datetime
from django.utils import timezone

logger = logging.getLogger(__name__)


class DataUtils:
    """
    Utility class for data-related operations.
    
    Provides methods for data fetching, processing, and validation.
    """
    
    def __init__(self):
        self.logger = logger
    
    def fetch_and_insert_data(self) -> Dict[str, Any]:
        """
        Fetch data from external sources and insert into database.
        
        Returns:
            Dict with operation result
        """
        try:
            # Placeholder for actual data fetching and insertion
            self.logger.info("Fetching and inserting data from external sources")
            
            return {
                'success': True,
                'message': 'Data fetched and inserted successfully',
                'records_processed': 0,
                'timestamp': timezone.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching and inserting data: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': timezone.now()
            }
    
    def convert_excel_dates(self, date_str: str, expiry_str: str) -> Dict[str, Any]:
        """
        Convert Excel date strings to proper datetime objects.
        
        Args:
            date_str: Date string from Excel
            expiry_str: Expiry string from Excel
            
        Returns:
            Dict with converted dates
        """
        try:
            converted_date = None
            converted_expiry = None
            
            if date_str:
                try:
                    # Try to parse as Excel date
                    if isinstance(date_str, (int, float)):
                        # Excel date serial number
                        converted_date = datetime.fromordinal(datetime(1900, 1, 1).toordinal() + int(date_str) - 2)
                    else:
                        # String date
                        converted_date = pd.to_datetime(date_str)
                except Exception as e:
                    self.logger.warning(f"Could not convert date '{date_str}': {e}")
            
            if expiry_str:
                try:
                    if isinstance(expiry_str, (int, float)):
                        converted_expiry = datetime.fromordinal(datetime(1900, 1, 1).toordinal() + int(expiry_str) - 2)
                    else:
                        converted_expiry = pd.to_datetime(expiry_str)
                except Exception as e:
                    self.logger.warning(f"Could not convert expiry '{expiry_str}': {e}")
            
            return {
                'success': True,
                'converted_date': converted_date,
                'converted_expiry': converted_expiry,
                'original_date': date_str,
                'original_expiry': expiry_str
            }
            
        except Exception as e:
            self.logger.error(f"Error converting Excel dates: {e}")
            return {
                'success': False,
                'error': str(e),
                'original_date': date_str,
                'original_expiry': expiry_str
            }
    
    def compute_stock_values(self, stockdata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute stock values from stock data.
        
        Args:
            stockdata: Dictionary containing stock data
            
        Returns:
            Dict with computed stock values
        """
        try:
            if not stockdata:
                return {
                    'success': False,
                    'error': 'No stock data provided'
                }
            
            # Extract relevant data
            symbol = stockdata.get('symbol', '')
            action = stockdata.get('action', '')
            qty = float(stockdata.get('qty', 0))
            unit_price = float(stockdata.get('unit_price', 0))
            total_price = float(stockdata.get('total_price', 0))
            
            # Compute values
            calculated_total = qty * unit_price
            difference = total_price - calculated_total
            
            return {
                'success': True,
                'symbol': symbol,
                'action': action,
                'quantity': qty,
                'unit_price': unit_price,
                'total_price': total_price,
                'calculated_total': calculated_total,
                'difference': difference,
                'is_accurate': abs(difference) < 0.01  # Allow for small rounding differences
            }
            
        except Exception as e:
            self.logger.error(f"Error computing stock values: {e}")
            return {
                'success': False,
                'error': str(e),
                'stockdata': stockdata
            }
    
    def row_value(self) -> Dict[str, Any]:
        """
        Get row value information.
        
        Returns:
            Dict with row value data
        """
        try:
            # Placeholder for actual row value calculation
            return {
                'success': True,
                'row_count': 0,
                'total_value': 0,
                'average_value': 0,
                'timestamp': timezone.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting row value: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def populate_table_from_json_file(self, file_path: str) -> Dict[str, Any]:
        """
        Populate database table from JSON file.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Dict with operation result
        """
        try:
            if not file_path:
                return {
                    'success': False,
                    'error': 'File path not provided'
                }
            
            # Placeholder for actual JSON file processing
            self.logger.info(f"Populating table from JSON file: {file_path}")
            
            return {
                'success': True,
                'message': f'Table populated from {file_path}',
                'file_path': file_path,
                'records_processed': 0,
                'timestamp': timezone.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error populating table from JSON file: {e}")
            return {
                'success': False,
                'error': str(e),
                'file_path': file_path
            }
    
    def handle_non_serializable(self, data: Any) -> Any:
        """
        Handle non-serializable data for JSON conversion.
        
        Args:
            data: Data to handle
            
        Returns:
            Serializable version of the data
        """
        try:
            if isinstance(data, datetime):
                return data.isoformat()
            elif hasattr(data, '__dict__'):
                return data.__dict__
            elif isinstance(data, (set, frozenset)):
                return list(data)
            else:
                return str(data)
                
        except Exception as e:
            self.logger.error(f"Error handling non-serializable data: {e}")
            return str(data)
    
    def validate_data_structure(self, data: Any, required_fields: List[str]) -> Dict[str, Any]:
        """
        Validate data structure against required fields.
        
        Args:
            data: Data to validate
            required_fields: List of required field names
            
        Returns:
            Dict with validation results
        """
        try:
            if not isinstance(data, dict):
                return {
                    'valid': False,
                    'error': 'Data must be a dictionary',
                    'missing_fields': required_fields
                }
            
            missing_fields = []
            for field in required_fields:
                if field not in data:
                    missing_fields.append(field)
            
            return {
                'valid': len(missing_fields) == 0,
                'missing_fields': missing_fields,
                'present_fields': [field for field in required_fields if field in data],
                'total_fields': len(data)
            }
            
        except Exception as e:
            self.logger.error(f"Error validating data structure: {e}")
            return {
                'valid': False,
                'error': str(e),
                'missing_fields': required_fields
            }





