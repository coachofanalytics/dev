"""
Views for audit log viewing and export.

Provides user-friendly interfaces for viewing audit logs with
filtering and export capabilities.
"""

from typing import Any
from django.views import View
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.db.models import Q, QuerySet
from django.utils import timezone
from datetime import timedelta
import csv
import json

from audit.models import AuditLog, LoginHistory


class AuditLogListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """
    View for listing audit logs with filtering.

    Requires 'audit.view_audit_log' permission.
    """

    model = AuditLog
    template_name = "audit/audit_log_list.html"
    context_object_name = "audit_logs"
    paginate_by = 50
    permission_required = "audit.view_audit_log"

    def get_queryset(self) -> QuerySet:
        """
        Get filtered queryset based on URL parameters.

        Returns:
            QuerySet: Filtered audit logs
        """
        queryset = AuditLog.objects.select_related("user", "content_type").all()

        # Filter by event type
        event_type = self.request.GET.get("event_type")
        if event_type:
            queryset = queryset.filter(event_type=event_type)

        # Filter by severity
        severity = self.request.GET.get("severity")
        if severity:
            queryset = queryset.filter(severity=severity)

        # Filter by user
        username = self.request.GET.get("username")
        if username:
            queryset = queryset.filter(
                Q(username__icontains=username) | Q(user__username__icontains=username)
            )

        # Filter by IP address
        ip_address = self.request.GET.get("ip_address")
        if ip_address:
            queryset = queryset.filter(ip_address__icontains=ip_address)

        # Filter by date range
        date_from = self.request.GET.get("date_from")
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)

        date_to = self.request.GET.get("date_to")
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)

        # Filter by search query
        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(
                Q(description__icontains=search)
                | Q(username__icontains=search)
                | Q(request_path__icontains=search)
            )

        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs: Any) -> dict:
        """Add filter options to context."""
        context = super().get_context_data(**kwargs)

        # Add filter choices
        context["event_types"] = AuditLog.EVENT_TYPE_CHOICES
        context["severities"] = AuditLog.SEVERITY_CHOICES

        # Add current filters
        context["current_filters"] = {
            "event_type": self.request.GET.get("event_type", ""),
            "severity": self.request.GET.get("severity", ""),
            "username": self.request.GET.get("username", ""),
            "ip_address": self.request.GET.get("ip_address", ""),
            "date_from": self.request.GET.get("date_from", ""),
            "date_to": self.request.GET.get("date_to", ""),
            "search": self.request.GET.get("search", ""),
        }

        return context


class AuditLogDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """
    View for displaying audit log details.

    Requires 'audit.view_audit_log' permission.
    """

    model = AuditLog
    template_name = "audit/audit_log_detail.html"
    context_object_name = "audit_log"
    permission_required = "audit.view_audit_log"


class LoginHistoryListView(LoginRequiredMixin, ListView):
    """
    View for listing user's own login history.

    Shows current user's login history without requiring special permissions.
    """

    model = LoginHistory
    template_name = "audit/login_history_list.html"
    context_object_name = "login_history"
    paginate_by = 50

    def get_queryset(self) -> QuerySet:
        """Get current user's login history."""
        return (
            LoginHistory.objects.filter(user=self.request.user)
            .order_by("-attempted_at")
        )

    def get_context_data(self, **kwargs: Any) -> dict:
        """Add statistics to context."""
        context = super().get_context_data(**kwargs)

        # Calculate statistics
        queryset = self.get_queryset()

        # Last 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_logins = queryset.filter(attempted_at__gte=thirty_days_ago)

        context["stats"] = {
            "total_logins": queryset.count(),
            "successful_logins": queryset.filter(status="success").count(),
            "failed_logins": queryset.filter(status="failed").count(),
            "recent_logins": recent_logins.count(),
            "unique_ips": queryset.values("ip_address").distinct().count(),
            "unique_devices": queryset.values("device_fingerprint")
            .distinct()
            .count(),
        }

        return context


class AuditLogExportView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    View for exporting audit logs to CSV.

    Requires 'audit.export_audit_log' permission.
    """

    permission_required = "audit.export_audit_log"

    def get(self, request: Any) -> HttpResponse:
        """
        Export audit logs to CSV.

        Args:
            request: HTTP request

        Returns:
            HttpResponse: CSV file download
        """
        # Get filtered queryset using same logic as list view
        queryset = AuditLog.objects.select_related("user", "content_type").all()

        # Apply same filters as list view
        event_type = request.GET.get("event_type")
        if event_type:
            queryset = queryset.filter(event_type=event_type)

        severity = request.GET.get("severity")
        if severity:
            queryset = queryset.filter(severity=severity)

        username = request.GET.get("username")
        if username:
            queryset = queryset.filter(
                Q(username__icontains=username) | Q(user__username__icontains=username)
            )

        date_from = request.GET.get("date_from")
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)

        date_to = request.GET.get("date_to")
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)

        queryset = queryset.order_by("-created_at")

        # Create CSV response
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            f'attachment; filename="audit_logs_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        )

        writer = csv.writer(response)

        # Write header
        writer.writerow(
            [
                "Timestamp",
                "Event Type",
                "Severity",
                "User",
                "Description",
                "IP Address",
                "Request Method",
                "Request Path",
                "User Agent",
            ]
        )

        # Write data
        for log in queryset[:10000]:  # Limit to 10,000 records
            writer.writerow(
                [
                    log.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    log.get_event_type_display(),
                    log.severity,
                    log.username,
                    log.description,
                    log.ip_address or "",
                    log.request_method or "",
                    log.request_path or "",
                    log.user_agent[:100] if log.user_agent else "",
                ]
            )

        return response


class AuditLogStatsView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    View for audit log statistics API.

    Returns JSON statistics for dashboards and charts.
    Requires 'audit.view_audit_log' permission.
    """

    permission_required = "audit.view_audit_log"

    def get(self, request: Any) -> JsonResponse:
        """
        Get audit log statistics.

        Args:
            request: HTTP request

        Returns:
            JsonResponse: Statistics data
        """
        # Get date range
        days = int(request.GET.get("days", 30))
        start_date = timezone.now() - timedelta(days=days)

        # Get recent logs
        logs = AuditLog.objects.filter(created_at__gte=start_date)

        # Calculate statistics
        stats = {
            "total_events": logs.count(),
            "by_event_type": {},
            "by_severity": {},
            "by_day": {},
            "top_users": [],
            "top_ips": [],
        }

        # Events by type
        for event_type, label in AuditLog.EVENT_TYPE_CHOICES:
            count = logs.filter(event_type=event_type).count()
            if count > 0:
                stats["by_event_type"][label] = count

        # Events by severity
        for severity, label in AuditLog.SEVERITY_CHOICES:
            count = logs.filter(severity=severity).count()
            stats["by_severity"][label] = count

        # Events by day (last 7 days)
        for i in range(7):
            day = timezone.now() - timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            count = logs.filter(
                created_at__gte=day_start, created_at__lt=day_end
            ).count()
            stats["by_day"][day.strftime("%Y-%m-%d")] = count

        # Top 10 users
        from django.db.models import Count

        top_users = (
            logs.exclude(username="")
            .values("username")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )
        stats["top_users"] = list(top_users)

        # Top 10 IP addresses
        top_ips = (
            logs.exclude(ip_address__isnull=True)
            .values("ip_address")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )
        stats["top_ips"] = list(top_ips)

        return JsonResponse(stats)
