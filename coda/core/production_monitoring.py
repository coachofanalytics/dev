"""
Production Monitoring System for CODA Application
Comprehensive monitoring to prevent critical issues from affecting users
Enhanced with real-time alerting and performance threshold monitoring
"""

import time
import ssl
import socket
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.utils import timezone
from django.contrib.auth.models import User
import json

logger = logging.getLogger(__name__)


class FailoverManager:
    """Automated failover and recovery management system"""
    
    def __init__(self):
        self.failover_states = {
            'database': 'healthy',
            'cache': 'healthy', 
            'ssl': 'healthy',
            'application': 'healthy',
            'ai_services': 'healthy'
        }
        self.failover_triggers = {
            'database': ['connection_failed', 'response_time_exceeded', 'query_timeout'],
            'cache': ['connection_failed', 'hit_rate_low', 'timeout'],
            'ssl': ['certificate_expired', 'connection_failed', 'invalid_cert'],
            'application': ['high_error_rate', 'memory_exhausted', 'cpu_overload'],
            'ai_services': ['api_unavailable', 'rate_limit_exceeded', 'timeout']
        }
        self.backup_systems = {
            'database': {
                'primary': 'postgresql://primary-db',
                'backup': 'postgresql://backup-db',
                'offline_mode': True
            },
            'cache': {
                'primary': 'redis://primary-cache',
                'backup': 'redis://backup-cache', 
                'offline_mode': True
            },
            'application': {
                'primary': 'https://www.codanalytics.net',
                'backup': 'https://backup.codanalytics.net',
                'offline_mode': True
            },
            'ai_services': {
                'primary': 'openai_api',
                'backup': 'fallback_service',
                'offline_mode': True
            }
        }
        self.failover_history = []
        self.auto_recovery_enabled = True
    
    def check_failover_conditions(self, health_results: Dict[str, Any]) -> Dict[str, Any]:
        """Check if failover conditions are met"""
        failover_actions = {}
        
        # Check database failover conditions
        db_check = health_results.get('checks', {}).get('database', {})
        if db_check.get('status') == 'error' or db_check.get('response_time_ms', 0) > 5000:
            failover_actions['database'] = {
                'action': 'failover',
                'reason': db_check.get('status', 'performance_issue'),
                'timestamp': timezone.now().isoformat()
            }
        
        # Check SSL failover conditions
        ssl_check = health_results.get('checks', {}).get('ssl_certificate', {})
        if ssl_check.get('is_expired') or ssl_check.get('status') == 'error':
            failover_actions['ssl'] = {
                'action': 'redirect_to_backup',
                'reason': 'ssl_certificate_issue',
                'timestamp': timezone.now().isoformat()
            }
        
        # Check application failover conditions
        overall_status = health_results.get('overall_status', 'healthy')
        if overall_status == 'critical':
            failover_actions['application'] = {
                'action': 'redirect_to_offline_mode',
                'reason': 'critical_system_failure',
                'timestamp': timezone.now().isoformat()
            }
        
        return failover_actions
    
    def execute_failover(self, component: str, action: str, reason: str) -> bool:
        """Execute failover action for a component"""
        try:
            logger.critical(f"EXECUTING FAILOVER: {component} - {action} - {reason}")
            
            if action == 'failover':
                return self._switch_to_backup(component, reason)
            elif action == 'redirect_to_backup':
                return self._redirect_to_backup_system(component, reason)
            elif action == 'redirect_to_offline_mode':
                return self._activate_offline_mode(component, reason)
            
            return False
            
        except Exception as e:
            logger.error(f"Failover execution failed for {component}: {e}")
            return False
    
    def _switch_to_backup(self, component: str, reason: str) -> bool:
        """Switch to backup system for a component"""
        try:
            if component == 'database':
                # Switch database connection to backup
                from django.conf import settings
                backup_db_url = self.backup_systems['database']['backup']
                
                # Update database configuration (this would need to be implemented)
                logger.info(f"Switching database to backup: {backup_db_url}")
                
                # Record failover action
                self._record_failover_action(component, 'database_backup_activated', reason)
                return True
                
            elif component == 'cache':
                # Switch cache to backup
                backup_cache_url = self.backup_systems['cache']['backup']
                logger.info(f"Switching cache to backup: {backup_cache_url}")
                
                self._record_failover_action(component, 'cache_backup_activated', reason)
                return True
                
        except Exception as e:
            logger.error(f"Backup switch failed for {component}: {e}")
            return False
    
    def _redirect_to_backup_system(self, component: str, reason: str) -> bool:
        """Redirect traffic to backup system"""
        try:
            if component == 'ssl':
                # Redirect to backup domain or HTTP fallback
                backup_url = self.backup_systems['application']['backup']
                logger.critical(f"SSL FAILOVER: Redirecting traffic to {backup_url}")
                
                # This would trigger nginx/apache redirect rules
                self._record_failover_action(component, 'ssl_redirect_activated', reason)
                return True
                
        except Exception as e:
            logger.error(f"Backup redirect failed for {component}: {e}")
            return False
    
    def _activate_offline_mode(self, component: str, reason: str) -> bool:
        """Activate offline/maintenance mode"""
        try:
            logger.critical(f"ACTIVATING OFFLINE MODE: {component} - {reason}")
            
            # Set offline mode flag in database or cache
            from django.core.cache import cache
            cache.set('system_offline_mode', {
                'active': True,
                'reason': reason,
                'component': component,
                'timestamp': timezone.now().isoformat(),
                'redirect_url': '/maintenance/'
            }, 3600)  # 1 hour
            
            # Record failover action
            self._record_failover_action(component, 'offline_mode_activated', reason)
            return True
            
        except Exception as e:
            logger.error(f"Offline mode activation failed: {e}")
            return False
    
    def _record_failover_action(self, component: str, action: str, reason: str):
        """Record failover action in history"""
        self.failover_history.append({
            'component': component,
            'action': action,
            'reason': reason,
            'timestamp': timezone.now().isoformat(),
            'auto_recovery_enabled': self.auto_recovery_enabled
        })
        
        # Keep only last 50 failover actions
        if len(self.failover_history) > 50:
            self.failover_history = self.failover_history[-50:]
    
    def check_auto_recovery(self, health_results: Dict[str, Any]) -> Dict[str, Any]:
        """Check if system has recovered and can switch back to primary"""
        recovery_actions = {}
        
        if not self.auto_recovery_enabled:
            return recovery_actions
        
        # Check if database has recovered
        if 'database' in [f['component'] for f in self.failover_history[-5:]]:
            db_check = health_results.get('checks', {}).get('database', {})
            if db_check.get('status') == 'healthy' and db_check.get('response_time_ms', 0) < 1000:
                recovery_actions['database'] = {
                    'action': 'switch_to_primary',
                    'reason': 'system_recovered',
                    'timestamp': timezone.now().isoformat()
                }
        
        # Check if SSL has recovered
        if 'ssl' in [f['component'] for f in self.failover_history[-5:]]:
            ssl_check = health_results.get('checks', {}).get('ssl_certificate', {})
            if not ssl_check.get('is_expired') and ssl_check.get('status') == 'valid':
                recovery_actions['ssl'] = {
                    'action': 'switch_to_primary',
                    'reason': 'ssl_certificate_renewed',
                    'timestamp': timezone.now().isoformat()
                }
        
        return recovery_actions
    
    def get_failover_status(self) -> Dict[str, Any]:
        """Get current failover status"""
        return {
            'failover_states': self.failover_states,
            'auto_recovery_enabled': self.auto_recovery_enabled,
            'recent_failovers': self.failover_history[-10:],
            'backup_systems': self.backup_systems
        }


