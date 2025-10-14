"""
Health Check Views for Production Monitoring
Provides comprehensive health check endpoints for monitoring systems
"""

import json
import logging
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.conf import settings
from core.production_monitoring import production_monitor, SSLMonitor, DatabaseHealthMonitor, CacheHealthMonitor, AlertManager, SecurityMonitor, FailoverManager
from core.performance_monitoring import PerformanceMonitor

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
def health_check(request):
    """Basic health check endpoint"""
    try:
        return JsonResponse({
            'status': 'healthy',
            'timestamp': production_monitor.get_cached_health_status()['timestamp'],
            'service': 'CODA Application'
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def comprehensive_health_check(request):
    """Comprehensive health check endpoint"""
    try:
        domain = request.GET.get('domain', getattr(settings, 'PRODUCTION_DOMAIN', 'www.codanalytics.net'))
        results = production_monitor.run_comprehensive_check(domain)
        
        # Determine HTTP status code based on overall status
        status_code = 200
        if results['overall_status'] == 'critical':
            status_code = 503
        elif results['overall_status'] == 'warning':
            status_code = 200
        elif results['overall_status'] == 'degraded':
            status_code = 200
        
        return JsonResponse(results, status=status_code)
    except Exception as e:
        logger.error(f"Comprehensive health check failed: {e}")
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def ssl_health_check(request):
    """SSL-specific health check endpoint"""
    try:
        domain = request.GET.get('domain', getattr(settings, 'PRODUCTION_DOMAIN', 'www.codanalytics.net'))
        
        # Check SSL certificate
        cert_result = SSLMonitor.check_ssl_certificate(domain)
        
        # Check SSL redirect
        redirect_result = SSLMonitor.check_ssl_redirect(domain)
        
        results = {
            'domain': domain,
            'ssl_certificate': cert_result,
            'ssl_redirect': redirect_result,
            'overall_ssl_status': 'healthy'
        }
        
        # Determine overall SSL status
        if (cert_result.get('status') == 'error' or 
            redirect_result.get('status') == 'error' or
            cert_result.get('is_expired') or
            not redirect_result.get('redirects_to_https')):
            results['overall_ssl_status'] = 'critical'
        elif cert_result.get('is_expiring_soon'):
            results['overall_ssl_status'] = 'warning'
        
        status_code = 200
        if results['overall_ssl_status'] == 'critical':
            status_code = 503
        
        return JsonResponse(results, status=status_code)
    except Exception as e:
        logger.error(f"SSL health check failed: {e}")
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def database_health_check(request):
    """Database-specific health check endpoint"""
    try:
        results = DatabaseHealthMonitor.check_database_health()
        status_code = 200 if results['status'] == 'healthy' else 503
        return JsonResponse(results, status=status_code)
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def cache_health_check(request):
    """Cache-specific health check endpoint"""
    try:
        results = CacheHealthMonitor.check_cache_health()
        status_code = 200 if results['status'] == 'healthy' else 503
        return JsonResponse(results, status=status_code)
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def performance_health_check(request):
    """Performance monitoring health check endpoint"""
    try:
        perf_monitor = PerformanceMonitor()
        results = perf_monitor.get_performance_summary()
        return JsonResponse(results)
    except Exception as e:
        logger.error(f"Performance health check failed: {e}")
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def readiness_check(request):
    """Kubernetes-style readiness check"""
    try:
        # Check critical services
        db_health = DatabaseHealthMonitor.check_database_health()
        cache_health = CacheHealthMonitor.check_cache_health()
        
        # Determine readiness
        is_ready = (db_health['status'] == 'healthy' and 
                   cache_health['status'] == 'healthy')
        
        results = {
            'ready': is_ready,
            'timestamp': production_monitor.get_cached_health_status()['timestamp'],
            'services': {
                'database': db_health['status'],
                'cache': cache_health['status']
            }
        }
        
        status_code = 200 if is_ready else 503
        return JsonResponse(results, status=status_code)
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JsonResponse({
            'ready': False,
            'error': str(e)
        }, status=503)


@require_http_methods(["GET"])
def liveness_check(request):
    """Kubernetes-style liveness check"""
    try:
        # Simple check to see if the application is responding
        return JsonResponse({
            'alive': True,
            'timestamp': production_monitor.get_cached_health_status()['timestamp']
        })
    except Exception as e:
        logger.error(f"Liveness check failed: {e}")
        return JsonResponse({
            'alive': False,
            'error': str(e)
        }, status=503)


@csrf_exempt
@require_http_methods(["POST"])
def trigger_health_check(request):
    """Manually trigger a comprehensive health check"""
    try:
        data = json.loads(request.body) if request.body else {}
        domain = data.get('domain', getattr(settings, 'PRODUCTION_DOMAIN', 'www.codanalytics.net'))
        
        results = production_monitor.run_comprehensive_check(domain)
        
        return JsonResponse({
            'message': 'Health check triggered successfully',
            'results': results
        })
    except Exception as e:
        logger.error(f"Manual health check trigger failed: {e}")
        return JsonResponse({
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def health_dashboard(request):
    """HTML dashboard for health monitoring"""
    try:
        domain = request.GET.get('domain', getattr(settings, 'PRODUCTION_DOMAIN', 'www.codanalytics.net'))
        results = production_monitor.get_cached_health_status(domain)
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>CODA Health Dashboard</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .status {{ padding: 10px; margin: 10px 0; border-radius: 4px; }}
                .status.healthy {{ background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
                .status.warning {{ background-color: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }}
                .status.degraded {{ background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}
                .status.critical {{ background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}
                .check {{ margin: 15px 0; padding: 15px; border: 1px solid #ddd; border-radius: 4px; }}
                .check h3 {{ margin-top: 0; }}
                .refresh {{ text-align: center; margin: 20px 0; }}
                .refresh button {{ padding: 10px 20px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }}
                .refresh button:hover {{ background-color: #0056b3; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🏥 CODA Health Dashboard</h1>
                    <p>Domain: {domain}</p>
                    <p>Last Updated: {results.get('timestamp', 'Unknown')}</p>
                </div>
                
                <div class="status {results.get('overall_status', 'unknown')}">
                    <h2>Overall Status: {results.get('overall_status', 'Unknown').upper()}</h2>
                </div>
                
                <div class="refresh">
                    <button onclick="location.reload()">🔄 Refresh</button>
                </div>
        """
        
        # Add individual check results
        for check_name, check_result in results.get('checks', {}).items():
            status = check_result.get('status', 'unknown')
            html_content += f"""
                <div class="check">
                    <h3>🔍 {check_name.replace('_', ' ').title()}</h3>
                    <div class="status {status}">
                        Status: {status.upper()}
                    </div>
                    <pre>{json.dumps(check_result, indent=2)}</pre>
                </div>
            """
        
        html_content += """
            </div>
            <script>
                // Auto-refresh every 30 seconds
                setTimeout(() => location.reload(), 30000);
            </script>
        </body>
        </html>
        """
        
        return HttpResponse(html_content, content_type='text/html')
    except Exception as e:
        logger.error(f"Health dashboard failed: {e}")
        return HttpResponse(f"Error loading dashboard: {e}", status=500)


@require_http_methods(["GET"])
def enhanced_health_check(request):
    """Enhanced health check with alerting and performance monitoring"""
    try:
        domain = request.GET.get('domain', getattr(settings, 'PRODUCTION_DOMAIN', 'www.codanalytics.net'))
        results = production_monitor.get_enhanced_health_status(domain)
        
        # Determine HTTP status code based on overall status
        status_code = 200
        if results['overall_status'] == 'critical':
            status_code = 503
        elif results['overall_status'] == 'warning':
            status_code = 200
        elif results['overall_status'] == 'degraded':
            status_code = 200
        
        return JsonResponse(results, status=status_code)
    except Exception as e:
        logger.error(f"Enhanced health check failed: {e}")
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def performance_thresholds_check(request):
    """Check performance thresholds and return status"""
    try:
        thresholds = production_monitor.check_performance_thresholds()
        
        # Determine if any thresholds are exceeded
        any_exceeded = any(
            threshold.get('alert_triggered', False) 
            for threshold in thresholds.values() 
            if isinstance(threshold, dict)
        )
        
        status_code = 200
        if any_exceeded:
            status_code = 200  # Still return 200 but with warning info
        
        return JsonResponse({
            'status': 'warning' if any_exceeded else 'healthy',
            'thresholds': thresholds,
            'timestamp': production_monitor.get_cached_health_status()['timestamp']
        }, status=status_code)
    except Exception as e:
        logger.error(f"Performance thresholds check failed: {e}")
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def security_health_check(request):
    """Security-specific health check endpoint"""
    try:
        security_monitor = SecurityMonitor()
        results = security_monitor.check_security_events()
        
        status_code = 200
        if results.get('status') == 'error':
            status_code = 503
        
        return JsonResponse(results, status=status_code)
    except Exception as e:
        logger.error(f"Security health check failed: {e}")
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def alerting_status_check(request):
    """Check alerting system status"""
    try:
        alert_manager = production_monitor.alert_manager
        
        return JsonResponse({
            'status': 'healthy',
            'alerting_system': {
                'thresholds_configured': len(alert_manager.thresholds),
                'active_alerts': len(alert_manager.sent_alerts),
                'alert_cooldown_minutes': alert_manager.alert_cooldown / 60,
                'thresholds': alert_manager.thresholds,
                'last_checked': timezone.now().isoformat()
            }
        })
    except Exception as e:
        logger.error(f"Alerting status check failed: {e}")
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def test_alert_system(request):
    """Test alert system functionality (admin only)"""
    try:
        # Check if user is admin
        if not request.user.is_authenticated or not request.user.is_staff:
            return JsonResponse({
                'status': 'error',
                'error': 'Admin access required'
            }, status=403)
        
        data = json.loads(request.body) if request.body else {}
        test_severity = data.get('severity', 'warning')
        test_component = data.get('component', 'test')
        
        # Send test alert
        alert_manager = production_monitor.alert_manager
        success = alert_manager.process_alert({
            'severity': test_severity,
            'message': 'This is a test alert to verify the alerting system is working',
            'component': test_component,
            'timestamp': timezone.now()
        })
        
        return JsonResponse({
            'status': 'success' if success else 'error',
            'message': 'Test alert sent successfully' if success else 'Failed to send test alert',
            'test_data': {
                'severity': test_severity,
                'component': test_component,
                'timestamp': timezone.now().isoformat()
            }
        })
    except Exception as e:
        logger.error(f"Test alert system failed: {e}")
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def failover_status_check(request):
    """Check failover system status"""
    try:
        failover_manager = production_monitor.failover_manager
        
        return JsonResponse({
            'status': 'healthy',
            'failover_system': failover_manager.get_failover_status(),
            'last_checked': timezone.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Failover status check failed: {e}")
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def trigger_failover(request):
    """Manually trigger failover for testing (admin only)"""
    try:
        # Check if user is admin
        if not request.user.is_authenticated or not request.user.is_staff:
            return JsonResponse({
                'status': 'error',
                'error': 'Admin access required'
            }, status=403)
        
        data = json.loads(request.body) if request.body else {}
        component = data.get('component', 'database')
        action = data.get('action', 'failover')
        reason = data.get('reason', 'manual_test_trigger')
        
        # Execute failover
        failover_manager = production_monitor.failover_manager
        success = failover_manager.execute_failover(component, action, reason)
        
        return JsonResponse({
            'status': 'success' if success else 'error',
            'message': f'Failover {action} for {component} {"executed" if success else "failed"}',
            'failover_data': {
                'component': component,
                'action': action,
                'reason': reason,
                'timestamp': timezone.now().isoformat(),
                'success': success
            }
        })
    except Exception as e:
        logger.error(f"Manual failover trigger failed: {e}")
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def deactivate_failover(request):
    """Deactivate failover mode (admin only)"""
    try:
        # Check if user is admin
        if not request.user.is_authenticated or not request.user.is_staff:
            return JsonResponse({
                'status': 'error',
                'error': 'Admin access required'
            }, status=403)
        
        # Deactivate offline mode
        from django.core.cache import cache
        cache.delete('system_offline_mode')
        cache.delete('emergency_failover_mode')
        
        return JsonResponse({
            'status': 'success',
            'message': 'Failover modes deactivated successfully',
            'timestamp': timezone.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Failover deactivation failed: {e}")
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=500)

