"""
Custom template tags for finance app
"""

from django import template

register = template.Library()


@register.filter
def lookup(dictionary, key):
    """
    Look up a key in a dictionary
    Usage: {{ dictionary|lookup:key }}
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None


@register.filter
def get_item(dictionary, key):
    """
    Get an item from a dictionary with a default value
    Usage: {{ dictionary|get_item:key }}
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key, '')
    return ''


@register.filter
def currency_format(value, currency='USD'):
    """
    Format a number as currency
    Usage: {{ value|currency_format:'USD' }}
    """
    if value is None:
        return '$0.00'
    
    try:
        # Convert to float if it's a Decimal
        if hasattr(value, 'quantize'):
            value = float(value)
        else:
            value = float(value)
        
        if currency == 'USD':
            return f'${value:,.2f}'
        elif currency == 'KES':
            return f'KSh {value:,.2f}'
        else:
            return f'{currency} {value:,.2f}'
    except (ValueError, TypeError):
        return '$0.00'


@register.filter
def percentage_format(value, decimals=1):
    """
    Format a number as percentage
    Usage: {{ value|percentage_format:2 }}
    """
    if value is None:
        return '0.0%'
    
    try:
        value = float(value)
        return f'{value:.{decimals}f}%'
    except (ValueError, TypeError):
        return '0.0%'
