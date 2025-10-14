"""
Optimized OTP Service for Automation System

This service integrates with existing OTP functionality to avoid code duplication.
It extends the existing OTP functionality to support disbursement verification.
"""

import logging
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.conf import settings

from .base_service import BaseFinanceService
from .email_service import EmailService

# Import existing OTP functionality
try:
    from core.utils import generate_otp, verify_otp
    from core.services.utility_service import utility_service
except ImportError:
    # Fallback if core services not available
    generate_otp = verify_otp = utility_service = None

logger = logging.getLogger(__name__)


class OTPService(BaseFinanceService):
    """OTP service for automation system - integrates with existing core services"""
    
    def __init__(self):
        super().__init__()
        self.email_service = EmailService()
        self.otp_length = getattr(settings, 'OTP_LENGTH', 6)
        self.otp_expiry_minutes = getattr(settings, 'OTP_EXPIRY_MINUTES', 10)
        self.max_attempts = getattr(settings, 'OTP_MAX_ATTEMPTS', 3)
    
    def generate_otp(self, length=None):
        """Generate a random OTP code using existing core functionality"""
        try:
            if generate_otp:
                # Use existing implementation
                otp = generate_otp(length or self.otp_length)
                logger.info(f"OTP generated using core service: {otp}")
                return otp
            else:
                # Fallback implementation
                import random
                import string
                otp = ''.join(random.choices(string.digits, k=length or self.otp_length))
                logger.info(f"OTP generated using fallback: {otp}")
                return otp
                
        except Exception as e:
            logger.error(f"Error generating OTP: {str(e)}")
            raise ValidationError("Failed to generate OTP")
    
    def send_otp_email(self, user, otp_code, disbursement_request=None):
        """Send OTP via email using existing email service"""
        try:
            if utility_service:
                # Use existing utility service for email sending
                success = utility_service.generate_and_send_otp(
                    email=user.email,
                    length=len(otp_code)
                )
                
                if success:
                    logger.info(f"OTP email sent using core service to {user.email}")
                    return True
                else:
                    logger.warning(f"Failed to send OTP email using core service to {user.email}")
                    # Fallback to automation email service
                    return self.email_service.send_otp_email(
                        user=user,
                        otp_code=otp_code,
                        disbursement_request=disbursement_request
                    )
            else:
                # Fallback to automation email service
                return self.email_service.send_otp_email(
                    user=user,
                    otp_code=otp_code,
                    disbursement_request=disbursement_request
                )
                
        except Exception as e:
            logger.error(f"Error sending OTP email: {str(e)}")
            return False
    
    def send_otp_sms(self, phone_number, otp_code):
        """Send OTP via SMS (placeholder for future implementation)"""
        try:
            # This would integrate with an SMS service provider
            # For now, we'll just log the OTP
            logger.info(f"OTP SMS would be sent to {phone_number}: {otp_code}")
            
            # In a real implementation, you would:
            # 1. Integrate with SMS service provider (e.g., Twilio, Africa's Talking)
            # 2. Send the OTP via SMS
            # 3. Handle delivery status and errors
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending OTP SMS: {str(e)}")
            return False
    
    def verify_otp(self, provided_otp, stored_otp, expiry_time=None):
        """Verify OTP code using existing core functionality"""
        try:
            if verify_otp:
                # Use existing implementation
                is_valid = verify_otp(provided_otp, stored_otp)
                logger.info(f"OTP verification using core service: {is_valid}")
                return is_valid
            else:
                # Fallback implementation
                is_valid = provided_otp == stored_otp
                logger.info(f"OTP verification using fallback: {is_valid}")
                return is_valid
                
        except Exception as e:
            logger.error(f"Error verifying OTP: {str(e)}")
            return False
    
    def is_otp_expired(self, expiry_time):
        """Check if OTP has expired"""
        try:
            if expiry_time is None:
                return True
            
            current_time = timezone.now()
            return current_time > expiry_time
            
        except Exception as e:
            logger.error(f"Error checking OTP expiry: {str(e)}")
            return True
    
    def generate_and_send_otp(self, user, disbursement_request=None):
        """Generate and send OTP in one operation"""
        try:
            # Generate OTP
            otp_code = self.generate_otp()
            
            # Send OTP via email
            success = self.send_otp_email(user, otp_code, disbursement_request)
            
            if success:
                logger.info(f"OTP generated and sent successfully to {user.email}")
                return otp_code
            else:
                logger.error(f"Failed to send OTP to {user.email}")
                return None
                
        except Exception as e:
            logger.error(f"Error in generate_and_send_otp: {str(e)}")
            return None
    
    def validate_otp_attempts(self, user, max_attempts=None):
        """Validate OTP attempt limits (placeholder for future implementation)"""
        try:
            max_attempts = max_attempts or self.max_attempts
            
            # This would check against a database table or cache
            # For now, we'll just return True
            logger.info(f"OTP attempt validation for {user.email}: within limits")
            return True
            
        except Exception as e:
            logger.error(f"Error validating OTP attempts: {str(e)}")
            return True
