# custom_tags.py
from django import template
import json
from urllib.parse import urlencode

register = template.Library()

@register.filter
def format_dynamic_fields(value):
    if not value:
        return ""  # Return an empty string if value is None or empty
    try:
        dynamic_fields = json.loads(value)
        if not isinstance(dynamic_fields, dict):
            raise json.JSONDecodeError  # Raise an error if the decoded JSON is not a dictionary

        formatted_fields = []
        for field_name, field_value in dynamic_fields.items():
            formatted_field = f"<strong>{field_name}:</strong> {field_value}"
            formatted_fields.append(formatted_field)
        return "<br>".join(formatted_fields)
    except json.JSONDecodeError:
        return ""  # Return an empty string if value is not a valid JSON string or if decoding fails
@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, '')
@register.simple_tag
def querystring(request, **kwargs):
    # Make a mutable copy of the request's GET parameters
    query = request.GET.copy()
    
    # Update the query parameters with the provided kwargs
    for key, value in kwargs.items():
        query[key] = value
    
    # Return the encoded querystring
    return query.urlencode()