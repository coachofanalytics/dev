"""
Audit logging service.

Provides a clean API for creating audit logs throughout the application.
All audit logs are immutable and retained for 7 years for compliance.
"""

from typing import Optional, Dict, Any, Union
from django.contrib.auth.models import User
from django.http import HttpRequest
from django.contrib.contenttypes.models import ContentType
from django.db.models import Model

from audit.models import AuditLog, LoginHistory


class AuditService:
    """Service for creating and managing audit logs."""

    # 7 years retention in days (accounting for leap years)
    RETENTION_DAYS = 2555

    @staticmethod
    def log_event(
        event_type: str,
        description: str,
        user: Optional[User] = None,
        username: Optional[str] = None,
        request: Optional[HttpRequest] = None,
        ip_address: Optional[str] = None,
        severity: str = "info",
        related_object: Optional[Model] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """
        Create an audit log entry.

        Args:
            event_type: Type of event (must match EVENT_TYPE_CHOICES)
            description: Human-readable description
            user: User who triggered the event
            username: Username (if user not available)
            request: HTTP request object (for extracting IP, user agent, etc.)
            ip_address: IP address (if request not available)
            severity: Event severity (info, warning, error, critical)
            related_object: Django model instance related to this event
            metadata: Additional context data

        Returns:
            AuditLog: Created audit log instance

        Example:
            >>> from audit.services import AuditService
            >>> AuditService.log_event(
            ...     event_type="login_success",
            ...     description="User logged in successfully",
            ...     user=request.user,
            ...     request=request,
            ... )
        """
        # Extract request metadata if request provided
        request_data = {}
        if request:
            request_data = {
                "ip_address": AuditService._get_client_ip(request),
                "user_agent": request.META.get("HTTP_USER_AGENT", ""),
                "request_method": request.method,
                "request_path": request.path,
            }

        # Determine username
        if not username and user:
            username = user.username

        # Get content type and object ID for related object
        content_type = None
        object_id = None
        if related_object:
            content_type = ContentType.objects.get_for_model(related_object)
            object_id = related_object.pk

        # Create audit log
        audit_log = AuditLog.objects.create(
            event_type=event_type,
            severity=severity,
            description=description,
            user=user,
            username=username or "",
            content_type=content_type,
            object_id=object_id,
            ip_address=ip_address or request_data.get("ip_address"),
            user_agent=request_data.get("user_agent", ""),
            request_method=request_data.get("request_method", ""),
            request_path=request_data.get("request_path", ""),
            metadata=metadata or {},
        )

        return audit_log

    @staticmethod
    def log_login_attempt(
        username: str,
        status: str,
        request: HttpRequest,
        user: Optional[User] = None,
        failure_reason: Optional[str] = None,
        risk_score: int = 0,
        device_fingerprint: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> LoginHistory:
        """
        Log a login attempt with device fingerprinting.

        Args:
            username: Username attempting to login
            status: Login status (success, failed, blocked)
            request: HTTP request object
            user: User instance (if login successful)
            failure_reason: Reason for failure (if applicable)
            risk_score: Risk score 0-100
            device_fingerprint: Unique device identifier
            metadata: Additional context data

        Returns:
            LoginHistory: Created login history instance

        Example:
            >>> from audit.services import AuditService
            >>> AuditService.log_login_attempt(
            ...     username="john_doe",
            ...     status="success",
            ...     request=request,
            ...     user=user,
            ... )
        """
        # Parse user agent
        user_agent_data = AuditService._parse_user_agent(
            request.META.get("HTTP_USER_AGENT", "")
        )

        # Create login history
        login_history = LoginHistory.objects.create(
            user=user,
            username=username,
            status=status,
            failure_reason=failure_reason,
            ip_address=AuditService._get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            device_fingerprint=device_fingerprint,
            device_type=user_agent_data.get("device_type", ""),
            browser=user_agent_data.get("browser", ""),
            os=user_agent_data.get("os", ""),
            session_key=request.session.session_key or "",
            risk_score=risk_score,
            metadata=metadata or {},
        )

        # Also create a corresponding audit log
        event_type = f"login_{status}"
        severity = "warning" if status != "success" else "info"

        AuditService.log_event(
            event_type=event_type,
            description=f"Login attempt: {status}",
            user=user,
            username=username,
            request=request,
            severity=severity,
            metadata={
                "login_history_id": str(login_history.id),
                "failure_reason": failure_reason,
                "risk_score": risk_score,
            },
        )

        return login_history

    @staticmethod
    def log_user_action(
        action: str,
        description: str,
        user: User,
        request: Optional[HttpRequest] = None,
        target_user: Optional[User] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """
        Log a user action with old/new value tracking.

        Args:
            action: Action type (user_created, user_updated, etc.)
            description: Description of the action
            user: User performing the action
            request: HTTP request object
            target_user: User being acted upon (if different from user)
            old_values: Previous values before change
            new_values: New values after change

        Returns:
            AuditLog: Created audit log instance

        Example:
            >>> AuditService.log_user_action(
            ...     action="user_updated",
            ...     description="Updated user profile",
            ...     user=request.user,
            ...     request=request,
            ...     old_values={"email": "old@example.com"},
            ...     new_values={"email": "new@example.com"},
            ... )
        """
        metadata = {}
        if old_values:
            metadata["old_values"] = old_values
        if new_values:
            metadata["new_values"] = new_values
        if target_user:
            metadata["target_user_id"] = target_user.id
            metadata["target_username"] = target_user.username

        return AuditService.log_event(
            event_type=action,
            description=description,
            user=user,
            request=request,
            related_object=target_user or user,
            metadata=metadata,
        )

    @staticmethod
    def log_payment_event(
        event_type: str,
        description: str,
        user: User,
        transaction: Optional[Model] = None,
        amount: Optional[float] = None,
        currency: str = "USD",
        payment_method: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """
        Log a payment-related event.

        Args:
            event_type: Type of payment event
            description: Description of the event
            user: User involved in payment
            transaction: Transaction model instance
            amount: Payment amount
            currency: Currency code
            payment_method: Payment method used
            metadata: Additional context

        Returns:
            AuditLog: Created audit log instance
        """
        payment_metadata = metadata or {}
        if amount:
            payment_metadata["amount"] = amount
        if currency:
            payment_metadata["currency"] = currency
        if payment_method:
            payment_metadata["payment_method"] = payment_method
        if transaction:
            payment_metadata["transaction_id"] = str(transaction.pk)

        return AuditService.log_event(
            event_type=event_type,
            description=description,
            user=user,
            related_object=transaction,
            severity="info" if "completed" in event_type else "warning",
            metadata=payment_metadata,
        )

    @staticmethod
    def _get_client_ip(request: HttpRequest) -> str:
        """
        Get client IP address from request.

        Handles proxies and load balancers correctly.

        Args:
            request: HTTP request object

        Returns:
            str: Client IP address
        """
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR", "")
        return ip

    @staticmethod
    def _parse_user_agent(user_agent: str) -> Dict[str, str]:
        """
        Parse user agent string to extract device info.

        Args:
            user_agent: User agent string

        Returns:
            Dict containing device_type, browser, and os
        """
        # Basic user agent parsing (in production, use user-agents library)
        ua_lower = user_agent.lower()

        # Determine device type
        if "mobile" in ua_lower or "android" in ua_lower or "iphone" in ua_lower:
            device_type = "mobile"
        elif "tablet" in ua_lower or "ipad" in ua_lower:
            device_type = "tablet"
        else:
            device_type = "desktop"

        # Determine browser
        if "chrome" in ua_lower:
            browser = "Chrome"
        elif "firefox" in ua_lower:
            browser = "Firefox"
        elif "safari" in ua_lower:
            browser = "Safari"
        elif "edge" in ua_lower or "edg" in ua_lower:
            browser = "Edge"
        else:
            browser = "Unknown"

        # Determine OS
        if "windows" in ua_lower:
            os = "Windows"
        elif "mac" in ua_lower or "macos" in ua_lower:
            os = "macOS"
        elif "linux" in ua_lower:
            os = "Linux"
        elif "android" in ua_lower:
            os = "Android"
        elif "ios" in ua_lower or "iphone" in ua_lower or "ipad" in ua_lower:
            os = "iOS"
        else:
            os = "Unknown"

        return {
            "device_type": device_type,
            "browser": browser,
            "os": os,
        }
