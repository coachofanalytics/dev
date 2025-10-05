"""
AI Services Utils

This module contains utility functions for AI services operations.
Extracted from the massive ai_services/utils.py file to improve maintainability.

Following the modular monolith architecture, these utilities delegate complex operations
to specialized utility classes and provide simple interfaces for common tasks.
"""

import logging
from typing import Optional, Dict, Any, List
from django.utils import timezone

from .utilities import DataUtils, EmailUtils, FileProcessingUtils, StockUtils

logger = logging.getLogger(__name__)

# Initialize utility classes
data_utils = DataUtils()
email_utils = EmailUtils()
file_processing_utils = FileProcessingUtils()
stock_utils = StockUtils()


def fetch_and_insert_data() -> Dict[str, Any]:
    """
    Fetch data from external sources and insert into database.
    
    Returns:
        Dict with operation result
    """
    return data_utils.fetch_and_insert_data()


def convert_excel_dates(date_str: str, expiry_str: str) -> Dict[str, Any]:
    """
    Convert Excel date strings to proper datetime objects.
    
    Args:
        date_str: Date string from Excel
        expiry_str: Expiry string from Excel
        
    Returns:
        Dict with converted dates
    """
    return data_utils.convert_excel_dates(date_str, expiry_str)


def compute_stock_values(stockdata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute stock values from stock data.
    
    Args:
        stockdata: Dictionary containing stock data
        
    Returns:
        Dict with computed stock values
    """
    return data_utils.compute_stock_values(stockdata)


def row_value() -> Dict[str, Any]:
    """
    Get row value information.
    
    Returns:
        Dict with row value data
    """
    return data_utils.row_value()


def get_gmail_service() -> Dict[str, Any]:
    """
    Get Gmail service instance.
    
    Returns:
        Dict with Gmail service information
    """
    return email_utils.get_gmail_service()


def search_messages(service: Any, query: str) -> Dict[str, Any]:
    """
    Search Gmail messages.
    
    Args:
        service: Gmail service instance
        query: Search query
        
    Returns:
        Dict with search results
    """
    return email_utils.search_messages(service, query)


def get_message(service: Any, msg_id: str) -> Dict[str, Any]:
    """
    Get Gmail message by ID.
    
    Args:
        service: Gmail service instance
        msg_id: Message ID
        
    Returns:
        Dict with message data
    """
    return email_utils.get_message(service, msg_id)


def stock_data(symbol: str, action: str, qty: float, unit_price: float, total_price: float, date: str) -> Dict[str, Any]:
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
    return stock_utils.stock_data(symbol, action, qty, unit_price, total_price, date)


def crypto_data(symbol: str, action: str, unit_price: float, total_price: float, date: str) -> Dict[str, Any]:
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
    return stock_utils.crypto_data(symbol, action, unit_price, total_price, date)


def getdata(file: str) -> Dict[str, Any]:
    """
    Get data from file.
    
    Args:
        file: File path or name
        
    Returns:
        Dict with file data
    """
    return file_processing_utils.getdata(file)


def GetSubject(soup: Any) -> str:
    """
    Get subject from HTML soup.
    
    Args:
        soup: BeautifulSoup object
        
    Returns:
        Subject string
    """
    return file_processing_utils.GetSubject(soup)


def populate_table_from_json_file(file_path: str) -> Dict[str, Any]:
    """
    Populate database table from JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Dict with operation result
    """
    return data_utils.populate_table_from_json_file(file_path)


def move_questions_to_user_answer_status(username: str) -> Dict[str, Any]:
    """
    Move questions to user answer status.
    
    Args:
        username: Username
        
    Returns:
        Dict with operation result
    """
    return data_utils.move_questions_to_user_answer_status(username)


def populate_budget_categories(cat: str) -> Dict[str, Any]:
    """
    Populate budget categories.
    
    Args:
        cat: Category name
        
    Returns:
        Dict with operation result
    """
    return data_utils.populate_budget_categories(cat)


def populate_budget_subcategories(subcat: str) -> Dict[str, Any]:
    """
    Populate budget subcategories.
    
    Args:
        subcat: Subcategory name
        
    Returns:
        Dict with operation result
    """
    return data_utils.populate_budget_subcategories(subcat)


def transfer_transactions_to_codabudget(current_user: Any) -> Dict[str, Any]:
    """
    Transfer transactions to CODA budget.
    
    Args:
        current_user: Current user instance
        
    Returns:
        Dict with operation result
    """
    return data_utils.transfer_transactions_to_codabudget(current_user)


def handle_non_serializable(data: Any) -> Any:
    """
    Handle non-serializable data for JSON conversion.
    
    Args:
        data: Data to handle
        
    Returns:
        Serializable version of the data
    """
    return data_utils.handle_non_serializable(data)


def process_excel_file(file_path: str) -> Dict[str, Any]:
    """
    Process Excel file.
    
    Args:
        file_path: Path to Excel file
        
    Returns:
        Dict with processing result
    """
    return file_processing_utils.process_excel_file(file_path)


def download_recording(direct_download_url: str) -> Dict[str, Any]:
    """
    Download recording from URL.
    
    Args:
        direct_download_url: Direct download URL
        
    Returns:
        Dict with download result
    """
    return file_processing_utils.download_recording(direct_download_url)


def upload_to_google_drive(service: Any, file_content: Any, filename: str, folder_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Upload file to Google Drive.
    
    Args:
        service: Google Drive service instance
        file_content: File content
        filename: Filename
        folder_id: Optional folder ID
        
    Returns:
        Dict with upload result
    """
    return file_processing_utils.upload_to_google_drive(service, file_content, filename, folder_id)





