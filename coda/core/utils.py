# In uat/core/utils.py
import random
import string
import secrets
import logging

logger = logging.getLogger(__name__)

def generate_otp(length=6):
    """Generate OTP only - for verification purposes"""
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))

def generate_password(length=12):
    """Generate secure password only - for user accounts"""
    characters = string.ascii_letters + string.digits + "!@#$%&"
    return ''.join(secrets.choice(characters) for _ in range(length))

def generate_password_and_otp(password_length=12, otp_length=6):
    """Generate both password and OTP using centralized utility service."""
    try:
        from core.services.utility_service import utility_service
        return utility_service.generate_password_and_otp(password_length, otp_length)
    except Exception as e:
        logger.error(f"Error in generate_password_and_otp: {e}")
        return generate_password(password_length), generate_otp(otp_length)

def generate_and_send_otp(email, length=6):
    """Generate OTP and send to email using centralized utility service."""
    try:
        from core.services.utility_service import utility_service
        return utility_service.generate_and_send_otp(email, length)
    except Exception as e:
        logger.error(f"Error in generate_and_send_otp: {e}")
        return generate_otp(length)  # Fallback

def verify_otp(user_otp, stored_otp):
    """Verify OTP using centralized utility service."""
    try:
        from core.services.utility_service import utility_service
        return utility_service.verify_otp(user_otp, stored_otp)
    except Exception as e:
        logger.error(f"Error in verify_otp: {e}")
        return user_otp.upper() == stored_otp.upper()