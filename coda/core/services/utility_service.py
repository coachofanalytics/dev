"""
Centralized Utility Service

This service consolidates all utility functionality across the CODA application
to eliminate duplication and provide a single source of truth for utility operations.

Replaces duplicate utility functions in:
- main/utilities/
- ai_services/utilities/
- management/utils.py
- Various other apps
"""

import logging
import random
import string
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from django.utils import timezone
from django.utils.text import slugify
from django.db import models

logger = logging.getLogger(__name__)


class UtilityService:
    """
    Centralized utility service that provides common utility functions
    used across the CODA application.
    
    This service consolidates utility functionality from multiple implementations
    into a single, robust service.
    """
    
    def __init__(self):
        self.logger = logger
    
    def generate_password_and_otp(self, password_length: int = 12, otp_length: int = 6) -> tuple:
        """
        Generate password and OTP.
        
        Uses: core/utils.py generate_password_and_otp()
        
        Args:
            password_length: Length of password to generate
            otp_length: Length of OTP to generate
            
        Returns:
            Tuple of (password, otp)
        """
        try:
            password = self._generate_password(password_length)
            otp = self._generate_otp(otp_length)
            return password, otp
        except Exception as e:
            self.logger.error(f"Error generating password and OTP: {e}")
            return "default_password", "123456"
    
    def generate_and_send_otp(self, email: str, length: int = 6) -> str:
        """
        Generate and send OTP.
        
        Uses: core/utils.py generate_and_send_otp()
        
        Args:
            email: Email address to send OTP to
            length: Length of OTP to generate
            
        Returns:
            Generated OTP string
        """
        try:
            otp = self._generate_otp(length)
            
            # Send OTP via email
            from mail.services.email_service import email_service
            
            context = {
                'otp': otp,
                'email': email,
                'purpose': 'otp_verification'
            }
            
            success = email_service.send_generic_notification(
                to_email=[email],
                subject="CODA - Your Verification Code",
                template='email/otp_verification.html',
                context=context
            )
            
            if success:
                return otp
            else:
                self.logger.warning(f"Failed to send OTP email to {email}")
                return otp  # Still return OTP even if email fails
                
        except Exception as e:
            self.logger.error(f"Error generating and sending OTP: {e}")
            return self._generate_otp(length)  # Fallback
    
    def verify_otp(self, user_otp: str, stored_otp: str) -> bool:
        """
        Verify OTP.
        
        Uses: core/utils.py verify_otp()
        
        Args:
            user_otp: OTP provided by user
            stored_otp: OTP stored in system
            
        Returns:
            True if OTP is valid
        """
        try:
            return user_otp == stored_otp
        except Exception as e:
            self.logger.error(f"Error verifying OTP: {e}")
            return False
    
    def convert_date(self, date_string: str) -> Optional[datetime]:
        """
        Convert date string to datetime object.
        
        Uses: main/utilities/date_utils.py date_converter()
        
        Args:
            date_string: Date string in various formats
            
        Returns:
            datetime object or None if conversion fails
        """
        try:
            if not date_string:
                return None
            
            date_formats = [
                '%Y-%m-%d %H:%M:%S', 
                '%m/%d/%Y', 
                '%Y-%m-%d',
                '%d/%m/%Y',
                '%Y-%m-%d %H:%M',
                '%m-%d-%Y',
                '%d-%m-%Y'
            ]
            
            for date_format in date_formats:
                try:
                    return datetime.strptime(date_string, date_format)
                except ValueError:
                    continue
            
            # If no format matches, try parsing with dateutil
            try:
                from dateutil import parser
                return parser.parse(date_string)
            except ImportError:
                pass
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error converting date: {e}")
            return None
    
    def get_15th_of_next_month(self) -> datetime:
        """
        Get the 15th day of next month.
        
        Uses: main/utilities/date_utils.py get_15th_of_next_month()
        
        Returns:
            datetime object for 15th of next month
        """
        try:
            today = timezone.now().date()
            
            # Calculate next month
            if today.month == 12:
                next_month = today.replace(year=today.year + 1, month=1, day=15)
            else:
                next_month = today.replace(month=today.month + 1, day=15)
            
            return datetime.combine(next_month, datetime.min.time())
            
        except Exception as e:
            self.logger.error(f"Error getting 15th of next month: {e}")
            return timezone.now()
    
    def generate_unique_slug(self, instance, new_slug: Optional[str] = None) -> str:
        """
        Generate unique slug for model instance.
        
        Uses: management/utils.py unique_slug_generator()
        
        Args:
            instance: Model instance
            new_slug: Optional custom slug
            
        Returns:
            Unique slug string
        """
        try:
            if new_slug is not None:
                slug = new_slug
            else:
                # Generate slug from name or title
                if hasattr(instance, 'name') and instance.name:
                    slug = slugify(instance.name)
                elif hasattr(instance, 'title') and instance.title:
                    slug = slugify(instance.title)
                else:
                    slug = slugify(str(instance))
            
            # Ensure slug is not empty
            if not slug:
                slug = "untitled"
            
            # Check for uniqueness
            model_class = instance.__class__
            original_slug = slug
            
            counter = 1
            while model_class.objects.filter(slug=slug).exists():
                slug = f"{original_slug}-{counter}"
                counter += 1
            
            return slug
            
        except Exception as e:
            self.logger.error(f"Error generating unique slug: {e}")
            return f"slug-{random.randint(1000, 9999)}"
    
    def split_num_str(self, my_str: str) -> List[str]:
        """
        Split numeric string into individual characters.
        
        Uses: management/utils.py split_num_str()
        
        Args:
            my_str: String to split
            
        Returns:
            List of individual characters
        """
        try:
            return list(my_str)
        except Exception as e:
            self.logger.error(f"Error splitting numeric string: {e}")
            return []
    
    def generate_random_string(self, length: int = 10) -> str:
        """
        Generate random string.
        
        Args:
            length: Length of string to generate
            
        Returns:
            Random string
        """
        try:
            return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
        except Exception as e:
            self.logger.error(f"Error generating random string: {e}")
            return "default_string"
    
    def format_currency(self, amount: float, currency: str = "USD") -> str:
        """
        Format currency amount.
        
        Args:
            amount: Amount to format
            currency: Currency code
            
        Returns:
            Formatted currency string
        """
        try:
            if currency == "USD":
                return f"${amount:,.2f}"
            elif currency == "KES":
                return f"KSh {amount:,.2f}"
            else:
                return f"{currency} {amount:,.2f}"
        except Exception as e:
            self.logger.error(f"Error formatting currency: {e}")
            return str(amount)
    
    def calculate_age(self, birth_date: datetime) -> int:
        """
        Calculate age from birth date.
        
        Args:
            birth_date: Birth date
            
        Returns:
            Age in years
        """
        try:
            today = timezone.now().date()
            return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        except Exception as e:
            self.logger.error(f"Error calculating age: {e}")
            return 0
    
    def _generate_password(self, length: int) -> str:
        """Generate secure password."""
        try:
            characters = string.ascii_letters + string.digits + "!@#$%^&*"
            return ''.join(random.choices(characters, k=length))
        except Exception as e:
            self.logger.error(f"Error generating password: {e}")
            return "default_password"
    
    def _generate_otp(self, length: int) -> str:
        """Generate OTP."""
        try:
            return ''.join(random.choices(string.digits, k=length))
        except Exception as e:
            self.logger.error(f"Error generating OTP: {e}")
            return "123456"
    
    def random_string_generator(self, size: int = 25, chars: str = string.ascii_lowercase + string.digits) -> str:
        """Generate a random string of specified size and characters."""
        try:
            return ''.join(random.choice(chars) for _ in range(size))
        except Exception as e:
            self.logger.error(f"Error generating random string: {e}")
            return "default_string"


# Global instance for easy access
utility_service = UtilityService()

