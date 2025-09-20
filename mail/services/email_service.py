"""
Centralized Email Service

This service consolidates all email functionality across the CODA application
to eliminate duplication and provide a single source of truth for email operations.

Replaces duplicate email functions in:
- accounts/utils.py
- finance/utils.py  
- management/utils.py
- investing/utils.py
- ai_services/utilities/email_utils.py
"""

import logging
from typing import List, Dict, Any, Optional
from django.shortcuts import render
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.core.mail.backends.smtp import EmailBackend
from django.conf import settings
from ..custom_email import send_email, validate_email_address

logger = logging.getLogger(__name__)


class EmailService:
    """
    Centralized email service using the robust mail/custom_email.py implementation.
    
    This service provides a unified interface for all email operations across
    the CODA application, eliminating duplicate email implementations.
    """
    
    def __init__(self):
        self.logger = logger
    
    def send_verification_email(self, user, password: Optional[str] = None) -> bool:
        """
        Send user verification email.
        
        Replaces: accounts/utils.py send_verification_email()
        
        Args:
            user: User instance
            password: Optional password for new users
            
        Returns:
            bool: True if email sent successfully
        """
        try:
            subject = "Welcome to CODA - Email Verification"
            
            context = {
                'user': user,
                'password': password,
                'verification_url': f"{settings.BASE_URL}/accounts/verify/{user.id}/",
                'purpose': 'verification'
            }
            
            return send_email(
                category=0,  # Use EMAIL_INFO
                to_email=[user.email],
                subject=subject,
                html_template='accounts/registration/verification_email.html',
                context=context
            )
            
        except Exception as e:
            self.logger.error(f"Error sending verification email: {e}")
            return False
    
    def send_application_email(self, instance) -> bool:
        """
        Send application status email to applicant.
        
        Replaces: accounts/utils.py send_email_to_applicant()
        
        Args:
            instance: Application instance
            
        Returns:
            bool: True if email sent successfully
        """
        try:
            subject = "Update on Your Application Progress"
            
            context = {
                'user': instance,
                'application': instance,
                'purpose': 'application_update'
            }
            
            return send_email(
                category=0,  # Use EMAIL_INFO
                to_email=[instance.email],
                subject=subject,
                html_template='accounts/verification_applicant.html',
                context=context
            )
            
        except Exception as e:
            self.logger.error(f"Error sending application email: {e}")
            return False
    
    def send_finance_notification(self, loan_application, notification_type: str) -> bool:
        """
        Send finance notification email.
        
        Replaces: finance/utils.py send_borrower_notification_email()
        
        Args:
            loan_application: Loan application instance
            notification_type: Type of notification
            
        Returns:
            bool: True if email sent successfully
        """
        try:
            subject = f"Loan Application Update - {notification_type.title()}"
            
            context = {
                'loan_application': loan_application,
                'notification_type': notification_type,
                'purpose': 'payment'
            }
            
            return send_email(
                category=2,  # Use EMAIL_FIN for finance
                to_email=[loan_application.borrower.email],
                subject=subject,
                html_template='finance/email/loan_notification.html',
                context=context
            )
            
        except Exception as e:
            self.logger.error(f"Error sending finance notification: {e}")
            return False
    
    def send_guarantor_verification_email(self, loan_application, guarantor) -> bool:
        """
        Send guarantor verification success email.
        
        Replaces: finance/utils.py send_guarantor_verification_success_email()
        
        Args:
            loan_application: Loan application instance
            guarantor: Guarantor instance
            
        Returns:
            bool: True if email sent successfully
        """
        try:
            subject = "Guarantor Verification Successful"
            
            context = {
                'loan_application': loan_application,
                'guarantor': guarantor,
                'purpose': 'payment'
            }
            
            return send_email(
                category=2,  # Use EMAIL_FIN for finance
                to_email=[guarantor.email],
                subject=subject,
                html_template='finance/email/guarantor_verification_success.html',
                context=context
            )
            
        except Exception as e:
            self.logger.error(f"Error sending guarantor verification email: {e}")
            return False
    
    def send_investor_welcome_email(self, investment) -> bool:
        """
        Send investor welcome email.
        
        Replaces: investing/utils.py send_investor_welcome_email()
        
        Args:
            investment: Investment instance
            
        Returns:
            bool: True if email sent successfully
        """
        try:
            subject = "Welcome to CODA Investment Platform"
            
            context = {
                'investment': investment,
                'investor': investment.investor,
                'purpose': 'investment'
            }
            
            return send_email(
                category=0,  # Use EMAIL_INFO
                to_email=[investment.investor.email],
                subject=subject,
                html_template='investing/email/investor_welcome.html',
                context=context
            )
            
        except Exception as e:
            self.logger.error(f"Error sending investor welcome email: {e}")
            return False
    
    def send_generic_notification(self, to_email: List[str], subject: str, 
                                template: str, context: Dict[str, Any], 
                                category: int = 0) -> bool:
        """
        Send generic notification email.
        
        Replaces: management/utils.py email_template()
        
        Args:
            to_email: List of recipient email addresses
            subject: Email subject
            template: Template path
            context: Template context
            category: Email category (0=INFO, 1=HR, 2=FIN)
            
        Returns:
            bool: True if email sent successfully
        """
        try:
            return send_email(
                category=category,
                to_email=to_email,
                subject=subject,
                html_template=template,
                context=context
            )
            
        except Exception as e:
            self.logger.error(f"Error sending generic notification: {e}")
            return False
    
    def send_system_alert(self, alert_data: Dict[str, Any]) -> bool:
        """
        Send system alert email to administrators.
        
        Used by: core/production_monitoring.py AlertManager
        
        Args:
            alert_data: Alert information
            
        Returns:
            bool: True if email sent successfully
        """
        try:
            subject = f"🚨 CODA Alert: {alert_data.get('component', 'System')} - {alert_data.get('severity', 'Warning').upper()}"
            
            context = {
                'alert_data': alert_data,
                'timestamp': alert_data.get('timestamp'),
                'domain': getattr(settings, 'PRODUCTION_DOMAIN', 'www.codanalytics.net'),
                'purpose': 'system_alert'
            }
            
            # Get admin emails
            from django.contrib.auth.models import User
            admin_users = User.objects.filter(is_staff=True, is_active=True)
            admin_emails = [user.email for user in admin_users if user.email]
            
            if not admin_emails:
                self.logger.warning("No admin emails found for system alert")
                return False
            
            return send_email(
                category=1,  # Use EMAIL_HR for system alerts
                to_email=admin_emails,
                subject=subject,
                html_template='email/system_alert.html',
                context=context
            )
            
        except Exception as e:
            self.logger.error(f"Error sending system alert: {e}")
            return False
    
    def validate_emails(self, email_list: List[str]) -> Dict[str, List[str]]:
        """
        Validate a list of email addresses.
        
        Args:
            email_list: List of email addresses to validate
            
        Returns:
            Dict with 'valid' and 'invalid' email lists
        """
        valid_emails = []
        invalid_emails = []
        
        for email in email_list:
            if validate_email_address(email):
                valid_emails.append(email)
            else:
                invalid_emails.append(email)
        
        return {
            'valid': valid_emails,
            'invalid': invalid_emails
        }


# Global instance for easy access
email_service = EmailService()
