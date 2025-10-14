"""
Failover Middleware for CODA Application
Automatically redirects users to maintenance page or backup systems during failures
"""

import logging
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.core.cache import cache
from django.conf import settings
from django.urls import reverse

logger = logging.getLogger(__name__)


class FailoverMiddleware:
    """
    Middleware to handle automatic failover and offline mode
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip failover checks for certain paths
        skip_paths = [
            '/health/',
            '/admin/',
            '/maintenance/',
            '/static/',
            '/media/',
            '/favicon.ico',
        ]
        
        if any(request.path.startswith(path) for path in skip_paths):
            return self.get_response(request)
        
        # Check if system is in offline mode
        offline_mode = cache.get('system_offline_mode')
        
        if offline_mode and offline_mode.get('active', False):
            logger.warning(f"System in offline mode - redirecting {request.path}")
            
            # Allow admin users to access the system
            if hasattr(request, 'user') and request.user.is_authenticated and request.user.is_staff:
                return self.get_response(request)
            
            # Redirect to maintenance page
            return self._show_maintenance_page(request, offline_mode)
        
        # Check for SSL failover redirect
        if self._should_redirect_to_backup(request):
            backup_url = self._get_backup_url(request)
            if backup_url:
                logger.info(f"Redirecting to backup system: {backup_url}")
                return HttpResponseRedirect(backup_url)
        
        response = self.get_response(request)
        
        # Add failover headers
        response['X-Failover-Status'] = 'primary'
        response['X-System-Health'] = self._get_system_health_status()
        
        return response
    
    def _show_maintenance_page(self, request, offline_mode):
        """Show maintenance page with system status"""
        context = {
            'offline_mode': offline_mode,
            'reason': offline_mode.get('reason', 'System maintenance'),
            'component': offline_mode.get('component', 'System'),
            'timestamp': offline_mode.get('timestamp'),
            'estimated_downtime': 'We are working to restore service as quickly as possible.',
            'contact_info': 'For urgent matters, please contact support.',
        }
        
        return render(request, 'maintenance.html', context, status=503)
    
    def _should_redirect_to_backup(self, request):
        """Check if request should be redirected to backup system"""
        # Check for SSL failover conditions
        if request.is_secure() and self._is_ssl_failing():
            return True
        
        # Check for high error rate
        if self._is_system_overloaded():
            return True
        
        return False
    
    def _get_backup_url(self, request):
        """Get backup URL for redirection"""
        # Check cache for backup URL configuration
        backup_config = cache.get('backup_system_config')
        
        if backup_config and backup_config.get('active'):
            backup_domain = backup_config.get('backup_domain')
            if backup_domain:
                protocol = 'https' if request.is_secure() else 'http'
                return f"{protocol}://{backup_domain}{request.get_full_path()}"
        
        # Fallback to HTTP if HTTPS is failing
        if request.is_secure():
            return f"http://{request.get_host()}{request.get_full_path()}"
        
        return None
    
    def _is_ssl_failing(self):
        """Check if SSL is currently failing"""
        ssl_status = cache.get('ssl_failover_status')
        return ssl_status and ssl_status.get('failing', False)
    
    def _is_system_overloaded(self):
        """Check if system is overloaded and should redirect to backup"""
        system_load = cache.get('system_load_status')
        return system_load and system_load.get('overloaded', False)
    
    def _get_system_health_status(self):
        """Get current system health status"""
        health_status = cache.get('system_health_status', 'healthy')
        return health_status


class EmergencyFailoverMiddleware:
    """
    Emergency failover middleware for critical failures
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check for emergency failover conditions
        emergency_mode = cache.get('emergency_failover_mode')
        
        if emergency_mode and emergency_mode.get('active', False):
            logger.critical(f"EMERGENCY FAILOVER ACTIVE - {request.path}")
            
            # Show emergency maintenance page
            context = {
                'emergency_mode': True,
                'message': 'We are experiencing technical difficulties. Our team is working to resolve this issue.',
                'estimated_resolution': 'We expect to have service restored within the next hour.',
                'alternative_contact': 'For urgent matters, please contact us directly.',
            }
            
            return render(request, 'emergency_maintenance.html', context, status=503)
        
        return self.get_response(request)

