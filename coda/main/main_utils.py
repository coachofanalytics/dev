"""
Main Utils

This module contains utility functions for main operations.
Extracted from the massive main/utils.py file to improve maintainability.

Following the modular monolith architecture, these utilities delegate complex operations
to specialized utility classes and provide simple interfaces for common tasks.
"""

import logging
from typing import Optional, Dict, Any, List
from django.utils import timezone
from django.db import models

from .utilities import DateUtils, StringUtils, FileUtils, AIUtils

logger = logging.getLogger(__name__)

# Initialize utility classes
date_utils = DateUtils()
string_utils = StringUtils()
file_utils = FileUtils()
ai_utils = AIUtils()


def date_converter(date_string: str) -> Optional[timezone.datetime]:
    """
    Convert date string to datetime object.
    
    Args:
        date_string: Date string in various formats
        
    Returns:
        datetime object or None if conversion fails
    """
    return date_utils.date_converter(date_string)


def get_15th_of_next_month() -> timezone.datetime:
    """
    Get the 15th day of the next month.
    
    Returns:
        datetime object representing the 15th of next month
    """
    return date_utils.get_15th_of_next_month()


def get_next_group_name(current_group_name: str) -> str:
    """
    Get the next group name in sequence.
    
    Args:
        current_group_name: Current group name
        
    Returns:
        Next group name in sequence
    """
    return date_utils.get_next_group_name(current_group_name)


def switch_groups() -> Dict[str, Any]:
    """
    Switch groups based on current date.
    
    Returns:
        Dict with group switching information
    """
    return date_utils.switch_groups()


def notification_days(notification_obj: Any) -> int:
    """
    Calculate notification days based on notification object.
    
    Args:
        notification_obj: Notification object with date information
        
    Returns:
        Number of days until notification
    """
    return date_utils.notification_days(notification_obj)


def random_string_generator(size: int = 25, chars: str = None) -> str:
    """
    Generate a random string of specified size.
    
    Args:
        size: Length of the random string
        chars: Character set to use for generation
        
    Returns:
        Random string of specified size
    """
    if chars is None:
        import string
        chars = string.ascii_lowercase + string.digits
    
    return string_utils.random_string_generator(size, chars)


def all_applications() -> List[str]:
    """
    Get list of all application names.
    
    Returns:
        List of application names
    """
    try:
        from django.apps import apps
        return [app.label for app in apps.get_app_configs()]
    except Exception as e:
        logger.error(f"Error getting applications: {e}")
        return []


def applications_models() -> Dict[str, List[str]]:
    """
    Get models for each application.
    
    Returns:
        Dict mapping app names to their model names
    """
    try:
        from django.apps import apps
        result = {}
        
        for app_config in apps.get_app_configs():
            app_name = app_config.label
            models_list = []
            
            for model in app_config.get_models():
                models_list.append(model.__name__)
            
            result[app_name] = models_list
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting application models: {e}")
        return {}


def dates_functionality() -> Dict[str, Any]:
    """
    Get comprehensive date functionality information.
    
    Returns:
        Dict with various date-related information
    """
    return date_utils.dates_functionality()


def upload_image_to_drive(image_path: str, folder_id: str, image_name: str) -> Dict[str, Any]:
    """
    Upload image to Google Drive.
    
    Args:
        image_path: Path to the image file
        folder_id: Google Drive folder ID
        image_name: Name for the uploaded image
        
    Returns:
        Dict with upload result
    """
    return file_utils.upload_image_to_drive(image_path, folder_id, image_name)


def unique_slug_generator(instance: models.Model, new_slug: Optional[str] = None) -> str:
    """
    Generate a unique slug for a model instance.
    
    Args:
        instance: Django model instance
        new_slug: Optional custom slug
        
    Returns:
        Unique slug string
    """
    return string_utils.unique_slug_generator(instance, new_slug)


def slug_pre_save_receiver(sender: models.Model, instance: models.Model, *args, **kwargs) -> None:
    """
    Pre-save receiver for automatic slug generation.
    
    Args:
        sender: Model class
        instance: Model instance
        *args: Additional arguments
        **kwargs: Additional keyword arguments
    """
    string_utils.slug_pre_save_receiver(sender, instance, *args, **kwargs)


def openai_user_message(openai_context: str, requirement: Optional[str] = None) -> str:
    """
    Generate OpenAI user message.
    
    Args:
        openai_context: Context for the message
        requirement: Optional requirement
        
    Returns:
        Formatted user message
    """
    return ai_utils.openai_user_message(openai_context, requirement)


def generate_chatbot_response(user_message: str, user_message_dict: Optional[Dict] = None) -> str:
    """
    Generate chatbot response.
    
    Args:
        user_message: User's message
        user_message_dict: Optional user message dictionary
        
    Returns:
        Chatbot response
    """
    return ai_utils.generate_chatbot_response(user_message, user_message_dict)


def parse_user_query(user_query: str) -> Dict[str, Any]:
    """
    Parse user query for intent and parameters.
    
    Args:
        user_query: User's query string
        
    Returns:
        Dict with parsed query information
    """
    return string_utils.parse_user_query(user_query)


def generate_database_response(user_message: str, app: str = 'investing', table: str = 'investments') -> str:
    """
    Generate database response.
    
    Args:
        user_message: User's message
        app: Application name
        table: Table name
        
    Returns:
        Database response
    """
    return ai_utils.generate_database_response(user_message, app, table)


def analyze_website_for_wcag_compliance(uploaded_file_content: str) -> Dict[str, Any]:
    """
    Analyze website for WCAG compliance.
    
    Args:
        uploaded_file_content: Website content to analyze
        
    Returns:
        Dict with compliance analysis
    """
    return ai_utils.analyze_website_for_wcag_compliance(uploaded_file_content)


def handle_openai_api_exception(responses: Any) -> Dict[str, Any]:
    """
    Handle OpenAI API exceptions.
    
    Args:
        responses: API responses
        
    Returns:
        Dict with error handling information
    """
    return ai_utils.handle_openai_api_exception(responses)


def parse_json_response(responses: Any) -> Dict[str, Any]:
    """
    Parse JSON response.
    
    Args:
        responses: Response to parse
        
    Returns:
        Dict with parsed response
    """
    return ai_utils.parse_json_response(responses)


def countdown_in_month() -> Dict[str, Any]:
    """
    Calculate countdown information for the current month.
    
    Returns:
        Dict with countdown information
    """
    return date_utils.countdown_in_month()





