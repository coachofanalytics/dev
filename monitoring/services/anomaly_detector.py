"""
Anomaly detection service for security monitoring.

Detects suspicious patterns like impossible travel, new devices, and unusual behavior.
"""

from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.utils import timezone
from audit.models import LoginHistory
from monitoring.services.alert_service import AlertService
import logging

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """
    Service for detecting anomalous security events.

    Analyzes login patterns, device usage, and geographic locations
    to identify potential security threats.
    """

    # Impossible travel threshold: 800 km/h (faster than commercial aircraft)
    MAX_TRAVEL_SPEED_KMH = 800

    @classmethod
    def check_login_anomalies(
        cls,
        user: User,
        ip_address: str,
        user_agent: str,
        location_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Check for anomalies in login attempt.

        Args:
            user: User attempting to log in
            ip_address: IP address of login attempt
            user_agent: User agent string
            location_data: Geographic location data (optional)

        Returns:
            Dictionary with anomaly detection results and risk score

        Example:
            >>> result = AnomalyDetector.check_login_anomalies(
            ...     user=user,
            ...     ip_address='1.2.3.4',
            ...     user_agent='Mozilla/5.0...',
            ...     location_data={'country': 'CN', 'city': 'Beijing'}
            ... )
            >>> result['risk_score']  # 0-100
            75
            >>> result['anomalies']
            ['impossible_travel', 'new_device']
        """
        anomalies = []
        risk_score = 0
        alerts_sent = []

        # Check for impossible travel
        if location_data:
            impossible_travel = cls._check_impossible_travel(user, location_data)
            if impossible_travel:
                anomalies.append('impossible_travel')
                risk_score += 40
                alert_result = AlertService.send_impossible_travel_alert(
                    user=user,
                    previous_location=impossible_travel['previous_location'],
                    current_location=impossible_travel['current_location'],
                    time_diff_hours=impossible_travel['time_diff_hours']
                )
                alerts_sent.append({
                    'type': 'impossible_travel',
                    'sent': alert_result
                })

        # Check for new device
        is_new_device = cls._check_new_device(user, user_agent)
        if is_new_device:
            anomalies.append('new_device')
            risk_score += 20
            alert_result = AlertService.send_new_device_alert(
                user=user,
                device_info=user_agent[:100],  # Truncate for readability
                ip_address=ip_address
            )
            alerts_sent.append({
                'type': 'new_device',
                'sent': alert_result
            })

        # Check for new IP address
        is_new_ip = cls._check_new_ip(user, ip_address)
        if is_new_ip:
            anomalies.append('new_ip_address')
            risk_score += 15

        # Check for unusual login time
        unusual_time = cls._check_unusual_login_time(user)
        if unusual_time:
            anomalies.append('unusual_login_time')
            risk_score += 10

        # Check for rapid login attempts (velocity check)
        high_velocity = cls._check_login_velocity(user)
        if high_velocity:
            anomalies.append('high_velocity')
            risk_score += 25

        return {
            'risk_score': min(risk_score, 100),  # Cap at 100
            'anomalies': anomalies,
            'requires_mfa': risk_score >= 50,  # Require MFA if risk >= 50
            'alerts_sent': alerts_sent
        }

    @classmethod
    def _check_impossible_travel(
        cls,
        user: User,
        current_location: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Check if user traveled impossibly fast between logins.

        Args:
            user: User to check
            current_location: Current login location data

        Returns:
            Dictionary with travel details if impossible travel detected, None otherwise
        """
        try:
            # Get last successful login
            last_login = LoginHistory.objects.filter(
                user=user,
                successful=True
            ).order_by('-login_time').first()

            if not last_login or not last_login.metadata:
                return None

            previous_location = last_login.metadata.get('location', {})
            if not previous_location:
                return None

            # Calculate time difference
            time_diff = timezone.now() - last_login.login_time
            time_diff_hours = time_diff.total_seconds() / 3600

            # Skip check if too much time has passed (more than 24 hours)
            if time_diff_hours > 24:
                return None

            # Simple distance calculation (would use geopy in production)
            # For now, just check if countries are different
            prev_country = previous_location.get('country_code', '')
            curr_country = current_location.get('country_code', '')

            if prev_country and curr_country and prev_country != curr_country:
                # Different countries within a short time frame
                if time_diff_hours < 2:  # Less than 2 hours
                    return {
                        'previous_location': f"{previous_location.get('city', 'Unknown')}, {prev_country}",
                        'current_location': f"{current_location.get('city', 'Unknown')}, {curr_country}",
                        'time_diff_hours': time_diff_hours
                    }

            return None

        except Exception as e:
            logger.error(f"Error checking impossible travel: {e}")
            return None

    @classmethod
    def _check_new_device(cls, user: User, user_agent: str) -> bool:
        """
        Check if this is a new device for the user.

        Args:
            user: User to check
            user_agent: User agent string

        Returns:
            True if this is a new device, False otherwise
        """
        try:
            # Check if this user agent has been seen before
            previous_login = LoginHistory.objects.filter(
                user=user,
                user_agent=user_agent,
                successful=True
            ).exists()

            return not previous_login

        except Exception as e:
            logger.error(f"Error checking new device: {e}")
            return False

    @classmethod
    def _check_new_ip(cls, user: User, ip_address: str) -> bool:
        """
        Check if this is a new IP address for the user.

        Args:
            user: User to check
            ip_address: IP address to check

        Returns:
            True if this is a new IP, False otherwise
        """
        try:
            previous_login = LoginHistory.objects.filter(
                user=user,
                ip_address=ip_address,
                successful=True
            ).exists()

            return not previous_login

        except Exception as e:
            logger.error(f"Error checking new IP: {e}")
            return False

    @classmethod
    def _check_unusual_login_time(cls, user: User) -> bool:
        """
        Check if login time is unusual for this user.

        Args:
            user: User to check

        Returns:
            True if login time is unusual, False otherwise
        """
        try:
            current_hour = timezone.now().hour

            # Get user's typical login hours (most common hours from history)
            recent_logins = LoginHistory.objects.filter(
                user=user,
                successful=True,
                login_time__gte=timezone.now() - timedelta(days=30)
            ).values_list('login_time', flat=True)

            if not recent_logins or len(recent_logins) < 5:
                # Not enough history
                return False

            # Calculate most common login hours
            login_hours = [login.hour for login in recent_logins]
            common_hours = set(login_hours)

            # If current hour is not in user's common hours and it's very late/early
            if current_hour not in common_hours and (current_hour < 6 or current_hour > 23):
                return True

            return False

        except Exception as e:
            logger.error(f"Error checking unusual login time: {e}")
            return False

    @classmethod
    def _check_login_velocity(cls, user: User) -> bool:
        """
        Check if there are too many login attempts in short time (velocity check).

        Args:
            user: User to check

        Returns:
            True if high velocity detected, False otherwise
        """
        try:
            # Check for more than 10 login attempts in last 5 minutes
            recent_cutoff = timezone.now() - timedelta(minutes=5)
            recent_attempts = LoginHistory.objects.filter(
                user=user,
                login_time__gte=recent_cutoff
            ).count()

            return recent_attempts > 10

        except Exception as e:
            logger.error(f"Error checking login velocity: {e}")
            return False

    @classmethod
    def calculate_risk_score(
        cls,
        failed_attempts: int,
        is_new_device: bool,
        is_new_ip: bool,
        suspicious_location: bool
    ) -> int:
        """
        Calculate risk score based on multiple factors.

        Args:
            failed_attempts: Number of recent failed login attempts
            is_new_device: Whether this is a new device
            is_new_ip: Whether this is a new IP address
            suspicious_location: Whether location seems suspicious

        Returns:
            Risk score from 0-100

        Example:
            >>> AnomalyDetector.calculate_risk_score(
            ...     failed_attempts=3,
            ...     is_new_device=True,
            ...     is_new_ip=True,
            ...     suspicious_location=False
            ... )
            55
        """
        score = 0

        # Failed attempts (0-40 points)
        score += min(failed_attempts * 10, 40)

        # New device (20 points)
        if is_new_device:
            score += 20

        # New IP (15 points)
        if is_new_ip:
            score += 15

        # Suspicious location (25 points)
        if suspicious_location:
            score += 25

        return min(score, 100)
