"""
Database Optimization Service

This module provides database query optimization utilities including
select_related, prefetch_related, and query performance monitoring.
"""

import logging
import time
from typing import Any, Dict, List, Optional, Union
from django.db import models, connection
from django.db.models import QuerySet, Prefetch
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """Database query optimization utilities."""
    
    @staticmethod
    def optimize_queryset(queryset: QuerySet, select_related: List[str] = None, 
                         prefetch_related: List[str] = None, 
                         prefetch_objects: List[Prefetch] = None) -> QuerySet:
        """
        Optimize queryset with select_related and prefetch_related.
        
        Args:
            queryset: Django QuerySet to optimize
            select_related: List of fields for select_related
            prefetch_related: List of fields for prefetch_related
            prefetch_objects: List of Prefetch objects
            
        Returns:
            Optimized QuerySet
        """
        try:
            # Apply select_related for foreign key relationships
            if select_related:
                queryset = queryset.select_related(*select_related)
            
            # Apply prefetch_related for many-to-many and reverse foreign key relationships
            if prefetch_related:
                queryset = queryset.prefetch_related(*prefetch_related)
            
            # Apply custom Prefetch objects
            if prefetch_objects:
                queryset = queryset.prefetch_related(*prefetch_objects)
            
            return queryset
            
        except Exception as e:
            logger.error(f"Query optimization error: {e}")
            return queryset
    
    @staticmethod
    def get_optimized_user_queryset(user_model, include_profile: bool = True, 
                                   include_groups: bool = True) -> QuerySet:
        """
        Get optimized user queryset with common relationships.
        
        Args:
            user_model: User model class
            include_profile: Whether to include user profile
            include_groups: Whether to include user groups
            
        Returns:
            Optimized user QuerySet
        """
        select_related = []
        prefetch_related = []
        
        if include_profile:
            select_related.append('profile')
        
        if include_groups:
            prefetch_related.append('groups')
        
        return QueryOptimizer.optimize_queryset(
            user_model.objects.all(),
            select_related=select_related,
            prefetch_related=prefetch_related
        )
    
    @staticmethod
    def get_optimized_loan_queryset(loan_model, include_user: bool = True,
                                   include_guarantor: bool = True) -> QuerySet:
        """
        Get optimized loan queryset with common relationships.
        
        Args:
            loan_model: Loan model class
            include_user: Whether to include user relationship
            include_guarantor: Whether to include guarantor relationship
            
        Returns:
            Optimized loan QuerySet
        """
        select_related = []
        
        if include_user:
            select_related.append('user')
            select_related.append('user__profile')
        
        if include_guarantor:
            select_related.append('guarantor')
        
        return QueryOptimizer.optimize_queryset(
            loan_model.objects.all(),
            select_related=select_related
        )


class QueryPerformanceMonitor:
    """Monitor and log database query performance."""
    
    def __init__(self, slow_query_threshold: float = 0.1):
        """
        Initialize query performance monitor.
        
        Args:
            slow_query_threshold: Threshold in seconds for slow queries
        """
        self.slow_query_threshold = slow_query_threshold
        self.query_count = 0
        self.total_time = 0.0
        self.slow_queries = []
    
    def start_monitoring(self):
        """Start monitoring database queries."""
        self.query_count = 0
        self.total_time = 0.0
        self.slow_queries = []
        
        # Reset Django's query log
        connection.queries_log.clear()
    
    def stop_monitoring(self) -> Dict[str, Any]:
        """
        Stop monitoring and return performance statistics.
        
        Returns:
            Dictionary with performance statistics
        """
        queries = connection.queries
        self.query_count = len(queries)
        
        for query in queries:
            query_time = float(query['time'])
            self.total_time += query_time
            
            if query_time > self.slow_query_threshold:
                self.slow_queries.append({
                    'sql': query['sql'],
                    'time': query_time
                })
        
        return {
            'total_queries': self.query_count,
            'total_time': self.total_time,
            'average_time': self.total_time / self.query_count if self.query_count > 0 else 0,
            'slow_queries': len(self.slow_queries),
            'slow_query_threshold': self.slow_query_threshold,
        }
    
    def log_slow_queries(self):
        """Log slow queries for debugging."""
        for query in self.slow_queries:
            logger.warning(f"Slow query ({query['time']:.3f}s): {query['sql'][:200]}...")


