"""
Payment Control Middleware for CODA Client Sites
Blocks site access when client payment is not made
"""

import logging
import os
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.conf import settings
from django.urls import reverse

logger = logging.getLogger(__name__)


class PaymentControlMiddleware:
    """
    Middleware to control site access based on payment status
    Reads PAYMENT_STATUS from Heroku environment variables
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip payment checks for certain paths
        skip_paths = [
            '/admin/',
            '/static/',
            '/media/',
            '/favicon.ico',
            '/health/',
            '/payment-status/',  # Allow access to payment status page
        ]
        
        # Skip if path starts with any skip pattern
        if any(request.path.startswith(path) for path in skip_paths):
            return self.get_response(request)
        
        # Check payment status from environment variable
        payment_status = self._get_payment_status()
        
        if not payment_status['is_paid']:
            logger.warning(f"Payment not made - blocking access to {request.path}")
            
            # Allow admin/staff users to access the system
            if self._is_admin_user(request):
                logger.info(f"Admin user {request.user} accessing system despite payment status")
                return self.get_response(request)
            
            # Block access and show payment required page
            return self._show_payment_required_page(request, payment_status)
        
        # Payment is made, allow access
        return self.get_response(request)
    
    def _get_payment_status(self):
        """
        Get payment status from Heroku environment variables
        """
        try:
            # Primary payment status variable
            payment_made = os.environ.get('PAYMENT_MADE', 'true').lower()
            
            # Alternative payment status variable (for flexibility)
            payment_status = os.environ.get('PAYMENT_STATUS', 'active').lower()
            
            # Client name for customization
            client_name = os.environ.get('CLIENT_NAME', 'Client')
            
            # Payment due date
            payment_due = os.environ.get('PAYMENT_DUE_DATE', '')
            
            # Grace period in days (optional)
            grace_period_days = int(os.environ.get('PAYMENT_GRACE_DAYS', '0'))
            
            # Determine if payment is made
            is_paid = (
                payment_made in ['true', '1', 'yes', 'paid'] or
                payment_status in ['active', 'paid', 'current']
            )
            
            return {
                'is_paid': is_paid,
                'client_name': client_name,
                'payment_due': payment_due,
                'grace_period_days': grace_period_days,
                'payment_status': payment_status,
                'payment_made': payment_made,
            }
            
        except Exception as e:
            logger.error(f"Error getting payment status: {e}")
            # Default to allowing access if there's an error
            return {
                'is_paid': True,
                'client_name': 'Client',
                'payment_due': '',
                'grace_period_days': 0,
                'payment_status': 'unknown',
                'payment_made': 'unknown',
            }
    
    def _is_admin_user(self, request):
        """
        Check if user is admin or staff
        """
        if hasattr(request, 'user') and request.user.is_authenticated:
            return request.user.is_staff or request.user.is_superuser
        return False
    
    def _show_payment_required_page(self, request, payment_status):
        """
        Show payment required page
        """
        context = {
            'client_name': payment_status['client_name'],
            'payment_due': payment_status['payment_due'],
            'grace_period_days': payment_status['grace_period_days'],
            'payment_status': payment_status['payment_status'],
            'site_url': request.build_absolute_uri('/'),
        }
        
        # Try to render custom template, fallback to simple response
        try:
            return render(request, 'payment_required.html', context, status=503)
        except:
            # Fallback simple HTML response
            html_content = self._get_fallback_payment_page(context)
            return HttpResponse(html_content, status=503, content_type='text/html')
    
    def _get_fallback_payment_page(self, context):
        """
        Generate fallback payment required page HTML
        """
        client_name = context['client_name']
        payment_due = context['payment_due']
        
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Payment Required - {client_name}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f8f9fa;
                    margin: 0;
                    padding: 20px;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                }}
                .container {{
                    background: white;
                    padding: 40px;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    text-align: center;
                    max-width: 600px;
                }}
                .icon {{
                    font-size: 64px;
                    color: #dc3545;
                    margin-bottom: 20px;
                }}
                h1 {{
                    color: #333;
                    margin-bottom: 20px;
                }}
                .message {{
                    color: #666;
                    line-height: 1.6;
                    margin-bottom: 30px;
                }}
                .contact {{
                    background-color: #f8f9fa;
                    padding: 20px;
                    border-radius: 5px;
                    margin-top: 30px;
                }}
                .contact h3 {{
                    margin-top: 0;
                    color: #333;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="icon">🔒</div>
                <h1>Service Temporarily Unavailable</h1>
                <div class="message">
                    <p><strong>Dear {client_name},</strong></p>
                    <p>Your website access has been temporarily suspended due to outstanding payment.</p>
                    {f'<p><strong>Payment Due:</strong> {payment_due}</p>' if payment_due else ''}
                    <p>Please contact your account manager or our support team to restore access.</p>
                </div>
                <div class="contact">
                    <h3>Need Help?</h3>
                    <p>Contact CODA Support:</p>
                    <p>Email: support@codatrainingapp.com</p>
                    <p>Phone: +254 XXX XXX XXX</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html


class PaymentStatusView:
    """
    View class to check payment status via API endpoint
    """
    
    @staticmethod
    def get_payment_status(request):
        """
        API endpoint to check current payment status
        """
        from django.http import JsonResponse
        
        middleware = PaymentControlMiddleware(lambda x: None)
        payment_status = middleware._get_payment_status()
        
        return JsonResponse({
            'payment_made': payment_status['is_paid'],
            'client_name': payment_status['client_name'],
            'payment_due': payment_status['payment_due'],
            'status': 'active' if payment_status['is_paid'] else 'suspended',
            'timestamp': middleware._get_current_timestamp(),
        })
    
    @staticmethod
    def _get_current_timestamp():
        """
        Get current timestamp for API response
        """
        from datetime import datetime
        return datetime.now().isoformat()








