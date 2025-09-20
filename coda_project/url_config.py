"""
Dynamic URL Configuration System

This allows you to change app names in one place and have all URLs update automatically.
"""

# =========================
# APP URL CONFIGURATION
# =========================
APP_URLS = {
    'professional_services': 'professional_services',
    'ai_services': 'ai_services', 
    'data': 'professional_services',  # Legacy mapping
    'get_data': 'ai_services',        # Legacy mapping
}

# =========================
# ROLE-BASED URL PATTERNS
# =========================
ROLE_URLS = {
    'training': {
        'base': 'bitraining',
        'progress': 'training_progress',
        'schedule': 'schedule',
        'courses': 'courses',
    },
    'interview': {
        'base': 'interview',
        'prep': 'prepquestions',
        'uploads': 'iuploads',
        'roles': 'roles',
        'feedback': 'student_feedback',
    },
    'projects': {
        'base': 'project_story',
        'updates': 'updatelist',
    },
    'jobs': {
        'tracker': 'job_tracker',
        'market': 'job_market',
    },
    'development': {
        'base': 'Development',
        'uploads': 'interviewuploads',
    }
}

# =========================
# URL GENERATION FUNCTIONS
# =========================
def get_app_url(app_name, path=''):
    """
    Get the full URL for an app with optional path
    
    Args:
        app_name: The app identifier (e.g., 'data', 'professional_services')
        path: Optional path to append
        
    Returns:
        Full URL string
    """
    actual_app = APP_URLS.get(app_name, app_name)
    if path:
        return f"/{actual_app}/{path}"
    return f"/{actual_app}/"

def get_role_url(app_name, role, action='base'):
    """
    Get URL for a specific role and action
    
    Args:
        app_name: The app identifier
        role: The role (e.g., 'training', 'interview')
        action: The action within the role (e.g., 'base', 'progress')
        
    Returns:
        Full URL string
    """
    if role not in ROLE_URLS:
        raise ValueError(f"Unknown role: {role}")
    
    if action not in ROLE_URLS[role]:
        raise ValueError(f"Unknown action '{action}' for role '{role}'")
    
    path = ROLE_URLS[role][action]
    return get_app_url(app_name, path)

def get_legacy_url(old_app, path=''):
    """
    Get URL for legacy app names (for backward compatibility)
    """
    return get_app_url(old_app, path)

# =========================
# CONTEXT PROCESSOR
# =========================
def url_context_processor(request):
    """
    Django context processor to make URL functions available in templates
    """
    return {
        'get_app_url': get_app_url,
        'get_role_url': get_role_url,
        'get_legacy_url': get_legacy_url,
        'APP_URLS': APP_URLS,
        'ROLE_URLS': ROLE_URLS,
    }

# =========================
# TEMPLATE TAGS
# =========================
from django import template
from django.template import Library

register = Library()

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