class DatabaseIndexOptimizer:
    """Database index optimization utilities."""
    
    @staticmethod
    def get_recommended_indexes(model_class) -> List[Dict[str, Any]]:
        """
        Get recommended database indexes for a model.
        
        Args:
            model_class: Django model class
            
        Returns:
            List of recommended index configurations
        """
        recommendations = []
        
        # Common field patterns that benefit from indexes
        common_index_fields = [
            'created_at', 'updated_at', 'created_date', 'updated_date',
            'status', 'is_active', 'is_deleted', 'category', 'type'
        ]
        
        # Check model fields for common index candidates
        for field_name, field in model_class._meta.fields.items():
            if field_name in common_index_fields:
                recommendations.append({
                    'fields': [field_name],
                    'name': f'{model_class._meta.db_table}_{field_name}_idx',
                    'reason': f'Common query field: {field_name}'
                })
        
        # Check for foreign key fields
        for field_name, field in model_class._meta.fields.items():
            if isinstance(field, models.ForeignKey):
                recommendations.append({
                    'fields': [field_name],
                    'name': f'{model_class._meta.db_table}_{field_name}_fk_idx',
                    'reason': f'Foreign key field: {field_name}'
                })
        
        # Check for common composite index patterns
        if hasattr(model_class, 'user') and hasattr(model_class, 'status'):
            recommendations.append({
                'fields': ['user', 'status'],
                'name': f'{model_class._meta.db_table}_user_status_idx',
                'reason': 'Common filter combination: user + status'
            })
        
        if hasattr(model_class, 'created_at') and hasattr(model_class, 'status'):
            recommendations.append({
                'fields': ['created_at', 'status'],
                'name': f'{model_class._meta.db_table}_created_status_idx',
                'reason': 'Common filter combination: created_at + status'
            })
        
        return recommendations
    
    @staticmethod
    def generate_index_migration(model_class, indexes: List[Dict[str, Any]]) -> str:
        """
        Generate Django migration code for database indexes.
        
        Args:
            model_class: Django model class
            indexes: List of index configurations
            
        Returns:
            Migration code string
        """
        migration_code = f"""
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('{model_class._meta.app_label}', '0001_initial'),
    ]
    
    operations = [
"""
        
        for index in indexes:
            fields_str = ', '.join([f"'{field}'" for field in index['fields']])
            migration_code += f"""
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS {index['name']} ON {model_class._meta.db_table} ({', '.join(index['fields'])});",
            reverse_sql="DROP INDEX IF EXISTS {index['name']};"
        ),
"""
        
        migration_code += """
    ]
"""
        
        return migration_code


class QueryCache:
    """Cache database query results."""
    
    @staticmethod
    def cache_queryset_result(queryset: QuerySet, cache_key: str, 
                             timeout: int = 300) -> List[Any]:
        """
        Cache queryset result.
        
        Args:
            queryset: Django QuerySet
            cache_key: Cache key
            timeout: Cache timeout in seconds
            
        Returns:
            List of model instances
        """
        try:
            # Try to get from cache first
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Query cache hit: {cache_key}")
                return cached_result
            
            # Execute query and cache result
            logger.debug(f"Query cache miss: {cache_key}")
            result = list(queryset)
            cache.set(cache_key, result, timeout)
            
            return result
            
        except Exception as e:
            logger.error(f"Query cache error for key {cache_key}: {e}")
            return list(queryset)
    
    @staticmethod
    def invalidate_query_cache(pattern: str):
        """
        Invalidate cached query results matching pattern.
        
        Args:
            pattern: Cache key pattern to invalidate
        """
        try:
            # This is a simplified version - in production you'd use Redis SCAN
            keys = cache.keys(pattern)
            if keys:
                cache.delete_many(keys)
                logger.info(f"Invalidated {len(keys)} query cache entries")
        except Exception as e:
            logger.error(f"Query cache invalidation error for pattern {pattern}: {e}")


class DatabaseHealthChecker:
    """Check database health and performance."""
    
    @staticmethod
    def check_connection() -> Dict[str, Any]:
        """
        Check database connection health.
        
        Returns:
            Dictionary with connection health information
        """
        try:
            start_time = time.time()
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
            end_time = time.time()
            
            return {
                'status': 'healthy',
                'response_time': end_time - start_time,
                'result': result[0] if result else None,
                'timestamp': time.time()
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': time.time()
            }
    
    @staticmethod
    def get_table_sizes() -> List[Dict[str, Any]]:
        """
        Get database table sizes.
        
        Returns:
            List of table size information
        """
        try:
            with connection.cursor() as cursor:
                if connection.vendor == 'postgresql':
                    cursor.execute("""
                        SELECT 
                            schemaname,
                            tablename,
                            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                        FROM pg_tables 
                        WHERE schemaname = 'public'
                        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                    """)
                elif connection.vendor == 'sqlite':
                    cursor.execute("""
                        SELECT 
                            name as tablename,
                            (SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=main.name) as row_count
                        FROM sqlite_master 
                        WHERE type='table' AND name NOT LIKE 'sqlite_%'
                    """)
                else:
                    # Generic fallback
                    cursor.execute("SHOW TABLES")
                
                results = cursor.fetchall()
                
                table_info = []
                for row in results:
                    if connection.vendor == 'postgresql':
                        table_info.append({
                            'schema': row[0],
                            'table': row[1],
                            'size': row[2]
                        })
                    else:
                        table_info.append({
                            'table': row[0],
                            'info': row[1] if len(row) > 1 else 'N/A'
                        })
                
                return table_info
                
        except Exception as e:
            logger.error(f"Database health check error: {e}")
            return []
    
    @staticmethod
    def get_slow_queries() -> List[Dict[str, Any]]:
        """
        Get information about slow queries (if supported by database).
        
        Returns:
            List of slow query information
        """
        try:
            with connection.cursor() as cursor:
                if connection.vendor == 'postgresql':
                    cursor.execute("""
                        SELECT 
                            query,
                            calls,
                            total_time,
                            mean_time,
                            rows
                        FROM pg_stat_statements 
                        ORDER BY mean_time DESC 
                        LIMIT 10
                    """)
                else:
                    # Not supported for other databases
                    return []
                
                results = cursor.fetchall()
                
                slow_queries = []
                for row in results:
                    slow_queries.append({
                        'query': row[0][:200] + '...' if len(row[0]) > 200 else row[0],
                        'calls': row[1],
                        'total_time': row[2],
                        'mean_time': row[3],
                        'rows': row[4]
                    })
                
                return slow_queries
                
        except Exception as e:
            logger.error(f"Slow queries check error: {e}")
            return []


