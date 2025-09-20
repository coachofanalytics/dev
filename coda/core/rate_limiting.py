"""
Rate Limiting Service

This module provides comprehensive rate limiting functionality for the CODA application,
including API rate limiting, user-based throttling, and IP-based restrictions.
"""

import time
import logging
import hashlib
from functools import wraps
from typing import Dict, List, Optional, Tuple, Any
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse
from django.utils import timezone
from django.conf import settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """Base rate limiter class."""
    
    def __init__(self, requests: int, window: int, cache_alias: str = 'default'):
        """
        Initialize rate limiter.
        
        Args:
            requests: Number of requests allowed
            window: Time window in seconds
            cache_alias: Cache alias to use
        """
        self.requests = requests
        self.window = window
        self.cache_alias = cache_alias
        self.cache = cache
    
    def is_allowed(self, key: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if request is allowed.
        
        Args:
            key: Unique key for rate limiting
            
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        try:
            current_time = int(time.time())
            window_start = current_time - self.window
            
            # Get current request count
            cache_key = f"rate_limit:{key}:{current_time // self.window}"
            current_count = self.cache.get(cache_key, 0)
            
            if current_count >= self.requests:
                return False, {
                    'allowed': False,
                    'limit': self.requests,
                    'remaining': 0,
                    'reset_time': (current_time // self.window + 1) * self.window,
                    'retry_after': (current_time // self.window + 1) * self.window - current_time,
                }
            
            # Increment counter
            self.cache.set(cache_key, current_count + 1, self.window)
            
            return True, {
                'allowed': True,
                'limit': self.requests,
                'remaining': self.requests - current_count - 1,
                'reset_time': (current_time // self.window + 1) * self.window,
                'retry_after': 0,
            }
            
        except Exception as e:
            logger.error(f"Rate limiting error for key {key}: {e}")
            # Fail open - allow request if rate limiting fails
            return True, {
                'allowed': True,
                'limit': self.requests,
                'remaining': self.requests,
                'reset_time': int(time.time()) + self.window,
                'retry_after': 0,
                'error': str(e),
            }


class SlidingWindowRateLimiter:
    """Sliding window rate limiter for more precise rate limiting."""
    
    def __init__(self, requests: int, window: int, cache_alias: str = 'default'):
        """
        Initialize sliding window rate limiter.
        
        Args:
            requests: Number of requests allowed
            window: Time window in seconds
            cache_alias: Cache alias to use
        """
        self.requests = requests
        self.window = window
        self.cache_alias = cache_alias
        self.cache = cache
    
    def is_allowed(self, key: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if request is allowed using sliding window.
        
        Args:
            key: Unique key for rate limiting
            
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        try:
            current_time = time.time()
            window_start = current_time - self.window
            
            # Get all request timestamps for this key
            cache_key = f"sliding_rate_limit:{key}"
            timestamps = self.cache.get(cache_key, [])
            
            # Remove old timestamps outside the window
            timestamps = [ts for ts in timestamps if ts > window_start]
            
            if len(timestamps) >= self.requests:
                oldest_request = min(timestamps)
                retry_after = oldest_request + self.window - current_time
                
                return False, {
                    'allowed': False,
                    'limit': self.requests,
                    'remaining': 0,
                    'reset_time': oldest_request + self.window,
                    'retry_after': max(0, retry_after),
                }
            
            # Add current request timestamp
            timestamps.append(current_time)
            
            # Store updated timestamps
            self.cache.set(cache_key, timestamps, self.window)
            
            return True, {
                'allowed': True,
                'limit': self.requests,
                'remaining': self.requests - len(timestamps),
                'reset_time': current_time + self.window,
                'retry_after': 0,
            }
            
        except Exception as e:
            logger.error(f"Sliding window rate limiting error for key {key}: {e}")
            # Fail open
            return True, {
                'allowed': True,
                'limit': self.requests,
                'remaining': self.requests,
                'reset_time': time.time() + self.window,
                'retry_after': 0,
                'error': str(e),
            }


class RateLimitManager:
    """Manage multiple rate limiters for different scenarios."""
    
    def __init__(self):
        self.limiters = {}
        self._setup_default_limiters()
    
    def _setup_default_limiters(self):
        """Setup default rate limiters."""
        # API rate limiters
        self.limiters['api_general'] = RateLimiter(100, 3600)  # 100 requests per hour
        self.limiters['api_auth'] = RateLimiter(10, 300)      # 10 auth requests per 5 minutes
        self.limiters['api_loan'] = RateLimiter(20, 3600)     # 20 loan requests per hour
        self.limiters['api_payment'] = RateLimiter(50, 3600)  # 50 payment requests per hour
        
        # User-specific limiters
        self.limiters['user_general'] = SlidingWindowRateLimiter(1000, 3600)  # 1000 requests per hour
        self.limiters['user_loan_application'] = RateLimiter(5, 86400)         # 5 loan applications per day
        self.limiters['user_payment'] = RateLimiter(100, 3600)               # 100 payments per hour
        
        # IP-based limiters
        self.limiters['ip_general'] = RateLimiter(200, 3600)   # 200 requests per hour per IP
        self.limiters['ip_auth'] = RateLimiter(20, 300)       # 20 auth requests per 5 minutes per IP
    
    def get_limiter(self, limiter_name: str) -> Optional[RateLimiter]:
        """Get rate limiter by name."""
        return self.limiters.get(limiter_name)
    
    def add_limiter(self, name: str, limiter: RateLimiter):
        """Add custom rate limiter."""
        self.limiters[name] = limiter
    
    def check_rate_limit(self, limiter_name: str, key: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Check rate limit using specified limiter.
        
        Args:
            limiter_name: Name of the rate limiter
            key: Unique key for rate limiting
            
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        limiter = self.get_limiter(limiter_name)
        if not limiter:
            logger.warning(f"Rate limiter '{limiter_name}' not found")
            return True, {'allowed': True, 'error': 'limiter_not_found'}
        
        return limiter.is_allowed(key)


class RateLimitKeyGenerator:
    """Generate consistent rate limiting keys."""
    
    @staticmethod
    def get_user_key(user_id: int, limiter_type: str = 'general') -> str:
        """Generate user-based rate limiting key."""
        return f"user:{user_id}:{limiter_type}"
    
    @staticmethod
    def get_ip_key(ip_address: str, limiter_type: str = 'general') -> str:
        """Generate IP-based rate limiting key."""
        return f"ip:{ip_address}:{limiter_type}"
    
    @staticmethod
    def get_api_key(api_endpoint: str, limiter_type: str = 'general') -> str:
        """Generate API endpoint-based rate limiting key."""
        return f"api:{api_endpoint}:{limiter_type}"
    
    @staticmethod
    def get_combined_key(user_id: Optional[int], ip_address: str, 
                         limiter_type: str = 'general') -> str:
        """Generate combined user and IP rate limiting key."""
        if user_id:
            return f"combined:{user_id}:{ip_address}:{limiter_type}"
        else:
            return f"ip:{ip_address}:{limiter_type}"


class RateLimitMiddleware:
    """Django middleware for rate limiting."""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limit_manager = RateLimitManager()
    
    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Check rate limits
        is_allowed, rate_limit_info = self._check_request_rate_limit(request)
        
        if not is_allowed:
            return self._create_rate_limit_response(rate_limit_info)
        
        response = self.get_response(request)
        
        # Add rate limit headers to response
        self._add_rate_limit_headers(response, rate_limit_info)
        
        return response
    
    def _check_request_rate_limit(self, request: HttpRequest) -> Tuple[bool, Dict[str, Any]]:
        """Check rate limits for the request."""
        try:
            # Get client IP
            ip_address = self._get_client_ip(request)
            
            # Determine limiter type based on request path
            limiter_type = self._get_limiter_type(request.path)
            
            # Check IP-based rate limit
            ip_key = RateLimitKeyGenerator.get_ip_key(ip_address, limiter_type)
            is_allowed, rate_limit_info = self.rate_limit_manager.check_rate_limit(
                f'ip_{limiter_type}', ip_key
            )
            
            if not is_allowed:
                return False, rate_limit_info
            
            # Check user-based rate limit if user is authenticated
            if hasattr(request, 'user') and request.user.is_authenticated:
                user_key = RateLimitKeyGenerator.get_user_key(request.user.id, limiter_type)
                is_allowed, rate_limit_info = self.rate_limit_manager.check_rate_limit(
                    f'user_{limiter_type}', user_key
                )
                
                if not is_allowed:
                    return False, rate_limit_info
            
            return True, rate_limit_info
            
        except Exception as e:
            logger.error(f"Rate limit middleware error: {e}")
            # Fail open - allow request if rate limiting fails
            return True, {'allowed': True, 'error': str(e)}
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        return ip
    
    def _get_limiter_type(self, path: str) -> str:
        """Determine limiter type based on request path."""
        if '/auth/' in path or '/login/' in path:
            return 'auth'
        elif '/loan/' in path:
            return 'loan'
        elif '/payment/' in path:
            return 'payment'
        else:
            return 'general'
    
    def _create_rate_limit_response(self, rate_limit_info: Dict[str, Any]) -> HttpResponse:
        """Create rate limit exceeded response."""
        from django.http import JsonResponse
        
        response_data = {
            'error': 'Rate limit exceeded',
            'message': 'Too many requests. Please try again later.',
            'rate_limit_info': rate_limit_info,
        }
        
        response = JsonResponse(response_data, status=429)
        response['Retry-After'] = str(int(rate_limit_info.get('retry_after', 60)))
        
        return response
    
    def _add_rate_limit_headers(self, response: HttpResponse, rate_limit_info: Dict[str, Any]):
        """Add rate limit headers to response."""
        response['X-RateLimit-Limit'] = str(rate_limit_info.get('limit', 0))
        response['X-RateLimit-Remaining'] = str(rate_limit_info.get('remaining', 0))
        response['X-RateLimit-Reset'] = str(int(rate_limit_info.get('reset_time', 0)))


class RateLimitDecorator:
    """Decorator for rate limiting specific views."""
    
    def __init__(self, limiter_name: str, key_func: Optional[callable] = None):
        """
        Initialize rate limit decorator.
        
        Args:
            limiter_name: Name of the rate limiter to use
            key_func: Function to generate rate limit key from request
        """
        self.limiter_name = limiter_name
        self.key_func = key_func or self._default_key_func
        self.rate_limit_manager = RateLimitManager()
    
    def _default_key_func(self, request: HttpRequest) -> str:
        """Default key generation function."""
        if hasattr(request, 'user') and request.user.is_authenticated:
            return RateLimitKeyGenerator.get_user_key(request.user.id, 'decorator')
        else:
            ip_address = request.META.get('REMOTE_ADDR', '127.0.0.1')
            return RateLimitKeyGenerator.get_ip_key(ip_address, 'decorator')
    
    def __call__(self, view_func):
        """Apply rate limiting to view function."""
        @wraps(view_func)
        def wrapper(request: HttpRequest, *args, **kwargs):
            key = self.key_func(request)
            is_allowed, rate_limit_info = self.rate_limit_manager.check_rate_limit(
                self.limiter_name, key
            )
            
            if not is_allowed:
                from django.http import JsonResponse
                return JsonResponse({
                    'error': 'Rate limit exceeded',
                    'rate_limit_info': rate_limit_info,
                }, status=429)
            
            response = view_func(request, *args, **kwargs)
            
            # Add rate limit headers
            response['X-RateLimit-Limit'] = str(rate_limit_info.get('limit', 0))
            response['X-RateLimit-Remaining'] = str(rate_limit_info.get('remaining', 0))
            response['X-RateLimit-Reset'] = str(int(rate_limit_info.get('reset_time', 0)))
            
            return response
        
        return wrapper


# Convenience decorators
def rate_limit(limiter_name: str, key_func: Optional[callable] = None):
    """Convenience decorator for rate limiting views."""
    return RateLimitDecorator(limiter_name, key_func)


def api_rate_limit(requests: int = 100, window: int = 3600):
    """Convenience decorator for API rate limiting."""
    limiter_name = f"api_custom_{requests}_{window}"
    rate_limit_manager = RateLimitManager()
    rate_limit_manager.add_limiter(limiter_name, RateLimiter(requests, window))
    
    return RateLimitDecorator(limiter_name)


def user_rate_limit(requests: int = 1000, window: int = 3600):
    """Convenience decorator for user rate limiting."""
    limiter_name = f"user_custom_{requests}_{window}"
    rate_limit_manager = RateLimitManager()
    rate_limit_manager.add_limiter(limiter_name, SlidingWindowRateLimiter(requests, window))
    
    return RateLimitDecorator(limiter_name, lambda request: RateLimitKeyGenerator.get_user_key(request.user.id, 'custom'))