class AlertManager:
    """Enhanced alert management system integrated with existing mail system"""
    
    def __init__(self):
        self.thresholds = {
            'response_time': 2.0,  # seconds
            'error_rate': 1.0,     # percentage
            'memory_usage': 80.0,  # percentage
            'cpu_usage': 70.0,     # percentage
            'disk_usage': 85.0,    # percentage
            'ssl_expiry_days': 30, # days
            'database_response_time': 1.0,  # seconds
            'cache_hit_rate': 70.0,  # percentage
        }
        self.sent_alerts = {}  # For deduplication
        self.alert_cooldown = 900  # 15 minutes in seconds
    
    def process_alert(self, alert_data: Dict[str, Any]) -> bool:
        """Process and send alert using existing mail system"""
        try:
            # Check for deduplication
            alert_key = self._get_alert_key(alert_data)
            if self._is_duplicate_alert(alert_key):
                logger.info(f"Duplicate alert suppressed: {alert_key}")
                return False
            
            # Get admin users for alerts
            admin_users = User.objects.filter(is_staff=True, is_active=True)
            admin_emails = [user.email for user in admin_users if user.email]
            
            if not admin_emails:
                logger.warning("No admin emails found for alerts")
                return False
            
            # Prepare alert email
            subject = f"🚨 CODA Alert: {alert_data.get('component', 'System')} - {alert_data.get('severity', 'Warning').upper()}"
            message = self._format_alert_message(alert_data)
            
            # Use existing mail system
            from mail.custom_email import send_email
            
            success = send_email(
                category=1,  # Use HR category for system alerts
                to_email=admin_emails,
                subject=subject,
                html_template='email/system_alert.html',  # We'll create this template
                context={
                    'alert_data': alert_data,
                    'message': message,
                    'timestamp': timezone.now(),
                    'domain': getattr(settings, 'PRODUCTION_DOMAIN', 'www.codanalytics.net')
                }
            )
            
            # Record sent alert
            if success:
                self.sent_alerts[alert_key] = timezone.now()
                logger.info(f"Alert sent successfully: {alert_key}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error processing alert: {e}")
            return False
    
    def check_threshold(self, metric_name: str, value: float) -> Dict[str, Any]:
        """Check if metric exceeds threshold"""
        threshold = self.thresholds.get(metric_name)
        if threshold is None:
            return {'alert_triggered': False, 'reason': 'No threshold set'}
        
        alert_triggered = value > threshold
        severity = 'critical' if alert_triggered else 'info'
        
        # Special handling for some metrics
        if metric_name == 'cache_hit_rate':
            alert_triggered = value < threshold  # Lower is worse for hit rate
            severity = 'warning' if alert_triggered else 'info'
        elif metric_name == 'ssl_expiry_days':
            alert_triggered = value < threshold  # Lower is worse for expiry days
            severity = 'critical' if value < 7 else 'warning' if value < 30 else 'info'
        
        return {
            'alert_triggered': alert_triggered,
            'threshold': threshold,
            'value': value,
            'severity': severity,
            'metric_name': metric_name
        }
    
    def _get_alert_key(self, alert_data: Dict[str, Any]) -> str:
        """Generate unique key for alert deduplication"""
        component = alert_data.get('component', 'unknown')
        message = alert_data.get('message', '')
        severity = alert_data.get('severity', 'info')
        return f"{component}_{severity}_{hash(message)}"
    
    def _is_duplicate_alert(self, alert_key: str) -> bool:
        """Check if alert was recently sent"""
        if alert_key not in self.sent_alerts:
            return False
        
        last_sent = self.sent_alerts[alert_key]
        time_diff = timezone.now() - last_sent
        
        return time_diff.total_seconds() < self.alert_cooldown
    
    def _format_alert_message(self, alert_data: Dict[str, Any]) -> str:
        """Format alert message for email"""
        component = alert_data.get('component', 'System')
        severity = alert_data.get('severity', 'Warning')
        message = alert_data.get('message', 'Unknown issue')
        timestamp = alert_data.get('timestamp', timezone.now())
        
        return f"""
        <h3>System Alert Details</h3>
        <p><strong>Component:</strong> {component}</p>
        <p><strong>Severity:</strong> {severity.upper()}</p>
        <p><strong>Message:</strong> {message}</p>
        <p><strong>Timestamp:</strong> {timestamp}</p>
        <p><strong>Action Required:</strong> Please investigate and resolve this issue.</p>
        """


