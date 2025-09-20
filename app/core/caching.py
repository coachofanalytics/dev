"""
Caching Service

This module provides a comprehensive caching service for the CODA application,
offering different caching strategies and utilities for service layers.
"""

import hashlib
import json
import logging
from functools import wraps
from typing import Any, Callable, Optional, Union
from django.core.cache import cache, caches
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class CacheService:
    """Comprehensive caching service for CODA application."""
    
    def __init__(self, cache_alias: str = 'default'):
        """
        Initialize cache service.
        
        Args:
            cache_alias: Cache alias to use (default, sessions, analytics)
        """
        self.cache_alias = cache_alias
        self.cache = caches[cache_alias]
        self.default_timeout = settings.CACHES[cache_alias]['TIMEOUT']
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            default: Default value if key not found
            
        Returns:
            Cached value or default
        """
        try:
            return self.cache.get(key, default)
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return default
    
    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            timeout: Cache timeout in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            timeout = timeout or self.default_timeout
            self.cache.set(key, value, timeout)
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.cache.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    def get_or_set(self, key: str, callable_func: Callable, timeout: Optional[int] = None) -> Any:
        """
        Get value from cache or set it using callable.
        
        Args:
            key: Cache key
            callable_func: Function to call if key not in cache
            timeout: Cache timeout in seconds
            
        Returns:
            Cached value or result from callable
        """
        try:
            return self.cache.get_or_set(key, callable_func, timeout or self.default_timeout)
        except Exception as e:
            logger.error(f"Cache get_or_set error for key {key}: {e}")
            return callable_func()
    
    def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching pattern.
        
        Args:
            pattern: Pattern to match (supports wildcards)
            
        Returns:
            Number of keys deleted
        """
        try:
            # This is a simplified version - in production you'd use Redis SCAN
            keys = self.cache.keys(pattern)
            if keys:
                self.cache.delete_many(keys)
                return len(keys)
            return 0
        except Exception as e:
            logger.error(f"Cache clear_pattern error for pattern {pattern}: {e}")
            return 0
    
    def increment(self, key: str, delta: int = 1, timeout: Optional[int] = None) -> int:
        """
        Increment numeric value in cache.
        
        Args:
            key: Cache key
            delta: Amount to increment by
            timeout: Cache timeout in seconds
            
        Returns:
            New value after increment
        """
        try:
            return self.cache.incr(key, delta)
        except Exception as e:
            logger.error(f"Cache increment error for key {key}: {e}")
            return 0
    
    def decrement(self, key: str, delta: int = 1) -> int:
        """
        Decrement numeric value in cache.
        
        Args:
            key: Cache key
            delta: Amount to decrement by
            
        Returns:
            New value after decrement
        """
        try:
            return self.cache.decr(key, delta)
        except Exception as e:
            logger.error(f"Cache decrement error for key {key}: {e}")
            return 0


class CacheKeyGenerator:
    """Utility class for generating consistent cache keys."""
    
    @staticmethod
    def generate_key(*args, **kwargs) -> str:
        """
        Generate cache key from arguments.
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Generated cache key
        """
        # Combine all arguments into a string
        key_parts = []
        
        # Add positional arguments
        for arg in args:
            if isinstance(arg, (str, int, float)):
                key_parts.append(str(arg))
            else:
                key_parts.append(hashlib.md5(str(arg).encode()).hexdigest()[:8])
        
        # Add keyword arguments
        for key, value in sorted(kwargs.items()):
            if isinstance(value, (str, int, float)):
                key_parts.append(f"{key}:{value}")
            else:
                key_parts.append(f"{key}:{hashlib.md5(str(value).encode()).hexdigest()[:8]}")
        
        return ":".join(key_parts)
    
    @staticmethod
    def user_key(user_id: int, *args, **kwargs) -> str:
        """Generate user-specific cache key."""
        return CacheKeyGenerator.generate_key("user", user_id, *args, **kwargs)
    
    @staticmethod
    def service_key(service_name: str, *args, **kwargs) -> str:
        """Generate service-specific cache key."""
        return CacheKeyGenerator.generate_key("service", service_name, *args, **kwargs)
    
    @staticmethod
    def analytics_key(analytics_type: str, *args, **kwargs) -> str:
        """Generate analytics-specific cache key."""
        return CacheKeyGenerator.generate_key("analytics", analytics_type, *args, **kwargs)


