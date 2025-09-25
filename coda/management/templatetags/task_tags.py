"""
Custom template tags for task-related functionality
"""

from django import template

register = template.Library()

@register.filter
def getattr(obj, attr):
    """Get attribute from object"""
    try:
        return getattr(obj, attr)
    except (AttributeError, TypeError):
        return None

@register.filter
def get_field_value(obj, field_name):
    """Get field value from object, handling both attributes and methods"""
    try:
        value = getattr(obj, field_name)
        if callable(value):
            return value()
        return value
    except (AttributeError, TypeError):
        return None