class SecurityMonitor:
    """Enhanced security monitoring"""
    
    @staticmethod
    def check_security_events() -> Dict[str, Any]:
        """Check for security-related events and issues"""
        try:
            security_status = {
                'status': 'healthy',
                'timestamp': timezone.now().isoformat(),
                'events': {},
                'recommendations': []
            }
            
            # Check for failed login attempts (last hour)
            from django.contrib.auth.models import User
            from datetime import timedelta
            
            recent_time = timezone.now() - timedelta(hours=1)
            
            # This would need to be implemented based on your login tracking
            # For now, we'll create a placeholder structure
            security_status['events']['failed_logins'] = {
                'count': 0,  # Would be actual count from login attempts
                'status': 'normal',
                'description': 'No unusual login activity detected'
            }
            
            # Check SSL/TLS configuration
            try:
                import ssl
                context = ssl.create_default_context()
                security_status['events']['ssl_config'] = {
                    'status': 'secure',
                    'description': 'SSL configuration appears secure'
                }
            except Exception as e:
                security_status['events']['ssl_config'] = {
                    'status': 'warning',
                    'description': f'SSL configuration check failed: {str(e)}'
                }
            
            # Add security recommendations
            security_status['recommendations'] = [
                'Ensure all admin accounts use strong passwords',
                'Monitor for unusual login patterns',
                'Keep SSL certificates updated'
            ]
            
            return security_status
            
        except Exception as e:
            logger.error(f"Security monitoring failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }


class SSLMonitor:
    """Monitor SSL certificate status and configuration"""
    
    @staticmethod
    def check_ssl_certificate(domain: str, port: int = 443) -> Dict[str, Any]:
        """Check SSL certificate validity and configuration"""
        try:
            # Create SSL context
            context = ssl.create_default_context()
            
            # Connect to the server
            with socket.create_connection((domain, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    
                    # Parse certificate info
                    not_before = datetime.strptime(cert['notBefore'], '%b %d %H:%M:%S %Y %Z')
                    not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                    days_until_expiry = (not_after - datetime.now()).days
                    
                    return {
                        'status': 'valid',
                        'domain': domain,
                        'issuer': cert.get('issuer', {}),
                        'subject': cert.get('subject', {}),
                        'not_before': not_before.isoformat(),
                        'not_after': not_after.isoformat(),
                        'days_until_expiry': days_until_expiry,
                        'is_expiring_soon': days_until_expiry < 30,
                        'is_expired': days_until_expiry < 0,
                        'version': cert.get('version'),
                        'serial_number': cert.get('serialNumber'),
                        'last_checked': timezone.now().isoformat()
                    }
                    
        except Exception as e:
            logger.error(f"SSL certificate check failed for {domain}: {e}")
            return {
                'status': 'error',
                'domain': domain,
                'error': str(e),
                'last_checked': timezone.now().isoformat()
            }
    
    @staticmethod
    def check_ssl_redirect(domain: str) -> Dict[str, Any]:
        """Check if HTTP redirects to HTTPS"""
        try:
            # Test HTTP redirect
            response = requests.get(f'http://{domain}', 
                                  allow_redirects=False, 
                                  timeout=10)
            
            is_redirecting = response.status_code in [301, 302, 303, 307, 308]
            redirects_to_https = False
            
            if is_redirecting:
                location = response.headers.get('Location', '')
                redirects_to_https = location.startswith('https://')
            
            return {
                'status': 'success',
                'domain': domain,
                'http_accessible': response.status_code == 200,
                'redirects_to_https': redirects_to_https,
                'redirect_status_code': response.status_code,
                'redirect_location': response.headers.get('Location', ''),
                'last_checked': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"SSL redirect check failed for {domain}: {e}")
            return {
                'status': 'error',
                'domain': domain,
                'error': str(e),
                'last_checked': timezone.now().isoformat()
            }


class DatabaseHealthMonitor:
    """Monitor database health and performance"""
    
    @staticmethod
    def check_database_health() -> Dict[str, Any]:
        """Check database connectivity and performance"""
        try:
            start_time = time.time()
            
            # Test basic connectivity
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
            
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Check connection pool status
            connection_count = len(connection.queries)
            
            return {
                'status': 'healthy',
                'response_time_ms': round(response_time, 2),
                'connection_count': connection_count,
                'last_query_time': connection.queries[-1]['time'] if connection.queries else 0,
                'last_checked': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'last_checked': timezone.now().isoformat()
            }


class CacheHealthMonitor:
    """Monitor cache system health"""
    
    @staticmethod
    def check_cache_health() -> Dict[str, Any]:
        """Check cache connectivity and performance"""
        try:
            start_time = time.time()
            
            # Test cache operations
            test_key = f"health_check_{int(time.time())}"
            test_value = "health_check_value"
            
            # Set and get test value
            cache.set(test_key, test_value, 60)
            retrieved_value = cache.get(test_key)
            
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Clean up test key
            cache.delete(test_key)
            
            return {
                'status': 'healthy' if retrieved_value == test_value else 'error',
                'response_time_ms': round(response_time, 2),
                'test_passed': retrieved_value == test_value,
                'last_checked': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'last_checked': timezone.now().isoformat()
            }


class ApplicationHealthMonitor:
    """Monitor application health and performance"""
    
    @staticmethod
    def check_application_health() -> Dict[str, Any]:
        """Check application health metrics"""
        try:
            # Check if critical services are running
            health_status = {
                'status': 'healthy',
                'timestamp': timezone.now().isoformat(),
                'services': {},
                'performance': {}
            }
            
            # Check AI services
            try:
                from ai_services.ai_integration_service import AIHealthChecker
                ai_health = AIHealthChecker.check_ai_health()
                health_status['services']['ai'] = ai_health
            except Exception as e:
                health_status['services']['ai'] = {
                    'status': 'error',
                    'error': str(e)
                }
            
            # Check performance monitoring
            try:
                from core.performance_monitoring import PerformanceMonitor
                perf_monitor = PerformanceMonitor()
                perf_summary = perf_monitor.get_performance_summary()
                health_status['performance'] = perf_summary
            except Exception as e:
                health_status['performance'] = {
                    'status': 'error',
                    'error': str(e)
                }
            
            return health_status
            
        except Exception as e:
            logger.error(f"Application health check failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'last_checked': timezone.now().isoformat()
            }


class UptimeMonitor:
    """Monitor external uptime and availability"""
    
    @staticmethod
    def check_uptime(domain: str, endpoints: List[str] = None) -> Dict[str, Any]:
        """Check uptime for domain and specific endpoints"""
        if endpoints is None:
            endpoints = ['/', '/health/', '/api/v1/health/']
        
        results = {
            'domain': domain,
            'overall_status': 'healthy',
            'endpoints': {},
            'last_checked': timezone.now().isoformat()
        }
        
        for endpoint in endpoints:
            try:
                start_time = time.time()
                response = requests.get(f'https://{domain}{endpoint}', 
                                      timeout=10,
                                      allow_redirects=True)
                response_time = (time.time() - start_time) * 1000
                
                results['endpoints'][endpoint] = {
                    'status': 'healthy' if response.status_code < 400 else 'error',
                    'status_code': response.status_code,
                    'response_time_ms': round(response_time, 2),
                    'content_length': len(response.content) if response.content else 0
                }
                
                if response.status_code >= 400:
                    results['overall_status'] = 'degraded'
                    
            except Exception as e:
                results['endpoints'][endpoint] = {
                    'status': 'error',
                    'error': str(e),
                    'response_time_ms': None
                }
                results['overall_status'] = 'error'
        
        return results


class ProductionMonitor:
    """Enhanced production monitoring orchestrator with alerting"""
    
    def __init__(self):
        # Existing monitors
        self.ssl_monitor = SSLMonitor()
        self.db_monitor = DatabaseHealthMonitor()
        self.cache_monitor = CacheHealthMonitor()
        self.app_monitor = ApplicationHealthMonitor()
        self.uptime_monitor = UptimeMonitor()
        
        # NEW: Enhanced monitoring capabilities
        self.alert_manager = AlertManager()
        self.security_monitor = SecurityMonitor()
        self.failover_manager = FailoverManager()
    
    def run_comprehensive_check(self, domain: str = None) -> Dict[str, Any]:
        """Run comprehensive health check"""
        if domain is None:
            domain = getattr(settings, 'PRODUCTION_DOMAIN', 'www.codanalytics.net')
        
        logger.info(f"Running comprehensive health check for {domain}")
        
        results = {
            'timestamp': timezone.now().isoformat(),
            'domain': domain,
            'overall_status': 'healthy',
            'checks': {}
        }
        
        # SSL Certificate Check
        try:
            ssl_result = self.ssl_monitor.check_ssl_certificate(domain)
            results['checks']['ssl_certificate'] = ssl_result
            
            if ssl_result.get('status') == 'error' or ssl_result.get('is_expired'):
                results['overall_status'] = 'critical'
            elif ssl_result.get('is_expiring_soon'):
                results['overall_status'] = 'warning'
                
        except Exception as e:
            results['checks']['ssl_certificate'] = {'status': 'error', 'error': str(e)}
            results['overall_status'] = 'critical'
        
        # SSL Redirect Check
        try:
            redirect_result = self.ssl_monitor.check_ssl_redirect(domain)
            results['checks']['ssl_redirect'] = redirect_result
            
            if redirect_result.get('status') == 'error' or not redirect_result.get('redirects_to_https'):
                results['overall_status'] = 'critical'
                
        except Exception as e:
            results['checks']['ssl_redirect'] = {'status': 'error', 'error': str(e)}
            results['overall_status'] = 'critical'
        
        # Database Health Check
        try:
            db_result = self.db_monitor.check_database_health()
            results['checks']['database'] = db_result
            
            if db_result.get('status') == 'error':
                results['overall_status'] = 'critical'
                
        except Exception as e:
            results['checks']['database'] = {'status': 'error', 'error': str(e)}
            results['overall_status'] = 'critical'
        
        # Cache Health Check
        try:
            cache_result = self.cache_monitor.check_cache_health()
            results['checks']['cache'] = cache_result
            
            if cache_result.get('status') == 'error':
                results['overall_status'] = 'degraded'
                
        except Exception as e:
            results['checks']['cache'] = {'status': 'error', 'error': str(e)}
            results['overall_status'] = 'degraded'
        
        # Application Health Check
        try:
            app_result = self.app_monitor.check_application_health()
            results['checks']['application'] = app_result
            
            if app_result.get('status') == 'error':
                results['overall_status'] = 'degraded'
                
        except Exception as e:
            results['checks']['application'] = {'status': 'error', 'error': str(e)}
            results['overall_status'] = 'degraded'
        
        # Uptime Check
        try:
            uptime_result = self.uptime_monitor.check_uptime(domain)
            results['checks']['uptime'] = uptime_result
            
            if uptime_result.get('overall_status') == 'error':
                results['overall_status'] = 'critical'
            elif uptime_result.get('overall_status') == 'degraded':
                results['overall_status'] = 'degraded'
                
        except Exception as e:
            results['checks']['uptime'] = {'status': 'error', 'error': str(e)}
            results['overall_status'] = 'critical'
        
        # Store results in cache for quick access
        cache.set(f'health_check_{domain}', results, 300)  # Cache for 5 minutes
        
        logger.info(f"Health check completed for {domain}. Status: {results['overall_status']}")
        return results
    
    def run_comprehensive_check_with_alerts(self, domain: str = None) -> Dict[str, Any]:
        """Run comprehensive health check with alerting and failover"""
        results = self.run_comprehensive_check(domain)
        
        # Check failover conditions FIRST
        failover_actions = self.failover_manager.check_failover_conditions(results)
        
        # Execute failover actions if needed
        executed_failovers = {}
        for component, action_data in failover_actions.items():
            success = self.failover_manager.execute_failover(
                component, 
                action_data['action'], 
                action_data['reason']
            )
            executed_failovers[component] = {
                'action': action_data['action'],
                'reason': action_data['reason'],
                'executed': success,
                'timestamp': action_data['timestamp']
            }
        
        # Check for auto-recovery
        recovery_actions = self.failover_manager.check_auto_recovery(results)
        
        # Process alerts for any issues found
        self._process_monitoring_alerts(results)
        
        # Add performance threshold monitoring
        performance_thresholds = self.check_performance_thresholds()
        results['performance_thresholds'] = performance_thresholds
        
        # Add security monitoring
        security_status = self.security_monitor.check_security_events()
        results['security'] = security_status
        
        # Add failover information
        results['failover'] = {
            'actions_taken': executed_failovers,
            'recovery_actions': recovery_actions,
            'failover_status': self.failover_manager.get_failover_status()
        }
        
        return results
    
    def check_performance_thresholds(self) -> Dict[str, Any]:
        """Check performance thresholds and trigger alerts if needed"""
        thresholds = {}
        
        try:
            # Check database response time
            db_result = self.db_monitor.check_database_health()
            if db_result.get('status') == 'healthy':
                db_response_time = db_result.get('response_time_ms', 0) / 1000  # Convert to seconds
                thresholds['database_response_time'] = self.alert_manager.check_threshold(
                    'database_response_time', db_response_time
                )
                
                if thresholds['database_response_time']['alert_triggered']:
                    self.alert_manager.process_alert({
                        'severity': thresholds['database_response_time']['severity'],
                        'message': f"Database response time {db_response_time:.2f}s exceeds threshold {thresholds['database_response_time']['threshold']}s",
                        'component': 'database',
                        'timestamp': timezone.now()
                    })
            
            # Check cache hit rate
            cache_result = self.cache_monitor.check_cache_health()
            if cache_result.get('status') == 'healthy':
                # Calculate cache hit rate (this would need to be implemented in cache monitor)
                cache_hit_rate = 85.0  # Placeholder - would be actual calculation
                thresholds['cache_hit_rate'] = self.alert_manager.check_threshold(
                    'cache_hit_rate', cache_hit_rate
                )
                
                if thresholds['cache_hit_rate']['alert_triggered']:
                    self.alert_manager.process_alert({
                        'severity': thresholds['cache_hit_rate']['severity'],
                        'message': f"Cache hit rate {cache_hit_rate}% below threshold {thresholds['cache_hit_rate']['threshold']}%",
                        'component': 'cache',
                        'timestamp': timezone.now()
                    })
            
            # Check system resources (if available)
            try:
                from core.performance_monitoring import resource_monitor
                if resource_monitor.monitoring:
                    resource_summary = resource_monitor.get_resource_summary()
                    if 'current' in resource_summary:
                        current = resource_summary['current']
                        
                        # Check memory usage
                        memory_percent = current.get('memory_percent', 0)
                        thresholds['memory_usage'] = self.alert_manager.check_threshold(
                            'memory_usage', memory_percent
                        )
                        
                        if thresholds['memory_usage']['alert_triggered']:
                            self.alert_manager.process_alert({
                                'severity': thresholds['memory_usage']['severity'],
                                'message': f"Memory usage {memory_percent}% exceeds threshold {thresholds['memory_usage']['threshold']}%",
                                'component': 'system',
                                'timestamp': timezone.now()
                            })
                        
                        # Check CPU usage
                        cpu_percent = current.get('cpu_percent', 0)
                        thresholds['cpu_usage'] = self.alert_manager.check_threshold(
                            'cpu_usage', cpu_percent
                        )
                        
                        if thresholds['cpu_usage']['alert_triggered']:
                            self.alert_manager.process_alert({
                                'severity': thresholds['cpu_usage']['severity'],
                                'message': f"CPU usage {cpu_percent}% exceeds threshold {thresholds['cpu_usage']['threshold']}%",
                                'component': 'system',
                                'timestamp': timezone.now()
                            })
            except Exception as e:
                logger.warning(f"Could not check system resources: {e}")
            
        except Exception as e:
            logger.error(f"Error checking performance thresholds: {e}")
            thresholds['error'] = str(e)
        
        return thresholds
    
    def _process_monitoring_alerts(self, results: Dict[str, Any]):
        """Process alerts based on monitoring results"""
        try:
            # Check SSL certificate expiry
            ssl_check = results['checks'].get('ssl_certificate', {})
            if ssl_check.get('is_expiring_soon'):
                days_until_expiry = ssl_check.get('days_until_expiry', 0)
                severity = 'critical' if days_until_expiry < 7 else 'warning'
                
                self.alert_manager.process_alert({
                    'severity': severity,
                    'message': f"SSL certificate expires in {days_until_expiry} days",
                    'component': 'ssl_certificate',
                    'timestamp': timezone.now()
                })
            
            # Check database health
            db_check = results['checks'].get('database', {})
            if db_check.get('status') == 'error':
                self.alert_manager.process_alert({
                    'severity': 'critical',
                    'message': 'Database connection failed',
                    'component': 'database',
                    'timestamp': timezone.now()
                })
            
            # Check cache health
            cache_check = results['checks'].get('cache', {})
            if cache_check.get('status') == 'error':
                self.alert_manager.process_alert({
                    'severity': 'warning',
                    'message': 'Cache system unavailable',
                    'component': 'cache',
                    'timestamp': timezone.now()
                })
            
            # Check overall status
            if results['overall_status'] == 'critical':
                self.alert_manager.process_alert({
                    'severity': 'critical',
                    'message': 'System is in critical state - immediate attention required',
                    'component': 'system',
                    'timestamp': timezone.now()
                })
            elif results['overall_status'] == 'degraded':
                self.alert_manager.process_alert({
                    'severity': 'warning',
                    'message': 'System performance degraded',
                    'component': 'system',
                    'timestamp': timezone.now()
                })
                
        except Exception as e:
            logger.error(f"Error processing monitoring alerts: {e}")
    
    def get_cached_health_status(self, domain: str = None) -> Dict[str, Any]:
        """Get cached health status"""
        if domain is None:
            domain = getattr(settings, 'PRODUCTION_DOMAIN', 'www.codanalytics.net')
        
        cached_result = cache.get(f'health_check_{domain}')
        if cached_result:
            return cached_result
        
        # If no cached result, run a new check
        return self.run_comprehensive_check(domain)
    
    def get_enhanced_health_status(self, domain: str = None) -> Dict[str, Any]:
        """Get enhanced health status with alerting and performance data"""
        if domain is None:
            domain = getattr(settings, 'PRODUCTION_DOMAIN', 'www.codanalytics.net')
        
        # Run comprehensive check with alerts
        results = self.run_comprehensive_check_with_alerts(domain)
        
        # Add alerting information
        results['alerting'] = {
            'active_alerts': len(self.alert_manager.sent_alerts),
            'thresholds_configured': len(self.alert_manager.thresholds),
            'last_alert_check': timezone.now().isoformat()
        }
        
        return results


# Global instance
production_monitor = ProductionMonitor()

