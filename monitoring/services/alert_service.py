"""
Alert service for sending security notifications.

Supports multiple notification channels: email, Slack, and logging.
"""

from typing import Dict, Any, List, Optional
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
import logging
import requests

logger = logging.getLogger(__name__)


class AlertService:
    """
    Service for sending security alerts via multiple channels.

    Supports email, Slack webhooks, and logging.
    """

    @classmethod
    def send_alert(
        cls,
        alert_type: str,
        severity: str,
        message: str,
        user: Optional[User] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Send security alert via configured channels.

        Args:
            alert_type: Type of alert (e.g., 'suspicious_login', 'brute_force', 'impossible_travel')
            severity: Alert severity ('low', 'medium', 'high', 'critical')
            message: Human-readable alert message
            user: User associated with the alert (optional)
            metadata: Additional alert context (optional)

        Returns:
            Dictionary with success status for each channel

        Example:
            >>> AlertService.send_alert(
            ...     alert_type='suspicious_login',
            ...     severity='high',
            ...     message='Login from new device in different country',
            ...     user=user,
            ...     metadata={'ip': '1.2.3.4', 'country': 'CN'}
            ... )
            {'email': True, 'slack': True, 'log': True}
        """
        metadata = metadata or {}
        results = {
            'email': False,
            'slack': False,
            'log': False
        }

        # Always log the alert
        log_message = f"[{severity.upper()}] {alert_type}: {message}"
        if user:
            log_message += f" | User: {user.username}"
        if metadata:
            log_message += f" | Metadata: {metadata}"

        if severity == 'critical':
            logger.critical(log_message)
        elif severity == 'high':
            logger.error(log_message)
        elif severity == 'medium':
            logger.warning(log_message)
        else:
            logger.info(log_message)

        results['log'] = True

        # Send email alerts for high/critical severity
        if severity in ['high', 'critical']:
            results['email'] = cls._send_email_alert(
                alert_type, severity, message, user, metadata
            )

        # Send Slack alerts if configured
        if hasattr(settings, 'SLACK_WEBHOOK_URL') and settings.SLACK_WEBHOOK_URL:
            results['slack'] = cls._send_slack_alert(
                alert_type, severity, message, user, metadata
            )

        return results

    @classmethod
    def _send_email_alert(
        cls,
        alert_type: str,
        severity: str,
        message: str,
        user: Optional[User],
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Send email alert to security team.

        Args:
            alert_type: Type of alert
            severity: Alert severity
            message: Alert message
            user: User associated with alert
            metadata: Additional context

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            admin_email = getattr(settings, 'SECURITY_ADMIN_EMAIL', None)
            if not admin_email:
                logger.warning("SECURITY_ADMIN_EMAIL not configured, skipping email alert")
                return False

            subject = f"[{severity.upper()}] Security Alert: {alert_type}"

            email_body = f"""
Security Alert Notification
============================

Alert Type: {alert_type}
Severity: {severity.upper()}
Timestamp: {metadata.get('timestamp', 'N/A')}

Message:
{message}

"""

            if user:
                email_body += f"""
User Information:
- Username: {user.username}
- Email: {user.email}
- User ID: {user.id}

"""

            if metadata:
                email_body += f"""
Additional Details:
"""
                for key, value in metadata.items():
                    email_body += f"- {key}: {value}\n"

            email_body += f"""

---
This is an automated security alert from Biashara Bridges.
"""

            send_mail(
                subject=subject,
                message=email_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[admin_email],
                fail_silently=False,
            )

            logger.info(f"Email alert sent successfully for {alert_type}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            return False

    @classmethod
    def _send_slack_alert(
        cls,
        alert_type: str,
        severity: str,
        message: str,
        user: Optional[User],
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Send alert to Slack channel via webhook.

        Args:
            alert_type: Type of alert
            severity: Alert severity
            message: Alert message
            user: User associated with alert
            metadata: Additional context

        Returns:
            True if Slack message sent successfully, False otherwise
        """
        try:
            webhook_url = getattr(settings, 'SLACK_WEBHOOK_URL', None)
            if not webhook_url:
                return False

            # Color coding by severity
            color_map = {
                'low': '#36a64f',      # green
                'medium': '#ff9900',   # orange
                'high': '#ff0000',     # red
                'critical': '#8b0000'  # dark red
            }

            color = color_map.get(severity, '#808080')

            # Build Slack message payload
            payload = {
                'attachments': [{
                    'color': color,
                    'title': f'🚨 Security Alert: {alert_type}',
                    'text': message,
                    'fields': [
                        {
                            'title': 'Severity',
                            'value': severity.upper(),
                            'short': True
                        }
                    ],
                    'footer': 'Biashara Bridges Security',
                    'ts': metadata.get('timestamp', None)
                }]
            }

            if user:
                payload['attachments'][0]['fields'].extend([
                    {
                        'title': 'User',
                        'value': user.username,
                        'short': True
                    },
                    {
                        'title': 'Email',
                        'value': user.email,
                        'short': True
                    }
                ])

            # Add metadata fields
            for key, value in metadata.items():
                if key != 'timestamp':
                    payload['attachments'][0]['fields'].append({
                        'title': key.replace('_', ' ').title(),
                        'value': str(value),
                        'short': True
                    })

            response = requests.post(
                webhook_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()

            logger.info(f"Slack alert sent successfully for {alert_type}")
            return True

        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
            return False

    @classmethod
    def send_brute_force_alert(cls, username: str, ip_address: str, attempts: int) -> Dict[str, bool]:
        """
        Send alert for brute force attack detection.

        Args:
            username: Username being attacked
            ip_address: Source IP address
            attempts: Number of failed attempts

        Returns:
            Dictionary with success status for each channel
        """
        return cls.send_alert(
            alert_type='brute_force_attack',
            severity='high',
            message=f"Brute force attack detected: {attempts} failed login attempts for user '{username}' from IP {ip_address}",
            metadata={
                'username': username,
                'ip_address': ip_address,
                'failed_attempts': attempts
            }
        )

    @classmethod
    def send_impossible_travel_alert(
        cls,
        user: User,
        previous_location: str,
        current_location: str,
        time_diff_hours: float
    ) -> Dict[str, bool]:
        """
        Send alert for impossible travel detection.

        Args:
            user: User who triggered alert
            previous_location: Previous login location
            current_location: Current login location
            time_diff_hours: Time between logins in hours

        Returns:
            Dictionary with success status for each channel
        """
        return cls.send_alert(
            alert_type='impossible_travel',
            severity='high',
            message=f"Impossible travel detected: User logged in from {current_location} just {time_diff_hours:.1f} hours after login from {previous_location}",
            user=user,
            metadata={
                'previous_location': previous_location,
                'current_location': current_location,
                'time_diff_hours': time_diff_hours
            }
        )

    @classmethod
    def send_new_device_alert(cls, user: User, device_info: str, ip_address: str) -> Dict[str, bool]:
        """
        Send alert for login from new device.

        Args:
            user: User who logged in
            device_info: Device information string
            ip_address: IP address of login

        Returns:
            Dictionary with success status for each channel
        """
        return cls.send_alert(
            alert_type='new_device_login',
            severity='medium',
            message=f"User {user.username} logged in from a new device",
            user=user,
            metadata={
                'device': device_info,
                'ip_address': ip_address
            }
        )
