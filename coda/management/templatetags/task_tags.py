"""
Custom template tags for task-related functionality
"""

from django import template
import builtins

register = template.Library()

@register.filter
def getattr(obj, attr):
    """Get attribute from object"""
    try:
        # Use Python built-in getattr to avoid recursion with this filter name
        return builtins.getattr(obj, attr)
    except (AttributeError, TypeError):
        return None

@register.filter
def get_field_value(obj, field_name):
    """Get field value from object, handling both attributes and methods"""
    try:
        value = builtins.getattr(obj, field_name)
        if callable(value):
            return value()
        return value
    except (AttributeError, TypeError):
        return None


@register.filter(name="split_csv")
def split_csv(value, separator=","):
    """Split a comma-separated string into a list.

    Useful for passing comma-separated values to includes, e.g.:
        {% include 'components/table.html' with table_headers='A,B' object_fields='a,b' %}
    """
    if value is None:
        return []
    try:
        # Ensure we always return a clean list without surrounding whitespace
        return [part.strip() for part in str(value).split(separator) if part.strip() != ""]
    except Exception:
        return [str(value)]

