"""
Audit middleware for automatic request/response logging.

This middleware automatically logs significant HTTP requests and responses
for security auditing and compliance purposes.
"""

from typing import Callable, Optional
import time
import logging

from django.http import HttpRequest, HttpResponse
from django.contrib.auth.models import User
from django.utils.deprecation import MiddlewareMixin

from audit.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class AuditMiddleware(MiddlewareMixin):
    """
    Middleware for automatic audit logging of HTTP requests.

    Logs significant requests including:
    - Admin actions
    - API requests
    - Data modifications
    - Sensitive operations
    """

    # Paths to always log (admin, API, sensitive operations)
    ALWAYS_LOG_PATHS = [
        "/admin/",
        "/api/",
        "/accounts/password/",
        "/accounts/delete/",
        "/payments/",
        "/gdpr/",
    ]

    # HTTP methods that modify data
    MODIFICATION_METHODS = ["POST", "PUT", "PATCH", "DELETE"]

    # Paths to exclude from logging (static files, health checks, etc.)
    EXCLUDE_PATHS = [
        "/static/",
        "/media/",
        "/health/",
        "/favicon.ico",
        "/__debug__/",
    ]

    def process_request(self, request: HttpRequest) -> None:
        """
        Process request before view is called.

        Captures request start time for performance tracking.

        Args:
            request: HTTP request object
        """
        # Store request start time for performance tracking
        request._audit_start_time = time.time()

    def process_response(
        self, request: HttpRequest, response: HttpResponse
    ) -> HttpResponse:
        """
        Process response after view is called.

        Logs significant requests based on path, method, and user actions.

        Args:
            request: HTTP request object
            response: HTTP response object

        Returns:
            HttpResponse: The response object (unchanged)
        """
        # Skip excluded paths
        if self._should_exclude(request):
            return response

        # Skip successful GET requests to non-sensitive paths
        if (
            request.method == "GET"
            and not self._is_sensitive_path(request)
            and response.status_code < 400
        ):
            return response

        # Log the request
        try:
            self._log_request(request, response)
        except Exception as e:
            # Don't let logging errors break the application
            logger.error(f"Error logging request: {e}", exc_info=True)

        return response

    def _should_exclude(self, request: HttpRequest) -> bool:
        """
        Check if request should be excluded from logging.

        Args:
            request: HTTP request object

        Returns:
            bool: True if request should be excluded
        """
        path = request.path
        return any(path.startswith(excluded) for excluded in self.EXCLUDE_PATHS)

    def _is_sensitive_path(self, request: HttpRequest) -> bool:
        """
        Check if request path is sensitive and should always be logged.

        Args:
            request: HTTP request object

        Returns:
            bool: True if path is sensitive
        """
        path = request.path
        return any(path.startswith(sensitive) for sensitive in self.ALWAYS_LOG_PATHS)

    def _should_log(self, request: HttpRequest, response: HttpResponse) -> bool:
        """
        Determine if request should be logged.

        Args:
            request: HTTP request object
            response: HTTP response object

        Returns:
            bool: True if request should be logged
        """
        # Always log sensitive paths
        if self._is_sensitive_path(request):
            return True

        # Always log modification requests
        if request.method in self.MODIFICATION_METHODS:
            return True

        # Always log errors (4xx, 5xx)
        if response.status_code >= 400:
            return True

        # Don't log other GET requests
        return False

    def _log_request(self, request: HttpRequest, response: HttpResponse) -> None:
        """
        Log the HTTP request.

        Args:
            request: HTTP request object
            response: HTTP response object
        """
        if not self._should_log(request, response):
            return

        # Calculate request duration
        duration = None
        if hasattr(request, "_audit_start_time"):
            duration = time.time() - request._audit_start_time

        # Determine event type and severity
        event_type, severity = self._get_event_type_and_severity(request, response)

        # Build description
        description = self._build_description(request, response, duration)

        # Build metadata
        metadata = self._build_metadata(request, response, duration)

        # Get user
        user = request.user if request.user.is_authenticated else None

        # Log the event
        try:
            AuditService.log_event(
                event_type=event_type,
                description=description,
                user=user,
                request=request,
                severity=severity,
                metadata=metadata,
            )
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}", exc_info=True)

    def _get_event_type_and_severity(
        self, request: HttpRequest, response: HttpResponse
    ) -> tuple[str, str]:
        """
        Determine event type and severity based on request/response.

        Args:
            request: HTTP request object
            response: HTTP response object

        Returns:
            tuple: (event_type, severity)
        """
        # Admin actions
        if request.path.startswith("/admin/"):
            return ("admin_action", "info")

        # API access
        if request.path.startswith("/api/"):
            severity = "warning" if response.status_code >= 400 else "info"
            return ("api_access", severity)

        # Payment operations
        if request.path.startswith("/payments/"):
            if response.status_code >= 400:
                return ("payment_failed", "error")
            return ("payment_initiated", "info")

        # Profile updates
        if "/profile/" in request.path and request.method in self.MODIFICATION_METHODS:
            return ("profile_updated", "info")

        # User management
        if "/accounts/" in request.path:
            if "/password/" in request.path:
                return ("password_changed", "info")
            if "/delete/" in request.path:
                return ("user_deleted", "warning")
            return ("user_updated", "info")

        # Errors
        if response.status_code >= 500:
            return ("system_error", "critical")
        elif response.status_code >= 400:
            return ("suspicious_activity", "warning")

        # Default
        return ("admin_action", "info")

    def _build_description(
        self, request: HttpRequest, response: HttpResponse, duration: Optional[float]
    ) -> str:
        """
        Build human-readable description of the request.

        Args:
            request: HTTP request object
            response: HTTP response object
            duration: Request duration in seconds

        Returns:
            str: Description string
        """
        user_str = (
            request.user.username if request.user.is_authenticated else "Anonymous"
        )

        desc = f"{user_str} - {request.method} {request.path}"

        # Add status code
        desc += f" [{response.status_code}]"

        # Add duration if available
        if duration is not None:
            desc += f" ({duration:.2f}s)"

        return desc

    def _build_metadata(
        self, request: HttpRequest, response: HttpResponse, duration: Optional[float]
    ) -> dict:
        """
        Build metadata dictionary with request details.

        Args:
            request: HTTP request object
            response: HTTP response object
            duration: Request duration in seconds

        Returns:
            dict: Metadata dictionary
        """
        metadata = {
            "method": request.method,
            "path": request.path,
            "status_code": response.status_code,
            "content_type": response.get("Content-Type", ""),
        }

        if duration is not None:
            metadata["duration_seconds"] = round(duration, 3)

        # Add query parameters (excluding sensitive ones)
        if request.GET:
            safe_params = {
                k: v
                for k, v in request.GET.items()
                if k.lower() not in ["password", "token", "secret", "key"]
            }
            if safe_params:
                metadata["query_params"] = safe_params

        # Add referer
        if request.META.get("HTTP_REFERER"):
            metadata["referer"] = request.META["HTTP_REFERER"]

        # Add request ID if available
        if hasattr(request, "id"):
            metadata["request_id"] = str(request.id)

        return metadata
