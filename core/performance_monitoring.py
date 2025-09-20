"""
Performance Monitoring Service

This module provides comprehensive performance monitoring for the CODA application,
including metrics collection, performance tracking, and optimization recommendations.
"""

import time
import logging
import threading
from typing import Any, Dict, List, Optional, Callable
from functools import wraps
from django.core.cache import cache
from django.conf import settings
from django.db import connection
from django.utils import timezone

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """Collect and store performance metrics."""
    
    def __init__(self):
        self.metrics = {
            'request_count': 0,
            'total_response_time': 0.0,
            'average_response_time': 0.0,
            'slow_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'database_queries': 0,
            'database_time': 0.0,
            'memory_usage': 0.0,
            'cpu_usage': 0.0,
            'errors': 0,
        }
        self.lock = threading.Lock()
    
    def record_request(self, response_time: float, is_slow: bool = False):
        """Record request metrics."""
        with self.lock:
            self.metrics['request_count'] += 1
            self.metrics['total_response_time'] += response_time
            self.metrics['average_response_time'] = (
                self.metrics['total_response_time'] / self.metrics['request_count']
            )
            if is_slow:
                self.metrics['slow_requests'] += 1
    
    def record_cache_operation(self, hit: bool):
        """Record cache operation."""
        with self.lock:
            if hit:
                self.metrics['cache_hits'] += 1
            else:
                self.metrics['cache_misses'] += 1
    
    def record_database_operation(self, query_count: int, query_time: float):
        """Record database operation."""
        with self.lock:
            self.metrics['database_queries'] += query_count
            self.metrics['database_time'] += query_time
    
    def record_error(self):
        """Record error occurrence."""
        with self.lock:
            self.metrics['errors'] += 1
    
    def update_system_metrics(self):
        """Update system resource metrics."""
        try:
            if PSUTIL_AVAILABLE:
                process = psutil.Process()
                self.metrics['memory_usage'] = process.memory_info().rss / 1024 / 1024  # MB
                self.metrics['cpu_usage'] = process.cpu_percent()
            else:
                self.metrics['memory_usage'] = 0
                self.metrics['cpu_usage'] = 0
        except Exception as e:
            logger.error(f"Error updating system metrics: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        with self.lock:
            self.update_system_metrics()
            return self.metrics.copy()
    
    def reset_metrics(self):
        """Reset all metrics."""
        with self.lock:
            for key in self.metrics:
                if isinstance(self.metrics[key], (int, float)):
                    self.metrics[key] = 0


class PerformanceMonitor:
    """Main performance monitoring class."""
    
    def __init__(self, slow_request_threshold: float = 1.0):
        """
        Initialize performance monitor.
        
        Args:
            slow_request_threshold: Threshold in seconds for slow requests
        """
        self.slow_request_threshold = slow_request_threshold
        self.metrics = PerformanceMetrics()
        self.start_time = time.time()
    
    def start_request_monitoring(self):
        """Start monitoring a request."""
        return RequestMonitor(self)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        metrics = self.metrics.get_metrics()
        uptime = time.time() - self.start_time
        
        # Calculate rates
        request_rate = metrics['request_count'] / uptime if uptime > 0 else 0
        error_rate = (metrics['errors'] / metrics['request_count'] * 100) if metrics['request_count'] > 0 else 0
        cache_hit_rate = (metrics['cache_hits'] / (metrics['cache_hits'] + metrics['cache_misses']) * 100) if (metrics['cache_hits'] + metrics['cache_misses']) > 0 else 0
        
        return {
            'uptime_seconds': uptime,
            'uptime_hours': uptime / 3600,
            'metrics': metrics,
            'rates': {
                'requests_per_second': request_rate,
                'error_rate_percent': error_rate,
                'cache_hit_rate_percent': cache_hit_rate,
            },
            'health_status': self._get_health_status(metrics),
            'recommendations': self._get_optimization_recommendations(metrics),
        }
    
    def _get_health_status(self, metrics: Dict[str, Any]) -> str:
        """Determine overall health status."""
        error_rate = (metrics['errors'] / metrics['request_count'] * 100) if metrics['request_count'] > 0 else 0
        if error_rate > 5:
            return 'critical'
        elif metrics['average_response_time'] > 2.0:
            return 'warning'
        elif metrics['cache_hit_rate'] < 50:
            return 'warning'
        else:
            return 'healthy'
    
    def _get_optimization_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """Get optimization recommendations based on metrics."""
        recommendations = []
        
        if metrics['average_response_time'] > 1.0:
            recommendations.append("Consider implementing more aggressive caching")
        
        if metrics['cache_hit_rate'] < 70:
            recommendations.append("Optimize cache keys and increase cache timeout")
        
        if metrics['database_queries'] > 50:
            recommendations.append("Optimize database queries with select_related/prefetch_related")
        
        if metrics['memory_usage'] > 500:  # MB
            recommendations.append("Monitor memory usage and consider memory optimization")
        
        if metrics['slow_requests'] > metrics['request_count'] * 0.1:
            recommendations.append("Investigate slow request patterns")
        
        return recommendations


class RequestMonitor:
    """Monitor individual request performance."""
    
    def __init__(self, performance_monitor: PerformanceMonitor):
        self.performance_monitor = performance_monitor
        self.start_time = time.time()
        self.query_count_start = len(connection.queries)
        self.cache_hits = 0
        self.cache_misses = 0
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.finish_monitoring()
    
    def finish_monitoring(self):
        """Finish monitoring and record metrics."""
        end_time = time.time()
        response_time = end_time - self.start_time
        
        # Count database queries
        query_count = len(connection.queries) - self.query_count_start
        
        # Record metrics
        is_slow = response_time > self.performance_monitor.slow_request_threshold
        self.performance_monitor.metrics.record_request(response_time, is_slow)
        self.performance_monitor.metrics.record_database_operation(query_count, response_time)
        
        # Log slow requests
        if is_slow:
            logger.warning(f"Slow request detected: {response_time:.3f}s, {query_count} queries")


def monitor_performance(func: Callable) -> Callable:
    """
    Decorator to monitor function performance.
    
    Args:
        func: Function to monitor
        
    Returns:
        Decorated function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        start_queries = len(connection.queries)
        
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            logger.error(f"Error in monitored function {func.__name__}: {e}")
            raise
        finally:
            end_time = time.time()
            execution_time = end_time - start_time
            query_count = len(connection.queries) - start_queries
            
            logger.info(f"Function {func.__name__} executed in {execution_time:.3f}s with {query_count} queries")
    
    return wrapper


class APIPerformanceMonitor:
    """Monitor API endpoint performance."""
    
    def __init__(self):
        self.endpoint_metrics = {}
    
    def record_api_call(self, endpoint: str, method: str, response_time: float, 
                       status_code: int, query_count: int = 0):
        """Record API call metrics."""
        key = f"{method}:{endpoint}"
        
        if key not in self.endpoint_metrics:
            self.endpoint_metrics[key] = {
                'call_count': 0,
                'total_time': 0.0,
                'average_time': 0.0,
                'status_codes': {},
                'total_queries': 0,
                'average_queries': 0.0,
            }
        
        metrics = self.endpoint_metrics[key]
        metrics['call_count'] += 1
        metrics['total_time'] += response_time
        metrics['average_time'] = metrics['total_time'] / metrics['call_count']
        metrics['total_queries'] += query_count
        metrics['average_queries'] = metrics['total_queries'] / metrics['call_count']
        
        status_str = str(status_code)
        if status_str not in metrics['status_codes']:
            metrics['status_codes'][status_str] = 0
        metrics['status_codes'][status_str] += 1
    
    def get_endpoint_summary(self) -> Dict[str, Any]:
        """Get API endpoint performance summary."""
        return {
            'endpoints': self.endpoint_metrics,
            'total_endpoints': len(self.endpoint_metrics),
            'slowest_endpoints': self._get_slowest_endpoints(),
            'most_called_endpoints': self._get_most_called_endpoints(),
        }
    
    def _get_slowest_endpoints(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get slowest endpoints."""
        sorted_endpoints = sorted(
            self.endpoint_metrics.items(),
            key=lambda x: x[1]['average_time'],
            reverse=True
        )
        
        return [
            {
                'endpoint': endpoint,
                'average_time': metrics['average_time'],
                'call_count': metrics['call_count']
            }
            for endpoint, metrics in sorted_endpoints[:limit]
        ]
    
    def _get_most_called_endpoints(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get most called endpoints."""
        sorted_endpoints = sorted(
            self.endpoint_metrics.items(),
            key=lambda x: x[1]['call_count'],
            reverse=True
        )
        
        return [
            {
                'endpoint': endpoint,
                'call_count': metrics['call_count'],
                'average_time': metrics['average_time']
            }
            for endpoint, metrics in sorted_endpoints[:limit]
        ]


class SystemResourceMonitor:
    """Monitor system resource usage."""
    
    def __init__(self):
        self.monitoring = False
        self.monitor_thread = None
        self.resource_history = []
    
    def start_monitoring(self, interval: int = 60):
        """
        Start monitoring system resources.
        
        Args:
            interval: Monitoring interval in seconds
        """
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring system resources."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
    
    def _monitor_loop(self, interval: int):
        """Main monitoring loop."""
        while self.monitoring:
            try:
                resource_data = self._collect_resource_data()
                self.resource_history.append(resource_data)
                
                # Keep only last 100 entries
                if len(self.resource_history) > 100:
                    self.resource_history = self.resource_history[-100:]
                
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Resource monitoring error: {e}")
                time.sleep(interval)
    
    def _collect_resource_data(self) -> Dict[str, Any]:
        """Collect current resource data."""
        try:
            if PSUTIL_AVAILABLE:
                process = psutil.Process()
                
                return {
                    'timestamp': time.time(),
                    'cpu_percent': psutil.cpu_percent(),
                    'memory_percent': psutil.virtual_memory().percent,
                    'memory_used_mb': psutil.virtual_memory().used / 1024 / 1024,
                    'memory_available_mb': psutil.virtual_memory().available / 1024 / 1024,
                    'process_memory_mb': process.memory_info().rss / 1024 / 1024,
                    'process_cpu_percent': process.cpu_percent(),
                    'disk_usage_percent': psutil.disk_usage('/').percent,
                }
            else:
                return {
                    'timestamp': time.time(),
                    'cpu_percent': 0,
                    'memory_percent': 0,
                    'memory_used_mb': 0,
                    'memory_available_mb': 0,
                    'process_memory_mb': 0,
                    'process_cpu_percent': 0,
                    'disk_usage_percent': 0,
                    'psutil_unavailable': True,
                }
        except Exception as e:
            logger.error(f"Error collecting resource data: {e}")
            return {
                'timestamp': time.time(),
                'error': str(e)
            }
    
    def get_resource_summary(self) -> Dict[str, Any]:
        """Get resource usage summary."""
        if not self.resource_history:
            return {'status': 'no_data'}
        
        latest = self.resource_history[-1]
        
        # Calculate averages
        cpu_values = [r.get('cpu_percent', 0) for r in self.resource_history if 'cpu_percent' in r]
        memory_values = [r.get('memory_percent', 0) for r in self.resource_history if 'memory_percent' in r]
        
        return {
            'current': latest,
            'averages': {
                'cpu_percent': sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                'memory_percent': sum(memory_values) / len(memory_values) if memory_values else 0,
            },
            'history_count': len(self.resource_history),
            'monitoring_active': self.monitoring,
        }


# Global performance monitor instance
performance_monitor = PerformanceMonitor()
api_monitor = APIPerformanceMonitor()
resource_monitor = SystemResourceMonitor()


def performance_middleware(get_response):
    """
    Django middleware for performance monitoring.
    
    Args:
        get_response: Django get_response function
        
    Returns:
        Middleware function
    """
    def middleware(request):
        with performance_monitor.start_request_monitoring():
            response = get_response(request)
            return response
    
    return middleware
