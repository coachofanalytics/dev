"""
Shared Core Utilities

Re-exports utility functions from main.utils.
All apps should import utilities from shared_core.utils, not main.utils.

This provides:
- path_values: Extract values from path
- dates_functionality: Date utility functions
- generate_chatbot_response: Chatbot response generation
- today_date: Get today's date
- date_converter: Convert date strings
"""
from main.utils import (
    path_values,
    dates_functionality,
    generate_chatbot_response,
    today_date,
    date_converter,
    countdown_in_month,
)

__all__ = [
    'path_values',
    'dates_functionality',
    'generate_chatbot_response',
    'today_date',
    'date_converter',
    'countdown_in_month',
]

