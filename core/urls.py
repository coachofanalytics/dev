"""
URL Configuration for Core App
Health check endpoints and monitoring URLs
"""

from django.urls import path
from . import health_views

app_name = 'core'

urlpatterns = [
    # Basic health checks
    path('health/', health_views.health_check, name='health_check'),
    path('health/comprehensive/', health_views.comprehensive_health_check, name='comprehensive_health_check'),
    path('health/enhanced/', health_views.enhanced_health_check, name='enhanced_health_check'),
    
    # Component-specific health checks
    path('health/ssl/', health_views.ssl_health_check, name='ssl_health_check'),
    path('health/database/', health_views.database_health_check, name='database_health_check'),
    path('health/cache/', health_views.cache_health_check, name='cache_health_check'),
    path('health/performance/', health_views.performance_health_check, name='performance_health_check'),
    path('health/security/', health_views.security_health_check, name='security_health_check'),
    path('health/alerting/', health_views.alerting_status_check, name='alerting_status_check'),
    
    # Kubernetes-style health checks
    path('health/readiness/', health_views.readiness_check, name='readiness_check'),
    path('health/liveness/', health_views.liveness_check, name='liveness_check'),
    
    # Performance monitoring
    path('health/thresholds/', health_views.performance_thresholds_check, name='performance_thresholds_check'),
    
    # Dashboard and management
    path('health/dashboard/', health_views.health_dashboard, name='health_dashboard'),
    path('health/test-alert/', health_views.test_alert_system, name='test_alert_system'),
    path('health/trigger/', health_views.trigger_health_check, name='trigger_health_check'),
    
    # Failover management
    path('health/failover/', health_views.failover_status_check, name='failover_status_check'),
    path('health/failover/trigger/', health_views.trigger_failover, name='trigger_failover'),
    path('health/failover/deactivate/', health_views.deactivate_failover, name='deactivate_failover'),
]
