"""
Date Utilities

Handles all date-related operations including:
- Date conversion and formatting
- Date calculations and manipulations
- Notification scheduling
- Group switching based on dates

This utility encapsulates date-related functionality previously scattered across main/utils.py
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from django.utils import timezone

logger = logging.getLogger(__name__)


class DateUtils:
    """
    Utility class for date-related operations.
    
    Provides methods for date conversion, calculations, and scheduling.
    """
    
    def __init__(self):
        self.logger = logger
    
    def date_converter(self, date_string: str) -> Optional[datetime]:
        """
        Convert date string to datetime object.
        
        Args:
            date_string: Date string in various formats
            
        Returns:
            datetime object or None if conversion fails
        """
        try:
            if not date_string:
                return None
            
            # Try different date formats
            formats = [
                '%Y-%m-%d',
                '%m/%d/%Y',
                '%d/%m/%Y',
                '%Y-%m-%d %H:%M:%S',
                '%m/%d/%Y %H:%M:%S',
                '%d/%m/%Y %H:%M:%S'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_string, fmt)
                except ValueError:
                    continue
            
            # If no format matches, try parsing with dateutil
            try:
                from dateutil import parser
                return parser.parse(date_string)
            except ImportError:
                self.logger.warning(f"dateutil not available, cannot parse date: {date_string}")
                return None
            except Exception as e:
                self.logger.error(f"Error parsing date '{date_string}': {e}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error in date_converter: {e}")
            return None
    
    def get_15th_of_next_month(self) -> datetime:
        """
        Get the 15th day of the next month.
        
        Returns:
            datetime object representing the 15th of next month
        """
        try:
            now = timezone.now()
            
            # Calculate next month
            if now.month == 12:
                next_month = now.replace(year=now.year + 1, month=1, day=15)
            else:
                next_month = now.replace(month=now.month + 1, day=15)
            
            return next_month
            
        except Exception as e:
            self.logger.error(f"Error calculating 15th of next month: {e}")
            return timezone.now() + timedelta(days=30)
    
    def get_next_group_name(self, current_group_name: str) -> str:
        """
        Get the next group name in sequence.
        
        Args:
            current_group_name: Current group name
            
        Returns:
            Next group name in sequence
        """
        try:
            # Extract number from group name if it exists
            if current_group_name and current_group_name[-1].isdigit():
                group_number = int(current_group_name[-1])
                next_number = (group_number % 3) + 1  # Cycle through 1, 2, 3
                return current_group_name[:-1] + str(next_number)
            else:
                return current_group_name + "1"
                
        except Exception as e:
            self.logger.error(f"Error getting next group name: {e}")
            return current_group_name + "1"
    
    def switch_groups(self) -> Dict[str, Any]:
        """
        Switch groups based on current date.
        
        Returns:
            Dict with group switching information
        """
        try:
            now = timezone.now()
            day_of_month = now.day
            
            # Determine which group should be active based on day of month
            if day_of_month <= 10:
                active_group = "Group1"
            elif day_of_month <= 20:
                active_group = "Group2"
            else:
                active_group = "Group3"
            
            return {
                'active_group': active_group,
                'day_of_month': day_of_month,
                'switch_date': now,
                'next_switch': self.get_15th_of_next_month()
            }
            
        except Exception as e:
            self.logger.error(f"Error switching groups: {e}")
            return {
                'active_group': "Group1",
                'day_of_month': 1,
                'switch_date': timezone.now(),
                'next_switch': timezone.now() + timedelta(days=30)
            }
    
    def notification_days(self, notification_obj: Any) -> int:
        """
        Calculate notification days based on notification object.
        
        Args:
            notification_obj: Notification object with date information
            
        Returns:
            Number of days until notification
        """
        try:
            if not notification_obj:
                return 0
            
            # Get notification date from object
            notification_date = getattr(notification_obj, 'date', None)
            if not notification_date:
                return 0
            
            # Calculate days until notification
            now = timezone.now()
            if isinstance(notification_date, str):
                notification_date = self.date_converter(notification_date)
            
            if notification_date:
                delta = notification_date - now
                return max(0, delta.days)
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Error calculating notification days: {e}")
            return 0
    
    def countdown_in_month(self) -> Dict[str, Any]:
        """
        Calculate countdown information for the current month.
        
        Returns:
            Dict with countdown information
        """
        try:
            now = timezone.now()
            
            # Calculate days until end of month
            if now.month == 12:
                next_month = now.replace(year=now.year + 1, month=1, day=1)
            else:
                next_month = now.replace(month=now.month + 1, day=1)
            
            days_until_end = (next_month - now).days
            
            # Calculate days until next class (assuming 15th of next month)
            next_class_date = self.get_15th_of_next_month()
            days_until_class = (next_class_date - now).days
            
            return {
                'days_until_end_of_month': days_until_end,
                'days_until_next_class': days_until_class,
                'next_class_date': next_class_date,
                'current_date': now,
                'month_progress': (now.day / 30) * 100  # Approximate month progress
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating countdown: {e}")
            return {
                'days_until_end_of_month': 0,
                'days_until_next_class': 0,
                'next_class_date': timezone.now(),
                'current_date': timezone.now(),
                'month_progress': 0
            }
    
    def dates_functionality(self) -> Dict[str, Any]:
        """
        Get comprehensive date functionality information.
        
        Returns:
            Dict with various date-related information
        """
        try:
            now = timezone.now()
            
            return {
                'current_date': now,
                'formatted_date': now.strftime('%Y-%m-%d'),
                'formatted_datetime': now.strftime('%Y-%m-%d %H:%M:%S'),
                'day_of_week': now.strftime('%A'),
                'day_of_month': now.day,
                'month_name': now.strftime('%B'),
                'year': now.year,
                'quarter': (now.month - 1) // 3 + 1,
                'week_of_year': now.isocalendar()[1],
                'days_in_month': (now.replace(month=now.month % 12 + 1, day=1) - timedelta(days=1)).day,
                'is_weekend': now.weekday() >= 5,
                'is_month_end': now.day >= 28,  # Approximate
                'timezone': str(now.tzinfo) if now.tzinfo else 'UTC'
            }
            
        except Exception as e:
            self.logger.error(f"Error in dates_functionality: {e}")
            return {
                'current_date': timezone.now(),
                'formatted_date': timezone.now().strftime('%Y-%m-%d'),
                'formatted_datetime': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                'day_of_week': 'Unknown',
                'day_of_month': 1,
                'month_name': 'Unknown',
                'year': 2024,
                'quarter': 1,
                'week_of_year': 1,
                'days_in_month': 30,
                'is_weekend': False,
                'is_month_end': False,
                'timezone': 'UTC'
            }