def cache_result(timeout: int = 300, cache_alias: str = 'default', key_func: Optional[Callable] = None):
    """
    Decorator to cache function results.
    
    Args:
        timeout: Cache timeout in seconds
        cache_alias: Cache alias to use
        key_func: Function to generate cache key from function arguments
    
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = CacheKeyGenerator.generate_key(
                    func.__name__, 
                    *args, 
                    **kwargs
                )
            
            # Try to get from cache
            cache_service = CacheService(cache_alias)
            cached_result = cache_service.get(cache_key)
            
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}: {cache_key}")
                return cached_result
            
            # Execute function and cache result
            logger.debug(f"Cache miss for {func.__name__}: {cache_key}")
            result = func(*args, **kwargs)
            cache_service.set(cache_key, result, timeout)
            
            return result
        
        return wrapper
    return decorator


def cache_invalidate(pattern: str, cache_alias: str = 'default'):
    """
    Decorator to invalidate cache after function execution.
    
    Args:
        pattern: Cache key pattern to invalidate
        cache_alias: Cache alias to use
    
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            # Invalidate cache
            cache_service = CacheService(cache_alias)
            cache_service.clear_pattern(pattern)
            
            return result
        
        return wrapper
    return decorator


class CacheMetrics:
    """Cache performance metrics collector."""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.deletes = 0
        self.errors = 0
    
    def record_hit(self):
        """Record cache hit."""
        self.hits += 1
    
    def record_miss(self):
        """Record cache miss."""
        self.misses += 1
    
    def record_set(self):
        """Record cache set."""
        self.sets += 1
    
    def record_delete(self):
        """Record cache delete."""
        self.deletes += 1
    
    def record_error(self):
        """Record cache error."""
        self.errors += 1
    
    def get_hit_rate(self) -> float:
        """Get cache hit rate."""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        return {
            'hits': self.hits,
            'misses': self.misses,
            'sets': self.sets,
            'deletes': self.deletes,
            'errors': self.errors,
            'hit_rate': self.get_hit_rate(),
        }


# Global cache metrics instance
cache_metrics = CacheMetrics()


# Convenience functions for common caching operations
def cache_user_data(user_id: int, data_type: str, data: Any, timeout: int = 300) -> bool:
    """Cache user-specific data."""
    key = CacheKeyGenerator.user_key(user_id, data_type)
    return CacheService().set(key, data, timeout)


def get_user_data(user_id: int, data_type: str, default: Any = None) -> Any:
    """Get user-specific data from cache."""
    key = CacheKeyGenerator.user_key(user_id, data_type)
    return CacheService().get(key, default)


def cache_service_result(service_name: str, method_name: str, *args, **kwargs) -> Any:
    """Cache service method result."""
    key = CacheKeyGenerator.service_key(service_name, method_name, *args, **kwargs)
    return CacheService().get(key)


def set_service_result(service_name: str, method_name: str, result: Any, timeout: int = 300, *args, **kwargs) -> bool:
    """Set service method result in cache."""
    key = CacheKeyGenerator.service_key(service_name, method_name, *args, **kwargs)
    return CacheService().set(key, result, timeout)


def cache_analytics_data(analytics_type: str, data: Any, timeout: int = 1800, *args, **kwargs) -> bool:
    """Cache analytics data."""
    key = CacheKeyGenerator.analytics_key(analytics_type, *args, **kwargs)
    return CacheService('analytics').set(key, data, timeout)


def get_analytics_data(analytics_type: str, default: Any = None, *args, **kwargs) -> Any:
    """Get analytics data from cache."""
    key = CacheKeyGenerator.analytics_key(analytics_type, *args, **kwargs)
    return CacheService('analytics').get(key, default)


