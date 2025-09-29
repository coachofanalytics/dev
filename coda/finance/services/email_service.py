"""
Optimized Email Service for Automation System

This service integrates with existing email functionality to avoid code duplication.
It extends the existing email service to support automation-specific notifications.
"""

import logging
from django.template.loader import render_to_string
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

from .base_service import BaseFinanceService

# Import existing email functionality
try:
    from mail.services.email_service import EmailService as BaseEmailService
    from mail.custom_email import send_email
except ImportError:
    # Fallback if mail services not available
    BaseEmailService = send_email = None

logger = logging.getLogger(__name__)


class EmailService(BaseFinanceService):
    """Email service for automation system - integrates with existing mail services"""
    
    def __init__(self):
        super().__init__()
        self.base_email_service = BaseEmailService() if BaseEmailService else None
        self.site_name = getattr(settings, 'SITE_NAME', 'CODA')
        self.site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
    
    def send_generic_email(self, to_email, subject, template, context):
        """Send generic email using existing email service"""
        try:
            if self.base_email_service:
                # Use existing email service
                success = self.base_email_service.send_generic_notification(
                    to_email=to_email,
                    subject=subject,
                    template=template,
                    context=context
                )
                logger.info(f"Generic email sent using base service to {to_email}")
                return success
            else:
                # Fallback to custom email function
                return send_email(
                    to_email=to_email,
                    subject=subject,
                    template=template,
                    context=context
                )
                
        except Exception as e:
            logger.error(f"Error sending generic email: {str(e)}")
            return False
    
    def send_budget_request_submitted_email(self, user, request):
        """Send budget request submitted notification"""
        try:
            context = {
                'user': user,
                'request': request,
                'site_name': self.site_name,
                'site_url': self.site_url,
                'timestamp': timezone.now()
            }
            
            # Use existing email service with automation template
            success = self.send_generic_email(
                to_email=[user.email],
                subject=f"Budget Request Submitted - {self.site_name}",
                template='emails/budget_request_submitted.html',
                context=context
            )
            
            if success:
                logger.info(f"Budget request submitted email sent to {user.email}")
            else:
                logger.error(f"Failed to send budget request submitted email to {user.email}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending budget request submitted email: {str(e)}")
            return False
    
    def send_approval_required_email(self, approver, request):
        """Send approval required notification"""
        try:
            context = {
                'user': approver,
                'request': request,
                'site_name': self.site_name,
                'site_url': self.site_url,
                'timestamp': timezone.now()
            }
            
            success = self.send_generic_email(
                to_email=[approver.email],
                subject=f"Approval Required - Budget Request #{request.id} - {self.site_name}",
                template='emails/approval_required.html',
                context=context
            )
            
            if success:
                logger.info(f"Approval required email sent to {approver.email}")
            else:
                logger.error(f"Failed to send approval required email to {approver.email}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending approval required email: {str(e)}")
            return False
    
    def send_approval_decision_email(self, user, request, decision):
        """Send approval decision notification"""
        try:
            context = {
                'user': user,
                'request': request,
                'decision': decision,
                'site_name': self.site_name,
                'site_url': self.site_url,
                'timestamp': timezone.now()
            }
            
            success = self.send_generic_email(
                to_email=[user.email],
                subject=f"Budget Request {decision.title()} - {self.site_name}",
                template='emails/approval_decision.html',
                context=context
            )
            
            if success:
                logger.info(f"Approval decision email sent to {user.email}")
            else:
                logger.error(f"Failed to send approval decision email to {user.email}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending approval decision email: {str(e)}")
            return False
    
    def send_otp_email(self, user, otp_code, disbursement_request=None):
        """Send OTP verification email"""
        try:
            context = {
                'user': user,
                'otp_code': otp_code,
                'disbursement_request': disbursement_request,
                'site_name': self.site_name,
                'site_url': self.site_url,
                'timestamp': timezone.now(),
                'expires_in': 10  # minutes
            }
            
            success = self.send_generic_email(
                to_email=[user.email],
                subject=f"OTP Verification - {self.site_name}",
                template='emails/otp_verification.html',
                context=context
            )
            
            if success:
                logger.info(f"OTP email sent to {user.email}")
            else:
                logger.error(f"Failed to send OTP email to {user.email}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending OTP email: {str(e)}")
            return False
    
    def send_disbursement_notification(self, user, disbursement, notification_type='otp_sent'):
        """Send disbursement notification"""
        try:
            context = {
                'user': user,
                'disbursement': disbursement,
                'site_name': self.site_name,
                'site_url': self.site_url,
                'timestamp': timezone.now()
            }
            
            # Choose template based on notification type
            template_map = {
                'otp_sent': 'emails/otp_verification.html',
                'completed': 'emails/disbursement_completed.html',
                'failed': 'emails/disbursement_failed.html'
            }
            
            template = template_map.get(notification_type, 'emails/disbursement_completed.html')
            
            success = self.send_generic_email(
                to_email=[user.email],
                subject=f"Disbursement {notification_type.title()} - {self.site_name}",
                template=template,
                context=context
            )
            
            if success:
                logger.info(f"Disbursement {notification_type} email sent to {user.email}")
            else:
                logger.error(f"Failed to send disbursement {notification_type} email to {user.email}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending disbursement notification: {str(e)}")
            return False
    
    def send_escalation_notification(self, user, request, escalation_level):
        """Send escalation notification"""
        try:
            context = {
                'user': user,
                'request': request,
                'escalation_level': escalation_level,
                'site_name': self.site_name,
                'site_url': self.site_url,
                'timestamp': timezone.now()
            }
            
            success = self.send_generic_email(
                to_email=[user.email],
                subject=f"Budget Request Escalated - {self.site_name}",
                template='emails/escalation_notification.html',
                context=context
            )
            
            if success:
                logger.info(f"Escalation notification sent to {user.email}")
            else:
                logger.error(f"Failed to send escalation notification to {user.email}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending escalation notification: {str(e)}")
            return False
    
    def send_test_email(self, user):
        """Send test email to verify email system"""
        try:
            context = {
                'user': user,
                'site_name': self.site_name,
                'site_url': self.site_url,
                'timestamp': timezone.now(),
                'django_version': getattr(settings, 'DJANGO_VERSION', 'Unknown'),
                'python_version': f"{__import__('sys').version_info.major}.{__import__('sys').version_info.minor}.{__import__('sys').version_info.micro}",
                'timezone': str(timezone.get_current_timezone())
            }
            
            success = self.send_generic_email(
                to_email=[user.email],
                subject=f"Test Email - {self.site_name}",
                template='emails/test_email.html',
                context=context
            )
            
            if success:
                logger.info(f"Test email sent to {user.email}")
            else:
                logger.error(f"Failed to send test email to {user.email}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending test email: {str(e)}")
            return False
    
    def _html_to_text(self, html_content):
        """Convert HTML content to plain text (simple implementation)"""
        try:
            import re
            # Remove HTML tags
            text = re.sub(r'<[^>]+>', '', html_content)
            # Clean up whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            return text
        except Exception as e:
            logger.error(f"Error converting HTML to text: {str(e)}")
            return html_content
