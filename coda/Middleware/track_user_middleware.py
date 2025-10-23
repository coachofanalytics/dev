"""
Track User Middleware

Middleware to track the current user for use in Django signals.
This allows signals to know which user triggered the change.

Usage in signals:
    from Middleware.track_user_middleware import get_current_user
    user = get_current_user()
"""

from threading import local

# Thread-local storage for current user
_thread_locals = local()


def get_current_user():
    """
    Get the current user from thread-local storage
    
    Returns:
        User instance or None if no user in current thread
    """
    return getattr(_thread_locals, 'user', None)


def set_current_user(user):
    """
    Set the current user in thread-local storage
    
    Args:
        user: User instance to store
    """
    _thread_locals.user = user


class TrackUserMiddleware:
    """
    Middleware to track current user for signal handlers
    
    Makes request.user available in signals via thread-local storage.
    This is necessary because Django signals don't have access to the request object.
    
    Add to MIDDLEWARE in settings.py:
        'Middleware.track_user_middleware.TrackUserMiddleware',
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Store user in thread-local storage
        _thread_locals.user = getattr(request, 'user', None)
        
        # Process the request
        response = self.get_response(request)
        
        # Clean up (optional, but good practice)
        if hasattr(_thread_locals, 'user'):
            del _thread_locals.user
        
        return response


