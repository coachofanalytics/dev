"""
Dynamic URL Template Tags

Usage in templates:
{% load url_tags %}
<a href="{% app_url 'data' 'bitraining' %}">Training</a>
<a href="{% role_url 'data' 'training' 'progress' %}">Progress</a>
"""

from django import template
from coda_project.url_config import get_app_url, get_role_url, get_legacy_url

register = template.Library()

@register.simple_tag
def app_url(app_name, path=''):
    """Template tag for app URLs"""
    return get_app_url(app_name, path)

@register.simple_tag  
def role_url(app_name, role, action='base'):
    """Template tag for role URLs"""
    return get_role_url(app_name, role, action)

@register.simple_tag
def legacy_url(old_app, path=''):
    """Template tag for legacy URLs"""
    return get_legacy_url(old_app, path)
