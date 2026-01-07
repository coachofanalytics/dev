"""
Django admin configuration for GDPR models.
"""

from django.contrib import admin
from django.utils.html import format_html

from gdpr.models import (
    ConsentRecord,
    DataExportRequest,
    DataDeletionRequest,
    PrivacyPolicyVersion,
)


@admin.register(ConsentRecord)
class ConsentRecordAdmin(admin.ModelAdmin):
    """Admin interface for consent records."""

    list_display = [
        "user",
        "consent_type",
        "is_given_display",
        "version",
        "given_at",
        "withdrawn_at",
    ]

    list_filter = [
        "consent_type",
        "is_given",
        "given_at",
    ]

    search_fields = [
        "user__username",
        "user__email",
    ]

    readonly_fields = [
        "id",
        "user",
        "consent_type",
        "version",
        "consent_text",
        "ip_address",
        "user_agent",
        "given_at",
        "withdrawn_at",
        "created_at",
        "updated_at",
    ]

    fieldsets = (
        ("Consent Information", {
            "fields": ("id", "user", "consent_type", "is_given", "version")
        }),
        ("Details", {
            "fields": ("consent_text",)
        }),
        ("Metadata", {
            "fields": ("ip_address", "user_agent")
        }),
        ("Timestamps", {
            "fields": ("given_at", "withdrawn_at", "created_at", "updated_at")
        }),
    )

    def is_given_display(self, obj):
        """Display consent status with color."""
        if obj.is_given:
            return format_html('<span style="color: green;">✓ Given</span>')
        return format_html('<span style="color: red;">✗ Withdrawn</span>')
    is_given_display.short_description = "Status"


@admin.register(DataExportRequest)
class DataExportRequestAdmin(admin.ModelAdmin):
    """Admin interface for data export requests."""

    list_display = [
        "user",
        "status_display",
        "export_format",
        "requested_at",
        "file_size_display",
        "download_count",
    ]

    list_filter = [
        "status",
        "export_format",
        "requested_at",
    ]

    search_fields = [
        "user__username",
        "user__email",
    ]

    readonly_fields = [
        "id",
        "user",
        "requested_at",
        "processed_at",
        "expires_at",
        "last_downloaded_at",
        "file_size",
        "download_count",
    ]

    fieldsets = (
        ("Request Information", {
            "fields": ("id", "user", "status", "export_format")
        }),
        ("File Information", {
            "fields": ("file_path", "file_size", "download_count")
        }),
        ("Timestamps", {
            "fields": ("requested_at", "processed_at", "expires_at", "last_downloaded_at")
        }),
        ("Error Information", {
            "fields": ("error_message",),
            "classes": ("collapse",),
        }),
    )

    def status_display(self, obj):
        """Display status with color."""
        colors = {
            "pending": "orange",
            "processing": "blue",
            "completed": "green",
            "failed": "red",
            "expired": "gray",
        }
        color = colors.get(obj.status, "black")
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = "Status"

    def file_size_display(self, obj):
        """Display file size in human-readable format."""
        if not obj.file_size:
            return "-"

        size = obj.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    file_size_display.short_description = "File Size"


@admin.register(DataDeletionRequest)
class DataDeletionRequestAdmin(admin.ModelAdmin):
    """Admin interface for data deletion requests."""

    list_display = [
        "username",
        "email",
        "status_display",
        "requested_at",
        "grace_period_end",
        "deleted_at",
    ]

    list_filter = [
        "status",
        "requested_at",
    ]

    search_fields = [
        "username",
        "email",
    ]

    readonly_fields = [
        "id",
        "user",
        "username",
        "email",
        "requested_at",
        "scheduled_deletion_at",
        "deleted_at",
        "cancelled_at",
        "data_removed",
    ]

    fieldsets = (
        ("Request Information", {
            "fields": ("id", "user", "username", "email", "status", "reason")
        }),
        ("Schedule", {
            "fields": ("grace_period_end", "scheduled_deletion_at")
        }),
        ("Completion", {
            "fields": ("deleted_at", "cancelled_at", "data_removed")
        }),
        ("Error Information", {
            "fields": ("error_message",),
            "classes": ("collapse",),
        }),
    )

    def status_display(self, obj):
        """Display status with color."""
        colors = {
            "pending": "orange",
            "grace_period": "blue",
            "processing": "purple",
            "completed": "red",
            "cancelled": "green",
            "failed": "darkred",
        }
        color = colors.get(obj.status, "black")
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = "Status"


@admin.register(PrivacyPolicyVersion)
class PrivacyPolicyVersionAdmin(admin.ModelAdmin):
    """Admin interface for privacy policy versions."""

    list_display = [
        "version",
        "title",
        "is_active_display",
        "effective_date",
        "created_at",
        "created_by",
    ]

    list_filter = [
        "is_active",
        "effective_date",
    ]

    search_fields = [
        "version",
        "title",
        "summary",
    ]

    readonly_fields = [
        "id",
        "created_at",
        "created_by",
    ]

    fieldsets = (
        ("Version Information", {
            "fields": ("id", "version", "title", "is_active", "effective_date")
        }),
        ("Content", {
            "fields": ("content", "summary")
        }),
        ("Metadata", {
            "fields": ("created_at", "created_by")
        }),
    )

    def is_active_display(self, obj):
        """Display active status with color."""
        if obj.is_active:
            return format_html('<span style="color: green;">✓ Active</span>')
        return format_html('<span style="color: gray;">○ Inactive</span>')
    is_active_display.short_description = "Status"
