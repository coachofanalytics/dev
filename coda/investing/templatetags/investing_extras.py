"""
Custom template tags and filters for investing app
"""

from django import template

register = template.Library()


@register.filter
def lookup(dictionary, key):
    """
    Template filter to lookup dictionary value by key
    Usage: {{ row|lookup:header }}
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key, '')
    return ''

