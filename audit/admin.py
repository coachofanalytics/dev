"""
Read-only admin interface for audit logs.

Audit logs are immutable and can only be viewed, not modified or deleted.
This admin interface enforces read-only access while providing comprehensive
filtering and search capabilities.
"""

from typing import Any, Optional
from django.contrib import admin
from django.http import HttpRequest
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
import json

from audit.models import AuditLog, LoginHistory


class ReadOnlyAdminMixin:
    """
    Mixin to make admin interface read-only.

    Prevents add, change, and delete operations on audit logs.
    """

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Prevent adding new records."""
        return False

    def has_change_permission(
        self, request: HttpRequest, obj: Any = None
    ) -> bool:
        """Allow viewing but not changing."""
        return False

    def has_delete_permission(
        self, request: HttpRequest, obj: Any = None
    ) -> bool:
        """Prevent deleting records."""
        return False


@admin.register(AuditLog)
class AuditLogAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    """
    Admin interface for audit logs.

    Read-only interface with comprehensive filtering and search.
    """

    list_display = [
        "created_at",
        "event_type_badge",
        "severity_badge",
        "username_link",
        "description_short",
        "ip_address",
        "view_details",
    ]

    list_filter = [
        "event_type",
        "severity",
        "created_at",
        ("user", admin.RelatedOnlyFieldListFilter),
    ]

    search_fields = [
        "username",
        "description",
        "ip_address",
        "user__username",
        "user__email",
    ]

    readonly_fields = [
        "id",
        "event_type",
        "severity_badge",
        "description",
        "user_link",
        "username",
        "content_type",
        "object_id",
        "content_object_link",
        "ip_address",
        "user_agent",
        "request_method",
        "request_path",
        "metadata_formatted",
        "created_at",
    ]

    fieldsets = [
        (
            "Event Information",
            {
                "fields": [
                    "id",
                    "event_type",
                    "severity_badge",
                    "description",
                    "created_at",
                ]
            },
        ),
        (
            "User Information",
            {
                "fields": [
                    "user_link",
                    "username",
                ]
            },
        ),
        (
            "Related Object",
            {
                "fields": [
                    "content_type",
                    "object_id",
                    "content_object_link",
                ],
                "classes": ["collapse"],
            },
        ),
        (
            "Request Details",
            {
                "fields": [
                    "ip_address",
                    "user_agent",
                    "request_method",
                    "request_path",
                ],
                "classes": ["collapse"],
            },
        ),
        (
            "Additional Data",
            {
                "fields": ["metadata_formatted"],
                "classes": ["collapse"],
            },
        ),
    ]

    date_hierarchy = "created_at"

    def event_type_badge(self, obj: AuditLog) -> str:
        """Display event type as a colored badge."""
        colors = {
            "login_success": "#28a745",
            "login_failed": "#dc3545",
            "logout": "#6c757d",
            "password_changed": "#ffc107",
            "payment_completed": "#28a745",
            "payment_failed": "#dc3545",
            "user_created": "#17a2b8",
            "user_deleted": "#dc3545",
        }
        color = colors.get(obj.event_type, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_event_type_display(),
        )

    event_type_badge.short_description = "Event Type"

    def severity_badge(self, obj: AuditLog) -> str:
        """Display severity as a colored badge."""
        colors = {
            "info": "#17a2b8",
            "warning": "#ffc107",
            "error": "#dc3545",
            "critical": "#721c24",
        }
        color = colors.get(obj.severity, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.severity.upper(),
        )

    severity_badge.short_description = "Severity"

    def username_link(self, obj: AuditLog) -> str:
        """Display username with link to user admin."""
        if obj.user:
            url = reverse("admin:auth_user_change", args=[obj.user.pk])
            return format_html('<a href="{}">{}</a>', url, obj.username)
        return obj.username or "Anonymous"

    username_link.short_description = "User"

    def user_link(self, obj: AuditLog) -> str:
        """Display user with link to user admin."""
        if obj.user:
            url = reverse("admin:auth_user_change", args=[obj.user.pk])
            return format_html(
                '<a href="{}">{} ({})</a>',
                url,
                obj.user.username,
                obj.user.email,
            )
        return obj.username or "Anonymous"

    user_link.short_description = "User"

    def content_object_link(self, obj: AuditLog) -> str:
        """Display link to related content object if available."""
        if obj.content_object and obj.content_type:
            try:
                app_label = obj.content_type.app_label
                model_name = obj.content_type.model
                url = reverse(
                    f"admin:{app_label}_{model_name}_change",
                    args=[obj.object_id],
                )
                return format_html(
                    '<a href="{}">{}</a>',
                    url,
                    str(obj.content_object),
                )
            except Exception:
                return str(obj.content_object)
        return "-"

    content_object_link.short_description = "Related Object"

    def description_short(self, obj: AuditLog) -> str:
        """Display truncated description."""
        if len(obj.description) > 100:
            return obj.description[:100] + "..."
        return obj.description

    description_short.short_description = "Description"

    def metadata_formatted(self, obj: AuditLog) -> str:
        """Display metadata as formatted JSON."""
        if obj.metadata:
            formatted = json.dumps(obj.metadata, indent=2, sort_keys=True)
            return format_html("<pre>{}</pre>", formatted)
        return "-"

    metadata_formatted.short_description = "Metadata"

    def view_details(self, obj: AuditLog) -> str:
        """Display view details button."""
        url = reverse("admin:audit_auditlog_change", args=[obj.pk])
        return format_html(
            '<a class="button" href="{}">View Details</a>',
            url,
        )

    view_details.short_description = "Actions"


@admin.register(LoginHistory)
class LoginHistoryAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    """
    Admin interface for login history.

    Read-only interface for viewing login attempts with device information.
    """

    list_display = [
        "attempted_at",
        "status_badge",
        "username_link",
        "ip_address",
        "location",
        "device_info",
        "risk_score_badge",
    ]

    list_filter = [
        "status",
        "failure_reason",
        "attempted_at",
        "device_type",
        "country",
        ("user", admin.RelatedOnlyFieldListFilter),
    ]

    search_fields = [
        "username",
        "ip_address",
        "user__username",
        "user__email",
        "browser",
        "os",
        "country",
        "city",
    ]

    readonly_fields = [
        "id",
        "user_link",
        "username",
        "status_badge",
        "failure_reason",
        "ip_address",
        "user_agent",
        "device_fingerprint",
        "device_type",
        "browser",
        "os",
        "country",
        "city",
        "latitude",
        "longitude",
        "session_key",
        "risk_score_badge",
        "metadata_formatted",
        "attempted_at",
    ]

    fieldsets = [
        (
            "Login Attempt",
            {
                "fields": [
                    "id",
                    "attempted_at",
                    "status_badge",
                    "failure_reason",
                    "risk_score_badge",
                ]
            },
        ),
        (
            "User Information",
            {
                "fields": [
                    "user_link",
                    "username",
                ]
            },
        ),
        (
            "Device Information",
            {
                "fields": [
                    "device_fingerprint",
                    "device_type",
                    "browser",
                    "os",
                    "user_agent",
                ]
            },
        ),
        (
            "Location",
            {
                "fields": [
                    "ip_address",
                    "country",
                    "city",
                    "latitude",
                    "longitude",
                ],
                "classes": ["collapse"],
            },
        ),
        (
            "Session",
            {
                "fields": ["session_key"],
                "classes": ["collapse"],
            },
        ),
        (
            "Additional Data",
            {
                "fields": ["metadata_formatted"],
                "classes": ["collapse"],
            },
        ),
    ]

    date_hierarchy = "attempted_at"

    def status_badge(self, obj: LoginHistory) -> str:
        """Display login status as colored badge."""
        colors = {
            "success": "#28a745",
            "failed": "#dc3545",
            "blocked": "#6c757d",
        }
        color = colors.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = "Status"

    def username_link(self, obj: LoginHistory) -> str:
        """Display username with link to user admin."""
        if obj.user:
            url = reverse("admin:auth_user_change", args=[obj.user.pk])
            return format_html('<a href="{}">{}</a>', url, obj.username)
        return obj.username

    username_link.short_description = "User"

    def user_link(self, obj: LoginHistory) -> str:
        """Display user with link to user admin."""
        if obj.user:
            url = reverse("admin:auth_user_change", args=[obj.user.pk])
            return format_html(
                '<a href="{}">{} ({})</a>',
                url,
                obj.user.username,
                obj.user.email,
            )
        return obj.username

    user_link.short_description = "User"

    def device_info(self, obj: LoginHistory) -> str:
        """Display device information summary."""
        info = []
        if obj.device_type:
            info.append(obj.device_type.title())
        if obj.browser:
            info.append(obj.browser)
        if obj.os:
            info.append(obj.os)
        return " / ".join(info) if info else "-"

    device_info.short_description = "Device"

    def risk_score_badge(self, obj: LoginHistory) -> str:
        """Display risk score as colored badge."""
        score = obj.risk_score

        if score >= 70:
            color = "#dc3545"  # Red - high risk
        elif score >= 40:
            color = "#ffc107"  # Yellow - medium risk
        else:
            color = "#28a745"  # Green - low risk

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            f"Risk: {score}",
        )

    risk_score_badge.short_description = "Risk Score"

    def metadata_formatted(self, obj: LoginHistory) -> str:
        """Display metadata as formatted JSON."""
        if obj.metadata:
            formatted = json.dumps(obj.metadata, indent=2, sort_keys=True)
            return format_html("<pre>{}</pre>", formatted)
        return "-"

    metadata_formatted.short_description = "Metadata"
